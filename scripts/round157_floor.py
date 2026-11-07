"""Original inventory objective with a necessary free-fleet resource projection.

The qualified R153 RN model and objective-bound transport are reused.
Added resource columns use aggregate service/handling equalities to avoid
expanding every state in every small-subset row. No excluded old inventory
is treated as an upper for this stronger domain.
"""
from fractions import Fraction as F
from itertools import combinations
from round153_pricing import Oracle,stock_value
from round152_math import h_exact,unary_dp
from round143_math import outward
from round143_lp import semantics,residual
from round157_resource import travel_bounds,native_quality
from round157_inventory import instance
from round157_fleet import verify
from round157_common import *

def attach(oracle,data,bounds):
    from round100_gurobi_runtime import gp
    m=oracle.model;z=oracle.x;scope=oracle.scope;ks=range(len(data['Q']));b=data['initial']
    supports={s['i']:s['support'] for s in scope['stations']}
    keys=[(k,i,v) for k in ks for i,vs in supports.items() for v in vs
          if v!=b[i] and abs(v-b[i])<=data['Q'][k]]
    service=m.addVars(keys,vtype='B',name='resource_service')
    for i,vs in supports.items():
        for v in vs:
            if v!=b[i]:m.addConstr(gp.quicksum(service[k,i,v] for k in ks if (k,i,v) in service)==z[i,v],
                                  name=f'resource_assign_{i}_{v}')
    s=m.addVars([(k,i) for k in ks for i in supports],lb=0,ub=1,name='resource_visit')
    P=m.addVars(ks,lb=0,ub=sum(b[1:]),name='resource_pickup')
    D=m.addVars(ks,lb=0,ub=sum(data['capacity'][1:]),name='resource_drop')
    for k in ks:
        for i,vs in supports.items():
            m.addConstr(s[k,i]==gp.quicksum(service[k,i,v] for v in vs if (k,i,v) in service),
                        name=f'resource_visit_def_{k}_{i}')
        m.addConstr(P[k]==gp.quicksum(max(0,b[i]-v)*x for (kk,i,v),x in service.items() if kk==k),
                    name=f'resource_pickup_def_{k}')
        m.addConstr(D[k]==gp.quicksum(max(0,v-b[i])*x for (kk,i,v),x in service.items() if kk==k),
                    name=f'resource_drop_def_{k}')
        m.addConstr(P[k]>=D[k],name=f'resource_return_lb_{k}')
        m.addConstr(P[k]-D[k]<=data['Q'][k],name=f'resource_return_ub_{k}')
        handling=(data['pickup']+data['drop'])*P[k]
        m.addConstr(handling<=data['T'],name=f'resource_handling_{k}')
        for no,row in enumerate(bounds):
            ids=row['stations'];lb=row['lower']
            m.addConstr(handling+lb*(gp.quicksum(s[k,i] for i in ids)-len(ids)+1)<=data['T'],
                        name=f'resource_subset_{k}_{no}')
    m.update();return dict(service=service,s=s,P=P,D=D,supports=supports)

def objective(oracle):
    from round100_gurobi_runtime import gp
    scope=oracle.scope;ss=scope['stations'];m=oracle.model
    d={(s['i'],v):h_exact(s,v) for s in ss for v in s['support']}
    anchors={s['i']:(min(d[s['i'],v] for v in s['support'])+max(d[s['i'],v] for v in s['support']))/2 for s in ss}
    centered={k:v-anchors[k[0]] for k,v in d.items()}
    largest=max([1.]+[abs(float(v)) for v in centered.values()]+[1e-30])
    scale=math.ldexp(1.,math.ceil(math.log2(largest)));beta=1/F(scale)
    costs={k:v/F(scale) for k,v in centered.items()}
    m.setObjective(float(beta)*oracle.q+gp.quicksum(outward(v,False)*oracle.x[k] for k,v in costs.items()))
    m.update()
    correction=sum(max([F(0)]+[F(oracle.x[s['i'],v].Obj)-costs[s['i'],v] for v in s['support']]) for s in ss)
    correction+=max(F(0),(F(oracle.q.Obj)-beta)*F(scope['gamma_U']))
    guard=1e-6*(abs(float(beta))+sum(max(abs(float(costs[s['i'],v])) for v in s['support']) for s in ss)+1.)
    return dict(d=d,anchors=anchors,scale=scale,correction=correction,guard=guard)

def original_lower(native,transport):
    return F(transport['scale'])*(F(native)-F(transport['guard'])-transport['correction'])+sum(transport['anchors'].values(),F(0))

def retain_known_lower(oracle,lower):
    from round100_gurobi_runtime import gp
    # At integral inventories q>=G and the upward coefficients bound H
    # from above. Hence this expression is >=J>=the already qualified L.
    # This is a helper-pricing row, never a row in the physical main search.
    terms={(s['i'],y):outward(h_exact(s,y),True) for s in oracle.scope['stations'] for y in s['support']}
    row=oracle.model.addConstr(oracle.q+gp.quicksum(a*oracle.x[k] for k,a in terms.items())>=outward(F(lower),False),
                              name='known_original_inventory_lower')
    oracle.model.update();return row

