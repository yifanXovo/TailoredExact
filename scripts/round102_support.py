"""Offline exact integer support DP. No solver and no route sufficiency claim.

All stations remain choices, including zero-weight suppliers/receivers. P is
cumulative pickup (not bounded by Q); D may exceed P at an intermediate DP
layer. Only the final states require D<=P. Profit and unreachable arithmetic
are integer; the safe resource comparisons are exact dyadic fractions.
"""
from fractions import Fraction as F
import numpy as np
import hashlib, time
NEG=-(1<<60)
def exact(x):return F.from_float(float(x))
def support(c,k,w,keep_grid=False):
    tick=time.perf_counter();n=len(c['initial'])-1;Q=c['capacities'][k]
    assert len(w)==n+1 and all(len(x)==3 for x in w)
    assert all(type(x)==int for row in w for x in row)
    A=[min(c['initial'][i],Q) for i in range(n+1)]
    B=[min(c['station_capacity'][i]-c['initial'][i],Q) for i in range(n+1)]
    A[0]=B[0]=0
    bound=sum(abs(w[i][0])*A[i]+abs(w[i][1])*B[i]+abs(w[i][2]) for i in range(1,n+1))
    if bound>=1<<52:raise ValueError('unsupported exact score range')
    cost=exact(c['handling_lower']);T=exact(c['horizon_upper'])
    U=sum(A)
    if cost>0:U=min(U,int(T//cost))
    if U>2048:raise ValueError('unsupported DP resource dimension; no bound emitted')
    # Every final D<=P<=U; truncating intermediate D>U cannot remove a final
    # state because both resource totals are monotone.
    ell=[exact(c['shortest_lower'][0][i])+exact(c['shortest_lower'][i][0]) for i in range(n+1)]
    order=sorted(range(1,n+1),key=lambda i:(ell[i],i))
    dp=np.full((U+1,U+1),NEG,dtype=np.int64);dp[0,0]=0
    best=0;levels=[];winner=None
    for pos,i in enumerate(order):
        old=dp;new=old.copy();alpha,beta,gamma=w[i]
        for a in range(1,min(A[i],U)+1):
            np.maximum(new[a:,:],old[:-a,:]+alpha*a+gamma,out=new[a:,:])
        for b in range(1,min(B[i],U)+1):
            np.maximum(new[:,b:],old[:,:-b]+beta*b+gamma,out=new[:,b:])
        dp=new
        if pos+1<len(order) and ell[order[pos+1]]==ell[i]:continue
        cap=U if cost==0 else min(U,int((T-ell[i])//cost))
        value=NEG
        if cap>=0:
            value=max(int(dp[p,:p+1].max()) for p in range(cap+1))
            if value>best:best=value;winner=[i,cap]
        levels.append(dict(station=i,travel_lower=float(ell[i]),pickup_cap=cap,maximum=value if value>NEG//2 else None))
    r=dict(vehicle=k,weights=w,upper=best,resource_limit=U,levels=levels,winner=winner,
        seconds=time.perf_counter()-tick,grid_sha256=hashlib.sha256(dp.tobytes()).hexdigest(),
        exact_integer_profit=True,all_stations_retained=True)
    if keep_grid:r['final_grid']= [[None if int(x)<NEG//2 else int(x) for x in row] for row in dp]
    return r
def row(c,weights,mu=None,keep_grid=False):
    n=len(c['initial'])-1;mu=mu or [0]*(n+1)
    assert len(mu)==n+1 and all(type(x)==int and x>=0 for x in mu)
    proofs=[]
    for k,w in enumerate(weights):
        penalized=[ [a,b,g-mu[i]] for i,(a,b,g) in enumerate(w)]
        proofs.append(support(c,k,penalized,keep_grid))
    return dict(weights=weights,multipliers=mu,rhs=sum(mu)+sum(p['upper'] for p in proofs),proofs=proofs)
