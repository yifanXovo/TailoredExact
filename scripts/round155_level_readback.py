"""Actual fixed-level trajectory, complete candidate and endpoint readback.

Run only after the phase closes, following its independent price/Q readback.
This reconstructs saved selector models and performs no Optimize.
"""
from fractions import Fraction as F
from types import SimpleNamespace
from round143_lp import semantics
from round143_math import outward
from round152_math import states
from round153_audit import exact_matrix,replay_q_bounds,independent_residual
from round153_lp import primal_record
from round153_pricing import stock_value
from round155_level_check import matrix_check
from round155_price_certificate import qualified_price,qualified_phase
from round155_common import *


def run(label,phase,loop_readback):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA
    folder=OUT/'coupled'/phase;path=folder/'result.json';qualified_result,result=qualified_phase(path);plan=read(folder/'plan.json')
    prior=read(plan['source']);audit_path=OUT/'qualification'/loop_readback/'result.json';audit=read(audit_path)
    checked=next(v for v in audit['phases'] if Path(v['result']).resolve()==path.resolve())
    assert audit['PASS'] and checked['SHA256']==sha(path) and not result['refresh_required']
    assert checked['qualified_result_SHA']==sha(qualified_result)
    assert sha(plan['Q'])==plan['Q_SHA']==result['Q_SHA'] and sha(plan['source'])==plan['source_SHA']
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    scope=plan['scope'];pool={tuple(Y):j for j,Y in enumerate(prior['columns'])};fvalues={}
    lower,upper=prior['lower'],prior['upper'];zeta=(F(lower)+F(upper))/2
    exits=[];facts=[];matrices=[];selected_count=0;nonoptimal=0
    rmp_paths=sorted(folder.glob('iter*/RMP/result.json'))
    calls=sorted(folder.glob('iter*/selection/call.json'));assert calls
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(plan['Q'],env=env) as q:
            names={v.VarName for v in q.getVars()};original_rows={c.ConstrName for c in q.getConstrs()}
            q_semantics=semantics(q);q_matrix=exact_matrix(q)
        bounds=replay_q_bounds(q_matrix,load_gz(folder/'Q_bounds.json.gz'))
        with gp.read(str(folder/'iter000000/RMP/model.mps'),env=env) as m, gp.read(str(calls[0].parent/'model.mps'),env=env) as dual:
            assert semantics(m,names,original_rows)==q_semantics
            columns={Y:m.getVarByName(f'hull_lambda_{j:05}') for Y,j in pool.items()}
            assert all(v is not None for v in columns.values())
            master=SimpleNamespace(m=m,gp=gp,original_names=names,scope=scope,columns=columns)
            mapping={c.ConstrName:f'pi_{j}' for j,c in enumerate(m.getConstrs())}
            native_vars={v.VarName:v for v in dual.getVars()}
            def add_inventory(Y):
                assert Y not in pool
                value=stock_value(scope,Y);assert value['feasible'];fvalues[Y]=value['f']
                rows=[m.getConstrByName('hull_convexity'),m.getConstrByName('hull_gini')]
                coeff=[1.,-outward(value['f'],True)]
                for s,y in zip(scope['stations'],Y):
                    if y!=s['support'][0]:
                        rows.append(m.getConstrByName(f'hull_link_{s["i"]}_{y}'));coeff.append(1.)
                name=f'hull_lambda_{len(pool):05}'
                var=m.addVar(lb=0.,obj=0.,column=gp.Column(coeff,rows),name=name)
                dual.addConstr(gp.LinExpr(coeff,[native_vars[mapping[c.ConstrName]] for c in rows])<=0.,name='dual_'+name)
                pool[Y]=len(pool);columns[Y]=var
            def accept_upper(rr,iteration):
                nonlocal upper,zeta
                if rr['Status']!=2 or not rr.get('primal',{}).get('qualified'):return False
                upper=min(upper,rr['objective'])
                if F(upper)<zeta:
                    exits.append((str(zeta),'qualified_full_Q_primal_below',iteration,lower,upper))
                    zeta=(F(lower)+F(upper))/2
                return True
            for rp in rmp_paths:
                step=rp.parent.parent;iteration=int(step.name.removeprefix('iter'));rr=read(rp)
                if not accept_upper(rr,iteration):
                    assert not (step/'selection/call.json').exists();continue
                selection=step/'selection';call_path=selection/'call.json'
                if not call_path.exists():
                    assert upper-lower<=plan['tolerance'];continue
                call=read(call_path);returned=read(selection/'result.json')
                assert F(call['zeta_exact'])==zeta==F(returned['zeta_exact'])
                assert F(call['nominal_level_exact'])==zeta+F(1e-7)
                assert F(call['nominal_RHS'])>=F(call['nominal_level_exact'])-F(call['original_constant'])
                assert call['current_stock_count']==len(pool)
                dual.getConstrByName('nominal_fixed_level').RHS=call['nominal_RHS'];dual.update();m.update()
                assert (dual.NumVars,dual.NumConstrs,dual.NumNZs)==(call['columns'],call['rows'],call['nonzeros'])
                if call_path in (calls[0],calls[-1]):
                    matrix=matrix_check(master,dual,call['nominal_RHS']);matrices.append(dict(iteration=iteration,**matrix))
                    if 'nominal_level_omitted_coefficients_exact' in call:
                        assert matrix['nominal_level_omitted_coefficients_exact']==call['nominal_level_omitted_coefficients_exact']
                warm=primal_record(dual,load_gz(selection/'warm_point.json.gz'))
                assert warm['qualified']==call['warm_check']['qualified']
                assert abs(warm['constraints']-call['warm_check']['constraints'])<1e-12
                assert call['Seed']==0 and call['Threads']==1 and call['Method']==0 and call['LPWarmStart']==1
                if call.get('iteration_rule')=='selector_variable_count_plus_2000':
                    assert call['IterationLimit']==dual.NumVars+2000
                candidate=None;point_check=None;ceiling=None
                if returned['SolCount']:
                    point=load_gz(selection/'point.json.gz');assert set(point)==set(native_vars)
                    point_check=primal_record(dual,point)
                    assert point_check['qualified']==returned['primal']['qualified']
                    if (selection/'candidate_multipliers.json.gz').exists():
                        candidate=load_gz(selection/'candidate_multipliers.json.gz')
                        assert candidate=={name:point[var] for name,var in mapping.items()}
                        cert=load_gz(selection/'candidate_certificate.json.gz')
                        cq=independent_residual(q_matrix,bounds,cert,scope)
                        beta=max(F(0),F(candidate['hull_gini']));alpha=F(candidate['hull_convexity'])
                        costs={(s['i'],y):-F(candidate.get(f'hull_link_{s["i"]}_{y}',0.)) for s in scope['stations'] for y in s['support']}
                        for Y in pool:
                            if Y not in fvalues:
                                value=stock_value(scope,Y);assert value['feasible'];fvalues[Y]=value['f']
                        minimum=min(beta*fvalues[Y]+sum((costs[s['i'],y] for s,y in zip(scope['stations'],Y)),F(0)) for Y in pool)
                        aK=min(alpha,minimum);ceiling=cq+aK
                        assert str(aK)==cert['a_true_RMP_exact'] and str(minimum)==cert['true_column_min_exact']
                        assert str(ceiling)==returned['qualified_ceiling_exact']
                        assert returned['ceiling_meets_level']==(ceiling>=zeta)
                        if 'nominal_level_omitted_coefficients_exact' in call:
                            correction=sum((F(value)*F(point[name]) for name,value in call['nominal_level_omitted_coefficients_exact'].items()),F(0))
                            assert str(correction)==returned['nominal_level_omitted_contribution_exact']
                accepted=(candidate is not None and point_check['qualified'] and returned['Status'] in (2,7,9) and ceiling>=zeta)
                assert returned['selected']==accepted
                assert returned['nonoptimal_feasible_accepted']==(accepted and returned['Status']!=2)
                facts.append(dict(iteration=iteration,Status=returned['Status'],SolCount=returned['SolCount'],
                    accepted=accepted,complete_candidate_primal=point_check,complete_current_column_minimum=candidate is not None,
                    corrected_ceiling_exact=str(ceiling) if ceiling is not None else None,level_exact=str(zeta)))
                if not accepted:
                    assert not (step/'direction.json').exists() and not (step/'pricing/result.json').exists();continue
                selected_count+=1;nonoptimal+=returned['Status']!=2
                d=read(step/'direction.json');p=qualified_price(step/'pricing/result.json');rec=read(step/'result.json')
                assert F(d['zeta_exact'])==zeta and F(d['C_Q_exact'])==cq and F(d['a_K_exact'])==aK
                assert d['selection_result_SHA']==sha(selection/'result.json') and d['columns_before']==len(pool)
                tau=zeta-cq;assert F(d['tau_exact'])==tau and tau<=aK
                lm=F(p['lower']);lower=max(lower,outward(cq+min(aK,lm),False))
                true_upper=min([minimum]+[F(v['price_exact']) for v in p['stocks']])
                assert rec['target_proved']==(lm>=tau) and rec['target_disproved']==(true_upper<tau)
                assert (rec['lower'],rec['upper'])==(lower,upper)
                feedback=load_gz(step/'column_feedback.json.gz')
                for row in feedback:
                    Y=tuple(row['stock']['Y']);assert row['new']==(Y not in pool)
                    if row['new']:add_inventory(Y)
                    else:assert F(row['stock']['price_exact'])>=tau
                m.update();dual.update()
                if lm>=tau:
                    exits.append((str(zeta),'qualified_whole_price_lower',iteration,lower,upper));zeta=(F(lower)+F(upper))/2
            final=folder/'final_RMP/result.json'
            if final.exists():assert accept_upper(read(final),len(result['records']))
            assert (lower,upper)==(result['lower'],result['upper'])
            assert list(pool)==[tuple(Y) for Y in result['columns']]
            assert str(zeta)==result['unresolved_level_exact']
            claimed=[(v['zeta_exact'],v['exit'],v['iteration'],v['lower'],v['upper']) for v in result['resolved_levels']]
            assert exits==claimed
            with gp.read(str(folder/'last_selection.mps'),env=env) as actual:
                assert semantics(actual)==semantics(dual)
                matrices.append(dict(final=True,**matrix_check(master,actual,dual.getConstrByName('nominal_fixed_level').RHS)))
            with gp.read(str(folder/'last_master.mps'),env=env) as actual:
                assert semantics(actual)==semantics(m)
    write(target/'result.json',dict(PASS=True,phase=phase,result_SHA=sha(path),
        qualified_result=str(qualified_result),qualified_result_SHA=sha(qualified_result),loop_readback_SHA=sha(audit_path),
        candidates=facts,matrices=matrices,selected_count=selected_count,nonoptimal_feasible_accepted=nonoptimal,
        resolved_levels=exits,unresolved_level_exact=str(zeta),lower=lower,upper=upper,Optimize=0,
        all_accepted_candidate_CQ_and_current_column_minima_replayed=True,
        selection_objective_or_status_never_used_as_hull_bound=True,source_SHA=sha(__file__),nonimplementer_agent_review=False))
    print(json.dumps(dict(PASS=True,phase=phase,selected_count=selected_count,resolved_levels=len(exits),Optimize=0)),flush=True)


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
