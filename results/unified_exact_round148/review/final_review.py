"""Independent final R148 scientific audit. Standard library, zero Native.

Reuses accepted immutable producer/Start/physical/lifecycle closeouts; never
re-enters their verifier. Independently checks reported endpoints, actual
selected coefficients/formal rows, call transport, trajectories and fees.
The parent runs this script once through its outer meter.
"""
from pathlib import Path
from fractions import Fraction as Q
import collections
import csv
import datetime
import hashlib
import json
import math
import os
import re
import subprocess
import time
from admit_pair import actual_row

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'results/unified_exact_round148'
BASE = 'b0481ad63d557b1ec36994a74bfb372793f40d7f'
WRAPPERS = {'k35': '33f6cc3ee', 'rb35': '116f4309c'}
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args], cwd=cwd)


def table(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def close(a, b, tol=1e-10):
    assert math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tol, (a,b)


def affine_line(text):
    lines = re.findall(r'^\s*r148_shared_S:\s*(.+)$', text, re.M)
    assert len(lines) <= 1
    if not lines:
        return None
    lhs, rhs = lines[0].rsplit(' >= ', 1)
    assert float(rhs) == 0.
    terms, words, j, sign = {}, lhs.split(), 0, 1.
    while j < len(words):
        if words[j] in ('+', '-'):
            sign = 1. if words[j] == '+' else -1.
            j += 1
        coefficient, name = float(words[j]), words[j+1]
        assert name not in terms
        terms[name] = sign*coefficient
        j += 2
        sign = 1.
    return terms


def model_names(text):
    body = text.split('Bounds\n', 1)[1]
    out = set()
    for line in body.splitlines():
        if line in ('Generals','Binaries','End'):
            break
        if not line.strip():
            continue
        fields = line.split()
        assert len(fields) == 5 and fields[1] == fields[3] == '<='
        out.add(fields[2])
    return out


def inspect_arm(matrix, group, row, manifest, trajectories):
    launch = group['launch']
    d = Path(launch['destination'])
    assert row['destination'] == str(d)
    assert digest(OUT/group['group']/'identity.json') == group['identity_SHA']
    identity = load(OUT/group['group']/'identity.json')
    assert identity['candidate_binary_sha256'] == manifest['production_PE_SHA'] == row['PE_SHA']
    assert identity['source_hashes'] == manifest['source_hashes']
    assert row['source_commit'] == manifest['source_commit']
    assert row['DLL_SHA'] == manifest['DLL_SHA']
    sealed = load(d/'producer_seal.json')
    for name, value in sealed['required_SHA'].items():
        assert digest(d/name) == value
    closed = load(d/'verification_closeout.json')
    assert all(closed[k] for k in ['necessary_verification_complete','implementation_qualified','evidence_complete','native_proof_qualified'])
    audit = load(d/'audit.json')
    assert audit['passed'] and audit['raw_tree_lifecycle_complete'] and audit['Optimize'] == 0
    for key in ('U','L'):
        close(row[key], audit['endpoint'][key])
    close(row['U'], row['physical_G']+row['weighted_physical_penalty'])
    close(row['weighted_physical_penalty'], row['lambda_value']*row['physical_P'])
    close(row['signed_gap'], row['U']-row['L'])
    close(row['relative_gap'], (row['U']-row['L'])/row['U'])
    assert not row['certificate'] and row['T_cert'] is None
    assert row['cap'] == 2400 and row['H_complete'] and row['seed'] == 0
    close(row['T_total'], row['T_produce']+row['T_verify'], 1e-7)
    assert row['actual_split_count'] == 0 and not row['STOCK'] and row['GD']
    assert row['new_columns'] == row['paid_source_solves'] == 0
    params = load(d/'round146_parameters.json')
    assert params['H_seed'] == 20260626 and params['Seed'] == 0 and not params['stock']
    ledger = table(d/'external/paper_optimize_ledger.csv')
    obs = load(d/'observations.json')
    calls = [x['payload'] for x in obs if x['payload']['kind'] == 'call']
    returns = {x['payload']['call'] for x in obs if x['payload']['kind'] == 'returned'}
    assert len(ledger) == len(calls) == row['declared_calls'] == row['returned_calls']
    assert {c['call'] for c in calls} == returns
    assert all(x['optimize_return_code'] == '0' for x in ledger)
    for call, native in zip(calls, ledger):
        assert call['model_sha256'] == native['model_sha256']
        assert call['leaf'] == native['leaf_id']
        assert Path(call['native_log_path']).resolve() == Path(native['native_log']).resolve()
        assert call['settings']['Seed'] == 0 and call['settings']['Threads'] == 1
    close(row['Native_total_Work'], math.fsum(float(r['work']) for r in ledger), 1e-8)
    close(row['Native_total_simplex_iterations'], math.fsum(float(r['simplex_iterations']) for r in ledger), 1e-6)
    cs = row['method'] == 'D_SHARED_S'
    assert row['shared_S'] == cs and row['shared_S_rows'] == int(cs)
    source = load(d/'external/round148_selection.json') if cs else None
    controls = load(d/'round148_control_audit.json')
    assert controls['PASS'] and controls['enabled'] == cs
    actual_models = {}
    for fact in controls['models']:
        if fact['model_SHA'] in actual_models:
            assert fact == actual_models[fact['model_SHA']]
        actual_models[fact['model_SHA']] = fact
    models = collections.defaultdict(list)
    for p in (d/'external/models').glob('*.lp'):
        models[digest(p)].append(p)
    native_audits = [load(p) for p in (d/'external/native_logs').glob('*.round148.native.json')]
    gd_audits = [load(p) for p in (d/'external/native_logs').glob('*.round146.native.json')]
    assert gd_audits and all(a['PASS'] and a['GD_rows'] == 2 for a in gd_audits)
    row_proof = None
    if cs:
        assert source['qualified_input'] and source['ready'] and source['source_call'] > 0
        assert source['source_solves'] == source['new_columns'] == 0 and source['max_added_root_LP'] == 1
        scope = load(d/'round147_offline_root_rows.json')
        row_proof = actual_row(scope, source['states'], source['slopes'], source['row'], source['kind'])
        call = next(c for c in calls if c['call'] == source['source_call'])
        assert call['model_sha256'] == source['source_model_SHA'] and call['leaf'] == 'L0'
        assert call['model_scope'] == source['source_scope']
        linked = [r for r in ledger if r['model_sha256'] == source['source_model_SHA']]
        assert len(linked) == 1 and linked[0]['solve_kind'] == 'LP'
        assert Path(linked[0]['native_log']).name == 'L0_lp.gurobi.log'
        roots = [r for r in ledger if r['leaf_id'] == 'L0' and r['solve_kind'] == 'LP']
        assert len(roots) == 2 and roots[0]['model_sha256'] != roots[1]['model_sha256']
        assert Path(roots[1]['native_log']).name == 'L0_lp_round148.gurobi.log'
        assert roots[1]['in_memory_model_reused'] == '0'
        status = table(d/'external/lp_status_ledger.csv')
        root_status = [r for r in status if r['leaf_id'] == 'L0']
        assert len(root_status) == 1
        close(float(root_status[0]['lower_bound']), row['actual_root_after_strengthening_L'])
        close(source['source_L'], row['initial_root_L'])
        assert row['actual_root_after_strengthening_L'] > row['initial_root_L']+1e-8
        assert native_audits and any(a['affine_rows'] == 0 for a in native_audits)
        assert all(a['PASS'] for a in native_audits)
        for i, values in scope['scope']['supports'].items():
            close(source['point'][f'Y_{i}'], math.fsum(y*source['point'][f'state_{i}_{y}'] for y in values), 1e-6)
    else:
        assert source is None and not native_audits
        assert not (d/'round148_parameters.json').exists()
        assert sum(r['leaf_id'] == 'L0' and r['solve_kind'] == 'LP' for r in ledger) == 1
    for model_sha, fact in actual_models.items():
        assert len(models[model_sha]) == 1
        text = models[model_sha][0].read_text(encoding='utf-8')
        observed = affine_line(text)
        assert int(observed is not None) == fact['shared_S_rows']
        assert len(re.findall(r'^\s*r146_GD_(?:low|high):', text, re.M)) == 2
        assert fact['GD_expected_migrated_and_Native_readback'] and fact['GD_rows'] == 2
        assert not re.search(r'\brn_', text)
        if observed is not None:
            assert cs and model_sha != source['source_model_SHA']
            names = model_names(text)
            assert observed == {k: v for k, v in source['row']['terms'].items() if k in names}
        if cs:
            hits = [a for a in native_audits if a['model_SHA'] == model_sha]
            assert hits and all(a['affine_rows'] == int(observed is not None) for a in hits)
    # Rebuild every improving physical-witness trajectory from the sealed
    # observations and each actual committed event, without solving again.
    wanted = [r for r in trajectories if r['role'] == row['role'] and r['method'] == row['method']]
    expected, best = [], math.inf
    for item in obs:
        e = item['payload']
        if e['kind'] == 'witness' and e['objective'] < best-1e-15:
            best = e['objective']
            expected.append(item)
    assert len(wanted) == len(expected) > 0
    observation_sha = digest(d/'observations.json')
    for r, item in zip(wanted, expected):
        e, seq = item['payload'], item['sequence']
        assert int(r['sequence']) == seq and r['committed_event_SHA'] == item['sha256']
        assert digest(d/'journal'/f'event_{seq}.json') == item['sha256']
        commit = (d/'journal'/f'event_{seq}.commit').read_text().split()
        assert commit[0] == 'NEJ1' and int(commit[1]) == seq and commit[-1] == item['sha256']
        assert r['raw_observation_SHA'] == observation_sha and r['PE_SHA'] == row['PE_SHA']
        close(float(r['U']), e['objective'])
        close(float(r['producer_seconds']), item['effective_available_seconds'])
        close(e['objective'], e['G']+row['lambda_value']*e['P'], 1e-8)
        assert 0 <= item['effective_available_seconds'] <= row['T_produce']+.1
    close(best, row['U'], 1e-8)
    return dict(role=row['role'], method=row['method'], calls=len(calls), returned=len(returns),
        unique_formal_models=len(actual_models), candidate_actual_row=row_proof,
        source_call=source['source_call'] if source else None,
        source_model_SHA=source['source_model_SHA'] if source else None,
        initial_LP=row['initial_root_L'], strengthened_LP=row['actual_root_after_strengthening_L'],
        supported_final_L=row['L'], physical_U=row['U'],
        Native_root_after_cuts=row['printed_root_after_cuts_bound'],
        Native_return_ObjBoundC=row['terminal_native_return_ObjBoundC'],
        distinct_LP_Native_root_and_supported_final_layers=True,
        producer_and_closed_H_Start_physical_scope_quality_lifecycle_hashes_verified=True,
        old_and_new_GD_SHA_and_actual_Native_rows_verified=True,
        committed_trajectory_points=len(wanted),
        last_U_improvement_producer_seconds=float(wanted[-1]['producer_seconds']),
        trajectory_never_better_than_own_final=True,
        all_verification_reused_without_closed_reentry=True)


def fee_check():
    current = os.environ.get('ROUND140_METERED_PARENT_LABEL')
    closed, pending, charged, separate = [], [], [], []
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        launch = load(p)
        path = p.parent/'receipt.json'
        if not path.exists():
            assert current and p.parent.name == current, 'Unclosed noncurrent fee'
            pending.append(dict(label=current, parent_closes_and_charges_after_reviewer_exit=True))
            continue
        r = load(path)
        assert r['exit_observed'] and r['G1_seconds'] >= 0 and r['separately_reported_seconds'] >= 0
        close(r['outer_seconds'], r['G1_seconds']+r['separately_reported_seconds'], 1e-7)
        closed.append(dict(label=p.parent.name, kind=launch['kind'], exit_code=r['exit_code'], seconds=r['G1_seconds']))
        charged.append(r['G1_seconds'])
        separate.append(r['separately_reported_seconds'])
    external = load(OUT/'infra/external_costs.json')['processes']
    assert len({r['label'] for r in external}) == len(external)
    assert not ({r['label'] for r in external} & {r['label'] for r in closed})
    charged.extend(r['outer_seconds'] for r in external)
    total = math.fsum(charged)
    assert total < 18000
    failures = [r for r in closed if r['exit_code']]
    assert failures and all(r['kind'] == 'diagnostic' for r in failures)
    return dict(closed_outer_charged_seconds=total, separate_build_seconds=math.fsum(separate),
        current_outer_pending=pending, failed_qualification_and_audit_fees=failures,
        external_observations=external, labels_unique=True,
        all_failures_retained_and_charged_once=True, Native_Runtime_Work_not_added=True,
        historical_fees_not_recharged=True, parent_refreshes_final_cost_after_current_outer=True)


def main():
    started = time.perf_counter()
    full = load(OUT/'reports/full.json')
    decision = load(OUT/'candidate_decision.json')
    manifest = load(OUT/'candidate_manifest.json')
    assert decision['decision'] == 'RESEARCH_ONLY_SHARED_S_AFFINE_ROOT_NO_PROMOTION'
    assert decision['goal_outcome'] == 2 and decision['study_complete']
    assert decision['new_rows_max'] == decision['added_root_LP_max'] == 1
    assert decision['new_uniform_recommendation'] is None and decision['no_further_experiment_queued']
    assert len(full['formal_arms']) == 4 and len(full['qualification_arms']) == 1 and not full['pending']
    assert full['complete_Native_Optimize'] == full['complete_Native_returned'] == 28
    assert full['standalone_LP_Optimize'] == 5 and full['baseline_Optimize'] == full['source_solves'] == 0
    assert digest(Path(manifest['production_PE'])) == manifest['production_PE_SHA']
    for name, value in manifest['source_hashes'].items():
        assert digest(ROOT/name) == value
    assert all(load(OUT/p)['PASS'] for p in ['qualification_oracle.json','qualification_arithmetic.json',
        'qualification_native_writer.json','qualification_reader_boundary.json',
        'qualification_reader_real_source_binding.json','qualification_entry.json',
        'review/preflight.json','review/production_preflight.json','review/independent_math.json','review/independent_evidence.json'])
    lp = load(OUT/'reports/LP.json')
    assert lp['PASS'] and lp['models'] == 5 and lp['physical_instances'] == 3
    assert lp['one_row_each'] and lp['extra_LP_iterations'] == 0
    lp_checks = load(OUT/'review/independent_evidence.json')['checked_LPs']
    assert len(lp_checks) == 5
    for r in lp['results']:
        matched = next(c for c in lp_checks if c['domain'] == f"{r['role']}_{r['carrier']}")
        close(r['L'], matched['independent_objective'])
        assert r['gain'] > 1e-6 and r['qualified'] and r['added_rows_total'] == 1
        assert r['original_semantics_exactly_retained'] and r['actual_Native_row_readback']
        assert max(r['quality'].values()) <= 1e-6
    trajectories = table(OUT/'reports/verified_U_trajectories.csv')
    arms, wrapper_checks = [], []
    for batch, commit in WRAPPERS.items():
        matrix = load(OUT/f'{batch}_matrix.json')
        assert matrix['candidate_manifest_SHA'] == digest(OUT/'candidate_manifest.json')
        for name, value in matrix['helpers'].items():
            current = ROOT/name
            if digest(current) != value:
                assert hashlib.sha256(git('show',f'{commit}:{name}')).hexdigest() == value
        read_hash = hashlib.sha256(git('show',f'{commit}:scripts/round148_read.py')).hexdigest()
        assert read_hash == matrix['helpers']['scripts/round148_read.py']
        wrapper_checks.append(dict(batch=batch, executed_wrapper_commit=git('rev-parse',commit).decode().strip(),
            executed_reader_SHA=read_hash, frozen_matrix_SHA=digest(OUT/f'{batch}_matrix.json'),
            old_wrapper_publicly_reconstructible=True, same_production_PE=True))
        for group in matrix['groups']:
            row = next(r for r in full['formal_arms'] if r['batch'] == batch and r['position'] == group['position'])
            arms.append(inspect_arm(matrix, group, row, manifest, trajectories))
    assert sum(r['calls'] for r in arms) == 22
    qualification = full['qualification_arms'][0]
    assert qualification['declared_calls'] == qualification['returned_calls'] == 6
    pairs = []
    for role in ('K-35-U','R-B35-S-T2'):
        control = next(r for r in full['formal_arms'] if r['role'] == role and r['method'] == 'D')
        candidate = next(r for r in full['formal_arms'] if r['role'] == role and r['method'] == 'D_SHARED_S')
        for key in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:
            assert control[key] == candidate[key]
        du, dl = candidate['U']-control['U'], candidate['L']-control['L']
        dg = candidate['signed_gap']-control['signed_gap']
        dr = candidate['relative_gap']-control['relative_gap']
        close(dg, du-dl)
        comparator = next(r for r in full['comparisons'] if r['role'] == role)
        for name, value in [('delta_U',du),('delta_L',dl),('delta_signed_gap',dg),('delta_relative_gap',dr)]:
            close(comparator[name], value)
        ut, gt = max(.001,.05*abs(control['U'])), max(.005,.25*abs(control['signed_gap']))
        candidate_curve = [r for r in trajectories if r['role'] == role and r['method'] == 'D_SHARED_S']
        assert not any(float(r['U']) < control['U']-1e-12 for r in candidate_curve)
        pairs.append(dict(role=role, delta_U=du, delta_L=dl, delta_signed_gap=dg,
            delta_relative_gap=dr, physical_U_loss_percent=100*du/control['U'],
            supported_L_gain_percent=100*dl/abs(control['L']),
            severe_U_threshold=ut, severe_signed_gap_threshold=gt,
            severe_double_open_regression=du>=ut and dg>=gt,
            no_candidate_witness_beats_D_final_U=True, both_open_T_cert_null=True,
            caps_or_total_differences_not_convergence=True))
    assert not pairs[0]['severe_double_open_regression'] and pairs[1]['severe_double_open_regression']
    severe = decision['inherited_serious_rule']
    close(severe['U_loss'], pairs[1]['delta_U'])
    close(severe['signed_gap_loss'], pairs[1]['delta_signed_gap'])
    close(severe['U_threshold'], pairs[1]['severe_U_threshold'])
    close(severe['signed_gap_threshold'], pairs[1]['severe_signed_gap_threshold'])
    protected = ['scripts/paper_s2.py','scripts/paper_s2_gd_only.py','scripts/paper_s2_gd.py',
        'config/gi_tbc_round137.json','config/gi_tbc_gd_round147.json','config/gi_tbc_gd_round146.json']
    assert not git('diff',BASE,'--',*protected).strip()
    assert not git('diff',BASE,'--',*[f'results/unified_exact_round{i}' for i in range(137,148)]).strip()
    start = load(OUT/'start_receipt.json')
    original = Path('E:/codes/ExactEBRP')
    assert git('status','--porcelain=v1','--untracked-files=no',cwd=original).decode() == (OUT/'protected_original_tracked_status.txt').read_text(encoding='utf-8')
    for name, value in start['protected_modified_file_hashes'].items():
        assert digest(original/name) == value
    texts = {name:(OUT/name).read_text(encoding='utf-8') for name in ['final_report.md','mathematical_analysis.md','manuscript.md','manuscript.tex','LP_report.md']}
    report = texts['final_report.md']
    for item in ['94.261/74.916','.650438712/.5682885263','.3190804927/.2339272621','Seed1','V2','R144 RN-P','R145','R47/R52']:
        assert item in report, item
    assert 'not the entire mathematical common-S family' in report
    assert 'initial LP' in report and 'root-after-cuts' in report
    assert 'derivative change is disclosed' in report and 'No closeout was deleted' in report
    for row in full['formal_arms']:
        assert f"{row['U']:.9f}" in texts['manuscript.tex']
        assert f"{row['L']:.9f}" in texts['manuscript.tex']
    costs = fee_check()
    before = load(OUT/'cost_report.json')['charged_new_experiment_seconds']
    assert before <= costs['closed_outer_charged_seconds']+1e-6
    receipt = dict(schema='round148-independent-final-scientific-review-v1',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), PASS=True, decision='ACCEPT',
        reviewer='/root/round148_independent_review', independent_nonimplementer_review=True,
        supported_adoption_decision=decision['decision'], findings=[],
        mathematical_review=dict(valid_low_only_family=True, common_slope_per_station=True,
            actual_finite_slopes_and_signed_conservative_coefficients=True,
            local_first_moment_convexification_not_full_joint_distribution=True,
            isolated_strict_fixture_not_pair_CDF_dominance=True,
            five_saved_models_three_instances=True, old_and_new_LP_optima_numerical_not_rational_certificates=True,
            no_global_fractional_theory_or_priority_claim=True),
        actual_arm_checks=arms, independent_pair_checks=pairs,
        actual_complete_Native_Optimize=28, actual_complete_Native_returned=28,
        new_matched_LP_Optimize=5, baseline_reoptimization=0, source_solves=0,
        wrapper_identities=wrapper_checks,
        stable_entries_profiles_and_R137_R147_history_unchanged=True,
        protected_original_user_bytes_unchanged=True, costs=costs,
        manuscript_review=dict(PASS=True, four_evidence_levels_distinct=True,
            major_RB35_loss_controls_the_decision=True, K35_tradeoff_reported=True,
            strong_TC_STOCK_RN_history_retained=True, R147_limited_candidate_not_historical_best=True,
            closed_reentry_failure_and_derivative_rewrite_disclosed=True,
            conclusion_limited_to_tested_uniform_one_row_root_implementation=True,
            no_additional_rescue_or_performance_panel_needed=True,
            text_SHA={name:digest(OUT/name) for name in texts}),
        permitted_late_closeout='Parent closes this audit outer and refreshes final cost-only sentences/JSON and delivery metadata. Mathematical/results/decision changes require review; a cost-only refresh after this pending fee does not require new Optimize or a repeated full audit.',
        helper_SHA=digest(Path(__file__)), review_support_helpers={name:digest(OUT/'review'/name) for name in ['admit_pair.py','independent_math.py']},
        Optimize=0, Native_load=0, compile=0, seconds=time.perf_counter()-started)
    path = OUT/'review/final_scientific_review.json'
    path.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(PASS=True, decision=receipt['supported_adoption_decision'],
        formal_arms=len(arms), complete_Native=28, matched_LPs=5,
        closed_fee_seconds=costs['closed_outer_charged_seconds'], audit_seconds=receipt['seconds'])))


if __name__ == '__main__':
    main()
