"""Round112 isolated identities, budgets and closed process receipts."""
from round103_common import ROOT, CMAKE, NINJA, sha, read, write, env
from round110_common import process_origin
from pathlib import Path
import json, os, subprocess, sys, time
OUT=ROOT/'results/unified_exact_round112'
BUILD=ROOT/'build/research/round112-paid-v1'
PE=BUILD/'ExactEBRP.exe'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
BASE='ded38c756a32a464bfa9800212da75778707d974'

def bindings():
    paths=[ROOT/'CMakeLists.txt']+sorted((ROOT/'src').rglob('*.cpp'))+sorted((ROOT/'src').glob('*.inc'))+sorted((ROOT/'include').rglob('*.hpp'))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths}

def budget():
    ls=list((OUT/'fees').glob('*/launch.json'));rs=[read(p.parent/'receipt.json') for p in ls if (p.parent/'receipt.json').exists()]
    starts=sum(read(p)['conservative_process_starts'] for p in ls)
    seconds=sum(r['outer_seconds_upper'] for r in rs)
    qs=sum(read(p)['conservative_process_starts'] for p in ls if read(p)['qualification'])
    qt=sum(r['outer_seconds_upper'] for r in rs if r['qualification'])
    return dict(paid_starts=starts,paid_outer_seconds=seconds,qualification_starts=qs,qualification_seconds=qt,
        remaining_starts=56-starts,remaining_outer_seconds=48000-seconds,
        unclosed=[str(p.parent.relative_to(ROOT)) for p in ls if not (p.parent/'receipt.json').exists()])

def check_identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA'] and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings']
    return p

def engineering(label,command,timeout=1800):
    d=OUT/'engineering'/label;d.mkdir(parents=True,exist_ok=False)
    command=list(map(str,command));tick=time.perf_counter();code=None
    write(d/'launch.json',dict(command=command,cwd=str(ROOT),engineering=True,native_starts=0,Optimize=0,started_unix=time.time()))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        child=subprocess.Popen(command,cwd=ROOT,env=env(),stdout=so,stderr=se)
        write(d/'process.json',dict(pid=child.pid,parent=os.getpid()))
        try:code=child.wait(timeout=timeout)
        finally:write(d/'receipt.json',dict(exit_code=code,seconds=time.perf_counter()-tick,engineering=True,native_starts=0,Optimize=0))
    print(json.dumps(read(d/'receipt.json')),flush=True)
    if code:raise RuntimeError((d/'stdout.log').read_text()[-3000:]+(d/'stderr.log').read_text()[-3000:])

if __name__=='__main__':engineering(sys.argv[1],sys.argv[2:])
