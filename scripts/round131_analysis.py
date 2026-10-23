"""One post-formal reconstruction of the fixed three layers; no Optimize."""
from round131_benchmark import *
import csv, math, statistics
from round127_analysis import qualified
from round129_qualify import support_family
from round130_analysis import phase_value
from compare_round112_startup import reconstruct as H
import round108_reader as core

def table(path,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def comparison(g,s,p):
    q=dict(group=g['number'],layer=g['layer'],id=g['role']['id'],seed=g['seed'],repeat=g['repeat'],left='S2',right='P',
        classification='UNEVALUABLE',direction='UNEVALUABLE',S2_certified=bool(s['certificate']),P_certified=bool(p['certificate']),
        S2_T_cert=s['T_cert'],P_T_cert=p['T_cert'],S2_T_produce=s['T_produce'],P_T_produce=p['T_produce'],
        S2_T_verify=s['T_verify'],P_T_verify=p['T_verify'],S2_T_total=s['T_total'],P_T_total=p['T_total'],
        S2_minus_P_seconds=None,P_over_S2_certification_ratio=None,absolute_seconds_difference=None,
        materiality=None,tiny_10_second_warning=False,P_only_risk=False,objective_conflict=False,
        S2_U=s['U'],S2_L=s['L'],P_U=p['U'],P_L=p['L'])
    if not qualified(s) or not qualified(p):return q
    assert s['input_SHA']==p['input_SHA'] and s['PE_SHA']==p['PE_SHA']==PE_SHA and s['DLL_SHA']==p['DLL_SHA']==DLL_SHA
    if s['certificate'] and p['certificate']:
        if abs(s['U']-p['U'])>1e-7:return dict(q,objective_conflict=True)
        dt=s['T_cert']-p['T_cert'];fast=min(s['T_cert'],p['T_cert'])
        q.update(classification='BOTH_CERTIFIED',direction='Win' if dt<0 else 'Lose' if dt>0 else 'Tie',
            S2_minus_P_seconds=dt,P_over_S2_certification_ratio=p['T_cert']/s['T_cert'],absolute_seconds_difference=abs(dt),
            materiality=('S2_MATERIALLY_FASTER' if dt<0 else 'P_MATERIALLY_FASTER') if abs(dt)>=max(10,.1*fast) else 'TIME_CLOSE',
            tiny_10_second_warning=g['layer']=='B' and dt>=10)
    elif s['certificate']:q.update(classification='S2_ONLY_CERTIFIED',direction='Win',materiality='S2_ONLY_CERTIFIED')
    elif p['certificate']:q.update(classification='P_ONLY_CERTIFIED',direction='Lose',materiality='P_ONLY_CERTIFIED',P_only_risk=True)
    else:q.update(classification='BOTH_OPEN',direction='UNDETERMINED')
    return q

def stats(arms,pairs):
    both=[q for q in pairs if q['classification']=='BOTH_CERTIFIED']
    ratios=[q['P_over_S2_certification_ratio'] for q in both]
    return dict(arms=len(arms),matched_groups=len(pairs),distinct_inputs=len({a['input_SHA'] for a in arms}),
        classes=dict(collections.Counter(q['classification'] for q in pairs)),directions=dict(collections.Counter(q['direction'] for q in pairs)),
        certification_counts={m:sum(qualified(a) and a['certificate'] for a in arms if a['method']==m) for m in ['P','S2']},
        nonzero_certification_counts={m:sum(qualified(a) and a['certificate'] and a['U']>1e-7 for a in arms if a['method']==m) for m in ['P','S2']},
        zero_certification_counts={m:sum(qualified(a) and a['certificate'] and a['own_exact_zero'] for a in arms if a['method']==m) for m in ['P','S2']},
        no_backend_exposure={m:sum(a['native_Optimize']==0 for a in arms if a['method']==m) for m in ['P','S2']},
        both_certified_intersection_n=len(both),both_certified_intersection=[{k:q[k] for k in ['group','id','seed','repeat']} for q in both],
        conditional_geometric_mean_P_over_S2=math.exp(statistics.fmean(map(math.log,ratios))) if ratios else None,
        total_production_seconds_including_open={m:sum(a['T_produce'] for a in arms if a['method']==m) for m in ['P','S2']},
        total_production_is_not_total_certification_time=True,open_T_cert_imputed=False,
        scope='conditional ratios describe only the listed both-certified intersection, not the whole panel; no independence or significance claim')

def interval(values):
    return dict(n=len(values),median=statistics.median(values) if values else None,minimum=min(values) if values else None,maximum=max(values) if values else None)

def tiny(arms,pairs):
    result=[]
    for id in ['SM-C8-S','SM-B10-B']:
        qq=[q for q in pairs if q['id']==id];aa=[a for a in arms if a['id']==id]
        assert len(qq)==6 and len(aa)==12
        seeds=[]
        for seed in [0,1,2]:
            pp=[q for q in qq if q['seed']==seed];assert [q['repeat'] for q in pp]==[1,2]
            ds=[q['S2_minus_P_seconds'] for q in pp if q['S2_minus_P_seconds'] is not None]
            seeds.append(dict(seed=seed,observations=pp,valid_both_certified_repeats=len(ds),
                S2_minus_P_seconds=interval(ds) if len(ds)==2 else None,
                fluctuation_estimated_from_fewer_than_two=False,
                repeatable_10_second_warning=len(ds)==2 and all(x>=10 for x in ds),
                P_only_certification_risk=any(q['P_only_risk'] for q in pp)))
        result.append(dict(id=id,all_six=qq,by_seed=seeds,
            S2_minus_P_seconds=interval([q['S2_minus_P_seconds'] for q in qq if q['S2_minus_P_seconds'] is not None]),
            certification_seconds={m:interval([a['T_cert'] for a in aa if a['method']==m and a['T_cert'] is not None]) for m in ['P','S2']},
            production_seconds_all_six={m:interval([a['T_produce'] for a in aa if a['method']==m]) for m in ['P','S2']},
            warnings_10_seconds=sum(q['tiny_10_second_warning'] for q in qq),P_only_risks=sum(q['P_only_risk'] for q in qq),
            at_least_two_10_second_warnings_among_six=sum(q['tiny_10_second_warning'] for q in qq)>=2,
            practical_threshold_is_not_a_noise_theorem=True,
            representativeness='known legal empty-fleet/structurally easy role, not all tiny difficulty' if id=='SM-B10-B' else 'one known tiny shortage role'))
    return result

def run():
    manifest=read(OUT/'experiment_manifest.json');arms=[];pairs=[];costs=[];model_index=[];call_index=[];physical=[];issues=[]
    for g in manifest['groups']:
        camp=OUT/g['name'];i=read(camp/'identity.json');aa=read(camp/'reconstructed.json')['arms']
        assert [a['method'] for a in aa]==g['methods'] and len(aa)==2
        for a,l in zip(aa,i['launches']):
            d=Path(l['destination']);p=l['panel'];r=read(d/'result.json');events=read(d/'observations.json')
            assert a['T_cert']==(a['T_produce'] if a['certificate'] and qualified(a) else None)
            assert a['PE_SHA']==PE_SHA and a['DLL_SHA']==DLL_SHA and a['input_SHA']==p['input_sha256']
            assert a['seed']==g['seed'] and a['repeat']==g['repeat']
            if a.get('source_reduced'):issues.append(dict(type='SAME_SCOPE_SOURCE_REVOKED',group=g['number'],method=a['method'],rejected_calls=a.get('rejected_calls')))
            a.update(group=g['number'],layer=g['layer'],source=p['source'],inventory=p['inventory'],geometry=p['geometry'],
                signed_gap=a['U']-a['L'],absolute_gap=abs(a['U']-a['L']),
                actual_observation_end_seconds=a['T_produce'],right_censored=not a['certificate'] if qualified(a) else None,
                censoring_scope='qualified own complete production observation end, never nominal cap or extrapolated final certification' if qualified(a) else 'UNEVALUABLE evidence gap; not ordinary algorithmic censoring',
                run_identity=sha(d/'launch.json')+':'+sha(d/'producer_receipt.json'))
            arms.append(a)
            h=H(ROOT,p,d) if a['method']=='S2' else None
            ledger=core.rows(d/'external/paper_optimize_ledger.csv') if (d/'external/paper_optimize_ledger.csv').exists() else []
            phases=core.rows(d/'phases.csv');h_start=phase_value(phases,'hga_start','start');h_end=phase_value(phases,'decoded_descent_complete','complete')
            starts=[read(s) for s in (d/'external/native_logs').glob('*.round68.start.json')]
            subclocks=[s.get('mapping_validation_submission_seconds') for s in starts]
            seen={};root_model=None;root_call=None
            for event in events:
                c=event['payload']
                if c['kind']!='call':continue
                call_index.append(dict(group=g['number'],layer=g['layer'],id=p['id'],seed=g['seed'],repeat=g['repeat'],method=a['method'],**c))
                if c['model_sha256'] in seen:continue
                path=core.portable(ROOT,c['model_path']);assert sha(path)==c['model_sha256']
                m=core.lp_model(path);families=collections.Counter(support_family(row) for row in m['rows'])
                supply_terms=[sum(n.startswith('p_') for n,v in terms) for terms,sense,rhs in m['rows'] if support_family((terms,sense,rhs))=='ordered_supply']
                if a['method']=='S2' and families['cover_3']+families['conditional_3']!=0:issues.append(dict(type='UNEXPECTED_TRIPLE',group=g['number'],model_SHA=c['model_sha256']))
                sentinel=sum(not t and s=='<=' and rhs==-1 for t,s,rhs in m['rows'])
                penalties=[rhs for terms,sense,rhs in m['rows'] if sense=='>=' and len(terms)==p['V'] and all(n.startswith('e_') for n,v in terms)]
                analytic=c['lower_g']+.15*max(penalties) if penalties and not c['full_original'] else None
                fact=dict(group=g['number'],layer=g['layer'],id=p['id'],seed=g['seed'],repeat=g['repeat'],method=a['method'],
                    model_SHA=c['model_sha256'],path=str(path),leaf=c['leaf'],rows=len(m['rows']),columns=len(m['order']),
                    pair_cover=families['cover_2'],pair_conditional=families['conditional_2'],triple_cover=families['cover_3'],triple_conditional=families['conditional_3'],
                    ordered_supply_compatible_rows=families['ordered_supply'],
                    ordered_supply_compatible_pickup_terms=sum(supply_terms),
                    ordered_supply_pickup_terms_per_row_min=min(supply_terms) if supply_terms else None,
                    ordered_supply_pickup_terms_per_row_max=max(supply_terms) if supply_terms else None,
                    support_pair_candidate_upper=p['M']*math.comb(p['V'],2) if a['method']=='S2' else None,
                    support_triple_enumeration_enabled=False if a['method']=='S2' else None,shared_candidate_cap=50000,
                    actual_candidate_counter=None,
                    candidate_upper_scope='fixed pair-only enumeration upper bound from source, not a retained actual counter or violation count',
                    sentinel_rows=sentinel,scope=[c['lower_g'],c['upper_g']],cutoff=c.get('cutoff'),analytic_region_lower=analytic,
                    interpretation='semantic improving-domain closure, not inclusive physical infeasibility' if sentinel else 'ordinary submitted model',
                    corrected_same_vehicle_classifier=True)
                model_index.append(fact);seen[c['model_sha256']]=fact
                if root_model is None and (c['full_original'] or c['leaf']=='L0'):root_model=fact;root_call=c
            # For zero-startup arms, missing models/diagnostics remain unknown.
            families=root_model or {}
            cost=dict(group=g['number'],layer=g['layer'],id=p['id'],seed=g['seed'],repeat=g['repeat'],method=a['method'],
                H_complete=h['complete'] if h else None,initial_own_U=h['physical']['F'] if h else None,
                H_logged_descent_seconds=h_end-h_start if h_start is not None and h_end is not None else None,
                admission_and_H_until_backend_seconds=phase_value(phases,'exact_phase_start','start') if h else None,
                actual_native_calls=a['native_Optimize'],actual_solve_kinds=dict(collections.Counter(x['solve_kind'] for x in ledger)) if ledger else ({'complete_original_compact_milp':a['native_Optimize']} if a['method']=='P' else {}),
                LP_native_seconds=sum(float(x['solver_runtime']) for x in ledger if x['solve_kind']=='LP') if ledger else None,
                MIP_native_seconds=sum(float(x['solver_runtime']) for x in ledger if x['solve_kind']!='LP') if ledger else r.get('gurobi_runtime') if a['native_Optimize'] else None,
                LP_native_work=sum(float(x['work']) for x in ledger if x['solve_kind']=='LP') if ledger else None,
                MIP_native_work=sum(float(x['work']) for x in ledger if x['solve_kind']!='LP') if ledger else r.get('gurobi_work') if a['native_Optimize'] else None,
                native_nodes=sum(float(x['nodes']) for x in ledger) if ledger else r.get('gurobi_node_count') if a['native_Optimize'] else None,
                model_generation_seconds=r.get('external_gini_tree_model_build_seconds') if ledger else r.get('gurobi_model_build_seconds'),
                native_model_read_seconds=r.get('external_gini_tree_model_read_seconds') if ledger else r.get('gurobi_model_read_seconds'),
                Start_check_submission_seconds=sum(subclocks) if subclocks and all(x is not None for x in subclocks) else None,
                actual_submitted_Starts=sum(bool(x['submitted']) for x in starts) if starts else 0 if a['method']=='P' else None,
                split_count=r.get('external_gini_tree_split_count'),partial_target_calls=r.get('external_gini_tree_partial_mip_optimize_count'),target_reached_events=r.get('external_gini_tree_partial_mip_target_reached_count'),
                support_pair_cover_rows=families.get('pair_cover'),support_pair_conditional_rows=families.get('pair_conditional'),
                support_triple_rows=families.get('triple_cover',0)+families.get('triple_conditional',0) if root_model else None,
                raw_top_level_support_counts={key:r.get(key) for key in [
                    'compact_bc_support_duration_pair_cuts_added','compact_bc_support_duration_triple_cuts_added',
                    'compact_bc_pairwise_transfer_compatibility_cuts_added','tailored_bc_support_duration_pair_candidates',
                    'tailored_bc_support_duration_pair_cuts_added','tailored_bc_support_duration_triple_candidates',
                    'tailored_bc_support_duration_triple_cuts_added']},
                raw_support_count_scope='original top-level serialized counters, preserved as recorded; not assumed to count the complete external submitted matrix',
                ordered_supply_compatible_rows=families.get('ordered_supply_compatible_rows'),root_model_SHA=families.get('model_SHA'),
                ordered_supply_compatible_pickup_terms=families.get('ordered_supply_compatible_pickup_terms'),
                native_statuses=[x['native_status'] for x in ledger] if ledger else [r.get('gurobi_status_text')] if a['native_Optimize'] else [],
                T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total'],T_cert=a['T_cert'])
            costs.append(cost)
            physical.append(dict(group=g['number'],layer=g['layer'],id=p['id'],seed=g['seed'],repeat=g['repeat'],method=a['method'],
                run_identity=a['run_identity'],producer_seal_SHA=sha(d/'producer_seal.json'),audit_SHA=sha(d/'audit.json'),
                physical_evidence_SHA=sha(d/'independent_evidence.json'),verification_closeout_SHA=sha(d/'verification_closeout.json'),
                qualified=qualified(a),certificate=a['certificate'],certificate_basis=a['certificate_basis'],certificate_source=a.get('certificate_source'),
                own_zero=a['own_exact_zero'],backend_exposed=a['native_Optimize']>0,
                raw_claimed_certificate=a.get('raw_claimed_certificate'),raw_claimed_U=a.get('raw_claimed_U'),raw_claimed_L=a.get('raw_claimed_L')))
        by={a['method']:a for a in aa};pairs.append(comparison(g,by['S2'],by['P']))
    assert len(arms)==52 and len(pairs)==26 and len({a['input_SHA'] for a in arms})==10
    consistency=[]
    for p in read(OUT/'input_manifest.json')['roles']:
        aa=[a for a in arms if a['id']==p['id'] and qualified(a)]
        best=min((a['U'] for a in aa),default=None)
        bad=[dict(group=a['group'],method=a['method'],own_L=a['L'],other_verified_physical_U=best) for a in aa if a['L']>best+1e-7]
        consistency.append(dict(id=p['id'],input_SHA=p['input_sha256'],qualified_observations=len(aa),minimum_U_for_contradiction_only=best,violations=bad))
        issues.extend(dict(type='SAME_INPUT_BOUND_CONTRADICTION',id=p['id'],**x) for x in bad)
    issues.extend(dict(type='BOTH_CERTIFIED_OBJECTIVE_CONFLICT',group=q['group']) for q in pairs if q['objective_conflict'])
    execution='COMPLETE' if all(qualified(a) for a in arms) and all(q['classification']!='UNEVALUABLE' for q in pairs) and not issues else 'PARTIAL'
    summary=dict(execution=execution,stage_exit='PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION' if issues else 'FINAL_VERSION_BENCHMARK_COMPLETE' if execution=='COMPLETE' else 'PARTIAL',
        actual_formal_arms=52,matched_groups=26,distinct_inputs=10,new_inputs=0,
        layers={layer:stats([a for a in arms if a['layer']==layer],[q for q in pairs if q['layer']==layer]) for layer in ['A','B','C']},
        no_pooled_success_rate_or_geomean=True,no_cap_or_unknown_time_imputation=True,issues=issues)
    tiny_summary=tiny([a for a in arms if a['layer']=='B'],[q for q in pairs if q['layer']=='B'])
    for name,rows in [('arms',arms),('pairs',pairs),('mechanism_costs',costs),('model_index',model_index),('native_call_index',call_index),('physical_evidence_index',physical)]:table(OUT/(name+'.csv'),rows)
    write(OUT/'observations.json',dict(arms=arms,pairs=pairs,costs=costs))
    write(OUT/'stratified_summary.json',summary);write(OUT/'tiny_summary.json',dict(roles=tiny_summary))
    write(OUT/'cross_arm_bound_consistency.json',dict(status='PASS' if not issues else 'ISSUE',records=consistency,issues=issues,
        comparison_tolerance=1e-7,own_U_bound_Start_or_certificate_transferred=False))
    write(OUT/'numeric_policy_impacts.json',dict(negative_signed_gaps=[{k:a[k] for k in ['group','id','seed','repeat','method','U','L','signed_gap','certificate','T_cert','raw_claimed_U','raw_claimed_L','raw_claimed_certificate']} for a in arms if a['signed_gap']<0],
        rejected_call_diagnostics=[dict(group=a['group'],method=a['method'],source_reduced=a.get('source_reduced'),rejected_calls=a['rejected_calls']) for a in arms if a.get('rejected_calls')],
        raw_gaps_retained=True,L_clipped=False,new_tolerance=False,policy='original source/return/cover and numerical window; no rational global proof'))
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':run()
