"""Pure current-panel aggregation; no optimizer, native library or live raw polling."""
from round137_common import *
import collections, inspect, statistics
import round134_analyze as inherited
import round108_reader as core
import round108_decisions as accepted_decisions
csv_write=inherited.csv_write

def observed_phase_span(phases,start_event,end_event,label_key):
    """A matched recorded phase interval, never a complete-cost decomposition."""
    starts=[dict(r) for r in phases if r['event']==start_event]
    ends=[dict(r) for r in phases if r['event']==end_event]
    result=dict(start_event=start_event,end_event=end_event,label_key=label_key,
        starts=starts,ends=ends,span_seconds=None,status='NOT_RECORDED',complete_cost_decomposition=False)
    if starts or ends:
        result['status']='AMBIGUOUS_OR_INCOMPLETE_EVENTS'
        if len(starts)==len(ends)==1:
            import re
            def label(row):
                found=re.search(r'(?:^|;)'+re.escape(label_key)+r'=([^;]+)',row.get('detail',''))
                return found.group(1) if found else None
            left,right=starts[0],ends[0]
            low,high=float(left['process_seconds']),float(right['process_seconds'])
            if (math.isfinite(low) and math.isfinite(high) and high>=low and
                int(right['sequence'])>int(left['sequence']) and label(left) and label(left)==label(right)):
                result.update(status='MATCHED_SINGLE_RECORDED_SPAN',span_seconds=high-low,
                    matched_label=label(left),start_status=left.get('status'),end_status=right.get('status'))
    return result

def am_decisions(d,launch):
    """Join the existing finite and logical decision observations by sequence."""
    finite_path=d/'external/adaptive_mass_decision_ledger.csv'
    logical_path=d/'external/c6_split_decision_ledger.csv'
    finite=core.rows(finite_path) if finite_path.exists() else []
    logical=core.rows(logical_path) if logical_path.exists() else []
    by_sequence={r['decision_sequence']:r for r in finite}
    assert len(by_sequence)==len(finite)
    assert len({r['decision_sequence'] for r in logical})==len(logical)
    assert set(by_sequence)<={r['decision_sequence'] for r in logical}
    out=[]
    for raw in logical:
        row=dict(raw);sequence=row['decision_sequence'];fm=by_sequence.get(sequence)
        row['legacy_C6_rho']=row.pop('rho',None)
        row['legacy_C6_rho_source']=row.pop('rho_source',None)
        row['legacy_C6_threshold_comparison']=row.pop('threshold_comparison',None)
        left=row['left_child_infeasible']=='1';right=row['right_child_infeasible']=='1'
        if left or right:
            assert fm is None
            classification='LOGICAL_BOTH_INFEASIBLE' if left and right else 'LOGICAL_ONE_INFEASIBLE'
            row.update(tau=str(launch['AM_threshold']),S_AM=None,score_tolerance=None,
                margin_at_actual_tau=None,finite_score_gate=False)
        else:
            assert fm is not None,('missing declared finite AM decision',d,sequence)
            assert fm['interval_id']==row['interval_id'] and fm['selected_action']==row['selected_action']
            row.update(fm);assert float(row['tau'])==launch['AM_threshold']
            reason=row['deterministic_reason']
            gate=reason in ['adaptive_mass_score_reaches_tau','adaptive_mass_score_below_tau_native_target']
            classification='FINITE_SCORE_GATE' if gate else 'FINITE_TERMINAL_NO_STRICT' if reason=='adaptive_mass_no_strict_child_improvement' else 'FINITE_OTHER_ACTION'
            score,tolerance=float(row['S_AM']),float(row['score_tolerance'])
            row.update(margin_at_actual_tau=score+tolerance-launch['AM_threshold'] if math.isfinite(score) and math.isfinite(tolerance) else None,
                finite_score_gate=gate)
        row.update(exposure_class=classification,position=launch['global_launch_number'],role=launch['id'],
            seed=launch['seed'],method=launch['method'],tau_controls_logical_infeasibility=False,
            source_finite_ledger_SHA=sha(finite_path) if finite_path.exists() else None,
            source_all_child_ledger_SHA=sha(logical_path) if logical_path.exists() else None,
            offline_actions_at_other_tau_not_speed_counterfactual=True)
        out.append(row)
    return out

