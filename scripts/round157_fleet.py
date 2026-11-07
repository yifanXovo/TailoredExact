"""Free-fleet original-T completion: exact inventory selectors and arc load flow.

This is the R61 physical projection, with arc load flow replacing node-load
big-M implications. Objective terms involving G/H disappear only after the
permitted inventory set is fixed. No vehicle assignment or route is fixed.
"""
from round157_inventory import instance, value, classes, family
from round157_common import *

def verify(data,witness):
    n=data['n'];Y=list(data['initial']);seen=set();vehicles=set();durations=[];returns=[]
    pickups=drops=0
    for route in witness['routes']:
        k=route['vehicle']; assert 0<=k<len(data['Q']) and k not in vehicles
        vehicles.add(k);nodes=route['nodes'];assert nodes[0]==nodes[-1]==0
        ops={o['station']:(o['pickup'],o['drop']) for o in route['operations']}
        assert len(ops)==len(route['operations'])==len(nodes)-2
        assert set(ops)==set(nodes[1:-1])
        load=0;p=d=0
        for i in nodes[1:-1]:
            assert 1<=i<=n and i not in seen;seen.add(i)
            a,b=ops[i];assert int(a)==a>=0 and int(b)==b>=0 and ((a>0) != (b>0))
            load+=a-b; assert 0<=load<=data['Q'][k]
            Y[i]+=b-a;assert 0<=Y[i]<=data['capacity'][i]
            p+=a;d+=b
        travel=math.fsum(data['distance'][i][j] for i,j in zip(nodes,nodes[1:]))
        # Depot unloading is charged. Starting supply is zero, irrespective
        # of the input's depot placeholder. Thus p=d+return_load exactly.
        assert p==d+load
        duration=travel+data['pickup']*p+data['drop']*(d+load)
        durations.append(duration);returns.append(load);pickups+=p;drops+=d
    ratios=[Y[i]/data['target'][i] for i in range(1,n+1)]
    S=math.fsum(ratios)
    A=math.fsum(abs(a-b) for pos,a in enumerate(ratios) for b in ratios[pos+1:])
    G=A/(n*S) if S else 0.
    H=data['lam']*math.fsum(data['weights'][i]*abs(ratios[i-1]-1) for i in range(1,n+1))
    objective=G+H
    reported=witness.get('objective',witness.get('F'))
    if reported is not None: assert abs(reported-objective)<=1e-7,(reported,objective)
    return dict(Y=Y[1:],G=G,H=H,J=objective,pickup=pickups,drop=drops,
                durations=durations,returns=returns,maximum_duration=max(durations,default=0),
                original_T_feasible=max(durations,default=0)<=data['T']+1e-7,
                total_duration=math.fsum(durations))

