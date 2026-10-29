"""Round139 finite process accounting. No process starts at import.

Only outer metered processes are charged. Native H/LP/MIP children and Work
are observations, never additional fees. Polling reads small durable metadata.
"""
from pathlib import Path
import argparse, ctypes, datetime, hashlib, json, math, os, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT / 'results/unified_exact_round139'
TEMP = WORK / 'temp/round139'
BUILD = WORK / 'build-cache/round139'
BASE = 'd606062edddf58c13a7c3acb48e896fc787ff856'
SOURCE = BASE
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
DOCUMENT_PYTHON = Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
COMPILER = Path('D:/msys64/ucrt64/bin/g++.exe')
E3 = BUILD / 'ExactEBRP.exe'
RESEARCH = BUILD / 'Round139Research.exe'
ORIGINAL_E3 = WORK / 'build-cache/round133/ExactEBRP.exe'
ORIGINAL_RESEARCH = WORK / 'build-cache/round132/Round132Research.exe'
EXPORTER = WORK / 'build-cache/round130/Round130ExportE3.exe'
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
ORIGINAL_PE_SHA = 'edfd4e2839afbe8571f00860402ae7596f702d4b494c1da8af0043acabf209ce'
LIMITS = dict(native=57600., diagnostic=57600.)
TOTAL_LIMIT = 57600.

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    """Atomic small JSON metadata; no reader can observe a partial replacement."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.tmp-{os.getpid()}')
    with temporary.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                                    *map(str, args)], cwd=cwd)

def environment():
    TEMP.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(TEMP), TMP=str(TEMP), PYTHONDONTWRITEBYTECODE='1')
    env['PATH'] = 'D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;' + env.get('PATH', '')
    return env

env = environment

def process_birth(pid):
    """Read actual Windows creation time from an OS handle, including PID reuse."""
    if os.name != 'nt':
        raise RuntimeError('Round139 live process identity requires Windows GetProcessTimes')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return None
    try:
        created, exited, kern, user = [ctypes.c_uint64() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *[ctypes.byref(x) for x in (created, exited, kern, user)]):
            raise ctypes.WinError(ctypes.get_last_error())
        if exited.value:
            return None
        return dict(creation_filetime=created.value,
                    creation_unix=created.value / 10000000. - 11644473600.)
    finally:
        kernel.CloseHandle(handle)

def process_snapshot(pid_record):
    """Small PID/birth query only; no result/journal/trajectory decoding."""
    current = process_birth(pid_record['pid'])
    same = bool(current and current['creation_filetime'] == pid_record['creation_filetime'])
    return dict(pid=pid_record['pid'], same_process_alive=same,
                recorded_creation_filetime=pid_record['creation_filetime'], actual=current,
                command=pid_record['command'])

def budget():
    charged = {kind: 0. for kind in LIMITS}
    separate, pending = 0., []
    for launch_path in sorted((OUT / 'fees').glob('*/launch.json')):
        launch = read(launch_path)
        receipt_path = launch_path.parent / 'receipt.json'
        if not receipt_path.exists():
            pending.append(dict(label=launch_path.parent.name, kind=launch['kind'],
                                reservation=launch.get('reservation_seconds', 0.),
                                PID_path=str(launch_path.parent / 'PID.json')))
            continue
        receipt = read(receipt_path)
        assert receipt['exit_observed'] is True
        value = float(receipt['G1_seconds'])
        assert math.isfinite(value) and value >= 0
        if launch['kind'] in charged:
            charged[launch['kind']] += value
        else:
            assert value == 0
        separate += float(receipt['separately_reported_seconds'])
    # E's independently executed exact-arithmetic processes precede this meter.
    external = OUT / 'infra/external_costs.json'
    if external.exists():
        for row in read(external).get('processes', []):
            assert row['kind'] in charged
            charged[row['kind']] += float(row['outer_seconds'])
    total = sum(charged.values())
    return dict(G1_seconds=total, remaining_G1_seconds=TOTAL_LIMIT-total,
                by_category=charged, limits=LIMITS,
                category_remaining={k:LIMITS[k]-charged[k] for k in LIMITS},
                separately_reported_seconds=separate, unclosed=pending,
                nested_H_LP_MIP_Work_not_added=True)

def _kill_owned_tree(child, identity, folder):
    alive = process_snapshot(identity)
    if child.poll() is not None:
        return
    assert alive['same_process_alive'], 'PID identity changed; refuse unrelated termination'
    result = subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'],
                            capture_output=True, timeout=30)
    write(folder / 'timeout_termination.json', dict(UTC=utc(), identity=alive,
          exit_code=result.returncode, stdout=result.stdout.decode(errors='replace'),
          stderr=result.stderr.decode(errors='replace')))
    child.wait(timeout=30)

def metered(label, kind, args, reservation=0, timeout=None, cwd=ROOT):
    """Run one finite outer. Existing labels never launch a second process.

    Non-native verification segments may be excluded only when the child writes
    explicit, disjoint cost_segments/<label>/*.json under this contract.
    """
    assert label and Path(label).name == label and label not in ('.','..')
    assert timeout is not None and 0 < float(timeout) <= 28800
    assert not os.environ.get('ROUND139_METERED_PARENT_LABEL'), 'nested fees would double count'
    before = budget()
    assert not before['unclosed'], ('inspect healthy or interrupted outer first', before['unclosed'])
    reservation = float(reservation or timeout)
    assert reservation > 0
    if kind in LIMITS:
        assert reservation <= before['remaining_G1_seconds'], before
        assert reservation <= before['category_remaining'][kind], before
    folder = OUT / 'fees' / label
    folder.mkdir(parents=True, exist_ok=False)
    command = list(map(str,args))
    tick, started = time.perf_counter(), time.time()
    write(folder/'launch.json',dict(UTC=utc(),kind=kind,command=command,cwd=str(cwd),
          timeout_seconds=float(timeout),reservation_seconds=reservation,budget_before=before,
          parent_pid=os.getpid(),parent_birth=process_birth(os.getpid())))
    child_env = environment()
    child_env['ROUND139_METERED_PARENT_LABEL'] = label
    timeout_hit, failure, identity, child = False, None, None, None
    with (folder/'stdout.log').open('xb') as stdout, (folder/'stderr.log').open('xb') as stderr:
        try:
            child = subprocess.Popen(command,cwd=cwd,env=child_env,stdout=stdout,stderr=stderr)
            birth = process_birth(child.pid)
            # Very short children may have exited before the handle query. The
            # Popen-owned handle still supplies the immutable creation FILETIME.
            if birth is None:
                created, exited, kern, user = [ctypes.c_uint64() for _ in range(4)]
                kernel = ctypes.WinDLL('kernel32',use_last_error=True)
                kernel.GetProcessTimes.argtypes = [ctypes.c_void_p,*([ctypes.c_void_p]*4)]
                assert kernel.GetProcessTimes(int(child._handle),*[ctypes.byref(x) for x in (created,exited,kern,user)])
                birth = dict(creation_filetime=created.value,creation_unix=created.value/10000000.-11644473600.)
            identity = dict(pid=child.pid,parent_pid=os.getpid(),command=command,**birth)
            write(folder/'PID.json',identity)
            child.wait(timeout=float(timeout))
        except subprocess.TimeoutExpired:
            timeout_hit = True
            _kill_owned_tree(child,identity,folder)
        except BaseException as error:
            failure = dict(type=type(error).__name__,message=str(error),UTC=utc())
            write(folder/'supervisor_failure.json',failure)
            if child is not None and child.poll() is None and identity is not None:
                # Keep the healthy process visible for an explicit resume; an
                # interruption does not authorize a second launch of this arm.
                write(folder/'pending_exit.json',dict(failure=failure,identity=identity,
                      still_alive=process_snapshot(identity),no_automatic_rerun=True))
                raise
    if child is None:
        rc = 127
    else:
        rc = int(child.returncode)
    elapsed = time.perf_counter()-tick
    segment_root = OUT/'cost_segments'/label
    segments = [read(path) for path in segment_root.glob('*.json')] if segment_root.exists() else []
    assert all(row.get('native_Optimize') == 0 and row['seconds'] >= 0 for row in segments)
    separately_measured = sum(row['seconds'] for row in segments)
    assert 0 <= separately_measured <= elapsed
    cost = elapsed-separately_measured if kind in LIMITS else 0.
    write(folder/'receipt.json',dict(exit_code=rc,outer_seconds=elapsed,G1_seconds=cost,
          separately_reported_seconds=elapsed-cost,start_unix=started,end_unix=time.time(),
          timeout=timeout_hit,supervisor_failure=failure,exit_observed=True,
          nested_H_LP_MIP_not_added=True,budget_category=kind))
    after = budget()
    print(json.dumps(dict(label=label,exit_code=rc,outer_seconds=elapsed,budget=after)),flush=True)
    if kind in LIMITS and (after['category_remaining'][kind] < 0 or after['remaining_G1_seconds'] < 0):
        raise RuntimeError('Measured budget exceeded; no later process may start')
    return 124 if timeout_hit else (1 if failure is not None else rc)

def light_status(label):
    folder=OUT/'fees'/label
    receipt=folder/'receipt.json'
    if receipt.exists():
        return dict(label=label,state='EXIT_OBSERVED',receipt=read(receipt))
    pid=folder/'PID.json'
    return dict(label=label,state='RUNNING_OR_INTERRUPTED',
                process=process_snapshot(read(pid)) if pid.exists() else None)

def native_identity(path=E3, expected_sha=None):
    path=Path(path)
    actual=sha(path)
    assert expected_sha is None or actual==expected_sha
    assert sha(DLL)==DLL_SHA
    return dict(PE=str(path),PE_SHA=actual,DLL=str(DLL),DLL_SHA=DLL_SHA)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('budget')
    status=sub.add_parser('status');status.add_argument('label')
    meter=sub.add_parser('meter');meter.add_argument('label');meter.add_argument('kind')
    meter.add_argument('--reservation',type=float,default=0)
    meter.add_argument('--timeout',type=float,required=True)
    arguments=sys.argv[1:]
    separator=arguments.index('--') if '--' in arguments else len(arguments)
    command=arguments[separator+1:]
    options=parser.parse_args(arguments[:separator])
    if options.action=='budget': print(json.dumps(budget()))
    elif options.action=='status': print(json.dumps(light_status(options.label)))
    else:
        assert command,'meter requires -- followed by a command'
        sys.exit(metered(options.label,options.kind,command,options.reservation,options.timeout))
