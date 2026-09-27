"""Round77 frozen D7 complete-method screen on unchanged qualified R76 v1 bytes."""
import json
import os
from pathlib import Path
import subprocess
import time
import round70_affinity as affinity
import round73_native_evidence as evidence
from round76_qualify import ROOT, OUT as ROUND76, sha, write
from round76_startup import replay_closure, csvrows
import analyze_round61 as physical_module
STAGE=ROOT/'results/unified_exact_round77'

OUT = STAGE/'campaign'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    preflight_started=time.perf_counter()
    build = ROOT/'build/round76/v1'
    qualification = read(ROUND76/'qualification_v1.json')
    assert len(qualification['attempts']) == 3 and all(a['returncode'] == 0 for a in qualification['attempts'])
    frozen = qualification['identity']
    for name, digest in frozen['source'].items():
        assert sha(ROOT/name) == digest, name
    assert sha(ROOT/'CMakeLists.txt') == frozen['cmake_sha256']
    assert '100% tests passed, 0 tests failed out of 58' in (build/'tests.log').read_text(encoding='utf-8')
    qa=read(ROUND76/'qualification_v1_audit.json')
    assert qa['passed'] and qa['actual_optimize_calls']==129
    assert sha(build/'ExactEBRP.exe')==qa['binary_sha256']
    assert read(ROUND76/'native_integration_audit.json')['passed']
    assert not (ROUND76/'qualification_active.lock').exists()
    assert not (ROUND76/'startup/active_run.lock').exists()
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round77-jdsc-protection'
    assert not subprocess.check_output(['git','status','--porcelain','--','src','include','tests','CMakeLists.txt','scripts/round77_research.py','results/unified_exact_round77/plan.md'],cwd=ROOT).strip(), 'Freeze measured source and driver before launch'
    assert not OUT.exists(), 'Never repeat a formal tranche'
    OUT.mkdir()
    panel = {p['id']: p for p in read(ROOT/'results/unified_exact_round71/protocol.json')['panel']}
    roles=[(panel['D7'],arm,False) for arm in ['P-GRB','JDS-C','K1-R']]
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    references={}
    for p in [panel['D7']]:
        ref=OUT/'reference'/p['id'];ref.mkdir(parents=True)
        command=list(map(str,[build/'Round65ReferenceBuild.exe',p['instance_path'],p['T_seconds'],
            p['pickup_seconds'],p['drop_seconds'],p['lambda'],ref]))
        write(ref/'launch.json',dict(command=command,binary_sha256=sha(build/'Round65ReferenceBuild.exe'),
            input=p,cap=30,expected_optimize_calls=0,plan_sha256=sha(STAGE/'plan.md')))
        start=time.monotonic()
        with (ref/'stdout.log').open('w') as stdout,(ref/'stderr.log').open('w') as stderr:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=30)
        write(ref/'completion.json',dict(returncode=result.returncode,wall_seconds=time.monotonic()-start))
        assert result.returncode==0
        references[p['id']]=read(ref/'build.json')
        assert references[p['id']]['optimizer_calls']==0
    launches = []
    for number, (p,arm,forced) in enumerate(roles,1):
        assert sha(ROOT/p['instance_path']) == p['input_sha256']
        dest = OUT/'local_raw'/f'{number:02d}_{p["id"]}_{arm}'
        command = [build/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],
            '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
            '--time-limit',1194,'--process-wall-time-limit',1200,'--process-shutdown-margin',3,
            '--threads',1,'--mip-threads',1,'--gurobi-seed',0,'--gurobi-presolve',-1,
            '--method','gurobi' if arm=='P-GRB' else 'gcap-frontier',
            '--round61-candidate-mode','off','--out',dest/'result.json','--log',dest/'native.log',
            '--process-phase-ledger',dest/'phases.csv','--external-gini-artifact-dir',dest/'external',
            '--primal-heuristic-generation-log',dest/'hga.csv','--progress-log',dest/'progress.csv',
            '--native-evidence-dir',dest/'journal']
        if arm == 'P-GRB':
            command += ['--plain-baseline','--gurobi-model-export',dest/'compact.lp',
                '--round24-expected-gurobi-model-fingerprint',references[p['id']]['fingerprint'],
                '--round24-executable-sha256',sha(build/'ExactEBRP.exe'),
                '--round24-manifest-executable-sha256',sha(build/'ExactEBRP.exe')]
        else:
            command += ['--algorithm-preset',{'JDS-C':'research-round76-vds-physical-closure','K1-R':'research-round65-k1-h'}[arm],
                        '--round65-witness-audit','true','--round65-hga-zero-stop','true']
        launches.append(dict(number=number,panel=p,arm=arm,forced=forced,command=list(map(str,command)),
                             destination=str(dest.relative_to(ROOT)),cap=1200,hard_stop_seconds=1198))
    identity = dict(source_commit=frozen['source_commit'],binary_sha256=sha(build/'ExactEBRP.exe'),
        source=frozen['source'],qualification_sha256=sha(ROUND76/'qualification_v1.json'),
        driver_sha256=sha(__file__),reader_sha256=sha(evidence.__file__),
        physical_sha256=sha(evidence.physical_module.__file__),plan_sha256=sha(STAGE/'plan.md'),
        launches=launches,references=references,maximum_process_seconds=3600,formal_performance=True)
    write(OUT/'identity.json',identity)
    reference_wall=sum(read(p)['wall_seconds'] for p in (OUT/'reference').glob('*/completion.json'))
    write(STAGE/'qualification.json',dict(inherited_source=frozen['source_commit'],
        inherited_binary_sha256=identity['binary_sha256'],inherited_ctest_count=58,
        newly_executed_ctests=0,new_native_fixture_calls=0,new_build_calls=0,
        source_and_binary_revalidated=True,preflight_wall_including_reference_seconds=time.perf_counter()-preflight_started,
        reference_builds=1,reference_optimize_calls=0,reference_wall_seconds=reference_wall,
        scope='Fresh hashes and binding only; inherited tests and costs are not counted again.'))
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    records=[]
    try:
        for launch in launches:
            started=time.monotonic();dest=ROOT/launch['destination'];dest.mkdir(parents=True)
            write(OUT/'active_experiment.json',dict(number=launch['number'],arm=launch['arm'],started_unix=time.time(),driver_pid=os.getpid(),destination=launch['destination']))
            write(dest/'launch.json',launch)
            with (OUT/'processes.jsonl').open('a',encoding='utf-8') as f:
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
                if launch['arm']=='JDS-C':
                    # Archived data are used only for post-run identity/replay checks,
                    # never provided to the algorithm as a witness or bound.
                    initial=read(dest/'hga.csv.closure.csv.initial.json')
                    final=read(dest/'hga.csv.closure.csv.final.json')
                    physical_module.ROOT=ROOT
                    baseline=read(ROUND76/'startup/local_raw/D7/JDS-X/result.json')
                    endpoint=dict(final,upper_bound=final['F'])
                    audited['closure']=replay_closure(launch['panel'],dest,baseline,endpoint)
                    logical=lambda row:{k:v for k,v in row.items() if k!='elapsed_seconds'}
                    previous=ROUND76/'startup/local_raw/D7/JDS-C/hga.csv.descent.csv'
                    assert list(map(logical,csvrows(dest/'hga.csv.descent.csv')))==list(map(logical,csvrows(previous)))
                    audited['all25_startup_paths_match_frozen_screen']=True
                    assert 'verification_failed=1' not in '\n'.join(result.get('notes',[])) if result else True
                audited.update(passed=True,offline_replay_seconds=time.perf_counter()-audit_started)
            except Exception as exc:
                audited=dict(passed=False,error=repr(exc),offline_replay_seconds=time.perf_counter()-audit_started)
            write(dest/'audit.json',audited)
            records.append(dict(number=launch['number'],id=launch['panel']['id'],arm=launch['arm'],
                                **completion,audit=audited))
            write(OUT/'summary.json',dict(records=records,total_wall_seconds=sum(r['wall_seconds'] for r in records),
                offline_replay_seconds=sum(r['audit']['offline_replay_seconds'] for r in records),
                completed=len(records),planned=3,formal_performance=True))
            print(json.dumps(dict(number=launch['number'],id=launch['panel']['id'],arm=launch['arm'],
                wall=wall,reason=reason,passed=audited['passed'],detail=audited.get('error',
                audited.get('endpoint')))),flush=True)
            assert audited['passed'], 'Stop the formal tranche after the first validity failure; no automatic rerun'
            assert sum(r['audit'].get('native_calls_started',0) for r in records)<=60, 'Campaign resource ceiling; never an internal solver decision'
    finally:
        lock.unlink()
        write(OUT/'driver_completion.json',dict(completed=len(records),planned=3,all_valid=len(records)==3 and all(r['audit']['passed'] for r in records),ended_unix=time.time()))


if __name__=='__main__':main()