def build(data,supports,env,groups=None):
    from round100_gurobi_runtime import gp
    n=data['n'];ks=range(len(data['Q']));initial=data['initial'];d=data['distance']
    assert set(supports)==set(range(1,n+1))
    model=gp.Model(env=env);model.ModelName='R157_free_fleet_original_T'
    z=model.addVars([(i,v) for i,vs in supports.items() for v in vs],vtype='B',name='select')
    for i,vs in supports.items():model.addConstr(gp.quicksum(z[i,v] for v in vs)==1,name=f'select_one_{i}')
    if groups:
        for gno,group in enumerate(groups):
            for sv,count in group['counts'].items():
                v=int(sv)
                model.addConstr(gp.quicksum(z[i,v] for i in group['stations'] if (i,v) in z)==count,
                                name=f'class_count_{gno}_{v}')
    wkeys=[(k,i,v) for k in ks for i,vs in supports.items() for v in vs
           if v!=initial[i] and abs(v-initial[i])<=data['Q'][k]]
    w=model.addVars(wkeys,vtype='B',name='service')
    for i,vs in supports.items():
        for v in vs:
            if v!=initial[i]:
                model.addConstr(gp.quicksum(w[k,i,v] for k in ks if (k,i,v) in w)==z[i,v],
                                name=f'assign_service_{i}_{v}')
    s={(k,i):gp.quicksum(w[k,i,v] for v in supports[i] if (k,i,v) in w) for k in ks for i in supports}
    p={(k,i):gp.quicksum((initial[i]-v)*w[k,i,v] for v in supports[i] if v<initial[i] and (k,i,v) in w)
       for k in ks for i in supports}
    drop={(k,i):gp.quicksum((v-initial[i])*w[k,i,v] for v in supports[i] if v>initial[i] and (k,i,v) in w)
          for k in ks for i in supports}
    active={k:[i for i in supports if any((k,i,v) in w for v in supports[i])] for k in ks}
    arcs=[(k,i,j) for k in ks for i in [0]+active[k] for j in [0]+active[k] if i!=j]
    x=model.addVars(arcs,vtype='B',name='arc')
    flow=model.addVars(arcs,lb=0,name='load')
    u=model.addVars([(k,i) for k in ks for i in active[k]],lb=0,ub=n,name='order')
    for k,i,j in arcs:
        model.addConstr(flow[k,i,j]<=data['Q'][k]*x[k,i,j],name=f'arc_capacity_{k}_{i}_{j}')
        if i==0:flow[k,i,j].UB=0
    for k in ks:
        ids=active[k]
        model.addConstr(gp.quicksum(x[k,0,j] for j in ids)<=1,name=f'depart_once_{k}')
        model.addConstr(gp.quicksum(x[k,0,j]-x[k,j,0] for j in ids)==0,name=f'return_once_{k}')
        for i in ids:
            out=gp.quicksum(x[k,i,j] for j in [0]+ids if j!=i)
            incoming=gp.quicksum(x[k,j,i] for j in [0]+ids if j!=i)
            model.addConstr(out==s[k,i],name=f'out_degree_{k}_{i}')
            model.addConstr(incoming==s[k,i],name=f'in_degree_{k}_{i}')
            model.addConstr(gp.quicksum(flow[k,i,j]-flow[k,j,i] for j in [0]+ids if j!=i)==p[k,i]-drop[k,i],
                            name=f'load_conservation_{k}_{i}')
            model.addConstr(u[k,i]>=s[k,i],name=f'order_lb_{k}_{i}')
            model.addConstr(u[k,i]<=n*s[k,i],name=f'order_ub_{k}_{i}')
            for j in ids:
                if i!=j:model.addConstr(u[k,j]>=u[k,i]+1-(n+1)*(1-x[k,i,j]),name=f'order_arc_{k}_{i}_{j}')
        travel=gp.quicksum(d[i][j]*x[k,i,j] for kk,i,j in arcs if kk==k)
        model.addConstr(travel+(data['pickup']+data['drop'])*gp.quicksum(p[k,i] for i in ids)<=data['T'],
                        name=f'original_time_{k}')
    model.setObjective(0.)
    model.update()
    return model,dict(z=z,w=w,x=x,flow=flow,u=u,s=s,p=p,drop=drop,active=active,supports=supports)

def lift(data,ref,witness):
    checked=verify(data,witness);Y=checked['Y']
    point={v.VarName:0. for group in ('z','w','x','flow','u') for v in ref[group].values()}
    for i,vs in ref['supports'].items():
        assert Y[i-1] in vs
        point[ref['z'][i,Y[i-1]].VarName]=1.
    for route in witness['routes']:
        k=route['vehicle'];nodes=route['nodes'];load=0;ops={o['station']:o for o in route['operations']}
        for pos,(i,j) in enumerate(zip(nodes,nodes[1:])):
            point[ref['x'][k,i,j].VarName]=1.
            point[ref['flow'][k,i,j].VarName]=load
            if j:
                op=ops[j];load+=op['pickup']-op['drop']
                point[ref['w'][k,j,Y[j-1]].VarName]=1.
                point[ref['u'][k,j].VarName]=pos+1
    return point

def decode(data,ref):
    witness=dict(routes=[])
    for k,ids in ref['active'].items():
        succ={i:j for (kk,i,j),v in ref['x'].items() if kk==k and v.X>.5}
        if not succ:continue
        assert 0 in succ
        nodes=[0];ops=[];seen=set()
        while True:
            i=succ[nodes[-1]];nodes.append(i)
            if i==0:break
            assert i not in seen;seen.add(i)
            chosen=[v for (kk,j,v),x in ref['w'].items() if kk==k and j==i and x.X>.5]
            assert len(chosen)==1;v=chosen[0]
            ops.append(dict(station=i,pickup=max(0,data['initial'][i]-v),drop=max(0,v-data['initial'][i])))
        assert set(succ)==set(nodes[:-1])
        witness['routes'].append(dict(vehicle=k,nodes=nodes,operations=ops))
    checked=verify(data,witness);witness['objective']=checked['J'];witness['inventory']=checked['Y']
    return witness,checked

