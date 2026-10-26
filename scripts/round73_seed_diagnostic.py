"""Second frozen startup tranche: constructive-seeded descent, with fresh controls."""
import ast
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import analyze_round61 as physical_module
import round70_affinity as affinity
from round73_qualify import ROOT, OUT as STAGE, sha, write
OUT=STAGE/"seed_revision"


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def route_hash(witness):
    parts=[]
    for r in sorted(witness['routes'],key=lambda x:x['vehicle']):
        ops=sorted((op['station'],op['pickup'],op['drop']) for op in r['operations'])
        parts.append('v='+str(r['vehicle'])+';nodes='+''.join(str(i)+',' for i in r['nodes'])+
                     ';ops='+''.join(':'.join(map(str,op))+',' for op in ops)+'|')
    return hashlib.sha256(''.join(parts).encode('ascii')).hexdigest()

def replay_joint(p,folder,result):
    trace=list(csv.DictReader((folder/'hga.csv.joint.csv').open(encoding='utf-8')))
    assert trace[0]['status']=='initial_verified'
    assert trace[-1]['status'] in ['motif_exhausted','whole_run_deadline']
    text=(ROOT/p['instance_path']).read_text(encoding='utf-8')
    points=ast.literal_eval(re.search(r'(?m)^\s*points\s*=\s*(\[[^\n]*\])',text)[1])
    def duration(route):
        nodes=route['nodes']
        return sum(math.hypot(points[a][0]-points[b][0],points[a][1]-points[b][1])/1.5
                   for a,b in zip(nodes,nodes[1:]))+(float(p['pickup_seconds'])+float(p['drop_seconds']))*sum(op['pickup'] for op in route['operations'])
    routes={};prior_time=-1;prior_value=float(trace[0]['objective']);accepted=0
    first=physical_module.physical(p,dict(routes=[],objective=prior_value))
    assert first['original_T_feasible']
    for row in trace[1:]:
        assert float(row['process_seconds'])>=prior_time;prior_time=float(row['process_seconds'])
        if row['status']!='accepted_verified':continue
        k,pick,drop,q,a,b=[int(row[key]) for key in ['vehicle','pickup','drop','quantity','pickup_leg','drop_leg']]
        assert q>0 and (pick or drop)
        route=routes.setdefault(k,dict(vehicle=k,nodes=[0,0],operations=[]))
        old=duration(route)
        if drop:route['nodes'].insert(b+1,drop);route['operations'].append(dict(station=drop,pickup=0,drop=q))
        if pick:route['nodes'].insert(a+1,pick);route['operations'].append(dict(station=pick,pickup=q,drop=0))
        assert abs(duration(route)-old-float(row['added_duration']))<=1e-6
        current=dict(routes=list(routes.values()),objective=float(row['objective']))
        checked=physical_module.physical(p,current)
        assert checked['original_T_feasible'] and prior_value-checked['F']>1e-12
        prior_value=checked['F'];accepted+=1;assert int(row['step'])==accepted
    assert route_hash(dict(routes=list(routes.values())))==route_hash(result)
    assert abs(prior_value-result['upper_bound'])<1e-7
    return dict(accepted=accepted,terminal_status=trace[-1]['status'],
                placements=int(trace[-1]['placements']),quantities=int(trace[-1]['quantity_evaluations']),
                all_prefixes_independently_replayed=True)

