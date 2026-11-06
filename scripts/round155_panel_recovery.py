"""Observed pre-Native dispatch recovery with one serial owner and fresh fees.

The production adapter, frozen matrix, idle guard, PE and all algorithm
parameters are unchanged. Never start an independent waiting dispatcher.
"""
import round155_common as common
from round155_common import *
from round100_idle import ensure_idle

LABEL='panel_recovery_v1'
GATE=OUT/'review/panel_dispatch_recovery_admission.json'
TARGET=OUT/'infra'/LABEL
KEYS=['necessary_verification_complete','implementation_qualified','evidence_complete','performance_eligible']


def accepted(position,fee_label,matrix):
    group=matrix['groups'][position-1];destination=Path(group['launch']['destination'])
    assert group['position']==position and sha(OUT/group['group']/'identity.json')==group['identity_SHA']
    rp=OUT/'fees'/fee_label/'receipt.json';receipt=read(rp)
    assert receipt['exit_observed'] and receipt['exit_code']==0 and not receipt['timeout'] and not receipt['supervisor_failure']
    cp=destination/'verification_closeout.json';close=read(cp)
    assert all(close[key] for key in KEYS),close
    ep=destination/'round154_endpoint.json';endpoint=read(ep)
    assert endpoint['arm_id']==group['launch']['arm_id'] and endpoint['performance_eligible']
    assert endpoint['verification_closeout_SHA']==sha(cp)
    assert endpoint['audit_SHA']==close['audit_SHA']==sha(destination/'audit.json')
    return dict(position=position,arm_id=endpoint['arm_id'],fee_label=fee_label,
        receipt_SHA=sha(rp),G1_seconds=receipt['G1_seconds'],endpoint_SHA=sha(ep),closeout_SHA=sha(cp))


