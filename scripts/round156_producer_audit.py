"""Read back fresh helper prices and preserve the exact pre-build manifests."""
from fractions import Fraction as F
from round152_math import unary_dp
from round143_math import outward
from round143_lp import semantics
from round156_review import exact_value
from round156_common import *

def run(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_pricing import Oracle
    affinity();assert binding()['sha256']==DLL_SHA
    facts=[];target=OUT/'review'/label;target.mkdir(parents=True,exist_ok=False)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for path in sorted((OUT/'producer_checks').glob('*/result.json')):
            arm=read(path);folder=path.parent/'helper';r=read(folder/'result.json');s=read(folder/'source.json')
            p=read(folder/'pricing/result.json');c=read(folder/'pricing/call.json');scope=r['scope'];ss=scope['stations']
            assert r['qualified'] and not r['global_deadline_stop'] and r['node_limit']==c['node_limit']==16384
            assert s['producer_rule']==r['producer_rule']=='RN16384_original_gap'
            assert s['no_historical_inventory_or_price_loaded'] and r['no_historical_inventory_or_price_loaded']
            assert sha(s['source'])==s['source_SHA']==r['source_SHA']
            manifest=Path(s['helper_manifest']);assert sha(manifest)==s['helper_manifest_SHA']==r['source_helper_manifest_SHA']
            snapshot=path.parent/'helper_manifest.snapshot.json';assert not snapshot.exists();snapshot.write_bytes(manifest.read_bytes())
            deps=read(snapshot)['helper_dependencies']
            assert deps==s['dependencies']
            for name,digest in r['loaded_project_sources'].items():assert sha(ROOT/name)==deps[name]==digest
            d={(site['i'],y):F(site['omega'])*abs(F(site['c'])*y-1) for site in ss for y in site['support']}
            assert p['d_exact']=={f'{i}:{y}':str(v) for (i,y),v in d.items()}
            fallback=F(scope['gamma_L'])+F(unary_dp(scope,d)['exact'])
            anchors={int(k):F(v) for k,v in c['anchors_exact'].items()};scale=F(c['scale'])
            with gp.read(str(folder/'pricing/model.mps'),env=env) as saved:
                assert sha(folder/'pricing/model.mps')==c['model_SHA']
                oracle=Oracle(scope,env,old_joint=True);m=oracle.model
                m.setObjective(float(1/scale)*oracle.q+gp.quicksum(outward((value-anchors[k[0]])/scale,False)*oracle.x[k] for k,value in d.items()))
                m.update();assert semantics(m)==semantics(saved)
                correction=sum((max([F(0)]+[F(oracle.x[site['i'],y].Obj)-(d[site['i'],y]-anchors[site['i']])/scale for y in site['support']]) for site in ss),F(0))
                correction+=max(F(0),(F(oracle.q.Obj)-1/scale)*F(scope['gamma_U']))
                assert correction==F(c['objective_correction_scaled_exact']);oracle.close()
            q=p['calls'][0];assert q['Status'] in (2,8) and q['bound_status_qualified']
            lower=max(fallback,scale*(F(q['native_bound'])-F(c['numerical_guard_scaled'])-correction)+sum(anchors.values(),F(0)))
            if p['zero_lower'] is not None:lower=min(lower,F(p['zero_lower']))
            assert F(r['lower'])<=lower and r['lower']==p['lower']==arm['lower']
            for v in p['stocks']:
                checked=exact_value(scope,v['Y']);assert checked['feasible'] and checked['phi']==F(v['price_exact'])
            assert r['upper']==p['upper']==arm['upper']>=min(float(F(v['price_exact'])) for v in p['stocks'])
            facts.append(dict(role=arm['role'],lower=arm['lower'],upper=arm['upper'],gap=arm['gap'],nodes=q['nodes'],
                Status=q['Status'],Native_Work=q['Work'],helper_outer_seconds=arm['helper_outer_seconds'],
                helper_manifest_snapshot_SHA=sha(snapshot),result_SHA=sha(path),Optimize=0))
    assert len(facts)==5
    expected={'N-B35-S':2700,'R-B35-S-T1':1590,'R-X20-S-T1':65}
    initial=read(OUT/'starting_inventory.json')
    for f in facts:
        if f['role'] in expected:
            assert f['nodes']==expected[f['role']]
            assert (f['lower'],f['upper'])==(initial[f['role']]['lower'],initial[f['role']]['upper'])
        if f['role']=='R-X35-S-T2':assert f['gap']<=1e-4 and f['lower']-initial[f['role']]['lower']>1e-3
    write(target/'result.json',dict(PASS=True,facts=facts,Optimize=0,source_SHA=sha(__file__),
        actual_new_entry_SHA=sha(ROOT/'scripts/round156_online.py'),
        prebuild_manifest_HEAD_is_base_not_complete_new_code_commit=True,
        actual_source_identity_is_exact_dependency_hashes_and_metered_source_snapshots=True,
        historical_prebuild_manifests_preserved_before_final_build_manifest=True,
        same_agent_independent_reconstruction=True))
    write(OUT/'reports/fresh_producers.json',dict(rows=facts,limited_K20_check=True,no_replacement_instance=True))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
