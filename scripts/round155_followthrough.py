"""Finite post-panel readback, remaining deep capacity, and final raw reports.

No new research rule is selected here. Stop at the first failed child; never
retry, publish, delete, or mark the user goal complete. Waiting is uncharged
orchestration; every arithmetic/Native child has exactly one outer fee.
"""
from round155_common import *


def job(label,seconds,script,*args,kind='verification'):
    return dict(label=label,seconds=seconds,script=script,args=list(args),kind=kind)


def prepare(label='remaining_capacity_queue_v1'):
    configure();target=OUT/'infra'/label;target.mkdir(parents=True,exist_ok=False)
    predecessor=OUT/'infra/long_and_panel_queue_v2';identity=read(predecessor/'started.json')
    birth=meter.process_birth(identity['pid'])
    assert birth and birth['creation_filetime']==identity['creation_filetime']
    assert read(predecessor/'status.json')['decision']=='RUNNING_CHILD'
    stages=[]
    for role,short in [('K-35-U','K35'),('N-C20-U','NC20')]:
        phase=f'{role}_feasible_level_deep_v2';path=OUT/'coupled'/phase/'result.json';result=read(path)
        assert result['decision']=='no_qualified_feasible_level_candidate' and not result['refresh_required']
        a=short+'_level_v2_readback_v1';s=short+'_level_v2_selector_readback_v1'
        stages.append(job(a,1200,'round155_audit.py','loops',a,phase))
        stages.append(job(s,1800,'round155_level_readback.py','run',s,phase,a))
        stages.append(job(short+'_level_deep_support_v2',600,'round155_loop.py','replay',role,'level_deep_support_v2',str(path)))
        a=short+'_level_support_readback_v1'
        stages.append(job(a,600,'round155_audit.py','support_replays',a,role+'_level_deep_support_v2'))
    stages.append(job('prepare_remaining_deep_v1',120,'round155_deepen.py','prepare_remaining','bounded_remaining_v1'))
    sources=['round155_followthrough.py','round155_deepen.py','round155_audit.py','round155_level_readback.py',
             'round155_level_check.py','round155_loop.py','round155_oracle.py','round155_common.py','round155_reports.py']
    # Completed immutable level results are small source anchors. Their full
    # models/points and prices are verified only after the serial lane is idle.
    anchors={f'{role}_feasible_level_deep_v2':sha(OUT/'coupled'/f'{role}_feasible_level_deep_v2'/'result.json')
             for role in ['K-35-U','N-C20-U']}
    write(target/'plan.json',dict(UTC=utc(),label=label,predecessor=str(predecessor),predecessor_identity=identity,
        wait_limit_seconds=25200,predecessor_terminal='PREDECLARED_RUNS_COMPLETE_FINAL_REVIEW_REQUIRED',
        frozen_sources={name:sha(ROOT/'scripts'/name) for name in sources},closed_level_anchors=anchors,
        initial_jobs=stages,remaining_plan=str(OUT/'remaining_deep_plan.json'),
        remaining_phase_label='bounded_remaining_v1',post_loop_audit_cap=10800,
        no_parallel_experiments=True,stop_on_any_failure=True,waiting_not_experiment_cost=True,
        no_automatic_retry_publication_or_goal_completion=True,
        retain_original_eight_hour_per_domain_capacity=True,
        no_new_oracle_or_selector_variant=True))
    print(json.dumps(dict(label=label,predecessor=identity,initial_jobs=len(stages))),flush=True)


