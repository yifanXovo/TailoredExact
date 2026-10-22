"""Bounded publication and receipt closeout; no native work or recovery repetition."""
from round129_common import *
import csv

BRANCH='codex/round129-uniform-pair-support-confirmation'
PARENT='codex/round128-inclusive-root-ablation'

def science():
    assert git('branch','--show-current').decode().strip()==BRANCH
    assert not git('diff','--cached','--name-only').strip(),'Preserve any unrelated staged work'
    manifest=read(OUT/'export_manifest.json')
    paths={r['path'] for r in manifest['files']}|{'results/unified_exact_round129/export_manifest.json'}
    for row in manifest['files']:
        p=ROOT/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['SHA256'],row['path']
    assert not git('diff','--name-only',BASE,'--','src','include','CMakeLists.txt').strip()
    pathfile=TEMP/'science_stage_paths.nul';pathfile.write_bytes(b'\0'.join(p.encode('utf-8') for p in sorted(paths))+b'\0')
    git('add','-f','--pathspec-from-file='+str(pathfile),'--pathspec-file-nul')
    staged=set(git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0'))
    assert staged and staged<=paths,staged-paths
    assert not any(p.startswith(('src/','include/')) or p=='CMakeLists.txt' for p in staged)
    result=git('commit','-m','Round129: complete uniform MS2 confirmation and retain finite evidence')
    commit=git('rev-parse','HEAD').decode().strip()
    write(OUT/'publication_science.json',dict(UTC=utc(),science_commit=commit,branch=BRANCH,base_branch=PARENT,
        measured_parent=BASE,staged_files=len(staged),published_push_pending=True,
        local_export_manifest_SHA=sha(OUT/'export_manifest.json'),normal_commit_no_production_change=True))
    print(result.decode('utf-8',errors='replace'));print(json.dumps(dict(science_commit=commit,staged_files=len(staged))))

def finish():
    science=read(OUT/'publication_science.json');restore=read(OUT/'public_restore_receipt.json')
    cleanup=read(OUT/'cleanup_receipt.json');protect=read(OUT/'review/final_protection_check.json')
    pr=read(OUT/'review/created_PR_readback.json');pdf=read(OUT/'review/pdf_visual_review.json')
    account=read(OUT/'resource_accounting.json');decision=read(OUT/'scientific_decision.json')
    independent=read(OUT/'review/final_independent_evidence.json');obs=read(OUT/'observations.json')
    archives=read(OUT/'raw_archive_manifest.json')['archives'];scan=read(OUT/'review/publication_scan.json')
    assert restore['status']=='PASS' and restore['science_commit']==science['science_commit']
    assert restore['anonymous_public_HTTPS'] and not restore['local_raw_or_old_checkout_fallback']
    assert all(restore[k]==0 for k in ['Optimize','native_starts','compilation'])
    assert cleanup['status']=='PASS' and protect['status']=='PASS'
    assert pr['draft'] and pr['state']=='open' and not pr['merged'] and pr['head_sha']==science['science_commit'] and pr['base']==PARENT
    assert pdf['status']=='PASS' and pdf['PDF_SHA']==sha(OUT/'manuscript.pdf')
    assert account['closed_under_outer_limit'] and not account['closure_pending'] and not budget()['unclosed']
    assert decision['execution']=='COMPLETE' and independent['status']=='PASS'
    assert len(obs['arms'])==len(obs['pairs'])==30 and len(archives)==11 and scan['status']=='PASS'
    assert not git('diff','--name-only',BASE,'--','src','include','CMakeLists.txt').strip()
    assert sha(OUT/'paper_method_config.json')==read(OUT/'manuscript_lineage.json')['inherited_exact_blob_hashes']['results/unified_exact_round126/paper_method_config.json']
    measured=account['exact_subprocess_outer_seconds'];paid=account['paid_outer_seconds']
    note=(f"\n## Actual finite delivery and closure\n\nScience commit `{science['science_commit']}` is published in Draft PR {pr['url']} stacked on `{PARENT}` at `{BASE}`. The first created-PR readback is open, Draft and unmerged with that science head. A small subsequent metadata commit carries these actual delivery receipts; its final remote observation is retained separately to avoid a recursive self-commit claim.\n\n"
        f"Exactly one anonymous public empty-root recovery passed on that science commit: {restore['files']} declared files, {len(restore['archives'])} current archives, and {sum(a['members'] for a in restore['archives'])} indexed raw members. All file/part/member hashes and the isolated portable check pass; zero Optimize, native starts or compilation, no local-raw or historical-carrier fallback. Same-root attempts/failures are retained in review/public_recovery_attempts; no second recovery is performed for metadata.\n\n"
        f"Guarded owned cleanup status: {cleanup['status']}. Its {len(cleanup['actions'])} recorded actions address only declared duplicate archives, inspected regenerable page PNGs, the byte-identical final temporary PDF and this verified recovery expansion. The observed E-volume free-space delta is {cleanup['observed_volume_delta_bytes']} bytes; this is not an exact attributed reclamation measurement. Authoritative raw/models/tables, distinct prior PDFs, failures, original binaries, main user content and old worktrees remain. Main HEAD matches the initial snapshot: {protect['main_head_matches_initial']}; the three initial dirty-file SHA256 values still match: {protect['initial_user_dirty_hashes_still_match']}.\n\n"
        f"Closed outer accounting is {paid:.6f} / 39600 seconds: {measured:.6f} measured nonoverlapping child seconds, the explicit 900-second conservative setup allowance and 60-second final metadata allowance. Formal group outer time is {account['by_kind']['formal']:.6f} seconds; no formal recovery/retry and no production compilation occurred. Nested H/LP/MIP seconds are not added again, and interactive waiting is not claimed as measured CPU. All closed launch/receipt objects are retained in resource_accounting.json without recursively repacking future fees.\n\n"
        "The complete 30-arm confirmation ends here. The recommendation remains a uniform next-paper candidate; actual defaults and historical full-MB identities remain unchanged.\n")
    for name in ['final_report.md','review_actions.md','reproducibility.md']:
        with (OUT/name).open('a',encoding='utf-8') as f:f.write(note)
    body=(OUT/'PR_BODY.md').read_text(encoding='utf-8')
    body=body.replace('One science-commit anonymous empty-root recovery and guarded owned duplicate cleanup will be appended only after their actual receipts; no further experiment is authorized.',
        f"One anonymous empty-root recovery passed at science commit `{science['science_commit']}` ({restore['files']} declared files, 11 current archives, zero Optimize/native starts/compilation, no local fallback). Guarded owned duplicate cleanup passed; unique evidence, user changes and old worktrees are retained. Closed outer accounting is {paid:.3f}/39600 seconds, including explicit 900+60-second setup/metadata allowances and every closed child receipt. No further experiment is authorized.")
    (OUT/'PR_BODY.md').write_text(body,encoding='utf-8')
    (OUT/'RESUME.md').write_text(f"Round129 COMPLETE. Recommendation: {decision['tag']}; current defaults remain full-MB. All30 formal arms/30 typed comparisons and five conditions are complete, separate final review and affected-page PDF review pass. Draft PR {pr['url']}, base {PARENT}, science {science['science_commit']}. One anonymous empty-root recovery and owned duplicate cleanup PASS. Closed accounting {paid:.6f}/39600 seconds (explicit setup900/metadata60 allowances). No more experiments or recovery runs. Final normal metadata push/readback is the remaining short publication action; final post-push observation is local/nonrecursive.\n",encoding='utf-8')
    checks=[
        ('Precommit recipe / once-only unscreened generation','source_recipe.json; preregistration commits; input_manifest.json; independent evidence'),
        ('Same E2 / DLL / frozen argv and production source','E2_identity.json; argv_freeze.json; independent review'),
        ('All30 fixed arms /10 groups; no tuning or retry','experiment_manifest.json; reconstructed group receipts'),
        ('All30 typed comparisons / null open clocks','arms.csv; pairs.csv; independent evidence'),
        ('All five candidate rules and protection','scientific_decision.json; candidate_decision.md'),
        ('Actual H/root/difference and cost attribution','actual_method_differences.json; mechanism_costs.csv'),
        ('Open / reverse / signed-gap / inherited negative evidence retained','final_report.md; manuscript.md; independent review'),
        ('Separate final executor / physical / matrix / certificate chain','review/final_independent_review.md'),
        ('Maintained manuscript / PDF and affected-page QA','manuscript_lineage.json; review/pdf_visual_review.json'),
        ('Current finite publication content scan','review/publication_scan.json; export_manifest.json'),
        ('One anonymous science-commit empty-root recovery','public_restore_receipt.json'),
        ('Owned cleanup / raw and user protection','cleanup_receipt.json; review/final_protection_check.json'),
        ('Closed outer accounting under39600, no double counting','resource_accounting.json'),
        ('One stacked open Draft PR / normal pushes','review/created_PR_readback.json; final local post-push readback'),
    ]
    audit=dict(UTC=utc(),status='COMPLETE_SCIENCE_AND_DELIVERY_FINAL_METADATA_PUSH_PENDING',decision=decision['tag'],
        actual_requirements=[dict(requirement=k,evidence=v,completed=True,scope='actual finite evidence; final normal metadata push/readback remains' if k.startswith('One stacked') else 'actual finite evidence') for k,v in checks],
        scientific_and_delivery_obligations_completed=True,final_short_metadata_push_readback_pending=True,
        no_extra_experiment_or_second_recovery_authorized=True)
    write(OUT/'completion_audit.json',audit)
    (OUT/'completion_audit.md').write_text('# Round129 finite completion audit\n\n'+''.join(f'- PASS: {k}. Evidence: {v}.\n' for k,v in checks)+'\nThe final normal metadata push/readback is recorded locally after this commit, without recursive repacking or a second recovery.\n',encoding='utf-8')
    write(OUT/'delivery_receipt.json',dict(UTC=utc(),status='SCIENCE_AND_DELIVERY_PASS_FINAL_METADATA_PUSH_PENDING',PR=pr['url'],
        science_commit=science['science_commit'],base_branch=PARENT,measured_base_commit=BASE,
        recovery_receipt_SHA=sha(OUT/'public_restore_receipt.json'),cleanup_receipt_SHA=sha(OUT/'cleanup_receipt.json'),
        protection_receipt_SHA=sha(OUT/'review/final_protection_check.json'),resource_accounting_SHA=sha(OUT/'resource_accounting.json'),
        final_postpush_observation_will_be_local=True,no_second_recovery=True))
    print(json.dumps(dict(closeout_written=True,paid_outer_seconds=paid,PR=pr['url'])))

if __name__=='__main__':{'science':science,'finish':finish}[sys.argv[1]]()
