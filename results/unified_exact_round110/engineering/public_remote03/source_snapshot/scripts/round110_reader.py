"""Round110 stdlib raw reconstruction using the audited R108 core and rebuild loop.
Only panel bookkeeping, Seed readback, new decision tables and budgets differ.
No solver/environment load; absolute measured paths translate to explicit root.
"""
from round108_reader import *
import round110_decisions as decision
import round109_seed_scope as computed
import round110_evidence as numerical
ROUND='results/unified_exact_round110'
_inherited_full_fleet=full_fleet
_inherited_endpoint=endpoint

def endpoint(root,launch,ident,d,j,formal):
    return numerical.endpoint(root,launch,ident,d,j,formal,_inherited_endpoint)

def full_fleet(root,p,w):
    value=_inherited_full_fleet(root,p,w);a=evidence.instance(root,p);cars=[]
    for route in value['routes']:
        pickup=sum(op['pickup'] if isinstance(op,dict) else op[1] for op in route['operations'])
        station_drop=sum(op['drop'] if isinstance(op,dict) else op[2] for op in route['operations'])
        return_unload=pickup-station_drop
        travel=sum(math.hypot(a['xy'][i][0]-a['xy'][j][0],a['xy'][i][1]-a['xy'][j][1])/1.5 for i,j in zip(route['nodes'],route['nodes'][1:]))
        handling=(p['pickup_seconds']+p['drop_seconds'])*pickup
        assert return_unload>=0 and handling==p['pickup_seconds']*pickup+p['drop_seconds']*(station_drop+return_unload)
        cars.append(dict(vehicle=route.get('vehicle',route.get('vehicle_id')),actual_station_count=len(route['operations']),pickup=pickup,station_drop=station_drop,
            return_unload=return_unload,station_handling_seconds=p['pickup_seconds']*pickup+p['drop_seconds']*station_drop,
            return_unload_seconds=p['drop_seconds']*return_unload,travel_seconds=travel,handling_seconds=handling,closed_duration_seconds=travel+handling))
    value.update(lambda_P=p['lambda']*value['P'],sum_omega=sum(a['w'][1:]),total_initial_stock=sum(a['b'][1:]),
        total_final_stock=sum(value['Y'][1:]),total_target=sum(a['D'][1:]),total_return_load=sum(value['return_loads']),
        service_station_count=sum(c['actual_station_count'] for c in cars),cars=sorted(cars,key=lambda c:c['vehicle']))
    return value

def fee_records(out):
    data=[]
    for directory in sorted((out/'fees').iterdir()):
        launch=read(directory/'launch.json');receipt=read(directory/'receipt.json')
        assert not launch.get('engineering',False) and not receipt.get('engineering',False)
        assert launch['conservative_process_starts']==receipt['conservative_process_starts']
        data.append(dict(label=directory.name,outer_seconds=receipt['outer_seconds'],exit_code=receipt['exit_code'],
            stop_reason=receipt['stop_reason'],conservative_process_starts=receipt['conservative_process_starts'],
            wrapper_processes=launch['actual_wrapper_processes'],declared_children=launch['declared_native_children'],
            actual_native_children_with_launch=receipt.get('actual_native_children_with_launch',1),
            prepaid_child_slot=launch.get('prepaid_native_child'),
            prepaid_native_children=launch.get('prepaid_native_children',1 if launch.get('prepaid_native_child') else 0),
            newly_billed_native_children=launch.get('newly_billed_native_children',launch['declared_native_children']-(1 if launch.get('prepaid_native_child') else 0)),
            original_coupon=launch.get('original_coupon'),supplemental_plan_SHA=launch.get('supplemental_plan_SHA'),
            extra_driver_processes=receipt.get('extra_driver_processes',0),earlier_fee_refunded=receipt.get('earlier_fee_refunded',False),
            native_child_fee_already_in_qualification_cli02=receipt.get('native_child_fee_already_in_qualification_cli02',False),
            earlier_failure_slots_refunded=False,nested_seconds_added=False))
    return data

