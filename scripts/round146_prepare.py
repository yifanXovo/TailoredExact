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
if __name__=='__main__':globals()[sys.argv[1]]()
