"""Pure AP-only matrix contract, using the actual loaded ratios and support."""
import collections, math, re
from fractions import Fraction as F
def contract(model,data,enabled):
    support=collections.defaultdict(list);ratios={}
    for n in model['bounds']:
        m=re.fullmatch(r'state_(\d+)_(\d+)',n)
        if m:support[int(m[1])].append(int(m[2]))
    for row,sense,rhs in model['rows']:
        t=dict(row)
        if sense=='=' and rhs==0 and len(t)==2:
            for n,c in t.items():
                m=re.fullmatch(r'r_(\d+)',n)
                if m and c==1 and f'Y_{m[1]}' in t:ratios[int(m[1])]=-t[f'Y_{m[1]}']
    assert set(support)==set(ratios)
    expected={};states=0
    for i,ys in support.items():
        weight=data['w'][i]
        if weight>0:expected[f'e_{i}']=weight
        for y in ys:
            exact=F(weight)*abs(F(ratios[i])*y-1)
            deviation=abs(float(F(ratios[i])*y-1)) # correctly rounded binary64 fma result
            lower=math.nextafter(deviation,0.) if deviation>0 else 0.
            weighted=weight*lower
            coefficient=math.nextafter(weighted,0.) if weighted>0 else 0.
            assert 0<=F(coefficient)<=exact
            if coefficient>1e-12:expected[f'state_{i}_{y}']=-coefficient
            states+=1
    ap=(tuple(sorted(expected.items())),'>=',0.)
    count=collections.Counter(model['rows'])[ap]
    assert count==(1 if enabled else 0),('AP row count',enabled,count)
    return dict(enabled=enabled,AP_rows=count,state_coefficients_checked=states,
        actual_loaded_ratio_and_support=True,exact_downward_coefficient_check=True,
        added_columns=0,coefficients=len(expected) if enabled else 0)
