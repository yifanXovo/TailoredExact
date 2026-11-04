"""Rebuild compact tables from closed evidence; never launch a producer."""
import csv
from fractions import Fraction as F
from round143_math import outward
from round153_common import *

def table(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader()
        writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()} for row in rows)

def trajectory(folder,arm):
    """Descriptive controller trace; only the sealed endpoint is qualified."""
    audit=read(folder/'audit.json');cover=audit.get('qualified_cover')
    rows=cover.get('timeline',[]) if cover else []
    times=[float(r['process_elapsed_seconds']) for r in rows]
    assert all(math.isfinite(t) and t>=0 for t in times) and times==sorted(times)
    assert math.isfinite(arm['T_produce']) and arm['T_produce']>=0
    end=max((float(r['process_elapsed_seconds']) for r in rows),default=0.)
    assert end<=arm['T_produce']
    # Charge all observed wrapper/preprocess/postprocess overhead to the
    # displayed controller timestamps. The inherited audit does not bind
    # every CSV row to its then-available proof/witness, so this shift does
    # not qualify intermediate bound attainments or their event times.
    offset=max(0.,arm['T_produce']-end);out=[]
    for r in rows:
        out.append(dict(process_seconds=float(r['process_elapsed_seconds']),
            shifted_recorded_producer_seconds=float(r['process_elapsed_seconds'])+offset,
            U=float(r['verified_global_upper_bound']),L=float(r['recomputed_complete_cover_bound']),
            source='controller_trace_from_completed_audited_run',event=r['event_type'],
            qualification='recorded_controller_only'))
    out.append(dict(process_seconds=None,shifted_recorded_producer_seconds=arm['T_produce'],
        U=arm['U'],L=arm['L'],source='sealed_qualified_endpoint',event='complete_producer_endpoint',
        qualification='qualified_endpoint'))
    for row in out:row['gap']=row['U']-row['L']
    return dict(arm_id=arm['arm_id'],role=arm['id'],method=arm['R153_method'],rows=out,
        whole_producer_overhead_shift=offset,exact_first_witness_time_claimed=False,
        intermediate_values_and_event_times_not_individually_qualified=True,
        trace_does_not_replace_T_cert=True,T_verify_separate=arm['T_verify'],audit_SHA=sha(folder/'audit.json'))

