"""Round123 fixed E workspace and frozen production identities; no algorithm changes."""
from pathlib import Path
import ast, datetime, hashlib, json, os, shutil, subprocess, sys, time
import round120_common as old

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
MAIN=Path('E:/codes/ExactEBRP')
OUT=ROOT/'results/unified_exact_round123'
TEMP=WORK/'temp/round123'
EVIDENCE=WORK/'evidence/round123'
BASE='f3363d9ddede2725496e4a3e0466bbf4d1cec089'
SOURCE='355eefd2be3fe5651195681faf7b3a63ee4032f8'
PE=Path('C:/Users/Administrator/.codex/worktrees/round121-frozen-d1-confirmation/ExactEBRP/build/research/round120/ExactEBRP.exe')
PE_SHA='5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
TOTAL_LIMIT=70000
QUAL_PLAN=2000
QUAL_LIMIT=4000
METHODS=['P-GRB','M-B','ENS-C']
PAIRS=[('M-B','P-GRB'),('ENS-C','P-GRB'),('M-B','ENS-C')]
sha=old.sha; read=old.read; write=old.write; utc=old.utc; bindings=old.bindings

def workspace():
    assert ROOT.resolve().is_relative_to(WORK.resolve())
    for p in [WORK,ROOT,OUT,TEMP,EVIDENCE]:
        p.mkdir(parents=True,exist_ok=True)
        for q in [p,*p.parents]:
            if q.exists(): assert not q.is_junction() and not q.is_symlink(),str(q)
    os.environ['TEMP']=str(TEMP); os.environ['TMP']=str(TEMP)
    return dict(main=str(MAIN),execution=str(ROOT),common_git_dir=str((MAIN/'.git').resolve()),
        raw=str(OUT/'campaign'),temporary=str(TEMP),archive=str(EVIDENCE),
        restore_parent=str(WORK/'restore'),volume_free_bytes=shutil.disk_usage(WORK).free,
        TEMP=os.environ['TEMP'],TMP=os.environ['TMP'],no_reparse_redirection=True)

def environment():
    workspace(); e=old.environment(); e['TEMP']=str(TEMP); e['TMP']=str(TEMP); return e

def identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings'] and len(bindings())==216
    assert p['source_commit_before_native']==SOURCE
    return p

def helpers():
    names=set(read(OUT/'inherited_helper_names.json'))
    names.update('scripts/'+n for n in ['round123_common.py','round123_prepare.py','round123_evidence.py','round123_runner.py'])
    return {n:sha(ROOT/n) for n in sorted(names)}

def budget():
    closed=[]; unknown=[]
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        if (p.parent/'receipt.json').exists(): closed.append((read(p),read(p.parent/'receipt.json')))
        else: unknown.append(p.parent.name)
    seconds=sum(r['outer_seconds_upper'] for l,r in closed)
    return dict(paid_outer_seconds=seconds,remaining_outer_seconds=TOTAL_LIMIT-seconds,
        qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        paid_starts=sum(r['conservative_process_starts'] for l,r in closed),
        additional_controllers=sum(r.get('controller_process_count',0) for l,r in closed),unclosed=unknown,
        start_count_is_observed_not_a_hard_gate=True,native_seconds_not_added_twice=True)

def fee_begin(label,qualification,reserve):
    from round115_common import process_origin
    tick,birth=process_origin(); b=budget(); d=OUT/'fees'/label
    assert not d.exists() and not b['unclosed'],b
    assert b['remaining_outer_seconds']>=reserve,b
    if qualification: assert b['qualification_seconds']<QUAL_LIMIT
    d.mkdir(parents=True)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),wrapper_pid=os.getpid(),
        wrapper_creation_unix=birth,qualification=qualification,remaining_obligation_reserve=reserve,
        budget_before=b,UTC=utc(),workspace=workspace()))
    return d,tick

def fee_pending(d,tick,code,launches):
    states=[]
    for l in launches:
        p=Path(l['destination']); birth=p/'child_process_origin.json'
        state='actual_started' if birth.exists() else 'unknown_if_started' if (p/'launch.json').exists() else 'not_started'
        states.append(dict(id=l['id'],arm=l['arm'],state=state,
            child_birth_SHA=sha(birth) if birth.exists() else None))
    actual=sum(s['state']=='actual_started' for s in states)
    uncertain=sum(s['state']=='unknown_if_started' for s in states)
    write(d/'pending_exit_receipt.json',dict(exit_code=code,outer_seconds_lower=time.perf_counter()-tick,
        actual_native_children=actual,uncertain_native_children=uncertain,child_states=states,
        conservative_process_starts=1+actual+uncertain,wrapper_pid=os.getpid(),necessary_trailer_complete=True))

