"""Finite-support resource/epigraph arithmetic and known reference rows."""
from fractions import Fraction as F
from itertools import combinations
import math
from round143_math import denominator, outward
from round140_math import count_rows

def states(scope):
    return [(s['i'],y) for s in scope['stations'] for y in s['support']]

def h_exact(s,y):return F(s['omega'])*abs(F(s['c'])*y-1)
def h_values(scope):return {(s['i'],y):float(h_exact(s,y)) for s in scope['stations'] for y in s['support']}

def evaluate(scope,Y,pi=None,exact=False):
    ss=scope['stations']; yy=tuple(int(y) for y in Y); assert len(yy)==len(ss)
    r=[F(s['c'])*y for s,y in zip(ss,yy)]; S=sum(r,F(0))
    A=sum((abs(a-b) for a,b in combinations(r,2)),F(0)); G=A/(len(ss)*S) if S else F(0)
    P=sum((h_exact(s,y) for s,y in zip(ss,yy)),F(0))
    phi=max(F(scope['gamma_L']),G)+P
    feasible=all(y in s['support'] for s,y in zip(ss,yy)) and scope['Bminus']<=sum(yy)<=scope['B'] and G<=F(scope['gamma_U'])
    price=phi-sum((F((pi or {}).get((s['i'],y),0)) for s,y in zip(ss,yy)),F(0))
    result=dict(Y=list(yy),total=sum(yy),S=S,A=A,G=G,penalty=P,phi=phi,price=price,feasible=feasible)
    return result if exact else {k:float(v) if isinstance(v,F) else v for k,v in result.items()}

def unary_dp(scope,costs):
    """Exact rational DP on HARD integer totals; ignores G/bin only as relaxation."""
    dp={0:(F(0),())}
    for s in scope['stations']:
        nxt={}
        for total,(cost,yy) in dp.items():
            for y in s['support']:
                t=total+y
                if t>scope['B']:continue
                v=cost+F(costs[s['i'],y])
                if t not in nxt or v<nxt[t][0]:nxt[t]=(v,yy+(y,))
        dp=nxt
    valid=[(v,yy,t) for t,(v,yy) in dp.items() if t>=scope['Bminus']]
    if not valid:return None
    v,yy,t=min(valid)
    return dict(lower=outward(v,False),exact=str(v),Y=list(yy),total=t)

def s_bounds(scope):
    ss=scope['stations']; c={s['i']:F(s['c']) for s in ss}; supports={s['i']:s['support'] for s in ss}
    d=denominator(c,supports,scope['Bminus'],scope['B'])
    assert 'S_U_exact' in d
    # Every positive S has at least one strictly positive supported c_i*y.
    positive=min([c[s['i']]*y for s in ss for y in s['support'] if y>0],default=None)
    lo=max(F(d['S_L_exact']),positive or F(0)); hi=F(d['S_U_exact'])
    return dict(lower=outward(lo,False),upper=outward(hi,True),lower_exact=str(lo),upper_exact=str(hi),box=d,
                zero_possible=scope['Bminus']==0 and all(0 in s['support'] for s in ss))

def bins(scope,relative_width=.10):
    b=s_bounds(scope);lo,hi=b['lower'],b['upper'];out=[]
    if hi>0:
        assert lo>0
        while lo<hi:
            upper=min(hi,lo/(1-relative_width))
            assert upper>lo
            out.append([lo,upper]);lo=upper
        if not out:out=[[lo,hi]]
    return b,out

def ap_row(scope):
    terms={f"e_{s['i']}":s['omega'] for s in scope['stations'] if s['omega']}
    for s in scope['stations']:
        for y in s['support']:
            a=outward(h_exact(s,y),False)
            if a>=1e-12:terms[f"state_{s['i']}_{y}"]=-a
    return dict(name='r152_known_AP',terms=terms,sense='>',rhs=0.)

