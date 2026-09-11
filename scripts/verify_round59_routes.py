"""Independent Python route/inventory audit, reading frozen original inputs."""
import ast
import csv
import json
import math
import re
import time
from round59_research import ROOT, OUT, RAW, write, sha

def data(row):
    text=(ROOT/row['instance_path']).read_text()
    def vector(name):
        return ast.literal_eval(re.search(r'^'+name+r'\s*=\s*(\[.*\])',text,re.M)[1])
    b=vector('initial');target=vector('target');cap=vector('capacities');weights=vector('weights')
    if abs(max(weights[1:])-10)<1e-6: weights=[w/10 for w in weights]
    points=vector('points')
    dist=[[math.hypot(a[0]-b[0],a[1]-b[1])/1.5 for b in points] for a in points]
    q=ast.literal_eval(text.splitlines()[0][text.splitlines()[0].index('['):])
    return dict(b=b,target=target,capacity=cap,weights=weights,dist=dist,Q=q,V=int(row['V']),M=int(row['M']),T=float(row['T_seconds']))

def objective(d,y):
    r=[y[i]/d['target'][i] for i in range(1,d['V']+1)]
    S=sum(r);H=sum(abs(a-b) for i,a in enumerate(r) for b in r[i+1:])
    G=H/(len(r)*S) if S>0 else 0
    P=sum(d['weights'][i+1]*abs(a-1) for i,a in enumerate(r))
    return G+0.15*P

def verify(d,result):
    y=list(d['b']);seen=set();vehicles=set();loaded_returns=0;max_travel=0
    for route in result.get('routes',[]):
        k=route['vehicle'];assert k not in vehicles and 0<=k<d['M'];vehicles.add(k)
        nodes=route['nodes'];assert len(nodes)>=2 and nodes[0]==nodes[-1]==0
        ops={op['station']:op for op in route['operations']}
        assert len(ops)==len(route['operations']) and set(ops)==set(nodes[1:-1])
        load=0;pick=0;drop=0
        for i in nodes[1:-1]:
            assert 1<=i<=d['V'] and i not in seen;seen.add(i)
            op=ops[i];p=op['pickup'];q=op['drop'];assert p==int(p) and q==int(q)
            assert p>=0 and q>=0 and (p==0)!=(q==0)
            load+=p-q;assert 0<=load<=d['Q'][k]
            y[i]+=q-p;assert 0<=y[i]<=d['capacity'][i]
            pick+=p;drop+=q
        travel=sum(d['dist'][a][b] for a,b in zip(nodes,nodes[1:]))
        assert travel+120*pick<=d['T']+1e-7
        assert 60*pick+60*drop+60*load==120*pick
        loaded_returns+=load>0;max_travel=max(max_travel,travel)
    F=objective(d,y)
    assert all(0<=y[i]<=d['capacity'][i] for i in range(1,d['V']+1))
    assert abs(F-result['objective'])<=1e-7*max(1,abs(F))
    assert y==result['verification']['final_inventories']
    return dict(passed=True,objective=F,loaded_returns=loaded_returns,max_route_travel=max_travel)

def main():
    panel={r['id']:r for r in json.loads((OUT/'panel.json').read_text())['panel']}
    conditions=[];audits=[]
    for id,row in panel.items():
        d=data(row)
        conditions.append(dict(id=id,input_sha256=sha(ROOT/row['instance_path']),
            initial=d['b'],target=d['target'],capacity=d['capacity'],weights=d['weights'],Q=d['Q'],
            total_station_initial=sum(d['b'][1:]),total_station_target=sum(d['target'][1:]),
            empty_objective=objective(d,d['b']),distance_rule='Euclidean from stored points divided by 1.5'))
        for p in sorted((RAW/'screen120'/row.get('artifact_id',id)).glob('*/result.json')):
            result=json.loads(p.read_text());v=result.get('verification',{})
            if not v.get('original_solution_feasible'): continue
            started=time.perf_counter();audit=verify(d,result)
            audit.update(id=id,arm=p.parent.name,result_sha256=sha(p),audit_seconds=time.perf_counter()-started)
            audits.append(audit)
    write(OUT/'input_conditions.json',conditions)
    write(OUT/'independent_route_audit.json',audits)
    print('Independent route audits passed:',len(audits))

if __name__=='__main__': main()
