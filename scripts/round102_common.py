"""Exclusive Round102 management. Import starts no solver."""
from round101_common import ROOT, CMAKE, NINJA, sha, read, write, bindings, env
import subprocess, time, json
OUT = ROOT/'results/unified_exact_round102'
BUILD = ROOT/'build/research/round102-service-v1'
def receipt(label, command, cap=300, calls=0, engineering=False):
    d=OUT/('engineering' if engineering else 'fees')/label
    d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=list(map(str,command)),cap_seconds=cap,
        maximum_Optimize_calls=calls,source_hashes=bindings()))
    tick=time.perf_counter();code=None;reason='normal_return'
    try:
        with (d/'stdout.log').open('x') as so,(d/'stderr.log').open('x') as se:
            p=subprocess.run(list(map(str,command)),cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=cap)
        code=p.returncode
    except subprocess.TimeoutExpired:reason='whole_process_timeout'
    r=dict(exit_code=code,stop_reason=reason,outer_seconds=time.perf_counter()-tick,
        maximum_Optimize_calls=calls,engineering=engineering)
    write(d/'receipt.json',r);print(json.dumps(r),flush=True)
    if code!=0:raise RuntimeError(str(d)+' '+(d/'stderr.log').read_text()[-3000:])
    return r
