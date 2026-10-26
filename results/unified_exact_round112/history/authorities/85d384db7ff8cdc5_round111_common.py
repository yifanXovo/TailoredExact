"""Exclusive Round111 paths and engineering receipts. No native launch on import."""
from round103_common import ROOT, sha, read, write, bindings, env
from round110_common import process_origin
from pathlib import Path
import json, os, subprocess, sys, time

OUT = ROOT/'results/unified_exact_round111'
OLD_ROOT = Path('E:/codes/ExactEBRP-round110')
OLD = 'results/unified_exact_round110'
BASE = '13ed7eeb83b647f585837638ed9158b84f274d66'
SCIENCE = 'c4efe042bc6654ccd2e14b7e0d65c904a15d3390'
PE_SHA = 'c0384284aefd5aa2acc5d885ef37b0cfad6f93d083a5feb9ee693c41a786b411'
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
PE = ROOT/'build/research/round111-inherited/ExactEBRP.exe'
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')

def check_identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA and sha(DLL)==DLL_SHA
    assert bindings()==p['source_bindings'] and len(bindings())==205
    return p

def budget():
    launches=list((OUT/'fees').glob('*/launch.json'))
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    def charge(p):
        actual=read(p.parent/'receipt.json')['outer_seconds']
        correction=p.parent/'outer_accounting_interval.json'
        if correction.exists():
            value=read(correction)
            assert value['original_outer_seconds']==actual
            lower,upper=value['outer_seconds_interval']
            assert lower==actual and upper>=lower and value['budget_charge_seconds']==upper
            return upper
        return actual
    seconds=sum(charge(p) for p in launches if (p.parent/'receipt.json').exists())
    q=[p for p in launches if read(p)['qualification'] or
        ((p.parent/'charge_classification.json').exists() and read(p.parent/'charge_classification.json')['qualification'])]
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=24-starts,
        remaining_outer_seconds=18000-seconds,qualification_starts=sum(read(p)['conservative_process_starts'] for p in q),
        qualification_seconds=sum(charge(p) for p in q if (p.parent/'receipt.json').exists()),
        unclosed=[p.parent.relative_to(ROOT).as_posix() for p in launches if not (p.parent/'receipt.json').exists()])

def engineering(label,command,cwd=None,timeout=1800):
    d=OUT/'engineering'/label;d.mkdir(parents=True,exist_ok=False)
    command=list(map(str,command));cwd=Path(cwd or ROOT).resolve()
    sources={}
    for source in sorted((ROOT/'scripts').glob('round111*.py')):
        target=d/'source_snapshot/scripts'/source.name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes());sources[source.relative_to(ROOT).as_posix()]=sha(source)
    write(d/'launch.json',dict(command=command,cwd=str(cwd),sources=sources,started_unix=time.time(),
        engineering=True,native_processes=0,Optimize=0))
    tick=time.perf_counter();code=None
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        child=subprocess.Popen(command,cwd=cwd,env=env(),stdout=so,stderr=se)
        write(d/'process.json',dict(pid=child.pid,parent_pid=os.getpid()))
        try:code=child.wait(timeout=timeout)
        finally:write(d/'receipt.json',dict(exit_code=code,seconds=time.perf_counter()-tick,engineering=True,
            native_processes=0,Optimize=0,stdout_SHA=sha(d/'stdout.log'),stderr_SHA=sha(d/'stderr.log'),sources=sources))
    print(json.dumps(read(d/'receipt.json')),flush=True)
    if code:raise RuntimeError((d/'stderr.log').read_text(encoding='utf-8')[-3000:])

if __name__=='__main__':engineering(sys.argv[1],sys.argv[2:])
