"""Independent eight-position and four-pair bridge completion review."""
from pathlib import Path
import collections,csv,datetime,hashlib,json,math,re,time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def main():
    tick=time.perf_counter();matrix_path=OUT/'plans/D3_matrix_frozen.json';matrix=read(matrix_path)
    assert sha(matrix_path)=='1f1839df95a8d2d62280aa4e4417177cd6d2829ec7618c2acdf3273893f88182'
    gate_path=OUT/'review/D3_admission.json';gate=read(gate_path)
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(matrix_path)
    for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest
    amendment=read(OUT/'plans/postverify_handoff_repair_amendment.json')
    adapter_SHA=sha(ROOT/'scripts/round133_postverify_repair.py');assert adapter_SHA==amendment['bindings']['adapter_SHA']==gate['effective_adapter_SHA']
    results=[];by={};canonical={};raw_seed1_flags=[]
    for group in matrix['groups']:
        identity_path=OUT/group['group']/'identity.json';assert sha(identity_path)==group['identity_SHA']
        identity=read(identity_path);launch=group['launch'];assert identity['launches']==[launch]
        d=Path(launch['destination']);arm=read(d/'round133_endpoint.json');audit=read(d/'audit.json');close=read(d/'verification_closeout.json')
        producer=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json');total=read(d/'arm_total_receipt.json')
        assert arm['audit_SHA']==close['audit_SHA']==sha(d/'audit.json')
        assert arm['verification_closeout_SHA']==sha(d/'verification_closeout.json') and arm['arm_total_receipt_SHA']==sha(d/'arm_total_receipt.json')
        assert sha(d/'producer_seal.json')==producer['producer_seal_SHA'] and producer['native_stopped_no_reentry']
        assert arm['implementation_qualified'] and arm['native_proof_qualified'] and arm['performance_evidence_eligible'] and arm['certificate']
        assert close['evidence_complete'] and audit['passed'] and not audit['controlled_legacy_model_scope_unevaluable']
        assert not audit['source_rejections'] and not audit['own_source_adjudication']['rejections'] and not arm['source_reduced']
        assert arm['U']>0 and arm['L']>0 and arm['signed_gap']==arm['U']-arm['L'] and abs(arm['signed_gap'])<=1e-7
        assert arm['T_produce']==arm['T_cert']==producer['T_produce']<=launch['cap_seconds']
        assert abs(arm['T_verify']-(total['t_verified_perf']-producer['t_produce_perf']))<1e-8
        assert abs(arm['T_total']-(total['t_verified_perf']-producer['t0_perf']))<1e-8
        assert audit['full_H']['complete'] and audit['full_H']['seed_ids']==list(range(1,26)) and audit['Start_checks']
        assert audit['physical']['F']==arm['U']
        native=rows(d/'external/paper_optimize_ledger.csv');events=rows(d/'external/paper_tree_events.csv');targets=rows(d/'external/native_target_ledger.csv')
        assert [r['solve_kind'] for r in native]==['LP','LP','LP','MIP'] and len(audit['model_contracts'])==4
        assert native[-1]['native_status']=='OPTIMAL' and all(r['optimize_return_code']=='0' for r in native)
        assert not targets and not any(r['event']=='atomic_split' for r in events)
        assert len(audit['call_log_bindings'])==4
        for contract in audit['model_contracts']:
            shortcut=contract['no_improver_shortcut_check']
            assert not shortcut['model_scope_issue'] and not shortcut['identified_legacy_shortcut_rows']
            assert not shortcut['actual_constant_infeasibility_rows_zero_based']
            model=contract['model'];path=ROOT/model['path'];assert sha(path)==model['SHA']
            canonical.setdefault(model['SHA'],path)
            if launch['version']!='candidate' and launch['seed']==1:
                raw_seed1_flags.append(dict(position=group['position'],call=contract['call'],raw_preconditions=contract['raw_native_preconditions']))
        effective=[]
        for binding_path in (OUT/'repair/postverify_handoff').glob('*/binding.json'):
            binding=read(binding_path)
            if binding['launch']['destination']!=str(d):continue
            success_path=binding_path.parent/'success.json'
            if not success_path.exists():continue
            success=read(success_path)
            assert binding['launch']==launch and binding['identity_SHA']==group['identity_SHA']
            assert binding['adapter_SHA']==adapter_SHA and binding['reader_SHA']==matrix['helpers']['scripts/round133_read.py']
            assert binding['producer_receipt_SHA']==sha(d/'producer_receipt.json') and binding['producer_seal_SHA']==sha(d/'producer_seal.json')
            assert success['passed'] and success['binding_SHA']==sha(binding_path) and success['effective_adapter_H_applied']
            assert all(sha(d/name)==digest for name,digest in success['outputs'].items())
            assert success['T_produce']==arm['T_produce'] and success['Optimize']==success['native_starts']==0
            assert success['accepted_H_fleet']==audit['full_H']['fleet']
            effective.append(sha(success_path))
        assert len(effective)==1
        record=dict(position=group['position'],role=arm['id'],seed=arm['seed'],version=arm['version'],U=arm['U'],L=arm['L'],signed_gap=arm['signed_gap'],
            T_produce=arm['T_produce'],T_verify=arm['T_verify'],T_total=arm['T_total'],T_cert=arm['T_cert'],
            actual_native_statuses=[r['native_status'] for r in native],Optimize=4,LP=3,MIP=1,split=0,target=0,NEXT=0,
            implementation=True,native_source=True,certificate=True,performance=True,old_shortcut_observed=False,
            H_semantic_SHA=arm['H_semantic_SHA'],H_fleet_SHA=arm['H_fleet_SHA'],canonical_model_SHA=[r['model_sha256'] for r in native],
            effective_success_SHA=effective[0],audit_SHA=sha(d/'audit.json'))
        results.append(record);by[(arm['id'],arm['seed'],arm['version']=='candidate')]=record
    # Independently scan each actual unique current LP for the exact old empty row.
    marker=re.compile(r'^\s*[^\s:]+:\s*(?:[+-]?0(?:\.0*)?)?\s*<=\s*-1(?:\.0*)?\s*$',re.M)
    for digest,path in canonical.items():assert not marker.search(path.read_text(encoding='utf-8-sig')),str(path)
    assert len(results)==8 and len(canonical)==6
    pairs=[]
    for role in ('SC-C15-B','SC-B20-S'):
        for seed in (0,1):
            new,old=by[(role,seed,True)],by[(role,seed,False)]
            assert new['U']==old['U'] and new['L']==old['L']
            assert new['canonical_model_SHA']==old['canonical_model_SHA']
            assert new['H_semantic_SHA']==old['H_semantic_SHA'] and new['H_fleet_SHA']==old['H_fleet_SHA']
            difference=new['T_cert']-old['T_cert'];threshold=max(30.,.1*old['T_cert'])
            assert abs(difference)<threshold
            pairs.append(dict(id=role,seed=seed,left='candidate S2',right='original E3 S2',classification='BOTH_CERTIFIED',
                direction='Win' if difference<0 else 'Lose' if difference>0 else 'Tie',legacy_materiality='TIME_CLOSE',
                candidate_T_cert=new['T_cert'],original_T_cert=old['T_cert'],candidate_minus_original=difference,
                original_over_candidate_ratio=old['T_cert']/new['T_cert'],materiality_threshold=threshold,
                actual_matrices_and_complete_own_H_matched=True))
    reports=read(OUT/'reports/D3/pairs.json')['pairs'];assert len(reports)==4
    for record in pairs:
        match=next(row for row in reports if row['id']==record['id'] and row['seed']==record['seed'])
        for key in ('left','right','classification','direction','legacy_materiality'):assert match[key]==record[key]
        assert match['left_minus_right_seconds']==record['candidate_minus_original']
        assert match['right_over_left_certification_ratio']==record['original_over_candidate_ratio']
    managed=read(OUT/'reports/D3/postverify_repair_management_gate.json')
    assert managed['all_sealed_formal_arms_effective_policy_checked'] and len(managed['checked'])==8
    assert managed['matrix_SHA']==sha(matrix_path)
    for name,digest in managed['reports'].items():assert sha(OUT/'reports/D3'/name)==digest
    charged=0.;pending=[]
    for launch_path in (OUT/'fees').glob('*/launch.json'):
        receipt_path=launch_path.parent/'receipt.json';launch_record=read(launch_path)
        if not receipt_path.exists():pending.append(str(launch_path));continue
        fee=read(receipt_path);assert fee['exit_observed']
        if launch_record['kind']=='D3':charged+=fee['G1_seconds']
    assert not pending and charged<=7200
    report=dict(schema='round133-independent-D3-completion-review-v1',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reviewer='/root/reliability_review',decision='PASS_FIXED_COMPLETE_VERSION_BRIDGE',matrix_SHA=sha(matrix_path),
        candidate_manifest_SHA=matrix['candidate_manifest_SHA'],effective_adapter_SHA=adapter_SHA,
        actual_positions=8,complete_pairs=4,implementation_qualified=8,native_source_qualified=8,certificates=8,UNEVALUABLE=0,
        positions=results,pairs=pairs,directions=dict(collections.Counter(r['direction'] for r in pairs)),all_pairs_TIME_CLOSE=True,
        conditional_geometric_mean_original_over_candidate=math.exp(sum(math.log(p['original_over_candidate_ratio']) for p in pairs)/4),
        original_requested_Seed1_raw_flags_preserved=raw_seed1_flags,
        full_source_preflight_receipt_SHA=sha(OUT/'review/D3_old_source_preflight.json'),
        old_model_shortcut_branch_used=False,actual_calls_checked=32,actual_unique_canonical_matrices_checked=6,
        actual_known_artificial_empty_rows_observed=0,canonical_matrices_old_new_equal_per_pair=True,
        complete_H_and_accepted_fleet_old_new_matched_per_pair=True,
        actual_path='All8 have parent LP,2 child probes and terminal MIP; no committed split,target,NEXT',
        charged_D3_seconds=charged,cap_total_seconds=7200,nested_costs_not_added=True,
        scope_limits=['Four known role/Seed pairs are not a holdout, population speed result or broad performance stability claim',
            'These actual bridge matrices did not trigger the removed artificial-row block',
            'Root-terminal timings do not establish target/NEXT/child-cover performance; D1/D2 provide finite correctness coverage',
            'Native internal numerical causes remain unknown and historical source rejection is not restored'],
        extra_Optimize=0,compilation=0,outer_review_seconds=time.perf_counter()-tick)
    target=OUT/'review/D3_completion_review.json';assert not target.exists()
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS_FIXED_8_AND_4',directions=report['directions'],all_TIME_CLOSE=True,
        actual_unique_matrices=6,actual_old_marker=0,D3_G1=charged,Optimize=0,seconds=time.perf_counter()-tick)))
if __name__=='__main__':main()
