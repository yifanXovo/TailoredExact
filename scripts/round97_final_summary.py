"""Read-only, zero-Optimize consolidation; never changes frozen evidence.

Fresh output only. Versions and original failure states remain explicit;
comparisons are copied from reviewed within-build views, never synthesized
across builds. Large local artifacts remain in their existing hash indices.
"""
import csv
import json
from pathlib import Path
from round97_campaign_v2 import ROOT, OUT, read, sha, ext
import round97_outcome_evidence as outcomes


def table(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    ext.ensure_idle()
    target = OUT / 'final_summary'
    assert not target.exists(), 'Do not overwrite final evidence'
    bindings = {}

    def bind(path):
        path = Path(path).resolve()
        bindings[path.relative_to(ROOT).as_posix()] = sha(path)
        return path

    bind(__file__)
    costs = read(bind(OUT / 'costs/confirmation_c3_complete/identity.json'))
    cost_rows = list(csv.DictReader(bind(OUT / 'costs/confirmation_c3_complete/solver_arms.csv').open()))
    rows = []
    for paid in cost_rows:
        batch, number = paid['batch'], int(paid['number'])
        identity = read(bind(OUT / batch / 'identity.json'))
        launch = next(x for x in identity['launches'] if x['number'] == number)
        raw = Path(launch['destination'])
        audit = read(bind(raw / 'audit.json'))
        done = read(bind(raw / 'completion.json'))
        endpoint = audit.get('endpoint')
        recovery_source = ''
        if batch == 'development02' and number == 9:
            summaries = [json.loads(s) for s in bind(OUT / batch / 'summary.jsonl').read_text().splitlines()]
            recovered, _, _, paths, _ = outcomes.load(launch, summaries[number - 1])
            for p in paths:
                bind(p)
            endpoint = recovered['endpoint']
            recovery_source = 'independently_recovered_root_mip_evidence'
        normal = done['stop_reason'] == 'normal_return' and audit['passed']
        result = read(bind(raw / 'result.json')) if normal else None
        assert float(paid['process_wall_seconds']) == done['process_wall_seconds']
        u = endpoint['U'] if endpoint else None
        gap = endpoint['gap'] if endpoint else None
        rows.append(dict(
            batch=batch, number=number, id=launch['id'], arm=launch['arm'],
            purpose='qualification' if batch.startswith('qualification') else
                    'confirmation' if batch.startswith('confirmation') else 'development',
            operator='none' if launch['arm'] in ('P-GRB', 'OFF') else launch.get('operator', 'r83'),
            registered_operator=launch.get('operator', ''),
            physical_closure_active=launch['arm'] not in ('P-GRB', 'OFF'),
            source_ref=identity.get('source_ref', ''),
            binary_sha256=identity['candidate_binary_sha256'],
            input_sha256=launch['panel']['input_sha256'],
            mathematical_T_seconds=launch['panel']['T_seconds'],
            common_cap_seconds=launch['cap_seconds'],
            process_wall_seconds=done['process_wall_seconds'],
            stop_reason=done['stop_reason'], original_audit_passed=audit['passed'],
            normal_return=normal, U=u, L=endpoint['L'] if endpoint else None,
            absolute_gap=gap,
            relative_gap=gap / max(abs(u), 1e-10) if u is not None and gap is not None else None,
            certificate=endpoint['certificate'] if normal else None,
            certificate_status=('certified' if endpoint['certificate'] else 'not_certified_at_normal_return')
                               if normal else 'unknown_interrupted_or_failed',
            endpoint_source=recovery_source or (endpoint['source'] if endpoint else 'unavailable_original_audit_failed'),
            verified_complete_optimize_calls=paid['verified_optimize_count'],
            observed_call_scopes=paid['observed_native_call_scopes'],
            source_directory=raw.resolve().relative_to(ROOT).as_posix()))
    assert len(rows) == costs['solver_starts'] == 36
    assert abs(sum(r['process_wall_seconds'] for r in rows) - costs['solver_process_seconds']) < 1e-8
    assert len({r['source_directory'] for r in rows}) == 36

    views = [
        ('h1_development', 'development01_analysis'),
        ('v2_qualification_only', 'qualification03_analysis'),
        ('v2_development_and_attribution', 'analysis_views/development_with_attribution_analysis'),
        *[(f'v2_confirmation_{role}', f'analysis_views/confirmation01_{role}_v4_analysis')
          for role in ('C1', 'C2', 'C3')],
    ]
    pairs = []
    for context, directory in views:
        bind(OUT / directory / 'identity.json')
        bind(OUT / directory / 'arms.csv')
        path = bind(OUT / directory / 'pairs.csv')
        for row in csv.DictReader(path.open()):
            pairs.append(dict(comparison_context=context, source_csv=path.relative_to(ROOT).as_posix(), **row))

    evidence_paths = [
        'research_state.md', 'history_increment.md', 'mathematical_algorithm.md',
        'production_v2_identity.json', 'confirmation_candidate_freeze.json',
        'confirmation_inputs.json', 'confirmation_recipe.json', 'operator_selection.json',
        'review_attribution.md', 'revision02_static_review.md', 'review_operator_selection.md',
        'review_confirmation_runner.md', 'review_v1_recovery.md',
        'qualification03/gate.json', 'incumbent_observation_semantics.json',
        'development01_analysis/identity.json', 'qualification03_analysis/identity.json',
        'development02/evidence_f5.json', 'development02/evidence_d7.json',
        'development02/evidence_v1.json', 'development02/evidence_v1_recovered_prefix.json',
        'development02/evidence_f2.json', 'development02/evidence_f2_observations.json',
        'attribution01/evidence_complete.json',
        *[f'confirmation01/evidence_{role}.json' for role in ('C1', 'C2', 'C3')],
        *[f'confirmation01/queue_{role}/cross_arm_consistency.json' for role in ('C1', 'C2', 'C3')],
        *[f'trajectories/{name}/identity.json' for name in
          ('development01_f5', 'development02_f5', 'development02_d7', 'development02_v1',
           'development02_f2', 'confirmation01_c1', 'confirmation01_c2', 'confirmation01_c3')],
        'costs/confirmation_c3_complete/unstarted.csv',
    ]
    for relative in evidence_paths:
        bind(OUT / relative)
    target.mkdir()
    table(target / 'all_solver_arms.csv', rows)
    table(target / 'within_build_pairs.csv', pairs)
    for path in target.iterdir():
        bind(path)
    record = dict(
        schema='round97-final-summary-v1', new_solver_starts=0, optimizer_calls=0,
        solver_rows=len(rows), copied_pair_rows=len(pairs), source_bindings=bindings,
        conclusions=dict(stage='mixed_confirmed_results',
                         default_promotion=False, merge=False,
                         stable_eventual_superiority_to_P='not_established'),
        accounting_snapshot='results/unified_exact_round97/costs/confirmation_c3_complete/identity.json',
        caveats=[
            'All36 actual solver attempts appear once. Qualification01 unstarted superseded arms are separate, not paid runs.',
            'Failed qualification01 endpoint and all interrupted certificate fields remain unavailable.',
            'V1 recovery is separate evidence; its original raw audit remains failed.',
            'Purpose/binary columns prohibit treating different versions or short qualification arms as a common performance campaign.',
            'Operator is effective: P-GRB and OFF use none; registered_operator preserves any inactive manifest placeholder. No P command contains the closure option.',
            'Pairs are copied verbatim within each reviewed context. Union-schema blank columns mean absent source fields, not zero.',
            'Detailed event/cost columns remain in bound source views; no new cross-build pairs or average performance claim.',
            'Physical/model/vector and archive byte checks are in bound source indices. Large local files are not promised in a clean clone.',
            'Final prose, reproduction and whole-stage independent review are deliberately not recursively hashed here.',
            'This artifact and its wrapper are zero-Optimize engineering work, to be included in the final cost snapshot.',
        ])
    with (target / 'evidence_index.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(solver_rows=len(rows), pair_rows=len(pairs), optimizer_calls=0)))


if __name__ == '__main__':
    main()
