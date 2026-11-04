"""Purposeful exhaustive small-domain checks of the actual reference oracle."""
from itertools import product
from fractions import Fraction as F
from round152_math import *
from round152_oracle import solve_bin,price,fallback
from round152_common import *

def scope(c,supports,bm,B,gl,gu,weights=None):
    return dict(Bminus=bm,B=B,gamma_L=gl,gamma_U=gu,cutoff=10.,stations=[dict(i=i+1,c=v,omega=(weights or [.125]*len(c))[i],support=list(supports[i]),lo=min(supports[i]),hi=max(supports[i])) for i,v in enumerate(c)])

def check():
    from round150_lp import affinity
    from round100_gurobi_runtime import binding
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification';target.mkdir(exist_ok=False);facts=[]
    cases=[('R133_known_control',scope([1.]*4,[[0,1,2]]*4,0,3,0.,.75,[.15]*4)),
           ('heterogeneous_nonminimal',scope([.5,1.,2.],[[0,1,2],[0,2],[0,1]],1,4,.25,.65)),
           ('zero_and_signed',scope([.5,1.],[[0,1,3],[0,1,2]],0,3,.2,.5)),
           ('zero_only',scope([.5,1.],[[0],[0]],0,0,.3,.5))]
    for tag,d in cases:
        pi={(s['i'],y):(-.375 if (s['i']+y)%2 else .625) for s in d['stations'] for y in s['support']}
        allp=[evaluate(d,Y,pi,True) for Y in product(*[s['support'] for s in d['stations']])];feasible=[p for p in allp if p['feasible']]
        exact=min(p['price'] for p in feasible);low,dp=fallback(d,pi);assert F(low)<=exact
        bounds,cover=bins(d,.3);zero=[p for p in feasible if p['S']==0]
        valid_bins=[]
        for j,inter in enumerate(cover):
            ell,u=map(F,inter);members=[p for p in feasible if ell<=p['S']<=u]
            for p in members:
                H=max(F(d['gamma_L']),p['A']/(len(d['stations'])*u))+p['penalty']-sum(F(pi[s['i'],y]) for s,y in zip(d['stations'],p['Y']))
                eps=min(F(d['gamma_U']),F(len(d['stations'])-1,len(d['stations'])))*(1-ell/u)
                assert 0<=p['price']-H<=eps
            rr=solve_bin(d,pi,inter,target/tag/f'bin{j}',cap=10)
            if rr['proven_empty']:assert not members
            if rr['lower'] is not None and members:assert rr['lower']<=float(min(p['price'] for p in members))+1e-8
            if rr['upper'] is not None:assert rr['upper']>=float(exact)-1e-12
            valid_bins.append(dict(interval=inter,members=len(members),lower=rr['lower'],upper=rr['upper'],empty=rr['proven_empty']))
        for p in feasible:
            assert p['S']==0 or any(F(l)<=p['S']<=F(u) for l,u in cover)
            # Every nonminimal legal completion dominates phi and each support row.
            alpha=exact;rhs=alpha+sum(F(pi[s['i'],y]) for s,y in zip(d['stations'],p['Y']))
            g=max(F(d['gamma_L']),p['G']);assert rhs<=g+p['penalty']
            if g<F(d['gamma_U']):assert rhs<=(g+F(d['gamma_U']))/2+p['penalty']+F(1,8)
        changed={k:v+(.125 if k[1]%2 else -.25) for k,v in pi.items()}
        delta=sum(max(F(changed[s['i'],y])-F(pi[s['i'],y]) for y in s['support']) for s in d['stations'])
        assert exact-delta<=min(evaluate(d,p['Y'],changed,True)['price'] for p in feasible)
        facts.append(dict(tag=tag,total_states=len(allp),feasible_states=len(feasible),exact_price=str(exact),fallback=low,zero_states=len(zero),bins=valid_bins,
                          nonminimal_completion=True,negative_potentials=True,downward_potential_transport=True))
    # A child-derived bound cannot be lifted to a parent without repricing.
    parent=scope([1.,1.],[[0,1],[0,1]],0,2,0.,.5)
    pp={(s['i'],y):0. for s in parent['stations'] for y in s['support']}
    child=dict(parent,Bminus=1,B=1)
    pmin=min(evaluate(parent,Y,pp,True)['price'] for Y in product([0,1],repeat=2))
    cmin=min(evaluate(child,Y,pp,True)['price'] for Y in product([0,1],repeat=2) if evaluate(child,Y,pp,True)['feasible'])
    assert cmin>pmin
    write(target/'result.json',dict(PASS=True,facts=facts,child_to_parent_counterexample=dict(parent=str(pmin),child=str(cmin)),
          no_physical_G_lower_screen=True,bin_MIP_bounds_checked_against_exhaustive_true_objective=True,numerical_bounds_not_rational_optimality_claim=True))
    print(json.dumps(dict(PASS=True,cases=len(facts),bin_solves=sum(len(v['bins']) for v in facts))),flush=True)

if __name__=='__main__':check()
