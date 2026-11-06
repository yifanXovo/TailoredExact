"""Targeted checks of the new interfaces, using enumeration and reconstruction."""
from fractions import Fraction as F
from itertools import product
from round152_qualify import scope
from round153_coupled import Master,support_row
from round153_pricing import stock_value,serial_stock
from round143_math import outward
from round155_loop import direction,solve,classify_columns,witness,column_usage
from round155_oracle import make_oracle,reconstruct,semantic_hash
from round143_lp import semantics
from round155_common import *

def run(label='interfaces_v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    old=read(OLD154/'qualification/goal_stop_v1/result.json');assert old['PASS']
    for key,name in [('core_SHA','round154_residual.py'),('strong_SHA','round154_strengthened.py'),
                     ('goal_oracle_SHA','round154_goal_oracle.py'),('RN_core_SHA','round153_pricing.py')]:
        assert old[key]==sha(ROOT/'scripts'/name)
    domain=scope([1.,.5],[[0,1,2,3,4]]*2,1,4,.05,.31)
    costs={(s['i'],y):F(-2)*y if s['i']==1 else F(.5)*y for s in domain['stations'] for y in s['support']}
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for rule in ['first','bounded']:
            oracle=make_oracle(domain,env,rule,target/rule/'oracle_evidence')
            for j,beta in enumerate([F(0),F(1.7)]):
                values=[stock_value(domain,Y,beta,costs) for Y in product(*[s['support'] for s in domain['stations']])]
                legal=[v for v in values if v['feasible']];exact=min(v['price'] for v in legal)
                folder=target/rule/f'call{j}'
                r=oracle.price(beta,costs,exact+F(.25),folder,cap=20.,warm=[max(legal,key=lambda v:v['price'])['Y']],
                    lp_cap=0.,node_limit=256 if rule=='bounded' else None)
                assert F(r['lower'])<=exact<=F(r['upper'])
                with reconstruct(folder/'matrix_delta.json.gz',gp,env) as back:
                    assert semantics(back)==semantics(oracle.model)
                for v in r['stocks']:
                    checked=stock_value(domain,v['Y'],beta,costs)
                    assert checked['feasible'] and checked['price']==F(v['price_exact'])
                facts.append(dict(rule=rule,call=j,true_price_exact=str(exact),lower=r['lower'],upper=r['upper'],
                    complete_matrix_reconstructed=True,Optimize_on_reconstruction=0,Native_status=r['calls'][0]['Status']))
            oracle.close()
        # The observed repair: Native drops tiny centered state coefficients.
        # Enumerate one complete small domain, exercising both existing rules.
        tiny_scope=scope([1.,.5],[[0,1,2]]*2,1,4,0.,1.)
        tiny_cost={(i,y):v for i in [1,2] for y,v in enumerate([F(-1),-F(1,2**60),F(1)])}
        for rule in ['first','bounded']:
            values=[stock_value(tiny_scope,Y,F(1.7),tiny_cost) for Y in product([0,1,2],repeat=2)]
            legal=[v for v in values if v['feasible']];exact=min(v['price'] for v in legal)
            folder=target/('tiny_'+rule)
            oracle=make_oracle(tiny_scope,env,rule,folder/'oracle_evidence')
            returned=oracle.price(F(1.7),tiny_cost,exact+F(.25),folder/'price',cap=20.,
                warm=[max(legal,key=lambda v:v['price'])['Y']],lp_cap=0.,node_limit=256 if rule=='bounded' else None)
            transport=returned['native_state_transport']
            assert transport['changed_state_costs'] and F(transport['additional_scaled_residual_error_exact'])>0
            assert transport['actual_cost_bounds_cover_complete_domain'] and transport['original_numerical_guard_retained']
            assert F(returned['lower'])<=exact<=F(returned['upper'])
            with reconstruct(folder/'price/matrix_delta.json.gz',gp,env) as back:
                assert semantics(back)==semantics(oracle.model)
            facts.append(dict(rule=rule,observed_tiny_state_omission_exercised=True,
                exact_price=str(exact),corrected_lower=returned['lower'],
                extra_scaled_error_exact=transport['additional_scaled_residual_error_exact'],
                native_bound_accepted=transport['native_bound_accepted'],complete_matrix_reconstructed=True))
            oracle.close()
        # A full two-site Q gives a known complete-hull optimum by enumeration.
        small=scope([1.,1.],[[0,1],[0,1]],1,2,0.,1.)
        with gp.Model(env=env) as m:
            G=m.addVar(lb=0,ub=1,obj=1,name='G')
            x={}
            for s in small['stations']:
                for y in s['support']:
                    x[s['i'],y]=m.addVar(lb=0,ub=1,obj=(.2 if s['i']==1 else .3)*y,name=f'state_{s["i"]}_{y}')
                m.addConstr(gp.quicksum(x[s['i'],y] for y in s['support'])==1,name=f'onehot_{s["i"]}')
            m.addConstr(x[1,1]+x[2,1]>=1,name='total_lower');m.update()
            master=Master(m,small,gp,env)
            assert master.add([1,0]) and master.add([0,1]) and not master.add([1,0])
            rr=solve(master,target/'micro_before',save_model=True);assert rr['Status']==2 and rr['primal']['qualified']
            dr=direction(master)
            old_cert=master.certificate(float(dr['certificate']['a_raw']),{k:float(v) for k,v in dr['pi'].items()},
                float(dr['beta']),outward(dr['fallback'],False))
            assert old_cert['lower_exact']==dr['certificate']['lower_exact']
            assert old_cert['a_true_RMP_exact']==str(dr['aK'])
            tau=dr['aK']-F(.01)
            v=stock_value(small,[1,1],dr['beta'],dr['d']);assert v['price']<tau
            feedback,added=classify_columns(master,[serial_stock(v)],dr['beta'],dr['d'],dr['aK'],tau)
            assert added==[(1,1)] and feedback[0]['negative']
            after=solve(master,target/'micro_after',save_model=True);assert after['Status']==2 and after['primal']['qualified']
            assert after['objective']<rr['objective']-.1 and abs(after['objective']-(.5+1e-8))<1e-10
            assert master.columns[1,1].X>.999999
            tracking={(1,1):dict(origin_phase='prior_phase',added_iteration=0,used_iterations=0,
                maximum_weight=0.,first_used_iteration=None,first_used_phase=None)}
            used=column_usage(master,tracking,'continued_phase',0,target/'micro_usage.json.gz')
            usage=load_gz(target/'micro_usage.json.gz')
            assert tracking[1,1]['first_used_phase']=='continued_phase' and used[0]['origin_phase']=='prior_phase'
            assert usage['marginal_contributions']=={'1:1':1.,'2:1':1.}
            dr2=direction(master);full_min=min(stock_value(small,Y,dr2['beta'],dr2['d'])['price']
                for Y in [(0,1),(1,0),(1,1)])
            lower=dr2['cq']+min(dr2['aK'],full_min)
            assert lower<=F(.5)+F(1e-12) and float(lower)>.5-1e-7
            duplicate=serial_stock(stock_value(small,[1,1],dr2['beta'],dr2['d']))
            duplicate_rows,none=classify_columns(master,[duplicate],dr2['beta'],dr2['d'],dr2['aK'],dr2['aK']-F(.01))
            assert not none and not duplicate_rows[0]['new']
            row,correction=support_row(small,dr2['beta'],dr2['pi'],outward(full_min,False),0)
            for Y in [(0,1),(1,0),(1,1)]:
                v=stock_value(small,Y)
                point={'G':v['f']}|{f'state_{s["i"]}_{y}':F(int(y==y0)) for s,y0 in zip(small['stations'],Y) for y in s['support']}
                assert sum((F(a)*point[k] for k,a in row['terms'].items()),F(0))>=F(row['rhs'])
            witness(master,target/'micro_primal.json.gz',after['primal'])
            facts.append(dict(direct_equals_inherited_certificate=True,strict_negative_column_fed_back=True,
                duplicate_not_counted=True,subsequent_weight=master.columns[1,1].X,before=rr['objective'],after=after['objective'],
                enumerated_hull_value=.5,qualified_lower=float(lower),support_valid_on_entire_enumerated_domain=True))
    result=dict(PASS=True,facts=facts,scope='new dual/cache, incremental matrix, dedup, feedback and observed Native state-coefficient transport',
        reused_residual_qualification=str(OLD154/'qualification/goal_stop_v1/result.json'),
        inherited_qualification_SHA=sha(OLD154/'qualification/goal_stop_v1/result.json'),
        loop_SHA=sha(ROOT/'scripts/round155_loop.py'),oracle_SHA=sha(ROOT/'scripts/round155_oracle.py'),
        price_certificate_SHA=sha(ROOT/'scripts/round155_price_certificate.py'),
        checker_SHA=sha(__file__),no_new_production_behavior=True)
    write(target/'result.json',result)
    print(json.dumps(dict(PASS=True,checks=len(facts))),flush=True)

def admit(label='interfaces_v1'):
    path=OUT/'qualification'/label/'result.json';r=read(path)
    assert r['PASS'] and r['loop_SHA']==sha(ROOT/'scripts/round155_loop.py') and r['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    assert r['price_certificate_SHA']==sha(ROOT/'scripts/round155_price_certificate.py')
    write(OUT/'review/loop_admission.json',dict(decision='ACCEPT',source_SHA=r['loop_SHA'],oracle_SHA=r['oracle_SHA'],
        price_certificate_SHA=r['price_certificate_SHA'],actual_Native_state_transport_exercised=True,
        qualification_SHA=sha(path),review_method='independent exact enumeration, inherited-certificate comparison and matrix reconstruction',
        nonimplementer_agent_review=False,full_Q_no_shrinkage=True,signed_residual_conversion_unchanged=True,
        no_bound_from_selection_objective=True,upper_requires_full_primal=True,
        no_saturation_claim_from_screen=True,static_review='review/interface_math.md'))

if __name__=='__main__': globals()[sys.argv[1]](*sys.argv[2:])
