"""Receipt-scoped post-seal recovery; frozen producers and helpers stay intact.

The cold producer's final fleet defines own_U.  An earlier observational fleet
may have a smaller feasible objective.  The R86 ordering assertion between the
two feasible U values is replaced in memory by an explicitly scoped proof of
both fleets and all bound inequalities.  No endpoint is selected or improved.
All derived recovery files live outside the original, failed raw directory.
"""
from pathlib import Path
import argparse, ast, contextlib, copy, inspect, json, os, subprocess, sys, time, traceback
import round122_common as common
import round86_native_evidence as native
import round108_reader as core

ROUND='results/unified_exact_round122'
RAW='campaign/group08/raw/03_PB-C50-S_S1_P-GRB'
VIEW='recovery/group08/p_sidecars'
EXPECTED={
    'result.json':'c5884b1cd88f9077e37842296e749fa1132c75fdf231c13c027b8b89b885e04c',
    'observations.json':'b35f45c42c1eb97575b7228d8645210c8a81b4820c40ec74b1b0513ce7dfee8f',
    'producer_receipt.json':'1d3452a853622581642ca1320a4af24534c390af9e8b4e3260d1a95cf0cb4ee3',
    'producer_seal.json':'de752c8eebc3ed9d42f7f23b1d46c7ecc8e02abd94137d1761ca93d42bfb2d6a',
    'audit.json':'df1dd3b51e9245476c43e2786ce8baef43d084bc5d8f86ff6cf9d9152d8ed2c1',
}
INPUT_SHA='3e17bd07ae0abbfebfd8264540e6f5bd737a0d4506c4b6e96950936153db9992'
FINAL_U=0.39178055857928196
FINAL_L=0.34945085964584033
HISTORY_U=0.391713327901773
SIDECARS=frozenset(['computed_seed_scope.json','round120_model_contracts.json','call_log_views.json',
    'round120_event_contract.json','round120_extended_verification.json','audit.json',
    'independent_evidence.json','native_claims.json','claim_rejections.json','audit_execution_metrics.json',
    'postexit_audit_receipt.json','verification_closeout.json','arm_total_receipt.json'])

def paths(root):
    out=Path(root)/ROUND
    return out,out/RAW,out/VIEW

def source_equivalence(root):
    source=(Path(root)/'scripts/round86_native_evidence.py').read_text(encoding='utf-8-sig')
    original=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='finalize_endpoint')
    expected=ast.parse("assert audited['UB']+1e-7 >= upper").body[0]
    replacement=ast.parse('assert _r122_history_guard(root,panel,arm,audited,records,result,upper)').body[0]
    modified=copy.deepcopy(original);changed=[]
    class Replace(ast.NodeTransformer):
        def visit_Assert(self,node):
            if ast.dump(node,include_attributes=False)==ast.dump(expected,include_attributes=False):
                changed.append(1);return ast.copy_location(copy.deepcopy(replacement),node)
            return self.generic_visit(node)
    modified=Replace().visit(modified);assert changed==[1]
    reversed_node=copy.deepcopy(modified);reverted=[]
    class Reverse(ast.NodeTransformer):
        def visit_Assert(self,node):
            if ast.dump(node,include_attributes=False)==ast.dump(replacement,include_attributes=False):
                reverted.append(1);return ast.copy_location(copy.deepcopy(expected),node)
            return self.generic_visit(node)
    reversed_node=Reverse().visit(reversed_node)
    assert reverted==[1] and ast.dump(reversed_node,include_attributes=False)==ast.dump(original,include_attributes=False)
    return modified,dict(changed_assertions=1,all_other_AST_identical=True,
        original_finalizer_file_SHA=common.sha(Path(root)/'scripts/round86_native_evidence.py'),
        original_assertion=ast.unparse(expected),replacement_assertion=ast.unparse(replacement),
        final_U_L_certificate_assignment_AST_unchanged=True,all_source_scope_and_bound_checks_retained=True)

def originals(root):
    _,d,_=paths(root)
    return {p.relative_to(d).as_posix():common.sha(p) for p in sorted(d.rglob('*')) if p.is_file()}

