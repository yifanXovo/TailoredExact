"""Continue a node-limited undecided price with the already qualified first rule.

This is an offline allocation after actual readbacks, not a new formulation
or a production policy keyed by instance. The old closed phase stays intact.
Every child is serial, separately metered, and stops on any failure.
"""
from round155_common import *


def prepare(label='nc_stalled_continuation_v1'):
    from round100_idle import ensure_idle
    configure();ensure_idle();account=budget()
    own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert [item['label'] for item in account['unclosed']]==[own]
    parent=OUT/'infra/remaining_capacity_queue_v3'
    state=read(parent/'status.json');identity=read(parent/'started.json')
    assert state['decision']=='REMAINING_RESEARCH_AND_RAW_READBACK_COMPLETE_FINAL_JUDGMENT_REQUIRED'
    birth=meter.process_birth(identity['pid'])
    assert not birth or birth['creation_filetime']!=identity['creation_filetime']
    for item in state['completed']:
        receipt=OUT/'fees'/item['label']/'receipt.json';value=read(receipt)
        assert sha(receipt)==item['receipt_SHA'] and value['exit_observed'] and value['exit_code']==0
        assert not value['timeout'] and not value['supervisor_failure']
    gate=read(OUT/'review/loop_admission.json')
    for key,name in [('source_SHA','round155_loop.py'),('oracle_SHA','round155_oracle.py'),
                     ('price_certificate_SHA','round155_price_certificate.py')]:
        assert gate[key]==sha(ROOT/'scripts'/name)
    assert gate['decision']=='ACCEPT'
    source=OUT/'coupled/N-C20-U_bounded_remaining_v1/result.json';prior=read(source)
    assert prior['decision']=='undecided_price_no_new_column' and not prior['refresh_required']
    last=prior['records'][-1]
    assert last['added']==last['added_negative']==0 and not last['target_proved'] and not last['target_disproved']
    price=source.parent/f'iter{last["iteration"]:06}'/'pricing/result.json';p=read(price)
    assert p['decision']=='UNDECIDED' and len(p['calls'])==1
    assert p['calls'][0]['Status']==8 and p['calls'][0]['nodes']==256
    audit=OUT/'qualification/NC20_remaining_deep_readback_v1/result.json';checked=read(audit)
    assert checked['PASS'] and checked['Optimize']==0 and len(checked['phases'])==1
    assert checked['phases'][0]['SHA256']==sha(source)
    replay=OUT/'support_LP/N-C20-U_remaining_deep_support_v1/result.json';r=read(replay)
    support_check=OUT/'qualification/NC20_remaining_support_readback_v1/result.json';s=read(support_check)
    assert s['PASS'] and s['Optimize']==0 and len(s['replays'])==1
    assert s['replays'][0]['SHA256']==sha(replay)
    # Preserve the actual last optimal basis and complete pool. Replaying the
    # supports must not have obtained a stronger bound that this source loses.
    assert r['lower']==prior['lower'] and r['upper']==prior['upper']
    assert r['columns']==prior['columns'] and r['supports']==prior['supports']
    basis=source.parent/'last_master.bas';assert basis.exists()
    paid=[]
    for name in ['NC20_feasible_level_deep_v2','NC20_bounded_remaining_v1']:
        path=OUT/'fees'/name/'receipt.json';v=read(path)
        assert v['exit_observed'] and v['exit_code']==0 and not v['timeout']
        paid.append(dict(label=name,SHA256=sha(path),G1_seconds=v['G1_seconds']))
    reservation=math.floor(28800-sum(v['G1_seconds'] for v in paid))
    assert reservation>2400
    phase='first_stalled_continuation_v1';role='N-C20-U'
    def job(name,seconds,script,*args,kind='verification'):
        return dict(label=name,seconds=seconds,script=script,args=list(args),kind=kind)
    jobs=[job('NC20_'+phase,reservation,'round155_loop.py','run',role,phase,'first',
              str(reservation-600),'0',str(source),'1200',kind='research'),
          job('NC20_stalled_continuation_readback_v1',10800,'round155_audit.py','loops',
              'NC20_stalled_continuation_readback_v1',role+'_'+phase),
          job('NC20_stalled_continuation_support_v1',600,'round155_loop.py','replay',role,
              'stalled_continuation_support_v1',str(OUT/'coupled'/f'{role}_{phase}'/'result.json')),
          job('NC20_stalled_continuation_support_readback_v1',600,'round155_audit.py','support_replays',
              'NC20_stalled_continuation_support_readback_v1',role+'_stalled_continuation_support_v1'),
          job('final_raw_research_report_v2',600,'round155_reports.py','research')]
    assert account['remaining_G1_seconds']-account['unclosed'][0]['reservation']>sum(v['seconds'] for v in jobs)+7200
    for item in jobs:assert not (OUT/'fees'/item['label']).exists()
    target=OUT/'infra'/label;target.mkdir(parents=True,exist_ok=False)
    report_snapshot={};saved=target/'preceding_research_reports';saved.mkdir()
    for name in ['research_phases.csv','research_phases.json','coupled_trajectory.csv',
                 'column_quality.csv','matched_loop_comparisons.csv']:
        path=OUT/'reports'/name;destination=saved/name
        destination.write_bytes(path.read_bytes())
        assert sha(destination)==sha(path)
        report_snapshot[name]=dict(path=str(destination),SHA256=sha(destination))
    names=['round155_nc_continue.py','round155_loop.py','round155_oracle.py','round155_price_certificate.py',
           'round155_common.py','round155_audit.py','round155_reports.py']
    plan=dict(UTC=utc(),label=label,decision='ADMIT_UNDECIDED_NODE_LIMIT_CONTINUATION',
        predecessor_status_SHA=sha(parent/'status.json'),predecessor_identity=identity,
        source=str(source),source_SHA=sha(source),basis=str(basis),basis_SHA=sha(basis),
        stalled_price=str(price),stalled_price_SHA=sha(price),general_readback_SHA=sha(audit),
        support_readback_SHA=sha(support_check),support_replay_SHA=sha(replay),
        existing_interface_gate_SHA=sha(OUT/'review/loop_admission.json'),
        frozen_sources={name:sha(ROOT/'scripts'/name) for name in names},jobs=jobs,
        actual_prior_deep_fees=paid,remaining_eight_hour_reference_seconds=reservation,
        rule='existing first-counterexample oracle, no fixed node limit, price cap1200s',
        no_iteration_count_limit=True,scope_and_Q_unchanged=True,original_tolerance=1e-4,
        Seed=0,Threads=1,selection='current optimal RMP basic dual',
        trigger='previous bounded256 call exhausted its node allowance, returned only existing columns, and left its target undecided',
        no_new_selector_formulation_or_parameter_grid=True,no_new_production_policy=True,
        old_phase_is_not_saturation_evidence=True,no_automatic_publication_or_goal_completion=True,
        preserved_preceding_research_reports=report_snapshot,budget_at_preparation=account)
    write(target/'plan.json',plan)
    print(json.dumps(dict(decision=plan['decision'],label=label,reservation=reservation,jobs=len(jobs))),flush=True)


