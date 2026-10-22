"""Normal staged publication and receipt closeout; never starts native work."""
from round130_common import *
from round130_closeout import safe_git

BRANCH = 'codex/round130-ms2-paper-attribution'
PARENT = 'codex/round129-uniform-pair-support-confirmation'


def source_guard():
    identity()
    frozen_source = read(OUT/'preformal_source_provenance.json')['source_commit']
    assert not safe_git('diff', '--name-only', frozen_source, '--', 'src', 'include', 'CMakeLists.txt').strip()
    changed = set(safe_git('diff', '--name-only', BASE, '--', 'src', 'include', 'CMakeLists.txt').decode().splitlines())
    assert changed == {'include/Round127Research.hpp', 'src/GurobiBaseline.cpp'}, changed
    return frozen_source


def science():
    assert safe_git('branch', '--show-current').decode().strip() == BRANCH
    assert not safe_git('diff', '--cached', '--name-only').strip(), 'Preserve unrelated staged work'
    source_guard()
    manifest = read(OUT/'export_manifest.json')
    paths = {row['path'] for row in manifest['files']} | {
        'results/unified_exact_round130/export_manifest.json',
        'results/unified_exact_round130/review/loose_publication_scan.json'}
    for row in manifest['files']:
        p = ROOT/row['path']
        assert p.stat().st_size == row['bytes'] and sha(p) == row['SHA256'], row['path']
    assert read(OUT/'review/publication_scan.json')['status'] == 'PASS'
    assert read(OUT/'review/loose_publication_scan.json')['status'] == 'PASS'
    owned_paths = {p for p in paths if p.startswith(('results/unified_exact_round130/', 'scripts/round130_'))}
    inherited_paths = paths-owned_paths
    inherited_tracked = set(safe_git('ls-files', '-z', '--', *sorted(inherited_paths)).decode().strip('\0').split('\0'))
    assert inherited_tracked == inherited_paths, ('undeclared untracked historical dependency', inherited_paths-inherited_tracked)
    # Historical dependencies already belong to the stacked base. Do not stage
    # them again or risk a transport-EOL normalization changing an old table.
    pathfile = TEMP/'science_stage_paths.nul'
    pathfile.write_bytes(b'\0'.join(p.encode('utf-8') for p in sorted(owned_paths))+b'\0')
    safe_git('add', '-f', '--pathspec-from-file='+str(pathfile), '--pathspec-file-nul')
    staged = set(safe_git('diff', '--cached', '--name-only', '-z').decode().strip('\0').split('\0'))
    assert staged and staged <= owned_paths, staged-owned_paths
    assert not any(p.startswith(('src/', 'include/')) or p == 'CMakeLists.txt' for p in staged)
    result = safe_git('commit', '-m', 'Round130: complete same-start and pair-root attribution with the sole MS2 paper version')
    commit = safe_git('rev-parse', 'HEAD').decode().strip()
    write(OUT/'publication_science.json', dict(UTC=utc(), science_commit=commit,
        branch=BRANCH, base_branch=PARENT, base_commit=BASE,
        frozen_source_commit=read(OUT/'preformal_source_provenance.json')['source_commit'],
        staged_files=len(staged), published_push_pending=True,
        export_manifest_SHA=sha(OUT/'export_manifest.json'),
        no_source_change_after_E3_freeze=True,
        recovery_will_pin_this_science_commit_not_future_receipts=True))
    print(result.decode('utf-8', errors='replace'))
    print(json.dumps(dict(science_commit=commit, staged_files=len(staged))))


