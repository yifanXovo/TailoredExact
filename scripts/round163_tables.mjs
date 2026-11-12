// Author the requested CSV additions through Artifact Tool; preserve legacy bytes.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook } from '@oai/artifact-tool';

const authoringStart=performance.now();
const root=path.resolve(process.argv[2]);
const out=path.join(root,'results/unified_exact_round163');
const temp=path.resolve(process.argv[3]);
const read=async name=>JSON.parse(await fs.readFile(path.join(out,name),'utf8'));
const schema=await read('main_table_schema_readback.json');
const inputs=(await read('input_manifest.json')).roles;
const arms=await read('reports/complete_arms.json');
const source=(await read('table_source_binding.json')).fixed_results_commit;
if(arms.length!==18||inputs.length!==6)throw Error('complete frozen panel required');
const all=await fs.readFile(schema.tables[0].path);
const originalText=new TextDecoder(schema.tables[0].encoding).decode(all);
const workbook=await Workbook.fromCSV(originalText,{sheetName:'All tested'});
const sheet=workbook.worksheets.getItem('All tested');
await fs.mkdir(temp,{recursive:true});
// CSV has no cell styles. This bounded read-only preview is for schema/value QA.
sheet.getRange('A1:J92').format.columnWidth=26;
sheet.getRange('A1:J92').format.font={name:'Arial',size:11};
const before=await workbook.render({sheetName:'All tested',range:'A1:J4',scale:1,format:'png'});
await fs.writeFile(path.join(temp,'master_before.png'),new Uint8Array(await before.arrayBuffer()));
const byId={};
for(const arm of arms){(byId[arm.id]??={})[arm.method]=arm;}
const scenario={shortage:['库存短缺','S'],balanced:['库存平衡','B'],surplus:['库存盈余','U']};
const textCSV=rows=>rows.map(row=>row.map(v=>{
  const text=v===null||v===undefined?'':String(v);
  return /[",\r\n]/.test(text)?'"'+text.replaceAll('"','""')+'"':text;
}).join(',')).join('\r\n')+'\r\n';
const endpoint=a=>[a.certificate?'已收敛':'未收敛',a.certificate?a.T_cert:null,
  a.certificate||a.relative_gap===null?null:100*a.relative_gap,a.L,a.U];
const additions=inputs.map(p=>{
  const b=byId[p.id].B,plain=byId[p.id].P;
  if(!b.performance_eligible||!plain.performance_eligible)throw Error('unqualified B/P pair');
  const [label,code]=scenario[p.inventory];
  const note=`冻结B/P；B ${b.state} U=${b.U} L=${b.L}；P ${plain.state} U=${plain.U} L=${plain.L}；旧分类阈值未确认，分类留空。`;
  const link=member=>`https://github.com/yifanXovo/TailoredExact/blob/${source}/${member}`;
  return [p.id,p.V,p.M,label,code,p.source,p.geometry==='compact'?'紧凑分布':'区域分布',p.T_seconds,p.lambda,null,
    0,1,163,p.cap_seconds,...endpoint(b),...endpoint(plain),'',note,
    link('results/unified_exact_round163/reports/complete_arms.json'),
    link('results/unified_exact_round163/input_manifest.json')];
});
for(const row of additions)if(row.length!==28)throw Error('28-column schema required');
const nextRow=schema.tables[0].rows+2;
const endRow=nextRow+5;
sheet.getRange(`A${nextRow}:AB${endRow}`).values=additions;
sheet.getRange(`I${nextRow}:J${endRow}`).setNumberFormat('0.00000000000000000');
for(let i=0;i<6;i++)sheet.getRange(`J${nextRow+i}`).formulas=[[`=I${nextRow+i}/0.15`]];
workbook.recalculate();
const saved=sheet.getRange(`A${nextRow}:AB${endRow}`).values;
for(let i=0;i<6;i++){
  if(Math.abs(saved[i][9]-inputs[i].lambda/.15)>1e-12)throw Error('lambda/.15 mismatch');
  for(const j of [17,18,22,23])if(saved[i][j]!==additions[i][j])throw Error('endpoint transport changed');
}
const inspected=await workbook.inspect({kind:'table',range:`All tested!A${nextRow}:X${endRow}`,include:'values,formulas',
  tableMaxRows:6,tableMaxCols:24,maxChars:3500});
await fs.writeFile(path.join(temp,'master_added_rows_inspection.ndjson'),inspected.ndjson);
const after=await workbook.render({sheetName:'All tested',range:`A${nextRow}:J${endRow}`,scale:1,format:'png'});
await fs.writeFile(path.join(temp,'master_after.png'),new Uint8Array(await after.arrayBuffer()));
const canonical=textCSV([schema.canonical_increment_header,...saved]);
await fs.writeFile(path.join(out,'reports/GI_TBC_vs_P_GRB_Round163_Increment.csv'),'\ufeff'+canonical,'utf8');
await fs.writeFile(path.join(temp,'master_append_utf8.csv'),textCSV(saved),'utf8');
await fs.writeFile(path.join(out,'table_authoring.json'),JSON.stringify({
  engine:'@oai/artifact-tool',outputs:'requested CSV, no unrequested XLSX',schema_columns:28,new_pairs:6,
  formula:'weight multiplier = actual lambda / 0.15',
  original_header_preserved_in_existing_files:true,duplicate_empty_source_headers_preserved:true,
  existing_records_reserialized:false,classification_left_blank:true,source_commit:source,
  expected_new_row_start:nextRow,previews:path.join(temp,'master_before.png')+'; '+path.join(temp,'master_after.png'),
  ordinary_document_IO_seconds:(performance.now()-authoringStart)/1000,
  snapshot_source:'qualified B and cold P only; E+ retained solely in the separate 18-arm comparison'
},null,2)+'\n','utf8');
console.log(JSON.stringify({authored_pairs:saved.length,columns:28,source_commit:source}));
