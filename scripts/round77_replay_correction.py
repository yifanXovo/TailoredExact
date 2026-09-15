"""One offline reconstruction of the stopped supervisor's snapshot adapter."""
import copy
import time
import traceback
from pathlib import Path
from round76_qualify import ROOT,sha,read,write
from round76_startup import replay_closure,normalize,csvrows
from round68_start_audit import actual_vector_check,mapping
import round73_native_evidence as evidence

OUT=ROOT/'results/unified_exact_round77/campaign'
def main():
    started=time.perf_counter();destination=OUT/'supervisor_scope_correction.json'
    assert not destination.exists() and not (OUT/'active_run.lock').exists()
    frozen=read(OUT/'identity.json');original=read(OUT/'summary.json')
    assert original['completed']==2 and not (OUT/'local_raw/03_D7_K1-R').exists()
    assert sha(ROOT/'scripts/round77_research.py')==frozen['driver_sha256']
    assert sha(evidence.__file__)==frozen['reader_sha256']
    assert sha(ROOT/'build/round76/v1/ExactEBRP.exe')==frozen['binary_sha256']
    for name,digest in frozen['source'].items():assert sha(ROOT/name)==digest,name
    launch=frozen['launches'][1];done=original['records'][1];folder=ROOT/launch['destination']
    assert done['arm']=='JDS-C' and done['returncode']==0 and done['stop_reason']=='normal_return'
    assert done['wall_seconds']<=1200 and done['within_cap']
    assert not done['audit']['passed'] and 'list indices' in done['audit']['error']
    assert read(folder/'launch.json')==launch
    binding=read(folder/'affinity.json');assert done['restored']==binding['binding']['before']
    assert sha(ROOT/launch['panel']['instance_path'])==launch['panel']['input_sha256']
    records=read(folder/'observations.json')
    for row in records:
        checked=evidence.receipt(folder/'journal'/f"event_{row['sequence']}.commit",row['first_observed_seconds'],launch['cap'])
        assert checked==row
    audited=evidence.audit(ROOT,launch['panel'],records,frozen['binary_sha256'])
    assert audited['native_calls_started']>=1 and audited['physical_witnesses']>=1
    result=read(folder/'result.json')
    assert not any(word in result['status'].lower() for word in ['failed','invalid','error','numeric'])
    physical=evidence.physical_module.physical(launch['panel'],result)
    assert physical['original_T_feasible']
    for flag in ['external_gini_tree_root_coverage_valid','external_gini_tree_parent_child_coverage_valid',
                 'external_gini_tree_backend_parameter_roundtrip_valid']:assert result[flag]
    assert audited['UB']+1e-7>=result['upper_bound']
    assert result['lower_bound']<=result['upper_bound']+1e-7
    scopes={r['payload']['call']:r['payload'] for r in records if r['payload']['kind']=='call'}
    for row in records:
        e=row['payload']
        if e['kind']=='bound' and e['global_available']:
            evidence.replay_bound(scopes[e['call']],e['native_bound'],audited['witnesses']+[physical])
    audited['normal_result_certificate']=result['strict_certified_original_problem']
    audited['endpoint']=dict(U=result['upper_bound'],L=result['lower_bound'],gap=result['upper_bound']-result['lower_bound'],
        certificate=result['strict_certified_original_problem'],source='normal_finalized_physical_endpoint',status=result['status'])
    final=read(folder/'hga.csv.closure.csv.final.json')
    baseline=read(ROOT/'results/unified_exact_round76/startup/local_raw/D7/JDS-X/result.json')
    wrong=dict(final,upper_bound=final['F']);assert isinstance(wrong['routes'][0]['operations'][0],list)
    failure_started=time.perf_counter()
    try:replay_closure(launch['panel'],folder,baseline,wrong)
    except TypeError as exc:
        reproduced=dict(error=repr(exc),traceback=traceback.format_exc(),wall_seconds=time.perf_counter()-failure_started)
        assert 'route_hash(result)' in reproduced['traceback'] and 'list indices' in reproduced['error']
    else:raise AssertionError('Original adapter error was not reproduced')
    audited['closure']=replay_closure(launch['panel'],folder,baseline,normalize(wrong))
    logical=lambda row:{k:v for k,v in row.items() if k!='elapsed_seconds'}
    before=ROOT/'results/unified_exact_round76/startup/local_raw/D7/JDS-C/hga.csv.descent.csv'
    assert list(map(logical,csvrows(folder/'hga.csv.descent.csv')))==list(map(logical,csvrows(before)))
    assert 'verification_failed=1' not in '\n'.join(result.get('notes',[]))
    audited['all25_startup_paths_match_frozen_screen']=True
    mapping.run.ROOT=ROOT;mapping.audit.physical_module.ROOT=ROOT
    starts=[]
    for c in scopes.values():
        log=Path(c['native_log_path']);contents=log.read_text(encoding='utf-8',errors='replace')
        assert contents.count('Optimize a model')==1 and 'Gurobi Optimizer version 13.0.2' in contents
        if not c['native_preconditions']:continue
        meta=Path(str(log)+'.round68.start.json');data=read(meta);model=Path(c['model_path'])
        assert sha(model)==data['model_sha256']==c['model_sha256'] and data['leaf']==c['leaf']
        witness=read(folder/'external'/(data['source']+'_witness.json'))
        checked=mapping.check_model(launch['panel'],witness,model)
        assert checked['compatible_interval'] and checked['compatible_cutoff'] and checked['all_bounds_types_rows_valid']
        assert all(data[k] for k in ['mapping_complete','rows_valid','objective_valid','readback_valid','submitted'])
        assert data['status']=='accepted_by_native_log' and 'Loaded user MIP start with objective' in contents
        actual=actual_vector_check(launch['panel'],witness,model,Path(str(log)+'.round68.start.values.csv'))
        assert actual['actual_rows']==data['checked_rows']
        starts.append(dict(call=c['call'],metadata_sha256=sha(meta),independent_actual_vector=actual))
    assert starts
    elapsed=time.perf_counter()-started;assert elapsed<=30
    audited.update(passed=True,offline_replay_seconds=elapsed)
    report=dict(independent_checks_passed=True,number=2,arm='JDS-C',original_summary_sha256=sha(OUT/'summary.json'),
        original_run_audit_sha256=sha(folder/'audit.json'),original_audit=done['audit'],validated_audit=audited,
        reproduced_adapter_failure=reproduced,actual_Start_checks=starts,wall_seconds=elapsed,optimizer_calls=0,
        frozen_driver_sha256=frozen['driver_sha256'],script_sha256=sha(__file__),
        correction='Normalize only the snapshot-backed wrapper result to CLI operation dictionaries; original raw data and criteria unchanged.',
        unlaunched_frozen_control_may_continue=True)
    write(destination,report)
    print(dict(passed=True,endpoint=audited['endpoint'],calls=audited['native_calls_started'],
        witnesses=audited['physical_witnesses'],closure=audited['closure'],wall_seconds=elapsed))
if __name__=='__main__':main()