def finish():
    source_guard()
    science = read(OUT/'publication_science.json')
    restore = read(OUT/'public_restore_receipt.json')
    cleanup = read(OUT/'cleanup_receipt.json')
    protect = read(OUT/'review/final_protection_check.json')
    pr = read(OUT/'review/created_PR_readback.json')
    pdf = read(OUT/'review/pdf_visual_review.json')
    account = read(OUT/'resource_accounting.json')
    decision = read(OUT/'scientific_decision.json')
    independent = read(OUT/'review/final_independent_evidence.json')
    observations = read(OUT/'observations.json')
    archives = read(OUT/'raw_archive_manifest.json')['archives']
    assert restore['status'] == 'PASS' and restore['science_commit'] == science['science_commit']
    assert restore['anonymous_public_HTTPS'] and not restore['local_raw_or_old_checkout_fallback']
    assert all(restore[k] == 0 for k in ['Optimize', 'native_starts', 'compilation'])
    assert cleanup['status'] == protect['status'] == 'PASS'
    assert pr['draft'] and pr['state'] == 'open' and not pr['merged']
    assert pr['head_sha'] == science['science_commit'] and pr['base'] == PARENT
    assert pdf['status'] == 'PASS' and pdf['PDF_SHA'] == sha(OUT/'manuscript.pdf')
    assert account['closed_under_outer_limit'] and not account['closure_pending'] and not budget()['unclosed']
    assert decision['execution'] == 'COMPLETE' and independent['status'] == 'PASS'
    assert len(observations['arms']) == 24 and len(observations['pairs']) == 30 and len(archives) == 8
    assert read(OUT/'review/publication_scan.json')['status'] == 'PASS'
    assert not read(OUT/'paper_version_manifest.json')['formal_results_pending']
    science.update(published_push_pending=False, public_PR=pr['url'],
        public_science_head_verified=True, delivery_confirmation_UTC=utc())
    write(OUT/'publication_science.json', science)
    paid, measured = account['paid_outer_seconds'], account['exact_subprocess_outer_seconds']
    note = f'''
## Actual finite delivery and closure

The science snapshot `{science['science_commit']}` is published in Draft PR {pr['url']}, stacked on `{PARENT}` at `{BASE}`. Created-PR readback is open, Draft and unmerged with that science head. The subsequent small metadata commit carries actual delivery receipts. Its final normal push/readback is recorded locally, avoiding recursive self-commit claims or another recovery.

Exactly one anonymous public empty-root recovery passed at that science commit: {restore['files']} declared files, eight archives (six formal groups, qualification/closed fees and one accurately labelled old B20 coverage arm), {sum(a['members'] for a in restore['archives'])} indexed raw members. Every declared file/part/member hash and the isolated portable check passes. Optimize/native starts/compilation are all zero, with no local raw/old-checkout fallback. Same-root attempt/failure records are retained. No second recovery is performed for metadata. export_manifest.json describes that fixed science snapshot; later receipt prose is intentionally not represented as the same byte snapshot.

Guarded owned cleanup passed with {len(cleanup['actions'])} recorded actions on declared duplicate ZIPs, inspected reconstructible page PNGs, a byte-identical temporary final PDF and this verified recovery expansion. The observed E-volume free-space delta is {cleanup['observed_volume_delta_bytes']} bytes; it is not an exact attribution of reclaimed bytes. Unique raw/models/Starts/tables, distinct PDFs, failures, original E2/E3/DLL, user content and old worktrees remain. Main HEAD matches its initial value: {protect['main_head_matches_initial']}. The three guarded user files match the explicitly dated late snapshot: {protect['late_user_dirty_hashes_still_match']}. No initial dirty-file hashes were taken, so this is not a claim of task-start byte equality. Research-content writes and cleanup targets exclude main; the linked worktree uses its authorized shared Git metadata/object store.

Closed outer accounting is {paid:.6f}/39600 seconds: {measured:.6f} measured nonoverlapping child seconds, explicit 900-second conservative setup allowance and 60-second final metadata allowance. Formal outer time is {account['by_kind']['formal']:.6f} seconds; build plus incremental qualification is {account['qualification_plus_build_seconds']:.6f}/3600 seconds. No formal retry/recovery or compilation during performance occurred. Nested H/LP/MIP seconds are not added; interactive waiting is not claimed as CPU. Every closed launch/receipt remains in resource_accounting.json without recursive repacking.

The fixed 24-arm attribution study is complete. S2/MS2 remains the sole adopted method. Scientific outcome: `{decision['tag']}`. No extra experiment is authorized.
'''
    for name in ['final_report.md', 'review_actions.md', 'reproducibility.md']:
        value=(OUT/name).read_text(encoding='utf-8')
        value=value.replace('One science-commit anonymous empty-root recovery and guarded owned duplicate cleanup will be appended only after their actual receipts; no further experiment is authorized.',
            'One science-commit anonymous empty-root recovery and guarded owned duplicate cleanup passed; their actual scope is recorded below. No further experiment is authorized.')
        value=value.replace('Actual scope and receipts are supplied after execution.', 'Actual scope and receipts are recorded below.')
        value=value.replace('Publication scan, one anonymous science-commit recovery, guarded duplicate cleanup and final normal stacked Draft-PR readback are recorded after those operations actually occur.',
            'Publication scan, one anonymous science-commit recovery, guarded duplicate cleanup and created Draft-PR readback have their actual receipts below; the final metadata push has a local nonrecursive readback.')
        (OUT/name).write_text(value+note,encoding='utf-8')
    body = (OUT/'PR_BODY.md').read_text(encoding='utf-8')
    body = body.replace('One science-commit anonymous empty-root recovery and guarded owned duplicate cleanup will be appended only after their actual receipts; no further experiment is authorized.',
        f'One anonymous public empty-root recovery passed at science commit `{science["science_commit"]}` ({restore["files"]} files, eight finite archives, all member hashes and the isolated checker, zero Optimize/native starts/compilation and no local fallback). Guarded owned duplicate cleanup passed, preserving unique evidence, binaries, failures, user changes and old worktrees. Closed outer accounting: {paid:.3f}/39600 seconds including explicit 900+60-second allowances and every nonoverlapping child receipt. No further experiment is authorized.')
    (OUT/'PR_BODY.md').write_text(body, encoding='utf-8')
    (OUT/'RESUME.md').write_text(f'Round130 science and delivery COMPLETE. {decision["tag"]}. All24 arms/30 typed comparisons, separate final review and actual affected-page PDF review pass. Draft PR {pr["url"]}; base {PARENT}; science {science["science_commit"]}. One anonymous empty-root recovery and guarded owned cleanup PASS. Closed outer accounting {paid:.6f}/39600 seconds (explicit setup900/metadata60 allowances). No extra experiment or recovery. Only the final normal metadata push/readback remains, with a local nonrecursive post-push receipt.\n', encoding='utf-8')
    checks = [
        ('Adopted sole S2/MS2 version and accurate predecessor migration', 'paper_version_manifest.json; paper_method_config.json; evidence_migration.csv'),
        ('Frozen original-S2/P E2/E3 bridge and new-control qualification', 'E3_frozen.json; preformal_source_provenance.json; qualification/'),
        ('Independent preformal PS/S2R source/model/Start/root/budget admission', 'review/preformal_independent_review.md; review/performance_admission.json'),
        ('All24 fixed paid arms and all30 typed comparisons on six shared groups', 'arms.csv; pairs.csv; stratified_summary.json; campaign/group01..06'),
        ('Actual same-H/root/Start, split-target exposure, costs and signed coverage facts', 'same_H.csv; actual_method_differences.json; mechanism_costs.csv; closure_sources.csv'),
        ('Substantive three-axis decision with all adverse/open outcomes', 'claim_decision.md; scientific_decision.json; final_report.md'),
        ('Independent final arithmetic/denominators and finite evidence/fleet replay', 'review/final_independent_review.md; review/final_independent_evidence.json'),
        ('Full maintained paper/appendices and actual PDF affected-page review', 'manuscript_lineage.json; manuscript.pdf; review/pdf_visual_review.json'),
        ('Actual-member and loose publication scan with finite exact dependencies', 'raw_archive_manifest.json; export_manifest.json; review/publication_scan.json'),
        ('One science-commit anonymous empty-root recovery without native work', 'public_restore_receipt.json; review/public_recovery_attempts/'),
        ('Bounded owned cleanup and unique/user/old-worktree protection', 'cleanup_receipt.json; review/final_protection_check.json'),
        ('All nonoverlapping outer fees closed under39600 without nested double counting', 'resource_accounting.json'),
        ('English stacked open Draft PR with normal publication', 'review/created_PR_readback.json; final local post-push receipt'),
    ]
    write(OUT/'completion_audit.json', dict(UTC=utc(),
        status='SCIENCE_AND_DELIVERY_COMPLETE_FINAL_METADATA_PUSH_READBACK_PENDING',
        scientific_tag=decision['tag'], actual_requirements=[dict(requirement=a, evidence=b, completed=True) for a,b in checks],
        final_short_metadata_push_readback_pending=True, no_extra_experiment_or_second_recovery=True))
    (OUT/'completion_audit.md').write_text('# Round130 completion audit\n\n'+''.join(
        f'- PASS: {a}. Evidence: {b}.\n' for a,b in checks)+'\nThe final normal metadata push/readback is recorded locally after this commit without a second recovery or recursive receipt commit.\n', encoding='utf-8')
    write(OUT/'delivery_receipt.json', dict(UTC=utc(),
        status='SCIENCE_AND_DELIVERY_PASS_FINAL_METADATA_PUSH_READBACK_PENDING', PR=pr['url'],
        science_commit=science['science_commit'], base_branch=PARENT, measured_base_commit=BASE,
        recovery_receipt_SHA=sha(OUT/'public_restore_receipt.json'), cleanup_receipt_SHA=sha(OUT/'cleanup_receipt.json'),
        protection_receipt_SHA=sha(OUT/'review/final_protection_check.json'), resource_accounting_SHA=sha(OUT/'resource_accounting.json'),
        final_postpush_observation_is_local_and_nonrecursive=True, no_second_recovery=True))
    print(json.dumps(dict(closeout_written=True, paid_outer_seconds=paid, PR=pr['url'])))


