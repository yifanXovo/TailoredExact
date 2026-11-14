"""New-only evidence carriers and exact scientific-commit source bundle."""
from round166_common import *
import argparse,csv,gzip,io,zipfile

LIMIT=64*1024*1024

def safe_name(name):
    p=Path(name)
    assert not p.is_absolute() and '..' not in p.parts,name
    lower=p.name.lower()
    assert p.suffix.lower() not in ['.lic','.key','.pem'],name
    assert lower not in ['.env','credentials','credentials.json','gurobi130.dll'],name
    return p.as_posix()

def member(archive,name,data):
    info=zipfile.ZipInfo(safe_name(name),date_time=(2026,11,14,0,0,0))
    info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=0
    archive.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)

def compressed_map(path,entries):
    text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=list(entries[0]));writer.writeheader();writer.writerows(entries)
    with path.open('xb') as stream:
        with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0) as zipped:zipped.write(text.getvalue().encode('utf-8'))

def evidence():
    tick=time.perf_counter();assert read(OUT/'reports/summary.json')['complete']
    assert not (OUT/'evidence_archives.json').exists(),'existing carriers are immutable; inspect instead of repacking'
    root=OUT/'artifacts';root.mkdir(exist_ok=True);selected=[]
    def add(path,purpose):
        for p in sorted(path.rglob('*')):
            if p.is_file():selected.append((p,p.relative_to(ROOT).as_posix(),purpose))
    for g in read(OUT/'matrix_frozen.json')['groups']:add(Path(g['launch']['destination']),'formal-'+str(g['position']))
    for p in sorted((OUT/'qualification/controller').glob('*/raw')):add(p,'controller-qualification')
    for sub in ['global','legacy_B']:add(OUT/'qualification'/sub,'qualification-'+sub)
    selected += [(p,p.relative_to(ROOT).as_posix(),'local-LP-qualification') for p in sorted((OUT/'qualification/local').glob('*.lp'))]
    # Global ignore rules also hide tiny matrices/native logs and build logs.
    # Preserve those new objects, including failed reader/driver evidence.
    names={name for _,name,_ in selected}
    extra=list((OUT/'build').rglob('*'))+list((OUT/'qualification').rglob('*'))+list((OUT/'fees').glob('*.log'))+list((OUT/'analysis').glob('*.log'))+[OUT/'panel_stdout.log']
    for p in sorted(extra):
        if not p.is_file() or '__pycache__' in p.parts:continue
        name=p.relative_to(ROOT).as_posix()
        if name in names:continue
        if p.suffix.lower() not in ['.log','.lp','.mps','.mst','.sol'] and 'build' not in p.relative_to(OUT).parts:continue
        selected.append((p,name,'new-build-or-diagnostic-log/matrix'));names.add(name)
    for name in ['ExactEBRP.exe','Round166Qualification.exe','Round166LegacyExport.exe']:
        p=WORK/'build-cache/round166'/name
        assert p.is_file();selected.append((p,'runtime/'+name,'own-executable'))
    cache=WORK/'build-cache/round166/CMakeCache.txt'
    assert sha(cache)==read(OUT/'candidate_manifest.json')['cmake_cache']['SHA256']
    assert not any(token in cache.read_text(encoding='utf-8').upper() for token in ['WLSSECRET','PASSWORD=','LICENSEID=','TOKENSERVER='])
    selected.append((cache,'runtime/CMakeCache.txt','own-build-configuration'))
    assert len({name for _,name,_ in selected})==len(selected)
    assert sha(WORK/'build-cache/round166/ExactEBRP.exe')==read(OUT/'candidate_manifest.json')['production_PE_SHA']
    archives=[];mapping=[];current=None;current_path=None;uncompressed=0;count=0
    def close():
        nonlocal current
        if current:
            current.close();archives.append(dict(**bind(current_path),members=count,uncompressed_bytes=uncompressed));current=None
    for p,name,purpose in selected:
        n=p.stat().st_size;assert n<=LIMIT,('individual object needs a separately designed carrier',p,n)
        if current and uncompressed+n>LIMIT:close()
        if current is None:
            current_path=root/f'round166_new_evidence_{len(archives)+1:03}.zip'
            assert not current_path.exists(),'preserve incomplete attempt for inspection'
            current=zipfile.ZipFile(current_path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True)
            uncompressed=0;count=0
        data=p.read_bytes();assert len(data)==n
        member(current,name,data);mapping.append(dict(archive=current_path.relative_to(ROOT).as_posix(),member=name,bytes=n,
            SHA256=hashlib.sha256(data).hexdigest(),purpose=purpose))
        uncompressed+=n;count+=1
    close()
    assert all(a['bytes']<95*1024*1024 for a in archives)
    map_path=root/'round166_new_evidence_members.csv.gz';compressed_map(map_path,mapping)
    write(OUT/'evidence_archives.json',dict(UTC=utc(),schema='round166-new-only-carriers-v1',archives=archives,
        member_map=bind(map_path),members=len(mapping),uncompressed_bytes=sum(m['bytes'] for m in mapping),
        compressed_bytes=sum(a['bytes'] for a in archives),max_uncompressed_partition=LIMIT,
        formal_positions=12,qualification_preserved=True,own_executables=3,
        measured_CMake_cache_included=True,
        commercial_DLL_included=False,license_or_credentials_included=False,private_antecedent_included=False,
        old_carrier_repacked=False,old_complete_physical_archive_duplicated=False,
        duplicate_deletion=0,seconds=time.perf_counter()-tick,Optimize=0,generator=bind(Path(__file__))))
    print(json.dumps(dict(archives=len(archives),members=len(mapping),bytes=sum(a['bytes'] for a in archives),seconds=time.perf_counter()-tick)))