def check_scope(root):
    out,d,_=paths(root)
    for name,digest in EXPECTED.items():assert common.sha(d/name)==digest,('recovery scope changed',name)
    identity=common.read(out/'campaign/group08/identity.json')
    launch=next(l for l in identity['launches'] if l['arm']=='P-GRB')
    assert launch['seed']==1 and launch['number']==3 and launch['panel']['input_sha256']==INPUT_SHA
    assert common.sha(Path(root)/launch['panel']['input_path'])==INPUT_SHA
    candidate=common.read(out/'candidate_identity.json')
    assert identity['helpers']==candidate['helpers'] and identity['source_hashes']==candidate['source_bindings']
    for name,digest in {**candidate['helpers'],**candidate['source_bindings']}.items():assert common.sha(Path(root)/name)==digest,name
    seal=common.read(d/'producer_seal.json');p=common.read(d/'producer_receipt.json')
    assert p['producer_seal_SHA']==EXPECTED['producer_seal.json'] and p['native_stopped_no_reentry']
    for name,digest in seal['required_SHA'].items():assert common.sha(d/name)==digest
    return launch,identity

def history_guard(root,panel,arm,audited,records,result,upper,checks):
    out,d,_=paths(root)
    assert arm=='P-GRB' and panel['gurobi_seed']==1 and panel['input_sha256']==INPUT_SHA
    assert common.sha(d/'result.json')==EXPECTED['result.json'] and common.sha(d/'observations.json')==EXPECTED['observations.json']
    assert result==common.read(d/'result.json') and records==common.read(d/'observations.json')
    assert result['upper_bound']==upper==FINAL_U and result['lower_bound']==FINAL_L
    assert result['strict_certified_original_problem'] is False and result['gurobi_optimize_count']==1
    assert len(records)==223 and audited['physical_witnesses']==156 and len(audited['witnesses'])==156
    assert audited['UB']==HISTORY_U and audited['UB']+1e-7<upper
    # Recompute every original fleet using the strict complete physical reader.
    witnesses=[core.full_fleet(root,panel,q['payload']) for q in records if q['payload']['kind']=='witness']
    final=core.full_fleet(root,panel,result)
    assert len(witnesses)==156 and min(w['F'] for w in witnesses)==HISTORY_U and final['F']==FINAL_U
    assert all(abs(a['F']-b['F'])<=1e-14 for a,b in zip(audited['witnesses'],witnesses))
    calls=[q['payload'] for q in records if q['payload']['kind']=='call']
    returns=[q['payload'] for q in records if q['payload']['kind']=='returned']
    bounds=[q['payload'] for q in records if q['payload']['kind']=='bound']
    expected=dict(read_return_code=0,Threads=1,Seed=1,Presolve=-1,MIPGap=0,MIPGapAbs=0,
        FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    assert len(calls)==len(returns)==1 and returns[0]['return_code']==0 and calls[0]['settings']==expected
    assert calls[0]['full_original'] and calls[0]['model_scope']=='complete_original_compact_milp'
    assert calls[0]['model_sha256']==panel['reference']['canonical_sha256']==common.sha(d/'compact.lp')
    assert len(bounds)==64 and all(not b['global_available'] and b['global_bound'] is None and not b['inconsistent'] for b in bounds)
    assert max(b['native_bound'] for b in bounds)==result['gurobi_obj_bound_c']==FINAL_L
    assert all(b['native_bound']<=w['F']+1e-7 for b in bounds for w in witnesses+[final])
    assert FINAL_L<=min(HISTORY_U,FINAL_U)+1e-7 and audited['LB']<=HISTORY_U+1e-7
    checks.append(dict(history_U=HISTORY_U,final_U=FINAL_U,final_L=FINAL_L,witnesses=156,bounds=64,
        all_physical_and_bound_inequalities_verified=True,final_endpoint_unchanged=True,
        no_new_solution_bound_or_observation=True))
    return True

@contextlib.contextmanager
def evidence_view(root,*,writing=False):
    """Route only exact derived P sidecars; raw failure and producer stay intact."""
    root=Path(root).absolute();out,d,view=paths(root)
    if writing:view.mkdir(parents=True,exist_ok=True)
    assert view.is_dir()
    node,equivalence=source_equivalence(root);checks=[]
    original_open,original_stat=Path.open,Path.stat
    original_finalize=native.finalize_endpoint
    raw_key=os.path.normcase(os.path.abspath(d))
    mapping={os.path.normcase(os.path.abspath(d/n)):view/n for n in SIDECARS}
    def key(path):return os.path.normcase(os.path.abspath(path))
    def routed_open(path,mode='r',*args,**kwargs):
        name=key(path);target=mapping.get(name,path)
        if any(c in mode for c in 'wax+') and (name==raw_key or name.startswith(raw_key+os.sep)):
            assert writing and name in mapping,('write to immutable original P evidence',str(path))
        return original_open(target,mode,*args,**kwargs)
    def routed_stat(path,*args,**kwargs):return original_stat(mapping.get(key(path),path),*args,**kwargs)
    namespace=dict(vars(native),_r122_history_guard=lambda *args:history_guard(*args,checks))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
        str(Path(__file__))+'::one_hash_scoped_readonly_assertion','exec'),namespace)
    def finalizer(root_arg,panel,arm,audited,records,result,reason,reference):
        if arm=='P-GRB' and panel.get('input_sha256')==INPUT_SHA and panel.get('gurobi_seed')==1:
            assert reason=='normal_return'
            return namespace['finalize_endpoint'](root_arg,panel,arm,audited,records,result,reason,reference)
        return original_finalize(root_arg,panel,arm,audited,records,result,reason,reference)
    active=[True]
    def boundary(event,args):
        if active[0] and event in ['subprocess.Popen','socket.connect']:
            raise AssertionError('native/process/network forbidden during read-only recovery view')
    sys.addaudithook(boundary)
    Path.open,Path.stat,native.finalize_endpoint=routed_open,routed_stat,finalizer
    try:yield dict(equivalence=equivalence,semantic_guard_checks=checks,sidecar_names=sorted(SIDECARS))
    finally:
        Path.open,Path.stat,native.finalize_endpoint=original_open,original_stat,original_finalize
        active[0]=False

