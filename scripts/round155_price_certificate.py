"""Conservative residual transport from the actually saved Native state costs.

The original numerical guard is retained in full. The additional exact error
only accounts for the observed Native state-coefficient omissions. The price
domain and optimization model are unchanged.
"""
from fractions import Fraction as F
from itertools import combinations
from round143_math import outward
from round152_math import states,unary_dp
from round153_pricing import stock_value
from round155_common import *


def recover_actual(path, result=None):
    path=Path(path);p=read(path) if result is None else result
    c=read(path.parent/'call.json');delta=load_gz(path.parent/'matrix_delta.json.gz')
    ext=read(path.parent/'strengthening.json');scope=p['scope'];ss=scope['stations']
    assert not p['prior_residual_transports'], 'Round155 closed loops use fresh same-direction bounds'
    rows={name:(sense,F(rhs),{k:F(v) for k,v in terms}) for name,sense,rhs,terms in delta['rows']}
    native={k:-rows['hard_cost_D_definition'][2].get(f'x[{k[0]},{k[1]}]',F(0)) for k in states(scope)}
    written=c['residual_coefficients'];intended={tuple(map(int,k.split(':'))):F(v) for k,v in written['state'].items()}
    def row(name,terms,sense,rhs):
        assert rows[name]==(sense,F(rhs),{k:F(v) for k,v in terms.items() if v}),name
    row('hard_cost_D_definition',{'hard_cost_D':1}|{f'x[{i},{y}]':-v for (i,y),v in native.items()},'=',0)
    row('hard_cost_W_definition',{'hard_cost_W':1}|{f'Sx[{i},{y}]':-v for (i,y),v in native.items()},'=',0)
    W={f'Sx[{i},{y}]':-v for (i,y),v in native.items()}
    row('floor_residual',W|{'S':-F(written['S_floor']),'residual_scaled':1},'>',0)
    row('G_residual',W|{'S':-F(written['S_G']),'residual_scaled':1}|
        {f'abs[{i},{j}]':-F(written['A']) for i,j in combinations([s['i'] for s in ss],2)},'>',0)
    l,u=map(F,c['positive_S_bounds']);a,b=map(F,ext['tight_cost_bounds'])
    for name,slope,endpoint,sense in [('ll',l,a,'>'),('uu',u,b,'>'),('ul',u,a,'<'),('lu',l,b,'<')]:
        row('tight_DP_cost_product_'+name,{'hard_cost_W':1,'hard_cost_D':-slope,'S':-endpoint},sense,outward(-slope*endpoint,sense=='<'))
    assert len(rows)==8
    changed={f'{i}:{y}':dict(intended_exact=str(intended[i,y]),actual_exact=str(v))
             for (i,y),v in native.items() if v!=intended[i,y]}
    if changed:
        lo=F(unary_dp(scope,native)['exact']);hi=-F(unary_dp(scope,{k:-v for k,v in native.items()})['exact'])
    else:
        lo,hi=map(F,ext['tight_cost_DP_exact'])
    domain_covered=a<=lo<=hi<=b
    d={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()}
    anchors={s['i']:(min(d[s['i'],y] for y in s['support'])+max(d[s['i'],y] for y in s['support']))/2 for s in ss}
    scale=F(c['scale'])
    epsilon=u*sum((max([F(0)]+[native[s['i'],y]-(d[s['i'],y]-anchors[s['i']])/scale
                               for y in s['support']]) for s in ss),F(0))
    beta=F(p['beta_exact']);tau=F(p['tau_exact'])
    fallback=beta*F(scope['gamma_L'])+F(unary_dp(scope,d)['exact'])
    positive=fallback;ell=None;q=p['calls'][0]
    accepted=bool(q['bound_status_qualified'] and domain_covered)
    if accepted:
        ell=scale*(F(q['native_bound'])-F(c['residual_guard_scaled'])-epsilon)
        positive=max(positive,tau+ell/(u if ell>=0 else l))
    lower=positive
    if c['bounds']['zero_possible']:
        lower=min(lower,stock_value(scope,[0]*len(ss),beta,d)['price'])
    if p['inherited_lower'] is not None:
        assert F(p['inherited_lower'])<=fallback
        lower=max(lower,F(p['inherited_lower']))
    assert all(lower<=F(v['price_exact']) for v in p['stocks'])
    return dict(schema='round155-actual-native-state-transport-v1',
        call_SHA=sha(path.parent/'call.json'),matrix_delta_SHA=sha(path.parent/'matrix_delta.json.gz'),
        strengthening_SHA=sha(path.parent/'strengthening.json'),changed_state_costs=changed,
        native_cost_DP_lower_exact=str(lo),native_cost_DP_upper_exact=str(hi),
        actual_cost_bounds_cover_complete_domain=domain_covered,
        additional_scaled_residual_error_exact=str(epsilon),original_numerical_guard_retained=True,
        native_bound_accepted=accepted,residual_lower_exact=str(ell) if ell is not None else None,
        positive_lower=outward(positive,False),lower_exact=str(lower),lower=outward(lower,False),
        target_proved=lower>=tau,absolute_price_gap=c['absolute_price_gap'],source_SHA=sha(__file__))


def corrected_result(original, correction):
    result=dict(original)
    result.update(lower=correction['lower'],positive_lower=correction['positive_lower'],
        residual_lower_exact=correction['residual_lower_exact'],target_proved=correction['target_proved'],
        native_state_transport=correction)
    true_upper=min((F(v['price_exact']) for v in result['stocks']),default=None)
    result['decision']='RESOLVED' if true_upper is not None and true_upper-F(correction['lower_exact'])<=F(correction['absolute_price_gap']) else 'UNDECIDED'
    return result


def qualified_price(path):
    """Read a forward corrected result or a hash-bound historical correction."""
    path=Path(path);raw=read(path)
    if 'native_state_transport' in raw:return raw
    index=OUT/'review/native_price_corrections.json'
    if not index.exists():return raw
    key=path.resolve().relative_to(ROOT.resolve()).as_posix()
    item=read(index)['prices'].get(key)
    if item is None:return raw
    assert sha(path)==item['raw_result_SHA']
    corrected=ROOT/item['qualified_price'];assert sha(corrected)==item['qualified_price_SHA']
    result=read(corrected);assert result['raw_result_SHA']==sha(path)
    return result


def qualified_phase(path):
    path=Path(path);index=OUT/'review/native_price_corrections.json'
    if not index.exists():return path,read(path)
    key=path.resolve().relative_to(ROOT.resolve()).as_posix();item=read(index)['phases'].get(key)
    if item is None:return path,read(path)
    assert sha(path)==item['raw_result_SHA']
    corrected=ROOT/item['qualified_result'];assert sha(corrected)==item['qualified_result_SHA']
    return corrected,read(corrected)
