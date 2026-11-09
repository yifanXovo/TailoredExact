"""Hard original-objective level over the complete RN/resource projection.

The sole expression alternative rounds integer handling budgets and removes
dominated subsets. Both forms use the SAME R92 raw/emitted lower envelope,
conservative acceptance horizon and complete inventory scope.
"""
from fractions import Fraction as F
from itertools import combinations
from round157_inventory import instance,value
from round157_resource import travel_bounds,native_quality
from round157_floor import attach
from round153_pricing import Oracle
from round152_math import h_exact
from round143_math import outward
from round143_lp import semantics,residual
from round158_common import *

def emitted(v):
    # CplexBaseline addTerm/writeExpr, binary64 max_digits10 round trip.
    if abs(v)<=1e-12:return 0.
    return math.copysign(1.,v) if abs(abs(v)-1.)<=1e-12 else v

def coefficient_package(source):
    path=OUT/'qualification/coefficient_v2'/(source['panel']['input_sha256']+'.json')
    package=read(path);assert package['input_SHA']==source['panel']['input_sha256']
    return package,sha(path)

def envelope(data,actual=None):
    rho=1-F(1,2**53);eta=F(1,2**1074);n=data['n']
    cmp=F(outward(F(data['T'])+F(1e-7),True))
    physical=(cmp+(n+7)*eta)/(rho**max(n+2,4))
    # Preserve the inherited R61/R157 threshold-time acceptance margin.
    horizon=max(F(data['T'])+F(1e-5*max(1,data['T'])),physical)
    rawh=F(data['pickup'])+F(data['drop']);h=min(rawh,F(emitted(data['pickup']+data['drop'])))
    if actual is not None:h=min(h,F(actual['handling']))
    assert h>0
    distance=data['distance'] if actual is None else actual['distance']
    matrix=[[outward(min(F(v),F(emitted(v))),False) for v in row] for row in distance]
    modeldata=dict(data,pickup=outward(h,False),drop=0.,T=outward(horizon,True),distance=matrix)
    return modeldata,dict(h_exact=str(F(modeldata['pickup'])),H_exact=str(F(modeldata['T'])),
        raw_handling_exact=str(rawh),physical_horizon_exact=str(physical),R61_margin=1e-5*max(1,data['T']),
        original_T=data['T'],R92_common_raw_emitted_lower_envelope=actual is not None,
        coefficient_source='actual saved C++ physical duration coefficients' if actual is not None else 'synthetic or legacy reconstructed coefficients',
        physical_contract='lawful one-tour fleet; inherited binary64 arithmetic/operation-count qualification; exact nonnegative lower arithmetic')

def budgets(data,bounds):
    h=F(data['pickup']);H=F(data['T']);U=H//h;assert 0<=U<2**53
    rows=[];by={};kept=[]
    for no,row in enumerate(bounds):
        ids=tuple(row['stations']);b=(H-F(row['lower']))//h
        proper=[by[R] for size in range(1,len(ids)) for R in combinations(ids,size)]
        forbid=next((r for r in proper if r['budget']<0),None)
        dominate=next((r for r in proper if r['budget']<=b),None)
        reason='forbidden_subset' if forbid else 'global_budget' if b>=U else 'dominated_subset' if dominate else 'keep'
        record=dict(index=no,stations=list(ids),budget=int(b),lower=row['lower'],reason=reason,
            dominator=(forbid or dominate)['stations'] if (forbid or dominate) else None)
        by[ids]=record;rows.append(record)
        if reason=='keep':kept.append(record)
    return dict(U=int(U),rows=rows,kept=kept,original_subsets=len(rows),kept_subsets=len(kept),
        negative=sum(r['budget']<0 for r in rows),minimal_forbidden=sum(r['budget']<0 for r in kept))

def cutoff(oracle,tau):
    from round100_gurobi_runtime import gp
    scope=oracle.scope;cost={(s['i'],y):h_exact(s,y) for s in scope['stations'] for y in s['support']}
    anchor={s['i']:(min(cost[s['i'],y] for y in s['support'])+max(cost[s['i'],y] for y in s['support']))/2 for s in scope['stations']}
    largest=max([1.]+[abs(float(v-anchor[k[0]])) for k,v in cost.items()])
    scale=math.ldexp(1.,math.ceil(math.log2(largest)));beta=1/F(scale)
    exact={k:(v-anchor[k[0]])/F(scale) for k,v in cost.items()}
    coefficients={k:(0. if abs(outward(v,False))<1e-13 else outward(v,False)) for k,v in exact.items()}
    correction=sum(max([F(0)]+[F(coefficients[s['i'],y])-exact[s['i'],y] for y in s['support']]) for s in scope['stations'])
    rhs=outward((F(tau)-sum(anchor.values(),F(0)))/F(scale)+correction,True)
    oracle.model.addConstr(float(beta)*oracle.q+gp.quicksum(a*oracle.x[k] for k,a in coefficients.items())<=rhs,
        name='original_objective_level')
    oracle.model.update()
    return dict(tau_exact=str(F(tau)),scale=scale,beta_exact=str(beta),RHS=rhs,
        anchors_exact={str(i):str(v) for i,v in anchor.items()},positive_omission_correction_exact=str(correction),
        omitted_small=sum(a==0 and exact[k]!=0 for k,a in coefficients.items()),
        coverage='At integral inventory q=G exists (gamma_L=0); emitted expression <= (J-sum anchors)/scale + correction. RHS is rounded up.',
        known_lower_auxiliary_row_used=False)

