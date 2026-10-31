"""Read only small live metadata and bounded Native tails; never decode raw."""
from round144_common import *
def tail(path,limit=2000):
    if not path.exists():return ''
    with path.open('rb') as f:f.seek(0,2);length=f.tell();f.seek(max(0,length-limit));data=f.read(limit)
    return data.decode('utf-8',errors='replace')
def main():
    a=read(OUT/'active_position.json');g=read(OUT/f'{a["batch"]}_matrix.json')['groups'][a['position']-1];d=Path(g['launch']['destination']);fee=OUT/'fees'/a['fee_label']
    launch=read(fee/'launch.json') if (fee/'launch.json').exists() else None
    receipt=read(fee/'receipt.json') if (fee/'receipt.json').exists() else None
    value=dict(UTC=utc(),arm=a['arm_id'],elapsed_outer_seconds=(receipt['outer_seconds'] if receipt else time.time()-datetime.datetime.fromisoformat(launch['UTC']).timestamp()) if launch else None,
        complete=receipt is not None,receipt=receipt,
        terminal_tail=tail(d/'external/native_logs/L0_terminal_mip.gurobi.log',1200).splitlines()[-4:],stderr=tail(fee/'stderr.log',1200))
    if (d/'external/round144_source.json').exists():value['source']=read(d/'external/round144_source.json')
    if (d/'round135_endpoint.json').exists():
        p=read(d/'round135_endpoint.json');value['endpoint']={k:p.get(k) for k in ['U','L','certificate','T_produce','T_cert','T_verify','T_total','performance_eligible']}
    print(json.dumps(value,ensure_ascii=False))
if __name__=='__main__':main()
