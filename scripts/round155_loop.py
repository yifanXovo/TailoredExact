"""Persistent full-Q basic-dual closed loops, with exact original-price columns."""
from fractions import Fraction as F
from round143_math import outward
from round153_coupled import Master,support_row
from round153_lp import dual_certificate,primal_record,add_rows,finite_bounds
from round153_pricing import stock_value,serial_stock,keyed
from round152_math import states,unary_dp
from round155_common import *

def solve(master,target,cap=180.,save_model=False):
    m=master.m;target.mkdir(parents=True,exist_ok=True)
    m.Params.Threads=1;m.Params.Seed=0;m.Params.TimeLimit=cap
    m.Params.FeasibilityTol=1e-8;m.Params.OptimalityTol=1e-8;m.Params.Method=1
    m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
    m.update()
    if save_model:m.write(str(target/'model.mps'))
    write(target/'call.json',dict(UTC=utc(),Seed=0,Threads=1,Method=1,cap=cap,columns=m.NumVars,rows=m.NumConstrs,
          nonzeros=m.NumNZs,model_SHA=sha(target/'model.mps') if save_model else None,original_Q_variables_free=True))
    tick=time.perf_counter();m.optimize();native=time.perf_counter()-tick
    result=dict(Status=m.Status,Runtime=m.Runtime,Work=m.Work,native_seconds=native,iterations=m.IterCount,solutions=m.SolCount)
    write(target/'return.json',result)
    if m.SolCount:
        result.update(objective=m.ObjVal,primal=master.primal())
        if m.Status==2:result['quality']={k:m.getAttr(k) for k in ('ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio')}
    write(target/'result.json',result)
    return result

def direction(master,selected=None):
    """Cache exact original prices once, retaining the inherited correction."""
    m=master.m
    if selected is None:selected={c.ConstrName:c.Pi for c in m.getConstrs()}
    alpha=F(selected['hull_convexity']);beta=max(F(0),F(selected['hull_gini']))
    pi={k:F(selected[c.ConstrName]) for k,c in master.links.items()}
    d={k:-pi.get(k,F(0)) for k in states(master.scope)}
    prices={Y:beta*v['f']+sum((d[s['i'],y] for s,y in zip(master.scope['stations'],Y)),F(0)) for Y,v in master.values.items()}
    aK=min(alpha,min(prices.values()))
    cert=dual_certificate(m,pi=selected,bounds=master.bounds,exclude_columns=[v.VarName for v in master.columns.values()],
                          exclude_rhs=['hull_convexity','hull_gini'])
    assert cert['qualified'],cert['unresolved_infinite']
    cq=F(cert['lower_exact'])
    dp=unary_dp(master.scope,d);fallback=beta*F(master.scope['gamma_L'])+F(dp['exact'])
    cert.update(a_raw=float(alpha),a_true_RMP=outward(aK,False),a_true_RMP_exact=str(aK),
        true_column_min_exact=str(min(prices.values())),beta=float(beta),pi=keyed(pi),
        completion_margin_not_in_lower=True,bounds_derived_only_from_Q=True,one_convexity_correction=True)
    return dict(beta=beta,pi=pi,d=d,prices=prices,aK=aK,cq=cq,fallback=fallback,certificate=cert)

def witness(master,path,check):
    m=master.m
    point={v.VarName:v.X for v in m.getVars() if v.X!=0.}
    stocks=[dict(column=var.VarName,Y=list(Y),weight=var.X,f_exact=str(master.values[Y]['f']))
            for Y,var in master.columns.items() if var.X!=0.]
    save_gz(path,dict(sparse_point=point,missing_variables_are_zero=True,stocks=stocks,check=check,objective=m.ObjVal))

def classify_columns(master,stocks,beta,d,aK,tau):
    rows=[];added=[]
    for stock in sorted(stocks,key=lambda v:(F(v['price_exact']),tuple(v['Y']))):
        assert all(type(y) is int for y in stock['Y']),'returned inventory must already use exact supported integers'
        value=stock_value(master.scope,stock['Y'],beta,d)
        assert value['feasible'] and value['price']==F(stock['price_exact']) and value['f']==F(stock['f_exact'])
        Y=tuple(value['Y']);new=master.add(Y)
        row=dict(stock=serial_stock(value),new=new,true_reduced_cost_exact=str(value['price']-aK),
            target_violation_exact=str(value['price']-tau),negative=value['price']<aK)
        rows.append(row)
        if new:added.append(Y)
        # A duplicate is recorded as such and cannot count as progress.
        if not new:assert value['price']>=tau,'duplicate counterexample violates the qualified current-column ceiling'
    return rows,added

