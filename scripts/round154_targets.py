"""Freeze useful original-price proof tasks on the inherited complete pools."""
from fractions import Fraction as F
from round143_math import outward
from round152_math import states,unary_dp
from round153_coupled import Master
from round153_lp import optimize
from round153_pricing import stock_value
from round153_stabilize import select_dual
from round154_common import *

def prepare(role,label,mode='fresh_near_optimal',prior_override='none'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    tick=time.perf_counter();folder=OUT/'directions'/label;folder.mkdir(parents=True,exist_ok=False)
    table=next(r for r in read(OLD153/'reports/scientific_table.json')['rows'] if r['role']==role)
    priorpath=ROOT/table['coupled_result'] if prior_override=='none' else Path(prior_override)
    prior=read(priorpath);scope=prior['scope']
    qpath=OLD153/'reference'/role/'direct/model.mps';assert prior['Q_SHA']==sha(qpath)
    write(folder/'plan.json',dict(UTC=utc(),role=role,mode=mode,prior_result=str(priorpath),prior_SHA=sha(priorpath),
          Q_SHA=sha(qpath),columns=len(prior['columns']),supports=len(prior['supports']),
          motive='K saved near-optimal certificate retains direct room; NC selects anew against all54210 stocks after old direction ceiling exhaustion',
          full_original_Q=True,full_support=True,absolute_hull_target=1e-4,no_production_results_used=True))
    values={tuple(Y):stock_value(scope,Y) for Y in prior['columns']}
    assert all(v['feasible'] for v in values.values())
    inherited_price=[];original=None;qualified_RMP_upper_source=None
    if mode=='saved_near_optimal':
        original=OLD153/'coupled'/f'{role}_near_optimal_zero_pool/iter00010'
        cert=load_gz(original/'certificate.json.gz');p=read(original/'pricing/result.json')
        assert cert['qualified'] and p['scope']==scope and p['complete_domain']
        beta=p['beta'];d={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()}
        paths=[original/'pricing/result.json',OLD153/'coupled'/f'{role}_post_primal_fixed_long/pricing/result.json']
        for path in paths:
            r=read(path);assert r['scope']==scope and r['beta']==beta and r['d_exact']==p['d_exact']
            inherited_price.append(dict(path=str(path),SHA256=sha(path),lower=r['lower'],seconds=r['seconds']))
        old_lower=max(F(p['lower']) for p in inherited_price)
    else:
        assert mode=='fresh_near_optimal'
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
            with gp.read(str(qpath),env=env) as m:
                master=Master(m,scope,gp,env)
                for Y in values:master.add(Y)
                m.update();rr=optimize(m,folder/'RMP',cap=180.,save_model=True)
                assert rr['Status']==2 and master.primal()['qualified']
                save_gz(folder/'primal.json.gz',dict(point={v.VarName:v.X for v in m.getVars()},check=master.primal(),
                         stocks=[dict(Y=list(Y),weight=var.X,f_exact=str(master.values[Y]['f'])) for Y,var in master.columns.items() if abs(var.X)>1e-14]))
                # This complete RMP already evaluates every newly ingested
                # stock. Consume its qualified upper and discharge that
                # refresh obligation without buying a duplicate solve.
                previous_upper=prior['upper'];prior=dict(prior,upper=min(previous_upper,m.ObjVal))
                refreshed=dict(prior,gap=prior['upper']-prior['lower'],refresh_required=False,
                    prior_results=[str(priorpath)],refresh=dict(Native_status=rr['Status'],RMP_objective=m.ObjVal,
                    primal=master.primal(),all_columns=len(values),upper_updated=prior['upper']<previous_upper,
                    no_new_lower_claim=True,primal_witness=str(folder/'primal.json.gz')),
                    decision='DIRECTION_PREPARATION_ALSO_REFRESHED_ALL_COLUMNS')
                write(folder/'refreshed_pool.json',refreshed)
                qualified_RMP_upper_source=dict(refreshed_pool=str(folder/'refreshed_pool.json'),
                    refreshed_pool_SHA=sha(folder/'refreshed_pool.json'),primal=str(folder/'primal.json.gz'),
                    primal_SHA=sha(folder/'primal.json.gz'),return_SHA=sha(folder/'RMP/return.json'))
                selected,record=select_dual(master,folder/'selection',band=1e-7,cap=180.,center='zero')
                assert selected,'inspect selection before any expensive price'
                a=selected['hull_convexity'];pi={k:selected[c.ConstrName] for k,c in master.links.items()};beta=max(0.,selected['hull_gini'])
                d={k:F(-pi.get(k,0.)) for k in states(scope)}
                dp=unary_dp(scope,d);old_lower=F(beta)*F(scope['gamma_L'])+F(dp['exact'])
                cert=master.certificate(a,pi,beta,outward(old_lower,False),selected)
                save_gz(folder/'Q_bounds.json.gz',dict(bounds=master.bounds,derivations=master.derivations))
    assert F(cert['beta'])==F(beta)
    d={k:d.get(k,F(0)) for k in states(scope)}
    assert all(F(cert['pi'].get(f'{i}:{y}',0.))==-v for (i,y),v in d.items())
    prices={Y:F(beta)*v['f']+sum(d[s['i'],y] for s,y in zip(scope['stations'],Y)) for Y,v in values.items()}
    best=sorted(prices,key=lambda Y:(prices[Y],Y))[:4];U=min(prices.values())
    cq=F(cert['lower_exact']);aK=F(cert['a_true_RMP_exact']);ceiling=cq+min(aK,U)
    desired=F(prior['upper'])-F(1e-4);assert desired>F(prior['lower'])
    # Freeze the task before viewing either current oracle's result.
    zeta=min(desired,ceiling-F(1e-7));assert zeta>F(prior['lower'])+F(1e-4),(role,float(ceiling))
    tau=zeta-cq
    save_gz(folder/'certificate.json.gz',cert)
    result=dict(UTC=utc(),role=role,label=label,scope=scope,Q_SHA=sha(qpath),Q_path=str(qpath),
                prior_result=str(priorpath),prior_result_SHA=sha(priorpath),columns=len(values),supports=len(prior['supports']),
                mode=mode,source_iteration=str(original) if original else None,beta=beta,beta_exact=str(F(beta)),
                qualified_RMP_upper_source=qualified_RMP_upper_source,
                d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()},
                C_Q_exact=str(cq),a_K_exact=str(aK),tau_exact=str(tau),zeta_exact=str(zeta),
                inherited_hull_lower=prior['lower'],inherited_hull_upper=prior['upper'],
                inherited_price_lower=outward(old_lower,False),inherited_price_sources=inherited_price,
                initial_true_price_upper=outward(U,True),initial_true_price_upper_exact=str(U),
                fixed_certificate_ceiling=outward(ceiling,True),fixed_certificate_ceiling_exact=str(ceiling),
                ceiling_is_not_full_hull_upper=True,initial_stocks=[list(Y) for Y in best],
                target_price=float(tau),target_hull=float(zeta),hull_lower_from_inherited_price=outward(cq+min(aK,old_lower),False),
                frozen_before_new_fixed_prices=True,seconds=time.perf_counter()-tick)
    write(folder/'direction.json',result);print(json.dumps({k:result[k] for k in ['role','target_price','target_hull','fixed_certificate_ceiling','initial_true_price_upper','inherited_price_lower','seconds']}),flush=True)

