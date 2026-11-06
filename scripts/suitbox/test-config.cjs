const fs=require('node:fs'),Module=require('node:module'),path=require('node:path'),ts=require('typescript');
const real=require('@start9labs/start-sdk');
function load(file,mocks){const m=new Module(path.resolve(file),module);m.filename=path.resolve(file);m.paths=module.paths;m.require=n=>n in mocks?mocks[n]:require(n);m._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,m.filename);return m.exports;}
const sdk={InputSpec:{of:x=>x},Value:new Proxy({},{get:()=>x=>x}),volumes:{main:{}},Mounts:{of:()=>({mountVolume:()=>({})})}};
const utils=load('startos/utils.ts',{'./sdk':{sdk},'bitcoin-core-startos/startos/utils':{rpcHostId:'rpc',rpcPort:8332}});
let serialize;
load('startos/fileModels/config.ts',{'../sdk':{sdk},'../utils':utils,'../i18n':{i18n:x=>x},'@start9labs/start-sdk':{...real,FileHelper:{raw:(where,write)=>{serialize=write;return {}}}}});
fs.writeFileSync('/work/generated-config.ini',serialize({clnrest:true}));
console.log('PASS: generated configuration from real package serializer');
