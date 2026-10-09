"""Round109 paths and exclusive receipts. Import never launches native work."""
from round103_common import ROOT, CMAKE, NINJA, sha, read, write, bindings, env
from pathlib import Path
import json, os, subprocess, sys, time

OUT=ROOT/'results/unified_exact_round109'
BUILD=ROOT/'build/research/round109-inherited-mb-v1'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
BASE='d11c94d81e6a2c5dcd64dad8c54b390f3cb4a027'
PE_SHA='4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0'
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'

def budget():
    launches=list((OUT/'fees').glob('*/launch.json'))
    receipts=list((OUT/'fees').glob('*/receipt.json'))
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    seconds=sum(read(p)['outer_seconds'] for p in receipts)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=72-starts,
        remaining_outer_seconds=100000-seconds,
        unclosed=[p.parent.relative_to(ROOT).as_posix() for p in launches if not (p.parent/'receipt.json').exists()])

def check_identity():
    assert sha(BUILD/'ExactEBRP.exe')==PE_SHA and sha(DLL)==DLL_SHA
    old=read(ROOT/'results/unified_exact_round108/candidate_identity.json')
    assert bindings()==old['source_bindings'],'production source drift'
    return old

def engineering(label,command,timeout=1200):
    from round100_idle import ensure_idle
    ensure_idle()
    directory=OUT/'engineering'/label;directory.mkdir(parents=True,exist_ok=False)
    snapshots=[]
    for source in sorted((ROOT/'scripts').glob('round109*.py')):
        target=directory/'source_snapshot/scripts'/source.name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes());snapshots.append(dict(path=source.relative_to(ROOT).as_posix(),SHA=sha(source)))
    for item in command:
        p=Path(str(item))
        if p.is_file() and p.suffix in ('.py','.cpp','.txt'):
            target=directory/'source_snapshot/command'/p.name;target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():target.write_bytes(p.read_bytes())
    command=list(map(str,command));write(directory/'launch.json',dict(command=command,cwd=str(ROOT),sources=snapshots,
        started_unix=time.time(),engineering=True,conservative_solver_starts=0))
    tick=time.perf_counter()
    with (directory/'stdout.log').open('xb') as so,(directory/'stderr.log').open('xb') as se:
        child=subprocess.Popen(command,cwd=ROOT,env=env(),stdout=so,stderr=se)
        write(directory/'process.json',dict(pid=child.pid,parent_pid=os.getpid()))
        try:code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:child.kill();code=child.wait()
    value=dict(exit_code=code,seconds=time.perf_counter()-tick,engineering=True,conservative_solver_starts=0,
        stdout_SHA=sha(directory/'stdout.log'),stderr_SHA=sha(directory/'stderr.log'),sources=snapshots)
    write(directory/'receipt.json',value);print(json.dumps(value),flush=True)
    if code:raise RuntimeError(str(directory)+': '+(directory/'stderr.log').read_text()[-3000:])
    return value

if __name__=='__main__':engineering(sys.argv[1],sys.argv[2:])
