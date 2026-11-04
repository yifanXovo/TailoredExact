"""Offline feasible-column discovery; never a full-domain pricing lower.

All heuristic scores are candidates only.  Every inserted inventory is
recomputed by stock_value, and only the unchanged complete master supplies
a qualified numerical primal upper.  Previously qualified lowers persist.
"""
from fractions import Fraction as F
from heapq import nsmallest
from itertools import product,combinations
from round153_common import *
from round153_pricing import stock_value
from round153_coupled import Master
from round153_lp import optimize


def neighbors(scope, parent):
    """All single-site states and all two-site changes preserving total."""
    ss=scope['stations'];parent=tuple(parent);total=sum(parent)
    for j,s in enumerate(ss):
        for y in s['support']:
            if y==parent[j]:continue
            if not scope['Bminus']<=total+y-parent[j]<=scope['B']:continue
            child=list(parent);child[j]=y;yield tuple(child)
    for j,s in enumerate(ss):
        for k in range(j+1,len(ss)):
            support=set(ss[k]['support'])
            for y in s['support']:
                delta=y-parent[j]
                if not delta or parent[k]-delta not in support:continue
                child=list(parent);child[j]=y;child[k]-=delta;yield tuple(child)


def score(scope, Y, beta, d):
    """Floating search order only; no bound and no feasibility authority."""
    ss=scope['stations'];n=len(ss);ratios=sorted(s['c']*y for s,y in zip(ss,Y))
    total=math.fsum(ratios)
    g=math.fsum((2*j-n+1)*r for j,r in enumerate(ratios))/(n*total) if total else 0.
    if g>scope['gamma_U']+1e-10:return math.inf
    return beta*max(scope['gamma_L'],g)+math.fsum(d.get((s['i'],y),0.) for s,y in zip(ss,Y))


def discover(scope, starts, beta, d, a, existing, per_start=64, max_new=512):
    pool={};examined=0;retained=0;rejected=0
    for parent in starts:
        def candidates():
            nonlocal examined
            for Y in neighbors(scope,parent):
                examined+=1
                if Y in existing:continue
                value=score(scope,Y,beta,d)
                if math.isfinite(value):yield value,Y
        # Ties use the integer inventory tuple, independent of hash ordering.
        selected=nsmallest(per_start,candidates())
        for approximate,Y in selected:
            if Y in pool:continue
            value=stock_value(scope,Y,beta,d)
            if not value['feasible']:rejected+=1;continue
            retained+=1
            if value['price']<F(a)-F(1e-9):pool[Y]=value
    chosen=sorted(pool,key=lambda Y:(pool[Y]['price'],Y))[:max_new]
    return chosen,dict(neighbors_scored=examined,exact_feasible_candidates=retained,
        exact_infeasible_candidates_rejected=rejected,negative_candidates=len(pool),
        per_start_limit=per_start,new_column_limit=max_new,
        candidate_order_is_not_a_bound=True,local_exhaustion_is_not_full_pricing=True,
        selected=[dict(Y=list(Y),f_exact=str(pool[Y]['f']),price_exact=str(pool[Y]['price'])) for Y in chosen])


def crossovers(first,second):
    differing=[j for j,(a,b) in enumerate(zip(first,second)) if a!=b]
    for size in (1,2):
        for positions in combinations(differing,size):
            left=list(first);right=list(second)
            for j in positions:left[j],right[j]=right[j],left[j]
            yield tuple(left),tuple(right)


def exchanges(scope, weighted, existing, max_pairs=64):
    """Keep complementary columns together, without individual RC filtering."""
    seen=0
    def candidates():
        nonlocal seen
        for (first,w1),(second,w2) in combinations(weighted,2):
            old=score(scope,first,1.,{})+score(scope,second,1.,{})
            for left,right in crossovers(first,second):
                seen+=1
                if left in existing and right in existing:continue
                if not (scope['Bminus']<=sum(left)<=scope['B'] and scope['Bminus']<=sum(right)<=scope['B']):continue
                change=score(scope,left,1.,{})+score(scope,right,1.,{})-old
                if math.isfinite(change) and change<-1e-12:
                    yield min(w1,w2)*change,first,second,left,right,w1,w2
    pairs=[];chosen={}
    for approximate,first,second,left,right,w1,w2 in nsmallest(max_pairs,candidates()):
        v=[stock_value(scope,Y) for Y in (first,second,left,right)]
        if not all(r['feasible'] for r in v):continue
        change=v[2]['f']+v[3]['f']-v[0]['f']-v[1]['f']
        if change>=0:continue
        assert all(sorted((first[j],second[j]))==sorted((left[j],right[j])) for j in range(len(first)))
        pairs.append(dict(parents=[list(first),list(second)],children=[list(left),list(right)],
            parent_weights=[w1,w2],f_exact=[str(r['f']) for r in v],f_sum_change_exact=str(change),
            movable_weight=min(w1,w2),single_column_RC_filter_not_applied=True))
        for Y in (left,right):
            if Y not in existing:chosen[Y]=None
    return list(chosen),dict(crossovers_scored=seen,pair_candidate_limit=max_pairs,pairs=pairs,
        retained_new_columns=len(chosen),marginal_preserving_pairs=True,
        full_Q_reoptimization_still_required=True,local_exhaustion_not_claimed=True)


