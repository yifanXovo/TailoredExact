"""Seal late publication engineering and observed science-A receipts from F roots.

Does not change the initial signed report or frozen scientific reviews. Does
not execute the publisher, verifier, reader, qualification driver or solver.
"""
from pathlib import Path
import ast, datetime, difflib, hashlib, json, os, sys, time

PUBLIC=Path('F:/ExactEBRP-round113-public01')
RESTORED=Path('F:/ExactEBRP-round113-restored01')
DEST=Path(__file__).resolve().parent
ROUND='results/unified_exact_round113'
HEAD='8dd38b790a4584f17aa75094f9451519e07bcdbe'
BASE='9165e69bf41d1eb323fd52b8cb4a8230dcb4edd4'

def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def sha(path):return sha_bytes(path.read_bytes())
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def git_blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
    tick=time.perf_counter();initial_path=DEST/'report.json';initial_bytes=initial_path.read_bytes();initial=read(initial_path)
    assert initial['decision']=='ACCEPT_ACTUAL_PUBLIC_RESTORE_BLOCKED_SCIENTIFIC_RESULT'
    assert initial['original_worktree_evidence_reads']==0 and initial['independent_restored_reader_rebuild']
    assert (initial['independent_exact_CSV_fields'],initial['independent_exact_JSON_leaves'])==(63224,203)
    assert initial['publication_engineering_delta'][0]['full_diff_verification_pending']
    assert initial['PR_remote_receipt_pending']
    assert sha(DEST/'audit.py')==initial['audit_source_SHA']
    outside_reads=[];outside_writes=[];execution_attempts=[]
    allowed=[str(p.resolve()).replace('\\','/').casefold() for p in [PUBLIC,RESTORED,DEST]]
    dest_norm=allowed[-1]
    def hook(event,args):
        if event in ['subprocess.Popen','os.system','os.posix_spawn','ctypes.dlopen']:
            execution_attempts.append(event);raise AssertionError('No execution during supplemental static review')
        if event not in ['open','os.listdir','os.scandir','os.mkdir','os.remove','os.rmdir','os.rename','os.chmod','os.utime']:return
        paths=[args[0]]
        if event=='os.rename':paths.append(args[1])
        for raw in paths:
            if not isinstance(raw,(str,bytes,os.PathLike)):continue
            p=str(Path(os.fsdecode(raw)).resolve()).replace('\\','/').casefold()
            permitted=any(p==a or p.startswith(a+'/') for a in allowed)
            if not permitted:
                outside_reads.append(p);raise AssertionError('Read outside two evidence roots and review directory: '+p)
            writing=event in ['os.mkdir','os.remove','os.rmdir','os.rename','os.chmod','os.utime']
            if event=='open':
                mode=args[1];flags=args[2] if len(args)>2 else 0
                writing=isinstance(mode,str) and any(v in mode for v in 'wax+') or flags is not None and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
            if writing and not (p==dest_norm or p.startswith(dest_norm+'/')):
                outside_writes.append(p);raise AssertionError('Write outside new review directory: '+p)
    sys.addaudithook(hook)
    out=RESTORED/ROUND;package=PUBLIC/ROUND/'compact_evidence';manifest_path=package/'manifest.json';manifest=read(manifest_path)
    assert sha(manifest_path)==initial['manifest_SHA']
    assert sha(package/'evidence.tar.gz')==initial['archive_SHA']
    candidate=read(out/'candidate_identity.json');members={v['path']:v for v in manifest['files']}
    whole=read(out/'review/whole_goal01/report.json');whole_hash=sha(out/'review/whole_goal01/report.json')
    post_hash=sha(out/'review/postformal01/report.json')
    assert len(members)==6095 and len(candidate['source_bindings'])==206 and len(candidate['helpers'])==42
    reader_hash=sha(RESTORED/'scripts/read_round113.py');assert reader_hash==initial['current_reader_SHA']=='7aecf8ae0a8fcad16bafa96b7739b9cd63f0c5436fa382bf421cfac8c30b7cc3'
    for name,h in {**candidate['source_bindings'],**candidate['helpers']}.items():assert sha(RESTORED/name)==h,name
    mismatches=[name for name,h in whole['bindings'].items() if sha(RESTORED/name)!=h]
    assert mismatches==['scripts/publish_round113.py']
    delta_root=PUBLIC/'engineering/publication_delta01'
    old=(delta_root/'bound_publisher_prototype.py').read_bytes();new=(delta_root/'actual_publisher.py').read_bytes()
    old_hash=sha_bytes(old);new_hash=sha_bytes(new)
    assert old_hash==whole['bindings']['scripts/publish_round113.py']=='05ef67218a484d379599d93db6a6e2327ca4fd806ae2570e43796fc3bd959acd'
    assert new_hash==manifest['restore_source_SHA']=='4b89a153246b5c63b5dfe26fd2f165f5e2dcdfe1807d341bd3cef7b73e099a98'
    assert new==(RESTORED/'scripts/publish_round113.py').read_bytes()==(PUBLIC/'scripts/publish_round113.py').read_bytes()
    edits=[
        (b"        if path.parent==out and path.name.startswith(('public_','remote_','pr_')) and path.name!='public_readme.md':continue\n",b"        if path.name.startswith(('public_','remote_','pr_')):continue\n"),
        (b"    for name,h in read(out/'inherited_r112/clock_manifest.json')['files'].items():\n        path=out/'inherited_r112'/name;assert sha(path)==h;add(path)\n",b''),
        (b"    add(root/'scripts/.gitattributes')\n",b''),
        (b"'inherited_r112/authoritative/campaign'",b"'inherited_r112/campaign'")]
    reconstructed=new
    for after,before in edits:
        assert reconstructed.count(after)==1
        reconstructed=reconstructed.replace(after,before,1)
    assert reconstructed==old
    old_tree=ast.parse(old);new_tree=ast.parse(new)
    def outside_pack(tree):return [ast.dump(n,include_attributes=False) for n in tree.body if not (isinstance(n,ast.FunctionDef) and n.name=='pack')]
    assert outside_pack(old_tree)==outside_pack(new_tree)
    diff=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='bound_publisher_prototype.py',tofile='actual_publisher.py'))
    supplied_patch=(delta_root/'publication_only.patch').read_text()
    assert diff.splitlines()[2:]==supplied_patch.splitlines()[2:]
    delta_receipt=read(delta_root/'receipt.json')
    assert delta_receipt['old_prototype_SHA']==old_hash and delta_receipt['actual_publisher_SHA']==new_hash
    assert delta_receipt['previous_two_change_claim_was_incomplete'] and delta_receipt['not_in_original_6095_scientific_members']
    assert delta_receipt['performance_helpers_changed']==delta_receipt['production_sources_changed']==delta_receipt['Optimize']==delta_receipt['native_starts']==0
    assert 'scripts/publish_round113.py' not in candidate['helpers'] and 'scripts/publish_round113.py' not in candidate['source_bindings']
    attribute_records=[]
    for name,text in [('scripts/.gitattributes','*round113* -text whitespace=cr-at-eol'),(ROUND+'/.gitattributes','** -text whitespace=cr-at-eol')]:
        raw=(RESTORED/name).read_bytes();assert text in raw.decode()
        assert sha_bytes(raw)==members[name]['sha256']
        attribute_records.append(dict(path=name,SHA=sha_bytes(raw),scope='new Round113 paths only'))
    verifier_root=PUBLIC/'engineering/remote_verification_failure01'
    v_old=(verifier_root/'observed_science_verifier.py').read_bytes();v_new=(verifier_root/'actual_publication_verifier.py').read_bytes()
    v_old_hash=sha_bytes(v_old);v_new_hash=sha_bytes(v_new)
    assert v_old==(RESTORED/'scripts/verify_round113_publication.py').read_bytes()
    assert v_old_hash==members['scripts/verify_round113_publication.py']['sha256']=='2f11bd97f3e1cb7d3260d5fd91359678005c18049ff2267d33d323de210d855d'
    assert v_new_hash=='0ee2a1f164d09f7d102c7682a9be7e8cf05dfaf1ea45451e53a3b17252cc9601'
    v_diff=''.join(difflib.unified_diff(v_old.decode().splitlines(keepends=True),v_new.decode().splitlines(keepends=True),fromfile='scienceA_verifier',tofile='publication_receipt_verifier'))
    assert v_diff==(verifier_root/'publication_verifier_delta.patch').read_text()
    assert b"assert raw_digest==frozen==manifest_files[name]['sha256']" in v_new
    assert b"assert working.replace(b'\\r\\n',b'\\n')==blobs[name]" in v_new
    assert b"assert name=='scripts/verify_round113_publication.py'" in v_new
    assert b"assert check['committed_bytes']==check['working_bytes']==v['bytes']" in v_new
    assert b"check['committed_SHA256']==check['working_SHA256']==v['sha256']" in v_new
    assert 'scripts/verify_round113_publication.py' not in candidate['helpers']
    v_failure=read(verifier_root/'receipt.json')
    assert v_failure['attempt_exit_code']==1 and not v_failure['receipt_created'] and not v_failure['scientific_archive_repacked']
    assert v_failure['Optimize']==v_failure['native_starts']==v_failure['production_sources_changed']==v_failure['performance_helpers_changed']==0
    remote_path=PUBLIC/'engineering/remote_publication_A.json';remote=read(remote_path)
    pr=remote['observed_PR']
    assert remote['passed'] and remote['observed_head']==pr['headRefOid']==HEAD and remote['verified_base_commit']==BASE
    assert pr['state']=='OPEN' and pr['isDraft'] and pr['number']==175
    assert pr['headRefName']=='codex/round113-geographic-attribution-completion' and pr['baseRefName']=='codex/round112-paid-start-backend-attribution'
    assert pr['url']=='https://github.com/yifanXovo/TailoredExact/pull/175'
    assert remote['carrier_archive_SHA']==initial['archive_SHA'] and remote['carrier_archive_bytes']==32982912 and remote['actual_carrier_parts']==0
    assert remote['verifier_execution_SHA256']==v_new_hash and remote['frozen_raw_sources_checked']==206 and remote['frozen_raw_helpers_checked']==42
    assert remote['receipt_not_in_observed_commit'] and remote['no_future_commit_claim'] and remote['Optimize']==0
    objects=remote['required_objects'];assert len(objects)==len({v['path'] for v in objects})==361
    normalized=set(remote['historical_Git_CRLF_to_LF_paths']);assert len(normalized)==5
    assert remote['post_science_verifier_working_delta']==['scripts/verify_round113_publication.py']
    normalized_found=set();checked=[];frozen_checked=[]
    pack_path=PUBLIC/'engineering/science_A/public_pack_receipt.json';pack=read(pack_path);provenance=read(pack_path.parent/'provenance.json')
    assert provenance['observed_scientific_commit']==HEAD and provenance['not_an_original_scientific_carrier_member']
    assert sha(pack_path)==provenance['sha256']=='2ba5fb4c87ef86cc93a0e458187c84d53982b5340eacf002eea4c4ab42ee323d'
    assert git_blob(pack_path.read_bytes())==provenance['Git_blob_oid']=='94ebd8b4ce5c9438784540bea63cbd5ff395cd0e'
    assert pack['files']==6095 and pack['archive_SHA']==initial['archive_SHA'] and pack['manifest_SHA']==initial['manifest_SHA']
    assert pack['archive_bytes']==32982912 and pack['source_SHA']==new_hash and pack['Optimize']==pack['exit_code']==0
    for row in objects:
        name=row['path'];assert row['remote_Git_object_matches']
        if name==ROUND+'/public_pack_receipt.json':source=pack_path
        elif name.startswith(ROUND+'/compact_evidence/'):source=PUBLIC/name
        else:source=RESTORED/name
        assert source.is_file(),name
        raw=source.read_bytes();working=raw
        if name in normalized:
            committed=raw.replace(b'\r\n',b'\n');assert committed!=raw,name
            normalized_found.add(name);assert row['byte_relation']=='HISTORICAL_GIT_CRLF_TO_LF_RAW_BYTES_PRESERVED_IN_CARRIER'
        else:committed=raw
        if name=='scripts/verify_round113_publication.py':
            working=v_new;assert row['byte_relation']=='POST_SCIENCE_PUBLICATION_VERIFIER_WORKING_DELTA'
        assert len(committed)==row['committed_bytes'] and sha_bytes(committed)==row['committed_SHA256'] and git_blob(committed)==row['Git_blob_oid'],name
        assert len(working)==row['working_bytes'] and sha_bytes(working)==row['working_SHA256'],name
        frozen=candidate['source_bindings'].get(name,candidate['helpers'].get(name))
        if frozen is not None:
            assert row['frozen_raw_identity_matches_manifest'] and sha_bytes(raw)==frozen==members[name]['sha256']
            assert len(raw)==members[name]['bytes'];frozen_checked.append(name)
        checked.append(dict(path=name,Git_blob_oid=row['Git_blob_oid'],committed_SHA256=row['committed_SHA256'],committed_bytes=row['committed_bytes'],two_F_root_bytes_independently_reconstructed=True))
    assert normalized_found==normalized and set(frozen_checked)==set(candidate['source_bindings'])|set(candidate['helpers'])
    summary=read(out/'reports_final/summary.json')
    assert summary['stage']=='BLOCKED' and summary['new_qualified_formal_arms']==3 and summary['postexit_blocked_new_formal_arms']==1 and summary['unstarted_new_formal_arms']==4
    assert summary['evaluable_pairs']==21 and summary['pair_positions']==30 and summary['conservative_starts']==15 and summary['outer_fee_seconds_upper']==6112.501114845276
    assert all(summary['backend_conclusions'][name]['status']=='INCOMPLETE_ATTRIBUTION' for name in ['ENS-C','M-B'])
    assert not (out/'campaign/raw/04_G50-C1_S0_P-GRB/whole_arm_receipt.json').exists()
    assert initial_path.read_bytes()==initial_bytes
    support_files={}
    for directory in [delta_root,verifier_root,pack_path.parent]:
        for path in sorted(directory.iterdir()):
            if path.is_file():support_files[path.relative_to(PUBLIC).as_posix()]=dict(SHA=sha(path),bytes=path.stat().st_size,late_supplement_not_original_export_or_carrier=True)
    support_files[remote_path.relative_to(PUBLIC).as_posix()]=dict(SHA=sha(remote_path),bytes=remote_path.stat().st_size,late_supplement_not_original_export_or_carrier=True)
    assert not outside_reads and not outside_writes and not execution_attempts
    report=dict(schema='round113-independent-restored-final-supplement-v1',reviewer='/root/independent_review',signed_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        decision='ACCEPT_ACTUAL_PUBLIC_RESTORE_AND_OBSERVED_SCIENCE_A_PUBLICATION_WITH_BLOCKED_SCIENCE',
        initial_report_SHA=sha(initial_path),initial_report_bytes_unchanged=True,initial_audit_source_SHA=sha(DEST/'audit.py'),
        initial_independent_rebuild_seconds=initial['independent_reader_rebuild_seconds'],exact_CSV_fields=63224,exact_JSON_leaves=203,
        manifest_SHA=initial['manifest_SHA'],archive_SHA=initial['archive_SHA'],archive_bytes=32982912,archive_parts=0,science_members=6095,
        frozen_whole_goal_report_SHA=whole_hash,frozen_postformal_report_SHA=post_hash,frozen_scientific_reviews_not_edited=True,
        production_sources_verified=206,performance_helpers_verified=42,current_reader_SHA=reader_hash,
        publisher_prototype_binding_unchanged=False,all_other_whole_goal_bindings_exact=True,
        publication_engineering_delta=dict(old_prototype_SHA=old_hash,old_prototype_bytes=len(old),actual_source_SHA=new_hash,actual_source_bytes=len(new),
            four_exact_edits_independently_verified=True,edits=delta_receipt['changed_hunks'],previous_two_edit_claim_incomplete=True,
            old_source_is_hash_verified_reconstruction_not_contemporaneous_snapshot=True,only_pack_function_changed=True,
            exports_restorer_and_imports_AST_unchanged=True,outside_performance_closure=True,full_diff_verification_pending=False),
        exact_byte_Git_attribute_records=attribute_records,
        post_science_verifier_delta=dict(scientific_carrier_verifier_SHA=v_old_hash,actual_publication_verifier_SHA=v_new_hash,
            exact_patch_verified=True,original_failed_attempt_retained=True,changes_only_publication_verification=True,
            frozen_raw_SHA_and_size_equals_candidate_and_manifest=True,historical_Git_only_CRLF_to_LF_equivalence_allowed=True,
            verifier_only_working_delta_explicit=True,carrier_raw_and_committed_SHA_and_size_still_exact=True,scientific_carrier_repacked=False,
            actual_verifier_not_executed_by_reviewer=True),
        actual_parent_science_A_remote_receipt_SHA=sha(remote_path),observed_scientific_HEAD=HEAD,observed_PR=pr,verified_base_commit_in_actual_receipt=BASE,
        actual_parent_remote_receipt_read_and_checked=True,remote_Git_blob_records=361,independently_reconstructed_from_two_F_roots=361,
        independent_git_blob_checks=checked,historical_CRLF_to_LF_paths=sorted(normalized),frozen_raw_objects_verified=248,
        independent_live_Git_or_API_query=False,scientific_head_receipt_only=True,future_receipt_commit_or_final_remote_HEAD_verified=False,
        supplemental_public_files=support_files,all_late_supplements_outside_original_four_file_export_and_6095_member_carrier=True,
        resolves_initial_publication_diff_pending=True,resolves_initial_science_A_PR_remote_receipt_pending=True,
        scientific_state='BLOCKED',qualified_new=3,normal_return_POSTEXIT_VALIDATION_BLOCKED=1,G100_fixed_unstarted=4,
        cold_formal_endpoints_and_whole_remain_absent=True,qualified_old=12,evaluable_pairs=21,pair_positions=30,
        backend_conclusions='ENS-C and M-B both INCOMPLETE_ATTRIBUTION',single_next_priority='branch3 finite insufficiency; STOP',
        total_conservative_starts=15,total_outer_fee_seconds_upper=6112.501114845276,old_LP_matrices_reparsed=0,
        reviewer_subprocess_or_native_or_compiler_or_qualification_starts=0,reviewer_Optimize=0,reviewer_original_worktree_evidence_reads=0,
        no_reader_rebuild_or_archive_pack_or_export_or_restore_repeated_in_supplement=True,review_writes_only_new_restored01=True,
        supplemental_review_seconds=time.perf_counter()-tick,supplemental_audit_source_SHA=sha(Path(__file__)),
        engineering_failure_log_SHA=sha(DEST/'engineering_failures.json'),
        limitations=['The initial report remains byte-for-byte unchanged; this separate final supplement resolves its explicitly pending publication items.',
            'Remote observations are reviewed from an actually completed parent receipt; reviewer performed no independent live GitHub query.',
            'Only science A 8dd was observed. A later receipt commit or later remote head is outside this signature.',
            'Publication-only tooling and attributes changed after the frozen whole-goal prototype; runtime performance closure, reader and science did not.',
            'Evidence restoration does not reproduce native solver performance; PE/DLL/license remain excluded.',
            'Source-derived normal zero-Optimize fixtures remain synthetic; actual CLI cancellation was not exposed.',
            'Cold P normally returned but failed authority validation; no missing whole receipt or endpoint is synthesized.',
            'G100 outcomes and zero optimum remain unknown; no algorithm LOSS or hidden branch root cause is inferred.'])
    save(DEST/'final_supplement.json',report)
    print(json.dumps(dict(decision=report['decision'],objects=361,publisher_exact_edits=4,initial_report_unchanged=True,seconds=report['supplemental_review_seconds'])))

if __name__=='__main__':main()
