"""Finite independent R130 review from a supplied/public recovery root.

Only the standard library is imported before the NOT_READY gate. All 24 arm
closeouts and the author's analysis/claim outputs must exist before any model,
Start, H trace, native log or evidence-reader module is opened. This program
never compiles, loads a native library, starts a solver, or calls a producer.

The thirty typed comparisons, symmetric materiality rule, six shared matched
group denominators and attribution axes are implemented here. R130 analysis
and decision modules are not imported. Read-only established physical, Start,
model and source/return/coverage readers are reused after the readiness gate.

Example, after the fixed experiment and author analysis have closed:
  python -B scripts/round130_portable_check.py --receipt PATH
An incomplete panel returns NOT_READY (exit 2) without heavy evidence reads.
"""

from pathlib import Path, PurePosixPath
import argparse
import collections
import csv
import datetime
import hashlib
import json
import math
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
PE = '2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
E2 = 'ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa'
DLL = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
BASE = 'ce70acd2fb3fa6b7d0033f0cbc74c2aab3113d73'
METHODS = ('P', 'PS', 'S2', 'S2R')
PAIR_TYPES = (('S2', 'P'), ('PS', 'P'), ('S2', 'PS'), ('S2', 'S2R'), ('S2R', 'PS'))
IDS = ('UC-B20-B', 'UC-C20-U', 'UC-B30-S')
ORDERS = (('P', 'PS', 'S2', 'S2R'), ('S2R', 'S2', 'PS', 'P'),
          ('PS', 'S2R', 'P', 'S2'), ('S2', 'P', 'S2R', 'PS'),
          ('S2', 'P', 'S2R', 'PS'), ('PS', 'S2R', 'P', 'S2'))
HASHES = {}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    path = Path(path).resolve()
    if path not in HASHES:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                h.update(block)
        HASHES[path] = h.hexdigest()
    return HASHES[path]


def portable(value):
    """Map recorded paths only into ROOT, with no old-checkout fallback."""
    value = str(value).replace('\\', '/')
    for prefix in ('results/', 'reference/', 'scripts/', 'src/', 'include/'):
        if value.startswith(prefix):
            suffix = value
            break
        at = value.find('/' + prefix)
        if at >= 0:
            suffix = value[at + 1:]
            break
    else:
        raise AssertionError(('path lacks a published-root mapping', value))
    rel = PurePosixPath(suffix)
    assert not rel.is_absolute() and '..' not in rel.parts
    result = ROOT.joinpath(*rel.parts).resolve()
    assert result.is_relative_to(ROOT), ('path escaped supplied root', value)
    return result


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def same(a, b, tolerance=1e-8):
    assert a is not None and b is not None
    assert math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance, (a, b)


def eligible(arm):
    return all(arm.get(k) is True for k in
               ('formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified')) \
        and not arm.get('source_reduced', False)


def comparison(left, right, group, number):
    """Certification first; strict unrounded direction; symmetric materiality."""
    result = dict(group=number, id=group['role']['id'], seed=group['seed'],
        left=left['method'], right=right['method'], classification='UNEVALUABLE',
        direction='UNEVALUABLE', left_certified=bool(left.get('certificate')),
        right_certified=bool(right.get('certificate')), left_T_cert=left.get('T_cert'),
        right_T_cert=right.get('T_cert'), left_T_produce=left.get('T_produce'),
        right_T_produce=right.get('T_produce'), left_minus_right_seconds=None,
        right_over_left_certification_ratio=None, materiality=None,
        material_threshold_seconds=None)
    if not (eligible(left) and eligible(right)):
        return result
    for key in ('PE_SHA', 'DLL_SHA', 'input_SHA', 'seed'):
        assert left[key] == right[key], ('comparison identity mismatch', key)
    ac, bc = left['certificate'], right['certificate']
    if ac and bc:
        same(left['U'], right['U'], 1e-7)
        a, b = left['T_cert'], right['T_cert']
        assert a is not None and b is not None and a > 0 and b > 0
        delta = a - b
        threshold = max(10., .10 * min(a, b))
        result.update(classification='BOTH_CERTIFIED',
            direction='Win' if delta < 0 else 'Lose' if delta > 0 else 'Tie',
            left_minus_right_seconds=delta, right_over_left_certification_ratio=b / a,
            material_threshold_seconds=threshold,
            materiality='LEFT_MATERIALLY_FASTER' if -delta >= threshold else
                        'RIGHT_MATERIALLY_FASTER' if delta >= threshold else 'TIME_CLOSE')
    elif ac:
        result.update(classification='LEFT_ONLY_CERTIFIED', direction='Win')
    elif bc:
        result.update(classification='RIGHT_ONLY_CERTIFIED', direction='Lose')
    else:
        result.update(classification='BOTH_OPEN', direction='UNDETERMINED')
    return result


def shared_denominators(pairs):
    """Each of the five types shares six groups from three known inputs."""
    result = {}
    for left, right in PAIR_TYPES:
        rows = [q for q in pairs if (q['left'], q['right']) == (left, right)]
        assert len(rows) == 6 and {q['group'] for q in rows} == set(range(1, 7))
        assert {q['id'] for q in rows} == set(IDS)
        both = [q for q in rows if q['classification'] == 'BOTH_CERTIFIED']
        ratios = [q['right_over_left_certification_ratio'] for q in both]
        result[left + '/' + right] = dict(rows=6, nonalias_typed_entries=6,
            evaluable_nonalias_entries=sum(q['classification'] != 'UNEVALUABLE' for q in rows),
            unevaluable_nonalias_entries=sum(q['classification'] == 'UNEVALUABLE' for q in rows),
            alias_entries=0, classes=dict(collections.Counter(q['classification'] for q in rows)),
            directions=dict(collections.Counter(q['direction'] for q in rows)),
            both_certified_intersection_n=len(both), both_certified_ids=[q['id'] for q in both],
            conditional_geometric_mean=math.exp(math.fsum(math.log(v) for v in ratios) / len(ratios)) if ratios else None,
            distinct_input_denominator=3, Seed_observations_per_input=2,
            six_groups_share_the_same_method_observations=True,
            independent_trial_count_not_inferred_from_thirty_differences=True)
    return result


