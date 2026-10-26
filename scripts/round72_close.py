"""Close the mixed validation stage without promoting the killed run to an endpoint."""
import csv
import gzip
import json
import time
import round72_campaign as campaign


def main():
    started = time.perf_counter()
    campaign.assert_frozen()
    run = campaign.run
    stage, out = campaign.STAGE, run.OUT
    assert not (out / 'active_run.lock').exists()
    gate = run.read(out / 'long_gate.json')
    for name in ['runs', 'pairs']:
        assert run.sha(out / (name + '.csv')) == gate[name + '_sha256']
        assert run.sha(out / ('short_' + name + '.csv')) == gate[name + '_sha256']
    entries = run.runner.entries()
    full = [e for e in entries if e['charged']]
    assert len(full) == 10
    assert [(e['id'], e['arm']) for e in full[9:]] == [('D7', 'P-GRB')]
    failed = full[-1]
    folder = run.ROOT / failed['destination']
    completion = run.read(folder / 'completion.json')
    assert completion['watchdog'] and not completion['within_budget']
    assert completion['returncode'] != 0 and not (folder / 'result.json').exists()
    log = (folder / 'native.log').read_text()
    assert log.count('Optimize a model with') == 1
    assert 'Model fingerprint: 0xe9c08735' in log
    assert 'Set parameter TimeLimit to value 3596.6733358' in log
    assert 'Time limit reached' not in log
    phases = list(csv.DictReader((folder / 'phases.csv').open()))
    assert phases[-1]['event'] == 'plain_gurobi_optimize_launch'
    manifest = []
    for label, source_folder in [('failed_D7_P-GRB', folder),
                                 ('D7_reference_build', run.RAW / 'reference_build' / 'D7')]:
        target = stage / 'failure_evidence' / label
        target.mkdir(parents=True, exist_ok=True)
        for source in sorted(source_folder.iterdir()):
            assert source.is_file()
            data = source.read_bytes()
            artifact = target / (source.name + '.gz')
            encoded = gzip.compress(data, mtime=0)
            if artifact.exists():
                assert gzip.decompress(artifact.read_bytes()) == data
            else:
                artifact.write_bytes(encoded)
            assert gzip.decompress(artifact.read_bytes()) == data
            manifest.append(dict(source=str(source.relative_to(run.ROOT)),
                source_sha256=run.sha(source), artifact=str(artifact.relative_to(stage)),
                sha256=run.sha(artifact), compact_bytes=artifact.stat().st_size,
                original_bytes=len(data)))
    # Recheck the existing short-stage delivery without changing its frozen audit.
    old_manifest = run.read(out / 'evidence_manifest.json')
    for e in old_manifest:
        artifact, source = out / e['artifact'], run.ROOT / e['source']
        assert run.sha(artifact) == e['sha256'] and run.sha(source) == e['source_sha256']
        if artifact.name == 'result_summary.json':
            raw = run.read(source)
            assert all(k in raw and raw[k] == v for k, v in run.read(artifact).items())
        else:
            decoded = gzip.decompress(artifact.read_bytes()) if artifact.suffix == '.gz' else artifact.read_bytes()
            assert decoded == source.read_bytes()
    attempt_rows = []
    for e in full:
        c = run.read(run.ROOT / e['destination'] / 'completion.json')
        attempt_rows.append(dict(number=e['charged_number'], id=e['id'], arm=e['arm'],
            cap_seconds=e['cap_seconds'], wall_seconds=c['wall_seconds'],
            failure=c['returncode'] != 0 or c['watchdog'] or not c['within_budget'],
            status='watchdog_no_formal_endpoint' if e == failed else 'audited_short_endpoint',
            source=e['destination']))
    with (stage / 'attempts.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(attempt_rows[0]))
        writer.writeheader(); writer.writerows(attempt_rows)
    diagnostic = run.read(stage / 'diagnostic_summary.json')
    exports = [run.read(run.ROOT / e['destination'] / 'completion.json') for e in entries if not e['charged']]
    resource = dict(diagnostic_launches=6, full_launches=10, valid_full_endpoints=9,
        failed_full_launches=1, total_experiment_launches=16,
        total_experiment_wall_seconds=diagnostic['actual_wall'] + sum(r['wall_seconds'] for r in attempt_rows),
        total_experiment_optimize_calls=37, valid_short_optimize_calls=36, failed_long_optimize_calls=1,
        new_ctests=0, new_qualification_optimize_calls=0, inherited_ctests=49,
        inherited_native_test_calls=39, no_opt_exports=len(exports),
        no_opt_export_wall_seconds=sum(c['wall_seconds'] for c in exports),
        unlaunched_long_arms=['K1-R', 'DS-X'],
        scope='All actual attempts charged, including killed P-GRB. Prior campaign tables/audits remain the immutable nine-run checkpoint.')
    run.write(stage / 'resource_summary.json', resource)
    run.write(stage / 'failure_manifest.json', manifest)
    run.write(stage / 'long_failure.json', dict(run_number=10, id='D7', arm='P-GRB',
        input_sha256=failed['input_sha256'], executable_sha256=failed['executable_sha256'],
        completion=completion, original_cap_seconds=3600, actual_optimize_calls=1,
        last_native_progress_line=log.splitlines()[-1],
        result_json_present=False, formal_UB=None, formal_LB=None, formal_gap=None,
        certificate=False, final_physical_witness_available=False,
        observed_last_phase=phases[-1],
        known_defect='Progress and physical final solution are serialized only after synchronous Optimize returns.',
        root_cause_limit='The exact native reason for non-return is not established; TimeLimit is not a hard-return guarantee.',
        unlaunched_arms=['K1-R', 'DS-X'], repeated=False))
    dispatch = run.read(stage / 'long_dispatch.json')
    dispatch.update(active_queue=False, terminal_session_exit_code=1,
        status='first_long_arm_watchdog_failure_queue_aborted', unlaunched_arms=['K1-R', 'DS-X'])
    run.write(stage / 'long_dispatch.json', dispatch)
    run.write(stage / 'stage_decision.json', dict(stage_complete=True, overall_goal_achieved=False,
        disposition='Mixed validation: short certificate gains credible; long protection test incomplete after baseline watchdog failure.',
        candidate_default_off=True, independent_confirmation=False, long_comparison_valid=False,
        remaining_main_issue='R71 D7 protection loss remains unresolved.',
        next_step='Qualify durable deadline evidence on all relevant arms before fresh long comparisons; investigate direct joint insertion for D7 primal quality.',
        no_more_round72_launches=True))
    audit = dict(short_artifacts_rechecked=len(old_manifest), failure_and_reference_artifacts=len(manifest),
        additional_compact_bytes=sum(e['compact_bytes'] for e in manifest),
        original_raw_bytes=sum(e['original_bytes'] for e in manifest),
        all_checks_passed=True, source_and_input_bindings_passed=True,
        short_gate_tables_unchanged=True, optimizer_calls=0,
        wall_seconds=time.perf_counter()-started, script_sha256=run.sha(__file__))
    run.write(stage / 'closure_verification.json', audit)
    print(json.dumps(dict(resource=resource, closure=audit), indent=2))


if __name__ == '__main__':
    main()
