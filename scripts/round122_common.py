"""Round122 fixed workspace, frozen production and explicit outer accounting."""
from pathlib import Path
import ast, datetime, hashlib, json, os, shutil, subprocess, sys, time
import round120_common as inherited

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
MAIN=Path('E:/codes/ExactEBRP')
OUT=ROOT/'results/unified_exact_round122'
EVIDENCE=WORK/'evidence/round122'
TEMP=WORK/'temp/round122'
BASE='65c5aaa56583bcddf9baeae7392bd94baaed9396'
SOURCE='355eefd2be3fe5651195681faf7b3a63ee4032f8'
PE=Path('C:/Users/Administrator/.codex/worktrees/round121-frozen-d1-confirmation/ExactEBRP/build/research/round120/ExactEBRP.exe')
PE_SHA='5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
sha=inherited.sha; read=inherited.read; write=inherited.write; utc=inherited.utc; bindings=inherited.bindings
TOTAL_LIMIT=100000
QUAL_PLAN=3000
QUAL_LIMIT=6000
METHODS=['P-GRB','ENS-C','M-B','MB-D1']
PAIRS=[('MB-D1','P-GRB'),('M-B','P-GRB'),('ENS-C','P-GRB'),('MB-D1','M-B'),('MB-D1','ENS-C'),('M-B','ENS-C')]

def workspace():
    assert ROOT.resolve().is_relative_to(WORK.resolve()) and str(WORK.resolve()).lower()=='e:\\codes\\exactebrp-work'
    for p in [WORK,ROOT,OUT,TEMP,EVIDENCE]:
        p.mkdir(parents=True,exist_ok=True)
        for q in [p,*p.parents]:
            if q.exists():assert not q.is_junction() and not q.is_symlink(),str(q)
    # Supervisor inherits os.environ directly: this must be process-scoped.
    os.environ['TEMP']=str(TEMP);os.environ['TMP']=str(TEMP)
    return dict(main=str(MAIN),execution=str(ROOT),common_git_dir=str((MAIN/'.git').resolve()),raw=str(OUT/'campaign'),
        temporary=str(TEMP),archive=str(EVIDENCE),restore_parent=str(WORK/'restore'),volume_free_bytes=shutil.disk_usage(WORK).free,
        TEMP=os.environ['TEMP'],TMP=os.environ['TMP'],no_reparse_redirection=True)

def environment():
    workspace();e=inherited.environment();e['TEMP']=str(TEMP);e['TMP']=str(TEMP);return e

def helpers():
    names=set(inherited.helper_paths());pending=['round122_common','round122_data','round122_prepare','round122_evidence',
        'round122_campaign','read_round122','qualify_round122','round122_decision','round122_runner']
    seen=set()
    while pending:
        name=pending.pop();p=ROOT/'scripts'/(name+'.py')
        if name in seen or not p.is_file():continue
        seen.add(name);names.add(p.relative_to(ROOT).as_posix())
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending.extend(m for m in modules if m and (ROOT/'scripts'/(m+'.py')).is_file())
    names.add('scripts/round122_reference.cpp')
    return {n:sha(ROOT/n) for n in sorted(names)}

def identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings'] and p['source_commit_before_native']==SOURCE
    return p

def budget():
    launches=sorted((OUT/'fees').glob('*/launch.json'));closed=[];starts=0;unknown=[]
    for path in launches:
        l=read(path);r=read(path.parent/'receipt.json') if (path.parent/'receipt.json').exists() else None
        if r:closed.append((l,r));starts+=r['conservative_process_starts']
        else:unknown.append(path.parent.name)
    seconds=sum(r['outer_seconds_upper'] for l,r in closed)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_outer_seconds=TOTAL_LIMIT-seconds,
        qualification_starts=sum(r['conservative_process_starts'] for l,r in closed if l['qualification']),
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),unclosed=unknown,
        startup_count_is_observed_not_a_hard_ceiling=True,native_components_not_added_twice=True)

def fee_begin(label,children,cap,qualification,reservation):
    from round115_common import process_origin
    workspace();tick,creation=process_origin();b=budget();d=OUT/'fees'/label
    assert not d.exists() and not b['unclosed'],b
    assert b['remaining_outer_seconds']>=cap+reservation['seconds']
    if qualification:assert b['qualification_seconds']+cap<=QUAL_LIMIT
    d.mkdir(parents=True)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),wrapper_pid=os.getpid(),wrapper_creation_unix=creation,
        conservative_process_starts=children+1,declared_native_children=children,qualification=qualification,outer_cap=cap,
        budget_before=b,remaining_fixed_obligations=reservation,frozen_UTC=utc(),workspace=workspace(),
        count_is_prospective_reservation_not_claim_of_actual_launch=True))
    return d,tick

def child_states(launches):
    states=[]
    for l in launches:
        d=Path(l['destination']);p=d/'child_process_origin.json'
        state='actual_started' if p.is_file() else 'unknown_if_started' if (d/'launch.json').is_file() else 'not_started'
        states.append(dict(id=l['id'],arm=l['arm'],seed=l['seed'],state=state,
            PID_receipt_SHA=sha(p) if p.is_file() else None))
    return states

def fee_pending(d,tick,qualification,code,actual,states=None):
    uncertain=sum(s['state']=='unknown_if_started' for s in states or [])
    if states is not None:actual=sum(s['state']=='actual_started' for s in states)
    write(d/'pending_exit_receipt.json',dict(exit_code=code,outer_seconds_lower=time.perf_counter()-tick,qualification=qualification,
        actual_native_children=actual,uncertain_native_children=uncertain,child_states=states,
        wrapper_pid=os.getpid(),conservative_process_starts=actual+uncertain+1,
        necessary_trailer_complete=True,nested_native_seconds_added=False))
    print(json.dumps(dict(wrapper_pending_exit=str(d),exit_code=code)),flush=True)

def initialize():
    w=workspace();old=read(ROOT/'results/unified_exact_round121/production_identity.json')
    assert sha(PE)==old['production_PE_SHA']==PE_SHA and sha(DLL)==old['DLL_SHA']==DLL_SHA
    assert bindings()==old['source_bindings']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==BASE
    write(OUT/'production_identity.json',dict(old,round=122,actual_base=BASE,production_PE_path=str(PE),
        source_commit_before_native=SOURCE,original_PE_reused_in_place=True,copied_original_PE_without_recompile=False,
        Seed='per preregistered group 0 or 1',verified_UTC=utc()))
    dirty=subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=MAIN).decode().splitlines()
    write(OUT/'initialization_receipt.json',dict(workspace=w,base=BASE,main_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=MAIN).decode().strip(),
        main_tracked_status=dirty,main_dirty_SHA={s[3:]:sha(MAIN/s[3:]) for s in dirty},app_calling_cwd=str(MAIN),
        app_global_worktree_setting_not_modified=True,app_setting_not_claimed=True,no_prior_R122_branch_or_execution_found=True,
        applicable_AGENTS_found=[],UTC=utc(),native_starts=0,Optimize=0))
    print(json.dumps(dict(PE_SHA=sha(PE),DLL_SHA=sha(DLL),source_files=len(bindings()),workspace=w)))

if __name__=='__main__':initialize()
