"""Expand the complete frozen Round137 GI-TBC argv (historical S2); run only with --run.

No campaign import, model compilation, input selection or algorithm switching.
The pure Windows affinity helper preserves the original measurement setting.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import math
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/gi_tbc_round137.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def number(value, positive=False):
    try:
        parsed = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('a finite number is required') from error
    if not math.isfinite(parsed) or parsed < 0 or (positive and parsed == 0):
        raise argparse.ArgumentTypeError('a finite positive number is required' if positive
                                         else 'a finite nonnegative number is required')
    return value


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--out-dir', type=Path, required=True, help='new directory; never overwritten')
    p.add_argument('--T', type=lambda v: number(v, True), required=True,
                   help='physical route horizon in seconds')
    p.add_argument('--pickup-time', type=number, default='60', help='seconds per unit')
    p.add_argument('--drop-time', type=number, default='60', help='seconds per unit, including return unloading')
    p.add_argument('--lambda', dest='lambda_value', type=number, default='0.15')
    p.add_argument('--cap', type=int, required=True, help='whole native process budget in seconds (>36)')
    p.add_argument('--seed', type=int, required=True, help='explicit Gurobi Seed; own H remains frozen')
    p.add_argument('--exe', type=Path, help='local GI-TBC-compatible executable; default uses verified Round137 PE')
    p.add_argument('--run', action='store_true', help='execute; otherwise only display the expanded command')
    p.add_argument('--json', action='store_true', help='display the complete machine-readable launch plan')
    return p


def normalize(argv, config):
    """Only paths and the explicitly allowed data/experiment values vary."""
    result = list(argv)
    result[0] = '${exe}'
    for flag, key in config['normalized_flags'].items():
        if result.count(flag) != 1:
            raise ValueError('missing or repeated frozen flag: ' + flag)
        result[result.index(flag) + 1] = '${' + key + '}'
    return result


def plan(args, config):
    if args.cap <= 36 or args.seed < 0:
        raise ValueError('--cap must exceed 36 seconds and --seed must be nonnegative')
    instance, output = args.input.resolve(), args.out_dir.resolve()
    executable = (args.exe or Path(config['default_executable'])).resolve()
    if not instance.is_file():
        raise ValueError('input file is missing: ' + str(instance))
    if output.exists():
        raise ValueError('output directory already exists; choose a new --out-dir: ' + str(output))
    if not executable.is_file():
        raise ValueError('executable is missing; supply --exe: ' + str(executable))
    digest = sha(executable)
    if args.exe is None and digest != config['verified_PE_SHA256']:
        raise ValueError('default executable differs from the verified Round137 PE')
    values = dict(exe=str(executable), input=str(instance), T=args.T,
                  pickup_time=args.pickup_time, drop_time=args.drop_time,
                  native_limit=str(args.cap - config['native_limit_offset_seconds']),
                  cap=str(args.cap), seed=str(args.seed), **{'lambda': args.lambda_value})
    values.update({key: str(output / name) for key, name in dict(
        result='result.json', log='native.log', phases='phases.csv', external='external',
        hga='hga.csv', progress='progress.csv', journal='journal').items()})
    command = [values[token[2:-1]] if token.startswith('${') and token.endswith('}')
               else token for token in config['argv']]
    if normalize(command, config) != config['argv']:
        raise ValueError('expanded command differs from the frozen GI-TBC vector')
    dll = Path(config['verified_DLL'])
    dll_sha = sha(dll) if dll.is_file() else None
    if args.run and args.exe is None and dll_sha != config['verified_DLL_SHA256']:
        raise ValueError('default DLL is missing or differs from the verified Round137 DLL')
    return dict(schema='paper-S2-launch-v1', algorithm=config['algorithm'], AP=False,
                command=command, windows_command=subprocess.list2cmdline(command), cwd=str(ROOT),
                output_directory=str(output), input_SHA256=sha(instance),
                executable_SHA256=digest, matches_verified_PE=digest == config['verified_PE_SHA256'],
                verified_DLL_path=str(dll), observed_DLL_SHA256=dll_sha,
                matches_verified_DLL=dll_sha == config['verified_DLL_SHA256'],
                config_SHA256=sha(CONFIG), source_commit=config['source_commit'],
                physical_T_seconds=float(args.T), process_cap_seconds=args.cap,
                native_time_limit_seconds=args.cap - config['native_limit_offset_seconds'],
                hard_stop_seconds=args.cap - config['hard_stop_offset_seconds'],
                affinity_mask=config['affinity_mask'], dry_run=not args.run,
                complete_own_H=True, campaign_postverification_performed=False,
                interpretation='entry/producer output only; formal paper evidence retains its original audit and clocks')


def save_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def execute(launch):
    if os.name != 'nt':
        raise ValueError('the frozen runtime/affinity configuration requires Windows')
    from round70_affinity import inherited_core, read_masks
    output = Path(launch['output_directory'])
    output.mkdir(parents=True, exist_ok=False)
    save_new(output / 'launch.json', launch)
    environment = dict(os.environ)
    environment['PATH'] = 'D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;' + environment.get('PATH', '')
    scratch = output / 'tmp'
    scratch.mkdir()
    environment.update(TEMP=str(scratch), TMP=str(scratch))
    start = time.perf_counter()
    child, error, reason, binding = None, None, 'normal_return', None
    try:
        with inherited_core(launch['affinity_mask']) as binding:
            with (output / 'stdout.log').open('x') as stdout, (output / 'stderr.log').open('x') as stderr:
                child = subprocess.Popen(launch['command'], cwd=launch['cwd'], env=environment,
                                         stdout=stdout, stderr=stderr)
                masks = read_masks(child.pid)
                if masks['process_mask'] != launch['affinity_mask']:
                    raise RuntimeError('child affinity differs from the frozen single CPU')
                save_new(output / 'affinity.json', dict(parent=binding, child=masks, pid=child.pid))
                child.wait(timeout=max(0.01, launch['hard_stop_seconds'] - (time.perf_counter() - start)))
    except subprocess.TimeoutExpired:
        reason = 'whole_run_hard_stop'
    except BaseException as exc:
        reason, error = 'launcher_failure', repr(exc)
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait()
        elapsed = time.perf_counter() - start
        returncode = child.returncode if child is not None else 127
        save_new(output / 'completion.json', dict(
            UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), returncode=returncode,
            process_and_cleanup_seconds=elapsed, process_cap_seconds=launch['process_cap_seconds'],
            stop_reason=reason, error=error, affinity=binding, certificate_inferred=False,
            performance_sample=False, campaign_postverification_performed=False))
    return 124 if reason == 'whole_run_hard_stop' else (1 if error else returncode)


def main():
    p = parser()
    args = p.parse_args()
    try:
        launch = plan(args, read(CONFIG))
        print(json.dumps(launch, indent=2) if args.json else launch['windows_command'], flush=True)
        return execute(launch) if args.run else 0
    except (OSError, ValueError) as error:
        p.error(str(error))


if __name__ == '__main__':
    sys.exit(main())
