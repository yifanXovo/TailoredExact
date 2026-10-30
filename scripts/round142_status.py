"""Small live receipts and provisional samples only; no evidence/model replay."""
from round142_common import *

def tail(path,maximum=8192):
    if not path.exists():return []
    with path.open('rb') as stream:
        stream.seek(max(0,path.stat().st_size-maximum));data=stream.read()
    return data.decode('utf-8',errors='replace').splitlines()

def status():
    active=read(OUT/'active_position.json');matrix=read(OUT/f'{active["batch"]}_matrix.json')
    group=matrix['groups'][active['position']-1];d=Path(group['launch']['destination'])
    result=dict(active=active,process=light_status(active['fee_label']))
    samples=tail(d/'samples.jsonl');result['sample']=json.loads(samples[-1]) if samples else None
    result['native_tail']=tail(d/'external/native_logs/L0_terminal_mip.gurobi.log')[-3:]
    return result

if __name__=='__main__':
    result=status()
    if '--compact' in sys.argv:
        sample=result['sample'] or {}
        result=dict(arm=result['active']['arm_id'],state=result['process']['state'],
            seconds=sample.get('process_seconds'),U=sample.get('provisional_U'),L=sample.get('provisional_L'),
            native_last=result['native_tail'][-1] if result['native_tail'] else None)
    print(json.dumps(result,ensure_ascii=False))
