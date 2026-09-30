"""Idle-only checks of the draft independent hash reader against saved v1 data.

No solver, no native model load and no synthesized qualification success.
The full v2 event auditor intentionally cannot consume the v1 session schema.
"""
import copy
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'scripts/round97_build.py').is_file())
sys.path.insert(0, str(ROOT / 'scripts'))
from round96_prepare import read, write, sha, citi
import round96_external as ext


def main():
    ext.ensure_idle()
    assert Path(__file__).resolve() == ROOT / 'scripts/round97_v2_reader_fixture.py', 'Promote the reviewed fixture before recording qualification evidence'
    started = time.perf_counter()
    reader_path = ROOT / 'scripts/round97_campaign_v2.py'
    spec = importlib.util.spec_from_file_location('round97_v2_fixture_reader', reader_path)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    out = ROOT / 'results/unified_exact_round97'
    destination = out / 'revision02_reader_fixture.json'
    assert not destination.exists()
    checked, starts_checked, mutations_checked = [], 0, 0
    for label, number in [('qualification02', 3), ('development01', 1), ('development01', 2)]:
        identity = read(out / label / 'identity.json')
        launch = identity['launches'][number-1]
        capacities = citi.parse_instance_mirror(ROOT / launch['panel']['input_path'])['Q']
        folder = Path(launch['destination']) / 'external'
        events = [json.loads(line) for line in (folder / 'round97/events.jsonl').read_text().splitlines()]
        solutions = [e for e in events if e['kind'] == 'solution']
        for witness_path in sorted((folder / 'round97').glob('input_*.json')):
            witness = read(witness_path)
            expected = witness['sha256']
            assert reader.normalized_hash(witness['routes'], capacities) == expected
            dict_form = copy.deepcopy(witness['routes'])
            for route in dict_form:
                route['operations'] = [dict(zip(('station', 'pickup', 'drop'), op))
                                       if isinstance(op, list) else op for op in route['operations']]
                route['operations'].reverse()
            dict_form.reverse()
            assert reader.normalized_hash(dict_form, capacities) == expected
            checked.append(dict(path=witness_path.relative_to(ROOT).as_posix(), sha256=sha(witness_path), state_hash=expected))
        for setup_path in (folder / 'native_logs').glob('*.round97.setup.json'):
            setup = read(setup_path)
            start_path = Path(str(setup_path).replace('.round97.setup.json', '.round68.start.json'))
            start = read(start_path) if start_path.exists() else None
            current_hash = None
            if start is not None and start['submitted']:
                assert start['model_sha256'] == setup['model_sha256']
                witness = read(folder / (start['source'] + '_witness.json'))
                current_hash = reader.normalized_hash(witness['routes'], capacities)
            for event in solutions:
                if event['call'] == setup['call']:
                    assert event['model_sha256'] == setup['model_sha256']
                    expected = None if current_hash is None else event['input_hash'] == current_hash
                    assert event['matches_supplied_start_physical_state'] is expected
                    starts_checked += 1
        initial = read(folder / 'initial_witness.json')['routes']
        initial_hash = reader.normalized_hash(initial, capacities)
        assert any(e['input_hash'] == initial_hash for e in solutions)
        changed = copy.deepcopy(initial)
        used = [r for r in changed if r['operations']]
        assert len(used) >= 2 and used[0]['vehicle'] != used[1]['vehicle']
        first, second = used[:2]
        assert capacities[first['vehicle']] == capacities[second['vehicle']]
        first['vehicle'], second['vehicle'] = second['vehicle'], first['vehicle']
        assert reader.normalized_hash(changed, capacities) == initial_hash
        heterogeneous = list(capacities)
        heterogeneous[first['vehicle']] += 1
        assert reader.normalized_hash(changed, heterogeneous) != reader.normalized_hash(initial, heterogeneous)
        altered = copy.deepcopy(initial)
        route = next(r for r in altered if len(r['nodes']) >= 4)
        route['nodes'][1], route['nodes'][2] = route['nodes'][2], route['nodes'][1]
        assert reader.normalized_hash(altered, capacities) != initial_hash
        mutations_checked += 3
    assert checked and starts_checked and mutations_checked
    write(destination, dict(passed=True, optimizer_calls=0, wall_seconds=time.perf_counter()-started,
        fixture_sha256=sha(__file__), reader_sha256=sha(reader_path), witnesses=checked,
        event_start_matches_checked=starts_checked, hash_mutations_checked=mutations_checked,
        scope='Saved real v1 canonical hashes and Start associations, two witness formats, operation/route presentation order, equal/unequal capacity labels and changed route order. Does not qualify v2 production or full v2 event schema.'))
    print(json.dumps(dict(passed=True, witnesses=len(checked), start_matches=starts_checked,
                          mutations=mutations_checked, optimizer_calls=0)))


if __name__ == '__main__':
    main()