def eligibility_limits(d,launch,source_rejected=False):
    """Audit recorded guards within retained scheduler epochs, preserving gaps."""
    if launch['arm']!='M-B' or launch['method']=='S2R':
        return dict(status='NOT_APPLICABLE',evaluations=0,depth_rejections=0,width_rejections=0,unknown=0),[]
    leaf_path=d/'external/paper_leaf_ledger.csv';split_path=d/'external/split_decision_ledger.csv'
    leaves=core.rows(leaf_path) if leaf_path.exists() else []
    leaves={r['leaf_id']:r for r in leaves}
    split=core.rows(split_path) if split_path.exists() else []
    out=[]
    for raw in split:
        leaf=leaves.get(raw['parent_id']);eligible=raw['eligible'].lower() in ('true','1')
        row=dict(parent_id=raw['parent_id'],eligible=eligible,recorded_reason=raw['reason'])
        if source_rejected:row.update(classification='UNKNOWN_AFTER_SOURCE_REJECTION_RESET',depth=None,width=None)
        elif leaf is None:row.update(classification='UNKNOWN_LEAF_GEOMETRY',depth=None,width=None)
        else:
            depth=int(leaf['depth']);width=float(leaf['gamma_U'])-float(leaf['gamma_L'])
            depth_block=depth>=8;width_block=width<=1e-4+1e-12
            if eligible:assert not depth_block and not width_block,('recorded eligibility contradicts leaf limits',d,row)
            row.update(depth=depth,width=width,depth_condition_rejected=not eligible and depth_block,
                width_condition_evaluated=not depth_block,
                width_condition_rejected=not eligible and not depth_block and width_block,
                width_would_also_reject=not eligible and depth_block and width_block,
                classification='ELIGIBLE' if eligible else 'LIMIT_CONDITION_REJECTED' if depth_block or width_block else 'OTHER_POLICY_INELIGIBILITY')
        out.append(row)
    unknown=sum(r['classification'] in ['UNKNOWN_LEAF_GEOMETRY','UNKNOWN_AFTER_SOURCE_REJECTION_RESET','OTHER_POLICY_INELIGIBILITY'] for r in out)
    summary=dict(status='NO_RECORDED_ELIGIBILITY_EVALUATION' if not out else 'PARTIAL' if unknown else 'RECORDED_GUARD_ROWS_AUDITED',
        evaluations=len(out),depth_rejections=sum(r.get('depth_condition_rejected',False) for r in out),
        width_rejections=sum(r.get('width_condition_rejected',False) for r in out),
        width_also_would_reject=sum(r.get('width_would_also_reject',False) for r in out),unknown=unknown,
        maximum_depth=8,minimum_width=1e-4,width_numeric_margin=1e-12,
        source_premise='Recorded guard rows cover completed eligible decisions and reached ineligible branches; eligible work can stop before its row. Ordinary retained scheduler epochs preserve leaf geometry/depth; source-rejection reset makes this reconstruction unknown. The guard is depth<8 && width>1e-4+1e-12, with short-circuit evaluation.',
        only_recorded_rows_audited=True,missing_row_not_proof_of_no_attempt=True,
        source_rejection_reset_guard=source_rejected,no_test_or_rejection_inferred_from_zero_width_proof=True)
    return summary,out

