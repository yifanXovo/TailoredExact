"""Finite independent R131 review; never produce or optimize an experiment.

The standard-library readiness gate precedes every evidence-reader import and
every formal model, fleet, H trace or native-log read. --preflight checks only
the frozen ten-input / twenty-six-group contract and actual argv bindings.
The default final review requires all fifty-two closeouts and author tables.
The established physical/model/Start/source/return/coverage reader is reused;
the comparison, null and stratum calculations below are independent of the
author's R131 analysis and decision code.
"""

from pathlib import Path, PurePosixPath
import argparse
import collections
import contextlib
import csv
import datetime
import hashlib
import importlib
import json
import math
import statistics
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
PE = '2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
DLL = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
EXPECTED_PARENT = 'c302bae0ec128f0d4c651fb29d04cb41b491f721'
HASHES = {}
RAW_SUPPORT_FIELDS = (
    'compact_bc_support_duration_pair_cuts_added',
    'compact_bc_support_duration_triple_cuts_added',
    'compact_bc_pairwise_transfer_compatibility_cuts_added',
    'tailored_bc_support_duration_pair_candidates',
    'tailored_bc_support_duration_pair_cuts_added',
    'tailored_bc_support_duration_triple_candidates',
    'tailored_bc_support_duration_triple_cuts_added',
)

# Transcribed from the human's fixed contract, rather than the author manifest.
# id, layer, V, M, inventory, geometry, capacities, physical T, per-arm cap, SHA.
SPECS = (
    ('SC-C15-S', 'A', 15, 2, 'shortage', 'compact', [30, 30], 3600, 600,
     '9849095e3496254fa9ea28715939b7380bd47fbaa6e998bff56c688e0e176101'),
    ('SC-B15-S', 'A', 15, 2, 'shortage', 'regional', [20, 40], 5400, 600,
     'b87de1a37e60cc2e7cbbf7885bac1155ac4c0b14356de7c5af92e402555474de'),
    ('SC-C15-B', 'A', 15, 2, 'balanced', 'regional', [30, 30], 5400, 600,
     'c0d5fc4eee62e1e454b8acde8b721640e410bf496593b14d4cbdb1ccf36f14ea'),
    ('SC-B20-S', 'A', 20, 2, 'shortage', 'compact', [30, 30], 5400, 1200,
     '70ebad164c3da58c52d0ad7fce651a6f4d90f54323a939d6c109a17eaffb8b3c'),
    ('SC-C20-S', 'A', 20, 2, 'shortage', 'regional', [20, 40], 7200, 1200,
     '5729b59070d5451750e8e0b2446b08381e5c001e96d3c3f247e57801f6dcde11'),
    ('SC-B20-U', 'A', 20, 2, 'surplus', 'compact', [30, 30], 7200, 1200,
     'c688de15fc31612b83885efe2e86e60f50ba57a5c5119f7e7801bf240a096bab'),
    ('SM-C8-S', 'B', 8, 1, 'shortage', 'compact', [20], 2400, 90,
     'cd0c04a81c0096147d1c365eb4da02ad85397bbef2987d0b13be00628a6b3be0'),
    ('SM-B10-B', 'B', 10, 2, 'balanced', 'regional', [15, 25], 3600, 90,
     '32496a729183c1fa6c9837bb6a18455f8e60ea96fc8a8b803a2ddc5ae15aca8f'),
    ('PB-C35-U', 'C', 35, 3, 'surplus', 'regional', [20, 25, 30], 10800, 2400,
     '67fa5712962980350c0b7be00abbcc4866af0fe376d0395b565ec082d36842e5'),
    ('PB-B35-B', 'C', 35, 3, 'balanced', 'compact', [25, 25, 25], 7200, 2400,
     '41fdb57cad176be7746bb7c884f62da1643920ac2c49d75bd5235663936a5e3a'),
)
SPEC = {r[0]: r for r in SPECS}
# (id, Seed, repeat, method order), exactly the twenty-six supplied rows.
GROUPS = (
    ('SC-C15-S', 0, 1, ('P', 'S2')), ('SC-C15-S', 1, 1, ('S2', 'P')),
    ('SC-B15-S', 0, 1, ('S2', 'P')), ('SC-B15-S', 1, 1, ('P', 'S2')),
    ('SC-C15-B', 0, 1, ('P', 'S2')), ('SC-C15-B', 1, 1, ('S2', 'P')),
    ('SC-B20-S', 0, 1, ('S2', 'P')), ('SC-B20-S', 1, 1, ('P', 'S2')),
    ('SC-C20-S', 0, 1, ('P', 'S2')), ('SC-C20-S', 1, 1, ('S2', 'P')),
    ('SC-B20-U', 0, 1, ('S2', 'P')), ('SC-B20-U', 1, 1, ('P', 'S2')),
    ('SM-C8-S', 0, 1, ('P', 'S2')), ('SM-C8-S', 0, 2, ('S2', 'P')),
    ('SM-C8-S', 1, 1, ('S2', 'P')), ('SM-C8-S', 1, 2, ('P', 'S2')),
    ('SM-C8-S', 2, 1, ('P', 'S2')), ('SM-C8-S', 2, 2, ('S2', 'P')),
    ('SM-B10-B', 0, 1, ('S2', 'P')), ('SM-B10-B', 0, 2, ('P', 'S2')),
    ('SM-B10-B', 1, 1, ('P', 'S2')), ('SM-B10-B', 1, 2, ('S2', 'P')),
    ('SM-B10-B', 2, 1, ('S2', 'P')), ('SM-B10-B', 2, 2, ('P', 'S2')),
    ('PB-C35-U', 0, 1, ('P', 'S2')), ('PB-B35-B', 0, 1, ('S2', 'P')),
)


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
    """Recorded paths map only inside the supplied root, with no fallback."""
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
        raise AssertionError(('no published-root mapping', value))
    rel = PurePosixPath(suffix)
    assert not rel.is_absolute() and '..' not in rel.parts
    path = ROOT.joinpath(*rel.parts).resolve()
    assert path.is_relative_to(ROOT), ('path escaped supplied root', value)
    return path


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def same(actual, expected, tolerance=1e-8):
    assert actual is not None and expected is not None
    assert math.isfinite(actual) and math.isfinite(expected)
    assert abs(actual - expected) <= tolerance, (actual, expected, tolerance)


