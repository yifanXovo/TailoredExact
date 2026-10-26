"""One bounded three-anchor domain branch, selected from actual mixtures.
No route heuristic is used as an infeasibility test. Only a shortest-path
closed visiting lower bound plus handling proves a necessary-plan exclusion.
Selection scores are heuristic; subsequent support and member certificates
always verify the chosen domain with the identical floating predicate.
"""
from round103_hull import *
from itertools import combinations
import numpy as np
def select_anchors(c,k,combination):
    plans=[r['plan'] for r in combination];lam=np.array([float(F(r['lambda_rational'])) for r in combination]);n=len(c['initial'])-1
    for p in plans:validate(c,k,p)
    visited=np.array([[p[i][2] for i in range(n+1)] for p in plans],dtype=np.int8)
    handling=np.array([mul_lower(c['handling_lower'],sum(r[0] for r in p)) for p in plans])
    solo=np.array([max([add_lower(c['shortest_lower'][0][i],c['shortest_lower'][i][0]) for i in range(1,n+1) if p[i][2]]+[0.]) for p in plans])
    pool=[i for i in range(1,n+1) if visited[:,i].any()]
    pairs={(a,b):anchor_travel(c,[a,b])[3] for a,b in combinations(pool,2)}
    best=None;count=0
    for size in [2,3]:
        for A in combinations(pool,size):
            tau=[0.]*(1<<size)
            for j,i in enumerate(A):tau[1<<j]=add_lower(c['shortest_lower'][0][i],c['shortest_lower'][i][0])
            for a,b in combinations(range(size),2):tau[(1<<a)|(1<<b)]=pairs[tuple(sorted((A[a],A[b])))]
            if size==3:
                costs=[]
                for order in permutations(A):
                    cost=0.;prev=0
                    for i in order:cost=add_lower(cost,c['shortest_lower'][prev][i]);prev=i
                    costs.append(add_lower(cost,c['shortest_lower'][prev][0]))
                tau[7]=min(costs)
            masks=sum(visited[:,i]*(1<<j) for j,i in enumerate(A))
            travel=np.maximum(solo,np.asarray(tau)[masks]);gap=np.maximum(0.,travel+handling-c['horizon_upper'])
            score=float(lam@gap);count+=1
            key=(score,-size,tuple(-i for i in A))
            if best is None or key>best[0]:best=(key,list(A),tau)
    if best is None or best[0][0]<=0:return dict(anchors=[],score=0.,evaluated_subsets=count,excluded_mass_rational='0',exclusions=[])
    _,A,tau=best;exclusions=[];mass=F(0)
    for r in combination:
        try:validate(c,k,r['plan'],A)
        except AssertionError:
            value=validate(c,k,r['plan']);mask=sum((1<<j) for j,i in enumerate(A) if r['plan'][i][2]);travel=max(value['travel_lower'],tau[mask])
            lb=add_lower(travel,mul_lower(c['handling_lower'],value['P']));assert lb>c['horizon_upper']
            mass+=F(r['lambda_rational']);exclusions.append(dict(lambda_rational=r['lambda_rational'],plan=r['plan'],P=value['P'],D=value['D'],closed_visit_lower=travel,duration_lower=lb,horizon_upper=c['horizon_upper']))
    return dict(anchors=A,score=best[0][0],evaluated_subsets=count,anchor_travel=tau,excluded_mass_rational=str(mass),exclusions=exclusions,
        rule='maximize mixture-weighted positive closed-anchor-visit plus handling resource gap over all pairs/triples; prefer fewer anchors then station order on ties')
def main(label,parent):
    from round100_idle import ensure_idle
    ensure_idle();source=OUT/'diagnostics'/parent;directory=OUT/'diagnostics'/label;directory.mkdir(parents=True,exist_ok=False)
    c=read(source/'contract.json')['resource'];where=sorted(source.glob('iteration_*'))[-1] if list(source.glob('iteration_*')) else source
    tick=time.perf_counter();selections=[]
    for k in range(len(c['capacities'])):
        r=read(where/f'vehicle_{k}.json');assert r['combination']
        choice=select_anchors(c,k,r['combination']);choice['vehicle']=k;selections.append(choice)
    write(directory/'selection.json',dict(parent=parent,parent_point=str(where/'complete_point.json'),parent_contract_sha256=sha(source/'contract.json'),
        seconds=time.perf_counter()-tick,Optimize_calls=0,DP_calls=0,selections=selections))
    print(json.dumps(dict(label=label,selections=[{k:v for k,v in q.items() if k not in ['exclusions','anchor_travel']} for q in selections],seconds=time.perf_counter()-tick)))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