def lifted(data,scope,oracle,ref,witness):
    checked=verify(data,witness);Y=checked['Y'];v=stock_value(scope,Y,1,{(s['i'],y):h_exact(s,y) for s in scope['stations'] for y in s['support']})
    assert v['feasible'] and v['S']>0
    point={var.VarName:0. for var in oracle.model.getVars()};t=1/v['S']
    for s,y in zip(scope['stations'],Y):
        i=s['i']
        for state in s['support']:
            point[f'x[{i},{state}]']=float(state==y)
            point[f'w[{i},{state}]']=float(t) if state==y else 0.
        point[f'z[{i}]']=float(t*y);point[f'r[{i}]']=float(F(s['c'])*t*y)
    point['t']=float(t);point['q']=float(v['G'])
    for si,sj in combinations(scope['stations'],2):
        i,j=si['i'],sj['i'];point[f'a[{i},{j}]']=abs(point[f'r[{i}]']-point[f'r[{j}]'])
    for route in witness['routes']:
        k=route['vehicle'];pick=drop=0
        for op in route['operations']:
            i=op['station'];pick+=op['pickup'];drop+=op['drop']
            point[ref['service'][k,i,Y[i-1]].VarName]=1.
            point[ref['s'][k,i].VarName]=1.
        point[ref['P'][k].VarName]=pick;point[ref['D'][k].VarName]=drop
    assert set(point)=={var.VarName for var in oracle.model.getVars()}
    return point,checked

