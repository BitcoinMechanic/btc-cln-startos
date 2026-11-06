"""Repack :1 JavaScript over the exact verified :0 images; no engine rebuild.

Usage: python3 package/scripts/suitbox/pack-legacy.py BUILD_DIR BASELINE_DIR
Both directories must be within the existing StartOS packaging workspace.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import tarfile


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def run(args, **kwargs):
    return subprocess.check_output([str(a) for a in args], **kwargs)


def member(package, name):
    return run(['start-cli', 's9pk', 'inspect', package, 'cat', name])


R, B = (Path(a).resolve() for a in sys.argv[1:])
P = R/'package'
baseline = B/'c-lightning_x86_64.s9pk'
assert sha(baseline) == 'a255a81fa5e8e13bf2d7a8c65d4f7fa3cf76ec164224e9204d3872a528ffdd5b'
prior = json.loads((B/'build-receipt.json').read_text())
assert prior['sha256'] == sha(baseline)
assert (R/'typecheck.log').read_text() == ''
assert (R/'sdk-lint.log').read_text() == ''
for file, marker in [('migration-test.log', 'PASS:'), ('legacy-wiring.log', 'PASS:'),
                     ('legacy-python-tests.log', 'OK'), ('installed-registry.log', 'PASS:'),
                     ('funded-legacy-final.log', '"ordinary_payments": 5')]:
    assert marker in (R/file).read_text(), file
input0 = json.loads((B/'input-manifest.json').read_text())
sources = {}
for image, ident in prior['images'].items():
    archive = B/(image+'-'+ident.removeprefix('sha256:')+'-image.tar')
    with tarfile.open(archive) as t:
        entries = json.load(t.extractfile('manifest.json'))
        assert len(entries) == 1
        config_bytes = t.extractfile(entries[0]['Config']).read()
        assert 'sha256:'+hashlib.sha256(config_bytes).hexdigest() == ident
        config = json.loads(config_bytes)
        assert len(entries[0]['Layers']) == len(config['rootfs']['diff_ids'])
        for layer, expected in zip(entries[0]['Layers'], config['rootfs']['diff_ids']):
            assert 'sha256:'+hashlib.file_digest(t.extractfile(layer), 'sha256').hexdigest() == expected
    sources[image] = {'ociLayout': {'path':str(archive)}}
with (P/'javascript/index.js').open('a') as js:
    for image, source in sources.items():
        js.write('\nmodule.exports.manifest.images['+json.dumps(image)+'].source='+json.dumps(source)+';\n')
manifest = json.loads(run(['node','-e','console.log(JSON.stringify(require("./javascript/index.js").manifest))'],cwd=P,text=True))
assert manifest['id'] == 'c-lightning' and manifest['version'] == '#privkeyio:26.6.10:1' and manifest['volumes'] == ['main']
assert set(manifest['images']) == {'lightning','ui'}
for image in manifest['images'].values():
    assert image['arch'] == ['x86_64'] and image['emulateMissing'] is False


def migration_clauses(value):
    return set(re.sub(r'[()\s]', '', value).split('||'))


expected_from = {'=#privkeyio:26.6.10:1', '=#privkeyio:26.6.10:0', '=26.6.10:0'}
assert migration_clauses(manifest['canMigrateFrom']) == expected_from
assert manifest['canMigrateTo'] == '=#privkeyio:26.6.10:1'
(R/'input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
output = R/'c-lightning_x86_64.s9pk'
with (R/'pack.log').open('w') as log:
    subprocess.run(['start-cli','s9pk','pack','--arch=x86_64','-o',str(output)],cwd=P,stdout=log,stderr=subprocess.STDOUT,check=True)
packed = json.loads(run(['start-cli','s9pk','inspect',output,'manifest'],text=True))
(R/'packed-manifest.json').write_text(json.dumps(packed,indent=2)+'\n')
for key in ('id','version','volumes','canMigrateTo'):
    assert packed[key] == manifest[key], key
assert migration_clauses(packed['canMigrateFrom']) == expected_from
for name, dependency in manifest['dependencies'].items():
    for field in ('requirement','description','optional'):
        if field in dependency:
            assert packed['dependencies'][name][field] == dependency[field]
for image in ('lightning', 'ui'):
    for field in ('arch','emulateMissing'):
        assert packed['images'][image][field] == manifest['images'][image][field]
    for suffix in ('json','squashfs'):
        name='images/x86_64/'+image+'.'+suffix
        assert hashlib.sha256(member(output,name)).digest() == hashlib.sha256(member(baseline,name)).digest(), 'packed image changed: '+name
js_squash = R/'packed-js.squashfs'
js_squash.write_bytes(member(output,'javascript.squashfs'))
packed_js = run(['unsquashfs','-cat',js_squash,'index.js'])
assert hashlib.sha256(packed_js).hexdigest() == sha(P/'javascript/index.js')
assert b'wallet_requires_clean_shutdown' in packed_js and b'retired_payment_attempt_not_failed_self_payment' in packed_js
(R/'packed-index.js').write_bytes(packed_js)
subprocess.run(['node','scripts/suitbox/test-installed.cjs',str(R/'packed-index.js')],cwd=P,check=True)
receipt = dict(version='#privkeyio:26.6.10:1',sha256=sha(output),baseline_installer_sha256=sha(baseline),
               images=prior['images'],native_runtime_ui_byte_identical_to_baseline=True,
               new_checks=['exact-version-graph','read-only-temporary-mount-and-failure-controls','legacy-wallet-validator-positive-and-negative-controls',
                           'real-regtest-wallet-current-and-archived-funding','five-ordinary-payments-and-same-volume-update',
                           'legacy-record-preservation-and-no-implicit-authority','explicit-coordinator-setup-and-restart','packed-javascript-manifest-and-28-actions',
                           'packed-native-runtime-ui-byte-comparison'],
               inherited_native_checks=prior['checks'],inherited_checks_rerun=False,legacy_fixture_envelopes='synthetic; bound to real disposable BTC wallet evidence',
               live_StartOS_acceptance=False,routed_cross_chain_swaps_rerun=False,existing_controller_unchanged=True)
(R/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
(R/'SHA256SUMS').write_text(''.join(sha(R/name)+'  '+name+'\n' for name in ('c-lightning_x86_64.s9pk','build-receipt.json')))
print(json.dumps(receipt,indent=2))
