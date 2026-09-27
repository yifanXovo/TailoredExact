"""Compact read-only recovery snapshot, without scanning model files."""
import csv,json,time
import round68_research as run

if __name__=='__main__':
    completed=[];active=[]
    for e in run.runner.entries():
        if not e['charged']:continue
        folder=run.ROOT/e['destination']
        if (folder/'completion.json').exists():
            c=run.read(folder/'completion.json');completed.append(c)
        else:
            phase=None
            if (folder/'phases.csv').exists():
                phases=list(csv.DictReader((folder/'phases.csv').open()))
                if phases:phase=phases[-1]['event']
            logs=list(folder.glob('external/native_logs/*.log'))
            if not logs and (folder/'native.log').exists():logs=[folder/'native.log']
            tail=[];latest=None
            if logs:
                latest=max(logs,key=lambda p:p.stat().st_mtime)
                # Only a short tail is needed; full logs are immutable evidence.
                with latest.open('rb') as f:
                    f.seek(max(0,latest.stat().st_size-1600));tail=f.read().decode('utf-8',errors='replace').splitlines()[-3:]
            active.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],cap=e['cap_seconds'],
                approximate_wall_elapsed=round(time.time()-e['started_unix'],1),last_persisted_phase=phase,
                latest_native_log=str(latest) if latest else None,tail=tail))
    print(json.dumps(dict(completed=len(completed),paid_completed_wall_seconds=sum(c['wall_seconds'] for c in completed),
        active=active,optimizer_call_count_note='Final count only after completed native ledger audit'),indent=2))