def metadata():
    from round127_release import scan
    assert read(OUT/'delivery_receipt.json')['status'] == 'SCIENCE_AND_DELIVERY_PASS_FINAL_METADATA_PUSH_READBACK_PENDING'
    assert not safe_git('diff', '--cached', '--name-only').strip(), 'Preserve unrelated staged work'
    source_guard()
    names = ['publication_science.json', 'public_restore_receipt.json', 'cleanup_receipt.json',
        'resource_accounting.json', 'final_report.md', 'review_actions.md', 'reproducibility.md',
        'PR_BODY.md', 'RESUME.md', 'completion_audit.json', 'completion_audit.md', 'delivery_receipt.json']
    files = {OUT/name for name in names}
    files.update(p for p in (OUT/'review').rglob('*') if p.is_file() and not p.name.endswith('.local.json'))
    scanned = sum(scan(p) for p in files)
    scan_receipt = OUT/'review/final_metadata_scan.json'
    write(scan_receipt, dict(UTC=utc(), status='PASS', actual_files_scanned=len(files),
        actual_bytes_scanned=scanned, fixed_science_snapshot_recovery_not_repeated=True,
        scope='Actual final receipt/prose files only; source/carriers/PDF retain the recovered science snapshot'))
    files.add(scan_receipt)
    paths = {p.relative_to(ROOT).as_posix() for p in files}
    assert all(p.startswith('results/unified_exact_round130/') for p in paths)
    pathfile = TEMP/'metadata_stage_paths.nul'
    pathfile.write_bytes(b'\0'.join(p.encode('utf-8') for p in sorted(paths))+b'\0')
    safe_git('add', '-f', '--pathspec-from-file='+str(pathfile), '--pathspec-file-nul')
    staged = set(safe_git('diff', '--cached', '--name-only', '-z').decode().strip('\0').split('\0'))
    assert staged and staged <= paths, staged-paths
    output = safe_git('commit', '-m', 'Round130: record public recovery, owned cleanup and closed delivery receipts')
    print(output.decode('utf-8', errors='replace'))
    print(json.dumps(dict(metadata_commit=safe_git('rev-parse', 'HEAD').decode().strip(),
        staged_files=len(staged), final_normal_push_and_local_readback_pending=True)))


if __name__ == '__main__':
    {'science': science, 'finish': finish, 'metadata': metadata}[sys.argv[1]]()
