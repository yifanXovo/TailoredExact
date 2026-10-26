"""Independent Round108 inheritance audit. Standard library; git/rg only.

Does not import project helpers, construct a native environment, compile,
generate inputs, or launch a solver. Writes exclusively below review/.
"""
import argparse
import csv
import hashlib
import io
import json
import subprocess
import time
from pathlib import Path

R100 = 'b5d6d83bb8fc74682de6f1f6862c2e687712f4cf'
R107 = 'b5db3f038f64215766a54498d8acc82e384de733'
SEALED = {
    'S12': ('reference/round106_confirmation/S12.txt', '475763e70a2dc3b9d28a88028378e76946cbebf33aa7b7e5b033e018dd13369f'),
    'N36': ('reference/round106_confirmation/N36.txt', '52d7e43a1cc3717cfe7183b302212c7ef0a4e81f3e62642c4fe8f83c546e6fea'),
}
UNCHANGED = [
    'src/CplexBaseline.cpp', 'include/CplexBaseline.hpp',
    'include/Round98StateService.hpp', 'src/MipStartMapping.cpp',
    'src/Evaluator.cpp', 'src/ControllingLeafScheduler.cpp',
    'src/PaperK1AmSf.cpp', 'src/IntervalRowFactory.cpp',
    'include/CanonicalCompactModel.hpp',
    'include/PhysicalWitnessValidation.hpp', 'src/PhysicalWitnessValidation.cpp',
]
CHANGED = ['src/main.cpp', 'include/Instance.hpp', 'src/GurobiBaseline.cpp',
           'src/PaperExternalGiniTree.cpp', 'include/FixedIntervalMipBackend.hpp']
