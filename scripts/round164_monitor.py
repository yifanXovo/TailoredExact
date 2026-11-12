"""Small active-position and log-tail reads; never audits or solves."""
from pathlib import Path
import json,time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round164'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def tail(p,n=4096):
    with p.open('rb') as stream:
        stream.seek(0,2);stream.seek(max(0,stream.tell()-n));return stream.read().decode('utf-8','replace').splitlines()
def observe():
    matrix=read(OUT/'matrix_frozen.json');active=read(OUT/'active_position.json')
    group=matrix['groups'][active['position']-1];launch=group['launch'];d=Path(launch['destination'])
    done=[g['position'] for g in matrix['groups'] if (Path(g['launch']['destination'])/'round164_endpoint.json').exists()]
    value=dict(position=group['position'],**group['arm'],completed=len(done),cap=launch['cap_seconds'])
    origin=d/'child_process_origin.json'
    if origin.exists():
        o=read(origin);value.update(PID=o['pid'],elapsed=round(time.time()-o['actual_creation_unix'],1))
    logs=list((d/'external/native_logs').glob('*.gurobi.log'))
    if not logs and (d/'native.log').exists():logs=[d/'native.log']
    if logs:
        log=max(logs,key=lambda p:p.stat().st_mtime)
        value.update(log=log.name,last=[s for s in tail(log) if s.strip()][-2:])
    if (OUT/'runtime_status.json').exists():
        last=read(OUT/'runtime_status.json');a=last['arm']
        value['last_closed']=dict(position=last['position'],id=a['id'],seed=a['seed'],method=a['R164_method'],
            U=a['U'],L=a['L'],state=a['state'])
    value['panel_complete']=(OUT/'panel_complete.json').exists()
    print(json.dumps(value,ensure_ascii=False),flush=True)
if __name__=='__main__':observe()