def layer(group):
    return SPEC[group['role']['id']][1]


def eligible(arm):
    return all(arm.get(k) is True for k in
               ('formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified')) \
        and not arm.get('source_reduced', False)


def arm_key(arm):
    return arm['id'], int(arm['seed']), int(arm['repeat']), arm['method']


def pair_key(pair):
    return int(pair['group']), pair['left'], pair['right']


def options(command):
    out = {}
    index = 1
    while index < len(command):
        name = command[index]
        assert name.startswith('--') and name not in out, ('duplicate/positional option', name)
        index += 1
        if index < len(command) and not command[index].startswith('--'):
            out[name] = command[index]
            index += 1
        else:
            out[name] = True
    return out


def fixed_role(panel):
    id, _, v, m, inventory, geography, capacities, duration, cap, digest = SPEC[panel['id']]
    expected = dict(V=v, M=m, inventory=inventory, geometry=geography,
                    Q_vector=capacities, T_seconds=duration, cap_seconds=cap,
                    pickup_seconds=60, drop_seconds=60, **{'lambda': .15})
    for key, value in expected.items():
        assert panel[key] == value, ('fixed input contract', id, key, panel.get(key), value)
    assert panel['input_sha256'] == digest and sha(portable(panel['input_path'])) == digest
    assert panel.get('prospective_new_validation', False) is False
    return expected


def command_contract(launch, group):
    command, panel = launch['command'], launch['panel']
    o = options(command)
    cap = panel['cap_seconds']
    method = launch['method']
    required = {
        '--lambda': '0.15', '--T': str(panel['T_seconds']), '--pickup-time': '60',
        '--drop-time': '60', '--time-limit': str(cap - 6),
        '--process-wall-time-limit': str(cap), '--process-shutdown-margin': '30',
        '--threads': '1', '--mip-threads': '1', '--gurobi-seed': str(group['seed']),
        '--gurobi-presolve': '-1', '--round61-candidate-mode': 'off',
        '--round127-mode': {'P': 'p', 'S2': 'ms2'}[method],
    }
    path_outputs = {
        '--out': 'result.json', '--log': 'native.log', '--process-phase-ledger': 'phases.csv',
        '--external-gini-artifact-dir': 'external', '--primal-heuristic-generation-log': 'hga.csv',
        '--progress-log': 'progress.csv', '--native-evidence-dir': 'journal',
    }
    if method == 'P':
        required.update({'--method': 'gurobi', '--plain-baseline': True,
                         '--round24-expected-gurobi-model-fingerprint': str(panel['reference']['fingerprint']),
                         '--round24-executable-sha256': PE, '--round24-manifest-executable-sha256': PE})
        path_outputs['--gurobi-model-export'] = 'compact.lp'
    else:
        required.update({'--method': 'gcap-frontier', '--algorithm-preset': 'research-round83-vds-equal-net-exchange',
                         '--round90-lp-g-split': 'false', '--round65-witness-audit': 'true',
                         '--round65-hga-zero-stop': 'true', '--round98-state-service': 'm-binary'})
    assert set(o) == set(required) | set(path_outputs) | {'--input'}, ('unexpected/missing full argv', method, set(o))
    for key, value in required.items():
        assert o[key] == value, ('argv', group['role']['id'], method, key, o.get(key), value)
    assert portable(o['--input']) == portable(panel['input_path'])
    dest = portable(launch['destination'])
    for key, suffix in path_outputs.items():
        assert portable(o[key]) == dest / suffix, ('output identity', key)
    assert str(command[0]).replace('\\', '/').endswith('/build-cache/round130/ExactEBRP.exe')
    assert launch['hard_stop_seconds'] == cap - 2 and launch['cap_seconds'] == cap
    assert launch['seed'] == panel['gurobi_seed'] == group['seed']
    assert launch['repeat'] == group['repeat'] and launch['binary_layer'] == 'E3'
    assert launch['id'] == panel['id'] == group['role']['id']


