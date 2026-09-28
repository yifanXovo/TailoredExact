"""One fixed-owner, free-order contrast after the F5 restricted certificate.

Same full quantity/Gini model, optional served nodes, path MTZ and arc loads.
Independent diagnostic only, never timed internal production subproblem.
"""
import argparse
import ctypes as ct
import itertools
import math
import time
from pathlib import Path
import round96_fixed_route as f

def assignment(m,ins,w,y,orders):
    n=ins['V'];r=[y[i]/ins['target'][i] for i in range(1,n+1)];ss=sum(r)
    g=sum(abs(a-b) for j,a in enumerate(r) for b in r[j+1:])/(n*ss) if ss else 0
    x={name:0. for name in m.bounds};x['G']=g
    for i in range(1,n+1):
        x[f'r{i}']=r[i-1];x[f'e{i}']=abs(r[i-1]-1)
        for yy in range(ins['capacities'][i]+1):
            if f's{i}_{yy}' in x:x[f's{i}_{yy}']=float(yy==y[i]);x[f'q{i}_{yy}']=g*float(yy==y[i])
        for j in range(i+1,n+1):x[f'h{i}_{j}']=abs(r[i-1]-r[j-1])
    for route in w['routes']:
        k=route['vehicle'];original=route['nodes'];end=len(original)-1
        pos={i:j for j,i in enumerate(original[1:-1],1)}
        selected=[pos[i] for i in orders[k] if y[i]!=ins['initial'][i]]
        chain=[0]+selected+[end];load=0
        for rank,(a,b) in enumerate(zip(chain,chain[1:]),1):
            x[f'x{k}_{a}_{b}']=1
            if b!=end:load+=ins['initial'][original[b]]-y[original[b]]
            x[f'l{k}_{b}']=load;x[f'u{k}_{b}']=rank
    return x

def build(p,w):
    m,old,ins,states=f.build(p,w)
    # First rows are exactly station product/link/absolute rows then Gini rows.
    n=ins['V'];count=sum(3*len(states[i])+5 for i in states)+n*(n-1)+1
    m.rows=m.rows[:count]
    for name in list(m.bounds):
        if name.startswith('a'):del m.bounds[name]
    m.binary=[name for name in m.binary if not name.startswith('a')]
    for route in w['routes']:
        k=route['vehicle'];nodes=route['nodes'];last=len(nodes)-1;Q=ins['Q'][k];arcs={};duration={}
        for j in range(1,last+1):m.var(f'l{k}_{j}',0,Q);m.var(f'u{k}_{j}',0,last)
        for a in range(last):
            for b in range(1,last+1):
                if a==b:continue
                name=m.var(f'x{k}_{a}_{b}',0,1,True);arcs[a,b]=name
                duration[name]=ins['distances'][nodes[a]][nodes[b]]
                order={f'u{k}_{b}':1,name:-(last+1)}
                if a:order[f'u{k}_{a}']=-1
                m.row(order,'>=',-last)
                load={f'l{k}_{b}':1}
                if a:load[f'l{k}_{a}']=-1
                if b!=last:
                    i=nodes[b];initial=ins['initial'][i]
                    for yy in states[i]:load[f's{i}_{yy}']=yy
                    big=Q+max(initial,ins['capacities'][i]-initial)
                else:initial=0;big=Q
                m.row(dict(load,**{name:big}),'<=',initial+big)
                m.row(dict(load,**{name:-big}),'>=',initial-big)
        m.row({name:1 for (a,b),name in arcs.items() if a==0},'=',1)
        m.row({name:1 for (a,b),name in arcs.items() if b==last},'=',1)
        for j,i in enumerate(nodes[1:-1],1):
            incoming={name:1 for (a,b),name in arcs.items() if b==j};incoming[f's{i}_{ins["initial"][i]}']=1
            outgoing={name:1 for (a,b),name in arcs.items() if a==j};outgoing[f's{i}_{ins["initial"][i]}']=1
            m.row(incoming,'=',1);m.row(outgoing,'=',1)
            for yy in states[i]:duration[f's{i}_{yy}']=(p['pickup_seconds']+p['drop_seconds'])*max(0,ins['initial'][i]-yy)
        m.row(duration,'<=',p['T_seconds'])
    y=ins['initial'].copy()
    for route in w['routes']:
        for op in route['operations']:y[op['station']]+=op['drop']-op['pickup']
    x=assignment(m,ins,w,y,{r['vehicle']:r['nodes'][1:-1] for r in w['routes']})
    m.verify(x);return m,x,ins,states

