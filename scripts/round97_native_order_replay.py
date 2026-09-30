"""Prospective native-state H2 replay. No optimizer; never runs beside a solver."""
import argparse
import ast
import ctypes as ct
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from round97_campaign import ROOT, OUT, BUILD, bindings, read, write, sha, ext, evidence
from round96_prepare import citi
from round96_order_analyze import operations, duration

DEST = OUT / 'native_order_replay'
BIN = BUILD / 'Round96RouteOrderDiagnostic.exe'


def helper_bindings():
    paths = {Path(m.__file__).resolve() for m in list(sys.modules.values())
             if getattr(m, '__file__', None)}
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)
            if p.is_relative_to(ROOT/'scripts') and p.suffix == '.py'}


def ensure_idle():
    ext.ensure_idle()
    raw = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command',
        "Get-CimInstance Win32_Process -Filter \"Name = 'Round96RouteOrderDiagnostic.exe'\" | Select-Object ProcessId | ConvertTo-Json -Compress"],
        text=True).strip()
    assert not raw, ('native order diagnostic active', raw)


def source(label, number):
    identity = read(OUT / label / 'identity.json')
    launch = identity['launches'][number - 1]
    completed = [json.loads(s) for s in (OUT / label / 'summary.jsonl').read_text().splitlines()]
    assert len(completed) >= number and completed[number - 1]['audit_passed']
    folder = Path(launch['destination']) / 'external/round97'
    rows = [json.loads(s) for s in (folder / 'events.jsonl').read_text().splitlines()]
    return launch, folder, [r for r in rows if r['kind'] == 'solution']


