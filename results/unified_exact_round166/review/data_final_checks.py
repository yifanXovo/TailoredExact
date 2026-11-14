"""Independent final read-only checks. Does not import any producer or solver."""
from pathlib import Path
from collections import Counter
from fractions import Fraction as F
import csv,gzip,hashlib,importlib.util,io,json,math,re,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round166';HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(HERE))
import round108_reader as parser
from data_c166_model_check import check_c166_model
from data_recover import physical
START=time.perf_counter();checks=Counter();bindings=[]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(Path(p).read_bytes())
def canonical(x):return sha_bytes(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
def require(condition,label):
    assert condition,label
    checks[label]+=1
def bind(p):
    p=Path(p);v=dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,SHA256=sha(p));bindings.append(v);return v
def verify_binding(b):
    p=ROOT/b['path'];require(sha(p)==b.get('SHA256',b.get('SHA')),'bound file SHA')
    if 'bytes' in b:require(p.stat().st_size==b['bytes'],'bound file bytes')
def csvrows(p,encoding='utf-8-sig'):
    with Path(p).open(encoding=encoding,newline='') as f:return list(csv.DictReader(f))

# Every new carrier and every indexed member, without extracting or repacking.
archives=read(OUT/'evidence_archives.json');event_hashes={};archive_summary=[]
with gzip.open(ROOT/archives['member_map']['path'],'rt',encoding='utf-8',newline='') as f:members=list(csv.DictReader(f))
require(len(members)==archives['members']==63594,'new carrier member total')
verify_binding(archives['member_map']);member_by_name={r['member']:r for r in members}
require(len(member_by_name)==len(members),'new member map unique paths')
excluded=[];owned_executables=[]
for ar in archives['archives']:
    verify_binding(ar);rr=[r for r in members if r['archive']==ar['path']]
    with zipfile.ZipFile(ROOT/ar['path']) as z:
        require(set(z.namelist())=={r['member'] for r in rr},'archive names equal member map')
        count=total=0
        for r in rr:
            data=z.read(r['member']);require(len(data)==int(r['bytes']) and sha_bytes(data)==r['SHA256'],'archive actual member hash/bytes')
            count+=1;total+=len(data);name=r['member'];base=name.rsplit('/',1)[-1].lower()
            if re.search(r'/journal/event_\d+\.json$',name):event_hashes[name]=canonical(json.loads(data))
            if name.lower().endswith('.exe'):owned_executables.append(dict(member=name,SHA256=sha_bytes(data),PE_magic=data[:2]==b'MZ'))
            if base.endswith(('.dll','.lic','.docx')) or re.search(r'(^|[._-])(credential|license|gurobi\.lic|secret|token)([._-]|$)',base):excluded.append(name)
        require(count==ar['members'] and total==ar['uncompressed_bytes'],'archive per-part totals')
        archive_summary.append(dict(path=ar['path'],members=count,uncompressed_bytes=total,SHA256=ar['SHA256']))
require(not excluded,'no commercial DLL/license/credential/private-docx members')
require(len(owned_executables)==3 and all(p['PE_magic'] for p in owned_executables),'three own PE files only')
require(sum(a['uncompressed_bytes'] for a in archive_summary)==315804565,'archive uncompressed total')
require(sum(a['bytes'] for a in archives['archives'])==54628621,'archive compressed total')

