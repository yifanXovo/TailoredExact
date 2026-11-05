"""Close the admitted interior study before the independent frozen panel."""
from round154_common import *

def run_finalization():
    configure();assert not budget()['unclosed']
    label='NC20_updated_midpoint';parent=OUT/'fixed_prices'/label
    assert (parent/'RN_goal_screen/hull_result.json').exists() and (parent/'residual_goal_screen/hull_result.json').exists()
    terminal=list(parent.glob('*_long/hull_result.json'))
    assert (parent/'long_skip.json').exists() or (parent/'remaining_long_skip.json').exists() or len(terminal)==2,'registered study must reach its own stopping decision'
    for receipt in (OUT/'fees').glob(label+'*/receipt.json'):assert read(receipt)['exit_code']==0
    prices=sorted(str(p.parent) for p in parent.glob('*/hull_result.json'))
    prior=OUT/'support_LP/N-C20-U_target_residual_v1/result.json'
    run('NC20_interior_ingest_v1',300,'round154_coupled.py',['ingest','N-C20-U','after_interior',''+str(prior),*prices])
    ingested=OUT/'coupled/N-C20-U_after_interior/result.json'
    run('NC20_interior_support_v1',300,'round154_coupled.py',['replay','N-C20-U','after_interior',str(ingested)])
    supported=OUT/'support_LP/N-C20-U_after_interior/result.json'
    if read(supported)['refresh_required']:
        run('NC20_interior_final_refresh_v1',300,'round154_coupled.py',['refresh','N-C20-U','interior_final_refresh',str(supported)])
        final=OUT/'coupled/N-C20-U_interior_final_refresh/result.json'
    else:final=supported
    assert not read(final)['refresh_required']
    old=next(r for r in read(OLD153/'reports/scientific_table.json')['rows'] if r['role']=='N-B35-S')
    write(OUT/'science_state.json',dict(UTC=utc(),roles={
        'N-B35-S':dict(result=str(ROOT/old['coupled_result']),support_result=str(ROOT/old['support_result']),
            inherited_global_lower=old['coupled_L'],no_new_NB_pricing=True),
        'K-35-U':dict(result=str(OUT/'support_LP/K-35-U_target_residual_v2/result.json'),support_result=str(OUT/'support_LP/K-35-U_target_residual_v2/result.json')),
        'N-C20-U':dict(result=str(final),support_result=str(supported))},
        every_new_column_evaluated=True,all_new_supports_replayed_in_complete_free_Q=True,
        inherited_NB_support_gain_retained=True,full_hull_accuracy_target=1e-4))
    from round154_reports import prices as price_report,coupled,science,costs
    price_report();coupled();science();costs()
    print(json.dumps(dict(main_research_closed=True,science_state_SHA=sha(OUT/'science_state.json'),budget=budget())),flush=True)

if __name__=='__main__':run_finalization()
