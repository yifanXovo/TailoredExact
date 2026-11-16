"""Read-only completion watcher; each returned row is audited once, no solver launch."""
from round170_common import *
import subprocess

def main():
    started=time.perf_counter();last=None
    while time.time()-SCIENCE_START<SCIENCE_CAP:
        matrix=read(OUT/'matrix_frozen.json')['positions']
        completed=[p for p in matrix if (Path(p['directory'])/'completion.json').is_file()]
        waiting=[p['position'] for p in completed if not (OUT/f"review/complete_audit_{p['position']:02}.json").is_file()]
        if waiting:
            audit_tick=time.perf_counter();audit_started=time.time()
            rc=subprocess.call([sys.executable,'-X','utf8','-B',ROOT/'scripts/round170_audit.py',*map(str,waiting)],cwd=ROOT)
            fees=OUT/'review/audit_process_costs.json';records=read(fees) if fees.exists() else []
            records.append(dict(positions=waiting,start_epoch=audit_started,UTC=utc(),rc=rc,
                audit_process_outer_seconds=time.perf_counter()-audit_tick,Optimize=0,
                scope='includes interpreter/import/adapter/postreturn audit and report serialization; inner audit_seconds are nested'))
            write(fees,records)
            assert rc==0,'preserve reader failure; repair reader only, never repeat a solver for reporting'
        audited=sum((OUT/f"review/complete_audit_{p['position']:02}.json").is_file() for p in matrix)
        active=read(OUT/'active_position.json') if (OUT/'active_position.json').is_file() else None
        state=dict(UTC=utc(),returned=len(completed),audited=audited,total=22,
            active_position=active['position'] if active else None,
            active_arm=active['arm'] if active else None,role=active['role'] if active else None,
            Native_Seed=active['Native_Seed'] if active else None,
            current_process_elapsed=round(time.time()-active['started_epoch'],1) if active else None,
            science_elapsed_conservative_seconds=round(time.time()-SCIENCE_START,1),
            watcher_seconds=time.perf_counter()-started,Optimize_by_watcher=0)
        write(OUT/'monitor_status.json',state)
        print(json.dumps(state),flush=True)
        if audited==22:return
        time.sleep(30)
    raise RuntimeError('science capacity reached; no extra optimization is authorized')
if __name__=='__main__':main()