def build(source,env,variant,tau):
    from round100_gurobi_runtime import gp
    scope=source['scope'];assert scope['gamma_L']==0
    data=instance(source['panel']);actual,package_SHA=coefficient_package(source)
    modeldata,contract=envelope(data,actual);contract['coefficient_package_SHA']=package_SHA
    bounds=travel_bounds(modeldata,list(range(1,data['n']+1)));plan=budgets(modeldata,bounds)
    o=Oracle(scope,env,old_joint=True);assert o.model is not None and not o.bounds['zero_possible']
    old=semantics(o.model);cols={v.VarName for v in o.model.getVars()};rows={r.ConstrName for r in o.model.getConstrs()}
    ref=attach(o,modeldata,bounds);m=o.model
    if variant=='rounded':
        m.remove([r for r in m.getConstrs() if r.ConstrName.startswith('resource_subset_') or r.ConstrName.startswith('resource_handling_')])
        for k in range(len(data['Q'])):
            m.addConstr(ref['P'][k]<=plan['U'],name=f'rounded_global_{k}')
            for r in plan['kept']:
                ids=r['stations'];b=r['budget'];visit=gp.quicksum(ref['s'][k,i] for i in ids)
                if b<0:m.addConstr(visit<=len(ids)-1,name=f'rounded_forbidden_{k}_{r["index"]}')
                else:m.addConstr(ref['P'][k]+(plan['U']-b)*visit<=b+(plan['U']-b)*len(ids),name=f'rounded_budget_{k}_{r["index"]}')
        m.update()
    else:assert variant=='raw'
    cut=cutoff(o,tau);m.setObjective(0.);m.update()
    assert semantics(m,cols,rows)==old
    return o,ref,dict(contract=contract,budget_plan=plan,cutoff=cut,bounds=bounds,
        inventory_rows_columns_unchanged=True,zero_branch_absent_by_qualified_hard_total=True,variant=variant)

def extract(o,ref,data,point,bounds):
    scope=o.scope;Y=[]
    for s in scope['stations']:
        chosen=[y for y in s['support'] if abs(point[o.x[s['i'],y].VarName]-1)<=1e-5]
        assert len(chosen)==1;Y.append(chosen[0])
    ids={k:[] for k in range(len(data['Q']))}
    for (k,i,y),var in ref['service'].items():
        x=point[var.VarName];assert abs(x-round(x))<=1e-5
        if x>.5:assert Y[i-1]==y;ids[k].append(i)
    flat=[i for part in ids.values() for i in part]
    assert len(flat)==len(set(flat)) and set(flat)=={i for i,y in enumerate(Y,1) if y!=data['initial'][i]}
    vehicles=[]
    for k,part in ids.items():
        P=sum(max(0,data['initial'][i]-Y[i-1]) for i in part);D=sum(max(0,Y[i-1]-data['initial'][i]) for i in part)
        assert 0<=P-D<=data['Q'][k]
        ell=max([F(0)]+[F(r['lower']) for r in bounds if set(r['stations'])<=set(part)])
        duration=(F(data['pickup'])+F(data['drop']))*P+ell
        vehicles.append(dict(vehicle=k,stations=part,P=P,D=D,return_load=P-D,required_time=float(duration),required_time_exact=str(duration)))
    val=value(scope,Y);assert val['feasible']
    return dict(Y=Y,assignment=ids,J=outward(val['phi'],True),J_exact=str(val['phi']),vehicles=vehicles,
        physical_U=None,resource_time_upper=max(r['required_time'] for r in vehicles))

