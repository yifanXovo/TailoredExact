"""Bounded, solver-free necessary conditions for the three diagnostic patterns.

No rows are submitted. Other stations remain free to help; the lower bounds
remain valid even when those stations are added to a route.
"""
import ast
import csv
import itertools
import json
import math
import re
import time
from round61_research import ROOT, OUT, RAW, panel, sha, write

def main(output=None):
    output = output or OUT
    source=ROOT/'results/gf_verified_candidate_native_round60/fixed_inventory_selection.json'
    histories=json.loads(source.read_text()); records=[]
    for x in histories:
        start=time.perf_counter();identity=x['id'];p=panel()[identity]
        text=(ROOT/p['instance_path']).read_text()
        def vec(name):return ast.literal_eval(re.search(r'(?m)^'+name+r'\s*=\s*(.*)$',text)[1])
        b=vec('initial');pts=vec('points');caps=vec('capacities');y=x['fixed_inventory']
        Q=ast.literal_eval(text.splitlines()[0][text.splitlines()[0].index('['):]);M=len(Q)
        c=float(p['pickup_seconds'])+float(p['drop_seconds']);T=float(p['T_seconds'])
        dist=lambda i,j:math.dist(pts[i],pts[j])/1.5
        active=[i for i in range(1,len(y)) if b[i]!=y[i]]
        pickups={i:max(0,b[i]-y[i]) for i in active};drops={i:max(0,y[i]-b[i]) for i in active}
        single=max((2*dist(0,i)+c*max(pickups[i],drops[i]),i) for i in active)
        pair_lb={}
        for i,j in itertools.combinations(active,2):
            pair_lb[i,j]=dist(0,i)+dist(i,j)+dist(j,0)+c*max(pickups[i]+pickups[j],drops[i]+drops[j])
        incompatible={e for e,lb in pair_lb.items() if lb>T+1e-5*max(1,T)}
        clique=None;checks=0;exhaustive=True
        for C in itertools.combinations(active,M+1):
            if checks>=50000:exhaustive=False;break
            checks+=1
            if all(e in incompatible for e in itertools.combinations(C,2)):
                clique=list(C);break
        record=dict(id=identity,source_inventory_sha256=sha(source),input_sha256=p['input_sha256'],
            T=T,M=M,single_station_LB=single,aggregate_handling_LB=c*sum(pickups.values())/M,
            incompatible_pairs=len(incompatible),clique_subset_checks=checks,maximum_subset_checks=50000,
            no_clique_exhaustively_checked=clique is None and exhaustive,clique=clique,
            proof_scope='original physical problem at the unchanged T, all other stations present and allowed to help',
            necessary_condition_seconds=time.perf_counter()-start)
        if clique:
            record['pair_proofs']=[dict(i=i,j=j,Y_i=y[i],Y_j=y[j],pickup_i=pickups[i],pickup_j=pickups[j],
                drop_i=drops[i],drop_j=drops[j],travel_lower=dist(0,i)+dist(i,j)+dist(j,0),
                handling_lower=c*max(pickups[i]+pickups[j],drops[i]+drops[j]),duration_lower=pair_lb[i,j])
                for i,j in itertools.combinations(clique,2)]
            record['Tstar_lower_from_clique']=min(v['duration_lower'] for v in record['pair_proofs'])
            terms={};rhs=1
            for i in clique:
                for h in range(caps[i].bit_length()):
                    bit=(y[i]>>h)&1;terms[f'bit_{i}_{h}']=-1 if bit else 1;rhs-=bit
            record['no_good']=dict(coefficients=terms,rhs=rhs)
            point_checks=[];retained_points=[]
            for folder in [ROOT/'results/gf_verified_candidate_native_round60/local_raw/fixed_120'/identity/'off',
                           RAW/'fixed120'/identity/'off',RAW/'long600'/identity/'off']:
                sample=folder/'node_samples.csv'
                if not sample.exists():continue
                points={}
                with sample.open(newline='') as f:
                    for row in csv.DictReader(f):
                        if row['variable'] in terms:
                            key=(row['sample_kind'],row['root_callback_sequence'],row['node_bucket'])
                            points.setdefault(key,{})[row['variable']]=float(row['value'])
                for key,values in points.items():
                    assert len(values)==len(terms)
                    activity=sum(terms[n]*v for n,v in values.items())
                    point_checks.append(dict(source=str(sample.relative_to(ROOT)),source_sha256=sha(sample),
                        sample=key,activity=activity,rhs=rhs,violation=rhs-activity,violated=rhs-activity>1e-7))
                    retained_points.append(dict(source=str(sample.relative_to(ROOT)),sample=key,values=values))
            record['point_checks']=point_checks
            record['static_trial']='not_run_nonviolated_on_recorded_points' if not any(v['violated'] for v in point_checks) else 'requires_separate_cost_gate'
            write(output/('cheap_conflict_'+identity+'_bit_points.json'),retained_points)
        records.append(record)
    write(output/'cheap_inventory_time_diagnostics.json',records)
    print([(r['id'],r['clique'],r.get('Tstar_lower_from_clique')) for r in records])

if __name__=='__main__':
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path)
    main(parser.parse_args().out)
