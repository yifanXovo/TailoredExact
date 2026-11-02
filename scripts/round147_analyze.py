"""Idle-only four-cell aggregation; old cells retain original round and cost."""
import csv
import re
from round147_common import *


def rows(path):
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def table(path, values):
    if not values:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(k for r in values for k in r)))
        writer.writeheader()
        writer.writerows(values)


def new_row(matrix, group):
    launch = group['launch']
    destination = Path(launch['destination'])
    endpoint = read(destination / 'round135_endpoint.json')
    control = read(destination / 'round147_control_audit.json')
    audit = read(destination / 'audit.json')
    assert endpoint['native_proof_qualified'] and endpoint['performance_eligible'] and control['PASS']
    assert not audit['source_rejections'] and endpoint['declared_calls'] == endpoint['returned_calls']
    assert endpoint['T_cert'] is None if not endpoint['certificate'] else endpoint['T_cert'] == endpoint['T_produce']
    ledger = rows(destination / 'external/paper_optimize_ledger.csv')
    assert all(r['optimize_return_code'] == '0' for r in ledger)
    terminal = next((r for r in reversed(ledger) if 'terminal' in r['native_log']), None)
    observations = [r['payload'] for r in read(destination / 'observations.json')]
    bylog = {r['native_log_path']: r['call'] for r in observations if r['kind'] == 'call'}
    cid = bylog[terminal['native_log']] if terminal else None
    quality = next((r for r in observations if r['kind'] == 'native_quality' and r['call'] == cid), None)
    result = read(destination / 'result.json')
    panel = launch['panel']
    identity = read(OUT / group['group'] / 'identity.json')
    fee = read(OUT / 'fees' / f'{matrix["batch"]}_{group["position"]:03}' / 'receipt.json')
    record = dict(round=147, evidence_kind='new_round147', batch=matrix['batch'],
        position=group['position'], role=launch['id'], method=launch['R147_method'], seed=launch['seed'],
        formal_entered=True, input_SHA=panel['input_sha256'], physical_T=panel['T_seconds'],
        lambda_value=panel['lambda'], cap=launch['cap_seconds'], source_commit=identity['measured_source_commit'],
        PE_SHA=identity['candidate_binary_sha256'], DLL_SHA=identity['dll_sha256'],
        **{k: endpoint[k] for k in ['U', 'L', 'certificate', 'signed_gap', 'relative_gap', 'T_produce',
            'T_cert', 'T_verify', 'T_total', 'H_complete', 'H_semantic_SHA', 'H_fleet_SHA',
            'declared_calls', 'returned_calls']},
        physical_G=audit['physical']['G'], physical_P=audit['physical']['P'],
        weighted_physical_penalty=endpoint['U'] - audit['physical']['G'],
        external_supported_final_L=endpoint['L'],
        terminal_native_return_ObjBoundC=quality.get('ObjBoundC') if quality else None,
        terminal_native_return_ObjVal=quality.get('ObjVal') if quality else None,
        LP_calls=sum(v['solve_kind'] == 'LP' for v in ledger),
        target_calls=sum('TARGET' in v['solve_kind'] for v in ledger),
        terminal_calls=sum(v['solve_kind'] == 'MIP' for v in ledger),
        Native_total_Work=sum(float(v['work']) for v in ledger),
        Native_total_runtime=sum(float(v['solver_runtime']) for v in ledger),
        terminal_Work=float(terminal['work']) if terminal else 0.,
        terminal_nodes=float(terminal['nodes']) if terminal else 0.,
        initial_root_L=next((float(v['lower_bound']) for v in rows(destination / 'external/lp_status_ledger.csv')
            if v['leaf_id'] == 'L0'), None), actual_split_count=result['external_gini_tree_split_count'],
        performance_eligible=True, native_proof_qualified=True,
        STOCK=control['STOCK'], GD=control['GD'],
        GD_rows=max([x['GD_rows'] for x in control['models']] or [0]),
        GD_nonzeros=max([x['GD_nonzeros'] for x in control['models']] or [0]),
        stock_rows=max([x['stock_rows'] for x in control['models']] or [0]),
        coefficient_generation_seconds=(control['root_generation'] or {}).get('generation_seconds', 0.),
        new_columns=0, paid_source_solves=0, destination=str(destination),
        fee_outer_seconds=fee['outer_seconds'], new_round147_charge_seconds=fee['G1_seconds'])
    if terminal:
        text = Path(terminal['native_log']).read_text(encoding='utf-8', errors='replace')
        root = re.findall(r'Root relaxation: objective ([-+\d.eE]+), ([\d,]+) iterations, ([-+\d.eE]+) seconds', text)
        if root:
            record.update(native_root_relaxation_objective=float(root[-1][0]),
                native_root_simplex_iterations=int(root[-1][1].replace(',', '')),
                native_root_relaxation_seconds=float(root[-1][2]))
        after = re.findall(r'^\s*0\s+\d+\s+[-+\d.eE]+\s+\d+\s+\d+\s+[-+\d.eE]+\s+([-+\d.eE]+)\s+', text, re.M)
        if after:
            record['printed_root_after_cuts_bound'] = float(after[-1])
        size = re.findall(r'Optimize a model with ([\d,]+) rows, ([\d,]+) columns and ([\d,]+) nonzeros', text)
        if size:
            record.update(dict(zip(['terminal_rows', 'terminal_columns', 'terminal_nonzeros'],
                                   [int(v.replace(',', '')) for v in size[-1]])))
    return record


