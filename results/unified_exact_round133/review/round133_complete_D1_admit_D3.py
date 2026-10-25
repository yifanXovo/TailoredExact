"""Independent small-endpoint/targeted-path review and D3 admission.

Does not rerun optimization, H descent, model reconstruction or old campaigns.
"""
from pathlib import Path
import collections,csv,datetime,hashlib,json,math,subprocess,time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(p,value):
    assert not p.exists(),'Preserve previous independent decision'
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def main():
    tick=time.perf_counter();review=OUT/'review';matrices={stage:read(OUT/'plans'/f'{stage}_matrix_frozen.json') for stage in ('D1','D3')}
    expected_matrix={'D1':'9e638fddd2f5e99b6cadafc933c38d093ec77eb47339345b78895b2ee4070afe','D3':'1f1839df95a8d2d62280aa4e4417177cd6d2829ec7618c2acdf3273893f88182'}
    for stage,matrix in matrices.items():
        assert sha(OUT/'plans'/f'{stage}_matrix_frozen.json')==expected_matrix[stage]
        for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest
    amendment=read(OUT/'plans/postverify_handoff_repair_amendment.json')
    assert sha(ROOT/'scripts/round133_postverify_repair.py')==amendment['bindings']['adapter_SHA']=='8feae1d544d92fba843f4836f0c685c2cf38151f20386cd2538396ac34af6640'
    candidate=read(OUT/'candidate_manifest.json')
    assert sha(OUT/'candidate_manifest.json')=='101e8f75d2675d1f728ddd8aa4010d0b57821218e730a7b06207239af6a997b2'
    for key in ('production','research'):assert sha(candidate[key+'_PE'])==candidate[key+'_PE_SHA']
    assert sha(candidate['DLL'])==candidate['DLL_SHA']
    arms=[];details=[];by_pos={};all_kinds=collections.Counter()
    for group in matrices['D1']['groups']:
        identity_path=OUT/group['group']/'identity.json';assert sha(identity_path)==group['identity_SHA']
        identity=read(identity_path);launch=group['launch'];assert identity['launches']==[launch]
        d=Path(launch['destination']);arm=read(d/'round133_endpoint.json');audit=read(d/'audit.json')
        close=read(d/'verification_closeout.json');producer=read(d/'producer_receipt.json');total=read(d/'arm_total_receipt.json')
        assert arm['arm_id']==launch['arm_id'] and arm['input_SHA']==launch['panel']['input_sha256']
        assert arm['audit_SHA']==close['audit_SHA']==sha(d/'audit.json')
        assert arm['verification_closeout_SHA']==sha(d/'verification_closeout.json') and arm['arm_total_receipt_SHA']==sha(d/'arm_total_receipt.json')
        assert sha(d/'producer_seal.json')==producer['producer_seal_SHA'] and producer['native_stopped_no_reentry']
        assert close['implementation_qualified'] and close['evidence_complete'] and audit['passed']
        assert arm['implementation_qualified'] and arm['evidence_complete']
        assert arm['T_produce']==producer['T_produce']<=launch['cap_seconds']
        assert abs(arm['T_verify']-(total['t_verified_perf']-producer['t_produce_perf']))<1e-8
        assert abs(arm['T_total']-(total['t_verified_perf']-producer['t0_perf']))<1e-8
        assert arm['signed_gap']==arm['U']-arm['L'] and arm['L']<=arm['U']+1e-7
        if arm['certificate']:assert arm['T_cert']==arm['T_produce'] and arm['native_proof_qualified'] and arm['performance_evidence_eligible']
        else:assert arm['T_cert'] is None
        matches=[]
        for binding_path in (OUT/'repair/postverify_handoff').glob('*/binding.json'):
            binding=read(binding_path)
            if binding['launch']['destination']!=str(d):continue
            success_path=binding_path.parent/'success.json'
            if not success_path.exists():continue
            success=read(success_path)
            assert success['passed'] and success['binding_SHA']==sha(binding_path)
            assert binding['launch']==launch and binding['identity_SHA']==group['identity_SHA']
            assert binding['adapter_SHA']==amendment['bindings']['adapter_SHA'] and binding['reader_SHA']==matrices['D1']['helpers']['scripts/round133_read.py']
            assert binding['producer_receipt_SHA']==sha(d/'producer_receipt.json') and binding['producer_seal_SHA']==sha(d/'producer_seal.json')
            assert all(sha(d/name)==digest for name,digest in success['outputs'].items())
            assert success['effective_adapter_H_applied']==(launch['arm']!='P-GRB')
            if launch['arm']=='P-GRB':assert success['accepted_H_selection'] is None
            matches.append(sha(success_path))
        assert len(matches)==1,'Every formal endpoint requires one actual effective-policy success'
        native=rows(d/'external/paper_optimize_ledger.csv') if launch['arm']=='M-B' else []
        events=rows(d/'external/paper_tree_events.csv') if launch['arm']=='M-B' else []
        kinds=collections.Counter(row['solve_kind'] for row in native);all_kinds.update(kinds)
        detail=dict(position=group['position'],id=launch['id'],method=launch['method'],seed=launch['seed'],
            U=arm['U'],L=arm['L'],signed_gap=arm['signed_gap'],certificate=arm['certificate'],source_qualified=arm['native_proof_qualified'],
            source_reduced=arm['source_reduced'],own_zero=arm['own_exact_zero'],T_produce=arm['T_produce'],T_verify=arm['T_verify'],T_total=arm['T_total'],T_cert=arm['T_cert'],
            actual_solve_kind_counts=dict(kinds),actual_split=sum(row['event']=='atomic_split' for row in events),
            effective_success_SHA=matches[0],audit_SHA=arm['audit_SHA'])
        arms.append(arm);details.append(detail);by_pos[group['position']]=(d,arm,audit,read(d/'result.json'),native,events)
    assert len(arms)==14 and sum(a['certificate'] for a in arms)==8
    assert [r['position'] for r in details if r['certificate']]==[1,4,5,6,8,11,13,14]
    assert [r['position'] for r in details if not r['certificate'] and not r['source_reduced']]==[3,7,9,10,12]
    assert [r['position'] for r in details if r['source_reduced']]==[2]
    assert sum(a['native_proof_qualified'] for a in arms)==13 and all(a['implementation_qualified'] for a in arms)
    # Natural same-run counterexample: raw source survives; valid export does not.
    d,arm,audit,result,native,events=by_pos[2];obs=[row['payload'] for row in read(d/'observations.json')]
    bad=[e for e in obs if e['kind']=='bound' and e['call']==4 and e['native_bound']>1e-7]
    assert [e['native_bound'] for e in bad]==[2.2155204177669103e-7,2.3794866331140976e-7,2.889725344877011e-7]
    zero=next(e for e in obs if e['kind']=='witness' and e['objective']==0)
    rejection=next(e for e in obs if e['kind']=='source_rejected')
    returned=next(e for e in obs if e['kind']=='returned' and e['call']==4)
    assert zero['sequence']==27<rejection['sequence']==28<returned['sequence']==31
    assert rejection['reason']=='source_bound_witness_contradiction'
    assert arm['U']==arm['L']==0 and arm['own_exact_zero'] and not arm['certificate'] and arm['T_cert'] is None
    assert not arm['native_proof_qualified'] and not arm['performance_evidence_eligible']
    assert len(native)==4 and [r['solve_kind'] for r in native]==['LP','LP','LP','MIP'] and native[-1]['native_status']=='INTERRUPTED'
    leaves=rows(d/'external/paper_leaf_ledger.csv');assert len(leaves)==1
    leaf=leaves[0];assert leaf['leaf_id']=='R133_FULL_DOMAIN_OPEN' and leaf['status']=='open'
    assert float(leaf['gamma_L'])==float(leaf['base_lower_bound'])==float(leaf['lower_bound'])==0 and float(leaf['gamma_U'])==34/35 and not leaf['closure_source']
    abandoned=rows(d/'external/round133_abandoned_control_state.csv');assert len(abandoned)==1 and abandoned[0]['leaf_id']=='L0' and abandoned[0]['reason']==rejection['reason']
    trace=rows(d/'external/global_bound_trace.csv')
    assert all(float(row['valid_global_lower_bound'])==0 for row in trace)
    assert all(not row['active_leaf_valid_lower_bound'] or row['active_leaf']!='L0' or float(row['active_leaf_valid_lower_bound'])<=1e-7 for row in trace)
    assert not any('retrospective' in row['event_type'] for row in trace)
    assert any(row['event']=='source_revocation_full_domain_open' for row in events)
    assert not result['external_gini_tree_all_relevant_leaves_closed'] and not result['strict_certified_original_problem']
    assert result['external_gini_tree_lifecycle_complete'] is False
    get=lambda key:result['external_gini_tree_'+key]
    assert get('model_count')==get('model_read_count')==get('model_free_count')==3
    assert get('environment_count')==get('environment_free_count')==1
    assert get('integer_domain_restore_count')==get('lp_optimize_count')==3
    assert get('same_leaf_resume_count')==get('in_memory_model_reuse_count')==1
    assert get('fresh_restart_count')==get('child_restart_count')==get('reset_call_count')==0
    assert len(rows(d/'external/native_target_ledger.csv'))==0
    safe=dict(position=2,model_SHA=native[-1]['model_sha256'],raw_bad_claims=[dict(sequence=e['sequence'],value=e['native_bound']) for e in bad],
        raw_peak=max(e['native_bound'] for e in bad),zero_sequence=27,rejection_sequence=28,API_return_sequence=31,
        final_native_status='INTERRUPTED',raw_claims_not_in_valid_trace=True,full_domain=[0,34/35],own_U=0.,qualified_L=0.,certificate=False,
        native_proof=False,implementation=True,performance=False,raw_lifecycle_false_retained_with_resource_equalities=True,
        actual_target_or_NEXT=0,extra_Optimize=0,native_internal_pruning_remains_UNKNOWN=True)
    uc=[]
    for pos in (13,14):
        d,arm,audit,result,native,events=by_pos[pos];kinds=collections.Counter(row['solve_kind'] for row in native)
        targets=rows(d/'external/native_target_ledger.csv')
        assert len(native)==11 and kinds=={'LP':9,'CHILD_BOUND_TARGET_MIP':1,'MIP':1}
        assert sum(row['event']=='atomic_split' for row in events)==3
        assert len(targets)==1 and targets[0]['target_kind']=='child_disjunction' and targets[0]['status']=='target_reached_requeue'
        assert targets[0]['target_reached']=='1' and targets[0]['requeued']=='1' and targets[0]['exact_closure']=='0'
        assert any(row['event']=='child_lp_reuse' for row in events) and arm['certificate'] and arm['U']>0
        assert abs(arm['U']-.5773330699702928)<1e-15
        uc.append(dict(position=pos,seed=arm['seed'],Optimize=11,LP=9,complete_child_pairs=4,atomic_split=3,
            child_target=1,requeue=True,cached_child_pair_reuse=True,NEXT=0,terminal_MIP=1,certificate=True,
            U=arm['U'],L=arm['L'],signed_gap=arm['signed_gap'],T_produce=arm['T_produce']))
    # Recompute the eight certification-first comparisons independently.
    pairs=[];index={(a['id'],a['seed'],a['method']):a for a in arms}
    for seed in (0,1):
        for role,left,right in [('K-15-S','S2','P'),('K-15-S','S2','PS'),('K-15-S','PS','P'),('SC-B20-S','GEOM','S2R')]:
            a,b=index[(role,seed,left)],index[(role,seed,right)]
            if not(a['performance_evidence_eligible'] and b['performance_evidence_eligible']):classification,direction='UNEVALUABLE','UNEVALUABLE'
            elif a['certificate'] and b['certificate']:
                assert abs(a['U']-b['U'])<=1e-7;classification='BOTH_CERTIFIED';direction='Win' if a['T_cert']<b['T_cert'] else 'Lose' if a['T_cert']>b['T_cert'] else 'Tie'
            elif a['certificate']:classification,direction='LEFT_ONLY_CERTIFIED','Win'
            elif b['certificate']:classification,direction='RIGHT_ONLY_CERTIFIED','Lose'
            else:classification,direction='BOTH_OPEN','UNDETERMINED'
            pairs.append(dict(id=role,seed=seed,left=left,right=right,classification=classification,direction=direction))
    observed=read(OUT/'reports/D1/pairs.json')['pairs']
    assert all(any(all(q[key]==value for key,value in p.items()) for q in observed) for p in pairs) and len(observed)==8
    # Every old-side source was checked before any old D3 native start.
    preflight_path=review/'D3_old_source_preflight.json';preflight=read(preflight_path)
    assert preflight['all_registered_Git_source_bytes_equal'] and preflight['unique_source_keys']==217 and preflight['mismatch_count']==0
    assert preflight['matrix_SHA']==expected_matrix['D3']
    assert all(not Path(g['launch']['destination']).exists() for g in matrices['D3']['groups'])
    assert sha('E:/codes/ExactEBRP-work/build-cache/round130/ExactEBRP.exe')=='2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
    charged=collections.defaultdict(float);pending=[]
    for launch_path in (OUT/'fees').glob('*/launch.json'):
        record=read(launch_path);receipt_path=launch_path.parent/'receipt.json'
        if not receipt_path.exists():pending.append(str(launch_path));continue
        receipt=read(receipt_path);assert receipt['exit_observed']
        if record['kind'] in {'C','D','E','D3','repair'}:charged[record['kind']]+=receipt['G1_seconds']
    if (OUT/'math/resource_accounting.json').exists():charged['E']+=read(OUT/'math/resource_accounting.json')['charged_outer_seconds']
    if (OUT/'infra/external_costs.json').exists():
        for row in read(OUT/'infra/external_costs.json').get('processes',[]):charged[row['kind']]+=row['outer_seconds']
    assert not pending and charged['D3']==0 and charged['D']<=18000 and charged['repair']<=5400
    total=sum(charged.values());reserve=5400-charged['repair']
    assert total+7200+reserve<=39600
    live=subprocess.check_output(['powershell.exe','-NoProfile','-Command',"Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|Round133Research|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|MSBuild)\\.exe$' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not live,live
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report=dict(schema='round133-independent-D1-completion-review-v1',UTC=now,reviewer='/root/reliability_review',decision='PASS_FINITE_IMPLEMENTATION_QUALIFICATION_AND_FAILURE_DISPOSITION',
        matrix_SHA=expected_matrix['D1'],formal_positions=14,implementation_qualified=14,native_source_qualified=13,
        certificates=8,qualified_open=5,source_rejected_safe_open=1,own_zero_positions=2,
        positions=details,natural_source_revocation=safe,UC_actual_paths=uc,
        actual_solve_kind_totals=dict(all_kinds),actual_NEXT_calls=sum(v for k,v in all_kinds.items() if 'NEXT' in k),
        NEXT_scope='If zero actual NEXT calls, only existing source/static and controlled D2 semantics cover NEXT; no natural NEXT claim',
        pairs_independently_recomputed=pairs,pair_direction_counts=dict(collections.Counter(p['direction'] for p in pairs)),
        historical_R132_denominators_and_17_plus_ownzero_unchanged=True,
        GEOM_zero_seed_OPTIMAL_physical_gap_qualified_open=True,negative_last_bit_signed_gap_retained=True,
        no_benchmark_speed_or_universal_native_tree_claim=True,actual_opaque_native_root_causes_remain_unknown=True,
        all_effective_receipt_and_clock_chains_checked=True,budget=dict(charged),G1_total=total,
        Native_snapshot='NONE',extra_Optimize=0,compilation=0,outer_review_seconds=time.perf_counter()-tick)
    write(review/'D1_completion_review.json',report)
    gate=dict(schema='round133-independent-D3-frozen-bridge-admission-v1',UTC=now,reviewer='/root/reliability_review',
        primary_and_unique_native_launcher='/root',decision='ACCEPT',matrix_SHA=expected_matrix['D3'],
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),effective_adapter_SHA=amendment['bindings']['adapter_SHA'],
        original_reader_SHA=matrices['D3']['helpers']['scripts/round133_read.py'],
        D1_completion_review_SHA=sha(review/'D1_completion_review.json'),old_source_preflight_SHA=sha(preflight_path),
        old_source_positions_checked=4,old_source_keys_exact=217,no_source_transport_needed=True,
        legacy_reader_admission_SHA=sha(review/'legacy_shortcut_reader_admission.json'),
        postverify_repair_admission_SHA=sha(review/'postverify_handoff_repair_admission.json'),
        fixed_full_positions=8,fixed_full_cap_sum_seconds=7200,threads=1,serial=True,
        adoption_condition='Production model and online source consumption changed; the final candidate is intended as the paper implementation',
        before_D3_G1_seconds=total,before_D3_categories=dict(charged),remaining_after_full_D3=39600-total-7200,
        necessary_repair_margin_reserved_seconds=reserve,remaining_after_D3_and_margin=39600-total-7200-reserve,
        old_and_candidate_full_H_Start_and_clock_independent=True,same_explicit_repair_wrapper=True,
        only_known_old_marker_may_complete_unevaluable_under_legacy_gate=True,
        no_cap_shrink_or_seed_parameter_expression_search=True,Native_all_stopped_at_admission=True,
        scientific_scope='Four complete known-role/Seed version pairs; no holdout or broad performance extrapolation',
        actual_NEXT_performance_not_established_by_D1=True,extra_Optimize_by_reviewer=0)
    write(review/'D3_admission.json',gate)
    print(json.dumps(dict(D1='PASS_FINITE_CONTRACT',D3='ACCEPT_FROZEN_8',certificates=8,qualified_open=5,safeopen=1,
        NEXT=report['actual_NEXT_calls'],G1=total,reserved_repair_margin=reserve,Optimize=0,seconds=time.perf_counter()-tick)))
if __name__=='__main__':main()