def gather(stage):
    source=inspect.getsource(inherited.gather)
    source=source.replace("manifest=read(OUT/f'{stage}_matrix_frozen.json')", "manifest=read(OUT/'matrix_frozen.json');manifest=dict(manifest,groups=[g for g in manifest['groups'] if g['stage']==stage])")
    source=source.replace("endpoint=d/'round134_endpoint.json'", "endpoint=d/'round135_endpoint.json'")
    source=source.replace("assert e['certificate']==result['strict_certified_original_problem']", "assert isinstance(e['certificate'],bool)")
    source=source.replace("if e['certificate']:assert e['certificate_qualified'] and e['T_cert']==e['T_produce'] and e['performance_eligible']", "if e['certificate'] and e['performance_eligible']:assert e['certificate_qualified'] and e['T_cert']==e['T_produce']")
    ns=dict(vars(inherited),ROOT=ROOT,OUT=OUT);exec(compile(source,__file__+'::accepted_gather','exec'),ns)
    rows,missing,ops=ns['gather'](stage);matrix=read(OUT/'matrix_frozen.json')
    for r in rows:
        launch=matrix['groups'][r['position']-1]['launch'];p=launch['panel'];d=Path(launch['destination'])
        result=read(d/'result.json');audit=read(d/'audit.json');data=core.evidence.instance(ROOT,p)
        endpoint=read(d/'round135_endpoint.json');relative,relative_reason=accepted_decisions.relative(endpoint)
        y=audit['physical']['Y'];r.update(S=sum(y[i]/data['D'][i] for i in range(1,p['V']+1)),
            n=p['V'],source=p.get('source'),base_id=p.get('base_id',p['id']),
            physical_configuration_id=p.get('physical_configuration_id',p['id']),
            T=p['T_seconds'],AM_threshold=launch['AM_threshold'],
            raw_claimed_certificate=result['strict_certified_original_problem'],
            raw_result_relative_gap=result.get('gap'),
            relative_gap=relative,relative_gap_null_reason=relative_reason,
            H_complete=endpoint.get('H_complete'),
            H_semantic_SHA=endpoint.get('H_semantic_SHA'),
            H_fleet_SHA=endpoint.get('H_fleet_SHA'))
        if 'relative_gap' in endpoint:
            assert relative==endpoint['relative_gap'] and relative_reason==endpoint['relative_gap_null_reason']
        shortage=sum(data['D'][1:])-sum(data['b'][1:])
        floor=p['lambda']*min(data['w'][i]/data['D'][i] for i in range(1,p['V']+1))*shortage if shortage>0 else 0.
        r['offline_problem_floor']=floor;r['offline_floor_not_backfilled_into_producer_certificate']=True
        ledger=d/'external/paper_optimize_ledger.csv';calls=core.rows(ledger) if ledger.exists() else []
        r['native_solver_seconds']=sum(float(x['solver_runtime']) for x in calls) if calls else result.get('gurobi_runtime')
        r['root_lp_seconds']=sum(float(x['solver_runtime']) for x in calls if x['solve_kind']=='LP' and x['leaf_id']=='L0')
        r['child_lp_seconds']=sum(float(x['solver_runtime']) for x in calls if x['solve_kind']=='LP' and x['leaf_id']!='L0')
        r['native_MIP_seconds']=sum(float(x['solver_runtime']) for x in calls if x['solve_kind']!='LP') if calls else result.get('gurobi_runtime')
        r['model_build_seconds']=result.get('external_gini_tree_model_build_seconds')
        phases=core.rows(d/'phases.csv')
        h_phase=observed_phase_span(phases,'hga_start','decoded_descent_complete','label')
        first_model_phase=observed_phase_span(phases,'root_canonical_model_construction_start','root_canonical_model_construction_complete','leaf')
        r['H_seconds']=h_phase['span_seconds']
        r['H_phase_span_status']=h_phase['status'];r['H_phase_end_status']=h_phase.get('end_status')
        r['root_model_construction_seconds']=first_model_phase['span_seconds']
        r['first_model_phase_span_status']=first_model_phase['status']
        r['first_model_phase_end_status']=first_model_phase.get('end_status')
        r['cost_phase_ledger_SHA']=sha(d/'phases.csv')
        r['effort_counter_source']='SUM_RETURNED_PAPER_OPTIMIZE_CALLS' if calls else 'RESULT_COUNTERS_NO_EXPLICIT_PAPER_LEDGER'
        r['explicit_L0_LP_calls']=sum(x['solve_kind']=='LP' and x['leaf_id']=='L0' for x in calls)
        r['explicit_nonL0_LP_calls']=sum(x['solve_kind']=='LP' and x['leaf_id']!='L0' for x in calls)
        write(OUT/f'reports/cost_phases/position_{r["position"]:03}.json',dict(H_search_phase=h_phase,first_canonical_model_phase=first_model_phase,
            phase_ledger_SHA=r['cost_phase_ledger_SHA'],nested_diagnostic_not_extra_budget=True,
            H_complete_is_a_separate_qualification_field=r['H_complete']))
        point=d/'external/round127_root_lp.csv'
        status=d/'external/round127_root_lp_status.json'
        if point.exists() and status.exists() and read(status).get('complete'):
            values={x['name']:float(x['value']) for x in core.rows(point)}
            r['observed_root_LP_objective']=values['G']+p['lambda']*sum(data['w'][i]*values[f'e_{i}'] for i in range(1,p['V']+1))
            r['observed_root_status']=calls[0]['native_status'] if calls else None
            r['observed_root_scope']=audit['model_contracts'][0]['scope'] if audit['model_contracts'] else None
        else:
            r['observed_root_LP_objective']=None;r['observed_root_status']=None
            r['observed_root_scope']=None;r['observed_root_point_missing_reason']='not_exposed_or_optional_point_incomplete'
        r['observed_root_LP_optimum']=r['observed_root_LP_objective'] if r['observed_root_status']=='OPTIMAL' else None
        if audit['model_contracts'] and launch['arm']=='M-B':
            model=core.lp_model(ROOT/audit['model_contracts'][0]['model']['path'])
            dedicated={'W_SP','r_min','r_max'}
            domain={n:dict(bounds=model['bounds'][n],type=model['types'][n]) for n in model['order'] if n not in dedicated}
            canonical=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            r['initial_shared_domain_SHA']=canonical(domain)
            r['initial_objective_SHA']=canonical(model['objective'])
        else:r['initial_shared_domain_SHA']=r['initial_objective_SHA']=None
        decisions=am_decisions(d,launch)
        r['AM_decisions']=len(decisions)
        r['AM_actions']=dict(collections.Counter(x['selected_action'] for x in decisions))
        r['AM_max_decision_parent_depth']=max((int(x['depth']) for x in decisions),default=None)
        r['AM_max_probed_child_depth']=max((int(x['depth'])+1 for x in decisions),default=None)
        leaves=d/'external/paper_leaf_ledger.csv';leaves=core.rows(leaves) if leaves.exists() else []
        r['final_max_materialized_leaf_depth']=max((int(x['depth']) for x in leaves),default=None)
        r['final_min_materialized_leaf_width']=min((float(x['gamma_U'])-float(x['gamma_L']) for x in leaves),default=None)
        r['AM_depth_limit']=8;r['AM_minimum_width']=1e-4
        limits,limit_rows=eligibility_limits(d,launch,source_rejected=r['source_rejected'])
        r['AM_limit_trigger_audit']=limits['status']
        r['AM_limit_eligibility_evaluations']=limits['evaluations']
        r['AM_depth_limit_rejections']=limits['depth_rejections'];r['AM_width_limit_rejections']=limits['width_rejections']
        r['AM_width_limit_also_would_reject']=limits.get('width_also_would_reject',0)
        r['AM_limit_audit_unknown']=limits['unknown']
        write(OUT/f'reports/AM/limits_{r["position"]:03}.json',dict(summary=limits,observations=limit_rows))
        r['AM_class_counts']=dict(collections.Counter(x['exposure_class'] for x in decisions))
        r['AM_finite_score_gates']=sum(x['finite_score_gate'] for x in decisions)
        r['AM_exposure']='EXPOSED_CHILD_DECISIONS' if decisions else 'NO_CHILD_DECISION_EXPOSURE'
        write(OUT/f'reports/AM/position_{r["position"]:03}.json',decisions)
        r['AM_reasons']=dict(collections.Counter(x['deterministic_reason'] for x in decisions))
    csv_write(OUT/f'reports/{stage}/arms.csv',rows);write(OUT/f'reports/{stage}/arms.json',rows)
    return rows,missing,ops

