"""Bounded operational metadata; no model, journal or result parsing."""
from pathlib import Path
import datetime,json,time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round127'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))

def status():
    active=[]
    for launch in sorted((OUT/'fees').glob('*/launch.json')):
        if (launch.parent/'receipt.json').exists():continue
        fee=read(launch);command=fee.get('command',[])
        entry=dict(fee=launch.parent.name,kind=fee['kind'])
        if len(command)>=4 and command[2].replace('\\','/')=='scripts/round127_campaign.py':
            group=OUT/command[3]
            for origin in sorted((group/'raw').glob('*/child_process_origin.json')):
                d=origin.parent
                if (d/'producer_receipt.json').exists():continue
                native=read(origin)
                entry.update(active_arm=d.name,native_pid=native['pid'],
                    seconds_since_native_creation=time.time()-native['actual_creation_unix'],
                    note='Operational age only; not T_produce, a result or a proof.')
        active.append(entry)
    return dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),active_fees=active,
        sealed_formal_arms=sum(1 for stage in ['main','tiny','core']
            for _ in (OUT/stage).glob('*/raw/*/arm_total_receipt.json')),
        sealed_groups={stage:sum((p/'reconstructed.json').exists() for p in (OUT/stage).iterdir() if p.is_dir())
            for stage in ['main','tiny','core']},models_journals_results_read=0)

if __name__=='__main__':print(json.dumps(status()))