matrix=read(OUT/'matrix_frozen.json');candidate=read(OUT/'candidate_manifest.json');arms=read(OUT/'reports/complete_arms.json');pairs=read(OUT/'reports/pairs.json');summary=read(OUT/'reports/summary.json');runtime=read(OUT/'reports/runtime_metrics.json');cost=read(OUT/'cost_report.json')
for p in [OUT/'matrix_frozen.json',OUT/'candidate_manifest.json',OUT/'reports/summary.json',OUT/'reports/complete_arms.json',OUT/'reports/pairs.json',OUT/'reports/runtime_metrics.json',OUT/'cost_report.json']:bind(p)
require(len(matrix['groups'])==len(arms)==12 and len(pairs)==6,'one complete fixed 12-arm matrix')
require(matrix['source_commit']=='0298dd45fbc3645af927c4a4dd1d43ecbdb567a9','formal measured source commit')
require(sha(candidate['production_PE'])==matrix['PE_SHA']==candidate['production_PE_SHA'],'common actual production PE')
require(sha(candidate['DLL'])==matrix['DLL_SHA']==candidate['DLL_SHA'],'common actual Gurobi DLL')
require(any(p['SHA256']==matrix['PE_SHA'] for p in owned_executables),'measured own PE in carrier')
for name,digest in candidate['source_hashes'].items():require(sha(ROOT/name)==digest,'frozen source SHA')
for name,digest in matrix['helper_hashes'].items():require(sha(ROOT/name)==digest,'frozen helper SHA')
changed=subprocess.check_output(['git','diff','--name-only',matrix['source_commit'],'--','src','include','CMakeLists.txt'],cwd=ROOT).decode().strip()
require(not changed,'measured source clean against actual commit')
require(sum(g['launch']['cap_seconds'] for g in matrix['groups'])==21600,'original complete cap sum')
require(matrix['reservation']==25200 and matrix['NodeLimit']=='unlimited','reservation separate/unlimited nodes')
formal_calls=0;models={};start_vectors=0;journal_events=0;physical_rows=[];fee_total=0.;prior_end=-math.inf;clock_rows=[];max_start_residual=0.
for g,a,metric in zip(matrix['groups'],arms,runtime):
    l=g['launch'];p=l['panel'];d=Path(l['destination']);ident=read(OUT/g['group']/'identity.json');audit=read(d/'audit.json');result=read(d/'result.json');fee=read(OUT/'fees'/f'{g["position"]:03}.json');receipt=read(d/'producer_receipt.json');endpoint=read(d/'round166_endpoint.json')
    require(a['position']==g['position'] and a['id']==g['input_id'] and a['method']==g['method'],'actual method/input/position alignment')
    require(a['seed']==0 and a['source_build']==matrix['source_commit'] and a['PE_SHA']==matrix['PE_SHA'] and a['DLL_SHA']==matrix['DLL_SHA'],'per-arm measured identities')
    require(sha(ROOT/p['input_path'])==p['input_sha256']==a['input_SHA'],'per-arm actual input SHA')
    require(all(a[k] for k in ['formal_protocol_qualified','performance_eligible','performance_evidence_eligible','numbers_qualified','implementation_qualified','evidence_complete','native_proof_qualified','H_complete']),'all independent qualification fields pass')
    require(audit['passed'] and audit['raw_bytes_unchanged'] and not audit['source_rejections'],'raw qualified endpoint without rejection')
    require((a['T_cert'] is not None)==a['certificate'],'OPEN certificate time is null')
    require(abs(a['T_produce']+a['T_verify']-a['T_total'])<1e-9 and a['T_produce']==receipt['T_produce']<=p['cap_seconds'],'produce/verify clocks separated')
    require(fee['status']=='COMPLETE' and fee['arm_wrapper_is_fresh_process'] and fee['producer_cap']==p['cap_seconds'],'fresh paid wrapper per formal arm')
    # Independent FILETIME-to-binary64 Unix conversions differ by up to two
    # microseconds at this epoch; this is a clock-serialization comparison,
    # not a relaxation of the optimization qualification tolerance.
    require(abs(receipt['t0_unix']-fee['birth']['creation_unix'])<5e-6,'producer starts at own OS wrapper birth')
    require(fee['start_unix']+0.1>=prior_end,'formal arms serial without overlap');prior_end=fee['start_unix']+fee['seconds'];fee_total+=fee['seconds']
    require(fee['reservation']==p['cap_seconds']+300 and fee['watchdog']==p['cap_seconds']+900,'reservation and fault watchdog do not change cap')
    args=l['command'];tokens={args[i]:args[i+1] for i in range(1,len(args)-1,2)}
    require(tokens['--round166-breakpoint']==('on' if a['method']=='C166' else 'off'),'actual representation flag')
    require(tokens['--round127-mode']=='ms2' and tokens['--round98-state-service']=='m-binary','frozen complete B algorithm interface')
    require(tokens['--threads']==tokens['--mip-threads']=='1' and tokens['--gurobi-seed']=='0' and tokens.get('--primal-heuristic-seed','20260626')=='20260626' and matrix['H_seed']==20260626,'single native thread/fixed Seeds')
    require('opt.primal_heuristic_seed = 20260626u;' in (ROOT/'src/PaperK1AmSf.cpp').read_text(encoding='utf-8'),'frozen inherited H preset seed')
    if a['method']=='C166':require(read(d/'round166_parameters.json')['H_seed']==20260626,'C166 actual H seed readback')
    forbidden=['--external-incumbent','--hga-incumbent','--incumbent-json','--frontier-import-interval-bound','--frontier-resume-state']
    require(not any(t in tokens for t in forbidden) and not any('qualification/parents' in t or 'data_physical_archive' in t for t in args),'no free archived plan/bound import')
    require(tokens.get('--incumbent-archive-auto','false')=='false','automatic incumbent archive off')
    expected_algorithm='research-C166-breakpoint-bit' if a['method']=='C166' else 'research-round99-ensc-discrete-structure-m-binary'
    require(result['algorithm_preset']==expected_algorithm,'actual produced algorithm identity')
    physical_data=parser.evidence.instance(ROOT,p);physical_data.update(n=p['V'],m=p['M']);v=physical(physical_data,p,audit['physical']['routes'])
    require(v['Y']==audit['physical']['Y'] and abs(v['F']-a['U'])<1e-12,'independent complete formal fleet physics/objective')
    physical_rows.append(dict(position=a['position'],id=a['id'],method=a['method'],G=v['G'],P=v['P'],F=v['F'],returns=v['returns']))
    observations=read(d/'observations.json');calls=[o['payload'] for o in observations if o['payload']['kind']=='call'];ledger=csvrows(d/'external/paper_optimize_ledger.csv')
    require(len(calls)==len(ledger)==a['native_Optimize']==a['declared_calls']==a['returned_calls'],'all actual native calls counted')
    formal_calls+=len(calls)
    for o in observations:
        path=(d/'journal'/f'event_{o["sequence"]}.json').relative_to(ROOT).as_posix()
        require(path in member_by_name and member_by_name[path]['SHA256']==o['sha256'] and event_hashes[path]==canonical(o['payload']),'actual journal bytes/payload pinned in carrier');journal_events+=1
    require(abs(calls[0]['cutoff']-audit['full_H']['physical']['F'])<1e-12,'initial cutoff is own completed H')
    for call,row in zip(calls,ledger):
        settings=call['settings'];expected={'Threads':1,'Seed':0,'Presolve':-1,'MIPFocus':0,'Cuts':-1,'MIPGap':0,'MIPGapAbs':0,'FeasibilityTol':1e-6,'IntFeasTol':1e-5,'OptimalityTol':1e-6}
        require(all(settings[k]==v for k,v in expected.items()) and settings['read_return_code']==0 and call['native_preconditions']==1,'actual native parameter readback')
        require(row['optimize_return_code']=='0' and row['model_sha256']==call['model_sha256'] and row['leaf_id']==call['leaf'],'native ledger/journal/canonical identity join')
        if row['solve_kind']=='LP':require(row['integer_domain_restored']=='1','actual LP to MIP original types restored')
        model_path=Path(call['model_path']);digest=sha(model_path);require(digest==call['model_sha256'],'immutable epoch canonical bytes')
        if digest not in models:
            model=parser.lp_model(model_path);models[digest]=model
            if a['method']=='C166':check_c166_model(model,p,physical_data)
            else:parser.model_contract(ROOT,p,model_path,'M-B')
        model=models[digest]
        require(model['bounds']['G']==(call['lower_g'],call['upper_g']),'native G scope equals actual canonical bounds')
        require((model['objective'][0],'<=',call['cutoff']-model['objective'][1]) in model['rows'],'inclusive native cutoff is actual row')
    for sc in audit['Start_checks']:
        st=ROOT/sc['start_path'];require(sha(st)==sc['start_sha256'],'Start JSON pinned')
        start=read(st);values_path=Path(str(st).replace('.json','.values.csv'));require(sha(values_path)==sc['vector_sha256'],'Start complete vector pinned')
        rr=csvrows(values_path);model=models[sc['model_sha256']];values={r['variable']:float(r['value']) for r in rr}
        require(set(values)==set(model['order']) and len(rr)==len(model['order']),'Start every actual semantic column')
        require(all(r['type']==model['types'][r['variable']] and float(r['readback'])==float(r['value']) for r in rr),'Start ordered/native type and readback')
        residual=0.
        for terms,sense,rhs in model['rows']:
            activity=math.fsum(values[n]*c for n,c in terms);residual=max(residual,abs(activity-rhs) if sense=='=' else activity-rhs if sense=='<=' else rhs-activity)
        require(residual<=1e-7 and start['rows_valid'] and start['submitted'] and start['readback_valid'] and start['objective_valid'],'Start all actual rows and submitted identity')
        require(abs(math.fsum(c*values[n] for n,c in model['objective'][0])+model['objective'][1]-start['objective'])<=1e-7,'Start original objective')
        max_start_residual=max(max_start_residual,residual);start_vectors+=1
    require(sum(float(r['solver_runtime']) for r in ledger)<=a['T_produce']+1,'native Runtime is nested in paid producer')
    clock_rows.append(dict(position=a['position'],T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total'],wrapper_seconds=fee['seconds']))

require(formal_calls==summary['total_native_Optimize']==62,'formal actual Optimize total 62')
require(read(OUT/'qualification.json')['actual_Optimize']==96 and cost['total_new_native_Optimize']==158,'diagnostic 96/formal 62 remain separate')
require(read(OUT/'qualification.json')['diagnostic_window_seconds']<=3600,'diagnostic outer cap')
require(abs(fee_total-summary['actual_wrapper_outer_seconds'])<1e-8 and abs(sum(a['T_total'] for a in arms)-summary['actual_produce_plus_verify'])<1e-8,'outer fees summed once')
require(Counter(a['method'] for a in arms if a['certificate'])==Counter(B=3,C166=2),'actual certificate counts B3 C1662')
for pair in pairs:
    b=next(a for a in arms if a['id']==pair['id'] and a['method']=='B');c=next(a for a in arms if a['id']==pair['id'] and a['method']=='C166');joint=b['certificate'] and c['certificate']
    require(b['H_semantic_SHA']==c['H_semantic_SHA'] and b['H_fleet_SHA']==c['H_fleet_SHA'],'matched independently paid H within pair')
    require(pair['joint_CERT']==joint and pair['delta_U_C166_minus_B']==c['U']-b['U'] and pair['delta_L_C166_minus_B']==c['L']-b['L'],'pair endpoint deltas')
    if joint:
        threshold=max(10,.1*min(b['T_cert'],c['T_cert']));difference=c['T_cert']-b['T_cert']
        require(pair['C166_over_B_T_cert']==c['T_cert']/b['T_cert'] and pair['substantive_threshold_seconds']==threshold and pair['substantive_difference']==(abs(difference)>=threshold),'fixed joint-CERT ratio and substantive scale')
    else:require(pair['C166_over_B_T_cert'] is None,'no OPEN certificate-time ratio')
require(sum(p['joint_CERT'] for p in pairs)==2,'joint-CERT denominator 2')

# Current offline physical archive is the same independently recovered one.
archive=read(OUT/'review/data_physical_archive.json');compaction=read(OUT/'review/data_archive_compaction.json')
require(sha(OUT/'review/data_physical_archive.json')==compaction['compact_archive']['SHA256'],'all historical fleet/qualification values unchanged after compaction')
for r in archive['records']:
    profile=next(p for p in archive['inputs'] if p['family']==r['family']);a=profile['physical'];p=dict(V=a['n'],M=a['m'],Q_vector=a['Q'],T_seconds=a['T'],pickup_seconds=a['pickup_seconds'],drop_seconds=a['drop_seconds'],**{'lambda':r['verified']['lambda_value']})
    v=physical(a,p,r['verified']['routes']);require(v==r['verified'],'all 50 complete archive fleets independently recomputed')
    q=r['qualification']['qualified_cover'];require(q['historical_source_reference_not_new_qualification'] and r['lower_qualified'] and r['qualification']['lower_is_global_original_physical_problem'],'global L qualification retained as historical source')
parameter=read(OUT/'analysis/parameter_envelopes.json');independent=read(OUT/'review/data_envelope_check.json')
for ours,theirs in zip(parameter['families'],independent):
    require(ours['family']==theirs['family'] and F(ours['worst_gap']['gap']['exact'])==F(theirs['worst_envelope_gap']['gap']['rational'])+F(1,10**12),'independent exact continuous parameter maximum')
resource=read(OUT/'analysis/resource_intervals.json')
body=(ROOT/'results/unified_exact_round137/paper_body.md').read_text(encoding='utf-8')
safe_displays=[('0.2822618761','0.2822620892'),('0.2105292995','0.2105295021'),('0.1112611656','0.3725317852'),('0.0600858983','0.3813035291')]
for r,(lo,hi) in zip(resource,safe_displays):
    require(F(lo)<=F(r['lower_exact'])<=F(r['upper_exact'])<=F(hi),'paper resource endpoints round outward')
    require(f'[{lo}, {hi}]' in body,'current body matches safe resource interval')
for r,text in zip(parameter['families'],['0.002356282','0.000000100002','0.015594269','0.136115162']):require(F(text)>=F(r['worst_gap']['gap']['exact']) and text in body,'paper regret bound rounds outward')
require(F('1.00002e-7')>=F(parameter['families'][1]['worst_gap']['gap']['exact']) and '1.00002e-7' in body,'abstract fixed fleet guarantee rounds outward')
require([r['operations_T1']['returns'] for r in resource]==[0,1,2,1] and [r['operations_T2']['returns'] for r in resource]==[0,0,3,0],'all four loaded-return changes retained')

# Preserve the original 28-column CSV schema and all old table bytes.
rec=read(OUT/'CSV_reconciliation.json');old=ROOT/rec['local_working_copy']['path'];require(sha(old)==rec['local_working_copy']['SHA256'],'103-row old CSV bytes unchanged')
desktop=next(r for r in rec['bounded_entry_search'] if r['path'].startswith('C:'));require(sha(desktop['path'])==desktop['SHA256'],'91-row user CSV bytes unchanged')
inc=ROOT/rec['independent_increment']['path'];raw=inc.read_bytes();require(raw.startswith(b'\xef\xbb\xbf'),'increment UTF-8 BOM')
oldrows=list(csv.reader(io.StringIO(old.read_text(encoding='gb18030'))));newrows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))));require(newrows[0]==oldrows[0] and len(newrows)==7 and all(len(r)==28 for r in newrows),'six-row increment exact 28-column schema')
mapping=read(OUT/'reports/CSV_increment_mapping.json')
for row,mp in zip(newrows[1:],mapping):
    a=next(a for a in arms if a['position']==mp['position']);require(a['method']=='B' and mp['method']=='B' and not mp['new_strict_B_P_pair'],'increment contains only unpaired new B controls')
    require(row[20:24]==['','','',''] and row[19]=='无配对结果' and row[24]=='N/A','increment does not borrow old P results')
    require(float(row[17])==a['L'] and float(row[18])==a['U'],'increment binary64 endpoints match')
    require((row[15]=='')==(not a['certificate']),'CSV OPEN certificate time blank')
    if a['certificate']:require(float(row[15])==a['T_cert'],'CSV actual qualified certificate time')