def prepare():
    common.workspace();l,i=check_scope(common.ROOT);out,d,view=paths(common.ROOT)
    target=out/'recovery/group08';assert not (target/'prerecord.json').exists()
    last=i['launches'][3];assert last['arm']=='MB-D1' and last['number']==4 and last['seed']==1
    assert not Path(last['destination']).exists() and not (out/'fees/formal08/04_before.json').exists()
    failure=common.read(out/'fees/formal08/receipt.json');assert failure['exit_code']==1 and failure['actual_exit_observed'] and failure['actual_native_children']==3
    b=common.budget();assert not b['unclosed'] and b['remaining_outer_seconds']>=1200+3720
    _,equivalence=source_equivalence(common.ROOT)
    retained={n:common.sha(out/n) for n in ['fees/formal08/failure.txt','fees/formal08/receipt.json',
        'fees/formal08/pending_exit_receipt.json','controller/formal08/stderr.log']}
    target.mkdir(parents=True,exist_ok=True)
    common.write(target/'prerecord.json',dict(schema='round122-group08-scoped-readonly-recovery-v1',UTC=common.utc(),
        cause='Legacy assertion orders two separately valid feasible U values; frozen own_U uses final result fleet.',
        script_SHA=common.sha(__file__),candidate_identity_SHA=common.sha(out/'candidate_identity.json'),
        independent_investigation_SHA=common.sha(out/'review/group08_cold_investigation.json'),
        original_P_files=originals(common.ROOT),retained_failed_attempt_files=retained,equivalence=equivalence,
        final_U=FINAL_U,final_L=FINAL_L,final_certificate=False,historical_observational_U=HISTORY_U,
        T_produce=common.read(d/'producer_receipt.json')['T_produce'],
        T_verify_policy='Actual monotonic verification close minus original t_produce; includes failure, investigation and waiting gap.',
        read_only_fee=dict(label='postseal08a',native_children=0,outer_reservation=1200),
        continuation=dict(label='continue08d1',only_ordinal=4,launch=last,full_group_rerun=False,
            prerequisite='Successful sealed P re-audit plus actual independent adapter admission.',
            identical_frozen_argv_PE_DLL_environment=True,wrapper_birth_import_charged_to_this_D1_T_produce=True,
            cap_seconds=3600,management_reservation=120),budget_before=b,
        no_producer_rerun=True,no_new_Optimize_during_reaudit=True,no_measured_helper_file_changes=True))
    print(json.dumps(dict(prerecorded=True,ordinal=4,remaining=b['remaining_outer_seconds'])),flush=True)

