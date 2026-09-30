"""Post-campaign committed-evidence checkpoints, no solver and no splicing."""
import csv,json,sys
from round98_common import *
import round86_native_evidence as evidence

def run(campaign,label):
    camp=OUT/campaign;q=read(camp/'identity.json');rows=[]
    records=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()]
    for r in records:
        l=q['launches'][r['number']-1]
        if l['cap_seconds']<3600:continue
        dest=Path(l['destination']);observations=read(dest/'observations.json');audit=read(dest/'audit.json')
        assert audit['passed']
        for checkpoint in [900,1800,3600]:
            if checkpoint>l['cap_seconds']:continue
            if r['completion']['stop_reason']=='normal_return' and r['completion']['process_wall_seconds']<=checkpoint:
                e=audit['endpoint'];source='same_run_normal_completion_before_checkpoint'
            else:
                prefix=[x for x in observations if x['effective_available_seconds']<=checkpoint]
                a=evidence.audit(ROOT,l['panel'],prefix,q['candidate_binary_sha256'])
                e=dict(U=a['UB'],L=a['LB'],gap=a['gap'],certificate=False);source='same_run_committed_prefix_only'
            rows.append(dict(campaign=campaign,role=l['id'],arm=l['arm'],checkpoint=checkpoint,
                U=e['U'],L=e['L'],gap=e['gap'],certificate=e['certificate'],source=source,
                relative_gap=e['gap']/max(abs(e['U']),1e-12) if e['U'] is not None and e['gap'] is not None else None,
                launch_sha256=sha(dest/'launch.json'),observations_sha256=sha(dest/'observations.json')))
    assert rows
    with (OUT/(label+'.csv')).open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
if __name__=='__main__':run(*sys.argv[1:])
