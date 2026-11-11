"""Compact metadata-only panel monitor; no validation or Optimize."""
from pathlib import Path
import json,time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round163'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def tail(p,n=4096):
    with p.open('rb') as f:
        f.seek(0,2);f.seek(max(0,f.tell()-n));return f.read().decode('utf-8','replace').splitlines()
def observe():
    m=read(OUT/'matrix_frozen.json');a=read(OUT/'active_position.json');g=m['groups'][a['position']-1];l=g['launch'];d=Path(l['destination'])
    closed=[q['position'] for q in m['groups'] if (Path(q['launch']['destination'])/'round163_endpoint.json').exists()]
    value=dict(position=g['position'],id=l['id'],method=l['R163_method'],completed=closed,cap=l['cap_seconds'])
    p=d/'child_process_origin.json'
    if p.exists():
        origin=read(p);value.update(PID=origin['pid'],elapsed=round(time.time()-origin['actual_creation_unix'],1))
    logs=list((d/'external/native_logs').glob('*.gurobi.log'))
    if not logs and (d/'native.log').exists():logs=[d/'native.log']
    if logs:
        p=max(logs,key=lambda p:p.stat().st_mtime);value.update(log=p.name,last=[s for s in tail(p) if s.strip()][-2:])
    if (OUT/'panel_complete.json').exists():value['complete']=True
    if (OUT/'runtime_status.json').exists():
        v=read(OUT/'runtime_status.json');arm=v['arm'];value['last_closed']=dict(position=v['position'],method=arm['R163_method'],U=arm['U'],L=arm['L'],state=arm['state'])
    print(json.dumps(value,ensure_ascii=False),flush=True)
if __name__=='__main__':observe()
