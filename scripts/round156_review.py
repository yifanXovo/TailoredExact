"""Separate finite-domain arithmetic and saved-model review for actual changes."""
from fractions import Fraction as F
from itertools import product
from round156_common import *

def micro_scope(c,ys,bm,b,gL=0.,gU=1.,weights=None):
    return dict(Bminus=bm,B=b,gamma_L=gL,gamma_U=gU,cutoff=2.,stations=[
        dict(i=j+1,lo=min(y),hi=max(y),support=y,c=x,omega=(weights or [.17]*len(c))[j])
        for j,(x,y) in enumerate(zip(c,ys))])

def exact_value(scope,Y):
    ratios=[F(s['c'])*y for s,y in zip(scope['stations'],Y)]
    S=sum(ratios,F(0));n=len(ratios)
    A=sum((abs(ratios[i]-ratios[j]) for i in range(n) for j in range(i+1,n)),F(0))
    G=A/(n*S) if S else F(0)
    H=sum((F(s['omega'])*abs(F(s['c'])*y-1) for s,y in zip(scope['stations'],Y)),F(0))
    feasible=all(y in s['support'] for s,y in zip(scope['stations'],Y)) and scope['Bminus']<=sum(Y)<=scope['B'] and G<=F(scope['gamma_U'])
    return dict(phi=max(F(scope['gamma_L']),G)+H,H=H,S=S,A=A,feasible=feasible)

