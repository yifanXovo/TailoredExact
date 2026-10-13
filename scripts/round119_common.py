"""Round119 frozen runtime identity and nonrefundable conservative fees."""
from round119_support import ROOT,OUT,sha,read,write
from pathlib import Path
import ctypes,datetime,os,sys,time
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
PE=ROOT/'build/research/round119/ExactEBRP.exe'
EXPORTER=ROOT/'build/research/round119/Round119Qualification.exe'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
BASE='a756929a428f7afde30cbf66babbe44d0a1860ce'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def bindings():
    paths=[ROOT/'CMakeLists.txt']
    for folder in ['include','src']:
        paths += [p for p in (ROOT/folder).rglob('*') if p.suffix in ['.hpp','.h','.cpp','.inc']]
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def helpers():
    names=read(ROOT/'results/unified_exact_round118/helper_paths.json')['paths']
    names+=['scripts/'+p for p in ['round119_common.py','round119_support.py','round119_prepare.py',
        'round119_campaign.py','round119_evidence.py','qualify_round119.py','read_round119.py']]
    names+=['tests/round119_qualification.cpp']
    return {p:sha(ROOT/p) for p in sorted(set(names))}
def identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA'] and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings']
    return p
def environment():
    e=dict(os.environ);e['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+e.get('PATH','');return e
def budget():
    launches=list((OUT/'fees').glob('*/launch.json'))
    closed=[(read(p),read(p.parent/'receipt.json')) for p in launches if (p.parent/'receipt.json').exists()]
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    seconds=sum(r['outer_seconds_upper'] for _,r in closed)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=40-starts,remaining_outer_seconds=48000-seconds,
        qualification_starts=sum(read(p)['conservative_process_starts'] for p in launches if read(p)['qualification']),
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        unclosed=[p.parent.name for p in launches if not (p.parent/'receipt.json').exists()])
def fee_begin(label,children,cap,qualification,reservation):
    from round115_common import process_origin
    tick,creation=process_origin();b=budget();d=OUT/'fees'/label
    assert not d.exists() and not b['unclosed']
    assert b['remaining_starts']>=children+1+reservation['starts']
    assert b['remaining_outer_seconds']>=cap+reservation['seconds']
    if qualification:
        assert b['qualification_starts']+children+1<=12 and b['qualification_seconds']+cap<=2400
    d.mkdir(parents=True)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),wrapper_pid=os.getpid(),wrapper_creation_unix=creation,
        conservative_process_starts=children+1,declared_native_children=children,qualification=qualification,
        outer_cap=cap,budget_before=b,remaining_fixed_obligations=reservation,helpers=helpers(),frozen_UTC=utc()))
    return d,tick
def fee_pending(d,tick,qualification,code,actual):
    write(d/'pending_exit_receipt.json',dict(exit_code=code,outer_seconds_lower=time.perf_counter()-tick,
        qualification=qualification,actual_native_children=actual,
        conservative_process_starts=read(d/'launch.json')['conservative_process_starts'],wrapper_pid=os.getpid(),
        necessary_trailer_complete=True,nested_native_seconds_added=False))
    print(json.dumps(dict(wrapper_pending_exit=str(d),exit_code=code)),flush=True)
def close_fee(label):
    d=OUT/'fees'/label;l=read(d/'launch.json');r=read(d/'pending_exit_receipt.json');assert not (d/'receipt.json').exists()
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];api.OpenProcess.restype=ctypes.c_void_p
    api.CloseHandle.argtypes=[ctypes.c_void_p]
    h=api.OpenProcess(0x1000,False,l['wrapper_pid'])
    if h:
        try:
            code=ctypes.c_ulong();assert api.GetExitCodeProcess(ctypes.c_void_p(h),ctypes.byref(code)) and code.value!=259
            assert code.value==r['exit_code']
        finally:api.CloseHandle(h)
    else:assert ctypes.get_last_error()==87,'wrapper exit cannot be established'
    upper=max(r['outer_seconds_lower'],time.time()-l['wrapper_creation_unix'])
    write(d/'receipt.json',dict(r,outer_seconds_upper=upper,actual_exit_observed=True,
        outer_interval=[r['outer_seconds_lower'],upper],caller_observed_unix=time.time(),
        charge_includes_exit_observation_delay=True,nested_native_seconds_added=False))
    print(json.dumps(budget()),flush=True)
import json
import csv
csv.field_size_limit(64*1024*1024)
if __name__=='__main__':close_fee(sys.argv[1])
