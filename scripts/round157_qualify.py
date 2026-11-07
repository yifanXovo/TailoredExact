"""Separate saved-row lifts and exhaustive tiny-domain physical qualification."""
import itertools
from round157_fleet import build, lift, verify, decode
from round157_inventory import instance, family, classes
from round157_common import *

def enumerated(data,members):
    # Independent ordered-partition enumeration: no solver rows or potentials.
    n=data['n'];M=len(data['Q']);b=data['initial'];d=data['distance']
    for Y in members:
        active=[i for i in range(1,n+1) if b[i]!=Y[i-1]]
        for order in itertools.permutations(active):
            for cuts in itertools.combinations_with_replacement(range(len(order)+1),M-1):
                boundaries=(0,)+cuts+(len(order),);routes=[];valid=True
                for k in range(M):
                    nodes=[0]+list(order[boundaries[k]:boundaries[k+1]])+[0]
                    load=0;pick=0;operations=[]
                    for i in nodes[1:-1]:
                        delta=b[i]-Y[i-1];load+=delta;pick+=max(0,delta)
                        if not 0<=load<=data['Q'][k]:valid=False;break
                        operations.append(dict(station=i,pickup=max(0,delta),drop=max(0,-delta)))
                    if not valid:break
                    duration=sum(d[i][j] for i,j in zip(nodes,nodes[1:]))+(data['pickup']+data['drop'])*pick
                    if duration>data['T']+1e-10:valid=False;break
                    if len(nodes)>2:routes.append(dict(vehicle=k,nodes=nodes,operations=operations))
                if valid:return dict(routes=routes)
    return None

def micro(initial,Y,Q,T,positions=None,handling=.5):
    n=len(Y);positions=positions or list(range(n+1))
    return dict(n=n,Q=Q,initial=[987654]+initial,capacity=[999999]+[max(4,a,v) for a,v in zip(initial,Y)],
                target=[0]+[2]*n,weights=[0]+[1]*n,lam=.15,pickup=handling,drop=handling,T=T,
                distance=[[abs(a-b) for b in positions] for a in positions])

def qualify():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round143_lp import residual
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification/v1';target.mkdir(parents=True,exist_ok=False)
    facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,source in read(OUT/'inventory_families.json').items():
            data=instance(source['panel']);witness=source['positive_control']['witness'];checked=verify(data,witness)
            assert checked['original_T_feasible']
            model,ref=build(data,{i:[v] for i,v in enumerate(checked['Y'],1)},env)
            point=lift(data,ref,witness);q=residual(model,point)
            assert q['constraints']<=1e-7 and q['bounds']<=1e-7,q
            path=target/f'{role}_positive.mps';model.write(str(path))
            for v in model.getVars():v.Start=point[v.VarName]
            model.Params.Threads=1;model.Params.Seed=0;model.Params.SolutionLimit=1;model.Params.NodeLimit=128
            model.optimize();assert model.SolCount
            decoded,check=decode(data,ref);assert check['original_T_feasible']
            model.dispose()
            with gp.read(str(path),env=env) as reopened:
                qr=residual(reopened,point);assert qr==q
            write(target/f'{role}_positive_lift.json',dict(point=point,quality=q,physical=checked,
                witness_source_SHA=source['positive_control']['SHA'],model_SHA=sha(path)))
            facts.append(dict(role=role,positive_control='PASS',original_T=data['T'],physical_J=checked['J'],
                              maximum_duration=checked['maximum_duration'],mapped_all_rows=q,Optimize=1))
        cases=[('heterogeneous_pass',[3,0],[1,2],[1,3],12,None),
               ('heterogeneous_fail',[3,0],[1,2],[1,1],12,None),
               ('loaded_return_pass',[3],[1],[2],4,None),
               ('loaded_return_time_fail',[3],[1],[2],3,None),
               ('zero_empty',[0,0],[0,0],[2],1,None),
               ('depot_placeholder_no_supply',[1,0],[1,1],[3],100,None),
               ('space_fixed_fail',[2,0],[0,2],[2],10,[0,1,100]),
               ('space_family_pass',[2,0],[0,2],[2],10,[0,1,100])]
        for name,initial,Y,Q,T,positions in cases:
            data=micro(initial,Y,Q,T,positions)
            members=[Y] if name!='space_family_pass' else [Y,[2,0]]
            scope=dict(gamma_L=0,gamma_U=1.,Bminus=0,B=sum(Y),stations=[dict(i=i,c=.5,omega=.15,
                support=list(range(data['capacity'][i]+1))) for i in range(1,len(Y)+1)])
            groups=classes(scope,Y) if name=='space_family_pass' else None
            if groups:assert family(scope,Y)==[[0,2],[2,0]]
            supports={i:sorted({v[i-1] for v in members}) for i in range(1,len(Y)+1)}
            expected=enumerated(data,members);model,ref=build(data,supports,env,groups)
            model.Params.Threads=1;model.Params.Seed=0;model.Params.TimeLimit=20;model.Params.NodeLimit=10000
            model.Params.DualReductions=0;model.Params.SolutionLimit=1
            path=target/f'{name}.mps';model.write(str(path));model.optimize()
            assert (model.SolCount>0)==(expected is not None),(name,model.Status)
            if expected is None:assert model.Status==gp.GRB.INFEASIBLE
            else:
                result,check=decode(data,ref);assert check['original_T_feasible'] and check['Y'] in members
                q=residual(model,lift(data,ref,expected));assert q['constraints']<=1e-8 and q['bounds']<=1e-8,q
            facts.append(dict(case=name,exhaustive_feasible=expected is not None,status=model.Status,
                              SolCount=model.SolCount,model_SHA=sha(path),PASS=True))
            model.dispose()
    different=dict(stations=[dict(i=1,c=.1,omega=.2),dict(i=2,c=math.nextafter(.1,1.),omega=.2)])
    assert len(classes(different,[1,2]))==2
    write(target/'result.json',dict(UTC=utc(),PASS=True,facts=facts,Seed=0,Threads=1,
          exact_coefficient_grouping=True,loaded_return_unloading_charged=True,
          independent_exhaustive_ordered_partitions=True,all_physical_positive_controls_retained=True,
          review_by='same agent, separate arithmetic and saved-row reconstruction',source_SHA=sha(__file__)))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':qualify()
