"""Reviewer-owned, read-only formal admission from frozen data and sealed raw.

No production helpers, solver imports, compilation or optimization. The parent
may run this ordinary Python script inside its outer cost meter.
"""
from fractions import Fraction as Q
from pathlib import Path
from itertools import product
import csv
import datetime
import hashlib
import json
import math
import sys
import time
from independent_math import bounds_nodes

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'results/unified_exact_round148'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def table(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def actual_row(block, states, slopes, row, kind):
    cs = {int(i): Q(v) for i, v in block['scope']['c_binary64'].items()}
    n, beta = len(cs), sum(Q(v) for v in slopes)
    terms = row['terms']
    valid = [s for s in states if s['feasible']]
    if kind == 'affine_low':
        assert terms['G'] == 1.
        rhs = {}
        for s in valid:
            i, y = s['i'], s['y']
            b = Q(slopes[i-1])
            nodes = bounds_nodes(n, cs[i]*y, Q(s['lower']), Q(s['upper']))
            rhs[f'state_{i}_{y}'] = min(p-b*t for t, p in nodes)+beta*cs[i]*y
        assert set(terms) <= set(rhs)|{'G'}
        assert all(-Q(terms.get(k, 0.)) <= q for k, q in rhs.items())
        return dict(kind=kind, independently_recomputed_actual_binary64_slopes=True,
            conservative_RHS_coefficients=len(rhs),
            conservative_box_loss=float(sum(q+Q(terms.get(k, 0.)) for k, q in rhs.items())))
    assert kind in ('moment_lower', 'moment_upper') and terms.get('G', 0.) == 0.
    candidates = []
    for station in cs:
        bound = {s['y']: Q(s['lower' if kind == 'moment_lower' else 'upper'])
                 for s in valid if s['i'] == station}
        qs = {f"state_{s['i']}_{s['y']}": (bound[s['y']] if s['i'] == station else Q(0))-cs[s['i']]*s['y'] for s in valid}
        if kind == 'moment_upper':
            qs = {k: -v for k, v in qs.items()}
        if all(-Q(terms.get(k, 0.)) <= q for k, q in qs.items()):
            candidates.append(station)
    assert candidates
    return dict(kind=kind, independently_checked_moment_station_candidates=candidates)


def check_driver():
    facts = []
    for path in sorted((OUT/'qualification/driver').glob('*/actual.json')):
        actual = load(path)
        if not actual['applicable']:
            assert path.parent.name == 'zero_domain'
            facts.append(dict(case=path.parent.name, omitted_positive_S_unproved=True))
            continue
        bounds_path = path.parent/'gd_bounds.json'
        if bounds_path.exists():
            block = load(bounds_path)
        else:
            block = load(ROOT/'results/unified_exact_round146/LP'/f'{path.parent.name}_GD'/'compiled_rows.json')
        fact = actual_row(block, block['states'], actual['slopes'], actual['row'], actual['kind'])
        if path.parent.name == 'strict_zero_old_GD':
            assert actual['old_GD_rows'] == 0 and actual['violation'] > .08
        facts.append(dict(case=path.parent.name, old_GD_rows=actual['old_GD_rows'], **fact))
    assert len(facts) == 10
    return facts


def qualification():
    matrix = load(OUT/'qualification_matrix.json')
    d = Path(matrix['groups'][0]['launch']['destination'])
    sealed = load(d/'producer_seal.json')
    for name, value in sealed['required_SHA'].items():
        assert digest(d/name) == value
    closeout = load(d/'verification_closeout.json')
    assert closeout['necessary_verification_complete'] and closeout['implementation_qualified']
    assert closeout['native_proof_qualified'] and closeout['evidence_complete']
    audit = load(d/'audit.json')
    assert audit['passed'] and audit['raw_bytes_unchanged']
    assert audit['Optimize'] == 0 and audit['raw_tree_lifecycle_complete']
    assert load(d/'round146_parameters.json')['H_seed'] == 20260626
    assert load(OUT/'qualification_reader_recovery.json')['producer_seal_SHA'] == digest(d/'producer_seal.json')
    selection = load(d/'external/round148_selection.json')
    assert selection['qualified_input'] and selection['ready'] and selection['source_call'] == 1
    scope = load(d/'round147_offline_root_rows.json')
    row_check = actual_row(scope, selection['states'], selection['slopes'], selection['row'], selection['kind'])
    actual = table(d/'external/paper_optimize_ledger.csv')
    status = table(d/'external/lp_status_ledger.csv')
    assert len(actual) == 6 and len(status) == 3
    assert [r['solve_kind'] for r in actual] == ['LP','LP','LP','LP','CHILD_BOUND_TARGET_MIP','MIP']
    assert actual[0]['model_sha256'] == selection['source_model_SHA']
    assert Path(actual[0]['native_log']).name == 'L0_lp.gurobi.log'
    assert Path(actual[1]['native_log']).name == 'L0_lp_round148.gurobi.log'
    assert actual[0]['model_sha256'] != actual[1]['model_sha256']
    assert actual[1]['in_memory_model_reused'] == '0'
    assert actual[0]['integer_domain_restored'] == actual[1]['integer_domain_restored'] == '1'
    assert abs(float(status[0]['lower_bound'])-.23827958875065106) < 1e-12
    assert abs(selection['source_L']-.23601030234236481) < 1e-12
    parent = table(d/'external/parent_child_bound_ledger.csv')
    assert abs(float(parent[0]['parent_lp_bound'])-float(status[0]['lower_bound'])) < 1e-12
    trace = table(d/'external/global_bound_trace.csv')
    first = next(r for r in trace if r['event_type'] == 'parent_lp_completion')
    assert abs(float(first['valid_global_lower_bound'])-float(status[0]['lower_bound'])) < 1e-12
    controls = load(d/'round148_control_audit.json')
    assert controls['PASS']
    by = {}
    for fact in controls['models']:
        if fact['model_SHA'] in by:
            assert by[fact['model_SHA']] == fact, 'Repeated call has inconsistent model facts'
        else:
            by[fact['model_SHA']] = fact
    models = list(by.values())
    assert len(models) == 4 and sum(r['shared_S_rows'] == 0 for r in models) == 1
    assert all(r['GD_rows'] == 2 and r['GD_expected_migrated_and_Native_readback'] for r in models)
    assert by[selection['source_model_SHA']]['shared_S_rows'] == 0
    assert by[actual[1]['model_sha256']]['shared_S_rows'] == 1
    source_paths = [p for p in (d/'external/models').glob('*.lp') if digest(p) == selection['source_model_SHA']]
    formal_paths = [p for p in (d/'external/models').glob('*.lp') if digest(p) == actual[1]['model_sha256']]
    assert len(source_paths) == len(formal_paths) == 1
    assert 'r148_shared_S:' not in source_paths[0].read_text(encoding='utf-8')
    assert formal_paths[0].read_text(encoding='utf-8').count('r148_shared_S:') == 1
    returns = {load(p)['call'] for p in (d/'journal').glob('event_*.json') if load(p)['kind'] == 'returned'}
    assert returns == set(range(1, 7))
    return dict(producer_seal_SHA=digest(d/'producer_seal.json'), actual_calls=6, returned_calls=6,
        actual_models=4, actual_source_call=1, source_model_SHA=selection['source_model_SHA'],
        formal_model_SHA=actual[1]['model_sha256'], independent_actual_row=row_check,
        root_LP_before=selection['source_L'], root_LP_after=float(status[0]['lower_bound']),
        old_source_point_and_log_retained=True, actual_cache_discard_proved_by_nonreuse=True,
        complete_H_Start_quality_scope_lifecycle_closeout=True,
        reader_view_review='Only the never-installed source root is omitted from LP-status/cover pairing. It remains in all complete Native/model/quality/lifecycle/cost checks; the control trace and parent-child ledger use the new root. This corrects an old one-LP-per-status assumption without changing production or optimizing again.',
        failure_and_recovery_retained=True)


def main(batch):
    start = time.perf_counter()
    assert batch in ('k35', 'rb35')
    matrix_path = OUT/f'{batch}_matrix.json'
    matrix, manifest = load(matrix_path), load(OUT/'candidate_manifest.json')
    assert matrix['candidate_manifest_SHA'] == digest(OUT/'candidate_manifest.json')
    assert digest(Path(manifest['production_PE'])) == manifest['production_PE_SHA']
    for name, value in manifest['source_hashes'].items():
        assert digest(ROOT/name) == value
    for name, value in matrix['helpers'].items():
        assert digest(ROOT/name) == value
    groups = matrix['groups']
    assert len(groups) == 2 and {g['launch']['method'] for g in groups} == {'D', 'D_SHARED_S'}
    normalized = []
    for group in groups:
        launch = group['launch']
        assert digest(OUT/group['group']/'identity.json') == group['identity_SHA']
        identity = load(OUT/group['group']/'identity.json')
        assert identity['candidate_binary_sha256'] == manifest['production_PE_SHA']
        assert identity['source_hashes'] == manifest['source_hashes']
        cmd = launch['command']
        flag = lambda name: cmd[cmd.index(name)+1]
        assert cmd[0] == manifest['production_PE']
        assert flag('--round146-gd') == 'on'
        assert flag('--round148-shared-s') == ('on' if launch['method'] == 'D_SHARED_S' else 'off')
        assert flag('--gurobi-seed') == '0' and flag('--threads') == flag('--mip-threads') == '1'
        assert flag('--process-wall-time-limit') == str(launch['cap_seconds'])
        if '--primal-heuristic-seed' in cmd:
            assert flag('--primal-heuristic-seed') == '20260626'
        else:
            assert flag('--algorithm-preset') == 'research-round83-vds-equal-net-exchange'
        assert not any(x in cmd for x in ['--round138-stock-rlt','--round143-rn','--round144-projection','--round145-projection'])
        assert digest(ROOT/launch['panel']['input_path']) == launch['panel']['input_sha256']
        assert float(flag('--T')) == launch['panel']['T_seconds']
        assert float(flag('--lambda')) == launch['panel']['lambda']
        assert launch['panel']['V'] == 35 and launch['panel']['M'] == 3
        if batch == 'k35':
            assert launch['id'] == 'K-35-U' and launch['cap_seconds'] == 2400
            assert launch['panel']['T_seconds'] == 10800 and launch['panel']['lambda'] == .15
        else:
            panel = launch['panel']
            assert launch['id'] == 'R-B35-S-T2' and launch['cap_seconds'] == 2400
            assert panel['T_seconds'] == 7200 and panel['rho'] == 1.
            assert abs(panel['lambda']-1/panel['Omega']) < 1e-15
        normalized.append([x.replace(launch['destination'], '<DEST>') if x not in ('on','off') else x for x in cmd])
    a, b = normalized
    at = a.index('--round148-shared-s')+1
    assert a[:at]+a[at+1:] == b[:at]+b[at+1:]
    assert matrix['serial'] and matrix['threads'] == 1 and matrix['H_seed'] == 20260626
    driver = check_driver()
    q = qualification()
    stage_reason = None
    reader_repair = None
    if batch == 'rb35':
        # Use accepted saved endpoints and closeouts; do not repeat proof/Start
        # reconstruction or re-enter immutable producer verification.
        full = load(OUT/'reports/full.json')
        comparisons = full['comparisons']
        if isinstance(comparisons, dict):
            comparisons = [comparisons]
        prior = [r for r in comparisons if r['role'] == 'K-35-U']
        assert len(prior) == 1
        prior = prior[0]
        assert prior['same_new_PE'] and prior['own_H_equal']
        assert not prior['D_certificate'] and not prior['shared_S_certificate']
        assert prior['D_T_cert'] is None and prior['shared_S_T_cert'] is None
        assert prior['shared_S_U'] > prior['D_U']
        assert prior['shared_S_L'] > prior['D_L']
        assert prior['shared_S_relative_gap'] < prior['D_relative_gap']
        assert abs(prior['delta_U']-(prior['shared_S_U']-prior['D_U'])) < 1e-15
        assert abs(prior['delta_L']-(prior['shared_S_L']-prior['D_L'])) < 1e-15
        km = load(OUT/'k35_matrix.json')
        for group in km['groups']:
            d = Path(group['launch']['destination'])
            closed = load(d/'verification_closeout.json')
            assert closed['necessary_verification_complete'] and closed['native_proof_qualified']
        boundary = load(OUT/'qualification_reader_boundary.json')
        binding = load(OUT/'qualification_reader_real_source_binding.json')
        disposition = load(OUT/'engineering/reader_closed_reentry_disposition.json')
        assert boundary['PASS'] and boundary['Optimize'] == boundary['Native_load'] == 0
        assert binding['PASS'] and binding['raw_integer_preconditions_before_relaxation'] == 1
        assert binding['accepted_controller_kind'] == 'LP'
        assert binding['closed_producer_and_verification_hashes_unchanged']
        assert binding['closed_verification_not_reentered']
        assert boundary['helper_SHA'] == binding['helper_SHA'] == digest(ROOT/'scripts/round148_context.py')
        assert disposition['early_guard_added'] and disposition['producer_seals_and_verification_component_hashes_unchanged']
        stage_reason = dict(prior_role='K-35-U', D_U=prior['D_U'], D_L=prior['D_L'],
            shared_S_U=prior['shared_S_U'], shared_S_L=prior['shared_S_L'],
            delta_U=prior['delta_U'], delta_L=prior['delta_L'],
            delta_relative_gap=prior['delta_relative_gap'],
            judgment='The completed K35 pair has a small incumbent loss and a genuine supported-L/gap benefit. This is a tradeoff, not dominance or faster convergence. It justifies the conditional RB35 pressure pair to test whether the same uniform mechanism preserves D incumbent quality; no automatic wider matrix follows.')
        reader_repair = dict(PASS=True, source_SHA_context_zero_GD=True,
            raw_integer_flag_not_misused_as_LP_kind=True, targeted_real_binding_checked=True,
            reader_only_no_production_or_PE_change=True,
            closed_reentry_failure_retained=True, immutable_guard_not_bypassed=True,
            derivative_rewrite_disclosed=True,
            derivative_scope='Only the legacy postverification arithmetic derivative was rewritten before the old guard; same coefficient/domain content with new timing. Producer and endpoint/closeout hashes stayed fixed; no claim that every derivative byte stayed identical.')
    # Fees are read without interpreting any incomplete current reviewer outer.
    charged = math.fsum(load(p)['G1_seconds'] for p in (OUT/'fees').glob('*/receipt.json'))
    charged += math.fsum(r['outer_seconds'] for r in load(OUT/'infra/external_costs.json')['processes'])
    assert 18000-charged >= matrix['new_nominal_caps']+600
    receipt = dict(schema='round148-independent-formal-admission-v1', UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        decision='ACCEPT', PASS=True, independent_nonimplementer_review=True,
        reviewer='/root/round148_independent_review', matrix_SHA=digest(matrix_path),
        candidate_manifest_SHA=digest(OUT/'candidate_manifest.json'), PE_SHA=manifest['production_PE_SHA'],
        production_source_commit=manifest['source_commit'], nominal_new_caps=matrix['new_nominal_caps'],
        charged_before_admission=charged, remainder_before_admission=18000-charged,
        qualifications=q, independent_driver_fraction_checks=driver,
        conditional_stage_reason=stage_reason, post_K35_reader_repair=reader_repair,
        actual_physical_pair='Same new PE, own complete H, original physical problem and uniform one-row/one-added-LP mechanism; D control differs only in the default-off switch.',
        findings=[], Optimize=0, Native_load=0, compile=0, seconds=time.perf_counter()-start,
        execution_hash=digest(Path(__file__)),
        next_gate=('Return and validate both complete K35 arms before conditional RB35 or any further experiment; preserve the cap windows regardless of interim performance.'
            if batch == 'k35' else 'Return and validate both complete RB35 pressure arms. Decide from the actual incumbent/bound tradeoff; do not automatically open K20, RX20, another seed, or a rescue mechanism. Preserve the entered cap windows.'))
    (OUT/'review'/f'{batch}_admission.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(decision='ACCEPT', batch=batch, matrix_SHA=receipt['matrix_SHA'], seconds=receipt['seconds'])))


if __name__ == '__main__':
    main(sys.argv[1])
