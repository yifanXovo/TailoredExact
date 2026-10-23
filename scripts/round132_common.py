"""Round132 paths, immutable frozen assets, and disjoint cost categories."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time, shutil

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
OUT=ROOT/'results/unified_exact_round132'
TEMP=WORK/'temp/round132'
BUILD=WORK/'build-cache/round132'
BASE='b97418ecc0b9f739232af484f999770c130ceb76'
SOURCE='7564a5415331b380e24d1ec06936dcfd56557e67'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
DOCUMENT_PYTHON=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')
E3=WORK/'build-cache/round130/ExactEBRP.exe'
PE_SHA='2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
EXPORTER=WORK/'build-cache/round130/Round130ExportE3.exe'
LIMITS=dict(C=32400,D=84000,qualification=3600,E=10800,C3=4800,repair=8400)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(*a,cwd=ROOT):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*map(str,a)],cwd=cwd)
def environment():
    TEMP.mkdir(parents=True,exist_ok=True)
    e=dict(os.environ,TEMP=str(TEMP),TMP=str(TEMP),PYTHONDONTWRITEBYTECODE='1')
    e['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+e.get('PATH','')
    return e
def frozen_identity():
    seal=read(ROOT/'results/unified_exact_round130/E3_frozen.json')
    assert sha(E3)==PE_SHA==seal['PE_SHA'] and sha(DLL)==DLL_SHA
    assert sha(EXPORTER)==seal['exporter_SHA']
    for n,h in seal['source_bindings'].items():assert sha(ROOT/n)==h,n
    return dict(PE=str(E3),PE_SHA=PE_SHA,DLL=str(DLL),DLL_SHA=DLL_SHA,
                exporter=str(EXPORTER),exporter_SHA=seal['exporter_SHA'],
                source_commit=SOURCE,source_bindings=seal['source_bindings'],production_compile=0)
def budget():
    by={k:0. for k in LIMITS};delivery=0.;unclosed=[]
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        rp=p.parent/'receipt.json'
        if not rp.exists():unclosed.append(p.parent.name);continue
        l,r=read(p),read(rp)
        if l['kind'] in by:by[l['kind']]+=r['G1_seconds']
        delivery+=r['separately_reported_seconds']
    return dict(G1_seconds=sum(by.values()),remaining_G1_seconds=144000-sum(by.values()),
                by_category=by,limits=LIMITS,separately_reported_seconds=delivery,unclosed=unclosed)
def metered(label,kind,args,reservation=0,timeout=None):
    before=budget();assert not before['unclosed'],before
    if kind in LIMITS:
        assert before['remaining_G1_seconds']>=reservation,before
        assert before['by_category'][kind]<LIMITS[kind],before
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    command=list(map(str,args));tick=time.perf_counter();start=time.time()
    write(d/'launch.json',dict(UTC=utc(),kind=kind,command=command,cwd=str(ROOT),budget_before=before))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        p=subprocess.Popen(command,cwd=ROOT,env=environment(),stdout=so,stderr=se)
        write(d/'PID.json',dict(pid=p.pid,parent_pid=os.getpid(),launched_unix=start,command=command))
        rc=p.wait(timeout=timeout)
    elapsed=time.perf_counter()-tick
    # Campaign children report disjoint post-production verification/reconstruction
    # segments. Their outer supervisor is counted once, excluding those segments.
    segments=OUT/'cost_segments'/label
    separate=sum(read(q)['seconds'] for q in segments.glob('*.json')) if segments.exists() else 0.
    assert 0<=separate<=elapsed
    charged=elapsed-separate if kind in LIMITS else 0.
    write(d/'receipt.json',dict(exit_code=rc,outer_seconds=elapsed,G1_seconds=charged,
        separately_reported_seconds=elapsed-charged,start_unix=start,end_unix=time.time(),
        exit_observed=True,nested_H_LP_MIP_not_added=True))
    print(json.dumps(dict(label=label,exit_code=rc,seconds=elapsed,budget=budget())),flush=True)
    if rc:print((d/'stderr.log').read_text(encoding='utf-8',errors='replace')[-4500:],flush=True)
    return rc
def bootstrap():
    OUT.mkdir(parents=True,exist_ok=True);assets=frozen_identity()
    task=Path('C:/Users/Administrator/Desktop/TailoredExact_Next_Round_Complete_Goal_v2.md')
    assert not (OUT/'goal.md').exists();shutil.copyfile(task,OUT/'goal.md')
    main=Path('E:/codes/ExactEBRP');dirty=[]
    for line in git('status','--porcelain','--untracked-files=no',cwd=main).decode().splitlines():
        n=line[3:];p=main/n
        dirty.append(dict(status=line[:2],path=n,SHA=sha(p) if p.is_file() else None,bytes=p.stat().st_size if p.is_file() else None))
    write(OUT/'user_dirty_baseline.json',dict(UTC=utc(),scope='three already tracked dirty paths only; no whole-tree byte claim',
        main_HEAD=git('rev-parse','HEAD',cwd=main).decode().strip(),paths=dirty))
    write(OUT/'initialization.json',dict(UTC=utc(),base=BASE,branch=git('branch','--show-current').decode().strip(),
        work_root=str(WORK),worktree=str(ROOT),applicable_AGENTS=[],prior_R132=False,active_solvers=[],
        PR193=dict(state='open',draft=True,merged=False,head=BASE),free_bytes=shutil.disk_usage(WORK).free,
        peak_increment_allowance_bytes=36*1024**3,peak_includes='raw + carriers + one recovery + build/doc intermediates',
        limits=LIMITS,source_task_SHA=sha(task),assets=assets,existing_trees_preserved=True))
    write(OUT/'E3_binding.json',assets)
    (OUT/'.gitignore').write_text('campaign/\nfees/\nqualification/references/\nresearch/\n',encoding='utf-8')
    (OUT/'RESUME.md').write_text('Round132 initialized on frozen R131. No H/LP/MIP started. Freeze source recipe and full D run table, then independent admission. All active PID/creation/argv and sealed arms must be checked before resume.\n',encoding='utf-8')
    print('R132 initialized; exact frozen E3/DLL/source hashes pass; no Optimize.')
if __name__=='__main__':
    if sys.argv[1]=='bootstrap':bootstrap()
    elif sys.argv[1]=='budget':print(json.dumps(budget()))
    elif sys.argv[1]=='meter':sys.exit(metered(sys.argv[2],sys.argv[3],sys.argv[4:]))
