"""Bounded initial identities; protect preexisting user and historical assets."""
from round146_common import *
def initial():
    configure();assert not (OUT/'start_receipt.json').exists()
    protected=Path('E:/codes/ExactEBRP');status=git('status','--porcelain=v1','--untracked-files=no',cwd=protected).decode()
    (OUT/'protected_original_tracked_status.txt').write_text(status,encoding='utf-8')
    write(OUT/'start_receipt.json',dict(UTC=utc(),branch=git('branch','--show-current').decode().strip(),base=BASE,
        main=git('rev-parse','origin/main').decode().strip(),R145_in_main=False,PR_base='codex/round145-normalized-resource-consistency',
        predecessor_PR=dict(number=207,open=True,Draft=True,head=BASE),goal_SHA=sha(OUT/'goal.md'),
        protected_original=str(protected),protected_tracked_status_SHA=sha(OUT/'protected_original_tracked_status.txt'),
        active_tree_tracked_clean_at_entry=True,preexisting_untracked_old_round_assets_retained=True,no_preexisting_solver_seen=True,
        ceiling_seconds=28800,Gurobi_Seed=0,H_seed=20260626,threads=1,serial=True,affinity_mask=4,
        preliminary_attachments_available=False,preliminary_reconstruction='goal and local fixed historical carriers; zero old Optimize',
        policy='All new assets in ExactEBRP-work; bounded post-PR current-round cleanup only'))
    print('Round146 entry and protected status recorded')
def selection():
    configure();m=read(OUT/'candidate_manifest.json');lp=[read(p) for p in sorted((OUT/'LP').glob('*/result.json'))]
    assert len(lp)==5 and all(r['qualified'] and r['gain']>1e-6 for r in lp)
    write(OUT/'candidate_selection.json',dict(UTC=utc(),candidate='STOCK+GD-state',reference='STOCK',uniform=True,
        decision_basis='K20 combination objective .251016 exceeds standalone GD .236010 and STOCK .204590; cheap GD has real information beyond joint and on all three BASE domains',
        frozen_before_formal=True,initial_stage='same-PE K20 pair, cap1200 each; no automatic extension',
        source_commit=m['source_commit'],PE_SHA=m['production_PE_SHA'],LP_results=lp,root_once=True,new_rows_max=2,new_columns=0,paid_source_solves=0,
        baseline_reoptimization=0,optional_state_Hoover_diagnostic_needed=False,reason_no_backup='Direct original-variable rows already yield clear real optimized gains'))
    p=read(ROOT/'config/gi_tbc_round137.json');p.update(schema='round146-direct-GD-frozen-argv-v1',algorithm='GI-TBC + STOCK + direct state-conditioned Gini deviation rows',
        source_commit=m['source_commit'],research_head=m['source_commit'],default_executable=m['production_PE'],verified_PE_SHA256=m['production_PE_SHA'],
        round=146,source_manifest='results/unified_exact_round146/candidate_manifest.json',research_profile=True,GD=True,STOCK=True,
        parent_profile_SHA256=sha(ROOT/'config/gi_tbc_round137.json'))
    p['argv']+=['--round138-stock-rlt','--round146-gd','on'];write(ROOT/'config/gi_tbc_gd_round146.json',p)
    print('Uniform STOCK+GD-state candidate and separate research entry frozen')
if __name__=='__main__':globals()[sys.argv[1]]()