def prepare_closed(label='remaining_capacity_queue_v2'):
    """Prepare only AFTER the sole panel owner has actually exited successfully."""
    configure()
    from round100_idle import ensure_idle
    import round155_panel_recovery as recovery
    ensure_idle();account=budget();own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert [item['label'] for item in account['unclosed']]==[own]
    old_target=OUT/'infra/remaining_capacity_queue_v1';old=read(old_target/'plan.json')
    failed=read(old_target/'status.json')
    assert failed['decision']=='FAILED_STOPPED' and not failed['completed']
    parent=OUT/'infra/panel_recovery_v1';identity=read(parent/'started.json')
    birth=meter.process_birth(identity['pid'])
    assert not birth or birth['creation_filetime']!=identity['creation_filetime'],'panel owner must exit before this preparation'
    state=read(parent/'status.json');panel_path=OUT/'panel_completion.json';panel=read(panel_path)
    assert state['decision']==panel['decision']=='ALL_SIX_FROZEN_ARMS_VERIFIED'
    assert state['panel_completion_SHA']==sha(panel_path)
    matrix=read(OUT/'confirmation_matrix.json');assert panel['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    assert len(panel['accepted_arms'])==6 and {v['position'] for v in panel['accepted_arms']}==set(range(1,7))
    for item in panel['accepted_arms']:
        assert recovery.accepted(item['position'],item['fee_label'],matrix)==item
    assert not Path(old['remaining_plan']).exists()
    for item in old['initial_jobs']:assert not (OUT/'fees'/item['label']).exists()
    for name,digest in old['frozen_sources'].items():
        if name not in ('round155_followthrough.py','round155_deepen.py'):
            assert sha(ROOT/'scripts'/name)==digest,('unrelated research source changed',name)
    sources={name:sha(ROOT/'scripts'/name) for name in old['frozen_sources']}
    sources['round155_panel_recovery.py']=sha(ROOT/'scripts/round155_panel_recovery.py')
    target=OUT/'infra'/label;target.mkdir(parents=True,exist_ok=False)
    plan=dict(old,UTC=utc(),label=label,predecessor=str(parent),predecessor_identity=identity,
        predecessor_terminal='ALL_SIX_FROZEN_ARMS_VERIFIED',wait_limit_seconds=1,
        predecessor_already_closed=True,panel_completion_SHA=sha(panel_path),
        no_independent_waiting_dispatcher=True,frozen_sources=sources,
        recovery_of_failed_plan_SHA=sha(old_target/'plan.json'),
        recovery_of_failed_status_SHA=sha(old_target/'status.json'),
        unchanged_initial_jobs_and_research_rules=True)
    write(target/'plan.json',plan)
    write(OUT/'review/remaining_capacity_recovery_admission.json',dict(UTC=utc(),
        decision='ADMIT_POST_PANEL_ONLY_REMAINING_CAPACITY_QUEUE',plan_SHA=sha(target/'plan.json'),
        panel_completion_SHA=sha(panel_path),source_SHA=sha(__file__),idle_check_passed=True,
        old_failed_queue_retained=True,no_research_algorithm_change=True))
    print(json.dumps(dict(label=label,initial_jobs=len(plan['initial_jobs']),predecessor_already_closed=True)),flush=True)


def prepare_after_readbacks(label='remaining_capacity_queue_v3'):
    """Bind actual repaired readbacks; never rerun the failed v2 child/queue."""
    from round100_idle import ensure_idle
    from round155_price_certificate import qualified_phase
    import round155_panel_recovery as recovery
    configure();ensure_idle();account=budget();own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert [item['label'] for item in account['unclosed']]==[own]
    old_target=OUT/'infra/remaining_capacity_queue_v2';old=read(old_target/'plan.json')
    failed=read(old_target/'status.json');old_identity=read(old_target/'started.json')
    birth=meter.process_birth(old_identity['pid'])
    assert not birth or birth['creation_filetime']!=old_identity['creation_filetime']
    assert failed['decision']=='FAILED_STOPPED' and not failed['completed']
    assert failed['current_job']=='K35_level_v2_readback_v1'
    failed_receipt=read(OUT/'fees/K35_level_v2_readback_v1/receipt.json')
    assert failed_receipt['exit_observed'] and failed_receipt['exit_code']!=0
    parent=OUT/'infra/panel_recovery_v1';identity=read(parent/'started.json')
    birth=meter.process_birth(identity['pid'])
    assert not birth or birth['creation_filetime']!=identity['creation_filetime']
    state=read(parent/'status.json');panel_path=OUT/'panel_completion.json';panel=read(panel_path)
    assert state['decision']==panel['decision']=='ALL_SIX_FROZEN_ARMS_VERIFIED'
    assert state['panel_completion_SHA']==sha(panel_path)
    matrix=read(OUT/'confirmation_matrix.json');assert panel['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    assert len(panel['accepted_arms'])==6 and {v['position'] for v in panel['accepted_arms']}==set(range(1,7))
    for item in panel['accepted_arms']:
        assert recovery.accepted(item['position'],item['fee_label'],matrix)==item
    gate_path=OUT/'review/loop_admission.json';gate=read(gate_path)
    assert gate['decision']=='ACCEPT'
    for key,name in [('source_SHA','round155_loop.py'),('oracle_SHA','round155_oracle.py'),
                     ('price_certificate_SHA','round155_price_certificate.py')]:
        assert gate[key]==sha(ROOT/'scripts'/name)
    def evidence(path,fee_label):
        receipt_path=OUT/'fees'/fee_label/'receipt.json';receipt=read(receipt_path)
        assert receipt['exit_observed'] and receipt['exit_code']==0
        assert not receipt['timeout'] and not receipt['supervisor_failure']
        return dict(path=str(path),SHA256=sha(path),fee_label=fee_label,
                    receipt=str(receipt_path),receipt_SHA=sha(receipt_path),G1_seconds=receipt['G1_seconds'])
    roles=[]
    for role,short,audit_label in [('K-35-U','K35','K35_level_v2_readback_v2'),
                                  ('N-C20-U','NC20','NC20_level_v2_readback_v1')]:
        raw=OUT/'coupled'/f'{role}_feasible_level_deep_v2'/'result.json'
        qualified,result=qualified_phase(raw)
        assert qualified.resolve()!=raw.resolve()
        assert result['decision']=='no_qualified_feasible_level_candidate' and not result['refresh_required']
        a=OUT/'qualification'/audit_label/'result.json';audit=read(a)
        assert audit['PASS'] and audit['Optimize']==0
        found=next(v for v in audit['phases'] if Path(v['result']).resolve()==raw.resolve())
        assert found['SHA256']==sha(raw) and found['qualified_result_SHA']==sha(qualified)
        selector_label=short+'_level_v2_selector_readback_v1'
        s=OUT/'qualification'/selector_label/'result.json';selector=read(s)
        assert selector['PASS'] and selector['result_SHA']==sha(raw)
        assert selector['qualified_result_SHA']==sha(qualified) and not selector['resolved_levels']
        replay_label=short+'_level_deep_support_v2'
        r=OUT/'support_LP'/f'{role}_level_deep_support_v2'/'result.json';replay=read(r)
        assert Path(replay['prior_results'][0]).resolve()==qualified.resolve()
        assert replay['columns']==result['columns'] and replay['supports']==result['supports']
        assert replay['scope']==result['scope'] and not replay['refresh_required']
        support_label=short+'_level_support_readback_v1'
        b=OUT/'qualification'/support_label/'result.json';support=read(b)
        assert support['PASS'] and support['Optimize']==0
        checked=next(v for v in support['replays'] if Path(v['result']).resolve()==r.resolve())
        assert checked['SHA256']==sha(r)
        roles.append(dict(role=role,raw_result=str(raw),raw_result_SHA=sha(raw),
            qualified_result=str(qualified),qualified_result_SHA=sha(qualified),
            evidence=dict(general=evidence(a,audit_label),selector=evidence(s,selector_label),
                          support_replay=evidence(r,replay_label),support_readback=evidence(b,support_label))))
    correction=OUT/'review/native_price_corrections.json'
    constructor=evidence(OUT/'qualification/price_transport_requalification_v1/result.json',
                         'price_transport_requalification_v1')
    assert not Path(old['remaining_plan']).exists()
    initial=job('prepare_remaining_deep_v1',120,'round155_deepen.py','prepare_remaining','bounded_remaining_v1')
    assert not (OUT/'fees'/initial['label']).exists()
    binding_path=OUT/'review/remaining_readback_bindings.json';assert not binding_path.exists()
    write(binding_path,dict(UTC=utc(),decision='ACCEPT_ACTUAL_LEVEL_PRICES_SELECTORS_AND_SUPPORTS',roles=roles,
        constructor=constructor,price_corrections_SHA=sha(correction),loop_admission_SHA=sha(gate_path),
        raw_failed_receipt_preserved=True,raw_historical_prices_unchanged=True,
        actual_native_coefficients_and_full_domain_bounds_independently_checked=True,
        original_guard_plus_additional_one_sided_transport=True,no_extra_optimization_for_price_corrections=True,
        independent_review_method='separate exact arithmetic and actual matrix/primal readback; not a nonimplementer agent'))
    sources=set(old['frozen_sources'])|{'round155_price_certificate.py','round155_price_requalify.py','round155_qualify.py'}
    target=OUT/'infra'/label;target.mkdir(parents=True,exist_ok=False)
    plan=dict(old,UTC=utc(),label=label,predecessor=str(parent),predecessor_identity=identity,
        predecessor_terminal='ALL_SIX_FROZEN_ARMS_VERIFIED',wait_limit_seconds=1,
        predecessor_already_closed=True,panel_completion_SHA=sha(panel_path),
        initial_jobs=[initial],completed_prerequisites_binding=str(binding_path),
        completed_prerequisites_binding_SHA=sha(binding_path),
        frozen_sources={name:sha(ROOT/'scripts'/name) for name in sorted(sources)},
        recovery_of_failed_plan_SHA=sha(old_target/'plan.json'),recovery_of_failed_status_SHA=sha(old_target/'status.json'),
        actual_prerequisites_already_paid=True,no_repeat_of_completed_readbacks=True,
        corrected_support_sources_required=True,research_selection_and_pricing_rules_unchanged=True)
    plan.pop('unchanged_initial_jobs_and_research_rules',None)
    write(target/'plan.json',plan)
    write(OUT/'review/remaining_capacity_recovery_v3_admission.json',dict(UTC=utc(),
        decision='ADMIT_AFTER_ACTUAL_PRICE_AND_SUPPORT_READBACKS',plan_SHA=sha(target/'plan.json'),
        binding_SHA=sha(binding_path),panel_completion_SHA=sha(panel_path),source_SHA=sha(__file__),
        idle_check_passed=True,all_failed_queues_retained=True,remaining_deep_not_yet_run=True))
    print(json.dumps(dict(label=label,initial_jobs=1,paid_prerequisites=8,binding_SHA=sha(binding_path))),flush=True)


def run(label='remaining_capacity_queue_v1'):
    configure();target=OUT/'infra'/label;plan=read(target/'plan.json')
    with (target/'started.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(UTC=utc(),pid=os.getpid(),**meter.process_birth(os.getpid()),plan_SHA=sha(target/'plan.json')),stream,indent=2)
    state=dict(label=label,decision='WAITING_FOR_PANEL_QUEUE',completed=[])
    def record(**updates):
        state.update(updates,UTC=utc());write(target/'status.json',state)
    def frozen():
        for name,digest in plan['frozen_sources'].items():
            assert sha(ROOT/'scripts'/name)==digest,('pending source changed',name)
        if 'completed_prerequisites_binding' in plan:
            assert sha(plan['completed_prerequisites_binding'])==plan['completed_prerequisites_binding_SHA']
    def stop_requested():return (target/'stop_requested.json').exists()
    def execute(item):
        if stop_requested():raise RuntimeError('review stop requested before next child')
        frozen();assert not (OUT/'fees'/item['label']).exists(),('never retry implicitly',item['label'])
        assert not budget()['unclosed']
        record(decision='RUNNING_CHILD',current_job=item['label'],command=item)
        print(json.dumps(dict(queue=label,starting=item['label'])),flush=True)
        run_child=item
        # The worker itself is outside any fee; c.run supplies the sole outer.
        import round155_common as common
        common.run(run_child['label'],run_child['seconds'],run_child['script'],run_child['args'],kind=run_child.get('kind','research'))
        rp=OUT/'fees'/item['label']/'receipt.json';receipt=read(rp)
        assert receipt['exit_observed'] and receipt['exit_code']==0 and not receipt['timeout']
        state['completed'].append(dict(label=item['label'],G1_seconds=receipt['G1_seconds'],receipt_SHA=sha(rp)))
        record(current_job=None)
    try:
        frozen();record();tick=time.perf_counter();parent=Path(plan['predecessor']);identity=plan['predecessor_identity']
        while True:
            if stop_requested():record(decision='STOPPED_BEFORE_NEXT_CHILD');return
            # A concurrently replaced tiny status file can be observed between
            # writes. A bounded read retry is not a child restart.
            status=None
            for attempt in range(5):
                try:status=read(parent/'status.json');break
                except (json.JSONDecodeError,FileNotFoundError):time.sleep(.05)
            assert status is not None,'predecessor status unreadable'
            if status['decision']==plan['predecessor_terminal']:
                if plan.get('predecessor_already_closed'):
                    birth=meter.process_birth(identity['pid'])
                    assert not birth or birth['creation_filetime']!=identity['creation_filetime']
                    assert sha(OUT/'panel_completion.json')==plan['panel_completion_SHA']
                break
            assert status['decision'] not in ('FAILED_STOPPED','STOPPED_BEFORE_NEXT_CHILD'),status
            birth=meter.process_birth(identity['pid'])
            assert birth and birth['creation_filetime']==identity['creation_filetime'],('predecessor no longer live',status)
            assert time.perf_counter()-tick<plan['wait_limit_seconds'],'bounded panel wait expired'
            record(waited_seconds=time.perf_counter()-tick,predecessor_job=status.get('current_job'),predecessor_alive=True)
            time.sleep(10)
        assert not budget()['unclosed'];frozen()
        for phase,digest in plan['closed_level_anchors'].items():
            assert sha(OUT/'coupled'/phase/'result.json')==digest
        record(predecessor_terminal_SHA=sha(parent/'status.json'))
        for item in plan['initial_jobs']:execute(item)
        remaining=read(plan['remaining_plan'])
        assert remaining['decision']=='ADMIT_REMAINING_SUBSTANTIVE_BASIC_CONTINUATIONS'
        for p in remaining['roles']:
            assert p['label']==plan['remaining_phase_label'] and sha(p['source'])==p['source_SHA']
            execute(job(p['fee_label'],p['outer_reservation_seconds'],'round155_loop.py','run',p['role'],p['label'],p['rule'],
                        str(p['phase_seconds']),str(p['iterations']),p['source'],str(p['price_cap']),kind='research'))
            outcome=read(OUT/'coupled'/f'{p["role"]}_{p["label"]}'/'result.json')
            assert not outcome['refresh_required']
        for p in remaining['roles']:
            role=p['role'];short='K35' if role=='K-35-U' else 'NC20';phase=f'{role}_{p["label"]}'
            a=short+'_remaining_deep_readback_v1'
            execute(job(a,plan['post_loop_audit_cap'],'round155_audit.py','loops',a,phase))
            execute(job(short+'_remaining_deep_support_v1',600,'round155_loop.py','replay',role,'remaining_deep_support_v1',
                        str(OUT/'coupled'/phase/'result.json')))
            a=short+'_remaining_support_readback_v1'
            execute(job(a,600,'round155_audit.py','support_replays',a,role+'_remaining_deep_support_v1'))
        execute(job('final_raw_complete_report_v1',300,'round155_reports.py','complete'))
        execute(job('final_raw_checkpoint_report_v1',600,'round155_reports.py','checkpoints'))
        execute(job('final_raw_research_report_v1',600,'round155_reports.py','research'))
        record(decision='REMAINING_RESEARCH_AND_RAW_READBACK_COMPLETE_FINAL_JUDGMENT_REQUIRED')
        print(json.dumps(state),flush=True)
    except BaseException as error:
        record(decision='FAILED_STOPPED',error=repr(error));raise


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
