"""NC/TS against actual binary64 RN bounds; exact signed-box transport."""
import collections, math
from fractions import Fraction as F
from round140_math import count_rows
from round143_math import outward

def safe_row(name, terms, sense, rhs, bounds):
    """Round exact rational coefficients with a directed finite-box RHS."""
    terms={k:F(v) for k,v in terms.items() if v}
    rhs=F(rhs); converted={k:float(v) for k,v in terms.items()}
    errors={k:F(converted[k])-v for k,v in terms.items()}
    assert sense in ('>','<')
    correction=sum((min(e*F(bounds[k][0]),e*F(bounds[k][1])) if sense=='>'
                    else max(e*F(bounds[k][0]),e*F(bounds[k][1])) for k,e in errors.items()), F(0))
    transported=outward(rhs+correction,sense=='<')
    smallest=min([1.]+[abs(v) for v in converted.values() if v]);scale=0
    while math.ldexp(smallest,scale)<1e-12:scale+=1
    result=dict(name=name,sense=sense,rhs=math.ldexp(transported,scale),
        terms={k:math.ldexp(v,scale) for k,v in converted.items() if v})
    proof=dict(exact_terms={k:str(v) for k,v in terms.items()},exact_rhs=str(rhs),
        coefficient_box_correction=str(correction),unscaled_rhs=transported,scale_exponent=scale)
    return result,proof

def joint_rows(spec,bounds):
    support={int(i):ys for i,ys in spec['supports'].items()}
    ratio={int(i):F(v) for i,v in spec['c_binary64'].items()}
    count=count_rows(support,ratio,spec['Bminus'],spec['B'])
    assert not count['inventory_domain_infeasible']
    rows=[];proofs={};n=len(support)
    H={f'rn_h_{i}_{j}':F(1) for i in support for j in support if i<j}
    for label,key,constant in [('NC1','TC',F(0)),('NC2','TC2',count['constant'])]:
        terms=dict(H);terms['rn_t']=-constant
        terms.update({f'rn_w_{i}_{y}':-v for (i,y),v in count[key].items() if v})
        row,p=safe_row('r145_'+label,terms,'>',0,bounds);rows.append(row);proofs[row['name']]=p
    L,U=F(spec['L_t']),F(spec['U_t']);bm,b=F(count['Bminus']),F(count['B'])
    for number,slope,endpoint,sense in [(1,L,bm,'>'),(2,U,b,'>'),(3,U,bm,'<'),(4,L,b,'<')]:
        # RN inventory equalities identify sum(rn_Y_i) with sum(y*w_iy).
        terms={f'rn_Y_{i}':F(1) for i in support}
        terms.update({f'Y_{i}':-slope for i in support});terms['rn_t']=-endpoint
        row,p=safe_row(f'r145_TS{number}',terms,sense,-endpoint*slope,bounds)
        rows.append(row);proofs[row['name']]=p
    return dict(rows=rows,transport_proofs=proofs,count=dict(thresholds=len(count['thresholds']),
        lower_positive=sum(x['ell']>0 for x in count['thresholds']),
        negative_slopes=sum(x['slope']<0 for x in count['thresholds']),
        negative_NC2_coefficients=sum(x<0 for x in count['TC2'].values()),
        constant_exact=str(count['constant']),tau_bounds=[int(bm),int(b)],
        ranges=[dict(theta=x['t'],delta=x['delta'],ell=x['ell'],u=x['u']) for x in count['thresholds']]))

def row_activity(row,point):
    lhs=math.fsum(a*point[k] for k,a in row['terms'].items());rhs=row['rhs']
    slack=lhs-rhs if row['sense']=='>' else rhs-lhs if row['sense']=='<' else -abs(lhs-rhs)
    scale=max([1.,abs(rhs)]+[abs(a) for a in row['terms'].values()])
    return dict(name=row['name'],lhs=lhs,rhs=rhs,slack=slack,violation=max(0.,-slack),scaled_violation=max(0.,-slack)/scale)

def project(rows,bounds,drop=1e-12):
    """Complete additional block dual projection, including NC, TS and any old extras."""
    a=collections.defaultdict(F);rhs=F(0);active=[];repairs=[]
    for row in rows:
        raw=F(row['Pi']);pi=max(raw,F(0)) if row['sense']=='>' else min(raw,F(0)) if row['sense']=='<' else raw
        assert row['sense'] in ('>','<','=')
        if pi!=raw:repairs.append(row['name'])
        if not pi:continue
        active.append(row['name']);rhs+=pi*F(row['rhs'])
        for k,v in row['terms'].items():a[k]+=pi*F(v)
    support=F(0);residuals={}
    for k in list(a):
        if k.startswith('rn_'):
            lo,hi=map(F,bounds[k]);support+=max(a[k]*lo,a[k]*hi);residuals[k]=str(a.pop(k))
    rhs-=support;correction=F(0);terms={}
    for k,v in a.items():
        assert k=='G' or k.startswith(('state_','Y_','h_','zprod_','state_g_')),k
        if not v:continue
        d=float(v)
        if abs(d)<drop:d=0.
        e=F(d)-v;lo,hi=map(F,bounds[k]);correction+=min(e*lo,e*hi)
        if d:terms[k]=d
    return dict(name='r145_PC',sense='>',terms=terms,rhs=outward(rhs+correction,False),
        exact_terms={k:str(v) for k,v in a.items() if v},exact_projected_rhs=str(rhs),
        box_support_exact=str(support),conversion_correction_exact=str(correction),
        new_column_residuals_exact=residuals,sign_repairs=repairs,active_source_rows=active,
        complete_source_rows=[r['name'] for r in rows],formal_RN_columns=0)