def manifest_contract(out):
    manifest, inputs = read(out / 'experiment_manifest.json'), read(out / 'input_manifest.json')
    argv, binding = read(out / 'argv_freeze.json'), read(out / 'execution_binding.json')
    frozen = read(out / 'E3_binding.json')
    assert manifest['round'] == 131 and len(manifest['groups']) == len(GROUPS)
    assert manifest['formal_arms'] == argv['formal_arms'] == binding['formal_arms'] == 52
    assert manifest['matched_groups'] == argv['typed_comparisons'] == binding['formal_pairs'] == 26
    assert manifest['distinct_inputs'] == 10 and manifest['nominal_formal_seconds'] == 33360
    assert manifest['layers'] == dict(A=dict(groups=12, arms=24, nominal_seconds=21600, distinct_inputs=6),
                                     B=dict(groups=12, arms=24, nominal_seconds=2160, distinct_inputs=2),
                                     C=dict(groups=2, arms=4, nominal_seconds=9600, distinct_inputs=2))
    assert manifest['own_H_seed'] == 20260626 and manifest['no_pooling_across_layers']
    assert manifest['certification_imputation'] is False and manifest['extra_experiments_authorized'] is False
    assert binding['formal_methods'] == ['P', 'S2'] and binding['serial']
    assert argv['actual_modes'] == dict(P='p', S2='ms2') and argv['Optimize'] == 0
    assert tuple(p['id'] for p in inputs['roles']) == tuple(r[0] for r in SPECS)
    assert frozen['PE_SHA'] == argv['PE_SHA'] == PE and frozen['DLL_SHA'] == argv['DLL_SHA'] == DLL
    inherited = read(portable(frozen['inherited_E3_seal']))
    assert sha(portable(frozen['inherited_E3_seal'])) == frozen['inherited_E3_seal_SHA']
    assert inherited['qualification_complete'] and not inherited['final_qualification_pending']
    assert frozen['source_bindings'] == inherited['source_bindings']
    assert frozen['source_commit'] == '7564a5415331b380e24d1ec06936dcfd56557e67'
    assert frozen['production_compile'] == 0 and frozen['algorithm_change'] is False
    for key, filename in (('protocol_SHA', 'experiment_manifest.json'),
                          ('input_manifest_SHA', 'input_manifest.json'), ('E3_binding_SHA', 'E3_binding.json')):
        assert binding[key] == sha(out / filename), ('execution seal', filename)
    for path, digest in frozen['source_bindings'].items():
        assert sha(ROOT / path) == digest, ('frozen production source', path)
    for path, digest in binding['adapters'].items():
        assert sha(ROOT / path) == digest, ('bound adapter', path)
    for panel in inputs['roles']:
        fixed_role(panel)
    assert len(argv['full_plans']) == 26
    positions, destinations, keys, fees, plans = 0, set(), set(), collections.Counter(), []
    for number, (group, contract, frozen_plan) in enumerate(zip(manifest['groups'], GROUPS, argv['full_plans']), 1):
        id, seed, repeat, order = contract
        assert (group['role']['id'], group['seed'], group['repeat'], tuple(group['methods'])) == contract
        if 'layer' in group:
            assert group['layer'] == SPEC[id][1]
        if 'stratum' in group:
            assert group['stratum'] == SPEC[id][1]
        fixed_role(group['role'])
        plan_path = out / group['name'] / 'identity.json'
        plan = read(plan_path)
        assert plan == frozen_plan and sha(plan_path) == binding['groups'][group['name']]
        assert plan['candidate_binary_sha256'] == PE and plan['dll_sha256'] == DLL
        assert plan['source_hashes'] == frozen['source_bindings']
        assert plan['measured_source_commit'] == frozen['source_commit']
        assert plan['runner_sha256'] == sha(ROOT / 'scripts/round131_benchmark.py')
        assert plan['prereg_sha256'] == binding['protocol_SHA']
        common = plan['prereg']['common']
        for key, value in dict(affinity_mask=4, threads=1, mip_threads=1, gurobi_presolve=-1,
                native_limit_offset_seconds=6, hard_stop_offset_seconds=2, shutdown_margin_seconds=30,
                requested_mip_gap=0, requested_mip_gap_abs=0, FeasibilityTol=1e-6,
                IntFeasTol=1e-5, OptimalityTol=1e-6).items():
            assert common[key] == value, ('common contract', number, key)
        assert common['gurobi_seed'] == seed and common['gurobi_version'] == '13.0.2'
        assert tuple(l['method'] for l in plan['launches']) == order
        for position, launch in enumerate(plan['launches'], 1):
            fixed_role(launch['panel'])
            command_contract(launch, group)
            assert launch['number'] == position and launch['group_number'] == number
            assert launch['global_launch_number'] == 2 * (number - 1) + position
            assert launch['evidence_layer'] == layer(group)
            dest = portable(launch['destination'])
            key = (id, seed, repeat, launch['method'])
            assert dest not in destinations and key not in keys
            destinations.add(dest)
            keys.add(key)
            positions += 1
            fees[layer(group)] += launch['cap_seconds']
        plans.append(plan)
    assert positions == len(destinations) == len(keys) == 52
    assert dict(fees) == dict(A=21600, B=2160, C=9600) and sum(fees.values()) == 33360
    return manifest, plans, dict(fixed_arms=52, matched_comparisons=26, distinct_inputs=10,
        nominal_seconds_by_layer=dict(fees), nominal_formal_seconds=33360,
        parent_recorded=manifest.get('base'), expected_R130_parent=EXPECTED_PARENT,
        source_bindings=len(frozen['source_bindings']), fixed_input_SHA_checked=10,
        full_argv_checked=52, same_seed_repeat_in_unique_key=True,
        actual_mode_and_native_parameters_after_run_pending=True,
        Optimize=0, native_starts=0, compilation=0)


def closeout_gate(out):
    """Only existence and small group identities before the no-content gate."""
    required = ('experiment_manifest.json', 'input_manifest.json', 'argv_freeze.json',
                'execution_binding.json', 'E3_binding.json')
    missing = [relative(out / name) for name in required if not (out / name).is_file()]
    if missing:
        return missing
    manifest = read(out / 'experiment_manifest.json')
    if len(manifest.get('groups', [])) != 26:
        return ['manifest must contain the fixed twenty-six groups']
    count = 0
    for group in manifest['groups']:
        camp = out / group['name']
        for name in ('identity.json', 'reconstructed.json'):
            if not (camp / name).is_file():
                missing.append(relative(camp / name))
        if not (camp / 'identity.json').is_file():
            continue
        for launch in read(camp / 'identity.json')['launches']:
            count += 1
            dest = portable(launch['destination'])
            for name in ('arm_total_receipt.json', 'producer_seal.json', 'producer_receipt.json',
                         'verification_closeout.json', 'audit.json', 'independent_evidence.json'):
                if not (dest / name).is_file():
                    missing.append(relative(dest / name))
    if count != 52:
        missing.append('all fifty-two fixed launch positions must exist')
    for name in ('arms.csv', 'pairs.csv', 'observations.json', 'stratified_summary.json',
                 'tiny_summary.json', 'mechanism_costs.csv', 'model_index.csv', 'numeric_policy_impacts.json',
                 'benchmark_assessment.md', 'cross_arm_bound_consistency.json'):
        if not (out / name).is_file():
            missing.append(relative(out / name))
    return missing