def reaudit():
    from round122_evidence import verify
    out,d,view=paths(common.ROOT);pr=common.read(out/'recovery/group08/prerecord.json')
    assert pr['script_SHA']==common.sha(__file__);l,i=check_scope(common.ROOT)
    assert originals(common.ROOT)==pr['original_P_files']
    with evidence_view(common.ROOT,writing=True) as proof:
        value=verify(l,i)
        assert value['passed'] and value['native_proof_qualified'] and value['endpoint']['U']==FINAL_U and value['endpoint']['L']==FINAL_L
        assert value['endpoint']['certificate'] is False and len(proof['semantic_guard_checks'])==1
        total=common.read(d/'arm_total_receipt.json');producer=common.read(d/'producer_receipt.json')
        assert total['T_verify']==total['t_verified_perf']-producer['t_produce_perf']
        assert total['T_total']==producer['T_produce']+total['T_verify'] or abs(total['T_total']-producer['T_produce']-total['T_verify'])<1e-8
    assert originals(common.ROOT)==pr['original_P_files']
    for name,digest in pr['retained_failed_attempt_files'].items():assert common.sha(out/name)==digest
    common.write(out/'recovery/group08/reaudit_receipt.json',dict(passed=True,UTC=common.utc(),
        prerecord_SHA=common.sha(out/'recovery/group08/prerecord.json'),script_SHA=common.sha(__file__),
        evidence=proof,original_all_P_file_hashes_unchanged=True,original_failed_fee_and_audit_unchanged=True,
        derived_recovery_sidecars={n:common.sha(view/n) for n in SIDECARS if (view/n).is_file()},
        final_U=FINAL_U,final_L=FINAL_L,certificate=False,T_produce=producer['T_produce'],
        T_verify=total['T_verify'],T_total=total['T_total'],waiting_gap_retained=True,Optimize=0,native_starts=0))
    print(json.dumps(dict(recovered=True,final_U=FINAL_U,T_verify=total['T_verify'])),flush=True)

def continuation():
    import round122_campaign as campaign
    from round100_idle import ensure_idle
    out,_,_=paths(common.ROOT);pr=common.read(out/'recovery/group08/prerecord.json')
    accepted=common.read(out/'review/recovery_adapter_admission.json')
    assert accepted['decision']=='ACCEPT' and accepted['script_SHA']==common.sha(__file__)==pr['script_SHA']
    assert accepted['reaudit_receipt_SHA']==common.sha(out/'recovery/group08/reaudit_receipt.json')
    i=common.read(out/'campaign/group08/identity.json');l=i['launches'][3]
    assert l==pr['continuation']['launch'] and not Path(l['destination']).exists()
    assert i['helpers']==common.helpers() and i['source_hashes']==common.bindings();common.identity();ensure_idle()
    fee,tick=common.fee_begin('continue08d1',1,3720,False,dict(starts=0,seconds=0))
    code=1
    try:
        capacity=common.workspace();assert capacity['volume_free_bytes']>=common.read(out/'workspace_capacity.json')['minimum_group_start_free_bytes']
        common.write(fee/'capacity_before.json',capacity)
        birth=common.read(fee/'launch.json')['wrapper_creation_unix']
        common.write(fee/'04_before.json',dict(number=4,id=l['id'],arm=l['arm'],seed=1,t0_perf=tick,t0_unix=birth,
            original_position_never_started=True,wrapper_birth_and_import_in_T_produce=True,prerecord_SHA=common.sha(out/'recovery/group08/prerecord.json')))
        campaign.execute(l,i,tick,birth)
        common.write(fee/'04_after.json',dict(producer_receipt_SHA=common.sha(Path(l['destination'])/'producer_receipt.json'),
            total_receipt_SHA=common.sha(Path(l['destination'])/'arm_total_receipt.json'),verification_complete=True))
        from read_round122 import rebuild_group
        start=time.perf_counter()
        with evidence_view(common.ROOT):rebuild_group(8,out/'reconstruction/group08')
        common.write(fee/'group_verification_receipt.json',dict(seconds=time.perf_counter()-start,inside_group_outer_clock=True,
            current_core_SHA=common.sha(out/'reconstruction/group08/current_core.json'),Optimize=0,
            original_P_failure_preserved_and_separate_recovery_view_used=True));code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:common.fee_pending(fee,tick,False,code,1,common.child_states([l]))

