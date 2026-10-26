"""Exhaustive physical-vs-MILP qualification on 125 inventories; one native micro."""
import itertools
import math
import time
from pathlib import Path
import round96_fixed_route as f

def mapping(m,ins,w,y):
    n=ins['V'];r=[y[i]/ins['target'][i] for i in range(1,n+1)];ss=sum(r)
    g=sum(abs(a-b) for j,a in enumerate(r) for b in r[j+1:])/(n*ss) if ss else 0
    x={k:0. for k in m.bounds};x['G']=g
    for i in range(1,n+1):
        x[f'r{i}']=r[i-1];x[f'e{i}']=abs(r[i-1]-1)
        for yy in range(ins['capacities'][i]+1):
            x[f's{i}_{yy}']=float(yy==y[i]);x[f'q{i}_{yy}']=g*x[f's{i}_{yy}']
        for j in range(i+1,n+1): x[f'h{i}_{j}']=abs(r[i-1]-r[j-1])
    for route in w['routes']:
        nodes=route['nodes'];indices=[0]+[j for j in range(1,len(nodes)-1) if y[nodes[j]]!=ins['initial'][nodes[j]]]+[len(nodes)-1]
        for a,b in zip(indices,indices[1:]):x[f'a{route["vehicle"]}_{a}_{b}']=1.
    return x

def main():
    start=time.perf_counter(); dest=f.OUT/'qualification';dest.mkdir(exist_ok=False)
    path=dest/'three_station.txt'
    path.write_text('3 1 [2]\ncapacities = [100, 4, 4, 4]\ninitial = [50, 3, 0, 2]\ntarget = [0, 2, 2, 2]\nweights = [0, 1, 1, 1]\nmin_ratio = [0, 0, 0, 0]\npoints = [(0, 0), (0, 0), (0, 0), (0, 0)]\n')
    p=dict(instance_path=path.relative_to(f.ROOT).as_posix(),input_sha256=f.sha(path),T_seconds=6,pickup_seconds=1,drop_seconds=1,**{'lambda':.15})
    w=dict(F=1/3+.15,routes=[dict(vehicle=0,nodes=[0,1,2,3,0],operations=[dict(station=1,pickup=1,drop=0),dict(station=2,pickup=0,drop=1),dict(station=3,pickup=1,drop=0)])])
    # Recompute the hand fixture: Y=(2,1,1), G=1/6, P=1.
    w['F']=1/6+.15
    wp=dest/'initial.json';f.write(wp,w);m,_,ins,_=f.build(p,w);best=math.inf;feasible=0;sign_flip=0;deleted=0;zero_sum=0
    for v in itertools.product(range(5),repeat=3):
        y=[50]+list(v);x=mapping(m,ins,w,y);routes=[];b=ins['initial']
        nodes=[i for i in [1,2,3] if y[i]!=b[i]]
        route=dict(vehicle=0,nodes=[0]+nodes+[0],operations=[dict(station=i,pickup=max(0,b[i]-y[i]),drop=max(0,y[i]-b[i])) for i in nodes])
        obj=sum(c*x[k] for k,c in m.objective.items());ww=dict(routes=[route],F=obj)
        try:
            phys=f.evidence.physical_module.physical(p,ww);ok=phys['original_T_feasible']
        except AssertionError: ok=False
        try:m.verify(x);modelok=True
        except AssertionError:modelok=False
        assert ok==modelok,(v,ok,modelok)
        if ok:
            feasible+=1;best=min(best,obj);sign_flip+=y[1]>b[1] or y[3]>b[3];deleted+=len(nodes)<3;zero_sum+=sum(v)==0
    assert feasible and deleted and sign_flip
    # S=0 is physically impossible here (five bikes exceed Q=2), but its G mapping was also checked.
    case=dict(id='micro',panel=p,witness_path=wp.relative_to(f.ROOT).as_posix(),witness_sha256=f.sha(wp),cap_seconds=30)
    f.write(dest/'exhaustive_before_native.json',dict(tuples=125,feasible=feasible,best=best,sign_flip_cases=sign_flip,deletion_cases=deleted,zero_sum_feasible=zero_sum,source_sha256=f.sha(__file__)))
    f.solve(case,dest/'native',start)
    result=f.read(dest/'native/result.json');assert result['certificate'] and abs(result['final']['F']-best)<1e-7
    f.write(dest/'gate.json',dict(passed=True,optimizer_calls=1,tuples=125,exact_enumeration_optimum=best,
        native_optimum=result['final']['F'],diagnostic_source_sha256=f.sha(f.__file__),elapsed_before_write=time.perf_counter()-start))

if __name__=='__main__':main()