def run(role,variant,label,tau='default',nodes=2000000000,cap=21600):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    admission_path=OUT/'qualification/level_v2/result.json'
    admission=read(admission_path);assert admission['PASS']
    row_gate_path=OUT/'qualification/level_v2/actual_raw_implication.json'
    assert read(row_gate_path)['PASS']
    source=read(OLD157/'inventory_sources.json')[role]
    tau=F(read(OUT/'initial_intervals.json')[role]['tau']) if tau=='default' else F(tau)
    folder=OUT/'level'/label;folder.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();o,ref,metadata=build(source,env,variant,tau);m=o.model
        m.Params.Threads=1;m.Params.Seed=0;m.Params.MIPFocus=1;m.Params.NodeLimit=int(nodes);m.Params.TimeLimit=float(cap)
        m.Params.MIPGap=0;m.Params.MIPGapAbs=0;m.Params.IntFeasTol=1e-6;m.Params.DualReductions=0
        m.Params.LogFile=str(folder/'native.log');m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.SolutionLimit=1
        # Identical unfixed partial inventory hint on both expressions.
        Y=read(OUT/'candidates.json')[role]['Y']
        for s,y in zip(source['scope']['stations'],Y):
            for v in s['support']:o.x[s['i'],v].Start=float(y==v)
        m.write(str(folder/'model.mps'))
        with gp.read(str(folder/'model.mps'),env=env) as back:assert semantics(back)==semantics(m)
        approved=next(r for r in admission['facts'] if r['role']==role and r['variant']==variant)
        assert sha(folder/'model.mps')==approved['model_SHA'],'actual hard-level matrix must match its pre-long admission'
        write(folder/'mathematics.json',metadata)
        write(folder/'call.json',dict(UTC=utc(),role=role,variant=variant,tau=float(tau),tau_exact=str(tau),scope=source['scope'],
            model_SHA=sha(folder/'model.mps'),mathematics_SHA=sha(folder/'mathematics.json'),
            Seed=0,Threads=1,MIPFocus=1,NodeLimit=int(nodes),TimeLimit=float(cap),SolutionLimit=1,
            original_T=source['panel']['T_seconds'],assignment_free=True,all_inventory_decisions_free=True,
            objective='constant zero hard-level feasibility',physical_positive_control_not_a_level_start=True,
            partial_hint='same Y3 inventory selectors only; no fixed bounds or assignment',
            admission_relative='qualification/level_v2/result.json',admission_SHA=sha(admission_path),
            actual_row_gate_relative='qualification/level_v2/actual_raw_implication.json',actual_row_gate_SHA=sha(row_gate_path)))
        durable=Durable(folder);m.optimize(durable.observe);assert not durable.errors
        quality=native_quality(m,folder/'native.log')
        result=dict(UTC=utc(),role=role,variant=variant,tau=float(tau),tau_exact=str(tau),status=m.Status,
            SolCount=m.SolCount,NodeCount=m.NodeCount,Runtime=m.Runtime,Work=m.Work,IterCount=m.IterCount,
            numerical_quality=quality,classification='UNKNOWN',U_R=None,physical_U=None,
            level_excluded=False,new_lower=source['lower'],NumVars=m.NumVars,NumConstrs=m.NumConstrs,NumNZs=m.NumNZs,
            normal_Optimize_return=True,graceful_external_stop=durable.stopped,model_SHA=sha(folder/'model.mps'))
        if m.SolCount:
            point={v.VarName:v.X for v in m.getVars()};save_gz(folder/'solution.json.gz',point)
            data=instance(source['panel']);actual,_=coefficient_package(source)
            data=dict(data,distance=actual['distance']);rawbounds=travel_bounds(data,list(range(1,data['n']+1)))
            checked=extract(o,ref,data,point,rawbounds);q=residual(m,point)
            integer=max([abs(v.X-round(v.X)) for v in m.getVars() if v.VType!='C']+[0.])
            valid=quality['numeric_ok'] and max(q['constraints'],q['bounds'],integer)<=1e-5
            rawtime=max(F(r['required_time_exact']) for r in checked['vehicles'])
            original_feasible=valid and rawtime<=F(data['T'])
            within=F(checked['J_exact'])<=tau
            write(folder/'assignment_check.json',dict(checked,matrix=q,integer=integer,
                original_T_resource_feasible=original_feasible,true_J_in_level=within))
            if original_feasible:result.update(U_R=checked['J'],classification='RESOURCE_FEAS_IN_LEVEL' if within else 'RESOURCE_FEAS_OUTSIDE_EXACT_LEVEL')
        elif m.Status==gp.GRB.INFEASIBLE and quality['numeric_ok']:
            result.update(classification='LEVEL_INFEAS',level_excluded=True,new_lower=outward(tau,False))
        result['total_seconds']=time.perf_counter()-tick;write(folder/'result.json',result);o.close()
    print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
