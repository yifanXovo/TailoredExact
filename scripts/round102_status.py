"""Read-only compact campaign status; no solver, audit, or experimentation."""
import json, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
camp = root / 'results/unified_exact_round102' / sys.argv[1]
records = [json.loads(s) for s in (camp / 'summary.jsonl').read_text().splitlines()] if (camp / 'summary.jsonl').exists() else []
identity = json.loads((camp / 'identity.json').read_text())
active = [a for a in identity['launches'] if a['number'] > len(records) and Path(a['destination']).exists()]
out = dict(campaign=camp.name, completed=len(records), planned=len(identity['launches']))
if records:
    r = records[-1]
    out['last_complete'] = dict(arm=r['arm'], id=r['id'], endpoint=r['endpoint'], audit_passed=r['audit_passed'])
if active:
    a = active[-1]
    dest = Path(a['destination'])
    out['active'] = dict(number=a['number'], id=a['id'], arm=a['arm'])
    path = dest / 'samples.jsonl'
    if path.exists():
        lines = path.read_text().splitlines()
        if lines:
            s = json.loads(lines[-1])
            out['active'].update({k:s.get(k) for k in ['process_seconds', 'provisional_U', 'provisional_L', 'provisional_gap']})
    path = dest / 'affinity.json'
    if path.exists():
        out['active']['pid'] = json.loads(path.read_text()).get('pid')
print(json.dumps(out, separators=(',', ':')))
