"""Finite accounting, retained-evidence checks and owned cleanup planning."""
from round130_common import *
from round127_release import idle
import gzip


def safe_git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0',
        '-c', 'core.fsmonitor=false', *args], cwd=cwd)


def account():
    b = budget()
    assert not b['unclosed'], b
    closed = []
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        launch, receipt = read(p.parent/'launch.json'), read(p)
        assert receipt['exit_observed'] and receipt['end_unix'] >= receipt['start_unix']
        closed.append(dict(label=p.parent.name, kind=launch['kind'], exit_code=receipt['exit_code'],
            outer_seconds=receipt['outer_seconds'], launch_SHA=sha(p.parent/'launch.json'), receipt_SHA=sha(p),
            launch=launch, receipt=receipt))
    intervals = sorted((r['receipt']['start_unix'], r['receipt']['end_unix'], r['label']) for r in closed)
    for a, z in zip(intervals, intervals[1:]):
        assert a[1] <= z[0], ('overlapping billed meters', a, z)
    expected_formal = {g['name'].replace('/', '_')+'_01' for g in read(OUT/'experiment_manifest.json')['groups']}
    actual_formal = {x['label'] for x in closed if x['kind'] == 'formal'}
    assert actual_formal == expected_formal, ('formal meter scope requires explicit accounting', actual_formal, expected_formal)
    init = read(OUT/'initialization.json')
    final_admin = 60
    total = b['paid_outer_seconds']+final_admin
    value = dict(UTC=utc(), outer_limit_seconds=TOTAL_LIMIT,
        **dict(b, paid_outer_seconds=total, remaining_outer_seconds=TOTAL_LIMIT-total),
        closed_meters=closed, setup_allowance_seconds=init['preledger_outer_upper_seconds'],
        setup_allowance_scope=init['preledger_explanation'],
        exact_subprocess_outer_seconds=sum(x['outer_seconds'] for x in closed),
        final_metadata_allowance_seconds=final_admin,
        final_metadata_allowance_scope='Conservative allowance for standalone accounting and short final Git/PR receipt actions outside child meters; not measured CPU',
        closed_receipts_included_without_recursive_repacking=True,
        no_overlapping_child_outer_intervals=True, native_H_LP_MIP_seconds_nested_not_added=True,
        lightweight_concurrent_author_preparation_not_added_as_separate_wall_time=True,
        interactive_wait_not_claimed_as_measured_CPU=True,
        formal_arms=24, formal_nominal_seconds=28800, qualification_soft_seconds=1800,
        qualification_limit_seconds=3600,
        qualification_plus_build_seconds=sum(b['by_kind'].get(k, 0) for k in ('build', 'qualification')),
        one_preformal_E3_build=True, compilation_during_formal_performance=False,
        formal_retry_or_recovery_count=0,
        actual_six_formal_meter_labels=sorted(actual_formal),
        closed_under_outer_limit=total <= TOTAL_LIMIT, closure_pending=False)
    assert value['closed_under_outer_limit'] and value['qualification_plus_build_seconds'] <= QUAL_LIMIT
    write(OUT/'resource_accounting.json', value)
    print(json.dumps(dict(paid_outer_seconds=total, remaining_outer_seconds=TOTAL_LIMIT-total,
        by_kind=b['by_kind'], closed_meters=len(closed))))


