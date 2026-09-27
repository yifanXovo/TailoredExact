"""Refresh mutable recovery metadata only; never start, stop, or audit a solver."""
import hashlib
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round85'
def read(p):return json.loads(p.read_text(encoding='utf-8'))

def main():
    path=OUT/'runtime_checkpoint.json';old=read(path)
    assert not old.get('stage_complete'), 'Never reopen a closed stage'
    c=OUT/'campaign';summary=read(c/'summary.json')
    last=read(c/'active_experiment.json');locked=(c/'active_run.lock').exists()
    affinity=read(ROOT/last['destination']/'affinity.json')
    now=time.time()
    data=dict(stage=85,plan_commit=old['plan_commit'],driver_session=22846,
        driver_pid=last['driver_pid'],completed=summary['completed'],planned=21,
        active=last if locked else None,last_experiment=last,
        campaign_lock_present=locked,recorded_child_pid=affinity['pid'],
        recorded_child_mask=affinity['child']['process_mask'],
        active_elapsed_at_snapshot=now-last['started_unix'] if locked else None,
        total_completed_process_seconds=summary['total_wall_seconds'],
        completed_native_starts=sum(r['audit']['native_calls_started'] for r in summary['records']),
        completed_native_returns=sum(r['audit']['native_calls_returned'] for r in summary['records']),
        updated_unix=now,stage_complete=False,overall_goal_complete=False,no_relaunch=True,
        snapshot_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Mutable recovery snapshot, not a performance checkpoint or proof of PID liveness. Native and driver status must be read independently.')
    if (c/'driver_completion.json').exists():data['driver_completion']=read(c/'driver_completion.json')
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data))

if __name__=='__main__':main()