def complete():
    configure();matrix=read(OUT/'confirmation_matrix.json');arms=[];missing=[];traces={};targets=[]
    for group in matrix['groups']:
        launch=group['launch'];d=Path(launch['destination']);path=d/'round135_endpoint.json'
        if not path.exists():missing.append(group['position']);continue
        close=read(d/'verification_closeout.json');arm=read(path)
        identity_path=OUT/group['group']/'identity.json';identity=read(identity_path)
        assert sha(identity_path)==group['identity_SHA'] and arm['PE_SHA']==identity['candidate_binary_sha256']
        assert arm['source_commit']==identity['measured_source_commit']
        assert close['implementation_qualified'] and close['evidence_complete'] and close['performance_eligible']
        assert arm['arm_id']==launch['arm_id'] and arm['input_SHA']==launch['panel']['input_sha256']
        assert arm['audit_SHA']==close['audit_SHA']==sha(d/'audit.json')
        assert arm['verification_closeout_SHA']==sha(d/'verification_closeout.json')
        assert arm['arm_total_receipt_SHA']==sha(d/'arm_total_receipt.json')
        floor=read(d/'round153_control_audit.json');root=floor['root']
        helper_path=d/'external/round153_floor/result.json'
        helper=read(helper_path) if helper_path.exists() else None
        arm.update(R153_method=launch['R153_method'],actual_cap=launch['cap_seconds'],
            endpoint_source_commit=arm['source_commit'],
            candidate_measured_source_commit=identity['measured_source_commit'],delivery_base_commit=identity['delivery_base_commit'],
            source_commit_semantics='complete endpoint source_commit equals candidate_measured_source_commit; delivery_base_commit is separately identified',
            helper_seconds=root['helper_process_seconds'] if root else 0.,
            own_floor=root['lower'] if root and root['qualified'] else None,
            helper_global_stop=root['global_deadline_stop'] if root else False,
            floor_models=len(floor['models']),floor_native_audits=len(floor['Native_audits']),
            formal_Native_calls=arm['native_Optimize'],helper_Native_calls=helper['new_Native_calls'] if helper else 0,
            helper_call_without_completed_result=(d/'external/round153_floor/pricing/call.json').exists() and helper is None,
            helper_runtime_already_in_T_produce=True)
        if not arm['certificate']:assert arm.get('T_cert') is None
        traces[arm['arm_id']]=trajectory(d,arm)
        arms.append(arm)
    pairs=[]
    for role in matrix['roles']:
        by={a['R153_method']:a for a in arms if a['id']==role}
        if set(by)!={'B','J'}:continue
        b,j=by['B'],by['J'];assert b['input_SHA']==j['input_SHA'] and b['PE_SHA']==j['PE_SHA'] and b['seed']==j['seed']==0
        pairs.append(dict(role=role,cap=b['actual_cap'],B_U=b['U'],J_U=j['U'],J_minus_B_U=j['U']-b['U'],
            B_L=b['L'],J_L=j['L'],J_minus_B_L=j['L']-b['L'],B_gap=b['U']-b['L'],J_gap=j['U']-j['L'],
            B_certificate=b['certificate'],J_certificate=j['certificate'],B_T_cert=b.get('T_cert'),J_T_cert=j.get('T_cert'),
            B_T_produce=b['T_produce'],J_T_produce=j['T_produce'],B_T_verify=b['T_verify'],J_T_verify=j['T_verify'],
            B_T_total=b['T_total'],J_T_total=j['T_total'],J_helper_seconds=j['helper_seconds'],
            own_floor=j['own_floor'],B_arm=b['arm_id'],J_arm=j['arm_id'],both_own_H=b['H_complete'] and j['H_complete'],
            same_own_H_semantic_trace=b['H_semantic_SHA']==j['H_semantic_SHA'],
            same_own_H_canonical_fleet=b['H_fleet_SHA']==j['H_fleet_SHA'],
            equal_H_hash_does_not_mean_shared_or_free_H=True))
        for metric,values in [('U',[b['U'],j['U']]),('L',[b['L'],j['L']]),('gap',[b['U']-b['L'],j['U']-j['L']])]:
            for value in sorted(set(values)):
                row=dict(role=role,metric=metric,target=value,target_selection='descriptive_common_final_endpoint_levels')
                for method,a in [('B',b),('J',j)]:
                    hits=[r['shifted_recorded_producer_seconds'] for r in traces[a['arm_id']]['rows']
                          if (r[metric]>=value if metric=='L' else r[metric]<=value)]
                    row[method+'_observed_shifted_trace_time']=min(hits) if hits else None
                    row[method+'_not_reached_in_observed_trace']=not bool(hits)
                    actual=a['U']-a['L'] if metric=='gap' else a[metric]
                    endpoint_hit=actual>=value if metric=='L' else actual<=value
                    row[method+'_qualified_endpoint_producer_time']=a['T_produce'] if endpoint_hit else None
                targets.append(row)
    write(OUT/'reports/complete_arms.json',dict(arms=arms,missing_positions=missing,matrix_SHA=sha(OUT/'confirmation_matrix.json')))
    write(OUT/'reports/complete_pairs.json',dict(pairs=pairs,open_certificate_time_imputed=False,performance_source='sealed round135 endpoints under inherited R134 policy'))
    write(OUT/'reports/complete_trajectories.json',dict(arms=list(traces.values()),
        common_targets=targets,posthoc_descriptive_not_additional_confirmatory_tests=True,
        clock='recorded controller event plus observed producer overhead; intermediate values/times are descriptive only',
        T_cert_and_T_verify_and_T_total_reported_separately=True))
    if arms:table(OUT/'reports/complete_arms.csv',arms)
    if pairs:table(OUT/'reports/complete_pairs.csv',pairs)
    if targets:table(OUT/'reports/common_targets.csv',targets)
    print(json.dumps(dict(closed_arms=len(arms),pairs=len(pairs),missing=missing)),flush=True)