def support_family(row):
    terms, sense, rhs = row
    terms = dict(terms)
    z = {n for n in terms if n.startswith('z_')}
    p = {n for n in terms if n.startswith('p_')}
    if len(z) in (2, 3) and sense == '<=' and len({n.split('_')[1] for n in z | p}) == 1:
        if set(terms) == z and all(terms[n] == 1 for n in z) and rhs == len(z) - 1:
            return 'cover_' + str(len(z))
        if set(terms) == z | p and len(p) == len(z) \
                and {n.replace('p_', 'z_', 1) for n in p} == z \
                and all(terms[n] == 120 for n in p) and len({terms[n] for n in z}) == 1:
            return 'conditional_' + str(len(z))
    # Receiver rows have one d column, no visit/Gini/state variables.
    if sense == '<=' and rhs == 0 and sum(n.startswith('d_') for n in terms) == 1 \
            and all(n.startswith(('d_', 'p_')) for n in terms):
        return 'ordered_supply'
    return None


def root_difference(core, left_call, right_call):
    pa, pb = portable(left_call['model_path']), portable(right_call['model_path'])
    a, b = core.lp_model(pa), core.lp_model(pb)
    for key in ('objective', 'order', 'types', 'bounds'):
        assert a[key] == b[key], ('non-sentinel root difference', key)
    ca, cb = collections.Counter(a['rows']), collections.Counter(b['rows'])
    removed, added = ca - cb, cb - ca
    assert not added and set(removed) <= {((), '<=', -1.)}, ('unexpected S2R root row difference', removed, added)
    family = collections.Counter(support_family(row) for row in b['rows'])
    assert family['cover_3'] == family['conditional_3'] == 0
    return dict(removed_semantic_sentinel_rows=sum(removed.values()),
        all_other_rows_columns_types_bounds_objective_identical=True,
        pair_cover=family['cover_2'], pair_conditional=family['conditional_2'],
        ordered_supply=family['ordered_supply'], triple_rows=0, other_root_rows_retained=True)


def full_vector(core, model_path, csv_path, value_column='value'):
    """All saved columns/types/bounds/rows/original objective, at 1e-7."""
    model = core.lp_model(model_path)
    with Path(csv_path).open(newline='', encoding='utf-8-sig') as f:
        table = list(csv.DictReader(f))
    assert [q['variable'] for q in table] == model['order']
    values = {q['variable']: float(q[value_column]) for q in table}
    assert len(values) == len(table) and all(math.isfinite(v) for v in values.values())
    maximum = 0.
    for q in table:
        name, value = q['variable'], values[q['variable']]
        assert q['type'] == model['types'][name]
        if 'readback' in q:
            assert math.isfinite(float(q['readback'])) and value == float(q['readback'])
        lo, hi = model['bounds'][name]
        maximum = max(maximum, lo - value, value - hi)
        if q['type'] in ('B', 'I', 'N'):
            assert abs(value - round(value)) <= 1e-7
    for terms, sense, rhs in model['rows']:
        lhs = math.fsum(coefficient * values[name] for name, coefficient in terms)
        violation = abs(lhs - rhs) if sense == '=' else max(0., lhs - rhs) if sense == '<=' else max(0., rhs - lhs)
        maximum = max(maximum, violation)
    assert maximum <= 1e-7, ('full-vector residual', relative(csv_path), maximum)
    terms, constant = model['objective']
    objective = constant + math.fsum(coefficient * values[name] for name, coefficient in terms)
    return dict(columns=len(table), rows=len(model['rows']), maximum_row_violation=maximum,
                objective=objective, model_SHA=sha(model_path), vector_SHA=sha(csv_path)), values


def root_chain(core, native, h):
    """State the nonzero two-call obligation and actual returned status."""
    dest, result, calls = native['dest'], native['result'], native['calls']
    if h['physical']['F'] <= 1e-12 and not calls:
        return dict(status='INHERITED_STARTUP_ZERO_BACKEND_UNEXPOSED', two_call_obligation=False,
                    own_U0=h['physical']['F'], native_Optimize=0)
    ledger = core.rows(dest / 'external/paper_optimize_ledger.csv')
    assert [q['solve_kind'] for q in ledger] == ['LP', 'MIP']
    assert all(q['leaf_id'] == 'L0' and int(q['optimize_return_code']) == 0 for q in ledger)
    assert len(calls) == 2 and all(q['leaf'] == 'L0' for q in calls)
    assert len({q['model_sha256'] for q in calls}) == 1
    assert int(ledger[0]['integer_domain_restored']) == 1
    upper = min(h['physical']['F'], (native['launch']['panel']['V'] - 1) / native['launch']['panel']['V'])
    for call in calls:
        same(call['lower_g'], 0., 0.)
        same(call['upper_g'], upper, 1e-12)
        same(call['cutoff'], h['physical']['F'], 1e-12)
    for key in ('split_count', 'partial_mip_optimize_count', 'child_restart_count', 'reset_call_count', 'canonical_artifact_invalidation_count'):
        assert result['external_gini_tree_' + key] == 0
    receipts = [(p, read(p)) for p in sorted((dest / 'external/native_logs').glob('*.round68.start.json'))]
    submitted = [(p, q) for p, q in receipts if q.get('submitted')]
    pre = [(p, q) for p, q in receipts if q.get('source') == 'round128_own_U0_pre_lp']
    assert len(submitted) == len(pre) == 1
    assert not pre[0][1]['submitted'] and pre[0][1]['mapping_complete'] and pre[0][1]['rows_valid'] and pre[0][1]['objective_valid']
    assert all(submitted[0][1][k] for k in ('mapping_complete', 'rows_valid', 'objective_valid', 'readback_valid'))
    assert result['external_gini_tree_warm_start_submitted_count'] == 1
    model = portable(calls[0]['model_path'])
    start_csv = submitted[0][0].with_name(submitted[0][0].name[:-5] + '.values.csv')
    pre_csv = pre[0][0].with_name(pre[0][0].name.replace('.round68.start.json', '.round128.pre_lp.values.csv'))
    start, values = full_vector(core, model, start_csv)
    precheck, before = full_vector(core, model, pre_csv, 'mapped_value')
    assert before == values
    same(start['objective'], h['physical']['F'], 1e-7)
    leaves = core.rows(dest / 'external/paper_leaf_ledger.csv')
    assert len(leaves) == 1 and leaves[0]['leaf_id'] == 'L0'
    native_optimal = ledger[1]['native_status'] == 'OPTIMAL'
    complete_optimal = native_optimal and leaves[0]['status'] == 'closed' \
        and leaves[0]['closure_source'] == 'native_terminal_mip_optimal'
    if native['arm']['certificate']:
        assert complete_optimal and result['external_gini_tree_lifecycle_complete']
    if ledger[1]['native_status'] in ('TIME_LIMIT', 'INTERRUPTED'):
        assert not native['arm']['certificate'] and not result['external_gini_tree_all_relevant_leaves_closed']
        assert leaves[0]['closure_source'] != 'native_terminal_mip_optimal'
    assert ledger[0]['native_status'] != 'INFEASIBLE' and ledger[1]['native_status'] != 'INFEASIBLE'
    return dict(status='CHECKED', two_call_obligation=True, own_U0=h['physical']['F'],
        native_statuses=[q['native_status'] for q in ledger], one_submitted_Start=True,
        complete_native_optimal_root_return=complete_optimal, pre_LP=precheck, submitted_Start=start,
        pre_LP_and_submitted_readback_values_identical=True, raw_signed_gap=native['arm']['gap'],
        no_child_target_split_or_rebuild=True)


