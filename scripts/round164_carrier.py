"""New-only archival, bounded anonymous public readback and zero-delete cleanup."""
from round164_common import *
import gzip,shutil,urllib.request,zipfile

def package():
    assert read(OUT/'panel_complete.json')['arms']==24 and not budget()['unclosed']
    assert read(OUT/'review/identities.json')['all_three_final_reviews']=='PASS'
    tick=time.perf_counter()
    old_index_path='results/unified_exact_round163/evidence/new_evidence_01.members.json.gz'
    old_index_bytes=git('show',R163_SCIENCE+':'+old_index_path)
    assert len(old_index_bytes)<10000000
    old_by_digest={}
    for entry in json.loads(gzip.decompress(old_index_bytes)):
        old_by_digest.setdefault((entry['SHA256'],entry['bytes']),[]).append(entry['path'])
    target=OUT/'artifacts';assert not target.exists()
    files=[];excluded=[]
    for path in sorted(OUT.rglob('*')):
        if not path.is_file() or target in path.parents:continue
        rel=path.relative_to(OUT)
        if rel.parts[0] in ('evidence','public_restore'):continue
        # These exact old zero-Optimize reference bytes are available through
        # the pinned R163 member map. Do not repackage inherited raw as new.
        inherited_ref=(rel.parts[0]=='campaign' and len(rel.parts)>2 and rel.parts[2]=='reference') or (
            rel.parts[:2]==('qualification','references') and 'qualification-existing-native-tiny' not in rel.parts) or (
            rel.parts[:2]==('qualification','smokes') and 'reference' in rel.parts and
            'qualification-existing-native-tiny' not in rel.parts)
        if inherited_ref:
            digest,size=sha(path),path.stat().st_size
            members=old_by_digest.get((digest,size),[])
            assert members,('old canonical reference needs fixed member identity',path)
            excluded.append(dict(path=path.relative_to(ROOT).as_posix(),SHA256=digest,bytes=size,
                old_commit=R163_SCIENCE,old_archive='results/unified_exact_round163/artifacts/new_evidence_01.zip',
                old_member=sorted(members)[0],
                reason='old canonical reference, retained by fixed R163 archive/member/SHA instead'))
            continue
        assert path.suffix.lower() not in ('.exe','.dll','.lic','.key','.pem'),('runtime or credential excluded',path)
        assert path.name.lower() not in ('.env','credentials','credentials.json','gurobi.lic')
        files.append(path)
    files.extend((ROOT/'scripts').glob('round164*'))
    files.extend(ROOT/'docs'/name for name in ('round164_seed_confirmation.md','current_mainline.md','unified_exact_research_index.md'))
    files.extend(ROOT/'results/unified_exact_round137'/name for name in ('paper_body.md','mathematical_analysis.md','supplement.md'))
    files=sorted({p for p in files if p.is_file()})
    target.mkdir(parents=True,exist_ok=False)
    archives=[];entries=[];bundle=None;destination=None
    def close():
        nonlocal bundle,entries
        if bundle is None:return
        bundle.close();index=OUT/'evidence'/(destination.stem+'.members.json.gz');index.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(index,'wt',encoding='utf-8') as stream:json.dump(entries,stream,separators=(',',':'))
        archives.append(dict(path=destination.relative_to(ROOT).as_posix(),SHA256=sha(destination),
            bytes=destination.stat().st_size,members=len(entries),uncompressed_bytes=sum(e['bytes'] for e in entries),
            index=index.relative_to(ROOT).as_posix(),index_SHA256=sha(index)))
        print(json.dumps(dict(archive=destination.name,bytes=destination.stat().st_size,members=len(entries))),flush=True)
        bundle=None;entries=[]
    for path in files:
        if bundle is None:
            destination=target/f'new_evidence_{len(archives)+1:02}.zip'
            bundle=zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True)
        name=path.relative_to(ROOT).as_posix();digest=sha(path);size=path.stat().st_size
        bundle.write(path,name);assert sha(path)==digest,'evidence changed during packaging'
        entries.append(dict(path=name,SHA256=digest,bytes=size,compressed_bytes=bundle.getinfo(name).compress_size))
        if destination.stat().st_size>=40*1024**2:close()
    close()
    write(OUT/'carrier_manifest.json',dict(schema='round164-new-only-carrier-v1',UTC=utc(),archives=archives,
        bytes=sum(a['bytes'] for a in archives),members=sum(a['members'] for a in archives),
        inherited_reference_duplicates_excluded=excluded,old_raw_carriers_included=0,
        old_reference_index=dict(commit=R163_SCIENCE,path=old_index_path,SHA256=hashlib.sha256(old_index_bytes).hexdigest()),
        unique_new_science_and_failures_retained=True,commercial_runtime_credentials_or_licenses_included=False,
        measured_PE_published=False,measured_PE_SHA256=PE_SHA,packaging_IO_seconds=time.perf_counter()-tick,
        recovery_scope='new byte/member integrity and finite old public metadata bindings; no licensed semantic or performance rerun'))

def read_gz(path):
    with gzip.open(path,'rt',encoding='utf-8') as stream:return json.load(stream)

def download(url,destination):
    with urllib.request.urlopen(url,timeout=30) as response,destination.open('xb') as stream:
        assert response.status==200
        shutil.copyfileobj(response,stream,1024*1024)

