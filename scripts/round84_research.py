"""Round84 frozen ENS-C long protection and finite same-build repetition."""
import json
import os
from pathlib import Path
import subprocess
import time
import round70_affinity as affinity
import round73_native_evidence as evidence
from round83_qualify import ROOT, OUT as ROUND83, sha, write
from round76_startup import csvrows
from round75_startup import normalize, route_hash
from round78_audit import audit as replay_balanced
from round83_audit_v2 import audit as replay_exchange
import analyze_round61 as physical_module
STAGE=ROOT/'results/unified_exact_round84'
ROLE_IDS=['D6','D7','U6']
CAPS={i:3600 for i in ROLE_IDS}
ARMS={i:['P-GRB','ENS-C','K1-R'] for i in ROLE_IDS}

OUT = STAGE/'campaign'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    preflight_started=time.perf_counter()
    build = ROOT/'build/round83/v1'
    qualification = read(ROUND83/'qualification_v1.json')
    assert len(qualification['attempts']) == 3 and all(a['returncode'] == 0 for a in qualification['attempts'])
    frozen = qualification['identity']
    for name, digest in frozen['source'].items():
        assert sha(ROOT/name) == digest, name
    assert sha(ROOT/'CMakeLists.txt') == frozen['cmake_sha256']
    assert '100% tests passed, 0 tests failed out of 62' in (build/'tests.log').read_text(encoding='utf-8')
    qa=read(ROUND83/'qualification_v1_audit.json')
    assert qa['passed'] and qa['actual_optimize_calls']==165
    assert sha(build/'ExactEBRP.exe')==qa['binary_sha256']
    prior_reference=read(ROUND83/'campaign/reference/U6/launch.json')
    assert sha(build/'Round65ReferenceBuild.exe')==prior_reference['binary_sha256']
    assert read(ROUND83/'native_integration_audit.json')['passed']
    assert not (ROUND83/'qualification_active.lock').exists()
    assert not (ROUND83/'startup/active_run.lock').exists()
    assert read(ROUND83/'campaign/driver_completion.json')['all_valid']
    assert read(ROUND83/'campaign/audit.json')['all_checks_passed']
    assert read(ROUND83/'campaign/mechanism_audit.json')['all_checks_passed']
    assert not (ROUND83/'campaign/active_run.lock').exists()
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round84-ensc-long-protection-replication'
    assert not subprocess.check_output(['git','status','--porcelain','--','src','include','tests','CMakeLists.txt','scripts/round84_research.py','results/unified_exact_round84/plan.md','results/unified_exact_round84/protocol.json'],cwd=ROOT).strip(), 'Freeze source and driver first'
    startup=read(ROUND83/'startup/completion_summary.json')
    assert startup['attempted']==startup['valid']==10 and startup['optimize_calls']==0
    assert read(STAGE/'base_publication.json')['head_sha']=='131d09280a1563243d0201e68367b26baf5079c3'
    assert not OUT.exists(), 'Never repeat a formal tranche'
    OUT.mkdir()
    panel = {p['id']: p for p in read(STAGE/'protocol.json')['panel']}
    assert list(panel)==ROLE_IDS
    roles=[(panel[i],arm,False) for i in ROLE_IDS for arm in ARMS[i]]
    assert len(roles)==9 and sum(CAPS[p['id']] for p,_,_ in roles)==32400
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    references={}
    for p in [panel[i] for i in ROLE_IDS]:
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
        cap=CAPS[p['id']]
        dest = OUT/'local_raw'/f'{number:02d}_{p["id"]}_{arm}'
        command = [build/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],
            '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
            '--time-limit',cap-6,'--process-wall-time-limit',cap,'--process-shutdown-margin',3,
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
            command += ['--algorithm-preset',{'BDS-C':'research-round78-vds-balanced-descent','ENS-C':'research-round83-vds-equal-net-exchange','K1-R':'research-round65-k1-h'}[arm],
                        '--round65-witness-audit','true','--round65-hga-zero-stop','true']
        launches.append(dict(number=number,panel=p,arm=arm,forced=forced,command=list(map(str,command)),
                             destination=str(dest.relative_to(ROOT)),cap=cap,hard_stop_seconds=cap-2))
    identity = dict(source_commit=frozen['source_commit'],binary_sha256=sha(build/'ExactEBRP.exe'),
        reference_binary_sha256=sha(build/'Round65ReferenceBuild.exe'),
        source=frozen['source'],qualification_sha256=sha(ROUND83/'qualification_v1.json'),
        driver_sha256=sha(__file__),reader_sha256=sha(evidence.__file__),
        balanced_replay_sha256=sha(ROOT/'scripts/round78_audit.py'),exchange_replay_sha256=sha(ROOT/'scripts/round83_audit_v2.py'),
        closure_replay_sha256=sha(ROOT/'scripts/round76_startup.py'),
        physical_sha256=sha(evidence.physical_module.__file__),plan_sha256=sha(STAGE/'plan.md'),
        launches=launches,references=references,prior_bindings=read(STAGE/'protocol.json')['prior_bindings'],startup_summary_sha256=sha(ROUND83/'startup/completion_summary.json'),protocol_sha256=sha(STAGE/'protocol.json'),maximum_process_seconds=32400,formal_performance=True)
    write(OUT/'identity.json',identity)
    reference_wall=sum(read(p)['wall_seconds'] for p in (OUT/'reference').glob('*/completion.json'))
    write(STAGE/'full_preflight.json',dict(inherited_source=frozen['source_commit'],
        inherited_binary_sha256=identity['binary_sha256'],inherited_ctest_count=62,
        newly_executed_ctests=0,new_native_fixture_calls=0,new_build_calls=0,
        source_and_binary_revalidated=True,preflight_wall_including_reference_seconds=time.perf_counter()-preflight_started,
        reference_builds=3,reference_optimize_calls=0,reference_wall_seconds=reference_wall,
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
                    if audited['native_calls_started']==0:
                        assert result is not None and result['strict_certified_original_problem']
                        zero_check=evidence.physical_module.physical(launch['panel'],result)
                        assert zero_check['original_T_feasible'] and abs(zero_check['F'])<=1e-7
                        assert abs(result['lower_bound'])<=1e-7 and audited['LB']==0
                        assert launch['arm']!='P-GRB'
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
                            if audited['native_calls_started']:
                                assert result['external_gini_tree_backend_parameter_roundtrip_valid']
                        assert audited['UB']+1e-7>=result['upper_bound']
                        audited['normal_result_certificate']=result['strict_certified_original_problem']
                        assert result['lower_bound']<=result['upper_bound']+1e-7
                        audited['endpoint']=dict(U=result['upper_bound'],L=result['lower_bound'],gap=result['upper_bound']-result['lower_bound'],certificate=result['strict_certified_original_problem'],source='normal_finalized_physical_endpoint',status=result['status'])
                    else:
                        audited['endpoint']=dict(U=audited['UB'],L=audited['LB'],gap=audited['gap'],certificate=False,source='interrupted_committed_evidence',status=reason)
                if launch['arm'] in ['BDS-C','ENS-C']:
                    # Post-run current-witness replay; no archived route is an algorithm input.
                    folder=dest/('hga.csv.exchange' if launch['arm']=='ENS-C' else 'hga.csv.balanced')
                    initial=normalize(read(folder/'initial.json'))
                    audited['neutral']=(replay_exchange if launch['arm']=='ENS-C' else replay_balanced)(launch['panel'],folder,initial)
                    assert not read(folder/'result.json')['verification_failed']
                    startup_events=[r['payload'] for r in observations if r['payload']['kind']=='witness' and r['payload']['call']==0]
                    assert len(startup_events)==1
                    handed=normalize(startup_events[0]);final=normalize(read(folder/'final.json'))
                    final_match=route_hash(handed)==route_hash(final)
                    initial_match=route_hash(handed)==route_hash(initial)
                    assert final_match or initial_match,'Startup handoff differs from both verified controller states'
                    if not final_match:
                        assert read(folder/'initial.json')['F']-read(folder/'final.json')['F']<=1.0001e-10
                    audited['outer_handoff']=dict(final_route_match=final_match,initial_route_match=initial_match)
                    audited['all25_startup_paths_match_frozen_screen']=None
                    audited['prior_startup_binding']='No archived witness is an algorithm input. Offline same-build startup comparison follows in mechanism audit.'
                    assert 'verification_failed=1' not in '\n'.join(result.get('notes',[])) if result else True
                audited.update(passed=True,offline_replay_seconds=time.perf_counter()-audit_started)
            except Exception as exc:
                audited=dict(passed=False,error=repr(exc),offline_replay_seconds=time.perf_counter()-audit_started)
            write(dest/'audit.json',audited)
            records.append(dict(number=launch['number'],id=launch['panel']['id'],arm=launch['arm'],
                                **completion,audit=audited))
            write(OUT/'summary.json',dict(records=records,total_wall_seconds=sum(r['wall_seconds'] for r in records),
                offline_replay_seconds=sum(r['audit']['offline_replay_seconds'] for r in records),
                completed=len(records),planned=9,formal_performance=True))
            print(json.dumps(dict(number=launch['number'],id=launch['panel']['id'],arm=launch['arm'],
                wall=wall,reason=reason,passed=audited['passed'],detail=audited.get('error',
                audited.get('endpoint')))),flush=True)
            assert audited['passed'], 'Stop the formal tranche after the first validity failure; no automatic rerun'
            assert sum(r['audit'].get('native_calls_started',0) for r in records)<=250, 'Campaign resource ceiling; never an internal solver decision'
    finally:
        lock.unlink()
        write(OUT/'driver_completion.json',dict(completed=len(records),planned=9,all_valid=len(records)==9 and all(r['audit']['passed'] for r in records),ended_unix=time.time()))


if __name__=='__main__':main()
