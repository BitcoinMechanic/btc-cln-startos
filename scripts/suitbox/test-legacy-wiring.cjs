const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),ts=require('typescript');
function load(file,mocks={}){const filename=path.resolve(file),m=new Module(filename,module);m.filename=filename;m.paths=module.paths;m.require=n=>n in mocks?mocks[n]:require(n);m._compile(ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,filename);return m.exports;}
async function main(){
 const {legacyUpgradeProgram}=load('startos/live/legacyUpgradeProgram.ts');
 assert.ok(legacyUpgradeProgram.includes('mode=ro&immutable=1'));
 assert.ok(legacyUpgradeProgram.includes('legacy_authority_imported=False'));
 const effects={},root='/synthetic-volume';let response,calls=0,checked=0;
 const mounts={};
 const sdk={volumes:{main:{subpath:p=>{assert.equal(p,'');return root}}},Mounts:{of:()=>({mountVolume:o=>{assert.deepEqual(o,{volumeId:'main',subpath:null,mountpoint:'/root/.lightning',readonly:true});return mounts}})},SubContainer:{withTemp:async(e,image,m,name,fn)=>{
   assert.equal(e,effects);assert.deepEqual(image,{imageId:'lightning'});assert.equal(m,mounts);assert.equal(name,'legacy-btc-upgrade-check');
   return fn({exec:async argv=>{assert.deepEqual(argv,['python3','-B','-c',legacyUpgradeProgram,'/root/.lightning']);calls++;return response}})
 }}};
 const {verifyLegacyOfficialBtcUpgrade}=load('startos/live/legacyUpgrade.ts',{'../sdk':{sdk},'../utils':{rootDir:'/root/.lightning',verifyOfficialBtcUpgrade:async(r,fn)=>{assert.equal(r,root);checked++;await fn()}},'./legacyUpgradeProgram':{legacyUpgradeProgram}});
 response={exitCode:0,stdout:JSON.stringify({admitted:true,legacy_records_preserved:true,legacy_authority_imported:false})};
 await verifyLegacyOfficialBtcUpgrade(effects);assert.equal(calls,1);assert.equal(checked,1);
 for(const reply of [{exitCode:1,stdout:'private malformed output'}, {exitCode:0,stdout:JSON.stringify({admitted:true})}, {exitCode:1,stdout:JSON.stringify({admitted:false,reason:'private-secret=value'})}, {exitCode:0,stdout:JSON.stringify({admitted:false,reason:'pending_or_unknown_payment'})}]){
   response=reply;await assert.rejects(()=>verifyLegacyOfficialBtcUpgrade(effects),e=>!e.message.includes('private')&&e.message.includes('preserved'));
 }
 console.log('PASS: exact embedded Python; read-only mount; no daemon invocation; failure/partial/malformed reports cannot admit migration');
}
main().catch(e=>{console.error(e);process.exitCode=1});