def main():
    version='v4';build=ROOT/'build/round73'/version
    qualification=read(STAGE/f'qualification_{version}.json')
    assert len(qualification['attempts'])==3 and all(a['returncode']==0 for a in qualification['attempts'])
    frozen=qualification['identity']
    for name,digest in frozen['source'].items():assert sha(ROOT/name)==digest,name
    assert sha(ROOT/'CMakeLists.txt')==frozen['cmake_sha256']
    assert sha(STAGE/'plan.md')==frozen['plan_sha256']
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'plan.md').exists()
    (OUT/'plan.md').write_bytes((STAGE/'seed_extension.md').read_bytes())
    assert '100% tests passed, 0 tests failed out of 53' in (build/'tests.log').read_text(encoding='utf-8')
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round73-joint-insertion'
    ledger=OUT/'diagnostic_processes.jsonl';assert not ledger.exists(),'Never repeat or replace a diagnostic tranche'
    panel={p['id']:p for p in read(ROOT/'results/unified_exact_round71/protocol.json')['panel']}
    selected=[panel[i] for i in ['D3','C2','D4','D6','D7']]
    for p in selected:assert sha(ROOT/p['instance_path'])==p['input_sha256']
    identity=dict(source_commit=frozen['source_commit'],binary_sha256=sha(build/'ExactEBRP.exe'),
        qualification_sha256=sha(STAGE/f'qualification_{version}.json'),source=frozen['source'],
        driver_sha256=sha(__file__),physical_verifier_sha256=sha(physical_module.__file__),
        plan_sha256=sha(OUT/'plan.md'),panel=selected,max_launches=10,cap_seconds=30,maximum_seconds=300,
        expected_optimize_calls=0,scope='Paid UB-only development diagnostics; never formal exact endpoints')
    write(OUT/'diagnostic_identity.json',identity)
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    records=[];physical_module.ROOT=ROOT
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    try:
        for p in selected:
            for arm,preset in [('DS-X','research-round71-vds-interroute-descent'),('JDS-X','research-round73-vds-joint-seeded-descent')]:
                dest=OUT/'local_raw'/p['id']/arm;assert not dest.exists();dest.mkdir(parents=True)
                cmd=[build/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],
                    '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
                    '--time-limit',24,'--process-wall-time-limit',30,'--process-shutdown-margin',3,
                    '--threads',1,'--mip-threads',1,'--gurobi-seed',0,'--gurobi-presolve',-1,
                    '--method','primal-heuristic','--algorithm-preset',preset,'--round61-candidate-mode','off',
                    '--out',dest/'result.json','--log',dest/'native.log','--process-phase-ledger',dest/'phases.csv',
                    '--external-gini-artifact-dir',dest/'external','--heuristic-candidates-csv',dest/'heuristic.csv',
                    '--primal-heuristic-generation-log',dest/'hga.csv','--progress-log',dest/'progress.csv',
                    '--round65-hga-zero-stop','true','--round60-hga-candidate-log',dest/'hga_events.csv']
                cmd=list(map(str,cmd))
                entry=dict(number=len(records)+1,id=p['id'],arm=arm,command=cmd,input=p,
                    executable_sha256=identity['binary_sha256'],started_unix=time.time(),cap=30,
                    expected_optimize_calls=0,destination=str(dest.relative_to(ROOT)))
                write(dest/'launch.json',entry)
                with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(entry)+'\n')
                started=time.monotonic();watchdog=False
                with affinity.inherited_core() as binding:
                    with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
                        proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                        child=affinity.read_masks(proc.pid);assert child['process_mask']==4
                        write(dest/'affinity.json',dict(binding=binding,child=child,child_pid=proc.pid))
                        try:code=proc.wait(timeout=40)
                        except subprocess.TimeoutExpired:proc.kill();proc.wait();code=proc.returncode;watchdog=True
                completion=dict(returncode=code,wall=time.monotonic()-started,watchdog=watchdog,restored=affinity.read_masks())
                completion['within_cap']=completion['wall']<=30;write(dest/'completion.json',completion)
                assert code==0 and not watchdog and completion['within_cap']
                assert completion['restored']==binding['before']
                result=read(dest/'result.json')
                assert result['method']=='primal-heuristic' and result['certificate_scope']=='primal_heuristic_ub_only'
                assert not result['strict_certified_original_problem'] and not (dest/'external').exists()
                assert result['hga_total_generations']==0
                if (dest/'native.log').exists():assert 'Optimize a model' not in (dest/'native.log').read_text(encoding='utf-8')
                physical=physical_module.physical(p,dict(result,inventory=result['verification']['final_inventories']))
                assert physical['original_T_feasible'] and abs(physical['F']-result['upper_bound'])<1e-7
                if arm=='JDS-X':
                    constructive=list(csv.DictReader((dest/'hga.csv.joint.csv').open(encoding='utf-8')))
                    prefix={}
                    for row in constructive:
                        if row['status']!='accepted_verified':continue
                        k,pick,drop,q,a,b=[int(row[key]) for key in ['vehicle','pickup','drop','quantity','pickup_leg','drop_leg']]
                        route=prefix.setdefault(k,dict(vehicle=k,nodes=[0,0],operations=[]))
                        if drop:route['nodes'].insert(b+1,drop);route['operations'].append(dict(station=drop,pickup=0,drop=q))
                        if pick:route['nodes'].insert(a+1,pick);route['operations'].append(dict(station=pick,pickup=q,drop=0))
                    ji=dict(routes=list(prefix.values()),objective=float(constructive[-1]['objective']),upper_bound=float(constructive[-1]['objective']))
                    detail=replay_joint(p,dest,ji)
                    write(dest/'replayed_constructive_witness.json',ji)
                    trace=list(csv.DictReader((dest/'hga.csv.descent.csv').open(encoding='utf-8')))
                    baseline_trace=list(csv.DictReader((OUT/'local_raw'/p['id']/'DS-X/hga.csv.descent.csv').open(encoding='utf-8')))
                    logical=lambda row:{k:v for k,v in row.items() if k!='elapsed_seconds'}
                    first=[row for row in trace if int(row['seed'])<=24]
                    complete_first=[int(row['seed']) for row in first if row['exhausted']=='1']==list(range(1,25))
                    if complete_first:assert list(map(logical,first))==list(map(logical,baseline_trace))
                    extra=[row for row in trace if int(row['seed'])==25]
                    if result['decoded_descent_complete']:
                        assert result['decoded_descent_seeds_completed']==25 and extra and extra[-1]['exhausted']=='1'
                    baseline=next(row for row in records if row['id']==p['id'] and row['arm']=='DS-X')
                    if complete_first:assert physical['F']<=baseline['UB']+1e-10
                    assert physical['F']<=ji['objective']+1e-10
                    order=list(csv.DictReader((dest/'hga.csv.joint_seed.csv').open(encoding='utf-8')))
                    assert sorted(int(row['station']) for row in order)==list(range(1,int(p['V'])+1))
                    detail.update(JI_UB=ji['objective'],complete_first24=complete_first,first24_logical_paths_equal=complete_first,
                        completed_seeds=result['decoded_descent_seeds_completed'],descent_complete=result['decoded_descent_complete'],
                        extra_seed_passes=len(extra),extra_seed_checks=sum(int(row['decoded_checks']) for row in extra),
                        extra_seed_moves=sum(int(row['accepted']) for row in extra),
                        extra_seed_cross_moves=sum(int(row['accepted_cross_route']) for row in extra))
                else:
                    assert result['decoded_descent_complete'] and result['decoded_descent_seeds_completed']==24
                    detail=dict(completed_seeds=24,cross_checks=result['decoded_descent_cross_route_checks'],cross_moves=result['decoded_descent_cross_route_moves'])
                row=dict(number=entry['number'],id=p['id'],arm=arm,wall=completion['wall'],UB=physical['F'],
                    physical=physical,detail=detail,route_sha256=route_hash(result),optimizer_calls=0,result_sha256=sha(dest/'result.json'))
                records.append(row);write(OUT/'diagnostic_results.json',records)
                print(json.dumps(row),flush=True)
        write(OUT/'diagnostic_summary.json',dict(completed=len(records),wall_seconds=sum(r['wall'] for r in records),
            optimize_calls=0,failures=0,full_exact_runs=0,scope='Startup attribution only; no performance or confirmation claim'))
    finally:lock.unlink()

if __name__=='__main__':main()
