"""Independent full physical enumeration of two saved, exposed endpoints."""
import ast
import hashlib
import math
import re
import time
from pathlib import Path
from round75_qualify import ROOT,OUT,sha,read,write
from round75_startup import normalize

def check_one(p,folder):
    start=time.perf_counter()
    raw=(ROOT/p['instance_path']).read_text(encoding='utf-8')
    def vector(name):
        match=re.search(r'(?m)^\s*'+name+r'\s*=\s*(\[[^\n]*\])',raw)
        return ast.literal_eval(match[1]) if match else []
    initial,target,capacity,points,weights=[vector(s) for s in ['initial','target','capacities','points','weights']]
    n=len(initial)-1;head=raw.splitlines()[0];Q=ast.literal_eval(head[head.index('['):])
    if not weights:weights=[0]+[1]*n
    if abs(max(weights[1:])-10)<=1e-6:weights=[x/10 for x in weights]
    distance=[[math.hypot(x-u,y-v)/1.5 for u,v in points] for x,y in points]
    witness=normalize(read(folder/'hga.csv.quantity.csv.initial.json'))
    template=[];signed={}
    for route in witness['routes']:
        operations={op['station']:op['pickup']-op['drop'] for op in route['operations']}
        ordered=[(i,operations[i]) for i in route['nodes'][1:-1]]
        template.append((route['vehicle'],ordered));signed.update(operations)
    assert len(signed)==sum(len(ops) for _,ops in template)
    def evaluate(a,b,t):
        y=list(initial)
        for vehicle,operations in template:
            load=0;pickups=0;station_drop=0;travel=0.;last=0
            for station,original in operations:
                operation=original+(t if station==a else (-t if station==b else 0))
                if operation==0:continue
                y[station]=initial[station]-operation
                if not 0<=y[station]<=capacity[station]:return None
                load+=operation
                if not 0<=load<=Q[vehicle]:return None
                pickups+=max(0,operation);station_drop+=max(0,-operation)
                travel+=distance[last][station];last=station
            travel+=distance[last][0]
            duration=travel+float(p['pickup_seconds'])*pickups+float(p['drop_seconds'])*station_drop+float(p['drop_seconds'])*load
            if duration>float(p['T_seconds'])+1e-7:return None
        ratios=[y[i]/target[i] for i in range(1,n+1)]
        S=sum(ratios);H=sum(abs(ratios[i]-ratios[j]) for i in range(n) for j in range(i))
        G=H/(n*S) if S else 0
        P=sum(weights[i]*abs(ratios[i-1]-1) for i in range(1,n+1))
        return G+float(p['lambda'])*P
    baseline=evaluate(0,0,0);assert baseline is not None and abs(baseline-witness['F'])<1e-10
    stations=sorted(signed);enumerated=0;feasible=0;improving=0;best=None;argbest=None
    for ia,a in enumerate(stations):
        for b in [0]+stations[ia+1:]:
            for value in range(initial[a]-capacity[a],initial[a]+1):
                t=value-signed[a]
                if not t:continue
                if time.perf_counter()-start>30:raise TimeoutError('Declared offline endpoint oracle cap30s')
                enumerated+=1;objective=evaluate(a,b,t)
                if objective is None:continue
                feasible+=1
                if baseline-objective>1e-12:improving+=1
                if best is None or objective<best:best=objective;argbest=[a,b,t]
    cpp=read(folder/'audit.json')['detail']
    assert feasible==cpp['feasible_candidates']
    assert improving==0 and cpp['accepted']==0
    return dict(id=p['id'],input_sha256=sha(ROOT/p['instance_path']),witness_sha256=sha(folder/'hga.csv.quantity.csv.initial.json'),
        original_F=baseline,enumerated_station_domain_neighbors=enumerated,physically_feasible_neighbors=feasible,
        strict_improving_neighbors=improving,minimum_candidate_F=best,minimum_candidate_choice=argbest,
        production_feasible_count=cpp['feasible_candidates'],counts_agree=True,
        elapsed_seconds=time.perf_counter()-start,optimizer_calls=0)

def main():
    assert not (OUT/'startup/active_run.lock').exists()
    destination=OUT/'endpoint_oracles.json';assert not destination.exists()
    summary=read(OUT/'startup/summary.json');assert summary['valid']==summary['attempted']==10
    panel={p['id']:p for p in read(ROOT/'results/unified_exact_round71/protocol.json')['panel']}
    report=dict(plan_sha256=sha(OUT/'endpoint_oracle_plan.md'),script_sha256=sha(__file__),records=[],completed=False)
    write(destination,report)
    for key in ['D6','D7']:
        try:
            record=check_one(panel[key],OUT/'startup/local_raw'/key/'QDS-X')
            report['records'].append(record);write(destination,report);print(record,flush=True)
        except Exception as error:
            report['failure']=dict(id=key,error=repr(error));write(destination,report);raise
    report['completed']=True;report['total_wall_seconds']=sum(r['elapsed_seconds'] for r in report['records'])
    write(destination,report)

if __name__=='__main__':main()
