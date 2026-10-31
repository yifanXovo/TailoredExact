"""Solver-free RN domain derivation and exact small witnesses.

Fractions interpret the actual loaded binary64 c_i, rather than rounded 1/D_i.
The compact product system is two bounds per state and one mass row per site.
"""
from fractions import Fraction as F
from itertools import combinations
import collections, re
from round143_common import *

def outward(q, upper):
    value = float(q)
    if (F(value) < q) if upper else (F(value) > q):
        value = math.nextafter(value, math.inf if upper else -math.inf)
    assert (F(value) >= q) if upper else (F(value) <= q)
    return value

def denominator(c, supports, bminus, b):
    lo = {i:min(supports[i]) for i in c}
    hi = {i:max(supports[i]) for i in c}
    tau_l, tau_u = max(bminus,sum(lo.values())), min(b,sum(hi.values()))
    if tau_l > tau_u:
        return dict(applicable=False,reason='INFEASIBLE_BOX_TOTAL_SCOPE')
    def extremum(total, reverse):
        y = dict(lo); remaining = total-sum(y.values())
        for i in sorted(c,key=lambda i:(c[i],i),reverse=reverse):
            add = min(remaining,hi[i]-y[i]); y[i] += add; remaining -= add
        assert remaining == 0
        return sum((F(c[i])*y[i] for i in c),F(0)), y
    sl, yl = extremum(tau_l,False); su, yu = extremum(tau_u,True)
    result = dict(S_L_exact=str(sl),S_U_exact=str(su),tau_L=tau_l,tau_U=tau_u,
        minimizer=yl,maximizer=yu,Bminus=bminus,B=b,
        c_binary64={i:float(c[i]) for i in c},c_exact={i:str(F(c[i])) for i in c},
        supports=supports,arithmetic='Fraction of actual binary64 coefficients')
    if sl <= 0:
        return dict(result,applicable=False,reason='NO_GLOBAL_POSITIVE_DENOMINATOR_BOUND')
    assert su >= sl > 0
    return dict(result,applicable=True,L_t=outward(1/su,False),U_t=outward(1/sl,True),
        L_t_exact=str(1/su),U_t_exact=str(1/sl))

def specification(parsed,scope):
    n = scope['panel']['V']; c = {}; supports = {i:[] for i in range(1,n+1)}
    for name in parsed['order']:
        match = re.fullmatch(r'state_(\d+)_(\d+)',name)
        if match:
            i,y=map(int,match.groups()); assert parsed['bounds'][name] == (0.,1.)
            supports[i].append(y)
    rows = collections.Counter(parsed['rows'])
    for i in supports:
        supports[i].sort(); assert supports[i]
        found=[]
        for terms,sense,rhs in parsed['rows']:
            d=dict(terms)
            if sense=='=' and rhs==0 and set(d)=={f'r_{i}',f'Y_{i}'}:
                found.append(-d[f'Y_{i}']/d[f'r_{i}'])
        assert found and len(set(found))==1 and found[0]>0
        # The observed writer uses coefficient +1 on r_i: no ratio rounding.
        assert rows[(tuple(sorted({f'r_{i}':1.,f'Y_{i}':-found[0]}.items())),'=',0.)]
        c[i]=found[0]
        simplex=tuple((f'state_{i}_{y}',1.) for y in supports[i])
        assert rows[(tuple(sorted(simplex)),'=',1.)]
        link={f'Y_{i}':1.}
        link.update({f'state_{i}_{y}':-float(y) for y in supports[i] if y})
        assert rows[(tuple(sorted(link.items())),'=',0.)]
    assert scope['B']==scope['panel']['total_initial']
    assert scope['Bminus']==max(0,scope['B']-sum(scope['panel']['Q_vector']))
    return denominator(c,supports,scope['Bminus'],scope['B'])

