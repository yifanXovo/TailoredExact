"""Small full-enumeration controls for the actually new coupled interfaces."""
from itertools import product
from fractions import Fraction as F
from round152_qualify import scope
from round152_small import build
from round153_coupled import Master,support_row
from round153_pricing import Oracle,stock_value,serial_stock
from round153_lp import optimize
from round153_common import *

def run(label='v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    d=scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75,[.125]*3)
    universe=[stock_value(d,Y) for Y in product(*[s['support'] for s in d['stations']])]
    universe=[v for v in universe if v['feasible']]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with build(gp,env,d) as m:
            full=Master(m,d,gp,env)
            for v in universe:full.add(v['Y'])
            m.update();rr=optimize(m,target/'all_columns');assert rr['Status']==2
            primal=full.primal();assert primal['qualified'],primal
            all_value=m.ObjVal;exact_global=min(v['phi'] for v in universe)
            assert abs(all_value-float(exact_global))<=2e-8
            facts.append(dict(tag='all_columns',columns=len(universe),value=all_value,exact_global=str(exact_global),primal=primal))
        with build(gp,env,d) as m:
            restricted=Master(m,d,gp,env)
            candidate=sorted(universe,key=lambda v:v['phi'],reverse=True)[0]
            restricted.add(candidate['Y']);m.update();rr=optimize(m,target/'restricted')
            assert rr['Status']==2
            a,pi,beta=restricted.prices();oracle=Oracle(d,env)
            price=oracle.price(beta,{k:-v for k,v in pi.items()},target/'restricted_pricing',cap=20)
            cert=restricted.certificate(a,pi,beta,price['lower'])
            save_gz(target/'restricted/certificate.json.gz',cert)
            assert cert['coupled_lower']<=all_value+1e-8<=m.ObjVal+1e-8
            assert price['upper']-a<0
            row,transport=support_row(d,beta,pi,price['lower'],0)
            for v in universe:
                for g in [v['f'],F(d['gamma_U'])]:
                    lhs=F(row['terms'].get('G',0))*g+sum(F(row['terms'].get(f'state_{s["i"]}_{y}',0)) for s,y in zip(d['stations'],v['Y']))
                    assert lhs>=F(row['rhs'])
            facts.append(dict(tag='restricted_bounds',RMP_upper=m.ObjVal,all_columns_value=all_value,
                              qualified_lower=cert['coupled_lower'],negative_reduced_cost=price['upper']-a,
                              beta=beta,transport=transport,all_integer_completions_checked=True))
            oracle.close()
        # Fixed marginals are a qualification fixture only. A missing singleton
        # column is infeasible although the full coupled model is feasible.
        with build(gp,env,d) as m:
            marg={(1,1):1.,(2,1):.75,(2,2):.25,(3,2):.5,(3,3):.5}
            for s in d['stations']:
                for y in s['support']:m.addConstr(m.getVarByName(f'state_{s["i"]}_{y}')==marg.get((s['i'],y),0.))
            m.update();master=Master(m,d,gp,env);master.add([1,1,2]);m.update()
            missing=optimize(m,target/'missing_columns');assert missing['Status']==3
            master.start_phase();phase=optimize(m,target/'phase_I');assert phase['Status']==2 and m.ObjVal>0
            old_artificial=m.ObjVal
            for v in universe:master.add(v['Y'])
            m.update();fullphase=optimize(m,target/'phase_I_full_columns');assert fullphase['Status']==2 and m.ObjVal<1e-8
            master.finish_phase();normal=optimize(m,target/'phase_II');assert normal['Status']==2 and master.primal()['qualified']
            facts.append(dict(tag='missing_columns_phase_I',restricted_status=missing['Status'],phase_I_objective=old_artificial,
                              full_phase_I_objective=fullphase['objective'],normal_upper=m.ObjVal,
                              upper_from_artificials=False,full_hull_feasible=True))
        pd=scope([.5,1.],[[0,1,3],[0,1,2]],0,3,.2,.5)
        pu=[stock_value(pd,Y) for Y in product(*[s['support'] for s in pd['stations']])]
        pu=[v for v in pu if v['feasible']]
        for beta in [0.,2.5,32.]:
            costs={(s['i'],y):(-.625 if y%2 else .375) for s in pd['stations'] for y in s['support']}
            true=min(stock_value(pd,v['Y'],beta,costs)['price'] for v in pu)
            oracle=Oracle(pd,env,old_joint=False);price=oracle.price(beta,costs,target/f'price_beta_{beta}',cap=20)
            assert F(price['lower'])<=true<=F(price['upper']),price
            facts.append(dict(tag='general_price',beta=beta,exact=str(true),lower=price['lower'],upper=price['upper'],calls=len(price['calls']),
                              hard_resource_and_Gupper=True,zero_and_nonminimal_completion=True))
            oracle.close()
        # Necessary old NC/TS additions in the pricing relaxation must preserve
        # the full integer minimum as checked by exhaustive enumeration.
        costs={(s['i'],y):(.3*y if s['i']%2 else -.2*y) for s in d['stations'] for y in s['support']}
        true=min(stock_value(d,v['Y'],1.7,costs)['price'] for v in universe)
        oracle=Oracle(d,env,old_joint=True);price=oracle.price(1.7,costs,target/'price_with_old_joint',cap=20)
        assert F(price['lower'])<=true<=F(price['upper'])
        facts.append(dict(tag='old_joint_price',exact=str(true),lower=price['lower'],upper=price['upper']))
        oracle.close()
    write(target/'result.json',dict(PASS=True,facts=facts,scope=d,
          covers=['RMP_upper_direction','dual_with_single_intercept_correction','true_f_rounding','negative_reduced_cost',
                  'missing_columns_and_Phase_I','full_domain_beta_zero','signed_costs','nonminimal_completion','coefficient_transport'],
          no_performance_sample=True))
    print(json.dumps(dict(PASS=True,fixtures=len(facts))),flush=True)

def joint_control(label):
    from round100_gurobi_runtime import gp
    from round150_lp import affinity
    configure();affinity();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    d=scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75,[.125]*3)
    universe=[stock_value(d,Y) for Y in product(*[s['support'] for s in d['stations']])]
    universe=[v for v in universe if v['feasible']]
    costs={(s['i'],y):(.3*y if s['i']%2 else -.2*y) for s in d['stations'] for y in s['support']}
    true=min(stock_value(d,v['Y'],1.7,costs)['price'] for v in universe)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        oracle=Oracle(d,env,old_joint=True);m=oracle.model;checks=0
        for v in universe:
            t=1/v['S'];point={'t':t,'q':v['f']}
            for s,y0 in zip(d['stations'],v['Y']):
                i=s['i'];point[f'z[{i}]']=y0*t;point[f'r[{i}]']=F(s['c'])*y0*t
                for y in s['support']:
                    point[f'x[{i},{y}]']=F(y==y0);point[f'w[{i},{y}]']=t*(y==y0)
            for i,j in combinations([s['i'] for s in d['stations']],2):point[f'a[{i},{j}]']=abs(point[f'r[{i}]']-point[f'r[{j}]'])
            for c in m.getConstrs():
                e=m.getRow(c);lhs=sum(F(e.getCoeff(k))*point[e.getVar(k).VarName] for k in range(e.size()));rhs=F(c.RHS)
                assert lhs>=rhs if c.Sense=='>' else lhs<=rhs if c.Sense=='<' else lhs==rhs,(v['Y'],c.ConstrName,lhs,rhs)
                checks+=1
        price=oracle.price(1.7,costs,target/'price',cap=20);assert F(price['lower'])<=true<=F(price['upper'])
        write(target/'result.json',dict(PASS=True,all_integer_row_checks=checks,stocks=len(universe),true_price=str(true),
              lower=price['lower'],upper=price['upper'],transport=oracle.joint_transport,
              review_issue='TS x-coefficient multiplication rounding transported with one-hot support',old_results_not_rerun=True))
        oracle.close()

