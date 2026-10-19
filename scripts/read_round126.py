"""R126 main classifications explicitly exclude the historical both-open WIN rule."""
from round126_common import *
import collections, math, statistics
from round122_evidence import extension,event_chain
import read_round118 as reader
import read_round116 as inherited_reader
import round108_reader as core

def certification_pair(m,p):
    out=dict(id=m['id'],group_number=m['group_number'],seed=0,cap_seconds=m['cap_seconds'],candidate='M-B',control='P-GRB',
        MB_certified=m.get('certificate'),P_certified=p.get('certificate'),MB_T_cert=m.get('T_cert'),P_T_cert=p.get('T_cert'),
        MB_T_produce=m.get('T_produce'),P_T_produce=p.get('T_produce'),MB_T_total=m.get('T_total'),P_T_total=p.get('T_total'),
        speedup=None,observed_P_minus_MB_seconds=None,time_materiality_seconds=None,time_description=None,total_time_speedup=None,
        certified_objectives_compatible=None,one_sided_time_inference='none; actual return is not a counterfactual time-to-certification')
    good=all(a.get('formal_protocol_qualified') and a.get('certificate_qualified') and a.get('numbers_qualified') and not a.get('source_reduced') for a in [m,p])
    if not good:return dict(out,classification='UNEVALUABLE',evaluable=False,basis='required identity/lifecycle/physical/proof qualification unavailable or rejected')
    mc,pc=bool(m['certificate']),bool(p['certificate'])
    if mc and pc:
        compatible=abs(m['U']-p['U'])<=1e-7
        out['certified_objectives_compatible']=compatible
        if not compatible:return dict(out,classification='UNEVALUABLE',evaluable=False,basis='same-input certified physical objectives violate inherited 1e-7 consistency policy')
        mt,pt=m['T_cert'],p['T_cert'];assert mt and pt and mt>0 and pt>0
        diff=pt-mt;a=max(30.,.10*pt)
        out.update(speedup=pt/mt,observed_P_minus_MB_seconds=diff,time_materiality_seconds=a,
            time_description='MB_FASTER' if diff>=a else 'P_FASTER' if -diff>=a else 'TIME_CLOSE',
            total_time_speedup=p['T_total']/m['T_total'],total_time_order='MB_FASTER' if p['T_total']>m['T_total'] else 'P_FASTER' if p['T_total']<m['T_total'] else 'EQUAL')
        category='BOTH_CERTIFIED'
    else:category='MB_ONLY_CERTIFIED' if mc else 'P_ONLY_CERTIFIED' if pc else 'BOTH_OPEN'
    return dict(out,classification=category,evaluable=True,basis='complete qualified certification outcomes; gap is supplementary')

def rebuild_group(number,destination):
    n=int(number);dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    i=read(OUT/f'campaign/group{n:02d}/identity.json');candidate=read(OUT/'candidate_identity.json')
    assert i['helpers']==candidate['helpers']==helpers() and i['source_hashes']==bindings()
    core.start_reader.ROOT=ROOT;recs=collections.defaultdict(list)
    with extension():
        items=[reader.item(ROOT,l,i,recs) for l in i['launches']]
        claims=[q for v in items if v['complete'] for q in v['claims']]
        witnesses=[q for v in items if v['complete'] for q in v['ind']['witnesses']]
        final=inherited_reader.reconcile(claims,witnesses)
        assert final==inherited_reader.reconcile(list(reversed(claims)),list(reversed(witnesses)))
        arms=[reader.finalize(ROOT,v,final,recs) for v in items]
        mechanism=[dict(arm=v['l']['arm'],**event_chain(ROOT,v['l'],v['d'],v['j'])) for v in items if v['complete']]
    for a,v in zip(arms,items):
        p=v['l']['panel'];a.update(method=a['arm'],seed=0,source=p['source'],inventory=p['inventory'],input_identity=p['input_sha256'],
            T_cert=a['T_produce'] if a.get('certificate') and a.get('formal_protocol_qualified') else None,
            startup_zero=bool(a.get('certificate') and a.get('own_exact_zero') and a.get('native_Optimize')==0),
            observed_end='normal certified return' if a.get('certificate') else 'valid open normal return' if a.get('formal_protocol_qualified') else 'missing or unqualified observation')
        if p['inventory']=='shortage' and a.get('certificate'):
            assert a['U']>1e-12 and not a.get('own_exact_zero'),'shortage zero conflicts with sealed positive arithmetic; investigate before using proof'
    by={a['arm']:a for a in arms};pair=certification_pair(by['M-B'],by['P-GRB'])
    value=dict(group_number=n,arms=arms,pair=pair,adjudication=final,mechanism=mechanism,
        source_SHA=SOURCE,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA)
    write(dest/'current_core.json',value)
    for name,rows in dict(recs,arms=arms,certification_pairs=[pair]).items():
        if rows:core.table(dest/(name+'.csv'),rows)
    return value

