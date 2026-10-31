"""Bounded live status: small metadata and at most 8192 trailing log bytes."""
from round143_common import *

def tail(path,limit=8192):
    if not path.exists():return ''
    with path.open('rb') as f:
        f.seek(0,2);length=f.tell();f.seek(max(0,length-limit));data=f.read(limit)
    return data.decode('utf-8',errors='replace')

def main():
    active=read(OUT/'active_position.json');batch=active['batch'];position=active['position']
    group=read(OUT/f'{batch}_matrix.json')['groups'][position-1];d=Path(group['launch']['destination'])
    folder=OUT/'fees'/active['fee_label'];launch=read(folder/'launch.json') if (folder/'launch.json').exists() else None
    receipt=read(folder/'receipt.json') if (folder/'receipt.json').exists() else None
    status=dict(UTC=utc(),active=active,elapsed_outer_seconds=(receipt['outer_seconds'] if receipt else time.time()-datetime.datetime.fromisoformat(launch['UTC']).timestamp()) if launch else None,
        receipt=receipt,stderr_tail=tail(folder/'stderr.log',1500))
    if (folder/'PID.json').exists():status['process']=_process_status(active['fee_label'])
    if (d/'round135_endpoint.json').exists():
        a=read(d/'round135_endpoint.json');status['endpoint']={k:a.get(k) for k in ['U','L','certificate','T_cert','T_produce','T_verify','T_total','performance_eligible']}
    elif (d/'native.log').exists():status['native_tail']=tail(d/'native.log',3500).splitlines()[-12:]
    if (d/'progress.csv').exists():status['progress_tail']=tail(d/'progress.csv',1500).splitlines()[-2:]
    status['terminal_tail']=tail(d/'external/native_logs/L0_terminal_mip.gurobi.log',3500).splitlines()[-3:]
    if '--compact' in sys.argv:
        status=dict(UTC=status['UTC'],arm=active['arm_id'],elapsed_outer_seconds=status['elapsed_outer_seconds'],
            complete=receipt is not None,endpoint=status.get('endpoint'),terminal_tail=status['terminal_tail'],stderr=status['stderr_tail'])
    print(json.dumps(status,ensure_ascii=False))

def _process_status(label):
    import round140_common
    return round140_common.light_status(label)

if __name__=='__main__':main()
