"""Run the three once-frozen conditional groups, serially and without revision.

Admission is a recorded research decision, not default adoption. This wrapper
does not redraw inputs, tune the candidate, retry an arm or stitch budgets.
"""
from round103_campaign import prepare,run
from round103_common import *
from round103_budget import account
from round100_idle import ensure_idle

if __name__=='__main__':
    ensure_idle();decision=read(OUT/'stage_decision.json')
    assert decision['decision']=='admit' and decision['no_candidate_revision']
    assert decision['candidate_default_enabled'] is False
    freeze=read(OUT/'confirmation_freeze.json')
    assert freeze['before_any_confirmation_search'] and freeze['no_redraw']
    assert freeze['production_freeze_sha256']==sha(OUT/'production_freeze.json')
    assert read(OUT/'production_freeze.json')['source_bindings']==bindings()
    names=['confirmation01','confirmation_long01','long_tail01']
    assert [s['name'] for s in freeze['stages']]==names
    assert all(not (OUT/name).exists() for name in names)
    for stage in freeze['stages']:assert sha(ROOT/stage['path'])==stage['sha256']
    budget=account();assert not budget['incomplete'] and not budget['reserved']
    # Nine full arms and three physical reference children. All reader fees
    # already incurred remain charged; future readers have ample reserve.
    assert budget['completed_starts']+12+4<=72
    assert budget['completed_seconds']+24300+180+2400<=80000
    write(OUT/'confirmation_batch_plan.json',dict(stages=names,arms=9,physical_reference_children=3,
        planned_arm_cap_seconds=24300,sequential=True,no_retries=True,no_redraw=True,
        no_candidate_revision=True,production_freeze_sha256=sha(OUT/'production_freeze.json'),
        confirmation_freeze_sha256=sha(OUT/'confirmation_freeze.json'),
        admission_sha256=sha(OUT/'stage_decision.json'),wrapper_sha256=sha(__file__),
        budget_before_batch=budget))
    for name in names:
        stage=next(s for s in freeze['stages'] if s['name']==name)
        prepare(name,ROOT/stage['path'])
        for number in range(1,4):run(name,number)
        print(json.dumps(dict(completed_group=name,budget=account())),flush=True)
    print('All three frozen confirmation/long groups completed; candidate/default unchanged.',flush=True)
