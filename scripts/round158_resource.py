"""Finite original-T resource upper search, full free assignment and saved points."""
import re
from fractions import Fraction as F
from round157_inventory import instance,classes,value
from round157_resource import travel_bounds,fixed_model,native_quality
from round143_lp import residual,semantics
from round143_math import outward
from round158_common import *

def arithmetic(data,scope,members,point,bounds):
    """Independent integral decode; exact binary-coefficient time reconstruction."""
    supports={i:sorted({Y[i-1] for Y in members}) for i in range(1,data['n']+1)}
    Y=[]
    for i,vs in supports.items():
        chosen=[v for v in vs if abs(point.get(f'resource_select[{i},{v}]',0)-1)<=1e-5]
        assert len(chosen)==1;Y.append(chosen[0])
    assert Y in members
    assignment={k:[] for k in range(len(data['Q']))};pattern=re.compile(r'resource_service\[(\d+),(\d+),(\d+)\]')
    for name,x in point.items():
        match=pattern.fullmatch(name)
        if match:
            assert abs(x-round(x))<=1e-5
            if x>.5:
                k,i,v=map(int,match.groups());assert v==Y[i-1] and v!=data['initial'][i]
                assert abs(v-data['initial'][i])<=data['Q'][k];assignment[k].append(i)
    ids=[i for part in assignment.values() for i in part]
    assert len(ids)==len(set(ids)) and set(ids)=={i for i,v in enumerate(Y,1) if v!=data['initial'][i]}
    vehicles=[]
    for k,ids in assignment.items():
        P=sum(max(0,data['initial'][i]-Y[i-1]) for i in ids);D=sum(max(0,Y[i-1]-data['initial'][i]) for i in ids)
        assert 0<=P-D<=data['Q'][k]
        ell=max([F(0)]+[F(r['lower']) for r in bounds if set(r['stations'])<=set(ids)])
        t=(F(data['pickup'])+F(data['drop']))*P+ell
        vehicles.append(dict(vehicle=k,stations=ids,P=P,D=D,return_load=P-D,time_exact=str(t),time=float(t)))
    val=value(scope,Y);assert val['feasible']
    maximum=max((F(r['time_exact']) for r in vehicles),default=F(0))
    return dict(Y=Y,assignment=assignment,vehicles=vehicles,J_exact=str(val['phi']),J=outward(val['phi'],True),
        required_time_exact=str(maximum),required_time=float(maximum),original_T_resource_feasible=maximum<=F(data['T']),
        physical_route=False,physical_U=None)

def run(role,label,nodes=262144,cap=1800):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OLD157/'inventory_sources.json')[role];candidate=read(OUT/'candidates.json')[role]
    scope=source['scope'];data=instance(source['panel']);members=candidate['members']
    supports={i:sorted({Y[i-1] for Y in members}) for i in range(1,data['n']+1)}
    active=[i for i,vs in supports.items() if any(v!=data['initial'][i] for v in vs)]
    folder=OUT/'resource'/label;folder.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    bounds=travel_bounds(data,active);write(folder/'travel_bounds.json',bounds)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        model,ref=fixed_model(data,supports,classes(scope,candidate['Y']),env,bounds)
        model.Params.Threads=1;model.Params.Seed=0;model.Params.MIPFocus=1
        model.Params.MIPGap=0;model.Params.MIPGapAbs=0;model.Params.NodeLimit=int(nodes);model.Params.TimeLimit=float(cap)
        model.Params.IntFeasTol=1e-6;model.Params.DualReductions=0
        model.Params.LogFile=str(folder/'native.log');model.Params.OutputFlag=1;model.Params.LogToConsole=0
        if role=='N-B35-S':
            start=load_gz(OUT/'infra/nb_relaxed_assignment.json.gz')
            assert set(start)=={v.VarName for v in model.getVars()}
            for v in model.getVars():v.Start=start[v.VarName]
        model.write(str(folder/'model.mps'))
        with gp.read(str(folder/'model.mps'),env=env) as back:assert semantics(back)==semantics(model)
        write(folder/'condition.json',dict(UTC=utc(),role=role,members=members,scope=scope,panel=source['panel'],
            model_SHA=sha(folder/'model.mps'),bounds_SHA=sha(folder/'travel_bounds.json'),
            family_objective_exact=candidate['J_exact'],assignment_free=True,Seed=0,Threads=1,MIPFocus=1,
            NodeLimit=int(nodes),TimeLimit=float(cap),old_assignment_start=role=='N-B35-S',physical_U_claim=False))
        durable=Durable(folder);found=[False];proved=[False]
        def observe(m,where):
            durable.observe(m,where)
            if where==gp.GRB.Callback.MIPSOL:
                if m.cbGet(gp.GRB.Callback.MIPSOL_OBJ)<=data['T']-1e-5*data['T']:
                    found[0]=True;m.terminate()
            if where==gp.GRB.Callback.MIP and m.cbGet(gp.GRB.Callback.MIP_OBJBND)>data['T']+1e-5*data['T']:
                proved[0]=True;m.terminate()
        model.optimize(observe);assert not durable.errors,durable.errors
        quality=native_quality(model,folder/'native.log');qualified=quality['numeric_ok'] and (model.Status in (2,8,9,15) or (model.Status==11 and (found[0] or proved[0] or durable.stopped)))
        result=dict(UTC=utc(),role=role,status=model.Status,SolCount=model.SolCount,NodeCount=model.NodeCount,
            Runtime=model.Runtime,Work=model.Work,IterCount=model.IterCount,numerical_quality=quality,
            required_time_lower=model.ObjBound if abs(model.ObjBound)<1e90 else None,
            raw_resource_time_upper=model.ObjVal if model.SolCount else None,classification='UNKNOWN',
            normal_Optimize_return=True,graceful_external_stop=durable.stopped,valid_resource_upper=None,physical_U=None,
            model_SHA=sha(folder/'model.mps'),NumVars=model.NumVars,NumConstrs=model.NumConstrs)
        if model.SolCount:
            point={v.VarName:v.X for v in model.getVars()};save_gz(folder/'solution.json.gz',point)
            checked=arithmetic(data,scope,members,point,bounds);q=residual(model,point)
            assert q['constraints']<=1e-5 and q['bounds']<=1e-5,q
            write(folder/'assignment_check.json',dict(checked,matrix_quality=q))
            if quality['numeric_ok'] and checked['original_T_resource_feasible']:
                result.update(classification='RESOURCE_FEAS',valid_resource_upper=checked['J'],Y=checked['Y'])
        if qualified and result['required_time_lower'] is not None and result['required_time_lower']>data['T']+1e-5*data['T']:
            assert result['classification']!='RESOURCE_FEAS';result['classification']='FAMILY_RESOURCE_INFEAS'
        result['total_seconds']=time.perf_counter()-tick;write(folder/'result.json',result);model.dispose()
    print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