def pair(a,b,kind):
    assert a['input_SHA']==b['input_SHA'] and a['PE_SHA']==b['PE_SHA']
    assert a['lambda_value']==b['lambda_value'] and a['T']==b['T']
    # Offline consistency only: no other arm's witness enters production or
    # repairs a claim. A contradiction must be inspected before any ranking.
    assert a['L']<=b['U']+1e-7 and b['L']<=a['U']+1e-7,('paired bound/feasible objective contradiction',a['position'],b['position'])
    if a['certificate'] and b['certificate'] and a['performance_eligible'] and b['performance_eligible']:
        assert abs(a['U']-b['U'])<=1e-7,('certified physical objectives differ',a['position'],b['position'])
    p=inherited.pair(a,b);p['comparison_kind']=kind
    p['shared_baseline']=False;p['left_source_stage']=a['stage'];p['right_source_stage']=b['stage']
    p.update(left_position=a['position'],right_position=b['position'],
        left_U_minus_right=a['U']-b['U'],left_L_minus_right=a['L']-b['L'],
        left_gap_minus_right=a['signed_gap']-b['signed_gap'],
        left_full_seconds=a['T_produce'],right_full_seconds=b['T_produce'],
        left_certificate=a['certificate'],right_certificate=b['certificate'],
        left_endpoint_dominates=a['U']<=b['U']+1e-7 and a['L']>=b['L']-1e-7 and (a['U']<b['U']-1e-7 or a['L']>b['L']+1e-7),
        right_endpoint_dominates=b['U']<=a['U']+1e-7 and b['L']>=a['L']-1e-7 and (b['U']<a['U']-1e-7 or b['L']>a['L']+1e-7))
    p['matched_own_H']=bool(a['H_complete'] and b['H_complete'] and a['H_semantic_SHA']==b['H_semantic_SHA'] and a['H_fleet_SHA']==b['H_fleet_SHA'])
    p['matched_initial_root_domain_objective_cutoff']=bool(a.get('initial_shared_domain_SHA') and
        a['initial_shared_domain_SHA']==b.get('initial_shared_domain_SHA') and a['initial_objective_SHA']==b.get('initial_objective_SHA') and
        a.get('observed_root_scope')==b.get('observed_root_scope'))
    p['root_LP_attribution_exposed']=bool(p['matched_own_H'] and p['matched_initial_root_domain_objective_cutoff'] and
        a.get('observed_root_LP_optimum') is not None and b.get('observed_root_LP_optimum') is not None)
    p['root_LP_left_minus_right']=a['observed_root_LP_optimum']-b['observed_root_LP_optimum'] if p['root_LP_attribution_exposed'] else None
    return p

