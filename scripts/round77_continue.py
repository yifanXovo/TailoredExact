"""Execute only the unlaunched frozen K1-R control after independent scope repair."""
import json
import os
import subprocess
import time
from pathlib import Path
import round70_affinity as affinity
import round73_native_evidence as evidence
from round76_qualify import ROOT,OUT as ROUND76,sha,read,write
from round77_analyze import campaign_summary
STAGE=ROOT/'results/unified_exact_round77';OUT=STAGE/'campaign'

def main():
    assert not (OUT/'active_run.lock').exists()
    assert not (OUT/'continuation_identity.json').exists()
    identity=read(OUT/'identity.json');correction=read(OUT/'supervisor_scope_correction.json')
    assert correction['independent_checks_passed'] and correction['unlaunched_frozen_control_may_continue']
    assert correction['original_summary_sha256']==sha(OUT/'summary.json')
    assert sha(ROOT/'scripts/round77_research.py')==identity['driver_sha256']
    assert sha(evidence.__file__)==identity['reader_sha256']
    assert sha(evidence.physical_module.__file__)==identity['physical_sha256']
    assert sha(STAGE/'plan.md')==identity['plan_sha256']
    assert sha(ROOT/'build/round76/v1/ExactEBRP.exe')==identity['binary_sha256']
    for name,digest in identity['source'].items():assert sha(ROOT/name)==digest,name
    assert not subprocess.check_output(['git','status','--porcelain','--','scripts/round77_continue.py','scripts/round77_analyze.py'],cwd=ROOT).strip()
    launches=[identity['launches'][2]]
    assert launches[0]['number']==3 and launches[0]['arm']=='K1-R' and launches[0]['cap']==1200
    assert not (ROOT/launches[0]['destination']).exists()
    assert sha(ROOT/launches[0]['panel']['instance_path'])==launches[0]['panel']['input_sha256']
    references=identity['references']
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    write(OUT/'continuation_identity.json',dict(driver_sha256=sha(__file__),
        original_identity_sha256=sha(OUT/'identity.json'),original_summary_sha256=sha(OUT/'summary.json'),
        correction_sha256=sha(OUT/'supervisor_scope_correction.json'),
        repair_plan_sha256=sha(STAGE/'supervisor_repair_plan.md'),launches=launches,
        new_launches=1,cap_seconds=1200,completed_runs_repeated=0,additional_optimize_allocation=0))
    records=campaign_summary()['records'];assert len(records)==2 and all(r['audit']['passed'] for r in records)
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        for launch in launches:
            started=time.monotonic();dest=ROOT/launch['destination'];dest.mkdir(parents=True)
            write(OUT/'continuation_active_experiment.json',dict(number=launch['number'],arm=launch['arm'],started_unix=time.time(),driver_pid=os.getpid(),destination=launch['destination']))
            write(dest/'launch.json',launch)
            with (OUT/'continuation_processes.jsonl').open('a',encoding='utf-8') as f:
                f.write(json.dumps(dict(launch,started_unix=time.time()))+'\n')
            observations=[];reason='normal_return';has_native=False;has_bound=False;next_event=1
            child=None
            with affinity.inherited_core() as binding:
                try:
                    with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
                        child=subprocess.Popen(launch['command'],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                        child_binding=affinity.read_masks(child.pid)
                        assert child_binding['process_mask']==4
                        write(dest/'affinity.json',dict(binding=binding,child=child_binding,pid=child.pid))
                        while True:
                            while True:
                                path=dest/'journal'/f'event_{next_event}.commit'
                                if not path.exists():break
                                try:
                                    # Timestamp only AFTER complete receipt/hash read.
                                    r=evidence.receipt(path,0,launch['cap'])
                                except (AssertionError,FileNotFoundError,UnicodeError,ValueError):
                                    break  # Writer may still be inside its last commit.
                                observed=time.monotonic()-started
                                if observed>launch['cap']:break
                                r['first_observed_seconds']=observed
                                r['effective_available_seconds']=max(observed,r['data_close_seconds'])
                                observations.append(r);next_event+=1
                                e=r['payload']
                                has_native |= e['kind']=='witness' and e['source'].startswith('native_MIPSOL')
                                has_bound |= e['kind']=='bound'
                            if child.poll() is not None:break
                            if launch['forced'] and has_native and has_bound:
                                reason='forced_after_committed_native_physical_and_bound';child.kill();break
                            if time.monotonic()-started>=launch['hard_stop_seconds']:
                                reason='whole_run_hard_stop';child.kill();break
                            time.sleep(.01)
                        child.wait(timeout=max(.01,launch['cap']-(time.monotonic()-started)))
                finally:
                    if child is not None and child.poll() is None:
                        child.kill();child.wait(timeout=2)
            wall=time.monotonic()-started
            completion=dict(returncode=child.returncode,wall_seconds=wall,within_cap=wall<=launch['cap'],
                stop_reason=reason,restored=affinity.read_masks(),forced_criterion_seen=has_native and has_bound,
                observed_commits=len(observations))
            write(dest/'completion.json',completion)
            write(dest/'observations.json',observations)
            # Offline independent replay is separately charged, never subtracted
            # from the process, and cannot backdate a previously unseen receipt.
            audit_started=time.perf_counter()
            try:
                assert completion['within_cap'] and completion['restored']==binding['before']
                if launch['forced']:
                    assert reason=='forced_after_committed_native_physical_and_bound'
                    assert not (dest/'result.json').exists(), 'forced diagnosis must occur before final output'
                else:
                    assert (child.returncode==0 and reason=='normal_return') or reason=='whole_run_hard_stop'
                result=read(dest/'result.json') if reason=='normal_return' else None
                startup_exit=result is not None and result['status']=='paper_hga_global_deadline'
                if startup_exit:
                    assert launch['arm']=='K1-R' and not observations and not (dest/'journal').exists()
                    physical=evidence.physical_module.physical(launch['panel'],result)
                    assert physical['original_T_feasible'] and result['lower_bound']==0
                    assert not result['strict_certified_original_problem']
                    audited=dict(UB=physical['F'],LB=0,gap=physical['F'],native_calls_started=0,
                        native_calls_returned=0,physical_witnesses=1,native_physical_witnesses=0,
                        global_native_bound_events=0,certificate=False,normal_result_certificate=False,
                        endpoint=dict(U=physical['F'],L=0,gap=physical['F'],certificate=False,
                            source='normal_startup_deadline_physical_only',status=result['status']))
                else:
                    audited=evidence.audit(ROOT,launch['panel'],observations,identity['binary_sha256'])
                    assert audited['native_calls_started']>=1
                    # Any same-run original physical witness is a valid U, including startup.
                    assert audited['physical_witnesses']>=1
                    if reason=='normal_return':
                        assert not any(t in result['status'].lower() for t in ['failed','invalid','error','numeric']), result['status']
                        physical=evidence.physical_module.physical(launch['panel'],result)
                        assert physical['original_T_feasible']
                        if launch['arm']=='P-GRB':
                            assert result['gurobi_native_domain_audit_passed']
                            assert result['gurobi_model_fingerprint']==references[launch['panel']['id']]['fingerprint']
                        else:
                            assert result['external_gini_tree_root_coverage_valid']
                            assert result['external_gini_tree_parent_child_coverage_valid']
                            assert result['external_gini_tree_backend_parameter_roundtrip_valid']
                        assert audited['UB']+1e-7>=result['upper_bound']
                        audited['normal_result_certificate']=result['strict_certified_original_problem']
                        assert result['lower_bound']<=result['upper_bound']+1e-7
                        audited['endpoint']=dict(U=result['upper_bound'],L=result['lower_bound'],gap=result['upper_bound']-result['lower_bound'],certificate=result['strict_certified_original_problem'],source='normal_finalized_physical_endpoint',status=result['status'])
                    else:
                        audited['endpoint']=dict(U=audited['UB'],L=audited['LB'],gap=audited['gap'],certificate=False,source='interrupted_committed_evidence',status=reason)
                audited.update(passed=True,offline_replay_seconds=time.perf_counter()-audit_started)
            except Exception as exc:
                audited=dict(passed=False,error=repr(exc),offline_replay_seconds=time.perf_counter()-audit_started)
            write(dest/'audit.json',audited)
            records.append(dict(number=launch['number'],id=launch['panel']['id'],arm=launch['arm'],
                                **completion,audit=audited))
            write(OUT/'continuation_summary.json',dict(records=records,total_wall_seconds=sum(r['wall_seconds'] for r in records),
                offline_replay_seconds=sum(r['audit']['offline_replay_seconds'] for r in records),
                completed=len(records),planned=3,formal_performance=True))
            print(json.dumps(dict(number=launch['number'],id=launch['panel']['id'],arm=launch['arm'],
                wall=wall,reason=reason,passed=audited['passed'],detail=audited.get('error',
                audited.get('endpoint')))),flush=True)
            assert audited['passed'], 'Stop the formal tranche after the first validity failure; no automatic rerun'
            assert sum(r['audit'].get('native_calls_started',0) for r in records)<=60, 'Campaign resource ceiling; never an internal solver decision'
    finally:
        lock.unlink()
        write(OUT/'continuation_completion.json',dict(completed=len(records),planned=3,all_valid=len(records)==3 and all(r['audit']['passed'] for r in records),ended_unix=time.time()))


if __name__=='__main__':main()
