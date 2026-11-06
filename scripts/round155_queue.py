"""Finite serial dispatch after a verified live arm; never selects research outcomes.

Waiting is orchestration only. Every child uses the existing outer fee meter;
the queue does not add a second experimental charge or launch a solver itself.
"""
import subprocess
from round155_common import *

def prepare(label='screen_queue_v1',qualification='interfaces_v1',screens_only='false'):
    target=OUT/'infra'/label;target.mkdir(parents=True,exist_ok=False)
    if screens_only=='true':
        gate=read(OUT/'review/loop_admission.json')
        assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(ROOT/'scripts/round155_loop.py')
        assert gate['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
        assert gate['qualification_SHA']==sha(OUT/'qualification'/qualification/'result.json')
        jobs=[]
    else:
        assert screens_only=='false'
        jobs=[dict(label=qualification,seconds=600,script='round155_qualify.py',args=['run',qualification]),
              dict(label='loop_admission_'+qualification,seconds=120,script='round155_qualify.py',args=['admit',qualification])]
    for role,short in [('K-35-U','K35'),('N-C20-U','NC20')]:
        for rule in ['first','bounded']:
            phase=rule+'_screen_v1'
            jobs.append(dict(label=short+'_'+phase,seconds=2100,script='round155_loop.py',
                args=['run',role,phase,rule,'1800','12','initial','120'],
                result=str(OUT/'coupled'/f'{role}_{phase}'/'result.json')))
    sources=['round155_queue.py','round155_common.py','round155_qualify.py',
             'round155_loop.py','round155_oracle.py']
    write(target/'plan.json',dict(UTC=utc(),label=label,wait_for='confirmation_001',
        required_closeout=str(OUT/'campaign_confirmation/001/raw/R155_001_N-B35-S_S0_B/verification_closeout.json'),
        frozen_sources={name:sha(ROOT/'scripts'/name) for name in sources},jobs=jobs,
        qualified_interface=qualification,qualification_already_admitted=screens_only=='true',
        finite_screen_only=True,substantive_continuation_requires_actual_result_review=True,
        stop_on_any_failure=True,no_parallel_experiments=True,waiting_not_experiment_cost=True))

def run(label='screen_queue_v1'):
    configure();target=OUT/'infra'/label;plan=read(target/'plan.json')
    # Exclusive creation prevents two dispatchers from racing on one fee label.
    lock=target/'started.json'
    with lock.open('x',encoding='utf-8') as stream:
        json.dump(dict(UTC=utc(),pid=os.getpid(),**meter.process_birth(os.getpid()),
                       plan_SHA=sha(target/'plan.json')),stream,indent=2)
    state=dict(label=label,UTC=utc(),decision='WAITING_FOR_VERIFIED_ARM',completed=[])
    def record(**updates):
        state.update(updates,UTC=utc());write(target/'status.json',state)
    def frozen():
        for name,digest in plan['frozen_sources'].items():
            assert sha(ROOT/'scripts'/name)==digest,('pending queue source changed',name)
    def stop_requested():
        return (target/'stop_requested.json').exists()
    try:
        frozen();record()
        receipt_path=OUT/'fees'/plan['wait_for']/'receipt.json'
        wait_start=time.perf_counter();missing_since=None
        while not receipt_path.exists():
            if stop_requested():record(decision='STOPPED_BEFORE_NEXT_CHILD');return
            live=meter.light_status(plan['wait_for'])
            alive=live.get('process',{}).get('same_process_alive',False)
            if alive:missing_since=None
            elif missing_since is None:missing_since=time.perf_counter()
            assert missing_since is None or time.perf_counter()-missing_since<180,('predecessor exited without receipt',live)
            assert time.perf_counter()-wait_start<plan.get('wait_limit_seconds',9000),'bounded wait expired'
            record(waited_seconds=time.perf_counter()-wait_start,predecessor=live)
            time.sleep(10)
        receipt=read(receipt_path)
        assert receipt['exit_observed'] and receipt['exit_code']==0 and not receipt['timeout'] and not receipt['supervisor_failure'],receipt
        if plan.get('predecessor_kind')=='coupled':
            result=read(plan['required_result']);assert not result['refresh_required']
            assert result['lower']<=result['upper'] and result['Q_SHA']==plan['predecessor_Q_SHA']
            record(predecessor_receipt_SHA=sha(receipt_path),predecessor_result_SHA=sha(plan['required_result']),
                   predecessor_decision=result['decision'],predecessor_iterations=len(result['records']))
        else:
            closeout=read(plan['required_closeout'])
            for key in ['necessary_verification_complete','implementation_qualified','evidence_complete','performance_eligible']:
                assert closeout[key],(key,closeout)
            record(predecessor_receipt_SHA=sha(receipt_path),predecessor_closeout_SHA=sha(plan['required_closeout']))
        for job in plan['jobs']:
            if stop_requested():record(decision='STOPPED_BEFORE_NEXT_CHILD');return
            frozen();assert not (OUT/'fees'/job['label']).exists(),('never resume/retry implicitly',job['label'])
            if job.get('source'):assert sha(job['source'])==job['source_SHA'],('queued source changed',job['source'])
            if job.get('entrypoint')=='campaign':
                argv=[str(PYTHON),'-B',str(ROOT/'scripts/round155_campaign.py'),'one',str(job['position'])]
            else:
                argv=[str(PYTHON),'-B',str(ROOT/'scripts/round155_common.py'),job['label'],str(job['seconds']),job['script'],*job['args']]
            record(decision='RUNNING_CHILD',current_job=job['label'],command=argv)
            print(json.dumps(dict(queue=label,starting=job['label'])),flush=True)
            child=subprocess.run(argv,cwd=str(ROOT),env=meter.environment(),check=False)
            fee=read(OUT/'fees'/job['label']/'receipt.json')
            assert child.returncode==0 and fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout'],(job,child.returncode,fee)
            outcome=dict(label=job['label'],receipt_SHA=sha(OUT/'fees'/job['label']/'receipt.json'))
            if job.get('result'):
                result=read(job['result']);assert not result['refresh_required']
                outcome.update(result_SHA=sha(job['result']),lower=result['lower'],upper=result['upper'],
                               decision=result['decision'],iterations=len(result['records']))
            if job.get('closeout'):
                closeout=read(job['closeout'])
                for key in ['necessary_verification_complete','implementation_qualified','evidence_complete','performance_eligible']:
                    assert closeout[key],(key,closeout)
                outcome['closeout_SHA']=sha(job['closeout'])
            state['completed'].append(outcome);record(current_job=None)
        record(decision=plan.get('completion_decision','FINITE_SCREEN_QUEUE_COMPLETE'))
        print(json.dumps(state),flush=True)
    except BaseException as error:
        record(decision='FAILED_STOPPED',error=repr(error))
        raise

def prepare_followthrough(label='long_and_panel_queue_v1'):
    """Only already-frozen NC20 and three remaining own-H B/E arms."""
    configure();target=OUT/'infra'/label;target.mkdir(parents=True,exist_ok=False)
    deep_path=OUT/'level_deep_plan_v2.json';deep=read(deep_path);k,nc=deep['roles']
    assert (k['role'],nc['role'])==('K-35-U','N-C20-U')
    live=meter.light_status(k['fee_label']);assert live.get('process',{}).get('same_process_alive')
    gate=read(OUT/'review/level_admission.json')
    assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(ROOT/'scripts/round155_level.py')
    assert gate['loop_SHA']==sha(ROOT/'scripts/round155_loop.py') and gate['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    panel=read(OUT/'confirmation_matrix.json');panel_gate=read(OUT/'review/confirmation_admission.json')
    assert panel_gate['decision']=='ACCEPT' and panel_gate['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    assert panel_gate['source_SHA']==sha(ROOT/'scripts/round155_campaign.py')
    jobs=[dict(label=nc['fee_label'],seconds=nc['outer_reservation_seconds'],script='round155_level.py',
        args=['run',nc['role'],nc['label'],str(nc['phase_seconds']),nc['source'],str(nc['price_cap'])],
        source=nc['source'],source_SHA=nc['source_SHA'],
        result=str(OUT/'coupled'/f'{nc["role"]}_{nc["label"]}'/'result.json'))]
    for position in (2,3,4):
        group=panel['groups'][position-1];launch=group['launch']
        assert launch['cap_seconds']==7200
        jobs.append(dict(label=f'confirmation_{position:03}',entrypoint='campaign',position=position,
            seconds=launch['cap_seconds']+900,
            closeout=str(OUT/group['group']/'raw'/launch['arm_id']/'verification_closeout.json')))
    assert all(not (OUT/'fees'/job['label']).exists() for job in jobs)
    account=budget();assert [v['label'] for v in account['unclosed']]==[k['fee_label']]
    assert account['remaining_G1_seconds']>=k['outer_reservation_seconds']+sum(v['seconds'] for v in jobs)+21600
    sources=['round155_queue.py','round155_common.py','round155_campaign.py','round155_level.py','round155_loop.py','round155_oracle.py']
    write(target/'plan.json',dict(UTC=utc(),label=label,wait_for=k['fee_label'],wait_limit_seconds=k['outer_reservation_seconds']+600,
        predecessor_kind='coupled',predecessor_Q_SHA=k['Q_SHA'],
        required_result=str(OUT/'coupled'/f'{k["role"]}_{k["label"]}'/'result.json'),
        live_predecessor_at_freeze=live,level_deep_plan_SHA=sha(deep_path),confirmation_matrix_SHA=sha(OUT/'confirmation_matrix.json'),
        frozen_sources={name:sha(ROOT/'scripts'/name) for name in sources},jobs=jobs,
        completion_decision='PREDECLARED_RUNS_COMPLETE_FINAL_REVIEW_REQUIRED',
        no_new_strategy_or_research_outcome_selected=True,stop_on_any_failure=True,no_parallel_experiments=True,
        waiting_not_experiment_cost=True,each_child_metered_once=True,no_automatic_publication=True))
    print(json.dumps(dict(label=label,wait_for=k['fee_label'],jobs=[v['label'] for v in jobs])),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
