"""Finite service-based screening on twelve preserved complete old-LP points.
Saved native snippets are inspected separately; incomplete snippets never
serve as full-old-LP witnesses. Import starts no Optimize.
"""
from round102_common import *
from round102_support import exact, row
from fractions import Fraction as F
import math,sys,ast
OLD=ROOT/'results/unified_exact_round101'
def matrix_names(role):
    f=(OLD/'diagnostics/lp01'/role/'matrix.txt').open();n,r=map(int,f.readline().split())
    return [f.readline().split()[0] for _ in range(n)]
def service_values(c,names,point):
    cols={s:j for j,s in enumerate(names)};M=len(c['capacities']);V=len(c['initial'])-1
    return [[[point[cols[f'{tag}_{k}_{i}']] if i else 0 for tag in ['p','d','z']] for i in range(V+1)] for k in range(M)]
def large_rank(c,events):
    # These candidates are uniform-q and one direction. Eligibility differs
    # only by capacity on the audited common travel/handling contract.
    q=events[0][2];T=exact(c['horizon_upper']);cost=exact(c['handling_lower']);slots=[]
    for Q in c['capacities']:
        eligible=[i for i,s,t in events if q<=Q and exact(c['shortest_lower'][0][i])+exact(c['shortest_lower'][i][0])+cost*q<=T]
        if not eligible:slots.append(0);continue
        ell=min(exact(c['shortest_lower'][0][i])+exact(c['shortest_lower'][i][0]) for i in eligible)
        slots.append(min(len(eligible),len(events) if cost==0 else int((T-ell)//(cost*q))))
    # A sum of slots is always an upper rank even with nonuniform eligibility.
    return min(len(events),sum(slots)),slots
def S_candidates(c,sv,saved):
    n=len(c['initial'])-1;Q=max(c['capacities']);U=[[sum(exact(k[i][t]) for k in sv) for t in range(2)] for i in range(n+1)]
    rows=[];seen=set();count=0
    def add(events,rhs,proof):
        nonlocal count
        A=[];coeff={};constant=F(rhs);activity=F(0)
        for i,s,q in events:
            cap=min(c['initial'][i] if s<0 else c['station_capacity'][i]-c['initial'][i],Q)
            if q>cap:continue
            denominator=cap-q+1;u=U[i][s>0]
            if u>q-1:
                A.append([i,s,q]);coeff[(i,s)]=F(1,denominator)
                constant+=F(q-1,denominator);activity+=u/denominator
        key=(tuple(map(tuple,A)),constant)
        if not A or key in seen:return
        seen.add(key);count+=1
        rows.append(dict(events=events,active_events=A,rhs=float(constant),rhs_fraction=str(constant),
            rank=rhs,proof=proof,coefficients=[[i,s,float(a),str(a)] for (i,s),a in coeff.items()],
            activity=float(activity),excess=float(activity-constant)))
    for r in saved:add(r['proof']['events'],r['proof']['rank'],r['proof'])
    for s in [-1,1]:
        for q in range(1,Q+1):
            pool=[]
            for i in range(1,n+1):
                cap=min(c['initial'][i] if s<0 else c['station_capacity'][i]-c['initial'][i],Q)
                if q<=cap and U[i][s>0]>q-1:pool.append([i,s,q])
            pool.sort(key=lambda e:(-(U[e[0]][s>0]-q+1)/(min(c['initial'][e[0]] if s<0 else c['station_capacity'][e[0]]-c['initial'][e[0]],Q)-q+1),e[0]))
            for length in range(1,len(pool)+1):
                events=pool[:length];rank,slots=large_rank(c,events)
                if rank<length:add(events,rank,dict(method='exact_dyadic_directional_slot_upper',slots=slots))
    rows.sort(key=lambda r:-r['excess']);return rows,count
def J_catalog(c,sv):
    n=len(c['initial'])-1;M=len(sv);scale=1024
    for family in ['occupancy','actual-direction','desired-direction','fixed-charge']:
        W=[]
        for k in range(M):
            w=[[0,0,0]]
            for i in range(1,n+1):
                a=min(c['initial'][i],c['capacities'][k]);b=min(c['station_capacity'][i]-c['initial'][i],c['capacities'][k]);p,d,z=sv[k][i]
                alpha=round(scale/max(1,a));beta=round(scale/max(1,b));gamma=0
                if family=='actual-direction':
                    if p/max(1,a)>=d/max(1,b):beta=0
                    else:alpha=0
                    if p+d<1e-6:alpha=beta=0
                if family=='desired-direction':
                    # Coordinate target is not needed: this is the net direction
                    # of the actual original service point aggregated across cars.
                    if sum(v[i][0]-v[i][1] for v in sv)>=0:beta=0
                    else:alpha=0
                if family=='fixed-charge':
                    if p>=d:beta=0;q=max(1,min(a,math.ceil(p/max(z,1e-6))))
                    else:alpha=0;q=max(1,min(b,math.ceil(d/max(z,1e-6))))
                    gamma=-(q-1)*(alpha+beta)
                    if p+d<1e-6:alpha=beta=gamma=0
                w.append([alpha,beta,gamma])
            W.append(w)
        yield family,W
def activity(weights,sv):return sum(exact(x)*a for wk,vk in zip(weights,sv) for wi,vi in zip(wk,vk) for a,x in zip(wi,vi))
def main(label):
    from round100_idle import ensure_idle
    ensure_idle();d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False);records=[]
    for p in read(OUT/'development_inputs.json')['roles']:
        role=p['id'];bank=OLD/'compact_evidence/lp'/role;c=read(bank/'raw.separation.json')['contract'];names=matrix_names(role)
        saved=[read(bank/f'implication_{j}.json')['row'] for j in [0,1]]
        points=[('raw',list(map(float,(bank/'raw.point').read_text().split())))]+[(f'implication_{j}',read(bank/f'implication_{j}.json')['point']) for j in [0,1]]
        rd=d/role;rd.mkdir();role_rows=[]
        for kind,point in points:
            sv=service_values(c,names,point);sr,count=S_candidates(c,sv,saved)
            jr=[]
            for family,W in J_catalog(c,sv):
                r=row(c,W);act=activity(W,sv);r.update(family=family,activity=float(act),excess=float(act-r['rhs']),
                    normalized_excess=float(act-r['rhs'])/max(1,sum(abs(a)*max(1,min(c['capacities'][k],c['initial'][i] if t==0 else c['station_capacity'][i]-c['initial'][i])) if t<2 else abs(a) for k,wk in enumerate(W) for i,wi in enumerate(wk) for t,a in enumerate(wi))))
                jr.append(r)
            write(rd/(kind+'.json'),dict(S=sr[:4],S_candidate_count=count,J=jr,service_values=sv,
                original_point_source=str(bank/(kind+'.point' if kind=='raw' else kind+'.json')),
                actual_matrix_source='results/unified_exact_round101/diagnostics/lp01/'+role+'/matrix.txt',contract=c))
            item=dict(role=role,point=kind,S_candidates=count,S_best_excess=sr[0]['excess'] if sr else None,
                J=[dict(family=r['family'],excess=r['excess'],normalized_excess=r['normalized_excess'],seconds=sum(p['seconds'] for p in r['proofs'])) for r in jr])
            records.append(item);print(json.dumps(item),flush=True)
    # Explicit original-input F5 negative example.
    c=read(OLD/'compact_evidence/lp/F5/raw.separation.json')['contract'];r=read(OLD/'compact_evidence/lp/F5/implication_0.json')['row']
    caps=sorted(min(c['initial'][i],max(c['capacities'])) for i,s,q in r['proof']['events'])
    write(d/'F5_nominal_redundancy.json',dict(events=r['proof']['events'],caps=caps,smallest16_sum=sum(caps[:16]),
        nominal_total_pickup_budget=4*7200/120,rank=r['proof']['rank'],safe_handling=c['handling_lower'],safe_horizon=c['horizon_upper'],
        scope='nominal exact coefficients only; actual export implication separately checked',
        rational_upper_property='h(u)<=u/cap on [0,cap]; fractional knapsack fills cheapest caps first'))
    write(d/'summary.json',dict(records=records,Optimize_calls=0,finite_catalog=True))
if __name__=='__main__':main(sys.argv[1])