def comparison(s2, p, group, number):
    """No tolerance on time direction; no imputation for an open endpoint."""
    row = dict(group=number, id=group['role']['id'], seed=group['seed'], repeat=group['repeat'],
        layer=layer(group), left='S2', right='P', classification='UNEVALUABLE', direction='UNEVALUABLE',
        S2_certified=bool(s2.get('certificate')), P_certified=bool(p.get('certificate')),
        S2_T_cert=s2.get('T_cert'), P_T_cert=p.get('T_cert'),
        S2_T_produce=s2.get('T_produce'), P_T_produce=p.get('T_produce'),
        S2_T_verify=s2.get('T_verify'), P_T_verify=p.get('T_verify'),
        S2_T_total=s2.get('T_total'), P_T_total=p.get('T_total'),
        S2_minus_P_seconds=None, P_over_S2_certification_ratio=None, absolute_seconds_difference=None,
        materiality=None, tiny_10_second_warning=False, P_only_risk=False, objective_conflict=False,
        S2_U=s2['U'], S2_L=s2['L'], P_U=p['U'], P_L=p['L'])
    if not (eligible(s2) and eligible(p)):
        return row
    for key in ('PE_SHA', 'DLL_SHA', 'input_SHA', 'seed', 'repeat'):
        assert s2[key] == p[key], ('matched-pair identity', key)
    a, b = bool(s2['certificate']), bool(p['certificate'])
    if a and b:
        same(s2['U'], p['U'], 1e-7)
        sa, pb = s2['T_cert'], p['T_cert']
        assert sa is not None and pb is not None and min(sa, pb) > 0
        delta = sa - pb
        row.update(classification='BOTH_CERTIFIED',
            direction='Win' if delta < 0 else 'Lose' if delta > 0 else 'Tie',
            S2_minus_P_seconds=delta, P_over_S2_certification_ratio=pb / sa,
            absolute_seconds_difference=abs(delta))
        threshold = max(10., .10 * min(sa, pb))
        row['materiality'] = 'S2_MATERIALLY_FASTER' if -delta >= threshold else \
                            'P_MATERIALLY_FASTER' if delta >= threshold else 'TIME_CLOSE'
        row['tiny_10_second_warning'] = layer(group) == 'B' and delta >= 10.
    elif a:
        row.update(classification='S2_ONLY_CERTIFIED', direction='Win', materiality='S2_ONLY_CERTIFIED')
    elif b:
        row.update(classification='P_ONLY_CERTIFIED', direction='Lose', materiality='P_ONLY_CERTIFIED', P_only_risk=True)
    else:
        row.update(classification='BOTH_OPEN', direction='UNDETERMINED')
    return row


def distribution(values):
    values = list(values)
    return dict(n=len(values), median=statistics.median(values) if values else None,
                minimum=min(values) if values else None, maximum=max(values) if values else None)


def independent_summaries(arms, pairs):
    strata = {}
    for name, wanted_pairs, wanted_arms, inputs in (('A', 12, 24, 6), ('B', 12, 24, 2), ('C', 2, 4, 2)):
        rows = [q for q in pairs if q['layer'] == name]
        aa = [a for a in arms if a['layer'] == name]
        assert len(rows) == wanted_pairs and len(aa) == wanted_arms and len({q['id'] for q in rows}) == inputs
        both = [q for q in rows if q['classification'] == 'BOTH_CERTIFIED']
        ratios = [q['P_over_S2_certification_ratio'] for q in both]
        strata[name] = dict(matched_groups=len(rows), arms=len(aa), distinct_inputs=inputs,
            classes=dict(collections.Counter(q['classification'] for q in rows)),
            directions=dict(collections.Counter(q['direction'] for q in rows)),
            both_certified_intersection_n=len(both),
            both_certified_intersection=[{k:q[k] for k in ('group', 'id', 'seed', 'repeat')} for q in both],
            conditional_geometric_mean_P_over_S2=math.exp(math.fsum(math.log(r) for r in ratios) / len(ratios)) if ratios else None,
            total_production_seconds_including_open={m: math.fsum(a['T_produce'] for a in aa if a['method'] == m) for m in ('P', 'S2')},
            certification_counts={m: sum(bool(a['certificate']) and eligible(a) for a in aa if a['method'] == m) for m in ('P', 'S2')},
            nonzero_certification_counts={m: sum(bool(a['certificate']) and eligible(a) and a['U'] > 1e-7 for a in aa if a['method'] == m) for m in ('P', 'S2')},
            zero_certification_counts={m: sum(bool(a['certificate']) and eligible(a) and a['own_exact_zero'] for a in aa if a['method'] == m) for m in ('P', 'S2')},
            no_backend_exposure={m: sum(a['native_Optimize'] == 0 for a in aa if a['method'] == m) for m in ('P', 'S2')},
            total_production_is_not_total_certification_time=True, open_T_cert_imputed=False)
    tiny = []
    for id in ('SM-C8-S', 'SM-B10-B'):
        rows = [q for q in pairs if q['id'] == id]
        assert [(q['seed'], q['repeat']) for q in rows] == [(s, r) for s in (0, 1, 2) for r in (1, 2)]
        both = [q for q in rows if q['classification'] == 'BOTH_CERTIFIED']
        aa = [a for a in arms if a['id'] == id]
        seeds = []
        for seed in (0, 1, 2):
            rr = [q for q in rows if q['seed'] == seed]
            bb = [q for q in rr if q['classification'] == 'BOTH_CERTIFIED']
            seeds.append(dict(seed=seed, observations=rr, valid_both_certified_repeats=len(bb),
                S2_minus_P_seconds=distribution(q['S2_minus_P_seconds'] for q in bb) if len(bb) == 2 else None,
                fluctuation_estimated_from_fewer_than_two=False,
                repeatable_10_second_warning=len(bb) == 2 and all(q['tiny_10_second_warning'] for q in bb),
                P_only_certification_risk=any(q['P_only_risk'] for q in rr)))
        tiny.append(dict(id=id, all_six=rows, by_seed=seeds,
            S2_minus_P_seconds=distribution(q['S2_minus_P_seconds'] for q in both),
            certification_seconds={m: distribution(a['T_cert'] for a in aa if a['method'] == m and a['T_cert'] is not None) for m in ('P', 'S2')},
            production_seconds_all_six={m: distribution(a['T_produce'] for a in aa if a['method'] == m) for m in ('P', 'S2')},
            warnings_10_seconds=sum(q['tiny_10_second_warning'] for q in rows),
            at_least_two_10_second_warnings_among_six=sum(q['tiny_10_second_warning'] for q in rows) >= 2,
            P_only_risks=sum(q['P_only_risk'] for q in rows), practical_threshold_is_not_a_noise_theorem=True))
    return strata, tiny


