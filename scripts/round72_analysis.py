"""Stage-specific summaries and the predeclared long-run admission gate."""
import argparse,csv,json,shutil,hashlib
import round72_campaign as campaign
run=campaign.run

def rows(name):
    path=run.OUT/name
    return list(csv.DictReader(path.open(encoding='utf-8-sig'))) if path.exists() else []

def gate():
    campaign.assert_frozen()
    target=run.OUT/'long_gate.json';assert not target.exists(),'Immutable gate already recorded'
    records=rows('runs.csv');pairs=rows('pairs.csv')
    assert len(records)==9 and {(r['id'],r['arm']) for r in records}=={(i,a) for i in ['D3','C2','D4'] for a in ['P-GRB','DS','DS-X']}
    assert all(r['failure']=='False' for r in records)
    resource=run.read(run.OUT/'resource_status.json')
    integrity=run.read(run.OUT/'delivery_verification.json')
    assert resource['failures']==0 and integrity['completed_experiments']==9
    assert integrity['artifact_hashes_and_content_passed'] and integrity['source_and_input_hashes_passed']
    p=[r for r in pairs if r['candidate_arm']=='DS-X' and r['reference']=='P-GRB']
    ds=[r for r in pairs if r['candidate_arm']=='DS-X' and r['reference']=='DS']
    assert len(p)==len(ds)==3
    for name in ['runs.csv','pairs.csv']:
        shutil.copyfile(run.OUT/name,run.OUT/('short_'+name))
    harmful=[r for r in p if r['practical_classification'] in ['severe_regression','certificate_loss']]
    useful=[r for r in ds if r['practical_classification'] in ['material_improvement','severe_improvement','certificate_gain']]
    decision=dict(admitted=not harmful and bool(useful),completed_short_runs=9,
        runs_sha256=run.sha(run.OUT/'runs.csv'),pairs_sha256=run.sha(run.OUT/'pairs.csv'),
        delivery_sha256=run.sha(run.OUT/'delivery_verification.json'),
        audit_sha256={name:run.sha(run.OUT/name) for name in ['witness_model_checks.json','start_checks.json','coverage_checks.csv','descent_checks.json','affinity_checks.json','native_version_checks.json']},
        frozen_short_tables=['short_runs.csv','short_pairs.csv'],
        p_relative_harmful=harmful,ds_relative_useful=useful,
        rule='All nine fully audited, no severe P-relative loss or certificate loss, at least one material DS gain or recovered certificate',
        scope='Experiment admission only; never an instance-specific algorithm switch',
        next_arms=['P-GRB','K1-R','DS-X'],next_id='D7',next_common_cap=3600,
        maximum_additional_launches=3,maximum_additional_seconds=10800,
        analysis_script_sha256=run.sha(__file__))
    run.write(target,decision);print(json.dumps(decision,indent=2))

def summary():
    campaign.assert_frozen()
    import round71_startup_analysis as startup
    startup.main()
    diagnostic_entries=[json.loads(line) for line in (campaign.STAGE/'diagnostic_processes.jsonl').read_text().splitlines()]
    attribution=[]
    for entry in run.runner.entries():
        if not entry['charged'] or entry['id']=='D7' or entry['arm']=='P-GRB':continue
        folder=run.ROOT/entry['destination']
        if not (folder/'completion.json').exists():continue
        prior=next(d for d in diagnostic_entries if (d['id'],d['arm'])==(entry['id'],entry['arm']))
        old_folder=run.ROOT/prior['destination']
        witness=run.read(folder/'external/initial_witness.json')
        old_witness=run.read(old_folder/'result.json')
        def logical_trace(path):
            with path.open(encoding='utf-8-sig') as stream:
                trace=[{k:v for k,v in row.items() if k!='elapsed_seconds'} for row in csv.DictReader(stream)]
            return hashlib.sha256(json.dumps(trace,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        full_hash=campaign.package.route_hash(witness);old_hash=campaign.package.route_hash(old_witness)
        full_trace=logical_trace(folder/'hga.csv.descent.csv');old_trace=logical_trace(old_folder/'hga.csv.descent.csv')
        attribution.append(dict(id=entry['id'],arm=entry['arm'],same_full_initial_routes=full_hash==old_hash,
            same_logical_descent_trace=full_trace==old_trace,full_route_sha256=full_hash,
            diagnostic_route_sha256=old_hash,full_logical_trace_sha256=full_trace,
            diagnostic_logical_trace_sha256=old_trace,
            scope='Separately recomputed and paid startup, compared after execution; no witness was imported'))
    run.write(run.OUT/'diagnostic_to_full_attribution.json',attribution)
    records=rows('runs.csv');pairs=rows('pairs.csv')
    text=['# Round72 complete-run results','',
        'All times are paid process wall; gaps are signed U-L. Certificates retain',
        'the original numerical standard. No startup cost is subtracted.','',
        '|Role|Arm|Cap(s)|Wall(s)|Certified|UB|LB|Gap|','|---|---|---:|---:|---|---:|---:|---:|']
    for r in records:
        text.append('|'+ '|'.join([r['id'],r['arm'],r['cap'],f"{float(r['wall']):.3f}",r['certificate'],*[f"{float(r[k]):.12g}" for k in ['UB','LB','signed_absolute_gap']]])+'|')
    text+=['','|Role|Candidate/reference|Classification|UB delta|LB delta|','|---|---|---|---:|---:|']
    for r in pairs:
        text.append(f"|{r['id']}|{r['candidate_arm']}/{r['reference']}|{r['practical_classification']}|{float(r['UB_delta']):.9g}|{float(r['LB_delta']):.9g}|")
    (run.OUT/'result_tables.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    diagnostic=run.read(campaign.STAGE/'diagnostic_summary.json')
    resource=run.read(run.OUT/'resource_status.json')
    combined=dict(diagnostic_launches=diagnostic['completed'],full_launches=resource['charged_completed'],
        total_experiment_launches=diagnostic['completed']+resource['charged_completed'],
        total_experiment_wall_seconds=diagnostic['actual_wall']+resource['actual_wall_seconds'],
        total_experiment_optimize_calls=resource['experiment_optimizer_calls'],
        new_ctests=0,new_qualification_optimize_calls=0,inherited_ctests=49,inherited_native_test_calls=39,
        no_opt_exports=resource['reference_build_only_runs'],no_opt_export_wall_seconds=resource['reference_build_wall_seconds'],
        scope='Diagnostic prefix and complete runs are separate evidence; historical qualification is not executed or charged again')
    run.write(campaign.STAGE/'resource_summary.json',combined)
    print(json.dumps(combined,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['gate','summary'])
    args=parser.parse_args();campaign.bind()
    gate() if args.action=='gate' else summary()