def analysis_preflight():
    matrix=read(OUT/'matrix_frozen.json')
    assert len(matrix['groups'])==120
    missing=[g['position'] for g in matrix['groups'] if not (Path(g['launch']['destination'])/'verification_closeout.json').is_file()
        or not (OUT/'fees'/f'arm_{g["position"]:03}'/'receipt.json').is_file()]
    assert not missing,('Full analysis requires all120 sealed positions before reading audit/model files',missing)
    for group in matrix['groups']:
        destination=Path(group['launch']['destination'])
        closeout=read(destination/'verification_closeout.json')
        fee=read(OUT/'fees'/f'arm_{group["position"]:03}'/'receipt.json')
        assert closeout['necessary_verification_complete'] and closeout['evidence_complete'],group['position']
        assert fee['exit_observed'] and not fee['timeout'] and fee['supervisor_failure'] is None,group['position']
        assert all(math.isfinite(float(fee[k])) for k in ['start_unix','end_unix','outer_seconds','G1_seconds','separately_reported_seconds'])
        assert fee['end_unix']>=fee['start_unix'] and fee['G1_seconds']>=0
        assert fee['nested_H_LP_MIP_not_added'] and fee['budget_category']=='native'
        # A returned worker's status is preserved, including arm1's resolved
        # postreader-only error. Full qualification is re-read by gather; this
        # small-metadata gate neither rewrites exits nor substitutes for it.
    returned=read(OUT/'run_loop_return.json')
    assert returned['stop_after']==120 and not returned['budget']['unclosed']
    assert not budget()['unclosed'],'Do not parse raw during a timed native arm'
    return matrix


