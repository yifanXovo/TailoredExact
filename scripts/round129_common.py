"""R129 finite task accounting; imported code never starts an optimizer."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time, shutil

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
PREVIOUS=WORK/'worktrees/round127'
OUT=ROOT/'results/unified_exact_round129'
TEMP=WORK/'temp/round129'
EVIDENCE=WORK/'evidence/round129'
BUILD=WORK/'build-cache/round128'
BASE='cc70757304a2019d95f0f934aa5520d0caa946c6'
SOURCE='355eefd2be3fe5651195681faf7b3a63ee4032f8'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')
E0=Path('C:/Users/Administrator/.codex/worktrees/round121-frozen-d1-confirmation/ExactEBRP/build/research/round120/ExactEBRP.exe')
E0_SHA='5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
E1=WORK/'build-cache/round127/ExactEBRP.exe'
E1_SHA='d668236e9396b2e12f02bb65d9819b98762d2a35aad1b186d352d234dae756c9'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
ARCHIVE=Path('C:/Users/Administrator/.codex/worktrees/round120-native-proof-disjunction/ExactEBRP/build/research/round120/libexact_ebrp_core.a')
E2=BUILD/'ExactEBRP.exe'
TOTAL_LIMIT=39600
QUAL_LIMIT=1800

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
    init=read(OUT/'initialization.json') if (OUT/'initialization.json').exists() else {}
    paid=init.get('preledger_outer_upper_seconds',0)+sum(r['outer_seconds'] for l,r in closed)
    return dict(paid_outer_seconds=paid,remaining_outer_seconds=TOTAL_LIMIT-paid,unclosed=unclosed,
        by_kind={k:sum(r['outer_seconds'] for l,r in closed if l['kind']==k) for k in sorted({l['kind'] for l,r in closed})},
        nested_H_LP_MIP_seconds_added=False)
def metered(label,kind,args,reservation=0,timeout=None):
    b=budget();assert not b['unclosed'],b
    assert b['remaining_outer_seconds']>=reservation,b
    if kind in ['qualification','build']:
        assert sum(b['by_kind'].get(k,0) for k in ['qualification','build'])<QUAL_LIMIT,b
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter();started=time.time()
    write(d/'launch.json',dict(UTC=utc(),kind=kind,command=list(map(str,args)),cwd=str(ROOT),budget_before=b,reservation=reservation))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        p=subprocess.Popen(list(map(str,args)),cwd=ROOT,env=environment(),stdout=so,stderr=se)
        write(d/'PID.json',dict(pid=p.pid,parent_pid=os.getpid(),launched_unix=started,command=list(map(str,args))))
        rc=p.wait(timeout=timeout)
    elapsed=time.perf_counter()-tick
    write(d/'receipt.json',dict(exit_code=rc,outer_seconds=elapsed,start_unix=started,end_unix=time.time(),exit_observed=True,nested_seconds_added=False))
    print(json.dumps(dict(label=label,exit_code=rc,outer_seconds=elapsed,budget=budget())),flush=True)
    if rc:print((d/'stderr.log').read_text(encoding='utf-8',errors='replace')[-5000:],flush=True)
    return rc
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='meter':sys.exit(metered(sys.argv[2],sys.argv[3],sys.argv[4:]))
    else:print(json.dumps(budget()))

E2_SHA="ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa"
EXPORTER=BUILD/"Round128ExportE2.exe"
EXPORTER_SHA="cc90b84bab79636098819e803c658efcc23ead0392bd2c641e4a9dd158b31277"
def identity():
    assert sha(E2)==E2_SHA and sha(DLL)==DLL_SHA and sha(EXPORTER)==EXPORTER_SHA
    assert source_bindings()==read(ROOT/"results/unified_exact_round128/E2_frozen.json")["source_bindings"]
    return dict(PE=str(E2),PE_SHA=E2_SHA,DLL=str(DLL),DLL_SHA=DLL_SHA,exporter=str(EXPORTER),exporter_SHA=EXPORTER_SHA,production_compilations=0)