def optimize(case,dest):
    start=time.perf_counter();p=case['panel'];w=f.read(f.ROOT/case['witness_path'])
    assert f.sha(f.ROOT/case['witness_path'])==case['witness_sha256']
    if 'input_sha256' in p:assert f.sha(f.ROOT/p['instance_path'])==p['input_sha256']
    before=f.evidence.physical_module.physical(p,w);assert before['original_T_feasible']
    m,x,ins,states=build(p,w);dest.mkdir(parents=True,exist_ok=False);m.export(dest/'model.lp')
    f.write(dest/'mapping.json',dict(witness_residual=m.verify(x),model_sha256=f.sha(dest/'model.lp'),
        source_sha256=f.sha(__file__),quantity_source_sha256=f.sha(f.__file__),case=case,
        restricted_set='same original owner, any relative visit order, optional zero deletion, all quantities and signs',
        no_original_global_bound=True))
    api=f.Gurobi();env=ct.c_void_p();model=ct.c_void_p()
    api.call('GRBloadenvinternal',ct.byref(env),str(dest/'native.log').encode(),13,0,2)
    try:
        api.call('GRBreadmodel',env,str(dest/'model.lp').encode(),ct.byref(model));menv=api.dll.GRBgetenv(model)
        settings={'Threads':1,'Seed':0,'Presolve':-1,'LogToConsole':0}
        for key,val in settings.items():api.call('GRBsetintparam',menv,key.encode(),val)
        for key,val in {'MIPGap':0.,'MIPGapAbs':0.,'FeasibilityTol':1e-6,'IntFeasTol':1e-5,'OptimalityTol':1e-6}.items():
            api.call('GRBsetdblparam',menv,key.encode(),val);v=ct.c_double();api.call('GRBgetdblparam',menv,key.encode(),ct.byref(v));assert v.value==val
            settings[key]=val
        for key in ['Threads','Seed','Presolve']:
            v=ct.c_int();api.call('GRBgetintparam',menv,key.encode(),ct.byref(v));assert v.value==settings[key]
        for name,val in x.items():
            idx=ct.c_int();api.call('GRBgetvarbyname',model,name.encode(),ct.byref(idx));assert idx.value>=0
            api.call('GRBsetdblattrelement',model,b'Start',idx.value,val)
        limit=case['cap_seconds']-(time.perf_counter()-start)-2;assert limit>0
        api.call('GRBsetdblparam',menv,b'TimeLimit',limit)
        f.write(dest/'optimize_started.json',dict(optimizer_calls=1,settings=settings,time_limit=limit,started_unix=time.time()))
        api.call('GRBoptimize',model);status=api.attr(model,'Status',True);solcount=api.attr(model,'SolCount',True)
        result=dict(status=status,solcount=solcount,initial_F=before['F'],restricted_bound=api.attr(model,'ObjBound'),
            runtime=api.attr(model,'Runtime'),optimizer_calls=1,original_global_bound=False)
        assert solcount>0
        size=api.attr(model,'NumVars',True);vv=(ct.c_double*size)();names=(ct.c_char_p*size)()
        api.call('GRBgetdblattrarray',model,b'X',0,size,vv);api.call('GRBgetstrattrarray',model,b'VarName',0,size,names)
        v={names[j].decode():vv[j] for j in range(size)}
        api.call('GRBwrite',model,str(dest/'solution.sol').encode())
        residual=m.verify(v);y=ins['initial'].copy()
        for i,domain in states.items():
            hits=[yy for yy in domain if v[f's{i}_{yy}']>.5];assert len(hits)==1;y[i]=hits[0]
        routes=[]
        for old in w['routes']:
            k=old['vehicle'];last=len(old['nodes'])-1;chain=[0];seen={0}
            while chain[-1]!=last:
                a=chain[-1];nexts=[b for b in range(1,last+1) if b!=a and v[f'x{k}_{a}_{b}']>.5]
                assert len(nexts)==1 and nexts[0] not in seen
                chain.append(nexts[0]);seen.add(nexts[0])
            nodes=[old['nodes'][j] for j in chain];ops=[dict(station=i,pickup=max(0,ins['initial'][i]-y[i]),drop=max(0,y[i]-ins['initial'][i])) for i in nodes[1:-1]]
            assert set(nodes[1:-1])=={i for i in old['nodes'][1:-1] if y[i]!=ins['initial'][i]}
            routes.append(dict(vehicle=k,nodes=nodes,operations=ops))
        r=[y[i]/ins['target'][i] for i in range(1,ins['V']+1)];ss=sum(r)
        g=sum(abs(a-b) for j,a in enumerate(r) for b in r[j+1:])/(ins['V']*ss) if ss else 0
        penalty=sum(ins['weights'][i]*abs(r[i-1]-1) for i in range(1,ins['V']+1))
        witness=dict(routes=routes,inventory=y,F=g+p['lambda']*penalty,G=g,P=penalty)
        physical=f.evidence.physical_module.physical(p,witness);assert physical['original_T_feasible']
        assert result['restricted_bound']<=physical['F']+1e-7
        result.update(final=physical,model_objective=api.attr(model,'ObjVal'),max_residual=residual,
            certificate=status==2 and abs(physical['F']-result['restricted_bound'])<=1e-7,
            elapsed_before_result_write=time.perf_counter()-start)
        f.write(dest/'witness.json',witness);f.write(dest/'result.json',result)
    finally:
        if model:api.dll.GRBfreemodel(model)
        api.dll.GRBfreeenv(env)

