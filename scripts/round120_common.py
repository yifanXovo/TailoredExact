"""Round120 identities and non-refundable outer process accounting."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round120'
OLD = Path('E:/codes/ExactEBRP-round119')
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
BASE = 'e6a3b2de67e3468c095331942da05d289f4f8aa3'
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
PE = ROOT / 'build/research/round120/ExactEBRP.exe'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def environment():
    e=dict(os.environ);e['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+e.get('PATH','');return e
def bindings():
    names=[ROOT/'CMakeLists.txt']
    for folder in ['src','include']:
        names += [p for p in (ROOT/folder).rglob('*') if p.suffix in ['.cpp','.inc','.hpp','.h']]
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(names)}
def helper_paths():
    import ast
    names=set();pending=['round120_common','round120_prepare','round120_campaign','round120_evidence',
        'read_round120','qualify_round120','round120_history','round120_math_audit']
    while pending:
        name=pending.pop();p=ROOT/'scripts'/(name+'.py')
        if name in names or not p.is_file():continue
        names.add(name)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending.extend(m for m in modules if m and (ROOT/'scripts'/(m+'.py')).is_file())
    paths=['scripts/'+n+'.py' for n in sorted(names)]
    paths += ['tests/round120_qualification.cpp','tests/round120_lp_diagnostics.cpp','tests/round120_qualification_support.hpp',
        'tests/round119_lifecycle_qualification.cpp','tests/round119_qualification.cpp','src/round65_reference_build.cpp']
    return sorted(set(paths))
def helpers():return {n:sha(ROOT/n) for n in helper_paths()}
def identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA'] and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings']
    return p
def budget():
    launches=sorted((OUT/'fees').glob('*/launch.json'))
    closed=[(read(p),read(p.parent/'receipt.json')) for p in launches if (p.parent/'receipt.json').exists()]
    starts=sum(read(p.parent/'receipt.json')['conservative_process_starts'] if (p.parent/'receipt.json').exists() else read(p)['conservative_process_starts'] for p in launches)
    seconds=sum(r['outer_seconds_upper'] for l,r in closed)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=40-starts,
        remaining_outer_seconds=48000-seconds,
        qualification_starts=sum(read(p.parent/'receipt.json')['conservative_process_starts'] if (p.parent/'receipt.json').exists() else read(p)['conservative_process_starts'] for p in launches if read(p)['qualification']),
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        unclosed=[p.parent.name for p in launches if not (p.parent/'receipt.json').exists()])
def fee_begin(label,children,cap,qualification,reservation):
    from round115_common import process_origin
    tick,creation=process_origin();b=budget();d=OUT/'fees'/label
    assert not d.exists() and not b['unclosed'],b
    assert b['remaining_starts']>=children+1+reservation['starts']
    assert b['remaining_outer_seconds']>=cap+reservation['seconds']
    if qualification:
        assert b['qualification_starts']+children+1<=16
        assert b['qualification_seconds']+cap<=3600
    d.mkdir(parents=True)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),wrapper_pid=os.getpid(),wrapper_creation_unix=creation,
        conservative_process_starts=children+1,declared_native_children=children,qualification=qualification,
        outer_cap=cap,budget_before=b,remaining_fixed_obligations=reservation,frozen_UTC=utc(),
        start_accounting='prospective maximum reserved; closure charges wrapper plus every actual or uncertain child start; failed starts remain charged, never-started slots are not process launches'))
    return d,tick
def fee_pending(d,tick,qualification,code,actual):
    write(d/'pending_exit_receipt.json',dict(exit_code=code,outer_seconds_lower=time.perf_counter()-tick,
        qualification=qualification,actual_native_children=actual,wrapper_pid=os.getpid(),
        conservative_process_starts=actual+1,maximum_prospectively_reserved_starts=read(d/'launch.json')['conservative_process_starts'],
        necessary_trailer_complete=True,nested_native_seconds_added=False))
    print(json.dumps(dict(wrapper_pending_exit=str(d),exit_code=code)),flush=True)
def close_fee(label):
    import ctypes
    d=OUT/'fees'/label;l=read(d/'launch.json');r=read(d/'pending_exit_receipt.json')
    assert not (d/'receipt.json').exists()
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];api.OpenProcess.restype=ctypes.c_void_p
    api.CloseHandle.argtypes=[ctypes.c_void_p]
    h=api.OpenProcess(0x1000,False,l['wrapper_pid'])
    if h:
        try:
            code=ctypes.c_ulong();assert api.GetExitCodeProcess(ctypes.c_void_p(h),ctypes.byref(code)) and code.value!=259
            assert code.value==r['exit_code']
        finally:api.CloseHandle(h)
    else: assert ctypes.get_last_error()==87,'wrapper exit cannot be established'
    upper=max(r['outer_seconds_lower'],time.time()-l['wrapper_creation_unix'])
    write(d/'receipt.json',dict(r,outer_seconds_upper=upper,actual_exit_observed=True,
        outer_interval=[r['outer_seconds_lower'],upper],caller_observed_unix=time.time(),
        charge_includes_exit_observation_delay=True,nested_native_seconds_added=False))
    print(json.dumps(budget()),flush=True)
if __name__=='__main__':close_fee(sys.argv[1])
