"""Bounded final version/lifecycle readback, no solver or producer entry."""
from round163_common import *

def run():
    assert read(OUT/'panel_complete.json')['arms']==18
    matrix=read(OUT/'matrix_frozen.json');candidate=read(OUT/'candidate_manifest.json')
    assert sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    for path,digest in candidate['source_hashes'].items():assert sha(ROOT/path)==digest,path
    for path,digest in matrix['helpers'].items():assert sha(ROOT/path)==digest,path
    for name,key in [('candidate_manifest.json','candidate_manifest_SHA256'),('input_manifest.json','input_manifest_SHA256'),
                     ('helper_manifest_Eplus.json','helper_manifest_SHA256'),('method_freeze.json','method_freeze_SHA256')]:
        assert sha(OUT/name)==matrix[key],name
    facts=[];previous_exit=None
    for group in matrix['groups']:
        launch=group['launch'];d=Path(launch['destination']);camp=OUT/group['group']
        assert sha(camp/'identity.json')==group['identity_SHA256']
        origin=read(d/'child_process_origin.json');binding=read(camp/'runtime_os_binding.json')
        assert origin['creation_from_live_OS_handle'] and origin['command']==launch['command']
        assert origin['PE_SHA']==PE_SHA and origin['source_commit']==MEASURED_CPP
        assert binding['PID']==origin['pid'] and abs(binding['CreationUnix']-origin['actual_creation_unix'])<.001
        assert binding['ProcessorAffinity']==4 and Path(binding['PE'])==PE
        assert len(binding['DLL'])==1 and Path(binding['DLL'][0]['FileName'])==Path(DLL)
        assert not binding['HashingDuringTimedSolve']
        assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
        endpoint=read(d/'round163_endpoint.json');close=read(d/'verification_closeout.json')
        for k in ['implementation_qualified','evidence_complete','performance_eligible']:assert endpoint[k] and close[k]
        assert endpoint['certificate_qualified'] and endpoint['native_proof_qualified']
        assert endpoint['PE_SHA']==PE_SHA and endpoint['DLL_SHA']==DLL_SHA
        fee=read(OUT/'fees'/f'arm_{group["position"]:03}'/'receipt.json')
        assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
        if previous_exit is not None:assert origin['actual_creation_unix']>previous_exit
        previous_exit=fee['end_unix']
        facts.append(dict(position=group['position'],id=launch['id'],method=launch['R163_method'],
            PID=origin['pid'],birth_unix=origin['actual_creation_unix'],observed_fee_exit_unix=fee['end_unix'],
            original_full_argv_SHA256=hashlib.sha256(json.dumps(origin['command'],ensure_ascii=False).encode()).hexdigest(),
            own_identity_SHA256=sha(camp/'identity.json'),live_OS_binding_SHA256=sha(camp/'runtime_os_binding.json'),
            endpoint_SHA256=sha(d/'round163_endpoint.json'),closeout_SHA256=sha(d/'verification_closeout.json'),
            input_SHA256=endpoint['input_SHA'],PE_SHA256=PE_SHA,DLL_SHA256=DLL_SHA,
            implementation_qualified=True,evidence_complete=True,performance_eligible=True))
    assert len(facts)==18
    manifest=read(OUT/'input_manifest.json');assert len(manifest['roles'])==6
    assert all(read(OUT/name)['PASS'] for name in ['main_table_novelty.json','r57_pilot_overlap.json','effective_input_novelty.json'])
    snapshots={}
    for label,commit,paths in [
        ('recipe','9d8836101',['method_freeze.json','source_recipe.json']),
        ('input','5d1e10f1a',['input_manifest.json']),
        ('matrix','830e92cc9',['matrix_frozen.json'])]:
        snapshots[label]=dict(commit=git('rev-parse',commit).decode().strip(),
            commit_unix=int(git('show','-s','--format=%ct',commit).decode().strip()),files={})
        for name in paths:
            raw=git('show',commit+':results/unified_exact_round163/'+name)
            assert raw==(OUT/name).read_bytes(),name
            snapshots[label]['files'][name]=hashlib.sha256(raw).hexdigest()
    assert snapshots['recipe']['commit_unix']<=snapshots['input']['commit_unix']<=snapshots['matrix']['commit_unix']<facts[0]['birth_unix']
    changed=git('diff','--name-only',BASE,'--','src','include','config').decode().splitlines()
    assert not changed,changed
    write(OUT/'science_identity.json',dict(PASS=True,UTC=utc(),base_commit=BASE,
        measured_CPP_commit=MEASURED_CPP,measured_PE=str(PE),measured_PE_SHA256=PE_SHA,DLL=str(DLL),DLL_SHA256=DLL_SHA,
        Gurobi_version='13.0.2',common_measured_PE_for_all=True,new_production_build=False,
        inherited_non_Gurobi_stub_difference=candidate['excluded_non_Gurobi_stub_difference'],
        prerequisite_commits=snapshots,formal_first_process_birth_unix=facts[0]['birth_unix'],
        input_manifest_SHA256=sha(OUT/'input_manifest.json'),matrix_SHA256=sha(OUT/'matrix_frozen.json'),
        method_freeze_SHA256=sha(OUT/'method_freeze.json'),candidate_manifest_SHA256=sha(OUT/'candidate_manifest.json'),
        helper_manifest_SHA256=sha(OUT/'helper_manifest_Eplus.json'),unchanged_algorithm_source_hashes=len(candidate['source_hashes']),
        unchanged_frozen_lifecycle_dependency_hashes=len(matrix['helpers']),serial_nonoverlapping_lifecycles=True,
        independent_own_H_and_sources=True,no_new_algorithm_core=True,mixed_Eplus_implementation='existing C++ method and unchanged historical Python inventory helper',
        all_18_live_OS_bindings=facts,protected_workspace=check_protected(),
        original_source_config_and_stable_defaults_unchanged=True,science_snapshot_commit='bound by following ordinary commit; no self-hash recursion',
        delivery_metadata_identity='subsequent normal commits, explicitly separated in publication.json',
        paper_recommendation_identity='decision.json; does not change released defaults',
        history_and_master_novelty_scope='manifest base/config keys sealed before panel; extra master correspondence and R57 pilot metadata readback after exposure, without redraw or producer'))
    print(json.dumps(dict(PASS=True,arms=18,source_files=len(candidate['source_hashes']),lifecycle_dependencies=len(matrix['helpers']))))

if __name__=='__main__':run()