def rn_admit(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_pricing import Oracle
    from round156_rn import ObservedRN,GENERATED_SHA
    from round143_lp import semantics
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'review'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.start()
        for j,domain in enumerate([micro_scope([1.,.5],[[0,1,2,3]]*2,1,4),micro_scope([1.,.5],[[0,1,2]]*2,0,3,.05,.9),
                micro_scope([1.,.5],[[0,1,2],[0,1,3]],1,3)]):
            values=[exact_value(domain,Y) for Y in product(*[s['support'] for s in domain['stations']])]
            exact=min(v['phi'] for v in values if v['feasible'])
            d={(s['i'],y):F(s['omega'])*abs(F(s['c'])*y-1) for s in domain['stations'] for y in s['support']}
            plain=Oracle(domain,env,old_joint=True);observed=ObservedRN(domain,env,old_joint=True);events=[]
            assert semantics(plain.model)==semantics(observed.model)
            observed.record_event=events.append
            r=observed.price(1.,d,target/str(j),node_limit=64,absolute_gap=1e-4)
            assert F(r['lower'])<=exact<=F(r['upper'])
            for e in events:
                if e['kind']=='bound':assert F(e['lower'])<=exact
                else:assert exact_value(domain,e['Y'])['phi']==F(e['price_exact'])
            facts.append(dict(exact=str(exact),lower=r['lower'],upper=r['upper'],events=len(events),same_original_RN_matrix=True))
            plain.close();observed.close()
    assert any(row['events'] for row in facts),'must exercise the observation callback, not just exact-DP exits'
    write(target/'result.json',dict(PASS=True,facts=facts,generated_SHA=GENERATED_SHA,
        source_SHA=sha(ROOT/'scripts/round156_rn.py'),review_SHA=sha(__file__),nonimplementer_agent_review=False))
    print(json.dumps(facts),flush=True)

def check_point(model,scope,Y,call):
    """Lift an original integer stock and check EVERY actual Native row exactly."""
    v=exact_value(scope,Y);ss=scope['stations'];S=v['S'];point={'S':S}
    actual={tuple(map(int,k.split(':'))):F(x) for k,x in call['actual_costs'].items()}
    D=sum((actual[s['i'],y] for s,y in zip(ss,Y)),F(0))
    point.update(hard_cost_D=D,hard_cost_W=S*D)
    for s,y0 in zip(ss,Y):
        i=s['i'];point[f'Y[{i}]']=F(y0);point[f'r[{i}]']=F(s['c'])*y0
        for y in s['support']:
            point[f'x[{i},{y}]']=F(y==y0);point[f'Sx[{i},{y}]']=S*F(y==y0)
    for i in range(len(ss)):
        for j in range(i+1,len(ss)):
            point[f'abs[{ss[i]["i"]},{ss[j]["i"]}]']=abs(F(ss[i]['c'])*Y[i]-F(ss[j]['c'])*Y[j])
    from round156_residual import native_row
    q=[]
    for name in ('floor_residual','G_residual'):
        row=native_row(model,name)
        q.append(F(row['rhs'])-sum((F(a)*point[k] for k,a in row['terms'].items() if k!='residual_scaled'),F(0)))
    point['residual_scaled']=max(q)
    for variable in model.getVars():
        value=point[variable.VarName]
        if math.isfinite(variable.LB) and abs(variable.LB)<1e90:assert value>=F(variable.LB),(variable.VarName,'LB',value,variable.LB)
        if math.isfinite(variable.UB) and abs(variable.UB)<1e90:assert value<=F(variable.UB),(variable.VarName,'UB',value,variable.UB)
    for c in model.getConstrs():
        e=model.getRow(c);lhs=sum((F(e.getCoeff(i))*point[e.getVar(i).VarName] for i in range(e.size())),F(0));rhs=F(c.RHS)
        assert (lhs>=rhs if c.Sense=='>' else lhs<=rhs if c.Sense=='<' else lhs==rhs),(c.ConstrName,lhs,rhs)
    true_residual=S*(v['phi']-F(call['tau_exact']))
    assert F(call['scale'])*(point['residual_scaled']-F(call['additional_scaled_error_exact']))<=true_residual
    return point['residual_scaled']<0

def residual_admit(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round156_residual import InventoryResidual
    from round155_oracle import reconstruct
    from round143_lp import semantics
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'review'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    domains=[micro_scope([1.,.5],[[0,1,2,3,4]]*2,1,4,.05,.7),
        micro_scope([1.,.5],[[0,1,2]]*2,0,3,0.,1.),
        micro_scope([1.,.5],[[0,1,2]]*2,1,3,0.,1.,weights=[2.**-51,.17])]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.start()
        for j,domain in enumerate(domains):
            legal=[(Y,exact_value(domain,Y)) for Y in product(*[s['support'] for s in domain['stations']])]
            legal=[(Y,v) for Y,v in legal if v['feasible']];opt=min(v['phi'] for Y,v in legal)
            ordered=sorted(legal,key=lambda p:p[1]['phi']);Yhat,vhat=ordered[min(2,len(ordered)-1)]
            upper=vhat['phi']+F(1,2**40)
            for condition in (False,True):
                folder=target/f'{j}_{int(condition)}';events=[]
                oracle=InventoryResidual(domain,env,folder/'evidence',condition);oracle.record_event=events.append
                for k,tau in enumerate([opt-F(.02),opt+F(.02)]):
                    if tau>=upper:tau=(opt+upper)/2
                    r=oracle.price(tau,upper,[Yhat],folder/f'price{k}',256,time.perf_counter()+30.,lp_cap=0.)
                    assert F(r['lower'])<=opt<=F(r['upper'])
                    c=read(folder/f'price{k}/call.json');covered=0;negative=0
                    for Y,v in legal:
                        if v['S'] and (not condition or v['H']<=upper-F(domain['gamma_L'])):
                            negative+=check_point(oracle.model,domain,Y,c);covered+=1
                    with reconstruct(folder/f'price{k}/matrix_delta.json.gz',gp,env) as back:
                        assert semantics(back)==semantics(oracle.model)
                    # Independently check the finite restricted objective, not its residual minimum.
                    DU=[v['phi'] for Y,v in legal if v['H']<=upper-F(domain['gamma_L'])]
                    assert min(DU)==opt and vhat['H']<=upper-F(domain['gamma_L'])
                    facts.append(dict(domain=j,condition=condition,target=k,opt_exact=str(opt),lower=r['lower'],upper=r['upper'],
                        exact_actual_row_lifts=covered,negative_q_lifts=negative,eplus_exact=c['eplus_exact'],
                        changed_costs=sum(F(c['actual_costs'][key])!=F(value) for key,value in c['intended_costs'].items()),
                        actual_matrix_reconstruction=True,target_proved=r['target_proved'],target_disproved=r['target_disproved']))
                for event in events:
                    if event['kind']=='bound':assert F(event['lower'])<=opt
                    else:assert exact_value(domain,event['Y'])['phi']==F(event['price_exact'])
                oracle.close()
    assert any(v['changed_costs'] and F(v['eplus_exact'])>0 for v in facts)
    assert any(v['negative_q_lifts'] for v in facts)
    assert any(v['target_proved'] for v in facts) and any(v['target_disproved'] for v in facts)
    write(target/'result.json',dict(PASS=True,facts=facts,source_SHA=sha(ROOT/'scripts/round156_residual.py'),review_SHA=sha(__file__),
        zero_and_signed_actual_centered_costs=True,nonimplementer_agent_review=False))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
