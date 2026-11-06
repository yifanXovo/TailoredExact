"""Inspect the observed saved-row mismatch without Optimize or qualification."""
from fractions import Fraction as F
from itertools import combinations
from round143_math import outward
from round155_common import *


def run(label='level_price_matrix_diagnostic_v1'):
    configure()
    target=OUT/'qualification'/label
    target.mkdir(parents=True,exist_ok=False)
    facts=[]
    for path in sorted((OUT/'coupled').glob('*_feasible_level_deep_v2/iter*/pricing/result.json')):
        p=read(path);c=read(path.parent/'call.json')
        delta=load_gz(path.parent/'matrix_delta.json.gz')
        w=c['residual_coefficients']
        wc={tuple(map(int,k.split(':'))):F(v) for k,v in w['state'].items()}
        actual={name:(sense,F(rhs),{k:F(v) for k,v in terms}) for name,sense,rhs,terms in delta['rows']}
        expected={}
        def row(name,terms,sense,rhs):
            expected[name]=(sense,F(rhs),{k:F(v) for k,v in terms.items() if v})
        row('hard_cost_D_definition',{'hard_cost_D':1}|{f'x[{i},{y}]':-v for (i,y),v in wc.items()},'=',0)
        row('hard_cost_W_definition',{'hard_cost_W':1}|{f'Sx[{i},{y}]':-v for (i,y),v in wc.items()},'=',0)
        W={f'Sx[{i},{y}]':-v for (i,y),v in wc.items()}
        row('floor_residual',W|{'S':-F(w['S_floor']),'residual_scaled':1},'>',0)
        row('G_residual',W|{'S':-F(w['S_G']),'residual_scaled':1}|
            {f'abs[{i},{j}]':-F(w['A']) for i,j in combinations([s['i'] for s in p['scope']['stations']],2)},'>',0)
        l,u=map(F,c['positive_S_bounds'])
        a,b=map(F,read(path.parent/'strengthening.json')['tight_cost_bounds'])
        for name,slope,endpoint,sense in [('ll',l,a,'>'),('uu',u,b,'>'),('ul',u,a,'<'),('lu',l,b,'<')]:
            row('tight_DP_cost_product_'+name,{'hard_cost_W':1,'hard_cost_D':-slope,'S':-endpoint},sense,outward(-slope*endpoint,sense=='<'))
        differences=[]
        assert set(actual)==set(expected)
        for name in expected:
            es,er,et=expected[name];as_,ar,at=actual[name]
            assert (es,er)==(as_,ar),(str(path),name,'sense/RHS mismatch')
            for variable in sorted(set(et)|set(at)):
                ev,av=et.get(variable,F(0)),at.get(variable,F(0))
                if ev!=av:
                    differences.append(dict(row=name,variable=variable,expected_exact=str(ev),actual_exact=str(av),
                        delta_exact=str(av-ev),absolute_delta=float(abs(av-ev)),omitted=av==0))
        facts.append(dict(path=path.relative_to(ROOT).as_posix(),result_SHA=sha(path),
            call_SHA=sha(path.parent/'call.json'),matrix_delta_SHA=sha(path.parent/'matrix_delta.json.gz'),
            differences=differences,lower=p['lower'],fallback_lower=p['fallback_lower'],
            inherited_lower=p['inherited_lower'],native_bound=p['calls'][0]['native_bound'],
            native_status=p['calls'][0]['Status'],bound_status_qualified=p['calls'][0]['bound_status_qualified'],
            residual_guard_scaled=c['residual_guard_scaled'],positive_S_bounds=c['positive_S_bounds'],
            tight_cost_bounds=[float(a),float(b)]))
    assert facts
    result=dict(decision='DIAGNOSTIC_ONLY_NO_QUALIFICATION',prices=facts,Optimize=0,Native_model_reads=0,
        source_SHA=sha(__file__),does_not_modify_or_accept_raw_scientific_evidence=True)
    write(target/'result.json',result)
    print(json.dumps(dict(prices=len(facts),with_differences=sum(bool(r['differences']) for r in facts),
        differences=sum(len(r['differences']) for r in facts),
        maximum_absolute_coefficient_difference=max((v['absolute_delta'] for r in facts for v in r['differences']),default=0.),
        lower_above_fallback=sum(r['lower']>r['fallback_lower'] for r in facts),Optimize=0)),flush=True)


