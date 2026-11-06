"""Pack tested native images in the existing StartOS packaging workspace."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
R=Path(__file__).resolve().parent
P=R/'package'
def run(args,**kw):return subprocess.check_output([str(a) for a in args],**kw)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert 'PASS:' in (R/'migration-test.log').read_text()
for name,marker in [('funded-upgrade.log','"ordinary_payments": 4'),('crash-baseline-matrix.log','scenarios=4'),('crash-patched.log','scenarios=4'),('full-config.log','PASS:'),('closing-replay.log','PASS:')]:
 assert marker in (R/name).read_text(),name
sources={};ids={}
for key,tag in [('lightning','suitbox-cln-runtime:26.06.10-suitbox1'),('ui','suitbox-cln-ui:26.6.10')]:
 ident=run(['docker','image','inspect','--format','{{.Id}}',tag],text=True).strip();ids[key]=ident
 archive=R/(key+'-'+ident.removeprefix('sha256:')+'-image.tar')
 if not archive.exists():subprocess.run(['docker','save','-o',str(archive),ident],check=True)
 with tarfile.open(archive) as t:
  entries=json.load(t.extractfile('manifest.json'));assert len(entries)==1
  assert 'sha256:'+hashlib.sha256(t.extractfile(entries[0]['Config']).read()).hexdigest()==ident
 sources[key]={'ociLayout':{'path':str(archive)}}
with (P/'javascript/index.js').open('a') as js:
 for key,source in sources.items():js.write('\nmodule.exports.manifest.images['+json.dumps(key)+'].source='+json.dumps(source)+';\n')
manifest=json.loads(run(['node','-e','console.log(JSON.stringify(require("./javascript/index.js").manifest))'],cwd=P,text=True))
assert manifest['version']=='#privkeyio:26.6.10:0'
assert manifest['id']=='c-lightning'
assert manifest['volumes']==['main']
for row in manifest['images'].values():assert row['arch']==['x86_64'] and row['emulateMissing'] is False
(R/'input-manifest.json').write_text(json.dumps(manifest,indent=2))
(R/'image-ids.json').write_text(json.dumps(ids,indent=2))
output=R/'c-lightning_x86_64.s9pk'
with (R/'pack.log').open('w') as log:subprocess.run(['start-cli','s9pk','pack','--arch=x86_64','-o',str(output)],cwd=P,stdout=log,stderr=subprocess.STDOUT,check=True)
packed=json.loads(run(['start-cli','s9pk','inspect',output,'manifest'],text=True))
(R/'packed-manifest.json').write_text(json.dumps(packed,indent=2))
for key in ('id','version','volumes','canMigrateFrom','canMigrateTo'):assert packed[key]==manifest[key],key
for key in ('lightning','ui'):
 for field in ('arch','emulateMissing'):assert packed['images'][key][field]==manifest['images'][key][field],(key,field)
for member,dest in [('javascript.squashfs','packed-js.squashfs'),('images/x86_64/lightning.squashfs','packed-runtime.squashfs'),('images/x86_64/ui.squashfs','packed-ui.squashfs')]:
 with (R/dest).open('wb') as out:subprocess.run(['start-cli','s9pk','inspect',str(output),'cat',member],stdout=out,check=True)
assert hashlib.sha256(run(['unsquashfs','-cat',R/'packed-js.squashfs','index.js'])).hexdigest()==sha(P/'javascript/index.js')
for key in ('runtime','ui'):
 subprocess.run(['unsquashfs','-f','-no-xattrs','-d',str(R/('packed-'+key+'-root')),str(R/('packed-'+key+'.squashfs'))],stdout=subprocess.DEVNULL,check=True)
print('PACKED; pending filesystem inventory comparison:',sha(output),flush=True)