def gd_rows(scope):
    ss=scope['stations'];n=len(ss);supports={s['i']:s['support'] for s in ss};c={s['i']:F(s['c']) for s in ss}
    root=denominator(c,supports,scope['Bminus'],scope['B'])
    if not root['applicable']:return []
    low={'G':float(n)};high={'G':float(n)}
    for s in ss:
        i=s['i']
        for y in s['support']:
            d=denominator(c,supports|{i:[y]},scope['Bminus'],scope['B'])
            if not d['applicable']:continue
            l,u=F(d['S_L_exact']),F(d['S_U_exact'])
            for terms,a in [(low,max(F(0),1-n*c[i]*y/l)),(high,max(F(0),n*c[i]*y/u-1))]:
                v=outward(a,False)
                if v>=1e-12:terms[f'state_{i}_{y}']=-v
    return [dict(name='r152_known_GD_'+tag,terms=t,sense='>',rhs=0.) for tag,t in [('low',low),('high',high)] if len(t)>1]

def old_resource_rows(scope):
    ss=scope['stations'];n=len(ss);a,b=F(scope['gamma_L']),F(scope['gamma_U']);bm,B=scope['Bminus'],scope['B']
    rows=[]
    for tag,gamma,bound,sense in [('loL',a,bm,'>'),('loU',b,B,'>'),('hiL',b,bm,'<'),('hiU',a,B,'<')]:
        terms={f"zprod_{s['i']}":1. for s in ss};terms['G']=-float(bound)
        terms.update({f"Y_{s['i']}":-float(gamma) for s in ss if gamma})
        rhs=outward(-gamma*bound,sense=='<')
        rows.append(dict(name='r152_known_stock_'+tag,terms=terms,sense=sense,rhs=rhs))
    supports={s['i']:s['support'] for s in ss};c={s['i']:F(s['c']) for s in ss}
    counts=count_rows(supports,c,bm,B);assert not counts['inventory_domain_infeasible']
    for tag in ['TC','TC2']:
        terms={f"h_{i}_{j}":1. for i,j in combinations(supports,2)}
        # Round RHS coefficients downward, even signed ones: s>=0.
        terms.update({f'state_{i}_{y}':-outward(v,False) for (i,y),v in counts[tag].items() if abs(float(v))>=1e-12})
        # Omitted tiny coefficients: finite-domain intercept transport.
        correction=sum(max([max(F(0),-v) for (j,y),v in counts[tag].items() if j==i and abs(float(v))<1e-12] or [F(0)]) for i in supports)
        rhs=outward((counts['constant'] if tag=='TC2' else F(0))-correction,False)
        rows.append(dict(name='r152_known_'+tag,terms=terms,sense='>',rhs=rhs))
    for j,t in enumerate(counts['thresholds']):
        terms={f'state_{s["i"]}_{y}':1. for s in ss for y in s['support'] if F(s['c'])*y>=F(t['t'])}
        rows.extend([dict(name=f'r152_known_count_{j}_{tag}',terms=terms,sense=sense,rhs=float(bound))
                     for tag,sense,bound in [('low','>',t['ell']),('high','<',t['u'])]])
    return rows

def old_count_factor_rows(scope):
    ss=scope['stations'];supports={s['i']:s['support'] for s in ss};c={s['i']:F(s['c']) for s in ss}
    counts=count_rows(supports,c,scope['Bminus'],scope['B']);a,b=F(scope['gamma_L']),F(scope['gamma_U']);rows=[]
    for j,t in enumerate(counts['thresholds']):
        selected=[(s['i'],y) for s in ss for y in s['support'] if F(s['c'])*y>=F(t['t'])]
        for tag,gamma,bound,sense in [('loL',a,t['ell'],'>'),('loU',b,t['u'],'>'),('hiL',b,t['ell'],'<'),('hiU',a,t['u'],'<')]:
            terms={f'state_g_{i}_{y}':1. for i,y in selected};terms['G']=-float(bound)
            terms.update({f'state_{i}_{y}':-float(gamma) for i,y in selected if gamma})
            rows.append(dict(name=f'r152_known_CP_{j}_{tag}',terms={k:v for k,v in terms.items() if v},sense=sense,rhs=outward(-gamma*bound,sense=='<')))
    return rows
