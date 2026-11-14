"""Small durable progress readback; never loads models, fleets or observations."""
from round166_common import *
def snapshot():
    active=read(OUT/'active_position.json');g=read(OUT/'matrix_frozen.json')['groups'][active['position']-1]
    d=Path(g['launch']['destination']);fee=read(OUT/'fees'/f'{active["position"]:03}.json')
    complete=[]
    for p in sorted((OUT/'fees').glob('???.json')):
        f=read(p)
        if f['status']=='COMPLETE':
            e=read(ROOT/f['endpoint']['path']);complete.append({k:e.get(k) for k in ['id','method','state','U','L','T_cert','T_produce','T_verify']})
    sample=None
    if (d/'samples.jsonl').exists():
        lines=(d/'samples.jsonl').read_text().splitlines()
        if lines:sample=json.loads(lines[-1])
    return dict(UTC=utc(),active=active,active_outer_seconds=time.time()-fee['start_unix'],status=fee['status'],
        completed=complete,last_sample=sample,panel_complete=(OUT/'panel_complete.json').exists())
if __name__=='__main__':
    if len(sys.argv)>1:
        start=time.monotonic();initial=snapshot()['active']['position']
        while time.monotonic()-start<min(55.,float(sys.argv[1])):
            time.sleep(1)
            if snapshot()['active']['position']!=initial or (OUT/'panel_complete.json').exists():break
    print(json.dumps(snapshot(),ensure_ascii=False,indent=2))
