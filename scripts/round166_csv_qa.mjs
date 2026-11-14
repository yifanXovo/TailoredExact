// Read-only CSV/schema/endpoint audit. No workbook edits, exports or optimization.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import crypto from 'node:crypto';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'results/unified_exact_round166');
const scratch='E:/codes/ExactEBRP-work/temp/round166/csv-qa';
const require=createRequire(path.join(scratch,'package.json'));
const {Workbook}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const read=async name=>JSON.parse(await fs.readFile(path.join(out,name),'utf8'));
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const assert=(condition,message)=>{if(!condition)throw new Error(message);};
const summary=await read('reports/summary.json');assert(summary.complete,'Require complete panel');
const file=path.join(out,'reports/GI_TBC_R166_B_controls_increment_28col.csv');
const bytes=await fs.readFile(file);assert(bytes.subarray(0,3).equals(Buffer.from([239,187,191])),'UTF8 BOM');
const workbook=await Workbook.fromCSV(bytes.toString('utf8').replace(/^\uFEFF/,''),{sheetName:'B controls'});
const sheet=workbook.worksheets.getItem('B controls');
const values=sheet.getUsedRange().values;
const baseline=path.join(root,'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv');
const baseBytes=await fs.readFile(baseline);
const baseWorkbook=await Workbook.fromCSV(new TextDecoder('gb18030').decode(baseBytes),{sheetName:'Original schema'});
const headers=baseWorkbook.worksheets.getItem('Original schema').getRange('A1:AB1').values[0];
const blank=v=>v===null||v===undefined||v==='';
assert(values.length===7 && values.every(row=>row.length===28),'Seven rows/28 columns');
assert(headers.every((v,i)=>blank(v)?blank(values[0][i]):v===values[0][i]),'Exact reference column labels including two blanks');
const arms=(await read('reports/complete_arms.json')).filter(a=>a.method==='B');
const groups=(await read('matrix_frozen.json')).groups;
const checks=[];
for(let i=0;i<6;i++){
  const row=values[i+1],a=arms[i],p=groups.find(g=>g.position===a.position).launch.panel;
  assert(row[0]===a.id,'ID');assert(Number(row[1])===p.V&&Number(row[2])===p.M,'Counts');
  assert(Number(row[7])===p.T_seconds&&Number(row[8])===p.lambda,'Physical T and actual lambda');
  assert(Number(row[10])===0&&Number(row[12])===166&&Number(row[13])===p.cap_seconds,'Seed/round/cap');
  assert(row[14]===(a.certificate?'已收敛':'未收敛'),'B state');
  assert(a.certificate?Number(row[15])===a.T_cert:blank(row[15]),'CERT clock versus OPEN blank');
  assert(a.certificate?blank(row[16]):Number(row[16])===100*a.relative_gap,'OPEN percentage versus CERT blank');
  assert(Number(row[17])===a.L&&Number(row[18])===a.U,'Full-precision qualified endpoints');
  assert(row[19]==='无配对结果'&&[20,21,22,23].every(j=>blank(row[j]))&&row[24]==='N/A','Unpaired P fields');
  assert(row[25].includes(a.arm_id)&&row[25].includes(a.source_commit)&&row[25].includes(a.PE_SHA),'Run/source/build provenance');
  assert(row[26].startsWith('https://github.com/yifanXovo/TailoredExact/')&&row[27].endsWith(p.input_path),'Two source fields');
  checks.push({row:i+2,id:a.id,position:a.position,passed:true});
}
assert((await fs.readFile(file)).equals(bytes)&&(await fs.readFile(baseline)).equals(baseBytes),'Read-only byte preservation');
const inspection=await workbook.inspect({kind:'region',sheetId:'B controls',range:'O1:Y7',include:'values',tableMaxRows:7,tableMaxCols:11,maxChars:2400});
const result={UTC:new Date().toISOString(),PASS:true,operation:'read-only CSV import and endpoint/schema audit',
  tool:'bundled @oai/artifact-tool; public Workbook.fromCSV/range.values/inspect APIs',
  rows:6,columns:28,blank_trailing_reference_headers_preserved:true,UTF8_BOM:true,
  original_working_copy_encoding:'GB18030; unchanged',P_numeric_fields_empty:true,new_B_P_pairs:0,
  exact_qualified_endpoint_numbers:true,OPEN_T_cert_blank:true,read_only:true,workbook_edits:0,workbook_exports:0,
  source_CSV_SHA256:hash(bytes),reference_SHA256:hash(baseBytes),checks,compact_inspection:inspection.ndjson,
  Optimization:0,authoritative_serialization:'The user-required28-column CSV and full binary64 values are preserved; no XLSX variant is produced.'};
await fs.writeFile(path.join(out,'CSV_QA.json'),JSON.stringify(result,null,2)+'\n','utf8');
console.log('Read-only Artifact Tool CSV QA PASS:6 rows,28 columns, exact endpoints, empty unpaired P fields.');
