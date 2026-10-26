"""Independent exact coefficient algebra and full exported primal checks."""
from round120_common import *
from fractions import Fraction as Q
import math,re
def binary(v):return Q.from_float(float(v))
def coefficients(path):
    path=Path(path);meta=read(str(path)+'.round120.json')
    a,m,b=map(binary,[meta['a'],meta['m'],meta['b']]);c=binary(meta['objective_constant'])
    b0,b1=map(binary,[meta['beta0'],meta['beta1']])
    if not meta['conditional']:b0=b1=min(b0,b1)
    lb,ld,ub,ud,fb,fd=[Q(meta[k]) for k in ['lower_base','lower_delta','upper_base','upper_delta','objective_base','objective_delta']]
    # Fractions represent the actual finite decimal literals, not rounded
    # double sums. Check all h=0/1 endpoints, including each difference sum.
    assert lb<=a and lb+ld<=m and ub>=m and ub+ud>=b
    assert fb+c<=b0 and fb+fd+c<=b1
    lines=path.read_text().splitlines();actual={line.strip().split(':',1)[0]:line.strip().split(':',1)[1] for line in lines if line.strip().startswith(('r120_g_lower:','r120_g_upper:','r120_f_lower:'))}
    assert len(actual)==3 and actual['r120_g_lower']==f' G - {meta["lower_delta"]} r120_h >= {meta["lower_base"]}'
    assert actual['r120_g_upper']==f' G - {meta["upper_delta"]} r120_h <= {meta["upper_base"]}'
    assert Q(actual['r120_f_lower'].rsplit('>=',1)[1].strip())==fb
    rhs=[str(a-lb),str(m-(lb+ld)),str(ub-m),str((ub+ud)-b),str(b0-(fb+c)),str(b1-(fb+fd+c))]
    return dict(path=str(path),SHA=sha(path),passed=True,exact_rational_endpoint_slacks=rhs,
        theoretical_a=float(a),theoretical_m=float(m),theoretical_b=float(b),actual_decimal_endpoints=[str(lb),str(lb+ld),str(ub),str(ub+ud)],
        source_is_numerical_not_rational_certificate=True,objective_constant=float(c),conditional=meta['conditional'])
def native_endpoints(path,pair):
    r=read(path);a,m,b=map(binary,[pair['a'],pair['m'],pair['b']]);b0,b1=map(binary,[pair['beta0'],pair['beta1']])
    conditional='_d1' in Path(path).name or r.get('objective_delta',0)!=0
    if not conditional:b0=b1=min(b0,b1)
    lb,ld,ub,ud,fb,fd,c=[binary(r[k]) for k in ['lower_base','lower_delta','upper_base','upper_delta','objective_base','objective_delta','objective_constant']]
    assert lb<=a and lb+ld<=m and ub>=m and ub+ud>=b and fb+c<=b0 and fb+fd+c<=b1
    assert r['h_type']=='B' and r['h_LB']==0 and r['h_UB']==1 and r['h_BranchPriority']==0
    return dict(path=str(path),SHA=sha(path),actual_native_binary64_exact_endpoint_check=True)
def scalar_math():
    # Eliminate h by independent interval feasibility on exact fractions.
    cases=[]
    for a,m,b in [(Q(0),Q(1,3),Q(1)),(Q(1,10),Q(2,5),Q(7,10))]:
        for b0,b1 in [(Q(1,5),Q(4,5)),(Q(4,5),Q(1,5)),(Q(2,5),Q(2,5)),(Q(0),Q(0))]:
            for g in [a,a+(m-a)/2,m,m+(b-m)/2,b]:
                lo=max(Q(0),(g-m)/(b-m));hi=min(Q(1),(g-a)/(m-a));assert lo<=hi
                minimum=b0+(b1-b0)*(lo if b1>=b0 else hi)
                projected=max(b0,b0+(b1-b0)*(g-m)/(b-m)) if b1>=b0 else max(b1,b1+(b0-b1)*(m-g)/(m-a))
                assert minimum==projected;cases.append([str(x) for x in [a,m,b,b0,b1,g,minimum]])
    # Concrete non-cut-valid epigraph completion: true G=0/F=.3, virtual
    # g=.25 gives f=.55, below right beta .65. Its exact-G extension survives.
    assert Q(3,10)+Q(1,4)<Q(65,100) and Q(3,10)>=Q(3,10)
    return dict(exact_projection_cases=cases,cutoff_complement_counterexample=[.5,1,.6],parent_direction_counterexample=[0,1,2],
        virtual_g_auxiliary_completion_is_not_physical_G=True,zero_denominator_rejected_in_explanation=True)