def prepare():
    ensure_idle()
    assert not DEST.exists() and BIN.exists()
    cases = []
    for role, label, number in [('F2', 'qualification02', 3), ('F5', 'development01', 1)]:
        launch, folder, events = source(label, number)
        if role == 'F2':
            selected = [r for r in events if r['event'] in [4, 7, 9]]
            assert len(selected) == 3
        else:
            unique = {}
            for r in events:
                if r.get('matches_supplied_start_physical_state') is False and r.get('nodes', 0) > 0:
                    unique.setdefault(r['input_hash'], r)
            ordered = list(unique.values())
            selected = [ordered[i] for i in sorted({0, (len(ordered)-1)//2, len(ordered)-1})] if ordered else []
        selected += [next(r for r in events if r.get('matches_supplied_start_physical_state') is True)]
        seen = set()
        for event in selected:
            h = event['input_hash']
            if h in seen:
                continue
            seen.add(h)
            path = folder / ('input_' + h + '.json')
            if not path.exists():
                # An exhausted output is cached before native later discovers it.
                # Keep the selected state, using its already retained witness.
                matches = [q for q in sorted(folder.glob('*.json'))
                           if read(q).get('sha256') == h and 'routes' in read(q)]
                assert matches, ('selected state witness missing', role, h)
                path = matches[0]
            assert read(path)['sha256'] == h
            cases.append(dict(id=f'{role}_event{event["event"]}', panel=launch['panel'],
                              source_batch=label, source_event=event, witness_path=str(path),
                              witness_sha256=sha(path), source_events_path=str(folder/'events.jsonl'),
                              source_events_sha256=sha(folder/'events.jsonl')))
    assert len(cases) <= 8
    write(DEST / 'identity.json', dict(cases=cases, source_hashes=bindings(), helper_hashes=helper_bindings(),
        diagnostic_source_sha256=sha(ROOT/'tests/round96_route_order_diagnostic.cpp'),
        binary_sha256=sha(BIN), runner_sha256=sha(__file__),
        selection_plan_sha256=sha(OUT/'native_order_replay_plan.md'),
        maximum_starts=len(cases), maximum_process_seconds=120*len(cases), optimizer_calls=0))
    print(json.dumps(dict(prepared=len(cases), optimizer_calls=0)))


def run(number):
    task_tick = time.perf_counter()
    ensure_idle()
    identity = read(DEST / 'identity.json')
    assert identity['source_hashes'] == bindings()
    assert identity['helper_hashes'] == helper_bindings()
    assert identity['binary_sha256'] == sha(BIN) and identity['runner_sha256'] == sha(__file__)
    assert identity['diagnostic_source_sha256'] == sha(ROOT/'tests/round96_route_order_diagnostic.cpp')
    assert identity['selection_plan_sha256'] == sha(OUT/'native_order_replay_plan.md')
    assert 1 <= number <= len(identity['cases'])
    case = identity['cases'][number - 1]
    for previous in identity['cases'][:number - 1]:
        prior = read(DEST/(previous['id']+'.audit.json'))
        assert prior['passed'] or prior.get('outcome') == 'diagnostic_timeout_unknown'
    p = case['panel']; cid = case['id']; witness = read(case['witness_path'])
    assert sha(case['witness_path']) == case['witness_sha256']
    assert sha(case['source_events_path']) == case['source_events_sha256']
    assert sha(ROOT/p['input_path']) == p['input_sha256']
    fleet = citi.parse_instance_mirror(ROOT/p['input_path'])['M']
    routes = {r['vehicle']: r for r in witness['routes']}
    lines = [str(fleet)]
    for k in range(fleet):
        route = routes.get(k, dict(vehicle=k, nodes=[0, 0], operations=[]))
        ops = {o[0]: o for o in route['operations']}
        lines.append(f'{k} {len(route["nodes"])-2}')
        lines.extend(' '.join(map(str, ops[i])) for i in route['nodes'][1:-1])
    routepath = DEST/(cid+'.routes.txt')
    with routepath.open('x') as f:
        f.write('\n'.join(lines)+'\n')
    dest = DEST/cid
    command = list(map(str, [BIN, ROOT/p['input_path'], routepath, p['T_seconds'],
                            p['pickup_seconds'], p['drop_seconds'], p['lambda'], dest]))
    write(DEST/(cid+'.launch.json'), dict(command=command, cap_seconds=120, optimizer_calls=0))
    env = dict(os.environ)
    env['PATH'] = 'D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;' + env.get('PATH', '')
    kernel = ct.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = ct.c_void_p
    kernel.SetProcessAffinityMask.argtypes = [ct.c_void_p, ct.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(), 4)
    tick = time.perf_counter()
    with (DEST/(cid+'.stdout.log')).open('x') as so, (DEST/(cid+'.stderr.log')).open('x') as se:
        try:
            code = subprocess.run(command, cwd=ROOT, env=env, stdout=so, stderr=se, timeout=120).returncode
            reason = 'normal_return' if code == 0 else 'process_failure'
        except subprocess.TimeoutExpired:
            code = None; reason = 'diagnostic_timeout'
    receipt = dict(id=cid, exit_code=code, stop_reason=reason,
                   wall_seconds=time.perf_counter()-tick, optimizer_calls=0)
    write(DEST/(cid+'.completion.json'), receipt)
    if reason == 'diagnostic_timeout':
        write(DEST/(cid+'.audit.json'), dict(passed=False, outcome='diagnostic_timeout_unknown',
            receipt=receipt, optimizer_calls=0, wrapper_seconds_before_write=time.perf_counter()-task_tick))
        print(json.dumps(dict(id=cid, outcome='diagnostic_timeout_unknown', receipt=receipt)))
        return
    if code != 0:
        write(DEST/(cid+'.audit.json'), dict(passed=False, outcome='process_failure', receipt=receipt,
            wrapper_seconds_before_write=time.perf_counter()-task_tick))
        raise RuntimeError('Preserve failed paid prefix; do not rerun or continue after failure')
    result = read(dest/'summary.json')
    assert result['input_sha256'] == p['input_sha256'] and result['route_sha256'] == sha(routepath)
    assert (result['old_exhausted'] or result['old_zero']) and not result['old_failed']
    assert (result['exhausted'] or result['zero']) and not result['verification_failed'] and not result['deadline']
    checked = []
    for path in sorted(dest.rglob('*.json')):
        value = read(path)
        if not isinstance(value, dict) or 'routes' not in value:
            continue
        verified = evidence.physical_module.physical(p, value)
        assert verified['original_T_feasible']
        checked.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path), physical=verified))
    raw_input = (ROOT/p['input_path']).read_text(encoding='utf-8')
    match = re.search(r'(?m)^\s*points\s*=\s*(\[[^\n]*\])', raw_input)
    assert match, 'This replay supports only the frozen Euclidean coordinate inputs'
    points = ast.literal_eval(match[1])
    independent_dist = [[math.hypot(a[0]-b[0], a[1]-b[1])/1.5 for b in points] for a in points]
    moves = []
    for k in range(1, result['order_moves']+1):
        old = dest/'order'/f'old_{k-1}'
        before = read(old/'final.json'); after = read(dest/'order'/f'order_{k}.json')
        assert operations(before) == operations(after)
        dist = read(old/'actual_distances.json')
        assert len(dist) == len(independent_dist)
        assert all(len(row) == len(points) for row in dist)
        assert all(abs(dist[i][j]-independent_dist[i][j]) <= 1e-10*max(1, independent_dist[i][j])
                   for i in range(len(points)) for j in range(len(points)))
        a = duration(before, p, independent_dist, fleet); b = duration(after, p, independent_dist, fleet)
        assert b < a and before['F'] == after['F'] and before['inventory'] == after['inventory']
        moves.append(dict(number=k, before=a, after=b, inventory_owner_operation_preserved=True))
    for kind in ['old', 'order']:
        v = evidence.physical_module.physical(p, read(dest/kind/'final.json'))
        assert abs(v['F']-result[kind+'_F']) < 1e-7
    assert result['order_F'] <= result['old_F'] + 1e-12
    write(DEST/(cid+'.audit.json'), dict(passed=True, outcome='passed', receipt=receipt, result=result,
                                        wrapper_seconds_before_write=time.perf_counter()-task_tick,
                                        witnesses=checked, order_moves=moves, optimizer_calls=0))
    print(json.dumps(dict(id=cid, initial=result['initial_F'], old=result['old_F'],
                          order=result['order_F'], seconds=receipt['wall_seconds'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--number', type=int)
    args = parser.parse_args()
    lock = OUT/'native_order_replay.lock'
    with lock.open('x') as f:
        json.dump(dict(pid=os.getpid(), action=args.action, number=args.number), f)
    try:
        if args.action == 'prepare':
            prepare()
        else:
            run(args.number)
    finally:
        lock.unlink()
