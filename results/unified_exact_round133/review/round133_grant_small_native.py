"""Bind independent, prospective gates after reviewing the frozen metadata.

This grants only the one D2 unit execution and conservative legacy reader
policy. It cannot launch a process, and does not grant D1 or D3 execution.
"""
from pathlib import Path
import datetime, hashlib, json, time

ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):
    assert not p.exists(),'Prospective admission is immutable'
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def main():
    tick=time.perf_counter();review=OUT/'review';fixed=OUT/'qualification/small_native01'
    candidate_sha='101e8f75d2675d1f728ddd8aa4010d0b57821218e730a7b06207239af6a997b2'
    d1_sha='9e638fddd2f5e99b6cadafc933c38d093ec77eb47339345b78895b2ee4070afe'
    d3_sha='1f1839df95a8d2d62280aa4e4417177cd6d2829ec7618c2acdf3273893f88182'
    unit_sha='58af0ed4accf77be62616a7d6acf79dff879f67be22467cf98b3da07695e305f'
    assert sha(OUT/'candidate_manifest.json')==candidate_sha
    assert sha(OUT/'plans/D1_matrix_frozen.json')==d1_sha
    assert sha(OUT/'plans/D3_matrix_frozen.json')==d3_sha
    assert sha(fixed/'fixture_manifest.json')==unit_sha
    unit=read(fixed/'fixture_manifest.json');protocol=read(fixed/'protocol.json');identity=read(fixed/'identity.json')
    for name,key in [('protocol.json','protocol_SHA'),('identity.json','identity_SHA'),('input.txt','input_SHA'),('inventory_oracle.json','oracle_SHA')]:
        assert sha(fixed/name)==unit[key]
    for name,digest in unit['helpers'].items():assert sha(ROOT/name)==digest
    launch=identity['launches'][0];assert protocol['launch']==launch
    assert not Path(launch['destination']).exists(),'Unit native result exists before this independent gate'
    assert unit['complete_process_cap_seconds']==45 and launch['cap_seconds']==45 and launch['hard_stop_seconds']==43
    assert unit['candidate_manifest_SHA']==candidate_sha and unit['D1_matrix_SHA']==d1_sha
    assert launch['version']=='candidate' and launch['method']=='S2' and launch['seed']==1
    d1=read(OUT/'plans/D1_matrix_frozen.json')
    template=next(g for g in d1['groups'] if g['launch']['id']=='K-15-S' and g['launch']['method']=='S2' and g['launch']['seed']==1)
    source=template['launch'];expected=[v.replace(source['destination'],launch['destination']) for v in source['command']]
    for flag,value in [('--input',str(fixed/'input.txt')),('--lambda','1'),('--T','240'),('--pickup-time','60'),('--drop-time','60'),
                       ('--time-limit','39'),('--process-wall-time-limit','45'),('--process-shutdown-margin','30'),
                       ('--gurobi-seed','1'),('--threads','1'),('--mip-threads','1')]:
        assert expected.count(flag)==1
        expected[expected.index(flag)+1]=value
    assert launch['command']==expected,'Unit differs from the reviewed complete own-H S2 template'
    assert launch['panel']['reference']['full_original_compact_reference_not_applicable']
    oracle=read(fixed/'inventory_oracle.json')
    assert oracle['exact_original_optimum']=='3/2' and oracle['enumerated_inventory_vectors']==3
    assert [(r['Y'],r['F']) for r in oracle['original_integer_inventories']]==[([0,0],'2'),([0,1],'3/2'),([1,0],'3/2')]
    assert oracle['loaded_return_route_duration_seconds']==120 and oracle['physical_horizon_seconds']==240
    reader_sha=sha(ROOT/'scripts/round133_read.py')
    assert reader_sha=='933af994bf3def115d9870c33f409709d5509a1b42f7b0546645691ce1b7c80a'
    legacy_path=OUT/'infra/legacy_scope_fixture_receipt.json';legacy=read(legacy_path)
    assert legacy['passed'] and legacy['check_count']==16 and legacy['Optimize']==0
    assert legacy['helper_hashes']['scripts/round133_read.py']==reader_sha
    faults_path=OUT/'qualification/reader_faults.json';faults=read(faults_path)
    assert faults['PASS'] and faults['reader_SHA']==reader_sha and faults['Optimize']==0
    fee=read(OUT/'fees/D2_reader_faults_03/receipt.json');assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
    transport_path=OUT/'infra/source_manifest_transport_mapping.json'
    assert sha(transport_path)=='6800dc3e82f39906dbaf088ee1d9867d906e15e490e30916b6f7e6f0bc81332a'
    checks=read(review/'frozen_matrix_identity_checks.json')
    assert checks['matrices']=={'D1':d1_sha,'D3':d3_sha} and checks['full_positions']==22
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    write(review/'legacy_shortcut_reader_admission.json',dict(schema='round133-independent-conservative-legacy-reader-admission-v1',
        UTC=now,reviewer='/root/reliability_review',primary_implementer='/root',decision='ACCEPT',
        reader_SHA=reader_sha,policy='OLD_D3_MARKER_UNEVALUABLE_AFTER_COMPLETE_AUDIT',
        D3_matrix_SHA=d3_sha,candidate_manifest_SHA=candidate_sha,legacy_fixture_SHA=sha(legacy_path),
        allowed='Only known source/mode/motif-bound ORIGINAL_E3 D3 marker receives evidence-complete UNEVALUABLE after all audits',
        forbidden='No physical-box proof, native numerical-counterexample reclassification, analytic certificate upgrade, or candidate exception',
        qualify_implementation_model_scope_native_performance_certificate=False,T_cert=None,
        D3_execution_admission=False,Optimize=0))
    write(review/'source_manifest_transport_review.json',dict(schema='round133-independent-metadata-transport-review-v1',
        UTC=now,decision='ACCEPT_METADATA_ONLY_EXACT_HASH_TRANSFORM',reviewer='/root/reliability_review',
        campaign_SHA=sha(ROOT/'scripts/round133_campaign.py'),mapping_SHA=sha(transport_path),
        independent_checks_SHA=sha(review/'frozen_matrix_identity_checks.json'),positions_checked=22,
        source_manifests_checked=4,all_original_argv_and_prereg_common_exact=True,
        actual_frozen_argv_exact_to_registered_adaptation=True,
        permitted='Pinned Git LF metadata converted to CRLF only when this exactly recovers the registered SHA; complete JSON equality checked',
        output_path_equivalence='Exact new argv retained; Windows slash/backslash equivalence checked only on adapted output path values',
        D3_order='Four complete pairs, counterbalanced prospectively by role-index plus Seed parity',
        inputs_models_raw_Start_native_settings_transformed=False,failed_initial_preflight_preserved=True,
        native_result_visible=False,Optimize=0))
    write(review/'D2_small_native_admission.json',dict(schema='round133-independent-D2-single-native-admission-v1',
        UTC=now,reviewer='/root/reliability_review',primary_implementer_and_unique_native_launcher='/root',decision='ACCEPT',
        fixture_manifest_SHA=unit_sha,candidate_manifest_SHA=candidate_sha,D1_matrix_SHA=d1_sha,D3_matrix_SHA=d3_sha,
        reader_SHA=reader_sha,common_SHA=sha(ROOT/'scripts/round133_common.py'),campaign_SHA=sha(ROOT/'scripts/round133_campaign.py'),
        small_native_script_SHA=sha(ROOT/'scripts/round133_small_native.py'),
        frozen_matrix_review_SHA=sha(review/'frozen_matrix_identity_checks.json'),
        final_reader_faults_SHA=sha(faults_path),legacy_fixture_SHA=sha(legacy_path),
        complete_process_cap_seconds=45,threads=1,native_processes=1,serial=True,
        budget='D2 within D18000; metered parent only; no nested H/LP/MIP fee added',
        exact_unit_optimum='3/2 from complete three-inventory relaxation, attained by no-op',
        independent_loaded_return_S0='Original feasible loaded return has objective2 and duration120<=240',
        no_old_or_C_solution_bound_Start_or_cache=True,
        both_complete_formal_matrices_frozen_before_any_unit_result=True,
        no_extra_MIP_NEXT_split_Optimize_or_retry_if_not_naturally_reached=True,
        not_formal_performance=True,not_lambda_sensitivity=True,D1_execution_admission=False,D3_execution_admission=False,
        next_gate='Inspect sealed unit production and verification result before formal D1 admission',
        Optimize_by_reviewer=0,outer_review_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(decision='ACCEPT_D2_UNIT_ONLY',reader=reader_sha,D1_execution=False,D3_execution=False,
        Optimize=0,seconds=time.perf_counter()-tick)))

if __name__=='__main__':main()