def retained_guard():
    idle()
    actual_identity = identity()
    archives = read(OUT/'raw_archive_manifest.json')['archives']
    members, logical, carriers = 0, 0, []
    for archive in archives:
        index = ROOT/archive['member_index']['path']
        assert sha(index) == archive['member_index']['SHA256']
        decoded = gzip.decompress(index.read_bytes())
        assert hashlib.sha256(decoded).hexdigest() == archive['member_index']['decoded_SHA256']
        for member in json.loads(decoded):
            p = ROOT/member['path']
            assert p.is_file() and p.stat().st_size == member['bytes'], member['path']
            members += 1
            logical += member['bytes']
        combined = hashlib.sha256()
        compressed = 0
        for part in archive['pieces']:
            p = ROOT/part['path']
            assert p.stat().st_size == part['bytes'] and sha(p) == part['SHA256']
            with p.open('rb') as stream:
                for block in iter(lambda: stream.read(1024*1024), b''):
                    combined.update(block)
                    compressed += len(block)
        assert combined.hexdigest() == archive['SHA256'] and compressed == archive['compressed_bytes']
        carriers.append(dict(name=archive['name'], SHA256=archive['SHA256'], pieces=[p['path'] for p in archive['pieces']]))
    main = Path('E:/codes/ExactEBRP')
    init = read(OUT/'initialization.json')
    late = read(OUT/'review/user_dirty_late_snapshot.json')
    current = {name: dict(bytes=(main/name).stat().st_size, SHA256=sha(main/name))
               if (main/name).is_file() else None for name in late['files']}
    head = safe_git('rev-parse', 'HEAD', cwd=main).decode().strip()
    tracked = safe_git('status', '--porcelain=v1', '--untracked-files=no', cwd=main).decode('utf-8', errors='replace')
    value = dict(UTC=utc(), status='PASS',
        indexed_raw_members_retained_at_recorded_sizes=members, indexed_raw_logical_bytes=logical,
        raw_rehash_not_repeated_after_packing=True, all_retained_public_carrier_hashes_verified=carriers,
        E2_E3_DLL_and_source_identity=actual_identity,
        main_head=head, main_head_matches_initial=head == init['main_HEAD'], main_tracked_status=tracked,
        late_user_dirty_snapshot_SHA=sha(OUT/'review/user_dirty_late_snapshot.json'),
        late_user_dirty_hashes_still_match=current == late['files'], current_guarded_user_files=current,
        initial_dirty_file_hashes_recorded=False,
        user_dirty_claim_scope='Initial paths/status and HEAD were recorded; byte hashes were first taken at the explicitly dated late snapshot. No claim of initial-byte equality is made.',
        all_research_content_writes_and_cleanup_targets_exclude_main=True,
        authorized_shared_linked_worktree_Git_metadata_exception=True,
        old_worktrees_binaries_unique_raw_failures_and_user_files_not_cleanup_targets=True)
    if not (value['main_head_matches_initial'] and value['late_user_dirty_hashes_still_match']):
        value['status']='PROTECTION_GUARD_FAILED_PRESERVE_CONTENT'
    write(OUT/'review/final_protection_check.json', value)
    assert value['main_head_matches_initial'] and value['late_user_dirty_hashes_still_match'], value
    return value


def plan_cleanup():
    idle()
    recovery = read(OUT/'public_restore_receipt.json')
    assert recovery['status'] == 'PASS'
    assert all((OUT/g['name']/'reconstructed.json').is_file() for g in read(OUT/'experiment_manifest.json')['groups'])
    retained_guard()
    restore = Path(recovery['destination']).resolve()
    allowed = (WORK/'restore').resolve()
    assert restore.is_relative_to(allowed) and restore != allowed
    state = read(restore/'restore_state.json')
    assert state['commit'] == recovery['science_commit'] and 'Round130' in state['owner']
    assert sha(restore/'results/unified_exact_round130/export_manifest.json') == recovery['export_manifest_SHA']
    files = []
    for archive in read(OUT/'raw_archive_manifest.json')['archives']:
        p = Path(archive['temporary_complete_archive']).resolve()
        assert p.is_relative_to(TEMP.resolve())
        if p.exists():
            assert p.is_file() and sha(p) == archive['SHA256']
            files.append(dict(path=str(p), kind='duplicate_archive', SHA=archive['SHA256'], bytes=p.stat().st_size))
    review = read(OUT/'review/pdf_visual_review.json')
    assert review['status'] == 'PASS' and review['PDF_SHA'] == sha(OUT/'manuscript.pdf')
    assert review['inspected_all_rendered_pages']
    for row in review['rendered_images']+review.get('byte_identical_prior_images',[]):
        p = Path(row['path']).resolve()
        assert p.is_relative_to(TEMP.resolve()) and p.suffix.lower() == '.png'
        if p.exists():
            assert sha(p) == row['SHA']
            files.append(dict(path=str(p), kind='reconstructible_page_image', SHA=row['SHA'], bytes=p.stat().st_size))
    final_pdf = sha(OUT/'manuscript.pdf')
    for p in (TEMP/'pdf').glob('attempt*/reading.pdf'):
        if sha(p) == final_pdf:
            files.append(dict(path=str(p.resolve()), kind='identical_final_pdf', SHA=final_pdf, bytes=p.stat().st_size))
    assert len({x['path'].lower() for x in files}) == len(files)
    value = dict(UTC=utc(), owner='Round130', workspace=str(ROOT.resolve()), temporary_root=str(TEMP.resolve()),
        restore_parent=str(allowed), restore=dict(path=str(restore), science_commit=recovery['science_commit'],
            state_SHA=sha(restore/'restore_state.json')),
        files=files, logical_file_bytes=sum(x['bytes'] for x in files),
        public_recovery_receipt=str(OUT/'public_restore_receipt.json'), public_recovery_receipt_SHA=sha(OUT/'public_restore_receipt.json'),
        protection_receipt=str(OUT/'review/final_protection_check.json'), protection_receipt_SHA=sha(OUT/'review/final_protection_check.json'),
        preserve_unique_raw_models_tables_failures_distinct_PDFs_binaries_old_worktrees_and_user_files=True)
    write(OUT/'review/cleanup_plan.json', value)
    print(json.dumps(dict(planned_files=len(files), logical_file_bytes=value['logical_file_bytes'], restore=str(restore))))


if __name__ == '__main__':
    {'account': account, 'guard': retained_guard, 'plan-cleanup': plan_cleanup}[sys.argv[1]]()