def run(label='nc_stalled_continuation_v1'):
    configure();target=OUT/'infra'/label;plan=read(target/'plan.json')
    with (target/'started.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(UTC=utc(),pid=os.getpid(),**meter.process_birth(os.getpid()),plan_SHA=sha(target/'plan.json')),stream,indent=2)
    state=dict(label=label,completed=[],decision='STARTING')
    def record(**values):state.update(values,UTC=utc());write(target/'status.json',state)
    try:
        assert sha(plan['source'])==plan['source_SHA'] and sha(plan['basis'])==plan['basis_SHA']
        for item in plan['jobs']:
            assert not (target/'stop_requested.json').exists(),'review stop requested before next child'
            for name,digest in plan['frozen_sources'].items():assert sha(ROOT/'scripts'/name)==digest
            assert not budget()['unclosed'] and not (OUT/'fees'/item['label']).exists()
            record(decision='RUNNING_CHILD',current_job=item['label'],command=item)
            print(json.dumps(dict(queue=label,starting=item['label'])),flush=True)
            import round155_common as common
            common.run(item['label'],item['seconds'],item['script'],item['args'],kind=item['kind'])
            rp=OUT/'fees'/item['label']/'receipt.json';receipt=read(rp)
            assert receipt['exit_observed'] and receipt['exit_code']==0 and not receipt['timeout'] and not receipt['supervisor_failure']
            state['completed'].append(dict(label=item['label'],G1_seconds=receipt['G1_seconds'],receipt_SHA=sha(rp)))
            record(current_job=None)
        record(decision='CONTINUATION_AND_READBACK_COMPLETE_FINAL_JUDGMENT_REQUIRED')
        print(json.dumps(state),flush=True)
    except BaseException as error:
        record(decision='FAILED_STOPPED',error=repr(error));raise


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
