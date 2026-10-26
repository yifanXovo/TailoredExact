"""Independent R109 actual-input/physics/model/Start/cover/decision audit.

The raw kernel inherits the independently audited R108 arithmetic. Production
summary, final report and primary decision are never inputs to the computation.
Reads are restricted to --root, except the explicitly supplied DLL in local
mode. Public mode requires an actual fresh restore receipt and absent PE.
"""
from pathlib import Path
from collections import Counter
import argparse, ast, csv, hashlib, json, math, re, runpy, sys, time, traceback

ap=argparse.ArgumentParser()
ap.add_argument('--root',required=True)
ap.add_argument('--mode',choices=('admission','resumption','final','public'),required=True)
ap.add_argument('--out',required=True,help='Exclusive output directory below this root review/')
ap.add_argument('--dll')
args=ap.parse_args()
ROOT=Path(args.root).resolve();OUT=ROOT/'results/unified_exact_round109';REVIEW=OUT/'review'
DEST=Path(args.out).resolve();assert DEST.is_relative_to(REVIEW)
PE=ROOT/'build/research/round109-inherited-mb-v1/ExactEBRP.exe'
DLL=Path(args.dll).resolve() if args.dll else None
assert args.mode!='public' or DLL is None
reads={};count=0;milestones=[];cache={}
TOL=1e-7;ZERO=1e-12
SETTINGS=dict(Threads=1,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
EXPECTED_PE='4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0'
EXPECTED_DLL='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'

def require(condition,message):
    global count
    count+=1
    if not condition:raise AssertionError(message)
def data(path):
    path=Path(path).resolve()
    require(path.is_relative_to(ROOT) or args.mode!='public' and DLL is not None and path==DLL,'read remains in explicit root or declared current DLL')
    raw=path.read_bytes();reads[str(path)]=hashlib.sha256(raw).hexdigest();return raw
def sha(path):return hashlib.sha256(data(path)).hexdigest()
def txt(path):return data(path).decode('utf-8-sig')
def obj(path):return json.loads(txt(path))
def rows(path):return list(csv.DictReader(txt(path).splitlines()))
def save(path,value):
    path=Path(path);require(path.resolve().is_relative_to(DEST),'write only to exclusive audit destination')
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def under_root(value):
    normalized=str(value).replace('\\','/')
    for marker in ('results/','reference/','build/','scripts/','src/','include/','tests/'):
        if marker in normalized:return ROOT/normalized[normalized.index(marker):]
    path=Path(normalized);require(not path.is_absolute(),'unsupported retained absolute evidence path');return ROOT/path
def near(a,b,tol=1e-7):return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol
def model(path):
    digest=sha(path)
    if digest not in cache:cache[digest]=lp(path)
    return cache[digest]
def production_pe_sha():return EXPECTED_PE
def native_dll_sha():return EXPECTED_DLL
qualified_scope_calls={}
def set_qualified_scope(proof):
    global qualified_scope_calls
    qualified_scope_calls={p['call']:p for p in proof['proofs']} if proof else {}
def native_scope_qualified(call):
    proof=qualified_scope_calls.get(call['call'])
    if proof is None:return call['native_preconditions']==1
    require(call['native_preconditions']==0 and proof['model_SHA']==call['model_sha256'],'computed scope preserves original false flag and exact model bytes')
    return proof['computed_native_scope_qualified'] and proof['facts']['actual_settings']==call['settings']
def independent_seed_scope(launch):
    s=runpy.run_path(str(REVIEW/'round109_independent_seed_scope.py'))
    s['audit'].__globals__.update(obj=obj,txt=txt,sha=sha,rows=rows,require=require,parse_model=model)
    return s['audit'](ROOT,launch)
def reference_path(panel):return OUT/'qualification/reference'/panel['id']/'original.lp'
def argv_map(command):
    result={};i=1
    flags={'--plain-baseline','--round100-continuous-quantities'}
    while i<len(command):
        key=command[i];require(key.startswith('--') and key not in result,'unique actual CLI option')
        if key in flags:result[key]=True;i+=1
        else:require(i+1<len(command),'CLI option has argument');result[key]=command[i+1];i+=2
    return result

parser=runpy.run_path(str(REVIEW/'round109_independent_parser.py'))
for name in ('input_file','physical','terms','lp'):
    parser[name].__globals__.update(data=data,txt=txt,require=require,near=near)
input_file=parser['input_file'];physical=parser['physical'];lp=parser['lp']
decision=runpy.run_path(str(REVIEW/'round109_independent_decision.py'))
exec(compile(txt(REVIEW/'round109_independent_kernel.py'),str(REVIEW/'round109_independent_kernel.py'),'exec'),globals())
exec(compile(txt(REVIEW/'round109_independent_numerical.py'),str(REVIEW/'round109_independent_numerical.py'),'exec'),globals())
exec(compile(txt(REVIEW/'round109_independent_main06.py'),str(REVIEW/'round109_independent_main06.py'),'exec'),globals())

def independent_checkpoints(arm,launch,timeline):
    points=[]
    for second in (300,600,900,1800,3600):
        if second>launch['cap_seconds']:continue
        events=[r for r in timeline if r['safe_complete_arm_available']<=second]
        upper=arm['complete_seconds'] if arm['complete_seconds'] is not None else arm['complete_seconds_interval'][1]
        lower=arm['complete_seconds'] if arm['complete_seconds'] is not None else arm['complete_seconds_interval'][0]
        if second>lower or not events:
            points.append(dict(seconds=second,observed=False,U=None,L=None,gap=None,reason='process ended or no qualified committed own evidence; no extrapolation'))
        else:
            event=events[-1];points.append(dict(seconds=second,observed=True,U=event['own_U'],L=event['committed_global_L'],gap=event['signed_gap'],sequence=event['sequence'],native_first_find_exact=False))
    return points

def frozen_protocol():
    protocol=obj(OUT/'protocol.json');manifest=obj(OUT/'input_manifest.json');roles=manifest['roles']
    expected=decision['PANEL'];require(len(roles)==len(protocol['roles'])==12,'twelve exact main inputs')
    physical=[]
    for role,prereg,row in zip(roles,protocol['roles'],expected):
        identifier,n,m,geometry,replicate,inventory,qclass,T,cap,methods=row
        q=[30]*m if qclass=='H' else [20,40] if m==2 else [20,25,35,40]*(m//4)
        wanted=dict(id=identifier,V=n,M=m,geometry=geometry,replicate=replicate,inventory=inventory,Q_class=qclass,Q_vector=q,T_seconds=T,cap_seconds=cap,
            method_order=list(methods),pickup_seconds=60,drop_seconds=60,**{'lambda':.15},gurobi_seed=0,panel_kind='main')
        require(all(prereg[k]==role[k]==v for k,v in wanted.items()),'independent complete role table '+identifier)
        parsed=input_file(ROOT/role['input_path'])
        require(sha(ROOT/role['input_path'])==role['input_sha256'] and (parsed['V'],parsed['M'],parsed['Q'])==(n,m,q),'exact input bytes and real header '+identifier)
        require(all(0<=parsed['initial'][i]<=parsed['capacities'][i] and parsed['target'][i]>0 for i in range(1,n+1)) and T>0,'original stock/target/time domain '+identifier)
        empty=[dict(vehicle=k,nodes=[0,0],operations=[]) for k in range(m)]
        ph=full_physics(parsed,empty,role)
        require(sum(ph['final_inventories'][1:])==sum(parsed['initial'][1:]),'empty fleet independently feasible without min_ratio '+identifier)
        physical.append(dict(id=identifier,V=n,M=m,input_SHA=role['input_sha256'],input_bytes=len(data(ROOT/role['input_path'])),empty_fleet_physical=ph,sum_omega=sum(parsed['weights'][1:])))
    require([(x['id'],x['gurobi_seed'],tuple(x['method_order'])) for x in protocol['seed_checks']]==[(r,1,ms) for r,_,ms in decision['SEED_CHECKS']],'three predetermined Seed1 groups')
    require(protocol['formal_arms']==42 and protocol['nominal_seconds']==88200 and protocol['main_nominal_seconds']==75600 and protocol['seed_nominal_seconds']==12600,'separate exact nominal denominations')
    require(protocol['maximum_starts']==72 and protocol['maximum_outer_seconds']==100000 and protocol['planned_formal_starts']==57,'fixed complete resource ceiling')
    require(protocol['no_early_performance_cancellation'] and protocol['full_42_required_for_normal_results'],'ordinary negative performance never cancels')
    require(protocol['closure_tolerance']==TOL and protocol['zero_objective_tolerance']==ZERO and protocol['signed_gap_not_clipped'],'inherited numerical closure and signed-gap contract')
    require(protocol['support_requires']==dict(all_42_valid_same_PE=True,all_12_eligible_at_initial_freeze=True,main_all_evaluable=True,main_MIN_WIN=6,main_MAX_LOSS=2,
        main_severe_regressions=0,WIN_in_each_V=[20,50,100],WIN_in_each_geometry=['compact','regional'],seed_all_evaluable=True,seed_severe_regressions=0,seed_min_not_LOSS=2,no_Seed0_WIN_to_Seed1_LOSS=True),'exact independent stage gate')
    source=ROOT/'results/data_generation_citibike_round57/source_station_table.csv'
    require(len(data(source))==69678 and sha(source)=='9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0','exact public source bytes rather than CRLF checkout')
    return protocol,manifest,physical

def current_bindings():
    candidate=obj(OUT/'candidate_identity.json');contract=obj(OUT/'candidate_contract_freeze.json');identity=obj(OUT/'campaign/identity.json')
    require(candidate['production_PE_SHA']==contract['production_PE_SHA']==identity['candidate_binary_sha256']==EXPECTED_PE,'actual frozen uniform PE identity')
    require(candidate['DLL_SHA']==contract['DLL_SHA']==identity['dll_sha256']==EXPECTED_DLL,'actual uniform native DLL identity')
    if args.mode=='public':
        require(not PE.exists(),'fresh evidence restoration does not distribute PE')
        restore=obj(ROOT/'restore_receipt.json')
        require(restore['exit_code']==0 and restore['public_files_only'] and not restore['original_workspace_reads'] and Path(restore['restored_root']).resolve()==ROOT,'actual fresh restoration root and access receipt')
    else:
        require(sha(PE)==EXPECTED_PE and DLL is not None and sha(DLL)==EXPECTED_DLL,'independent actual local PE and installed DLL byte rehash')
    require(candidate['source_bindings']==contract['source_bindings']==identity['source_hashes'],'same source on all bound paths')
    for path,digest in contract['source_bindings'].items():require(sha(ROOT/path)==digest,'unchanged production source '+path)
    for path,digest in identity['helpers'].items():require(sha(ROOT/path)==digest,'frozen actual performance helper '+path)
    require(identity['prereg_sha256']==sha(OUT/'protocol.json'),'exact 42-arm protocol binding')
    repair=obj(OUT/'engineering/qualification_wrapper_repair01/repair.json')
    before=OUT/'fees/qualification_cli01/source_snapshot/scripts/round109_campaign.py';after=OUT/'fees/qualification_cli02/source_snapshot/scripts/round109_campaign.py'
    require(sha(before)==repair['old_source_SHA'] and sha(after)==repair['new_source_SHA'],'actual failed/fixed wrapper source snapshots')
    fixed=txt(before).replace('for name,digest in helpers().items():','for helper_name,digest in helpers().items():').replace(
        'target=snapshots/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())',
        'target=snapshots/helper_name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/helper_name).read_bytes())')
    require(fixed.splitlines()==txt(after).splitlines(),'exact wrapper repair only renames loop-local snapshot variable')
    current=txt(after).replace("'round109_seed_audit.py',", "'round109_seed_audit.py','round109_seed_scope.py','round109_seed_recovery.py',\n        'round108_reader.py','round108_scopes.py','round108_decisions.py','round107_reader.py','round99_pure_start_audit.py',",1)
    require(current.splitlines()==txt(ROOT/'scripts/round109_campaign.py').splitlines(),'later frozen wrapper source only adds strict Seed scope/readers to bound helper inventory')
    oldidentity=obj(OUT/'engineering/qualification_wrapper_repair01/campaign_identity_before.json')
    require(oldidentity['launches']==identity['launches'] and oldidentity['source_hashes']==identity['source_hashes'] and oldidentity['prereg_sha256']==identity['prereg_sha256'],'wrapper compatibility repair preserves all42 real commands and algorithm identities')
    recovery=obj(REVIEW/'seed_recovery_budget_review.json')
    require(recovery['decision']=='ACCEPT' and recovery['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and recovery['coupon_original_receipt_SHA']==sha(OUT/'fees/qualification_cli02/receipt.json'),'independent one-slot recovery review binds current candidate and unchanged original prepaid fee')
    for label in ('seed_reader_repair01','seed_reader_repair02'):
        old=obj(OUT/'engineering'/label/'campaign_identity_before.json')
        require(old['launches']==identity['launches'] and old['source_hashes']==identity['source_hashes'] and old['prereg_sha256']==identity['prereg_sha256'],'strict metadata-only reader refreeze preserves all42 argv '+label)
    return candidate,identity

def bind_launches(identity,manifest):
    launches=identity['launches'];roles={r['id']:r for r in manifest['roles']}
    expected=[(r[0],0,m) for r in decision['PANEL'] for m in r[9]]+[(r,1,m) for r,_,ms in decision['SEED_CHECKS'] for m in ms]
    require([(l['id'],l['panel']['gurobi_seed'],l['arm']) for l in launches]==expected and len(launches)==42,'all42argv in exact serial predetermined order')
    require(sum(l['cap_seconds'] for l in launches)==88200,'all42 nominal cap sum')
    for launch in launches:
        panel=launch['panel'];role=roles[launch['id']];command=launch['command'];am=argv_map(command);cap=launch['cap_seconds'];seed=panel['gurobi_seed']
        require(under_root(command[0])==PE,'every real entrance uses frozen PE')
        wanted={'--input':role['input_path'],'--lambda':'0.15','--T':str(role['T_seconds']),'--pickup-time':'60','--drop-time':'60','--time-limit':str(cap-6),
            '--process-wall-time-limit':str(cap),'--process-shutdown-margin':'30','--threads':'1','--mip-threads':'1','--gurobi-seed':str(seed),'--gurobi-presolve':'-1'}
        require(all(am[k]==v for k,v in wanted.items()),'exact per-arm numerical/input/Seed argv')
        require(all(panel[k]==role[k] for k in ('input_path','input_sha256','V','M','Q_vector','T_seconds','cap_seconds','lambda','pickup_seconds','drop_seconds')),'Seed repeat changes neither bytes nor physical/scenario parameter')
        require('--round100-continuous-quantities' not in am,'separate ENS-Q option remains false')
        if launch['arm']=='P-GRB':require(am['--method']=='gurobi' and am['--plain-baseline'] is True and '--algorithm-preset' not in am and '--round98-state-service' not in am,'original cold P CLI')
        else:
            require(am['--method']=='gcap-frontier' and am['--algorithm-preset']=='research-round83-vds-equal-net-exchange' and am.get('--round98-state-service')==('m-binary' if launch['arm']=='M-B' else None),'only original M-B state-service append')
            require(am['--round90-lp-g-split']=='false' and am['--round61-candidate-mode']=='off' and not any(re.match(r'--round(?:9[567]|10[1-7])-',k) for k in am),'additional mechanisms absent')
        if args.mode=='admission':require(not under_root(launch['destination']).exists(),'formal arm remains unstarted before admission')
    return launches

def audit_references(manifest):
    checked=[];batch=obj(OUT/'qualification/batch_export_receipt.json');plan=obj(OUT/'qualification/plan.json')
    require(batch['passed'] and batch['actual_native_processes']==1 and batch['Optimize']==batch['presolve']==0 and not batch['solution_or_Start_generated'],'one actual native zero-solve batch child')
    require(batch['plan_SHA']==sha(OUT/'qualification/plan.json') and batch['reference_writer_source_SHA']==sha(ROOT/'src/round65_reference_build.cpp'),'actual batch binds original cold production writer')
    require(batch['stdout_SHA']==sha(OUT/'fees/qualification_prepare01/stdout.log') and 'batch_complete\t13\tOptimize=0' in txt(OUT/'fees/qualification_prepare01/stdout.log'),'actual batch stdout completes all twelve plus known qualification fixture')
    require(plan['reference_child_count']==1 and plan['CLI_children']==5 and plan['conservative_starts']==8,'original eight qualification start plan preserved')
    for panel in manifest['roles']:
        path=reference_path(panel);build=obj(path.parent/'build.json')
        require(build['optimizer_calls']==0 and sha(path)==build['canonical_sha256'],'each exact original cold reference built without Optimize')
        # Complete LP parsing binds every numeric row/column/type/bound/objective.
        native=model(path)
        require((len(native['rows']),len(native['bounds']))==(build['rows'],build['columns']),'actual complete cold reference row/column counts')
        require(batch['reference_models'][panel['id']]==build,'batch retained build attributes bind exact reference')
        counts=Counter(native['types'].values());domain=domain_contract(native,input_file(ROOT/panel['input_path']),'P-GRB')
        require(all(not re.fullmatch(r'round\d+.*',name) for name in native['bounds']),'reference remains original canonical model')
        checked.append(dict(id=panel['id'],SHA=sha(path),fingerprint=build['fingerprint'],rows=build['rows'],columns=build['columns'],native_types=dict(counts),domain=domain))
        cache.clear()
    return checked

def audit_fees(launches,admission=False):
    records=[];starts=0;seconds=0.
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        launch=obj(path);receipt=obj(path.parent/'receipt.json')
        require(launch['conservative_process_starts']==receipt['conservative_process_starts'] and not launch.get('engineering',False) and not receipt.get('engineering',False),'one fee per enclosing actual process tree')
        if receipt['exit_code'] and path.parent.name=='main05':
            proof=independent_numerical_recovery(launches[14],True)
            require(proof['decision']=='ACCEPT' and sha(path.parent/'receipt.json')==proof['unmodified_native_failure_fee_SHA'],'only exact known mathematical-evidence failure admits separately bound reader repair')
            require(receipt['exit_code']==1 and receipt['stop_reason']=='actual_exception' and receipt['actual_native_children_with_launch']==3 and launch['declared_native_children']==3 and launch['conservative_process_starts']==4,'original failed main05 still paid allactual3 plus wrapper')
            require('offline contradictory cross-arm physical/native evidence' in txt(path.parent/'failure.txt'),'real original numerical failure retained')
        elif receipt['exit_code'] and path.parent.name=='main06':
            contract=obj(REVIEW/'main06_recovery_contract_review01.json')
            require(sha(path.parent/'receipt.json')==contract['prepaid_coupon']['original_receipt_SHA'],'exact independently judged main06 failure receipt')
            require(receipt['exit_code']==1 and receipt['stop_reason']=='actual_exception' and receipt['actual_native_children_with_launch']==2 and launch['declared_native_children']==3 and launch['conservative_process_starts']==4,'original main06 actual2 plus unused18 remain paid4')
            require('Audit failed; retain evidence and stop before next arm' in txt(path.parent/'failure.txt'),'actual original failed main06 audit retained')
        elif receipt['exit_code'] and path.parent.name=='main09':
            failure=under_root(launches[24]['destination']);completion=obj(failure/'completion.json');original_audit=obj(failure/'audit.json')
            require(receipt['exit_code']==1 and receipt['stop_reason']=='actual_exception' and receipt['actual_native_children_with_launch']==1 and launch['declared_native_children']==3 and launch['conservative_process_starts']==4,'real main09 actual1 plus unstarted26/27 remain paid4')
            require(completion['returncode']==0xC00000FD and completion['committed_events']==0 and original_audit['passed'] is False and original_audit['endpoint'] is None,'exact unresolved abnormal parser stack-overflow failure; never performance endpoint')
            require('Audit failed; retain evidence and stop before next arm' in txt(path.parent/'failure.txt'),'actual original failed main09 wrapper retained')
        elif receipt['exit_code']:
            require(path.parent.name in ('qualification_cli01','qualification_cli02') and receipt['exit_code']==1 and receipt['stop_reason']=='actual_exception','only both visible qualification wrapper failures permitted')
            count=0 if path.parent.name=='qualification_cli01' else 4
            require(receipt['actual_native_children_with_launch']==count and launch['conservative_process_starts']==6,'each failed full5 declaration paid6 without refund; actual child count visible')
            reason='FileNotFoundError' if count==0 else 'Audit failed; retain evidence and stop before next arm'
            require(reason in txt(path.parent/'failure.txt'),'each exact raw wrapper failure remains visible')
        else:require(receipt['stop_reason']=='normal_return','ordinary complete paid fee wrapper')
        if path.parent.name=='qualification_seed_recovery01':
            original=OUT/'fees/qualification_cli02/receipt.json'
            coupon=launch['prepaid_native_child']
            require(launch['conservative_process_starts']==1 and launch['declared_native_children']==1 and receipt['actual_native_children_with_launch']==1,'one actual recovery wrapper plus one original prepaid native slot')
            require(coupon['fee']=='qualification_cli02' and coupon['ordinal']==5 and coupon['receipt_SHA']==sha(original) and coupon['never_started_verified'] and launch['no_refund'] and launch['no_double_native_fee'],'explicit untouched coupon ordinal and no doublecount/refund')
            q=obj(OUT/'qualification/cli01/identity.json');require(coupon['argv']==q['launches'][4]['command'],'paid-unused slot consumes only same fifth frozen native argv')
            require(receipt['native_child_fee_already_in_qualification_cli02'] and not receipt['nested_seconds_added'],'recovery fee uses outer wrapper without native seconds addition')
            rec=obj(OUT/'qualification/seed_reader_recovery01/recovery_receipt.json')
            require(rec['native_processes']==0 and str(rec['full_fourth_qualification_arm_seconds']).startswith('unknown:'),'fourth reader-only recovery has no native process and honestly unknown whole-arm clock')
            require(rec['old_audit_SHA']==sha(OUT/'qualification/seed_reader_recovery01/failed_audit_before.json') and rec['old_summary_SHA']==sha(OUT/'qualification/seed_reader_recovery01/failed_summary_before.jsonl'),'original failed fourth audit and summary retained exact bytes')
        elif receipt['exit_code']==0 and path.parent.name=='main07_prepaid01':
            plan=obj(OUT/'campaign/prepaid_recovery_plan02.json');side=obj(OUT/'campaign/reader_recovery/main06_numerical02.json');coupon=obj(OUT/'campaign/reader_recovery/prepaid18_consumption01.json')
            require(launch['declared_native_children']==receipt['actual_native_children_with_launch']==4 and launch['conservative_process_starts']==4 and launch['newly_billed_native_children']==receipt['newly_billed_native_children']==3 and launch['prepaid_native_children']==receipt['prepaid_native_children']==1,'actual4children plus1wrapper minus original paid18slot exactly4newstarts')
            require(launch['supplemental_plan_SHA']==sha(OUT/'campaign/prepaid_recovery_plan02.json') and launch['recovery_sidecar_SHA']==sha(OUT/'campaign/reader_recovery/main06_numerical02.json') and launch['original_coupon']==plan['prepaid_coupon']==side['prepaid_coupon']==coupon['coupon'],'unique original exact18 coupon and current source-bound plan')
            require(coupon['number']==18 and coupon['native_command']==launches[17]['command'] and coupon['original_fee_SHA']==sha(OUT/'fees/main06/receipt.json') and coupon['new_native_start_charge']==0 and coupon['original_paid_slot_retained'] and coupon['consumed_once_before_actual_native_launch'],'paid18 consumed once with same argv and no native refund or new fee')
            require(coupon['signed_admission_SHA']==sha(REVIEW/'performance_admission_resumption02.json') and coupon['supplemental_plan_SHA']==launch['supplemental_plan_SHA'] and receipt['extra_driver_processes']==0 and not receipt['earlier_fee_refunded'],'actual signed admission and no extra OS driver/refund')
            require([obj(path.parent/f'{n:02d}_before.json')['number'] for n in range(18,22)]==list(range(18,22)) and all(obj(path.parent/f'{n:02d}_after.json')['completed_and_audited'] for n in range(18,22)),'fixed serial order18 then19..21 allcompleted')
        elif receipt['exit_code']==0 and path.parent.name!='qualification_prepare01':
            require(receipt['actual_native_children_with_launch']==launch['declared_native_children'] and launch['conservative_process_starts']==1+launch['declared_native_children'],'ordinary formal wrapper declares exactly all actual native children and one wrapper')
        starts+=launch['conservative_process_starts'];seconds+=receipt['outer_seconds']
        records.append(dict(label=path.parent.name,starts=launch['conservative_process_starts'],outer_seconds=receipt['outer_seconds'],launch_SHA=sha(path),receipt_SHA=sha(path.parent/'receipt.json')))
    if admission:
        groups=[(r[8],r[9]) for r in decision['PANEL']]+[(cap,ms) for _,cap,ms in decision['SEED_CHECKS']]
        reserve=decision['remaining_budget'](starts,seconds,groups,overhead_seconds=1800.)
        require(starts==15 and seconds<=1200 and reserve['passed'],'paid15 qualification plus allremaining57=72/72 and88200 nominal fits after both saved wrapper failures')
        reserve['original_qualification_starts_reserved']=8;reserve['preserved_prechild_failure_extra_starts']=6
        reserve['additional_reader_recovery_wrapper_starts']=1
        reserve['actual_budget_replan_SHA']=sha(REVIEW/'seed_recovery_budget_review.json')
    else:
        require(starts<=72 and seconds<=100000,'actual allclosed conservative fees within hard limits');reserve=decision['remaining_budget'](starts,seconds,[])
    return dict(records=records,paid_starts=starts,paid_outer_seconds=seconds,reservation=reserve,nested_native_seconds_added=False)

def resumption_review(arms,launches,fees,identity):
    require(len(arms)==15 and [l['number'] for l in launches[:15]]==list(range(1,16)),'exact first15 closed actual formal arms')
    require(all(not under_root(l['destination']).exists() for l in launches[15:]),'all remaining27 actual native arms unstarted; no old-arm rerun')
    affected=arms[12:15];mb,ens,plain=affected
    require([(a['id'],a['seed'],a['arm']) for a in affected]==[('G50-C1',0,m) for m in ('M-B','ENS-C','P-GRB')],'exact affected group independently rebuilt')
    original_diag=obj(REVIEW/'cross_arm_diagnosis02/audit.json');contract=obj(REVIEW/'numerical_recovery_contract_review01.json')
    require(sha(REVIEW/'cross_arm_diagnosis02/audit.json')==contract['independent_diagnosis_SHA'],'original diagnosis unchanged')
    mechanisms=[]
    for a in (mb,ens):
        require(len(a['native_records'])==4 and [r['solve_kind'] for r in a['native_records']]==['LP','LP','LP','MIP'],'both methods made3 LP and1terminal MIP actualOptimize; never zero-call branch')
        require(len(a['model_contracts'])==3 and len(a['starts'])==len(a['start_attempts'])==1 and a['start_attempts'][0]['submitted'],'all three real models and existing complete Start independently checked')
        require(a['cover'] and a['cover']['whole_improving_domain_covered'],'real allcalls external partition independently checked')
        old=next(x for x in original_diag['independent_arms'] if x['arm']==a['arm'])
        require(old['native_records']==a['native_records'] and old['starts']==a['starts'] and old['cover']==a['cover'],'old diagnosis already auditedall4; correction is erroneous human mechanism prose, not omitted evidence')
        mechanisms.append(dict(arm=a['arm'],actual_Optimize=4,LP=3,terminal_MIP=1,submitted_existing_Start=1,native_records=a['native_records'],final_cover=a['cover']))
    require(ens['physical']['U']==ens['physical']['G']==ens['physical']['P']==0 and ens['certificate'] is True and ens['cover']['all_relevant_closed'],'ENS original physical zero certificate with actual closed root/native terminal provenance')
    zero=[w for w in ens['all_physical_witnesses'] if w['U']==0]
    require(zero and all(w['source']=='native_MIPSOL_verified_original_routes' for w in zero),'ENS zero physical witness actually originated inside native call4, never HGA startup')
    require(ens['native_records'][-1]['call']==4 and ens['native_records'][-1]['native_status']=='OPTIMAL' and ens['native_records'][-1]['returned_native_log_L']==0,'actual final native integer log OPTIMAL zero bound')
    require(not mb['certificate'] and mb['cover']['open_relevant_leaves']==1 and mb['native_records'][-1]['native_status']=='TIME_LIMIT','MB own open leaf/time limit remains uncertified')
    correction=dict(decision='ACCEPT_CORRECTION',original_diag_SHA=sha(REVIEW/'cross_arm_diagnosis02/audit.json'),original_contract_SHA=sha(REVIEW/'numerical_recovery_contract_review01.json'),
        erroneous_text_preserved=contract['mechanism_boundary'],correction='Both G50-C1 M-B and ENS-C executed3 LP and1 terminal MIP with one inherited existing Start. ENS zero fleet is native_MIPSOL call4; ENS certificate was already independently reconstructed through real terminal native OPTIMAL/root cover. No zero-call shortcut was executed. Prior human zeroOptimize/HGA-only characterization is withdrawn.',
        actual_raw_reaudited=True,physics_cold_counterexample_floor_and_thresholds_unchanged=True,mechanisms=mechanisms,ENS_zero_witnesses=zero,
        bounded_causal_statement='This one role establishes actual method outcomes and integer-domain difference, not independent causal attribution to p/d alone, Start alone or branching. No algorithm/rerun intervention occurred.',reviewer_Optimize=0)
    save(DEST/'mechanism_correction01.json',correction)
    require(plain['L']==0 and plain['certificate'] is False and plain['complete_seconds'] is None and plain['complete_seconds_interval']==[1770.375,1771.833281],'own P separately qualified floor0, no certificate promotion, unknown exact clock retained')
    require(plain['independent_numerical_recovery']['decision']=='ACCEPT' and not plain['native_bounds_mathematically_qualified'] and len(plain['rejected_raw_native_chronology'])==4,'all3callback claims and finalreturn explicitly rejected')
    groups=[(r[8],r[9]) for r in decision['PANEL'][5:]]+[(cap,ms) for _,cap,ms in decision['SEED_CHECKS']]
    reserve=decision['remaining_budget'](fees['paid_starts'],fees['paid_outer_seconds'],groups,overhead_seconds=1200.)
    require(fees['paid_starts']==35 and near(fees['paid_outer_seconds'],10901.428943390609,1e-8) and reserve['remaining_formal_starts']==37 and reserve['remaining_nominal_seconds']==72000 and reserve['passed'],'allpaid35 plus allremaining37=72 and remainingnominal72000+1200 fit; no failure refund')
    # The primary rebuild is a mandatory executed compatibility check, never
    # the source of independent physics, bound provenance or pair decisions.
    ep=OUT/'engineering/numerical_recovery_raw_rebuild01';receipt=obj(ep/'receipt.json')
    require(receipt['exit_code']==0 and receipt['engineering'] and receipt['conservative_solver_starts']==0 and receipt['stdout_SHA']==sha(ep/'stdout.log') and receipt['stderr_SHA']==sha(ep/'stderr.log') and not txt(ep/'stderr.log').strip(),'actual completed raw rebuild zero-solver receipt/output binding')
    for label in ('round109_numerical_recovery.py','round109_reader.py'):
        source=next(s for s in receipt['sources'] if Path(s['path']).name==label)
        require(source['SHA']==sha(ROOT/source['path']),'actual completed raw rebuild used current reader-only source '+label)
    finite=obj(OUT/'numerical_finite01/audit.json');fr=OUT/'engineering/numerical_recovery_finite01';freceipt=obj(fr/'receipt.json')
    require(finite['decision']=='ACCEPT' and finite['checks']==40 and len(finite['cases'])==40 and all(c['rejected'] for c in finite['cases']) and finite['zero_solver_calls'],'actual40 finite rejection cases passed')
    require(finite['helper_SHA']==sha(ROOT/'scripts/round109_numerical_recovery.py') and finite['reader_SHA']==sha(ROOT/'scripts/round109_reader.py') and finite['sidecar_SHA']==sha(OUT/'campaign/reader_recovery/main05_numerical01.json'),'finitecases exact actual source/sidecar binding')
    require(freceipt['exit_code']==0 and freceipt['conservative_solver_starts']==0 and freceipt['stdout_SHA']==sha(fr/'stdout.log') and freceipt['stderr_SHA']==sha(fr/'stderr.log'),'actual finite engineering receipt binding')
    reports=OUT/'reports_numerical_recovery01';table=rows(reports/'arms.csv');native=rows(reports/'native_calls.csv');reported_pairs=rows(reports/'pairs.csv')
    require(len(table)==15 and len(native)==64,'actual primaryraw tables15 formal plus5 qualification totaling64actualcalls')
    for a in arms:
        b=next(b for b in table if (b['id'],int(b['seed']),b['arm'])==(a['id'],a['seed'],a['arm']))
        require(near(float(b['U']),a['U']) and near(float(b['L']),a['L']) and (b['certificate']=='True')==a['certificate'],'primary endpoint corroborates independently computed own physics/bound/certificate')
        require((b['complete_seconds']=='' if a['complete_seconds'] is None else near(float(b['complete_seconds']),a['complete_seconds'],1e-9)),'exact/null clock publication agrees with actual independent timing proof')
    reported_P=next(b for b in table if (b['id'],b['arm'])==('G50-C1','P-GRB'))
    require(json.loads(reported_P['complete_seconds_interval'])==plain['complete_seconds_interval'] and reported_P['native_call_bounds_mathematically_qualified']=='False' and float(reported_P['raw_native_lower_bound_rejected'])==plain['independent_numerical_recovery']['raw_final_native_L'],'actualprimary bounded clock/rejectedrawbound labels exact')
    bound_table=rows(reports/'native_bounds.csv');Pbounds=[b for b in bound_table if (b['id'],b['arm'])==('G50-C1','P-GRB')]
    require(len(Pbounds)==3 and all(b['native_bound_mathematically_qualified']=='False' for b in Pbounds),'all3 real P callbacks marked mathematicallyunqualified in actualprimary table')
    pair_results=[]
    for n in range(0,15,3):
        own={a['arm']:a for a in arms[n:n+3]}
        require(max(a['L'] for a in own.values())<=min(a['U'] for a in own.values())+TOL,'unchanged1e-7 cross-arm closure after independently sourced rejection/floor')
        for x,y in [('M-B','P-GRB'),('M-B','ENS-C'),('ENS-C','P-GRB')]:
            result=decision['pair'](own[x],own[y]);pair_results.append(result)
            primary=next(r for r in reported_pairs if (r['id'],r['candidate'],r['control'])==(result['id'],x,y))
            require(primary['classification']==result['classification'] and (primary['severe_regression']=='True')==result['severe_regression'],'actualprimary pair agrees with own unchanged threshold arithmetic')
    for t in plain['complete_seconds_interval']:
        trial=dict(plain,complete_seconds=t)
        require(decision['pair'](mb,trial)['classification']=='WIN' and decision['pair'](mb,ens)['classification']=='LOSS' and decision['pair'](mb,ens)['severe_regression'] and decision['pair'](ens,trial)['classification']=='WIN','allaffectedclassifications invariant for entireboundedclock; Pnotcertifiedtimecomparison')
    return dict(decision='ACCEPT',resumption_allowed_now=True,scope='Only next never-started fixed group; no rerun or new native environment for reviewer',
        original_performance_admission_SHA=sha(REVIEW/'performance_admission.json'),original_candidate_identity_SHA=sha(OUT/'candidate_identity.json'),original_campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        correction_SHA=sha(DEST/'mechanism_correction01.json'),recovery=plain['independent_numerical_recovery'],remaining_budget=reserve,independent_pairs=pair_results,
        completed_raw_formal_arms=15,completed_raw_qualification_arms=5,remaining_formal_arms=27,all42_argv_unchanged=True,production_and_performance_helpers_unchanged=True,
        primary_rebuild_receipt_SHA=sha(ep/'receipt.json'),primary_rebuild_tables={p.name:sha(p) for p in [reports/'arms.csv',reports/'native_calls.csv',reports/'native_bounds.csv',reports/'pairs.csv',reports/'mechanism_summary.csv']},
        finite_audit_SHA=sha(OUT/'numerical_finite01/audit.json'),finite_receipt_SHA=sha(fr/'receipt.json'),original_main05_fee_failure_preserved=True,
        any_other_new_contradiction_must_stop=True,generic_automatic_floor_fallback_authorized=False,final42_selection_not_yet_made=True)

def main():
    DEST.mkdir(parents=True,exist_ok=False);tick=time.perf_counter();value={};error=None
    save(DEST/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_read_root=str(ROOT),source_SHA=sha(__file__),mode=args.mode,started_unix=time.time(),Optimize=0,native_environment=0))
    snapshots=DEST/'source_at_execution';snapshots.mkdir()
    for path in (Path(__file__),REVIEW/'round109_independent_parser.py',REVIEW/'round109_independent_kernel.py',REVIEW/'round109_independent_decision.py',REVIEW/'round109_independent_seed_scope.py',REVIEW/'round109_independent_numerical.py',REVIEW/'round109_independent_main06.py'):
        (snapshots/path.name).write_bytes(data(path))
    try:
        protocol,manifest,value['data_feasibility']=frozen_protocol();candidate,identity=current_bindings();launches=bind_launches(identity,manifest)
        value['bindings']=dict(candidate_identity_SHA=sha(OUT/'candidate_identity.json'),protocol_SHA=sha(OUT/'protocol.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),PE_SHA=EXPECTED_PE,DLL_SHA=EXPECTED_DLL,
            actual_PE_bytes_rehashed=args.mode!='public',actual_DLL_bytes_rehashed=args.mode!='public',source_bindings=candidate['source_bindings'],helper_bindings=identity['helpers'],all42_complete_argv=[l['command'] for l in launches])
        value['references']=audit_references(manifest)
        qualification_identity=obj(OUT/'qualification/cli01/identity.json');qualified=[]
        require(len(qualification_identity['launches'])==5,'five actual qualification children')
        require([(l['arm'],l['panel']['gurobi_seed']) for l in qualification_identity['launches']]==[('P-GRB',0),('ENS-C',0),('M-B',0),('P-GRB',1),('M-B',1)],'threeCLI plus P/MB Seed1 qualification on same known fixture')
        for launch in qualification_identity['launches']:
            arm,_,_=audit_arm(launch,qualification_identity,False);qualified.append(arm);cache.clear()
        value['qualification']=qualified
        actual_qualification=obj(OUT/'qualification/identity.json')
        require(actual_qualification['passed'] and actual_qualification['qualified_argv']==[l['command'] for l in qualification_identity['launches']] and actual_qualification['actual_seeds']==[0,0,0,1,1],'actual completed qualification binds five real argv and both seeds')
        value.update(production_PE_SHA=EXPECTED_PE,DLL_SHA=EXPECTED_DLL,candidate_identity_SHA=sha(OUT/'candidate_identity.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),qualification_identity_SHA=sha(OUT/'qualification/identity.json'))
        require(any(a['certificate'] for a in qualified) and any(r['solve_kind']=='LP' for a in qualified for r in a['native_records']) and any(a['starts'] for a in qualified),'actual LP/MIP/Start and legal complete certificate reached')
        value['fees']=audit_fees(launches,admission=args.mode=='admission')
        if args.mode!='admission':
            arms=[]
            completed=launches[:15] if args.mode=='resumption' else launches
            for launch in completed:
                arm,_,_=audit_arm(launch,identity,True);arms.append(arm);cache.clear()
            value['arms']=arms
            # This file must be independently signed before the first formal arm.
            admission=obj(REVIEW/'performance_admission.json')
            require(admission['decision']=='ACCEPT' and admission['bindings']['candidate_identity_SHA']==sha(OUT/'candidate_identity.json'),'unchanged independent signed admission candidate')
            eligibility=admission['input_eligibility']
            if args.mode=='resumption':
                value['resumption']=resumption_review(arms,launches,value['fees'],identity)
            else:
                value['selection']=decision['selection'](arms,eligibility)
                require(value['selection']['stage']!='BLOCKED','all42 actual valid normal endpoints and independent exact12 stage reconstruction')
        else:
            eligibility=obj(REVIEW/'input_eligibility.json')
            require(eligibility['decision']=='ACCEPT' and set(eligibility['eligible'])=={r[0] for r in decision['PANEL']} and all(eligibility['eligible'].values()),'independent exact12 initial unmeasured eligibility evidence')
            value['input_eligibility']=eligibility['eligible']
            value['formal_arms_already_started']=0
        value['decision']='ACCEPT'
    except Exception:
        error=traceback.format_exc();value['decision']='HOLD'
    value.update(error=error,completed_checks=count,completed_arms=milestones,mode=args.mode,explicit_read_root=str(ROOT),no_original_root_fallback=True,read_bindings=reads,
        reviewer_calls=dict(Optimize=0,LP_solve=0,native_environment=0,IIS=0,compiler=0,production_edits=0),engineering_elapsed_seconds=time.perf_counter()-tick,
        reviewer_sources={p.name:sha(p) for p in (Path(__file__),REVIEW/'round109_independent_parser.py',REVIEW/'round109_independent_kernel.py',REVIEW/'round109_independent_decision.py',REVIEW/'round109_independent_seed_scope.py',REVIEW/'round109_independent_numerical.py',REVIEW/'round109_independent_main06.py')})
    save(DEST/'audit.json',value);save(DEST/'receipt.json',dict(exit_code=int(error is not None),decision=value['decision'],audit_SHA=sha(DEST/'audit.json'),engineering_elapsed_seconds=time.perf_counter()-tick,cwd=str(Path.cwd()),source_SHA=sha(__file__)))
    print(json.dumps(dict(decision=value['decision'],error=error,completed_checks=count),ensure_ascii=False),flush=True)
    if error:sys.exit(1)
if __name__=='__main__':main()