def full():
    configure()
    assert not budget()['unclosed'], 'Aggregate only after serial timing closes'
    old = []
    for item in read(OUT / 'reuse_index.json')['old_cells']:
        row = dict(item['source_row'])
        row.update(round=146, evidence_kind=item['evidence_kind'], fixed_science=SCIENCE146,
            STOCK=row['method'] != 'BASE', GD=row['method'] == 'STOCK_GD',
            stock_rows=4 if row['method'] != 'BASE' else 0, new_round147_charge_seconds=0,
            original_start_unix=item['original_start_unix'], original_end_unix=item['original_end_unix'])
        old.append(row)
    new, pending, counts = [], [], []
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix = read(path)
        for group in matrix['groups']:
            launch = group['launch']
            destination = Path(launch['destination'])
            ledger = rows(destination / 'external/paper_optimize_ledger.csv')
            if ledger:
                counts.append(dict(batch=matrix['batch'], position=group['position'], arm_id=launch['arm_id'],
                    Optimize=len(ledger), returned=sum(r['optimize_return_code'] == '0' for r in ledger),
                    LP=sum(r['solve_kind'] == 'LP' for r in ledger), source_solves=0))
            if not (destination / 'round147_control_audit.json').exists():
                pending.append(dict(batch=matrix['batch'], position=group['position'],
                    role=launch['id'], method=launch['R147_method'], destination=str(destination)))
                continue
            new.append(new_row(matrix, group))
    role_order = {'K-20-S': 0, 'R-X20-S-T1': 1, 'K-35-U': 2, 'R-B35-S-T2': 3, 'K-15-S': 4}
    method_order = {'BASE': 0, 'STOCK': 1, 'GD': 2, 'STOCK_GD': 3}
    all_rows = sorted(old + new, key=lambda r: (role_order.get(r['role'], 99), r['seed'], method_order[r['method']]))
    comparisons = []
    for candidate in all_rows:
        for reference_method, candidate_method, transition in [('BASE', 'GD', 'B_to_D'),
            ('STOCK', 'STOCK_GD', 'S_to_SD'), ('GD', 'STOCK_GD', 'D_to_SD'), ('STOCK', 'GD', 'S_to_D'),
            ('BASE', 'STOCK_GD', 'B_to_SD')]:
            if candidate['method'] != candidate_method:
                continue
            reference = next((r for r in all_rows if r['method'] == reference_method and
                (r['role'], r['seed']) == (candidate['role'], candidate['seed'])), None)
            if reference is None:
                continue
            for key in ['input_SHA', 'physical_T', 'lambda_value', 'cap', 'source_commit', 'PE_SHA',
                        'DLL_SHA', 'H_semantic_SHA', 'H_fleet_SHA']:
                assert reference[key] == candidate[key], (candidate['role'], key)
            comparison = dict(role=candidate['role'], seed=candidate['seed'], transition=transition,
                reference=reference_method, candidate=candidate_method, reference_round=reference['round'],
                candidate_round=candidate['round'], same_PE=True, own_H_equal=True,
                same_round=reference['round'] == candidate['round'],
                timing_relation=('same_round_serial' if reference['round'] == candidate['round']
                                 else 'same_PE_cross_round'),
                identical_system_load_not_assumed=True,
                **{'reference_' + k: reference[k] for k in ['U', 'L', 'relative_gap', 'certificate', 'T_cert', 'T_total']},
                **{'candidate_' + k: candidate[k] for k in ['U', 'L', 'relative_gap', 'certificate', 'T_cert', 'T_total']},
                **{'delta_' + k: candidate[k] - reference[k] for k in ['U', 'L', 'relative_gap', 'T_total']},
                U_improvement_percent=100 * (reference['U'] - candidate['U']) / reference['U'],
                certificate_speedup_percent=(100 * (reference['T_cert'] - candidate['T_cert']) / reference['T_cert']
                    if reference['certificate'] and candidate['certificate'] else None),
                no_open_cap_as_convergence_time=True)
            comparisons.append(comparison)
    cost = budget()
    assert cost['G1_seconds'] <= 18000
    report = dict(UTC=utc(), new_arms=new, sealed_R146_references=old, four_cell_rows=all_rows,
        comparisons=comparisons, pending=pending, all_entered_native_counts=counts,
        new_Native_Optimize=sum(r['Optimize'] for r in counts), new_Native_returned=sum(r['returned'] for r in counts),
        new_standalone_LP_Optimize=0, old_LPs_reoptimized=0, old_formal_cells_reused=7,
        all_entered_preserved=True, budget=cost, Optimize=0, Native_load=0)
    write(OUT / 'reports/full.json', report)
    for name, values in [('new_arms', new), ('four_cell_evidence', all_rows), ('comparisons', comparisons),
                         ('new_native_counts', counts)]:
        table(OUT / 'reports' / (name + '.csv'), values)
    write(OUT / 'cost_report.json', dict(UTC=utc(), charged_new_experiment_seconds=cost['G1_seconds'],
        ceiling_seconds=18000, experiment=cost, build_seconds_separate=0,
        standalone_LP_Optimize=0, includes_own_H_all_solves_failures_and_complete_postverification=True,
        nested_H_LP_MIP_Work_not_added_again=True, reused_R146_cost_not_recharged=True,
        original_R146_experiment_seconds=read(OLD / 'cost_report.json')['charged_new_experiment_seconds'],
        pure_offline_authoring_math_and_public_IO_separate=True))
    print(json.dumps(dict(new=len(new), old=len(old), pending=len(pending), budget=cost,
        B_to_D=[r for r in comparisons if r['transition'] == 'B_to_D'])))


def trajectories():
    assert not budget()['unclosed']
    records = []
    for row in read(OUT / 'reports/full.json')['four_cell_rows']:
        destination = Path(row['destination'])
        best = math.inf
        for item in read(destination / 'observations.json'):
            event = item['payload']
            if event['kind'] != 'witness' or float(event['objective']) >= best - 1e-15:
                continue
            best = float(event['objective'])
            elapsed = float(item['effective_available_seconds'])
            assert 0 <= elapsed <= row['T_produce'] + .1
            records.append(dict(role=row['role'], method=row['method'], round=row['round'],
                evidence_kind=row['evidence_kind'], seed=row['seed'], producer_seconds=elapsed,
                U=best, sequence=item['sequence'], committed_event_SHA=item['sha256'],
                source=event['source'], PE_SHA=row['PE_SHA'], raw_observation_SHA=sha(destination / 'observations.json'),
                clock='effective committed availability; not Native time or complete T_total'))
        assert abs(best - row['U']) <= 1e-8
    table(OUT / 'reports/verified_U_trajectories.csv', records)


if __name__ == '__main__':
    globals()[sys.argv[1]]()
