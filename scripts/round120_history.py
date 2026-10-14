"""Read all frozen R119 cores and replay its nine published pairs; no solver."""
from round120_common import *
from round108_decisions import pair
def run():
    begin=time.perf_counter();assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=OLD).decode().strip()==BASE
    names=['goal.md','final_report.md','mathematical_contract.md','history_and_hypothesis.md','mechanism_account.json',
        'qualification/math_completion.json','qualification/math_completion_interpretation.json','review/extra_review.json','RESUME.md','resource_summary.json']
    hashes={n:sha(OLD/'results/unified_exact_round119'/n) for n in names}
    cores=[];replay=[]
    for n in [1,2,3]:
        path=OLD/'results/unified_exact_round119/reconstruction'/f'group{n:02d}/current_core.json';v=read(path)
        assert len(v['arms'])==len(v['pairs'])==3 and all(a['formal_protocol_qualified'] for a in v['arms'])
        arms={a['arm']:a for a in v['arms']}
        for p in v['pairs']:
            fresh=pair(arms[p['candidate']],arms[p['control']]);old=dict(p);old.pop('id',None)
            assert fresh==old,(n,p['candidate'],p['control']);replay.append(dict(id=v['group']['id'],**fresh))
        # Full JSON is decoded, including every original claim and witness;
        # retain compact actual conclusions instead of a second 30MB copy.
        cores.append(dict(path=str(path),SHA=sha(path),bytes=path.stat().st_size,
            complete_JSON_read=True,top_level_fields=list(v),
            arms=[{k:a.get(k) for k in ['arm','U','L','gap','certificate','T_produce','T_verify','T_total','native_Optimize','formal_protocol_qualified']} for a in v['arms']],
            mechanism=v['mechanism'],adjudication_fields=list(v['adjudication'])))
    b=read(OLD/'results/unified_exact_round119/resource_summary.json');assert b['paid_starts']==25 and not b['unclosed']
    assert read(OLD/'results/unified_exact_round119/stage_decision.json')['stage']=='STOP_TESTED_CONFIGURATION'
    old_input=read(OLD/'results/unified_exact_round119/input_manifest.json')
    safe_inputs=[p for p in old_input['development_roles']+old_input['qualification_roles']]
    for p in safe_inputs:
        src=OLD/p['input_path'];dst=ROOT/p['input_path'];assert sha(src)==p['input_sha256']
        if dst.exists():assert sha(dst)==sha(src)
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
    enum=old_input['enum_fixture'];src=OLD/enum['input_path'];dst=ROOT/enum['input_path'];assert sha(src)==enum['input_SHA']
    if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
    assert sha(dst)==enum['input_SHA']
    main=Path('E:/codes/ExactEBRP');tracked=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=no'],cwd=main).decode()
    files=[s[3:] for s in tracked.splitlines()];assert len(files)==3
    write(OUT/'initialization_receipt.json',dict(base=BASE,PR181_head=BASE,
        PR181_base='a756929a428f7afde30cbf66babbe44d0a1860ce',PR181_url='https://github.com/yifanXovo/TailoredExact/pull/181',
        main_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=main).decode().strip(),main_status=tracked,
        user_files_preserved_SHA={n:sha(main/n) for n in files},main_branch_untouched=True,
        worktree=str(ROOT),branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
        managed_worktree_operation='cf31d86d-2acd-4e8d-a6cb-258da0d63696',applicable_AGENTS_found=[],
        initial_relevant_solver_or_research_processes=[],initial_inventory_from_Win32_Process=True,
        R119_fees=b,R119_full_read_hashes=hashes,R118_complete_paper_SHA=sha(OLD/'results/unified_exact_round118/paper_algorithm_spec.md'),
        R119_cores=cores,R119_nine_pair_replay=replay,comparison_implementation_SHA=sha(ROOT/'scripts/round108_decisions.py'),
        Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-begin))
    write(OUT/'preflight_pair_replay.json',dict(passed=True,pairs=replay,unchanged_materiality_and_severe_rules=True,Optimize=0))
    print(json.dumps(dict(complete_cores=len(cores),published_pairs_replayed=len(replay),R119_stopped=True)))
if __name__=='__main__':run()