def split_cover_details(core, native):
    """Real committed child geometry and semantic-closure premises, not counts."""
    dest, panel = native['dest'], native['launch']['panel']
    leaves = core.rows(dest / 'external/paper_leaf_ledger.csv')
    by_id = {q['leaf_id']: q for q in leaves}
    assert len(by_id) == len(leaves)
    children = collections.defaultdict(list)
    for leaf in leaves:
        if leaf['parent_id']:
            assert leaf['parent_id'] in by_id
            children[leaf['parent_id']].append(leaf)
    geometry = []
    for parent, descendants in children.items():
        assert len(descendants) == 2, ('committed binary replacement lacks both children', parent)
        left, right = sorted(descendants, key=lambda q: int(q['child_index']))
        assert int(left['child_index']) == 0 and int(right['child_index']) == 1
        same(float(left['gamma_L']), float(by_id[parent]['gamma_L']), 0.)
        same(float(right['gamma_U']), float(by_id[parent]['gamma_U']), 0.)
        same(float(left['gamma_U']), float(right['gamma_L']), 0.)
        assert by_id[parent]['status'] in ('replaced', 'coalesced')
        geometry.append(dict(parent=parent, left=left['leaf_id'], right=right['leaf_id'],
            parent_scope=[float(by_id[parent]['gamma_L']), float(by_id[parent]['gamma_U'])],
            common_endpoint=float(left['gamma_U']), no_gap_or_omitted_side=True))
    actual = sum(q.get('event') == 'atomic_split' for q in native['item']['controller']['controller_events'])
    assert len(geometry) == actual
    data = core.evidence.instance(ROOT, panel)
    penalty_terms = tuple(sorted(('e_' + str(i), data['w'][i]) for i in range(1, panel['V'] + 1) if data['w'][i]))
    scopes, seen = [], set()
    for call in native['calls']:
        if call['model_sha256'] in seen:
            continue
        seen.add(call['model_sha256'])
        model = core.lp_model(portable(call['model_path']))
        sentinel = sum(not t and s == '<=' and rhs == -1 for t, s, rhs in model['rows'])
        floors = [rhs for terms, sense, rhs in model['rows'] if terms == penalty_terms and sense == '>=']
        if not sentinel:
            scopes.append(dict(leaf=call['leaf'], model_SHA=call['model_sha256'], sentinel_rows=0))
            continue
        assert floors and panel['lambda'] >= 0
        floor = max(floors)
        analytic = call['lower_g'] + panel['lambda'] * floor
        cutoff = call['cutoff']
        assert analytic >= cutoff - 1e-9, ('semantic closure lacks its actual analytic premise', call['leaf'])
        for witness in native['item']['ind']['witnesses']:
            if call['lower_g'] <= witness['G'] <= call['upper_g'] and witness['F'] <= cutoff:
                assert analytic <= witness['F'] + 1e-7, ('own same-domain witness contradicts closure premise', call['leaf'])
        interpretation = 'analytic floor > cutoff; inclusive cutoff exclusion subject to verified premises' if analytic > cutoff else \
            'analytic floor = cutoff; only strict improvement excluded, equal-cutoff physical point can remain' if analytic == cutoff else \
            'analytic floor slightly below cutoff; inherited numerical closure, not exact absence of every strict improver'
        scopes.append(dict(leaf=call['leaf'], model_SHA=call['model_sha256'], sentinel_rows=sentinel,
            true_G_scope=[call['lower_g'], call['upper_g']], cutoff=cutoff,
            actual_penalty_floor=floor, analytic_region_lower=analytic, analytic_minus_cutoff=analytic - cutoff,
            interpretation=interpretation, raw_signed_difference_retained=True,
            not_an_inclusive_physical_INFEASIBLE_claim=True, numerical_evidence_tolerance_unchanged=1e-7))
    return dict(actual_atomic_split_events=actual, binary_replacement_geometry=geometry,
                actual_call_semantic_closure_scopes=scopes, complete_leaf_ledger=leaves)


