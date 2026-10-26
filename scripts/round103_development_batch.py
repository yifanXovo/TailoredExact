"""Finite serial C2/N2/C3 protection plan, unchanged production candidate.

Every solve/reference receives its own existing campaign receipt. This
orchestrator never retries, regenerates confirmation, or selects by outcomes.
"""
from round103_campaign import prepare,run
from round103_common import *
from round100_idle import ensure_idle

if __name__=='__main__':
    ensure_idle()
    assert not (OUT/'development01').exists() and not (OUT/'protection_C3').exists()
    assert read(OUT/'production_freeze.json')['source_bindings']==bindings()
    write(OUT/'development_batch_plan.json',dict(
        stages=[dict(name='development01',physical_reference_children=2,arms=6,cap_seconds=1800),
                dict(name='protection_C3',physical_reference_children=1,arms=3,cap_seconds=1800)],
        sequential=True,no_retries=True,no_candidate_revision=True,
        production_freeze_sha256=sha(OUT/'production_freeze.json'),wrapper_sha256=sha(__file__)))
    subprocess.run([sys.executable,str(ROOT/'scripts/round103_prepare.py'),'development01'],cwd=ROOT,check=True)
    prepare('development01',OUT/'development01_protocol.json')
    for number in range(1,7):run('development01',number)
    prepare('protection_C3',OUT/'protection_C3_protocol.json')
    for number in range(1,4):run('protection_C3',number)
    print('Completed all nine development/protection arms; no confirmation started.',flush=True)
