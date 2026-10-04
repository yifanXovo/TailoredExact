"""Lightweight whole-process fee ledger; no solver or evidence replay."""
from round102_common import *
from pathlib import Path
def account():
    fees=[];reserved=[];incomplete=[]
    for camp in sorted(OUT.iterdir()):
        p=camp/'identity.json'
        if not p.exists():continue
        q=read(p)
        if 'launches' not in q:continue
        done={r['number']:r for r in (json.loads(x) for x in (camp/'summary.jsonl').read_text().splitlines())} if (camp/'summary.jsonl').exists() else {}
        for arm in q['launches']:
            label=f'{camp.name}/{arm["number"]}/{arm["id"]}/{arm["arm"]}'
            if arm['number'] in done:
                r=done[arm['number']];c=r['completion'];fees.append(dict(label=label,seconds=c['end_to_end_seconds'],starts=1,failed=not r['audit_passed'],
                    process_seconds=c['process_wall_seconds'],stop_reason=c['stop_reason']))
            else:reserved.append(dict(label=label,seconds=arm['cap_seconds'],starts=1,started=Path(arm['destination']).exists()))
        r=camp/'reference_batch_receipt.json'
        if r.exists():fees.append(dict(label=camp.name+'/reference_batch',seconds=read(r)['outer_seconds'],starts=1,Optimize_calls=0))
    for p in (OUT/'fees').glob('*/launch.json'):
        receipt_path=p.parent/'receipt.json'
        if not receipt_path.exists():incomplete.append(str(p.relative_to(OUT)));continue
        r=read(receipt_path);fees.append(dict(label='fees/'+p.parent.name,seconds=r['outer_seconds'],starts=1,failed=r['exit_code']!=0,
            maximum_Optimize_calls=r['maximum_Optimize_calls'],stop_reason=r['stop_reason']))
    seconds=sum(f['seconds'] for f in fees);starts=len(fees);potential_seconds=seconds+sum(f['seconds'] for f in reserved)
    return dict(completed_starts=starts,completed_seconds=seconds,reserved_starts=len(reserved),reserved_seconds=sum(f['seconds'] for f in reserved),
        maximum_plan_starts=starts+len(reserved),maximum_plan_seconds=potential_seconds,within_limits=starts+len(reserved)<=72 and potential_seconds<=80000,
        remaining_starts=72-starts-len(reserved),remaining_seconds=80000-potential_seconds,fees=fees,reserved=reserved,incomplete=incomplete,
        engineering_separate=True,internal_Optimize_not_double_billed=True)
if __name__=='__main__':
    r=account();print(json.dumps(r,indent=2));assert r['within_limits']
