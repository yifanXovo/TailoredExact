"""Finite accounting and guarded cleanup planning after actual public recovery."""
from round129_common import *
from round127_release import idle
import gzip

def account():
    b=budget();closed=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        launch=read(p.parent/'launch.json');r=read(p)
        closed.append(dict(label=p.parent.name,kind=launch['kind'],exit_code=r['exit_code'],outer_seconds=r['outer_seconds'],
            launch_SHA=sha(p.parent/'launch.json'),receipt_SHA=sha(p),launch=launch,receipt=r))
    # Account is run directly once all subprocess meters are closed. The fixed
    # allowance avoids recursively metering the receipt that meters itself.
    final_admin=60
    total=b['paid_outer_seconds']+final_admin
    value=dict(UTC=utc(),outer_limit_seconds=TOTAL_LIMIT,**dict(b,paid_outer_seconds=total,remaining_outer_seconds=TOTAL_LIMIT-total),closed_meters=closed,
        setup_allowance_seconds=read(OUT/'initialization.json')['preledger_outer_upper_seconds'],
        setup_allowance_scope=read(OUT/'initialization.json')['preledger_scope'],
        exact_subprocess_outer_seconds=sum(x['outer_seconds'] for x in closed),
        final_metadata_allowance_seconds=final_admin,
        final_metadata_allowance_scope='Conservative allowance for standalone accounting, short Git/PR metadata actions and receipt writes outside child meters; not measured CPU',
        closed_meter_receipts_included_without_recursive_repacking=True,
        native_H_LP_MIP_are_nested_not_added=True,concurrent_author_preparation_not_added_as_separate_wall_time=True,
        unknown_interactive_wait_not_claimed_as_exact_CPU=True,formal_nominal_seconds=30600,
        qualification_soft_seconds=900,qualification_limit_seconds=1800,production_compilations=0,
        closed_under_outer_limit=total<=TOTAL_LIMIT,
        closure_pending=bool(b['unclosed']))
    write(OUT/'resource_accounting.json',value);print(json.dumps(b))

def retained_guard():
    identity();archives=read(OUT/'raw_archive_manifest.json')['archives'];members=0;logical=0;carriers=[]
    for a in archives:
        index=ROOT/a['member_index']['path'];assert sha(index)==a['member_index']['SHA256']
        decoded=gzip.decompress(index.read_bytes());assert hashlib.sha256(decoded).hexdigest()==a['member_index']['decoded_SHA256']
        for m in json.loads(decoded):
            p=ROOT/m['path'];assert p.is_file() and p.stat().st_size==m['bytes'],m['path']
            members+=1;logical+=m['bytes']
        h=hashlib.sha256();compressed=0
        for part in a['pieces']:
            p=ROOT/part['path'];assert p.stat().st_size==part['bytes'] and sha(p)==part['SHA256']
            with p.open('rb') as f:
                for block in iter(lambda:f.read(1024*1024),b''):h.update(block);compressed+=len(block)
        assert h.hexdigest()==a['SHA256'] and compressed==a['compressed_bytes']
        carriers.append(dict(name=a['name'],SHA=a['SHA256'],pieces=[p['path'] for p in a['pieces']]))
    init=read(OUT/'initialization.json');main=Path('E:/codes/ExactEBRP')
    actual_head=git('rev-parse','HEAD',cwd=main).decode().strip()
    dirty={name:sha(main/name) if (main/name).is_file() else None for name in init['main_dirty_hashes']}
    value=dict(UTC=utc(),status='PASS',indexed_raw_members_retained_at_recorded_sizes=members,
        indexed_raw_logical_bytes=logical,raw_rehash_not_repeated_after_packing=True,
        all_retained_public_carrier_hashes_verified=carriers,original_E2_DLL_source_identity=identity(),
        main_head=actual_head,main_head_matches_initial=actual_head==init['main_head'],
        initial_user_dirty_hashes_still_match=dirty==init['main_dirty_hashes'],
        actual_initial_dirty_hashes_now=dirty,old_worktrees_not_cleanup_targets=True)
    write(OUT/'review/final_protection_check.json',value)
    return value

def plan_cleanup():
    idle();recovery=read(OUT/'public_restore_receipt.json');assert recovery['status']=='PASS'
    for g in read(OUT/'experiment_manifest.json')['groups']:assert (OUT/g['name']/'reconstructed.json').exists()
    protection=retained_guard()
    # Main is outside every allowed target. A concurrent user's main edit is
    # reported honestly and never reset or made a reason to delete their files.
    restore=Path(recovery['destination']).resolve();allowed=(WORK/'restore').resolve()
    assert restore.is_relative_to(allowed) and restore!=allowed
    state=read(restore/'restore_state.json');assert state['commit']==recovery['science_commit'] and 'Round129' in state['owner']
    assert sha(restore/'results/unified_exact_round129/export_manifest.json')==recovery['export_manifest_SHA']
    files=[]
    for a in read(OUT/'raw_archive_manifest.json')['archives']:
        p=Path(a['temporary_complete_archive']).resolve();assert p.is_relative_to(TEMP.resolve())
        if p.exists():
            assert p.is_file() and sha(p)==a['SHA256']
            files.append(dict(path=str(p),kind='duplicate_archive',SHA=a['SHA256'],bytes=p.stat().st_size))
    review_path=OUT/'review/pdf_visual_review.json'
    if review_path.exists():
        review=read(review_path);assert review['status']=='PASS' and review['PDF_SHA']==sha(OUT/'manuscript.pdf')
        images=list(review['rendered_images'])
        prior_path=OUT/'review/pdf_prior_visual_review.json'
        if prior_path.exists():
            prior=read(prior_path)
            assert prior['inspected_all_rendered_pages'] and sha(Path(prior['source_PDF_retained']))==prior['PDF_SHA']
            images.extend(prior['rendered_images'])
        for row in images:
            p=Path(row['path']).resolve();assert p.is_relative_to(TEMP.resolve()) and p.suffix.lower()=='.png'
            if p.exists():
                assert sha(p)==row['SHA']
                files.append(dict(path=str(p),kind='reconstructible_page_image',SHA=row['SHA'],bytes=p.stat().st_size))
    final_pdf=sha(OUT/'manuscript.pdf')
    for p in (TEMP/'pdf').glob('attempt*/reading.pdf'):
        if sha(p)==final_pdf:files.append(dict(path=str(p.resolve()),kind='identical_final_pdf',SHA=final_pdf,bytes=p.stat().st_size))
    value=dict(UTC=utc(),owner='Round129',workspace=str(ROOT.resolve()),temporary_root=str(TEMP.resolve()),
        restore_parent=str(allowed),restore=dict(path=str(restore),science_commit=recovery['science_commit'],state_SHA=sha(restore/'restore_state.json')),
        files=files,logical_file_bytes=sum(x['bytes'] for x in files),
        public_recovery_receipt=str(OUT/'public_restore_receipt.json'),public_recovery_receipt_SHA=sha(OUT/'public_restore_receipt.json'),
        protection_receipt=str(OUT/'review/final_protection_check.json'),protection_receipt_SHA=sha(OUT/'review/final_protection_check.json'),
        preserve_unique_raw_models_tables_failed_producers_distinct_PDFs_and_old_worktrees=True)
    write(OUT/'review/cleanup_plan.json',value);print(json.dumps(dict(planned_files=len(files),logical_file_bytes=value['logical_file_bytes'],restore=str(restore))))

if __name__=='__main__':{'account':account,'guard':retained_guard,'plan-cleanup':plan_cleanup}[sys.argv[1]]()