def column_usage(master,tracked,phase,iteration,path):
    """Track all Round155-origin columns across continuation phase boundaries."""
    used=[];marginals={}
    for Y,meta in tracked.items():
        weight=master.columns[Y].X
        if weight<=1e-10:continue
        meta['used_iterations']+=1;meta['maximum_weight']=max(meta['maximum_weight'],weight)
        if meta['first_used_iteration'] is None:
            meta['first_used_iteration']=iteration;meta['first_used_phase']=phase
        used.append(dict(Y=list(Y),weight=weight,origin_phase=meta['origin_phase'],added_iteration=meta['added_iteration']))
        for station,y in zip(master.scope['stations'],Y):
            marginals.setdefault(f'{station["i"]}:{y}',[]).append(weight)
    save_gz(path,dict(stocks=used,marginal_contributions={k:math.fsum(v) for k,v in marginals.items()},
        positive_weight_threshold=1e-10,includes_prior_Round155_phases=True,
        exact_full_primal_completion_checked_separately=True))
    return used

def run(role,label,rule='first',seconds='1800',iterations='12',previous='initial',price_cap='120'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    from round155_oracle import make_oracle
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    gate=read(OUT/'review/loop_admission.json')
    assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(__file__)
    assert gate['oracle_SHA']==sha(ROOT/'scripts/round155_oracle.py')
    assert gate['price_certificate_SHA']==sha(ROOT/'scripts/round155_price_certificate.py')
    tick=time.perf_counter();seconds=float(seconds);iterations=int(iterations);price_cap=float(price_cap);tolerance=1e-4
    initial=read(OUT/'starting_pools.json')[role]
    source=Path(initial['result']) if previous=='initial' else Path(previous);prior=read(source)
    if previous=='initial':assert sha(source)==initial['result_SHA']
    qp=Path(initial['Q']);assert sha(qp)==initial['Q_SHA']==prior['Q_SHA'] and prior['scope']==initial['scope']
    assert not prior.get('refresh_required',False)
    folder=OUT/'coupled'/f'{role}_{label}';folder.mkdir(parents=True,exist_ok=False)
    lower,upper=prior['lower'],prior['upper'];supports=list(prior['supports']);scope=prior['scope']
    records=[];new_columns={tuple(r['Y']):{k:v for k,v in r.items() if k!='Y'} for r in prior.get('new_column_usage',[])}
    upper_witness=prior.get('upper_witness_source');initial_count=len(prior['columns'])
    write(folder/'plan.json',dict(UTC=utc(),role=role,label=label,rule=rule,source=str(source),source_SHA=sha(source),
        Q=str(qp),Q_SHA=sha(qp),scope=scope,initial_columns=initial_count,initial_supports=len(supports),
        inherited_lower=lower,inherited_upper=upper,outer_allowance=seconds,iteration_limit=iterations or None,
        price_cap=price_cap,node_limit=256 if rule=='bounded' else None,price_absolute_gap=1e-7,
        tolerance=tolerance,Seed=0,Threads=1,selection='current_optimal_RMP_basic_dual',
        target='qualified_upper_minus_hull_tolerance',same_pool_no_competitor_results=True,
        absolute_price_and_residual_not_conflated=True,original_Q_variables_free=True,
        rule_does_not_switch_after_elapsed_seconds=True))
    costs=dict(build=0.,RMP=0.,selection=0.,certificate=0.,pricing=0.,feedback=0.)
    reason='offline_phase_allowance';refresh=True;iteration=0
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(qp),env=env) as m:
            start=time.perf_counter();master=Master(m,scope,gp,env)
            for Y in prior['columns']: assert master.add(Y)
            m.update();save_gz(folder/'Q_bounds.json.gz',dict(bounds=master.bounds,derivations=master.derivations))
            if (source.parent/'last_master.bas').exists():m.read(str(source.parent/'last_master.bas'))
            oracle=make_oracle(scope,env,rule,folder/'oracle_evidence');costs['build']+=time.perf_counter()-start
            while not iterations or iteration<iterations:
                if time.perf_counter()-tick>seconds-price_cap-240:
                    reason='offline_phase_allowance';break
                step=folder/f'iter{iteration:06}'
                start=time.perf_counter();rr=solve(master,step/'RMP',save_model=iteration==0);costs['RMP']+=time.perf_counter()-start
                if rr['Status']!=2 or not rr['primal']['qualified']:
                    reason='RMP_status_or_primal_qualification';break
                refresh=True
                if rr['objective']<upper:
                    upper=rr['objective'];upper_witness=str(step/'primal.json.gz');witness(master,Path(upper_witness),rr['primal'])
                elif iteration==0:
                    witness(master,step/'primal.json.gz',rr['primal'])
                used=column_usage(master,new_columns,label,iteration,step/'new_column_usage.json.gz')
                if upper-lower<=tolerance:reason='requested_hull_accuracy';break
                start=time.perf_counter();selected={c.ConstrName:c.Pi for c in m.getConstrs()}
                selection_seconds=time.perf_counter()-start;costs['selection']+=selection_seconds
                start=time.perf_counter();dr=direction(master,selected);costs['certificate']+=time.perf_counter()-start
                beta,pi,d,aK,cq=(dr[k] for k in ('beta','pi','d','aK','cq'))
                zeta=F(upper)-F(tolerance);tau=zeta-cq
                warm=sorted(dr['prices'],key=lambda Y:(dr['prices'][Y],Y))[:4]
                cert=dr['certificate'];ceiling=cq+aK
                frozen=dict(role=role,scope=scope,Q_SHA=prior['Q_SHA'],beta=float(beta),d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()},
                    C_Q_exact=str(cq),a_K_exact=str(aK),tau_exact=str(tau),zeta_exact=str(zeta),
                    initial_stocks=[list(Y) for Y in warm],initial_true_price_upper_exact=str(min(dr['prices'].values())),
                    inherited_price_lower_exact=str(dr['fallback']),columns_before=len(master.columns),
                    inherited_hull_lower=lower,inherited_hull_upper=upper,selection_method='direct_basic',frozen_before_price=True)
                write(step/'direction.json',frozen)
                if ceiling<zeta:
                    save_gz(step/'certificate.json.gz',cert);reason='qualified_direction_insufficient_ceiling';break
                start=time.perf_counter()
                price=oracle.price(beta,d,tau,step/'pricing',cap=price_cap,warm=warm,lp_cap=0.,absolute_gap=1e-7,
                    inherited_lower=outward(dr['fallback'],False),node_limit=256 if rule=='bounded' else None)
                costs['pricing']+=time.perf_counter()-start
                lm=F(price['lower']);fixed=cq+min(aK,lm);lower=max(lower,outward(fixed,False))
                cert.update(pricing_lower=price['lower'],pricing_lower_exact=str(lm),D_K_exact=str(cq+aK),
                    delta_exact=str(max(F(0),aK-lm)),coupled_lower=outward(fixed,False))
                save_gz(step/'certificate.json.gz',cert)
                start=time.perf_counter();row,correction=support_row(scope,beta,pi,price['lower'],len(supports))
                row['name']=f'r155_coupled_support_{len(supports):06}'
                support=dict(row=row,transport_exact=correction,price_path=(step/'pricing/result.json').relative_to(ROOT).as_posix(),
                    beta=float(beta),direction_SHA=sha(step/'direction.json'))
                supports.append(support);write(step/'support.json',support)
                feedback,added=classify_columns(master,price['stocks'],beta,d,aK,tau)
                save_gz(step/'column_feedback.json.gz',feedback)
                for Y in added:new_columns[Y]=dict(origin_phase=label,added_iteration=iteration,used_iterations=0,
                    maximum_weight=0.,first_used_iteration=None,first_used_phase=None)
                m.update();refresh=not bool(added);costs['feedback']+=time.perf_counter()-start
                negatives=sum(r['new'] and r['negative'] for r in feedback)
                true_upper=min([min(dr['prices'].values())]+[F(v['price_exact']) for v in price['stocks']])
                rec=dict(iteration=iteration,RMP_objective=rr['objective'],lower=lower,upper=upper,gap=upper-lower,
                    C_Q=float(cq),a_K=float(aK),beta=float(beta),target_hull=float(zeta),target_price=float(tau),
                    price_lower=price['lower'],price_upper=outward(true_upper,True),target_proved=lm>=tau,
                    target_disproved=true_upper<tau,columns=len(master.columns),supports=len(supports),
                    added=len(added),added_negative=negatives,duplicate_returns=sum(not r['new'] for r in feedback),
                    new_columns_used=len(used),new_column_total_weight=math.fsum(r['weight'] for r in used),
                    pricing_seconds=price['seconds'],selection_seconds=selection_seconds,selection_LP_Optimize=0,RMP_seconds=rr['native_seconds'],
                    cumulative_costs=dict(costs),elapsed_seconds=time.perf_counter()-tick,
                    Native_status=price['calls'][0]['Status'] if price['calls'] else None,rule=rule)
                records.append(rec);write(step/'result.json',rec)
                write(folder/'status.json',dict(role=role,label=label,decision='RUNNING',**rec))
                print(json.dumps(rec),flush=True)
                iteration+=1
                if upper-lower<=tolerance:reason='requested_hull_accuracy';break
                if not added:reason='undecided_price_no_new_column';break
                if not negatives:reason='no_new_true_negative_column';break
                if (folder/'checkpoint_requested.json').exists():reason='reviewed_checkpoint';break
            else:reason='matched_screen_iteration_allowance'
            if not refresh:
                start=time.perf_counter();rr=solve(master,folder/'final_RMP',cap=180.,save_model=True);costs['RMP']+=time.perf_counter()-start
                if rr['Status']==2 and rr['primal']['qualified']:
                    refresh=True;witness(master,folder/'final_primal.json.gz',rr['primal'])
                    if rr['objective']<upper:upper=rr['objective'];upper_witness=str(folder/'final_primal.json.gz')
                    column_usage(master,new_columns,label,iteration,folder/'final_column_usage.json.gz')
            m.write(str(folder/'last_master.mps'))
            if m.Status==2:m.write(str(folder/'last_master.bas'))
            if oracle.model is not None:oracle.model.write(str(folder/'last_price.mps'))
            oracle.close()
            costs['other_python_and_output']=max(0.,time.perf_counter()-tick-sum(costs.values()))
            result=dict(role=role,label=label,scope=scope,Q_SHA=prior['Q_SHA'],lower=lower,upper=upper,gap=upper-lower,
                columns=[list(Y) for Y in master.columns],supports=supports,records=records,prior_results=[str(source)],
                refresh_required=not refresh,upper_witness_source=upper_witness,decision=reason,
                inherited_upper_record=str(source),
                seconds=time.perf_counter()-tick,costs=costs,initial_columns=initial_count,rule=rule,
                original_variables_free=True,upper_is_not_physical=True,
                new_column_usage=[dict(Y=list(Y),**meta) for Y,meta in new_columns.items()])
            write(folder/'result.json',result)
    print(json.dumps({k:result[k] for k in ('role','label','lower','upper','gap','decision','seconds','costs')}),flush=True)