def main():
    analysis_preflight()
    plan=read(OUT/'experiment_plan.json');arms=[];operations=[];missing=[]
    for stage in plan['stages']:
        rows,absent,ops=gather(stage);arms+=rows;operations+=ops;missing+=absent
    by={(r['role'],r['seed'],r['method']):r for r in arms};pairs=[]
    for r in arms:
        if r['method']=='S2' and r['stage'] in ['B1','B2','B3','D2-main']:
            for control in ['P','PS']:
                other=by.get((r['role'],r['seed'],control))
                if other:pairs.append(pair(r,other,r['stage']))
        if r['method']=='PS' and r['stage'] in ['B1','B2','B3','D2-main']:
            other=by.get((r['role'],r['seed'],'P'))
            if other:pairs.append(pair(r,other,r['stage']))
        if r['stage'] in ['C1','C2','D2-AM','D2-mechanism']:
            baseline=by.get((r['role'],r['seed'],'S2'))
            if baseline:pairs.append(pair(r,baseline,r['stage']))
    # B3 has twelve newly executed positions. Its scientific weight comparison
    # also contains the two actual rho1 triplets already paid in B2. Reuse only
    # those registered observations; never manufacture another run or input.
    shared_roles=sorted({r['physical_configuration_id'] for r in arms if r['stage']=='B3'})
    assert len(shared_roles)==2
    shared_positions=[]
    for role in shared_roles:
        base={method:by[role,0,method] for method in ['P','PS','S2']}
        assert all(r['stage']=='B2' and abs(r['rho']-1)<1e-10 for r in base.values())
        shared_positions.extend(r['position'] for r in base.values())
        for left,right in [('S2','P'),('S2','PS'),('PS','P')]:
            shared=pair(base[left],base[right],'B3');shared['shared_baseline']=True
            pairs.append(shared)
    assert len(set(shared_positions))==6
    summary={}
    for stage in plan['stages']:
        rr=[r for r in arms if r['stage']==stage];pp=[p for p in pairs if p['comparison_kind']==stage]
        summary[stage]=dict(expected=plan['stages'][stage]['positions'],completed=len(rr),
            certificates=dict(collections.Counter(r['method'] for r in rr if r['certificate'] and r['performance_eligible'])),
            ineligible=[r['position'] for r in rr if not r['performance_eligible']],
            comparisons={f'{left}/{right}':dict(n=len(qq),classes=dict(collections.Counter(p['class'] for p in qq)),
                directions=dict(collections.Counter(p['direction'] for p in qq)),
                both_certified_n=sum(p['class']=='BOTH_CERTIFIED' for p in qq),
                both_certified_geomean=math.exp(statistics.fmean(math.log(p['right_over_left_ratio']) for p in qq if p['class']=='BOTH_CERTIFIED')) if any(p['class']=='BOTH_CERTIFIED' for p in qq) else None,
                material_wins=sum(p.get('material') is True and p['direction']=='Win' for p in qq),
                material_losses=sum(p.get('material') is True and p['direction']=='Lose' for p in qq))
                for left,right in sorted(set((p['left'],p['right']) for p in pp)) for qq in [[p for p in pp if p['left']==left and p['right']==right]]})
    summary['B3'].update(new_positions=sum(r['stage']=='B3' for r in arms),
        new_objective_configurations_per_method=len({r['role'] for r in arms if r['stage']=='B3'}),
        full_weight_configurations_per_method=len({p['role'] for p in pairs if p['comparison_kind']=='B3'}),
        shared_baseline_positions=sorted(shared_positions),shared_baseline_observation_stage='B2',
        no_shared_position_added_to_native_count=True)
    assert summary['B3']['new_positions']==12 and summary['B3']['new_objective_configurations_per_method']==4
    assert summary['B3']['full_weight_configurations_per_method']==6
    assert all(v['n']==6 for v in summary['B3']['comparisons'].values())
    write(OUT/'reports/arms.json',arms);csv_write(OUT/'reports/arms.csv',arms)
    write(OUT/'reports/pairs.json',pairs);csv_write(OUT/'reports/pairs.csv',pairs)
    write(OUT/'reports/operations.json',operations)
    write(OUT/'reports/summary.json',dict(UTC=utc(),registered=120,completed=len(arms),missing=missing,
        independent_certificate_count=sum(r['independent_proof'] for r in arms),
        rejected_native_independent_certificates=[r['arm_id'] for r in arms if r['source_rejected'] and r['independent_proof']],
        completed_positions=[r['position'] for r in arms],stages=summary,budget=budget(),
        base_inputs=16,physical_configurations=20,objective_configurations=24,
        denominator_warning='Seed/weight/variant repeats and shared stations are not independent random samples; historical panels separate; no censored time imputation',
        all_entered_adverse_open_and_ineligible_retained=True))
    write(OUT/'resource_accounting.json',budget())
    print(json.dumps(dict(completed=len(arms),missing=missing,stages=summary,budget=budget()['G1_seconds'])))

if __name__=='__main__':main()
