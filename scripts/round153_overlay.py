"""Combine paid full/conditional prices on a common exact S refinement."""
from fractions import Fraction as F
from round143_math import outward
from round152_math import s_bounds,unary_dp
from round153_common import *
from round153_pricing import stock_value,serial_stock
from round153_coupled import support_row
from round153_audit import audit_price


def run(role,label,resume,source_iteration,*parent_prices):
    configure();tick=time.perf_counter();prior=Path(resume)/'result.json';data=read(prior)
    source=Path(source_iteration);cert=load_gz(source/'certificate.json.gz');source_plan=read(source.parent/'plan.json')
    scope=data['scope'];assert data['role']==role and data['Q_SHA']==source_plan['Q_SHA']==sha(OUT/'reference'/role/'direct/model.mps')
    assert source_plan['scope']==scope and cert['qualified']
    target=OUT/'coupled'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False)
    inputs=[source/'pricing/result.json']+list(map(Path,parent_prices));assert len(inputs)==len(set(p.resolve() for p in inputs))
    seen={};parents=[audit_price(p,seen) for p in inputs];base=parents[0]
    assert all(p['complete_domain'] and p['scope']==scope and p['beta']==base['beta'] and p['d_exact']==base['d_exact'] for p in parents)
    costs={tuple(map(int,k.split(':'))):F(v) for k,v in base['d_exact'].items()};beta=base['beta'];pi={k:-v for k,v in costs.items()}
    assert cert['beta']==beta and all(F(cert['pi'].get(k,0.))==-F(v) for k,v in base['d_exact'].items())
    write(target/'plan.json',dict(UTC=utc(),role=role,scope=scope,Q_SHA=data['Q_SHA'],
        source_iteration=str(source),source_certificate_SHA=sha(source/'certificate.json.gz'),
        source_price_SHA=sha(inputs[0]),source_plan_SHA=sha(source.parent/'plan.json'),prior_result_SHA=sha(prior),
        new_RMP_solve=False,new_Native_calls=0,only_paid_same_direction_bounds_reused=True))
    bounds=json.loads(json.dumps(s_bounds(scope)));dp=unary_dp(scope,costs);assert dp is not None
    fallback=F(beta)*F(scope['gamma_L'])+F(dp['exact']);global_lower=max([fallback]+[F(p['lower']) for p in parents])
    conditions=[];points={F(bounds['lower_exact']),F(bounds['upper_exact'])}
    for p in parents:
        if not p.get('partitioned_full_price'):continue
        assert p['positive_S_bounds']==bounds
        for row in p['child_results']:
            child_path=ROOT/row['result'];child=read(child_path)
            assert not child['complete_domain'] and str(child_path.resolve()) in seen
            lo,hi=map(F,child['S_interval_exact']);points.update([lo,hi])
            conditions.append(dict(lo=lo,hi=hi,lower=F(child['lower']),path=str(child_path)))
    points=sorted(points);cells=[]
    if F(bounds['upper_exact'])>0:
        assert F(bounds['lower_exact'])>0
        cells=[(points[0],points[0])] if len(points)==1 else list(zip(points[:-1],points[1:]))
    lows=[max([global_lower]+[c['lower'] for c in conditions if c['lo']<=lo<=hi<=c['hi']]) for lo,hi in cells]
    zero=None
    if bounds['zero_possible']:
        z=stock_value(scope,[0]*len(scope['stations']),beta,costs);assert z['feasible'];zero=z['price']
    pieces=lows+([zero] if zero is not None else []);assert pieces
    lower=outward(max(global_lower,min(pieces)),False);stocks={}
    for Y in data['columns']+[v['Y'] for p in parents for v in p['stocks']]:
        v=stock_value(scope,Y,beta,costs);assert v['feasible'];stocks[tuple(v['Y'])]=v
    upper=outward(min(v['price'] for v in stocks.values()),True)
    pricing=target/'pricing';pricing.mkdir()
    price=dict(scope=scope,beta=beta,d=base['d'],d_exact=base['d_exact'],
        fallback_lower=outward(fallback,False),fallback_exact=str(fallback),zero_lower=outward(zero,False) if zero is not None else None,
        lower=lower,upper=upper,stocks=[serial_stock(v) for v in stocks.values()],calls=[],
        complete_domain=True,overlay_full_price=True,positive_S_bounds=bounds,
        source_prices=[dict(path=str(p),SHA256=sha(p)) for p in inputs],source_price_audit=seen,
        cells_exact=[[str(a),str(b)] for a,b in cells],cell_lowers_exact=list(map(str,lows)),
        same_direction_global_lower_exact=str(global_lower),
        reason='common_exact_positive_S_refinement_of_paid_bounds_plus_legal_zero',
        decision='RESOLVED' if upper-lower<=1e-5 else 'UNDECIDED',seconds=time.perf_counter()-tick,
        new_Optimize=0,new_RMP_solve=False,upper_is_inventory_price_only=True)
    write(pricing/'result.json',price)
    effective=max(F(base['lower']),F(lower));aK=F(cert['a_true_RMP_exact']);dk=F(cert['lower_exact'])+aK;delta=max(F(0),aK-effective)
    refined=dict(cert,pricing_lower=outward(effective,False),pricing_lower_exact=str(effective),
        D_K=outward(dk,False),D_K_exact=str(dk),delta=outward(delta,True),delta_exact=str(delta),
        coupled_lower=outward(dk-delta,False),source_certificate=str(source/'certificate.json.gz'),
        price_paths=[str(inputs[0]),str(pricing/'result.json')],same_direction_lower_max=True,new_Q_dual_or_RMP_solve=False)
    save_gz(target/'refined_certificate.json.gz',refined)
    row,transport=support_row(scope,beta,pi,lower,len(data['supports']))
    supports=data['supports']+[dict(row=row,transport_exact=transport,price_path=str((pricing/'result.json').relative_to(ROOT)),beta=beta)]
    result=dict(data,label=label,lower=max(data['lower'],refined['coupled_lower']),records=[],prior_results=[str(prior)],
        columns=[list(Y) for Y in sorted(stocks)],supports=supports,new_RMP_solve=False,
        refinements=[dict(certificate=str(target/'refined_certificate.json.gz'),corrected_lower=refined['coupled_lower'])],
        seconds=time.perf_counter()-tick,decision='PAID_CONDITIONAL_BOUND_OVERLAY')
    result['gap']=result['upper']-result['lower'];write(target/'result.json',result)
    print(json.dumps(dict(role=role,lower=result['lower'],upper=result['upper'],gap=result['gap'],
        price_lower=lower,price_upper=upper,cells=len(cells),new_Optimize=0,seconds=result['seconds'])),flush=True)


if __name__=='__main__':run(*sys.argv[1:])