def qualify():
    dest=f.OUT/'reorder_qualification';dest.mkdir(exist_ok=False)
    qp=f.OUT/'qualification';p=dict(instance_path=(qp/'three_station.txt').relative_to(f.ROOT).as_posix(),
        T_seconds=6,pickup_seconds=1,drop_seconds=1,**{'lambda':.15})
    w=f.read(qp/'initial.json');m,x,ins,states=build(p,w);best=math.inf;checked=0;feasible=0
    for raw in itertools.product(range(5),repeat=3):
        y=[50]+list(raw)
        for order in itertools.permutations([1,2,3]):
            xx=assignment(m,ins,w,y,{0:order});nodes=[i for i in order if y[i]!=ins['initial'][i]]
            ww=dict(F=sum(c*xx[k] for k,c in m.objective.items()),routes=[dict(vehicle=0,nodes=[0]+nodes+[0],
                operations=[dict(station=i,pickup=max(0,ins['initial'][i]-y[i]),drop=max(0,y[i]-ins['initial'][i])) for i in nodes])])
            try:physical=f.evidence.physical_module.physical(p,ww);ok=physical['original_T_feasible']
            except AssertionError:ok=False
            try:m.verify(xx);mok=True
            except AssertionError:mok=False
            assert ok==mok,(raw,order,ok,mok);checked+=1
            if ok:feasible+=1;best=min(best,ww['F'])
    f.write(dest/'exhaustive.json',dict(checked=checked,feasible=feasible,best=best,optimizer_calls=0))
    case=dict(panel=p,witness_path=(qp/'initial.json').relative_to(f.ROOT).as_posix(),witness_sha256=f.sha(qp/'initial.json'),cap_seconds=30)
    optimize(case,dest/'native');result=f.read(dest/'native/result.json');assert result['certificate'] and abs(result['final']['F']-best)<1e-7
    f.write(dest/'gate.json',dict(qualified=True,source_sha256=f.sha(__file__),quantity_source_sha256=f.sha(f.__file__),optimizer_calls=1,best=best))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['qualify','run']);args=parser.parse_args()
    kernel=ct.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ct.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ct.c_void_p,ct.c_size_t];assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    if args.mode=='qualify':qualify()
    else:
        gate=f.read(f.OUT/'reorder_qualification/gate.json');assert gate['qualified'] and gate['source_sha256']==f.sha(__file__)
        assert gate['quantity_source_sha256']==f.sha(f.__file__)
        case=next(c for c in f.read(f.OUT/'fixed_route_cases.json')['cases'] if c['id']=='F5_final')
        optimize(case,f.OUT/'reorder_F5_final')

if __name__=='__main__':main()
