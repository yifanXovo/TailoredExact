"""Round113 identities and closed fees. Imports do not launch work."""
from round112_common import ROOT, PYTHON, DLL, DLL_SHA, bindings, read, write, sha, env, process_origin
from pathlib import Path
import json, os, subprocess, sys, time

OUT = ROOT / 'results/unified_exact_round113'
OLD_ROOT = Path('E:/codes/ExactEBRP-round112')
BASE = '9165e69bf41d1eb323fd52b8cb4a8230dcb4edd4'
SOURCE = 'd0014a7163e3996fe120471420e56b089c9715ae'
PE_SHA = 'a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8'
PE = ROOT / 'build/research/round113-inherited/ExactEBRP.exe'
LAYER = 'R112_COMPLETE12_PLUS_R113_GEO8'

def budget():
    launches = list((OUT/'fees').glob('*/launch.json'))
    closed = [(read(p), read(p.parent/'receipt.json')) for p in launches if (p.parent/'receipt.json').exists()]
    starts = sum(read(p)['conservative_process_starts'] for p in launches)
    seconds = sum(r['outer_seconds_upper'] for _, r in closed)
    return dict(paid_starts=starts, paid_outer_seconds=seconds,
        qualification_starts=sum(read(p)['conservative_process_starts'] for p in launches if read(p)['qualification']),
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        remaining_starts=28-starts, remaining_outer_seconds=26000-seconds,
        unclosed=[p.parent.relative_to(ROOT).as_posix() for p in launches if not (p.parent/'receipt.json').exists()])

def check_identity():
    p = read(OUT/'production_identity.json')
    assert sha(PE) == p['production_PE_SHA'] == PE_SHA
    assert sha(DLL) == p['DLL_SHA'] == DLL_SHA
    assert bindings() == p['source_bindings'] and len(p['source_bindings']) == 206
    assert p['measured_source_commit'] == SOURCE
    return p

def close_fee(label):
    """Run only after the direct driver/wrapper has actually exited."""
    import ctypes
    d=OUT/'fees'/label; l=read(d/'launch.json'); r=read(d/'pending_exit_receipt.json')
    assert not (d/'receipt.json').exists()
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]; api.OpenProcess.restype=ctypes.c_void_p
    api.CloseHandle.argtypes=[ctypes.c_void_p]
    h=api.OpenProcess(0x1000,False,l['wrapper_pid'])
    if h:
        code=ctypes.c_ulong()
        try:
            assert api.GetExitCodeProcess(ctypes.c_void_p(h),ctypes.byref(code)) and code.value != 259
            assert code.value == r['exit_code']
        finally: api.CloseHandle(h)
    else: assert ctypes.get_last_error() == 87, 'cannot establish wrapper exit'
    upper=max(r['outer_seconds_lower'],time.time()-l['wrapper_creation_unix'])
    write(d/'receipt.json',dict(r,outer_seconds_upper=upper,actual_exit_observed=True,
        outer_interval=[r['outer_seconds_lower'],upper],caller_observed_unix=time.time(),
        charge_includes_wrapper_exit_observation_delay=True,clock_not_claimed_exact=True,
        fee_closure_engineering_native_starts=0))
    print(json.dumps(budget()),flush=True)

if __name__=='__main__':
    assert sys.argv[1]=='close-fee'
    close_fee(sys.argv[2])
