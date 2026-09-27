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
from round83_qualify import ROOT, OUT as STAGE, sha, read, write
from round76_startup import replay_closure
from round78_audit import audit as replay_balanced
from round83_audit_v2 import audit as replay_exchange
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

def audit_run(command, record):
    dest=ROOT/command['destination'];p=command['input']
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
    suffix='exchange' if command['arm']=='ENS-C' else 'balanced'
    current=normalize(read(dest/f'hga.csv.{suffix}/initial.json'))
    neutral=(replay_exchange if suffix=='exchange' else replay_balanced)(p,dest/f'hga.csv.{suffix}',current)
    final=normalize(read(dest/f'hga.csv.{suffix}/final.json'))
    handoff=route_hash(final)==route_hash(result)
    if not handoff:
        assert route_hash(result)==route_hash(current) and 0<=current['F']-final['F']<=1e-10
    detail.update(neutral_audit=neutral,neutral_endpoint_returned_to_outer=handoff)
    if command['arm']=='ENS-C':
        base=OUT/'local_raw'/p['id']/'BDS-C';baseline=read(base/'result.json')
        logical=lambda row:{k:v for k,v in row.items() if k!='elapsed_seconds'}
        assert list(map(logical,csvrows(dest/'hga.csv.descent.csv')))==list(map(logical,csvrows(base/'hga.csv.descent.csv')))
        assert route_hash(current)==route_hash(normalize(read(base/'hga.csv.balanced/initial.json')))
        detail.update(all25_logical_descent_paths_equal=True,same_initial_preclosure_witness=True,
            UB_delta_vs_BDS=physical['F']-baseline['upper_bound'])
        assert not (dest/'hga.csv.balanced').exists()
    else:
        assert not (dest/'hga.csv.exchange').exists()
    assert not (dest/'hga.csv.closure.csv').exists()
    assert not (dest/'hga.csv.quantity.csv').exists(), 'Neither arm inherits QDS-X'
    record.update(valid=True,UB=physical['F'],physical=physical,detail=detail,route_sha256=route_hash(result),
        result_sha256=sha(dest/'result.json'),offline_audit_seconds=time.perf_counter()-audit_start)
    return record

def main():
    assert not (OUT/'active_run.lock').exists()
    assert not (OUT/'completion_summary.json').exists(),'Never repeat resumed startup completion'
    identity=read(OUT/'identity.json');q=read(STAGE/'qualification_v1.json')
    for name,digest in q['identity']['source'].items():assert sha(ROOT/name)==digest,name
    assert sha(ROOT/'build/round83/v1/ExactEBRP.exe')==identity['binary_sha256']
    assert sha(ROOT/'scripts/round83_startup.py')==identity['driver_sha256']
    prior=read(OUT/'summary.json');assert prior['attempted']==6 and prior['valid']==5
    assert all(x['valid'] for x in prior['records'][:5]) and not prior['records'][5]['valid']
    records=copy.deepcopy(prior['records']);commands=identity['commands'];assert len(commands)==10
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    physical_module.ROOT=ROOT
    resumed=time.perf_counter()
    write(OUT/'resume_identity.json',dict(original_identity_sha256=sha(OUT/'identity.json'),
        original_summary_sha256=sha(OUT/'summary.json'),script_sha256=sha(__file__),
        corrected_reader_sha256=sha(ROOT/'scripts/round83_audit_v2.py'),
        new_launch_numbers=[7,8,9,10],replayed_without_native_rerun=[6],expected_new_optimize_calls=0))
    def save():write(OUT/'completion_summary.json',dict(records=records,attempted=len(records),
        valid=sum(bool(r.get('valid')) for r in records),paid_wall_seconds=sum(r['completion']['wall_seconds'] for r in records),
        optimize_calls=0,full_exact_runs=0,resume_seconds=time.perf_counter()-resumed,
        original_failure_retained='reader_failure.json',all_original_commands_completed=len(records)==10 and all(r['valid'] for r in records)))
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        records[5]=audit_run(commands[5],records[5]);write(ROOT/commands[5]['destination']/'audit_v2.json',records[5]);save()
        print(json.dumps(dict(recovered_original_run6=True,UB=records[5]['UB'],native_rerun=False)),flush=True)
        for command in commands[6:]:
            dest=ROOT/command['destination'];assert not dest.exists();dest.mkdir(parents=True)
            write(dest/'launch.json',dict(command,started_unix=time.time(),original_identity_sha256=sha(OUT/'identity.json')))
            with (OUT/'processes.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(command)+'\n')
            start=time.monotonic();watchdog=False
            with affinity.inherited_core() as binding:
                with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
                    proc=subprocess.Popen(command['command'],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                    child=affinity.read_masks(proc.pid);assert child['process_mask']==4
                    write(dest/'affinity.json',dict(binding=binding,child=child,child_pid=proc.pid))
                    try:code=proc.wait(timeout=max(.001,command['hard_deadline']-(time.monotonic()-start)))
                    except subprocess.TimeoutExpired:proc.kill();proc.wait();code=proc.returncode;watchdog=True
            completion=dict(returncode=code,wall_seconds=time.monotonic()-start,watchdog=watchdog,restored=affinity.read_masks())
            write(dest/'completion.json',completion)
            record=dict(number=command['number'],id=command['input']['id'],arm=command['arm'],completion=completion,valid=False)
            records.append(record);save()
            assert code==0 and not watchdog and completion['wall_seconds']<=60 and completion['restored']==binding['before']
            audit_run(command,record);write(dest/'audit.json',record);save()
            print(json.dumps({k:record[k] for k in ['number','id','arm','valid','UB','completion']}),flush=True)
    finally:lock.unlink()

if __name__=='__main__':main()
