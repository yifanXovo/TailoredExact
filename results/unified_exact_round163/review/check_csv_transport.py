"""Independent CSV-only Round163 transport check; no fleet or solver work.

Canonical reviewer /root/round163_execution_review. Execute only after the
six B/P rows have actually been appended; root meters all calculations.
"""
import argparse
import csv
import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import time

AGENT = '/root/round163_execution_review'


def require(test, message):
    if not test:
        raise AssertionError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def rows(data, encoding):
    return list(csv.reader(io.StringIO(data.decode(encoding), newline='')))


def number(text, value, message):
    require(text != '' and math.isfinite(float(text)) and abs(float(text)-value) <= 1e-12,
            f'{message}: {text!r} versus {value!r}')


def run(root, out):
    prior = read(out/'review/execution_readback.json')
    require(prior['PASS'] and len(prior['arms']) == 18, 'completed independent fleet review required')
    schema, discovery = read(out/'main_table_schema_readback.json'), read(out/'main_table_discovery.json')
    update, authoring = read(out/'main_table_update.json'), read(out/'table_authoring.json')
    source_commit = read(out/'table_source_binding.json')['fixed_results_commit']
    require(re.fullmatch(r'[0-9a-f]{40}', source_commit) is not None, 'immutable full result-source commit')
    require(authoring['source_commit'] == source_commit, 'Artifact authoring fixed-source identity')
    manifest = read(out/'input_manifest.json')['roles']
    reports = read(out/'reports/complete_arms.json')
    by_id = {}
    for arm in reports:
        by_id.setdefault(arm['id'], {})[arm['method']] = arm
    require(len(manifest) == 6 and len(by_id) == 6, 'six complete paired configurations')
    expected_header = schema['canonical_increment_header']
    increment_path = out/'reports/GI_TBC_vs_P_GRB_Round163_Increment.csv'
    increment = rows(increment_path.read_bytes(), 'utf-8-sig')
    require(len(increment) == 7 and increment[0] == expected_header and
            all(len(row) == 28 for row in increment), 'named canonical 28-column six-pair increment')
    require(len(schema['tables']) == len(update['tables']) == 2, 'two actual master paths')
    facts, actual_tables = [], []
    scenarios = {'shortage': ('库存短缺', 'S'), 'balanced': ('库存平衡', 'B'), 'surplus': ('库存盈余', 'U')}
    for index, meta in enumerate(schema['tables']):
        path = Path(meta['path'])
        actual = path.read_bytes()
        data = rows(actual, meta['encoding'])
        original = Path(discovery['tables'][index]['local_backup']).read_bytes()
        old = rows(original, meta['encoding'])
        receipt = update['tables'][index]
        prefix = Path(receipt['local_before_backup']).read_bytes()
        require(sha_bytes(original) == meta['SHA256'] == discovery['tables'][index]['SHA256'], 'original master snapshot bytes')
        require(prefix == original, 'original 85-record prefix unchanged before append')
        require(actual == prefix + actual[len(prefix):] and actual[:len(prefix)] == prefix, 'exact original byte prefix retained')
        require(len(old) == 86 and len(data) == 92 and all(len(v) == 28 for v in data), '85 historical plus six new records, 28 raw fields')
        require(data[:len(old)] == old and data[0] == meta['header'] and data[0][-2:] == ['', ''], 'legacy rows and duplicate unnamed source headers retained')
        require(data[0][:26] == expected_header[:26], 'legacy and canonical field positions')
        added = data[-6:]
        require(added == increment[1:], 'actual master suffix equals named canonical increment')
        require([row[0] for row in added] == [p['id'] for p in manifest], 'only the six prospective IDs appended')
        require(all(row[0] not in {r[0] for r in old[1:]} for row in added), 'no historical ID relabelled')
        keys = [(r[0], r[7], r[8], r[10], r[11], r[12], r[13]) for r in data[1:]]
        require(len(set(keys[-6:])) == 6 and not set(keys[:-6]) & set(keys[-6:]), 'new unique B/P experiment keys')
        for p, row in zip(manifest, added):
            b, plain = by_id[p['id']]['B'], by_id[p['id']]['P']
            require(b['performance_eligible'] and plain['performance_eligible'], 'qualified B/P source pair')
            require(row[1:3] == [str(p['V']), str(p['M'])], 'station/vehicle counts')
            require(tuple(row[3:5]) == scenarios[p['inventory']] and row[5] == p['source'], 'actual inventory/source labels')
            require(row[6] == ('紧凑分布' if p['geometry'] == 'compact' else '区域分布'), 'actual geography')
            number(row[7], p['T_seconds'], 'original physical T')
            number(row[8], p['lambda'], 'actual serialized lambda')
            number(row[9], p['lambda']/.15, 'lambda multiplier versus .15')
            require(row[10:13] == ['0', '1', '163'], 'Seed/repeat/data round')
            number(row[13], p['cap_seconds'], 'production cap kept distinct from physical T')
            for offset, arm in [(14, b), (19, plain)]:
                require(row[offset] == ('已收敛' if arm['certificate'] else '未收敛'), 'qualified status label')
                if arm['certificate']:
                    number(row[offset+1], arm['T_cert'], 'paid certified closure time')
                    require(row[offset+2] == '', 'CERT has no OPEN gap entry')
                else:
                    require(row[offset+1] == '', 'OPEN has no convergence time or substituted cap')
                    if arm['relative_gap'] is None:
                        require(row[offset+2] == '', 'undefined relative gap left blank')
                    else:
                        number(row[offset+2], 100*arm['relative_gap'], 'original OPEN gap percentage')
                number(row[offset+3], arm['L'], 'qualified full-problem lower')
                number(row[offset+4], arm['U'], 'qualified original fleet upper')
            require(row[24] == '', 'unconfirmed historical comparison category left blank')
            require(f'B {b["state"]}' in row[25] and f'P {plain["state"]}' in row[25] and 'U=' in row[25] and 'L=' in row[25], 'explicit certificate/U/L comparison facts')
            base_url = f'https://github.com/yifanXovo/TailoredExact/blob/{source_commit}/'
            require(row[26] == base_url+'results/unified_exact_round163/reports/complete_arms.json', 'positional experiment source column27')
            require(row[27] == base_url+'results/unified_exact_round163/input_manifest.json', 'distinct metadata source column28')
        require(str(path) == receipt['path'] and sha_bytes(prefix) == receipt['before_SHA256'] and
                sha_bytes(actual) == receipt['after_SHA256'], 'actual write receipt identities')
        require(receipt['before_rows'] == 85 and receipt['after_rows'] == 91 and receipt['added_rows'] == 6 and
                receipt['original_prefix_bytes_identical'] and receipt['header_cells_unchanged'], 'actual write receipt counts/prefix contract')
        facts.append(dict(path=str(path), encoding=meta['encoding'], before_rows=85, after_rows=91,
                          raw_columns=28, original_prefix_bytes=len(prefix), original_prefix_SHA256=sha_bytes(prefix),
                          after_SHA256=sha_bytes(actual), source_columns_one_based=[27, 28],
                          added_ids=[row[0] for row in added], only_verified_B_P_values=True,
                          OPEN_time_blank=True, Eplus_not_substituted=True))
        actual_tables.append(actual)
    require(actual_tables[0] == actual_tables[1], 'both actual master replicas agree byte-for-byte')
    repository_master = Path(update['repository_master_copy'])
    require(repository_master.read_bytes() == actual_tables[0] and
            sha_bytes(actual_tables[0]) == update['master_copy_SHA256'], 'repository master copy matches actual primary')
    require(update['only_verified_B_P_pairs'] and update['Eplus_not_relabelled_as_B'] and
            update['new_classification_values_blank'], 'reported append method/classification contract')
    return dict(PASS=True, canonical_agent_identity=AGENT, UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                scope='CSV-only transport/readback after the completed independent raw fleet audit',
                fleet_recomputed_again=False, no_solver_or_native_calls=True, no_project_imports=True,
                source_commit=source_commit, actual_master_files=facts,
                canonical_increment=str(increment_path), canonical_increment_SHA256=sha_bytes(increment_path.read_bytes()),
                historical_records_and_labels_unchanged=True, scientific_endpoints_unchanged=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    out = root/'results/unified_exact_round163'
    tick = time.perf_counter()
    try:
        result = run(root, out)
    except Exception as error:
        result = dict(PASS=False, canonical_agent_identity=AGENT, error_type=type(error).__name__, error=str(error),
                      fleet_recomputed_again=False, no_solver_or_native_calls=True)
    result['checker_seconds'] = time.perf_counter()-tick
    result['checker_SHA256'] = sha_bytes(Path(__file__).read_bytes())
    output = out/'review/csv_readback.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(dict(PASS=result['PASS'], output=str(output), error=result.get('error'))))
    return 0 if result['PASS'] else 1


if __name__ == '__main__':
    sys.exit(main())
