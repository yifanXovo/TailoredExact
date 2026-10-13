"""Round118 identity and nonrefundable conservative launch accounting."""
from round118_data import ROOT,OUT,BASE,sha,read,write,utc
from round115_common import bindings,env,process_origin
from pathlib import Path
import ctypes,json,os,sys,time
PE=ROOT/'build/research/round118-inherited/ExactEBRP.exe'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
SOURCE='d0014a7163e3996fe120471420e56b089c9715ae'
PE_SHA='a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8'
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'

def helpers():
    # Bind actual new bytes, including the two repaired read-only inherited readers.
    if (OUT/'helper_paths.json').exists():return {p:sha(ROOT/p) for p in read(OUT/'helper_paths.json')['paths']}
    names={Path(m.__file__).resolve() for m in list(sys.modules.values())
        if getattr(m,'__file__',None) and Path(m.__file__).suffix=='.py' and Path(m.__file__).resolve().is_relative_to(ROOT/'scripts')}
    names.update((ROOT/'scripts').glob('round118*.py'))
    names.update([ROOT/'scripts/publication_security.py',ROOT/'scripts/round118_reference.cpp'])
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(names) if p.is_file()}

def check_identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings'] and len(bindings())==206
    assert p['measured_source_commit']==SOURCE
    return p

def budget():
    launches=list((OUT/'fees').glob('*/launch.json'));closed=[(read(p),read(p.parent/'receipt.json')) for p in launches if (p.parent/'receipt.json').exists()]
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    seconds=sum(r['outer_seconds_upper'] for l,r in closed)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=20-starts,remaining_outer_seconds=28000-seconds,
        qualification_starts=sum(read(p)['conservative_process_starts'] for p in launches if read(p)['qualification']),
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        unclosed=[p.parent.name for p in launches if not (p.parent/'receipt.json').exists()])

def qualification_limit():
    # A prepared repair does not authorize another launch. Only the recorded
    # direct human response can raise this limit; failed declared slots remain.
    if (OUT/'budget_authorization_13.json').is_file():
        authorization=read(OUT/'budget_authorization_13.json')
        assert authorization['qualification_starts_new']==13
        assert authorization['reuse_sealed_PS_with_corrected_readonly_verifier'] is True
        assert authorization['qualification_outer_seconds']==1200
        assert authorization['total_starts']==20 and authorization['total_outer_seconds']==28000
        return 13
    if (OUT/'budget_authorization.json').is_file():
        assert read(OUT/'budget_authorization.json')['qualification_starts_new']==11
        return 11
    return 8

def fee_begin(label,children,cap,qualification):
    tick,creation=process_origin();b=budget();d=OUT/'fees'/label
    assert not b['unclosed'] and not d.exists()
    future=not (OUT/'fees/formal01/launch.json').exists() and qualification
    assert b['remaining_starts']>=children+1+(5 if future else 0)
    assert b['remaining_outer_seconds']>=cap+(21720 if future else 0)
    if qualification:
        assert b['qualification_starts']+children+1<=qualification_limit() and b['qualification_seconds']+cap<=1200
    d.mkdir(parents=True)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),wrapper_pid=os.getpid(),wrapper_creation_unix=creation,
        conservative_process_starts=children+1,declared_native_children=children,qualification=qualification,
        outer_cap=cap,budget_before=b,unstarted_formal_reservation=21720 if future else 0,helpers=helpers(),frozen_UTC=utc()))
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
    else:assert ctypes.get_last_error()==87,'cannot establish actual wrapper exit'
    upper=max(r['outer_seconds_lower'],time.time()-l['wrapper_creation_unix'])
    write(d/'receipt.json',dict(r,outer_seconds_upper=upper,actual_exit_observed=True,
        outer_interval=[r['outer_seconds_lower'],upper],caller_observed_unix=time.time(),
        charge_includes_wrapper_exit_observation_delay=True,nested_native_seconds_added=False))
    print(json.dumps(budget()),flush=True)

if __name__=='__main__':close_fee(sys.argv[1])
