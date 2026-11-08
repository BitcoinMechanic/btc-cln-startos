const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),ts=require('typescript')
function load(file,mocks={}){const filename=path.resolve(file),m=new Module(filename,module);m.filename=filename;m.paths=module.paths;m.require=n=>n in mocks?mocks[n]:require(n);m._compile(ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,filename);return m.exports}
async function main(){
 const calls=[];let address=null
 const sdk={Mounts:{of:()=>({mountVolume:()=>({})})},host:{getBridgeAddress:(_,options)=>{calls.push(options);return {const:async()=>address}}}}
 const u=load('startos/utils.ts',{'./sdk':{sdk},'bitcoin-core-startos/startos/utils':{rpcHostId:'rpc',rpcPort:8332}})
 for(const a of [null,'10.0.3.1:18432','[fd00:3::1]:45678']){
  address=a;calls.length=0;const result=await u.bitcoindRpcBridge({})
  assert.deepEqual(calls,[{packageId:'knots-prerdts',hostId:'rpc',internalPort:8332,ssl:false}])
  if(!a)assert.equal(result,null);else assert.deepEqual(result,a.startsWith('[')?{host:'fd00:3::1',port:45678}:{host:'10.0.3.1',port:18432})
 }
 const declared=[]
 sdk.Dependency={required:(id,opts)=>{declared.push({id,...opts});return {id}}}
 sdk.Dependencies={of:()=>({addDependency:v=>v})}
 load('startos/dependencies.ts',{'./sdk':{sdk},'./manifest/i18n':{depBitcoindDescription:'fixture'}})
 assert.equal(declared.length,1);assert.equal(declared[0].id,'knots-prerdts');assert.equal(declared[0].versionRange,'>=#knotsprerdts:31.2:0')
 const chain={chain:'main',initialblockdownload:false,pruned:true,pruneheight:961650,blocks:961700},hash='11'.repeat(32),header='22'.repeat(80)
 u.verifyBtcBackend(chain,hash,header);u.verifyBtcBackend({...chain,pruned:false},hash,header)
 for(const change of [{chain:'regtest'},{initialblockdownload:true},{pruneheight:-1},{pruneheight:'1'},{pruneheight:999999},{pruned:null},{blocks:0}])assert.throws(()=>u.verifyBtcBackend({...chain,...change},hash,header))
 assert.throws(()=>u.verifyBtcBackend(chain,'0000000000000050c1e5f69672f459293be14f46e5a494e7a8c8541396f18eeb',header))
 assert.throws(()=>u.verifyBtcBackend(chain,hash,'22'.repeat(164)))
 const rpc=[]
 await u.verifyBtcHistory(chain,async(method,...args)=>{rpc.push([method,...args]);return method==='getblockhash'?hash:'00'.repeat(200)})
 assert.deepEqual(rpc,[['getblockhash','961640'],['getblock',hash,'0']])
 for(const bad of ['', 'bad', '00'])await assert.rejects(()=>u.verifyBtcHistory(chain,async method=>method==='getblockhash'?hash:bad))
 await assert.rejects(()=>u.verifyBtcHistory(chain,async()=>{throw Error('unavailable')}))
 await u.verifyBtcHistory({...chain,pruned:false},async()=>{throw Error('unexpected probe')})
 console.log('PASS: exclusive companion dependency, assigned IPv4/IPv6 bridge, SHA256 identity, pruning metadata, historical block probe and unavailable-peer refusal')
}
main().catch(e=>{console.error(e);process.exitCode=1})
