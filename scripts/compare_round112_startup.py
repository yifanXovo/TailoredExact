"""Offline complete-H comparison; no optimizer and no performance-wrapper import."""
import csv, hashlib, json, math
from pathlib import Path
import round108_reader as core

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

CSV_METADATA={'process_seconds','elapsed_seconds','elapsed','timestamp','wall_seconds'}
JSON_METADATA={'sha256','elapsed_seconds','process_seconds','wall_seconds','timestamp','path'}

def semantic(value):
    if isinstance(value,dict):
        return {k:semantic(v) for k,v in value.items() if k not in JSON_METADATA}
    if isinstance(value,list):return [semantic(v) for v in value]
    return value

def csv_semantic(path):
    with path.open(newline='',encoding='utf-8') as f:
        return [{k:v for k,v in row.items() if k not in CSV_METADATA} for row in csv.DictReader(f)]

def fleet_key(p,routes):
    by_vehicle={q.get('vehicle',q.get('vehicle_id')):q for q in routes}
    fleet=[]
    for k,Q in enumerate(p['Q_vector']):
        q=by_vehicle.get(k,dict(nodes=[0,0],operations=[]))
        operations={(op['station'] if isinstance(op,dict) else op[0]):(op['pickup'],op['drop']) if isinstance(op,dict) else (op[1],op[2]) for op in q['operations']}
        fleet.append(dict(vehicle=k,Q=Q,nodes=q['nodes'],operations=[(n,*operations[n]) for n in q['nodes'][1:-1]]))
    # Only equal-Q vehicles are interchangeable. Capacity classes remain fixed.
    normalized=[]
    for Q in sorted(set(p['Q_vector'])):
        ids=[k for k,x in enumerate(p['Q_vector']) if x==Q]
        values=sorted((dict(nodes=fleet[k]['nodes'],operations=fleet[k]['operations']) for k in ids),key=lambda x:json.dumps(x,sort_keys=True))
        normalized.extend(dict(vehicle=k,Q=Q,**v) for k,v in zip(ids,values))
    return sorted(normalized,key=lambda x:x['vehicle'])

def reconstruct(root,p,d):
    root=Path(root);d=Path(d);base=d/'hga.csv.exchange'
    final=read(base/'final.json');physical=core.full_fleet(root,p,final)
    traces={}
    for path in sorted(d.glob('hga.csv.*.csv')):
        traces[path.name]=csv_semantic(path)
    seed=d/'hga.csv.joint_seed.csv'
    if seed.exists():traces[seed.name]=csv_semantic(seed)
    for path in sorted(base.iterdir()):
        if path.suffix=='.csv':traces['exchange/'+path.name]=csv_semantic(path)
        elif path.suffix=='.json':traces['exchange/'+path.name]=semantic(read(path))
        elif path.suffix=='.jsonl':traces['exchange/'+path.name]=[semantic(json.loads(s)) for s in path.read_text().splitlines()]
    # Closure final witnesses are also independently replayed, including empty cars.
    for path in base.glob('*.final.json'):core.full_fleet(root,p,read(path))
    startup_path=d/'result.json.round112.startup.json'
    if startup_path.exists():
        startup=read(startup_path);verify=core.full_fleet(root,p,startup)
        assert abs(verify['F']-physical['F'])<=1e-7
        assert fleet_key(p,startup['routes'])==fleet_key(p,final['routes'])
    descent=traces.get('hga.csv.descent.csv',[])
    seeds={int(row['seed']) for row in descent}
    interrupted=any(row.get('interrupted')=='1' for row in descent)
    # The generation summary records all 24 stochastic plus constructive seed.
    joint_seed=traces.get('hga.csv.joint_seed.csv',[])
    completion=not interrupted and seeds==set(range(1,26))
    return dict(complete=completion,seed_ids=sorted(seeds),interrupted=interrupted,
        physical=physical,fleet=fleet_key(p,final['routes']),semantic_traces=traces,
        original_input_SHA=p['input_sha256'],Q_vector=p['Q_vector'],generation_summary=joint_seed,
        metadata_excluded=sorted(CSV_METADATA|JSON_METADATA))

def compare(root,p,arms):
    values={name:reconstruct(root,p,path) for name,path in arms.items()}
    control=values['P-S'];rows=[]
    for name,v in values.items():
        if name=='P-S':continue
        fields=dict(full_H_complete=control['complete'] and v['complete'],
            semantic_trace_equal=control['semantic_traces']==v['semantic_traces'],
            complete_capacity_assigned_fleet_equal=control['fleet']==v['fleet'],
            final_inventory_equal=control['physical']['Y']==v['physical']['Y'],
            objective_equal=abs(control['physical']['F']-v['physical']['F'])<=1e-7)
        rows.append(dict(id=p['id'],candidate=name,control='P-S',**fields,
            qualified=all(fields.values()),reason='MATCHED_COMPLETE_H' if all(fields.values()) else 'H_INCOMPLETE' if not fields['full_H_complete'] else 'START_MISMATCH',
            differing_trace_files=sorted(k for k in set(v['semantic_traces'])|set(control['semantic_traces']) if v['semantic_traces'].get(k)!=control['semantic_traces'].get(k))))
    return dict(comparisons=rows,arms=values)
