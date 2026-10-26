"""Read-only finite source reconstruction of the new report/replay views."""
from pathlib import Path
import ast,datetime,hashlib,time
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt

def run():
    tick=time.perf_counter();receipt=read(OUT/'engineering/read_only_delivery_revision05.json')
    report=ROOT/'scripts/round122_finish_report.py';release=ROOT/'scripts/round122_release.py'
    for name in [report,release]:assert sha(name)==receipt['after_SHA'][name.relative_to(ROOT).as_posix()]
    text=report.read_text(encoding='utf-8');wrapper='def finish():\n    with recovery.evidence_view(ROOT):return _finish()\n\n'
    assert text.count(wrapper)==1 and text.count('import round122_group08_recovery as recovery\n')==1
    original=text.replace('import round122_group08_recovery as recovery\n','').replace(wrapper,'').replace('def _finish():','def finish():')
    assert hashlib.sha256(original.encode()).hexdigest()==receipt['before_SHA']['scripts/round122_finish_report.py']=='ca7058e870af0ce80e1ed8d8313b1b7514575288f38dc5f0f06916f632e29546'
    text=release.read_text(encoding='utf-8');tree=ast.parse(text)
    replay=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='restored_check')
    views=[n for n in replay.body if isinstance(n,ast.With)]
    assert len(views)==1 and ast.unparse(views[0].items[0].context_expr)=='recovery.evidence_view(root)'
    view=views[0];assert len(view.body)==1 and isinstance(view.body[0],ast.For)
    assert ast.unparse(view.body[0].iter)=='range(1, 9)'
    lines=text.splitlines(keepends=True);lines[view.lineno-1:view.end_lineno]=[s[4:] for s in lines[view.lineno:view.end_lineno]]
    original=''.join(lines).replace('import round122_group08_recovery as recovery\n','')
    assert hashlib.sha256(original.encode()).hexdigest()==receipt['before_SHA']['scripts/round122_release.py']=='9bc6c8ac8ff1a9b9498e6044b7c751b4911285b1fe71d5bcb9113561b0356d14'
    candidate=read(OUT/'candidate_identity.json')
    assert all(n not in candidate['helpers'] for n in ['scripts/round122_group08_recovery.py','scripts/round122_finish_report.py','scripts/round122_release.py'])
    result=dict(decision='PENDING',scope='Actual bounded static reconstruction of unmeasured report/replay recovery-path changes; no final formal review or restore executed.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        review_script_SHA=sha(__file__),parent_revision_receipt_SHA=sha(OUT/'engineering/read_only_delivery_revision05.json'),
        current_sources={p.relative_to(ROOT).as_posix():sha(p) for p in [report,release]},
        independently_recovered_exact_prior_bytes_SHA=receipt['before_SHA'],
        original_report_body_exactly_unchanged=True,original_replay_validation_exactly_unchanged=True,
        change='Only import the unmeasured recovery adapter and apply its read view around the unchanged report body / eight-group reconstruction loop.',
        public_export_and_empty_root_restore='PENDING_ACTUAL_EXECUTION_AFTER_ALL32_AND_SCIENCE_PUSH',
        actual_post_formal_review='PENDING_ALL_EIGHT_SEALED_GROUPS_AND_REPORTS',
        evolving_formal_raw_read=False,native_starts=0,Optimize=0,production_or_measured_helper_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('delivery_recovery_static_review.json',result)

if __name__=='__main__':run()
