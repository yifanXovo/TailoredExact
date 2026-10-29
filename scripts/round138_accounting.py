"""Conservative qualification reclassification; immutable original fees remain."""
from round138_common import *

def main():
    rows=[]
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(path);receipt_path=path.parent/'receipt.json'
        if launch['kind']!='engineering' or not receipt_path.exists():continue
        executable=Path(launch['command'][0]).name
        if executable not in ['Round137Export.exe','Round138Export.exe']:continue
        receipt=read(receipt_path);assert receipt['G1_seconds']==0 and receipt['exit_observed']
        rows.append(dict(label=path.parent.name,kind='diagnostic',outer_seconds=receipt['outer_seconds'],
            source_fee=receipt_path.relative_to(ROOT).as_posix(),receipt_SHA=sha(receipt_path),
            qualification_native_read_Optimize=0,original_fee_not_modified=True))
    total=sum(r['outer_seconds'] for r in rows)
    write(OUT/'infra/external_costs.json',dict(schema='round138-qualification-reclassification-v1',UTC=utc(),processes=rows,
        policy='Goal G1 qualification charged conservatively even for zero-Optimize native model reads; same amount deducted once from final ordinary net',
        ordinary_reclassification_seconds=total,original_fee_receipts_unchanged=True))
    b=budget();paths=sorted((OUT/'ordinary_steps').glob('*/receipt.json'));steps=[read(p) for p in paths]
    write(OUT/'cost_report.json',dict(UTC=utc(),experiment=b,qualification_reclassification_count=len(rows),
        qualification_reclassification_seconds=total,fee_ordinary_raw_seconds=b['separately_reported_seconds'],
        fee_ordinary_net_seconds=b['separately_reported_seconds']-total,
        additional_disjoint_ordinary_steps_seconds=sum(r['seconds'] for r in steps),
        additional_disjoint_ordinary_steps=len(steps),no_nested_experiment_double_charge=True,
        ordinary_step_receipts=[dict(label=p.parent.name,receipt_SHA=sha(p),receipt=r) for p,r in zip(paths,steps)],
        ordinary_precision_scope='Individually metered build/verification and explicit ordinary steps; interactive reading, editing, review and intermediate Git/tool actions are not exhaustively timed',
        initial_interactive_reading_and_writing_not_precision_metered=True,
        during_native_offline_point_check_seconds=read(OUT/'reports/offline_products.json')['seconds'],
        during_native_offline_seconds_overlap_and_are_not_added_again=True))
    print(json.dumps(dict(qualification_positions=len(rows),qualification_seconds=total,
                         completed_G1_seconds=b['G1_seconds'],open_fees=len(b['unclosed']))))

if __name__=='__main__':main()
