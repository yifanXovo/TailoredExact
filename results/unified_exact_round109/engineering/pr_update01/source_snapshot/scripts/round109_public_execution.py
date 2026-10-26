"""Record offline public operations from an explicit isolated cwd; no solver."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as file:
        while block := file.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as file:
        json.dump(value, file, indent=2, allow_nan=False)
        file.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--receipt-root', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--timeout', type=int, default=3600)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    cwd, source_root = Path(args.cwd).resolve(), Path(args.source_root).resolve()
    assert cwd.is_dir() and source_root == cwd
    assert command and Path(command[0]).resolve() == Path(sys.executable).resolve()
    program = Path(command[1]).resolve()
    assert program.is_relative_to(source_root) and program.suffix == '.py'
    assert program.name in ('round109_public.py', 'round109_finalize_blocked.py')
    directory = Path(args.receipt_root).resolve() / args.label
    directory.mkdir(parents=True, exist_ok=False)
    snapshots = []
    for source in sorted((source_root / 'scripts').glob('*.py')):
        target = directory / 'source_snapshot' / 'scripts' / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        snapshots.append(dict(path=source.relative_to(source_root).as_posix(), SHA=sha(source)))
    shutil.copyfile(__file__, directory / 'execution_source.py')
    launch = dict(command=command, cwd=str(cwd), source_root=str(source_root),
                  source_SHA=sha(__file__), sources=snapshots, started_unix=time.time(),
                  Python=sys.version, Python_executable=sys.executable,
                  original_worktree_data_reads=False, engineering=True,
                  conservative_solver_starts=0, Optimize=0, IIS=0)
    write(directory / 'launch.json', launch)
    tick = time.perf_counter()
    with (directory / 'stdout.log').open('xb') as so, (directory / 'stderr.log').open('xb') as se:
        child = subprocess.Popen(command, cwd=cwd, stdout=so, stderr=se)
        write(directory / 'process.json', dict(pid=child.pid, parent_pid=os.getpid()))
        timed_out = False
        try:
            code = child.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            child.kill()
            code = child.wait()
    receipt = dict(exit_code=code, timed_out=timed_out, seconds=time.perf_counter()-tick,
                   stdout_SHA=sha(directory / 'stdout.log'), stderr_SHA=sha(directory / 'stderr.log'),
                   launch_SHA=sha(directory / 'launch.json'), source_SHA=sha(__file__),
                   cwd=str(cwd), source_root=str(source_root), engineering=True,
                   conservative_solver_starts=0, Optimize=0, IIS=0)
    write(directory / 'receipt.json', receipt)
    print(json.dumps(receipt, allow_nan=False), flush=True)
    if code:
        raise SystemExit(code)


if __name__ == '__main__':
    main()
