"""Six bounded UB-only real-input diagnoses; no exact performance claim."""
import csv,json,os,subprocess,time
from pathlib import Path
import package_round71 as base
import round70_affinity as affinity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round72'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def main():
    base.bind();frozen,protocol=base.run.assert_frozen()
    assert not (base.run.OUT/'active_run.lock').exists()
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round72-vdsx-validation'
    ledger=OUT/'diagnostic_processes.jsonl';assert not ledger.exists(),'Never replace an earlier attempt'
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    write(OUT/'diagnostic_identity.json',dict(base_commit='73ce04d9a3c5031c2b5a1021523502f0a9a85168',
        source_freeze=frozen['source_commit'],binary_sha256=frozen['binary'],
        source= frozen['source'],inherited_ctests=49,new_ctests=0,new_native_qualification_calls=0,
        previous_qualification_native_calls=39,driver_sha256=base.run.sha(__file__),
        plan_sha256=base.run.sha(OUT/'plan.md'),maximum_launches=6,whole_process_cap=30,
        maximum_process_seconds=180,scope='Standalone primal-heuristic UB-only diagnostics; not exact runs'))
    records=[]
    try:
        for identity in ['D3','C2','D4']:
            p=base.run.panel()[identity];assert base.run.sha(ROOT/p['instance_path'])==p['input_sha256']
            for arm,preset in [('DS','research-round70-vds-descent'),('DS-X','research-round71-vds-interroute-descent')]:
                dest=OUT/'local_raw'/identity/arm;assert not dest.exists();dest.mkdir(parents=True)
                cmd=base.run.runner.full_command(p,dest,preset,'off',30)
                cmd[cmd.index('--method')+1]='primal-heuristic'
                cmd+=['--round65-hga-zero-stop','true','--round60-hga-candidate-log',dest/'hga_events.csv']
                cmd=list(map(str,cmd))
                entry=dict(number=len(records)+1,id=identity,arm=arm,command=cmd,input=p,
                    executable_sha256=base.run.sha(cmd[0]),started_unix=time.time(),cap=30,
                    kind='startup-only diagnostic',optimizer_calls_expected=0,destination=str(dest.relative_to(ROOT)))
                write(dest/'launch.json',entry)
                with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(entry)+'\n')
                env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
                started=time.monotonic();watchdog=False
                with affinity.inherited_core() as binding:
                    with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
                        proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                        child=affinity.read_masks(proc.pid);assert child['process_mask']==4
                        write(dest/'affinity.json',dict(binding=binding,child=child))
                        try:code=proc.wait(timeout=40)
                        except subprocess.TimeoutExpired:proc.kill();proc.wait();code=proc.returncode;watchdog=True
                wall=time.monotonic()-started
                completion=dict(returncode=code,wall=wall,watchdog=watchdog,within_cap=wall<=30,
                    restored_launcher=affinity.read_masks())
                write(dest/'completion.json',completion)
                assert code==0 and not watchdog and wall<=30
                assert completion['restored_launcher']==binding['before']
                result=read(dest/'result.json')
                assert result['method']=='primal-heuristic' and result['certificate_scope']=='primal_heuristic_ub_only'
                assert not result['strict_certified_original_problem'] and not (dest/'external').exists()
                assert result['decoded_descent_complete'] and result['decoded_descent_seeds_completed']==24
                assert result['hga_total_generations']==0 and result['decoded_descent_cross_route_enabled']==(arm=='DS-X')
                physical=base.audit.physical_module.physical(p,result)
                assert physical['original_T_feasible'] and abs(physical['F']-result['upper_bound'])<=1e-7
                row=dict(number=len(records)+1,id=identity,arm=arm,wall=wall,UB=physical['F'],physical=physical,
                    initial_route_sha256=base.route_hash(result),optimizer_calls=0,
                    cross_route_checks=result['decoded_descent_cross_route_checks'],
                    cross_route_moves=result['decoded_descent_cross_route_moves'],
                    completed_seeds=24,result_sha256=base.run.sha(dest/'result.json'),
                    scope='Verified UB-only diagnostic; no full-domain proof or performance comparison')
                records.append(row);write(OUT/'diagnostic_results.json',records)
                print({k:row[k] for k in ['number','id','arm','wall','UB','cross_route_checks','cross_route_moves']},flush=True)
        write(OUT/'diagnostic_summary.json',dict(completed=6,actual_wall=sum(r['wall'] for r in records),
            optimizer_calls=0,new_ctests=0,full_exact_runs=0,full_validation_complete=False,failures=0,
            scope='Actual six startup-only diagnostics, never substituted for the pending certification comparisons'))
    finally:lock.unlink()

if __name__=='__main__':main()
