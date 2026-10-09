const assert = require('node:assert/strict')
const fs = require('node:fs')
const { manifest, actions } = require('../javascript/index.js')
assert.equal(manifest.id, 'c-lightning')
assert.equal(manifest.version, '26.6.9:6')
assert.equal(manifest.packageRepo, 'https://github.com/BitcoinMechanic/btc-cln-startos')
assert.deepEqual(Object.keys(manifest.images), ['lightning', 'ui'])
assert.equal(manifest.images.lightning.source.dockerBuild.dockerfile, 'Dockerfile')
assert.equal(manifest.dependencies.bitcoind.optional, false)
for (const id of ['enable-reverse-session','pause-reverse-session','enable-swap-session', 'pause-swap-session', 'authorize-forward-pilot', 'gate-credential-status', 'gate-credential-create', 'gate-credential-revoke', 'inspection-credential-status', 'inspection-credential-create', 'inspection-credential-revoke', 'btc-gate-status', 'btc-gate-activate', 'controller-credential-status', 'controller-credential-create', 'controller-credential-revoke', 'coordinator-status', 'coordinator-prepare', 'node-info']) {
  assert.ok(actions.actions[id], id)
}
const backup = fs.readFileSync('startos/backups.ts', 'utf8')
assert.ok(backup.includes("'coordinator-preparation.json'"))
assert.ok(backup.includes("unlink('/media/startos/volumes/main/coordinator-preparation.json')"))
console.log('BTC package identity, images, preparation actions and restore invalidation checks OK')

assert.ok(backup.includes("'btc-gate-activation.json'"))
assert.ok(backup.includes('btc-gate-restored.json'))
assert.ok(!backup.includes("'bitcoin/swap-gate'"))
const main = fs.readFileSync('startos/main.ts', 'utf8')
assert.ok(main.includes("'/usr/local/libexec/btc-controller/gate.py'"))
assert.ok(main.includes("'launch'"))
console.log('BTC gate action registration, startup wrapper and restore barrier checks OK')

assert.ok(backup.includes('controller-inspection-read-only.json'))
assert.ok(require('node:fs').readFileSync('Dockerfile','utf8').includes('inspection_credential.py'))

require('./test-inspection-action.cjs')().catch(e => { console.error(e); process.exit(1) })

require('./test-reverse-session-actions.cjs')().catch(e=>{console.error(e);process.exit(1)})
