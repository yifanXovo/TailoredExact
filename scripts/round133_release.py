"""Current-only evidence carriers using the passed R129 transport recipe.

Packing is permitted only after all fixed native positions have sealed. The
old 34 carriers are referenced, never traversed or rebuilt by this entry.
"""
from round133_common import *
import inspect, zipfile, shutil


def publication_scan(path):
    from round127_release import scan as inherited_scan, BAD, FORBIDDEN
    import re
    path=Path(path)
    forbidden=FORBIDDEN|{'.o','.obj','.a','.lib','.pdb','.so','.dylib'}
    assert path.suffix.lower() not in forbidden,('forbidden published native asset',str(path))
    size=inherited_scan(path)
    # These two small source bundles are not raw carriers. Inspect their
    # members too; compressed bytes alone do not constitute a content scan.
    if path.name in {'candidate_source_bytes.zip','execution_helper_bytes.zip'}:
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                assert not member.is_dir()
                assert Path(member.filename).suffix.lower() not in forbidden,member.filename
                assert not Path(member.filename).is_absolute() and '..' not in Path(member.filename).parts
                tail=b''
                with archive.open(member) as stream:
                    while data:=stream.read(1024*1024):
                        for pattern in BAD:
                            assert not re.search(pattern,tail+data),('credential marker in source bundle',member.filename)
                        tail=data[-256:]
    return size

def idle():
    from round133_documents import idle as native_idle
    native_idle()
    gate=read(OUT/'review/pre_release_science_admission.json')
    assert gate['decision']=='ACCEPT' and gate['native_all_stopped'] is True
    assert gate['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    for stage in ('D1','D3'):
        assert gate['matrix_SHA'][stage]==sha(OUT/'plans'/f'{stage}_matrix_frozen.json')
    assert gate['effective_adapter_SHA']==sha(ROOT/'scripts/round133_postverify_repair.py')
    for name,digest in gate['science_document_bindings'].items():
        assert sha(OUT/name)==digest,('science changed after independent admission',name)
    # The final delivery review follows the actual public fixed-snapshot
    # recovery. This gate accepts only the completed scientific payload.
    assert gate['public_recovery_state']=='PENDING_ACTUAL_PUBLIC_RECOVERY'

def sources():
    """Preserve just the source bytes required by current executed policies."""
    idle()
    target=OUT/'source';target.mkdir(parents=True,exist_ok=True)
    manifest=OUT/'source_publication.json';assert not manifest.exists()
    helpers={}
    for stage in ('D1','D3'):
        for name,digest in read(OUT/'plans'/f'{stage}_matrix_frozen.json')['helpers'].items():
            assert name not in helpers or helpers[name]==digest
            assert sha(ROOT/name)==digest,name
            helpers[name]=digest
    unit=read(OUT/'qualification/small_native01/fixture_manifest.json')
    for name,digest in unit['helpers'].items():
        assert name not in helpers or helpers[name]==digest
        assert sha(ROOT/name)==digest,name
        helpers[name]=digest
    amendment=read(OUT/'plans/postverify_handoff_repair_amendment.json')
    helpers['scripts/round133_postverify_repair.py']=amendment['bindings']['adapter_SHA']
    helpers['scripts/round133_postverify_repair_tests.py']=amendment['bindings']['fixture_driver_SHA']
    source_rows=[]
    for role,row in amendment['bindings']['main_roles'].items():
        source=Path(row['path']);binding=Path(row['existing_main_binding'])
        for original,name,digest in ((source,f'reused_{role}_main.cpp',row['SHA']),
                (binding,f'reused_{role}_main_binding.json',row['existing_main_binding_SHA'])):
            assert sha(original)==digest
            published=target/name;assert not published.exists()
            shutil.copyfile(original,published);assert sha(published)==digest
            source_rows.append(dict(original=str(original),path=published.relative_to(ROOT).as_posix(),SHA=digest,
                bytes=published.stat().st_size,role=role,object_identity='attested SHA only; no object distributed'))
    # Old E3 source checks in the bridge use fixed public Git objects, never
    # the host's old checkout. Store only their named source-byte dependencies.
    legacy={}
    for group in read(OUT/'plans/D3_matrix_frozen.json')['groups']:
        identity=read(OUT/group['group']/'identity.json')
        if group['launch']['version']=='candidate':continue
        commit=identity['measured_source_commit']
        for name,digest in identity['source_hashes'].items():
            key=commit+':'+name
            if key in legacy:
                assert legacy[key]['SHA']==digest;continue
            raw=git('show',key)
            assert hashlib.sha256(raw).hexdigest()==digest,key
            published=target/'old_code'/commit/Path(name)
            published.parent.mkdir(parents=True,exist_ok=True)
            with published.open('xb') as stream:stream.write(raw)
            legacy[key]=dict(path=published.relative_to(ROOT).as_posix(),SHA=digest,bytes=len(raw),
                source_commit=commit,source_path=name)
    archive=OUT/'artifacts/execution_helper_bytes.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,digest in sorted(helpers.items()):
            assert sha(ROOT/name)==digest,name
            z.write(ROOT/name,name)
    write(manifest,dict(schema='round133-exact-current-execution-source-publication-v1',UTC=utc(),
        candidate_source_bundle=read(OUT/'candidate_manifest.json')['executed_source_bytes'],
        execution_helpers=dict(path=archive.relative_to(ROOT).as_posix(),SHA=sha(archive),
            bytes=archive.stat().st_size,members=helpers),reused_main_source_and_bindings=source_rows,
        old_E3_source_dependencies=legacy,old_source_is_pinned_public_code_not_native_assets=True,
        native_assets='PE/DLL/object/library digests are historical execution attestations, not distributed or remeasured in public recovery',
        no_native_or_vendor_headers=True,Optimize=0,compile=0))

def pack():
    idle()
    import round129_release as old
    source=inspect.getsource(old.pack)
    before="assert all((OUT/g['name']/'reconstructed.json').exists() for g in read(OUT/'experiment_manifest.json')['groups'])"
    after="assert all((Path(g['launch']['destination'])/'verification_closeout.json').exists() for g in groups)"
    assert source.count(before)==1;source=source.replace(before,after)
    before="plans=[(f'formal_group{g[\"number\"]:02d}',[p for p in (OUT/g['name']).rglob('*') if p.is_file()]) for g in read(OUT/'experiment_manifest.json')['groups']]"
    after="plans=[(g['group'].replace('/','_'),[p for p in (OUT/g['group']).rglob('*') if p.is_file()]) for g in groups]"
    assert source.count(before)==1;source=source.replace(before,after)
    before="plans.append(('qualification_closed_fees',support))"
    after="""support.extend(p for folder in ['diagnostics','math','dependencies','infra','repair']
        for p in (OUT/folder).rglob('*') if p.is_file())
    plans.append(('diagnostics_qualification_math_dependencies_closed_fees',support))
    extra=[]
    current_results=[Path(group['launch']['destination'])/'result.json' for group in groups]
    current_results.extend((OUT/'diagnostics').glob('*/result.json'))
    current_results.extend((OUT/'qualification').glob('*/raw/*/result.json'))
    for result_path in current_results:
        result=read(result_path)
        value=result.get('gurobi_progress_path')
        if value:
            path=ROOT/Path(value)
            assert path.resolve().is_relative_to((ROOT/'results/gurobi_work').resolve())
            if path.is_file():extra.append(path)
    if extra:plans.append(('current_native_progress',extra))"""
    assert source.count(before)==1;source=source.replace(before,after)
    assert source.count('round129-finite-carriers-v1')==1
    source=source.replace('round129-finite-carriers-v1','round133-finite-current-carriers-v1')
    groups=[group for stage in ('D1','D3') for group in read(OUT/'plans'/f'{stage}_matrix_frozen.json')['groups']]
    assert len(groups)==22
    namespace=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,WORK=WORK,sha=sha,read=read,write=write,
        idle=idle,budget=budget,groups=groups,scan=publication_scan)
    exec(compile(source,__file__+'::inherited_finite_pack','exec'),namespace);namespace['pack']()

