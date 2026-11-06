const assert = require('node:assert/strict')
const fs = require('node:fs/promises')
const { readFileSync } = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const Module = require('node:module')
const ts = require('typescript')
function load(file, mocks = {}) {
  const filename = path.resolve(file), mod = new Module(filename, module)
  mod.filename = filename; mod.paths = module.paths
  mod.require = name => name in mocks ? mocks[name] : require(name)
  mod._compile(ts.transpileModule(readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, filename)
  return mod.exports
}
async function main() {
 const root = await fs.mkdtemp(path.join(os.tmpdir(), 'suitbox-migration-'))
 const sdk = {volumes: {main: {subpath: () => root}}, Mounts: {of: () => ({mountVolume: () => ({})})}}
 const utils = load('startos/utils.ts', {'./sdk': {sdk}, 'bitcoin-core-startos/startos/utils': {rpcHostId:'rpc', rpcPort:8332}})
 let legacyCalls=0
 const current = load('startos/versions/current.ts', {'../live/legacyUpgrade':{verifyLegacyOfficialBtcUpgrade:async()=>{
   legacyCalls++; await utils.verifyOfficialBtcUpgrade(root)
 }}}).current
 const historical = load('startos/versions/v_privkeyio26.6.10_0.ts', {'../sdk':{sdk}, '../utils':utils}).v_privkeyio_26_6_10_0
 const graph = load('startos/versions/index.ts', {'./current':{current}, './v_privkeyio26.6.10_0':{v_privkeyio_26_6_10_0:historical}}).versionGraph
 const {ExtendedVersion} = Module.createRequire(require.resolve('@start9labs/start-sdk'))('@start9labs/start-core/exver')
 const from = ExtendedVersion.parse('26.6.10:0'), to = ExtendedVersion.parse('#privkeyio:26.6.10:1')
 assert.ok(graph.canMigrateFrom().satisfiedBy(from))
 for (const v of ['26.6.9:0','26.6.10:1','26.6.11:0','#privkeyio:26.6.9:0','#legacy:26.6.10:0']) assert.equal(graph.canMigrateFrom().satisfiedBy(ExtendedVersion.parse(v)),false,v)
 assert.equal(graph.canMigrateTo().satisfiedBy(from),false)
 const files = {'bitcoin/hsm_secret':'synthetic-secret','bitcoin/lightningd.sqlite3':'SQLite format 3\0sentinel','store.json':'{"restore":false,"rescan":-500,"custom":"keep"}', '.commando-env':'synthetic-rune-sentinel', 'data/app/config.json':'{"password":"synthetic-sentinel"}', '.watchtower/watchtowers_db.sql3':'watchtower-sentinel'}
 try {
  for (const [name,raw] of Object.entries(files)) {const p=path.join(root,name);await fs.mkdir(path.dirname(p),{recursive:true});await fs.writeFile(p,raw)}
  const versions=[],effects={setDataVersion:async({version})=>versions.push(version)}
  await graph.migrate({effects,from,to})
  assert.equal(legacyCalls,1,'official update must select the new direct validator, not historical :0 admission')
  assert.equal(versions.at(-1),to.toString())
  for (const [name,raw] of Object.entries(files)) assert.equal(await fs.readFile(path.join(root,name),'utf8'),raw)
  for (const name of ['node-restored.json','bitcoin/swap-coordinator-v1','bitcoin/bounded-authority-v1','forward-sessions','regtest']) {
   await fs.writeFile(path.join(root,name),'blocked');await assert.rejects(()=>graph.migrate({effects,from,to}));await fs.unlink(path.join(root,name))
  }
  await fs.mkdir(path.join(root,'forward-sessions'))
  let checked=0
  await utils.verifyOfficialBtcUpgrade(root,async()=>{checked++})
  assert.equal(checked,1)
  await assert.rejects(()=>utils.verifyOfficialBtcUpgrade(root,async()=>{throw Error('legacy refused')}),/legacy refused/)
  await fs.rmdir(path.join(root,'forward-sessions'))
  const prior=ExtendedVersion.parse('#privkeyio:26.6.10:0')
  assert.ok(graph.canMigrateFrom().satisfiedBy(prior))
  const callsBefore=legacyCalls
  await graph.migrate({effects,from:prior,to})
  assert.equal(legacyCalls,callsBefore,'already validated candidate namespace must not be reinterpreted as legacy')
  await fs.writeFile(path.join(root,'store.json'),'{"restore":true}');await assert.rejects(()=>graph.migrate({effects,from,to}));await fs.writeFile(path.join(root,'store.json'),files['store.json'])
  await fs.rename(path.join(root,'bitcoin/hsm_secret'),path.join(root,'saved-secret'))
  await fs.symlink('../saved-secret',path.join(root,'bitcoin/hsm_secret'));await assert.rejects(()=>graph.migrate({effects,from,to}));await fs.unlink(path.join(root,'bitcoin/hsm_secret'))
  await fs.rename(path.join(root,'saved-secret'),path.join(root,'bitcoin/hsm_secret'))
  const good={chain:'main',initialblockdownload:false,pruned:false,blocks:961700},hash='11'.repeat(32),header='22'.repeat(80)
  utils.verifyBtcBackend(good,hash,header)
  for (const c of [{...good,chain:'regtest'},{...good,pruned:true},{...good,initialblockdownload:true},{...good,blocks:0}]) assert.throws(()=>utils.verifyBtcBackend(c,hash,header))
  assert.throws(()=>utils.verifyBtcBackend(good,'0000000000000050c1e5f69672f459293be14f46e5a494e7a8c8541396f18eeb',header))
  assert.throws(()=>utils.verifyBtcBackend(good,hash,header+'00'))
  console.log('PASS: exact official-version admission; identity, database, UI, watchtower and flags unchanged; foreign/restore/legacy/symlink state refused; BTC backend boundaries')
 } finally {await fs.rm(root,{recursive:true,force:true})}
}
main().catch(e=>{console.error(e);process.exitCode=1})
