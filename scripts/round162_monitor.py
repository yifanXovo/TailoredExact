"""Lightweight current-panel observation; never launches or validates a solve."""
from pathlib import Path
import json,time,sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round162'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def tail(path,limit=8192):
    with path.open('rb') as stream:
        stream.seek(0,2);stream.seek(max(0,stream.tell()-limit));return stream.read().decode('utf-8','replace').splitlines()

def observe():
    current=read(OUT/'complete_active_position.json');matrix=read(OUT/'complete_matrix.json')
    group=matrix['groups'][current['position']-1];launch=group['launch'];dest=Path(launch['destination'])
    origin=dest/'child_process_origin.json'
    state=dict(position=current['position'],role=launch['id'],method=launch['R162_method'],cap=launch['cap_seconds'],
        completed=[g['position'] for g in matrix['groups'] if (Path(g['launch']['destination'])/'round162_endpoint.json').exists()])
    if origin.exists():
        p=read(origin);state.update(PID=p['pid'],elapsed=round(time.time()-p['actual_creation_unix'],1))
    phase=dest/'phases.csv'
    if phase.exists():state['phase']=tail(phase)[-1:]
    logs=list((dest/'external/native_logs').glob('*.gurobi.log'))
    if logs:
        log=max(logs,key=lambda p:p.stat().st_mtime);lines=[v for v in tail(log) if v.strip()]
        state.update(native_log=log.name,last_native_lines=lines[-3:])
    events=dest/'external/paper_tree_events.csv'
    if events.exists():state['last_tree_event']=tail(events)[-1:]
    status=OUT/'complete_runtime_status.json'
    if status.exists():
        last=read(status);a=last['arm'];state['last_closed']=dict(arm_id=last['arm_id'],U=a['U'],L=a['L'],certificate=a['certificate'])
    if '--compact' in sys.argv:
        state={k:state[k] for k in ('position','method','elapsed','completed') if k in state}|dict(
            native=state.get('native_log'),last=state.get('last_native_lines',[])[-1:])
    print(json.dumps(state,ensure_ascii=False),flush=True)

if __name__=='__main__':observe()