def manifest():
    """Freeze current files and explicit small dependencies for one recovery."""
    idle()
    assert (OUT/'raw_archive_manifest.json').is_file()
    assert (OUT/'source_publication.json').is_file()
    assert not (OUT/'export_manifest.json').exists()
    archived={'campaign','diagnostics','qualification','fees','repair','math','dependencies','infra'}
    late={'export_manifest.json','RESUME.md','runtime_status.json','public_restore_receipt.json',
          'cleanup_receipt.json','remote_readback.json','delivery_receipt.json','resource_accounting.json',
          'completion_audit.json'}
    files=set()
    for path in OUT.rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(OUT)
        if rel.parts[0] in archived or path.name in late:continue
        files.add(path)
    # Exact executed helpers come from their byte bundle. Delivery/math
    # entries stay readable in Git and are independently hashed here.
    files.update((ROOT/'scripts').glob('round133*.py'))
    files.update((ROOT/'tests').glob('round133*.cpp'))
    files.update([ROOT/'tests/native_evidence_journal_tests.cpp',ROOT/'.gitattributes',ROOT/'WORKSPACE_POLICY.md'])
    imported_metadata=ROOT/'results/unified_exact_round94/preregistration.json'
    assert sha(imported_metadata)=='767b8abe628bb5e84c8c44ddf2b65869f44212e17bea362fc0284b4afb445774'
    files.add(imported_metadata)
    entries=[]
    for path in sorted(files):
        publication_scan(path)
        entries.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
            SHA256=sha(path),serialization='exact bytes; hash-checked LF/CRLF transport materialization only'))
    tiny=dict(source_commit='52b02252ba47e8228b73e071d6ed692385a4f816',
        source_path='results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip',
        target='inherited_dependencies/complete_tiny_joint_study.zip',bytes=213859,
        SHA256='d2e55d7ae5fcaf5bb0c9d39a489b589006f3a29eb350b167fd790ad399a0aac1',
        purpose='Explicit fixed tiny carrier for J2/J3 exact replay; no other old campaign recovery')
    write(OUT/'export_manifest.json',dict(schema='round133-finite-current-public-export-v1',base_commit=BASE,
        files=entries,file_count=len(entries),external_dependencies=[tiny],
        archive_manifest='results/unified_exact_round133/raw_archive_manifest.json',
        source_publication='results/unified_exact_round133/source_publication.json',
        fixed_science_commit_is_required_from_caller=True,no_HEAD_or_local_raw_fallback=True,
        old_34_carriers_unchanged=True,one_owned_empty_root=True,Optimize=0,compilation=0,
        no_native_assets_credentials_licenses_fonts_or_external_full_papers=True,
        later_delivery_receipts_excluded_without_recursive_repacking=True))
    print(json.dumps(dict(files=len(entries),bytes=sum(row['bytes'] for row in entries),
        explicit_old_carrier_bytes=213859,Optimize=0)))

if __name__=='__main__':
    assert sys.argv[1:] in (['sources'],['pack'],['manifest'])
    {'sources':sources,'pack':pack,'manifest':manifest}[sys.argv[1]]()