def require_identity(root,identity,candidate):
    assert identity['candidate_binary_sha256']==candidate['production_PE_SHA'] and identity['dll_sha256']==candidate['DLL_SHA']
    assert identity['source_hashes']==candidate['source_bindings']
    for name,digest in candidate['source_bindings'].items():assert sha(root/name)==digest,name
    for name,digest in identity['helpers'].items():assert sha(root/name)==digest,name
    assert identity['prereg_sha256']==sha(portable(root,identity['protocol_path']))
    assert identity['runner_sha256']==sha(root/'scripts/round110_campaign.py')

def check_native_parameters(launch,result,journal):
    settings=dict(read_return_code=0,Threads=1,Seed=launch['seed'],Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    assert launch['command'][launch['command'].index('--gurobi-seed')+1]==str(launch['seed'])
    for call in journal['calls'].values():assert call['settings']==settings
    if journal['started']:
        for name,value in dict(threads=1,seed=launch['seed'],presolve=-1,mip_gap=0.,mip_gap_abs=0.).items():
            for suffix in ['requested','effective']:assert result['gurobi_'+name+'_'+suffix]==value
            for suffix in ['set_return_code','get_return_code']:assert result['gurobi_'+name+'_'+suffix]==0

def rebuild(root,dest,qualification_only=False):
    root=Path(root).resolve();out=root/ROUND;dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    start_reader.ROOT=root
    candidate=read(out/'candidate_identity.json');formal_gate=read(out/'review/performance_admission.json') if not qualification_only else None
    if formal_gate:assert formal_gate['decision']=='ACCEPT' and formal_gate['candidate_identity_SHA']==sha(out/'candidate_identity.json')
    campaigns=[('qualification/cli01',False)]+([] if qualification_only else [('campaign',True)])
    arms=[];qualified=[];records=collections.defaultdict(list);journals=[];unstarted=[];failures=[]
    for campaign,formal in campaigns:
        camp=out/campaign;ident=read(camp/'identity.json')
        # Qualification is before the final observational wrapper receipt; its
        # immutable original helper bindings are independently retained.
        if formal:require_identity(root,ident,candidate)
        else:
            assert ident['candidate_binary_sha256']==candidate['production_PE_SHA'] and ident['dll_sha256']==candidate['DLL_SHA']
            assert ident['source_hashes']==candidate['source_bindings']
        for launch in ident['launches']:
            d=portable(root,launch['destination']);label=dict(campaign=campaign,id=launch['id'],arm=launch['arm'],number=launch['number'],seed=launch['seed'],panel_kind=launch['panel_kind'])
            if not (d/'completion.json').exists():
                assert not d.exists(),'incomplete started arm needs explicit failure review'
                unstarted.append(dict(label,cap_seconds=launch['cap_seconds']));continue
            completion=read(d/'completion.json')
            if completion['stop_reason']!='normal_return' or completion['returncode']!=0 or not (d/'result.json').exists():
                failures.append(dict(label,completion=completion));continue
            observations=read(d/'observations.json')
            for observed in observations:
                payload=observed['payload']
                keys={'call':['full_original','native_preconditions'],'bound':['global_available','inconsistent'],'not_started':['actual_Optimize']}.get(payload['kind'],[])
                for key in keys:assert type(payload[key]) in [int,bool] and payload[key] in [0,1],('non-boolean native flag',key,payload)
                if payload['kind']=='witness_rejected':records['rejected_witnesses'].append(dict(label,payload=payload,available_seconds=observed['effective_available_seconds']))
            j=numerical.journal(root,launch,d) if formal else evidence.journal(root,launch['panel'],d)
            proof=numerical.qualify_seed(root,launch,observations,completion,ident)
            if launch['seed']==1 and proof is not None:
                assert proof==read(d/'computed_seed_scope.json'),'computed scope must rebuild from actual raw'
                records['computed_seed_scopes'].append(dict(label,**proof))
                j=computed.projected_journal(j,proof)
            j['return_sequences']={r['payload']['call']:r['payload']['sequence'] for r in observations if r['payload']['kind']=='returned'}
            ep=endpoint(root,launch,ident,d,j,formal);p=launch['panel'];check_native_parameters(launch,ep['result'],j);j['actual_frozen_seed']=launch['seed'];ep['physical']=full_fleet(root,p,ep['result'])
            if 'analytical_floor_proof' in ep:
                f=ep['analytical_floor_proof']
                records['analytical_full_domain_bounds'].append(dict(label,L=f['qualified_L'],source=f['qualified_L_source'],
                    scope='own complete original domain',native_bound=False,borrowed_ENS_bound_or_certificate=False,
                    recovery_sidecar=numerical.side_path(launch).as_posix(),recovery_sidecar_SHA=sha(root/numerical.side_path(launch)),
                    physical_floor_proof=f['physical_floor_proof'],cold_floor_proof=f['cold_floor_proof'],new_native_observation=False))
                records['rejected_raw_native_chronology'].extend(dict(label,**r) for r in ep['rejected_raw_native_chronology'])
            if not formal:
                if (d/'whole_arm_receipt.json').exists():ep['arm']['complete_seconds']=read(d/'whole_arm_receipt.json')['complete_seconds']
                else:
                    ep['arm']['qualification_complete_clock_unknown']=True
                    ep['arm']['supervisor_legacy_seconds']=ep['completion']['fully_observed_end_to_end_seconds']
                    ep['arm']['complete_seconds']=None
            journals.append((label,j,ep));arm=dict(campaign=campaign,seed=launch['seed'],panel_kind=launch['panel_kind'],**ep['arm']);(arms if formal else qualified).append(arm)
            # The original supervisor starts after the wrapper's identity checks.
            # Its total excluded pre/post work is an upper bound on the unknown
            # prelaunch offset. Add all of it for safe complete-window witness
            # bounds/checkpoints; do not pretend to know the exact offset.
            observed_window_upper=arm['complete_seconds'] if arm['complete_seconds'] is not None else arm.get('complete_seconds_upper')
            observed_window_lower=arm['complete_seconds'] if arm['complete_seconds'] is not None else arm.get('complete_seconds_lower')
            available_offset_upper=(observed_window_upper-ep['completion']['fully_observed_end_to_end_seconds']) if observed_window_upper is not None else None
            assert available_offset_upper is None or available_offset_upper>=0
            ep['availability_offset_upper']=available_offset_upper
            records['physical_fleets'].append(dict(label,**ep['physical']))
            records['physical_UBs'].append(dict(label,**ep['physical'],source='final_endpoint_own_complete_fleet',
                sequence=None,available=arm['complete_seconds'],discovery_seconds_lower=0.,
                discovery_seconds_upper=observed_window_upper,native_first_find_exact=False))
            for w in j['witnesses']:
                # Also verify complete vehicle namespace for every own UB.
                payload=next(r['payload'] for r in observations if r['payload']['sequence']==w['sequence'])
                fleet=full_fleet(root,p,payload)
                records['physical_UBs'].append(dict(label,**(w|fleet),
                    discovery_seconds_lower=0.,discovery_seconds_upper=w['available']+available_offset_upper if available_offset_upper is not None else None,
                    original_supervisor_available_seconds=w['available'],unseparated_wrapper_offset_upper_seconds=available_offset_upper,
                    discovery_clock='complete arm entry; all excluded pre/post wrapper work conservatively added' if available_offset_upper is not None else 'full clock unknown; original supervisor availability retained separately',native_first_find_exact=False))
            records['native_bounds'].extend(dict(label,**b) for b in j['bounds'])
            records['returned_native_bounds'].extend(dict(label,**b) for b in j['returned_native_proofs'])
            records['journal_failures'].extend(dict(label,**b) for b in j.get('journal_failures',[]))
            if 'native_final_without_returned_journal' in ep:
                records['native_final_without_returned_journal'].append(dict(label,**ep['native_final_without_returned_journal']))
            records['chronological_cover_provenance'].extend(dict(label,**r) for r in ep['chronological_cover'])
            for i,call in j['calls'].items():
                records['native_calls'].append(dict(label,call=i,actual_Optimize=i not in j['not_started_ids'],returned=i in j['returned_ids'],
                    returned_journal_missing=call.get('returned_journal_missing',False),
                    actual_normal_return_from_independent_rc_source=call.get('actual_normal_return_from_independent_rc_source',False),
                    model_SHA=call['model_sha256'],model_scope=call['model_scope'],full_original=call['full_original'],
                    native_bound_preconditions=call.get('raw_native_preconditions',call['native_preconditions']),
                    computed_scope_prerequisites=call.get('computed_native_prerequisites',False),
                    native_bounds_mathematically_qualified=call.get('native_bounds_mathematically_qualified',True),
                    native_log_path=portable(root,call['native_log_path']).relative_to(root).as_posix(),
                    settings=call['settings'],gini_lower=call['lower_g'],gini_upper=call['upper_g'],cutoff=call['cutoff']))
            if ep['cover']:
                for row in ep['cover']['timeline']:records['frontier'].append(dict(label,**row))
                for row in ep['cover']['leaves']:records['leaf_obligations'].append(dict(label,**row))
                for row in ep['cover'].get('scoped_proofs',[]):records['scoped_bound_proofs'].append(dict(label,**row))
            for name,data in ep['controller'].items():records[name].extend(dict(label,**r) for r in data)
            r=ep['result'];controller=ep['controller']
            model_paths=[d/'compact.lp'] if launch['arm']=='P-GRB' else sorted((d/'external/models').glob('*.lp'))
            bysha={sha(path):path for path in model_paths};typed_models={}
            for path in model_paths:
                rec,model=model_contract(root,p,path,launch['arm']);records['models'].append(dict(label,**rec));typed_models[rec['SHA']]=model
            for call_id,call in j['calls'].items():
                if call_id in j['not_started_ids']:continue
                checked=model_scope_contract(call,typed_models[call['model_sha256']],p)
                records['model_scope_bindings'].append(dict(label,call=call_id,model_SHA=call['model_sha256'],**checked))
            proof_rows=ep['controller']['controller_native']
            actual_LPs=[q for q in proof_rows if q['solve_kind']=='LP']
            assert len(actual_LPs)==len(controller['controller_LP_status'])
            LP_status_by_log={q['native_log']:s for q,s in zip(actual_LPs,controller['controller_LP_status'])}
            if launch['arm']=='P-GRB':
                proof_rows=[dict(model_sha256=sha(d/'compact.lp'),solve_kind='MIP',native_status='OPTIMAL' if r['gurobi_status']==2 else 'OPEN',native_log=str(d/'native.log'))]
                assert 'Loaded user MIP start' not in (d/'native.log').read_text(encoding='utf-8')
            for proof in proof_rows:
                model=typed_models[proof['model_sha256']];log=portable(root,proof['native_log']);text=log.read_text(encoding='utf-8')
                size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text)
                assert size and (int(size[1]),int(size[2]))==(len(model['rows']),len(model['order']))
                counts=collections.Counter(model['types'].values());native_counts=None
                if proof['solve_kind']!='LP':
                    match=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',text);assert match
                    native_counts=dict(C=int(match[1]),I=int(match[2])-int(match[3]),B=int(match[3]))
                    assert native_counts=={k:counts.get(k,0) for k in ['C','I','B']}
                    if proof['native_status']=='OPTIMAL':assert 'Optimal solution found' in text
                elif proof['native_status']=='OPTIMAL':
                    objective=re.findall(r'Optimal objective\s+([-+0-9.eE]+)',text);assert objective
                    status=LP_status_by_log[proof['native_log']]
                    if int(status['terminal_valid']):
                        assert int(status['optimal']) and close(float(objective[-1]),float(status['lower_bound']))
                elif proof['solve_kind']=='LP' and proof['native_status']=='INFEASIBLE':
                    assert 'Infeasible model' in text,'LP infeasibility requires linked actual native terminal evidence'
                records['native_type_readbacks'].append(dict(label,model_SHA=proof['model_sha256'],solve_kind=proof['solve_kind'],
                    log_path=log.relative_to(root).as_posix(),log_SHA=sha(log),rows=int(size[1]),columns=int(size[2]),
                    restored_native_types=native_counts,LP_type_evidence='original captured VType relaxation/restoration; no integer type line in native simplex log' if proof['solve_kind']=='LP' else None))
            submitted=[(path,read(path)) for path in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(path).get('submitted')]
            for digest in sorted({m['model_sha256'] for _,m in submitted}):
                assert digest in bysha
                recs=start_reader.audit_model(bysha[digest],[(path,m) for path,m in submitted if m['model_sha256']==digest], 'm-binary' if launch['arm']=='M-B' else 'off')
                records['starts'].extend(dict(label,**r) for r in recs)
            controller=ep['controller'];r=ep['result'];c=ep['completion']
            lp=sum(float(q['solver_runtime']) for q in controller['controller_native'] if q['solve_kind']=='LP')
            mip=r['gurobi_runtime'] if launch['arm']=='P-GRB' else sum(float(q['solver_runtime']) for q in controller['controller_native'] if q['solve_kind']!='LP')
            startup=r['process_elapsed_at_exact_phase_start_seconds'] if launch['arm']!='P-GRB' else 0.
            residual=c['process_wall_seconds']-startup-lp-mip;assert residual>=-1e-3
            wrapper_residual=arm['complete_seconds']-c['process_wall_seconds'] if arm['complete_seconds'] is not None else None
            assert wrapper_residual is None or wrapper_residual>=0
            records['time_partitions'].append(dict(label,complete_seconds=arm['complete_seconds'],startup_seconds=startup,
                complete_seconds_interval=arm.get('complete_seconds_interval'),later_repair_engineering_in_original_window=False,
                LP_native_inclusive_seconds=lp,MIP_native_callback_inclusive_seconds=mip,
                controller_model_mapping_raw_write_residual_seconds=residual,prelaunch_postexit_audit_crosscheck_seconds=wrapper_residual,
                AM_and_mapper_separate_timer='not measured; merged in residual',HGA_seconds_overlapping_startup=r.get('hga_wall_time_seconds'),
                supervisor_legacy_seconds=c['fully_observed_end_to_end_seconds'],nested_native_seconds_added=False,
                partition_sum=startup+lp+mip+residual+wrapper_residual if wrapper_residual is not None else None))
            kinds=collections.Counter(q['solve_kind'] for q in controller['controller_native'])
            if launch['arm']=='P-GRB':kinds['MIP']=j['started']
            covers=ep['cover']['timeline'] if ep['cover'] else []
            open_counts=[int(q['open_relevant_leaf_count']) for q in covers]
            root_LPs=[q for q in controller['controller_LP_status'] if q['leaf_id']=='L0']
            records['mechanism_summary'].append(dict(label,initial_own_physical_U=j['witnesses'][0]['F'] if j['witnesses'] else None,
                actual_native_Optimize=j['started'],LP_calls=kinds['LP'],
                partial_target_MIP_calls=kinds['CHILD_BOUND_TARGET_MIP']+kinds['NEXT_LEAF_TARGET_MIP'],
                child_bound_target_MIP_calls=kinds['CHILD_BOUND_TARGET_MIP'],next_leaf_target_MIP_calls=kinds['NEXT_LEAF_TARGET_MIP'],
                terminal_MIP_calls=kinds['MIP'],other_solve_kinds={k:v for k,v in kinds.items() if k not in ['LP','CHILD_BOUND_TARGET_MIP','NEXT_LEAF_TARGET_MIP','MIP']},
                AM_action_counts=dict(collections.Counter(q['selected_action'] for q in controller['controller_AM'])),
                actual_tree_event_counts=dict(collections.Counter(q['event'] for q in controller['controller_events'])),
                maximum_open_relevant_leaves=max(open_counts,default=0),multiple_open_relevant_leaves_observed=any(n>1 for n in open_counts),
                final_live_leaves=ep['cover']['live_leaves'] if ep['cover'] else None,
                root_LP_lower_bounds=[q['lower_bound'] for q in root_LPs],reported_integer_witnesses=len(j['witnesses']),
                no_assignment_route_oracle=True,lookahead_LP_is_committed_split=False,
                quantity_type_and_A_B_causal_contributions_reidentified=False))
            if formal:
                for checkpoint in [300,600,900,1200,1800,3600,5400]:
                    if checkpoint>p['cap_seconds']:continue
                    available=[x for x in j['trace'] if x['available']+available_offset_upper<=checkpoint]
                    assert observed_window_upper is not None and observed_window_lower is not None
                    if checkpoint>observed_window_upper:
                        records['checkpoints'].append(dict(label,seconds=checkpoint,observed=False,U=None,L=None,gap=None,
                            reason='process ended before checkpoint; no endpoint extrapolation'));continue
                    if checkpoint>observed_window_lower:
                        records['checkpoints'].append(dict(label,seconds=checkpoint,observed=False,U=None,L=None,gap=None,
                            reason='checkpoint intersects unknown exact historical completion interval'));continue
                    if not available:
                        records['checkpoints'].append(dict(label,seconds=checkpoint,observed=False,U=None,L=None,gap=None,reason='no qualified own journal evidence available'));continue
                    z=available[-1];records['checkpoints'].append(dict(label,seconds=checkpoint,observed=True,U=z['U'],L=z['L'],gap=z['U']-z['L'],
                        raw_native_L_before_rejection=z.get('raw_native_L_before_rejection'),
                        native_bound_mathematically_qualified=z.get('native_bound_mathematically_qualified',True),
                        lower_bound_source=z.get('lower_bound_source','qualified original native/complete-cover evidence'),
                        original_supervisor_available_seconds=z['available'],safe_complete_window_available_upper=z['available']+available_offset_upper,
                        reason='committed own physical evidence and independently proved own nonnegative floor; rejected native claims excluded' if 'analytical_floor_proof' in ep else 'committed own physical/native complete-scope evidence; all excluded wrapper overhead added conservatively'))
    for role in dict.fromkeys(a['id'] for a in arms):
        group=[a for a in arms if a['id']==role]
        assert max(a['L'] for a in group)<=min(a['U'] for a in group)+decision.CLOSURE_TOL
        certified=[a for a in group if a['certificate']]
        if certified:
            optimum=certified[0]['U'];assert all(close(a['U'],optimum) for a in certified)
            for label,j,ep in journals:
                if label['id']!=role or label['campaign'].startswith('qualification'):continue
                hits=[w for w in j['witnesses'] if abs(w['F']-optimum)<=decision.CLOSURE_TOL]
                endpoint_hit=abs(ep['physical']['F']-optimum)<=decision.CLOSURE_TOL
                uppers=([w['available']+ep['availability_offset_upper'] for w in hits] if ep['availability_offset_upper'] is not None else [])
                if endpoint_hit and ep['arm']['complete_seconds'] is not None:uppers.append(ep['arm']['complete_seconds'])
                records['optimal_witness_bounds'].append(dict(label,reliable_original_Fstar=optimum,
                    witnessed=bool(hits or endpoint_hit),discovery_seconds_lower=0. if uppers else None,
                    discovery_seconds_upper=min(uppers) if uppers else None,
                    native_first_find_exact=False,reason='safe interval ending at first committed verified optimal-valued own witness or complete endpoint observation' if uppers else 'optimal-valued fleet clock unknown' if hits or endpoint_hit else 'no recorded optimal-valued own fleet in window'))
    selection=None
    if not qualification_only:
        roles=read(out/'input_manifest.json')['roles']
        eligibility_record=read(out/'review/sealed_input_eligibility.json')
        assert eligibility_record['input_manifest_SHA']==sha(out/'input_manifest.json')
        eligibility=eligibility_record['eligibility']
        data={(a['id'],a['seed'],a['arm']):a for a in arms}
        for role in roles:
            for candidate_arm,control in [('M-B','P-GRB'),('M-B','ENS-C'),('ENS-C','P-GRB')]:
                key=(role['id'],0,candidate_arm);control_key=(role['id'],0,control)
                if key in data and control_key in data:records['pairs'].append(dict(id=role['id'],seed=0,panel_kind='main',**decision.pair(data[key],data[control_key])))
        for role in ['G20-C2','G50-R1','G100-R2']:
            if (role,1,'M-B') in data and (role,1,'P-GRB') in data:records['seed_pairs'].append(dict(id=role,seed=1,panel_kind='seed',**decision.pair(data[role,1,'M-B'],data[role,1,'P-GRB'])))
        if len(arms)==42:
            selection=decision.selection(arms,roles,eligibility,['formal_failures'] if failures else [])
            write(dest/'selection_decision.json',selection)
            records['seed_flips']=[dict(id=id,Seed0=selection['main_primary_pairs'][id]['classification'],Seed1=selection['seed_primary_pairs'][id]['classification'],WIN_to_LOSS=id in selection['Seed0_WIN_to_Seed1_LOSS']) for id in ['G20-C2','G50-R1','G100-R2']]
            records['stratum_gains']=[dict(dimension=dim,stratum=s,WIN_roles=wins) for dim,group in selection['stratum_WIN_roles'].items() for s,wins in group.items()]
        for comparison in records['pairs']+records['seed_pairs']:
            if comparison['classification'] in ['LOSS','MIXED']:
                delta_U=comparison['candidate_U']-comparison['control_U'];delta_L=comparison['candidate_L']-comparison['control_L']
                records['loss_decomposition'].append(dict(id=comparison['id'],seed=comparison['seed'],panel_kind=comparison['panel_kind'],candidate=comparison['candidate'],control=comparison['control'],classification=comparison['classification'],severe=comparison['severe_regression'],delta_U=delta_U,delta_L=delta_L,delta_gap=delta_U-delta_L,identity_verified=True,causal_identification=False))
    fee_rows=fee_records(out);records['fees']=fee_rows
    assert sum(r['conservative_process_starts'] for r in fee_rows)<=96 and sum(r['outer_seconds'] for r in fee_rows)<=110000
    records['failures']=failures;records['unstarted']=unstarted
    records['worst_losses']=sorted((r for r in records['pairs'] if r['classification'] in ['LOSS','MIXED']),key=lambda r:(not r['severe_regression'],r['control'],r['id']))
    table(dest/'arms.csv',arms);table(dest/'qualification_arms.csv',qualified)
    for name,data in sorted(records.items()):table(dest/(name+'.csv'),data)
    summary=dict(formal_arms=len(arms),functional_qualification_arms=len(qualified),failed_formal_arms=len(failures),
        conservative_starts=sum(r['conservative_process_starts'] for r in fee_rows),outer_solver_fee_seconds=sum(r['outer_seconds'] for r in fee_rows),
        actual_Optimize=sum(j['started'] for _,j,_ in journals),Optimize_returned=sum(j['returned'] for _,j,_ in journals),route_oracle=0,IIS=0,
        independently_proved_actual_native_returns_without_journal=sum(j.get('independently_proved_actual_native_returns',0) for _,j,_ in journals),
        actual_native_returns_including_independent_rc_sources=sum(j['returned']+j.get('independently_proved_actual_native_returns',0) for _,j,_ in journals),
        PE_SHA=candidate['production_PE_SHA'],DLL_SHA=candidate['DLL_SHA'],reader_SHA=sha(Path(__file__)),
        current_decision_reader_SHA=sha(root/'scripts/round110_decisions.py'),inherited_core_reader_SHA=sha(root/'scripts/round108_reader.py'),
        evidence_and_math_reconstruction_only=True,independent_engine_performance_rerun=False,stage=selection['stage'] if selection else None,
        table_rows={k:len(v) for k,v in sorted(records.items())})
    write(dest/'summary.json',summary);return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--qualification-only',action='store_true');parser.add_argument('--compare');a=parser.parse_args()
    print(json.dumps(rebuild(a.root,a.out,a.qualification_only),allow_nan=False))
    if a.compare:print(json.dumps(compare(a.compare,a.out),allow_nan=False))