READS = [
    'results/unified_exact_round100/final_report.md',
    'results/unified_exact_round100/mathematical_algorithm.md',
    'results/unified_exact_round100/candidate_freeze.json',
    'results/unified_exact_round100/independent_review.md',
    'results/unified_exact_round100/complete_results_final/runs.csv',
    'results/unified_exact_round100/complete_results_final/pairs.csv',
    'results/unified_exact_round100/complete_results_final/cost_failures.csv',
    'results/unified_exact_round100/complete_results_final/summary.json',
    'scripts/round100_common.py', 'scripts/round100_campaign.py',
    'scripts/round100_run_batch.py',
    'results/unified_exact_round106/confirmation_protocol.json',
    'results/unified_exact_round106/confirmation_generation_recipe.json',
    'results/unified_exact_round106/admission_decision.json',
    'results/unified_exact_round106/final_report.md',
    'results/unified_exact_round107/final_report.md',
    'results/unified_exact_round107/review/final_implementation_performance_review.md',
    'results/unified_exact_round107/review/delivery_review.md',
    'results/unified_exact_round107/confirmation_protocol.json',
    'results/unified_exact_round107/admission_decision.json',
    'results/unified_exact_round107/confirmation_cancellation.json',
    'results/unified_exact_round107/reports05/arm_results.csv',
    'results/unified_exact_round107/reports05/controller_AM.csv',
    'results/unified_exact_round107/reports05/requests.csv',
    'results/unified_exact_round107/reports05/leaf_obligations.csv',
    'results/unified_exact_round107/reports05/fees.csv',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(argv, cwd, receipts):
    assert Path(argv[0]).name.lower() in {'git', 'git.exe', 'rg', 'rg.exe'}
    tick = time.perf_counter()
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=False)
    receipts.append({'argv': argv, 'cwd': str(cwd), 'exit_code': p.returncode,
                     'seconds': time.perf_counter() - tick,
                     'stdout_sha256': sha(p.stdout), 'stderr_sha256': sha(p.stderr),
                     'stderr': p.stderr.decode('utf-8', errors='replace')})
    assert p.returncode in {0, 1}, receipts[-1]
    return p.returncode, p.stdout


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--history-root', required=True)
    parser.add_argument('--r106-root', required=True)
    parser.add_argument('--main-root', required=True)
    parser.add_argument('--output', required=True)
    a = parser.parse_args()
    root, history, output = map(Path, (a.root, a.history_root, a.output))
    allowed = root / 'results/unified_exact_round108/review'
    assert output.resolve().is_relative_to(allowed.resolve())
    output.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    commands, reads, source = [], {}, {}
    for name in READS:
        data = (history / name).read_bytes()
        data.decode('utf-8-sig')
        reads[str(history / name)] = {'sha256': sha(data), 'bytes': len(data)}
    for name in UNCHANGED + CHANGED:
        _, old = command(['git', 'show', R100 + ':' + name], root, commands)
        _, current = command(['git', 'show', R107 + ':' + name], root, commands)
        local = (root / name).read_bytes()
        match = old == current
        assert match if name in UNCHANGED else True
        assert local.replace(b'\r\n', b'\n') == current.replace(b'\r\n', b'\n'), name
        source[name] = {'R100_commit_sha256': sha(old),
                        'R107_commit_sha256': sha(current),
                        'current_worktree_sha256': sha(local),
                        'R100_R107_exact_blob_equal': match}
    freeze = json.loads((history / 'results/unified_exact_round100/candidate_freeze.json').read_text('utf-8'))
    assert freeze['selected_arm'] == 'M-B' and freeze['mode'] == 'm-binary'
    assert freeze['actual_source_phase'] == R100
    assert freeze['representation']['AB'] and freeze['representation']['pd'] == 'C'
    assert freeze['representation']['m'] == 'B' and not freeze['representation']['ENS_Q']
    assert not freeze['representation']['extra_direction_link']
    for name in UNCHANGED:
        assert freeze['source_bindings'][name] == source[name]['current_worktree_sha256'], name
    inputs = {}
    patterns = []
    for identity, (name, digest) in SEALED.items():
        data = (history / name).read_bytes()
        assert sha(data) == digest
        assert (root / name).read_bytes() == data
        patterns += [digest, name, name.replace('/', '\\'), name.replace('/', '\\\\')]
        inputs[identity] = {'path': name, 'sha256': digest, 'bytes': len(data),
                            'first_line': data.decode('utf-8').splitlines()[0]}
    scans = []
    for raw_root in [history, Path(a.r106_root), Path(a.main_root)]:
        argv = ['rg', '-l', '--follow', '--hidden', '--no-ignore', '-i', '-F']
        for pattern in patterns:
            argv += ['-e', pattern]
        for glob in ['*.json', '*.jsonl', '*.csv', '*.txt', '*.log', '*.md', '*.py']:
            argv += ['-g', glob]
        argv += ['results', 'scripts', 'reference']
        rc, raw = command(argv, raw_root, commands)
        matching = []
        for relative in raw.decode('utf-8').splitlines():
            p = raw_root / relative
            data = p.read_bytes()
            content = data.decode('utf-8-sig')
            relevant = [line for line in content.splitlines()
                        if any(pattern.lower() in line.lower() for pattern in patterns)]
            matching.append({'relative_path': relative.replace('\\', '/'),
                             'sha256': sha(data), 'bytes': len(data),
                             'matching_lines': relevant})
            reads[str(p)] = {'sha256': sha(data), 'bytes': len(data)}
        scans.append({'root': str(raw_root), 'exit_code': rc, 'matches': matching})
    r106 = json.loads((history / 'results/unified_exact_round106/admission_decision.json').read_text('utf-8'))
    assert r106['confirmation']['formal_arms_started'] == 0
    r107 = json.loads((history / 'results/unified_exact_round107/confirmation_cancellation.json').read_text('utf-8'))
    assert r107['Optimize_calls'] == 0 and r107['IIS_calls'] == 0
    for group in r107['groups']:
        assert group['actual_native_processes'] == group['actual_Optimize_calls'] == 0
        assert group['status'] == 'NOT_STARTED_CANCELLED'
    aliases = []
    for round_id, directory in [('88', 'runner_a1_g3'), ('89', 'runner_native_b1_g3'),
                               ('90', 'runner_lp_g_g3'), ('92', 'runner_handling_g3')]:
        p = history / f'results/unified_exact_round{round_id}/{directory}/identity.json'
        if not p.is_file():
            continue
        data = p.read_bytes()
        reads[str(p)] = {'sha256': sha(data), 'bytes': len(data)}
        identity = json.loads(data)
        panels = [v['panel'] for v in identity.get('launches', []) if v.get('id') == 'S12']
        for panel in panels:
            assert panel['input_sha256'] != SEALED['S12'][1]
        aliases.append({'round': round_id, 'path': str(p), 'S12_launch_count': len(panels),
                        'input_identities': sorted({(p['input_path'], p['input_sha256']) for p in panels})})
    _, log = command(['git', 'log', '--all', '--format=%H %s', '--'] +
                     [v[0] for v in SEALED.values()], root, commands)
    write(output / 'audit.json', {
        'reviewer': '/root/independent_admission',
        'layer': 'INDEPENDENT_ZERO_SOLVER_INHERITANCE_AUDIT',
        'R100_frozen_production_commit': R100, 'R107_delivery_commit': R107,
        'source_comparisons': source, 'complete_read_files': reads,
        'sealed_inputs': inputs, 'historical_text_scans': scans,
        'different_old_S12_aliases': aliases,
        'input_commit_history': log.decode('utf-8').splitlines(),
        'R106_confirmation_actual_formal_arms': 0,
        'R107_confirmation_actual_native_processes': 0,
        'R107_confirmation_actual_Optimize': 0,
        'current_PE_performance_admission': 'PENDING_ACTUAL_PE_CLI_QUALIFICATION_AND_PROTOCOL',
        'limits': 'Exact SHA/path historical text scans plus full retained records; archives are indexed through public manifests and no public-only restore or engine rerun is claimed here.',
    })
    write(output / 'commands.json', commands)
    receipt = {'exit_code': 0, 'engineering_seconds': time.perf_counter() - start,
               'Optimize_calls': 0, 'IIS_calls': 0, 'compiler_calls': 0,
               'solver_processes': 0, 'output_root': str(output.resolve()),
               'script_sha256': sha(Path(__file__).read_bytes()),
               'audit_sha256': sha((output / 'audit.json').read_bytes()),
               'commands_sha256': sha((output / 'commands.json').read_bytes())}
    write(output / 'receipt.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