def science():
    configure();decision=read(OUT/'candidate_decision.json');rows=[]
    for role,spec in decision['science_evidence'].items():
        ref=OUT/'reference'/role;domain=read(ref/'domain.json')
        direct=read(ref/'direct/result.json');union=read(ref/'union/result.json');joint=read(ref/'old_joint/result.json')
        coupled=read(ROOT/spec['coupled_result']);support=read(ROOT/spec['support_result'])
        projection=read(OUT/'projection'/role/'result.json')
        assert coupled['scope']==domain['scope'] and coupled['Q_SHA']==sha(ref/'direct/model.mps')
        assert support['Q_SHA']==coupled['Q_SHA'] and projection['full_oracle_projection_feasible']
        all_support=support['records'][-1]
        row=dict(role=role,B_L=domain['B_L'],old_strong_RN=joint['previous_numerical_value'],
            old_joint_L=joint['L'],old_joint_U=joint['U'],union_L=union['L'],union_U=union['U'],
            direct_L=direct['L'],direct_U=direct['U'],coupled_L=coupled['lower'],coupled_U=coupled['upper'],
            interval_width=coupled['upper']-coupled['lower'],gain_over_direct_L=coupled['lower']-direct['U'],
            remaining_above_support= coupled['upper']-all_support['L'],columns=len(coupled['columns']),
            support_rows=support['rows'],projection_rows=support['projection_rows'],support_L=all_support['L'],support_U=all_support['U'],
            current_Q_projection_compatible=True,primal_upper_is_not_physical=True,original_variables_free=True,
            outcome=spec['outcome'],coupled_result=spec['coupled_result'],support_result=spec['support_result'])
        rows.append(row)
    write(OUT/'reports/scientific_table.json',dict(rows=rows,numerical_upper_policy='inherited feasibility policy, not rational primal certificates',
        lower_policy='exact Q binary64 residual support plus guarded complete-domain Native pricing'))
    table(OUT/'reports/scientific_table.csv',rows)
    print(json.dumps(rows,indent=2),flush=True)

def phase_receipts():
    """Bind direct outer receipts without rewriting a partial raw decision."""
    result={}
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(p);command=launch['command'];script=None;args=[]
        for k,value in enumerate(command):
            if Path(value).name.startswith('round153_') and str(value).endswith('.py'):
                script=Path(value).name;args=command[k+1:];break
        wrapper=None
        if script=='round153_exact_worker.py' and len(args)>=4 and args[0]=='execute':
            wrapper=script;assert args[1]==p.parent.name
            script=args[2];args=args[4:]
        phase=None
        if script in ('round153_coupled.py','round153_refine.py','round153_overlay.py','round153_refresh.py') and len(args)>=2:
            phase=args[0]+'_'+args[1]
        elif script=='round153_primal_pool.py' and len(args)>=3 and args[0]=='run':
            phase=args[1]+'_'+args[2]
        elif script=='round153_attribution.py' and len(args)>=4 and args[0] in ('floor_close','support_close'):
            phase=args[1]+'_'+args[-1]
        if not phase:continue
        rp=p.parent/'receipt.json';r=read(rp) if rp.exists() else None
        result.setdefault(phase,[]).append(dict(label=p.parent.name,receipt_SHA=sha(rp) if r else None,
            process_runtime_wrapper=wrapper,
            exit_code=r.get('exit_code') if r else None,exit_observed=r.get('exit_observed') if r else False,
            G1_seconds=r.get('G1_seconds') if r else None,timeout=r.get('timeout') if r else None,
            supervisor_failure=r.get('supervisor_failure') if r else None))
    return result


