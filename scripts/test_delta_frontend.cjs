/* Pure contract checks without a browser or a second frontend implementation. */
const assert=require('node:assert/strict');
const fs=require('fs');
const vm=require('vm');
const ts=require('../web/frontend/node_modules/typescript');
function load(relative,jsonOverride){
  const source=fs.readFileSync(relative,'utf8');
  const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;
  const exports={};vm.runInNewContext(code,{exports,require:name=>name==='./vi.json'?jsonOverride:require(name)});return exports;
}
const format=load('web/frontend/lib/format.ts');
const labels=[2,10,18,26,34,42,50,58];
assert.equal(new Set(labels.map(id=>format.clusterColor(id,labels))).size,8);
assert(!labels.map(id=>format.clusterColor(id,labels)).includes(format.clusterColor(-1,labels)));
assert.equal(format.number(null),'—');assert.notEqual(format.number(0),'—');
const {localizePayload}=load('web/frontend/lib/vi.ts',{SENTINEL:'Đã dịch'});
const result=localizePayload({label:'SENTINEL',description:'SENTINEL',availability:'SENTINEL',version:'SENTINEL',unit:'SENTINEL',value:'123.000000000000000001',components:{reason:'SENTINEL'},protocol:{name:'SENTINEL'}});
assert.equal(result.label,'Đã dịch');assert.equal(result.description,'Đã dịch');
for(const key of ['availability','version','unit'])assert.equal(result[key],'SENTINEL');
assert.equal(result.value,'123.000000000000000001');assert.equal(result.components.reason,'SENTINEL');assert.equal(result.protocol.name,'SENTINEL');
console.log('PASS: sparse categorical palette, negative labels, null/zero formatting, typed identifiers and raw evidence remain untranslated.');
