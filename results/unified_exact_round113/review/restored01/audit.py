"""Independent public/restored-root final audit, never reads original evidence.

Reads only the two supplied F roots, runtime standard library and this new
review directory. No solver, qualification, compiler, pack or re-export.
"""
from pathlib import Path, PurePosixPath
import collections, csv, datetime, hashlib, importlib, json, math, os, sys, tarfile, time
PUBLIC=Path('F:/ExactEBRP-round113-public01')
RESTORED=Path('F:/ExactEBRP-round113-restored01')
DEST=Path(__file__).resolve().parent
ROUND='results/unified_exact_round113';OUT=RESTORED/ROUND
csv.field_size_limit(64*1024*1024)
FORBIDDEN={'.exe','.dll','.lic','.key','.pem','.pyc','.pdb','.obj','.o','.lib','.a'}
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(name,value):(DEST/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def leaves(v):
    if isinstance(v,dict):return sum(leaves(x) for x in v.values())
    if isinstance(v,list):return sum(leaves(x) for x in v)
    return 1
def safe(name):
    p=PurePosixPath(name)
    assert not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name
    assert p.suffix.lower() not in FORBIDDEN
    assert p.name.lower() not in ['.env','gurobi.lic','license.key']
    assert name=='CMakeLists.txt' or name.startswith(('results/','reference/','scripts/','src/','include/','tests/'))

def main():
    tick=time.perf_counter();package=PUBLIC/ROUND/'compact_evidence';manifest_path=package/'manifest.json';manifest=read(manifest_path)
    assert sha(manifest_path)=='e2998e98164cb80b63e3afb9e96f1775a5b03ace86831c0f365d341465a15348'
    archive=package/manifest['archive_path'];assert archive.name=='evidence.tar.gz'
    assert archive.stat().st_size==manifest['archive_bytes']==32982912
    assert sha(archive)==manifest['archive_sha256']=='990207810f40a0cdd46f40caaa1925d89e19103d82292d8fba143d4698e9bfbb'
    assert manifest['parts']==[] and manifest['archive_bytes']<manifest['single_blob_limit_bytes']==95*1024*1024
    assert manifest['part_bytes']==90*1024*1024 and not list(package.glob('*.part*'))
    assert manifest['no_PE_DLL_license_or_credentials'] and manifest['current_actual_raw_only']
    assert not manifest['old_full_carriers_copied'] and manifest['Optimize']==0
    records=manifest['files'];expected={v['path']:v for v in records};assert len(expected)==len(records)==6095
    member_hashes={}
    for record in records:
        name=record['path'];safe(name);path=RESTORED/name
        assert path.resolve().is_relative_to(RESTORED.resolve()) and not path.is_symlink() and path.is_file()
        assert path.stat().st_size==record['bytes'] and sha(path)==record['sha256'],name
        member_hashes[name]=record['sha256']
    archived=set();tar_total=0
    with tarfile.open(archive,'r|gz') as tar:
        for item in tar:
            safe(item.name);assert item.isfile() and not item.issym() and not item.islnk()
            assert item.name in expected and item.name not in archived
            record=expected[item.name];assert item.size==record['bytes']
            h=hashlib.sha256();stream=tar.extractfile(item);assert stream is not None
            while block:=stream.read(1024*1024):h.update(block)
            assert h.hexdigest()==record['sha256'],item.name
            archived.add(item.name);tar_total+=item.size
    assert archived==set(expected)
    extra_restored=[p.relative_to(RESTORED).as_posix() for p in RESTORED.rglob('*') if p.is_file() and p.relative_to(RESTORED).as_posix() not in expected]
    assert all(n in ['restore_receipt.json','core_comparison_receipt.json'] or '__pycache__/' in n and n.endswith('.pyc') for n in extra_restored)
    public_receipt=read(PUBLIC/'public_export_receipt.json')
    assert public_receipt['exit_code']==public_receipt['Optimize']==public_receipt['IIS']==0
    assert public_receipt['only_proposed_public_files_and_explicit_public_dependencies'] and len(public_receipt['files'])==4
    for record in public_receipt['files']:
        path=PUBLIC/record['path'];assert path.stat().st_size==record['bytes'] and sha(path)==record['sha256']
    assert public_receipt['archive_SHA']==manifest['archive_sha256']
    dependency=manifest['public_dependencies'];assert len(dependency)==1
    dependency=dependency[0];assert dependency['path']=='scripts/round110_public.py'
    assert dependency['commit']=='9165e69bf41d1eb323fd52b8cb4a8230dcb4edd4'
    assert sha(PUBLIC/dependency['path'])==sha(RESTORED/dependency['path'])==dependency['sha256']
    assert sha(PUBLIC/'scripts/publish_round113.py')==sha(RESTORED/'scripts/publish_round113.py')==manifest['restore_source_SHA']
    restore=read(RESTORED/'restore_receipt.json');compare=read(RESTORED/'core_comparison_receipt.json')
    assert restore['files']==6095 and restore['exit_code']==restore['Optimize']==restore['IIS']==0
    assert restore['public_files_only'] and not restore['original_workspace_reads'] and restore['exact_part_count']==0
    assert restore['archive_SHA']==manifest['archive_sha256'] and restore['manifest_SHA']==sha(manifest_path)
    assert compare['passed'] and compare['Optimize']==compare['IIS']==0 and not compare['original_worktree_fallback']
    assert compare['exact_csv_fields_compared']==63224 and compare['JSON_leaf_fields_compared']==203
    assert compare['stage']=='BLOCKED' and compare['exact_JSON_files_compared']==['backend_conclusions.json','summary.json']
    candidate=read(OUT/'candidate_identity.json');admission=read(OUT/'review/performance_admission.json')
    assert sha(OUT/'candidate_identity.json')==admission['candidate_identity_SHA']=='303e900baf8d6dfb6f80570a9c585aded727ef66202148df2237a900eee0ba2b'
    assert manifest['source_bindings']==candidate['source_bindings'] and len(candidate['source_bindings'])==206 and len(candidate['helpers'])==42
    for name,value in {**candidate['source_bindings'],**candidate['helpers']}.items():assert sha(RESTORED/name)==value,name
    reader=RESTORED/manifest['reader_path'];assert sha(reader)==manifest['reader_SHA']==compare['reader_SHA']==restore['reader_SHA']=='7aecf8ae0a8fcad16bafa96b7739b9cd63f0c5436fa382bf421cfac8c30b7cc3'
    admitted=OUT/'engineering/admitted_reader/read_round113.py'
    assert sha(admitted)==manifest['admitted_reader_SHA']==admission['offline_reader_SHA']
    old=OUT/'inherited_r112';clock=read(old/'clock_manifest.json')
    assert sha(old/'clock_manifest.json')==admission['inherited_clock_manifest_SHA']
    assert len(clock['files'])==146 and len(clock['arms'])==12 and clock['old_partial13_excluded']
    assert not clock['old_raw_reaudited'] and not clock['original_clock_adjusted']
    for name,h in clock['files'].items():assert sha(old/name)==h
    old_raw_names=[n for n in expected if n.startswith(ROUND+'/inherited_r112/authoritative/campaign/raw/')]
    assert all(int(n.split('/raw/',1)[1].split('_',1)[0])<=12 for n in old_raw_names)
    assert not any('/inherited_r112/' in n and n.endswith(('.lp','.tar.gz')) for n in expected)
    whole=read(OUT/'review/whole_goal01/report.json');post=read(OUT/'review/postformal01/report.json')
    assert whole['current_offline_reader_SHA']==sha(reader) and whole['decision']=='ACCEPT_BLOCKED_SCIENTIFIC_REPORTING_PENDING_PUBLIC_RESTORE_AND_PR'
    publication_deltas=[]
    for name,h in whole['bindings'].items():
        assert name in expected
        actual=sha(RESTORED/name)
        if actual!=h:
            assert name=='scripts/publish_round113.py',name
            assert h=='05ef67218a484d379599d93db6a6e2327ca4fd806ae2570e43796fc3bd959acd'
            assert actual=='4b89a153246b5c63b5dfe26fd2f165f5e2dcdfe1807d341bd3cef7b73e099a98'
            assert name not in candidate['helpers'] and name not in candidate['source_bindings']
            publication_deltas.append(dict(path=name,whole_goal_prototype_SHA=h,actual_public_restorer_SHA=actual,
                outside_runtime_performance_closure=True,full_diff_verification_pending=True))
    assert len(publication_deltas)==1
    publisher=(RESTORED/'scripts/publish_round113.py').read_bytes()
    assert b"'inherited_r112/authoritative/campaign'" in publisher
    assert b"add(root/'scripts/.gitattributes')" in publisher
    attributes=[]
    for name in ['scripts/.gitattributes',ROUND+'/.gitattributes']:
        assert name in expected
        attributes.append(dict(path=name,SHA=sha(RESTORED/name),text=(RESTORED/name).read_text()))
    assert sha(OUT/'review/postformal01/report.json')==whole['bindings'][ROUND+'/review/postformal01/report.json']
    for name,h in post['output_bindings'].items():assert sha(OUT/'review/postformal01'/name)==h
    original_reads=[];outside_writes=[];native_attempts=[];stdlib_runtime_DLL_initializers=[]
    dest_norm=str(DEST.resolve()).replace('\\','/').casefold()
    def audit_hook(event,args):
        if event=='ctypes.dlopen' and args[0] in ['libpython3.12.dll','kernel32']:
            frame=sys._getframe(1);stdlib_initializer=False
            while frame is not None:
                if frame.f_code.co_name=='<module>' and frame.f_code.co_filename.replace('\\','/').endswith('/ctypes/__init__.py'):
                    stdlib_initializer=True;break
                frame=frame.f_back
            if stdlib_initializer:
                stdlib_runtime_DLL_initializers.append(args[0]);return
        if event in ['subprocess.Popen','os.system','os.posix_spawn','ctypes.dlopen']:
            native_attempts.append(event);raise AssertionError('No subprocess or native library permitted during independent reader')
        if event not in ['open','os.listdir','os.scandir']:return
        raw=args[0]
        if not isinstance(raw,(str,bytes,os.PathLike)):return
        path=Path(os.fsdecode(raw));normalized=str(path.resolve()).replace('\\','/').casefold()
        if normalized.startswith('e:/codes/') and not (normalized==dest_norm or normalized.startswith(dest_norm+'/')):
            original_reads.append(normalized);raise AssertionError('Original worktree fallback rejected: '+normalized)
        if event=='open':
            mode=args[1];flags=args[2] if len(args)>2 else 0
            writing=isinstance(mode,str) and any(v in mode for v in 'wax+') or flags is not None and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
            if writing and not (normalized==dest_norm or normalized.startswith(dest_norm+'/')):
                outside_writes.append(normalized);raise AssertionError('Review write outside its own directory rejected')
    sys.addaudithook(audit_hook)
    sys.dont_write_bytecode=True
    sys.pycache_prefix=str(DEST/'unused_pycache')
    sys.path.insert(0,str(RESTORED/'scripts'))
    module=importlib.import_module('read_round113')
    assert Path(module.__file__).resolve()==reader.resolve()
    reconstructed=DEST/'independent_rebuilt';rebuild_tick=time.perf_counter()
    module.rebuild(RESTORED,reconstructed)
    module.core.compare(OUT/'reports_final',reconstructed)
    independently_rebuilt_seconds=time.perf_counter()-rebuild_tick
    compared_files=[];csv_fields=0;json_fields=0
    for path in sorted((OUT/'reports_final').iterdir()):
        other=reconstructed/path.name
        if path.suffix=='.csv':
            a=rows(path);b=rows(other);assert a==b
            fields=sum(len(row) for row in a);csv_fields+=fields
            compared_files.append(dict(name=path.name,type='CSV',rows=len(a),fields=fields,exact_fieldwise=True,
                expected_SHA=sha(path),rebuilt_SHA=sha(other)))
        elif path.suffix=='.json':
            a=read(path);b=read(other);assert a==b;count=leaves(a);json_fields+=count
            compared_files.append(dict(name=path.name,type='JSON',leaves=count,exact_parsed_value=True,
                expected_SHA=sha(path),rebuilt_SHA=sha(other)))
    assert csv_fields==compare['exact_csv_fields_compared']==63224
    assert json_fields==compare['JSON_leaf_fields_compared']==203
    summary=read(reconstructed/'summary.json');assert summary['stage']=='BLOCKED'
    assert (summary['new_qualified_formal_arms'],summary['postexit_blocked_new_formal_arms'],summary['unstarted_new_formal_arms'])==(3,1,4)
    assert (summary['inherited_qualified_formal_arms'],summary['evaluable_pairs'],summary['pair_positions'])==(12,21,30)
    assert summary['unqualified_new_formal_actual_Optimize']==summary['unqualified_new_formal_returned']==1
    assert summary['actual_Optimize_all_observed_new_and_qualification']==22
    assert not summary['current_reader_fee_pending'] and not summary['native_rerun'] and not summary['default_ENS_changed']
    assert summary['conservative_starts']==15 and summary['outer_fee_seconds_upper']==6112.501114845276
    new=rows(reconstructed/'new_arms.csv');cold=next(a for a in new if a['id']=='G50-C1' and a['arm']=='P-GRB')
    assert cold['status']=='POSTEXIT_VALIDATION_BLOCKED' and cold['native_Optimize']=='1'
    assert all(cold[k]=='' for k in ['U','L','gap','certificate','complete_seconds'])
    assert cold['formal_protocol_qualified']=='False'
    assert not (OUT/'campaign/raw/04_G50-C1_S0_P-GRB/whole_arm_receipt.json').exists()
    assert not (OUT/'campaign/raw/04_G50-C1_S0_P-GRB/audit_execution_metrics.json').exists()
    assert all(a['status']=='UNSTARTED' for a in new if a['id']=='G100-R2')
    for method in ['ENS-C','M-B']:assert summary['backend_conclusions'][method]['status']=='INCOMPLETE_ATTRIBUTION'
    decision=(OUT/'next_research_decision.md').read_text()
    assert 'branch3' in decision and 'authorizes no new work' in decision and 'stop' in decision
    assert not original_reads and not outside_writes and not native_attempts
    public_extra=[p.relative_to(PUBLIC).as_posix() for p in PUBLIC.rglob('*') if p.is_file() and p.relative_to(PUBLIC).as_posix() not in {r['path'] for r in public_receipt['files']}|{'public_export_receipt.json'}]
    assert all('__pycache__/' in n and n.endswith('.pyc') for n in public_extra)
    report=dict(schema='round113-independent-restored-root-final-review-v1',reviewer='/root/independent_review',
        signed_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='ACCEPT_ACTUAL_PUBLIC_RESTORE_BLOCKED_SCIENTIFIC_RESULT',
        public_root=str(PUBLIC),restored_root=str(RESTORED),original_worktree_evidence_reads=0,original_worktree_fallback=False,
        manifest_SHA=sha(manifest_path),archive_SHA=sha(archive),archive_bytes=archive.stat().st_size,actual_parts=0,
        manifest_members=6095,archive_members=6095,restored_members_verified=6095,archive_uncompressed_bytes=tar_total,
        duplicate_or_unsafe_or_link_members=False,all_exact_manifest_SHA_and_size_checks_pass=True,
        PE_DLL_license_credentials_excluded=True,old_full_carriers_copied=False,limited_old_authority_files=146,
        old_LP_matrices_reparsed=0,old_original_clocks_preserved=True,production_source_bindings_verified=206,
        performance_helpers_verified=42,production_PE_and_DLL_not_present=True,production_recompiled=False,
        current_reader_SHA=sha(reader),admitted_reader_SHA=sha(admitted),stdlib_restorer_SHA=manifest['restore_source_SHA'],
        pinned_stdlib_public_dependency=dependency,all_frozen_scientific_review_bindings_match_restored_bytes=True,
        publisher_prototype_binding_unchanged=False,publication_engineering_delta=publication_deltas,
        exact_byte_Git_attributes=attributes,
        parent_actual_export_receipt_SHA=sha(PUBLIC/'public_export_receipt.json'),parent_actual_restore_receipt_SHA=sha(RESTORED/'restore_receipt.json'),
        parent_actual_comparison_receipt_SHA=sha(RESTORED/'core_comparison_receipt.json'),
        independent_restored_reader_rebuild=True,independent_reader_rebuild_seconds=independently_rebuilt_seconds,
        independent_exact_CSV_fields=csv_fields,independent_exact_JSON_leaves=json_fields,compared_files=compared_files,
        scientific_stage='BLOCKED',qualified_new_arms=3,normal_return_POSTEXIT_VALIDATION_BLOCKED=1,fixed_unstarted_G100=4,
        qualified_old_arms=12,evaluable_pairs=21,pair_positions=30,new_evaluable_pairs=3,
        actual_Optimize_observed=22,unqualified_formal_Optimize=1,cold_formal_endpoint_and_whole_are_null=True,
        backend_conclusions='ENS-C and M-B both INCOMPLETE_ATTRIBUTION',single_next_priority='branch3 finite insufficiency and STOP',
        total_conservative_starts=15,total_outer_seconds_upper=6112.501114845276,
        public_generated_non_authoritative_cache_files=public_extra,restored_generated_non_authoritative_files=extra_restored,
        archive_contains_generated_caches=False,stdlib_python_runtime_DLL_initializers=stdlib_runtime_DLL_initializers,
        scientific_payload_HEAD_reported_by_parent='8dd38b790a4584f17aa75094f9451519e07bcdbe',
        live_Git_or_remote_HEAD_verified_in_this_two_root_review=False,PR_remote_receipt_pending=True,
        no_performance_change_from_scientific_payload_or_restoration=True,
        native_starts=0,Optimize=0,compiler_starts=0,qualification_or_fixture_starts=0,pack_or_export_or_restore_runs=0,
        review_writes_confined_to_new_review_directory=True,review_engineering_seconds=time.perf_counter()-tick,
        audit_source_SHA=sha(Path(__file__)),limitations=['Evidence-only recovery does not reproduce solver performance; PE/DLL/license excluded.',
            'Old matrix/scope/cover authority is inherited from signed limited R112 material; no old LP matrix reparse.',
            'Normal returned cold MIP is observed and charged but has no qualified formal endpoint or complete arm clock.',
            'G100 zero optimum and all four actual backend outcomes remain unknown.',
            'Scientific payload Git head is a parent-reported identity here; live PR/remote object verification remains a separate pending operation.',
            'No future receipt or commit is validated by this signature.'])
    save('report.json',report)
    print(json.dumps(dict(decision=report['decision'],files=6095,csv_fields=csv_fields,json_leaves=json_fields,
        independent_reader_seconds=independently_rebuilt_seconds,review_engineering_seconds=report['review_engineering_seconds'])))

if __name__=='__main__':main()