def admit():
    configure();ensure_idle();account=budget();own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert [r['label'] for r in account['unclosed']]==[own]
    failures=[]
    for label in ['long_and_panel_queue_v2','remaining_capacity_queue_v1']:
        target=OUT/'infra'/label;identity=read(target/'started.json');birth=meter.process_birth(identity['pid'])
        assert not birth or birth['creation_filetime']!=identity['creation_filetime']
        assert read(target/'status.json')['decision']=='FAILED_STOPPED'
        failures.append(dict(label=label,status_SHA=sha(target/'status.json'),started_SHA=sha(target/'started.json')))
    failed=OUT/'fees/confirmation_003';receipt=read(failed/'receipt.json')
    assert receipt['exit_observed'] and receipt['exit_code']==1 and not receipt['timeout']
    error=(failed/'stderr.log').read_text(encoding='utf-8')
    assert 'foreign optimizer/build process active' in error and 'round155_followthrough.py' in error
    matrix=read(OUT/'confirmation_matrix.json');gate=read(OUT/'review/confirmation_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    assert gate['source_SHA']==sha(ROOT/'scripts/round155_campaign.py')
    for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
    closed=[accepted(p,f'confirmation_{p:03}',matrix) for p in [1,2,5,6]]
    jobs=[]
    for position,label in [(3,'confirmation_003_retry_v1'),(4,'confirmation_004')]:
        group=matrix['groups'][position-1]
        assert not Path(group['launch']['destination']).exists(),'no previous producer evidence may be overwritten'
        assert not (OUT/'fees'/label).exists()
        jobs.append(dict(position=position,label=label,seconds=group['launch']['cap_seconds']+900))
    assert account['remaining_G1_seconds']-account['unclosed'][0]['reservation']>=sum(j['seconds'] for j in jobs)+21600
    TARGET.mkdir(parents=True,exist_ok=False)
    plan=dict(UTC=utc(),label=LABEL,jobs=jobs,previously_verified=closed,failed_queues=failures,
        failed_fee_label='confirmation_003',failed_receipt_SHA=sha(failed/'receipt.json'),
        failed_stderr_SHA=sha(failed/'stderr.log'),failed_attempt_before_Native=True,
        matrix_SHA=sha(OUT/'confirmation_matrix.json'),
        frozen_sources=dict(matrix['helpers'],**{'scripts/round155_panel_recovery.py':sha(__file__)}),
        no_independent_waiting_dispatcher=True,unchanged_idle_guard=True,
        unchanged_production_and_algorithms=True,stop_on_any_failure=True,no_implicit_retry=True)
    write(TARGET/'plan.json',plan)
    write(GATE,dict(UTC=utc(),decision='ADMIT_OBSERVED_PRE_NATIVE_PANEL_RECOVERY',
        plan_SHA=sha(TARGET/'plan.json'),source_SHA=sha(__file__),idle_check_passed=True,
        no_Native_or_Optimize_in_admission=True,old_failures_retained=True))
    print(json.dumps(dict(decision='ADMIT_OBSERVED_PRE_NATIVE_PANEL_RECOVERY',remaining_positions=[3,4])),flush=True)


def run():
    configure();gate=read(GATE);plan=read(TARGET/'plan.json')
    assert gate['decision']=='ADMIT_OBSERVED_PRE_NATIVE_PANEL_RECOVERY' and gate['source_SHA']==sha(__file__)
    assert gate['plan_SHA']==sha(TARGET/'plan.json')
    with (TARGET/'started.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(UTC=utc(),pid=os.getpid(),**meter.process_birth(os.getpid()),plan_SHA=sha(TARGET/'plan.json')),stream,indent=2)
    state=dict(label=LABEL,decision='ADMITTED',completed=[])
    def record(**updates):
        state.update(updates,UTC=utc());write(TARGET/'status.json',state)
    def frozen():
        assert sha(OUT/'confirmation_matrix.json')==plan['matrix_SHA']
        for name,digest in plan['frozen_sources'].items():assert sha(ROOT/name)==digest,name
    try:
        frozen();assert not budget()['unclosed'];ensure_idle();record()
        matrix=read(OUT/'confirmation_matrix.json')
        for item in plan['jobs']:
            if (TARGET/'stop_requested.json').exists():record(decision='STOPPED_BEFORE_NEXT_CHILD');return
            frozen();assert not budget()['unclosed'] and not (OUT/'fees'/item['label']).exists()
            launch=matrix['groups'][item['position']-1]['launch']
            assert not Path(launch['destination']).exists()
            write(OUT/'active_position.json',dict(UTC=utc(),stage='complete_E',position=item['position'],arm_id=launch['arm_id'],fee_label=item['label']))
            record(decision='RUNNING_CHILD',current_job=item['label'])
            print(json.dumps(dict(queue=LABEL,starting=item['label'])),flush=True)
            common.run(item['label'],item['seconds'],'round155_campaign.py',['arm',str(item['position'])],kind='native')
            state['completed'].append(accepted(item['position'],item['label'],matrix));record(current_job=None)
        records=[accepted(p,'confirmation_003_retry_v1' if p==3 else f'confirmation_{p:03}',matrix) for p in range(1,7)]
        write(OUT/'panel_completion.json',dict(UTC=utc(),decision='ALL_SIX_FROZEN_ARMS_VERIFIED',
            matrix_SHA=plan['matrix_SHA'],accepted_arms=records,recovery_plan_SHA=sha(TARGET/'plan.json'),
            failed_attempts=[dict(label=plan['failed_fee_label'],receipt_SHA=plan['failed_receipt_SHA'])],
            no_production_or_algorithm_change=True,no_free_cross_arm_information=True))
        record(decision='ALL_SIX_FROZEN_ARMS_VERIFIED',panel_completion_SHA=sha(OUT/'panel_completion.json'))
        print(json.dumps(state),flush=True)
    except BaseException as error:
        record(decision='FAILED_STOPPED',error=repr(error));raise


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