def qualify(label):
    from round152_qualify import scope
    configure();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    domains=[scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75,[.125]*3),
        scope([1.,.5],[[0,1,2,3,4]]*2,0,4,.05,.3),
        scope([.5,.25,.75],[[1],[0,2,5],[1,3]],2,7,.2,.8)]
    records=[];checks=0;pair_checks=0;accepted_pairs=0
    for domain in domains:
        labels=list(product(*[s['support'] for s in domain['stations']]))
        feasible=[Y for Y in labels if stock_value(domain,Y)['feasible']]
        costs={(s['i'],y):((-1)**(s['i']+y))*(y+1)/8 for s in domain['stations'] for y in s['support']}
        for parent in feasible:
            actual=set(neighbors(domain,parent));expected=set()
            for child in labels:
                changed=sum(a!=b for a,b in zip(parent,child))
                if domain['Bminus']<=sum(child)<=domain['B'] and (changed==1 or (changed==2 and sum(child)==sum(parent))):expected.add(child)
            assert actual==expected
            checks+=len(labels)
        for beta in (0.,1.7):
            for Y in labels:
                value=stock_value(domain,Y,beta,costs);approx=score(domain,Y,beta,costs)
                if value['feasible']:
                    assert math.isfinite(approx) and abs(approx-float(value['price']))<1e-12
                checks+=1
            selected,record=discover(domain,feasible,beta,costs,100.,set(),per_start=len(labels),max_new=len(labels))
            expected={Y for parent in feasible for Y in neighbors(domain,parent)
                if stock_value(domain,Y,beta,costs)['feasible']}
            assert set(selected)==expected
            for item in record['selected']:
                value=stock_value(domain,item['Y'],beta,costs)
                assert value['feasible'] and value['f']==F(item['f_exact']) and value['price']==F(item['price_exact'])
            records.append(dict(beta=beta,Cartesian_labels=len(labels),legal_stocks=len(feasible),selected=len(selected)))
        for first,second in combinations(feasible[:8],2):
            for left,right in crossovers(first,second):
                assert all(sorted((first[j],second[j]))==sorted((left[j],right[j])) for j in range(len(first)))
                assert all(y in s['support'] for s,y in zip(domain['stations'],left))
                assert all(y in s['support'] for s,y in zip(domain['stations'],right))
                pair_checks+=1
        selected,exchange=exchanges(domain,[(Y,1/len(feasible)) for Y in feasible[:8]],set())
        for pair in exchange['pairs']:
            values=[stock_value(domain,Y) for Y in pair['parents']+pair['children']]
            assert all(v['feasible'] for v in values)
            assert values[2]['f']+values[3]['f']-values[0]['f']-values[1]['f']==F(pair['f_sum_change_exact'])<0
            accepted_pairs+=1
        assert set(selected)=={tuple(Y) for p in exchange['pairs'] for Y in p['children']}
    assert accepted_pairs>0
    write(target/'result.json',dict(PASS=True,checks=checks,controls=records,Native_Optimize=0,
        marginal_pair_checks=pair_checks,accepted_complementary_pairs=accepted_pairs,
        implementation_SHA=sha(Path(__file__)),core_SHA=sha(ROOT/'scripts/round153_coupled.py'),
        stock_value_SHA=sha(ROOT/'scripts/round153_pricing.py'),
        unchanged_master_qualification_reused=True,heuristic_does_not_supply_lower=True))
    print(json.dumps(dict(PASS=True,checks=checks,controls=len(records))),flush=True)