def support_family(row):
    """R130's corrected same-vehicle interpretation, independently stated."""
    pairs, sense, rhs = row
    terms = dict(pairs)
    z = {n for n in terms if n.startswith('z_')}
    p = {n for n in terms if n.startswith('p_')}
    if len(z) in (2, 3) and sense == '<=' and len({n.split('_')[1] for n in z | p}) == 1:
        if set(terms) == z and all(terms[n] == 1 for n in z) and rhs == len(z) - 1:
            return 'cover_' + str(len(z))
        if set(terms) == z | p and len(p) == len(z) and {n.replace('p_', 'z_', 1) for n in p} == z \
                and all(terms[n] == 120 for n in p) and len({terms[n] for n in z}) == 1:
            return 'conditional_' + str(len(z))
    if sense == '<=' and rhs == 0 and sum(n.startswith('d_') for n in terms) == 1 \
            and all(n.startswith(('d_', 'p_')) for n in terms):
        return 'ordered_supply'
    return None


@contextlib.contextmanager
def no_handoff_write(adapter):
    """The old empty-route handoff diagnostic may be recomputed, never saved."""
    old = adapter.write
    diagnostics = []
    def record(path, value):
        path = portable(path)
        assert path.name == 'round127_empty_route_handoff.json', ('unexpected reader mutation', path)
        if path.exists():
            assert read(path) == value, ('retained handoff diagnostic drift', relative(path))
        diagnostics.append(dict(path=relative(path), recomputed=True, raw_modified=False))
    adapter.write = record
    try:
        yield diagnostics
    finally:
        adapter.write = old


def csv_rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def equal_value(expected, actual, label):
    if expected is None:
        assert actual is None, ('null invented', label, actual)
    elif isinstance(expected, bool):
        assert actual is expected, ('boolean drift', label, actual)
    elif isinstance(expected, (int, float)):
        same(actual, expected)
    elif isinstance(expected, dict):
        assert isinstance(actual, dict) and set(expected) <= set(actual), ('missing mapping fields', label)
        for key, value in expected.items():
            equal_value(value, actual[key], (label, key))
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(expected) == len(actual), ('sequence drift', label)
        for index, (left, right) in enumerate(zip(expected, actual)):
            equal_value(left, right, (label, index))
    else:
        assert actual == expected, ('value drift', label, actual, expected)


def check_author(out, arms, pairs, strata, tiny, actual_models, actual_costs):
    author = read(out / 'observations.json')
    aa = {arm_key(q): q for q in author['arms']}
    at = {arm_key(q): q for q in csv_rows(out / 'arms.csv')}
    pp = {pair_key(q): q for q in author['pairs']}
    pt = {pair_key(q): q for q in csv_rows(out / 'pairs.csv')}
    assert len(author['arms']) == len(aa) == len(at) == 52
    assert len(author['pairs']) == len(pp) == len(pt) == 26
    for arm in arms:
        other, row = aa[arm_key(arm)], at[arm_key(arm)]
        for key in ('certificate', 'formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified', 'source_reduced'):
            assert other.get(key, False) == arm.get(key, False)
            assert row[key] == str(arm.get(key, False))
        for key in ('U', 'L', 'gap', 'T_produce', 'T_verify', 'T_total', 'T_cert'):
            equal_value(arm[key], other[key], (arm_key(arm), key))
            if arm[key] is None:
                assert row[key] == '', ('CSV null invented', arm_key(arm), key)
            else:
                same(float(row[key]), arm[key])
        censoring = not arm['certificate'] if eligible(arm) else None
        equal_value(censoring, other['right_censored'], (arm_key(arm), 'right_censored'))
        assert row['right_censored'] == ('' if censoring is None else str(censoring))
        same(other['actual_observation_end_seconds'], arm['T_produce'])
    for pair in pairs:
        other, row = pp[pair_key(pair)], pt[pair_key(pair)]
        for key, value in pair.items():
            equal_value(value, other[key], (pair_key(pair), key))
            if value is None:
                assert row[key] == '', ('CSV pair null invented', pair_key(pair), key)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                same(float(row[key]), value)
            else:
                assert row[key] == str(value), ('CSV pair drift', pair_key(pair), key)
    summary = read(out / 'stratified_summary.json')
    # This key intentionally describes the three independent strata only.
    for name, independent in strata.items():
        other = summary['layers'][name]
        equal_value(independent, other, ('stratum', name))
    equal_value(tiny, read(out / 'tiny_summary.json')['roles'], 'tiny per-seed/repeat statistics')
    assert summary['actual_formal_arms'] == 52 and summary['matched_groups'] == 26 and summary['distinct_inputs'] == 10
    assert summary['new_inputs'] == 0 and summary['no_pooled_success_rate_or_geomean'] and summary['no_cap_or_unknown_time_imputation']
    model_rows = csv_rows(out / 'model_index.csv')
    index = {(int(q['group']), q['method'], q['model_SHA']):q for q in model_rows}
    assert len(index) == len(model_rows) == len(actual_models)
    for model in actual_models:
        row = index[model['group'], model['method'], model['model_SHA']]
        for key in ('rows', 'columns', 'pair_cover', 'pair_conditional', 'triple_cover', 'triple_conditional',
                    'ordered_supply_compatible_rows', 'ordered_supply_compatible_pickup_terms'):
            assert int(row[key]) == model[key], ('support/model family metadata drift', model['group'], model['method'], key)
        for key in ('ordered_supply_pickup_terms_per_row_min', 'ordered_supply_pickup_terms_per_row_max'):
            if model[key] is None:
                assert row[key] == '', ('supply-compatible diagnostic null invented', model['group'], key)
            else:
                assert int(row[key]) == model[key]
        assert row['actual_candidate_counter'] == '', ('unretained candidate counter invented', model['group'])
        if model['method'] == 'S2':
            panel = SPEC[GROUPS[model['group'] - 1][0]]
            assert int(row['support_pair_candidate_upper']) == panel[3] * math.comb(panel[2], 2)
            assert row['support_triple_enumeration_enabled'] == 'False'
        assert row['corrected_same_vehicle_classifier'] == 'True'
    impacts = read(out / 'numeric_policy_impacts.json')
    expected_negative = [{k:a[k] for k in ('group', 'id', 'seed', 'repeat', 'method', 'U', 'L', 'certificate',
                                          'T_cert', 'raw_claimed_U', 'raw_claimed_L', 'raw_claimed_certificate')}
                         | {'signed_gap':a['gap']} for a in arms if a['gap'] < 0]
    equal_value(expected_negative, impacts['negative_signed_gaps'], 'retained negative raw signed gaps')
    assert impacts['raw_gaps_retained'] and impacts['L_clipped'] is False and impacts['new_tolerance'] is False
    cost_json = {(int(q['group']), q['method']):q for q in author['costs']}
    cost_csv = {(int(q['group']), q['method']):q for q in csv_rows(out / 'mechanism_costs.csv')}
    assert len(cost_json) == len(cost_csv) == len(actual_costs) == 52
    for expected in actual_costs:
        key = expected['group'], expected['method']
        for field, value in expected.items():
            equal_value(value, cost_json[key][field], ('diagnostic/cost null', key, field))
            if value is None:
                assert cost_csv[key][field] == '', ('diagnostic CSV null invented', key, field)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                same(float(cost_csv[key][field]), value)
            elif isinstance(value, (dict, list)):
                equal_value(value, json.loads(cost_csv[key][field]), ('diagnostic/cost CSV object', key, field))
            else:
                assert cost_csv[key][field] == str(value)
    return dict(all_52_arms_and_26_pairs_match=True, all_nulls_match=True,
                all_three_strata_and_tiny_repeats_match=True)


