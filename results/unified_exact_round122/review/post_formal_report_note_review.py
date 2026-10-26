"""Bounded actual final report/table and visible recovery-note cross-check."""
import ast,datetime,hashlib,time
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt
from post_formal_independent import typed_equal

def run():
    tick=time.perf_counter();ind=read(REVIEW/'post_formal_independent.json');assert ind['decision']=='ACCEPT'
    source=ROOT/'scripts/round122_finish_report.py';revision=read(OUT/'engineering/read_only_delivery_revision06.json')
    assert sha(source)==revision['after_SHA']=='3bb701f7510c791634150a1376d435a9804b5c0315564e263ea639b5e7610502'
    text=source.read_bytes();tree=ast.parse(text.decode('utf-8'))
    wrapper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='finish')
    lines=text.splitlines(keepends=True)
    lines[wrapper.lineno-1:wrapper.end_lineno]=[b'def finish():\r\n',b'    with recovery.evidence_view(ROOT):return _finish()\r\n']
    before=b''.join(lines)
    assert hashlib.sha256(before).hexdigest()==revision['before_SHA']=='0203e1c55da255212f4a9b62faff43aa6cc7ce2bad2851a64273fdbad714c9af'
    generated=read(OUT/'engineering/report_receipt.json');note=read(OUT/'engineering/report_recovery_note_receipt.json')
    path=OUT/'final_report.md';report=path.read_text(encoding='utf-8');rr=read(OUT/'recovery/group08/reaudit_receipt.json')
    assert generated['report_script_SHA']==sha(source) and generated['Optimize']==generated['native_starts']==0
    assert note['final_report_SHA']==sha(path) and note['reaudit_receipt_SHA']==sha(OUT/'recovery/group08/reaudit_receipt.json')
    assert note['Optimize']==note['native_starts']==0
    typed_equal(ind['independent_stage'],read(OUT/'stage_decision.json'))
    assert '**COMPLETE / '+ind['independent_stage']['stage']+'**.' in report
    arms=read(OUT/'all32_arms.json');proof=['nonzero_numerical_certificate','independent_zero_certificate','reliable_open_bound','source_reduced_result']
    for a in arms:
        expected=f'| {a["group_number"]} | {a["source"]} | {a["id"]} | {a["V"]} | {a["seed"]} | {a["arm"]} | '+' | '.join(f'{a[k]:.10g}' for k in ['U','L','gap'])+' | '+' | '.join(str(int(a[k])) for k in proof)+' | '+' | '.join(f'{a[k]:.8g}' for k in ['T_produce','T_verify','T_total'])+' |'
        assert report.count(expected)==1
    for p in ind['independent_pairs']:
        expected=f'| {p["group_number"]} | {p["id"]} | {p["seed"]} | {p["candidate"]}/{p["control"]} | {p["classification"]} | {p["severe_regression"]} | {p["basis"]} |'
        assert report.count(expected)==1
    fragments=['Group08 cold P-GRB required a read-only legacy-auditor recovery after normal producer exit.',
        'original failed formal08 fee/audit and every original P file are preserved; recovered sidecars are separate.',
        'The final own U remains '+repr(rr['final_U'])+'; the smaller committed historical witness was not substituted.',
        'T_produce remains '+repr(rr['T_produce'])+'s, while T_verify='+repr(rr['T_verify'])+'s and T_total='+repr(rr['T_total'])+'s include failed verification, investigation and the full waiting interval.',
        'Only the original never-started fourth D1 position continued; no producer was rerun.']
    assert all(report.count(q)==1 for q in fragments)
    result=dict(decision='ACCEPT',scope='Actual report main tables, stage and visible group08 recovery note only; independent scientific review is separately bound.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),review_script_SHA=sha(__file__),
        independent_post_formal_review_SHA=sha(REVIEW/'post_formal_independent.json'),final_report_SHA=sha(path),
        report_helper_SHA=sha(source),report_revision06_SHA=sha(OUT/'engineering/read_only_delivery_revision06.json'),
        original_report_body_exact_prior_bytes_reconstructed=True,actual_note_receipt_SHA=sha(OUT/'engineering/report_recovery_note_receipt.json'),
        main_table_rows_checked=32,directed_pair_rows_checked=48,stage=ind['independent_stage']['stage'],
        recovery_note_matches_actual_sealed_evidence=True,original_failure_and_gap_disclosed=True,
        native_starts=0,Optimize=0,raw_or_helper_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_report_note_review.json',result)

if __name__=='__main__':run()