def restore(commit):
    tick=time.perf_counter();target=WORK/'restore'/f'round164-public-{commit[:12]}'
    target.mkdir(parents=True,exist_ok=False);manifest=read(OUT/'carrier_manifest.json');downloads=[];members=0
    for archive in manifest['archives']:
        url=f"https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/{archive['path']}"
        destination=target/Path(archive['path']).name;start=time.perf_counter();download(url,destination)
        assert destination.stat().st_size==archive['bytes'] and sha(destination)==archive['SHA256']
        entries=read_gz(ROOT/archive['index'])
        with zipfile.ZipFile(destination) as bundle:
            assert len(entries)==archive['members'] and sorted(bundle.namelist())==sorted(e['path'] for e in entries)
            for entry in entries:
                path=Path(entry['path']);assert not path.is_absolute() and '..' not in path.parts
                raw=bundle.read(entry['path']);assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['SHA256']
                members+=1
        downloads.append(dict(url=url,path=str(destination),bytes=destination.stat().st_size,SHA256=sha(destination),
            anonymous=True,seconds=time.perf_counter()-start))
    # A bounded public check of the immutable old manifest/input/index, rather
    # than replaying the old 50601-member evidence tree or solver campaigns.
    oldnames=['results/unified_exact_round163/input_manifest.json',
        'results/unified_exact_round163/inputs/R163-C35-U/first/instance.txt',
        'results/unified_exact_round163/reports/complete_arms.json',
        'results/unified_exact_round163/evidence/new_evidence_01.members.json.gz']
    old=[]
    for i,name in enumerate(oldnames):
        expected=git('show',R163_SCIENCE+':'+name)
        url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{R163_SCIENCE}/{name}'
        destination=target/f'old_metadata_{i:02}_{Path(name).name}';download(url,destination)
        assert destination.read_bytes()==expected
        old.append(dict(url=url,commit=R163_SCIENCE,path=name,SHA256=sha(destination),bytes=len(expected),anonymous=True))
    public_index={r['path']:r for r in read_gz(target/'old_metadata_03_new_evidence_01.members.json.gz')}
    access=read(OUT/'historical_member_access.json')['accesses']+read(OUT/'structural_member_sources.json')['accesses']
    for entry in access:
        assert public_index[entry['member']]['SHA256']==entry['SHA256']
        assert public_index[entry['member']]['bytes']==entry['bytes']
    for entry in manifest['inherited_reference_duplicates_excluded']:
        assert entry['old_commit']==R163_SCIENCE
        assert public_index[entry['old_member']]['SHA256']==entry['SHA256']
        assert public_index[entry['old_member']]['bytes']==entry['bytes']
    assert members==manifest['members']
    write(OUT/'public_restore_receipt.json',dict(PASS=True,UTC=utc(),science_commit=commit,target=str(target),
        downloads=downloads,bytes=sum(a['bytes'] for a in downloads),members_checked=members,
        all_new_archive_bytes_and_members_match=True,bounded_old_public_metadata=old,
        historical_member_references_checked_against_public_index=len(access),old_raw_archives_downloaded=0,
        excluded_old_reference_members_checked=len(manifest['inherited_reference_duplicates_excluded']),
        Optimize=0,compilation=0,commercial_runtime_downloaded=False,
        independent_semantic_or_performance_rerun=False,recovery_IO_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(PASS=True,new_members=members,old_public_metadata=len(old))))

def cleanup():
    assert read(OUT/'public_restore_receipt.json')['PASS']
    publication=read(OUT/'publication.json');assert publication['draft'] and publication['state']=='open'
    before=shutil.disk_usage(WORK).free;roots=[OUT,TEMP,Path(read(OUT/'public_restore_receipt.json')['target'])];facts=[]
    for root in roots:
        count=size=0;skipped=[]
        for directory,dirs,names in os.walk(root,followlinks=False):
            keep=[]
            for name in dirs:
                p=Path(directory)/name
                if getattr(p.lstat(),'st_file_attributes',0)&0x400:skipped.append(str(p))
                else:keep.append(name)
            dirs[:]=keep
            for name in names:
                p=Path(directory)/name
                if getattr(p.lstat(),'st_file_attributes',0)&0x400:skipped.append(str(p));continue
                count+=1;size+=p.stat().st_size
        facts.append(dict(root=str(root),files=count,bytes=size,reparse_points_not_followed=skipped))
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(PASS=True,UTC=utc(),screening='bounded current-round metadata only',roots=facts,
        deleted_files=0,deleted_bytes=0,observed_free_bytes_before=before,observed_free_bytes_after=after,
        observed_free_space_delta=after-before,protected_workspace=check_protected(),
        unique_science_and_failures_retained=True,active_worktree_retained=True,reused_PE_DLL_and_dependencies_retained=True,
        public_recovery_assets_retained=True,old_rounds_screened_or_deleted=False,global_settings_changed=False,
        reason='no completed current-only duplicate chosen for deletion; all retained assets support the delivered evidence'))
    print(json.dumps(dict(PASS=True,deleted_files=0,deleted_bytes=0,observed_free_space_delta=after-before)))

if __name__=='__main__':
    if sys.argv[1]=='restore':restore(sys.argv[2])
    else:globals()[sys.argv[1]]()
