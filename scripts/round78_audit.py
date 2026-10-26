"""Independent physical, strict-transition and balanced-placement replay; no solve."""
import ast
import copy
import json
import math
import re
import time
from pathlib import Path
import analyze_round61 as physical
from round75_startup import normalize,route_hash
from round76_startup import replay_closure
from round76_qualify import ROOT,read

class ClosurePaths:
    """Reuse the frozen reader with explicit diagnostic filenames, without copies."""
    def __init__(self,folder,index):self.folder,self.index=folder,index
    def __truediv__(self,name):
        assert name.startswith('hga.csv.closure.csv')
        return self.folder/name.replace('hga.csv.closure.csv',f'closure_{self.index}.csv',1)

def materialize(witness,key):
    source,first,last,target,leg=key
    routes=copy.deepcopy(witness['routes']);by={r['vehicle']:r for r in routes}
    a=by[source];block=a['nodes'][first+1:last+1]
    transferred=[op for op in a['operations'] if op['station'] in block]
    assert sum(op['pickup']-op['drop'] for op in transferred)==0
    a['nodes']=a['nodes'][:first+1]+a['nodes'][last+1:]
    a['operations']=[op for op in a['operations'] if op['station'] not in block]
    if not a['operations']:routes.remove(a)
    if target not in by:
        by[target]=dict(vehicle=target,nodes=[0,0],operations=[]);routes.append(by[target])
    b=by[target];b['nodes'][leg+1:leg+1]=block;b['operations'].extend(transferred)
    return dict(routes=sorted(routes,key=lambda r:r['vehicle']),F=witness['F'])

def oracle(p,witness,dist,Q,deadline):
    """Full route-order load/travel replay for every placement, not prefix caches."""
    nodes={r['vehicle']:r['nodes'][1:-1] for r in witness['routes']}
    ops={op['station']:(op['pickup'],op['drop']) for r in witness['routes'] for op in r['operations']}
    def duration(k,sequence):
        if not sequence:return 0.
        load=pick=drop=0;travel=0.;previous=0
        for i in sequence:
            a,b=ops[i];load+=a-b;pick+=a;drop+=b
            if load<0 or load>Q[k]:return None
            travel+=dist[previous][i];previous=i
        travel+=dist[previous][0]
        handling=float(p['pickup_seconds'])*pick+float(p['drop_seconds'])*drop+float(p['drop_seconds'])*load
        value=travel+handling
        return value if value<=float(p['T_seconds'])+1e-7 else None
    original=[duration(k,nodes.get(k,[])) for k in range(len(Q))];assert all(x is not None for x in original)
    current=sorted(original,reverse=True);best=None;counts=dict(balanced_blocks=0,placements=0,feasible=0,improving=0)
    for source,a in sorted(nodes.items()):
        for first in range(len(a)):
            for last in range(first+1,len(a)+1):
                if sum(ops[i][0]-ops[i][1] for i in a[first:last]):continue
                counts['balanced_blocks']+=1
                for target in range(len(Q)):
                    if target==source:continue
                    b=nodes.get(target,[])
                    for leg in range(len(b)+1):
                        assert time.perf_counter()<deadline,'offline audit budget exhausted'
                        counts['placements']+=1
                        ds=duration(source,a[:first]+a[last:]);dt=duration(target,b[:leg]+a[first:last]+b[leg:])
                        if ds is None or dt is None:continue
                        counts['feasible']+=1;potential=original.copy();potential[source]=ds;potential[target]=dt
                        potential.sort(reverse=True)
                        if not potential<current:continue
                        counts['improving']+=1
                        key=(source,first,last,target,leg);candidate=(potential,key)
                        if best is None or candidate<best:best=candidate
    return dict(counts,best_key=list(best[1]) if best else None,best_potential=best[0] if best else None,current_potential=current)

def audit(p,folder,original):
    start=time.perf_counter();deadline=start+60;physical.ROOT=ROOT
    text=(ROOT/p['instance_path']).read_text(encoding='utf-8')
    points=ast.literal_eval(re.search(r'(?m)^\s*points\s*=\s*(\[[^\n]*\])',text)[1])
    header=text.splitlines()[0];Q=ast.literal_eval(header[header.index('['):])
    dist=read(folder/'actual_distances.json')
    for i,a in enumerate(points):
        for j,b in enumerate(points):assert abs(dist[i][j]-math.hypot(a[0]-b[0],a[1]-b[1])/1.5)<1e-10
    current=normalize(read(folder/'initial.json'));assert route_hash(current)==route_hash(original)
    initial=physical.physical(p,current);assert initial['original_T_feasible']
    events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    event_map={row['iteration']:row for row in events};assert len(events)==len(event_map)
    closures=sorted(folder.glob('closure_*.csv'),key=lambda x:int(x.stem.split('_')[1]))
    rows=[];strict_moves=neutral=0;route_states={route_hash(current)}
    for index,trace in enumerate(closures):
        assert trace.name==f'closure_{index}.csv'
        final=normalize(read(Path(str(trace)+'.final.json')));endpoint=dict(final,upper_bound=final['F'])
        checked=replay_closure(p,ClosurePaths(folder,index),current,endpoint)
        strict_moves+=checked['accepted'];current=final
        if checked['accepted']:
            assert route_hash(current) not in route_states;route_states.add(route_hash(current))
        if index not in event_map:
            assert index==len(closures)-1 and current['F']==0;rows.append(dict(iteration=index,closure=checked,zero=True));continue
        row=event_map[index];o=oracle(p,current,dist,Q,deadline)
        for key in ['balanced_blocks','placements','feasible','improving']:assert row[key]==o[key],(key,row,o)
        assert row['found']==(o['best_key'] is not None)
        if row['found']:
            key=[row[k] for k in ['source','first','last','target','leg']];assert key==o['best_key'],(key,o)
            next_witness=materialize(current,key);actual=normalize(read(folder/f'neutral_{index}.json'))
            assert route_hash(next_witness)==route_hash(actual)
            verified=physical.physical(p,actual);assert verified['original_T_feasible']
            assert current['inventory']==actual['inventory'] and current['F']==actual['F']
            assert o['best_potential']<o['current_potential']
            assert route_hash(actual) not in route_states;route_states.add(route_hash(actual))
            current=actual;neutral+=1
        else:assert index==len(closures)-1
        rows.append(dict(iteration=index,closure=checked,balanced_oracle=o))
    final=normalize(read(folder/'final.json'));assert route_hash(final)==route_hash(current)
    endpoint=physical.physical(p,final);assert endpoint['original_T_feasible']
    result=read(folder/'result.json');assert not result['deadline'] and (result['exhausted'] or result['zero'])
    assert result['neutral']==neutral and result['insertions']+result['quantities']==strict_moves
    assert result['optimizer_calls']==0 and time.perf_counter()<deadline
    return dict(passed=True,initial=initial,final=endpoint,result=result,transitions=rows,
        neutral_states=neutral,strict_moves=strict_moves,unique_recorded_route_states=len(route_states),
        offline_seconds=time.perf_counter()-start,optimizer_calls=0,scope='Fixed-witness diagnosis, not full algorithm performance')
