"""Aggregate already closed receipts; no experimental work or added fee.

This lightweight administrative readback is disclosed separately. It does
not relabel nested Native Runtime/Work or helper timing as additional cost.
"""
from round156_common import *

def stage(label,kind):
    if kind=='build':return 'compilation_separate'
    if label.startswith('confirmation_'):return 'complete_panel_and_own_verification'
    if label.startswith('smoke_'):return 'integration_complete_smokes'
    if label.startswith(('initial_identity','r155_clock','r155_errata')):return 'identity_and_report_correction'
    if label.startswith('rx35_'):return 'matched_original_inventory_oracles'
    if label.startswith('fresh_') and not 'audit' in label:return 'uniform_fresh_producer_checks'
    if label.startswith(('residual_admit','rn_admit')):return 'targeted_math_and_interface_qualification'
    return 'evidence_review_and_final_verification'

def run():
    tick=time.perf_counter();configure();b=budget();assert not b['unclosed']
    receipts=[];by_stage={};failures=[];intervals=[]
    for path in sorted((OUT/'fees').glob('*/receipt.json')):
        label=path.parent.name;r=read(path);launch=read(path.parent/'launch.json')
        assert r['exit_observed'] and r['G1_seconds']>=0 and r['separately_reported_seconds']>=0
        assert abs(r['outer_seconds']-r['G1_seconds']-r['separately_reported_seconds'])<1e-8
        assert r['nested_H_LP_MIP_not_added']
        category=stage(label,launch['kind'])
        fact=dict(label=label,stage=category,budget_kind=launch['kind'],G1_seconds=r['G1_seconds'],
            separately_reported_seconds=r['separately_reported_seconds'],outer_seconds=r['outer_seconds'],
            exit_code=r['exit_code'],timeout=r['timeout'],receipt_SHA=sha(path),launch_SHA=sha(path.parent/'launch.json'),
            start_unix=r['start_unix'],end_unix=r['end_unix'])
        receipts.append(fact);by_stage[category]=by_stage.get(category,0.)+r['G1_seconds']
        intervals.append(fact)
        if r['exit_code'] or r['timeout'] or r['supervisor_failure']:failures.append(fact)
    ordered=sorted(intervals,key=lambda r:r['start_unix'])
    for first,second in zip(ordered,ordered[1:]):assert first['end_unix']<=second['start_unix'],(first['label'],second['label'])
    assert abs(sum(r['G1_seconds'] for r in receipts)-b['G1_seconds'])<1e-8
    assert abs(sum(r['separately_reported_seconds'] for r in receipts)-b['separately_reported_seconds'])<1e-8
    assert b['G1_seconds']<=172800
    panel=[r for r in receipts if r['label'].startswith('confirmation_')]
    assert len(panel)==9 and all(r['exit_code']==0 and not r['timeout'] for r in panel)
    write(OUT/'cost_report.json',dict(UTC=utc(),total_G1_seconds=b['G1_seconds'],total_G1_hours=b['G1_seconds']/3600,
        capacity_seconds=172800,remaining_capacity_seconds=b['remaining_G1_seconds'],by_budget_category=b['by_category'],
        by_descriptive_stage=by_stage,all_closed_receipts=receipts,actual_failed_children=failures,
        complete_panel_seconds=sum(r['G1_seconds'] for r in panel),separately_reported_build_seconds=b['separately_reported_seconds'],
        nested_Runtime_Work_H_helper_not_added=True,all_metered_outer_intervals_serial=True,
        stage_capacities_are_adjustable_not_minimum_spend=True,
        initial_setup_disclosure='Initial tool-only source/history/workspace metadata reads and isolated-worktree creation were not outer-metered. No fabricated estimate or corrective performance rerun is supplied.',
        separate_scope='Compilation is separately measured in its build receipt. Pure writing, lightweight source/receipt/status bookkeeping and public packaging/recovery I/O are outside G1; public I/O has its own receipts.',
        administration_seconds=time.perf_counter()-tick,administration_source_SHA=sha(__file__)))
    print(json.dumps(dict(G1_seconds=b['G1_seconds'],hours=b['G1_seconds']/3600,
        failed_children=len(failures),complete_panel_seconds=sum(r['G1_seconds'] for r in panel),
        separate_build_seconds=b['separately_reported_seconds'])),flush=True)

if __name__=='__main__':run()
