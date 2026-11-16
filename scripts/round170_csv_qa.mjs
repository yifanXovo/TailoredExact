// Read-only Artifact Tool audit. User-prescribed CSV bytes remain authoritative.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'results/unified_exact_round170');
const require=createRequire('E:/codes/ExactEBRP-work/temp/round170/csv-qa/package.json');
const {Workbook}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const read=async name=>JSON.parse(await fs.readFile(path.join(out,name),'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const assert=(condition,message)=>{if(!condition)throw new Error(message);};
const complete=await read('complete_arms.json');assert(complete.all_22_qualified,'Require actual qualified panel');
const file=path.join(out,'GI_TBC_R170_B_increment_28col.csv');
const bytes=await fs.readFile(file);assert(bytes.subarray(0,3).equals(Buffer.from([239,187,191])),'UTF8 BOM');
const workbook=await Workbook.fromCSV(bytes.toString('utf8').replace(/^\uFEFF/,''),{sheetName:'B records'});
const values=workbook.worksheets.getItem('B records').getUsedRange().values;
const baseline=path.join(root,'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv');
const old=await fs.readFile(baseline);
const original=await Workbook.fromCSV(new TextDecoder('gb18030').decode(old),{sheetName:'Original schema'});
const headers=original.worksheets.getItem('Original schema').getRange('A1:AB1').values[0];
const blank=v=>v===null||v===undefined||v==='';
assert(values.length===9&&values.every(r=>r.length===28),'8 records, 28 columns');
assert(headers.slice(0,26).every((v,i)=>blank(v)?blank(values[0][i]):v===values[0][i]),'Original first 26 headers');
assert(values[0][26]==='实验数据来源'&&values[0][27]==='实例元数据来源','Authoritative source/metadata headers');
const arms=complete.rows.filter(a=>a.arm==='B');
const roles=(await read('inputs_frozen.json')).roles;const checks=[];let pairs=0;
for(let i=0;i<8;i++){
  const row=values[i+1],a=arms[i],p=roles.find(p=>p.id===a.role);
  const plain=complete.rows.find(x=>x.role===a.role&&x.Native_Seed===a.Native_Seed&&x.arm==='P');
  assert(row[0]===a.role&&Number(row[1])===p.V&&Number(row[2])===p.M,'Role and dimensions');
  assert(Number(row[7])===p.T_seconds&&Number(row[8])===p.lambda,'Original T/lambda');
  assert(Number(row[10])===a.Native_Seed&&Number(row[12])===170&&Number(row[13])===600,'Seed/round/cap');
  assert(row[14]===(a.certificate?'已收敛':'未收敛'),'Qualified B status');
  assert(a.certificate?Number(row[15])===a.T_cert_process:blank(row[15]),'CERT process endpoint / OPEN blank');
  assert(a.certificate?blank(row[16]):Number(row[16])===100*a.relative_gap,'OPEN percent');
  assert(Number(row[17])===a.L&&Number(row[18])===a.U,'Exact B endpoints');
  if(plain){
    pairs++;
    assert(plain.Native_Seed===1&&row[19]===(plain.certificate?'已收敛':'未收敛'),'Actual Seed1 P status');
    assert(plain.certificate?Number(row[20])===plain.T_cert_process:blank(row[20]),'P CERT process endpoint');
    assert(plain.certificate?blank(row[21]):Number(row[21])===100*plain.relative_gap,'P OPEN percent');
    assert(Number(row[22])===plain.L&&Number(row[23])===plain.U,'Exact actual P endpoints');
    assert(row[24]==='分指标比较','No synthetic win total');
  }else assert(row[19]==='无配对结果'&&[20,21,22,23].every(j=>blank(row[j]))&&row[24]==='N/A'&&row[25].includes('N/A-P'),'Five genuinely unpaired rows');
  assert(row[25].includes(a.run_id)&&row[25].includes(a.source_commit)&&row[25].includes(a.PE_SHA256),'Actual run/source/PE');
  assert(row[26].endsWith('results/unified_exact_round170/complete_arms.json'),'Actual data source');
  assert(row[27]==='https://github.com/yifanXovo/TailoredExact/blob/8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb/results/unified_exact_round163/input_manifest.json','Fixed original metadata');
  checks.push({row:i+2,role:a.role,Native_Seed:a.Native_Seed,position:a.position,paired:!!plain,PASS:true});
}
assert(pairs===3,'Exactly 3 new strict B/P pairs');
assert((await fs.readFile(file)).equals(bytes)&&(await fs.readFile(baseline)).equals(old),'No bytes changed');
const inspection=await workbook.inspect({kind:'region',sheetId:'B records',range:'O1:Y9',include:'values',tableMaxRows:9,tableMaxCols:11,maxChars:1400});
const reconcile=await read('CSV_reconciliation.json');
assert(reconcile.qualified_new_B_records===8&&reconcile.new_strict_P_pairs===3&&reconcile.new_physical_inputs===0,'Reconcile actual contribution');
if(!reconcile.authoritative_118_available)assert(reconcile.actual_master===null&&reconcile.actual_master_rows_appended===0,'Absent base not fabricated');
await fs.writeFile(path.join(out,'CSV_QA.json'),JSON.stringify({UTC:new Date().toISOString(),PASS:true,
  operation:'read-only Artifact Tool CSV import/schema/endpoint validation',rows:8,columns:28,UTF8_BOM:true,
  exact_binary64_qualified_endpoints:true,new_B_P_pairs:pairs,unpaired_rows:5,new_physical_inputs:0,
  T_cert_uses_process_only:true,OPEN_gap_unit:'percent',C_M_excluded:true,workbook_edits:0,workbook_exports:0,
  source_CSV_SHA256:hash(bytes),protected_103_row_reference_SHA256:hash(old),checks,inspection:inspection.ndjson,
  source_contract:'User explicitly prescribes flat CSV, historical byte preservation and Python/Node intermediates; no workbook redesign/XLSX variant',Optimize:0},null,2)+'\n');
console.log('Read-only Artifact Tool CSV QA PASS: 8 B records, 3 actual P pairs, 5 unpaired, 28 columns, exact process clocks/endpoints.');