def run(role,label,resume,seconds='1200',tolerance='0.0001',qualification='primal_pool_v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    qualified=read(OUT/'qualification'/qualification/'result.json')
    assert qualified['PASS'] and qualified['implementation_SHA']==sha(Path(__file__))
    assert qualified['core_SHA']==sha(ROOT/'scripts/round153_coupled.py')
    assert qualified['stock_value_SHA']==sha(ROOT/'scripts/round153_pricing.py')
    seconds=float(seconds);tolerance=float(tolerance);assert tolerance>0
    tick=time.perf_counter();source=Path(resume)/'result.json';previous=read(source)
    target=OUT/'coupled'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False)
    qp=OUT/'reference'/role/'direct/model.mps';scope=read(OUT/'reference'/role/'domain.json')['scope']
    assert previous['scope']==scope and previous['Q_SHA']==sha(qp)
    columns=list(dict.fromkeys(tuple(Y) for Y in previous['columns']))
    assert len(columns)==len(previous['columns']);lower=previous['lower'];upper=previous['upper'];steps=[]
    write(target/'plan.json',dict(UTC=utc(),role=role,scope=scope,Q_SHA=sha(qp),
        prior_result=str(source),prior_result_SHA=sha(source),initial_columns=len(columns),
        outer_cap=seconds,absolute_target=tolerance,per_start_limit=64,max_single_negative_columns=512,
        max_complementary_pairs=64,max_new_columns_per_sweep=640,
        positive_weight_seed_limit=16,minimum_existing_price_seed_limit=16,
        stop='no new selected heuristic column, nonoptimal master, or normal offline cap',
        entire_original_Q_free=True,new_pricing_lower=False,
        qualification_SHA=sha(OUT/'qualification'/qualification/'result.json')))
    result=dict(role=role,label=label,scope=scope,Q_SHA=sha(qp),lower=lower,upper=upper,
        gap=upper-lower,columns=[list(Y) for Y in columns],records=[],supports=previous['supports'],
        prior_results=[str(source)],seconds=0.,decision='INITIALIZED_PRIMAL_DISCOVERY',
        upper_is_not_physical=True,original_variables_free=True,new_RMP_solve=True,
        primal_discovery_only=True,no_new_lower_claim=True,primal_sweeps=steps)
    write(target/'result.json',result)
    reason='offline_capacity_checkpoint'
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(qp),env=env) as m:
            master=Master(m,scope,gp,env)
            for Y in columns:master.add(Y)
            save_gz(target/'Q_bounds.json.gz',dict(bounds=master.bounds,derivations=master.derivations))
            sweep=0
            while time.perf_counter()-tick<seconds-35:
                folder=target/f'sweep{sweep:05}'
                solved=optimize(m,folder,cap=min(180.,seconds-(time.perf_counter()-tick)-10),save_model=sweep==0)
                primal=master.primal() if m.SolCount else None
                if primal and primal['qualified'] and m.ObjVal<upper:
                    upper=m.ObjVal
                    save_gz(target/'best_primal.json.gz',dict(point={v.VarName:v.X for v in m.getVars()},
                        stocks=[dict(Y=list(Y),weight=v.X,f_exact=str(master.values[Y]['f']))
                            for Y,v in master.columns.items() if abs(v.X)>1e-14],check=primal))
                result.update(upper=upper,gap=upper-lower)
                if solved['Status']!=2:reason='restricted_master_not_optimal';break
                a,pi,beta=master.prices();d={k:-v for k,v in pi.items()}
                positive=sorted((Y for Y,v in master.columns.items() if v.X>1e-10),
                    key=lambda Y:(-master.columns[Y].X,Y))[:16]
                cheap=sorted(master.columns,key=lambda Y:(score(scope,Y,beta,d),Y))[:16]
                starts=list(dict.fromkeys(positive+cheap))
                if upper-lower<=tolerance:
                    chosen=[];discovery=dict(requested_interval_accuracy=True);exchange=dict(pairs=[])
                elif time.perf_counter()-tick>=seconds-30:
                    chosen=[];discovery=dict(discovery_skipped_at_offline_cap=True);exchange=dict(pairs=[])
                else:
                    chosen,discovery=discover(scope,starts,beta,d,a,set(master.columns))
                    pair_columns,exchange=exchanges(scope,[(Y,master.columns[Y].X) for Y in positive],set(master.columns))
                    chosen=list(dict.fromkeys(chosen+pair_columns))
                assert len(chosen)<=640
                write(folder/'discovery.json',dict(starts=[list(Y) for Y in starts],
                    beta=beta,a=a,d={f'{i}:{y}':v for (i,y),v in d.items()},**discovery,
                    paired_exchange=exchange,new_columns=[list(Y) for Y in chosen]))
                before=len(master.columns)
                for Y in chosen:assert master.add(Y)
                m.update()
                record=dict(sweep=sweep,RMP_objective=solved['objective'],primal=primal,
                    lower=lower,upper=upper,gap=upper-lower,columns_before=before,
                    columns=len(master.columns),added=len(chosen),elapsed_seconds=time.perf_counter()-tick,
                    heuristic_price_is_not_lower=True)
                steps.append(record);write(folder/'result.json',record)
                result.update(upper=upper,gap=upper-lower,columns=[list(Y) for Y in master.columns],
                    seconds=time.perf_counter()-tick,decision='RUNNING_PRIMAL_DISCOVERY')
                write(target/'result.json',result)
                print(json.dumps({k:record[k] for k in ['sweep','lower','upper','gap','columns','added','elapsed_seconds']}),flush=True)
                if not chosen:
                    reason=('requested_interval_accuracy' if discovery.get('requested_interval_accuracy') else
                        'offline_capacity_checkpoint' if discovery.get('discovery_skipped_at_offline_cap') else
                        'NO_NEW_SELECTED_HEURISTIC_COLUMN_FULL_PRICE_UNDECIDED')
                    break
                sweep+=1
            m.write(str(target/'last_master.mps'))
    result.update(seconds=time.perf_counter()-tick,decision=reason)
    write(target/'result.json',result)
    print(json.dumps(dict(role=role,decision=reason,lower=lower,upper=upper)),flush=True)


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
