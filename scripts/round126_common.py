"""Bounded R126 administration; no native work on import."""
from pathlib import Path
import ast, datetime, hashlib, json, os, shutil, subprocess, sys, time
import round122_common as inherited

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
MAIN=Path('E:/codes/ExactEBRP')
OUT=ROOT/'results/unified_exact_round126'
TEMP=WORK/'temp/round126'
EVIDENCE=WORK/'evidence/round126'
BASE='eeae1a009f809a272dcb4b659f5758ded9304155'
SOURCE=inherited.SOURCE
PE=inherited.PE; PE_SHA=inherited.PE_SHA
DLL=inherited.DLL; DLL_SHA=inherited.DLL_SHA
PYTHON=inherited.PYTHON
TOTAL_LIMIT=18000
QUAL_PLAN=600
QUAL_LIMIT=1200
METHODS=['P-GRB','M-B']
sha=inherited.sha; read=inherited.read; write=inherited.write; utc=inherited.utc
bindings=inherited.bindings

def git(*args,cwd=ROOT):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=cwd)

def workspace():
    assert ROOT.resolve().is_relative_to(WORK.resolve())
    for p in [OUT,TEMP,EVIDENCE]:
        p.mkdir(parents=True,exist_ok=True)
        for q in [p,*p.parents]:
            if q.exists(): assert not q.is_symlink() and not q.is_junction(),str(q)
    os.environ['TEMP']=str(TEMP); os.environ['TMP']=str(TEMP)
    return dict(main=str(MAIN),worktree=str(ROOT),raw=str(OUT/'campaign'),temporary=str(TEMP),
                archive=str(EVIDENCE),free_bytes=shutil.disk_usage(WORK).free)

def environment():
    workspace(); e=inherited.environment();e.update(TEMP=str(TEMP),TMP=str(TEMP),PYTHONDONTWRITEBYTECODE='1');return e

def helpers():
    pending=['round126_common','round126_prepare','round126_campaign','read_round126','round126_data',
             'round122_evidence','round121_campaign'];seen=set()
    while pending:
        name=pending.pop();p=ROOT/'scripts'/(name+'.py')
        if name in seen or not p.is_file(): continue
        seen.add(name)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules=[n.name for n in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending.extend(m for m in modules if m and (ROOT/'scripts'/(m+'.py')).is_file())
    return {'scripts/'+n+'.py':sha(ROOT/'scripts'/(n+'.py')) for n in sorted(seen)}

def identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings'] and len(p['source_bindings'])==216
    assert p['source_commit_before_native']==SOURCE
    return p

def budget():
    closed=[];unclosed=[]
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        if (p.parent/'receipt.json').exists():closed.append((read(p),read(p.parent/'receipt.json')))
        else:unclosed.append(p.parent.name)
    setup=read(OUT/'initialization.json').get('preledger_setup_charge_upper_seconds',0) if (OUT/'initialization.json').exists() else 0
    paid=setup+sum(r['outer_seconds_upper'] for l,r in closed)
    return dict(paid_outer_seconds_upper=paid,remaining_outer_seconds=TOTAL_LIMIT-paid,unclosed=unclosed,
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['kind']=='qualification'),
        actual_native_starts=sum(r.get('actual_native_starts',0) for l,r in closed),
        preledger_setup_charge_upper_seconds=setup,nested_native_seconds_added=False)

def initialize():
    w=workspace();assert git('rev-parse','HEAD').decode().strip()==BASE
    prior=read(ROOT/'results/unified_exact_round122/production_identity.json')
    assert sha(PE)==prior['production_PE_SHA']==PE_SHA and sha(DLL)==prior['DLL_SHA']==DLL_SHA
    assert bindings()==prior['source_bindings'] and len(bindings())==216
    dirty=git('status','--short','--untracked-files=no',cwd=MAIN).decode().splitlines()
    status=git('status','--short',cwd=MAIN)
    (EVIDENCE/'main_initial_status.txt').write_bytes(status)
    write(OUT/'production_identity.json',dict(prior,round=126,actual_base=BASE,production_PE_path=str(PE),
        original_PE_reused_in_place=True,source_commit_before_native=SOURCE,no_compilation=True,verified_UTC=utc()))
    write(OUT/'initialization.json',dict(UTC=utc(),base=BASE,remote='https://github.com/yifanXovo/TailoredExact.git',
        PR187=dict(state='open',draft=True,head=BASE,branch='codex/round125-self-contained-methods'),
        main_HEAD=git('rev-parse','HEAD',cwd=MAIN).decode().strip(),main_tracked_status=dirty,
        main_dirty_SHA={s[3:]:sha(MAIN/s[3:]) for s in dirty},full_initial_status_SHA=sha(EVIDENCE/'main_initial_status.txt'),
        applicable_AGENTS=[],no_existing_R126_branch_worktree_or_results=True,no_active_solver_at_preflight=True,
        workspace=w,preledger_setup_charge_upper_seconds=120,
        preledger_charge_explanation='Conservative setup allowance for the already completed shell/git inspections and sparse checkout; not CPU time and not solver time. Individual command tool clocks, rather than elapsed conversation time, bound these brief calls.',
        new_native_starts=0,Optimize=0,production_compilations=0))
    write(OUT/'workspace_capacity.json',dict(free_bytes=w['free_bytes'],minimum_group_start_free_bytes=16*1024**3,
        planning_bytes=dict(authoritative_raw=6*1024**3,pack_temporary=2*1024**3,archive=2*1024**3,one_restore=6*1024**3),
        peak_increment_allowance_bytes=16*1024**3,one_authoritative_raw=True,no_PE_DLL_copy=True))
    print(json.dumps(dict(initialized=True,production_bindings=216,free_bytes=w['free_bytes'])))

if __name__=='__main__':initialize()
