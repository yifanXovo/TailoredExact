"""Independent review author; execute once only through root's paid serial receipt.

Three Optimize calls, no IIS, no subprocess, no DP. Reuses retained LP bytes;
physical enumeration/route decoding below is independent of project readers.
"""
import ast
import ctypes
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
REVIEW = Path(__file__).resolve().parent
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
PE_SHA = '8b17e33c612d9768edec0047df5ca9efdc088ee8fc5a67acfbf0dd1b5f5e19c9'
CONTROL = ROOT / 'results/unified_exact_round105/control01'
C2 = CONTROL / 'raw/06_R98-C2_IR-CORE/external/round105'
F2_MODE = ROOT / 'results/unified_exact_round105/modes/F2_01/F2_k0/mode.json'
POSITIVE = ROOT / 'results/unified_exact_round105/modes/C2_controls01/R98-C2_seed_k0/native/oracle'
SETTINGS = dict(Threads=1, Seed=0, Presolve=-1, MIPGap=0.0, MIPGapAbs=0.0,
                FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
MODELS = [
    ('actual_full_infeasible', C2 / 'pattern_1_k0/full.lp',
     'b5c64c410ad3c29e8b3abdcb6402da0557c8535351988cdcaeba70d12700dca4', 3),
    ('actual_released_core_infeasible', C2 / 'pattern_1_k0/core_confirm.lp',
     'd2a90a125286ce93adf62bb462f12915f07cf0406bb08efa9bbc5e4e6a863df2', 3),
    ('actual_paid_seed_positive_control', POSITIVE / 'full.lp',
     'f620005b1b096962aab057329a481f6ae1debab5ed7ae01eb5f4471875d566f1', 2),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def persist(path, data):
    """Atomic, fsynced review evidence; never uses production calls.csv schema."""
    path = Path(path)
    temp = path.with_name(path.name + '.pending')
    with temp.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def parse_instance(path):
    text = Path(path).read_text(encoding='utf-8')
    def vector(name):
        found = re.search(r'(?m)^\s*' + name + r'\s*=\s*(\[[^\n]*\])', text)
        assert found, name
        return ast.literal_eval(found.group(1))
    head = text.splitlines()[0]
    count, cars = map(int, head[:head.index('[')].split())
    q = ast.literal_eval(head[head.index('['):])
    data = dict(V=count, M=cars, Q=q, initial=vector('initial'),
                capacity=vector('capacities'), points=vector('points'))
    assert len(q) == cars and all(len(data[n]) == count + 1
                                  for n in ['initial', 'capacity', 'points'])
    return data


def physical(data, vehicle, nodes, operations, limit, pickup_time, drop_time):
    """Start empty, unique nonzero visits, exact prefixes, loaded return allowed."""
    assert nodes[0] == nodes[-1] == 0
    stops = nodes[1:-1]
    assert len(stops) == len(set(stops)) and set(stops) == set(operations)
    load = 0
    prefixes = []
    total_pickup = 0
    station_ok = True
    for station in stops:
        assert 1 <= station <= data['V']
        q = operations[station]
        assert isinstance(q, int) and q != 0
        load += q
        prefixes.append(load)
        total_pickup += max(q, 0)
        station_ok &= 0 <= data['initial'][station] - q <= data['capacity'][station]
    points = data['points']
    # The original frozen inputs use Euclidean meters / 1.5 meters per second.
    travel = sum(math.hypot(points[a][0] - points[b][0], points[a][1] - points[b][1]) / 1.5
                 for a, b in zip(nodes, nodes[1:]))
    handling = (pickup_time + drop_time) * total_pickup
    duration = travel + handling
    load_ok = all(0 <= value <= data['Q'][vehicle] for value in prefixes)
    return dict(nodes=nodes, operations=operations, prefixes=prefixes,
                return_load=load, total_pickup=total_pickup, travel=travel,
                handling=handling, duration=duration, original_T=limit,
                station_ok=bool(station_ok), load_ok=load_ok,
                feasible=bool(station_ok and load_ok and duration <= limit + 1e-7))


def solution_values(path):
    values = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, value = line.split()
        values[name] = float(value)
    return values


def decode_route(values, data, operations):
    selected = {(i, j) for i in range(data['V'] + 1) for j in range(data['V'] + 1)
                if i != j and values[f'x_{i}_{j}'] > 0.5}
    current = 0
    nodes = [0]
    used = set()
    seen = set()
    while True:
        outgoing = [b for a, b in selected if a == current]
        assert len(outgoing) == 1, ('ambiguous/open route', current, outgoing)
        next_node = outgoing[0]
        used.add((current, next_node))
        nodes.append(next_node)
        if next_node == 0:
            break
        assert next_node not in seen and next_node in operations
        seen.add(next_node)
        current = next_node
    assert used == selected and seen == set(operations), 'disconnected/extra/absent visits'
    for i in range(1, data['V'] + 1):
        q = operations.get(i, 0)
        assert abs(values[f'z_{i}'] - bool(q)) <= 1e-5
        assert abs(values[f'p_{i}'] - max(q, 0)) <= 1e-5
        assert abs(values[f'd_{i}'] - max(-q, 0)) <= 1e-5
    return nodes


def runtime_binding():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    kernel.GetModuleHandleW.restype = ctypes.c_void_p
    kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
    kernel.GetModuleFileNameW.restype = ctypes.c_uint
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.EnumProcessModules.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
                                       ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    psapi.EnumProcessModules.restype = ctypes.c_int
    modules = (ctypes.c_void_p * 2048)()
    needed = ctypes.c_uint()
    assert psapi.EnumProcessModules(kernel.GetCurrentProcess(), modules,
                                   ctypes.sizeof(modules), ctypes.byref(needed))
    assert needed.value <= ctypes.sizeof(modules)
    engines = []
    for module in list(modules)[:needed.value // ctypes.sizeof(ctypes.c_void_p)]:
        name = ctypes.create_unicode_buffer(32768)
        assert kernel.GetModuleFileNameW(module, name, len(name))
        if Path(name.value).name.lower() == 'gurobi130.dll':
            engines.append(Path(name.value))
    assert len(engines) == 1, ('unexpected/multiple engine modules', engines)
    actual = engines[0]
    assert os.path.normcase(str(actual.resolve())) == os.path.normcase(str(DLL.resolve()))
    assert sha(actual) == DLL_SHA
    return dict(path=str(actual), sha256=sha(actual), loaded_modules=list(map(str, engines)))


def quality_and_rows(model):
    quality = {name: float(model.getAttr(name)) for name in ['ConstrVio', 'BoundVio', 'IntVio']}
    assert all(math.isfinite(value) for value in quality.values())
    assert quality['ConstrVio'] <= 1e-6 and quality['BoundVio'] <= 1e-6 and quality['IntVio'] <= 1e-5
    maximum = 0.0
    for row in model.getConstrs():
        expression = model.getRow(row)
        activity = sum(expression.getCoeff(i) * expression.getVar(i).X for i in range(expression.size()))
        violation = (activity - row.RHS if row.Sense == '<' else row.RHS - activity
                     if row.Sense == '>' else abs(activity - row.RHS))
        maximum = max(maximum, violation)
    assert maximum <= 1e-6
    quality.update(independent_raw_max_row_violation=maximum, checked_rows=model.NumConstrs)
    return quality


def main():
    assert os.name == 'nt', 'Review native reproduction requires the frozen Windows runtime'
    expected_python = ROOT / 'build/research/round88-ot/venv/Scripts/python.exe'
    assert os.path.normcase(str(Path(sys.executable).resolve())) == os.path.normcase(str(expected_python.resolve()))
    counter_path = REVIEW / 'native_execution.json'
    assert not counter_path.exists(), 'Exactly one newly paid execution; do not overwrite prior starts'
    output = REVIEW / 'native_reproduction01'
    output.mkdir(exist_ok=False)
    record = dict(schema='round105-independent-review-native-v1', Optimize_starts=0,
                  IIS_starts=0, subprocess_starts=0, environment_starts=0,
                  planned_Optimize=3, planned_IIS=0, status='preparing',
                  script_sha256=sha(__file__), python=str(sys.executable), events=[])
    persist(counter_path, record)
    try:
        identity = read(CONTROL / 'identity.json')
        assert identity['candidate_binary_sha256'] == PE_SHA
        assert sha(ROOT / identity['prereg']['candidate_binary']) == PE_SHA
        assert identity['dll_sha256'] == DLL_SHA and sha(DLL) == DLL_SHA
        for name, digest in identity['source_hashes'].items():
            assert sha(ROOT / name) == digest, ('production source drift', name)
        for _, path, digest, _ in MODELS:
            assert sha(path) == digest, ('retained model drift', path)
        record['sources'] = dict(control_identity_sha256=sha(CONTROL / 'identity.json'),
                                 production_source_hashes=identity['source_hashes'], PE_sha256=PE_SHA,
                                 models={name: dict(path=str(path), sha256=digest)
                                         for name, path, digest, _ in MODELS})
        full_text = MODELS[0][1].read_text()
        core_text = MODELS[1][1].read_text()
        assumption = r'(?m)^\s*a_[0-9]+_[zpd]:[^\n]*\n'
        assert re.sub(assumption, '', full_text) == re.sub(assumption, '', core_text)
        proposal = read(C2 / 'pattern_1_k0/proposal.json')['groups']
        assert sorted({int(i) for i in re.findall(r'(?m)^\s*a_([0-9]+)_[zpd]:', core_text)}) == proposal
        f2_mode = read(F2_MODE)
        f2_panel = f2_mode['panel']
        assert sha(ROOT / f2_panel['input_path']) == f2_panel['input_sha256']
        f2 = parse_instance(ROOT / f2_panel['input_path'])
        f2_ops = {i: q for i, q in enumerate(f2_mode['operations'], 1) if q}
        assert len(f2_ops) == 3 and f2_mode['source_status'] == 9
        enumeration = [physical(f2, f2_mode['vehicle'], [0, *order, 0], f2_ops,
                                f2_panel['T_seconds'], f2_panel['pickup_seconds'], f2_panel['drop_seconds'])
                       for order in itertools.permutations(f2_ops)]
        assert len(enumeration) == 6 and not any(r['feasible'] for r in enumeration)
        persist(output / 'F2_all_six_orders.json', dict(mode_sha256=sha(F2_MODE), orders=enumeration,
                                                     conclusion='all_six_original_orders_infeasible'))
        launch = next(r for r in identity['launches'] if r['id'] == 'R98-C2' and r['arm'] == 'IR-CORE')
        panel = launch['panel']
        assert sha(ROOT / panel['input_path']) == panel['input_sha256']
        c2 = parse_instance(ROOT / panel['input_path'])
        seed = read(C2 / 'seed.json')
        seed_route = next(r for r in seed['routes'] if r['vehicle'] == 0)
        positive_ops = {}
        for op in seed_route['operations']:
            assert op['station'] not in positive_ops
            positive_ops[op['station']] = op['pickup'] - op['drop']
        positive_mode = read(POSITIVE.parents[1] / 'mode.json')
        assert positive_ops == {i: q for i, q in enumerate(positive_mode['operations'], 1) if q}
        assert sha(C2 / 'seed.json') == positive_mode['source_sha256']
        old_values = solution_values(POSITIVE / 'full.lp.sol')
        old_nodes = decode_route(old_values, c2, positive_ops)
        old_check = physical(c2, 0, old_nodes, positive_ops, panel['T_seconds'],
                             panel['pickup_seconds'], panel['drop_seconds'])
        assert old_check['feasible']
        persist(output / 'C2_existing_native_route_check.json', dict(
            seed_source=str(C2 / 'seed.json'), seed_sha256=sha(C2 / 'seed.json'),
            solution_sha256=sha(POSITIVE / 'full.lp.sol'), check=old_check))
        # Trusted runtime pattern: exact production DLL preloaded BEFORE gurobipy import.
        dll_directory = os.add_dll_directory(str(DLL.parent))
        production_runtime = ctypes.WinDLL(str(DLL), use_last_error=True)
        import gurobipy as gp
        assert gp.gurobi.version() == (13, 0, 2)
        record['runtime'] = dict(runtime_binding(), version=list(gp.gurobi.version()),
                                 python_package=gp.__file__)
        persist(counter_path, record)
        environment = gp.Env(empty=True)
        environment.setParam('LogToConsole', 0)
        environment.setParam('OutputFlag', 1)
        record['environment_starts'] += 1
        persist(counter_path, record)
        environment.start()
        deadline = time.monotonic() + 90.0
        results = []
        try:
            for name, path, digest, expected_status in MODELS:
                model = gp.read(str(path), env=environment)
                try:
                    for key in ['Threads', 'Seed', 'Presolve', 'MIPGap', 'MIPGapAbs']:
                        model.setParam(key, SETTINGS[key])
                    parameters = {key: model.getParamInfo(key)[2] for key in SETTINGS}
                    assert parameters == SETTINGS, ('original numeric contract mismatch', parameters)
                    assert time.monotonic() < deadline
                    model.setParam('TimeLimit', deadline - time.monotonic())
                    log_path = output / (name + '.log')
                    model.setParam('LogFile', str(log_path))
                    event = dict(number=record['Optimize_starts'] + 1, name=name, phase='before',
                                 model_sha256=digest, parameters=parameters,
                                 remaining_seconds=deadline - time.monotonic())
                    record['Optimize_starts'] += 1
                    record['events'].append(event)
                    record['status'] = 'native_running'
                    persist(counter_path, record)  # Required durable increment BEFORE each native call.
                    tick = time.monotonic()
                    model.optimize()
                    result = dict(name=name, status=model.Status, solutions=model.SolCount,
                                  native_seconds=time.monotonic() - tick, model_sha256=digest,
                                  parameters=parameters, runtime=runtime_binding())
                    record['events'].append(dict(number=event['number'], phase='after', **result))
                    persist(counter_path, record)
                    assert model.Status == expected_status, result
                    assert log_path.is_file()
                    log = log_path.read_text(errors='replace').lower()
                    assert not any(p in log for p in ['numerical trouble', 'numerical difficulties',
                                                     'unscaled primal violation', 'unscaled dual violation'])
                    if model.SolCount:
                        result['quality'] = quality_and_rows(model)
                        values = {v.VarName: v.X for v in model.getVars()}
                        nodes = decode_route(values, c2, positive_ops)
                        route_check = physical(c2, 0, nodes, positive_ops, panel['T_seconds'],
                                               panel['pickup_seconds'], panel['drop_seconds'])
                        assert route_check['feasible'] and abs(model.ObjVal) <= 1e-7
                        result['route_check'] = route_check
                        model.write(str(output / (name + '.sol')))
                    else:
                        assert expected_status == gp.GRB.INFEASIBLE
                    results.append(result)
                    persist(output / (name + '.json'), result)
                finally:
                    model.dispose()
        finally:
            environment.dispose()
        assert record['Optimize_starts'] == 3 and record['IIS_starts'] == record['subprocess_starts'] == 0
        record['status'] = 'PASS'
        record['scope'] = ('Independent author/physical six-order enumeration and route validation; same native '
                           'floating engine; retained LP models, not independent model construction, not rational '
                           'certificates, not independent full production reexecution or performance replication.')
        persist(output / 'result.json', dict(passed=True, results=results, scope=record['scope']))
        persist(counter_path, record)
        print(json.dumps(dict(passed=True, Optimize_starts=3, IIS_starts=0, subprocess_starts=0)))
        # Keep these handles alive until after all native objects are disposed.
        _ = dll_directory, production_runtime
    except BaseException as exc:
        record['status'] = 'FAIL'
        record['error'] = type(exc).__name__ + ': ' + str(exc)
        persist(counter_path, record)
        raise


if __name__ == '__main__':
    main()