def summarize():
    records=[read(OUT/f'reconstruction/group{n:02d}/current_core.json') for n in range(1,7) if (OUT/f'reconstruction/group{n:02d}/current_core.json').exists()]
    arms=[a for r in records for a in r['arms']];pairs=[r['pair'] for r in records]
    counts={c:sum(p['classification']==c for p in pairs) for c in ['BOTH_CERTIFIED','MB_ONLY_CERTIFIED','P_ONLY_CERTIFIED','BOTH_OPEN','UNEVALUABLE']}
    valid=len(arms)==12 and len(pairs)==6 and all(a.get('formal_protocol_qualified') for a in arms) and counts['UNEVALUABLE']==0
    reliability=any(r['adjudication']['rejections'] for r in records) or any(p.get('certified_objectives_compatible') is False for p in pairs)
    byid={p['id']:{a['arm']:a for a in arms if a['id']==p['id']} for p in pairs}
    support=[p['id'] for p in pairs if byid[p['id']]['M-B'].get('certificate') and byid[p['id']]['M-B']['U']>1e-12 and
        (p['classification']=='MB_ONLY_CERTIFIED' or p['classification']=='BOTH_CERTIFIED' and p['time_description']=='MB_FASTER')]
    losses=[p['id'] for p in pairs if p['classification']=='P_ONLY_CERTIFIED' or p['classification']=='BOTH_CERTIFIED' and p['time_description']=='P_FASTER']
    decision='PROOF_RELIABILITY_PRIORITY' if reliability else 'INCOMPLETE_CERTIFICATION_EVIDENCE' if not valid else 'LIMITED_DIRECT_CERTIFICATION_SUPPORT' if support and not losses else 'MIXED_DIRECT_CERTIFICATION_EVIDENCE' if support else 'NONZERO_CERTIFICATION_EVIDENCE_LIMITED'
    intersection=[p for p in pairs if p['classification']=='BOTH_CERTIFIED'];ratios=[p['speedup'] for p in intersection]
    per={m:dict(certified=sum(bool(a.get('certificate')) for a in arms if a['arm']==m),
        nonzero_certified=sum(bool(a.get('certificate')) and a['U']>1e-12 for a in arms if a['arm']==m),
        zero_certified=sum(bool(a.get('certificate')) and a['U']<=1e-12 for a in arms if a['arm']==m),
        startup_zero=sum(bool(a.get('startup_zero')) for a in arms if a['arm']==m)) for m in METHODS}
    value=dict(experiment_execution='COMPLETE' if valid else 'PARTIAL_OR_BLOCKED',fixed_problem_denominator=6,fixed_arm_denominator=12,
        observed_arms=len(arms),observed_pairs=len(pairs),categories=counts,per_method=per,scientific_judgment=decision,
        supporting_nonzero_problems=support,adverse_problems=losses,w=len(support),l=len(losses),
        both_certified_subset=dict(ids=[p['id'] for p in intersection],n=len(intersection),speedup_median=statistics.median(ratios) if ratios else None,
            speedup_geometric_mean=math.exp(statistics.fmean(math.log(x) for x in ratios)) if ratios else None,
            scope='conditional intersection only, not whole-panel average; no cap imputation'),
        physical_optima=[dict(id=id,values={m:a['U'] for m,a in aa.items() if a.get('certificate')}) for id,aa in byid.items() if any(a.get('certificate') for a in aa.values())],
        one_problem_even_if_both_methods_certify=True,fees=budget())
    core.table(OUT/'arms.csv',arms);core.table(OUT/'certification_pairs.csv',pairs);write(OUT/'certification_summary.json',value)
    return value

if __name__=='__main__':
    if sys.argv[1]=='summary':print(json.dumps(summarize()))
    else:rebuild_group(int(sys.argv[1]),sys.argv[2])