def worker(action):
    common.workspace()
    if action=='reaudit':
        fee,tick=common.fee_begin('postseal08a',0,1200,False,dict(starts=2,seconds=3720));code=1
        try:reaudit();code=0
        except BaseException:
            (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
        finally:common.fee_pending(fee,tick,False,code,0,[])
    else:continuation()

def run(action):
    from qualify_round120 import child_creation
    from round122_runner import subprocess_proxy
    common.workspace();label='postseal08a' if action=='reaudit' else 'continue08d1'
    log=common.OUT/'controller'/label;log.mkdir(parents=True,exist_ok=False)
    cmd=[str(common.PYTHON),'-B',str(Path(__file__)),action,'--worker']
    tick=time.perf_counter()
    with (log/'stdout.log').open('xb') as so,(log/'stderr.log').open('xb') as se:
        child=subprocess.Popen(cmd,cwd=common.ROOT,env=common.environment(),stdout=so,stderr=se)
        birth=child_creation(child)
        common.write(log/'launch.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=birth,command=cmd,
            controller_pid=os.getpid(),controller_actual_creation_unix=child_creation(subprocess_proxy()),
            controller_startup_is_additional_observed_process=True))
        code=child.wait()
    end=time.perf_counter();ended=time.time();fee=common.OUT/'fees'/label
    pending=common.read(fee/'pending_exit_receipt.json')
    assert pending['wrapper_pid']==child.pid and pending['exit_code']==code
    common.write(fee/'receipt.json',dict(pending,outer_seconds_upper=max(pending['outer_seconds_lower'],end-tick,ended-birth),
        actual_exit_observed=True,exit_observed_unix=ended,process_creation_unix=birth,actual_exit_code=code,
        controller_elapsed=end-tick,wrapper_import_creation_trailer_and_exit_included=True,nested_native_seconds_added=False,
        controller_process_count=1,controller_wait_is_nested_not_added_again=True))
    common.write(log/'receipt.json',dict(exit_code=code,seconds=end-tick,budget=common.budget()))
    assert code==0,dict(label=label,exit_code=code)
    if action=='continue':
        pr=common.read(common.OUT/'recovery/group08/prerecord.json')
        assert originals(common.ROOT)==pr['original_P_files']
        records={n:common.sha(common.OUT/'fees'/n/'receipt.json') for n in ['formal08','postseal08a','continue08d1']}
        common.write(common.OUT/'recovery/group08/group_closeout.json',dict(passed=True,all_four_original_positions_valid_once=True,
            original_failed_formal_fee_preserved=True,fee_receipts=records,reaudit_receipt_SHA=common.sha(common.OUT/'recovery/group08/reaudit_receipt.json'),
            independent_adapter_admission_SHA=common.sha(common.OUT/'review/recovery_adapter_admission.json'),
            group_core_SHA=common.sha(common.OUT/'reconstruction/group08/current_core.json'),
            native_arms_produced=4,rerun_producers=0,continued_only_original_ordinal4=True,UTC=common.utc()))
    print(json.dumps(dict(label=label,exit_code=code,budget=common.budget())),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','reaudit','continue']);parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.worker:worker(args.action)
    else:run(args.action)
