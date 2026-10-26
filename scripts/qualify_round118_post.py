"""One paid H100 reconstruction/Start/admission driver; no solver on import."""
from round118_common import *
import traceback
import round118_campaign as campaign
import read_round118 as reader
import round112_audit as start

def admit_in_process(campaign_name,fee_label,label):
    tick=time.perf_counter();q=OUT/'qualification'/label;q.mkdir()
    # The actual parent wrapper is still running. This gate covers closed arms,
    # not its own future exit; formal preflight additionally requires its receipt.
    i=read(OUT/campaign_name/'identity.json')
    original=reader.read
    # Current reader's qualification path is explicit in its API.
    value=reader.rebuild(ROOT,q/'reconstructed',True,campaign_name)
    assert len(value['arms'])==2 and all(a['formal_protocol_qualified'] for a in value['arms'])
    assert len(value['same_H'])==1 and value['same_H'][0]['qualified']
    ps=i['launches'][0];assert ps['arm']=='P-S' and i['launches'][1]['arm']=='M-B'
    Start=start.start_audit(ROOT,ps['panel'],Path(ps['destination']));write(q/'actual_Start.json',Start)
    assert read(OUT/'qualification/finite05/summary.json')['passed'] and i['helpers']==helpers()
    write(q/'summary.json',dict(passed=True,actual_CLI=2,complete_same_H=True,full_original_Start=True,
        production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,helpers=helpers(),driver_processes=0,
        holder='charged H100 wrapper',OS_children=0,Optimize=0,seconds=time.perf_counter()-tick))
    write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
        helpers=helpers(),fixed_manifest_SHA=sha(OUT/'fixed_manifest.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source=SOURCE,input_SHA=read(OUT/'input_manifest.json')['roles'][0]['input_sha256'],
        finite_replay_SHA=sha(OUT/'qualification/finite05/summary.json'),H100_post_SHA=sha(q/'summary.json'),
        reference_receipt_SHA=sha(OUT/'fees/reference01/receipt.json'),H100_fee_launch_SHA=sha(OUT/'fees'/fee_label/'launch.json'),
        H100_actual_wrapper_exit_pending=True,H100_fee_label=fee_label,qualification_campaign=campaign_name,
        numerical_tolerance=1e-7,measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),frozen_UTC=utc(),
        scope='one V40 group; H100 does not qualify V40 difficulty/all future epochs',old_admission_not_reassigned=True,
        authorized_qualification_maximum_starts=11,total_maximum_starts=20,qualification_maximum_outer_seconds=1200))

def run(label):
    fee,tick=fee_begin(label,0,60,True);code=1
    try:
        q=OUT/'qualification'/label;q.mkdir()
        value=reader.rebuild(ROOT,q/'reconstructed',True)
        assert len(value['arms'])==2 and all(a['formal_protocol_qualified'] for a in value['arms'])
        assert len(value['same_H'])==1 and value['same_H'][0]['qualified']
        i=read(OUT/'qualification/cli01/identity.json');ps=i['launches'][0];assert ps['arm']=='P-S' and i['launches'][1]['arm']=='M-B'
        Start=start.start_audit(ROOT,ps['panel'],Path(ps['destination']))
        write(q/'actual_Start.json',Start)
        finite=read(OUT/'qualification/finite03/summary.json');assert finite['passed']
        assert i['helpers']==helpers() and read(OUT/'candidate_identity.json')['helpers']==helpers()
        write(q/'summary.json',dict(passed=True,actual_CLI=2,complete_same_H=True,full_original_Start=True,
            production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,helpers=helpers(),driver_processes=1,OS_children=0,Optimize=0))
        gate=dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),helpers=helpers(),
            fixed_manifest_SHA=sha(OUT/'fixed_manifest.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
            production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source=SOURCE,input_SHA=read(OUT/'input_manifest.json')['roles'][0]['input_sha256'],
            finite_replay_SHA=sha(OUT/'qualification/finite03/summary.json'),H100_post_SHA=sha(q/'summary.json'),
            reference_receipt_SHA=sha(OUT/'fees/reference01/receipt.json'),H100_cli_receipt_SHA=sha(OUT/'fees/cli01/receipt.json'),
            qualification_actual_budget=budget(),numerical_tolerance=1e-7,measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),
            frozen_UTC=utc(),scope='one V40 formal group; H100 does not qualify V40 difficulty or every future epoch',
            original_math_and_algorithms=True,old_admission_not_reassigned_to_new_helpers=True,known_log_risk_qualified=True)
        write(OUT/'review/performance_admission.json',gate);code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])