def run(role,label,nodes=16384,cap=21600):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    assert read(OUT/'qualification/floor_v2/result.json')['PASS']
    assert read(OUT/'review/family_predeep_v1.json')['PASS']
    source=read(OUT/'inventory_sources.json')[role];scope=source['scope'];data=instance(source['panel'])
    assert scope['gamma_L']==0
    family_source=read(OUT/'inventory_families.json')[role]
    baseline=source['lower'];physical_upper=source['endpoint']['U']
    target_level=(baseline+physical_upper)/2
    folder=OUT/'floor'/label;folder.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    supports={s['i']:s['support'] for s in scope['stations']}
    active=[i for i,vs in supports.items() if any(v!=data['initial'][i] for v in vs)]
    bounds=travel_bounds(data,active);write(folder/'travel_bounds.json',bounds)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        oracle=Oracle(scope,env,old_joint=True);assert oracle.model is not None and not oracle.bounds['zero_possible']
        m=oracle.model;transport=objective(oracle);old=semantics(m)
        cols={v.VarName for v in m.getVars()};rows={c.ConstrName for c in m.getConstrs()}
        ref=attach(oracle,data,bounds)
        assert semantics(m,cols,rows)==old
        retain_known_lower(oracle,baseline)
        positive,checked=lifted(data,scope,oracle,ref,family_source['positive_control']['witness'])
        quality=residual(m,positive);assert quality['constraints']<=1e-7 and quality['bounds']<=1e-7,quality
        # This known route is a legal point in the stronger relaxation. A
        # MIP start fixes no bounds, assignment or order in the free model.
        for var in m.getVars():var.Start=positive[var.VarName]
        write(folder/'positive_lift.json',dict(point=positive,quality=quality,physical=checked,
            source_SHA=family_source['positive_control']['SHA'],known_route_MIP_start=True))
        m.Params.Threads=1;m.Params.Seed=0;m.Params.NodeLimit=int(nodes);m.Params.TimeLimit=float(cap)
        m.Params.MIPGap=0;m.Params.MIPGapAbs=1e-4/transport['scale'];m.Params.IntFeasTol=1e-6
        m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6;m.Params.MIPFocus=3;m.Params.DualReductions=0
        m.Params.LogFile=str(folder/'native.log');m.Params.OutputFlag=1;m.Params.LogToConsole=0
        m.write(str(folder/'model.mps'))
        with gp.read(str(folder/'model.mps'),env=env) as back:assert semantics(back)==semantics(m)
        call=dict(UTC=utc(),scope=scope,panel=source['panel'],baseline_lower=baseline,
            physical_upper=physical_upper,target_level_initial=target_level,
            rule='midpoint_of_baseline_L_and_minimum_of_physical_U_and_actual_original_J_inventory_hints',
            inventory_hints_are_not_physical_or_new_domain_uppers=True,
            old_RN_rows_columns_unchanged=True,positive_control_all_rows=quality,
            valid_new_domain_upper=outward(F(str(stock_value(scope,checked['Y'],1,transport['d'])['phi'])),True),
            deleted_best_inventory_not_used_as_new_upper=True,known_physical_route_MIP_start=True,
            saved_BB_tree=False,known_inventory_lower_row=baseline,physical_main_search_row_changes=0,
            scale=transport['scale'],anchors_exact={str(k):str(v) for k,v in transport['anchors'].items()},
            correction_exact=str(transport['correction']),numerical_guard_scaled=transport['guard'],
            NodeLimit=int(nodes),TimeLimit=float(cap),Seed=0,Threads=1,MIPFocus=3,
            original_inventory_price_gap=1e-4,not_complete_BRP_certification_tolerance=True,
            model_SHA=sha(folder/'model.mps'),bounds_SHA=sha(folder/'travel_bounds.json'),source_SHA=sha(__file__),
            old_joint=True,zero_branch_absent_by_qualified_hard_total=True,
            deepening_decision_SHA=sha(OUT/'deepening_decision.json'),
            physical_U_claim=False,new_original_objective_relaxation=True)
        write(folder/'call.json',call);events=[];stop=[False];callback_errors=[];level=[F(target_level)];hints=[]
        def observe(model,where):
            try:
                if where==gp.GRB.Callback.MIPSOL:
                    Y=[max(s['support'],key=lambda y:model.cbGetSolution(oracle.x[s['i'],y])) for s in scope['stations']]
                    val=stock_value(scope,Y,1,transport['d'])
                    if val['feasible'] and val['phi']>=F(baseline):
                        proposed=(F(baseline)+val['phi'])/2
                        if proposed<level[0]:
                            level[0]=proposed
                            hints.append(dict(seconds=time.perf_counter()-tick,Y=Y,J_exact=str(val['phi']),
                                J=float(val['phi']),new_target_exact=str(proposed),new_target=float(proposed),
                                physical_upper_claim=False,new_domain_upper_claim=False))
                    return
                if where!=gp.GRB.Callback.MIP:return
                raw=model.cbGet(gp.GRB.Callback.MIP_OBJBND);node=model.cbGet(gp.GRB.Callback.MIP_NODCNT)
                if abs(raw)>=1e90:return
                lower=max(F(baseline),original_lower(raw,transport))
                if not events or node>=events[-1]['nodes']+1024:
                    events.append(dict(seconds=time.perf_counter()-tick,nodes=node,native_bound=raw,
                                       original_lower=outward(lower,False),target_level=float(level[0])))
                if lower>level[0]:stop[0]=True;model.terminate()
            except BaseException as error:
                callback_errors.append(dict(type=type(error).__name__,message=str(error)));model.terminate()
        m.optimize(observe);write(folder/'events.json',events);write(folder/'inventory_level_hints.json',hints)
        assert not callback_errors,callback_errors
        numerical=native_quality(m,folder/'native.log')
        qualified=numerical['numeric_ok'] and (m.Status in (gp.GRB.OPTIMAL,gp.GRB.NODE_LIMIT,gp.GRB.TIME_LIMIT,gp.GRB.WORK_LIMIT) or (m.Status==gp.GRB.INTERRUPTED and stop[0]))
        raw=m.ObjBound if abs(m.ObjBound)<1e90 else None
        lower=max(F(baseline),original_lower(raw,transport)) if qualified and raw is not None else F(baseline)
        assert float(lower)<=checked['J']+1e-7
        result=dict(role=role,status=m.Status,bound_status_qualified=qualified,numerical_quality=numerical,SolCount=m.SolCount,
            NodeCount=m.NodeCount,Runtime=m.Runtime,Work=m.Work,IterCount=m.IterCount,native_bound=raw,
            original_objective_lower=outward(lower,False),baseline_lower=baseline,
            valid_new_domain_upper=call['valid_new_domain_upper'],target_level_initial=target_level,
            target_level=float(level[0]),target_level_exact=str(level[0]),
            level_excluded=lower>level[0],bound_stop=stop[0],physical_U=None,
            new_model_inventory_upper=None,old_inventory_upper_retained=False,
            NumVars=m.NumVars,NumConstrs=m.NumConstrs,NumNZs=m.NumNZs,
            model_SHA=sha(folder/'model.mps'),call_SHA=sha(folder/'call.json'),
            all_Y_full_original_scope=True,all_routes_project_to_necessary_resource_model=True,
            no_complete_fleet_from_resource_feasibility=True,total_seconds=time.perf_counter()-tick)
        if m.SolCount:
            point={v.VarName:v.X for v in m.getVars()};save_gz(folder/'solution.json.gz',point)
            Y=[max(s['support'],key=lambda y:oracle.x[s['i'],y].X) for s in scope['stations']]
            val=stock_value(scope,Y,1,transport['d'])
            write(folder/'inventory_point.json',dict(Y=Y,J=float(val['phi']),J_exact=str(val['phi']),
                native_rows=residual(m,point),physical_route=False,new_domain_upper_not_yet_independently_qualified=True))
        write(folder/'result.json',result);oracle.close()
    print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
