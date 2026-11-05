"""Finite qualification of only the new residual interface and product block."""
from fractions import Fraction as F
from itertools import product
from round152_qualify import scope
from round153_pricing import stock_value
from round154_residual import ResidualOracle,recover,transport
from round154_common import *

def check_extension(oracle,value,beta,d,tau,call,inflation=F(0)):
    """Exact Fraction of every actual written row at a true integer extension."""
    ss=oracle.scope['stations']; Y=value['Y']; S=value['S']; n=len(ss)
    rs=[F(s['c'])*y for s,y in zip(ss,Y)]
    A=sum(abs(a-b) for j,a in enumerate(rs) for b in rs[j+1:])+inflation
    D=sum(d[s['i'],y] for s,y in zip(ss,Y))
    residual=max(S*(beta*F(oracle.scope['gamma_L'])+D-tau),beta/F(n)*A+S*(D-tau))
    point={'S':S,'residual_scaled':residual/F(call['scale'])}
    for s,y0,r in zip(ss,Y,rs):
        i=s['i'];point[f'Y[{i}]']=F(y0);point[f'r[{i}]']=r
        for y in s['support']:
            point[f'x[{i},{y}]']=F(y==y0);point[f'Sx[{i},{y}]']=S*(y==y0)
    pairs=list(oracle.a)
    for k,(i,j) in enumerate(pairs):
        point[f'abs[{i},{j}]']=abs(point[f'r[{i}]']-point[f'r[{j}]'])+(inflation if k==0 else 0)
    if hasattr(oracle,'Dcost'):
        written=call['residual_coefficients']['state']
        Dc=sum(F(written[f'{s["i"]}:{y}']) for s,y in zip(ss,Y))
        point['hard_cost_D']=Dc;point['hard_cost_W']=S*Dc
    checks=0
    for v in oracle.model.getVars():
        if v.LB>-1e90: assert point[v.VarName]>=F(v.LB),(v.VarName,'LB')
        if v.UB<1e90: assert point[v.VarName]<=F(v.UB),(v.VarName,'UB')
    for row in oracle.model.getConstrs():
        e=oracle.model.getRow(row); lhs=sum(F(e.getCoeff(k))*point[e.getVar(k).VarName] for k in range(e.size()));rhs=F(row.RHS)
        assert (lhs>=rhs if row.Sense=='>' else lhs<=rhs if row.Sense=='<' else lhs==rhs),(Y,row.ConstrName,str(lhs-rhs))
        checks+=1
    return checks,residual

