"""Finalize only wrapper receipt bindings, retaining all pre-qualification bytes."""
from round108_common import *
import round108_campaign as campaign

def run():
    assert read(OUT/'qualification/identity.json')['passed']
    d=OUT/'engineering/wrapper_time_receipt01'
    old=read(d/'candidate_identity_before.json')
    assert old['source_bindings']==bindings()
    assert old['production_PE_SHA']==sha(BUILD/'ExactEBRP.exe') and old['DLL_SHA']==sha(DLL)
    for name,backup in [('bridge01','bridge_identity_before.json'),('confirmation01','confirmation_identity_before.json')]:
        q=read(d/backup);assert q['source_hashes']==bindings()
        assert all(not Path(x['destination']).exists() for x in q['launches'])
        assert q['launches']==read(OUT/name/'identity.json')['launches']
        (OUT/name/'identity.json').rename(OUT/name/'identity_pre_wrapper_receipt01.json')
        q.update(runner_sha256=sha(ROOT/'scripts/round108_campaign.py'),helpers=campaign.helpers(),
            final_wrapper_receipt_source_SHA=sha(ROOT/'scripts/round108_campaign.py'))
        write(OUT/name/'identity.json',q)
    (OUT/'candidate_identity.json').rename(OUT/'candidate_identity_pre_wrapper_receipt01.json')
    old.update(helpers=campaign.helpers(),actual_CLI_qualification_SHA=sha(OUT/'qualification/identity.json'),
        full_argv={name:[x['command'] for x in read(OUT/name/'identity.json')['launches']] for name in ['bridge01','confirmation01','qualification/cli01']},
        whole_arm_time_receipt='Wrapper before admission checks through durable post-audit after-record; overhead receipt included in outer fee',
        decision_reader_SHA=sha(ROOT/'scripts/round108_decisions.py'),
        wrapper_receipt_compatibility_repair_only=True,algorithm_performance_parameters_changed=False,
        zero_objective_tolerance=1e-12,complete_cover_closure_tolerance=1e-7,
        planned_total_conservative_starts=44,planned_confirmation_management='one wrapper per complete three-arm role; permits frozen cancellation between groups',
        phase='final pre-first-formal freeze')
    write(OUT/'candidate_identity.json',old)
    write(d/'receipt.json',dict(passed=True,engineering=True,Optimize_calls=0,IIS_calls=0,compiler_calls=0,
        production_PE_unchanged=True,source_unchanged=True,full_argv_unchanged=True,
        sole_change='Measure complete per-arm wrapper duration including postexit audit/write/check costs',
        before_campaign_SHA=sha(d/'round108_campaign_before.py'),after_campaign_SHA=sha(ROOT/'scripts/round108_campaign.py'),
        original_CLI_qualification_kept=True,no_formal_arm_started=True,
        updated_candidate_SHA=sha(OUT/'candidate_identity.json')))
    print('final current-PE candidate/21 argv and complete wrapper times frozen; no Optimize',flush=True)

if __name__=='__main__':run()
