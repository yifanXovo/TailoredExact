"""Stop one owned unfinished diagnostic after PID/birth identity readback."""
from round157_common import *

def run(label):
    fee=OUT/'fees'/label;assert not (fee/'receipt.json').exists()
    record=read(fee/'PID.json');identity=meter.process_snapshot(record)
    assert identity['same_process_alive']
    assert Path(record['command'][2]).resolve()==(ROOT/'scripts/round157_floor.py').resolve()
    log=OUT/'floor'/record['command'][4]/'native.log'
    tail=log.read_text(encoding='utf-8',errors='replace').splitlines()[-15:]
    reason='Early evidence-based reallocation before the planned 1024-node checkpoint: after about68 minutes the reported global bound remains at the valid prior floor, with773 observed nodes and growing per-node LP cost. Redirect to the preselected second family and one finite exclusion/repricing batch. This is an unfinished diagnostic; no new bound is consumed.'
    write(fee/'revision_termination.json',dict(UTC=utc(),reason=reason,identity=identity,
        no_new_bound_consumed=True,planned_checkpoint_nodes=1024,planned_checkpoint_reached=False,
        observed_log_tail=tail,log_SHA_before_stop=sha(log),goal_remains_active=True))
    stopped=subprocess.run(['taskkill','/PID',str(record['pid']),'/T','/F'],capture_output=True,text=True)
    write(fee/'termination_return.json',dict(returncode=stopped.returncode,stdout=stopped.stdout,stderr=stopped.stderr,UTC=utc()))
    assert stopped.returncode==0
    print(json.dumps(dict(stopped_owned_pid=record['pid'],no_new_bound_consumed=True)),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
