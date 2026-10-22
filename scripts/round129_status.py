"""Small retained-receipt snapshot; no matrix reads, hashing or solver calls."""
from round129_common import *

def snapshot():
    sealed=[];active=[]
    for g in read(OUT/'experiment_manifest.json')['groups']:
        i=OUT/g['name']/'identity.json'
        if not i.exists():continue
        for l in read(i)['launches']:
            d=Path(l['destination'])
            if (d/'arm_total_receipt.json').exists():
                r=read(d/'producer_receipt.json');sealed.append(dict(group=g['number'],id=l['id'],seed=l['seed'],method=l['method'],T_produce=r['T_produce']))
            elif d.exists():
                origin=read(d/'child_process_origin.json') if (d/'child_process_origin.json').exists() else None
                if origin:origin={k:origin[k] for k in ['pid','parent_pid','actual_creation_unix','PE_SHA']}
                progress=d/'progress.csv'
                last=progress.read_text(encoding='utf-8',errors='replace').splitlines()[-1:] if progress.exists() else []
                logs=list((d/'external/native_logs').glob('*.gurobi.log')) if l['method']!='P' else [d/'native.log']
                logs=[p for p in logs if p.is_file()]
                native=[]
                if logs:
                    log=max(logs,key=lambda p:p.stat().st_mtime)
                    with log.open('rb') as f:
                        f.seek(max(0,log.stat().st_size-4096));native=f.read().decode('utf-8',errors='replace').splitlines()[-2:]
                active.append(dict(group=g['number'],id=l['id'],seed=l['seed'],method=l['method'],origin=origin,progress=last,
                    native_log_tail=native,producer_sealed=(d/'producer_seal.json').exists(),producer_receipt=(d/'producer_receipt.json').exists()))
    b=budget()
    live=[dict(label=n,elapsed_since_launch_seconds=time.time()-read(OUT/'fees'/n/'PID.json')['launched_unix'])
          for n in b['unclosed'] if (OUT/'fees'/n/'PID.json').exists()]
    value=dict(UTC=utc(),sealed_arms=len(sealed),last_sealed=sealed[-3:],active=active,budget=b,
        pending_meter_elapsed=live,pending_elapsed_not_yet_in_closed_budget=True)
    print(json.dumps(value,ensure_ascii=False))
    return value

if __name__=='__main__':snapshot()
