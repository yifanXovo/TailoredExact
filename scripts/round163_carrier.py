"""New-only evidence packaging, bounded anonymous recovery and metadata screening."""
from round163_common import *
import gzip,shutil,urllib.request,zipfile

def package():
    assert read(OUT/'panel_complete.json')['arms']==18 and not budget()['unclosed']
    target=OUT/'artifacts';target.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();files=[]
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or target in p.parents:continue
        if any(s in p.parts for s in ('evidence','public_restore')):continue
        assert p.suffix.lower() not in ('.exe','.dll','.lic','.key','.pem'),('runtime/credential excluded',p)
        files.append(p)
    files.extend(sorted((ROOT/'scripts').glob('round163*')))
    files.append(ROOT/'docs/round163_stage_confirmation.md')
    files.extend(ROOT/'results/unified_exact_round137'/n for n in ['paper_body.md','mathematical_analysis.md','supplement.md'])
    files=sorted(set(p for p in files if p.is_file()))
    archives=[];index=[];bundle=None;dest=None
    def close():
        nonlocal bundle,index
        if bundle is None:return
        bundle.close()
        listing=OUT/'evidence'/(dest.stem+'.members.json.gz');listing.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(listing,'wt',encoding='utf-8') as f:json.dump(index,f,separators=(',',':'))
        archives.append(dict(path=dest.relative_to(ROOT).as_posix(),SHA256=sha(dest),bytes=dest.stat().st_size,
            members=len(index),uncompressed_bytes=sum(v['bytes'] for v in index),index=listing.relative_to(ROOT).as_posix(),index_SHA256=sha(listing)))
        print(json.dumps(dict(archive=dest.name,bytes=dest.stat().st_size,members=len(index))),flush=True)
        bundle=None;index=[]
    for p in files:
        if bundle is None:
            dest=target/f'new_evidence_{len(archives)+1:02}.zip'
            bundle=zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True)
        name=p.relative_to(ROOT).as_posix();before=sha(p);size=p.stat().st_size
        bundle.write(p,name)
        assert sha(p)==before,'evidence changed while packaging'
        member=bundle.getinfo(name)
        index.append(dict(path=name,SHA256=before,bytes=size,compressed_bytes=member.compress_size))
        if dest.stat().st_size>=40*1024**2:close()
    close()
    write(OUT/'carrier_manifest.json',dict(schema='round163-new-only-carrier-v1',UTC=utc(),archives=archives,
        bytes=sum(v['bytes'] for v in archives),members=sum(v['members'] for v in archives),
        unique_new_science_and_failures_retained=True,old_raw_carriers_included=0,commercial_runtime_credentials_or_licenses_included=False,
        reused_production_PE_published=False,reused_production_PE_SHA256=PE_SHA,
        recovery_scope='new byte/member evidence only; licensed Windows execution and measured performance not replayed',
        packaging_IO_seconds=time.perf_counter()-start))

def restore(commit):
    start=time.perf_counter();target=WORK/'restore'/f'round163-public-{commit[:12]}'
    target.mkdir(parents=True,exist_ok=False);manifest=read(OUT/'carrier_manifest.json');downloads=[];members=0
    for archive in manifest['archives']:
        name=archive['path'];url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/{name}'
        dest=target/Path(name).name;tick=time.perf_counter()
        with urllib.request.urlopen(url,timeout=30) as response,dest.open('xb') as f:
            assert response.status==200
            shutil.copyfileobj(response,f,1024*1024)
        assert dest.stat().st_size==archive['bytes'] and sha(dest)==archive['SHA256']
        entries=read_gz(ROOT/archive['index'])
        assert len(entries)==archive['members']
        with zipfile.ZipFile(dest) as z:
            assert sorted(z.namelist())==sorted(v['path'] for v in entries)
            for entry in entries:
                path=Path(entry['path']);assert not path.is_absolute() and '..' not in path.parts
                raw=z.read(entry['path']);assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['SHA256']
                members+=1
        downloads.append(dict(url=url,path=str(dest),bytes=dest.stat().st_size,SHA256=sha(dest),seconds=time.perf_counter()-tick,anonymous=True))
        print(json.dumps(dict(downloaded=dest.name,members=members)),flush=True)
    assert members==manifest['members']
    write(OUT/'public_restore_receipt.json',dict(PASS=True,UTC=utc(),science_commit=commit,target=str(target),downloads=downloads,
        bytes=sum(v['bytes'] for v in downloads),members_checked=members,all_new_archive_bytes_and_members_match=True,
        old_archives_downloaded=0,Optimize=0,compilation=0,commercial_runtime_downloaded=False,
        independent_semantic_or_performance_rerun=False,recovery_IO_seconds=time.perf_counter()-start))

def read_gz(p):
    with gzip.open(p,'rt',encoding='utf-8') as f:return json.load(f)

def cleanup():
    # Zero deletion is deliberate: the active worktree, unique raw/failures,
    # dependencies and bounded new-only recovery remain useful assets.
    assert read(OUT/'public_restore_receipt.json')['PASS']
    assert read(OUT/'publication.json')['draft'] and read(OUT/'publication.json')['state']=='open'
    before=shutil.disk_usage(WORK).free
    roots=[OUT,TEMP,Path(read(OUT/'public_restore_receipt.json')['target'])]
    facts=[]
    for root in roots:
        files=[];skipped=[]
        for directory,dirs,names in os.walk(root,followlinks=False):
            retained=[]
            for name in dirs:
                path=Path(directory)/name
                if getattr(path.lstat(),'st_file_attributes',0)&0x400:skipped.append(str(path))
                else:retained.append(name)
            dirs[:]=retained
            files.extend(Path(directory)/n for n in names if not (getattr((Path(directory)/n).lstat(),'st_file_attributes',0)&0x400))
        facts.append(dict(root=str(root),files=len(files),bytes=sum(p.stat().st_size for p in files),reparse_points_not_followed=skipped))
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(PASS=True,UTC=utc(),screening='bounded current-round metadata only',roots=facts,
        deleted_files=0,deleted_bytes=0,observed_free_bytes_before=before,observed_free_bytes_after=after,observed_free_space_delta=after-before,
        protected_workspace=check_protected(),active_worktree_retained=True,reused_PE_and_runtime_retained=True,
        unique_science_and_failures_retained=True,public_recovery_assets_retained=True,old_rounds_screened_or_deleted=False,
        global_settings_changed=False,reason='no current-only completed duplicate selected for deletion; all retained roots support this delivery/recovery'))
    print(json.dumps(dict(PASS=True,deleted_files=0,metadata_roots=facts)))

if __name__=='__main__':
    if sys.argv[1]=='restore':restore(sys.argv[2])
    else:globals()[sys.argv[1]]()
