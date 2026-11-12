"""Final bounded process/Seed/source readback, with no Optimize."""
from round164_common import *

def run():
    from round164_campaign import admission,seed_readback
    from round164_analyze import fee_label
    matrix=admission();candidate=read(OUT/'candidate_manifest.json')
    assert read(OUT/'panel_complete.json')['arms']==24
    for name,digest in candidate['source_hashes'].items():assert sha(ROOT/name)==digest,name
    assert not git('diff','--name-only',BASE,'--','src','include','config').decode().splitlines()
    assert read(OUT/'Seed0_reuse_qualification.json')['PASS']
    previous=None;facts=[];h={}
    freeze='bb69cb2f5e7d48ef71dd974edf32744728340c27'
    assert json.loads(git('show',freeze+':results/unified_exact_round164/matrix_frozen.json'))==matrix
    freeze_unix=int(git('show','-s','--format=%ct',freeze).decode().strip())
    for group in matrix['groups']:
        launch=group['launch'];d=Path(launch['destination']);camp=OUT/group['group']
        origin=read(d/'child_process_origin.json');binding=read(camp/'runtime_os_binding.json')
        fee=read(OUT/'fees'/fee_label(group['position'])/'receipt.json')
        endpoint=read(d/'round164_endpoint.json');close=read(d/'verification_closeout.json')
        assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
        assert fee['G1_seconds']==fee['outer_seconds'] and fee['separately_reported_seconds']==0
        assert origin['creation_from_live_OS_handle'] and origin['command']==launch['command']
        assert origin['source_commit']==MEASURED_CPP and origin['PE_SHA']==PE_SHA
        assert binding['PID']==origin['pid'] and abs(binding['CreationUnix']-origin['actual_creation_unix'])<.001
        assert binding['ProcessorAffinity']==4 and Path(binding['PE'])==PE
        assert len(binding['DLL'])==1 and Path(binding['DLL'][0]['FileName'])==Path(DLL)
        assert not binding['HashingDuringTimedSolve']
        assert binding['gurobi_seed']==group['arm']['gurobi_seed'] and binding['method']==group['arm']['method']
        assert origin['actual_creation_unix']>freeze_unix
        if previous is not None:assert origin['actual_creation_unix']>previous
        previous=fee['end_unix']
        actual=seed_readback(launch)
        assert all(endpoint[k] and close[k] for k in ['implementation_qualified','evidence_complete','performance_eligible'])
        assert endpoint['certificate_qualified'] and endpoint['native_proof_qualified']
        if group['arm']['method']=='B':
            assert endpoint['H_complete'];h.setdefault(launch['id'],[]).append(endpoint['H_semantic_SHA'])
            audit=read(d/'audit.json');assert audit['full_H']['complete']
        facts.append(dict(position=group['position'],**group['arm'],PID=origin['pid'],
            birth_unix=origin['actual_creation_unix'],observed_fee_exit_unix=fee['end_unix'],
            live_OS_binding_SHA256=sha(camp/'runtime_os_binding.json'),all_Native_calls=actual['Native_calls'],
            actual_settings_SHA256=sha(d/'round164_seed_audit.json'),input_SHA256=launch['panel']['input_sha256'],
            original_full_argv_SHA256=hashlib.sha256(json.dumps(origin['command'],ensure_ascii=False).encode()).hexdigest(),
            producer_seal_SHA256=sha(d/'producer_seal.json'),endpoint_SHA256=sha(d/'round164_endpoint.json'),
            verification_closeout_SHA256=sha(d/'verification_closeout.json'),fee_label=fee_label(group['position']),
            performance_eligible=True,own_new_lifecycle=True))
    assert len(facts)==24 and all(len(v)==2 and len(set(v))==1 for v in h.values())
    old=read(ROOT/'results/unified_exact_round163/reports/complete_arms.json')
    for name,hashes in h.items():
        prior=next(a for a in old if a['id']==name and a['method']=='B')
        assert hashes[0]==prior['H_semantic_SHA'],('fixed H semantics changed',name)
    write(OUT/'science_identity.json',dict(PASS=True,UTC=utc(),base_commit=BASE,preproduction_commit=freeze,
        measured_CPP_commit=MEASURED_CPP,measured_PE=str(PE),measured_PE_SHA256=PE_SHA,DLL=str(DLL),DLL_SHA256=DLL_SHA,
        Gurobi_version='13.0.2',source_hashes_unchanged=len(candidate['source_hashes']),
        common_original_production_PE_for_all=True,rebuild=False,new_algorithm_core=False,Eplus_helper_executed=False,
        all_24_positions=facts,serial_nonoverlapping_lifecycles=True,own_H_seed=20260626,
        all_three_Seed_H_semantics_equal=True,own_H_recomputed_and_paid_not_reused=True,
        input_manifest_SHA256=INPUT_MANIFEST_SHA,matrix_SHA256=sha(OUT/'matrix_frozen.json'),
        method_freeze_SHA256=sha(OUT/'method_freeze.json'),candidate_manifest_SHA256=sha(OUT/'candidate_manifest.json'),
        original_deadline_watchdog_shutdown_policy=True,scientific_reservation_margin=300,outer_fault_timeout_margin=900,
        failed_prelaunch_disposition='execution_dispositions.json',healthy_producers_repeated=0,
        historical_Seed0_eligibility='Seed0_reuse_qualification.json',protected_workspace=check_protected(),
        numerical_results_commit='following normal commit, separately pinned before table authoring',
        science_carrier_commit='subsequent immutable snapshot',delivery_head='later normal receipts, not self-referential',
        paper_main_method='B; paper conclusion and released main identity remain separate',
        released_main_defaults_changed=False,predecessor_merged=False))
    print('PASS: 24 distinct serial C++ lifecycles, all Native Seeds, own H and unchanged source/clock policy.')

if __name__=='__main__':run()