# Maintained source -> assembled manuscript -> current PDF identity (data scope).
build=read(OUT/'document_build.json');qa=read(OUT/'document_qa.json')
for d in build['outputs']:
    verify_binding(d);verify_binding(d['source']);verify_binding(d['intermediate_TeX'])
    q=next(q for q in qa['documents'] if q['path']==d['path']);require(q['SHA256']==d['SHA256'],'PDF QA exact current bytes')
    require(q['page_count']==(60 if 'manuscript' in d['path'] else 44),'current PDF page count')
    require(all(not p['outside_page'] and p['replacements']==0 and p['characters']>0 for p in q['pages']),'PDF mechanical no clipping/replacement/blank page')
paper=ROOT/'results/unified_exact_round137';app=(paper/'model_and_algorithm_appendices.md').read_text(encoding='utf-8');assembled=(paper/'manuscript.md').read_text(encoding='utf-8')
require(assembled==body.rstrip()+'\n\n\\clearpage\n\n'+app.rstrip()+'\n','maintained body/appendices exactly assembled')
require('B certifies 3/6 and C166 certifies 2/6' in body and '4.3488' in body and '0.06676618239' in body,'body contains final complete/decision results')

actual_inputs=[dict(id=g['input_id'],input_path=g['launch']['panel']['input_path'],SHA256=g['launch']['panel']['input_sha256']) for g in matrix['groups'][::2]]
result=dict(PASS=True,reviewer='independent data_review agent',UTC=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),new_Optimize=0,new_producer=0,checked_assertions=dict(checks),actual_checks=sum(checks.values()),formal_calls=formal_calls,diagnostic_calls=96,total_new_calls=158,formal_journal_events_verified=journal_events,unique_actual_models_checked=len(models),Start_vectors_recomputed=start_vectors,max_Start_row_residual=max_start_residual,archive_summary=archive_summary,owned_executables=owned_executables,excluded_members=excluded,formal_physical_endpoints=physical_rows,formal_clocks=clock_rows,actual_wrapper_seconds=fee_total,PDF_QA_state_at_read=qa['status'],visual_QA_scope='mechanical/data identity reviewed here; independent visual review remains owned by manuscript reviewer/primary agent',actual_input_SHA256=actual_inputs,input_bindings=bindings,seconds=time.perf_counter()-START,findings=[])
(HERE/'data_final.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['checked_assertions','input_bindings','formal_clocks','formal_physical_endpoints','archive_summary']},indent=2,ensure_ascii=False))
