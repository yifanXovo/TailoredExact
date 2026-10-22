"""Read only compact progress; never launch or resume a producer."""
from round130_common import *

def main():
    protocol=read(OUT/'experiment_manifest.json');finished=[];current=None
    for g in protocol['groups']:
        camp=OUT/g['name']
        if not (camp/'identity.json').exists():continue
        for l in read(camp/'identity.json')['launches']:
            d=Path(l['destination'])
            if (d/'arm_total_receipt.json').exists():
                r=read(d/'result.json');q=read(d/'producer_receipt.json')
                finished.append(dict(id=l['id'],seed=l['seed'],method=l['method'],T_produce=q['T_produce'],raw_status=r['status']))
            elif current is None:
                current=dict(group=g['name'],id=l['id'],seed=l['seed'],method=l['method'],producer_sealed=(d/'producer_seal.json').exists(),
                    destination=str(d),native_result_closed=(d/'completion.json').exists())
                if (d/'child_process_origin.json').exists():
                    origin=read(d/'child_process_origin.json')
                    current.update(pid=origin['pid'],age_seconds=time.time()-origin['actual_creation_unix'])
                p=d/'native.log'
                if p.exists():
                    with p.open('rb') as f:
                        f.seek(max(0,p.stat().st_size-2500));lines=f.read().decode('utf-8',errors='replace').splitlines()
                    current['native_log_tail']=lines[-5:]
    b=budget()
    if b['unclosed']:
        launch=read(OUT/'fees'/b['unclosed'][0]/'launch.json')
        live=max(0,time.time()-datetime.datetime.fromisoformat(launch['UTC']).timestamp())
        b.update(active_outer_seconds=live,paid_plus_active_seconds=b['paid_outer_seconds']+live)
    text=dict(UTC=utc(),finished_arms=len(finished),total_arms=24,last_completed=finished[-4:],current=current,budget=b)
    print(json.dumps(text,ensure_ascii=False))
if __name__=='__main__':main()
