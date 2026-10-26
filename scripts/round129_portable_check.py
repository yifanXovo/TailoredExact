"""Finite, solver-free R129 evidence review from a supplied/public recovery root.

The thirty pair directions and five research conditions below are independently
implemented here. No R129/R127 pair or candidate-decision routine is imported.
The established read-only physical, H, LP and source/return/cover readers are
reused for evidence interpretation. They are imported only after the complete
thirty-arm closeout gate. This module never starts native software or compiles.

Run only after all formal producers AND the author's analysis are complete:
    python -B scripts/round129_portable_check.py --receipt PATH
An incomplete panel returns NOT_READY without reading models/H/native logs.
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

PE = 'ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa'
DLL = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
BASE = 'cc70757304a2019d95f0f934aa5520d0caa946c6'
METHODS = ('P', 'MB', 'MS2')
PAIR_TYPES = (('MS2', 'P'), ('MS2', 'MB'), ('MB', 'P'))
NEW_IDS = ('UC-C15-S', 'UC-B20-B', 'UC-C20-U', 'UC-B30-S')
PROTECTED = 'PB-C20-B'
ORDERS = (('P', 'MB', 'MS2'), ('MS2', 'MB', 'P'),
          ('MB', 'MS2', 'P'), ('P', 'MS2', 'MB'),
          ('MS2', 'P', 'MB'), ('MB', 'P', 'MS2'),
          ('P', 'MB', 'MS2'), ('MS2', 'MB', 'P'),
          ('MB', 'MS2', 'P'), ('P', 'MS2', 'MB'))
ROOT = Path(__file__).resolve().parents[1]
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
    """Map recorded paths to ROOT; never read an original checkout fallback."""
    value = str(value).replace('\\', '/')
    for prefix in ('results/', 'reference/', 'scripts/', 'src/', 'include/'):
        if value.startswith(prefix):
            suffix = value
            break
        pos = value.find('/' + prefix)
        if pos >= 0:
            suffix = value[pos + 1:]
            break
    else:
        raise AssertionError(('path has no published-root mapping', value))
    rel = PurePosixPath(suffix)
    assert not rel.is_absolute() and '..' not in rel.parts
    path = ROOT.joinpath(*rel.parts).resolve()
    assert path.is_relative_to(ROOT), ('path escaped supplied root', value)
    return path


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def same(a, b, tolerance=1e-8):
    assert a is not None and b is not None
    assert math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance, (a, b)


def eligible(arm):
    return all(arm.get(k) is True for k in
               ('formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified')) \
        and not arm.get('source_reduced', False)


def comparison(left, right, group):
    """Certification-first, strict producer-clock direction; no cap imputation."""
    result = dict(group=group['number'], id=group['role']['id'], seed=group['seed'],
                  left=left['method'], right=right['method'], classification='UNEVALUABLE',
                  direction='UNEVALUABLE', left_T_cert=left['T_cert'], right_T_cert=right['T_cert'],
                  left_minus_right_seconds=None, right_over_left_certification_ratio=None)
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
        result.update(classification='BOTH_CERTIFIED',
                      direction='Win' if delta < 0 else 'Lose' if delta > 0 else 'Tie',
                      left_minus_right_seconds=delta, right_over_left_certification_ratio=b / a)
    elif ac:
        result.update(classification='LEFT_ONLY_CERTIFIED', direction='Win')
    elif bc:
        result.update(classification='RIGHT_ONLY_CERTIFIED', direction='Lose')
    else:
        result.update(classification='BOTH_OPEN', direction='UNDETERMINED')
    return result


def frozen_conditions(arms, pairs, mechanisms):
    """Independent implementation of user goal sections 8/9, all five rules."""
    a = {(x['id'], x['seed'], x['method']): x for x in arms}
    p = {(x['id'], x['seed'], x['left'], x['right']): x for x in pairs}
    d = {(x['id'], x['seed']): x for x in mechanisms}

    def certified(id, seed, method):
        v = a[id, seed, method]
        return eligible(v) and v['certificate'] is True

    counts = {str(s): {m: sum(certified(id, s, m) for id in NEW_IDS)
                       for m in METHODS} for s in (0, 1)}
    both = {m: sum(certified(id, 0, m) and certified(id, 1, m) for id in NEW_IDS)
            for m in METHODS}
    missed = {str(s): {m: sum(certified(id, s, 'P') and eligible(a[id, s, m])
                              and not a[id, s, m]['certificate'] for id in NEW_IDS)
                       for m in ('MB', 'MS2')} for s in (0, 1)}
    c1 = all(counts[str(s)]['MS2'] >= counts[str(s)]['MB'] for s in (0, 1)) \
        and both['MS2'] >= both['MB']
    c2 = all(missed[str(s)]['MS2'] <= missed[str(s)]['MB'] for s in (0, 1))
    protection = []
    for seed in (0, 1):
        bc, sc = certified(PROTECTED, seed, 'MB'), certified(PROTECTED, seed, 'MS2')
        mb, ms = a[PROTECTED, seed, 'MB']['T_cert'], a[PROTECTED, seed, 'MS2']['T_cert']
        loss = ms - mb if bc and sc else None
        protection.append(dict(seed=seed, MB_certified=bc, MS2_certified=sc,
            certificate_retained=(not bc or sc), MB_T_cert=mb, MS2_T_cert=ms,
            MS2_minus_MB_seconds=loss,
            slow_at_least_max30_or25pct=bool(bc and sc and loss >= max(30., .25 * mb))))
    c3 = all(x['certificate_retained'] for x in protection) \
        and not all(x['slow_at_least_max30_or25pct'] for x in protection)
    new_evidence = []
    for id in NEW_IDS:
        seeds = []
        for seed in (0, 1):
            sm, sp = p[id, seed, 'MS2', 'MB'], p[id, seed, 'MS2', 'P']
            mech = d[id, seed]
            mb, ms = a[id, seed, 'MB']['T_cert'], a[id, seed, 'MS2']['T_cert']
            both_cert = sm['classification'] == 'BOTH_CERTIFIED'
            saving = mb - ms if both_cert else None
            threshold = max(10., .10 * mb) if both_cert else None
            material = both_cert and saving >= threshold
            single = sm['classification'] == 'LEFT_ONLY_CERTIFIED'
            exposure = mech['triple_deletion_exposed'] and mech['component_interpretation_eligible']
            seeds.append(dict(seed=seed, MS2_MB_class=sm['classification'],
                MS2_MB_direction=sm['direction'], MS2_P_class=sp['classification'],
                MS2_P_direction=sp['direction'], triple_deletion_exposed=mech['triple_deletion_exposed'],
                component_interpretation_eligible=mech['component_interpretation_eligible'],
                zero_or_no_backend=not mech['MS2_root_exposed'], MS2_saving_seconds=saving,
                material_gain_threshold=threshold, both_certified_material_gain=bool(material),
                MS2_only_certified=single, rule4_seed_signal=bool(exposure and (material or single)),
                rule5_seed_win=sp['direction'] == 'Win'))
        new_evidence.append(dict(id=id, seeds=seeds,
            rule4_both_Seeds=all(s['rule4_seed_signal'] for s in seeds),
            rule5_both_Seeds=all(s['rule5_seed_win'] for s in seeds)))
    c4 = any(x['rule4_both_Seeds'] for x in new_evidence)
    c5 = any(x['rule5_both_Seeds'] for x in new_evidence)
    complete = len(arms) == len(pairs) == 30 and all(eligible(x) for x in arms) \
        and all(x['classification'] != 'UNEVALUABLE' for x in pairs)
    proof_issue = any(x.get('source_reduced') for x in arms)
    if proof_issue:
        tag = 'PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION'
    elif not complete:
        tag = 'PARTIAL_NECESSARY_EVIDENCE_MISSING'
    elif not (c1 and c2 and c3):
        tag = 'RETAIN_FULL_MB_SIMPLIFICATION_NOT_CONFIRMED'
    elif not (c4 and c5):
        tag = 'INSUFFICIENT_NEW_DIRECT_SUPPORT_RETAIN_MB'
    else:
        tag = 'RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE'
    return dict(execution='COMPLETE' if complete else 'PARTIAL', tag=tag,
        conditions={str(k): bool(v) for k, v in enumerate((c1, c2, c3, c4, c5), 1)},
        new_certificate_counts_by_Seed=counts, new_both_Seed_certified_problem_counts=both,
        new_P_certified_method_open_by_Seed=missed, protection=protection,
        new_input_evidence=new_evidence,
        rule4_supporting_new_inputs=[x['id'] for x in new_evidence if x['rule4_both_Seeds']],
        rule5_supporting_new_inputs=[x['id'] for x in new_evidence if x['rule5_both_Seeds']])


def support_kind(row):
    """Recognize actual single-vehicle support rows, retaining multiplicity."""
    terms, sense, rhs = row
    terms = dict(terms)
    z = {n for n in terms if n.startswith('z_')}
    p = {n for n in terms if n.startswith('p_')}
    if len(z) not in (2, 3) or sense != '<=':
        return None
    if len({n.split('_')[1] for n in z | p}) != 1:
        return None
    if set(terms) == z and all(terms[n] == 1 for n in z) and rhs == len(z) - 1:
        return 'cover_' + str(len(z))
    if set(terms) == z | p and len(p) == len(z) \
            and {n.replace('p_', 'z_', 1) for n in p} == z \
            and all(terms[n] == 120 for n in p) and len({terms[n] for n in z}) == 1:
        return 'conditional_' + str(len(z))
    return None


def matrix_difference(core, mb_call, ms_call):
    pa, pb = portable(mb_call['model_path']), portable(ms_call['model_path'])
    a, b = core.lp_model(pa), core.lp_model(pb)
    for key in ('objective', 'order', 'types', 'bounds'):
        assert a[key] == b[key], ('non-support matrix difference', key, relative(pa))
    ca, cb = collections.Counter(a['rows']), collections.Counter(b['rows'])
    assert not cb - ca, ('MS2 added/changed a row', relative(pb))
    removed = ca - cb
    families = collections.Counter()
    for row, multiplicity in removed.items():
        family = support_kind(row)
        assert family in ('cover_3', 'conditional_3'), ('unexpected removed row', row)
        families[family] += multiplicity
    af = collections.Counter(support_kind(row) for row in a['rows'])
    bf = collections.Counter(support_kind(row) for row in b['rows'])
    assert af['cover_2'] == bf['cover_2'] and af['conditional_2'] == bf['conditional_2']
    assert bf['cover_3'] == bf['conditional_3'] == 0
    assert sum(removed.values()) == af['cover_3'] + af['conditional_3']
    return dict(removed_rows=sum(removed.values()), removed_columns=[], families=dict(families),
        pair_cover_before=af['cover_2'], pair_conditional_before=af['conditional_2'],
        triple_cover_before=af['cover_3'], triple_conditional_before=af['conditional_3'],
        pair_cover_after=bf['cover_2'], pair_conditional_after=bf['conditional_2'],
        triple_cover_after=bf['cover_3'], triple_conditional_after=bf['conditional_3'],
        MB_model_SHA=sha(pa), MS2_model_SHA=sha(pb), MB_model=relative(pa), MS2_model=relative(pb),
        triple_deletion_exposed=bool(removed),
        remaining_objective_columns_order_types_bounds_and_duplicate_preserving_rows_identical=True)


def closeout_gate(out, manifest):
    """Only small metadata existence reads precede this gate."""
    missing = []
    if len(manifest.get('groups', [])) != 10:
        return ['manifest does not contain ten groups']
    for group in manifest['groups']:
        camp = out / group['name']
        if not (camp / 'reconstructed.json').is_file():
            missing.append(relative(camp / 'reconstructed.json'))
        if not (camp / 'identity.json').is_file():
            missing.append(relative(camp / 'identity.json'))
            continue
        for launch in read(camp / 'identity.json')['launches']:
            dest = portable(launch['destination'])
            for name in ('producer_seal.json', 'producer_receipt.json', 'arm_total_receipt.json',
                         'verification_closeout.json', 'audit.json', 'independent_evidence.json'):
                if not (dest / name).is_file():
                    missing.append(relative(dest / name))
    for name in ('arms.csv', 'pairs.csv', 'observations.json', 'actual_method_differences.json',
                 'scientific_decision.json', 'candidate_decision.md'):
        if not (out / name).is_file():
            missing.append(relative(out / name))
    return missing


def check(root):
    global ROOT
    ROOT = Path(root).resolve()
    out = ROOT / 'results/unified_exact_round129'
    tick = time.perf_counter()
    manifest = read(out / 'experiment_manifest.json')
    missing = closeout_gate(out, manifest)
    if missing:
        return dict(status='NOT_READY', reason='all thirty arms and author analysis must close first',
                    missing=missing, models_or_H_or_native_logs_read=False, Optimize=0), 2

    # Resolve reader imports inside the supplied recovery root as well. There
    # must be no implicit helper/source read from the invoking old checkout.
    sys.path.insert(0, str(ROOT / 'scripts'))
    # These imports are read-only parsers, not production/campaign executors.
    import round108_reader as core
    from compare_round112_startup import reconstruct as h_evidence
    core.start_reader.ROOT = ROOT
    input_manifest = read(out / 'input_manifest.json')
    identity = read(out / 'E2_identity.json')
    frozen = read(ROOT / 'results/unified_exact_round128/E2_frozen.json')
    binding = read(out / 'execution_binding.json')
    assert manifest['base'] == BASE and manifest['PE_SHA'] == identity['PE_SHA'] == frozen['PE_SHA'] == PE
    assert manifest['DLL_SHA'] == identity['DLL_SHA'] == frozen['DLL_SHA'] == DLL
    assert identity['source_bindings'] == frozen['source_bindings']
    assert binding['protocol_SHA'] == sha(out / 'experiment_manifest.json')
    assert binding['input_manifest_SHA'] == sha(out / 'input_manifest.json')
    assert binding['E2_identity_SHA'] == sha(out / 'E2_identity.json')
    for name, digest in identity['source_bindings'].items():
        assert sha(ROOT / name) == digest, ('source identity', name)
    for name, digest in binding['adapters'].items():
        assert sha(ROOT / name) == digest, ('execution adapter identity', name)
    assert tuple(p['id'] for p in input_manifest['new_roles']) == NEW_IDS
    assert input_manifest['protection_role']['id'] == PROTECTED
    assert input_manifest['new_problem_denominator'] == 4
    for panel in input_manifest['roles']:
        assert sha(ROOT / panel['input_path']) == panel['input_sha256']
    argv = read(out / 'argv_freeze.json')['full_plans']
    assert len(argv) == 10 and sum(len(x['launches']) for x in argv) == 30
    assert sum(len(g['methods']) * g['role']['cap_seconds'] for g in manifest['groups']) == 30600
    arms, pairs, mechanisms, artifacts = [], [], [], []
    sample_fleet = None
    model_hashes = set()
    qualified_sources = []

    for group, frozen_plan in zip(manifest['groups'], argv):
        number = group['number']
        assert tuple(group['methods']) == ORDERS[number - 1]
        assert tuple(map(tuple, group['pairs'])) == PAIR_TYPES and group['seed'] == (number - 1) % 2
        assert group['role']['id'] == (*NEW_IDS, PROTECTED)[(number - 1) // 2]
        camp = out / group['name']
        plan = read(camp / 'identity.json')
        assert plan == frozen_plan and sha(camp / 'identity.json') == binding['groups'][group['name']]
        assert plan['candidate_binary_sha256'] == PE and plan['dll_sha256'] == DLL
        assert plan['source_hashes'] == frozen['source_bindings']
        assert plan['prereg']['common']['affinity_mask'] == 4
        saved = read(camp / 'reconstructed.json')
        aa = saved['arms']
        assert [a['method'] for a in aa] == group['methods'] and len(aa) == len(plan['launches']) == 3
        native = {}
        for launch, arm in zip(plan['launches'], aa):
            dest = portable(launch['destination'])
            assert dest == portable(arm['destination'])
            command, panel = launch['command'], launch['panel']

            def arg(name):
                assert command.count(name) == 1, (number, launch['method'], name)
                return command[command.index(name) + 1]

            assert str(command[0]).replace('\\', '/').endswith('/build-cache/round128/ExactEBRP.exe')
            assert arg('--round127-mode') == ('p' if launch['method'] == 'P' else launch['method'].lower())
            assert '--round128-mode' not in command and '--round127-p-parameters' not in command
            assert arg('--gurobi-seed') == str(group['seed']) and arg('--threads') == arg('--mip-threads') == '1'
            assert arg('--gurobi-presolve') == '-1' and arg('--process-shutdown-margin') == '30'
            assert arg('--time-limit') == str(group['role']['cap_seconds'] - 6)
            assert arg('--process-wall-time-limit') == str(group['role']['cap_seconds'])
            assert launch['hard_stop_seconds'] == launch['cap_seconds'] - 2
            assert arg('--lambda') == '0.15' and arg('--pickup-time') == arg('--drop-time') == '60'
            assert arg('--T') == str(panel['T_seconds']) and launch['seed'] == arm['seed'] == group['seed']
            assert launch['repeat'] == 1 and arm['binary_layer'] == launch['binary_layer'] == 'E2'
            assert arm['PE_SHA'] == PE and arm['DLL_SHA'] == DLL and arm['input_SHA'] == panel['input_sha256']
            producer, total = read(dest / 'producer_receipt.json'), read(dest / 'arm_total_receipt.json')
            seal, close = read(dest / 'producer_seal.json'), read(dest / 'verification_closeout.json')
            audit, independent = read(dest / 'audit.json'), read(dest / 'independent_evidence.json')
            result, completion = read(dest / 'result.json'), read(dest / 'completion.json')
            origin = read(dest / 'child_process_origin.json')
            assert origin['command'] == command and origin['PE_SHA'] == PE and origin['seed'] == group['seed']
            assert origin['creation_from_live_OS_handle'] is True
            assert read(dest / 'launch.json')['command'] == command
            assert producer['producer_seal_SHA'] == sha(dest / 'producer_seal.json')
            assert seal['native_stopped_no_reentry'] and seal['required_outputs_closed']
            for name, digest in seal['required_SHA'].items():
                assert sha(dest / name) == digest, ('producer seal', number, arm['method'], name)
            assert total['producer_receipt_SHA'] == close['producer_receipt_SHA'] == sha(dest / 'producer_receipt.json')
            assert total['verification_closeout_SHA'] == sha(dest / 'verification_closeout.json')
            for field, name in (('audit_SHA', 'audit.json'), ('own_evidence_SHA', 'independent_evidence.json'),
                                ('claims_SHA', 'native_claims.json'), ('rejection_SHA', 'claim_rejections.json')):
                assert close[field] == sha(dest / name)
            assert close['necessary_verification_complete'] and total['necessary_verification_complete']
            assert close['no_new_solution_or_certificate_backfilled']
            produced = producer['t_produce_perf'] - producer['t0_perf']
            verified = total['t_verified_perf'] - producer['t_produce_perf']
            same(arm['T_produce'], produced)
            same(arm['T_verify'], verified)
            same(arm['T_total'], produced + verified)
            assert 0 < produced <= launch['cap_seconds'] and verified >= 0
            assert completion['returncode'] == 0 and completion['stop_reason'] == 'normal_return' and completion['within_cap']
            assert independent['result_SHA'] == sha(dest / 'result.json')
            assert independent['observations_SHA'] == sha(dest / 'observations.json')
            assert independent['completion_SHA'] == sha(dest / 'completion.json')
            physics = core.full_fleet(ROOT, panel, result)
            same(physics['F'], arm['U'], 1e-7)
            same(independent['own_U'], arm['U'], 1e-7)
            assert read(dest / 'production_checks.json')['final_physical_verification'] == independent['physical']
            assert physics['complete_fleet_vehicles'] == panel['M']
            endpoint = audit.get('endpoint')
            if not arm.get('source_reduced'):
                assert endpoint is not None and audit['passed']
                for field in ('U', 'L', 'gap'):
                    same(endpoint[field], arm[field], 1e-7)
                assert endpoint['certificate'] == arm['certificate']
            else:
                assert saved['per_arm_adjudication'][launch['number'] - 1]['damaged_calls']
            same(arm['gap'], arm['U'] - arm['L'], 1e-14)
            required = ('identity_verified', 'input_verified', 'model_domain_verified', 'journal_verified',
                        'return_verified', 'files_verified', 'own_physical_verified', 'independent_floor0')
            protocol_ok = all(independent.get(k) is True for k in required)
            assert arm['formal_protocol_qualified'] == protocol_ok
            assert arm['numbers_qualified'] == (protocol_ok and all(math.isfinite(arm[k]) for k in ('U', 'L')))
            assert arm['certificate_qualified'] == protocol_ok
            expected_t = produced if eligible(arm) and arm['certificate'] else None
            assert arm['T_cert'] == expected_t, ('unknown/open T_cert must be null', number, arm['method'])
            observations = read(dest / 'observations.json')
            calls = [x['payload'] for x in observations if x['payload']['kind'] == 'call']
            calls_by_id = {x['call']: x for x in calls}
            assert len(calls_by_id) == len(calls)
            for call in calls:
                assert sha(portable(call['model_path'])) == call['model_sha256']
                model_hashes.add(call['model_sha256'])
                settings = call['settings']
                for key, value in dict(Threads=1, Seed=group['seed'], Presolve=-1, MIPGap=0, MIPGapAbs=0,
                                       FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6).items():
                    assert settings[key] == value, ('actual native parameter', number, arm['method'], key)
            views = read(dest / 'call_log_views.json')
            assert views['producer_receipt_SHA'] == sha(dest / 'producer_receipt.json')
            assert views['actual_Optimize'] == arm['native_Optimize'] == independent['counts']['actual_Optimize']
            for view in views['bindings']:
                call = calls_by_id[view['call']]
                assert view['model_SHA'] == call['model_sha256']
                log = portable(view['raw_log'])
                assert sha(log) == view['raw_log_SHA']
                with log.open('rb') as f:
                    f.seek(view['byte_begin'])
                    segment = f.read(view['byte_end'] - view['byte_begin'])
                assert hashlib.sha256(segment).hexdigest() == view['segment_SHA']
                for key, value in view.get('parameters', {}).items():
                    if key != 'TimeLimit':
                        assert call['settings'][key] == value
                    else:
                        assert 0 < value <= launch['cap_seconds']
            if arm['method'] == 'P':
                params = read(dest / 'round127_parameters.json')
                assert (params['MIPFocus'], params['Cuts'], params['NumStart_before_optimize']) == (0, -1, 0)
                assert params['loaded_after_presets'] and params['authoritative_model_environment']
                assert '--plain-baseline' in command and arg('--method') == 'gurobi'
                assert '--gurobi-hga-start' not in command and '--round112-ens-start-compact' not in command
                assert arg('--round24-executable-sha256') == arg('--round24-manifest-executable-sha256') == PE
                assert len(calls) == 1 and calls[0]['full_original']
                assert sha(dest / 'compact.lp') == panel['reference']['canonical_sha256']
            else:
                assert arg('--method') == 'gcap-frontier' and arg('--round98-state-service') == 'm-binary'
                assert arg('--algorithm-preset') == 'research-round83-vds-equal-net-exchange'
                assert '--round112-ens-start-compact' not in command and '--round120-native-proof-d1' not in command
            arm = dict(arm, group=number, T_produce=produced, T_verify=verified,
                       T_total=produced + verified, T_cert=expected_t)
            nonempty = any(len(route['nodes']) > 2 or route['operations'] for route in physics['routes'])
            artifacts.append(dict(group=number, id=arm['id'], seed=arm['seed'], method=arm['method'],
                certificate=arm['certificate'], qualified=eligible(arm), source_reduced=arm.get('source_reduced', False),
                T_cert=expected_t, final_complete_fleet=physics, native_Optimize=arm['native_Optimize'],
                seal_SHA=sha(dest / 'producer_seal.json'), producer_receipt_SHA=sha(dest / 'producer_receipt.json'),
                verification_closeout_SHA=sha(dest / 'verification_closeout.json'),
                input_SHA=arm['input_SHA'], raw_signed_gap=arm['gap'], nonempty_final_fleet=nonempty))
            if sample_fleet is None and nonempty:
                sample_fleet = dict(group=number, id=arm['id'], seed=arm['seed'], method=arm['method'],
                                    result_SHA=sha(dest / 'result.json'), complete_physical_replay=physics)
            native[arm['method']] = dict(calls=calls, launch=launch, identity=plan, dest=dest, arm=arm)
            if eligible(arm) and arm['certificate'] and arm['native_Optimize'] > 0:
                qualified_sources.append(native[arm['method']])
            arms.append(arm)
        by = {x['method']: x for x in arms[-3:]}
        pairs.extend(comparison(by[left], by[right], group) for left, right in PAIR_TYPES)
        mb, ms = native['MB'], native['MS2']
        h0 = h_evidence(ROOT, mb['launch']['panel'], mb['dest'])
        h1 = h_evidence(ROOT, ms['launch']['panel'], ms['dest'])
        c0 = next((c for c in mb['calls'] if c['leaf'] == 'L0'), None)
        c1 = next((c for c in ms['calls'] if c['leaf'] == 'L0'), None)
        same_h = h0['complete'] and h1['complete'] and h0['fleet'] == h1['fleet'] \
            and h0['semantic_traces'] == h1['semantic_traces']
        same_scope = c0 is not None and c1 is not None \
            and all(c0[k] == c1[k] for k in ('lower_g', 'upper_g', 'cutoff'))
        same_parameters = c0 is not None and c1 is not None and c0['settings'] == c1['settings']
        diff = matrix_difference(core, c0, c1) if same_scope else None
        triple = bool(diff and diff['triple_deletion_exposed'])
        candidates = group['role']['M'] * (math.comb(group['role']['V'], 2) + math.comb(group['role']['V'], 3))
        assert candidates < 50000
        mechanisms.append(dict(group=number, id=group['role']['id'], seed=group['seed'],
            complete_H_actions_fleet_equal=bool(same_h), MB_H_complete=h0['complete'], MS2_H_complete=h1['complete'],
            H_fleet_equal=h0['fleet'] == h1['fleet'], H_semantic_actions_equal=h0['semantic_traces'] == h1['semantic_traces'],
            initial_own_U_values=[h0['physical']['F'], h1['physical']['F']],
            initial_U_equal=h0['physical']['F'] == h1['physical']['F'], initial_root_scope_U_equal=bool(same_scope),
            actual_initial_native_settings_equal=bool(same_parameters),
            MB_root_exposed=c0 is not None, MS2_root_exposed=c1 is not None,
            pair_plus_triple_candidates=candidates, support_cap=50000, support_cap_binding=False,
            actual_root_difference=diff, triple_deletion_exposed=triple,
            component_interpretation_eligible=bool(same_h and same_parameters and triple)))

    assert len(arms) == len(pairs) == 30 and len({a['input_SHA'] for a in arms}) == 5
    # Only a genuine observed native certificate supplies this sampled chain.
    sample_certificate = dict(status='UNAVAILABLE_IN_FIXED_PANEL',
        reason='No qualified final certificate with actual native Optimize; no alternative role is run')
    if qualified_sources:
        chosen = sorted(qualified_sources, key=lambda x: (x['arm']['U'] <= 0,
                        x['arm']['method'] == 'P', x['arm']['group'], x['arm']['method']))[0]
        # Reuse only the already qualified source/return/cover interpretation,
        # not either author's comparison or five-condition implementation.
        import round114_audit as audit_reader
        import round118_call_logs as call_logs
        from round128_evidence import extension
        launch, dest, plan = chosen['launch'], chosen['dest'], chosen['identity']
        with extension():
            journal = audit_reader.journal(ROOT, launch, dest, read(dest / 'observations.json'))
            views = call_logs.build(ROOT, launch, dest, journal, read(dest / 'result.json'))
            assert views['bindings'] == read(dest / 'call_log_views.json')['bindings']
            with call_logs.activate(views):
                old_journal = core.evidence.journal(ROOT, launch['panel'], dest)
                old_journal['return_sequences'] = journal['return_sequences']
                old_journal['return_available'] = journal['return_available']
                rebuilt = core.endpoint(ROOT, launch, plan, dest, old_journal, False)
            assert rebuilt['arm']['certificate'] is True
            same(rebuilt['arm']['U'], chosen['arm']['U'], 1e-7)
            same(rebuilt['arm']['L'], chosen['arm']['L'], 1e-7)
            sample_certificate = dict(status='CHECKED', group=chosen['arm']['group'],
                id=chosen['arm']['id'], seed=chosen['arm']['seed'], method=chosen['arm']['method'],
                certificate_basis=rebuilt['arm']['certificate_basis'], U=rebuilt['arm']['U'], L=rebuilt['arm']['L'],
                returned_native_proofs=old_journal.get('returned_native_proofs', []),
                complete_cover=rebuilt['cover'], chronological_cover=rebuilt['chronological_cover'],
                actual_call_source_return_bindings=views['bindings'],
                final_own_physical=rebuilt['physical'], producer_receipt_SHA=sha(dest / 'producer_receipt.json'),
                audit_SHA=sha(dest / 'audit.json'), result_SHA=sha(dest / 'result.json'), Optimize=0)

    # Match every typed comparison to author tables, retaining null open times.
    def csv_rows(path):
        with Path(path).open(newline='', encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))

    table = csv_rows(out / 'pairs.csv')
    keys = lambda x: (int(x['group']), x['left'], x['right'])
    table_by = {keys(x): x for x in table}
    assert len(table) == len(table_by) == 30
    for expected in pairs:
        actual = table_by[keys(expected)]
        for field in ('id', 'classification', 'direction'):
            assert actual[field] == expected[field], ('pair disagreement', keys(expected), field)
        assert int(actual['seed']) == expected['seed']
        for field in ('left_T_cert', 'right_T_cert', 'left_minus_right_seconds', 'right_over_left_certification_ratio'):
            if expected[field] is None:
                assert actual[field] == '', ('invented open time/ratio', keys(expected), field)
            else:
                same(float(actual[field]), expected[field], 1e-10)
    author_observations = read(out / 'observations.json')
    author_arms = {(x['id'], x['seed'], x['method']): x for x in author_observations['arms']}
    arm_table = {(x['id'], int(x['seed']), x['method']): x for x in csv_rows(out / 'arms.csv')}
    assert len(author_arms) == len(arm_table) == 30
    for arm in arms:
        key = arm['id'], arm['seed'], arm['method']
        other, row = author_arms[key], arm_table[key]
        for field in ('certificate', 'formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified', 'source_reduced'):
            assert other.get(field, False) == arm.get(field, False)
            if field in row:
                assert row[field] == str(arm.get(field, False))
        for field in ('U', 'L', 'gap', 'T_produce', 'T_verify', 'T_total'):
            same(other[field], arm[field])
            same(float(row[field]), arm[field])
        assert other['T_cert'] == arm['T_cert']
        if arm['T_cert'] is None:
            assert row['T_cert'] == ''
        else:
            same(float(row['T_cert']), arm['T_cert'])
    author_pairs = {keys(x): x for x in author_observations['pairs']}
    assert len(author_pairs) == 30
    for pair in pairs:
        other = author_pairs[keys(pair)]
        for field in pair:
            assert other[field] == pair[field], ('observations pair disagreement', keys(pair), field)
    author_diffs = {x['group']: x for x in read(out / 'actual_method_differences.json')['records']}
    assert len(author_diffs) == 10
    for mechanism in mechanisms:
        other = author_diffs[mechanism['group']]
        for field in mechanism:
            if field == 'actual_root_difference':
                expected_diff, saved_diff = mechanism[field], other[field]
                assert (expected_diff is None) == (saved_diff is None)
                if expected_diff is not None:
                    for k, v in expected_diff.items():
                        if k not in ('MB_model', 'MS2_model'):
                            assert saved_diff[k] == v, ('actual matrix summary disagreement', mechanism['group'], k)
            else:
                assert other[field] == mechanism[field], ('mechanism disagreement', mechanism['group'], field)
    decision = frozen_conditions(arms, pairs, mechanisms)
    author_decision = read(out / 'scientific_decision.json')
    for field in decision:
        assert author_decision[field] == decision[field], ('candidate condition/decision disagreement', field)
    assert author_decision['current_paper_identity_and_defaults_changed'] is False
    assert author_decision['old_MB_tables_relabelled'] is False
    assert author_decision['extra_experiments_to_get_favorable_result'] == 0
    assert decision['tag'] in (out / 'candidate_decision.md').read_text(encoding='utf-8-sig')
    representative = next((dict(status='CHECKED', group=x['group'], id=x['id'], seed=x['seed'],
                                **x['actual_root_difference'])
                           for x in mechanisms if x['triple_deletion_exposed']),
                          dict(status='UNAVAILABLE_IN_FIXED_PANEL', reason='No matching-scope positive triple deletion; no substitute run'))
    return dict(status='PASS', independent_executor='Round129 separate final reviewer',
        thirty_fixed_arms_complete=True, actual_producer_seals=30, distinct_input_count=5,
        new_problem_count=4, protection_input_count=1, typed_comparisons=30,
        comparisons_independently_recomputed=pairs, five_conditions_independently_recomputed=decision,
        every_pair_and_all_five_conditions_match_author=True,
        all_actual_final_complete_fleets_physically_replayed=True, arm_evidence=artifacts,
        all_group_H_roots_differences_independently_rechecked=mechanisms,
        distinct_actual_model_hashes_checked=len(model_hashes),
        representative_nonempty_fleet=sample_fleet or dict(status='UNAVAILABLE_IN_FIXED_PANEL', reason='All actual final fleets empty'),
        representative_actual_MS2_complete_triple_difference=representative,
        representative_actual_optimal_certificate_source_chain=sample_certificate,
        actual_native_exposure=sum(a['native_Optimize'] > 0 for a in arms),
        startup_zero_without_native=[dict(group=a['group'], id=a['id'], seed=a['seed'], method=a['method'])
                                    for a in arms if a['native_Optimize'] == 0 and a['certificate']],
        no_assumption_of_native_root_or_triple_exposure=True,
        E2_PE_SHA=PE, DLL_SHA=DLL, production_base=BASE,
        execution_binding_SHA=sha(out / 'execution_binding.json'), argv_SHA=sha(out / 'argv_freeze.json'),
        author_decision_SHA=sha(out / 'scientific_decision.json'),
        original_native_binary_bytes_excluded_from_portable_recovery=True,
        build_identity_scope='original frozen E2/source/OS-child/seal declarations; no native binary loaded by checker',
        no_original_root_fallback=True, Optimize=0, native_starts=0, compilation=0,
        finite_evidence_review_not_external_replication_or_full_rational_proof=True,
        seconds=time.perf_counter() - tick), 0


def write_receipt(path, result):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        n = 1
        while path.with_name(path.stem + f'.prior{n:02d}' + path.suffix).exists():
            n += 1
        retained = path.with_name(path.stem + f'.prior{n:02d}' + path.suffix)
        retained.write_bytes(path.read_bytes())
        result['previous_receipt_retained'] = str(retained)
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
            Optimize=0, native_starts=0, compilation=0,
            no_performance_retry_authorized=True), 1
    write_receipt(args.receipt, result)
    print(json.dumps({k: result[k] for k in ('status', 'Optimize')}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
