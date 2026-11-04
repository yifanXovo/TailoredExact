"""Wait for the admitted serial queue, then run only reviewed open-gap probes.

This supervisor is metadata bookkeeping, not an enclosing experimental fee.
Every new qualification/probe has exactly one common.run outer receipt.
It does not decide scientific completion, publication, or candidate adoption.
"""
from round153_common import *
from round153_common import run as run_child


def run():
    assert Path(sys.executable).resolve()==meter.DOCUMENT_PYTHON.resolve(), 'Use the direct ordinary metadata runtime, not the R88-venv launcher'
    assert not os.environ.get('ROUND140_METERED_PARENT_LABEL'), 'Waiting supervisor must not be an enclosing experiment fee'
    configure()
    gate=OUT/'review/primal_pool_design_review.md'
    assert gate.exists() and 'ACCEPT_FOR_SERIAL_SMALL_DISCOVERY_QUALIFICATION' in gate.read_text(encoding='utf-8')
    accepted='ef8190f6b6aa12730d4f6ab82658345fbb44d1358f45cfed363b8b59afa95da5'
    assert sha(ROOT/'scripts/round153_primal_pool.py')==accepted
    state=OUT/'afterqueue_status.json'
    write(state,dict(UTC=utc(),state='WAITING_FOR_REGISTERED_QUEUE',new_experiment_started=False))
    while True:
        status=read(OUT/'followthrough_status.json')
        if status.get('state')=='REGISTERED_QUEUE_CLOSED':break
        fee=OUT/'fees'/status.get('stage','')/'receipt.json'
        if status.get('stage')=='frozen_eight_position_campaign' and (OUT/'active_position.json').exists():
            fee=OUT/'fees'/read(OUT/'active_position.json')['fee_label']/'receipt.json'
        if fee.exists():
            r=read(fee)
            assert r['exit_code']==0 and r['exit_observed'] and not r['timeout'] and not r['supervisor_failure']
        time.sleep(10)
    assert not budget()['unclosed']
    # Queue closure alone is not enough: require all frozen endpoints and
    # both complete-Q support envelopes before admitting the diagnostics.
    matrix=read(OUT/'confirmation_matrix.json')
    assert sha(OUT/'confirmation_matrix.json')==read(OUT/'followthrough_plan.json')['production_matrix_SHA']
    assert read(OUT/'confirmation_run_return.json')['stop_after']==8
    for group in matrix['groups']:
        dest=Path(group['launch']['destination'])
        endpoint=read(dest/'round135_endpoint.json');close=read(dest/'verification_closeout.json')
        assert close['implementation_qualified'] and close['evidence_complete'] and close['performance_eligible']
        assert endpoint['arm_id']==group['launch']['arm_id']
        assert endpoint['verification_closeout_SHA']==sha(dest/'verification_closeout.json')
    assert len(matrix['groups'])==8
    probes=[]
    for role,tolerance in [('K-35-U',.0001),('N-C20-U',.00001)]:
        source=OUT/'coupled'/f'{role}_deepened_support_envelope'
        data=read(source/'result.json')
        assert data['decision']=='FREE_Q_SUPPORT_BOUND_TRANSFER'
        if data['upper']-data['lower']>tolerance:
            probes.append(dict(role=role,tolerance=tolerance,source=source.relative_to(ROOT).as_posix(),
                source_SHA=sha(source/'result.json'),observed_lower=data['lower'],observed_upper=data['upper']))
    assert budget()['remaining_G1_seconds']>=300+len(probes)*1600+3600+4800
    plan=OUT/'afterqueue_plan.json'
    assert not plan.exists()
    write(plan,dict(UTC=utc(),gate_SHA=sha(gate),implementation_SHA=accepted,probes=probes,
        frozen_eight_endpoints_closed_before_start=True,qualification_reservation=300,
        each_probe_reservation=1600,each_probe_internal_cap=1200,final_verification_and_margin_reserve=8400,
        no_automatic_extra_direction_or_production_change=True))
    if probes:
        write(state,dict(UTC=utc(),state='RUNNING',stage='primal_pool_qualification_v1'))
        run_child('primal_pool_qualification_v1',300,'round153_primal_pool.py',['qualify','primal_pool_v1'])
        for probe in probes:
            label=probe['role'].replace('-','')+'_primal_pool_v1'
            assert sha(ROOT/probe['source']/'result.json')==probe['source_SHA']
            write(state,dict(UTC=utc(),state='RUNNING',stage=label))
            run_child(label,1600,'round153_primal_pool.py',[
                'run',probe['role'],'primal_pool',probe['source'],'1200',str(probe['tolerance'])])
    write(state,dict(UTC=utc(),state='REVIEWED_DIAGNOSTICS_CLOSED',probes=probes,budget=budget(),
        study_completion_not_claimed=True,final_scientific_assessment_review_and_delivery_remain=True))
    print(json.dumps(read(state)),flush=True)


if __name__=='__main__':
    try:run()
    except BaseException as error:
        write(OUT/'afterqueue_status.json',dict(UTC=utc(),state='FAILED_STOPPED',error=repr(error),
            no_automatic_retry=True,study_completion_not_claimed=True))
        raise
