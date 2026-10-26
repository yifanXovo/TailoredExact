"""Record completed public-only restoration and exact raw reconstruction.

This supplements an already sealed carrier; it does not run a solver or rewrite
any raw record, report, old launch, or earlier receipt.
"""
import argparse, hashlib, json, sys, time
from pathlib import Path

ROUND = 'results/unified_exact_round108'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')

def run(root, recovered):
    begin = time.perf_counter()
    root, recovered = Path(root).resolve(), Path(recovered).resolve()
    out = root / ROUND
    directory = Path(__file__).resolve().parent
    restore_path = recovered / 'restore_receipt.json'
    restored = read(restore_path)
    assert restored['exit_code'] == 0 and restored['public_files_only']
    assert restored['original_workspace_reads'] is False
    assert Path(restored['restored_root']).resolve() == recovered
    assert root != recovered != Path(restored['public_root']).resolve()
    main = out / 'engineering/public_rebuild01'
    receipt = read(main / 'receipt.json')
    launch = read(main / 'launch.json')
    assert receipt['exit_code'] == 0 and receipt['timed_out'] is False
    assert Path(receipt['source_root']).resolve() == recovered
    assert Path(receipt['cwd']).resolve() == recovered
    assert sha(main / 'stdout.log') == receipt['stdout_SHA']
    assert sha(main / 'stderr.log') == receipt['stderr_SHA']
    assert sha(main / 'launch.json') == receipt['launch_SHA']
    lines = [json.loads(line) for line in (main / 'stdout.log').read_text(encoding='utf-8').splitlines() if line]
    assert len(lines) == 2
    summary, comparison = lines
    assert comparison['passed'] is True
    assert summary == read(recovered / 'rebuilt/summary.json')
    assert summary == read(recovered / ROUND / 'reports_final/summary.json')
    assert summary['formal_arms'] == 21 and summary['failed_formal_arms'] == 0
    assert summary['stage'] == 'SELECT_MB_FOR_BROAD_EVALUATION'
    expected = recovered / ROUND / 'reports_final'
    actual = recovered / 'rebuilt'
    csv_names = sorted(p.name for p in expected.glob('*.csv'))
    json_names = sorted(p.name for p in expected.glob('*.json'))
    assert comparison['exact_JSON_files_compared'] == json_names
    assert sorted(p.name for p in actual.glob('*.csv')) == csv_names
    for name in ['admission_decision.json', 'selection_decision.json']:
        assert read(recovered / ROUND / name) == read(actual / name)
    data = restore_path.read_bytes()
    with (out / 'public_restore_receipt.json').open('xb') as stream:
        stream.write(data)
    assert sha(out / 'public_restore_receipt.json') == sha(restore_path)
    value = dict(
        comparison=comparison, read_root=str(recovered),
        expected_root=str(expected), rebuilt_root=str(actual),
        command=receipt['command'], cwd=receipt['cwd'],
        exit_code=receipt['exit_code'], seconds=receipt['seconds'],
        source_SHA=sha(recovered / 'scripts/round108_reader.py'),
        raw_rebuild_wrapper_source_SHA=sha(recovered / 'scripts/round108_engineering.py'),
        wrapper_receipt_SHA=sha(main / 'receipt.json'), launch_SHA=sha(main / 'launch.json'),
        stdout_SHA=sha(main / 'stdout.log'), stderr_SHA=sha(main / 'stderr.log'),
        restore_receipt_SHA=sha(restore_path), csv_files=csv_names,
        CSV_header_and_row_field_dictionary_equality=True,
        all_JSON_values_equal=True, root_admission_and_selection_equal=True,
        source_snapshots=launch['sources'],
        raw_evidence_rebuilt=True, summary_copy_not_used=True,
        original_workspace_payload_reads=False, public_files_only=True,
        evidence_and_mathematical_reconstruction=True,
        independent_engine_performance_rerun=False,
        engineering=True, conservative_solver_starts=0, Optimize=0, IIS=0, route_oracle=0)
    write(out / 'public_comparison_receipt.json', value)
    write(directory / 'receipt.json', dict(
        command=[sys.executable, str(Path(__file__).resolve()), '--root', str(root), '--recovered-root', str(recovered)],
        exit_code=0, seconds=time.perf_counter()-begin, source_SHA=sha(__file__),
        restoration_receipt_copy_exact=True,
        comparison_receipt_SHA=sha(out / 'public_comparison_receipt.json'),
        restore_receipt_SHA=sha(out / 'public_restore_receipt.json'),
        engineering=True, conservative_solver_starts=0, Optimize=0, IIS=0))
    print(json.dumps(dict(comparison=comparison, CSV_files=len(csv_names), read_root=str(recovered))))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--recovered-root', required=True)
    args = parser.parse_args()
    run(args.root, args.recovered_root)
