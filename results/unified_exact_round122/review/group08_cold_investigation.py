"""Bounded independent read-only investigation of the sealed G08 cold failure.

No production import, native process, new witness, or new bound is generated.
Only this review's receipt and Markdown are written.
"""
from pathlib import Path
from fractions import Fraction
import ast,copy,datetime,hashlib,json,math,re,time,types
import independent_contract_round122 as contract
import independent_qualification_round122 as independent
from independent_review_round122 import read,sha,save_receipt

ROOT=contract.ROOT;OUT=contract.OUT;REVIEW=contract.REVIEW

def hashes(directory):
    return {p.relative_to(directory).as_posix():sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}

def exact_F(p,a,physical):
    ratios=[Fraction(y,d) for y,d in zip(physical['Y'][1:],a['target'][1:])];S=sum(ratios)
    G=sum(abs(x-y) for j,x in enumerate(ratios) for y in ratios[j+1:])/(len(ratios)*S) if S else Fraction(0)
    P=sum(Fraction(str(w))*abs(x-1) for w,x in zip(a['weights'][1:],ratios))
    return G+Fraction(str(p['lambda']))*P

def run():
    tick=time.perf_counter();candidate,bindings=contract.frozen_bindings()
    identity=read(OUT/'campaign/group08/identity.json');launch=next(l for l in identity['launches'] if l['arm']=='P-GRB')
    d=Path(launch['destination']);p=launch['panel'];before=hashes(d)
    failure=OUT/'fees/formal08/failure.txt';failure_SHA=sha(failure)
    assert "assert audited['UB']+1e-7 >= upper" in failure.read_text(encoding='utf-8')
    seal=read(d/'producer_seal.json');producer=read(d/'producer_receipt.json')
    assert producer['producer_seal_SHA']==sha(d/'producer_seal.json')
    assert all(sha(d/n)==h for n,h in seal['required_SHA'].items())
    assert producer['native_stopped_no_reentry'] and producer['required_outputs_closed'] and producer['T_produce']<=3600
    result=read(d/'result.json');completion=read(d/'completion.json');observations=read(d/'observations.json')
    assert completion['returncode']==0 and completion['stop_reason']=='normal_return' and completion['within_cap']
    assert result['process_return_code']==0 and result['process_shutdown_margin_seconds']==30
    assert result['gurobi_optimize_count']==1 and result['gurobi_optimize_return_code']==0 and not result['gurobi_hga_start_requested']
    assert result['gurobi_native_domain_audit_passed'] and result['gurobi_lifecycle_valid'] and result['native_mip_strict_gap_parameters_valid']
    assert result['gurobi_status']==9 and result['status']=='time_limit' and not result['strict_certified_original_problem']
    a=independent.instance(p);witnesses=[];calls=[];bounds=[];returns=[]
    for seq,q in enumerate(observations,1):
        assert q['sequence']==seq
        data=d/'journal'/f'event_{seq}.json';commit=d/'journal'/f'event_{seq}.commit'
        fields=commit.read_text(encoding='ascii').split();raw=data.read_bytes()
        assert fields[0]=='NEJ1' and int(fields[1])==seq and int(fields[3])==len(raw)
        assert fields[4]==sha(data)==q['sha256'] and json.loads(raw)==q['payload']
        assert float(fields[2])==q['data_close_seconds'] and 0<=q['effective_available_seconds']<=3600
        e=q['payload'];kind=e['kind']
        if kind=='witness':
            physical=independent.physical(p,a,e)
            assert abs(physical['G']-e['G'])<1e-7 and abs(physical['P']-e['P'])<1e-7 and abs(physical['F']-e['objective'])<1e-7
            witnesses.append((physical['F'],q,e,physical))
        elif kind=='call':calls.append(e)
        elif kind=='bound':bounds.append(e)
        elif kind=='returned':returns.append(e)
        else:assert kind=='identity',kind
    assert len(witnesses)==156 and len(calls)==len(returns)==1 and returns[0]['return_code']==0
    call=calls[0];assert call['full_original'] and call['model_scope']=='complete_original_compact_milp'
    assert call['lower_g']==0 and call['upper_g']==call['gmax']==.98
    expected=dict(read_return_code=0,Threads=1,Seed=1,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    assert call['settings']==expected and not call['native_preconditions']
    assert len(bounds)==64 and all(not b['global_available'] and b['global_bound'] is None and not b['inconsistent'] for b in bounds)
    assert sha(d/'compact.lp')==call['model_sha256']==p['reference']['canonical_sha256']
    order,model_bounds,types_map,rows,objective=contract.lp_reference(d/'compact.lp')
    assert len(order)==p['reference']['columns']==result['gurobi_num_vars']
    assert len(rows)==p['reference']['rows']==result['gurobi_num_constrs']
    assert result['gurobi_model_fingerprint']==p['reference']['fingerprint']
    assert not any(n=='r120_h' for n in order)
    quantities=[n for n in order if n.startswith(('p_','d_'))]
    assert len(quantities)==400 and all(types_map[n]=='I' for n in quantities)
    log=(d/'native.log').read_text(encoding='utf-8');assert log.count('Optimize a model with ')==1
    printed=re.findall(r'Best objective ([^,]+), best bound ([^,]+), gap',log);assert printed
    assert abs(float(printed[-1][0])-result['gurobi_obj_val'])<=1e-7
    assert abs(float(printed[-1][1])-result['gurobi_obj_bound_c'])<=1e-7
    computed=read(d/'computed_seed_scope.json')
    assert computed['actual_seed']==1 and computed['raw_flags_preserved'] and [x['call'] for x in computed['recovered_calls']]==[1]
    final=independent.physical(p,a,result);best=min(witnesses,key=lambda x:x[0]);observed_upper=best[0]
    assert abs(final['F']-result['upper_bound'])<1e-14
    assert best[1]['sequence']==217 and type(best[2]['improving']) in (bool,int) and best[2]['improving']==1
    assert observed_upper+1e-7<final['F']
    native_L=result['gurobi_obj_bound_c'];assert native_L==result['lower_bound']==max(b['native_bound'] for b in bounds)
    assert all(b['native_bound']<=x[0]+1e-7 for b in bounds for x in witnesses)
    assert native_L<=min(observed_upper,final['F'])+1e-7
    exact_best=exact_F(p,a,best[3]);exact_final=exact_F(p,a,final)
    assert exact_final>exact_best and float(exact_final-exact_best)>1e-7
    # Execute the unchanged actual legacy finalizer in memory to reproduce the
    # fault. Both arguments come from independently reverified sealed fleets.
    source='scripts/round86_native_evidence.py'
    physical_final=dict(final,original_T_feasible=True)
    physical_module=types.SimpleNamespace(ROOT=None,physical=lambda panel,value:copy.deepcopy(physical_final))
    namespace=dict(physical_module=physical_module,math=math,replay_bound=lambda *args:(_ for _ in ()).throw(AssertionError('unexpected raw global promotion')))
    strict=contract.extract(source,'finalize_endpoint',namespace)
    audited=dict(UB=observed_upper,LB=0.,physical_witnesses=156,native_calls_started=1,witnesses=[w[3] for w in witnesses])
    try:strict(ROOT,p,'P-GRB',copy.deepcopy(audited),observations,result,'normal_return',p['reference'])
    except AssertionError:strict_reproduced=True
    else:raise AssertionError('recorded failure not independently reproduced')
    # A memory-only, receipt-specific semantic compatibility guard establishes
    # whether the remainder of the exact legacy finalizer still passes. It does
    # not modify a helper or constitute a completed recovered full arm audit.
    guarded_checks=[]
    def independently_proved_history_guard(history,upper):
        assert history==observed_upper and upper==final['F']
        assert all(x[3]['F']>=0 for x in witnesses) and native_L<=min(history,upper)+1e-7
        assert sha(d/'result.json')==before['result.json'] and sha(d/'observations.json')==before['observations.json']
        guarded_checks.append(dict(observational_history_U=history,unchanged_normal_final_U=upper,
            both_own_fleets_physically_valid=True,native_lower_bound_not_contradicted=True,final_result_not_replaced=True))
        return True
    tree=copy.deepcopy(contract.node(source,'finalize_endpoint'))
    expected_node=ast.parse("assert audited['UB']+1e-7 >= upper").body[0].test
    changed=[0]
    class Compatibility(ast.NodeTransformer):
        def visit_Assert(self,n):
            if ast.dump(n.test,include_attributes=False)==ast.dump(expected_node,include_attributes=False):
                changed[0]+=1
                return ast.copy_location(ast.parse("assert independently_proved_history_guard(audited['UB'],upper)").body[0],n)
            return self.generic_visit(n)
    tree=Compatibility().visit(tree);assert changed==[1]
    guarded_ns=dict(namespace,independently_proved_history_guard=independently_proved_history_guard)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[tree],type_ignores=[])),'review-only receipt-specific R86 semantic check','exec'),guarded_ns)
    checked=copy.deepcopy(audited)
    guarded_ns['finalize_endpoint'](ROOT,p,'P-GRB',checked,observations,result,'normal_return',p['reference'])
    assert checked['endpoint']['U']==result['upper_bound'] and checked['endpoint']['L']==result['lower_bound'] and not checked['endpoint']['certificate']
    assert checked['UB']==observed_upper and len(guarded_checks)==1
    # Source-level producer semantics: observer is read-only and cold final
    # routes are reconstructed from returned native X, not observer best_.
    journal_header=(ROOT/'include/NativeEvidenceJournal.hpp').read_text(encoding='utf-8')
    cpp=(ROOT/'src/GurobiBaseline.cpp').read_text(encoding='utf-8')
    audit_source=(ROOT/'scripts/round114_audit.py').read_text(encoding='utf-8')
    assert 'Read-only, same-run observer' in journal_header and 'double best_' in journal_header
    assert 'GRB_DBL_ATTR_X' in cpp and 'result.upper_bound = result.verification.objective' in cpp
    assert "own_U=physical['F']" in audit_source
    fee=read(OUT/'fees/formal08/receipt.json')
    assert fee['exit_code']==1 and fee['actual_exit_observed'] and fee['actual_native_children']==3 and fee['uncertain_native_children']==0
    unstarted=next(l for l in identity['launches'] if l['arm']=='MB-D1')
    assert not Path(unstarted['destination']).exists() and not (OUT/'fees/formal08/04_before.json').exists()
    preserved=[]
    for arm in ['M-B','ENS-C']:
        old=next(l for l in identity['launches'] if l['arm']==arm);od=Path(old['destination'])
        pr=read(od/'producer_receipt.json');total=read(od/'arm_total_receipt.json');au=read(od/'audit.json')
        assert au['passed'] and au['native_proof_qualified'] and pr['producer_seal_SHA']==sha(od/'producer_seal.json')
        assert total['producer_receipt_SHA']==sha(od/'producer_receipt.json')
        preserved.append(dict(arm=arm,producer_receipt_SHA=sha(od/'producer_receipt.json'),total_SHA=sha(od/'arm_total_receipt.json')))
    contract.frozen_bindings();assert hashes(d)==before and sha(failure)==failure_SHA
    result_receipt=dict(decision='READ_ONLY_LEGACY_AUDITOR_MISMATCH_SUPPORTED',scope='Independent investigation only; not recovered-arm or all32/all48 admission.',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='independent executor /root/contract_review',script_SHA=sha(__file__),
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),frozen_bindings=bindings,
        input_SHA=p['input_sha256'],PE_SHA=contract.PE_SHA,result_SHA=before['result.json'],observations_SHA=before['observations.json'],
        producer_receipt_SHA=before['producer_receipt.json'],producer_seal_SHA=before['producer_seal.json'],failed_audit_SHA=before['audit.json'],failure_txt_SHA=failure_SHA,
        original_all_P_file_SHA=before,all_original_P_bytes_and_failure_preserved=True,
        physically_replayed_own_witnesses=156,best_committed_witness=dict(sequence=217,available_seconds=best[1]['effective_available_seconds'],
            event_JSON_SHA=sha(d/'journal/event_217.json'),commit_SHA=sha(d/'journal/event_217.commit'),
            G=best[3]['G'],P=best[3]['P'],F=observed_upper,Y=best[3]['Y'],fleet=best[3]['fleet'],exact_F=str(exact_best)),
        unchanged_final_own_result=dict(G=final['G'],P=final['P'],F=final['F'],Y=final['Y'],fleet=final['fleet'],exact_F=str(exact_final)),
        final_minus_best_physical_U=final['F']-observed_upper,exact_difference=str(exact_final-exact_best),
        original_assertion='audited history UB + 1e-7 >= final result U',original_assertion_independently_reproduced=strict_reproduced,
        semantics='R86 assumes final native-result physical U dominates all read-only MIPSOL physical witnesses. Frozen R114 own_U is final physical result. Two valid physical upper bounds need not have that ordering; neither is a lower-bound counterexample.',
        native_lower_bound=native_L,all64_bounds_below_every_committed_own_witness=True,actual_calls=1,actual_successful_returns=1,
        actual_model=dict(SHA=sha(d/'compact.lp'),rows=len(rows),columns=len(order),quantities_integer=400,full_original=True,no_D1_selector=True),
        raw_Seed1_global_flags_preserved=True,Seed1_actual_settings=expected,producer_T_produce=producer['T_produce'],
        original_legacy_prefix_failure_and_memory_only_semantic_suffix_test=dict(strict_failed=True,guarded_prefix_and_remaining_checks_passed=True,
            guard=guarded_checks,endpoint_U=checked['endpoint']['U'],endpoint_L=checked['endpoint']['L'],endpoint_certificate=False),
        original_MB_ENS_closeouts_preserved=preserved,original_formal08_failed_fee_SHA=sha(OUT/'fees/formal08/receipt.json'),
        original_formal08_outer_seconds=fee['outer_seconds_upper'],last_D1_explicitly_never_started=True,
        recovery_conditions=[
            'Preserve the original failed audit, all raw/models/journals/logs, producer receipts/seals and formal08 fee. Never rerun an already valid producer or select a better Seed/window.',
            'Retain final result U=0.39178055857928196, L=0.34945085964584033, certificate=False and original T_produce exactly. Keep seq217 observational U separate; do not replace the frozen final endpoint by it.',
            'Use a bound, reviewed read-only compatibility adapter for this proven history/final distinction. Verify both own physical fleets, actual original full-model scope, all bound/witness inequalities, Seed/settings, native returns and every other inherited audit predicate. Do not simply delete an assertion.',
            'Write fresh derived audit/closeout/clock sidecars in a distinct recovery view, preserving old failed files. Bind original producer identity and recovery helper identity. Re-run the complete affected pure audit and reader from unchanged sealed evidence.',
            'Keep original T_produce; extend T_verify/T_total to the actual new verification end, including the waiting interval. Charge new outer verification work once; never re-add historical native time.',
            'Only after affected pure audit and coherent group identity/view pass, pre-record continuation of the sole never-started original ordinal4 D1 at Seed1/cap3600/identical frozen PE+argv/environment, with its own full H/LP/Start/proofs paid, startup/imports included, capacity admission and complete remaining budget.',
            'The all32/all48 independent post-formal review, final stage, public restore and safe cleanup remain pending.'
        ],
        limitations=['No native lower bound was resolved again. This establishes no observed same-domain numerical contradiction among the sealed witnesses and native claims; it is not a rational certificate of the open optimum.',
            'The memory-only semantic finalizer test is not a completed recovered whole-arm audit or authorization to change production/model/parameters. Exact internal reason the native-return fleet differs from a prior callback fleet is not inferred.'],
        native_starts=0,Optimize=0,production_or_measured_helper_edits=0,raw_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('group08_cold_investigation.json',result_receipt)
    text='\n'.join(['# Independent group08 cold P-GRB audit-failure investigation','',
        '**Finding: a read-only legacy-auditor mismatch is supported; no same-domain lower-bound counterexample was found.** This is an investigation, not a completed recovery or final performance review.','',
        'All 156 original committed physical fleets and the final result fleet independently pass service direction/integrality, inventory, assigned-Q prefix/return loads and original time checks. Best own observed event217 has F=0.391713327901773; the unchanged final native-result fleet has F=0.39178055857928196. The exact positive difference is '+str(exact_final-exact_best)+' (about 6.72307e-5), so the 1e-7 assertion failure is real and not hidden by rounding.','',
        'Every one of the 64 native lower bounds, including final L=0.34945085964584033, stays below both physical upper bounds. The actual single returned call uses the original cold compact model, Seed1 and frozen settings; model/reference/log/source identities agree and no D1 selector or Start is present.','',
        'The failing R86 assertion enforces an ordering between an observational history minimum and the final native-result physical upper bound. The frozen R114 reader explicitly defines own_U from the final result fleet. The journal is a read-only observer and the cold producer reconstructs its final result from returned native X. A valid earlier observed physical fleet can give a stronger U than that final result without contradicting a native lower bound. Internal native acceptance/branch behavior is not inferred.','',
        'The unchanged original finalizer was actually executed in memory and reproduced the failure. A receipt-specific semantic guard, checking independently proved feasible U values and all lower-bound inequalities while retaining the exact final result, allowed all remaining original finalizer checks to pass. No measured helper was edited and this does not substitute for the required complete recovered audit.','',
        'Protocol-compliant recovery must preserve every original failure/raw/fee, use a separately bound read-only recovery view, retain final U/L/certificate and T_produce exactly, retain the full waiting gap in T_verify/T_total, and rerun no producer. A separately recorded continuation may then fill only the never-started original D1 position with the unchanged role/Seed/argv/PE/environment and full own work/fees. Full32/all48, final stage, restore and cleanup remain pending.',''])
    with (REVIEW/'group08_cold_investigation.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)

if __name__=='__main__':run()
