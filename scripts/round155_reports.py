"""Six-arm reports and conservative original-journal common checkpoints."""
import csv
from round155_price_certificate import qualified_phase
from round155_common import *

def table(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def complete():
    matrix=read(OUT/'confirmation_matrix.json');arms=[];missing=[]
    for group in matrix['groups']:
        launch=group['launch'];destination=Path(launch['destination']);path=destination/'round154_endpoint.json'
        if not path.exists():missing.append(group['position']);continue
        arm=read(path);close=read(destination/'verification_closeout.json')
        assert close['implementation_qualified'] and close['evidence_complete'] and close['performance_eligible']
        assert sha(destination/'audit.json')==arm['audit_SHA']
        control=read(destination/'round153_control_audit.json');root=control['root']
        arm.update(actual_cap=launch['cap_seconds'],method155=launch['R154_method'],
            supported_proof_L=arm['L'],raw_search_L=arm.get('raw_search_L',arm['L']),
            own_floor=root['lower'] if root and root['qualified'] else None,
            helper_seconds=root['helper_process_seconds'] if root else 0.,
            formal_floor_rows=sum(r['floor_rows'] for r in control['models']))
        assert arm['formal_floor_rows']==0
        if not arm['certificate']:assert arm['T_cert'] is None
        arms.append(arm)
    pairs=[]
    for role in ['N-B35-S','R-X35-S-T2','R-X20-S-T1']:
        by={r['method155']:r for r in arms if r['id']==role}
        if set(by)!={'B','E'}:continue
        b,e=by['B'],by['E'];assert b['PE_SHA']==e['PE_SHA'] and b['input_SHA']==e['input_SHA']
        pairs.append(dict(role=role,cap=b['actual_cap'],B_U=b['U'],E_U=e['U'],B_raw_L=b['raw_search_L'],E_raw_L=e['raw_search_L'],
            B_proof_L=b['L'],E_proof_L=e['L'],B_gap=b['U']-b['L'],E_gap=e['U']-e['L'],
            E_minus_B_U=e['U']-b['U'],E_minus_B_L=e['L']-b['L'],
            B_T_produce=b['T_produce'],E_T_produce=e['T_produce'],B_T_verify=b['T_verify'],E_T_verify=e['T_verify'],
            B_T_total=b['T_total'],E_T_total=e['T_total'],B_T_cert=b['T_cert'],E_T_cert=e['T_cert'],
            B_certificate=b['certificate'],E_certificate=e['certificate'],E_floor=e['own_floor'],E_helper_seconds=e['helper_seconds'],
            independent_own_H=True,H_semantics_equal=b['H_semantic_SHA']==e['H_semantic_SHA'],
            E_raw_beyond_floor=e['raw_search_L']>=e['own_floor'] if e['own_floor'] is not None else None))
    write(OUT/'reports/complete_arms.json',dict(arms=arms,missing_positions=missing))
    write(OUT/'reports/complete_pairs.json',dict(pairs=pairs,missing_positions=missing));table(OUT/'reports/complete_pairs.csv',pairs)
    print(json.dumps(dict(completed=len(arms),missing=missing,pairs=pairs)),flush=True)

def checkpoints():
    """Last committed qualified raw information, never retrospective telemetry.

    The full closeout has checked model scopes and chronological cover support.
    Call cover bounds are known at that call's sequence; qualified callback
    bounds and physical witnesses carry their own publication availability.
    Hidden changes between committed events are explicitly not reconstructed.
    """
    matrix=read(OUT/'confirmation_matrix.json');all_rows=[];mechanisms=[]
    for group in matrix['groups']:
        launch=group['launch'];d=Path(launch['destination']);ep=d/'round154_endpoint.json'
        if not ep.exists():continue
        arm=read(ep);audit=read(d/'audit.json');assert audit['passed'] and not audit['source_rejections']
        obs=read(d/'observations.json');byseq={r['sequence']:r for r in obs}
        events=[]
        for row in obs:
            p=row['payload'];t=row['effective_available_seconds'];kind=p['kind']
            if kind=='witness':
                # Full physical re-evaluation already passed during closeout.
                events.append(dict(t=t,sequence=p['sequence'],kind='witness',U=p['objective']))
            elif kind=='bound' and p['global_available']:
                assert p['local_available'] and not p['retrospective']
                events.append(dict(t=t,sequence=p['sequence'],kind='raw_bound',L=p['global_bound']))
            elif kind=='call' and not p['full_original'] and p['cover']:
                pieces=sorted(p['cover'],key=lambda q:q['lower_g']);covered=0.
                for q in pieces:assert q['lower_g']<=covered+1e-12;covered=max(covered,q['upper_g'])
                assert covered+1e-12>=min(p['cutoff'],p['gmax'])
                value=min([p['cutoff']]+[min(q['lower'],q['cutoff']) for q in pieces])
                events.append(dict(t=t,sequence=p['sequence'],kind='raw_cover_at_call',L=value))
        root=read(d/'round153_control_audit.json')['root'];floor=None;floor_time=None
        if launch['R154_method']=='E' and root and root['qualified']:
            control=read(d/'round154_control_audit.json');ledger=control['proof_ledger']
            assert ledger['root_complete'] and ledger['sources_live']
            # The unchanged producer runs/accepts the root helper before its
            # first formal root call; the inherited contract binds that call.
            first=next(r for r in obs if r['payload']['kind']=='call')
            floor_time=first['effective_available_seconds'];floor=min(root['own_cutoff'],root['lower'])
            events.append(dict(t=floor_time,sequence=first['sequence'],kind='own_floor_available',floor=floor))
        events.sort(key=lambda e:(e['t'],e['sequence']))
        U=None;raw=0.;active_floor=None;trace=[];crossing=None;previous_below=None
        for event in events:
            if 'U' in event:U=event['U'] if U is None else min(U,event['U'])
            if 'L' in event:raw=max(raw,event['L'])
            if 'floor' in event:active_floor=event['floor']
            proof=max(raw,active_floor) if active_floor is not None else raw
            if U is not None:assert proof<=U+1e-7
            trace.append(dict(**event,verified_U=U,raw_search_L_last_committed=raw,supported_proof_L=proof,
                own_floor_active=active_floor is not None and raw<active_floor))
            if active_floor is not None:
                if raw<active_floor:previous_below=event['t']
                elif crossing is None:crossing=dict(first_observed_at=event['t'],last_observed_below_at=previous_below)
        save_gz(OUT/'reports/time_chains'/f'{launch["arm_id"]}.json.gz',trace)
        caps=[2400,3600,4800,7200] if launch['cap_seconds']==7200 else [1200]
        for checkpoint in caps:
            if arm['T_produce']<=checkpoint:
                row=dict(U=arm['U'],raw_search_L=arm.get('raw_search_L',arm['L']),proof_L=arm['L'],
                    observed_at=arm['T_produce'],state='finished_before_checkpoint',certificate=arm['certificate'],
                    T_cert=arm['T_cert'],exact_running_snapshot=False)
            else:
                available=[r for r in trace if r['t']<=checkpoint]
                last=available[-1] if available else None
                row=dict(U=last['verified_U'] if last else None,raw_search_L=last['raw_search_L_last_committed'] if last else None,
                    proof_L=last['supported_proof_L'] if last else None,observed_at=last['t'] if last else None,
                    state='last_committed_information',certificate=False,T_cert=None,exact_running_snapshot=False)
            row.update(role=launch['id'],method=launch['R154_method'],checkpoint_seconds=checkpoint,
                same_long_run_checkpoint_not_an_independent_short_arm=True,no_future_return_or_termination_bound_backfilled=True,
                missing_exact_checkpoint=None if arm['T_produce']<=checkpoint else
                    'No exact-time native/cover snapshot; use the latest already committed qualified information.')
            row['gap']=row['U']-row['proof_L'] if row['U'] is not None and row['proof_L'] is not None else None
            all_rows.append(row)
        mechanisms.append(dict(role=launch['id'],method=launch['R154_method'],own_floor=floor,
            floor_available_no_later_than=floor_time,raw_crossing_observation_bracket=crossing,
            floor_still_active_at_endpoint=floor is not None and arm.get('raw_search_L',arm['L'])<floor,
            chronology_source='immutable original observations/effective_available_seconds',
            retrospective_global_bound_trace_not_used=True,observation_SHA=sha(d/'observations.json')))
    table(OUT/'reports/common_checkpoints.csv',all_rows)
    write(OUT/'reports/common_checkpoints.json',dict(rows=all_rows,mechanisms=mechanisms))
    print(json.dumps(dict(checkpoints=len(all_rows),arms=len(mechanisms))),flush=True)

def costs():
    b=budget();rows=[]
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(path);rp=path.parent/'receipt.json';r=read(rp) if rp.exists() else None
        rows.append(dict(label=path.parent.name,kind=launch['kind'],reservation=launch['reservation_seconds'],
            G1=r['G1_seconds'] if r else None,exit=r['exit_code'] if r else None,
            timeout=r['timeout'] if r else None,receipt_SHA=sha(rp) if r else None))
    write(OUT/'cost_report.json',dict(UTC=utc(),budget=b,receipts=rows,nested_Runtime_Work_H_helper_not_added=True,
        measurement_gaps='Lightweight tool-only source/history/status/schema reads and prelaunch source hashing are not separately G1-metered. Reads during a running outer experiment do not add a second charge. Pure writing and public I/O are separate.',
        not_a_claim_of_complete_wall_clock_accounting=True))
    table(OUT/'reports/costs.csv',rows);print(json.dumps(b),flush=True)

def research():
    """Report each actually completed phase; never combine competing arms for free."""
    initial=read(OUT/'starting_pools.json');phases=[];trajectory=[];feedback=[];fee_by_phase={};fee_by_result={}
    for launch_path in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(launch_path);command=launch['command'];receipt_path=launch_path.parent/'receipt.json'
        # Bound to the actual argv, not an inferred label spelling.
        positions=[i for i,arg in enumerate(command) if Path(arg).name in ('round155_loop.py','round155_level.py')]
        if not positions:continue
        position=positions[0];args=command[position+1:]
        if len(args)<3 or args[0] not in ('run','replay'):continue
        role,phase=args[1:3];key=(role,phase)
        fee=dict(label=launch_path.parent.name,receipt=read(receipt_path) if receipt_path.exists() else None,
            receipt_SHA=sha(receipt_path) if receipt_path.exists() else None)
        parent='coupled' if args[0]=='run' else 'support_LP'
        result_path=(OUT/parent/f'{role}_{phase}'/'result.json').resolve()
        assert result_path not in fee_by_result
        fee_by_result[result_path]=fee
        if args[0]=='run':
            assert key not in fee_by_phase;fee_by_phase[key]=fee
    def ancestry(path,seen=None):
        """Union outer fee labels along this actual branch, stopping at inherited rounds."""
        seen=set() if seen is None else seen;path=Path(path).resolve()
        if not path.is_relative_to(OUT.resolve()) or path in seen:return {}
        seen.add(path);record=read(path)
        if path not in fee_by_result and record.get('derived_certificate_correction_not_new_optimization'):
            name=record['qualification_constructor_label'];receipt=read(OUT/'fees'/name/'receipt.json')
            fee=dict(label=name,receipt=receipt)
            launch=read(OUT/'fees'/name/'launch.json')
            assert any(Path(arg).name=='round155_price_requalify.py' for arg in launch['command'])
        else:fee=fee_by_result[path];receipt=fee['receipt']
        assert receipt and receipt['exit_observed'] and receipt['exit_code']==0
        found={fee['label']:receipt['G1_seconds']}
        for parent in record['prior_results']:found.update(ancestry(parent,seen))
        return found
    for path in sorted((OUT/'coupled').glob('*/result.json')):
        qualified_result,result=qualified_phase(path);role=result['role'];phase=result['label'];plan=read(path.parent/'plan.json')
        binding=fee_by_phase[role,phase];receipt=binding['receipt'];assert receipt and receipt['exit_code']==0
        assert receipt['exit_observed'] and not result['refresh_required']
        assert result['Q_SHA']==initial[role]['Q_SHA'] and result['scope']==initial[role]['scope']
        usage=result.get('new_column_usage',[]);own=[r for r in usage if r['origin_phase']==phase]
        records=result['records'];before_L=plan['inherited_lower'];before_U=plan['inherited_upper']
        selections=[read(p) for p in sorted(path.parent.glob('iter*/selection/result.json'))]
        selection_statuses={str(s):sum(v['Status']==s for v in selections) for s in sorted({v['Status'] for v in selections})}
        prior_fees=ancestry(plan['source']);prior_cost=math.fsum(prior_fees.values())
        row=dict(role=role,phase=phase,rule=result['rule'],source=plan['source'],source_SHA=plan['source_SHA'],
            inherited_L=before_L,inherited_U=before_U,lower=result['lower'],upper=result['upper'],gap=result['gap'],
            lower_increment=result['lower']-before_L,upper_decrease=before_U-result['upper'],
            initial_columns=plan['initial_columns'],columns=len(result['columns']),supports=len(result['supports']),
            completed_iterations=len(records),decision=result['decision'],direct_outer_G1_seconds=receipt['G1_seconds'],
            fee_label=binding['label'],receipt_SHA=binding['receipt_SHA'],
            prior_R155_branch_G1_seconds=prior_cost,branch_G1_seconds=prior_cost+receipt['G1_seconds'],
            prior_branch_fee_labels=json.dumps(sorted(prior_fees)),
            tracked_R155_columns=len(usage),this_phase_columns=len(own),
            this_phase_columns_ever_used=sum(r['used_iterations']>0 for r in own),
            all_tracked_columns_ever_used=sum(r['used_iterations']>0 for r in usage),
            maximum_tracked_column_weight=max((r['maximum_weight'] for r in usage),default=0.),
            selection_LP_Optimize=len(selections) if selections else sum(r['selection_LP_Optimize'] for r in records),
            selection_status_counts=json.dumps(selection_statuses,sort_keys=True),
            qualified_selected_candidates=sum(v['selected'] for v in selections),
            nonoptimal_feasible_candidates_accepted=sum(v['nonoptimal_feasible_accepted'] for v in selections),
            unavailable_selected_candidates=sum(not v['selected'] for v in selections),
            resolved_level_count=len(result.get('resolved_levels',[])),
            resolved_levels_json=json.dumps(result.get('resolved_levels',[]),sort_keys=True),
            unresolved_level_exact=result.get('unresolved_level_exact'),
            duplicate_returns=sum(r['duplicate_returns'] for r in records),
            added_negative=sum(r['added_negative'] for r in records),
            source_result=path.relative_to(ROOT).as_posix(),result_SHA=sha(path),
            qualified_source_result=qualified_result.relative_to(ROOT).as_posix(),qualified_result_SHA=sha(qualified_result),
            historical_price_transport_corrected=qualified_result.resolve()!=path.resolve(),
            small_screen_is_not_saturation=plan['iteration_limit'] is not None,
            full_Q_primal_upper_is_not_physical_route_upper=True)
        row.update({name+'_seconds':value for name,value in result['costs'].items()});phases.append(row)
        trajectory.append(dict(role=role,phase=phase,kind='phase_start',iteration=-1,elapsed_seconds=0.,
            cumulative_branch_measured_seconds=prior_cost,
            lower=before_L,upper=before_U,gap=before_U-before_L,columns=plan['initial_columns'],supports=plan['initial_supports']))
        for record in records:
            trajectory.append(dict(role=role,phase=phase,kind='completed_feedback',
                cumulative_branch_measured_seconds=prior_cost+record['elapsed_seconds'],**record))
            data=load_gz(path.parent/f'iter{record["iteration"]:06}'/'column_feedback.json.gz')
            for number,item in enumerate(data):
                stock=item['stock'];feedback.append(dict(role=role,phase=phase,iteration=record['iteration'],return_number=number,
                    Y=json.dumps(stock['Y'],separators=(',',':')),new=item['new'],negative=item['negative'],
                    original_price_exact=stock['price_exact'],true_f_exact=stock['f_exact'],
                    true_reduced_cost_exact=item['true_reduced_cost_exact'],target_violation_exact=item['target_violation_exact']))
        trajectory.append(dict(role=role,phase=phase,kind='qualified_phase_endpoint',iteration=len(records),
            elapsed_seconds=result['seconds'],lower=result['lower'],upper=result['upper'],gap=result['gap'],
            cumulative_branch_measured_seconds=prior_cost+receipt['G1_seconds'],
            columns=len(result['columns']),supports=len(result['supports']),decision=result['decision']))
    comparisons=[]
    for role in ['K-35-U','N-C20-U']:
        by={p['rule']:p for p in phases if p['role']==role and p['phase'] in ('first_screen_v1','bounded_screen_v1')}
        if set(by)!={'first','bounded'}:continue
        first,bounded=by['first'],by['bounded']
        assert first['source_SHA']==bounded['source_SHA']==initial[role]['result_SHA']
        for key in ['inherited_L','inherited_U','initial_columns']:
            assert first[key]==bounded[key]
        comparison=dict(role=role,same_original_pool_SHA=initial[role]['result_SHA'],same_full_Q_SHA=initial[role]['Q_SHA'],
            comparison_scope='two predeclared short complete feedback loops, not saturation or a statistical population claim')
        for rule,arm in by.items():
            for key in ['lower','upper','gap','completed_iterations','direct_outer_G1_seconds','selection_seconds','pricing_seconds',
                        'RMP_seconds','certificate_seconds','feedback_seconds','this_phase_columns','this_phase_columns_ever_used',
                        'added_negative','duplicate_returns','decision']:
                comparison[rule+'_'+key]=arm[key]
        comparisons.append(comparison)
    table(OUT/'reports/research_phases.csv',phases)
    table(OUT/'reports/coupled_trajectory.csv',trajectory)
    table(OUT/'reports/column_quality.csv',feedback)
    table(OUT/'reports/matched_loop_comparisons.csv',comparisons)
    write(OUT/'reports/research_phases.json',dict(phases=phases,comparisons=comparisons,
        trajectory_cost_scope='Each branch sums distinct prior run/replay and explicit correction-constructor outer receipts on its actual source chain. Other global interface/readback fees remain in the complete G1 ledger. A shared correction constructor appears once in each dependent branch but is charged only once globally. Intermediate points add current measured loop elapsed time; initial imports and final process shutdown are included only at the outer-receipt endpoint. Branch trajectories are not additive global charges. Competing screens are separate branches.',
        different_direction_price_bounds_are_not_one_monotone_price_curve=True))
    print(json.dumps(dict(phases=len(phases),trajectory_rows=len(trajectory),column_returns=len(feedback),matched_roles=len(comparisons))),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
