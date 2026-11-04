"""Serial execution of already reviewed research and confirmation windows.

This supervisor adds no experiment and no nested outer charge. Every child
research step uses common.run; the frozen campaign meters its own arms.
Failures stop the queue with prior receipts/raw unchanged.
"""
from round153_common import *
from round153_common import run as run_child


def run():
    configure();assert not budget()['unclosed']
    predecessor=read(OUT/'fees/K35_saved_direction_long_v1/receipt.json')
    assert predecessor['exit_code']==0 and predecessor['exit_observed']
    assert not predecessor['timeout'] and not predecessor['supervisor_failure']
    assert (OUT/'coupled/K-35-U_saved_direction_long/result.json').exists()
    gates=['cut_pricing_design_review.md','k35_targeted_deepening_review.md','nc20_deepening_review.md']
    gate_hashes={name:sha(OUT/'review'/name) for name in gates}
    steps=[
        ('graphcut_qualification_v1',600,'round153_graphcut.py',['qualify','graphcut_v1']),
        ('NC20_saved_direction_graphcut_v1',1200,'round153_refine.py',[
            'N-C20-U','saved_direction_graphcut','results/unified_exact_round153/coupled/N-C20-U_saved_direction_transport',
            'results/unified_exact_round153/coupled/N-C20-U_level_zero_continued/iter00008','600','16','graphcut']),
        ('K35_saved_direction_graphcut_v1',1200,'round153_refine.py',[
            'K-35-U','saved_direction_graphcut','results/unified_exact_round153/coupled/K-35-U_saved_direction_long',
            'results/unified_exact_round153/coupled/K-35-U_price_deep/iter00003','600','16','graphcut']),
        ('NC20_saved_direction_long_v1',2200,'round153_refine.py',[
            'N-C20-U','saved_direction_long','results/unified_exact_round153/coupled/N-C20-U_saved_direction_graphcut',
            'results/unified_exact_round153/coupled/N-C20-U_level_zero_continued/iter00008','1800','1','partition']),
        ('K35_near_optimal_zero_pool_v1',7600,'round153_coupled.py',[
            'K-35-U','near_optimal_zero_pool','7200','300','0.0001','true',
            'results/unified_exact_round153/coupled/K-35-U_saved_direction_graphcut','zero_pool']),
        ('NC20_near_optimal_zero_pool_v1',5800,'round153_coupled.py',[
            'N-C20-U','near_optimal_zero_pool','5400','300','0.00001','true',
            'results/unified_exact_round153/coupled/N-C20-U_saved_direction_long','zero_pool']),
        ('K35_deepened_support_envelope_v1',600,'round153_attribution.py',[
            'support_close','K-35-U','results/unified_exact_round153/coupled/K-35-U_near_optimal_zero_pool','deepened_support_envelope']),
        ('NC20_deepened_support_envelope_v1',600,'round153_attribution.py',[
            'support_close','N-C20-U','results/unified_exact_round153/coupled/N-C20-U_near_optimal_zero_pool','deepened_support_envelope'])]
    path=OUT/'followthrough_plan.json'
    if not path.exists():write(path,dict(UTC=utc(),gates=gate_hashes,steps=steps,
        production_matrix_SHA=sha(OUT/'confirmation_matrix.json'),serial=True,
        no_adaptive_oracle_adoption=True,normal_qualified_arms_complete_their_registered_windows=True))
    else:assert read(path)['steps']==[list(s[:3])+[s[3]] for s in steps]
    pending=sum(s[1] for s in steps if not (OUT/'fees'/s[0]/'receipt.json').exists())
    assert budget()['remaining_G1_seconds']>=pending+16800+8*600+4800
    for label,reservation,script,args in steps:
        fee=OUT/'fees'/label
        if fee.exists():
            assert (fee/'receipt.json').exists(),'Open predecessor must finish before queue resume'
            receipt=read(fee/'receipt.json');assert receipt['exit_code']==0 and receipt['exit_observed'],'Inspect failed evidence; never rerun'
            assert not receipt['timeout'] and not receipt['supervisor_failure']
            continue
        write(OUT/'followthrough_status.json',dict(UTC=utc(),stage=label,state='RUNNING',registered_queue=True))
        print(json.dumps(dict(stage=label,state='START')),flush=True)
        run_child(label,reservation,script,args)
        print(json.dumps(dict(stage=label,state='CLOSED',receipt=read(fee/'receipt.json'))),flush=True)
    from round153_campaign import run as campaign
    write(OUT/'followthrough_status.json',dict(UTC=utc(),stage='frozen_eight_position_campaign',state='RUNNING'))
    campaign(8)
    write(OUT/'followthrough_status.json',dict(UTC=utc(),state='REGISTERED_QUEUE_CLOSED',budget=budget(),
        study_completion_not_claimed=True,final_scientific_review_and_delivery_remain=True))


if __name__=='__main__':
    run()
