"""Administrative aggregation of closed Round157 outer fees, with failures."""
from round157_common import *

def stage(label,kind):
    if kind=='build':return 'compilation_separate'
    if label.startswith('complete_'):return 'conditional_complete_panel'
    if 'qualification' in label or 'predeep' in label or label.startswith(('prepare','inventory')):return 'setup_and_necessary_qualification'
    if label.startswith(('rx35_fixed','rx35_family','nb35_fixed','nb35_family','resource_rx35_family','resource_nb35_family','tour_rx35','tour_nb35')):return 'preselected_physical_comparison'
    if label.startswith(('deepen','resource_','level_','time_','family_floor')):return 'evidence_based_deepening'
    return 'paper_and_final_verification'

def run():
    configure();b=budget();assert not b['unclosed'];facts=[];stages={};failures=[]
    for path in sorted((OUT/'fees').glob('*/receipt.json')):
        receipt=read(path);launch=read(path.parent/'launch.json');label=path.parent.name
        assert receipt['exit_observed'] and receipt['nested_H_LP_MIP_not_added']
        assert abs(receipt['outer_seconds']-receipt['G1_seconds']-receipt['separately_reported_seconds'])<1e-8
        category=stage(label,launch['kind'])
        fact=dict(label=label,stage=category,kind=launch['kind'],G1_seconds=receipt['G1_seconds'],
            separate_seconds=receipt['separately_reported_seconds'],outer_seconds=receipt['outer_seconds'],
            start_unix=receipt['start_unix'],end_unix=receipt['end_unix'],exit_code=receipt['exit_code'],
            timeout=receipt['timeout'],receipt_SHA=sha(path),launch_SHA=sha(path.parent/'launch.json'))
        facts.append(fact);stages[category]=stages.get(category,0.)+receipt['G1_seconds']
        if receipt['exit_code'] or receipt['timeout'] or receipt['supervisor_failure']:failures.append(fact)
    ordered=sorted(facts,key=lambda r:r['start_unix'])
    for first,second in zip(ordered,ordered[1:]):assert first['end_unix']<=second['start_unix']
    assert abs(sum(r['G1_seconds'] for r in facts)-b['G1_seconds'])<1e-8 and b['G1_seconds']<=TOTAL
    write(OUT/'cost_report.json',dict(UTC=utc(),capacity_seconds=TOTAL,total_G1_seconds=b['G1_seconds'],
        total_G1_hours=b['G1_seconds']/3600,remaining_seconds=b['remaining_G1_seconds'],
        by_descriptive_stage=stages,closed_receipts=facts,failed_children=failures,
        separately_reported_seconds=b['separately_reported_seconds'],all_outer_intervals_serial=True,
        paper_compile_render_seconds=(read(OUT/'paper_qa/render_receipt.json')['pure_writing_compile_render_seconds'] if (OUT/'paper_qa/render_receipt.json').exists() else None),
        pure_writing_wall_seconds=None,pure_writing_disclosure='Chat/source prose authoring has no outer wall meter; no time estimate is fabricated. The actual PDF compile/render has its own receipt.',
        public_IO_receipts=['carrier_manifest.json','public_restore_receipt.json','publication.json','cleanup_record.json'],
        nested_Runtime_Work_helper_H_not_added=True,initial_tool_setup_outer_unmetered=True,
        setup_disclosure='Initial source/history/workspace metadata reads and sparse-worktree creation were not outer-metered; no fabricated estimate is supplied.',
        separate_scope='Compilation, pure writing and public packaging/recovery are separately reported; scientific preparation, qualification, solving, verification and failures use the serial outer meter.'))
    print(json.dumps(dict(G1_seconds=b['G1_seconds'],hours=b['G1_seconds']/3600,stages=stages,failures=len(failures))),flush=True)

if __name__=='__main__':run()
