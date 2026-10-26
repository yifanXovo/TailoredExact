"""Frozen R120 production identity; R121 non-refundable outer accounting."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time
import round120_common as prior
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round121'
BASE='4872eb8421e43e57ef6e3727db4cd40e1c14f935'
SOURCE='355eefd2be3fe5651195681faf7b3a63ee4032f8'
PE=ROOT/'build/research/round120/ExactEBRP.exe'
PE_SHA='5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
QUALIFICATION_MAXIMUM_STARTS=12
QUALIFICATION_MAXIMUM_SECONDS=1800
sha=prior.sha;read=prior.read;write=prior.write;utc=prior.utc;environment=prior.environment;bindings=prior.bindings
def helpers():
    import ast
    names=set(prior.helper_paths());pending=['round121_common','round121_data','round121_prepare',
        'round121_campaign','round121_evidence','read_round121','qualify_round121','round121_fixtures','round121_decision']
    seen=set()
    while pending:
        name=pending.pop();p=ROOT/'scripts'/(name+'.py')
        if name in seen or not p.is_file():continue
        seen.add(name);names.add(p.relative_to(ROOT).as_posix())
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending.extend(m for m in modules if m and (ROOT/'scripts'/(m+'.py')).is_file())
    names.add('scripts/round121_reference.cpp')
    return {n:sha(ROOT/n) for n in sorted(names)}
def identity():
    p=read(OUT/'production_identity.json')
    assert sha(PE)==p['production_PE_SHA']==PE_SHA and sha(DLL)==p['DLL_SHA']==DLL_SHA
    assert bindings()==p['source_bindings']==read(ROOT/'results/unified_exact_round120/production_identity.json')['source_bindings']
    assert p['source_commit_before_native']==SOURCE
    return p
def budget():
    launches=sorted((OUT/'fees').glob('*/launch.json'));closed=[];starts=0;qs=0
    for p in launches:
        l=read(p);r=read(p.parent/'receipt.json') if (p.parent/'receipt.json').exists() else None
        count=r['conservative_process_starts'] if r else l['conservative_process_starts']
        starts+=count;qs+=count if l['qualification'] else 0
        if r:closed.append((l,r))
    seconds=sum(r['outer_seconds_upper'] for l,r in closed)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=40-starts,remaining_outer_seconds=48000-seconds,
        qualification_starts=qs,qualification_seconds=sum(r['outer_seconds_upper'] for l,r in closed if l['qualification']),
        unclosed=[p.parent.name for p in launches if not (p.parent/'receipt.json').exists()])
def fee_begin(label,children,cap,qualification,reservation):
    from round115_common import process_origin
    tick,creation=process_origin();b=budget();d=OUT/'fees'/label
    assert not d.exists() and not b['unclosed'],b
    assert b['remaining_starts']>=children+1+reservation['starts']
    assert b['remaining_outer_seconds']>=cap+reservation['seconds']
    if qualification:
        assert b['qualification_starts']+children+1<=QUALIFICATION_MAXIMUM_STARTS and b['qualification_seconds']+cap<=QUALIFICATION_MAXIMUM_SECONDS
    d.mkdir(parents=True)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),wrapper_pid=os.getpid(),wrapper_creation_unix=creation,
        conservative_process_starts=children+1,declared_native_children=children,qualification=qualification,outer_cap=cap,
        budget_before=b,remaining_fixed_obligations=reservation,frozen_UTC=utc(),
        start_accounting='wrapper plus actual/uncertain children; failed declarations charged, no refund for failure; nested native time not added'))
    return d,tick
fee_pending=prior.fee_pending
def close_fee(label):
    import types
    fn=types.FunctionType(prior.close_fee.__code__,dict(vars(prior),ROOT=ROOT,OUT=OUT,budget=budget),'close_R121_fee')
    return fn(label)
def initialize():
    assert not (OUT/'initialization_receipt.json').exists()
    old=read(ROOT/'results/unified_exact_round120/production_identity.json')
    assert old['source_commit_before_native']==SOURCE and old['production_PE_SHA']==sha(PE)==PE_SHA and old['DLL_SHA']==sha(DLL)==DLL_SHA
    assert old['source_bindings']==bindings()
    main=Path('E:/codes/ExactEBRP')
    status=subprocess.check_output(['git','status','--porcelain','-uno'],cwd=main).decode()
    dirty=[line[3:] for line in status.splitlines()]
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=main)
    (OUT/'preexisting_main_untracked_paths.txt').write_bytes(untracked)
    write(OUT/'initialization_receipt.json',dict(worktree=str(ROOT),base=BASE,branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
        initialized_UTC=utc(),main_worktree=str(main),main_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=main).decode().strip(),
        main_branch=subprocess.check_output(['git','branch','--show-current'],cwd=main).decode().strip(),main_tracked_status=status,
        main_dirty_SHA={n:sha(main/n) for n in dirty},main_untracked_inventory_SHA=sha(OUT/'preexisting_main_untracked_paths.txt'),
        applicable_AGENTS_found=[],active_solver_processes_observed=[],same_identity_R121_execution_found=False,
        PR182_head_verified=BASE,PR182_base='codex/round119-certificate-driven-domain-contraction',PR182_OPEN_Draft=True,
        engineering_only=True,native_starts=0,Optimize=0,human_time='unknown'))
    write(OUT/'production_identity.json',dict(old,round=121,actual_base=BASE,production_PE_path=PE.relative_to(ROOT).as_posix(),
        source_commit_before_native=SOURCE,copied_original_PE_without_recompile=True,Seed='per frozen role 0 or 1',
        verified_UTC=utc(),default_ENS_changed=False))
    print('R121 isolated; frozen source/PE/DLL verified; no native launch')
if __name__=='__main__':initialize() if sys.argv[1]=='initialize' else close_fee(sys.argv[1])
