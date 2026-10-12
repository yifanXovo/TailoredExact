"""Recover only the existing four in-scope roles from a safe restored root.

No network, solver, exporter, new input files or V100 reconstruction. Historical
signature exceptions are explicit and do not requalify a modified helper.
"""
import argparse
import collections
import json
import math
from pathlib import Path
import statistics
import time
import round108_reader as core
import round116_data as data
import read_round116_reporting as reader
from compare_round112_startup import compare as compare_H
from publication_security import sha

R116 = 'results/unified_exact_round116'
R117 = 'results/unified_exact_round117'
IDS = ['E20-C1', 'E20-R2', 'E50-C1', 'E50-R2']

def source_check(root):
    out = root / R116
    manifest = core.read(out / 'input_manifest.json')
    snapshot = core.read(out / 'source/snapshot.json')
    station_bytes = (root / snapshot['station_response_path']).read_bytes()
    assert sha(station_bytes) == manifest['raw_station_response_SHA'] == snapshot['station_response_SHA']
    assert core.sha(out / 'source/source_station_table.csv') == manifest['source_table_SHA']
    raw = json.loads(station_bytes)['data']['stations']
    rows = core.rows(out / 'source/source_station_table.csv')
    decisions = core.read(out / 'source/row_decisions.json')
    assert len(raw) == len(rows) == len(decisions) == 865
    for n, d in enumerate(decisions):
        assert d['original_row_index'] == n and d['original_row'] == raw[n]
        assert d['qualified_physical_row'] and not d['exclusion_reasons']
    ids = [r['station_id'] for r in rows]
    assert ids == sorted(ids, key=lambda s: s.encode()) and len(set(ids)) == len(ids)
    area = core.read(out / 'projection_contract.json')['area_of_use']
    stations = []
    for n, r in enumerate(rows):
        assert int(r['source_row_index']) == n
        indices = json.loads(r['original_row_indices'])
        c, lat, lon = int(r['capacity']), float(r['latitude']), float(r['longitude'])
        assert 0 < c < 100 and area['west'] <= lon <= area['east'] and area['south'] <= lat <= area['north']
        assert abs(float(r['inverse_longitude']) - lon) < 1e-10 and abs(float(r['inverse_latitude']) - lat) < 1e-10
        x, y = float(r['utm18n_easting_unrounded_m']), float(r['utm18n_northing_unrounded_m'])
        assert math.isfinite(x) and math.isfinite(y)
        assert r['utm18n_easting_m'] == f'{round(x,3):.3f}' and r['utm18n_northing_m'] == f'{round(y,3):.3f}'
        for i in indices:
            q = raw[i]
            assert q['station_id'] == r['station_id'] and q['capacity'] == c and q['lat'] == lat and q['lon'] == lon
            assert q.get('is_virtual_station') is not True
        stations.append(data.SourceStation(n, r['station_id'], c, round(x,3), round(y,3), lat, lon, tuple(indices)))
    data.configure(snapshot['station_response_SHA'])
    checked = []
    for p in manifest['roles']:
        if p['id'] not in IDS:
            continue
        assert p['V'] <= 50
        selection = data.select(stations, p['V'], p['geometry'], p['replicate'])
        selection['schema'] = 'cabi-geographic-selection-v1'
        landscape = data.landscape(selection, p['inventory'], stations)
        assert selection == core.read(root / p['selection_path'])
        assert landscape == core.read(root / p['landscape_path'])
        lines = data.old.instance_text(landscape, p['M'], p['Q_vector'][0]).splitlines()
        lines[0] = f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
        expected = ('\n'.join(lines).rstrip() + '\n').encode()
        assert (root / p['input_path']).read_bytes() == expected
        assert sha(expected) == p['input_sha256']
        parsed = data.old.parse_instance_mirror(root / p['input_path'])
        assert json.loads(json.dumps(parsed)) == core.read(root / 'reference/round116_external' / (p['id'] + '_parsed.json'))
        assert landscape['depot']['coordinate_utm18n_meters'] == [round(statistics.fmean(q[0] for q in parsed['points'][1:]),3), round(statistics.fmean(q[1] for q in parsed['points'][1:]),3)]
        checked.append({'id': p['id'], 'input_sha256': sha(expected), 'bytes': len(expected),
                        'station_id_capacity_coordinates_salts_inventory_target_weight_depot_equal': True})
    assert len(checked) == 4
    return {'source_rows': 865, 'roles': checked, 'station_raw_sha256': sha(station_bytes),
            'generation_salt': manifest['family'], 'raw_station_bytes_unchanged': True,
            'forward_PROJ_rerun': False, 'V100_generation_or_reconstruction': False,
            'new_input_files_written': 0}

