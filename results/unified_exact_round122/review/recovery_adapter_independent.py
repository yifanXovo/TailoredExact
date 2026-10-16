"""Bounded independent admission of the sealed G08 read-only recovery.

Only this review's JSON/Markdown are written. No verifier is rerun, no native
process is created, and original producers/failed files stay unchanged.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,importlib.util,json,os,sys,time,types
import independent_contract_round122 as contract
import independent_qualification_round122 as physical
from independent_review_round122 import read,sha,save_receipt
from group08_cold_investigation import hashes,exact_F

ROOT=contract.ROOT;OUT=contract.OUT;REVIEW=contract.REVIEW
OLD='a4b94e891fba441df4ae9f14300add80388e8d4af4f1a4bbc37a99414cf2c644'
CURRENT='bb97d9e525f2705b48325d27618921c0cafacded89c8ce11eeb6150344f1b60d'

def dump(node):return ast.dump(node,include_attributes=False)
def tree(path):return ast.parse(path.read_text(encoding='utf-8-sig'))
def funcs(t):return {n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def reject(action):
    try:action()
    except AssertionError:return
    raise AssertionError('negative case unexpectedly accepted')

def review():
    tick=time.perf_counter();candidate,binding=contract.frozen_bindings()
    source=ROOT/'scripts/round122_group08_recovery.py'
    old=OUT/'engineering/recovery_adapter_v1.py'
    assert sha(source)==CURRENT and sha(old)==OLD
    pr_path=OUT/'recovery/group08/prerecord.json';pr=read(pr_path)
    rr_path=OUT/'recovery/group08/reaudit_receipt.json';rr=read(rr_path)
    rev_path=OUT/'recovery/group08/continuation_revision.json';rev=read(rev_path)
    assert pr['script_SHA']==rr['script_SHA']==rev['previous_script_SHA']==OLD
    assert rev['script_SHA']==CURRENT and rev['prerecord_SHA']==rr['prerecord_SHA']==sha(pr_path)
    assert rev['reaudit_receipt_SHA']==sha(rr_path)
    before=funcs(tree(old));now=funcs(tree(source))
    equal=[name for name in before if dump(before[name])==dump(now[name])]
    assert equal==rev['all_other_functions_AST_identical']
    assert set(before)==set(now) and set(before)-set(equal)=={'run','continuation'}
    # Reconstruct the exact two allowed changes independently.
    old_cont=copy.deepcopy(before['continuation']);new_cont=copy.deepcopy(now['continuation'])
    start=next(k for k,n in enumerate(old_cont.body) if isinstance(n,ast.Assert) and "pr['script_SHA']" in ast.unparse(n))
    assert ast.unparse(old_cont.body[start])=="assert accepted['decision'] == 'ACCEPT' and accepted['script_SHA'] == common.sha(__file__) == pr['script_SHA']"
    inserted=new_cont.body[start:start+3]
    expected=ast.parse("revision=common.read(out/'recovery/group08/continuation_revision.json')\nassert revision['previous_script_SHA']==pr['script_SHA'] and revision['prerecord_SHA']==common.sha(out/'recovery/group08/prerecord.json')\nassert accepted['decision']=='ACCEPT' and accepted['script_SHA']==common.sha(__file__)==revision['script_SHA']").body
    assert [dump(n) for n in inserted]==[dump(n) for n in expected]
    new_cont.body[start:start+3]=[old_cont.body[start]]
    assert dump(new_cont)==dump(old_cont)
    old_run=copy.deepcopy(before['run']);new_run=copy.deepcopy(now['run'])
    old_with=next(n for n in old_run.body if isinstance(n,ast.With))
    new_with=next(n for n in new_run.body if isinstance(n,ast.With))
    assert len(new_with.body)==2 and isinstance(new_with.body[1],ast.Try)
    protected=new_with.body[1]
    assert not protected.orelse and not protected.finalbody
    assert [dump(n) for n in protected.body]==[dump(n) for n in old_with.body[1:]]
    frozen=funcs(tree(ROOT/'scripts/round122_runner.py'))['run']
    frozen_handler=next(n for n in ast.walk(frozen) if isinstance(n,ast.ExceptHandler))
    assert len(protected.handlers)==1 and dump(protected.handlers[0])==dump(frozen_handler)
    new_with.body=new_with.body[:1]+protected.body
    assert dump(new_run)==dump(old_run)
    # All top-level imports, constants and the main entry point are unchanged.
    residual=lambda t:[dump(n) for n in t.body if not isinstance(n,ast.FunctionDef)]
    assert residual(tree(old))==residual(tree(source))
    # Independently count/reverse the one permitted assertion in the actual R86 AST.
    original=contract.node('scripts/round86_native_evidence.py','finalize_endpoint')
    target=ast.parse("assert audited['UB']+1e-7 >= upper").body[0]
    replacements=[n for n in ast.walk(original) if isinstance(n,ast.Assert) and dump(n)==dump(target)]
    assert len(replacements)==1
    sys.path.insert(0,str(ROOT/'scripts'))
    spec=importlib.util.spec_from_file_location('reviewed_round122_recovery',source)
    recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
    modified,equivalence=recovery.source_equivalence(ROOT)
    replacement=ast.parse('assert _r122_history_guard(root,panel,arm,audited,records,result,upper)').body[0]
    found=[]
    class Reverse(ast.NodeTransformer):
        def visit_Assert(self,n):
            if dump(n)==dump(replacement):found.append(1);return copy.deepcopy(target)
            return self.generic_visit(n)
    assert dump(Reverse().visit(copy.deepcopy(modified)))==dump(original) and found==[1]
    assert equivalence==rr['evidence']['equivalence']==pr['equivalence']
    # Exact producer, source closure, failed fee and original file preservation.
    launch,identity=recovery.check_scope(ROOT);d=Path(launch['destination']);panel=launch['panel']
    original_hashes=hashes(d);assert original_hashes==pr['original_P_files']
    investigation=read(OUT/'review/group08_cold_investigation.json')
    assert original_hashes==investigation['original_all_P_file_SHA']
    assert sha(OUT/'candidate_identity.json')==pr['candidate_identity_SHA']==investigation['candidate_identity_SHA']
    for name,h in pr['retained_failed_attempt_files'].items():assert sha(OUT/name)==h
    seal=read(d/'producer_seal.json');producer=read(d/'producer_receipt.json')
    assert all(sha(d/n)==h for n,h in seal['required_SHA'].items())
    assert producer['producer_seal_SHA']==sha(d/'producer_seal.json')
    assert pr['T_produce']==rr['T_produce']==producer['T_produce']
    failed=read(OUT/'fees/formal08/receipt.json');fee=read(OUT/'fees/postseal08a/receipt.json')
    assert failed['exit_code']==1 and failed['actual_exit_observed'] and failed['actual_native_children']==3 and failed['uncertain_native_children']==0
    assert fee['exit_code']==fee['actual_exit_code']==0 and fee['actual_exit_observed'] and fee['actual_native_children']==fee['uncertain_native_children']==0
    assert fee['outer_seconds_upper']>=fee['exit_observed_unix']-fee['process_creation_unix']
    assert rr['passed'] and rr['Optimize']==rr['native_starts']==0
    view=OUT/'recovery/group08/p_sidecars'
    assert set(rr['derived_recovery_sidecars'])=={p.name for p in view.iterdir() if p.is_file()}
    assert set(rr['derived_recovery_sidecars'])<=recovery.SIDECARS
    for n,h in rr['derived_recovery_sidecars'].items():assert sha(view/n)==h
    audit=read(view/'audit.json');own=read(view/'independent_evidence.json')
    close=read(view/'verification_closeout.json');total=read(view/'arm_total_receipt.json')
    assert audit['passed'] and audit['native_proof_qualified'] and audit['independent_evidence_audit_passed']
    assert close['necessary_verification_complete'] and close['native_proof_qualified'] and close['no_new_solution_or_certificate_backfilled']
    for key,n in [('audit_SHA','audit.json'),('own_evidence_SHA','independent_evidence.json'),('claims_SHA','native_claims.json'),('rejection_SHA','claim_rejections.json'),('metrics_SHA','audit_execution_metrics.json')]:assert close[key]==sha(view/n)
    assert close['producer_receipt_SHA']==total['producer_receipt_SHA']==sha(d/'producer_receipt.json')
    assert total['verification_closeout_SHA']==sha(view/'verification_closeout.json')
    assert total['T_verify']==total['t_verified_perf']-producer['t_produce_perf']==rr['T_verify']
    assert abs(total['T_total']-producer['T_produce']-total['T_verify'])<1e-8
    assert abs(total['T_total']-(total['t_verified_perf']-producer['t0_perf']))<1e-8
    assert total['t_verified_unix']>failed['exit_observed_unix'] and rr['T_verify']>900
    assert abs(total['t_verified_unix']-producer['t_produce_unix']-total['T_verify'])<.001
    assert total['T_total']==rr['T_total']
    rejection=read(view/'claim_rejections.json')
    assert rejection['rejections']==rejection['damaged_calls']==[] and rejection['order_independent']
    # Fresh independent replay of all historical fleets and the retained final.
    observations=read(d/'observations.json');result=read(d/'result.json');a=physical.instance(panel)
    fleets=[physical.physical(panel,a,q['payload']) for q in observations if q['payload']['kind']=='witness']
    final=physical.physical(panel,a,result);minimum=min(x['F'] for x in fleets)
    assert len(fleets)==156 and minimum==recovery.HISTORY_U and final['F']==recovery.FINAL_U
    assert exact_F(panel,a,final)>min(exact_F(panel,a,x) for x in fleets)
    bounds=[q['payload'] for q in observations if q['payload']['kind']=='bound']
    assert len(bounds)==64 and max(x['native_bound'] for x in bounds)==recovery.FINAL_L
    assert all(x['native_bound']<=f['F']+1e-7 for x in bounds for f in fleets+[final])
    assert own['own_U']==audit['endpoint']['U']==rr['final_U']==result['upper_bound']==final['F']
    assert audit['endpoint']['L']==rr['final_L']==result['lower_bound']==recovery.FINAL_L
    assert audit['endpoint']['certificate'] is rr['certificate'] is False
    assert audit['UB']==minimum and audit['endpoint']['U']!=minimum
    # Actual read routing and exact retained finalizer execution; no files written.
    outside=read(d/'audit.json');old_open,old_stat=Path.open,Path.stat;old_finalize=recovery.native.finalize_endpoint
    with recovery.evidence_view(ROOT) as scope:
        assert read(d/'audit.json')==audit and sha(d/'audit.json')==sha(view/'audit.json')
        assert read(d/'result.json')==result and sha(d/'result.json')==original_hashes['result.json']
        assert (d/'arm_total_receipt.json').is_file()
        checked=dict(UB=minimum,LB=0.,physical_witnesses=156,native_calls_started=1,witnesses=copy.deepcopy(fleets))
        recovery.native.finalize_endpoint(ROOT,panel,'P-GRB',checked,observations,result,'normal_return',panel['reference'])
        assert checked['endpoint']==audit['endpoint'] and len(scope['semantic_guard_checks'])==1
    assert Path.open is old_open and Path.stat is old_stat and recovery.native.finalize_endpoint is old_finalize
    assert read(d/'audit.json')==outside and sha(d/'audit.json')==original_hashes['audit.json']
    # Mutated roles, hashes, endpoints and raw observations are rejected before
    # any compatibility success. No alternate data are added to the evidence.
    guard_args=(ROOT,panel,'P-GRB',audit,observations,result,result['upper_bound'],[])
    negatives=[]
    for label,change in [('arm',lambda x:x.__setitem__(2,'ENS-C')),('seed',lambda x:x[1].__setitem__('gurobi_seed',0)),('input',lambda x:x[1].__setitem__('input_sha256','0'*64)),('result',lambda x:x[5].__setitem__('upper_bound',minimum)),('observations',lambda x:x[4][0].__setitem__('sequence',0)),('observational_UB',lambda x:x[3].__setitem__('UB',final['F']))]:
        args=copy.deepcopy(list(guard_args));change(args);reject(lambda:recovery.history_guard(*args));negatives.append(label)
    # In-memory routing mode checks cannot open or change actual raw paths.
    view_node=now['evidence_view'];nested={n.name:n for n in ast.walk(view_node) if isinstance(n,ast.FunctionDef)}
    raw_key=os.path.normcase(os.path.abspath(d));mapping={os.path.normcase(os.path.abspath(d/n)):view/n for n in recovery.SIDECARS}
    routing_calls=[]
    ns=dict(os=os,raw_key=raw_key,mapping=mapping,writing=False,original_open=lambda *args,**kw:routing_calls.append((args,kw)))
    for n in [nested['key'],nested['routed_open']]:exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(n)],type_ignores=[])),'independent in-memory route check','exec'),ns)
    for n in ['audit.json','result.json','new/unmapped.json']:
        for mode in ['w','a','x','r+','wb']:
            reject(lambda n=n,mode=mode:ns['routed_open'](d/n,mode))
    assert not routing_calls
    ns['writing']=True;ns['routed_open'](d/'audit.json','w');assert routing_calls[-1][0][0]==view/'audit.json'
    reject(lambda:ns['routed_open'](d/'result.json','w'))
    # Continuation is the exact unstarted original ordinal4, with fresh producer
    # wrapper origin and unchanged frozen execute/LP/H/Start/search path.
    last=identity['launches'][3];assert last==pr['continuation']['launch']
    assert last['arm']=='MB-D1' and last['number']==4 and last['seed']==1 and last['panel']['cap_seconds']==3600
    assert not Path(last['destination']).exists() and not (OUT/'fees/formal08/04_before.json').exists()
    assert not (OUT/'fees/continue08d1').exists()
    assert pr['continuation']['cap_seconds']==3600 and pr['continuation']['management_reservation']==120
    continuation=ast.unparse(now['continuation'])
    assert 'campaign.execute(l, i, tick, birth)' in continuation and "common.fee_begin('continue08d1', 1, 3720" in continuation
    assert 'tick, creation = process_origin()' in ast.unparse(funcs(tree(ROOT/'scripts/round122_common.py'))['fee_begin'])
    budget=recovery.common.budget();assert not budget['unclosed'] and budget['remaining_outer_seconds']>3720
    contract.frozen_bindings();assert hashes(d)==original_hashes
    for name,h in pr['retained_failed_attempt_files'].items():assert sha(OUT/name)==h
    receipt=dict(decision='ACCEPT',scope='Exact sealed P read-only recovery adapter and sole never-started ordinal4 continuation admission; all32/all48 review remains pending.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        script_SHA=sha(source),reaudit_receipt_SHA=sha(rr_path),review_script_SHA=sha(__file__),
        previous_adapter_SHA=sha(old),prerecord_SHA=sha(pr_path),continuation_revision_SHA=sha(rev_path),
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),frozen_bindings=binding,
        single_assertion_reverse_AST_verified=True,other_legacy_finalizer_AST_retained=True,
        actual_reaudit_with_original_v1_verified=True,all9_audit_view_functions_AST_unchanged=True,
        changed_only_reviewed_owned_child_cleanup_and_identity_transition=True,
        owned_child_cleanup_AST_equal_to_frozen_runner=True,actual_read_route_and_restore_verified=True,
        negative_scope_cases=negatives,in_memory_immutable_raw_write_cases=15,
        original_all_P_file_hashes_unchanged=True,original_failure_and_fee_hashes_unchanged=True,
        original_P_producer_receipt_SHA=sha(d/'producer_receipt.json'),derived_sidecar_SHA=rr['derived_recovery_sidecars'],
        own_final_U=final['F'],own_final_L=recovery.FINAL_L,certificate=False,observational_U=minimum,
        independently_replayed_witnesses=156,independently_checked_native_bounds=64,
        final_endpoint_not_reselected=True,no_new_solution_bound_or_observation=True,
        T_produce=producer['T_produce'],T_verify=total['T_verify'],T_total=total['T_total'],
        original_monotonic_failure_and_wait_gap_retained=True,readonly_outer_seconds=fee['outer_seconds_upper'],
        continued_original_ordinal=4,D1_not_started_at_admission=True,continuation_launch=last,
        wrapper_OS_birth_and_import_in_D1_Tproduce=True,fee_cap=3720,remaining_outer=budget['remaining_outer_seconds'],
        producer_metadata_note='Frozen ordinal4 producer receipt first_arm flag remains false; recovery 04_before and actual tick explicitly bind continuation wrapper creation/import into this D1 producer clock.',
        limitations=['Original P is a qualified open numerical result, not an optimality certificate.',
            'This admission does not attest a future continuation outcome or all32/all48 stage; those require sealed evidence and independent final review.'],
        native_starts=0,Optimize=0,raw_or_measured_helper_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('recovery_adapter_admission.json',receipt)
    text='\n'.join(['# Independent recovery adapter admission','',
        '**ACCEPT** for the exact hash-bound read-only recovery and original never-started ordinal4 continuation. This is not the pending all32/all48 review.','',
        'The actual successful re-audit remains bound to preserved v1 source '+OLD+'. Current continuation source '+CURRENT+' differs only in the reviewed owned-child exception cleanup and explicit old/new identity transition; all nine audit/view functions retain their exact AST. The original finalizer differs at exactly one assertion and reverse reconstruction reproduces every other AST node.','',
        'All original P files and the failed audit/fee are unchanged. The 12 derived sidecars are separate; actual read routing selects them only in context and restores the original failed audit afterward. In-memory write-mode negatives and six hash/scope/data mutations are rejected.','',
        'Fresh independent physical math passes all 156 committed own fleets and the final fleet; all 64 lower bounds remain below them. The frozen final U=0.39178055857928196 and L=0.34945085964584033 remain an open result; historical U=0.391713327901773 is retained only as observational evidence. No result was selected again.','',
        'Original T_produce='+str(producer['T_produce'])+', T_verify='+str(total['T_verify'])+', T_total='+str(total['T_total'])+' seconds. Verification runs from the original monotonic producer seal through actual re-audit completion, retaining the failed-audit and waiting gap. The separately closed re-audit fee is '+str(fee['outer_seconds_upper'])+' seconds, with zero native starts.','',
        'Only the unchanged ordinal4 D1 Seed1 cap3600 remains authorized for continuation. Its destination and launch are absent at admission, fresh wrapper OS creation/import time enters its own T_produce, owned-child cleanup matches the frozen runner, and the remaining outer budget exceeds the cap3720 reservation. All future performance, final stage and restoration claims remain pending.',''])
    with (REVIEW/'recovery_adapter_admission.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)

if __name__=='__main__':review()