def compare(label,implementation,cap='60',name='screen'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_pricing import Oracle
    from round154_residual import ResidualOracle
    configure();affinity();assert binding()['sha256']==DLL_SHA
    path=OUT/'directions'/label/'direction.json';direction=read(path);scope=direction['scope']
    gate=read(OUT/'review/fixed_price_admission.json');assert gate['decision']=='ACCEPT' and gate['independent_nonimplementer_review']
    assert gate['directions'][label]==sha(path)
    assert read(OUT/'qualification/residual_v3/result.json')['residual_source_SHA']==sha(ROOT/'scripts/round154_residual.py')
    target=OUT/'fixed_prices'/label/f'{implementation}_{name}'
    d={tuple(map(int,k.split(':'))):F(v) for k,v in direction['d_exact'].items()}
    tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        if implementation in ('residual','residual_strong'):
            if implementation=='residual_strong':
                from round154_strengthened import StrengthenedResidualOracle
                qualification=read(OUT/'qualification/strong_residual_v2/result.json')
                assert qualification['PASS'] and qualification['strengthening_source_SHA']==sha(ROOT/'scripts/round154_strengthened.py')
                oracle=StrengthenedResidualOracle(scope,env)
            else: oracle=ResidualOracle(scope,env)
            r=oracle.price(direction['beta'],d,F(direction['tau_exact']),target,cap=float(cap),
                           warm=direction['initial_stocks'])
        else:
            assert implementation=='RN';oracle=Oracle(scope,env,old_joint=True)
            r=oracle.price(direction['beta'],d,target,cap=float(cap),warm=direction['initial_stocks'])
        oracle.close()
    cq,aK=F(direction['C_Q_exact']),F(direction['a_K_exact'])
    effective=max(F(r['lower']),F(direction['inherited_price_lower']))
    upper=min([F(direction['initial_true_price_upper_exact'])]+[F(v['price_exact']) for v in r['stocks']])
    lower=max(F(direction['inherited_hull_lower']),cq+min(aK,effective))
    write(target/'hull_result.json',dict(direction_SHA=sha(path),implementation=implementation,cap=float(cap),
          fresh_raw_price_lower=r['lower'],inherited_price_lower=direction['inherited_price_lower'],effective_price_lower=outward(effective,False),
          true_price_upper=outward(upper,True),target_price_exact=direction['tau_exact'],target_hull_exact=direction['zeta_exact'],
          target_proved=effective>=F(direction['tau_exact']),target_disproved=upper<F(direction['tau_exact']),
          fixed_certificate_lower=outward(cq+min(aK,effective),False),accumulated_hull_lower=outward(lower,False),
          fixed_certificate_ceiling=outward(cq+min(aK,upper),True),hull_upper=direction['inherited_hull_upper'],
          outer_child_seconds=time.perf_counter()-tick,Native=r['calls'],LP=r.get('LP'),stocks=len(r['stocks']),
          same_initial_information=True,performance_lower_distinct_from_inherited=True))
    print(json.dumps(read(target/'hull_result.json')),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
