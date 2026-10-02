"""Registered finite 15-arm zero-Optimize actual type/Start audit."""
from round99_common import *
from round99_start_audit import run
from round99_inner import MODES
if __name__=='__main__':
    camp=OUT/'factorial01';q=read(camp/'identity.json')
    records=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()]
    assert len(records)==18 and all(r['audit_passed'] for r in records)
    arms=[a for a in q['launches'] if a['arm']!='P-GRB'];assert len(arms)==15
    for a in arms:run(a['destination'],f'factorial_start_{a["number"]:02d}',MODES[a['arm']])
    print('finite children=15 model scopes, actual Optimize=0')
