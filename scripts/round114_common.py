"""Round114 frozen identities and conservative, exit-observed fees."""
from round113_common import ROOT, PYTHON, DLL, DLL_SHA, SOURCE, PE_SHA, bindings, read, write, sha, env, process_origin
from pathlib import Path
import json, os, sys, time

OUT=ROOT/'results/unified_exact_round114'
BASE='ea9410163aafd3877cdcde80e01ccd34d893f11b'
PE=ROOT/'build/research/round114-inherited/ExactEBRP.exe'
LAYER='R112_COMPLETE12_PLUS_R113_G50_4_PLUS_R114_G100_4'

def budget():
    launches=list((OUT/'fees').glob('*/launch.json'))
    closed=[(read(p),read(p.parent/'receipt.json')) for p in launches if (p.parent/'receipt.json').exists()]
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    seconds=sum(r['outer_seconds_upper'] for _,r in closed)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=16-starts,remaining_outer_seconds=17000-seconds,
        qualification_starts=sum(read(p)['conservative_process_starts'] for p in launches if read(p)['qualification']),
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        unclosed=[p.parent.relative_to(ROOT).as_posix() for p in launches if not (p.parent/'receipt.json').exists()])

def check_identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA
    assert sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings'] and len(p['source_bindings'])==206
    assert p['measured_source_commit']==SOURCE
    return p

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
    else:assert ctypes.get_last_error()==87,'cannot establish actual wrapper exit'
    upper=max(r['outer_seconds_lower'],time.time()-l['wrapper_creation_unix'])
    write(d/'receipt.json',dict(r,outer_seconds_upper=upper,actual_exit_observed=True,
        outer_interval=[r['outer_seconds_lower'],upper],caller_observed_unix=time.time(),
        charge_includes_wrapper_exit_observation_delay=True,nested_native_seconds_added=False))
    print(json.dumps(budget()),flush=True)

if __name__=='__main__':
    assert sys.argv[1]=='close-fee';close_fee(sys.argv[2])
