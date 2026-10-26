"""Render audited Round71 results without solver calls or historical writes."""
import argparse,csv
import package_round71 as package
run=package.run

def rows(path):return list(csv.DictReader(path.open(encoding='utf-8')))
def number(value):return f'{float(value):.12g}'

def main(complete=False):
    package.bind();run.assert_frozen()
    assert not (run.OUT/'active_run.lock').exists(),'Render at an audit boundary'
    resource=run.read(run.OUT/'resource_status.json');records=rows(run.OUT/'runs.csv')
    performance=[r for r in records if r['kind']=='performance']
    assert len(records)==resource['charged_completed'] and not resource['failures']
    if complete:
        decision=run.read(run.OUT/'stage_decision.json')
        assert decision['stage_complete'] and not decision['overall_goal_achieved']
        assert decision['completed_performance_runs']==len(performance)
        assert resource['native_micro']==6 and len(performance)<=25
        assert len(performance)==25 or decision['unopened_panel_reason']
    starts=run.read(run.OUT/'start_checks.json')
    initial=run.read(run.OUT/'witness_model_checks.json')['checks']
    identity=run.read(run.OUT/'build_v1.json')
    state='Completed bounded stage' if complete else 'Audited prefix; stage in progress'
    lines=['# Round71 result tables','',state+'. Overall research goal remains unmet.','',
        'All roles are exposed development data. No independent confirmation or extra repeat is included. D7 is one fresh1200s run per arm, not a continuation of Round70.','',
        '|Role|Arm|Cap|Certified|Paid wall|Verified UB|Global LB|Signed gap|Startup wall|',
        '|---|---|---:|---|---:|---:|---:|---:|---:|']
    for r in performance:
        lines.append('|'+ '|'.join([r['id'],r['arm'],r['cap'],r['certificate'],f"{float(r['wall']):.3f}",
            number(r['UB']),number(r['LB']),number(r['signed_absolute_gap']),f"{float(r['hga_seconds']):.3f}"])+'|')
    lines+=['','Signed gaps preserve tiny numerical discrepancies. Requested gaps0 do not imply a rational certificate. Startup remains part of formal paid time.','',
        '|Role|DS-X reference|Classification|Wall delta|UB delta|LB delta|Gap delta|Bound relation|',
        '|---|---|---|---:|---:|---:|---:|---|']
    for p in rows(run.OUT/'pairs.csv'):
        if p.get('candidate_arm')!='DS-X':continue
        lines.append('|'+ '|'.join([p['id'],p['reference'],p['practical_classification'],f"{float(p['wall_delta']):.3f}",
            number(p['UB_delta']),number(p['LB_delta']),number(p['signed_gap_delta']),p['bound_tradeoff']])+'|')
    lines+=['','Classifications use the frozen absolute and relative thresholds. Missing certificates and mixed UB/LB changes remain explicit. All DS diagnostic pairs are retained in pairs.csv; micros are excluded.','',
        f"{len(performance)} performance + {resource['native_micro']} micro runs; {resource['experiment_optimizer_calls']} experiment Optimize calls; {resource['actual_wall_seconds']:.3f}s paid process wall; zero validity failures.",
        f"Valid startup-only whole-run deadlines: {resource.get('valid_startup_deadline_runs',0)}; supervisor exceptions: {resource.get('supervisor_postcondition_failures',0)}. Such deadlines use independently justified global LB0, without a fabricated tree/certificate or replacement run.",
        f"Qualification: {resource['final_ctest_passed_tests']}/49 new CTests, {resource['total_qualification_native_optimizer_calls']} native calls and {resource['preflight_total_wall_seconds']:.3f}s configure/build/test. Ten no-opt reference exports cost {resource['reference_build_wall_seconds']:.3f}s.",
        f"Initial-witness/model checks: {len(initial)}, including {sum(not r['compatible_interval'] for r in initial)} incompatible Gini intervals. Actual Start decisions: {starts['actual_mip_decisions']}; eligible {starts['eligible']}, accepted {starts['accepted']}, full submitted vectors observed {starts['exact_vectors_observed']}.",
        'Native MIPSOL equality is qualified C++ observer evidence; independent replay checks retained submitted/readback vectors, rows, domains, objective and physical routes. Unretained full native event vectors cannot be replayed.','',
        f"Source freeze: {identity['source_commit']}; binary SHA256: {identity['binary']}.",
        'Gurobi13.0.2, Threads1, Seed0, PresolveAuto, original numerical standards; uniform logical processor2/mask4. P-GRB remains original compact/default without HGA, explicit external Start, new cuts or imported bounds.',
        'Source, model, input, route, coverage, affinity and actual-Start evidence are retained in this stage. Large models/logs/binary remain local at manifest paths.']
    target=run.OUT/'result_tables.md';target.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    run.write(run.OUT/'report_identity.json',dict(script_sha256=run.sha(__file__),complete_stage=complete,
        source_runs_sha256=run.sha(run.OUT/'runs.csv'),source_pairs_sha256=run.sha(run.OUT/'pairs.csv'),
        table_sha256=run.sha(target),optimizer_calls=0))
    print(state,'performance',len(performance),'table written')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--complete',action='store_true')
    main(parser.parse_args().complete)