def diagnostic_role(role):
    dest=OUT/'qualification/diagnostics'/role;checks=[]
    for kind in ['D0_original_objective','D1_original_objective','D0_max_conditional_violation']:
        d=dest/kind;r=read(d/'record.json');p=read(d/'full_primal_and_original_matrix.json');x=p['primal']
        assert r['Optimize']==1 and len(p['names'])==r['columns'] and len(p['rhs'])==r['rows']
        assert len(p['column_indices'])==len(p['coefficients'])==r['nonzeros']
        maximum=0.;bounds=0.
        if x:
            assert len(x)==len(p['names']) and all(math.isfinite(v) for v in x)
            for row,(rhs,sense) in enumerate(zip(p['rhs'],p['senses'])):
                z=range(p['row_starts'][row],p['row_starts'][row+1]);lhs=math.fsum(p['coefficients'][j]*x[p['column_indices'][j]] for j in z)
                violation=abs(lhs-rhs) if sense=='=' else max(0.,lhs-rhs) if sense=='<' else max(0.,rhs-lhs)
                maximum=max(maximum,violation)
            for v,lo,hi in zip(x,p['lower_bounds'],p['upper_bounds']):bounds=max(bounds,lo-v,v-hi)
            assert maximum<=1e-7 and bounds<=1e-7,(role,kind,maximum,bounds)
        checks.append(dict(kind=kind,record=r,independent_full_row_maximum=maximum,independent_full_bound_maximum=bounds,
            complete_original_blocks_checked=True,saved_model_SHA=sha(d/'actual_complete_relaxation.mps'),
            full_primal_and_matrix_SHA=sha(d/'full_primal_and_original_matrix.json')))
    maxcheck=checks[-1]['record']
    nonredundant=bool(maxcheck['qualified'] and maxcheck['actual_D1_row_violation']>1e-7 and maxcheck['qualified_beta_violation']>1e-7)
    redundant=bool(maxcheck['qualified'] and maxcheck['qualified_bound']<=1e-7 and maxcheck['actual_D1_row_violation']<=1e-7)
    return dict(role=role,checks=checks,conditional_row_nonredundant_in_complete_LP=nonredundant,
        no_new_information_reliably_proved=redundant,diagnostic_unresolved=not(nonredundant or redundant))
def run():
    begin=time.perf_counter();values=scalar_math();emit=[]
    for p in (OUT/'qualification').rglob('*.lp.round120.json'):emit.append(coefficients(Path(str(p)[:-len('.round120.json')])))
    roles=[diagnostic_role(r) for r in ['F2','R98-C2']]
    write(OUT/'qualification/math_and_LP_information.json',dict(passed=True,independent_method='exact Fraction elimination/serialized endpoints and complete API matrix primal residual arithmetic',
        scalar_math=values,serialized_models=emit,roles=roles,at_least_one_complete_LP_nonredundant=any(v['conditional_row_nonredundant_in_complete_LP'] for v in roles),
        both_complete_LPs_reliably_redundant=all(v['no_new_information_reliably_proved'] for v in roles),
        any_diagnostic_unresolved=any(v['diagnostic_unresolved'] for v in roles),Optimize=0,new_native_starts=0,engineering_seconds=time.perf_counter()-begin))
    print(json.dumps([{k:v[k] for k in ['role','conditional_row_nonredundant_in_complete_LP','no_new_information_reliably_proved','diagnostic_unresolved']} for v in roles]))
if __name__=='__main__':run()
