"""Single predeclared paid Q-PLUS control, after the initial Round66 panel."""
from pathlib import Path
import round66_research as run

def main():
    plan=run.read(run.OUT/'resource_plan_update_2.json')
    freeze=run.read(run.OUT/'build_v1.json')
    assert run.sha(run.BUILD/'ExactEBRP.exe')==freeze['binary']
    assert run.sha(Path(run.__file__))==freeze['driver']
    entries=run.runner.entries()
    assert sum(e['kind']=='performance' for e in entries)==16
    assert sum(e['kind']=='native-micro' for e in entries)==2
    assert all((run.ROOT/e['destination']/'completion.json').exists() for e in entries)
    identity,arm,cap=plan['allowed_id'],plan['allowed_arm'],plan['cap_seconds']
    assert (identity,arm,cap,plan['maximum_additional_launches'])==('D4','Q-PLUS',300,1)
    p=run.panel()[identity];assert run.sha(run.ROOT/p['instance_path'])==p['input_sha256']
    dest=run.RAW/'proof_screen'/identity/arm
    cmd=run.runner.full_command(p,dest,'research-round65-k1-h','off',cap)+[
        '--round65-witness-audit','true','--ub-event-log',dest/'ub_events.csv',
        '--round65-hga-zero-stop','true','--round60-hga-candidate-log',dest/'hga_events.csv',
        '--round64-shared-mode','q']
    run.runner.execute(cmd,dest,dict(id=identity,arm=arm,stage='proof_screen',scope='original_problem',
        resource_revision=2,driver_sha256=run.sha(Path(__file__)),
        build=run.sha(run.OUT/'build_v1.json'),input_sha256=p['input_sha256']),
        cap,'performance','all actual native calls in ledger')
    result=run.read(dest/'result.json');assert 'failed' not in result.get('status','')
if __name__=='__main__':main()
