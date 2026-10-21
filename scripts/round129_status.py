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
                progress=d/'progress.csv'
                last=progress.read_text(encoding='utf-8',errors='replace').splitlines()[-1:] if progress.exists() else []
                active.append(dict(group=g['number'],id=l['id'],seed=l['seed'],method=l['method'],origin=origin,progress=last,
                    producer_sealed=(d/'producer_seal.json').exists(),producer_receipt=(d/'producer_receipt.json').exists()))
    value=dict(UTC=utc(),sealed_arms=len(sealed),last_sealed=sealed[-3:],active=active,budget=budget())
    print(json.dumps(value,ensure_ascii=False))
    return value

if __name__=='__main__':snapshot()
