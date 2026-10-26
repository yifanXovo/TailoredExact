"""Own full-domain zero certificate after the one known failed native journal.

No primary recovery/model/physics function is imported. Guarded IO and the
inherited independent arithmetic are injected by the explicit-root raw reader.
"""
from fractions import Fraction

def independent_main06_arm(launch,identity):
    require((launch['number'],launch['id'],launch['seed'],launch['arm'])==(17,'G50-C2',0,'P-GRB'),'only the exact known failed journal tuple')
    current_reader=sha(ROOT/'scripts/round109_reader.py');matches=[]
    for path in (OUT/'campaign/reader_recovery').glob('main06_numerical*.json'):
        value=obj(path)
        if value['current_reader_source_bindings'].get('scripts/round109_reader.py')==current_reader:matches.append((path,value))
    require(len(matches)==1,'unique immutable current source-bound main06 recovery sidecar')
    sidepath,side=matches[0];contract=obj(REVIEW/'main06_recovery_contract_review01.json')
    require(contract['decision']=='CONDITIONAL_ACCEPT_READER_AND_PREPAID_SLOT_RECOVERY' and side['key']==[17,'G50-C2',0,'P-GRB'],'exact known fault and independently judged bounded recovery')
    require(side['original_candidate_identity_SHA']==contract['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and side['original_campaign_identity_SHA']==sha(OUT/'campaign/identity.json'),'same original frozen candidate/campaign identities')
    require(side['all42_native_argv']==[l['command'] for l in identity['launches']],'every native command unchanged')
    for rel,digest in side['current_reader_source_bindings'].items():require(sha(ROOT/rel)==digest,'current supplemental implementation source '+rel)
    for rel,digest in side['raw_files'].items():require(sha(ROOT/rel)==digest,'immutable main06 recovery raw dependency '+rel)
    d=under_root(launch['destination']);p=launch['panel'];raw=obj(d/'result.json');comp=obj(d/'completion.json');oldaudit=obj(d/'audit.json');actual=obj(d/'launch.json');q=input_file(ROOT/p['input_path'])
    require(actual['command']==launch['command'] and actual['panel']==p and actual['prereg_sha256']==identity['prereg_sha256'],'actual unchanged launch/input/model context')
    require(comp['returncode']==0 and comp['stop_reason']=='normal_return' and comp['within_cap'] and oldaudit['passed'] is False and oldaudit['error']=="AssertionError('full_bound_witness_inconsistency')",'normal actual process and original real audit failure retained')
    require(sha(ROOT/p['input_path'])==p['input_sha256'] and (q['V'],q['M'],q['Q'])==(p['V'],p['M'],p['Q_vector']),'same exact physical input and real heterogeneous vehicle capacities')
    ph=full_physics(q,raw['routes'],p)
    require(ph['U']==ph['G']==ph['P']==raw['objective']==raw['upper_bound']==0 and ph['final_inventories']==raw['final_inventories'] and ph['final_inventories'][1:]==q['target'][1:],'own exact complete original physical integer zero fleet; never ENS transfer')
    require(math.isfinite(p['lambda']) and p['lambda']>=0 and all(math.isfinite(w) and w>=0 for w in q['weights'][1:]) and all(t>0 for t in q['target'][1:]),'own original complete-domain objective F>=0 with original zero-denominator convention')
    m=model(d/'compact.lp');msha=sha(d/'compact.lp');require(msha==p['reference']['canonical_sha256']==sha(reference_path(p))==sha(OUT/'campaign/reference/G50-C2/original.lp'),'actual cold reference/matrix exact allpaths')
    domain=domain_contract(m,q,'P-GRB');expected={'G':1.,**{f'e_{i}':p['lambda']*q['weights'][i] for i in range(1,q['V']+1)}}
    require(set(m['objective'])==set(expected) and all(near(a,expected[n],1e-12) and math.isfinite(a) and a>=0 and m['bounds'][n][0]>=0 for n,a in m['objective'].items()),'exact original cold objective and complete-domain nonnegative objective-variable bounds')
    wp=REVIEW/'main06_diagnosis02/exact_binary64_matrix_witness.json';v=obj(wp);require(sha(wp)==contract['own_exact_cold_vector_SHA'],'actual independently constructed own-P exact cold counterexample')
    values={n:Fraction(vv[0],vv[1]) for n,vv in v['complete_column_values'].items()};require(set(values)==set(m['bounds']),'own counterexample covers every original cold column')
    for n,(lo,hi) in m['bounds'].items():require((not math.isfinite(lo) or values[n]>=Fraction(lo)) and (not math.isfinite(hi) or values[n]<=Fraction(hi)) and (m['types'][n]=='C' or values[n].denominator==1),'own exact cold column bounds/type '+n)
    for sense,rhs,terms in m['rows']:
        lhs=sum((values[n]*Fraction(a) for n,a in terms),Fraction(0));target=Fraction(rhs);require(lhs==target if sense=='=' else lhs<=target if sense=='<' else lhs>=target,'own exact cold counterexample matrix row')
    exact_objective=sum((values[n]*Fraction(a) for n,a in m['objective'].items()),Fraction(0));require(float(exact_objective)<ZERO*2,'exact cold counterpart objective below unchanged closure tolerance')
    obs=obj(d/'observations.json');calls=[];bounds=[];witnesses=[];failures=[];return_events=[];timeline=[];offset=side['complete_seconds_interval'][1]-comp['fully_observed_end_to_end_seconds'];rawL=0.
    for seq,o in enumerate(obs,1):
        e=o['payload'];bb=data(d/'journal'/f'event_{seq}.json');co=txt(d/'journal'/f'event_{seq}.commit').split()
        require(e['sequence']==o['sequence']==seq and co[0]=='NEJ1' and int(co[1])==seq and int(co[3])==len(bb) and hashlib.sha256(bb).hexdigest()==o['sha256']==co[4] and json.loads(bb)==e,'every complete original journal event and atomic commit')
        require(near(float(co[2]),o['data_close_seconds'],1e-9) and near(o['effective_available_seconds'],max(o['data_close_seconds'],o['first_observed_seconds']),1e-9),'exact retained original observation availability')
        if e['kind']=='identity':require(seq==1 and e['input_sha256']==p['input_sha256'] and (e['V'],e['M'],e['T'],e['lambda'],e['pickup_seconds'],e['drop_seconds'])==(p['V'],p['M'],p['T_seconds'],p['lambda'],p['pickup_seconds'],p['drop_seconds']),'actual identity/scenario parameters')
        elif e['kind']=='call':calls.append(e)
        elif e['kind']=='bound':bounds.append(e);rawL=max(rawL,e['native_bound'])
        elif e['kind']=='witness':
            w=full_physics(q,e['routes'],p);require(near(w['U'],e['objective']) and near(w['G'],e['G']) and near(w['P'],e['P']),'each own original integer physical journal witness')
            require(e['call']==1 and e['source']=='native_MIPSOL_verified_original_routes','own witness belongs to actual same cold call')
            w.update(sequence=seq,source=e['source'],raw_available=o['effective_available_seconds'],safe_complete_arm_available=o['effective_available_seconds']+offset);witnesses.append(w)
        elif e['kind']=='failure':failures.append(e)
        elif e['kind']=='returned':return_events.append(e)
        else:raise AssertionError(('unexpected actual failed-call event',e))
        if witnesses:
            U=min(w['U'] for w in witnesses);timeline.append(dict(sequence=seq,kind=e['kind'],raw_supervisor_available=o['effective_available_seconds'],safe_complete_arm_available=o['effective_available_seconds']+offset,own_U=U,committed_global_L=0.,signed_gap=U,raw_native_L_before_rejection=rawL,native_bound_mathematically_qualified=False,lower_bound_source='own complete original full-domain nonnegative floor'))
    require(len(obs)==142 and len(calls)==1 and not return_events and failures==[dict(schema=1,sequence=142,kind='failure',reason='full_bound_witness_inconsistency')],'failure142 remains failure, missingreturned remains absent')
    c=calls[0];require(c['call']==1 and c['full_original']==c['native_preconditions']==1 and c['model_sha256']==msha and c['settings']==dict(read_return_code=0,**SETTINGS,Seed=0),'full original integer cold call with actual nine readback settings')
    scope_contract(c,m,q)
    require([b['sequence'] for b in bounds]==[3,37] and bounds[0]['native_bound']==0 and bounds[1]['native_bound']==1.816725899087706e-6 and all(b['global_available']==1 and b['inconsistent']==0 and b['global_bound']==b['native_bound'] for b in bounds),'actual positive native claim retained and rejected without clipping or flag edits')
    require(witnesses[-1]['sequence']==141 and witnesses[-1]['U']==0 and float(exact_objective)+TOL<bounds[1]['native_bound'],'own zero witness and exact matrix counterpart expose genuine native numerical contradiction')
    for field in ['native_mip_evidence_available','native_mip_evidence_capture_complete','native_mip_lifecycle_valid','native_mip_solver_finalization_reached','native_mip_problem_freed','native_mip_environment_closed','gurobi_lifecycle_valid','gurobi_solver_finalization_reached','gurobi_native_domain_audit_passed','gurobi_native_variable_bounds_match','gurobi_native_objective_sense_match','native_mip_status_code_text_consistent']:require(raw[field] is True,'all original functional/native/domain obligations '+field)
    require(raw['native_mipopt_return_code']==raw['gurobi_optimize_return_code']==raw['native_mip_freeprob_return_code']==raw['native_mip_close_return_code']==0,'actual native return and cleanup rc0 outside missing journal')
    require(raw['native_mip_environment_count']==raw['native_mip_problem_count']==raw['native_mip_model_read_count']==raw['native_mip_mipopt_count']==raw['gurobi_optimize_count']==raw['native_mip_freeprob_count']==raw['native_mip_close_count']==1,'one actual environment/problem/model/nativecall and complete cleanup counts')
    require(raw['native_mip_status_text']=='OPTIMAL' and raw['gurobi_status']==2 and raw['native_mip_best_bound']==raw['native_mip_objective']==raw['lower_bound']==0 and raw['strict_certified_original_problem'] is True,'raw terminal0/OPTIMAL values retained as corroboration, not proof of older native-bound validity')
    nt=txt(d/'native.log');size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',nt);types=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',nt);counts=Counter(m['types'].values())
    native_types=dict(C=int(types[1]),I=int(types[2])-int(types[3]),B=int(types[3]))
    require((int(size[1]),int(size[2]))==(len(m['rows']),len(m['bounds'])) and native_types=={k:counts.get(k,0) for k in ['C','I','B']},'actual native complete original matrix size and pre-presolve real integer types')
    require('Optimal solution found (tolerance 0.00e+00)' in nt and 'Best objective 0.000000000000e+00, best bound 0.000000000000e+00' in nt and 'Loaded user MIP start' not in nt and raw['gurobi_hga_start_requested'] is False,'matching actual final nativecold log and absent Start')
    source=txt(ROOT/'src/GurobiBaseline.cpp');journal_source=txt(ROOT/'src/NativeEvidenceJournal.cpp')
    require('result.gurobi_optimize_return_code = api.optimize(model);' in source and 'result.native_mipopt_return_code = result.gurobi_optimize_return_code;' in source and 'failed_=true;' in journal_source and 'if(failed_) return;' in journal_source,'frozen source directly captures actualrc and explains missingreturned after actual journal failure')
    phases=rows(d/'phases.csv');events=[v['event'] for v in phases];needed=['plain_gurobi_optimize_launch','final_result_serialization_start','final_result_serialization_complete','process_exit']
    require(all(events.count(v)==1 for v in needed) and [events.index(v) for v in needed]==sorted(events.index(v) for v in needed) and phases[-1]['detail']=='rc=0','actual process serialization/exit after original optimize')
    fee=obj(OUT/'fees/main06/receipt.json');prior=obj(under_root(identity['launches'][15]['destination'])/'whole_arm_receipt.json');lower=comp['fully_observed_end_to_end_seconds'];upper=math.ceil((fee['outer_seconds']-prior['complete_seconds'])*1e6)/1e6
    require(fee['exit_code']==1 and fee['conservative_process_starts']==4 and fee['actual_native_children_with_launch']==2 and sha(OUT/'fees/main06/receipt.json')==contract['prepaid_coupon']['original_receipt_SHA'],'all original failed main06fees retained')
    require([lower,upper]==side['complete_seconds_interval']==contract['timing']['interval'] and 0<lower<=upper<launch['cap_seconds'] and not (d/'whole_arm_receipt.json').exists(),'honestly bounded missing fullP clock and unchangedcap, no fake receipt')
    records=[dict(call=1,leaf='',model_SHA=msha,model_path=c['model_path'],native_log_path=c['native_log_path'],actual_read_native_log=str((d/'native.log').relative_to(ROOT)),native_log_SHA=sha(d/'native.log'),native_status='OPTIMAL',solve_kind='MIP',return_sequence=None,actual_native_return_code=0,returned_journal_missing=True,native_types=native_types,returned_native_log_L=0.,native_bounds_mathematically_qualified=False)]
    result=dict(id=p['id'],seed=0,panel_kind='main',arm='P-GRB',U=0.,L=0.,gap=0.,relative_gap=None,numbers_qualified=True,certificate_qualified=True,certificate=True,complete_seconds=None,complete_seconds_interval=[lower,upper],PE_SHA=production_pe_sha(),DLL_SHA=native_dll_sha(),complete_receipt=None,normal_completion=comp,raw_status=raw['status'],raw_audit_passed=False,raw_tree_termination_reason=raw.get('external_gini_tree_failure_reason'),physical=ph,new_physical_UBs=[w for i,w in enumerate(witnesses) if i==0 or w['U']<min(x['U'] for x in witnesses[:i])],all_physical_witnesses=witnesses,total_physical_witnesses=len(witnesses),native_records=records,model_contracts=[dict(path=str((d/'compact.lp').relative_to(ROOT)),SHA=msha,**domain)],starts=[],start_attempts=[],cover=dict(independently_proved_complete_original_objective_floor=True,own_physical_zero=True,whole_improving_domain_covered=True,all_relevant_closed=True,open_relevant_leaves=0),plain_returned_final_bound=None,journal_event_count=142,chronological_native_cover_events=0,all_journal_commits_exact=True,availability_offset_seconds=offset,availability_offset_is_upper_bound_unknown_prelaunch=True,availability_exact_first_discovery=False,native_bounds_mathematically_qualified=False,native_return_journal_sequence=None,journal_failure=failures[0],independently_proved_actual_return_without_journal=True,
        independent_main06_recovery=dict(decision='ACCEPT',sidecar_SHA=sha(sidepath),helper_SHA=sha(ROOT/'scripts/round109_main06_recovery.py'),primary_reader_SHA=current_reader,certificate_source='own exact complete physical zero plus own original full-domain nonnegative objective',raw_callback_sequences_rejected=[3,37],raw_final_native_L=0.,final_native_bound_as_raw_only=True,exact_cold_vector_SHA=sha(wp),exact_cold_matrix_counterexample_objective=float(exact_objective),missing_original_returned_preserved=True,original_failed_audit_preserved=True),bindings={n:sha(d/n) for n in ['launch.json','result.json','completion.json','audit.json','observations.json','native.log','phases.csv','compact.lp']},actual_full_argv=actual['command'])
    result['checkpoints']=independent_checkpoints(result,launch,timeline)
    save(DEST/'G50-C2_seed0_P_GRB_timeline.json',timeline);save(DEST/'G50-C2_seed0_P_GRB_cover_chronology.json',[])
    milestones.append('G50-C2 P-GRB');print(json.dumps(dict(completed='G50-C2 P-GRB',U=0.,L=0.,certificate=True,complete_seconds=None,complete_seconds_interval=[lower,upper],actual_return_without_journal=True)),flush=True)
    return result,{msha:m},q
