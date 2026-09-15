"""Read-only compact progress snapshot; never a formal checkpoint or algorithm gate."""
import json
import csv
import re
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round78/campaign'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
a=read(OUT/'active_experiment.json');folder=ROOT/a['destination']
out=dict(arm=a['arm'],launch=a['number'],elapsed_seconds=round(time.time()-a['started_unix'],1),
    campaign_lock_present=(OUT/'active_run.lock').exists(),committed_events=len(list((folder/'journal').glob('*.commit'))))
if (folder/'phases.csv').exists():
    with (folder/'phases.csv').open(encoding='utf-8',newline='') as f: phases=list(csv.DictReader(f))
    if phases:out['latest_phase']={k:phases[-1].get(k) for k in ['event','status','detail']}
if (OUT/'summary.json').exists():
    s=read(OUT/'summary.json');out['completed']=s['completed']
    out['completed_endpoints']=[dict(arm=r['arm'],valid=r['audit']['passed'],endpoint=r['audit'].get('endpoint')) for r in s['records']]
logs=list((folder/'external/native_logs').glob('*.log'))+[folder/'native.log']
logs=[p for p in logs if p.exists() and p.stat().st_size]
if logs:
    p=max(logs,key=lambda x:x.stat().st_mtime_ns)
    with p.open('rb') as f:
        f.seek(max(0,p.stat().st_size-4096));lines=f.read().decode('utf-8',errors='replace').splitlines()
    progress=[s.strip() for s in lines if re.match(r'\s*[H*]?\s*\d+\s+\d+',s)]
    out['native_log']=str(p.relative_to(ROOT));out['latest_native_progress']=progress[-1] if progress else lines[-1] if lines else None
out['scope']='Unreviewed live progress; formal observed checkpoints are produced only by the frozen driver/audit.'
print(json.dumps(out,ensure_ascii=True))