def native_beta_control(label):
    from round100_gurobi_runtime import gp
    from round150_lp import affinity
    configure();affinity();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    d=scope([1.,.5],[[0,1,2,3,4]]*2,1,4,.05,.3)
    universe=[stock_value(d,Y) for Y in product(*[s['support'] for s in d['stations']])]
    universe=[v for v in universe if v['feasible']]
    costs={(s['i'],y):(-2.*y if s['i']==1 else .5*y) for s in d['stations'] for y in s['support']}
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for beta in [0.,2.5,32.]:
            true=min(stock_value(d,v['Y'],beta,costs)['price'] for v in universe)
            oracle=Oracle(d,env);r=oracle.price(beta,costs,target/f'beta_{beta}',cap=20)
            assert r['calls'] and F(r['lower'])<=true<=F(r['upper'])
            facts.append(dict(beta=beta,exact=str(true),lower=r['lower'],upper=r['upper'],calls=len(r['calls']),guard=r['calls'][0]['guard_original']))
            oracle.close()
    write(target/'result.json',dict(PASS=True,scope=d,facts=facts,forced_DP_witness_violates_Gupper=True,
          prior_fallback_tests_reused=True,new_Native_beta_interfaces_covered=True))

def stabilize_control(label,level=False):
    from round100_gurobi_runtime import gp
    from round150_lp import affinity
    from round153_stabilize import select_dual
    configure();affinity();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    d=scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75,[.125]*3)
    universe=[stock_value(d,Y) for Y in product(*[s['support'] for s in d['stations']])];universe=[v for v in universe if v['feasible']]
    exact=min(v['phi'] for v in universe)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with build(gp,env,d) as m:
            master=Master(m,d,gp,env);master.add(max(universe,key=lambda v:v['phi'])['Y']);m.update()
            r=optimize(m,target/'RMP');assert r['Status']==2
            band=(m.ObjVal-float(exact))/2 if level else 1e-7
            selected,record=select_dual(master,target/'dual_select',band=band);assert selected
            a=selected['hull_convexity'];pi={k:selected[c.ConstrName] for k,c in master.links.items()};beta=max(0.,selected['hull_gini'])
            oracle=Oracle(d,env,old_joint=True);price=oracle.price(beta,{k:-v for k,v in pi.items()},target/'price',cap=20)
            cert=master.certificate(a,pi,beta,price['lower'],selected);assert F(cert['coupled_lower'])<=exact<=F(m.ObjVal)
            assert price['upper']<a
            save_gz(target/'certificate.json.gz',cert)
            write(target/'result.json',dict(PASS=True,exact_all_columns_value=str(exact),lower=cert['coupled_lower'],
                  RMP_upper=m.ObjVal,beta=beta,negative_reduced_cost=price['upper']-a,
                  dual_selection_seconds=record['seconds'],no_potential_box=True,
                  selected_dual_not_primal_ObjVal_used=True,dual_true_price_correction=True,
                  level_selection=level,dual_band=band,level_not_used_as_lower=True))
            oracle.close()

if __name__=='__main__':
    if sys.argv[1]=='joint':
        from itertools import combinations
        joint_control(sys.argv[2])
    elif sys.argv[1]=='native_beta':native_beta_control(sys.argv[2])
    elif sys.argv[1]=='stabilize':stabilize_control(sys.argv[2])
    elif sys.argv[1]=='level':stabilize_control(sys.argv[2],True)
    else:run(*sys.argv[1:])
