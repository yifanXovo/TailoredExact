"""Independent full-route neutral enumeration and original physical/strict replay."""
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
from round78_audit import ClosurePaths
from round76_qualify import ROOT,read

def materialize(witness,key):
    kind,s,f,l,t,tf,tl=key
    nodes={r['vehicle']:r['nodes'][1:-1] for r in witness['routes']}
    ops={o['station']:o for r in witness['routes'] for o in r['operations']}
    a,b=nodes[s],nodes.get(t,[])
    x,y=a[f:l],b[tf:tl]
    assert sum(ops[i]['pickup']-ops[i]['drop'] for i in x)==sum(ops[i]['pickup']-ops[i]['drop'] for i in y)
    assert (kind==0 and tf==tl) or (kind==1 and s<t and x and y)
    nodes[s],nodes[t]=a[:f]+y+a[l:],b[:tf]+x+b[tl:]
    return dict(routes=[dict(vehicle=k,nodes=[0]+v+[0],operations=[copy.deepcopy(ops[i]) for i in v])
        for k,v in sorted(nodes.items()) if v],F=witness['F'])

def oracle(p,witness,dist,Q,deadline):
    nodes={r['vehicle']:r['nodes'][1:-1] for r in witness['routes']}
    ops={o['station']:(o['pickup'],o['drop']) for r in witness['routes'] for o in r['operations']}
    def duration(k,seq):
        if not seq:return 0.
        load=pickup=drop=0;travel=0.;previous=0
        for i in seq:
            a,b=ops[i];load+=a-b;pickup+=a;drop+=b
            if load<0 or load>Q[k]:return None
            travel+=dist[previous][i];previous=i
        travel+=dist[previous][0]
        handling=float(p['pickup_seconds'])*pickup+float(p['drop_seconds'])*drop+float(p['drop_seconds'])*load
        value=travel+handling
        return value if value<=float(p['T_seconds'])+1e-7 else None
    original=[duration(k,nodes.get(k,[])) for k in range(len(Q))];assert all(x is not None for x in original)
    current=sorted(original,reverse=True);best=None
    counts=dict(balanced_blocks=0,placements=0,feasible=0,improving=0,exchange_pairs=0,exchange_feasible=0,exchange_improving=0)
    def check(key,sa,sb):
        nonlocal best
        assert time.perf_counter()<deadline,'Offline audit cap exhausted'
        kind,s,f,l,t,tf,tl=key
        counts['placements' if kind==0 else 'exchange_pairs']+=1
        da,db=duration(s,sa),duration(t,sb)
        if da is None or db is None:return
        counts['feasible' if kind==0 else 'exchange_feasible']+=1
        potential=original.copy();potential[s]=da;potential[t]=db;potential.sort(reverse=True)
        if not potential<current:return
        counts['improving' if kind==0 else 'exchange_improving']+=1
        candidate=(potential,key)
        if best is None or candidate<best:best=candidate
    for s,a in sorted(nodes.items()):
        for f in range(len(a)):
            for l in range(f+1,len(a)+1):
                x=a[f:l];net=sum(ops[i][0]-ops[i][1] for i in x)
                if net==0:
                    counts['balanced_blocks']+=1
                    for t in range(len(Q)):
                        if t==s:continue
                        b=nodes.get(t,[])
                        for leg in range(len(b)+1):check((0,s,f,l,t,leg,leg),a[:f]+a[l:],b[:leg]+x+b[leg:])
                for t in range(s+1,len(Q)):
                    b=nodes.get(t,[])
                    for tf in range(len(b)):
                        for tl in range(tf+1,len(b)+1):
                            y=b[tf:tl]
                            if sum(ops[i][0]-ops[i][1] for i in y)==net:
                                check((1,s,f,l,t,tf,tl),a[:f]+y+a[l:],b[:tf]+x+b[tl:])
    return dict(counts,best_key=list(best[1]) if best else None,best_potential=best[0] if best else None,current_potential=current)

def audit(p,folder,original):
    start=time.perf_counter();deadline=start+120;physical.ROOT=ROOT
    text=(ROOT/p['instance_path']).read_text(encoding='utf-8')
    points=ast.literal_eval(re.search(r'(?m)^\s*points\s*=\s*(\[[^\n]*\])',text)[1])
    header=text.splitlines()[0];Q=ast.literal_eval(header[header.index('['):]);dist=read(folder/'actual_distances.json')
    for i,a in enumerate(points):
        for j,b in enumerate(points):assert abs(dist[i][j]-math.hypot(a[0]-b[0],a[1]-b[1])/1.5)<1e-10
    current=normalize(read(folder/'initial.json'));assert route_hash(current)==route_hash(original)
    initial=physical.physical(p,current);assert initial['original_T_feasible']
    events=[json.loads(s) for s in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    event_map={r['iteration']:r for r in events};assert len(events)==len(event_map)
    closures=sorted(folder.glob('closure_*.csv'),key=lambda x:int(x.stem.split('_')[1]))
    rows=[];strict_moves=neutral=exchanges=relocations=0;states={route_hash(current)}
    for index,trace in enumerate(closures):
        assert trace.name==f'closure_{index}.csv'
        final=normalize(read(Path(str(trace)+'.final.json')))
        checked=replay_closure(p,ClosurePaths(folder,index),current,dict(final,upper_bound=final['F']))
        strict_moves+=checked['accepted'];current=final
        if checked['accepted']:assert route_hash(current) not in states;states.add(route_hash(current))
        if index not in event_map:
            assert index==len(closures)-1 and current['F']==0;rows.append(dict(iteration=index,closure=checked,zero=True));continue
        row=event_map[index];o=oracle(p,current,dist,Q,deadline)
        for k in ['balanced_blocks','placements','feasible','improving','exchange_pairs','exchange_feasible','exchange_improving']:
            assert row[k]==o[k],(k,row,o)
        assert row['found']==(o['best_key'] is not None)
        if row['found']:
            key=[row[k] for k in ['kind','source','first','last','target','target_first','target_last']];assert key==o['best_key'],(key,o)
            next_witness=materialize(current,key);actual=normalize(read(folder/f'neutral_{index}.json'))
            assert route_hash(next_witness)==route_hash(actual)
            verified=physical.physical(p,actual);assert verified['original_T_feasible']
            assert current['inventory']==actual['inventory'] and current['F']==actual['F']
            assert o['best_potential']<o['current_potential'] and route_hash(actual) not in states
            states.add(route_hash(actual));current=actual;neutral+=1
            exchanges+=row['kind']==1;relocations+=row['kind']==0
        else:assert index==len(closures)-1
        rows.append(dict(iteration=index,closure=checked,neutral_oracle=o))
    final=normalize(read(folder/'final.json'));assert route_hash(final)==route_hash(current)
    endpoint=physical.physical(p,final);assert endpoint['original_T_feasible']
    result=read(folder/'result.json');assert not result['deadline'] and not result['verification_failed'] and (result['exhausted'] or result['zero'])
    assert result['neutral']==neutral and result['exchanges']==exchanges and result['relocations']==relocations
    assert result['insertions']+result['quantities']==strict_moves and result['optimizer_calls']==0 and time.perf_counter()<deadline
    return dict(passed=True,initial=initial,final=endpoint,result=result,transitions=rows,
        neutral_states=neutral,strict_moves=strict_moves,unique_recorded_route_states=len(states),
        offline_seconds=time.perf_counter()-start,optimizer_calls=0,scope='Fixed-witness diagnosis; no complete performance claim')
