"""New-only evidence packaging, public byte recovery and zero-delete receipts."""
from round168_common import *
import zipfile,gzip,concurrent.futures,urllib.request,os,platform

def package():
    out=OUT/'artifacts';out.mkdir(exist_ok=True);archive=out/'round168_new_raw_and_runtime.zip'
    assert not archive.exists(),'one carrier, never overwrite published bytes'
    entries=[]
    for name in ['campaign','tiny_qualification','tiny_frozen','preflight']:
        for p in sorted((OUT/name).rglob('*')):
            if p.is_file():entries.append((p,p.relative_to(OUT).as_posix()))
    for p in sorted((OUT/'review').glob('*.png')):entries.append((p,'review/'+p.name))
    entries.append((WORK/'build-cache/round168/Round168RouteFamily.exe','runtime/Round168RouteFamily.exe'))
    for path in ['src/round168_route_family.cpp','CMakeLists.txt']:
        entries.append((ROOT/path,'measured_source/'+path))
    rows=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,member in entries:
            assert p.suffix.lower() not in ['.dll','.lic'] and not any(w in p.name.lower() for w in ['license','credential'])
            z.write(p,member);rows.append(dict(member=member,bytes=p.stat().st_size,SHA256=sha(p),local_source=str(p)))
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    membermap=out/'round168_new_raw_members.csv.gz';membermap.write_bytes(gzip.compress(stream.getvalue().encode('utf-8'),mtime=0))
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist())==len(rows)
        for r in rows:assert hashlib.sha256(z.read(r['member'])).hexdigest()==r['SHA256']
    write(OUT/'evidence_archives.json',dict(UTC=utc(),new_only=True,carrier=bind(archive),membermap=bind(membermap),members=len(rows),
        raw_uncompressed_bytes=sum(r['bytes'] for r in rows),local_member_readback=True,own_project_PE_included=True,
        commercial_DLL_license_credentials_private_antecedent_included=False,historical_carriers_repacked=False,
        old_archive_members='archive_manifest.json references fixed R163/R164 carriers; archive/ is excluded',
        restore='campaign/, tiny_qualification/, tiny_frozen/, preflight/ expand under results/unified_exact_round168/; runtime/ is offline research PE'))
    print('New-only carrier',len(rows),'members',archive.stat().st_size,'bytes')

def recover(science):
    root=WORK/'recovery'/('round168-public-'+science[:12]);root.mkdir(parents=True,exist_ok=False)
    paths=git('diff','--name-only',BASE,science).splitlines();rows=[]
    for name in paths:
        raw=subprocess.check_output(['git','show',science+':'+name],cwd=ROOT)
        rows.append(dict(path=name,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
    start=time.perf_counter()
    def fetch(row):
        tick=time.perf_counter();name=row['path'];url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+science+'/'+urllib.parse.quote(name,safe='/')
        request=urllib.request.Request(url,headers={'User-Agent':'Round168-public-integrity-readback'})
        with urllib.request.urlopen(request,timeout=60) as response:raw=response.read()
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['SHA256'],name
        dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        return dict(**row,PASS=True,anonymous=True,normal_TLS=True,seconds=time.perf_counter()-tick)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:results=list(executor.map(fetch,rows))
    rawManifest=read(root/'results/unified_exact_round168/evidence_archives.json')
    mapPath=root/rawManifest['membermap']['path'];carrier=root/rawManifest['carrier']['path']
    members=list(csv.DictReader(io.StringIO(gzip.decompress(mapPath.read_bytes()).decode('utf-8'))))
    with zipfile.ZipFile(carrier) as z:
        assert len(z.infolist())==len(members)
        for r in members:
            raw=z.read(r['member']);assert len(raw)==int(r['bytes']) and hashlib.sha256(raw).hexdigest()==r['SHA256'],r['member']
    value=dict(UTC=utc(),scientific_commit=science,files=len(results),bytes=sum(r['bytes'] for r in results),results=results,
        new_raw_members_verified=len(members),all_member_bytes_verified=True,anonymous=True,normal_TLS=True,
        old_raw_downloaded=False,fresh_root=str(root),seconds=time.perf_counter()-start,PASS=True,
        scope='new or modified source/paper/necessary evidence byte recovery only; not a licensed semantic or performance rerun')
    write(OUT/'public_recovery.json',value);write(root/'recovery_receipt.json',value);print('Public byte recovery PASS',len(results),'files;',len(members),'raw members')

def protect():
    before=read(OUT/'protected_entry_correction.json')['protected'];after=protected();assert before==after
    write(OUT/'protected_tree_check.json',dict(UTC=utc(),PASS=True,protected=after,all_tracked_status_and_dirty_file_bytes_equal=True,zero_delete=True))

def cleanup():
    protect();start=time.perf_counter();freeBefore=__import__('shutil').disk_usage(WORK).free;assets=[]
    recovery=Path(read(OUT/'public_recovery.json')['fresh_root'])
    for p in [OUT,WORK/'build-cache/round168',WORK/'temp/round168',recovery]:
        files=[f for f in p.rglob('*') if f.is_file()];assets.append(dict(root=str(p),files=len(files),logical_bytes=sum(f.stat().st_size for f in files),retained=True))
    freeAfter=__import__('shutil').disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),screening='bounded current-round metadata only',assets=assets,actions=[],deleted_files=0,deleted_logical_bytes=0,
        volume_free_before=freeBefore,volume_free_after=freeAfter,observed_free_change=freeAfter-freeBefore,
        policy='retain unique models/failures, actual PE/build dependencies, QA, public recovery and active Draft; zero deletion allowed',seconds=time.perf_counter()-start))
    print('Protected trees equal; current-only screening retained all assets, zero deletions')

if __name__=='__main__':
    if sys.argv[1]=='recover':recover(sys.argv[2])
    else:globals()[sys.argv[1]]()
