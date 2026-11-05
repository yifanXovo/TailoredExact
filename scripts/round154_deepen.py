"""One registered midpoint proof task on a saved, updated complete pool.

Reuse the saved Q certificate and signed direction, recompute every current
stock price, and lower a_K if necessary. A threshold below the current
ceiling tests proof quality after the previous near-upper tasks found columns.
"""
from fractions import Fraction as F
from round143_math import outward
from round153_pricing import stock_value
from round154_common import *

def freeze(label, previous, iteration):
    tick=time.perf_counter();prior=read(previous);step=Path(iteration);old=read(step/'direction.json')
    assert not prior.get('refresh_required',False)
    assert prior['scope']==old['scope'] and prior['Q_SHA']==old['Q_SHA']
    cert=load_gz(step/'certificate.json.gz');assert cert['qualified']
    costs={tuple(map(int,k.split(':'))):F(v) for k,v in old['d_exact'].items()}
    prices={tuple(Y):stock_value(prior['scope'],Y,old['beta'],costs) for Y in prior['columns']}
    assert all(v['feasible'] for v in prices.values())
    warm=sorted(prices,key=lambda Y:(prices[Y]['price'],Y))[:4]
    true_min=prices[warm[0]]['price'];cq=F(cert['lower_exact']);aK=min(F(cert['a_raw']),true_min)
    ceiling=cq+min(aK,true_min);zeta=min((F(prior['lower'])+F(prior['upper']))/2,ceiling-F(1e-7))
    assert zeta>F(prior['lower'])+F(1e-4)
    price=read(step/'pricing/result.json')
    assert price['scope']==old['scope'] and price['beta']==old['beta'] and price['d_exact']==old['d_exact']
    inherited=F(price['lower']);delta=max(F(0),aK-inherited)
    cert.update(a_true_RMP=outward(aK,False),a_true_RMP_exact=str(aK),true_column_min_exact=str(true_min),
        D_K=outward(cq+aK,False),D_K_exact=str(cq+aK),delta=outward(delta,True),delta_exact=str(delta),
        coupled_lower=outward(cq+min(aK,inherited),False))
    folder=OUT/'directions'/label;folder.mkdir(parents=True,exist_ok=False)
    save_gz(folder/'certificate.json.gz',cert)
    sourcebounds=Path(old['source_Q_bounds']);save_gz(folder/'Q_bounds.json.gz',load_gz(sourcebounds))
    d=dict(old,label=label,mode='saved_updated_midpoint',UTC=utc(),Q_path=str(OLD153/'reference'/prior['role']/'direct/model.mps'),
        prior_result=str(previous),prior_result_SHA=sha(previous),columns=len(prices),supports=len(prior['supports']),
        source_iteration=None,source_loop_iteration=str(step),source_certificate_SHA=sha(step/'certificate.json.gz'),
        source_direction_SHA=sha(step/'direction.json'),source_Q_bounds=str(folder/'Q_bounds.json.gz'),
        C_Q_exact=str(cq),a_K_exact=str(aK),zeta_exact=str(zeta),tau_exact=str(zeta-cq),
        inherited_hull_lower=prior['lower'],inherited_hull_upper=prior['upper'],
        inherited_price_lower=outward(inherited,False),inherited_price_lower_exact=str(inherited),
        inherited_price_sources=[dict(path=str(step/'pricing/result.json'),SHA256=sha(step/'pricing/result.json'))],
        initial_stocks=[list(Y) for Y in warm],initial_true_price_upper=outward(true_min,True),initial_true_price_upper_exact=str(true_min),
        fixed_certificate_ceiling=outward(ceiling,True),fixed_certificate_ceiling_exact=str(ceiling),ceiling_exact=str(ceiling),
        target_hull=float(zeta),target_price=float(zeta-cq),
        hull_lower_from_inherited_price=outward(cq+min(aK,inherited),False),ceiling_is_not_full_hull_upper=True,
        target_rule='midpoint of inherited full-hull interval, capped below updated true-stock certificate ceiling by1e-7',
        motive='near-upper tasks returned counterexamples; test a meaningful interior proof threshold instead of extending a rejected target',
        frozen_before_new_fixed_prices=True,seconds=time.perf_counter()-tick)
    write(folder/'direction.json',d)
    print(json.dumps({k:d[k] for k in ['label','target_hull','target_price','fixed_certificate_ceiling','inherited_price_lower','seconds']}),flush=True)

