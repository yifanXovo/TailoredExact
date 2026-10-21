"""R127 v3 identities and non-overlapping outer process accounting.

Imports never start a solver. Existing production and user files are read only.
"""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time, shutil

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
OUT=ROOT/'results/unified_exact_round127'
TEMP=WORK/'temp/round127'
EVIDENCE=WORK/'evidence/round127'
BUILD=WORK/'build-cache/round127'
BASE='473594a56ae9f1730899111375b3210f437adec2'
SOURCE='355eefd2be3fe5651195681faf7b3a63ee4032f8'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')
E0=Path('C:/Users/Administrator/.codex/worktrees/round121-frozen-d1-confirmation/ExactEBRP/build/research/round120/ExactEBRP.exe')
E0_SHA='5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
ARCHIVE=Path('C:/Users/Administrator/.codex/worktrees/round120-native-proof-disjunction/ExactEBRP/build/research/round120/libexact_ebrp_core.a')
E1=BUILD/'ExactEBRP.exe'
TOTAL_LIMIT=54000
QUAL_LIMIT=5400

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(*args,cwd=ROOT):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=cwd)
def environment():
    TEMP.mkdir(parents=True,exist_ok=True)
    e=dict(os.environ,TEMP=str(TEMP),TMP=str(TEMP),PYTHONDONTWRITEBYTECODE='1')
    e['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+e.get('PATH','')
    return e
def source_bindings():
    names=[ROOT/'CMakeLists.txt']
    names += [p for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ['.cpp','.hpp','.h','.inc']]
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(names)}
def budget():
    closed=[];unclosed=[]
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        if (p.parent/'receipt.json').exists():closed.append((read(p),read(p.parent/'receipt.json')))
        else:unclosed.append(p.parent.name)
    setup=read(OUT/'initialization.json').get('preledger_outer_upper_seconds',0) if (OUT/'initialization.json').exists() else 0
    paid=setup+sum(r['outer_seconds'] for l,r in closed)
    return dict(paid_outer_seconds=paid,remaining_outer_seconds=TOTAL_LIMIT-paid,unclosed=unclosed,
        by_kind={k:sum(r['outer_seconds'] for l,r in closed if l['kind']==k) for k in sorted({l['kind'] for l,r in closed})},
        nested_H_LP_MIP_seconds_added=False)
def metered(label,kind,args,reservation=0,timeout=None):
    """Meter one child lifetime; a campaign child contains its serial arms once."""
    b=budget();assert not b['unclosed'],b
    assert b['remaining_outer_seconds']>=reservation,b
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter();started=time.time()
    write(d/'launch.json',dict(UTC=utc(),kind=kind,command=list(map(str,args)),cwd=str(ROOT),budget_before=b,reservation=reservation))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        p=subprocess.Popen(list(map(str,args)),cwd=ROOT,env=environment(),stdout=so,stderr=se)
        write(d/'PID.json',dict(pid=p.pid,parent_pid=os.getpid(),launched_unix=started,command=list(map(str,args))))
        rc=p.wait(timeout=timeout)
    elapsed=time.perf_counter()-tick
    write(d/'receipt.json',dict(exit_code=rc,outer_seconds=elapsed,start_unix=started,end_unix=time.time(),
        exit_observed=True,nested_seconds_added=False))
    print(json.dumps(dict(label=label,exit_code=rc,outer_seconds=elapsed,budget=budget())),flush=True)
    if rc:print((d/'stderr.log').read_text(encoding='utf-8',errors='replace')[-5000:],flush=True)
    return rc
def initialize():
    assert git('rev-parse','HEAD').decode().strip()==BASE
    prior=read(ROOT/'results/unified_exact_round126/production_identity.json')
    assert sha(E0)==E0_SHA==prior['production_PE_SHA'] and sha(DLL)==DLL_SHA
    assert source_bindings()==prior['source_bindings']
    assert sha(COMPILER)==prior['compiler_SHA']
    for p in [OUT,TEMP,EVIDENCE,BUILD]:
        p.mkdir(parents=True,exist_ok=True)
        assert p.resolve().is_relative_to(WORK.resolve())
    write(OUT/'initialization.json',dict(UTC=utc(),base=BASE,remote='https://github.com/yifanXovo/TailoredExact.git',
        PR188=dict(state='OPEN',isDraft=True,head=BASE,base='codex/round125-self-contained-methods'),
        original_source=SOURCE,E0_path=str(E0),E0_SHA=sha(E0),DLL_path=str(DLL),DLL_SHA=sha(DLL),
        compiler=str(COMPILER),compiler_SHA=sha(COMPILER),frozen_core_archive=str(ARCHIVE),frozen_core_archive_SHA=sha(ARCHIVE),
        applicable_AGENTS=[],initially_active_solvers=[],existing_R127_science=False,
        main_dirty_snapshot=str(EVIDENCE/'main_initial_status.txt'),main_dirty_snapshot_SHA=sha(EVIDENCE/'main_initial_status.txt'),
        free_bytes=shutil.disk_usage(WORK).free,peak_increment_allowance_bytes=24*1024**3,
        preledger_outer_upper_seconds=120,
        preledger_explanation='Conservative upper charge for brief preledger read-only tool calls, fetch and sparse linked checkout. Conversation/analysis time is not machine execution cost; all subsequent substantial child tasks are individually metered.'))
    write(OUT/'E0_identity.json',prior)
    print(json.dumps(dict(initialized=True,E0=E0_SHA,source_files=len(prior['source_bindings']),budget=budget())))

if __name__=='__main__':
    if sys.argv[1]=='initialize':initialize()
    elif sys.argv[1]=='meter':sys.exit(metered(sys.argv[2],sys.argv[3],sys.argv[4:]))
    else:print(json.dumps(budget()))
