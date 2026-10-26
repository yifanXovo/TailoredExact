"""Ten prospective startup-only runs, fresh matched controls and physical replay."""
import csv
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import analyze_round61 as physical_module
import round70_affinity as affinity
from round73_seed_diagnostic import route_hash, replay_joint
from round78_qualify import ROOT, OUT as STAGE, sha, read, write
from round76_startup import replay_closure
from round78_audit import audit as replay_balanced
OUT=STAGE/'startup'

def csvrows(path):
    with Path(path).open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))

def normalize(witness):
    result=copy.deepcopy(witness)
    for route in result['routes']:
        route.pop('duration',None)
        route['operations']=[op if isinstance(op,dict) else dict(station=op[0],pickup=op[1],drop=op[2])
                             for op in route['operations']]
    return result

def main():
    version=sys.argv[1];build=ROOT/'build/round78'/version
    q=read(STAGE/f'qualification_{version}.json')
    assert len(q['attempts'])==3 and all(a['returncode']==0 and not a['whole_tree_timeout'] for a in q['attempts'])
    assert '100% tests passed, 0 tests failed out of 60' in (build/'tests.log').read_text(encoding='utf-8')
    assert read(STAGE/'native_integration_audit.json')['passed']
    native=read(STAGE/f'qualification_{version}_audit.json')
    assert native['passed'] and native['actual_optimize_calls']<=native['allowed_optimize_calls']
    frozen=q['identity']
    for name,digest in frozen['source'].items():assert sha(ROOT/name)==digest,name
    assert sha(ROOT/'CMakeLists.txt')==frozen['cmake_sha256']
    assert sha(STAGE/'plan.md')==frozen['plan_sha256']
    assert sha(STAGE/'implementation_plan.md')==frozen['implementation_plan_sha256']
    assert not (STAGE/'qualification_active.lock').exists()
    assert not OUT.exists(),'A new startup tranche must never replace prior outputs'
    OUT.mkdir(parents=True)
    panel={p['id']:p for p in read(ROOT/'results/unified_exact_round71/protocol.json')['panel']}
    selected=[panel[key] for key in ['D3','C2','D4','D6','D7']]
    commands=[]
    for p in selected:
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
        for arm,preset in [('JDS-C','research-round76-vds-physical-closure'),('BDS-C','research-round78-vds-balanced-descent')]:
            dest=OUT/'local_raw'/p['id']/arm
            command=list(map(str,[build/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],
                '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
                '--time-limit',24,'--process-wall-time-limit',30,'--process-shutdown-margin',3,
                '--threads',1,'--mip-threads',1,'--gurobi-seed',0,'--gurobi-presolve',-1,
                '--method','primal-heuristic','--algorithm-preset',preset,'--round61-candidate-mode','off',
                '--out',dest/'result.json','--log',dest/'native.log','--process-phase-ledger',dest/'phases.csv',
                '--external-gini-artifact-dir',dest/'external','--heuristic-candidates-csv',dest/'heuristic.csv',
                '--primal-heuristic-generation-log',dest/'hga.csv','--progress-log',dest/'progress.csv',
                '--round65-hga-zero-stop','true','--round60-hga-candidate-log',dest/'hga_events.csv']))
            commands.append(dict(number=len(commands)+1,id=p['id'],arm=arm,command=command,input=p,
                destination=str(dest.relative_to(ROOT)),cap=30,hard_deadline=29.8,expected_optimize_calls=0))
    identity=dict(source_commit=frozen['source_commit'],source=frozen['source'],binary_sha256=sha(build/'ExactEBRP.exe'),
        qualification_sha256=sha(STAGE/f'qualification_{version}.json'),qualification_audit_sha256=sha(STAGE/f'qualification_{version}_audit.json'),
        cmake_sha256=frozen['cmake_sha256'],driver_sha256=sha(__file__),physical_verifier_sha256=sha(physical_module.__file__),
        reused_replay_sha256=sha(ROOT/'scripts/round73_seed_diagnostic.py'),plan_sha256=sha(STAGE/'plan.md'),
        implementation_plan_sha256=frozen['implementation_plan_sha256'],
        balanced_replay_sha256=sha(ROOT/'scripts/round78_audit.py'),
        closure_replay_sha256=sha(ROOT/'scripts/round76_startup.py'),
        commands=commands,max_launches=10,maximum_seconds=300,expected_optimize_calls=0,
        scope='Startup attribution only; exposed development panel, no proof/performance/confirmation claim')
    write(OUT/'identity.json',identity)
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    physical_module.ROOT=ROOT
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    records=[]
    def save():write(OUT/'summary.json',dict(records=records,attempted=len(records),valid=sum(bool(r.get('valid')) for r in records),
        paid_wall_seconds=sum(r['completion']['wall_seconds'] for r in records),optimize_calls=0,full_exact_runs=0))
    try:
        for command in commands:
            dest=ROOT/command['destination'];dest.mkdir(parents=True)
            p=command['input'];write(dest/'launch.json',dict(command,started_unix=time.time(),identity_sha256=sha(OUT/'identity.json')))
            with (OUT/'processes.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(command)+'\n')
            start=time.monotonic();watchdog=False
            with affinity.inherited_core() as binding:
                with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
                    proc=subprocess.Popen(command['command'],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                    child=affinity.read_masks(proc.pid);assert child['process_mask']==4
                    write(dest/'affinity.json',dict(binding=binding,child=child,child_pid=proc.pid))
                    try: code=proc.wait(timeout=max(.001,command['hard_deadline']-(time.monotonic()-start)))
                    except subprocess.TimeoutExpired:proc.kill();proc.wait();code=proc.returncode;watchdog=True
            completion=dict(returncode=code,wall_seconds=time.monotonic()-start,watchdog=watchdog,restored=affinity.read_masks())
            write(dest/'completion.json',completion)
            record=dict(number=command['number'],id=p['id'],arm=command['arm'],completion=completion,valid=False)
            records.append(record);save()
            assert code==0 and not watchdog and completion['wall_seconds']<=30
            assert completion['restored']==binding['before']
            audit_start=time.perf_counter()
            result=read(dest/'result.json')
            assert result['method']=='primal-heuristic' and result['certificate_scope']=='primal_heuristic_ub_only'
            assert not result['strict_certified_original_problem'] and not (dest/'external').exists()
            assert result['hga_total_generations']==0 and result['decoded_descent_complete'] and result['decoded_descent_seeds_completed']==25
            for path in dest.rglob('*.log'):assert 'Optimize a model' not in path.read_text(encoding='utf-8',errors='replace')
            physical=physical_module.physical(p,dict(result,inventory=result['verification']['final_inventories']))
            assert physical['original_T_feasible'] and abs(physical['F']-result['upper_bound'])<1e-10
            # Reconstruct the old constructor trace using its frozen independent replay.
            prefix={};joint=csvrows(dest/'hga.csv.joint.csv')
            for row in joint:
                if row['status']!='accepted_verified':continue
                k,pick,drop,qv,a,b=[int(row[key]) for key in ['vehicle','pickup','drop','quantity','pickup_leg','drop_leg']]
                route=prefix.setdefault(k,dict(vehicle=k,nodes=[0,0],operations=[]))
                if drop:route['nodes'].insert(b+1,drop);route['operations'].append(dict(station=drop,pickup=0,drop=qv))
                if pick:route['nodes'].insert(a+1,pick);route['operations'].append(dict(station=pick,pickup=qv,drop=0))
            ji=dict(routes=list(prefix.values()),objective=float(joint[-1]['objective']),upper_bound=float(joint[-1]['objective']))
            joint_audit=replay_joint(p,dest,ji)
            detail=dict(joint_audit=joint_audit)
            assert 'verification_failed=1' not in '\n'.join(result.get('notes',[]))
            if command['arm']=='BDS-C':
                base=OUT/'local_raw'/p['id']/'JDS-C';baseline=read(base/'result.json')
                logical=lambda row:{k:v for k,v in row.items() if k!='elapsed_seconds'}
                assert list(map(logical,csvrows(dest/'hga.csv.descent.csv')))==list(map(logical,csvrows(base/'hga.csv.descent.csv')))
                current=normalize(read(dest/'hga.csv.balanced/initial.json'))
                assert route_hash(current)==route_hash(normalize(read(base/'hga.csv.closure.csv.initial.json')))
                balanced=replay_balanced(p,dest/'hga.csv.balanced',current)
                final=normalize(read(dest/'hga.csv.balanced/final.json'))
                assert not read(dest/'hga.csv.balanced/result.json')['verification_failed']
                handoff=route_hash(final)==route_hash(result)
                if not handoff:
                    assert route_hash(result)==route_hash(current) and 0<=current['F']-final['F']<=1e-10
                detail.update(balanced_audit=balanced,all25_logical_descent_paths_equal=True,
                    same_initial_preclosure_witness=True,balanced_endpoint_returned_to_outer=handoff)
                assert physical['F']<=baseline['upper_bound']+1e-10
                assert not (dest/'hga.csv.closure.csv').exists()
            else:
                initial=normalize(read(dest/'hga.csv.closure.csv.initial.json'))
                initial['upper_bound']=initial['F']
                detail.update(replay_closure(p,dest,initial,result))
                assert not (dest/'hga.csv.balanced').exists()
            assert not (dest/'hga.csv.quantity.csv').exists(), 'Neither arm inherits QDS-X'
            record.update(valid=True,UB=physical['F'],physical=physical,detail=detail,route_sha256=route_hash(result),
                result_sha256=sha(dest/'result.json'),offline_audit_seconds=time.perf_counter()-audit_start)
            write(dest/'audit.json',record);save()
            print(json.dumps({k:record[k] for k in ['number','id','arm','valid','UB','completion']}),flush=True)
    finally:
        lock.unlink()

if __name__=='__main__':main()
