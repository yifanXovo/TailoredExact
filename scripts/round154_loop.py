"""Complete-Q coupling with a uniformly selected target oracle.

Every direction/task is saved before pricing. Stops use the actual hull
accuracy, a returned counterexample/undecided price, finite iterations or the
whole offline phase allowance. No time-based component switching is used.
"""
from fractions import Fraction as F
from round143_math import outward
from round152_math import states,unary_dp
from round153_coupled import Master,support_row
from round153_lp import optimize
from round153_stabilize import select_dual
from round153_pricing import stock_value
from round154_common import *

def run(role,label,previous,implementation='residual_goal',iterations='8',price_cap='600',seconds='6000',tolerance='.0001'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_exact_worker import enable
    from round154_goal_oracle import TargetResidualOracle,TargetRNOracle
    configure();affinity();enable();assert binding()['sha256']==DLL_SHA
    qualification=read(OUT/'qualification/goal_stop_v1/result.json')
    assert qualification['PASS'] and qualification['goal_oracle_SHA']==sha(ROOT/'scripts/round154_goal_oracle.py')
    assert qualification['core_SHA']==sha(ROOT/'scripts/round154_residual.py')
    assert qualification['strong_SHA']==sha(ROOT/'scripts/round154_strengthened.py')
    assert qualification['RN_core_SHA']==sha(ROOT/'scripts/round153_pricing.py')
    gate=read(OUT/'review/target_coupling_admission.json')
    assert gate['decision']=='ACCEPT' and gate['independent_nonimplementer_review']
    assert gate['source_SHA']==sha(__file__)
    assert implementation in ('residual_goal','RN_goal')
    tick=time.perf_counter();iterations=int(iterations);price_cap=float(price_cap);seconds=float(seconds);tolerance=float(tolerance)
    source=Path(previous);prior=read(source);scope=prior['scope'];qp=OLD153/'reference'/role/'direct/model.mps'
    assert prior['Q_SHA']==sha(qp) and prior['role']==role
    folder=OUT/'coupled'/f'{role}_{label}';folder.mkdir(parents=True,exist_ok=False)
    lower=prior['lower'];upper=prior['upper'];supports=list(prior['supports']);records=[]
    write(folder/'plan.json',dict(UTC=utc(),role=role,scope=scope,Q_SHA=sha(qp),prior_result=str(source),prior_SHA=sha(source),
        implementation=implementation,iterations=iterations,price_cap=price_cap,outer_allowance=seconds,absolute_target=tolerance,
        initial_columns=len(prior['columns']),initial_supports=len(supports),Seed=0,Threads=1,
        dual_rule='near-optimal zero-center band1e-7; if unqualified, current basic RMP dual; complete current pool',
        target_rule='qualified current RMP upper minus declared hull tolerance',all_Q_variables_free=True,
        no_support_shrinkage=True,no_other_direction_price_lower_mixing=True))
    refreshed=not bool(prior.get('refresh_required',False));reason='finite_iteration_allowance'
    upper_witness=prior.get('upper_witness_source')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(qp),env=env) as m:
            master=Master(m,scope,gp,env)
            for Y in prior['columns']:assert master.add(Y)
            m.update();save_gz(folder/'Q_bounds.json.gz',dict(bounds=master.bounds,derivations=master.derivations))
            oracle=TargetResidualOracle(scope,env) if implementation=='residual_goal' else TargetRNOracle(scope,env,old_joint=True)
            for iteration in range(iterations):
                if time.perf_counter()-tick>seconds-price_cap-600:
                    reason='whole_phase_allowance_before_new_price';break
                step=folder/f'iter{iteration:05}';rr=optimize(m,step/'RMP',cap=180.,save_model=True)
                assert rr['Status']==2;primal=master.primal();assert primal['qualified'];refreshed=True
                if m.ObjVal<upper:
                    upper=m.ObjVal
                    save_gz(folder/'best_primal.json.gz',dict(point={v.VarName:v.X for v in m.getVars()},check=primal,
                        stocks=[dict(Y=list(Y),weight=var.X,f_exact=str(master.values[Y]['f'])) for Y,var in master.columns.items() if abs(var.X)>1e-14]))
                    upper_witness=str(folder/'best_primal.json.gz')
                if upper-lower<=tolerance:reason='requested_hull_accuracy';break
                selected,selection=select_dual(master,step/'selection',band=1e-7,cap=120.,center='zero')
                if selected is None:
                    # A failed stabilization solve gives no certificate.
                    # The already optimal current RMP still supplies a basic
                    # dual; qualify it against the full Q below in exactly
                    # the same way as a selected direction.
                    selected={c.ConstrName:c.Pi for c in m.getConstrs()}
                    selection_method='current_basic_RMP_dual_after_unqualified_selection'
                else:selection_method='qualified_near_optimal_zero_center'
                write(step/'selected_direction_source.json',dict(method=selection_method,
                    selection_status=selection['status'],selection_SHA=sha(step/'selection/selection.json.gz'),
                    failed_selection_not_used_as_bound=True))
                a=selected['hull_convexity'];pi={k:selected[c.ConstrName] for k,c in master.links.items()};beta=max(0.,selected['hull_gini'])
                d={k:F(-pi.get(k,0.)) for k in states(scope)}
                dp=unary_dp(scope,d);fallback=F(beta)*F(scope['gamma_L'])+F(dp['exact'])
                cert=master.certificate(a,pi,beta,outward(fallback,False),selected)
                cq,aK=F(cert['lower_exact']),F(cert['a_true_RMP_exact']);zeta=F(upper)-F(tolerance);tau=zeta-cq
                warm=sorted(master.values,key=lambda Y:(F(beta)*master.values[Y]['f']+sum(d[s['i'],y] for s,y in zip(scope['stations'],Y)),Y))[:4]
                initial_price=min(F(beta)*master.values[Y]['f']+sum(d[s['i'],y] for s,y in zip(scope['stations'],Y)) for Y in warm)
                ceiling=cq+min(aK,initial_price)
                direction=dict(role=role,scope=scope,Q_SHA=sha(qp),beta=beta,d_exact={f'{i}:{y}':str(v) for (i,y),v in d.items()},
                    C_Q_exact=str(cq),a_K_exact=str(aK),tau_exact=str(tau),zeta_exact=str(zeta),initial_stocks=[list(Y) for Y in warm],
                    initial_true_price_upper_exact=str(initial_price),ceiling_exact=str(ceiling),columns_before=len(master.columns),
                    inherited_hull_lower=lower,inherited_hull_upper=upper,source_Q_bounds=str(folder/'Q_bounds.json.gz'),
                    inherited_price_lower_exact=str(fallback),
                    frozen_before_price=True,not_a_full_hull_ceiling=True,selection_method=selection_method)
                write(step/'direction.json',direction);save_gz(step/'provisional_certificate.json.gz',cert)
                if ceiling<zeta:reason='selected_direction_has_insufficient_ceiling';break
                if implementation=='residual_goal':price=oracle.price(beta,d,tau,step/'pricing',cap=price_cap,warm=warm)
                else:price=oracle.price(beta,d,step/'pricing',cap=price_cap,warm=warm,tau=tau)
                lm=F(price['lower']);dk=cq+aK;delta=max(F(0),aK-lm);fixed=cq+min(aK,lm)
                cert.update(pricing_lower=price['lower'],pricing_lower_exact=str(lm),delta=outward(delta,True),delta_exact=str(delta),
                    D_K=outward(dk,False),D_K_exact=str(dk),coupled_lower=outward(fixed,False))
                save_gz(step/'certificate.json.gz',cert);lower=max(lower,outward(fixed,False))
                row,correction=support_row(scope,beta,pi,price['lower'],len(supports));row['name']=f'r154_coupled_support_{len(supports):05}'
                supports.append(dict(row=row,transport_exact=correction,price_path=str((step/'pricing/result.json').relative_to(ROOT)),beta=beta,
                                     direction_SHA=sha(step/'direction.json')))
                added=0;negative=0;before=len(master.columns)
                for stock in price['stocks']:
                    v=stock_value(scope,stock['Y'],beta,d);assert v['feasible'] and v['price']==F(stock['price_exact'])
                    fresh=master.add(stock['Y']);added+=fresh;negative+=bool(fresh and v['price']<aK)
                if added:refreshed=False
                m.update()
                true_upper=min([initial_price]+[F(v['price_exact']) for v in price['stocks']]);ceiling=cq+min(aK,true_upper)
                rec=dict(iteration=iteration,RMP_objective=rr['objective'],beta=beta,C_Q=float(cq),a_K=float(aK),
                    target_hull=float(zeta),target_price=float(tau),price_lower=price['lower'],price_upper=outward(true_upper,True),
                    target_proved=lm>=tau,target_disproved=true_upper<tau,fixed_certificate_ceiling=outward(ceiling,True),
                    lower=lower,upper=upper,gap=upper-lower,columns_before=before,columns=len(master.columns),added=added,added_negative=negative,
                    supports=len(supports),pricing_seconds=price['seconds'],elapsed_seconds=time.perf_counter()-tick,
                    Native_status=price['calls'][0]['Status'] if price['calls'] else None,implementation=implementation,
                    negative_column_reference='true_column_corrected_a_K')
                records.append(rec);write(step/'result.json',rec)
                write(folder/'result.json',dict(prior,role=role,label=label,lower=lower,upper=upper,gap=upper-lower,
                    columns=[list(Y) for Y in master.columns],supports=supports,records=records,prior_results=[str(source)],
                    refresh_required=not refreshed,decision='RUNNING_TARGET_COUPLING',seconds=time.perf_counter()-tick))
                print(json.dumps(rec),flush=True)
                if upper-lower<=tolerance:reason='requested_hull_accuracy';break
                if added==0:reason='fixed_target_unresolved_no_new_column';break
                if negative==0:reason='fixed_target_unresolved_no_new_negative_column';break
            if not refreshed:
                final=optimize(m,folder/'final_refresh',cap=180.,save_model=True)
                assert final['Status']==2 and master.primal()['qualified'];refreshed=True
                if m.ObjVal<upper:upper=m.ObjVal;upper_witness=str(folder/'final_primal.json.gz')
                save_gz(folder/'final_primal.json.gz',dict(point={v.VarName:v.X for v in m.getVars()},check=master.primal(),
                    stocks=[dict(Y=list(Y),weight=var.X,f_exact=str(master.values[Y]['f'])) for Y,var in master.columns.items() if abs(var.X)>1e-14]))
            oracle.close()
            result=dict(prior,role=role,label=label,lower=lower,upper=upper,gap=upper-lower,columns=[list(Y) for Y in master.columns],
                supports=supports,records=records,prior_results=[str(source)],refresh_required=not refreshed,
                implementation=implementation,decision=reason,seconds=time.perf_counter()-tick,original_variables_free=True,
                upper_is_not_physical=True,last_columns_evaluated=True,upper_witness_source=upper_witness)
            write(folder/'result.json',result)
    print(json.dumps(dict(role=role,decision=reason,lower=lower,upper=upper,gap=upper-lower,columns=len(result['columns']))),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
