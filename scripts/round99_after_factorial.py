"""Explicit registered transition: completed factorial -> zero-call audit -> 4 repeats."""
import subprocess
from round99_common import *
import round99_campaign as campaign
if __name__=='__main__':
    records=[json.loads(s) for s in (OUT/'factorial01/summary.jsonl').read_text().splitlines()]
    assert len(records)==18 and all(r['audit_passed'] for r in records)
    campaign.ext.ensure_idle()
    python=ROOT/'build/research/round88-ot/venv/Scripts/python.exe'
    receipt('start_audit01',[python,ROOT/'scripts/round99_actual_start_batch.py'],kind='qualification',cap=240,optimizer_calls=0)
    p=dict(next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']=='F2'))
    p['method_order']=['R2','R1','M-B','Q-I'];p['cap_seconds']=900
    path=OUT/'repeat_protocol01.json';write(path,dict(roles=[p],phase='finite matched factor repeat',registered_plan_sha256=sha(OUT/'repeat_plan.md')))
    campaign.prepare('repeat01',path)
    for number in range(1,5):campaign.run('repeat01',number)
