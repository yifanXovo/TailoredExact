"""Closed-fee resource snapshots; never runs a solver or invents a future fee.

Run only after the formal parent observer and all substantive child tasks stop.
The brief accounting command itself belongs to the explicitly declared final
administrative allowance; it does not open a self-referential child fee.
"""
from round127_common import *
import argparse,math


def close(a,b,tolerance=1e-5):
    assert abs(a-b)<=tolerance,(a,b)


def merged(intervals):
    result=[]
    for a,b in sorted(intervals):
        assert b>=a,(a,b)
        if result and a<=result[-1][1]:result[-1][1]=max(result[-1][1],b)
        else:result.append([a,b])
    return result


def complement(start,end,intervals):
    result=[];cursor=start
    for a,b in merged([(max(start,a),min(end,b)) for a,b in intervals if min(end,b)>max(start,a)]):
        if a>cursor:result.append([cursor,a])
        cursor=max(cursor,b)
    if end>cursor:result.append([cursor,end])
    return result


def snapshot(phase):
    current=budget();assert not current['unclosed'],current
    formal_segments=[(p.parent.name,read(p)) for p in (OUT/'fees').glob('formal_evaluation*parent_gaps/receipt.json')]
    formal_segments.sort(key=lambda item:item[1]['actual_parent_birth_unix'])
    assert formal_segments and formal_segments[-1][1]['exit_code']==0,'final formal segment did not close successfully'
    assert all(r['outer_interval_complement'] for _,r in formal_segments)
    if any(r['exit_code']!=0 for _,r in formal_segments):
        # The failed original driver remains an actual paid segment. The
        # recovered arm uses its original sealed producer, not a native retry.
        assert read(OUT/'review/tiny07_failure_snapshot/preservation.json')['status']=='FAILURE_EVIDENCE_PRESERVED'
        recovery=read(OUT/'review/tiny07_readonly_verification_attempts/attempt02/receipt.json')
        assert recovery['status']=='PASS' and recovery['Optimize']==0
        assert all(recovery['original_producer_bytes_unchanged'].values())
    summary=read(OUT/'stratified_summary.json')
    assert summary['observed_formal_arms']==54 and summary['blocked_core_arms']==3 and summary['all_observed_arms_qualified']
    live=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|MSBuild)\\.exe$' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not live,('performance/build process active',live)
    ledger=[];intervals=[];allowances=[];parents=[];unlocated=[]
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(path);receipt=read(path.parent/'receipt.json');seconds=receipt['outer_seconds']
        assert math.isfinite(seconds) and seconds>=0 and receipt.get('nested_seconds_added') is False
        entry=dict(label=path.parent.name,kind=launch['kind'],outer_seconds=seconds,
            exit_code=receipt.get('exit_code'),launch_SHA256=sha(path),receipt_SHA256=sha(path.parent/'receipt.json'),
            launch_record=launch,outer_receipt=receipt)
        if receipt.get('outer_interval_complement'):
            entry['measurement']='actual parent lifetime outside the union of metered child intervals'
            parents.append((entry,receipt))
        elif 'start_unix' in receipt and 'end_unix' in receipt:
            a,b=receipt['start_unix'],receipt['end_unix'];assert b>=a
            close(b-a,seconds,.05)
            entry.update(measurement='observed complete child outer duration',start_unix=a,end_unix=b)
            intervals.append((a,b,entry['label']))
        elif 'upper allowance' in receipt.get('measurement','').lower():
            entry['measurement']=receipt['measurement'];allowances.append(entry)
        else:
            entry['measurement']='duration retained without an epoch interval; interval-union proof unavailable'
            unlocated.append(entry['label'])
        ledger.append(entry)
    overlaps=[]
    ordered=sorted(intervals);prior=None
    for a,b,label in ordered:
        if prior and a<prior[1]-1e-6:overlaps.append(dict(left=prior[2],right=label,overlap_seconds=prior[1]-a))
        if prior is None or b>prior[1]:prior=(a,b,label)
    assert not overlaps,('overlapping child fees require investigation',overlaps)
    parent_checks=[]
    for entry,receipt in parents:
        birth,end=receipt['actual_parent_birth_unix'],receipt['actual_parent_exit_unix']
        gaps=complement(birth,end,[(a,b) for a,b,label in intervals])
        close(sum(b-a for a,b in gaps),entry['outer_seconds'])
        assert len(gaps)==len(receipt['uncovered_intervals'])
        for actual,saved in zip(gaps,receipt['uncovered_intervals']):
            close(actual[0],saved[0]);close(actual[1],saved[1])
        parent_checks.append(dict(label=entry['label'],actual_parent_birth_unix=birth,
            actual_parent_exit_unix=end,charged_gap_seconds=entry['outer_seconds'],
            parent_exit_code=receipt['exit_code'],
            recomputed_from_closed_child_interval_union=True,observer_wait_not_billed_again=receipt['observer_wait_not_charged_again']))
    initialization=read(OUT/'initialization.json');setup=initialization['preledger_outer_upper_seconds']
    paid=setup+sum(row['outer_seconds'] for row in ledger);close(paid,current['paid_outer_seconds'])
    assert paid<=TOTAL_LIMIT
    recovery=read(OUT/'public_restore_receipt.json') if (OUT/'public_restore_receipt.json').exists() else None
    if phase=='post_recovery':
        assert recovery and recovery['status']=='PASS' and recovery['Optimize']==0
        assert any(row['label']=='final_publication_administration' for row in allowances),'Declare the bounded final administrative allowance before the final snapshot'
    report=dict(schema='round127-closed-outer-fee-snapshot-v1',UTC=utc(),phase=phase,
        machine_outer_limit_seconds=TOTAL_LIMIT,**current,closed_fee_count=len(ledger),
        measured_child_outer_seconds=sum(r['outer_seconds'] for r in ledger if r['measurement']=='observed complete child outer duration'),
        measured_parent_management_gap_seconds=sum(r['charged_gap_seconds'] for r in parent_checks),
        conservative_upper_allowance_seconds=setup+sum(r['outer_seconds'] for r in allowances),
        preledger_allowance=dict(seconds=setup,explanation=initialization['preledger_explanation']),
        explicit_fee_allowances=allowances,child_fee_interval_overlaps=overlaps,
        fee_labels_without_epoch_interval=unlocated,parent_gap_checks=parent_checks,
        formal_driver_segments=[dict(label=label,exit_code=r['exit_code'],
            actual_parent_birth_unix=r['actual_parent_birth_unix'],actual_parent_exit_unix=r['actual_parent_exit_unix'],
            charged_management_gap_seconds=r['outer_seconds']) for label,r in formal_segments],
        failed_child_fee_labels=[r['label'] for r in ledger if r['exit_code'] not in [0,None]],
        actual_formal_arms=54,training_runs=36,blocked_MD_positions=3,PT_aliases=0,
        nested_H_LP_MIP_added_again=False,CPU_time_claimed=False,closed_fee_ledger=ledger,
        public_recovery_commit=recovery['commit'] if recovery else None,
        snapshot_boundary='Closed actual fees plus explicitly labeled conservative upper administrative allowances at this UTC; no claim that science A proves future B or future receipts.',
        light_command_accounting='Brief direct bookkeeping commands are covered by the declared administrative allowance; substantial build/solve/review/document/archive/recovery child tasks retain their own outer receipts.')
    write(OUT/'resource_accounting.json',report)
    print(json.dumps(dict(phase=phase,paid_outer_seconds=paid,remaining_outer_seconds=TOTAL_LIMIT-paid,
        fee_count=len(ledger),upper_allowance_seconds=report['conservative_upper_allowance_seconds'],
        parent_gap_checks=len(parent_checks),unlocated_intervals=unlocated)))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['prepublication','post_recovery'],required=True)
    snapshot(parser.parse_args().phase)
