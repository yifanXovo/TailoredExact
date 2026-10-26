"""Round115 identities, prospective clocks and exit-observed conservative fees."""
from round114_common import ROOT, PYTHON, DLL, DLL_SHA, SOURCE, PE_SHA, bindings, read, write, sha, env, process_origin
from pathlib import Path
import ctypes, json, os, sys, time

OUT=ROOT/'results/unified_exact_round115'
BASE='e436748521cf5aabbe84a24a5e9cf3836550563c'
PE=ROOT/'build/research/round115-inherited/ExactEBRP.exe'
LAYER='R112_COMPLETE12_PLUS_R113_G50_3_PLUS_R115_G100_4_MEASUREMENT_V2'

def budget():
    launches=list((OUT/'fees').glob('*/launch.json'))
    closed=[(read(p),read(p.parent/'receipt.json')) for p in launches if (p.parent/'receipt.json').exists()]
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    seconds=sum(r['outer_seconds_upper'] for _,r in closed)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=24-starts,remaining_outer_seconds=20000-seconds,
        qualification_starts=sum(read(p)['conservative_process_starts'] for p in launches if read(p)['qualification']),
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        unclosed=[p.parent.relative_to(ROOT).as_posix() for p in launches if not (p.parent/'receipt.json').exists()])

def check_identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings'] and len(p['source_bindings'])==206
    assert p['measured_source_commit']==SOURCE
    return p

def close_fee(label):
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

def clock_evidence(d,l):
    p=read(d/'producer_receipt.json');v=read(d/'arm_total_receipt.json');seal=read(d/'producer_seal.json')
    assert p['state']=='PRODUCED_PENDING_VERIFICATION' and p['verification_passed'] is None
    assert p['producer_seal_SHA']==sha(d/'producer_seal.json')
    for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,('sealed producer changed',name)
    assert v['producer_receipt_SHA']==sha(d/'producer_receipt.json')
    assert v['verification_closeout_SHA']==sha(d/'verification_closeout.json') and v['necessary_verification_complete']
    assert p['t0_perf']<p['t_produce_perf']<=v['t_verified_perf']
    assert p['T_produce']==p['t_produce_perf']-p['t0_perf']
    assert v['T_verify']==v['t_verified_perf']-p['t_produce_perf']
    assert v['T_total']==v['t_verified_perf']-p['t0_perf']
    assert abs(v['T_total']-p['T_produce']-v['T_verify'])<1e-8
    assert p['cap_seconds']==l['cap_seconds'] and p['required_outputs_closed'] and p['native_stopped_no_reentry']
    c=read(d/'completion.json');assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    return dict(complete_seconds=p['T_produce'],T_produce=p['T_produce'],T_verify=v['T_verify'],T_total=v['T_total'],
        t0_perf=p['t0_perf'],t_produce_perf=p['t_produce_perf'],t_verified_perf=v['t_verified_perf'],
        t0_unix=p['t0_unix'],t_produce_unix=p['t_produce_unix'],t_verified_unix=v['t_verified_unix'],
        within_cap=p['T_produce']<=l['cap_seconds'],cap_seconds=l['cap_seconds'],
        cap_excess_seconds=max(0.,p['T_produce']-l['cap_seconds']),total_exceeds_3600=v['T_total']>3600,
        main_clock='T_produce',measurement_policy='v2',producer_receipt_SHA=sha(d/'producer_receipt.json'),
        total_receipt_SHA=sha(d/'arm_total_receipt.json'),group_future_review_in_arm=False)

if __name__=='__main__':
    assert sys.argv[1]=='close-fee';close_fee(sys.argv[2])
