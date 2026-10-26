"""Round110 exclusive identities/receipts; importing never launches native work."""
from round103_common import ROOT, CMAKE, NINJA, sha, read, write, bindings, env
from pathlib import Path
import ctypes, json, os, subprocess, sys, time

OUT = ROOT/'results/unified_exact_round110'
BUILD = ROOT/'build/research/round110-entry-v1'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
BASE = '8977da23a0be50da0ab2fceb69ad3ee04e040855'
OLD_PE_SHA = '4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0'
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'

def budget():
    launches=list((OUT/'fees').glob('*/launch.json'))
    receipts=list((OUT/'fees').glob('*/receipt.json'))
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    seconds=sum(read(p)['outer_seconds'] for p in receipts)
    qstarts=sum(read(p)['conservative_process_starts'] for p in launches if read(p).get('qualification'))
    qseconds=sum(read(p)['outer_seconds'] for p in receipts if read(p).get('qualification'))
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=96-starts,
        remaining_outer_seconds=110000-seconds,qualification_starts=qstarts,qualification_seconds=qseconds,
        unclosed=[p.parent.relative_to(ROOT).as_posix() for p in launches if not (p.parent/'receipt.json').exists()])

def process_origin():
    class FileTime(ctypes.Structure): _fields_=[('low',ctypes.c_uint32),('high',ctypes.c_uint32)]
    created,ended,kernel,user=FileTime(),FileTime(),FileTime(),FileTime()
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.GetCurrentProcess.restype=ctypes.c_void_p
    assert api.GetProcessTimes(ctypes.c_void_p(api.GetCurrentProcess()),ctypes.byref(created),ctypes.byref(ended),ctypes.byref(kernel),ctypes.byref(user))
    unix=((created.high<<32)+created.low)/10000000-11644473600
    return time.perf_counter()-(time.time()-unix),unix

def check_identity():
    identity=read(OUT/'production_identity.json')
    assert sha(BUILD/'ExactEBRP.exe')==identity['production_PE_SHA'] and sha(DLL)==DLL_SHA
    assert bindings()==identity['source_bindings'], 'production source drift'
    return identity

def engineering(label,command,timeout=1800):
    from round100_idle import ensure_idle
    ensure_idle()
    d=OUT/'engineering'/label;d.mkdir(parents=True,exist_ok=False)
    command=list(map(str,command));sources={}
    for source in sorted((ROOT/'scripts').glob('round110*')):
        if source.is_file():
            target=d/'source_snapshot/scripts'/source.name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.read_bytes());sources[source.relative_to(ROOT).as_posix()]=sha(source)
    for item in command:
        p=Path(item)
        if p.is_file() and p.suffix in ['.py','.cpp','.txt','.inc']:
            target=d/'source_snapshot/command'/p.name;target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists(): target.write_bytes(p.read_bytes())
    write(d/'launch.json',dict(command=command,cwd=str(ROOT),sources=sources,started_unix=time.time(),engineering=True,conservative_solver_starts=0))
    tick=time.perf_counter();code=None
    try:
        with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
            child=subprocess.Popen(command,cwd=ROOT,env=env(),stdout=so,stderr=se)
            write(d/'process.json',dict(pid=child.pid,parent_pid=os.getpid()))
            code=child.wait(timeout=timeout)
    finally:
        write(d/'receipt.json',dict(exit_code=code,seconds=time.perf_counter()-tick,engineering=True,
            conservative_solver_starts=0,stdout_SHA=sha(d/'stdout.log'),stderr_SHA=sha(d/'stderr.log'),sources=sources))
    print(json.dumps(read(d/'receipt.json')),flush=True)
    if code: raise RuntimeError((d/'stderr.log').read_text()[-2500:])

if __name__=='__main__': engineering(sys.argv[1],sys.argv[2:])
