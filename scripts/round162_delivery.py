"""Current-only science carrier, staged-byte public manifest and bounded recovery.

No solver, commercial binary, license or credential is copied by this script.
Publication is a separate explicit normal Git push / Draft-PR operation.
"""
from round162_common import *
import zipfile,shutil,urllib.request,urllib.parse

def package():
    assert not budget()['unclosed']
    tick=time.perf_counter();archive_dir=OUT/'artifacts';archive_dir.mkdir(exist_ok=True)
    assert not list(archive_dir.glob('new_evidence_*.zip')),'carrier already exists'
    sources=[]
    for name in ('runs','qualification','fees','launches','engineering/measured_source_bytes'):
        sources.extend(p for p in (OUT/name).rglob('*') if p.is_file())
    sources=sorted(set(sources));pieces=[];chunk=[];size=0
    for p in sources:
        assert p.suffix.lower() not in ('.exe','.dll','.lic','.key','.pfx')
        if size+p.stat().st_size>256*1024*1024 and chunk:
            pieces.append(chunk);chunk=[];size=0
        chunk.append(p);size+=p.stat().st_size
    if chunk:pieces.append(chunk)
    archives=[]
    for i,chunk in enumerate(pieces,1):
        target=archive_dir/f'new_evidence_{i:02}.zip';members=[]
        with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in chunk:
                name=p.relative_to(ROOT).as_posix();raw=p.read_bytes();z.writestr(name,raw)
                members.append(dict(member=name,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
        assert target.stat().st_size<95*1024*1024,'split compressed carrier before publication'
        index=target.with_name(target.stem+'.members.json.gz');save_gz(index,members)
        archives.append(dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,
            members=len(members),uncompressed_bytes=sum(x['bytes'] for x in members),index=index.relative_to(ROOT).as_posix(),index_SHA256=sha(index)))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=archives,old_archives_repacked=0,commercial_assets=False,
        unique_new_members=sum(v['members'] for v in archives),bytes=sum(v['bytes'] for v in archives),
        recovery_scope='new recorded matrices, evidence and final measured bytes; old inputs/parents remain fixed references'))
    write(OUT/'engineering/packaging.json',dict(UTC=utc(),seconds=time.perf_counter()-tick,files=len(sources),
        uncompressed_bytes=sum(p.stat().st_size for p in sources),archives=archives,science_Optimize=0,ordinary_IO=True))
    print(json.dumps(dict(archives=len(archives),bytes=sum(v['bytes'] for v in archives),seconds=time.perf_counter()-tick)),flush=True)

def manifest():
    # Stage the intended science files before this action. Hash index bytes,
    # not text materialized by a checkout's autocrlf settings.
    paths=git('diff','--cached','--name-only',BASE).decode().splitlines()
    records=[]
    for name in paths:
        if name.endswith('/public_manifest.json'):continue
        assert name.startswith(('results/unified_exact_round162/','scripts/round162_','src/','include/','docs/')) or name in ('CMakeLists.txt','.gitattributes'),name
        raw=git('show',':'+name)
        records.append(dict(path=name,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
    assert any(v['path'].endswith('goal.md') for v in records)
    write(OUT/'public_manifest.json',dict(UTC=utc(),files=records,own_path_excluded=True,
        hash_semantics='exact staged Git bytes; measured source and archived members have independent actual-byte hashes',
        old_history_replay=False,commercial_runtime_published=False))
    print('public staged-byte manifest:',len(records),'files',flush=True)

def restore(commit):
    tick=time.perf_counter();target=WORK/'restore'/('round162_public_'+commit[:12]);target.mkdir(parents=True,exist_ok=False)
    expected=sha(OUT/'public_manifest.json');downloads=[]
    def fetch(name):
        url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+commit+'/'+urllib.parse.quote(name,safe='/')
        with urllib.request.urlopen(url,timeout=60) as r:raw=r.read()
        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        downloads.append(dict(path=name,bytes=len(raw),SHA256=sha(dest)));return dest
    manifest_path=fetch('results/unified_exact_round162/public_manifest.json');assert sha(manifest_path)==expected
    public=read(manifest_path)
    for row in public['files']:
        path=fetch(row['path']);assert path.stat().st_size==row['bytes'] and sha(path)==row['SHA256'],row['path']
    carrier=read(target/'results/unified_exact_round162/carrier_manifest.json');member_count=0
    for a in carrier['archives']:
        path=target/a['path'];assert sha(path)==a['SHA256'];index=target/a['index'];assert sha(index)==a['index_SHA256']
        members=load_gz(index);assert len(members)==a['members']
        with zipfile.ZipFile(path) as z:
            assert set(z.namelist())=={v['member'] for v in members}
            for v in members:
                raw=z.read(v['member']);assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['SHA256'];member_count+=1
    value=dict(PASS=True,UTC=utc(),fixed_science=commit,root=str(target),download_count=len(downloads),
        downloaded_bytes=sum(v['bytes'] for v in downloads),members_verified=member_count,downloads=downloads,
        old_archives_downloaded=0,commercial_runtime=False,Optimize=0,compilation=0,
        scope='anonymous new-only byte/member recovery; not an independent Windows semantic or performance rerun',seconds=time.perf_counter()-tick)
    write(OUT/'public_restore_receipt.json',value)
    write(OUT/'publication_costs.json',dict(UTC=utc(),public_IO_seconds=value['seconds'],packaging=read(OUT/'engineering/packaging.json'),
        scientific_solver_seconds=0,nested_download_member_validation_not_added_twice=True))
    print(json.dumps({k:v for k,v in value.items() if k!='downloads'}),flush=True)

def cleanup():
    assert not budget()['unclosed'];before=shutil.disk_usage(WORK).free;roots=[ROOT,BUILD,WORK/'temp/round162']
    roots.extend((WORK/'restore').glob('round162_public_*'))
    inventory=[]
    for root in roots:
        assert root.resolve().is_relative_to(WORK.resolve()),root
        files=[p for p in root.rglob('*') if p.is_file()]
        inventory.append(dict(root=str(root),files=len(files),file_bytes=sum(p.stat().st_size for p in files)))
    protected=read(OUT/'infra/protected_initial.json');count=0
    for tree in protected['trees']:
        for path,digest in tree['dirty'].items():assert sha(Path(tree['tree'])/path)==digest;count+=1
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),scope='bounded metadata screening, current round only',inventory=inventory,
        deleted_files=0,deleted_bytes=0,free_bytes_before=before,free_bytes_after=after,observed_free_delta=after-before,
        protected_dirty_hashes_checked=count,protected_unchanged=True,old_round_deletion=False,
        retained='active worktree, unique scientific evidence/failures, all actual PEs/runtime dependencies, public recovery and build assets',
        reason='zero deletion; no current object needs removal for acceptance and measured runtime/source history remains necessary'))
    print('PASS bounded current-only screening; zero deletion; protected dirty hashes:',count,flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
