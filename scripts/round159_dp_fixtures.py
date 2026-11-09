"""Finite independent enumeration for the newly implemented exact-cost DP."""
from itertools import permutations
from fractions import Fraction as F
from round159_common import *

def run():
    facts=[]
    cases=[('prefix', [2,2,0,0],[0,0,3,1],3,1000),
           ('tour_over_T',[1,1,1,0,0],[0,0,0,1,2],3,365),
           ('empty',[0],[0],1,1000),
           ('capacity',[1]*21,[0]*21,21,100000)]
    for label,b,Y,Q,T in cases:
        n=len(b);folder=OUT/'qualification_dp'/label;folder.mkdir(parents=True,exist_ok=False)
        d=[[0 if i==j else (1 if label!='prefix' else 1+((i+j)*(i+j)+i*j)%9) for j in range(n+1)] for i in range(n+1)]
        lines=[f'{n} 1 0 {sum(b)+sum(Y)} 1 120 {T} {T}',str(Q)]
        for bi,yi in zip(b,Y):
            support=sorted(set([bi,yi]));lines.append(' '.join(map(str,[bi,max(bi,yi),1,0,len(support),*support])))
        lines+=[' '.join(map(str,row)) for row in d]
        lines+=[f'{T//120} 0',' '.join(map(str,Y)),' '.join('0' for _ in Y)]
        path=folder/'data.txt';path.write_text('\n'.join(lines)+'\n')
        subprocess.run([str(PE),'complete',str(path),'unused',str(folder/'output')],env=meter.environment(),check=True)
        result=read(folder/'output/completion.json');row=result['vehicles'][0]
        if label=='capacity':
            assert not row['complete'] and result['classification']=='UNKNOWN'
            facts.append(dict(label=label,P=sum(b),Q=Q,classification='UNKNOWN',slots_required=n*2**n));continue
        active=[i for i in range(1,n+1) if b[i-1]!=Y[i-1]]
        best=plain=None;best_order=None
        for order in permutations(active):
            nodes=(0,)+order+(0,);cost=sum(F(d[i][j]) for i,j in zip(nodes,nodes[1:]));plain=cost if plain is None else min(plain,cost)
            load=0;legal=True
            for i in order:load+=b[i-1]-Y[i-1];legal &= 0<=load<=Q
            if legal and (best is None or cost<best):best=cost;best_order=nodes
        assert row['complete'] and F(row['travel_scaled'])/2**53==best and F(row.get('unloaded_travel_scaled','0'))/2**53==plain
        expected='PHYSICAL_FEAS' if best+120*sum(max(0,bi-yi) for bi,yi in zip(b,Y))<=T+1e-7 else 'FIXED_COMBINATION_INFEAS'
        assert result['classification']==expected
        facts.append(dict(label=label,P=sum(max(0,bi-yi) for bi,yi in zip(b,Y)),Q=Q,travel_exact=str(best),unloaded_exact=str(plain),
            brute_force_orders=math.factorial(len(active)),classification=expected,chosen_route=list(best_order)))
    assert facts[0]['P']>facts[0]['Q']
    write(OUT/'dp_qualification.json',dict(UTC=utc(),PASS=True,facts=facts,PE_SHA=sha(PE),
        recurrence='cost[S,j] minimizes exact dyadic travel for every admissible load(S); predecessor removes j',
        not_a_new_theoretical_contribution=True,Optimize=0))

if __name__=='__main__':run()
