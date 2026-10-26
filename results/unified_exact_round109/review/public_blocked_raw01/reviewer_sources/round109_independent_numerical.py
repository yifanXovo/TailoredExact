"""Independent known-call numerical rejection, own floor and bounded timing.
Caller injects explicit-root guarded IO and the independent cold LP parser.
Never imports the primary recovery helper or creates a solver environment.
"""
from fractions import Fraction

def independent_numerical_recovery(launch,formal):
    if not formal or (launch['number'],launch['id'],launch['seed'],launch['arm'])!=(15,'G50-C1',0,'P-GRB'):return None
    d=under_root(launch['destination']);p=launch['panel']
    sidepath=OUT/'campaign/reader_recovery/main05_numerical01.json';side=obj(sidepath);contract=obj(REVIEW/'numerical_recovery_contract_review01.json')
    require(contract['decision']=='CONDITIONAL_ACCEPT_READER_ONLY_RESOLUTION','bounded independent contract review permits only exact evidence recovery')
    require(side['key']==[15,'G50-C1',0,'P-GRB'] and side['original_candidate_identity_SHA']==contract['candidate_identity_SHA']==sha(OUT/'candidate_identity.json'),'exact affected tuple and candidate binding')
    require(sha(REVIEW/'performance_admission.json')==contract['original_performance_admission_SHA'],'original signed admission untouched')
    identity=obj(OUT/'campaign/identity.json');candidate=obj(OUT/'candidate_identity.json')
    require(side['all42_native_argv']==[l['command'] for l in identity['launches']]==candidate['full_argv'],'every one of42 frozen native commands unchanged')
    require(side['production_source_bindings']==candidate['source_bindings']==identity['source_hashes'] and side['frozen_performance_helpers']==candidate['helpers']==identity['helpers'],'performance and production source identities unchanged')
    for rel,digest in side['raw_files'].items():require(sha(ROOT/rel)==digest,'unchanged exact numerical sidecar raw dependency '+rel)
    current_reader_SHA=sha(ROOT/'scripts/round109_reader.py');bridge_SHA=None
    require(side['helper_SHA']==sha(ROOT/'scripts/round109_numerical_recovery.py'),'original numerical helper remains exact bytes')
    if side['reader_SHA']!=current_reader_SHA:
        matching=[]
        for bridgepath in (OUT/'campaign/reader_recovery').glob('main06_numerical*.json'):
            bridge=obj(bridgepath)
            if bridge['current_reader_source_bindings'].get('scripts/round109_reader.py')==current_reader_SHA:matching.append((bridgepath,bridge))
        require(len(matching)==1,'exact unique new source-bound known17 compatibility bridge for original15 proof')
        bridgepath,bridge=matching[0]
        require(bridge['prior15_sidecar_SHA']==sha(sidepath) and bridge['prior15_proof']==side and bridge['original_candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and bridge['original_campaign_identity_SHA']==sha(OUT/'campaign/identity.json'),'bridge retains complete original15 proof and candidate identities')
        require(bridge['old_reader_snapshot_SHA']==side['reader_SHA']==sha(OUT/'engineering/main06_reader_source_before01/round109_reader_before.py'),'original bound reader bytes preserved as exact historical snapshot')
        for rel,digest in bridge['current_reader_source_bindings'].items():require(sha(ROOT/rel)==digest,'explicit current supplemental reader source '+rel)
        bridge_SHA=sha(bridgepath)
    else:require(side['reader_SHA']==current_reader_SHA,'original bound reader identity')
    m=model(d/'compact.lp');msha=sha(d/'compact.lp')
    require(msha==sha(reference_path(p))==sha(OUT/'campaign/reference/G50-C1/original.lp')==p['reference']['canonical_sha256']==contract['affected_evidence']['canonical_model_SHA'],'exact original frozen cold matrix on all paths')
    q=input_file(ROOT/p['input_path']);require(sha(ROOT/p['input_path'])==p['input_sha256'],'same exact affected original input')
    require(math.isfinite(p['lambda']) and p['lambda']>=0 and all(math.isfinite(w) and w>=0 for w in q['weights'][1:]) and all(t>0 for t in q['target'][1:]),'own original true-G/penalty objective full-domain nonnegative floor')
    expected_objective={'G':1.,**{f'e_{i}':p['lambda']*q['weights'][i] for i in range(1,q['V']+1)}}
    require(set(m['objective'])==set(expected_objective) and all(near(m['objective'][n],v,1e-12) for n,v in expected_objective.items()),'exact original cold physical objective semantics retained')
    require(all(math.isfinite(a) and a>=0 and math.isfinite(m['bounds'][n][0]) and m['bounds'][n][0]>=0 for n,a in m['objective'].items()),'every cold objective term and complete-domain lower bound nonnegative')
    witnesspath=REVIEW/'cross_arm_diagnosis02/exact_binary64_matrix_witness.json';witness=obj(witnesspath)
    require(sha(witnesspath)==contract['exact_cold_matrix_witness_SHA'],'immutable independently constructed counterexample vector')
    values={n:Fraction(v[0],v[1]) for n,v in witness['complete_column_values'].items()}
    require(set(values)==set(m['bounds']),'counterexample covers every actual cold column')
    for n,(lo,hi) in m['bounds'].items():
        require((not math.isfinite(lo) or values[n]>=Fraction(lo)) and (not math.isfinite(hi) or values[n]<=Fraction(hi)),'exact rational cold counterexample bound '+n)
        require(m['types'][n]=='C' or values[n].denominator==1,'exact rational original integer-domain counterexample '+n)
    for sense,rhs,terms in m['rows']:
        lhs=sum((values[n]*Fraction(a) for n,a in terms),Fraction(0));target=Fraction(rhs)
        require(lhs==target if sense=='=' else lhs<=target if sense=='<' else lhs>=target,'actual cold rational counterexample complete matrix row')
    exact_objective=sum((values[n]*Fraction(a) for n,a in m['objective'].items()),Fraction(0))
    require(exact_objective>=0 and float(exact_objective)<ZERO*2,'exact original binary64 cold model counterexample objective below closure tolerance')
    raw=obj(d/'result.json');comp=obj(d/'completion.json');observations=obj(d/'observations.json');saved=obj(d/'launch.json')
    calls=[o['payload'] for o in observations if o['payload']['kind']=='call'];returned=[o['payload'] for o in observations if o['payload']['kind']=='returned'];bounds=[o['payload'] for o in observations if o['payload']['kind']=='bound']
    require(len(calls)==len(returned)==1 and calls[0]['call']==returned[0]['call']==1 and returned[0]['return_code']==0,'one actual normal complete-original P call returned')
    call=calls[0];require(call['full_original']==call['native_preconditions']==1 and call['model_scope']=='complete_original_compact_milp' and call['model_sha256']==msha and call['settings']==dict(read_return_code=0,**SETTINGS,Seed=0),'correct full-domain scope/types/nine native settings remain distinct from numerical bound validity')
    require(saved['command']==launch['command'] and saved['panel']==p and comp['within_cap'] and comp['stop_reason']=='normal_return' and comp['returncode']==0,'all unrelated actual argv/functional/normal-return gates')
    require(raw['native_mip_status_text']=='TIME_LIMIT' and raw['strict_certified_original_problem'] is False,'native time limit and own P certificate stays false')
    require([e['sequence'] for e in bounds]==side['raw_bound_sequences']==[3,52,53] and [e['sequence'] for e in bounds if e['native_bound']>TOL]==[52,53],'all known native bound claims preserved and explicitly rejected')
    require(raw['native_mip_best_bound']==side['raw_final_native_L']==contract['affected_evidence']['raw_final_native_bound'] and float(exact_objective)+TOL<raw['native_mip_best_bound'],'strict native numerical contradiction with exact cold feasible counterexample')
    require(side['rejected_all_native_bounds_from_call'] and side['qualified_L']==0 and side['qualified_L_source']=='independently_proved_own_original_full_domain_nonnegative_floor','published claim uses separately proved own floor, never relabeled native bound')
    fee=obj(OUT/'fees/main05/receipt.json');require(sha(OUT/'fees/main05/receipt.json')==contract['original_main05_fee_receipt_SHA'] and fee['exit_code']==1 and fee['actual_native_children_with_launch']==3 and fee['conservative_process_starts']==4,'real original failure and all actual native fees retained without refund')
    prior=[obj(under_root(l['destination'])/'whole_arm_receipt.json')['complete_seconds'] for l in identity['launches'][12:14]]
    lower=comp['fully_observed_end_to_end_seconds'];raw_upper=fee['outer_seconds']-sum(prior);upper=math.ceil(raw_upper*1e6)/1e6
    require([lower,upper]==side['complete_seconds_interval']==contract['timing']['published_interval_seconds'] and math.isfinite(lower) and math.isfinite(upper) and 0<lower<=upper<=launch['cap_seconds'],'separately bounded historical execution/original audit interval within unchanged cap')
    require(not (d/'whole_arm_receipt.json').exists() and side['exact_complete_seconds'] is None and side['original_missing_whole_receipt_preserved'] and not side['later_repair_engineering_in_original_time_interval'],'no fabricated exact receipt or retroactive repair clock')
    return dict(decision='ACCEPT',call=1,model_SHA=msha,sidecar_SHA=sha(sidepath),primary_helper_SHA=side['helper_SHA'],primary_reader_SHA=current_reader_SHA,historical_reader_SHA=side['reader_SHA'],current_bridge_SHA=bridge_SHA,
        native_bound_sequences_rejected=[e['sequence'] for e in bounds],final_bound_return_sequence=returned[0]['sequence'],raw_final_native_L=raw['native_mip_best_bound'],native_bounds_mathematically_qualified=False,
        independently_qualified_own_full_domain_L=0.,cold_objective_terms_nonnegative=True,cold_objective_lower_bounds_nonnegative=True,lambda_and_original_weights_nonnegative=True,
        exact_counterexample_SHA=sha(witnesspath),exact_counterexample_objective=float(exact_objective),exact_counterexample_all_rows_and_domains_rechecked=True,
        complete_seconds=None,complete_seconds_interval=[lower,upper],raw_computed_upper=raw_upper,unmodified_native_failure_fee_SHA=sha(OUT/'fees/main05/receipt.json'),
        production_search_or_performance_helpers_changed=False,raw_global_flags_changed=False,ENS_U_or_certificate_imported_into_P=False)
