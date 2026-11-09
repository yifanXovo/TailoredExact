"""Bounded input recovery, identities, protection and predeclared decisions."""
import zipfile
from round140_common import git
from round157_inventory import family,value
from round158_common import *

def member(archive,name):
    carrier=next(r for r in read(OLD157/'carrier_manifest.json')['archives'] if r['name']==archive)
    path=ROOT/carrier['parts'][0]['path'];assert sha(path)==carrier['SHA256']
    with zipfile.ZipFile(path) as z:
        matches=[n for n in z.namelist() if n.endswith(name)]
        assert len(matches)==1,(name,matches)
        content=z.read(matches[0])
    return content,dict(commit=SCIENCE157,archive=archive,archive_SHA=carrier['SHA256'],
        member=matches[0],member_SHA=hashlib.sha256(content).hexdigest())

def run_prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'goal.md').write_bytes(Path('C:/Users/Administrator/Downloads/TailoredExact_Round158_Complete_Goal.md').read_bytes())
    assert git('rev-parse','HEAD',cwd=ROOT).decode().strip()==BASE
    protection=[]
    for tree in (Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round157'):
        names=git('diff','HEAD','--name-only','-z',cwd=tree).decode().split('\0')
        dirty={n:dict(SHA256=sha(tree/n),bytes=(tree/n).stat().st_size) for n in names if n and (tree/n).is_file()}
        path=OUT/'infra'/f'{tree.name}_initial_status.txt';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(git('status','--porcelain=v1','--untracked-files=normal',cwd=tree))
        protection.append(dict(tree=str(tree),head=git('rev-parse','HEAD',cwd=tree).decode().strip(),tracked_dirty=dirty,status_SHA=sha(path)))
    write(OUT/'infra/protected_initial.json',dict(UTC=utc(),trees=protection))
    manifest=read(OLD157/'source_manifest.json');assert sha(PYTHON)==manifest['Python_SHA'];assert sha(DLL)==DLL_SHA
    assert not git('ls-files','*AGENTS.md',cwd=ROOT).strip()
    content,receipt=member('family_floor.zip','new_upper.json');old=json.loads(content)
    role='R-X35-S-T2';sources=read(OLD157/'inventory_sources.json');source=sources[role]
    Y=old['Y'];v=value(source['scope'],Y);members=family(source['scope'],Y)
    assert len(members)==10 and v['feasible'] and v['phi']==__import__('fractions').Fraction(old['J_exact'])
    candidates={role:dict(Y=Y,members=members,J_exact=str(v['phi']),J=float(v['phi']),source=receipt,rank='retained Y3 family, not global third')}
    families=read(OLD157/'inventory_families.json');nb=families['N-B35-S']['candidates'][0]
    candidates['N-B35-S']=dict(Y=nb['Y'],members=nb['members'],J_exact=nb['J_exact'],J=nb['J'],source='R157 preselected best saved family')
    write(OUT/'candidates.json',candidates)
    # Recover only the two small inputs needed for NB continuation and errata.
    content,logref=member('floor.zip','rx35_resource_floor_v2/native.log')
    lines=content.decode(errors='replace').splitlines();tail=lines[-1]
    (OUT/'infra/r157_native_tail.txt').write_text('\n'.join(lines[-4:])+'\n',encoding='utf-8')
    write(OUT/'r157_errata.json',dict(UTC=utc(),displayed_nodes_at_least=774,call_completed=False,
        final_NodeCount=None,final_Work=None,source=logref,last_line=tail,
        old_report_773_is_earlier_observation=True,log_incumbents_not_saved_are_not_qualified_uppers=True,
        correction='At least 774 displayed nodes; Optimize did not return. No final NodeCount/Work is inferred.'))
    content,nbref=member('resource.zip','nb35_family4096_v1/solution.json.gz')
    path=OUT/'infra/nb_relaxed_assignment.json.gz';path.write_bytes(content)
    write(OUT/'infra/nb_assignment_source.json',nbref)
    levels={r:dict(L_I=s['lower'],U_I=s['upper'],U_R=s['endpoint']['U'],new_resource_assignment_upper=None,
        U_R_source='inherited physically checked route projects into resource domain',U_P=s['endpoint']['U'],
        tau=s['lower']+.25*(s['endpoint']['U']-s['lower'])) for r,s in sources.items()}
    write(OUT/'initial_intervals.json',levels)
    write(OUT/'research_plan.json',dict(UTC=utc(),base=BASE,main='b2b940c1e517a72e226ec60fc49ff19651737632',
        PR219_open_draft_unmerged=True,initial_process_inventory='No active solver observed; other app chats idle/not-loaded',
        C1=dict(primary='RX35 retained Y3 entire 10-member exact-coefficient family',secondary='NB35 preselected singleton, saved relaxed assignment start',
            assignment_free=True,MIPFocus=1,Seed=0,Threads=1,initial_TimeLimit=1800,initial_NodeLimit=262144),
        decision='Low verified resource upper transfers deep capacity to physical completion; otherwise hard objective quarter-gap level with one qualified rounded subset expression',
        substantive_capacity_seconds=129600,resource_stage_capacity_seconds=21600,total_capacity_seconds=TOTAL,
        no_physical_U_from_resource_assignment=True,no_old_producer_execution=True,production_changes=False,
        review_method='Same agent separate arithmetic and matrix readback; no independent reviewer identity claimed',
        python_SHA=sha(PYTHON),DLL_SHA=sha(DLL),goal_SHA=sha(OUT/'goal.md'),policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md')))
    print(json.dumps(dict(candidates={r:dict(J=c['J'],family=len(c['members'])) for r,c in candidates.items()},levels=levels,protected_files=sum(len(t['tracked_dirty']) for t in protection))),flush=True)

if __name__=='__main__':run_prepare()
