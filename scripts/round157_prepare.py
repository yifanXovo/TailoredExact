"""Read sealed E+ inventories and protect pre-existing user bytes; no Optimize."""
from round157_common import *
from round140_common import git

def run():
    assert git('rev-parse','HEAD').decode().strip() == BASE
    assert git('remote','get-url','origin').decode().strip() == 'https://github.com/yifanXovo/TailoredExact.git'
    OUT.mkdir(parents=True, exist_ok=True)
    goal = Path('C:/Users/Administrator/Downloads/TailoredExact_Round157_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(goal.read_bytes())
    protected = []
    for tree in [Path('E:/codes/ExactEBRP'), WORK/'worktrees/paper-current', PRIOR]:
        status = git('status','--porcelain=v1','--untracked-files=normal',cwd=tree)
        dest = OUT/'infra'/f'{tree.name}_initial_status.txt'
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(status)
        names = git('diff','HEAD','--name-only','-z',cwd=tree).decode().split('\0')
        files = {name:dict(SHA256=sha(tree/name),bytes=(tree/name).stat().st_size)
                 for name in names if name and (tree/name).is_file()}
        protected.append(dict(tree=str(tree),head=git('rev-parse','HEAD',cwd=tree).decode().strip(),
                              tracked_dirty=files,status_file=str(dest),status_SHA=sha(dest)))
    write(OUT/'infra/protected_initial.json', dict(UTC=utc(),trees=protected))
    manifest = read(PRIOR/'results/unified_exact_round156/helper_manifest_Eplus.json')
    assert sha(PYTHON)==manifest['python_SHA']
    assert sha(DLL)==manifest['DLL_SHA']==DLL_SHA
    assert not git('ls-files','*AGENTS.md').strip()
    matrix = read(PRIOR/'results/unified_exact_round156/confirmation_matrix.json')
    sources = {}
    for group in matrix['groups']:
        launch = group['launch']
        if launch['id'] not in ('R-X35-S-T2','N-B35-S') or launch['R156_method']!='Eplus': continue
        dest = Path(launch['destination'])
        folder = dest/'external/round153_floor'
        src = read(folder/'source.json')
        price = read(folder/'pricing/result.json')
        assert price['scope']==src['scope']
        assert sha(src['source'])==src['source_SHA']
        assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
        witnesses = [str(p) for p in dest.rglob('*witness*.json')]
        sources[launch['id']] = dict(scope=src['scope'],stocks=price['stocks'],
            lower=price['lower'],upper=price['upper'],panel=launch['panel'],launch=launch,
            pricing_path=str(folder/'pricing/result.json'),pricing_SHA=sha(folder/'pricing/result.json'),
            scope_source=str(src['source']),scope_source_SHA=src['source_SHA'],
            fixed_commit=SCIENCE156,group=group['group'],witness_paths=witnesses,
            endpoint=read(dest/'round156_endpoint.json'))
    assert len(sources)==2
    write(OUT/'inventory_sources.json', sources)
    write(OUT/'infra/initial_identity.json',dict(UTC=utc(),base=BASE,source_science=SCIENCE156,
        main='b2b940c1e517a72e226ec60fc49ff19651737632',PR218_open_draft_unmerged=True,
        policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),goal_SHA=sha(OUT/'goal.md'),
        python=str(PYTHON),python_SHA=sha(PYTHON),DLL=str(DLL),DLL_SHA=sha(DLL),
        old_producer_reruns=0,old_carrier_downloads=0,active_solver_processes_initially_observed=0,
        initial_metadata_and_worktree_setup_outer_unmetered=True,
        review_method='separate mathematical and saved-model readers by the same agent; no delegated review'))
    print(json.dumps({k:dict(lower=v['lower'],upper=v['upper'],stocks=len(v['stocks']),
          witness_paths=v['witness_paths'],panel={x:v['panel'][x] for x in ('T_seconds','Q_vector','lambda','pickup_seconds','drop_seconds')})
          for k,v in sources.items()}),flush=True)

if __name__=='__main__':run()