def validate(root, destination):
    tick = time.perf_counter()
    root, destination = Path(root).resolve(), Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    out = root / R116
    core.start_reader.ROOT = root
    candidate = core.read(out / 'candidate_identity.json')
    production = core.read(out / 'production_identity.json')
    mapping = {e['original_path']: e for e in core.read(root / R117 / 'redaction_manifest.json')['entries']}
    exceptions = []
    for p, expected in production['source_bindings'].items():
        assert core.sha(root / p) == expected
    assert len(production['source_bindings']) == 206
    for p, expected in candidate['helpers'].items():
        current = core.sha(root / p)
        if current != expected:
            e = mapping[p]
            assert e['original_sha256'] == expected and e['sanitized_sha256'] == current
            assert core.sha(root / e['preserved_historical_code_path']) == expected
            exceptions.append({'path': p, 'original_sha256': expected, 'safe_sha256': current,
                               'historical_qualification_not_reassigned_to_new_bytes': True})
    gate = core.read(out / 'review/performance_admission.json')
    assert gate['decision'] == 'ACCEPT' and gate['candidate_identity_SHA'] == core.sha(out / 'candidate_identity.json')
    fixed = core.read(out / 'fixed_manifest.json')
    original = core.read(out / 'reports_final/current_core.json')
    recs = collections.defaultdict(list)
    arms, same = [], []
    for group in fixed['groups']:
        if group['id'] not in IDS:
            continue
        identity = core.read(out / group['campaign'] / 'identity.json')
        assert core.sha(out / group['campaign'] / 'identity.json') == group['identity_SHA']
        assert identity['helpers'] == candidate['helpers'] and identity['source_hashes'] == production['source_bindings']
        assert identity['runner_sha256'] == core.sha(root / 'scripts/round116_campaign.py')
        assert identity['prereg_sha256'] == core.sha(out / 'protocol.json')
        assert identity['candidate_binary_sha256'] == production['production_PE_SHA'] and identity['dll_sha256'] == production['DLL_SHA']
        assert all(l['panel']['V'] <= 50 for l in identity['launches'])
        items = [reader.reconstruct_arm(root, l, identity, recs) for l in identity['launches']]
        assert all(item['complete'] for item in items)
        claims = [q for item in items for q in item['claims']]
        witnesses = [q for item in items for q in item['ind']['witnesses']]
        final = reader.reconcile(claims, witnesses)
        assert final == reader.reconcile(list(reversed(claims)), list(reversed(witnesses)))
        arms.extend(reader.finalize_arm(root, item, final, recs) for item in items)
        by = {item['l']['arm']: item for item in items}
        H = compare_H(root, identity['launches'][0]['panel'], {m: by[m]['d'] for m in ['P-S', 'ENS-C', 'M-B']})
        for h in H['comparisons']:
            exposed = by[h['candidate']]['j']['started'] > 0 and by['P-S']['j']['started'] > 0
            h.update(formal=True, backend_exposed=exposed, attribution_eligible=h['qualified'] and exposed,
                     attribution_reason='MATCHED_H_BACKENDS_EXPOSED' if h['qualified'] and exposed else 'H_NOT_COMPLETED' if not h['full_H_complete'] else 'BACKEND_NOT_EXPOSED' if h['qualified'] else 'START_MISMATCH')
            same.append(h)
    expected_arms = [a for a in original['arms'] if a['id'] in IDS]
    assert len(arms) == len(expected_arms) == 16 and arms == expected_arms
    assert same == [h for h in original['same_H'] if h['id'] in IDS and h['formal']]
    pairs = []
    lookup = {(a['id'], a['arm']): a for a in arms}
    for role_id in IDS:
        for X, C in reader.PAIRS:
            a, c = lookup[role_id, X], lookup[role_id, C]
            h = next((h for h in same if h['id'] == role_id and h['candidate'] == X), None) if C == 'P-S' and X in ['ENS-C', 'M-B'] else None
            pairs.append(dict(reader.pair(a,c), id=role_id, dU=a['U']-c['U'], dL=a['L']-c['L'], dGap=a['gap']-c['gap'], main_clock='T_produce',
                              candidate_proof_evidence=a['proof_evidence'], control_proof_evidence=c['proof_evidence'],
                              backend_attribution_eligible=h['attribution_eligible'] if h else None,
                              backend_attribution_reason=h['attribution_reason'] if h else None))
    assert len(pairs) == 24 and pairs == [p for p in original['pairs'] if p['id'] in IDS]
    source = source_check(root)
    summary = core.read(out / 'reports_final/summary.json')
    assert summary['execution_stage'] == 'BLOCKED' and summary['actual_formal_children'] == 18
    assert summary['qualified_formal_arms'] == 17 and summary['evaluable_pairs'] == 24 and summary['pair_positions'] == 36
    core.write(destination / 'arms.json', arms)
    core.write(destination / 'pairs.json', pairs)
    core.write(destination / 'same_H.json', same)
    core.write(destination / 'source_consistency.json', source)
    report = {'layer': 'AUTHOR_SCOPE_V_LE_60 / R116_V20_V50_DESCRIPTIVE_SUBSET',
              'restored_root': str(root), 'raw_reconstructed_arms': 16, 'reconstructed_pairs': 24,
              'all_original_scientific_fields_equal': True, 'source_check': source,
              'historical_helper_signature_exceptions': exceptions, 'production_source_files_equal': 206,
              'original_R116_state': 'BLOCKED', 'new_independent_confirmation': False,
              'original_root_fallback': False, 'V100_recovery': False, 'network_requests': 0,
              'native_starts': 0, 'Optimize': 0, 'implementer_authored': True,
              'engineering_seconds': time.perf_counter()-tick}
    core.write(destination / 'validation.json', report)
    print(json.dumps({k: report[k] for k in ['raw_reconstructed_arms','reconstructed_pairs','all_original_scientific_fields_equal','engineering_seconds']}), flush=True)
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    validate(args.root, args.out)