def source(science):
    tick=time.perf_counter();assert git('cat-file','-t',science)=='commit'
    assert not (OUT/'source_publication.json').exists()
    raw=read(OUT/'evidence_archives.json');separate={a['path'] for a in raw['archives']}
    changed=git('diff','--name-only','--no-renames','--diff-filter=AM',BASE,science).splitlines()
    paths=[p for p in changed if p not in separate]
    assert paths and all(p.startswith(('scripts/','config/','src/','include/','results/','docs/','.gitattributes','CMakeLists.txt')) for p in paths)
    target=OUT/'artifacts/round166_source_paper_changes.zip';assert not target.exists()
    mapping=[]
    proc=__import__('subprocess').Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=__import__('subprocess').PIPE,stdout=__import__('subprocess').PIPE)
    try:
        with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as archive:
            for name in paths:
                proc.stdin.write((science+':'+name+'\n').encode('utf-8'));proc.stdin.flush()
                header=proc.stdout.readline().decode('ascii').strip().split();assert len(header)==3 and header[1]=='blob',(name,header)
                length=int(header[2]);data=proc.stdout.read(length);assert len(data)==length and proc.stdout.read(1)==b'\n'
                member(archive,name,data)
                assert (ROOT/name).read_bytes()==data,('working/science bytes changed',name)
                mapping.append(dict(archive=target.relative_to(ROOT).as_posix(),member=name,bytes=length,SHA256=hashlib.sha256(data).hexdigest(),purpose='scientific-commit-change'))
    finally:
        proc.stdin.close();assert proc.wait(timeout=30)==0
    map_path=OUT/'artifacts/round166_source_paper_members.csv.gz';compressed_map(map_path,mapping)
    write(OUT/'source_publication.json',dict(UTC=utc(),science_commit=science,base=BASE,
        archive=bind(target),member_map=bind(map_path),changed_scientific_paths=len(changed),source_bundle_members=len(mapping),
        separately_carried_raw_archives=[dict(path=p,source_commit=science) for p in sorted(separate)],
        includes_only_new_or_changed_files=True,old_carriers_downloaded_or_repacked=0,
        exact_git_blob_bytes=True,all_working_bytes_match_science=True,
        scientific_commit_precedes_this_receipt=True,Optimize=0,seconds=time.perf_counter()-tick))
    print('Exact scientific-commit new/changed source/paper bundle:',len(mapping),'members.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['evidence','source']);parser.add_argument('--science');args=parser.parse_args()
    evidence() if args.action=='evidence' else source(args.science)