def solve_one(role,rank,mode,label,nodes=4096,cap=3600):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round143_lp import residual
    affinity();native=binding();assert native['sha256']==DLL_SHA
    source=read(OUT/'inventory_families.json')[role];candidate=source['candidates'][int(rank)-1]
    data=instance(source['panel']);Y=candidate['Y'];scope=source['scope']
    assert mode in ('fixed','family')
    members=[Y] if mode=='fixed' else candidate['members']
    supports={i:sorted({v[i-1] for v in members}) for i in range(1,data['n']+1)}
    groups=classes(scope,Y) if mode=='family' else None
    target=OUT/'fleet'/label;target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        model,ref=build(data,supports,env,groups)
        model.Params.Threads=1;model.Params.Seed=0;model.Params.MIPGap=0;model.Params.MIPGapAbs=0
        model.Params.NodeLimit=int(nodes);model.Params.TimeLimit=float(cap);model.Params.SolutionLimit=1
        model.Params.MIPFocus=1;model.Params.DualReductions=0
        model.Params.LogFile=str(target/'native.log');model.Params.OutputFlag=1;model.Params.LogToConsole=0
        model.write(str(target/'model.mps'))
        write(target/'condition.json',dict(role=role,rank=int(rank),mode=mode,Y=Y,members=members,
            supports=supports,classes=groups,J=candidate['J'],J_exact=candidate['J_exact'],
            original_T=data['T'],panel=source['panel'],model_SHA=sha(target/'model.mps'),
            all_assignment_order_load_free=True,objective='constant_zero',R61_arc_load_flow_projection=True,
            historical_route_start=False,Seed=0,Threads=1,NodeLimit=int(nodes),TimeLimit=float(cap),
            parameters={k:model.getParamInfo(k)[2] for k in ['Seed','Threads','MIPGap','MIPGapAbs','MIPFocus','SolutionLimit','DualReductions']},
            Native=native,source_SHA=sha(__file__),fixed_dependency_base=BASE))
        build_done=time.perf_counter();events=[]
        def observe(m,where):
            if where==gp.GRB.Callback.MIP:
                node=m.cbGet(gp.GRB.Callback.MIP_NODCNT)
                if not events or node>=events[-1]['nodes']+1024:
                    events.append(dict(seconds=time.perf_counter()-tick,nodes=node,
                        solutions=m.cbGet(gp.GRB.Callback.MIP_SOLCNT),simplex=m.cbGet(gp.GRB.Callback.MIP_ITRCNT)))
        write(target/'native_call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE',Optimize=1))
        model.optimize(observe);finished=time.perf_counter()
        result=dict(role=role,rank=int(rank),mode=mode,status=model.Status,SolCount=model.SolCount,
            Runtime=model.Runtime,Work=model.Work,NodeCount=model.NodeCount,IterCount=model.IterCount,
            build_seconds=build_done-tick,optimize_outer_seconds=finished-build_done,
            classification='UNKNOWN',physical_U=None,physical_L_change=0.,
            model_SHA=sha(target/'model.mps'),NumVars=model.NumVars,NumConstrs=model.NumConstrs,NumNZs=model.NumNZs,
            endpoint_UTC=utc(),NodeLimit=model.Params.NodeLimit,condition_SHA=sha(target/'condition.json'))
        if model.SolCount:
            witness,checked=decode(data,ref)
            assert checked['Y'] in members
            real=value(scope,checked['Y']);assert real['feasible'] and str(real['phi'])==candidate['J_exact']
            point={v.VarName:v.X for v in model.getVars()};quality=residual(model,point)
            quality['integer']=max([abs(v.X-round(v.X)) for v in model.getVars() if v.VType!='C'] or [0.])
            assert quality['constraints']<=1e-5 and quality['bounds']<=1e-5 and quality['integer']<=1e-5
            assert checked['original_T_feasible']
            write(target/'witness.json',witness);write(target/'physical_check.json',checked)
            save_gz(target/'solution.json.gz',point)
            result.update(classification='FEAS',physical_U=candidate['J'],quality=quality,
                          maximum_duration=checked['maximum_duration'],inventory=checked['Y'],
                          witness_SHA=sha(target/'witness.json'))
        elif model.Status==gp.GRB.INFEASIBLE:
            result.update(classification='INFEAS',exclusion_scope='one_inventory' if mode=='fixed' else 'exact_finite_class_family')
        write(target/'events.json',events);result['total_seconds']=time.perf_counter()-tick
        write(target/'result.json',result);model.dispose()
    print(json.dumps(result),flush=True)

if __name__=='__main__':solve_one(*sys.argv[1:])