def axes_from_evidence(pairs, mechanisms):
    lookup = {(q['id'], q['seed'], q['left'], q['right']): q for q in pairs}
    by = {(m['id'], m['seed']): m for m in mechanisms}
    axes, reversals = {}, []
    for axis, right in (('same_H_backend', 'PS'), ('outer_control', 'S2R')):
        rows = []
        for id in IDS:
            qq = [lookup[id, seed, 'S2', right] for seed in (0, 1)]
            mm = [by[id, seed] for seed in (0, 1)]
            if right == 'PS':
                attribution = all(m['S2_PS_same_complete_H'] and m['S2_PS_both_backends_exposed'] for m in mm)
            else:
                attribution = all(m['pure_outer_package_attribution_eligible'] and
                                  (m['S2_splits'] > 0 or m['S2_actual_target_calls'] > 0) for m in mm)
            positive = attribution and all(q['classification'] == 'LEFT_ONLY_CERTIFIED' or q['materiality'] == 'LEFT_MATERIALLY_FASTER' for q in qq)
            reverse = attribution and all(q['classification'] == 'RIGHT_ONLY_CERTIFIED' or q['materiality'] == 'RIGHT_MATERIALLY_FASTER' for q in qq)
            status = 'REPEATED_DIRECT_INCREMENT' if positive else 'REPEATED_REVERSE_REFERENCE_ADVANTAGE' if reverse else \
                'CLOSE_AT_BOTH_SEEDS' if all(q['classification'] == 'BOTH_CERTIFIED' and q['materiality'] == 'TIME_CLOSE' for q in qq) else \
                'UNDETERMINED' if all(q['classification'] == 'BOTH_OPEN' for q in qq) else 'MIXED_OR_LIMITED'
            row = dict(id=id, status=status, attribution_eligible=bool(attribution),
                seed_observations=[dict(seed=q['seed'], classification=q['classification'], direction=q['direction'],
                    materiality=q['materiality'], left_minus_right_seconds=q['left_minus_right_seconds'],
                    threshold=q['material_threshold_seconds']) for q in qq])
            rows.append(row)
            if reverse:
                reversals.append(dict(axis=axis, id=id))
        axes[axis] = dict(records=rows, repeated_direct_roles=[q['id'] for q in rows if q['status'] == 'REPEATED_DIRECT_INCREMENT'])
    return axes, reversals


def closeout_gate(out, manifest):
    """Existence and small group-identity reads only; never open formal raw."""
    missing = []
    if len(manifest.get('groups', [])) != 6:
        return ['manifest must contain the fixed six groups']
    positions = 0
    for group in manifest['groups']:
        camp = out / group['name']
        for name in ('identity.json', 'reconstructed.json'):
            if not (camp / name).is_file():
                missing.append(relative(camp / name))
        if not (camp / 'identity.json').is_file():
            continue
        plan = read(camp / 'identity.json')
        positions += len(plan['launches'])
        for launch in plan['launches']:
            dest = portable(launch['destination'])
            for name in ('arm_total_receipt.json', 'producer_seal.json', 'producer_receipt.json',
                         'verification_closeout.json', 'audit.json', 'independent_evidence.json'):
                if not (dest / name).is_file():
                    missing.append(relative(dest / name))
    if positions != 24:
        missing.append('all 24 fixed launch positions must exist')
    for name in ('arms.csv', 'pairs.csv', 'observations.json', 'actual_method_differences.json',
                 'stratified_summary.json', 'scientific_decision.json', 'claim_decision.md',
                 'claim_scope_assessment.json', 'cross_arm_bound_consistency.json'):
        if not (out / name).is_file():
            missing.append(relative(out / name))
    return missing


