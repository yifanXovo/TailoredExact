"""Bind the observed matched tests and independent readbacks to long continuations."""
from round155_common import *

def prepare(label='bounded_deep_v1'):
    configure();gate=read(OUT/'review/loop_admission.json')
    assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(ROOT/'scripts/round155_loop.py')
    assert gate['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    loop_audit_path=OUT/'qualification/matched_readback_v1/result.json'
    support_audit_path=OUT/'qualification/support_readback_v1/result.json'
    loops=read(loop_audit_path);supports=read(support_audit_path)
    assert loops['PASS'] and supports['PASS'] and loops['Optimize']==supports['Optimize']==0
    assert len(loops['phases'])==4 and len(loops['prices'])==48 and len(supports['replays'])==4
    rows=read(OUT/'reports/research_phases.json')['phases'];selected=[]
    for role,short in [('K-35-U','K35'),('N-C20-U','NC20')]:
        by={r['rule']:r for r in rows if r['role']==role and r['phase'] in ('first_screen_v1','bounded_screen_v1')}
        first,bounded=by['first'],by['bounded']
        assert first['source_SHA']==bounded['source_SHA']
        assert first['completed_iterations']==bounded['completed_iterations']==12
        assert first['this_phase_columns_ever_used']==bounded['this_phase_columns_ever_used']==0
        assert abs(first['upper_decrease'])<1e-10 and abs(bounded['upper_decrease'])<1e-10
        assert first['lower_increment']==bounded['lower_increment']==0
        f_rate=first['this_phase_columns']/first['direct_outer_G1_seconds']
        b_rate=bounded['this_phase_columns']/bounded['direct_outer_G1_seconds'];assert b_rate>f_rate
        source=OUT/'support_LP'/f'{role}_bounded_screen_support_v1'/'result.json';prior=read(source)
        audited=next(item for item in supports['replays'] if Path(item['result']).resolve()==source.resolve())
        assert audited['SHA256']==sha(source) and not prior['refresh_required']
        coupled=Path(prior['prior_results'][0]).resolve()
        witnessed=next(item for item in loops['phases'] if Path(item['result']).resolve()==coupled)
        assert witnessed['SHA256']==sha(coupled)
        selected.append(dict(role=role,label=label,fee_label=short+'_'+label,source=str(source),source_SHA=sha(source),
            rule='bounded',phase_seconds=28200,outer_reservation_seconds=28800,iterations=0,price_cap=120,
            deterministic_node_limit=256,pool_solutions=20,Seed=0,Threads=1,tolerance=1e-4,
            lower=prior['lower'],upper=prior['upper'],columns=len(prior['columns']),supports=len(prior['supports']),
            Q_SHA=prior['Q_SHA'],retained_upper_witness=witnessed['upper_witness'],
            first_new_columns_per_outer_second=f_rate,bounded_new_columns_per_outer_second=b_rate,
            no_positive_weight_or_hull_improvement_claim_from_screen=True,
            interface_gate_SHA=sha(OUT/'review/loop_admission.json')))
    account=budget()
    reserve=dict(two_substantive_continuations=57600,remaining_three_E_arms_with_verification=24300,
        one_observation_based_adjustment=14400,final_verification_failure_margin=21600)
    assert account['remaining_G1_seconds']>sum(reserve.values())
    path=OUT/'deep_plan.json';assert not path.exists()
    write(path,dict(UTC=utc(),decision='ADMIT_SUBSTANTIVE_CONTINUATIONS',roles=selected,budget=account,reserved_capacity=reserve,
        selection_reason='Bounded pricing returned more distinct legal columns per total paid second in both matched tests. Neither rule improved the hull materially or gave a tracked positive new-column weight; the longer opportunity tests whether more complete feedback removes the degeneracy.',
        loop_readback_SHA=sha(loop_audit_path),support_readback_SHA=sha(support_audit_path),
        small_screens_do_not_establish_saturation=True,scope_is_complete_original_Q=True,
        independent_review_method='separate exact arithmetic, actual matrix reconstruction and saved-primal readback; not a nonimplementer-agent review',
        no_runtime_instance_switch=True,offline_phase_capacity_not_a_hardware_based_algorithm_switch=True,
        targeted_adjustment_only_after_observed_stagnation=True))
    print(json.dumps(dict(decision='ADMIT_SUBSTANTIVE_CONTINUATIONS',roles=[r['role'] for r in selected],
        phase_capacity_seconds=57600,remaining_G1_seconds=account['remaining_G1_seconds'])),flush=True)

def prepare_level(label='feasible_level_deep_v1'):
    """Versioned allocation after an observed plateau, retaining deep capacity."""
    configure();gate_path=OUT/'review/level_admission.json';gate=read(gate_path)
    assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(ROOT/'scripts/round155_level.py')
    assert gate['loop_SHA']==sha(ROOT/'scripts/round155_loop.py') and gate['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    original=read(OUT/'deep_plan.json');checkpoint=OUT/'coupled/K-35-U_bounded_deep_v1/result.json'
    observed=read(checkpoint);fee=read(OUT/'fees/K35_bounded_deep_v1/receipt.json')
    audit_path=OUT/'qualification/K35_basic_checkpoint_readback_v1/result.json';audit=read(audit_path)
    assert audit['PASS'] and len(audit['phases'])==1 and audit['phases'][0]['SHA256']==sha(checkpoint)
    assert fee['exit_observed'] and fee['exit_code']==0 and not fee['timeout']
    assert observed['decision']=='reviewed_checkpoint' and not observed['refresh_required']
    assert len(observed['records'])>=100 and max(r['maximum_weight'] for r in observed['new_column_usage'])<=1e-10
    roles=[]
    for role,short,source_name,readback in [
        ('K-35-U','K35','K-35-U_bounded_deep_support_v1','K35_basic_support_readback_v1'),
        ('N-C20-U','NC20','N-C20-U_bounded_screen_support_v1','support_readback_v1')]:
        source=OUT/'support_LP'/source_name/'result.json';prior=read(source)
        check_path=OUT/'qualification'/readback/'result.json';checked=read(check_path)
        assert checked['PASS']
        item=next(v for v in checked['replays'] if Path(v['result']).resolve()==source.resolve())
        assert item['SHA256']==sha(source) and not prior['refresh_required']
        old=next(v for v in original['roles'] if v['role']==role)
        allowance=math.floor(old['outer_reservation_seconds']-(fee['G1_seconds'] if role=='K-35-U' else 0.))
        assert allowance>600
        roles.append(dict(role=role,label=label,fee_label=short+'_'+label,source=str(source),source_SHA=sha(source),
            rule='fixed_level_feasible_AP',outer_reservation_seconds=allowance,phase_seconds=allowance-600,
            price_cap=120,selection_cap=120,selection_iteration_limit=2000,iteration_limit=None,
            Seed=0,Threads=1,tolerance=1e-4,deterministic_node_limit=256,pool_solutions=20,
            lower=prior['lower'],upper=prior['upper'],columns=len(prior['columns']),supports=len(prior['supports']),
            Q_SHA=prior['Q_SHA'],source_readback_SHA=sha(check_path),interface_gate_SHA=sha(gate_path)))
    account=budget();reserved=dict(level_continuations=sum(r['outer_reservation_seconds'] for r in roles),
        remaining_E_with_verification=24300,unused_adjustment_or_followup_capacity=14400,final_review_failure_margin=21600)
    own=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert own and len(account['unclosed'])==1 and account['unclosed'][0]['label']==own
    assert account['remaining_G1_seconds']-account['unclosed'][0]['reservation']>=sum(reserved.values())
    path=OUT/'level_deep_plan.json';assert not path.exists()
    write(path,dict(UTC=utc(),decision='ADMIT_ONE_FIXED_LEVEL_ADJUSTMENT',roles=roles,
        supersedes_unstarted_rule_only='deep_plan.json NC20; K35 remaining capacity follows its actual reviewed checkpoint',
        original_plan_SHA=sha(OUT/'deep_plan.json'),K_checkpoint_SHA=sha(checkpoint),K_checkpoint_audit_SHA=sha(audit_path),
        K_completed_iterations=len(observed['records']),K_added_columns=len(observed['columns'])-observed['initial_columns'],
        K_outer_seconds=fee['G1_seconds'],budget=account,reserved_capacity=reserved,
        reason='Sustained valid basic-dual negative columns did not receive positive later RMP weights or improve the interval. Test the already-qualified fixed interior-level feasible AP selector with the remaining substantive capacity, uniformly on both domains.',
        not_a_saturation_claim=True,no_instance_specific_algorithm_switch=True,
        no_elapsed_time_switch_inside_any_algorithm=True,full_Q_and_price_domain_unchanged=True,
        selection_failure_is_unresolved_not_a_bound=True,unspent_capacity_remains_available=True))
    print(json.dumps(dict(decision='ADMIT_ONE_FIXED_LEVEL_ADJUSTMENT',roles=roles,
        remaining_G1_seconds=account['remaining_G1_seconds'])),flush=True)

def revise_level(label='feasible_level_deep_v2'):
    """One observed start-conversion repair, without a selector/oracle grid."""
    configure();old_path=OUT/'level_deep_plan.json';old=read(old_path)
    gate_path=OUT/'review/level_admission.json';gate=read(gate_path)
    assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(ROOT/'scripts/round155_level.py')
    assert gate['loop_SHA']==sha(ROOT/'scripts/round155_loop.py') and gate['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    attempt=OUT/'coupled/K-35-U_feasible_level_deep_v1/result.json';previous=read(attempt)
    fee_path=OUT/'fees/K35_feasible_level_deep_v1/receipt.json';fee=read(fee_path)
    check_path=OUT/'qualification/K35_level_initial_readback_v3/result.json';check=read(check_path)
    selection=read(attempt.parent/'iter000000/selection/result.json')
    call=read(attempt.parent/'iter000000/selection/call.json')
    assert previous['decision']=='no_qualified_feasible_level_candidate' and not previous['records']
    assert not previous['refresh_required'] and fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
    assert check['PASS'] and check['result_SHA']==sha(attempt) and check['warm']['qualified']
    assert selection['Status']==7 and selection['iterations']==2000 and selection['SolCount']==0
    assert call['warm_check']['qualified'] and call['IterationLimit']==2000
    roles=[]
    for p in old['roles']:
        r=dict(p,label=label,fee_label=('K35_' if p['role']=='K-35-U' else 'NC20_')+label)
        r.pop('selection_iteration_limit',None);r['selection_iteration_rule']='selector_variable_count_plus_2000'
        r['interface_gate_SHA']=sha(gate_path)
        if p['role']=='K-35-U':
            r.update(source=str(attempt),source_SHA=sha(attempt),lower=previous['lower'],upper=previous['upper'],
                     columns=len(previous['columns']),supports=len(previous['supports']),
                     outer_reservation_seconds=math.floor(p['outer_reservation_seconds']-fee['G1_seconds']),
                     source_readback_SHA=sha(check_path),source_readback_scope='complete actual selector matrix and warm point; no new prices or pools')
            r['phase_seconds']=r['outer_reservation_seconds']-600
        else:assert sha(r['source'])==r['source_SHA']
        roles.append(r)
    account=budget();own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert len(account['unclosed'])==1 and account['unclosed'][0]['label']==own
    reserved=dict(old['reserved_capacity'],level_continuations=sum(r['outer_reservation_seconds'] for r in roles))
    assert account['remaining_G1_seconds']-account['unclosed'][0]['reservation']>=sum(reserved.values())
    path=OUT/'level_deep_plan_v2.json';assert not path.exists()
    write(path,dict(old,UTC=utc(),roles=roles,budget=account,reserved_capacity=reserved,
        revision_of_SHA=sha(old_path),repair='The observed full-PStart conversion had3172 superbasic variables and exhausted2000 iterations before producing a Native solution. Allow NumVars+2000 iterations uniformly, retain the120s cap, same AP center and exact level gate. Explicitly record two Native-omitted nominal-level coefficients; no original dual-domain constraint or original-Q certificate is omitted.',
        first_attempt_SHA=sha(attempt),first_attempt_receipt_SHA=sha(fee_path),actual_initial_readback_SHA=sha(check_path),
        not_a_new_selector_or_parameter_grid=True))
    print(json.dumps(dict(plan=str(path),roles=roles)),flush=True)

def prepare_remaining(label='bounded_remaining_v1'):
    """Retain the unused substantive opportunity after actual selector exits."""
    from round155_price_certificate import qualified_phase
    configure();gate=read(OUT/'review/loop_admission.json')
    assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(ROOT/'scripts/round155_loop.py')
    assert gate['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    assert gate['price_certificate_SHA']==sha(ROOT/'scripts/round155_price_certificate.py')
    binding_path=OUT/'review/remaining_readback_bindings.json';bindings=read(binding_path)
    assert bindings['decision']=='ACCEPT_ACTUAL_LEVEL_PRICES_SELECTORS_AND_SUPPORTS'
    assert bindings['price_corrections_SHA']==sha(OUT/'review/native_price_corrections.json')
    assert bindings['loop_admission_SHA']==sha(OUT/'review/loop_admission.json')
    panel_path=OUT/'panel_completion.json';panel=read(panel_path)
    queue_path=OUT/'infra/panel_recovery_v1/status.json';queue=read(queue_path)
    assert queue['decision']==panel['decision']=='ALL_SIX_FROZEN_ARMS_VERIFIED'
    assert queue['panel_completion_SHA']==sha(panel_path)
    assert panel['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    accepted={item['position']:item for item in panel['accepted_arms']}
    assert len(panel['accepted_arms'])==6 and set(accepted)==set(range(1,7))
    for group in read(OUT/'confirmation_matrix.json')['groups']:
        item=accepted[group['position']];assert item['arm_id']==group['launch']['arm_id']
        rp=OUT/'fees'/item['fee_label']/'receipt.json';receipt=read(rp)
        assert sha(rp)==item['receipt_SHA'] and receipt['exit_observed'] and receipt['exit_code']==0
        assert not receipt['timeout'] and not receipt['supervisor_failure']
        d=Path(group['launch']['destination']);close=read(d/'verification_closeout.json')
        assert sha(d/'verification_closeout.json')==item['closeout_SHA']
        assert sha(d/'round154_endpoint.json')==item['endpoint_SHA']
        assert all(close[k] for k in ['necessary_verification_complete','implementation_qualified','evidence_complete','performance_eligible'])
    roles=[]
    for role,short,spent in [
        ('K-35-U','K35',['K35_bounded_deep_v1','K35_feasible_level_deep_v1','K35_feasible_level_deep_v2']),
        ('N-C20-U','NC20',['NC20_feasible_level_deep_v2'])]:
        bound=next(v for v in bindings['roles'] if v['role']==role)
        for evidence in bound['evidence'].values():
            assert sha(evidence['path'])==evidence['SHA256']
            assert sha(evidence['receipt'])==evidence['receipt_SHA']
            receipt=read(evidence['receipt'])
            assert receipt['exit_observed'] and receipt['exit_code']==0 and not receipt['timeout']
        coupled=OUT/'coupled'/f'{role}_feasible_level_deep_v2'/'result.json'
        qualified,old=qualified_phase(coupled)
        assert sha(coupled)==bound['raw_result_SHA'] and sha(qualified)==bound['qualified_result_SHA']
        audit_path=Path(bound['evidence']['general']['path']);audit=read(audit_path)
        selected=next(v for v in audit['phases'] if Path(v['result']).resolve()==coupled.resolve())
        assert audit['PASS'] and selected['SHA256']==sha(coupled)
        assert selected['qualified_result_SHA']==sha(qualified)
        level_path=Path(bound['evidence']['selector']['path']);level=read(level_path)
        assert level['PASS'] and level['result_SHA']==sha(coupled)
        assert level['qualified_result_SHA']==sha(qualified)
        assert old['decision']=='no_qualified_feasible_level_candidate' and not old['refresh_required']
        source=Path(bound['evidence']['support_replay']['path']);prior=read(source)
        assert Path(prior['prior_results'][0]).resolve()==qualified.resolve()
        support_path=Path(bound['evidence']['support_readback']['path']);support=read(support_path)
        found=next(v for v in support['replays'] if Path(v['result']).resolve()==source.resolve())
        assert support['PASS'] and found['SHA256']==sha(source)
        assert prior['columns']==old['columns'] and prior['supports']==old['supports'] and prior['scope']==old['scope']
        paid=[]
        for fee in spent:
            receipt_path=OUT/'fees'/fee/'receipt.json';receipt=read(receipt_path)
            assert receipt['exit_observed'] and receipt['exit_code']==0 and not receipt['timeout']
            paid.append(dict(label=fee,seconds=receipt['G1_seconds'],receipt_SHA=sha(receipt_path)))
        used=math.fsum(v['seconds'] for v in paid);capacity=math.floor(28800.-used);assert capacity>600
        roles.append(dict(role=role,label=label,fee_label=short+'_'+label,source=str(source),source_SHA=sha(source),
            rule='bounded',phase_seconds=capacity-600,outer_reservation_seconds=capacity,iterations=0,price_cap=120,
            deterministic_node_limit=256,pool_solutions=20,Seed=0,Threads=1,tolerance=1e-4,
            lower=prior['lower'],upper=prior['upper'],columns=len(prior['columns']),supports=len(prior['supports']),
            Q_SHA=prior['Q_SHA'],completed_deep_outer_seconds=used,completed_deep_receipts=paid,
            interface_gate_SHA=sha(OUT/'review/loop_admission.json'),
            actual_price_transport_binding_SHA=sha(binding_path),
            raw_level_result_SHA=sha(coupled),qualified_level_result_SHA=sha(qualified),
            loop_readback_SHA=sha(audit_path),level_readback_SHA=sha(level_path),support_readback_SHA=sha(support_path),
            retained_upper_witness=selected['upper_witness']))
    account=budget();own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert len(account['unclosed'])==1 and account['unclosed'][0]['label']==own
    reserve=dict(remaining_substantive=sum(v['outer_reservation_seconds'] for v in roles),
                 final_review_and_failures=21600,unallocated_adjustment_capacity=14400)
    assert account['remaining_G1_seconds']-account['unclosed'][0]['reservation']>=sum(reserve.values())
    path=OUT/'remaining_deep_plan.json';assert not path.exists()
    write(path,dict(UTC=utc(),decision='ADMIT_REMAINING_SUBSTANTIVE_BASIC_CONTINUATIONS',roles=roles,budget=account,
        reserved_capacity=reserve,original_deep_plan_SHA=sha(OUT/'deep_plan.json'),
        level_plan_SHA=sha(OUT/'level_deep_plan_v2.json'),
        panel_completion_SHA=sha(panel_path),panel_recovery_status_SHA=sha(queue_path),
        actual_price_transport_binding_SHA=sha(binding_path),
        reason='Both fixed-level attempts ended at unavailable selected candidates without a level or interval gain. Retain every paid valid new column/support and the remaining original8h/domain capacities. Resume the already-qualified basic-dual bounded-price loop without further L1 selection Optimize.',
        source_is_own_branch_only=True,no_new_oracle_or_selector_variant=True,
        full_Q_and_original_price_definition_unchanged=True,
        actual_native_state_transport_qualified_before_continuation=True,
        no_saturation_claim_from_selector_exit=True,
        no_instance_specific_or_elapsed_time_algorithm_switch=True))
    print(json.dumps(dict(decision='ADMIT_REMAINING_SUBSTANTIVE_BASIC_CONTINUATIONS',roles=roles)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
