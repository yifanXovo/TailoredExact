"""Independent read-only audit of the completed guarded cleanup."""
from pathlib import Path
import datetime, hashlib, json, time
ROOT=Path('E:/codes/ExactEBRP-work/worktrees/round133')
OUT=ROOT/'results/unified_exact_round133'
WORK=Path('E:/codes/ExactEBRP-work');TEMP=WORK/'temp/round133'
tick=time.perf_counter()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
receipt=read(OUT/'cleanup_receipt.json');plan=read(OUT/'review/cleanup_plan.json')
assert receipt['status']=='PASS' and receipt['plan_SHA']==sha(OUT/'review/cleanup_plan.json')
assert sha(OUT/'cleanup_receipt.json')=='738d3943a4ab2f8830bd45716e9cf2c12399ba9141bf07374314800bbaeee9f2'
assert sha(ROOT/'scripts/round133_cleanup.py')=='136a35cf99c66b380d2d1ee0a9c54279852cccf38ab284592f0a1488449f0072'
gate=read(OUT/'review/post_public_delivery_review.json')
assert gate['decision']=='ACCEPT_PUBLIC_RECOVERY_AND_GUARDED_CLEANUP'
assert receipt['public_restore_receipt_SHA']==gate['public_restore_receipt_SHA']==sha(OUT/'public_restore_receipt.json')
assert plan['root_all_files_match_declared_science_source_state']
assert receipt['removed_restore_files']==plan['restored_files']==321659
assert receipt['logical_deleted_file_bytes']==plan['logical_file_bytes']==1254522218
assert plan['restored_file_bytes']==1018474398
assert receipt['removed_duplicates']==plan['duplicates'] and len(plan['duplicates'])==206
assert plan['restored_file_bytes']+sum(r['bytes'] for r in plan['duplicates'])==plan['logical_file_bytes']
restored=Path(receipt['removed_owned_restore_root'])
assert restored==Path(plan['owned_restore_root'])==Path('E:/codes/ExactEBRP-work/restore/round133-public-e4c6f823')
assert restored!=WORK/'restore' and restored.is_relative_to(WORK/'restore') and not restored.exists()
assert receipt['free_E_after']-receipt['free_E_before']==receipt['observed_free_E_change_bytes']==1328017408
assert receipt['free_space_change_is_not_attributed_entirely_to_cleanup'] and receipt['all_absolute_targets_preverified']
assert receipt['Optimize']==receipt['compile']==0

expected={}
archives=read(OUT/'raw_archive_manifest.json')['archives']
for row in archives:
    target=str(Path(row['temporary_complete_archive']))
    expected[target]=dict(bytes=row['compressed_bytes'],SHA=row['SHA256'],kind='complete archive duplicate; public pieces retained')
    combined=hashlib.sha256()
    for piece in row['pieces']:
        path=ROOT/piece['path'];assert path.is_file() and path.stat().st_size==piece['bytes'] and sha(path)==piece['SHA256']
        with path.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''):combined.update(b)
    assert combined.hexdigest()==row['SHA256']
for path in sorted((OUT/'review').glob('pdf_render_attempt*.json'))+[OUT/'review/pdf_render_receipt.json']:
    data=read(path)
    for row in data['page_images']+data['contact_sheets']:
        key=str(Path(row['path']));assert key not in expected
        expected[key]=dict(SHA=row['SHA'],kind='hash-recorded reconstructible PDF render')
export=read(OUT/'pdf_export.json')
reading=str(Path(export['intermediate_root'])/'reading.pdf')
assert reading not in expected
expected[reading]=dict(SHA=sha(OUT/'manuscript.pdf'),kind='byte-identical final PDF duplicate')
assert len(expected)==206 and set(expected)=={r['path'] for r in plan['duplicates']}
counts={}
for row in plan['duplicates']:
    path=Path(row['path']);kind=row['kind'];item=expected[str(path)]
    assert item['SHA']==row['SHA'] and item['kind']==kind and not path.exists()
    if kind.startswith('complete archive'):
        assert path.is_relative_to(TEMP/'archives') and path!=TEMP/'archives'
        assert row['bytes']==item['bytes']
    else:
        assert path.is_relative_to(TEMP/'pdf') and path!=TEMP/'pdf'
        assert path.suffix in {'.png','.pdf'}
    assert not path.is_relative_to(ROOT)
    counts[kind]=counts.get(kind,0)+1
assert sorted(counts.values())==[1,24,181]

protected=read(OUT/'review/protected_final.json');baseline=read(OUT/'baseline.json')
assert protected['status']=='PASS' and len(protected['directed_dirty_bindings'])==3 and len(protected['assets'])==5
old_dirty={r['path']:r['sha256'] for r in baseline['dirty_bindings']}
for row in protected['directed_dirty_bindings']:
    assert row['SHA']==old_dirty[row['path']]==sha(row['path'])
