"""Round106 exclusive receipts and finite process accounting. Imports solve nothing."""
from round103_common import ROOT, CMAKE, NINJA, sha, read, write, bindings, env
from pathlib import Path
import json, os, subprocess, sys, time

OUT = ROOT / 'results/unified_exact_round106'
BUILD = ROOT / 'build/research/round106-events-v1'
MANAGEMENT_PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
NUMERICAL_PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')

def budget():
    folders = list((OUT/'fees').glob('*/launch.json'))
    receipts = list((OUT/'fees').glob('*/receipt.json'))
    seconds = sum(read(p)['outer_seconds'] for p in receipts)
    starts = sum(read(p)['conservative_process_starts'] for p in folders)
    return dict(paid_starts=starts, paid_outer_seconds=seconds,
                remaining_starts=72-starts, remaining_outer_seconds=80000-seconds,
                unclosed=sorted(str(p.parent.relative_to(ROOT)) for p in folders
                               if not (p.parent/'receipt.json').exists()))

def receipt(label, command, cap=600, engineering=False, children=0):
    from round100_idle import ensure_idle
    ensure_idle()
    b = budget()
    assert not b['unclosed'], ('inspect unclosed paid processes before resume', b)
    if not engineering:
        assert children >= 0 and b['remaining_starts'] >= 1+children
        assert b['remaining_outer_seconds'] >= cap
    d = OUT / ('engineering' if engineering else 'fees') / label
    d.mkdir(parents=True, exist_ok=False)
    write(d/'launch.json', dict(command=list(map(str,command)), cap_seconds=cap,
        engineering=engineering, declared_nested_process_starts=children,
        conservative_process_starts=1+children, budget_before=b,
        source_bindings=bindings(),
        command_file_hashes={str(p):sha(p) for p in map(Path,map(str,command)) if p.is_file()},
        started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    tick=time.perf_counter(); code=None; reason='normal_return'
    with (d/'stdout.log').open('x') as so, (d/'stderr.log').open('x') as se:
        proc=subprocess.Popen(list(map(str,command)),cwd=ROOT,env=env(),stdout=so,stderr=se)
        write(d/'process.json',dict(pid=proc.pid,parent_pid=os.getpid()))
        try: code=proc.wait(timeout=cap)
        except subprocess.TimeoutExpired:
            reason='whole_process_timeout'
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=se,stderr=se)
            proc.wait()
    r=dict(exit_code=code,stop_reason=reason,outer_seconds=time.perf_counter()-tick,
           engineering=engineering,conservative_process_starts=1+children)
    write(d/'receipt.json',r); print(json.dumps(r),flush=True)
    if code!=0:
        raise RuntimeError(str(d)+': '+(d/'stdout.log').read_text()[-2000:]+
                           (d/'stderr.log').read_text()[-2000:])
    return r

if __name__=='__main__':
    label,cap,kind=sys.argv[1:4]
    args=sys.argv[4:];children=0
    if args and args[0].startswith('--children='):
        children=int(args.pop(0).split('=',1)[1])
    receipt(label,args,float(cap),kind=='engineering',children)