def check(root):
    global ROOT
    ROOT = Path(root).resolve()
    out = ROOT / 'results/unified_exact_round130'
    tick = time.perf_counter()
    manifest = read(out / 'experiment_manifest.json')
    missing = closeout_gate(out, manifest)
    if missing:
        return dict(status='NOT_READY', reason='all 24 arm closeouts and author analysis/claim outputs must close first',
            missing=missing, models_or_H_or_native_logs_read=False, evidence_reader_modules_imported=False,
            Optimize=0, native_starts=0, compilation=0), 2

    sys.path.insert(0, str(ROOT / 'scripts'))
    import round108_reader as core
    import round114_audit as audit_reader
    import round112_audit as start_reader
    import round130_evidence as evidence_adapter
    import round118_call_logs as call_logs
    import read_round118 as reconstruction
    import read_round116 as source_reader
    from compare_round112_startup import reconstruct as h_evidence
    for module in (core, audit_reader, start_reader, evidence_adapter, call_logs, reconstruction, source_reader):
        assert Path(module.__file__).resolve().is_relative_to(ROOT), ('reader imported from another checkout', module.__name__)
    core.start_reader.ROOT = ROOT
    frozen, binding = read(out / 'E3_frozen.json'), read(out / 'execution_binding.json')
    argv = read(out / 'argv_freeze.json')
    assert manifest['base'] == BASE and frozen['PE_SHA'] == argv['PE_SHA'] == PE
    assert frozen['predecessor_PE_SHA'] == E2 and frozen['DLL_SHA'] == argv['DLL_SHA'] == DLL
    assert frozen['qualification_complete'] and not frozen['final_qualification_pending']
    assert sha(out / 'E3_frozen.json') == binding['E3_identity_SHA']
    assert sha(out / 'experiment_manifest.json') == binding['protocol_SHA']
    assert sha(out / 'input_manifest.json') == binding['input_manifest_SHA']
    for path, digest in frozen['source_bindings'].items():
        assert sha(ROOT / path) == digest, ('frozen source', path)
    for path, digest in binding['adapters'].items():
        assert sha(ROOT / path) == digest, ('bound adapter', path)
    panels = read(out / 'input_manifest.json')['roles']
    assert tuple(p['id'] for p in panels) == IDS
    for p in panels:
        assert sha(ROOT / p['input_path']) == p['input_sha256']
    assert manifest['formal_arms'] == argv['formal_arms'] == 24
    assert manifest['typed_shared_comparisons'] == argv['typed_comparisons'] == 30
    assert tuple(map(tuple, manifest['pairs'])) == PAIR_TYPES
    assert len(argv['full_plans']) == 6
    assert sum(4 * g['role']['cap_seconds'] for g in manifest['groups']) == 28800

    arms, pairs, mechanisms, artifacts, H_rows = [], [], [], [], []
    split_examples, root_chains, ps_layers = [], [], []
    model_hashes = set()
    representative_fleet = None
    for number, (group, frozen_plan) in enumerate(zip(manifest['groups'], argv['full_plans']), 1):
        assert tuple(group['methods']) == ORDERS[number - 1]
        assert group['role']['id'] == IDS[(number - 1) // 2] and group['seed'] == (number - 1) % 2
        assert tuple(map(tuple, group['pairs'])) == PAIR_TYPES
        camp = out / group['name']
        plan, saved = read(camp / 'identity.json'), read(camp / 'reconstructed.json')
        assert plan == frozen_plan and sha(camp / 'identity.json') == binding['groups'][group['name']]
        assert plan['candidate_binary_sha256'] == PE and plan['dll_sha256'] == DLL
        assert plan['source_hashes'] == frozen['source_bindings']
        assert plan['prereg']['common']['affinity_mask'] == 4
        assert [q['method'] for q in saved['arms']] == group['methods']
        recs = collections.defaultdict(list)
        with evidence_adapter.extension():
            items = [reconstruction.item(ROOT, launch, plan, recs) for launch in plan['launches']]
            witnesses = [dict(q, arm=item['l']['method']) for item in items if item['complete'] for q in item['ind']['witnesses']]
            local = [source_reader.reconcile(item.get('claims', []), witnesses) for item in items]
            rebuilt = [reconstruction.finalize(ROOT, item, finding, recs) for item, finding in zip(items, local)]
        native = {}
        for launch, original, arm, item in zip(plan['launches'], saved['arms'], rebuilt, items):
            assert item['complete'], ('required evidence incomplete', number, launch['method'])
            dest, panel, command = portable(launch['destination']), launch['panel'], launch['command']
            method = launch['method']
            def arg(name):
                assert command.count(name) == 1, (number, method, name)
                return command[command.index(name) + 1]
            assert str(command[0]).replace('\\', '/').endswith('/build-cache/round130/ExactEBRP.exe')
            assert '--round128-mode' not in command and '--round127-p-parameters' not in command
            if method == 'PS':
                assert '--round112-ens-start-compact' in command and '--round127-mode' not in command
            else:
                assert arg('--round127-mode') == {'P': 'p', 'S2': 'ms2', 'S2R': 's2-root'}[method]
                assert '--round112-ens-start-compact' not in command
            assert arg('--gurobi-seed') == str(group['seed']) and arg('--threads') == arg('--mip-threads') == '1'
            assert arg('--gurobi-presolve') == '-1' and arg('--process-shutdown-margin') == '30'
            assert arg('--time-limit') == '1194' and arg('--process-wall-time-limit') == '1200'
            assert arg('--lambda') == '0.15' and arg('--pickup-time') == arg('--drop-time') == '60'
            assert arg('--T') == str(panel['T_seconds']) and launch['hard_stop_seconds'] == 1198
            assert launch['seed'] == group['seed'] and launch['repeat'] == 1 and launch['binary_layer'] == 'E3'
            producer, total = read(dest / 'producer_receipt.json'), read(dest / 'arm_total_receipt.json')
            seal, closeout = read(dest / 'producer_seal.json'), read(dest / 'verification_closeout.json')
            result, completion = read(dest / 'result.json'), read(dest / 'completion.json')
            ind, origin = read(dest / 'independent_evidence.json'), read(dest / 'child_process_origin.json')
            assert origin['command'] == command and origin['PE_SHA'] == PE and origin['seed'] == group['seed']
            assert origin['creation_from_live_OS_handle'] is True
            assert producer['producer_seal_SHA'] == sha(dest / 'producer_seal.json')
            assert seal['native_stopped_no_reentry'] and seal['required_outputs_closed']
            for path, digest in seal['required_SHA'].items():
                assert sha(dest / path) == digest, ('producer seal', number, method, path)
            assert total['producer_receipt_SHA'] == closeout['producer_receipt_SHA'] == sha(dest / 'producer_receipt.json')
            assert total['verification_closeout_SHA'] == sha(dest / 'verification_closeout.json')
            for key, path in (('audit_SHA', 'audit.json'), ('own_evidence_SHA', 'independent_evidence.json'),
                              ('claims_SHA', 'native_claims.json'), ('rejection_SHA', 'claim_rejections.json')):
                assert closeout[key] == sha(dest / path)
            assert closeout['no_new_solution_or_certificate_backfilled'] and closeout['necessary_verification_complete']
            produced = producer['t_produce_perf'] - producer['t0_perf']
            verified = total['t_verified_perf'] - producer['t_produce_perf']
            assert 0 < produced <= 1200 and verified >= 0
            assert completion['returncode'] == 0 and completion['stop_reason'] == 'normal_return' and completion['within_cap']
            for key, path in (('result_SHA', 'result.json'), ('observations_SHA', 'observations.json'), ('completion_SHA', 'completion.json')):
                assert ind[key] == sha(dest / path)
            physics = core.full_fleet(ROOT, panel, result)
            assert physics['complete_fleet_vehicles'] == panel['M']
            same(physics['F'], arm['U'], 1e-7)
            same(arm['gap'], arm['U'] - arm['L'], 1e-14)
            for key, value in (('T_produce', produced), ('T_verify', verified), ('T_total', produced + verified)):
                same(arm[key], value)
            expected_time = produced if eligible(arm) and arm['certificate'] else None
            assert original['T_cert'] == expected_time
            for key in ('U', 'L', 'gap', 'T_produce', 'T_verify', 'T_total'):
                same(original[key], arm[key])
            for key in ('certificate', 'formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified', 'source_reduced'):
                assert original.get(key, False) == arm.get(key, False)
            observations = read(dest / 'observations.json')
            calls = [q['payload'] for q in observations if q['payload']['kind'] == 'call']
            assert len({q['call'] for q in calls}) == len(calls)
            for call in calls:
                assert sha(portable(call['model_path'])) == call['model_sha256']
                model_hashes.add(call['model_sha256'])
                assert call['settings'] == dict(read_return_code=0, Threads=1, Seed=group['seed'], Presolve=-1,
                    MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
            assert read(dest / 'call_log_views.json')['bindings'] == item['view']['bindings']
            assert read(dest / 'call_log_views.json')['actual_Optimize'] == arm['native_Optimize']
            arm = dict(arm, group=number, method=method, seed=group['seed'], binary_layer='E3',
                       T_cert=expected_time, destination=str(dest))
            if method in ('P', 'PS'):
                assert arg('--method') == 'gurobi' and '--plain-baseline' in command and '--gurobi-hga-start' not in command
                if calls:
                    assert len(calls) == 1 and calls[0]['full_original']
                    assert sha(dest / 'compact.lp') == panel['reference']['canonical_sha256']
                    params = read(dest / ('round127_parameters.json' if method == 'P' else 'round130_parameters.json'))
                    assert (params['MIPFocus'], params['Cuts'], params['NumStart_before_optimize']) == (0, -1, int(method == 'PS'))
                    assert params['loaded_after_presets'] and params['authoritative_model_environment']
                if method == 'PS':
                    checked = start_reader.start_audit(ROOT, panel, dest) if calls else None
                    assert all(q['native_preconditions'] == (group['seed'] == 0) for q in calls)
                    projected = item['j']['calls']
                    for call in calls:
                        assert projected[call['call']]['native_preconditions']
                    if group['seed']:
                        assert all(not q['payload']['global_available'] and q['payload']['global_bound'] is None
                                   for q in observations if q['payload']['kind'] == 'bound')
                    ps_layers.append(dict(group=number, id=arm['id'], seed=arm['seed'],
                        raw_call_native_preconditions=[bool(q['native_preconditions']) for q in calls],
                        computed_returned_call_prerequisites=[bool(projected[q['call']]['native_preconditions']) for q in calls],
                        raw_top_level_certificate=result['strict_certified_original_problem'],
                        qualified_certificate=arm['certificate'], full_Start=checked,
                        raw_observations_SHA=sha(dest / 'observations.json'),
                        raw_global_flags_not_promoted=True, no_incumbent_adoption_inferred_from_submission=True))
            else:
                assert arg('--method') == 'gcap-frontier' and arg('--round98-state-service') == 'm-binary'
                assert arg('--algorithm-preset') == 'research-round83-vds-equal-net-exchange'
            nonempty = any(len(q['nodes']) > 2 or q['operations'] for q in physics['routes'])
            artifact = dict(group=number, id=arm['id'], seed=arm['seed'], method=method,
                certificate=arm['certificate'], qualified=eligible(arm), source_reduced=arm.get('source_reduced', False),
                final_complete_fleet=physics, nonempty_final_fleet=nonempty, raw_signed_gap=arm['gap'],
                T_cert=expected_time, native_Optimize=arm['native_Optimize'],
                producer_seal_SHA=sha(dest / 'producer_seal.json'), result_SHA=sha(dest / 'result.json'),
                verification_closeout_SHA=sha(dest / 'verification_closeout.json'),
                source_return_cover_rebuilt_from_raw=True)
            artifacts.append(artifact)
            if representative_fleet is None and nonempty:
                representative_fleet = artifact
            native[method] = dict(arm=arm, launch=launch, dest=dest, result=result, calls=calls, item=item)
            arms.append(arm)

        by = {q['method']: q for q in arms[-4:]}
        pairs.extend(comparison(by[a], by[b], group, number) for a, b in PAIR_TYPES)
        hh = {method: h_evidence(ROOT, native[method]['launch']['panel'], native[method]['dest']) for method in ('PS', 'S2', 'S2R')}
        def matched(a, b):
            return bool(hh[a]['complete'] and hh[b]['complete'] and hh[a]['fleet'] == hh[b]['fleet']
                        and hh[a]['semantic_traces'] == hh[b]['semantic_traces'] and hh[a]['physical']['Y'] == hh[b]['physical']['Y'])
        for method in ('S2', 'S2R'):
            H_rows.append(dict(group=number, id=group['role']['id'], seed=group['seed'], left=method, right='PS',
                same_complete_H=matched(method, 'PS'), backend_exposed=by[method]['native_Optimize'] > 0 and by['PS']['native_Optimize'] > 0,
                left_H_complete=hh[method]['complete'], PS_H_complete=hh['PS']['complete']))
        roots = {method: next((q for q in native[method]['calls'] if method in ('P', 'PS') or q['leaf'] == 'L0'), None) for method in METHODS}
        compact_equal = roots['P'] is not None and roots['PS'] is not None \
            and core.lp_model(native['P']['dest'] / 'compact.lp') == core.lp_model(native['PS']['dest'] / 'compact.lp')
        if roots['PS'] is not None:
            assert compact_equal
        c0, c1 = roots['S2'], roots['S2R']
        same_scope = c0 is not None and c1 is not None and all(c0[k] == c1[k] for k in ('lower_g', 'upper_g', 'cutoff'))
        same_settings = c0 is not None and c1 is not None and c0['settings'] == c1['settings']
        difference = root_difference(core, c0, c1) if same_scope else None
        sentinels = 0
        if c0 is not None:
            m = core.lp_model(portable(c0['model_path']))
            sentinels = sum(not t and s == '<=' and rhs == -1 for t, s, rhs in m['rows'])
        controller = native['S2']['item']['controller']
        split_count = sum(q.get('event') == 'atomic_split' for q in controller['controller_events'])
        assert split_count == native['S2']['result']['external_gini_tree_split_count']
        ledger = controller['controller_native']
        target_calls = sum(q['solve_kind'] not in ('LP', 'MIP') for q in ledger)
        pure = bool(matched('S2', 'S2R') and same_scope and same_settings and difference and not sentinels)
        mechanism = dict(group=number, id=group['role']['id'], seed=group['seed'],
            P_PS_complete_original_compact_equal=bool(compact_equal),
            P_PS_fixed_native_parameters_equal=bool(roots['P'] is not None and roots['PS'] is not None and roots['P']['settings'] == roots['PS']['settings']),
            S2_PS_same_complete_H=matched('S2', 'PS'), S2_PS_both_backends_exposed=by['S2']['native_Optimize'] > 0 and by['PS']['native_Optimize'] > 0,
            S2_S2R_complete_H_equal=matched('S2', 'S2R'), S2_S2R_scope_cutoff_equal=bool(same_scope),
            S2_S2R_root_settings_equal=bool(same_settings), actual_root_difference=difference,
            pure_outer_package_attribution_eligible=pure, S2_splits=split_count,
            S2_actual_target_calls=target_calls, S2R_splits=native['S2R']['result']['external_gini_tree_split_count'])
        mechanisms.append(mechanism)
        root_chains.append(dict(group=number, id=group['role']['id'], seed=group['seed'],
                                **root_chain(core, native['S2R'], hh['S2R'])))
        if split_count:
            item = native['S2']['item']
            cover, chrono = item['ep'].get('cover'), item['ep'].get('chronological_cover')
            if not by['S2'].get('source_reduced'):
                assert cover is not None and cover['complete_coverage'] and chrono is not None
            split_examples.append(dict(group=number, id=group['role']['id'], seed=group['seed'],
                actual_atomic_split_events=split_count, certificate=by['S2']['certificate'],
                source_reduced=by['S2'].get('source_reduced', False), complete_cover=cover,
                chronological_cover=chrono, actual_events=controller['controller_events'],
                split_geometry_and_closure_scopes=split_cover_details(core, native['S2']),
                numerical_semantic_closures_are_not_inclusive_root_infeasibility=True))

    assert len(arms) == 24 and len(pairs) == 30 and len({q['input_SHA'] for q in arms}) == 3
    denominators = shared_denominators(pairs)
    # Cross-arm/Seed physical witnesses only revoke a contradictory global L.
    # They never replace an arm's own U, certificate, clock or search history.
    cross_input = []
    for id in IDS:
        rows = [q for q in arms if q['id'] == id and all(q.get(k) is True for k in
                ('formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified'))]
        assert len(rows) == 8
        best = min(q['U'] for q in rows)
        violations = [dict(method=q['method'], seed=q['seed'], own_L=q['L'],
                           other_verified_U=best) for q in rows if q['L'] > best + 1e-7]
        cross_input.append(dict(id=id, qualified_own_observations=len(rows),
            minimum_verified_physical_U_for_contradiction_only=best, violations=violations,
            own_U_values_or_bounds_or_certificates_transferred=False))
    author_cross = read(out / 'cross_arm_bound_consistency.json')
    assert author_cross['comparison_tolerance'] == 1e-7 and author_cross['records'] == cross_input
    assert author_cross['status'] == ('PASS' if not any(q['violations'] for q in cross_input) else 'PROOF_CONTRADICTION_REQUIRES_DECISION')
    assert not any(q['violations'] for q in cross_input), ('same-input physical witness contradicts a global bound', cross_input)
    author = read(out / 'observations.json')
    def csv_rows(path):
        with Path(path).open(newline='', encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))
    arm_key = lambda q: (q['id'], int(q['seed']), q['method'])
    pair_key = lambda q: (int(q['group']), q['left'], q['right'])
    author_arms = {arm_key(q): q for q in author['arms']}
    arm_table = {arm_key(q): q for q in csv_rows(out / 'arms.csv')}
    author_pairs = {pair_key(q): q for q in author['pairs']}
    pair_table = {pair_key(q): q for q in csv_rows(out / 'pairs.csv')}
    assert len(author_arms) == len(arm_table) == 24 and len(author_pairs) == len(pair_table) == 30
    for arm in arms:
        other, row = author_arms[arm_key(arm)], arm_table[arm_key(arm)]
        for key in ('certificate', 'formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified', 'source_reduced'):
            assert other.get(key, False) == arm.get(key, False)
            assert row[key] == str(arm.get(key, False))
        for key in ('U', 'L', 'gap', 'T_produce', 'T_verify', 'T_total'):
            same(other[key], arm[key]); same(float(row[key]), arm[key])
        assert other['T_cert'] == arm['T_cert']
        assert row['T_cert'] == '' if arm['T_cert'] is None else abs(float(row['T_cert']) - arm['T_cert']) <= 1e-8
    for pair in pairs:
        other, row = author_pairs[pair_key(pair)], pair_table[pair_key(pair)]
        for key, expected in pair.items():
            if expected is None:
                assert other[key] is None and row[key] == '', ('invented open/one-sided value', pair_key(pair), key)
            elif isinstance(expected, (float, int)) and not isinstance(expected, bool):
                same(other[key], expected); same(float(row[key]), expected)
            else:
                assert other[key] == expected and row[key] == str(expected), ('pair mismatch', pair_key(pair), key)
    differences = {q['group']: q for q in read(out / 'actual_method_differences.json')['records']}
    assert len(differences) == 6
    for mechanism in mechanisms:
        other = differences[mechanism['group']]
        for key in ('P_PS_complete_original_compact_equal', 'P_PS_fixed_native_parameters_equal',
                    'S2_S2R_complete_H_equal', 'S2_S2R_scope_cutoff_equal', 'S2_S2R_root_settings_equal',
                    'actual_root_difference', 'pure_outer_package_attribution_eligible', 'S2_splits', 'S2R_splits'):
            assert other[key] == mechanism[key], ('same-root/representation mismatch', mechanism['group'], key)
    author_h = {(q['group'], q['left']): q for q in author['same_H']}
    for h in H_rows:
        other = author_h[h['group'], h['left']]
        for key in h:
            assert other[key] == h[key], ('same-H mismatch', h['group'], h['left'], key)
    summary = read(out / 'stratified_summary.json')
    for name, independent in denominators.items():
        other = summary['by_comparison'][name]
        for key in ('rows', 'nonalias_typed_entries', 'evaluable_nonalias_entries', 'unevaluable_nonalias_entries',
                    'alias_entries', 'classes', 'directions', 'both_certified_intersection_n', 'both_certified_ids'):
            assert other[key] == independent[key], ('denominator mismatch', name, key)
        if independent['conditional_geometric_mean'] is None:
            assert other['conditional_geometric_mean'] is None
        else:
            same(other['conditional_geometric_mean'], independent['conditional_geometric_mean'])
    axes, reverse = axes_from_evidence(pairs, mechanisms)
    decision, scope = read(out / 'scientific_decision.json'), read(out / 'claim_scope_assessment.json')
    assert scope['all_reverse_roles_considered'] and scope['reverse_roles'] == reverse
    for name, axis in axes.items():
        other = decision['axes'][name]
        assert other['repeated_direct_roles'] == axis['repeated_direct_roles']
        for row, saved in zip(axis['records'], other['records']):
            for key in row:
                assert saved[key] == row[key], ('attribution-axis mismatch', name, row['id'], key)
    complete = all(eligible(q) for q in arms) and all(q['classification'] != 'UNEVALUABLE' for q in pairs)
    assert summary['execution'] == ('COMPLETE' if complete else 'PARTIAL')
    if any(q.get('source_reduced') for q in arms):
        assert scope['proof_or_identity_issue'], 'observed rejected proof source requires explicit priority disposition'
    expected_tag = 'PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION' if scope['proof_or_identity_issue'] else \
        'SELECTED_MS2_WITH_SCOPED_OR_MIXED_ATTRIBUTION' if not complete else \
        'REFERENCE_CONTROL_EXPOSES_CORE_CLAIM_GAP' if scope['reference_exposes_core_claim_gap'] else \
        'SELECTED_MS2_WITH_DIRECT_BACKEND_AND_CONTROL_EVIDENCE' if all(axis['repeated_direct_roles'] for axis in axes.values()) else \
        'SELECTED_MS2_WITH_SCOPED_OR_MIXED_ATTRIBUTION'
    assert decision['tag'] == expected_tag and expected_tag in (out / 'claim_decision.md').read_text(encoding='utf-8-sig')
    assert decision['R129_candidate_pass_not_reconsidered'] and decision['no_new_method_or_Seed_or_role_or_budget_authorized']
    return dict(status='PASS', independent_executor='Round130 separate final reviewer',
        fixed_arms=24, all_final_complete_fleets_physically_replayed=True, representative_nonempty_final_fleet=representative_fleet or
            dict(status='UNAVAILABLE_IN_FIXED_PANEL', reason='No nonempty final fleet observed; no substitute solve'),
        typed_comparisons=30, comparisons_independently_recomputed=pairs,
        symmetric_materiality='slower - faster >= max(10 seconds, 0.10 * faster)',
        six_shared_matched_groups=[dict(group=n, id=g['role']['id'], seed=g['seed'], arms=4, typed_comparisons=5) for n, g in enumerate(manifest['groups'], 1)],
        shared_denominators=denominators, distinct_inputs=3, Seed_observations_per_input=2,
        same_input_cross_arm_Seed_bound_consistency_independently_checked=cross_input,
        cross_arm_witnesses_used_for_contradiction_revocation_only=True,
        no_independent_trial_count_inferred_from_shared_comparisons=True,
        all_pairs_and_denominators_match_author=True, arm_evidence=artifacts,
        PS_raw_and_computed_layers=ps_layers, S2R_actual_root_chains=root_chains,
        actual_same_H_root_and_representation=mechanisms,
        actual_S2_split_cover_examples=split_examples or [dict(status='NOT_EXPOSED_IN_FIXED_PANEL',
            reason='No natural S2 split occurred; no forced split or substitute role')],
        split_formula_alone_not_the_treatment=True,
        attribution_axes_independently_recomputed=axes, repeated_reverse_reference_roles=reverse,
        scientific_label=expected_tag, core_claim_scope_judgment_is_explicit_author_and_reviewer_input=scope,
        formal_execution_complete=complete, retained_source_reduced_arms=sum(bool(q.get('source_reduced')) for q in arms),
        distinct_actual_model_hashes_checked=len(model_hashes), E3_PE_SHA=PE, predecessor_E2_PE_SHA=E2, DLL_SHA=DLL,
        execution_binding_SHA=sha(out / 'execution_binding.json'), argv_SHA=sha(out / 'argv_freeze.json'),
        author_decision_SHA=sha(out / 'scientific_decision.json'), checker_SHA=sha(Path(__file__)),
        native_binary_bytes_not_required_or_loaded=True, no_original_root_fallback=True,
        Optimize=0, native_starts=0, compilation=0,
        finite_evidence_review_not_third_party_external_replication_or_full_rational_proof=True,
        seconds=time.perf_counter() - tick), 0


def write_receipt(path, result):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        n = 1
        while path.with_name(path.stem + '.prior%02d' % n + path.suffix).exists():
            n += 1
        prior = path.with_name(path.stem + '.prior%02d' % n + path.suffix)
        prior.write_bytes(path.read_bytes())
        result['previous_receipt_retained'] = str(prior)
    result['UTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    tick = time.perf_counter()
    try:
        result, code = check(args.root)
    except Exception as error:
        result, code = dict(status='FAILED_REVIEW_PRESERVE_EVIDENCE', error=repr(error),
            traceback=traceback.format_exc(), seconds=time.perf_counter() - tick,
            Optimize=0, native_starts=0, compilation=0, no_performance_retry_authorized=True), 1
    write_receipt(args.receipt, result)
    print(json.dumps({key: result[key] for key in ('status', 'Optimize')}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
