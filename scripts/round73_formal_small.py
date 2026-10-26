"""First frozen full-proof screen: D3 and D4 with fresh P, DS-X, JDS-X."""
import json
import os
from pathlib import Path
import subprocess
import time
import round70_affinity as affinity
import round73_native_evidence as evidence
from round73_qualify import ROOT, OUT as STAGE, sha, write

OUT = STAGE/'formal_small'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    build = ROOT/'build/round73/v6'
    qualification = read(STAGE/'qualification_v6.json')
    assert len(qualification['attempts']) == 3 and all(a['returncode'] == 0 for a in qualification['attempts'])
    frozen = qualification['identity']
    for name, digest in frozen['source'].items():
        assert sha(ROOT/name) == digest, name
    assert sha(ROOT/'CMakeLists.txt') == frozen['cmake_sha256']
    assert '100% tests passed, 0 tests failed out of 54' in (build/'tests.log').read_text(encoding='utf-8')
    assert read(STAGE/'runtime_revision/audit.json')['all_checks_passed']
    assert not OUT.exists(), 'Never repeat a formal tranche'
    OUT.mkdir()
    panel = {p['id']: p for p in read(ROOT/'results/unified_exact_round71/protocol.json')['panel']}
    roles=[(panel[i],arm,False) for i in ['D3','D4'] for arm in ['P-GRB','DS-X','JDS-X']]
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    references={'D3':read(STAGE/'runtime_revision/reference/D3/build.json')}
    for p in [panel['D4']]:
        ref=OUT/'reference'/p['id'];ref.mkdir(parents=True)
        command=list(map(str,[build/'Round65ReferenceBuild.exe',p['instance_path'],p['T_seconds'],
            p['pickup_seconds'],p['drop_seconds'],p['lambda'],ref]))
        write(ref/'launch.json',dict(command=command,binary_sha256=sha(build/'Round65ReferenceBuild.exe'),
            input=p,cap=30,expected_optimize_calls=0,plan_sha256=sha(STAGE/'formal_small_plan.md')))
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
            '--time-limit',294,'--process-wall-time-limit',300,'--process-shutdown-margin',3,
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
            command += ['--algorithm-preset',{'DS-X':'research-round71-vds-interroute-descent','JDS-X':'research-round73-vds-joint-seeded-descent'}[arm],
                        '--round65-witness-audit','true','--round65-hga-zero-stop','true']
        launches.append(dict(number=number,panel=p,arm=arm,forced=forced,command=list(map(str,command)),
                             destination=str(dest.relative_to(ROOT)),cap=300,hard_stop_seconds=298))
    identity = dict(source_commit=frozen['source_commit'],binary_sha256=sha(build/'ExactEBRP.exe'),
        source=frozen['source'],qualification_sha256=sha(STAGE/'qualification_v6.json'),
        driver_sha256=sha(__file__),reader_sha256=sha(evidence.__file__),
        physical_sha256=sha(evidence.physical_module.__file__),plan_sha256=sha(STAGE/'formal_small_plan.md'),
        launches=launches,references=references,maximum_process_seconds=1800,formal_performance=True)
    write(OUT/'identity.json',identity)
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    records=[]
    try:
        for launch in launches:
            started=time.monotonic();dest=ROOT/launch['destination'];dest.mkdir(parents=True)
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
                audited=evidence.audit(ROOT,launch['panel'],observations,identity['binary_sha256'])
                assert audited['native_calls_started']>=1
                assert audited['native_physical_witnesses']>=1
                if reason=='normal_return':
                    result=read(dest/'result.json')
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
                    if launch['panel']['id']=='microzero':
                        assert result['strict_certified_original_problem'] and abs(result['upper_bound']-5/24)<1e-7
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
            write(OUT/'summary.json',dict(records=records,total_wall_seconds=sum(r['wall_seconds'] for r in records),
                offline_replay_seconds=sum(r['audit']['offline_replay_seconds'] for r in records),
                completed=len(records),planned=6,formal_performance=True))
            print(json.dumps(dict(number=launch['number'],id=launch['panel']['id'],arm=launch['arm'],
                wall=wall,reason=reason,passed=audited['passed'],detail=audited.get('error',
                audited.get('endpoint')))),flush=True)
            assert audited['passed'], 'Stop the formal tranche after the first validity failure; no automatic rerun'
    finally:
        lock.unlink()


if __name__=='__main__':main()
