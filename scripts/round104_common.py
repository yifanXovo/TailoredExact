"""Exclusive, self-paid R104 receipts. Import never starts optimization."""
from round103_common import ROOT, CMAKE, NINJA, PYTHON, sha, read, write, bindings, env
import subprocess, time, json, os, sys
from pathlib import Path
OUT = ROOT / 'results/unified_exact_round104'
BUILD = ROOT / 'build/research/round104-compression-v1'
PRIOR = ROOT / 'results/unified_exact_round103'

def receipt(label, command, cap=600, engineering=False):
    from round100_idle import ensure_idle
    ensure_idle()
    completed = list((OUT / 'fees').glob('*/receipt.json'))
    launches = list((OUT / 'fees').glob('*/launch.json'))
    seconds = sum(read(p)['outer_seconds'] for p in completed)
    if not engineering:
        assert len(launches) < 72 and seconds + cap <= 80000
        assert len(completed) == len(launches), 'unclosed paid process: inspect before resuming'
    d = OUT / ('engineering' if engineering else 'fees') / label
    d.mkdir(parents=True, exist_ok=False)
    write(d/'launch.json', dict(command=list(map(str, command)), cap_seconds=cap,
        engineering=engineering, source_bindings=bindings(),
        helper_bindings={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'scripts').glob('round104*.py')},
        command_file_hashes={str(p):sha(p) for p in map(Path,map(str,command)) if p.is_file()},
        started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    tick=time.perf_counter(); code=None; reason='normal_return'
    with (d/'stdout.log').open('x') as so, (d/'stderr.log').open('x') as se:
        p=subprocess.Popen(list(map(str,command)),cwd=ROOT,env=env(),stdout=so,stderr=se)
        write(d/'process.json',dict(pid=p.pid,parent_pid=os.getpid()))
        try: code=p.wait(timeout=cap)
        except subprocess.TimeoutExpired:
            reason='whole_process_timeout'
            subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=se,stderr=se)
            p.wait()
    r=dict(exit_code=code,stop_reason=reason,outer_seconds=time.perf_counter()-tick,engineering=engineering)
    write(d/'receipt.json',r); print(json.dumps(r),flush=True)
    if code!=0: raise RuntimeError(str(d)+' '+(d/'stderr.log').read_text()[-3000:])
    return r

if __name__=='__main__':
    receipt(sys.argv[1],sys.argv[4:],float(sys.argv[2]),sys.argv[3]=='engineering')
