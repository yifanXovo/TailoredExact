// Artifact-authored 28-column increment; original scientific CSV bytes survive.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook } from '@oai/artifact-tool';

const tick=performance.now();
const root=path.resolve(process.argv[2]);
const out=path.join(root,'results/unified_exact_round164');
const temp=path.resolve(process.argv[3]);
const read=async name=>JSON.parse(await fs.readFile(path.join(out,name),'utf8'));
const discovery=await read('main_table_final_discovery.json');
const source=(await read('table_source_binding.json')).fixed_numeric_science_commit;
const inputs=(await read('input_references.json')).roles;
const arms=await read('reports/complete_arms.json');
if(arms.length!==24||inputs.length!==6)throw Error('complete new frozen panel required');
const original=await fs.readFile(discovery.primary.path);
const workbook=await Workbook.fromCSV(new TextDecoder(discovery.primary.encoding).decode(original),{sheetName:'All tested'});
const sheet=workbook.worksheets.getItem('All tested');
await fs.mkdir(temp,{recursive:true});
// These are inspection previews only: the requested deliverables remain CSV.
sheet.getRange(`A1:AB${discovery.primary.rows+13}`).format.font={name:'Arial',size:11};
sheet.getRange(`A1:AB${discovery.primary.rows+13}`).format.columnWidth=28;
sheet.getRange('A1:AB1').format.wrapText=true;
sheet.getRange('A1:AB1').format.rowHeight=44;
const before=await workbook.render({sheetName:'All tested',range:'A1:L4',scale:1,format:'png'});
await fs.writeFile(path.join(temp,'master_before.png'),new Uint8Array(await before.arrayBuffer()));
if(process.argv.includes('--preview-only')){
  console.log(JSON.stringify({preview:path.join(temp,'master_before.png'),edited:false}));
  process.exit(0);
}
const key=(id,seed,method)=>`${id}|${seed}|${method}|1`;
const by=new Map();
for(const a of arms){
  const k=key(a.id,a.gurobi_seed,a.method);
  if(by.has(k)||a.repeat!==1)throw Error('duplicate actual run identity');
  by.set(k,a);
}
const scenario={shortage:['库存短缺','S'],balanced:['库存平衡','B'],surplus:['库存盈余','U']};
const link=(commit,member)=>`https://github.com/yifanXovo/TailoredExact/blob/${commit}/${member}`;
const endpoint=a=>[a.certificate?'已收敛':'未收敛',a.certificate?a.T_cert:null,
  a.certificate||a.relative_gap===null?null:100*a.relative_gap,a.L,a.U];
const additions=[];
for(const p of inputs)for(const seed of [1,2]){
  const b=by.get(key(p.id,seed,'B')),plain=by.get(key(p.id,seed,'P'));
  if(!b?.performance_eligible||!plain?.performance_eligible)throw Error('unqualified or missing B/P pair');
  const [label,code]=scenario[p.inventory];
  const note=`冻结B/P Seed${seed}；B ${b.state}；P ${plain.state}；ΔU=${b.U-plain.U}；ΔL=${b.L-plain.L}；旧分类阈值未确认，分类留空。`;
  additions.push([p.id,p.V,p.M,label,code,p.source,p.geometry==='compact'?'紧凑分布':'区域分布',
    p.T_seconds,p.lambda,null,seed,1,164,p.cap_seconds,...endpoint(b),...endpoint(plain),'',note,
    link(source,'results/unified_exact_round164/reports/complete_arms.json'),
    link('f7083ace21ad2a8bd54bed71711ceebcb97c9e8c','results/unified_exact_round163/input_manifest.json')]);
}
if(additions.length!==12||additions.some(r=>r.length!==28))throw Error('exactly twelve 28-column pairs required');
const first=discovery.primary.rows+2,last=first+11;
sheet.getRange(`A${first}:AB${last}`).values=additions;
sheet.getRange(`I${first}:J${last}`).setNumberFormat('0.00000000000000000');
for(let i=0;i<12;i++)sheet.getRange(`J${first+i}`).formulas=[[`=I${first+i}/0.15`]];
workbook.recalculate();
const saved=sheet.getRange(`A${first}:AB${last}`).values;
for(let i=0;i<12;i++){
  if(Math.abs(saved[i][9]-additions[i][8]/.15)>1e-12)throw Error('actual lambda/.15 transport mismatch');
  for(const j of [8,10,11,12,13,17,18,22,23])if(saved[i][j]!==additions[i][j])throw Error(`raw endpoint/identity transport mismatch ${i},${j}`);
}
const inspection=await workbook.inspect({kind:'table',range:`All tested!I${first}:X${last}`,
  include:'values,formulas',tableMaxRows:12,tableMaxCols:16,maxChars:5000});
await fs.writeFile(path.join(temp,'added_rows_inspection.ndjson'),inspection.ndjson);
const errors=await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',
  options:{useRegex:true,maxResults:30},summary:'new row formula scan',maxChars:3000});
await fs.writeFile(path.join(temp,'formula_error_scan.ndjson'),errors.ndjson);
const after=await workbook.render({sheetName:'All tested',range:`A${first}:L${last}`,scale:1,format:'png'});
await fs.writeFile(path.join(temp,'master_after.png'),new Uint8Array(await after.arrayBuffer()));
const endpoints=await workbook.render({sheetName:'All tested',range:`O${first}:X${first+3}`,scale:1,format:'png'});
await fs.writeFile(path.join(temp,'endpoint_preview.png'),new Uint8Array(await endpoints.arrayBuffer()));
const textCSV=records=>records.map(row=>row.map(v=>{
  const value=v===null||v===undefined?'':String(v);
  return /[",\r\n]/.test(value)?'"'+value.replaceAll('"','""')+'"':value;
}).join(',')).join('\r\n')+'\r\n';
await fs.writeFile(path.join(out,'reports/GI_TBC_vs_P_GRB_Round164_Increment.csv'),
  '\ufeff'+textCSV([discovery.canonical_increment_header,...saved]),'utf8');
await fs.writeFile(path.join(temp,'master_append_utf8.csv'),textCSV(saved),'utf8');
await fs.writeFile(path.join(out,'table_authoring.json'),JSON.stringify({
  engine:'@oai/artifact-tool',requested_output_format:'CSV; no unrequested XLSX',new_pairs:12,
  columns:28,Seeds:[1,2],round_numeric:164,repeat_actual_run:1,
  formula:'actual lambda / 0.15; rho is not this multiplier',fixed_numeric_science_commit:source,
  original_source_header_and_prefix_not_reserialized:true,Seed0_appended_again:false,Eplus_relabelled:false,
  original_master_rows:discovery.primary.rows,working_master_rows:discovery.primary.rows+12,
  unavailable_94_row_master_claimed_updated:false,ordinary_authoring_IO_seconds:(performance.now()-tick)/1000,
  previews:['master_before.png','master_after.png','endpoint_preview.png'].map(n=>path.join(temp,n))
},null,2)+'\n','utf8');
console.log(JSON.stringify({authored_pairs:12,columns:28,numeric_source_commit:source}));