def final_review(out, manifest, plans, contract):
    sys.path.insert(0, str(ROOT / 'scripts'))
    core = importlib.import_module('round108_reader')
    reconstruction = importlib.import_module('read_round118')
    source_reader = importlib.import_module('read_round116')
    evidence = importlib.import_module('round130_evidence')
    handoff = importlib.import_module('round127_evidence')
    h_reader = importlib.import_module('compare_round112_startup')
    for module in (core, reconstruction, source_reader, evidence, handoff):
        assert Path(module.__file__).resolve().is_relative_to(ROOT), ('foreign reader import', module.__name__)
        if hasattr(module, 'ROOT'):
            module.ROOT = ROOT
    for name in ('round130_evidence', 'round128_evidence', 'round114_audit', 'round112_audit',
                 'round118_call_logs', 'round122_evidence'):
        module = importlib.import_module(name)
        assert Path(module.__file__).resolve().is_relative_to(ROOT)
        if hasattr(module, 'ROOT'):
            module.ROOT = ROOT
    core.start_reader.ROOT = ROOT
    arms, pairs, artifacts, model_facts, raw_layers, actual_models, actual_costs = [], [], [], {}, [], [], []
    sample_fleet = sample_certificate = sample_pair = None
    handoff_diagnostics = []
    for number, (group, plan) in enumerate(zip(manifest['groups'], plans), 1):
        cap, camp = group['role']['cap_seconds'], out / group['name']
        saved = read(camp / 'reconstructed.json')['arms']
        assert len(saved) == 2 and [a['method'] for a in saved] == group['methods']
        recs = collections.defaultdict(list)
        with no_handoff_write(handoff) as diagnostics, evidence.extension():
            items = [reconstruction.item(ROOT, launch, plan, recs) for launch in plan['launches']]
            witnesses = [dict(w, arm=item['l']['method']) for item in items if item['complete'] for w in item['ind']['witnesses']]
            findings = [source_reader.reconcile(item.get('claims', []), witnesses) for item in items]
            rebuilt = [reconstruction.finalize(ROOT, item, finding, recs) for item, finding in zip(items, findings)]
        handoff_diagnostics.extend(diagnostics)
        local = {}
        for launch, original, arm, item in zip(plan['launches'], saved, rebuilt, items):
            assert item['complete'], ('required arm evidence incomplete', number, launch['method'])
            dest, panel, method = portable(launch['destination']), launch['panel'], launch['method']
            producer, total = read(dest / 'producer_receipt.json'), read(dest / 'arm_total_receipt.json')
            seal, closeout = read(dest / 'producer_seal.json'), read(dest / 'verification_closeout.json')
            result, completion = read(dest / 'result.json'), read(dest / 'completion.json')
            origin, ind = read(dest / 'child_process_origin.json'), read(dest / 'independent_evidence.json')
            assert origin['command'] == launch['command'] and origin['PE_SHA'] == PE and origin['seed'] == group['seed']
            assert origin['creation_from_live_OS_handle'] is True
            assert producer['producer_seal_SHA'] == sha(dest / 'producer_seal.json')
            assert seal['native_stopped_no_reentry'] and seal['required_outputs_closed']
            for path, digest in seal['required_SHA'].items():
                assert sha(dest / path) == digest, ('producer seal changed', number, method, path)
            assert total['producer_receipt_SHA'] == closeout['producer_receipt_SHA'] == sha(dest / 'producer_receipt.json')
            assert total['verification_closeout_SHA'] == sha(dest / 'verification_closeout.json')
            for key, name in (('audit_SHA', 'audit.json'), ('own_evidence_SHA', 'independent_evidence.json'),
                              ('claims_SHA', 'native_claims.json'), ('rejection_SHA', 'claim_rejections.json')):
                assert closeout[key] == sha(dest / name)
            assert closeout['no_new_solution_or_certificate_backfilled'] and closeout['necessary_verification_complete']
            produced = producer['t_produce_perf'] - producer['t0_perf']
            verified = total['t_verified_perf'] - producer['t_produce_perf']
            assert 0 < produced <= cap and verified >= 0
            assert completion['returncode'] == 0 and completion['stop_reason'] == 'normal_return' and completion['within_cap']
            for key, name in (('result_SHA', 'result.json'), ('observations_SHA', 'observations.json'), ('completion_SHA', 'completion.json')):
                assert ind[key] == sha(dest / name)
            physical = core.full_fleet(ROOT, panel, result)
            assert physical['complete_fleet_vehicles'] == panel['M']
            same(physical['F'], arm['U'], 1e-7)
            same(arm['gap'], arm['U'] - arm['L'], 1e-14)
            for key, value in (('T_produce', produced), ('T_verify', verified), ('T_total', produced + verified)):
                same(arm[key], value)
            expected_time = produced if eligible(arm) and arm['certificate'] else None
            assert original['T_cert'] == expected_time
            for key in ('U', 'L', 'gap', 'T_produce', 'T_verify', 'T_total'):
                same(original[key], arm[key])
            for key in ('certificate', 'formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified', 'source_reduced'):
                assert original.get(key, False) == arm.get(key, False)
            arm = dict(arm, group=number, method=method, seed=group['seed'], repeat=group['repeat'],
                       layer=layer(group), binary_layer='E3', T_cert=expected_time)
            observations = read(dest / 'observations.json')
            calls = [q['payload'] for q in observations if q['payload']['kind'] == 'call']
            assert len({q['call'] for q in calls}) == len(calls)
            arm_model_hashes = set()
            for call in calls:
                assert sha(portable(call['model_path'])) == call['model_sha256']
                assert call['settings'] == dict(read_return_code=0, Threads=1, Seed=group['seed'], Presolve=-1,
                    MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
                if call['model_sha256'] not in model_facts:
                    model = core.lp_model(portable(call['model_path']))
                    families = collections.Counter(support_family(row) for row in model['rows'])
                    supply_terms = [sum(name.startswith('p_') for name, _ in terms)
                                    for terms, sense, rhs in model['rows']
                                    if support_family((terms, sense, rhs)) == 'ordered_supply']
                    if method == 'S2':
                        assert families['cover_3'] == families['conditional_3'] == 0
                    fact = dict(model_SHA=call['model_sha256'], rows=len(model['rows']), columns=len(model['order']),
                        pair_cover=families['cover_2'], pair_conditional=families['conditional_2'],
                        ordered_supply_compatible_rows=families['ordered_supply'],
                        ordered_supply_compatible_pickup_terms=sum(supply_terms),
                        ordered_supply_pickup_terms_per_row_min=min(supply_terms) if supply_terms else None,
                        ordered_supply_pickup_terms_per_row_max=max(supply_terms) if supply_terms else None,
                        triple_cover=families['cover_3'], triple_conditional=families['conditional_3'],
                        triple_rows=families['cover_3'] + families['conditional_3'],
                        same_vehicle_support_classifier=True)
                    model_facts[call['model_sha256']] = fact
                    if method == 'S2' and sample_pair is None and fact['pair_cover'] + fact['pair_conditional'] > 0:
                        sample_pair = dict(group=number, id=arm['id'], seed=arm['seed'], repeat=arm['repeat'], **fact)
                if call['model_sha256'] not in arm_model_hashes:
                    actual_models.append(dict(group=number, method=method, **model_facts[call['model_sha256']]))
                    arm_model_hashes.add(call['model_sha256'])
            assert read(dest / 'call_log_views.json')['bindings'] == item['view']['bindings']
            assert read(dest / 'call_log_views.json')['actual_Optimize'] == arm['native_Optimize']
            if method == 'P' and calls:
                assert len(calls) == 1 and calls[0]['full_original']
                assert sha(dest / 'compact.lp') == panel['reference']['canonical_sha256']
                params = read(dest / 'round127_parameters.json')
                assert params == dict(MIPFocus=0, Cuts=-1, NumStart_before_optimize=0,
                                     loaded_after_presets=True, authoritative_model_environment=True)
            root_call = next((c for c in calls if c['full_original'] or c['leaf'] == 'L0'), None)
            root_model = model_facts[root_call['model_sha256']] if root_call else None
            starts = [read(path) for path in (dest / 'external/native_logs').glob('*.round68.start.json')]
            own_h = h_reader.reconstruct(ROOT, panel, dest) if method == 'S2' else None
            actual_costs.append(dict(group=number, method=method,
                H_complete=own_h['complete'] if own_h else None,
                initial_own_U=own_h['physical']['F'] if own_h else None,
                actual_native_calls=arm['native_Optimize'],
                actual_submitted_Starts=sum(bool(s['submitted']) for s in starts) if starts else 0 if method == 'P' else None,
                raw_top_level_support_counts={key: result.get(key) for key in RAW_SUPPORT_FIELDS},
                raw_support_count_scope='original top-level serialized counters, preserved as recorded; not assumed to count the complete external submitted matrix',
                support_pair_cover_rows=root_model['pair_cover'] if root_model else None,
                support_pair_conditional_rows=root_model['pair_conditional'] if root_model else None,
                support_triple_rows=root_model['triple_rows'] if root_model else None,
                ordered_supply_compatible_rows=root_model['ordered_supply_compatible_rows'] if root_model else None,
                ordered_supply_compatible_pickup_terms=root_model['ordered_supply_compatible_pickup_terms'] if root_model else None,
                root_model_SHA=root_model['model_SHA'] if root_model else None,
                T_produce=arm['T_produce'], T_verify=arm['T_verify'], T_total=arm['T_total'], T_cert=arm['T_cert']))
            nonempty = any(len(q['nodes']) > 2 or q['operations'] for q in physical['routes'])
            artifact = dict(group=number, id=arm['id'], seed=arm['seed'], repeat=arm['repeat'], method=method,
                certificate=arm['certificate'], qualified=eligible(arm), final_complete_fleet=physical,
                raw_top_level_certificate=result['strict_certified_original_problem'],
                raw_signed_gap=arm['gap'], T_cert=expected_time, native_Optimize=arm['native_Optimize'],
                producer_seal_SHA=sha(dest / 'producer_seal.json'), source_return_cover_rebuilt=True)
            if sample_fleet is None and nonempty:
                sample_fleet = dict(artifact, result_SHA=sha(dest / 'result.json'), nonempty=True)
            if sample_certificate is None and eligible(arm) and arm['certificate'] and arm['U'] > 1e-7:
                endpoint = item.get('ep', {})
                chain = item['chain']
                cold_proof = None
                if method == 'P':
                    assert chain['actual'] == [1] and chain['ledger'] == []
                    with core.call_logs.activate(item['view']):
                        cold_proof = core.cold_returned_bound(ROOT, dest, item['j'], result)
                    assert cold_proof['full_original'] and cold_proof['native_status'] == 2
                    same(cold_proof['L'], arm['L'], 1e-7)
                sample_certificate = dict(group=number, id=arm['id'], seed=arm['seed'], repeat=arm['repeat'], method=method,
                    own_U=arm['U'], own_L=arm['L'], physical=physical,
                    certificate_basis=arm['certificate_basis'], source_SHA=sha(dest / 'native_claims.json'),
                    certificate_domain='complete original cold compact MILP' if method == 'P' else 'complete original interval cover',
                    complete_original_return_proof=cold_proof,
                    verified_coverage=endpoint.get('cover'), chronological_coverage=endpoint.get('chronological_cover'),
                    actual_returned_calls=chain['actual'], optimize_ledger=chain['ledger'],
                    call_logs=[{k:q[k] for k in ('call', 'path', 'SHA')} for q in chain['logs']],
                    normal_return_verified=chain['normal_return_verified'],
                    full_source_return_cover_audit_replayed=True)
            raw_layers.append(dict(group=number, method=method, seed=arm['seed'], repeat=arm['repeat'],
                raw_call_native_preconditions=[bool(c['native_preconditions']) for c in calls],
                computed_call_native_prerequisites=[bool(item['j']['calls'][c['call']]['native_preconditions']) for c in calls],
                raw_top_level_certificate=result['strict_certified_original_problem'],
                qualified_certificate=arm['certificate'], raw_flags_not_modified=True))
            arms.append(arm)
            artifacts.append(artifact)
            local[method] = arm
        pairs.append(comparison(local['S2'], local['P'], group, number))
    assert len(arms) == len({arm_key(a) for a in arms}) == 52 and len(pairs) == 26
    cross = []
    for id in SPEC:
        rows = [a for a in arms if a['id'] == id and eligible(a)]
        best = min((a['U'] for a in rows), default=None)
        violations = [dict(method=a['method'], seed=a['seed'], repeat=a['repeat'], own_L=a['L'], other_verified_U=best)
                      for a in rows if a['L'] > best + 1e-7]
        cross.append(dict(id=id, qualified_own_observations=len(rows),
            minimum_verified_physical_U_for_contradiction_only=best, violations=violations,
            own_U_values_or_bounds_or_certificates_transferred=False))
    assert not any(q['violations'] for q in cross), ('proof contradiction requires decision', cross)
    strata, tiny = independent_summaries(arms, pairs)
    author_match = check_author(out, arms, pairs, strata, tiny, actual_models, actual_costs)
    complete = all(eligible(a) for a in arms) and all(q['classification'] != 'UNEVALUABLE' for q in pairs)
    summary = read(out / 'stratified_summary.json')
    expected_tag = 'PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION' if any(a.get('source_reduced') for a in arms) else \
                   'FINAL_VERSION_BENCHMARK_COMPLETE' if complete else 'PARTIAL'
    assert summary['stage_exit'] == expected_tag and summary['execution'] == ('COMPLETE' if complete else 'PARTIAL')
    contract = dict(contract, actual_mode_and_native_parameters_after_run_pending=False)
    return dict(status='PASS', independent_executor='Round131 separate reviewer agent', **contract,
        formal_execution_complete=complete, scientific_label=expected_tag,
        comparisons_independently_recomputed=pairs, three_layer_summaries=strata, tiny_per_seed_repeats=tiny,
        author_output_comparison=author_match, all_final_complete_fleets_physically_replayed=True,
        arm_evidence=artifacts, raw_and_computed_Seed_layers=raw_layers,
        representative_nonempty_fleet=sample_fleet or dict(status='UNAVAILABLE_IN_FIXED_PANEL'),
        representative_complete_nonzero_certificate=sample_certificate or dict(status='UNAVAILABLE_IN_FIXED_PANEL'),
        representative_actual_pair_only_model=sample_pair or dict(status='UNAVAILABLE_IN_FIXED_PANEL'),
        actual_model_counts_by_arm=actual_models,
        cross_arm_same_input_bound_consistency=cross, empty_route_handoff_read_only_diagnostics=handoff_diagnostics,
        all_nulls_checked_without_cap_imputation=True, no_cross_layer_weighted_win_rate=True,
        binary_bytes_not_required_or_loaded=True, no_original_root_fallback=True,
        finite_evidence_review_not_external_replication_or_full_rational_proof=True,
        execution_binding_SHA=sha(out / 'execution_binding.json'), checker_SHA=sha(Path(__file__)))


def check(root, preflight=False):
    global ROOT
    ROOT = Path(root).resolve()
    out = ROOT / 'results/unified_exact_round131'
    if preflight:
        needed = [n for n in ('experiment_manifest.json', 'input_manifest.json', 'argv_freeze.json',
                  'execution_binding.json', 'E3_binding.json') if not (out / n).is_file()]
        if needed:
            return dict(status='NOT_READY', missing=needed, evidence_reader_modules_imported=False,
                        models_or_H_or_native_logs_read=False, Optimize=0, native_starts=0, compilation=0), 2
        _, _, contract = manifest_contract(out)
        return dict(status='ACCEPT', review_stage='preformal_frozen_contract', **contract,
                    evidence_reader_modules_imported=False, models_or_H_or_native_logs_read=False), 0
    missing = closeout_gate(out)
    if missing:
        return dict(status='NOT_READY', reason='all 52 closeouts and author outputs must close first',
                    missing=missing, evidence_reader_modules_imported=False,
                    models_or_H_or_native_logs_read=False, Optimize=0, native_starts=0, compilation=0), 2
    manifest, plans, contract = manifest_contract(out)
    return final_review(out, manifest, plans, contract), 0


def write_receipt(path, result):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        number = 1
        while path.with_name(path.stem + '.prior%02d' % number + path.suffix).exists():
            number += 1
        prior = path.with_name(path.stem + '.prior%02d' % number + path.suffix)
        prior.write_bytes(path.read_bytes())
        result['previous_receipt_retained'] = str(prior)
    result['UTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    tick = time.perf_counter()
    try:
        result, code = check(args.root, preflight=args.preflight)
    except Exception as error:
        result, code = dict(status='FAILED_REVIEW_PRESERVE_EVIDENCE', error=repr(error),
            traceback=traceback.format_exc(), Optimize=0, native_starts=0, compilation=0,
            no_performance_retry_authorized=True), 1
    result['seconds'] = time.perf_counter() - tick
    write_receipt(args.receipt, result)
    print(json.dumps({k: result[k] for k in ('status', 'Optimize')}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
