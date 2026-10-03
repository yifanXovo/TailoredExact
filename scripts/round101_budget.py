"""Lightweight nonduplicated fee accounting, including reserved formal caps.
Reads receipts only; no native engine, certificate replay, compression or compile.
This is experiment management and is never called from production C++.
"""
import json
from round101_common import *

def account():
    fees=[];reserved=[];incomplete=[]
    for camp in sorted(OUT.iterdir()):
        identity=camp/'identity.json'
        if not camp.is_dir() or not identity.exists():continue
        q=read(identity)
        if 'launches' not in q:continue
        done={r['number']:r for r in (json.loads(x) for x in (camp/'summary.jsonl').read_text().splitlines())} if (camp/'summary.jsonl').exists() else {}
        for arm in q['launches']:
            label=f'{camp.name}/{arm["number"]}/{arm["id"]}/{arm["arm"]}'
            if arm['number'] in done:
                c=done[arm['number']]['completion']
                fees.append(dict(label=label,starts=1,seconds=c['end_to_end_seconds'],process_seconds=c['process_wall_seconds']))
            else:
                reserved.append(dict(label=label,starts=1,seconds=arm['cap_seconds'],started=Path(arm['destination']).exists()))
        batch=camp/'reference_batch_receipt.json'
        if batch.exists():
            c=read(batch);fees.append(dict(label=camp.name+'/reference_batch',starts=1,seconds=c['outer_seconds']))
        else:
            for p in (camp/'reference').glob('*/completion.json'):
                c=read(p)
                if not c.get('copy_only'):fees.append(dict(label=camp.name+'/reference/'+p.parent.name,starts=1,seconds=c['outer_seconds']))
    for category in ['qualification','diagnostic_receipts']:
        for p in (OUT/category).glob('*/receipt.json'):
            c=read(p);fees.append(dict(label=category+'/'+p.parent.name,starts=1,seconds=c['outer_seconds'],failed=c['exit_code']!=0))
        for p in (OUT/category).glob('*/launch.json'):
            if not (p.parent/'receipt.json').exists():incomplete.append(str(p.relative_to(OUT)))
    used=sum(f['seconds'] for f in fees);starts=sum(f['starts'] for f in fees)
    maximum=used+sum(r['seconds'] for r in reserved);maximum_starts=starts+len(reserved)
    return dict(completed_charged_starts=starts,completed_charged_seconds=used,
        reserved_starts=len(reserved),reserved_cap_seconds=sum(r['seconds'] for r in reserved),
        maximum_current_plan_starts=maximum_starts,maximum_current_plan_seconds=maximum,
        remaining_after_current_plan_starts=72-maximum_starts,remaining_after_current_plan_seconds=80000-maximum,
        within_limits=maximum_starts<=72 and maximum<=80000,fees=fees,reserved=reserved,
        incomplete_receipt_batches=incomplete,internal_Optimize_calls_not_double_billed=True,
        conservatism='Formal starts charged with full completion time including prelaunch; qualification pure/replay batches also counted. Engineering/offline audits separate.')

if __name__=='__main__':
    report=account();print(json.dumps(report,indent=2));assert report['within_limits']