def run(label='residual_v1',implementation='basic'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    if implementation=='strong':
        from round154_strengthened import StrengthenedResidualOracle
        oracle_class=StrengthenedResidualOracle
    else:
        assert implementation=='basic';oracle_class=ResidualOracle
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    fixtures=[scope([1.,.5],[[0,1,2,3,4]]*2,1,4,.05,.3),
              scope([.5,1.],[[0,1,3],[0,1,2]],0,3,.2,.5),
              scope([.1,.3,.7],[[0,1,2]]*3,1,4,.125,.6)]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        for j,domain in enumerate(fixtures):
            legal=[stock_value(domain,Y) for Y in product(*[s['support'] for s in domain['stations']])]
            legal=[v for v in legal if v['feasible']];assert legal
            costs={(s['i'],y):F(-.625)*y+F(.375)*(s['i']%2) for s in domain['stations'] for y in s['support']}
            if j==2:
                costs={(s['i'],y):F([-.3,.1,.7][y])+F(s['i'])*F(.013) for s in domain['stations'] for y in s['support']}
            for beta in [F(0),F(1.7)]:
                values=[stock_value(domain,v['Y'],beta,costs) for v in legal]
                true=min(v['price'] for v in values); positive=[v for v in values if v['S']>0]
                true_positive=min(v['price'] for v in positive)
                oracle=oracle_class(domain,env)
                previous=[]
                for k,tau in enumerate([true_positive-F(.25),true_positive+F(.25)]):
                    folder=target/f'fixture{j}_beta{float(beta)}_target{k}'
                    inherited=previous[-1]['lower'] if previous else None
                    r=oracle.price(beta,costs,tau,folder,cap=10.,warm=[v['Y'] for v in values],lp_cap=10.,prior_residuals=previous,inherited_lower=inherited)
                    if inherited is not None: assert r['lower']>=inherited
                    assert F(r['lower'])<=true<=F(r['upper'])
                    call=read(folder/'call.json');assert call['q_can_be_negative']
                    if j==2: assert any(F(v)>0 for v in call['state_downward_errors_exact'].values())
                    checks=0
                    for v in positive: checks+=check_extension(oracle,v,beta,costs,tau,call)[0]
                    exact_residual=min(v['S']*(v['price']-tau) for v in positive)
                    assert r['residual_lower_exact'] is not None and F(r['residual_lower_exact'])<=exact_residual
                    assert recover(tau,F(r['residual_lower_exact']),*call['positive_S_bounds'])<=true_positive
                    next_tau=tau+F(.125)
                    moved=transport(F(r['residual_lower_exact']),tau,next_tau,*call['positive_S_bounds'])
                    assert moved<=min(v['S']*(v['price']-next_tau) for v in positive)
                    previous_tau=tau-F(.125)
                    moved_back=transport(F(r['residual_lower_exact']),tau,previous_tau,*call['positive_S_bounds'])
                    assert moved_back<=min(v['S']*(v['price']-previous_tau) for v in positive)
                    if k==1: assert r['calls'][0]['native_incumbent']<0
                    if k==0: assert F(r['residual_lower_exact'])>0
                    facts.append(dict(fixture=j,beta=float(beta),tau_exact=str(tau),true_price_exact=str(true),
                                      true_positive_exact=str(true_positive),exact_residual=str(exact_residual),
                                      lower=r['lower'],upper=r['upper'],residual_lower_exact=r['residual_lower_exact'],
                                      all_integer_actual_row_checks=checks,zero_branch=r['zero_lower'] is not None,
                                      hard_resource_and_Gupper_retained=True,transport_checked=True))
                    previous.append(r)
                # Nonminimal abs completion is feasible but has no price authority.
                value=min(positive,key=lambda v:v['G']);trueA=value['G']*len(domain['stations'])*value['S']
                slack=F(len(domain['stations']))*F(domain['gamma_U'])*value['S']-trueA
                if slack>0:
                    checks,res=check_extension(oracle,value,beta,costs,tau,call,slack/2)
                    assert res>=value['S']*(value['price']-tau)
                    facts.append(dict(nonminimal_A=True,beta=float(beta),actual_row_checks=checks,
                                      auxiliary_completion_not_used_as_true_price=True))
                oracle.close()
        zero=scope([1.,.5],[[0],[0]],0,0,.2,.5)
        oracle=oracle_class(zero,env);r=oracle.price(0.,{(1,0):F(-1),(2,0):F(.25)},F(-.8),target/'zero_only',lp_cap=0)
        assert r['lower']==r['upper']==-.75 and not r['calls'];oracle.close()
        facts.append(dict(zero_only=True,price=r['lower']))
    # C3 strictness and the required hard-total limitation, using exact numbers.
    S,D=F(3),F(1);aggregate_W=F(2)
    assert aggregate_W>=2*D and aggregate_W>=4*D+2*S-8
    assert aggregate_W<=4*D and aggregate_W<=2*D+2*S-4
    assert S*D==3>aggregate_W
    state_point=dict(S=F(3,2),x1=F(1,2),z1=F(1,2),z0=F(1))
    W=2*state_point['z1'];assert W==1<state_point['S']
    for z,x in [(state_point['z1'],state_point['x1']),(state_point['z0'],state_point['x1'])]:
        assert x<=z<=2*x and state_point['S']-2*(1-x)<=z<=state_point['S']-(1-x)
    assert 2*state_point['z1']<state_point['S'] # total=1 product row cuts it
    write(target/'result.json',dict(PASS=True,facts=facts,residual_source_SHA=sha(ROOT/'scripts/round154_residual.py'),
          qualification_source_SHA=sha(__file__),matrix_readback=True,block_strictness=True,
          implementation=implementation,strengthening_source_SHA=sha(ROOT/'scripts/round154_strengthened.py') if implementation=='strong' else None,
          tighter_hard_total_counterexample=True,total_product_excludes_counterexample=True,
          no_claim_of_RN_or_full_Q_dominance=True,no_performance_sample=True))
    print(json.dumps(dict(PASS=True,fixtures=len(facts))),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
