"""Final bounded source/display confirmation; new receipt only during pack."""
import ast,datetime,hashlib,time
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt
from post_formal_independent import typed_equal

def run():
    tick=time.perf_counter();revision=read(OUT/'engineering/history_direction_editorial_revision.json')
    helper=ROOT/'scripts/round122_finish_report.py';old=OUT/'engineering/report_helper_before_history_clarification.py'
    report=OUT/'final_report.md';old_report=OUT/'engineering/final_report_before_history_clarification.md'
    assert sha(helper)==revision['report_helper_after_SHA']=='48dd2c6e0f9eba0d3d6a05479825d2e47e6af32ac9956a7b28e7982f87f42054'
    assert sha(old)==revision['report_helper_before_SHA']=='3bb701f7510c791634150a1376d435a9804b5c0315564e263ea639b5e7610502'
    added=("historical_R120_C2_Seed0_severe_M_B_loss_retained=True,legacy_historical_field_means_D1_vs_M_B=True,\r\n"
        "        historical_R120_C2_Seed0_comparison=dict(candidate='MB-D1',control='M-B',classification='LOSS',severe=True,M_B_P='WIN',authority='R121 final_report rows67-71'),historical_R121_all_three_new_open=True))").encode()
    removed=b'historical_R120_C2_Seed0_severe_M_B_loss_retained=True,historical_R121_all_three_new_open=True))'
    phrase_new=b'R120 C2 Seed0 severe D1/M-B LOSS is not erased by a Seed1 win.'
    phrase_old=b'R120 C2 Seed0 severe M-B regression is not erased by a Seed1 win.'
    data=helper.read_bytes();assert data.count(added)==data.count(phrase_new)==1
    restored=data.replace(added,removed).replace(phrase_new,phrase_old)
    assert restored==old.read_bytes()
    assert sha(report)==revision['final_report_after_SHA']=='84ede971c3830e003af8578541cbffc25e2931142684df11604d7eb12b8cb97e'
    assert sha(old_report)==revision['final_report_before_SHA']=='a3b79ee7c43ea3875c6439f7708e41ccf690aaf0c06ed2c3dcca902f54815252'
    assert report.read_bytes().replace(phrase_new,phrase_old)==old_report.read_bytes()
    note=read(OUT/'engineering/report_recovery_note_receipt.json')
    assert note['final_report_SHA']==sha(report) and note['reaudit_receipt_SHA']==sha(OUT/'recovery/group08/reaudit_receipt.json')
    ind=read(REVIEW/'post_formal_independent.json');claims=read(REVIEW/'post_formal_prose_claims.json')
    assert ind['decision']==claims['decision']=='ACCEPT'
    for k,n in [('all32_arms_SHA','all32_arms.json'),('all48_pairs_SHA','all48_pairs.json'),('stage_decision_SHA','stage_decision.json')]:assert sha(OUT/n)==ind[k]==revision['after_scientific_SHAs'][n]==revision['before_scientific_SHAs'][n]
    pairs=ind['independent_pairs'];negative=[q for q in pairs if q['classification'] in ['LOSS','MIXED','UNEVALUABLE'] or q['severe_regression']]
    saved=read(OUT/'major_negative_results.json');typed_equal(negative,saved['all_negative_or_mixed_pairs'])
    assert saved['historical_R120_C2_Seed0_severe_M_B_loss_retained'] and saved['legacy_historical_field_means_D1_vs_M_B']
    assert saved['historical_R120_C2_Seed0_comparison']==dict(candidate='MB-D1',control='M-B',classification='LOSS',severe=True,M_B_P='WIN',authority='R121 final_report rows67-71')
    spec=OUT/'paper_algorithm_spec.md';spec_receipt=read(OUT/'engineering/paper_spec_editorial_closeout.json')
    assert sha(spec)==spec_receipt['after_SHA']
    original=spec.read_text(encoding='utf-8');assert original.count(spec_receipt['new_paragraph'])==1
    original=original.replace(spec_receipt['new_paragraph'],spec_receipt['old_paragraph'])
    assert hashlib.sha256(original.encode()).hexdigest()==spec_receipt['before_SHA']=='ad7a2b40113a63b51e950a3a9c5a18872237452711dee4d7d04dc43b67e9a367'
    assert sha(OUT/'paper_result_interpretation.md')==claims['document_SHA']==revision['final_prose_SHA']
    assert sha(OUT/'paper_reference_recommendation.json')==revision['final_reference_SHA']=='377add04a80aac1e1a6b65201f5c93a695b8892341d58a1f90419f9a0caf2078'
    result=dict(decision='ACCEPT',scope='Bounded final editorial direction/spec/report refresh confirmation; source/pair/stage science unchanged; public restore not certified.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),review_script_SHA=sha(__file__),
        report_helper_SHA=sha(helper),final_report_SHA=sha(report),final_prose_SHA=claims['document_SHA'],
        independent_scientific_review_SHA=sha(REVIEW/'post_formal_independent.json'),final_prose_claims_review_SHA=sha(REVIEW/'post_formal_prose_claims.json'),
        new_helper_reverses_exactly_to_preserved_approved_helper=True,new_report_reverses_exactly_to_preserved_approved_report=True,
        all32_all48_stage_bytes_unchanged=True,all9_negative_pair_records_exactly_unchanged=True,
        historical_direction_explicit='R120 C2 Seed0 D1/M-B severe LOSS; M-B/P WIN',
        mathematical_spec_prior_text_exactly_recovered=True,current_spec_SHA=sha(spec),
        specification_receipt_SHA=sha(OUT/'engineering/paper_spec_editorial_closeout.json'),
        interpretation_reference_SHA=sha(OUT/'paper_reference_recommendation.json'),original_recovery_note_unchanged=True,
        native_starts=0,Optimize=0,existing_payload_member_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_editorial_confirmation.json',result)

if __name__=='__main__':run()
