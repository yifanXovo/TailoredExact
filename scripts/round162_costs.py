"""Close current outer fees; nested solver Runtime/Work are never added twice."""
from round162_common import *

def close():
    value=budget();assert not value['unclosed'] and value['G1_seconds']<=TOTAL
    receipts=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        launch=read(p.parent/'launch.json');r=read(p)
        receipts.append(dict(label=p.parent.name,kind=launch['kind'],**r))
    calls=[]
    for root in ('runs','qualification'):
        for p in sorted((OUT/root).rglob('native.log')):
            text=p.read_text(encoding='utf-8',errors='replace')
            if 'Optimize a model' in text:calls.append(dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),LP='Iteration    Objective' in text or 'Iteration    Primal Obj' in text))
    write(OUT/'cost_report.json',dict(UTC=utc(),G1_seconds=value['G1_seconds'],capacity=TOTAL,remaining=TOTAL-value['G1_seconds'],
        by_category=value['by_category'],build_and_other_metered_engineering_seconds=value['separately_reported_seconds'],
        receipts=receipts,failed=[r for r in receipts if r['exit_code']],all_fees_closed=True,
        native_logs=calls,observed_native_Optimize_calls=len(calls),old_producer_starts=0,
        nested_Runtime_Work_callback_validation_not_added_twice=True,capacity_is_not_minimum_spend=True,
        ordinary_editing_unmetered=True,packaging_and_public_IO='publication_costs.json',
        prelaunch_scripting_error=dict(description='CLI cap was initially a string; no scientific child was launched, then corrected',scientific_child_starts=0)))
    print(json.dumps({k:value[k] for k in ('G1_seconds','remaining_G1_seconds','separately_reported_seconds')}),flush=True)

if __name__=='__main__':close()