def rn_rows(spec):
    if not spec['applicable']:
        return []
    # JSON object keys become strings; make a single consistent representation.
    supports={int(i):ys for i,ys in spec['supports'].items()}
    c={int(i):v for i,v in spec['c_binary64'].items()}
    lt,ut=spec['L_t'],spec['U_t']; rows=[]
    def add(name,terms,sense,rhs=0.):
        rows.append(dict(name=name,terms={k:float(v) for k,v in terms.items() if v},sense=sense,rhs=float(rhs)))
    for i,ys in supports.items():
        for y in ys:
            w,s=f'rn_w_{i}_{y}',f'state_{i}_{y}'
            add(f'rn_lb_{i}_{y}',{w:1.,s:-lt},'>')
            add(f'rn_ub_{i}_{y}',{w:1.,s:-ut},'<')
        add(f'rn_mass_{i}',dict({f'rn_w_{i}_{y}':1. for y in ys},rn_t=-1.),'=')
        add(f'rn_inventory_{i}',{f'rn_Y_{i}':1.,**{f'rn_w_{i}_{y}':-y for y in ys if y}},'=')
    add('rn_normalization',{f'rn_Y_{i}':c[i] for i in supports},'=',1.)
    for i,j in combinations(supports,2):
        h=f'rn_h_{i}_{j}'
        add(f'rn_abs_p_{i}_{j}',{h:1.,f'rn_Y_{i}':-c[i],f'rn_Y_{j}':c[j]},'>')
        add(f'rn_abs_m_{i}_{j}',{h:1.,f'rn_Y_{i}':c[i],f'rn_Y_{j}':-c[j]},'>')
    add('rn_gini',{**{f'rn_h_{i}_{j}':1. for i,j in combinations(supports,2)},'G':-len(supports)},'<')
    return rows

def exact_fixtures():
    s=[[F(0),F(1)],[F(1,2),F(1,2)],[F(1),F(0)]]
    q=[[F(0),F(1,3)],[F(0),F(1,3)],[F(1,3),F(0)]]
    g=F(1,3); Y=[v[1] for v in s]; Z=[v[1] for v in q]
    assert all(sum(a)==1 and sum(b)==g and all(0<=v<=u for u,v in zip(a,b)) for a,b in zip(s,q))
    assert sum(Z)==F(2,3) and sum(Y)==F(3,2)
    h=[abs(Y[i]-Y[j]) for i,j in combinations(range(3),2)]
    assert sum(h)==2 and sum(h)<=3*sum(Z)
    J=sum(Z); tau=sum(Y)
    assert max(g,tau+2*g-2)<=J<=min(tau+g-1,2*g)
    # Support {0,1}: TC = tau; TC2 on tau in [1,2] is 2.
    assert sum(h)>=tau and sum(h)==2
    t=F(5,8); w=[[0,t],[2*t-1,1-t],[t,0]]
    assert all(sum(b)==t and all(F(1,2)*u<=v<=u for u,v in zip(a,b)) for a,b in zip(s,w))
    v=[a[1] for a in w]; assert sum(v)==1
    rn_g=sum(abs(v[i]-v[j]) for i,j in combinations(range(3),2))/3
    assert rn_g==F(5,12) and rn_g-g==F(1,12)
    fixed=denominator({i:1. for i in range(1,5)},{i:[0,1] for i in range(1,5)},3,3)
    assert F(fixed['L_t'])<=F(1,3)<=F(fixed['U_t'])
    assert F(1,4)+F(1,12)==F(1,3) and 4*F(1,4)==1
    zero=denominator({1:1.,2:.5},{1:[0,1],2:[0,2]},0,2)
    assert not zero['applicable'] and not rn_rows(zero)
    hole=denominator({1:.1,2:.3},{1:[0,2],2:[1,4]},2,4)
    for y1 in (0,2):
        for y2 in (1,4):
            if 2<=y1+y2<=4:
                val=F(.1)*y1+F(.3)*y2
                assert F(hole['S_L_exact'])<=val<=F(hole['S_U_exact'])
    return dict(PASS=True,three_station=dict(old_g='1/3',RN_minimum_g='5/12',separation='1/12',
        old_H='2',old_J='2/3',t='5/8',RN_w=[[str(x) for x in a] for a in w],
        scope='Declared Gini/stock/TC/TC2/endpoint-pair subblock; not a full BRP fixture'),
        four_station=dict(t='1/3',w1='1/4',w0='1/12',RN_g='0',TC_stock_min_g='1/4'),
        fixed_scope=fixed,zero_scope=zero,holey_scope=hole,Optimize=0,Native_load=0)

if __name__=='__main__':
    write(OUT/'math/fixtures.json',exact_fixtures())
    print('RN exact fixtures PASS; Optimize=0')
