"""Bind the current full pools and unchanged production identity, read-only."""
from round155_common import *
from round140_common import git
from round153_campaign import old_launch

def prepare():
    tick=time.perf_counter()
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('remote','get-url','origin').decode().strip()=='https://github.com/yifanXovo/TailoredExact.git'
    changed=git('diff','--name-only').decode().splitlines()
    protected={p:sha(ROOT/p) for p in changed if not p.startswith(('scripts/round155','results/unified_exact_round155')) and p not in ('.gitattributes','.gitignore')}
    write(OUT/'infra/protected_tracked_bytes.json',protected)
    rows=read(OLD154/'reports/scientific_table.json')['rows']
    sources={}
    for role in ['N-B35-S','K-35-U','N-C20-U']:
        row=next(r for r in rows if r['role']==role); path=Path(row['result']); prior=read(path)
        assert sha(path)==row['result_SHA'] and not prior.get('refresh_required',False)
        qp=OLD153/'reference'/role/'direct/model.mps'
        assert sha(qp)==prior['Q_SHA']
        sources[role]=dict(result=str(path),result_SHA=sha(path),fixed_commit=SCIENCE153 if OLD153 in path.parents else SCIENCE154,
            Q=str(qp),Q_SHA=sha(qp),Q_fixed_commit=SCIENCE153,lower=prior['lower'],upper=prior['upper'],
            columns=len(prior['columns']),supports=len(prior['supports']),scope=prior['scope'],
            upper_witness_source=prior.get('upper_witness_source'),prior_result_chain=prior.get('prior_results'))
    assert sources['K-35-U']['columns']==33896 and sources['K-35-U']['supports']==90
    assert sources['N-C20-U']['columns']==54235 and sources['N-C20-U']['supports']==63
    candidate=read(OLD154/'candidate_manifest.json')
    assert candidate['source_commit']=='d834d62c7a1be599867db04a427f1d43dd3631cb'
    assert sha(candidate['production_PE'])==candidate['production_PE_SHA']=='0d3a94183285cc2794676c717a23dc75a47c872ad48c26d2237dd8634f1a5a01'
    assert sha(DLL)==DLL_SHA
    roles={}
    for role,cap in [('N-B35-S',7200),('R-X35-S-T2',7200),('R-X20-S-T1',1200)]:
        launch=old_launch(role)
        roles[role]=dict(cap_seconds=cap,original=launch,input_SHA=sha(ROOT/launch['panel']['input_path']))
    assert roles['R-X35-S-T2']['input_SHA']=='c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2'
    assert roles['R-X20-S-T1']['input_SHA']=='2b467b5bb1e650a4c1e792e808dcf9575bcc76752fe378e16c838015344ddac6'
    write(OUT/'starting_pools.json',sources)
    write(OUT/'production_identity.json',dict(candidate_path=str(OLD154/'candidate_manifest.json'),candidate_SHA=sha(OLD154/'candidate_manifest.json'),
        helper_manifest=str(OLD154/'helper_manifest.json'),helper_manifest_SHA=sha(OLD154/'helper_manifest.json'),
        PE=candidate['production_PE'],PE_SHA=candidate['production_PE_SHA'],DLL=str(DLL),DLL_SHA=DLL_SHA,
        measured_source_commit=candidate['source_commit'],same_R153_producer=True,no_CPP_change=True,no_recompile=True,roles=roles))
    write(OUT/'infra/initial_identity.json',dict(UTC=utc(),HEAD=BASE,branch=git('branch','--show-current').decode().strip(),
        main='b2b940c1e517a72e226ec60fc49ff19651737632',R154_open_draft_unmerged=True,
        workspace_policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),goal_SHA=sha(OUT/'goal.md'),protected_tracked_count=len(protected),
        no_tracked_AGENTS=True,active_UI_protected=True,seconds=time.perf_counter()-tick))
    print(json.dumps(dict(PASS=True,pools={k:{x:v[x] for x in ('columns','supports','lower','upper')} for k,v in sources.items()},roles={k:v['original']['panel'] for k,v in roles.items()})),flush=True)

if __name__=='__main__': prepare()
