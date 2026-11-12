"""Closed nonoverlapping scientific fees and separately labelled ordinary work."""
from round164_common import *
import csv

def run():
    value=budget();assert not value['unclosed'] and value['G1_seconds']<=TOTAL
    fees=[];failures=[]
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(path);receipt=read(path.parent/'receipt.json')
        row=dict(label=path.parent.name,kind=launch['kind'],exit_code=receipt['exit_code'],timeout=receipt['timeout'],
            reservation_seconds=launch['reservation_seconds'],fault_timeout_seconds=launch['timeout_seconds'],
            outer_seconds=receipt['outer_seconds'],scientific_seconds=receipt['G1_seconds'],
            separately_reported_seconds=receipt['separately_reported_seconds'],
            start_unix=receipt['start_unix'],end_unix=receipt['end_unix'],exit_observed=receipt['exit_observed'])
        assert row['exit_observed'];fees.append(row)
        if row['exit_code'] or row['timeout']:failures.append(row)
    chronological=sorted(fees,key=lambda r:r['start_unix'])
    assert all(a['end_unix']<=b['start_unix'] for a,b in zip(chronological,chronological[1:])), 'overlapping scientific outer fees'
    external=read(OUT/'infra/external_costs.json')['processes'] if (OUT/'infra/external_costs.json').exists() else []
    assert abs(sum(r['scientific_seconds'] for r in fees)+sum(r['outer_seconds'] for r in external)-value['G1_seconds'])<1e-6
    ordinary=[]
    for name,key in [('table_authoring.json','ordinary_authoring_IO_seconds'),
        ('main_table_update.json','ordinary_transport_IO_seconds'),('carrier_manifest.json','packaging_IO_seconds'),
        ('public_restore_receipt.json','recovery_IO_seconds')]:
        if (OUT/name).exists():ordinary.append(dict(source=name,seconds=read(OUT/name)[key],category='ordinary authoring/transport I/O, outside science'))
    arms=read(OUT/'reports/complete_arms.json') if (OUT/'reports/complete_arms.json').exists() else []
    write(OUT/'cost_report.json',dict(UTC=utc(),scientific_seconds=value['G1_seconds'],scientific_hours=value['G1_seconds']/3600,
        scientific_capacity_seconds=TOTAL,remaining_scientific_seconds=value['remaining_G1_seconds'],
        measured_by_category=value['by_category'],original_reservation_plan=read(OUT/'protocol.json')['allocations'],
        stages_transferable_within_hard_total=True,closed_outer_processes=fees,external_nonoverlapping_scientific_segments=external,
        technical_failures=failures,technical_failure_count=len(failures),formal_arms=len(arms),
        T_produce_sum=sum(a['T_produce'] for a in arms),T_verify_sum=sum(a['T_verify'] for a in arms),
        T_total_sum=sum(a['T_total'] for a in arms),formal_scientific_outer_sum=sum(a['scientific_outer_seconds'] for a in arms),
        all_recorded_fees_closed=True,nested_Runtime_Work_H_helper_not_added=True,
        helper_Optimize_or_processes=0,production_rebuilds=0,
        reservation_margin_is_not_added_Native_runtime=True,fault_timeout_policy_unchanged='cap+900, bounded by remaining science',
        qualification_batch='six tiny nonperformance lifecycles; paid once at the enclosing outer, never compared as formal sample clocks',
        separately_observed_ordinary_work=ordinary,separate_measured_ordinary_IO_seconds=sum(v['seconds'] for v in ordinary),
        ordinary_preparation_and_writing='ordinary_work_record.json; enclosing wall intervals are not exact I/O or Optimize seconds',
        published_timing_scope='producer-close T_cert only on own qualified certificates; no OPEN cap imputation'))
    for filename,records in [('cost_failures.csv',fees),('failures.csv',failures)]:
        if records:
            target=OUT/'reports'/filename;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    print(json.dumps(dict(scientific_seconds=value['G1_seconds'],capacity=TOTAL,closed_fees=len(fees),failures=len(failures))))

if __name__=='__main__':run()
