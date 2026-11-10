"""Bounded fixed evidence readback; no historical Optimize."""
from round161_common import *
import shutil,zipfile

def setup():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'goal.md').write_bytes(Path('C:/Users/Administrator/Downloads/TailoredExact_Round161_Complete_Goal.md').read_bytes())
    protected=[]
    for tree in [Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round160']:
        status=git('status','--short','--untracked-files=no','-z',cwd=tree).decode()
        paths=[x[3:] for x in status.split('\0') if x]
        protected.append(dict(tree=str(tree),head=git('rev-parse','HEAD',cwd=tree).decode().strip(),
            dirty={p:sha(tree/p) for p in paths if (tree/p).is_file()}))
    write(OUT/'infra/protected_initial.json',dict(UTC=utc(),trees=protected))
    write(OUT/'infra/entry.json',dict(UTC=utc(),base=BASE,branch=git('branch','--show-current').decode().strip(),
        main='b2b940c1e517a72e226ec60fc49ff19651737632',R160_PR=222,R160_open=True,R160_draft=True,
        AGENTS='No applicable ancestor or tracked AGENTS.md',policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),
        active_solver_processes=0,scientific_capacity=TOTAL,old_producers_run=0,
        free_bytes=shutil.disk_usage(WORK).free))
    prior=WORK/'worktrees/round160/results/unified_exact_round160'
    archive=prior/'artifacts/new_core.zip';manifest=read(prior/'carrier_manifest.json')
    item=next(a for a in manifest['archives'] if a['path'].endswith('new_core.zip'));assert sha(archive)==item['SHA256']
    refs=[]
    with zipfile.ZipFile(archive) as z:
        for role in ('R-X35-S-T2','N-B35-S'):
            prefix='results/unified_exact_round160/inputs/'+role+'/'
            folder=OUT/'inputs'/role;folder.mkdir(parents=True,exist_ok=True)
            members=[]
            for name in ('source.json','parent.txt'):
                raw=z.read(prefix+name);(folder/name).write_bytes(raw);members.append(dict(member=prefix+name,SHA256=sha(folder/name),bytes=len(raw)))
            source=read(folder/'source.json');panel=source['panel']
            raw=git('show',BASE+':'+panel['input_path']);(folder/'instance.txt').write_bytes(raw)
            assert sha(folder/'instance.txt')==panel['input_sha256']
            refs.append(dict(role=role,parent_J=source['parent_J'],parent_stage=source['parent_stage'],
                fixed_commit=BASE,prior_science='695ea68caad088a54ebed45b7d49360d12bd0e8d',archive_SHA=sha(archive),members=members,
                input_path=panel['input_path'],input_SHA=sha(folder/'instance.txt'),own_H_seed=20260626,offline_development_only=True))
    write(OUT/'input_manifest.json',dict(roles=refs,old_producer_reruns=0))
    # Read only the specifically requested latest facts; do not replay archives.
    names=['goal.md','final_report.md','complete_comparison.json','trajectory_analysis_v1.json','trajectory_analysis_v2.json',
        'revision_decision.json','cost_report.json','final_review.json','candidate_manifest.json']
    write(OUT/'history_readback.json',dict(fixed_commit=BASE,files={n:sha(prior/n) for n in names},
        prior_cost=read(prior/'cost_report.json')['G1_seconds'],prior_comparison=read(prior/'complete_comparison.json')))
    print('setup PASS; fixed source offline own-H parents only')

if __name__=='__main__':setup()