def assess(label='level_price_omission_assessment_v1'):
    from round152_math import unary_dp,states
    from round153_pricing import stock_value
    configure();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    prior_path=OUT/'qualification/level_price_matrix_diagnostic_v1/result.json'
    diagnostic=read(prior_path);facts=[]
    for item in diagnostic['prices']:
        path=ROOT/item['path'];p=read(path);c=read(path.parent/'call.json')
        delta=load_gz(path.parent/'matrix_delta.json.gz');scope=p['scope'];ss=scope['stations']
        actual={name:(sense,F(rhs),{k:F(v) for k,v in terms}) for name,sense,rhs,terms in delta['rows']}
        native_cost={k:-actual['hard_cost_D_definition'][2].get(f'x[{k[0]},{k[1]}]',F(0)) for k in states(scope)}
        for name in ['hard_cost_W_definition','floor_residual','G_residual']:
            assert all(actual[name][2].get(f'Sx[{i},{y}]',F(0))==-v for (i,y),v in native_cost.items())
        lo=unary_dp(scope,native_cost);hi=unary_dp(scope,{k:-v for k,v in native_cost.items()})
        a,b=map(F,read(path.parent/'strengthening.json')['tight_cost_bounds'])
        d={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()}
        anchor={s['i']:(min(d[s['i'],y] for y in s['support'])+max(d[s['i'],y] for y in s['support']))/2 for s in ss}
        scale=F(c['scale']);l,u=map(F,c['positive_S_bounds'])
        error=u*sum((max([F(0)]+[native_cost[s['i'],y]-(d[s['i'],y]-anchor[s['i']])/scale
                               for y in s['support']]) for s in ss),F(0))
        q=p['calls'][0];assert q['bound_status_qualified']
        ell=scale*(F(q['native_bound'])-F(c['residual_guard_scaled'])-error)
        beta=F(p['beta_exact']);tau=F(p['tau_exact'])
        fallback=beta*F(scope['gamma_L'])+F(unary_dp(scope,d)['exact'])
        qualified=max(fallback,tau+ell/(u if ell>=0 else l))
        if c['bounds']['zero_possible']:
            qualified=min(qualified,stock_value(scope,[0]*len(ss),beta,d)['price'])
        support_path=path.parent.parent/'support.json';support=read(support_path)
        facts.append(dict(path=item['path'],result_SHA=sha(path),
            native_cost_DP_lower_exact=lo['exact'],native_cost_DP_upper_exact=str(-F(hi['exact'])),
            actual_DP_domain_bounds_contain_all_stocks=a<=F(lo['exact']) and b>=-F(hi['exact']),
            native_DP_lower_slack_exact=str(F(lo['exact'])-a),native_DP_upper_slack_exact=str(b+F(hi['exact'])),
            state_omission_residual_upper_error_exact=str(error),state_omission_residual_upper_error=float(error),
            same_numerical_guard_retained=True,corrected_price_lower_exact=str(qualified),
            corrected_price_lower=outward(qualified,False),recorded_price_lower=p['lower'],
            recorded_price_lower_is_below_corrected_exact=F(p['lower'])<=qualified,
            support_SHA=sha(support_path),
            saved_support_RHS_below_corrected_exact=F(support['row']['rhs'])<=qualified+F(support['transport_exact']),
            recorded_price_slack_exact=str(qualified-F(p['lower'])),
            saved_support_slack_exact=str(qualified+F(support['transport_exact'])-F(support['row']['rhs']))))
    write(target/'result.json',dict(decision='DIAGNOSTIC_ASSESSMENT_NOT_FINAL_QUALIFICATION',prices=facts,
        diagnostic_SHA=sha(prior_path),Optimize=0,Native_model_reads=0,source_SHA=sha(__file__)))
    print(json.dumps(dict(prices=len(facts),native_domain_bound_failures=sum(not r['actual_DP_domain_bounds_contain_all_stocks'] for r in facts),
        recorded_price_lower_failures=sum(not r['recorded_price_lower_is_below_corrected_exact'] for r in facts),
        saved_support_RHS_failures=sum(not r['saved_support_RHS_below_corrected_exact'] for r in facts),
        maximum_scaled_residual_error=max(r['state_omission_residual_upper_error'] for r in facts),Optimize=0)),flush=True)


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