def replay(role,label,previous):
    """All cumulative supports against the same free original Q."""
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    from round153_lp import optimize
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    tick=time.perf_counter();source=Path(previous);prior=read(source)
    initial=read(OUT/'starting_pools.json')[role];qp=Path(initial['Q'])
    assert prior['Q_SHA']==sha(qp);target=OUT/'support_LP'/f'{role}_{label}';target.mkdir(parents=True,exist_ok=False)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.read(str(qp),env=env) as m:
            bounds,derivations=finite_bounds(m);add_rows(m,[s['row'] for s in prior['supports']],gp)
            rr=optimize(m,target/'solve',cap=180.);assert rr['Status']==2 and rr['primal']['qualified']
            cert=dual_certificate(m,bounds=bounds);assert cert['qualified'];save_gz(target/'certificate.json.gz',cert)
    lower=max(prior['lower'],cert['lower'])
    result=dict(prior,lower=lower,gap=prior['upper']-lower,prior_results=[str(source)],
        support_replay=dict(L=cert['lower'],U=rr['objective'],supports=len(prior['supports']),all_original_variables_free=True,
          finite_support_upper_not_full_hull_upper=True),seconds=time.perf_counter()-tick)
    if prior.get('derived_certificate_correction_not_new_optimization'):
        result['inherited_price_correction']=dict(source=str(source),source_SHA=sha(source),
            constructor_label=prior['qualification_constructor_label'])
        for key in ['derived_certificate_correction_not_new_optimization',
                    'raw_solve_times_are_not_new_measurements','qualification_constructor_label']:
            result.pop(key,None)
    write(target/'result.json',result);print(json.dumps(result['support_replay']),flush=True)

if __name__=='__main__': globals()[sys.argv[1]](*sys.argv[2:])