def research():
    configure();iterations=[];phases=[];prices=[];paths=set();primal_sweeps=[]
    receipts=phase_receipts()
    for folder in sorted((OUT/'coupled').iterdir()):
        if not folder.is_dir() or not (folder/'result.json').exists():continue
        data=read(folder/'result.json');plan=read(folder/'plan.json') if (folder/'plan.json').exists() else {}
        fees=receipts.get(folder.name,[]);calls=list(folder.rglob('call.json'))
        closed=bool(fees) and all(r['receipt_SHA'] and r['exit_observed'] for r in fees)
        nonzero=any(r['exit_code']!=0 or r['timeout'] or r['supervisor_failure'] for r in fees)
        phases.append(dict(role=data['role'],phase=folder.name,decision=data['decision'],lower=data['lower'],
            upper=data['upper'],width=data['gap'],columns=len(data['columns']),support_rows=len(data['supports']),
            completed_local_records=sum((folder/f'iter{r["iteration"]:05}'/'result.json').exists() for r in data.get('records',[])),
            requested_accuracy=plan.get('absolute_target'),price_cap=plan.get('price_cap'),
            stabilization_mode=plan.get('stabilization_mode'),new_RMP_solve=data.get('new_RMP_solve',True),
            primal_discovery_only=data.get('primal_discovery_only',False),
            primal_refresh_only=data.get('primal_refresh_only',False),
            refreshed_RMP_objective=data.get('refresh',{}).get('RMP_objective'),
            refreshed_RMP_primal_qualified=bool(data.get('refresh',{}).get('primal',{}).get('qualified'))
                if data.get('refresh',{}).get('primal') is not None else None,
            completed_primal_sweeps=len(data.get('primal_sweeps',[])),
            direct_outer_fees=fees,direct_outer_G1_seconds=sum(r['G1_seconds'] or 0. for r in fees) if closed else None,
            outer_state=('CLOSED_RETAINED_PARTIAL_NONZERO_EXIT' if nonzero else 'CLOSED') if closed else
                'NO_DIRECT_OUTER_MATCH' if not fees else 'OUTER_NOT_CLOSED',
            raw_decision_preserved=True,phase_directory_Optimize_call_artifacts=len(calls),
            phase_directory_calls_without_saved_return=sum(not (p.parent/'return.json').exists() for p in calls),
            call_artifact_count_scope='This coupled phase directory only; separately stored support_LP, qualification and inherited artifacts excluded. Not a total Native-call census.',
            stored_seconds=data['seconds'],stored_seconds_may_be_nested_or_inherited=True,
            result=(folder/'result.json').relative_to(ROOT).as_posix()))
        for p in sorted(folder.glob('sweep*/result.json')):
            r=read(p);discovery=read(p.parent/'discovery.json');native=read(p.parent/'return.json')
            primal_sweeps.append(dict(role=data['role'],phase=folder.name,path=p.relative_to(ROOT).as_posix(),
                **{k:r[k] for k in ('sweep','RMP_objective','lower','upper','gap','columns_before','columns','added','elapsed_seconds')},
                primal_qualified=r['primal']['qualified'],Native_runtime=native['Runtime'],Native_Work=native['Work'],
                neighbors_scored=discovery.get('neighbors_scored',0),
                exact_feasible_candidates=discovery.get('exact_feasible_candidates',0),
                pair_crossovers_scored=discovery.get('paired_exchange',{}).get('crossovers_scored',0),
                complementary_pairs=len(discovery.get('paired_exchange',{}).get('pairs',[])),
                candidate_ranking_not_bound=True,lower_inherited=True,full_price_convergence_claimed=False))
        for p in sorted(folder.glob('iter*/result.json')):
            r=read(p)
            if 'iteration' not in r:continue
            row=dict(role=data['role'],phase=folder.name,path=p.relative_to(ROOT).as_posix())
            for key in ('iteration','phase_I','RMP_objective','beta','a','D_K','correction','pricing_lower','pricing_upper',
                        'reduced_cost_upper','lower','upper','gap','columns','columns_before','added','added_negative',
                        'all_true_legal_pool_columns','pricing_seconds','elapsed_seconds','selection_mode','dual_band'):
                row[key]=r.get(key)
            row['RMP_primal_qualified']=r['primal']['qualified'] if r.get('primal') else False
            cp=p.parent/'certificate.json.gz'
            if cp.exists():
                c=load_gz(cp);row['C_Q']=float(F(c['lower_exact']))
                row['RMP_minus_qualified_D_K']=r['RMP_objective']-c['D_K']
                if r['pricing_upper'] is not None:
                    ceiling=F(c['lower_exact'])+min(F(c['a_true_RMP_exact']),F(r['pricing_upper']))
                    row['fixed_direction_ceiling_from_true_price_upper']=outward(ceiling,True)
                    row['fixed_direction_ceiling_exact']=str(ceiling)
                row['dual_band_and_residual_effects_not_automatically_numerical_error']=True
            iterations.append(row);paths.add(p.parent/'pricing/result.json')
        if (folder/'pricing/result.json').exists():paths.add(folder/'pricing/result.json')
    paths.update((OUT/'floor').glob('*/pricing/result.json'))
    for p in sorted(paths):
        v=read(p);assert v['complete_domain']
        prices.append(dict(path=p.relative_to(ROOT).as_posix(),lower=v['lower'],upper=v['upper'],
            width=v['upper']-v['lower'] if v['upper'] is not None else None,beta=v['beta'],
            zero_projection_price=v['beta']==0.,true_legal_stock_uppers=len(v['stocks']),
            new_Native_calls=len(v['calls']),Native_runtime=sum(c['Runtime'] for c in v['calls']),
            price_Native_Work=sum(c.get('Work',0.) for c in v['calls']),
            price_Native_nodes=sum(c.get('nodes',0.) for c in v['calls']),
            candidate_selection_Native_calls=len(v.get('candidate_LP_calls',[])),
            Native_calls_total=len(v['calls'])+len(v.get('candidate_LP_calls',[])),
            candidate_selection_Native_runtime=sum(c['Runtime'] for c in v.get('candidate_LP_calls',[])),
            candidate_selection_Native_Work=sum(c.get('Work',0.) for c in v.get('candidate_LP_calls',[])),
            exact_integer_flow_calls=v.get('exact_integer_flow_calls',0),graphcut_full_price=v.get('graphcut_full_price',False),
            nested_price_seconds=v['seconds'],partitioned=v.get('partitioned_full_price',False),
            overlay_reuses_paid_bounds=v.get('overlay_full_price',False),
            pricing_extension=v.get('pricing_extension',{}).get('name'),
            extension_columns=v.get('pricing_extension',{}).get('extra_columns',0),
            extension_rows=v.get('pricing_extension',{}).get('extra_rows',0),
            decision=v['decision'],reason=v['reason'],numerical_policy=(
                'exact integer flow plus exact DP and true-stock upper; candidate LP is not a bound' if v.get('graphcut_full_price') else
                'declared guard plus exact DP and true-stock upper')))
    write(OUT/'reports/research_progress.json',dict(phases=phases,iterations=iterations,
        primal_sweeps=primal_sweeps,
        each_completed_iteration_listed_once=True,checkpoint_is_not_study_endpoint=True,
        nested_seconds_not_added_to_outer_fees=True))
    write(OUT/'reports/pricing_results.json',dict(prices=prices,qualification_not_performance=True,
        no_historical_pricing_recharged=True,nested_seconds_not_added_to_outer_fees=True))
    table(OUT/'reports/research_phases.csv',phases);table(OUT/'reports/coupled_iterations.csv',iterations)
    table(OUT/'reports/pricing_results.csv',prices)
    if primal_sweeps:table(OUT/'reports/primal_discovery.csv',primal_sweeps)
    print(json.dumps(dict(phases=len(phases),iterations=len(iterations),full_domain_prices=len(prices))),flush=True)

def costs():
    configure();current=budget();assert not current['unclosed'],current['unclosed']
    fees=[]
    for path in sorted((OUT/'fees').glob('*/receipt.json')):
        launch=read(path.parent/'launch.json');r=read(path)
        fees.append(dict(label=path.parent.name,kind=launch['kind'],**r,receipt_SHA=sha(path)))
    write(OUT/'cost_report.json',dict(UTC=utc(),experimental_capacity_seconds=115200.,**current,fees=fees,
        accounting='each new metered outer once; nested H/LP/MIP Runtime and Work not added',
        compilation_separate=True,old_paid_cost_not_recharged=True,pure_writing_and_public_IO_separate=True,
        measurement_gaps=['Pre-launch source snapshot and frozen-identity admission hashing, budget/bookkeeping reads and receipt formatting outside the outer timer are not separately timed. These small setup/identity checks are disclosed, not estimated or repaired by rerunning producers.'],
        failed_and_interrupted_runs_included=True,missing_outer_receipts=[]))
    table(OUT/'reports/costs.csv',fees)
    print(json.dumps(current),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
