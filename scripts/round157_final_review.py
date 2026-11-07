"""Final same-agent reconstruction of saved science, scopes and fee treatment.

This is not a claim of a separate human or subagent review. It does not
optimize and consumes no bound from an unfinished Native log.
"""
from fractions import Fraction as F
from round157_common import *
from round157_inventory import instance,value,family,signature
from round143_lp import semantics,residual
from round157_family_floor import exclude_family,inventory_point
from round157_floor import objective,original_lower,retain_known_lower
from round153_pricing import Oracle
from round107_reader import physical

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    decision=read(OUT/'final_decision.json');assert decision['study_complete']
    assert not decision['complete_candidate_frozen'] and not decision['complete_panel_started'], 'Review must be extended if a complete candidate was actually run'
    sources=read(OUT/'inventory_sources.json');families=read(OUT/'inventory_families.json');facts=[]
    for role,s in sources.items():
        d=instance(s['panel']);f=families[role]
        assert sha(ROOT/s['panel']['input_path'])==s['panel']['input_sha256']
        assert s['scope']['gamma_L']==0
        for candidate in f['candidates']:
            members=family(s['scope'],candidate['Y']);assert members==candidate['members']
            v=value(s['scope'],candidate['Y']);assert v['feasible'] and v['phi']==F(candidate['J_exact'])
            for Y in members:
                w=value(s['scope'],Y);assert w['feasible'] and w['phi']==v['phi'] and w['G']==v['G'] and w['penalty']==v['penalty']
                assert signature(s['scope'],Y)==signature(s['scope'],candidate['Y'])
        pos=physical(ROOT,s['panel'],f['positive_control']['witness'])
        assert abs(pos['F']-s['endpoint']['U'])<=1e-7
        nt=read(OUT/'review/non_time_uppers'/f'{role}_result.json')
        witness=read(OUT/'review/non_time_uppers'/f'{role}_witness.json')
        check=physical(ROOT,dict(s['panel'],T_seconds=nt['safe_non_time_bound']),witness)
        assert abs(check['maximum_duration']-nt['true_required_time_upper'])<=1e-7 and check['maximum_duration']>d['T']
        assert not nt['physical_U_claim']
        facts.append(dict(role=role,input_SHA=sha(ROOT/s['panel']['input_path']),
            families=[c['family_size'] for c in f['candidates']],positive_original_T=pos['maximum_duration'],
            non_time_true_Tstar_upper=nt['true_required_time_upper']))
    for name in ('v1','resource_v1','tour_v1','floor_v1','floor_v2','family_floor_v1'):
        path=OUT/'qualification'/name/'result.json'
        assert read(path)['PASS'],path
    assert read(OUT/'review/family_predeep_v1.json')['PASS']
    for path in (OUT/'review').glob('*_readback.json'):assert read(path)['PASS']
    fixed=[]
    for path in (OUT/'fleet').glob('*/result.json'):
        r=read(path);assert r['classification']=='UNKNOWN' and r['status']==8
        assert r['NodeCount']==4096 and r['physical_U'] is None
        fixed.append(dict(path=path.relative_to(ROOT).as_posix(),result_SHA=sha(path),classification='UNKNOWN'))
    assert len(fixed)==2
    unfinished=[]
    for folder in (OUT/'floor').iterdir():
        assert not (folder/'result.json').exists(), 'A returned full-domain model needs its own bound reconstruction'
        label='deepen_'+folder.name
        fee=read(OUT/'fees'/label/'receipt.json');termination=read(OUT/'fees'/label/'revision_termination.json')
        assert fee['exit_observed'] and fee['exit_code']!=0 and fee['G1_seconds']>0
        assert termination.get('no_new_bound_consumed','no new proof' in termination['reason'].lower())
        unfinished.append(dict(label=label,charged=fee['G1_seconds'],receipt_SHA=sha(OUT/'fees'/label/'receipt.json'),new_bound_consumed=False))
    priced=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for folder in sorted((OUT/'family_floor').iterdir()):
            call=read(folder/'call.json');r=read(folder/'result.json');s=sources[r['role']]
            assert call['family_review_SHA']==sha(OUT/'review/family_predeep_v1.json')
            assert call['model_SHA']==sha(folder/'model.mps')==r['model_SHA']
            assert r['call_SHA']==sha(folder/'call.json') and r['bound_status_qualified']
            assert r['all_physical_original_inventories_covered'] and r['physical_U'] is None
            for proof in call['proofs']:
                path=OUT/'resource'/proof['label'];pr=read(path/'result.json')
                assert sha(path/'result.json')==proof['result_SHA'] and sha(path/'condition.json')==proof['condition_SHA']
                assert pr['classification']=='RESOURCE_INFEAS' and pr['bound_status_qualified']
                assert pr['required_time_lower']>pr['original_T']+pr['margin']
            o=Oracle(s['scope'],env,old_joint=True);transport=objective(o);flags=[]
            for batch,anchor in enumerate(call['anchors']):flags+=exclude_family(o,anchor,batch)
            retain_known_lower(o,s['lower'])
            with gp.read(str(folder/'model.mps'),env=env) as saved:
                assert semantics(saved)==semantics(o.model)
                u=read(folder/'new_upper.json');point,v=inventory_point(o,u['Y'],flags)
                assert residual(saved,point)['constraints']<=1e-7 and residual(saved,point)['bounds']<=1e-7
                assert v['phi']==F(u['J_exact']) and not u['physical_route']
                if r['SolCount']:
                    sol=load_gz(folder/'solution.json.gz');q=residual(saved,sol)
                    assert max(q[k] for k in ('constraints','bounds'))<=1e-5
            expected=max(F(s['lower']),original_lower(r['native_bound'],transport))
            assert abs(float(expected)-r['original_lower'])<=1e-14 and expected<=v['phi']
            assert r['level_excluded']==(expected>F(call['target_level_exact']))
            priced.append(dict(role=r['role'],original_lower=r['original_lower'],new_inventory_upper=r['new_inventory_upper'],
                forbidden_inventories=len(flags),global_scope=True,physical_upper_claim=False,model_SHA=sha(folder/'model.mps')))
            o.close()
    assert len(priced)<=1
    report=read(OUT/'reports/table_manifest.json');assert report['log_only_unfinished_calls_not_consumed']
    # Fee ledger checks include all children already closed before this review;
    # the current verification's receipt is written by the enclosing supervisor.
    receipts=[]
    for path in (OUT/'fees').glob('*/receipt.json'):
        fee=read(path);assert fee['exit_observed'] and fee['nested_H_LP_MIP_not_added']
        receipts.append(fee)
    ordered=sorted(receipts,key=lambda x:x['start_unix'])
    assert all(a['end_unix']<=b['start_unix'] for a,b in zip(ordered,ordered[1:]))
    protected=read(OUT/'infra/protected_initial.json');protected_count=0
    for tree in protected['trees']:
        for path,old in tree['tracked_dirty'].items():
            assert sha(Path(tree['tree'])/path)==old['SHA256'];protected_count+=1
    write(OUT/'review/final_scientific_review.json',dict(UTC=utc(),PASS=True,scientific_blockers=[],
        review_kind='same-agent separate reconstruction routines; no independent-person or subagent claim',
        Optimize=0,source_SHA=sha(__file__),inventory_and_physical_checks=facts,
        fixed_queries=fixed,unfinished_full_domain_calls=unfinished,finite_original_objective_prices=priced,
        protected_tracked_dirty_files=protected_count,closed_fee_intervals_serial=True,
        unknown_does_not_change_physical_bounds=True,finite_family_not_entire_objective_level=True,
        resource_feasible_points_not_routes=True,excluded_old_upper_not_reused=True,
        complete_performance_not_claimed=True,current_review_fee_closed_by_parent=True))
    print(json.dumps(dict(PASS=True,priced=len(priced),protected=protected_count)),flush=True)

if __name__=='__main__':run()
