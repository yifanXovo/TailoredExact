"""Reconcile closed outer receipts and nested starts without double billing."""
from round104_common import *
import csv

def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []

def main():
    from round100_idle import ensure_idle
    ensure_idle();rows=[]
    for d in sorted((OUT/'fees').iterdir()):
        if not d.is_dir():continue
        launch=read(d/'launch.json');r=read(d/'receipt.json');cmd=launch['command']
        native=aux=dp=nested=0;scope='finite diagnostic reader/process'
        if any(s.endswith(('round104_observe.py','round104_campaign.py')) for s in cmd):
            action_index=next(i for i,s in enumerate(cmd) if s.endswith(('round104_observe.py','round104_campaign.py')))+1
            action,name=cmd[action_index:action_index+2];camp=OUT/name
            if action=='prepare':
                nested=len(list((camp/'reference').glob('*/completion.json')))
                assert all(read(p)['optimizer_calls']==0 for p in (camp/'reference').glob('*/completion.json'))
                scope='reference-builder children, no Optimize; all child time within parent receipt'
            else:
                number=int(cmd[action_index+2]);q=read(camp/'identity.json');a=q['launches'][number-1]
                dest=Path(a['destination']);audit=read(dest/'audit.json')
                assert audit['passed'];native=audit['native_calls_started'];h=audit.get('resource_hull',{})
                aux=h.get('auxiliary_Optimize_calls',0);dp=h.get('DP_calls',0);nested=1
                scope='complete native process, auxiliary generation and postexit audit paid by parent receipt'
        else:
            diag=OUT/'diagnostics'/d.name
            for path in diag.rglob('*calls.jsonl') if diag.exists() else []:
                if path.name=='oracle_calls.jsonl':continue
                aux+=sum(s.get('event')=='Optimize_begin' for s in lines(path))
            for path in diag.rglob('oracle_attempts.jsonl') if diag.exists() else []:
                dp+=sum(s.get('event')=='begin' for s in lines(path))
            nested+=len(list(diag.rglob('oracle_identity.json'))) if diag.exists() else 0
            nested+=len(list(diag.glob('*.cpp.json'))) if diag.exists() else 0
            supplement=diag/'fee_supplement.json'
            if supplement.exists():
                s=read(supplement);aux+=s.get('additional_Optimize_calls',0);dp+=s.get('additional_DP_calls',0)
                nested+=s.get('additional_child_starts',0)
        rows.append(dict(label=d.name,exit_code=r['exit_code'],failed=r['exit_code']!=0,stop_reason=r['stop_reason'],
            charged_outer_seconds=r['outer_seconds'],wrapper_starts=1,known_nested_process_starts=nested,
            conservative_counted_starts=1+nested,native_Optimize_calls=native,auxiliary_Optimize_calls=aux,DP_calls=dp,
            launch_sha256=sha(d/'launch.json'),receipt_sha256=sha(d/'receipt.json'),scope=scope))
    starts=sum(r['conservative_counted_starts'] for r in rows);seconds=sum(r['charged_outer_seconds'] for r in rows)
    assert starts<=72 and seconds<=80000
    engineering=[]
    for p in sorted((OUT/'engineering').glob('*/receipt.json')):
        r=read(p);engineering.append(dict(label=p.parent.name,**r,receipt_sha256=sha(p)))
    target=OUT/'fees.csv'
    with target.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=dict(wrapper_starts=len(rows),known_nested_process_starts=sum(r['known_nested_process_starts'] for r in rows),
        conservative_counted_starts=starts,charged_outer_seconds=seconds,
        native_Optimize_calls=sum(r['native_Optimize_calls'] for r in rows),auxiliary_Optimize_calls=sum(r['auxiliary_Optimize_calls'] for r in rows),
        DP_calls=sum(r['DP_calls'] for r in rows),failed_paid_labels=[r['label'] for r in rows if r['failed']],
        ceiling_starts=72,ceiling_outer_seconds=80000,nested_seconds_added_again=0,
        engineering=engineering,accounting='wrapper process wall time includes every sequential child and postexit audit; separate conservative starts count wrapper plus observed child starts, not Optimize iterations',
        source_sha256=sha(__file__),fee_csv_sha256=sha(target))
    write(OUT/'fees_summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='engineering'}))

if __name__=='__main__':main()