def compare(label,implementation,cap='600',name='screen'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round154_goal_oracle import TargetResidualOracle,TargetRNOracle
    configure();affinity();assert binding()['sha256']==DLL_SHA
    path=OUT/'directions'/label/'direction.json';d=read(path)
    gate=read(OUT/'review/interior_proof_admission.json')
    assert gate['decision']=='ACCEPT' and gate['independent_nonimplementer_review']
    assert gate['source_SHA']==sha(__file__) and gate['directions'][label]==sha(path)
    q=read(OUT/'qualification/goal_stop_v1/result.json');assert q['PASS']
    assert q['goal_oracle_SHA']==sha(ROOT/'scripts/round154_goal_oracle.py')
    assert q['core_SHA']==sha(ROOT/'scripts/round154_residual.py') and q['strong_SHA']==sha(ROOT/'scripts/round154_strengthened.py')
    assert q['RN_core_SHA']==sha(ROOT/'scripts/round153_pricing.py')
    target=OUT/'fixed_prices'/label/f'{implementation}_{name}';tick=time.perf_counter()
    costs={tuple(map(int,k.split(':'))):F(v) for k,v in d['d_exact'].items()}
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        if implementation=='residual_goal':
            oracle=TargetResidualOracle(d['scope'],env)
            r=oracle.price(d['beta'],costs,F(d['tau_exact']),target,cap=float(cap),warm=d['initial_stocks'])
        else:
            assert implementation=='RN_goal';oracle=TargetRNOracle(d['scope'],env,old_joint=True)
            r=oracle.price(d['beta'],costs,target,cap=float(cap),warm=d['initial_stocks'],tau=F(d['tau_exact']))
        oracle.close()
    cq,aK=F(d['C_Q_exact']),F(d['a_K_exact']);effective=max(F(r['lower']),F(d['inherited_price_lower']))
    upper=min([F(d['initial_true_price_upper_exact'])]+[F(v['price_exact']) for v in r['stocks']])
    write(target/'hull_result.json',dict(direction_SHA=sha(path),implementation=implementation,cap=float(cap),
        fresh_raw_price_lower=r['lower'],inherited_price_lower=d['inherited_price_lower'],effective_price_lower=outward(effective,False),
        true_price_upper=outward(upper,True),target_price_exact=d['tau_exact'],target_hull_exact=d['zeta_exact'],
        target_proved=effective>=F(d['tau_exact']),target_disproved=upper<F(d['tau_exact']),
        fixed_certificate_lower=outward(cq+min(aK,effective),False),
        accumulated_hull_lower=max(d['inherited_hull_lower'],outward(cq+min(aK,effective),False)),
        fixed_certificate_ceiling=outward(cq+min(aK,upper),True),hull_upper=d['inherited_hull_upper'],
        outer_child_seconds=time.perf_counter()-tick,Native=r['calls'],LP=r.get('LP'),stocks=len(r['stocks']),
        same_initial_information=True,performance_lower_distinct_from_inherited=True))
    print(json.dumps(read(target/'hull_result.json')),flush=True)

def study(label):
    for implementation in ['RN_goal','residual_goal']:
        run(f'{label}_{implementation}_screen_v1',900,'round154_deepen.py',['compare',label,implementation,'600','screen'])
    screens=[read(OUT/'fixed_prices'/label/f'{i}_screen/hull_result.json') for i in ['RN_goal','residual_goal']]
    if any(r['target_disproved'] for r in screens):
        write(OUT/'fixed_prices'/label/'long_skip.json',dict(reason='interior_target_disproved_by_verified_true_stock',
            no_family_or_full_hull_rejection=True));return
    if any(r['target_proved'] for r in screens):
        write(OUT/'fixed_prices'/label/'long_skip.json',dict(reason='declared_interior_target_already_proved_in_screen',
            no_unnecessary_long_proof=True));return
    for implementation in ['residual_goal','RN_goal']:
        run(f'{label}_{implementation}_long_v1',3900,'round154_deepen.py',['compare',label,implementation,'3600','long'])
        result=read(OUT/'fixed_prices'/label/f'{implementation}_long/hull_result.json')
        if result['target_disproved']:
            write(OUT/'fixed_prices'/label/'remaining_long_skip.json',dict(reason='interior_target_disproved_by_verified_true_stock_in_long',
                implementation=implementation,new_ceiling=result['fixed_certificate_ceiling'],
                no_matched_long_speed_claim=True,no_family_or_full_hull_rejection=True));break

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
