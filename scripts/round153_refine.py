"""Refine one saved full-domain price without resolving its restricted master."""
from fractions import Fraction as F
from round143_math import outward
from round153_common import *
from round153_coupled import support_row
from round153_partitioned import PartitionedOracle
from round153_pricing import stock_value


def run(role, label, resume, source_iteration, cap='300', parts='4', implementation='partition'):
    from round100_gurobi_runtime import gp, binding
    from round150_lp import affinity
    configure(); affinity(); assert binding()['sha256'] == DLL_SHA
    tick=time.perf_counter(); prior=Path(resume)/'result.json'; source=Path(source_iteration)
    data=read(prior); old=read(source/'pricing/result.json'); cert=load_gz(source/'certificate.json.gz')
    source_plan=read(source.parent/'plan.json');parts=int(parts);assert 1<=parts<=64
    assert implementation in ('partition','transport','graphcut')
    qualification=None
    if implementation=='transport':
        qp=OUT/'qualification/transport_v1/result.json';qr=read(qp);assert qr['PASS']
        assert all(r['extension']['extension_source_SHA']==sha(ROOT/'scripts/round153_transport.py') and
            r['extension']['frozen_core_SHA']==sha(ROOT/'scripts/round153_pricing.py') for r in qr['facts'])
        qualification=dict(path=str(qp),SHA256=sha(qp),new_interface_only=True)
    if implementation=='graphcut':
        qp=OUT/'qualification/graphcut_v1/result.json';qr=read(qp);assert qr['PASS']
        assert qr['source_SHA']==sha(ROOT/'scripts/round153_graphcut.py')
        assert all(r['frozen_core_SHA']==sha(ROOT/'scripts/round153_pricing.py') for r in qr['facts'])
        qualification=dict(path=str(qp),SHA256=sha(qp),new_interface_only=True)
    scope=data['scope']; qpath=OUT/'reference'/role/'direct/model.mps'
    assert data['role']==role and data['Q_SHA']==sha(qpath)
    assert source_plan['Q_SHA']==data['Q_SHA'] and source_plan['scope']==scope
    assert old['scope']==scope and old['complete_domain'] and cert['qualified']
    d={tuple(map(int,k.split(':'))):F(v) for k,v in old['d_exact'].items()}
    pi={k:-v for k,v in d.items()}; beta=old['beta']
    assert F(beta)==F(cert['beta'])
    assert all(F(cert['pi'].get(f'{i}:{y}',0.))==-v for (i,y),v in d.items())
    target=OUT/'coupled'/f'{role}_{label}'; target.mkdir(parents=True,exist_ok=False)
    write(target/'plan.json',dict(role=role,UTC=utc(),scope=scope,Q_SHA=data['Q_SHA'],
        source_iteration=str(source),source_certificate_SHA=sha(source/'certificate.json.gz'),
        source_plan_SHA=sha(source.parent/'plan.json'),positive_S_parts=parts if implementation in ('partition','graphcut') else None,
        pricing_implementation=implementation,
        pricing_qualification=qualification,
        source_price_SHA=sha(source/'pricing/result.json'),prior_result_SHA=sha(prior),
        Native_cap=float(cap) if implementation!='graphcut' else None,
        offline_graph_search_cap=float(cap) if implementation=='graphcut' else None,
        same_beta_d=True,old_Q_dual_reused=True,new_RMP_solve=False,
        motivation='Saved inventory-price upper permits a better corrected lower than the accumulated bound.',
        possible_corrected_lower_using_saved_price_upper=float(F(cert['lower_exact'])+min(F(cert['a_true_RMP_exact']),F(old['upper'])))))
    candidates=set(map(tuple,data['columns']))|{tuple(v['Y']) for v in old['stocks']}
    warm=sorted(candidates,key=lambda Y:stock_value(scope,Y,beta,d)['price'])[:4]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        if implementation=='transport':
            from round153_transport import TransportOracle
            oracle=TransportOracle(scope,env,old_joint=True)
        elif implementation=='graphcut':
            from round153_graphcut import GraphOracle
            oracle=GraphOracle(scope,env,parts=parts,iterations=20)
        else:oracle=PartitionedOracle(scope,env,old_joint=True,parts=parts)
        price=oracle.price(beta,d,target/'pricing',cap=float(cap),warm=warm)
        oracle.close()
    assert price['complete_domain'] and price['scope']==old['scope'] and price['beta']==old['beta'] and price['d_exact']==old['d_exact']
    effective=max(F(old['lower']),F(price['lower'])); aK=F(cert['a_true_RMP_exact'])
    cq=F(cert['lower_exact']); delta=max(F(0),aK-effective); dk=cq+aK
    refined=dict(cert,pricing_lower=outward(effective,False),pricing_lower_exact=str(effective),
        delta=outward(delta,True),delta_exact=str(delta),D_K=outward(dk,False),D_K_exact=str(dk),
        coupled_lower=outward(dk-delta,False),source_certificate=str(source/'certificate.json.gz'),
        price_paths=[str(source/'pricing/result.json'),str(target/'pricing/result.json')],
        same_direction_lower_max=True,new_Q_dual_or_RMP_solve=False)
    save_gz(target/'refined_certificate.json.gz',refined)
    row,transport=support_row(scope,beta,pi,price['lower'],len(data['supports']))
    supports=data['supports']+[dict(row=row,transport_exact=transport,
        price_path=str((target/'pricing/result.json').relative_to(ROOT)),beta=beta)]
    for v in price['stocks']:
        assert stock_value(scope,v['Y'])['feasible'];candidates.add(tuple(v['Y']))
    lower=max(data['lower'],refined['coupled_lower'])
    result=dict(data,label=label,lower=lower,gap=data['upper']-lower,records=[],
        prior_results=[str(prior)],columns=[list(Y) for Y in sorted(candidates)],supports=supports,
        primal_discovery_only=False,no_new_lower_claim=False,primal_sweeps=[],
        ancestor_primal_evidence_retained_via_prior_results=True,
        refinements=[dict(certificate=str(target/'refined_certificate.json.gz'),
            old_price_interval=[old['lower'],old['upper']],new_price_interval=[price['lower'],price['upper']],
            corrected_lower=refined['coupled_lower'])],
        new_RMP_solve=False,seconds=time.perf_counter()-tick,decision='SAME_DIRECTION_PRICE_REFINEMENT')
    write(target/'result.json',result)
    print(json.dumps(dict(role=role,lower=lower,upper=result['upper'],gap=result['gap'],
        old_price=[old['lower'],old['upper']],new_price=[price['lower'],price['upper']],
        columns=len(candidates),seconds=result['seconds'])),flush=True)


if __name__=='__main__':run(*sys.argv[1:])
