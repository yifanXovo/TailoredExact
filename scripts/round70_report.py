"""Render completed audited tables; does not launch or alter solver runs."""
import argparse,csv,json
import package_round70 as package
run=package.run

def rows(path):return list(csv.DictReader(path.open(encoding='utf-8')))
def number(value):return f'{float(value):.12g}'

def main(complete=False):
    package.bind();run.assert_frozen()
    assert not (run.OUT/'active_run.lock').exists(),'Render final tables at an audit boundary'
    resource=run.read(run.OUT/'resource_status.json');records=rows(run.OUT/'runs.csv')
    performance=[r for r in records if r['kind']=='performance']
    assert len(records)==resource['charged_completed'] and not resource['failures']
    if complete:assert len(performance)==27 and resource['native_micro']==6
    starts=run.read(run.OUT/'start_checks.json');old=run.read(run.OUT.parent/'revision1_failure.json')
    native_tests=run.read(run.OUT.parent/'qualification_native_call_audit.json')
    initial=run.read(run.OUT/'witness_model_checks.json')['checks']
    identity=run.read(run.OUT/'build_v1.json')
    state='Complete bounded stage' if complete else 'Audited prefix; bounded stage still in progress'
    lines=['# Round70 result tables', '',state+'. Overall research goal remains unmet.', '',
        'All roles are exposed development data. No independent confirmation, extra repeat or long extension is included.', '',
        '|Role|Arm|Cap|Certified|Paid wall|Verified UB|Global LB|Signed gap|Startup wall|',
        '|---|---|---:|---|---:|---:|---:|---:|---:|']
    for r in performance:
        lines.append('|'+ '|'.join([r['id'],r['arm'],r['cap'],r['certificate'],f"{float(r['wall']):.3f}",
            number(r['UB']),number(r['LB']),number(r['signed_absolute_gap']),f"{float(r['hga_seconds']):.3f}"])+'|')
    lines+=['','Signed gaps, including tiny negative numerical discrepancies, are preserved in the CSV. Zero requested gaps do not imply a rational certificate. Startup is never subtracted from formal total time.','',
        '|Role|DS reference|Classification|Wall delta|UB delta|LB delta|Gap delta|Bound relation|',
        '|---|---|---|---:|---:|---:|---:|---|']
    for p in rows(run.OUT/'pairs.csv'):
        if p.get('candidate_arm')!='DS':continue
        lines.append('|'+ '|'.join([p['id'],p['reference'],p['practical_classification'],f"{float(p['wall_delta']):.3f}",
            number(p['UB_delta']),number(p['LB_delta']),number(p['signed_gap_delta']),p['bound_tradeoff']])+'|')
    lines+=['','Classifications use the predeclared absolute and relative practical thresholds. A missing certificate is explicit; mixed UB/LB changes must be read with the raw values. Micros do not enter performance pairs.','',
        f"Revision2: {len(performance)} performance + {resource['native_micro']} micro runs; {resource['experiment_optimizer_calls']} experiment Optimize calls; {resource['actual_wall_seconds']:.3f}s complete paid wall; zero validity failures.",
        f"Startup-only whole-run deadlines: {resource.get('valid_startup_deadline_runs',0)}; supervisor postcondition exceptions: {resource.get('supervisor_postcondition_failures',0)}. These retained runs use independently justified global LB0, without inventing a proof tree or certificate; no rerun or replacement.",
        f"Revision1: {old['micro_runs']} superseded micros, including {old['failed_micro_runs']} DS configuration failures; {old['optimizer_calls']} calls and {old['actual_wall_seconds']:.3f}s retained, never replaced or counted as valid candidate performance.",
        f"Both CTest batches together: {native_tests['total_native_Optimize_calls']} native calls, separate from experiments. See qualification_native_call_audit.json for the runtime fixture count and independently counted CLI ledger.",
        f"Initial-witness/model checks: {len(initial)}, including {sum(not r['compatible_interval'] for r in initial)} incompatible Gini intervals. Actual Start decisions: {starts['actual_mip_decisions']}; eligible {starts['eligible']}, native accepted {starts['accepted']}, full submitted vectors observed {starts['exact_vectors_observed']}.",
        'Native MIPSOL equality is qualified C++ observer evidence. The independent replay checks the retained submitted/readback vectors, exported rows/types/objective and original physical routes; unretained full native event vectors cannot be replayed.', '',
        f"Frozen implementation commit: {identity['source_commit']}; executable SHA256: {identity['binary']}.",
        'Gurobi13.0.2 / Threads1 / Seed0 / PresolveAuto / original numerical standards. All fresh arms inherit logical processor2/mask4. P-GRB remains original compact/default, without HGA, explicit external Start, added cuts or imported bounds.', '',
        'Source, model, input, physical witness, full frontier, affinity and actual-Start evidence are under revision2/. Large raw models/logs and both binaries remain local. Read algorithm.md, small_screen.md, status.md and reproduce.md for scope.']
    (run.OUT.parent/'result_tables.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    run.write(run.OUT/'report_identity.json',dict(script_sha256=run.sha(__file__),complete_stage=complete,
        source_runs_sha256=run.sha(run.OUT/'runs.csv'),source_pairs_sha256=run.sha(run.OUT/'pairs.csv'),
        table_sha256=run.sha(run.OUT.parent/'result_tables.md'),optimizer_calls=0))
    print(state,'performance',len(performance),'table written')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--complete',action='store_true')
    main(parser.parse_args().complete)