for row in protected['assets']:
    path=Path(row['path']);assert path.is_file() and sha(path)==row['SHA'] and path.stat().st_size==row['bytes']
old_trees=[str(WORK/'worktrees'/f'round{n}') for n in range(122,133)]
assert all(Path(p).is_dir() for p in old_trees)
assert ROOT.is_dir() and Path('E:/codes/ExactEBRP').is_dir()
current=[]
for stage in ('D1','D3'):
    for group in read(OUT/'plans'/f'{stage}_matrix_frozen.json')['groups']:
        raw=Path(group['launch']['destination'])
        assert raw.is_relative_to(ROOT) and raw.is_dir() and (raw/'result.json').is_file()
        assert (raw/'producer_receipt.json').is_file() and (raw/'verification_closeout.json').is_file()
        current.append(str(raw))
assert len(current)==22
assert (OUT/'campaign/D1_01/raw/01_X-35-U_S0_S2_candidate/round133_verification_failure.json').is_file()
assert (OUT/'review/public_recovery_attempts/attempt01/receipt.json').is_file()
assert (OUT/'review/public_recovery_attempts/attempt02/receipt.json').is_file()
for path in (TEMP/'pdf/attempt01/reading.pdf',TEMP/'pdf/attempt02/reading.pdf',TEMP/'pdf/attempt03/reading.pdf'):
    assert path.is_file(),str(path)
fees={name:read(OUT/'fees'/name/'receipt.json') for name in ('delivery_cleanup01','delivery_protected_after_cleanup01')}
assert all(r['exit_code']==0 and r['exit_observed'] and not r['timeout'] and r['supervisor_failure'] is None and r['G1_seconds']==0 for r in fees.values())
assert fees['delivery_cleanup01']['outer_seconds']==164.47638070001267
assert receipt['cleanup_seconds']==17.329908100073226
result=dict(schema='round133-independent-actual-cleanup-review-v1',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    reviewer='/root/reliability_review',decision='PASS_ACTUAL_GUARDED_CLEANUP_AND_DIRECTED_PROTECTION',
    cleanup_receipt_SHA=sha(OUT/'cleanup_receipt.json'),cleanup_plan_SHA=sha(OUT/'review/cleanup_plan.json'),
    reviewed_cleanup_source_SHA=sha(ROOT/'scripts/round133_cleanup.py'),post_public_gate_SHA=sha(OUT/'review/post_public_delivery_review.json'),
    public_restore_receipt_SHA=sha(OUT/'public_restore_receipt.json'),removed_owned_root=str(restored),
    deleted_restore_files=321659,removed_duplicates=206,duplicate_classes=counts,
    logical_deleted_file_bytes=1254522218,restored_copy_bytes=1018474398,duplicate_bytes=sum(r['bytes'] for r in plan['duplicates']),
    observed_volume_free_change_bytes=1328017408,volume_change_not_equated_to_logical_deletion=True,
    all_recorded_deleted_targets_absent=True,all_targets_within_explicit_current_TEMP_or_owned_restore_parents=True,
    all_24_retained_carrier_piece_SHA_and_concatenated_SHA_rechecked=True,
    directed_dirty_bytes_rechecked=3,declared_original_candidate_PE_DLL_bytes_rechecked=5,
    protection_scope='Directed baseline byte checks and explicit deletion-path disjointness only; no whole-disk/all-history byte guarantee',
    retained_original_checkout=True,retained_current_worktree=True,retained_old_worktrees=old_trees,
    retained_current_22_raw_result_and_producer_closeout_dirs=current,distinct_PDF_attempts_preserved=[1,2,3],
    retained_original_H_verifier_failure_and_public_transport_failure=True,
    fees={name:dict(SHA=sha(OUT/'fees'/name/'receipt.json'),outer_seconds=row['outer_seconds'],G1_seconds=row['G1_seconds']) for name,row in fees.items()},
    cleanup_outer_seconds=164.47638070001267,internal_delete_seconds=17.329908100073226,
    predelete_hash_validation_is_in_outer_clock=True,final_document_and_publication_review='PENDING_STABLE_PROSE_AND_FINAL_METADATA',
    deletion_or_public_recovery_or_native_execution_by_reviewer=False,Optimize=0,compilation=0,
    independent_metadata_and_hash_review_seconds=time.perf_counter()-tick)
target=OUT/'review/actual_cleanup_review.json';assert not target.exists()
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(decision=result['decision'],SHA=sha(target),seconds=result['independent_metadata_and_hash_review_seconds'])))
