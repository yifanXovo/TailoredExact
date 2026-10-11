"""Additional independent whole-goal audit: source delta and existing reports.

Only offline arithmetic, original bytes, already observed native logs and
physical prefix checks. No rebuild, fixture, solver, compiler or public pack.
"""
from pathlib import Path
import ast, collections, csv, datetime, difflib, hashlib, json, math, re, sys, time
ROOT=Path('E:/codes/ExactEBRP-round113');OUT=ROOT/'results/unified_exact_round113';DEST=Path(__file__).resolve().parent
csv.field_size_limit(64*1024*1024)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(name,value):(DEST/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def boolean(v):
    assert v in ['True','False',''];return None if v=='' else v=='True'
def numeric(v):return None if v=='' else float(v)
def arm(row):
    a=dict(row)
    for key in ['U','L','gap','complete_seconds']:a[key]=numeric(a[key])
    for key in ['formal_protocol_qualified','certificate','certificate_qualified','numbers_qualified']:a[key]=boolean(a[key])
    return a
def independent_pair(a,c):
    if a['formal_protocol_qualified'] is not True or c['formal_protocol_qualified'] is not True:return 'UNEVALUABLE',None
    assert a['certificate_qualified'] and c['certificate_qualified']
    assert a['numbers_qualified'] and c['numbers_qualified']
    assert a['L']<=a['U']+1e-7 and c['L']<=c['U']+1e-7
    if a['certificate'] and not c['certificate']:return 'WIN',False
    if c['certificate'] and not a['certificate']:return 'LOSS',True
    if a['certificate'] and c['certificate']:
        delta=c['complete_seconds']-a['complete_seconds'];material=max(30,.10*c['complete_seconds'])
        value='WIN' if delta>=material else 'LOSS' if -delta>=material else 'TIE'
        return value,a['complete_seconds']>=2*c['complete_seconds'] and -delta>=120
    dU=c['U']-a['U'];dg=c['gap']-a['gap'];tu=max(.001,.01*abs(c['U']));tg=max(.001,.10*abs(c['gap']))
    improve=dU>=tu or dg>=tg;worsen=-dU>=tu or -dg>=tg
    value='MIXED' if improve and worsen else 'WIN' if improve else 'LOSS' if worsen else 'TIE'
    return value,-dU>=max(.001,.05*abs(c['U'])) and -dg>=max(.005,.25*abs(c['gap']))

def main():
    tick=time.perf_counter();bindings={}
    def bind(p):
        key=p.relative_to(ROOT).as_posix();bindings[key]=sha(p);return bindings[key]
    post=read(OUT/'review/postformal01/report.json');candidate=read(OUT/'candidate_identity.json');admission=read(OUT/'review/performance_admission.json')
    assert post['decision']=='BLOCKED_FINITE_INSUFFICIENT'
    assert bind(OUT/'candidate_identity.json')==post['candidate_identity_SHA']==admission['candidate_identity_SHA']
    for name,value in {**candidate['source_bindings'],**candidate['helpers']}.items():assert bind(ROOT/name)==value,name
    assert len(candidate['source_bindings'])==206 and len(candidate['helpers'])==42
    for name in ['report.json','new_raw.json','same_H.json','zero_floor.json','cold_contradiction.json','fees.json','unstarted.json','bindings.json','supplement.json','report.md']:
        bind(OUT/'review/postformal01'/name)
    old_reader=OUT/'engineering/admitted_reader/read_round113.py';new_reader=ROOT/'scripts/read_round113.py'
    assert bind(old_reader)==admission['offline_reader_SHA']=='4c5e9f75cfda72316c7b8a88beda4dfba7dbe8de75a1728305175843e886c83b'
    assert bind(new_reader)=='7aecf8ae0a8fcad16bafa96b7739b9cd63f0c5436fa382bf421cfac8c30b7cc3'
    old_ast=ast.parse(old_reader.read_text());new_ast=ast.parse(new_reader.read_text())
    old_funcs={n.name:ast.dump(n,include_attributes=False) for n in old_ast.body if isinstance(n,ast.FunctionDef)}
    new_funcs={n.name:ast.dump(n,include_attributes=False) for n in new_ast.body if isinstance(n,ast.FunctionDef)}
    assert old_funcs.keys()==new_funcs.keys()
    changed=[name for name in old_funcs if old_funcs[name]!=new_funcs[name]]
    assert changed==['rebuild']
    difference=''.join(difflib.unified_diff(old_reader.read_text().splitlines(True),new_reader.read_text().splitlines(True),
        fromfile='admitted_reader',tofile='current_reader'))
    (DEST/'independent_reader_delta.patch').write_text(difference,encoding='utf-8')
    assert 'POSTEXIT_VALIDATION_BLOCKED' in difference and 'plain_gurobi_optimize_launch' in difference
    assert 'U=None,L=None,gap=None' in difference
    assert 'unqualified_new_formal_actual_Optimize' in difference
    summary=read(OUT/'reports_final/summary.json');conclusions=read(OUT/'reports_final/backend_conclusions.json')
    assert summary['stage']=='BLOCKED' and summary['reader_SHA']==sha(new_reader)
    assert (summary['new_formal_arm_positions'],summary['new_qualified_formal_arms'],summary['postexit_blocked_new_formal_arms'],
        summary['interrupted_new_formal_arms'],summary['unstarted_new_formal_arms'])==(8,3,1,0,4)
    assert (summary['inherited_qualified_formal_arms'],summary['layered_arm_positions'],summary['pair_positions'],summary['evaluable_pairs'],summary['unevaluable_pairs'])==(12,20,30,21,9)
    assert summary['actual_Optimize_all_observed_new_and_qualification']==22
    assert summary['formal_native_Optimize_qualified_new_arms']==9 and summary['unqualified_new_formal_actual_Optimize']==summary['unqualified_new_formal_returned']==1
    assert summary['conservative_starts']==15 and summary['outer_fee_seconds_upper']==6112.501114845276
    assert summary['prior_round112_state']=='BLOCKED' and summary['prior_partial13_endpoint_rejected']
    assert not summary['old_clock_adjusted'] and not summary['all20_measured_under_new_wrapper'] and not summary['current_reader_fee_pending']
    assert summary['primary_benchmark']=='cold P-GRB' and not summary['default_ENS_changed'] and not summary['native_rerun']
    all_arms=[arm(r) for r in rows(OUT/'reports_final/arms.csv')];lookup={(r['id'],r['arm']):r for r in all_arms}
    assert len(all_arms)==len(lookup)==20
    inherited=[a for a in all_arms if a['origin_round']=='112'];new=[a for a in all_arms if a['origin_round']=='113']
    assert len(inherited)==12 and len(new)==8
    formal_review=read(OUT/'review/postformal01/new_raw.json')
    for observed in formal_review['arms']:
        a=lookup[observed['id'],observed['arm']]
        if observed['qualified_endpoint'] is not None:
            assert a['formal_protocol_qualified']
            for key in ['U','L','gap','certificate']:assert a[key]==observed['qualified_endpoint'][key]
            assert a['complete_seconds']==observed['complete_seconds']
            assert a['performance_helper_identity']==sha(OUT/'candidate_identity.json')
        else:
            assert a['status']=='POSTEXIT_VALIDATION_BLOCKED' and a['formal_protocol_qualified'] is False
            assert all(a[k] is None for k in ['U','L','gap','certificate','complete_seconds'])
            assert a['native_Optimize']=='1'
    for a in new:
        if a['id']=='G100-R2':
            assert a['status']=='UNSTARTED' and all(a[k] is None for k in ['U','L','gap','certificate','complete_seconds'])
            assert a['failure_reason']=='CURRENT_AUTHORITY_BARRIER_FIXED_STOP'
    clock=read(OUT/'inherited_r112/clock_manifest.json');by_number={str(x['number']):x for x in clock['arms']}
    assert sha(OUT/'inherited_r112/clock_manifest.json')==admission['inherited_clock_manifest_SHA']
    assert len(clock['files'])==146 and not clock['old_raw_reaudited']
    for a in inherited:
        assert a['formal_protocol_qualified'] and a['complete_seconds']==by_number[a['number']]['original_complete_seconds']
        assert a['performance_helper_identity']==by_number[a['number']]['original_candidate_identity_SHA']
    assert lookup['R108-L48','P-S']['gap']==-9.43689570931383e-16
    pairs=rows(OUT/'reports_final/pairs.csv');pair_review=[]
    assert len(pairs)==30
    for p in pairs:
        a=lookup[p['id'],p['candidate']];c=lookup[p['id'],p['control']]
        assert a['origin_round']==c['origin_round']==p['origin_round']
        assert a['input_SHA']==c['input_SHA'] and a['cap_seconds']==c['cap_seconds']
        classification,severe=independent_pair(a,c)
        assert p['classification']==classification and boolean(p['evaluable'])==(classification!='UNEVALUABLE')
        assert boolean(p['severe_regression'])==severe
        if classification=='UNEVALUABLE':assert all(p[k]=='' for k in ['dU','dL','dGap'])
        elif p['origin_round']=='113':
            assert float(p['dU'])==a['U']-c['U'] and float(p['dL'])==a['L']-c['L'] and float(p['dGap'])==a['gap']-c['gap']
        pair_review.append(dict(id=p['id'],candidate=p['candidate'],control=p['control'],classification=classification,severe=severe,origin_round=p['origin_round']))
    assert sum(p['classification']!='UNEVALUABLE' for p in pair_review)==21
    assert len(rows(OUT/'reports_final/new_pairs.csv'))==12 and len(rows(OUT/'reports_final/inherited_pairs.csv'))==18
    for method,expected in [('ENS-C',['WIN','WIN','LOSS','WIN','UNEVALUABLE']),('M-B',['WIN','WIN','LOSS','TIE','UNEVALUABLE'])]:
        v=conclusions[method]
        assert v['status']=='INCOMPLETE_ATTRIBUTION' and v['eligible_count']==4 and v['denominator']==5
        assert [r['classification'] for r in v['five_role_vector']]==expected
        assert [r['origin_round'] for r in v['five_role_vector']]==[112,112,112,113,113]
    counts=rows(OUT/'reports_final/native_counts.csv');unqualified=rows(OUT/'reports_final/unqualified_native_calls.csv')
    assert sum(int(q['actual_Optimize']) for q in counts)==21 and sum(int(q['returned']) for q in counts)==21
    assert len(unqualified)==1 and unqualified[0]['arm']=='P-GRB' and boolean(unqualified[0]['formal_endpoint']) is False
    assert boolean(unqualified[0]['actual_Optimize']) and boolean(unqualified[0]['returned'])
    assert len(rows(OUT/'reports_final/unstarted.csv'))==4
    failed=rows(OUT/'reports_final/execution_failures.csv');assert len(failed)==1 and failed[0]['status']=='POSTEXIT_VALIDATION_BLOCKED'
    assert failed[0]['actual_Optimize']=='1' and failed[0]['returned']=='1'
    same=rows(OUT/'reports_final/same_H.csv');assert len(same)==2 and all(boolean(x['qualified']) for x in same)
    assert set(rows(OUT/'reports_final/qualification_arms.csv')[0])
    targets=rows(OUT/'reports_final/target_discovery.csv');target={r['arm']:r for r in targets}
    assert float(target['ENS-C']['first_verified_own_zero_available_upper_seconds'])==322.2456690000836
    assert float(target['ENS-C']['whole_certification_seconds'])==lookup['G50-C1','ENS-C']['complete_seconds']
    assert target['ENS-C']['first_sequence']=='13' and boolean(target['ENS-C']['unknown_native_true_first_discovery'])
    assert target['M-B']['first_verified_own_zero_available_upper_seconds']==target['P-S']['first_verified_own_zero_available_upper_seconds']==''
    initial=read(OUT/'review/postformal01/same_H.json')
    assert all(abs(v['physical']['F']-.0325201793721973)<=1e-7 for v in initial['arms'].values())
    assert all(v['seed_ids']==list(range(1,26)) and v['complete'] for v in initial['arms'].values())
    physical=read(OUT/'physical_completion.json');instance={a['arm']:a for a in physical['arms']};physical_checks=[]
    assert physical['Optimize']==0 and len(instance)==3
    final_phys={a['arm']:a['physical'] for a in formal_review['arms'] if a['full_arm_performance_qualified']}
    for method,a in instance.items():
        original=final_phys[method]
        for key in ['F','G','P','Y','maximum_duration']:assert a[key]==original[key]
        assert len(a['routes'])==4 and a['Optimize']==0 and a['maximum_duration']<=a['T']==7200
        expected_deficit=[] if method=='ENS-C' else [20]
        assert [i for i in range(1,len(a['Y'])) if a['Y'][i]!=a['D'][i]]==expected_deficit
        if method!='ENS-C':assert a['Y'][20]==8 and a['D'][20]==9 and a['F']<initial['arms'][method]['physical']['F']-1e-7
        for route in a['routes']:
            load=0;prefix=[]
            operations={q['station']:q for q in route['operations']}
            for station in route['nodes'][1:-1]:
                op=operations[station];assert int(op['pickup'])==op['pickup'] and int(op['drop'])==op['drop']
                load+=op['pickup']-op['drop'];assert 0<=load<=route['Q']==30;prefix.append(load)
            assert prefix==route['prefix_loads'] and load==route['return_load']
        physical_checks.append(dict(arm=method,all_station_targets_exact=method=='ENS-C',integer_completion_deficit_station=expected_deficit,
            physical_final_F=a['F'],own_initial_H_F=initial['arms'][method]['physical']['F'],all_assigned_capacity_prefixes_legal=True))
    changed=physical['deterministic_single_change'];assert changed['is_search'] is False and not changed['hidden_MIP_cause_identified']
    route=next(q for q in instance['M-B']['routes'] if q['vehicle']==1);ops={q['station']:q for q in route['operations']};load=0;first=None
    assert ops[20]['pickup']==4 and ops[20]['drop']==0
    for station in route['nodes'][1:-1]:
        q=ops[station];load+=q['pickup']-q['drop']-(1 if station==20 else 0)
        if load<0:first=dict(station=station,load=load);break
    assert first==changed['first_invalid_prefix']==dict(station=47,load=-1)
    sharing=read(OUT/'qualification/finite01/sharing/receipt.json');mock=read(OUT/'qualification/finite01/supervisor/receipt.json')
    assert sharing['actual_CreateFileW'] and sharing['share_READ'] and sharing['share_WRITE'] and not sharing['share_DELETE']
    assert sharing['old_replace_failure']['winerror']==5
    assert not mock['actual_OS_child_execution'] and not mock['native_execution'] and len(mock['cases'])==7 and all(q['passed'] for q in mock['cases'])
    lifecycle=read(OUT/'qualification/finite03/lifecycle/receipt.json')
    assert not lifecycle['actual_deadline_cancellation_executed'] and lifecycle['no_extra_Optimize']
    assert sum(q.get('passed',False) for q in lifecycle['cases'])==3 and sum(q.get('rejected',False) for q in lifecycle['cases'])==13
    assert all(q['synthetic_fixture'] for q in lifecycle['cases'] if q.get('passed'))
    d=OUT/'qualification/cli01/raw/02_H100_S0_P-S';publication=read(d/'progress_publication_receipt.json')
    assert publication['qualification_fault_injected'] and publication['failure_count']==publication['attempts']==1
    assert publication['first_failure']['winerror']==5 and publication['disabled']
    assert read(d/'completion.json')['stop_reason']=='normal_return'
    for name in ['03_H100_S0_ENS-C','04_H100_S0_M-B']:
        q=read(OUT/'qualification/cli01/raw'/name/'progress_publication_receipt.json');assert not q['disabled'] and q['successes']==2
    incident=read(OUT/'blocking_incident.json');assert incident['actual_Optimize']==incident['returned']==1
    assert incident['status']=='BLOCKED' and not incident['cold_formal_endpoint'] and incident['whole_seconds'] is None
    assert incident['original_consistency_tolerance']==1e-7 and incident['no_clock_synthesized'] and incident['no_automatic_retry']
    for name,h in incident['evidence'].items():assert bind(ROOT/name)==h
    reconstruction=read(OUT/'engineering/offline_reader_final02_receipt.json')
    assert reconstruction['passed'] and reconstruction['Optimize']==0 and reconstruction['reader_SHA']==sha(new_reader)
    assert reconstruction['all_other_core_fields_unchanged'] and reconstruction['no_performance_mutation']
    core_members=sorted(p.name for p in (OUT/'reports_final').iterdir() if p.is_file())
    assert all(sha(OUT/'reports_final'/name)==sha(OUT/'engineering/offline_reader_final02'/name) for name in core_members)
    doc_names=['goal.md','RESUME.md','final_report.md','contribution_evidence_map.md','geographic_bottleneck_assessment.md','next_research_decision.md',
        'numerical_policy.md','mathematical_algorithm.md','minimal_diff.md','qualification.md','reader_delta.md','blocking_incident.md',
        'blocking_incident.json','physical_completion.json','public_readme.md']
    for name in doc_names:bind(OUT/name)
    for p in (OUT/'reports_final').iterdir():
        if p.is_file():bind(p)
    for p in [OUT/'engineering/offline_reader_delta.patch',OUT/'engineering/offline_reader_final02_receipt.json',
        OUT/'qualification/summary.json',OUT/'review/performance_admission.json',ROOT/'scripts/publish_round113.py',Path(__file__)]:bind(p)
    docs={name:(OUT/name).read_text(encoding='utf-8') for name in doc_names if name.endswith('.md')}
    assert all('primal difference' in docs[n] for n in ['final_report.md','contribution_evidence_map.md'])
    assert 'branch3' in docs['next_research_decision.md'] and 'authorizes no new work' in docs['next_research_decision.md']
    assert 'No native retries' in docs['final_report.md'] and '6112.501114845276' in docs['final_report.md']
    assert 'synthetic' in docs['numerical_policy.md'] and 'unknown' in docs['geographic_bottleneck_assessment.md']
    report=dict(schema='round113-additional-independent-whole-goal-review-v1',reviewer='/root/independent_review',
        signed_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='ACCEPT_BLOCKED_SCIENTIFIC_REPORTING_PENDING_PUBLIC_RESTORE_AND_PR',
        research_terminal_state='BLOCKED_FINITE_INSUFFICIENT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
        admitted_offline_reader_SHA=sha(old_reader),current_offline_reader_SHA=sha(new_reader),
        reader_delta_only_changed_function='rebuild',unchanged_clock_identity_native_log_functions=True,
        changed_scope='Missing whole postexit failure classification, existing raw joint phase/log/return/result call count, missing reason and reporting totals',
        performance_helpers_unchanged=42,production_source_bindings_unchanged=206,
        numerical_closure_tolerance=1e-7,pair_materiality_and_severity_thresholds_unchanged=True,
        no_missing_whole_clock_or_formal_endpoint_promoted=True,normal_cold_return_observed_actual_Optimize=1,
        all_current_new_and_qualification_actual_Optimize=22,new_qualified_formal_Optimize=9,unqualified_formal_Optimize=1,
        qualified_new_endpoints=3,postexit_authority_failed_normal_return=1,fixed_unstarted=4,
        fixed_layered_arm_positions=20,qualified_old_arms=12,qualified_layered_measurements=15,
        layered_pair_positions=30,evaluable_pairs=21,unevaluable_pairs=9,new_evaluable_pairs=3,
        independent_pair_arithmetic=pair_review,backend_vectors=conclusions,physical_completion_checks=physical_checks,
        G100_zero_optimum='UNKNOWN',primary_benchmark='cold P-GRB',default='ENS-C',uniform_research_candidate='M-B',
        no_hidden_P_S_or_ENS_adoption_gate=True,no_rolewise_hybrid=True,
        preserved_F2_proof_vs_P_and_primal_vs_P_S_distinction=True,C2_primary_severe_loss_and_backend_win_preserved=True,
        retained_R111_support_and_R110_cap_exclusion=True,old_partial13_not_formal=True,old_LP_matrices_reparsed=0,
        only_current_fixed_arm_children_started=4,formal_retries=0,qualification_evidence_scope_correct=True,
        real_Win32_sharing_failure_class_verified=True,unique_historical_holder='UNKNOWN',
        source_control_flow_mock_cases=7,legal_no_Optimize_fixtures=3,illegal_no_Optimize_fixtures=13,
        source_derived_no_Optimize_fixtures_not_native_cancellation_execution=True,
        fee_totals=post['total_fees'],fees_all_closed=True,failed_slots_refunded=False,
        whole_goal_checklist=dict(retained_old_authority_and_same_round_pairs=True,optional_publication_isolation=True,
            actual_Win32_fault_with_scope_limit=True,lifecycle_declaration_start_return_cancel_distinction=True,
            own_H_Start_model_domain_scope_cover_numerical_whole_clock=True,
            G50_zero_G100_unknown_primal_proof_time_causality_distinction=True,
            primary_cold_P_and_public_ENS_tradeoffs_no_hidden_gate=True,unique_branch3_priority_and_stop=True),
        single_next_priority='branch3: qualify original cold native bound semantics against independent legal zero witness; no new work in this round',
        report_document_bindings={name:bindings[(OUT/name).relative_to(ROOT).as_posix()] for name in doc_names},
        bindings=bindings,review_engineering_seconds=time.perf_counter()-tick,
        native_starts=0,Optimize=0,compiler_starts=0,qualification_or_fixture_starts=0,performance_or_raw_mutations=0,
        pending=['Actual fresh public export and empty-root restore plus independent restored-root fieldwise review',
                 'Actual stacked Draft PR creation and remote head/base/OPEN/DRAFT/payload object checks'],
        does_not_claim_unique_numerical_root_cause=True,does_not_claim_geographic_goal_completed=True,
        does_not_validate_future_publication_or_commits=True)
    save('report.json',report)
    print(json.dumps(dict(decision=report['decision'],reader_SHA=report['current_offline_reader_SHA'],pairs=30,evaluable=21,review_engineering_seconds=report['review_engineering_seconds'])))

if __name__=='__main__':main()
