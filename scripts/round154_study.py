"""Finite serial study queues; no background continuation is implicit."""
from round154_common import *

def screen():
    for label in ['K35_saved','NC20_fresh']:
        for implementation in ['RN','residual']:
            run(f'{label}_{implementation}_screen_v1',240,'round154_targets.py',
                ['compare',label,implementation,'60','screen'])

def K_long():
    gate=read(OUT/'review/long_price_admission.json')
    assert gate['decision']=='ACCEPT' and gate['independent_nonimplementer_review']
    assert gate['plan_SHA']==sha(OUT/'deepening_plan.md')
    run('K35_strong_long_v1',3900,'round154_targets.py',
        ['compare','K35_saved','residual_strong','3600','long'])
    first=read(OUT/'fixed_prices/K35_saved/residual_strong_long/hull_result.json')
    if first['target_disproved']:
        write(OUT/'fixed_prices/K35_saved/RN_long_skip.json',dict(reason='fixed_target_disproved_by_true_stock',
              new_ceiling=first['fixed_certificate_ceiling'],no_negative_family_claim=True))
    else:
        run('K35_RN_long_v1',3900,'round154_targets.py',
            ['compare','K35_saved','RN','3600','long'])

if __name__=='__main__':globals()[sys.argv[1]]()
