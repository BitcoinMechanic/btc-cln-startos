from pathlib import Path
import json,hashlib,subprocess
from inventory import inventory
R=Path(__file__).resolve().parent
def load(name):return json.loads((R/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=load('runtime-local-inventory.json')
assert inventory(R/'packed-runtime-root/usr/local')==source,'packed runtime differs'
old=inventory(R/'official-root/usr/local');dist=load('engine-dist-inventory.json')
for path,row in old.items():
 if path not in dist:assert source[path]==row,('official native file changed',path)
for path,row in dist.items():assert source[path]==row,('patched engine differs',path)
swap=load('original-swap-inventory.json')
assert {p.removeprefix('libexec/swap-node/'):v for p,v in source.items() if p.startswith('libexec/swap-node/')}==swap,'sealed swap runtime differs'
assert inventory(R/'packed-ui-root')==inventory(R/'official-ui-root'),'UI differs'
assert (R/'packed-runtime-root/opt/btc').is_symlink() and (R/'packed-runtime-root/opt/btc').readlink()==Path('/usr/local')
package=R/'c-lightning_x86_64.s9pk'
def member(package,name):return subprocess.check_output(['start-cli','s9pk','inspect',str(package),'cat',name])
for image in ('lightning','ui'):
 name=f'images/x86_64/{image}.json'
 assert json.loads(member(package,name))==json.loads(member(R/'official-c-lightning_26.6.10_0.s9pk',name)),('image metadata differs',image)
manifest=load('input-manifest.json');packed=load('packed-manifest.json')
for dep,row in manifest['dependencies'].items():
 for key in ('requirement','description','optional'):
  if key in row:assert packed['dependencies'][dep][key]==row[key],(dep,key)
receipt=dict(version='#privkeyio:26.6.10:0',sha256=sha(package),official_package_sha256=sha(R/'official-c-lightning_26.6.10_0.s9pk'),images=load('image-ids.json'),checks=['exact-version-migration-and-backend-boundaries','funded-official-to-candidate-update-four-payments','official-and-patched-four-plugin-crash-scenarios-each','recovery-witness-weight-baseline-and-repair','generated-config-full-plugins-and-restart','closing-channel-final-HTLC-replay','packed-manifest-and-javascript','packed-native-engine-and-original-plugins','unchanged-sealed-swap-runtime','unchanged-official-ui'],live_StartOS_acceptance=False,routed_cross_chain_swaps_rerun=False,existing_controller_unchanged=True)
(R/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
(R/'SHA256SUMS').write_text(''.join(sha(R/name)+'  '+name+'\n' for name in ['c-lightning_x86_64.s9pk','build-receipt.json']))
print(json.dumps(receipt,indent=2))
