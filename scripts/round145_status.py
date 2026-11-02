"""Small live snapshot only: no journal scan, Native load, compile or Optimize."""
from round145_common import *
def tail(path,lines=3):
    if not path.exists():return []
    with path.open('rb') as stream:
        stream.seek(max(0,path.stat().st_size-8192));data=stream.read()
    return data.decode('utf-8',errors='replace').splitlines()[-lines:]
def main():
    configure();active_path=OUT/'active_position.json'
    active=read(active_path) if active_path.exists() else None;snapshot=dict(UTC=utc(),active=active,budget=budget(),Optimize=0,Native_load=0)
    if active:
        matrix=read(OUT/(active['batch']+'_matrix.json'));group=next(g for g in matrix['groups'] if g['position']==active['position'])
        d=Path(group['launch']['destination']);logs=list((d/'external/native_logs').glob('*.gurobi.log'))
        latest=max(logs,key=lambda p:p.stat().st_mtime) if logs else None
        snapshot.update(latest_log=str(latest) if latest else None,native_diagnostic_tail=tail(latest) if latest else [],
            stderr_tail=tail(OUT/'fees'/active['fee_label']/'stderr.log'),
            latest_sealed=read(OUT/'runtime_status.json') if (OUT/'runtime_status.json').exists() else None,
            active_verification_closed=(d/'verification_closeout.json').exists())
    if '--full' not in sys.argv:
        snapshot=dict(UTC=snapshot['UTC'],active=active['arm_id'] if active else None,
            charged_closed_outer_seconds=snapshot['budget']['G1_seconds'],
            native_diagnostic_tail=snapshot.get('native_diagnostic_tail',[]),stderr_tail=snapshot.get('stderr_tail',[]),
            latest_sealed=snapshot.get('latest_sealed'),active_verification_closed=snapshot.get('active_verification_closed'))
    print(json.dumps(snapshot,ensure_ascii=False))
if __name__=='__main__':main()
