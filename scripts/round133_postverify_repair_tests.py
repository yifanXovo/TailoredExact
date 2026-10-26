"""Finite zero-native fixtures for the post-seal actual-H handoff amendment.

Synthetic folders exercise only the named pure helper predicates; they are not
producer evidence and never qualify a scientific arm or a performance result.
The real first arm is read, without invoking verify or changing any of its files.
"""
from round133_common import *
import copy, inspect
import round133_postverify_repair as repair

def main():
    tick=time.perf_counter();parent=OUT/'qualification/postverify_handoff_repair'
    parent.mkdir(parents=True,exist_ok=True)
    folder=parent/f'attempt_{len(list(parent.glob("attempt_*")))+1:02d}'
    folder.mkdir(exist_ok=False);checks=[]
    def check(name,predicate):
        assert predicate,name
        checks.append(dict(name=name,passed=True))
    def rejects(name,fn):
        try:fn()
        except (AssertionError,FileNotFoundError,KeyError):
            checks.append(dict(name=name,passed=True));return
        raise AssertionError(name+' incorrectly accepted')
    bindings=repair.amendment_bindings()
    check('all_original_frozen_helpers_have_exact_original_SHA',bindings['frozen_helpers']==repair.FROZEN)
    before,after=repair.reconstruction_source()
    expected="selection=repair_selection(root,p,d)\n    final=selection['accepted_witness'];physical=selection['accepted_physical']"
    original="final=read(base/'final.json');physical=core.full_fleet(root,p,final)"
    check('only_endpoint_initialization_changes_in_reconstruct_clone',after.replace(expected,original)==before)
    check('frozen_verify_code_itself_is_unchanged',repair._VERIFY is repair.reader.verify)
    check('PS_lifecycle_uses_the_same_compact_Start_audit_module',repair.reader.old_ps.inherited is repair.reader.compact_start)
    check('tie_stays_with_initial',repair.accepted_endpoint(1.,1.)=='initial.json')
    check('strict_improvement_selects_final',repair.accepted_endpoint(1.,.9)=='final.json')
    check('subthreshold_improvement_stays_with_initial',repair.accepted_endpoint(1.,1.-.5e-10)=='initial.json')
    threshold=1.-1e-10
    check('exact_binary64_subtraction_boundary_is_not_strict',repair.accepted_endpoint(1.,threshold)=='initial.json')
    check('next_binary64_below_boundary_is_strict',repair.accepted_endpoint(1.,math.nextafter(threshold,-math.inf))=='final.json')
    rejects('nonfinite_initial_rejected',lambda:repair.accepted_endpoint(math.nan,1.))
    rejects('nonfinite_final_rejected',lambda:repair.accepted_endpoint(1.,math.inf))
    cold=repair.handoff_receipt(ROOT,dict(arm='P-GRB'),folder/'no_H_folder_exists')
    check('cold_P_never_reads_nonexistent_H_artifacts',cold['effective_adapter_H_applied'] is False)
    check('cold_P_has_explicit_null_H_and_exchange_receipt_fields',all(cold[name] is None for name in
        ('accepted_H_selection','accepted_H_fleet','exchange_final_fleet','exchange_final_physical')))
    # Physically valid distinct capacity-assigned fleets with equal objective.
    # These are helper fixtures, not an actual exchange trace or producer run.
    unit=folder/'synthetic_helper_only';unit.mkdir()
    inp=unit/'input.txt'
    inp.write_text('2 2 [1,2]\ncapacities = [100000,2,2]\ninitial = [50000,1,0]\ntarget = [0,1,1]\nweights = [0,1,1]\nmin_ratio = [0,0,0]\npoints = [(0,0),(0,0),(0,0)]\n',encoding='utf-8')
    p=dict(input_path=str(inp),instance_path=str(inp),input_sha256=sha(inp),V=2,M=2,Q_vector=[1,2],
        T_seconds=240,pickup_seconds=60,drop_seconds=60,**{'lambda':1.})
    initial=dict(F=1.5,routes=[dict(vehicle=0,nodes=[0,1,2,0],operations=[[1,1,0],[2,0,1]])])
    final=dict(F=1.5,routes=[dict(vehicle=1,nodes=[0,1,2,0],operations=[[1,1,0],[2,0,1]])])
    third=dict(F=1.5,routes=[])
    ex=unit/'hga.csv.exchange';ex.mkdir()
    write(ex/'initial.json',initial);write(ex/'final.json',final)
    (unit/'hga.csv.descent.csv').write_text('seed,interrupted\n'+''.join(f'{i},0\n' for i in range(1,26)),encoding='utf-8')
    selected=repair.select_exchange(ROOT,p,unit)
    check('physical_tie_different_capacity_fleets_are_not_interchangeable',selected['accepted_fleet']!=selected['exchange_final_fleet'])
    check('physical_tie_selects_exact_initial_fleet',selected['selection']['accepted_snapshot']=='initial.json')
    reconstructed=repair.reconstruct_accepted(ROOT,p,unit)
    check('complete_25_seed_predicate_preserved',reconstructed['complete'] and reconstructed['seed_ids']==list(range(1,26)))
    check('accepted_fleet_and_distinct_real_exchange_final_are_both_retained',reconstructed['fleet']==selected['accepted_fleet'] and reconstructed['exchange_final_fleet']==selected['exchange_final_fleet'])
    check('semantic_trace_retains_actual_final_snapshot',reconstructed['semantic_traces']['exchange/final.json']==repair.reader.startup.semantic(read(ex/'final.json')))
    write(unit/'result.json.round112.startup.json',initial)
    check('PS_actual_accepted_initial_handoff_passes',repair.assert_startup_handoff(ROOT,p,unit)['exact_capacity_assigned_fleet_equal'])
    write(unit/'result.json.round112.startup.json',final)
    rejects('PS_unaccepted_neutral_final_handoff_rejected',lambda:repair.assert_startup_handoff(ROOT,p,unit))
    write(unit/'result.json.round112.startup.json',third)
    rejects('PS_third_same_objective_fleet_rejected',lambda:repair.assert_startup_handoff(ROOT,p,unit))
    rejects('reconstruct_PS_startup_must_also_match_accepted_fleet',lambda:repair.reconstruct_accepted(ROOT,p,unit))
    write(unit/'result.json.round112.startup.json',initial)
    (unit/'hga.csv.descent.csv').write_text('seed,interrupted\n'+''.join(f'{i},0\n' for i in range(1,25)),encoding='utf-8')
    check('missing_H_seed_still_incomplete',not repair.reconstruct_accepted(ROOT,p,unit)['complete'])
    (unit/'hga.csv.descent.csv').write_text('seed,interrupted\n'+''.join(f'{i},0\n' for i in range(1,26)),encoding='utf-8')
    # A physically valid strict improvement: pickup/loaded-return removes the
    # sole station item (F=2); no-op retains it (F=3/2).
    strict_initial=dict(F=2.,routes=[dict(vehicle=0,nodes=[0,1,0],operations=[[1,1,0]])])
    write(ex/'initial.json',strict_initial);write(ex/'final.json',third)
    write(unit/'result.json.round112.startup.json',third)
    check('physical_strict_final_handoff_passes',repair.reconstruct_accepted(ROOT,p,unit)['accepted_H_selection']['accepted_snapshot']=='final.json')
    write(unit/'result.json.round112.startup.json',strict_initial)
    rejects('PS_strict_improvement_cannot_keep_prior_initial',lambda:repair.assert_startup_handoff(ROOT,p,unit))
    # No H or Start function changes during the producer-visible deferred entry.
    old_h=repair.reader.startup.reconstruct;old_s=repair.reader.compact_start.start_audit
    with repair.deferred_verifier('fixture_no_invocation'):
        check('deferred_entry_does_not_patch_producer_H_or_PS',repair.reader.startup.reconstruct is old_h and repair.reader.compact_start.start_audit is old_s)
    check('deferred_entry_restores_original_verify',repair.reader.verify is repair._VERIFY)
    rejects('unsealed_postverification_context_rejected',lambda:repair.postseal_functions(unit,unit/'new_failure.json').__enter__())
    write(unit/'producer_seal.json',dict(native_stopped_no_reentry=True,helper_fixture_only=True))
    write(unit/'producer_receipt.json',dict(native_stopped_no_reentry=True,producer_seal_SHA=sha(unit/'producer_seal.json')))
    failure=unit/'round133_verification_failure.json';write(failure,dict(original_failure=True));failure_SHA=sha(failure)
    with repair.postseal_functions(unit,unit/'repair_failure.json'):
        check('H_and_PS_install_only_inside_linked_stopped_postseal_context',repair.reader.startup.reconstruct is repair.reconstruct_accepted and repair.reader.compact_start.start_audit is repair.start_audit_accepted)
        repair.reader.write(failure,dict(repair_failure=True))
    check('failure_redirect_preserves_original_failure_bytes',sha(failure)==failure_SHA and read(unit/'repair_failure.json')['repair_failure'])
    check('postseal_context_restores_all_pure_functions',repair.reader.startup.reconstruct is old_h and repair.reader.compact_start.start_audit is old_s and repair.reader.write is repair._WRITE)
    # A sealed scientific endpoint is never accepted/skipped/aggregated solely
    # because the original verifier wrote its closeout. Test only this helper
    # with explicit synthetic management inputs, not a frozen matrix position.
    management=folder/'synthetic_management_only';management.mkdir()
    attempts=management/'attempts';attempts.mkdir();managed=management/'closed';managed.mkdir()
    for name in ('audit.json','verification_closeout.json','arm_total_receipt.json','round133_endpoint.json','producer_receipt.json','producer_seal.json'):
        write(managed/name,dict(management_fixture_only=True,name=name))
    mg_launch=dict(arm='P-GRB',destination=str(managed));mg_gate=dict(helper_fixture_gate_only=True)
    mg_attempt=attempts/'one';mg_attempt.mkdir()
    mg_binding=dict(launch=mg_launch,identity_SHA='helper-fixture-identity',gate=mg_gate,
        adapter_SHA=sha(repair.__file__),reader_SHA=repair.FROZEN['scripts/round133_read.py'],
        original_verify_source_SHA=hashlib.sha256(inspect.getsource(repair._VERIFY).encode()).hexdigest(),old_failure_SHA=None,
        producer_receipt_SHA=sha(managed/'producer_receipt.json'),producer_seal_SHA=sha(managed/'producer_seal.json'))
    write(mg_attempt/'binding.json',mg_binding)
    validate=lambda:repair.validate_effective_receipt(managed,mg_launch,'helper-fixture-identity',mg_gate,attempts)
    rejects('closeout_without_success_cannot_skip_or_aggregate',validate)
    mg_success=dict(passed=True,binding_SHA=sha(mg_attempt/'binding.json'),Optimize=0,native_starts=0,
        old_failure_preserved=True,original_producer_seal_preserved=True,
        outputs={name:sha(managed/name) for name in ('audit.json','verification_closeout.json','arm_total_receipt.json','round133_endpoint.json')},
        **repair.handoff_receipt(ROOT,mg_launch,managed))
    write(mg_attempt/'success.json',mg_success)
    check('complete_bound_management_receipt_accepts_only_its_exact_outputs',validate()['success_SHA']==sha(mg_attempt/'success.json'))
    write(managed/'round133_endpoint.json',dict(changed_management_fixture=True))
    rejects('changed_endpoint_after_success_cannot_skip_or_aggregate',validate)
    run_source=inspect.getsource(repair.run);rebuild_source=inspect.getsource(repair.rebuild)
    check('run_skip_and_rebuild_both_invoke_the_effective_policy_gate',
        'validate_management_group(group,effective_gate)' in run_source and 'validate_management_group(group,gate)' in rebuild_source)
    # Read the actual failed arm once, retaining every producer/failed-audit file.
    identity=read(OUT/'campaign/D1_01/identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    raw_before={name:sha(d/name) for name in ['producer_seal.json','producer_receipt.json','observations.json','round133_verification_failure.json','hga.csv.exchange/initial.json','hga.csv.exchange/final.json']}
    actual=repair.select_exchange(ROOT,launch['panel'],d)
    observations=read(d/'observations.json');initial_witnesses=[r['payload'] for r in observations if r['payload']['kind']=='witness' and r['payload']['call']==0]
    check('actual_D1_01_has_one_initial_journal_witness',len(initial_witnesses)==1)
    actual_key=repair.reader.startup.fleet_key(launch['panel'],initial_witnesses[0]['routes'])
    check('actual_D1_01_journal_matches_only_accepted_initial',actual_key==actual['accepted_fleet'] and actual_key!=actual['exchange_final_fleet'])
    actual_H=repair.reconstruct_accepted(ROOT,launch['panel'],d)
    check('actual_D1_01_full_H_stays_complete',actual_H['complete'])
    check('actual_D1_01_trace_contains_unmodified_exchange_final',actual_H['semantic_traces']['exchange/final.json']==repair.reader.startup.semantic(read(d/'hga.csv.exchange/final.json')))
    check('actual_failed_arm_all_read_files_unchanged',raw_before=={name:sha(d/name) for name in raw_before})
    check('all_frozen_helpers_still_unchanged',repair.frozen_bindings()==repair.FROZEN)
    write(folder/'receipt.json',dict(schema='round133-accepted-H-postverify-controlled-fixtures-v1',UTC=utc(),
        passed=True,checks=checks,check_count=len(checks),bindings=bindings,driver_SHA=sha(__file__),
        original_verify_invoked=False,real_arm_read_only=True,real_raw_SHA=raw_before,
        synthetic_folders_are_not_producer_or_performance_evidence=True,Optimize=0,native_starts=0,
        seconds=time.perf_counter()-tick))
    print(json.dumps(dict(passed=True,checks=len(checks),receipt=str(folder/'receipt.json'),Optimize=0,seconds=time.perf_counter()-tick)),flush=True)

if __name__=='__main__':main()
