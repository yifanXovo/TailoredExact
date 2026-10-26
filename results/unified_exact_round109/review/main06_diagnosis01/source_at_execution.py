"""Independent diagnosis of the second real native-bound journal failure."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import argparse,csv,hashlib,json,math,re,runpy,sys,time,traceback
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
ROOT=Path(args.root).resolve();OUT=ROOT/'results/unified_exact_round109';REVIEW=OUT/'review';DEST=Path(args.out).resolve();assert DEST.is_relative_to(REVIEW);DEST.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def need(x,m):
    if not x:raise AssertionError(m)
tick=time.perf_counter();error=None;value={}
save(DEST/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0))
(DEST/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
try:
    original=sys.argv[:];sys.argv=[str(REVIEW/'round109_independent_raw.py'),'--root',str(ROOT),'--mode','final','--out',str(DEST),'--dll','D:/gurobi1302/win64/bin/gurobi130.dll']
    core=runpy.run_path(str(REVIEW/'round109_independent_raw.py'));sys.argv=original
    ident=read(OUT/'campaign/identity.json');first,plain,unused=ident['launches'][15:18]
    need([(l['number'],l['id'],l['arm']) for l in (first,plain,unused)]==[(16,'G50-C2','ENS-C'),(17,'G50-C2','P-GRB'),(18,'G50-C2','M-B')],'exact fixed three pending-group identities')
    ens,_,_=core['audit_arm'](first,ident,True);core['cache'].clear()
    d=Path(plain['destination']);p=plain['panel'];q=core['input_file'](ROOT/p['input_path']);raw=read(d/'result.json');actual=read(d/'launch.json');comp=read(d/'completion.json');failed=read(d/'audit.json')
    need(actual['command']==plain['command'] and actual['panel']==p and actual['prereg_sha256']==ident['prereg_sha256'],'full original actual P argv and identity unchanged')
    need(comp['returncode']==0 and comp['stop_reason']=='normal_return' and comp['within_cap'],'original P functional process returned normally inside cap')
    need(not failed['passed'] and failed['error']=="AssertionError('full_bound_witness_inconsistency')",'original real failure preserved as failed')
    ph=core['full_physics'](q,raw['routes'],p)
    need(ph['U']==ph['G']==ph['P']==raw['objective']==raw['upper_bound']==0 and ph['final_inventories']==raw['final_inventories']==q['target'],'own complete original integer physical zero fleet, all station targets reached')
    need(math.isfinite(p['lambda']) and p['lambda']>=0 and all(math.isfinite(w) and w>=0 for w in q['weights'][1:]) and all(t>0 for t in q['target'][1:]),'own full original physical-domain F=G+lambda*P>=0 including original zero denominator convention')
    observations=read(d/'observations.json');calls=[];bounds=[];witnesses=[];failures=[];returned=[]
    for seq,o in enumerate(observations,1):
        e=o['payload'];bb=core['data'](d/'journal'/f'event_{seq}.json');commit=core['txt'](d/'journal'/f'event_{seq}.commit').split()
        need(e['sequence']==o['sequence']==seq and hashlib.sha256(bb).hexdigest()==o['sha256']==commit[4] and json.loads(bb)==e and commit[0]=='NEJ1' and int(commit[1])==seq and int(commit[3])==len(bb),'all exact complete committed journalbytes')
        need(core['near'](float(commit[2]),o['data_close_seconds'],1e-9) and core['near'](o['effective_available_seconds'],max(o['data_close_seconds'],o['first_observed_seconds']),1e-9),'all original availability timestamps')
        if e['kind']=='identity':need(seq==1 and e['input_sha256']==p['input_sha256'] and e['analytical_full_domain_lower_bound']==0 and (e['V'],e['M'],e['T'],e['lambda'],e['pickup_seconds'],e['drop_seconds'])==(p['V'],p['M'],p['T_seconds'],p['lambda'],p['pickup_seconds'],p['drop_seconds']),'actual own input/physics identity')
        elif e['kind']=='call':calls.append(e)
        elif e['kind']=='bound':bounds.append(e)
        elif e['kind']=='witness':
            w=core['full_physics'](q,e['routes'],p);need(core['near'](w['U'],e['objective']) and core['near'](w['G'],e['G']) and core['near'](w['P'],e['P']),'every actual own committed complete physical witness')
            witnesses.append(dict(w,sequence=seq,source=e['source'],raw_available=o['effective_available_seconds']))
        elif e['kind']=='failure':failures.append(e)
        elif e['kind']=='returned':returned.append(e)
        elif e['kind']=='witness_rejected':pass
        else:raise AssertionError('unknown/new journal kind')
    need(len(calls)==1 and calls[0]['call']==1 and calls[0]['full_original']==calls[0]['native_preconditions']==1 and calls[0]['settings']==dict(read_return_code=0,**core['SETTINGS'],Seed=0),'exact full original cold call and actual nine native settings')
    need([b['sequence'] for b in bounds]==[3,37] and bounds[0]['native_bound']==0 and bounds[1]['native_bound']==1.816725899087706e-6 and all(b['call']==1 and b['global_available']==1 and b['inconsistent']==0 and b['global_bound']==b['native_bound'] for b in bounds),'original callback claims retained, positive bound37 actual beyond unchanged tolerance')
    need(len(observations)==142 and failures==[dict(schema=1,sequence=142,kind='failure',reason='full_bound_witness_inconsistency')] and not returned,'actual journal stops at failure142; no returned event or invented sequence')
    zero=[w for w in witnesses if w['U']==0];need(len(zero)==1 and zero[0]['sequence']==141 and zero[0]['source']=='native_MIPSOL_verified_original_routes','P own zero witness exposed historical bound contradiction')
    source=core['txt'](ROOT/'src/NativeEvidenceJournal.cpp');capture=core['txt'](ROOT/'src/GurobiBaseline.cpp')
    need('if(failed_) return;' in source and 'failed_=true;' in source and 'publish("returned"' in source,'frozen journal latches failure then suppresses actual subsequent returned publication')
    need('result.gurobi_optimize_return_code = api.optimize(model);' in capture and 'result.native_mipopt_return_code = result.gurobi_optimize_return_code;' in capture,'direct frozen native optimize-return capture into actual result field')
    need(raw['native_mipopt_return_code']==raw['gurobi_optimize_return_code']==0 and raw['native_mip_mipopt_count']==raw['gurobi_optimize_count']==1,'actual rc0 exists outside missing journal event, no inferred returned sequence')
    for f in ['native_mip_evidence_available','native_mip_evidence_capture_complete','native_mip_lifecycle_valid','native_mip_solver_finalization_reached','native_mip_problem_freed','native_mip_environment_closed','gurobi_lifecycle_valid','gurobi_native_domain_audit_passed','gurobi_native_variable_bounds_match','gurobi_native_objective_sense_match','native_mip_status_code_text_consistent']:need(raw[f] is True,'actual native lifecycle/domain capture '+f)
    need(raw['native_mip_status_text']=='OPTIMAL' and raw['native_mip_status_code']==2 and raw['native_mip_best_bound_available'] and raw['native_mip_objective_available'] and raw['native_mip_objective']==raw['native_mip_best_bound']==raw['gurobi_obj_bound_c']==raw['gurobi_obj_bound']==0,'raw final native readback0/OPTIMAL corroborates terminal log, does not validate older positive callback')
    native=core['txt'](d/'native.log');need('Optimal solution found (tolerance 0.00e+00)' in native and re.findall(r'Best objective ([^,]+), best bound ([^,]+), gap ([^\n]+)',native)[-1][:2]==('0.000000000000e+00','0.000000000000e+00'),'actual normal final native integer log objective/bound0')
    need(not raw['gurobi_hga_start_requested'] and 'Loaded user MIP start' not in native,'actual unchanged cold P with no submitted foreign or HGA Start')
    cold=d/'compact.lp';need(core['sha'](cold)==core['sha'](core['reference_path'](p))==p['reference']['canonical_sha256']==calls[0]['model_sha256'],'own current original model exact allpaths')
    m=core['model'](cold);domain=core['domain_contract'](m,q,'P-GRB');core['scope_contract'](calls[0],m,q)
    match=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',native);types=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',native);ct=Counter(m['types'].values())
    need((int(match[1]),int(match[2]))==(len(m['rows']),len(m['bounds'])) and {k:ct.get(k,0) for k in ['C','I','B']}==dict(C=int(types[1]),I=int(types[2])-int(types[3]),B=int(types[3])),'all actual original rows/columns/native pre-presolve integer types')
    need(m['objective']['G']==1 and all(math.isfinite(a) and a>=0 and m['bounds'][n][0]>=0 for n,a in m['objective'].items()),'own cold complete-domain objective floor0')
    # Build a complete diagnostic vector from this P's own zero fleet. Reuse
    # only the already audited mapping/rational-arithmetic body, never ENS U.
    fleet,mapping=core['normalize_existing_start_routes'](q,ph['full_routes']);mapped=core['full_physics'](q,fleet,p);need(mapped['U']==0,'allowed original same-capacity normalization retains own zero fleet')
    body=(REVIEW/'cross_arm_diagnosis02/source_at_execution.py').read_text()
    body=body[body.index('    vals={n:0.'):body.index('    observations=obj(Path(launches[2]')]
    import textwrap
    namespace=dict(core=core,m=m,q=q,ph=mapped,fleet=fleet,p=p,DEST=DEST,vals=None,need=need,save=save,sha=sha,math=math,re=re,Fraction=Fraction,csv=csv)
    exec(compile(textwrap.dedent(body),'inherited_audited_own_fleet_cold_vector_body','exec'),namespace)
    exact_obj=float(namespace['exact_objective']);need(exact_obj+core['TOL']<bounds[1]['native_bound'],'exact complete original binary64 matrix counterexample disproves stored positive callback')
    fee=read(OUT/'fees/main06/receipt.json');need(fee['exit_code']==1 and fee['conservative_process_starts']==4 and fee['actual_native_children_with_launch']==2,'actual main06 failure retains original4paid with2actualchildren')
    lower=comp['fully_observed_end_to_end_seconds'];upperraw=fee['outer_seconds']-ens['complete_seconds'];upper=math.ceil(upperraw*1e6)/1e6
    need(0<lower<=upper<plain['cap_seconds'] and not (d/'whole_arm_receipt.json').exists(),'missing fullPclock bounded honestly by original supervisor/enclosing wrapper-minus-ENS')
    timing=[]
    for t in (lower,upper):
        arm=dict(id=p['id'],seed=0,arm='P-GRB',U=0.,L=0.,gap=0.,certificate=True,certificate_qualified=True,numbers_qualified=True,complete_seconds=t)
        pr=core['decision']['pair'](ens,arm);need(pr['classification']=='WIN' and not pr['severe_regression'],'ENS/P WIN for complete entire original interval')
        timing.append(dict(sensitivity_P_seconds=t,classification=pr['classification'],severe_regression=pr['severe_regression'],ratio_at_interval_endpoint=ens['complete_seconds']/t))
    need(not Path(unused['destination']).exists() and not (OUT/'fees/main06/18_before.json').exists() and not (OUT/'fees/main06/17_after.json').exists(),'unique child18 prepaid but never started or completed; no later M-B arm')
    paid_starts=sum(read(f)['conservative_process_starts'] for f in (OUT/'fees').glob('*/receipt.json'));paid_seconds=sum(read(f)['outer_seconds'] for f in (OUT/'fees').glob('*/receipt.json'))
    remaining=ident['launches'][17:];groups=len({l['group_number'] for l in ident['launches'][18:]});nominal=sum(l['cap_seconds'] for l in remaining)
    need(paid_starts==39 and core['near'](paid_seconds,11659.298868327402,1e-8) and len(remaining)==25 and groups==9 and nominal==68400 and paid_starts+24+9==72 and paid_seconds+nominal+120*groups<=100000,'allremaining25native includingonly prepaid18 plus9actualfuturewrapper reserve; no refunds/extrastarts')
    value=dict(decision='ACCEPT_DIAGNOSIS_CONDITIONAL_RECOVERY',resumption_allowed_now=False,actual_issue='stored native callback37 positive numerical claim contradicted by this same cold-P own physical zero witness; terminal rawnativeL subsequently0',ENS=ens,
        P_own_physical=ph,P_qualified_L=0.,P_independent_complete_certificate=True,P_certificate_basis='own complete original physical zero fleet plus independently proved own original full-domain nonnegative floor',P_old_failed_audit_preserved=failed,
        actual_native_call=calls[0],raw_bounds=bounds,raw_failure=failures[0],raw_returned_journal_events=returned,native_return_basis='actual native_mipopt_return_code and gurobi_optimize_return_code0, direct frozen api.optimize assignment, matching full model/log and cleanup/normal process lifecycle',native_return_journal_sequence=None,native_return_event_missing_preserved=True,
        own_zero_witness=zero[0],complete_cold_model=dict(SHA=sha(cold),domain=domain,exact_vector_SHA=sha(DEST/'exact_binary64_matrix_witness.json'),exact_objective_upper=exact_obj,rows=len(m['rows']),columns=len(m['bounds']),normalization=mapping),
        P_timing=dict(exact_seconds=None,interval=[lower,upper],unrounded_upper=upperraw,later_repair_time_added_to_old_interval=False),ENS_P_time_class_invariant=timing,exact_certified_time_ratio=None,ENS_P_ratio_interval=[ens['complete_seconds']/upper,ens['complete_seconds']/lower],
        proposed_budget=dict(paid_starts=paid_starts,paid_outer_seconds=paid_seconds,remaining_native25=25,prepaid_unstarted_child=18,prepaid_receipt_SHA=sha(OUT/'fees/main06/receipt.json'),additional_native_fees=24,future_wrappers=9,additional_starts=33,total_starts72=72,remaining_nominal=nominal,remaining_wrapper_overhead=120*groups,no_refund=True,no_extra_driver=True),
        wrapper_plan_scope='Conditional necessary evidence/budget fault recovery only: new supplemental wrapper may process18 then19/20/21 serially under original per-arm caps/commands and group crosschecks, chargeone wrapper+3unpaidchildren, explicitly consume unique main06 ordinal3 coupon once. No existing frozen helper/source/candidate/protocol bytes changed.',
        required_gates=['Explicitly reject callback3/37 and retain rawfinal0 as raw; certify solely ownphysicalzero+floor, never ENS transfer or relabeled native bound.','Preserve failure142 and missingreturned sequence; reconstruct only actual returnrc0/lifecycle outsidejournal with bound source identities.','Keep wholePtime/ratio exactnull and outwardinterval. Every both-certified pair must have same class/severity for allinterval values; otherwise UNEVALUABLE/HOLD classification as contract requires.','Freeze supplemental wrapper and evidence projection with actual code/finite checks; preserve oldsummary/audit; no rerun; fullsource/argv/fees/admission supplement before native.','Coupon18 bound to originalmain06 receipt/ordinal/argv and actualunstartedproof; old4startfee untouched, no newly charged child18/no driver/newwrapper.','Actual reader rebuild and independent supplement pass; other new failures stillstop; all42 remainrequired.'],
        read_bindings=core['reads'],source_bindings={str(p):sha(ROOT/p) for p in ['src/NativeEvidenceJournal.cpp','src/GurobiBaseline.cpp']},Optimize=0,native_environment=0,production_edits=0)
    print(json.dumps(dict(decision=value['decision'],P_own_F=ph['U'],P_own_full_domain_certificate=True,raw_positive_bound=bounds[1]['native_bound'],journal_returned_missing=True,P_interval=[lower,upper],starts72=72)),flush=True)
except Exception:
    error=traceback.format_exc();value.update(decision='HOLD',error=error);print(error,file=sys.stderr,flush=True)
save(DEST/'audit.json',value);save(DEST/'receipt.json',dict(exit_code=int(error is not None),elapsed_engineering_seconds=time.perf_counter()-tick,source_SHA=sha(__file__),audit_SHA=sha(DEST/'audit.json'),Optimize=0,native_environment=0))
if error:sys.exit(1)
