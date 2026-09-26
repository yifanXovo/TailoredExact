"""Offline analysis of original-coordinate LP/node samples; not a local model."""
import csv
import json
import math
from collections import defaultdict
from round59_research import ROOT, OUT, RAW
from verify_round59_routes import data
from analyze_round59 import csvwrite

def metrics(values,d):
    assert 'G' in values and all('Y_'+str(i) in values and 'zprod_'+str(i) in values for i in range(1,d['V']+1))
    def family(prefix): return [v for k,v in values.items() if k.startswith(prefix)]
    def frac(xs): return sum(abs(v-round(v))>1e-7 for v in xs)
    G=values.get('G',0)
    ratios=[values['Y_'+str(i)]/d['target'][i] for i in range(1,d['V']+1)]
    S=sum(ratios)
    inventory_gini=sum(abs(a-b) for i,a in enumerate(ratios) for b in ratios[i+1:])/(d['V']*S) if S>0 else 0
    gy=[abs(values.get('zprod_'+str(i),0)-G*values.get('Y_'+str(i),0)) for i in range(1,d['V']+1)]
    excess=[]
    for i in range(1,d['V']+1):
        p=sum(values.get(f'p_{k}_{i}',0) for k in range(d['M']))
        q=sum(values.get(f'd_{k}_{i}',0) for k in range(d['M']))
        excess.append(p+q-abs(d['b'][i]-values.get(f'Y_{i}',0)))
    dist=[list(row) for row in d['dist']]
    for h in range(d['V']+1):
        for i in range(d['V']+1):
            for j in range(d['V']+1): dist[i][j]=min(dist[i][j],dist[i][h]+dist[h][j])
    count=eligible=violated=rawviolated=0;maxv=0
    for k in range(d['M']):
        for a in range(1,d['V']+1):
            for b in range(a+1,d['V']+1):
                count+=1
                z=values.get(f'z_{k}_{a}',0)+values.get(f'z_{k}_{b}',0)
                if z<=1+1e-7: continue
                eligible+=1
                t=min(dist[0][a]+dist[a][b]+dist[b][0],dist[0][b]+dist[b][a]+dist[a][0])
                p=values.get(f'p_{k}_{a}',0)+values.get(f'p_{k}_{b}',0)
                raw=120*p+t*(z-1)-d['T'];maxv=max(maxv,raw)
                rawviolated+=raw>1e-7
                violated+=raw/max(1,d['T']+t,abs(120*p)+abs(t*z))>1e-7
    return dict(G=G,continuous_inventory_gini=inventory_gini,Gini_representation_deficit=inventory_gini-G,
        fractional_inventory=frac(family('Y_')),fractional_arcs=frac(family('x_')),
        fractional_visits=frac(family('z_')),fractional_pickup=frac(family('p_')),
        fractional_drop=frac(family('d_')),fractional_modes=frac(family('mode_')),
        max_GY_deviation=max(gy),sum_GY_deviation=sum(gy),
        operation_cancellation_excess=sum(max(0,x) for x in excess),
        pair_candidates=count,pairs_passing_necessary_visit_test=eligible,
        pair_raw_violations=rawviolated,pair_scaled_violations=violated,max_pair_raw_violation=maxv)

def main():
    panel={r['id']:r for r in json.loads((OUT/'panel.json').read_text())['panel']}
    rows=[];domains=[]
    for path in sorted(RAW.glob('diagnostic_*/*/*/lp_variable_evidence.csv')):
        ident=json.loads((path.parent/'launch.json').read_text());d=data(panel[ident['id']])
        records=list(csv.DictReader(path.open()))
        values={r['variable_name']:float(r['primal_value']) for r in records}
        rows.append(dict(id=ident['id'],arm=ident['arm'],stage=ident['stage'],sample='plain_LP',**metrics(values,d)))
        widths=[max(0,math.floor(float(r['upper_bound'])+1e-9)-math.ceil(float(r['lower_bound'])-1e-9)+1) for r in records if r['variable_name'].startswith('Y_')]
        domains.append(dict(id=ident['id'],arm=ident['arm'],stage=ident['stage'],domain_width_sum=sum(widths),domain_width_max=max(widths,default=0),domain_widths=str(widths)))
    for path in sorted(RAW.glob('diagnostic_*/*/*/node_samples.csv')):
        ident=json.loads((path.parent/'launch.json').read_text());d=data(panel[ident['id']]);samples=defaultdict(dict)
        for r in csv.DictReader(path.open()):samples[r['node_count']][r['variable']]=float(r['value'])
        for node,values in samples.items():
            rows.append(dict(id=ident['id'],arm=ident['arm'],stage=ident['stage'],sample='native_node_count_'+node,**metrics(values,d)))
    csvwrite(OUT/'relaxation_census.csv',rows);csvwrite(OUT/'propagated_inventory_domains.csv',domains)
    print('relaxation samples:',len(rows))

if __name__=='__main__':main()
