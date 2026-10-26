"""Zero-Optimize qualification collation and pre-formal protocol freeze."""
from round107_common import *
import csv,shutil
original_write=write
def write(path,value):
    path=Path(path)
    if path.exists():
        history=OUT/'protocol_history/preflight01'/path.relative_to(OUT);history.parent.mkdir(parents=True,exist_ok=True)
        assert not history.exists();shutil.copy2(path,history);path.unlink()
    original_write(path,value)
def run():
    selected=[OUT/'qualification/final03/scope',OUT/'qualification/final03/target',OUT/'qualification/final03/outer_deadline',OUT/'qualification/final02/inner_deadline']
    plan=read(OUT/'qualification/final03/plan.json');assert bindings()==plan['source_bindings']
    older=read(OUT/'qualification/final02/plan.json')
    for name in ['src/GurobiBaseline.cpp','src/Round105GurobiDecomposition.inc','include/Round105Decomposition.hpp','include/Round107Research.hpp']:
        assert bindings()[name]==older['source_bindings'][name],'reused inner qualification function changed'
    assert sha(DLL)==older['DLL_SHA']
    assert sha(BUILD/'ExactEBRP.exe')==plan['candidate_PE_SHA'] and sha(DLL)==plan['DLL_SHA']
    target=read(selected[1]/'case_1/controller_result.json');assert target['certified'] and target['target_reached']==target['requeues']==1 and target['terminal_calls']==1
    qs=[json.loads(x) for x in (selected[0]/'terminal/round107/requests.jsonl').read_text().splitlines()]
    assert qs[0]['optimal_close_by_dominance'] and qs[1]['local_INF'] and not qs[1]['domain_start']
    assert qs[2]['qualified_local_bound']>qs[2]['own_global_UB'] and not qs[2]['domain_start']
    cross=read(selected[0]/'terminal/round107/request_3/summary.json');assert cross['cross_request_hits']==2 and cross['remapped_rows']>=1
    inner=read(selected[3]/'inner/deadline.json');assert inner['actual_oracle_Optimize']==1 and inner['cancelled'] and inner['IIS']==0 and inner['remaining']<=0
    outer=read(selected[2]/'round107/request_1/summary.json');assert outer['master_calls']==1 and outer['outer_cancelled']
    totals={};LPs=0
    for root in selected:
        for p in root.rglob('calls.csv'):
            for row in csv.DictReader(p.open(newline='')):
                if row['stage']=='after':totals[row['phase']]=totals.get(row['phase'],0)+1
        for p in root.rglob('requests.jsonl'):
            for line in p.read_text().splitlines():
                q=json.loads(line)
                if q['kind']=='LP' and q['native_status'] in (2,3):LPs+=1
    assert not totals.get('iis',0) and not totals.get('core_confirm',0)
    totals['LP']=LPs
    write(OUT/'qualification/identity.json',dict(passed=True,source_bindings=bindings(),production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),
        DLL_SHA=sha(DLL),fixture_PE_SHA=sha(BUILD/'Round107Tests.exe'),native_call_totals=totals,
        qualified_sources=[p.relative_to(ROOT).as_posix() for p in selected],
        fixture_execution_identity=dict(first_three_plan_SHA=sha(OUT/'qualification/final03/plan.json'),inner_plan_SHA=sha(OUT/'qualification/final02/plan.json')),
        exclusions=['all earlier failed or superseded qualifications retained','final01 fourth job had no native Optimize and does not qualify an inner deadline'],
        inner_qualification_reuse='Final02 uses identical GurobiBaseline wrapper/R105Session/header and DLL. Only R107 final-vector physical archive/evidence code subsequently changed; affected scope/target/outer deadline were rerun at final03.',
        actual_target_controller_requeue_terminal=True,actual_inner_outer_deadline=True,production_handoff=False,
        fee_snapshot=budget()))
    development=read(ROOT/'results/unified_exact_round106/development_protocol.json')
    roles=development['roles'];roles[1]['id']='R98-C2'
    for r in roles:r['method_order']=['P-GRB','ENS-C','GLOBAL-STRUCT','FRONTIER-STRUCT'];assert sha(ROOT/r['input_path'])==r['input_sha256']
    admission=dict(A='At least one role: candidate certified, P not; or both certified and candidate complete observed time <=0.90 P. Other role candidate certified, or both P/candidate censored with candidate own U <=1.01 P and absolute complete-cover gap <=1.25 P.',
        B='C2 own U <=0.99 P and complete-cover absolute gap <=0.80 P, with a better independently verified real fleet. F2 own U <=1.01 P and gap <=1.05 P. If F2 P certified, candidate must certify; both certified pass F2 without zero-gap ratios.',
        tolerance='All improvements exceed original certificate/objective tolerances; contradictory bounds are ERROR, no clipping.',
        ENS_tradeoff='Disclose ENS certification/time loss. A/B authorize only the sealed confirmation, not algorithm admission.',
        reject='C2 remaining near0.37-0.39 versus P near0.20 does not authorize confirmation merely because F2 certification returns.')
    confirmation=read(ROOT/'results/unified_exact_round106/confirmation_protocol.json')
    for r in confirmation['roles']:
        r['method_order']=[('FRONTIER-STRUCT' if m=='EVENT-STRUCT' else m) for m in r['method_order']]
        assert sha(ROOT/r['input_path'])==r['input_sha256']
    confirmation.update(status='SEALED_NOT_EXECUTED_PENDING_COMPLETE_DEVELOPMENT',candidate='FRONTIER-STRUCT',admission=admission,
        inherited_protocol_commit='0350dbcc60d1c68e5c499d2e9880ecc1deaf031c',inherited_protocol_SHA=sha(ROOT/'results/unified_exact_round106/confirmation_protocol.json'),
        cancellation='Complete started three-arm groups. Cancel only wholly unstarted groups with a documented negative development/confirmation result. Any canceled/incomplete group precludes ADVANCE.')
    write(OUT/'confirmation_protocol.json',confirmation)
    write(OUT/'development_protocol.json',dict(roles=roles,nominal_seconds=12000,maximum_formal_children=8,
        method_order='F2 four arms then R98-C2 four arms, serial; immutable before first formal run',
        process_shutdown_margin_seconds=30,parameters=dict(Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL_SHA=sha(DLL),source_bindings=bindings(),qualification_identity_SHA=sha(OUT/'qualification/identity.json'),
        confirmation_protocol_SHA=sha(OUT/'confirmation_protocol.json'),confirmation_admission=admission,
        freeze_before_performance=True,revision='At most one evidence-driven substantive mechanism after all eight, no new net-return/cuts/IIS/parameters/heuristics. Any production PE change requires all eight final-identity arms.',
        retention='Preserve all failed launches, before/after and missing records, inputs, source/PE identities, actual P fingerprints, fair same-run self-paid startup. No interim ranking or selective truncation.',
        metric_contract=['complete observation fee/time and censor status','first real new fleet/UB','Y and attribution modes/events','qualified complete-cover LB/gap/certificate','A/B/FULL/cache/remap/submission/deferred/accepted','master/callback/oracle/time and actual Optimize/IIS'],
        budget_limit=dict(conservative_starts=72,outer_solver_fee_seconds=80000),prohibited=['new net-return upper row','IIS/core','LP-G/R97/R98/R100','candidate restarts','external UB/cuts/caches','new startup/neighborhood/branch priority/parameter combinations']))
    write(OUT/'source_runtime_manifest.json',dict(production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),fixture_PE_SHA=sha(BUILD/'Round107Tests.exe'),
        reference_PE_SHA=sha(BUILD/'Round65ReferenceBuild.exe'),DLL_SHA=sha(DLL),source_bindings=bindings(),
        inheritance_head='0350dbcc60d1c68e5c499d2e9880ecc1deaf031c',default_algorithms_unchanged=True,
        qualifications='Multiple exact fixture PE identities, same production bindings; original paid failures retained; selected native evidence listed in qualification/identity.json'))
    print(json.dumps(dict(protocol_frozen=True,qualification_passed=True,native_calls=totals,budget=budget())))
if __name__=='__main__':run()
