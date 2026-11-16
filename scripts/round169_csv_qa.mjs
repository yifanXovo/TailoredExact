// Read-only Artifact Tool CSV audit. Exact requested CSV bytes remain authoritative.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'results/unified_exact_round169');
const require=createRequire('E:/codes/ExactEBRP-work/temp/round169/csv-qa/package.json');
const {Workbook}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const read=async name=>JSON.parse(await fs.readFile(path.join(out,name),'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const assert=(condition,message)=>{if(!condition)throw new Error(message);};
const complete=await read('complete_arms.json');assert(complete.all_18_qualified,'Require qualified panel');
const file=path.join(out,'GI_TBC_R169_B_controls_increment_28col.csv');
const bytes=await fs.readFile(file);assert(bytes.subarray(0,3).equals(Buffer.from([239,187,191])),'UTF8 BOM');
const workbook=await Workbook.fromCSV(bytes.toString('utf8').replace(/^\uFEFF/,''),{sheetName:'B controls'});
const values=workbook.worksheets.getItem('B controls').getUsedRange().values;
const baseline=path.join(root,'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv');
const old=await fs.readFile(baseline);
const baseWorkbook=await Workbook.fromCSV(new TextDecoder('gb18030').decode(old),{sheetName:'Original schema'});
const headers=baseWorkbook.worksheets.getItem('Original schema').getRange('A1:AB1').values[0];
const blank=v=>v===null||v===undefined||v==='';
assert(values.length===7&&values.every(r=>r.length===28),'6 records and 28 columns');
assert(headers.every((v,i)=>blank(v)?blank(values[0][i]):v===values[0][i]),'Exact original headers including two trailing blanks');
const arms=complete.rows.filter(a=>a.arm==='B');
const roles=(await read('h_panel_frozen.json')).roles;
const checks=[];
for(let i=0;i<6;i++){
  const row=values[i+1],a=arms[i],p=roles.find(p=>p.id===a.role);
  assert(row[0]===a.role&&Number(row[1])===p.V&&Number(row[2])===p.M,'Role and vehicle/station counts');
  assert(Number(row[7])===p.T_seconds&&Number(row[8])===p.lambda,'Physical T and original binary64 lambda');
  assert(Number(row[10])===0&&Number(row[12])===169&&Number(row[13])===a.cap_seconds,'Native Seed/round/cap');
  assert(row[14]===(a.certificate?'已收敛':'未收敛'),'Qualified B status');
  assert(a.certificate?Number(row[15])===a.T_total_with_independent_audit:blank(row[15]),'CERT measured time / OPEN blank');
  assert(a.certificate?blank(row[16]):Number(row[16])===100*a.relative_gap,'OPEN percentage / CERT blank');
  assert(Number(row[17])===a.L&&Number(row[18])===a.U,'Full binary64 qualified endpoints');
  assert(row[19]==='无配对结果'&&[20,21,22,23].every(j=>blank(row[j]))&&row[24]==='N/A','Unpaired P fields remain empty');
  assert(row[25].includes(a.run_id)&&row[25].includes(a.measured_core_source_commit)&&row[25].includes(a.PE_SHA256),'Actual run/source/PE');
  assert(row[26].endsWith('results/unified_exact_round169/complete_arms.json')&&row[27].endsWith(a.audit_path),'Fixed evidence links');
  checks.push({row:i+2,role:a.role,position:a.position,PASS:true});
}
assert((await fs.readFile(file)).equals(bytes)&&(await fs.readFile(baseline)).equals(old),'No bytes changed');
const inspect=await workbook.inspect({kind:'region',sheetId:'B controls',range:'O1:Y7',include:'values',tableMaxRows:7,tableMaxCols:11,maxChars:2200});
await fs.writeFile(path.join(out,'CSV_QA.json'),JSON.stringify({UTC:new Date().toISOString(),PASS:true,
  operation:'read-only Artifact Tool import/schema/endpoint validation',rows:6,columns:28,UTF8_BOM:true,
  exact_qualified_binary64_endpoints:true,P_fields_empty:true,new_B_P_pairs:0,workbook_edits:0,workbook_exports:0,
  source_CSV_SHA256:hash(bytes),protected_103_row_reference_SHA256:hash(old),checks,inspection:inspect.ndjson,
  source_contract:'User requests byte-exact CSV and unchanged historical rows; no workbook redesign, formulas or XLSX variant',Optimize:0},null,2)+'\n');
console.log('Read-only Artifact Tool CSV QA PASS: six B records, original 28 columns, exact endpoints, zero P pairs.');
