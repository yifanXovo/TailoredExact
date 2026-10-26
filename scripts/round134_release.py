"""Current-round publication, explicit dependencies and original-byte capsules."""
from round134_common import *
import csv,gzip,importlib,shutil,zipfile,re

FORBIDDEN={'.exe','.dll','.o','.obj','.a','.lib','.lic','.ttf','.otf','.woff','.woff2','.pyc'}
def idle():
    assert not budget()['unclosed']
    assert read(OUT/'sequence_driver_status.json')['state']=='COMPLETE_C_D_E_NATIVE'

def safe(name):
    p=Path(name)
    assert p.suffix.lower() not in FORBIDDEN,name
    assert not any(part in ('.git','__pycache__') for part in p.parts),name
    assert '\\' not in name and ':' not in name and '..' not in p.parts,name

def scan(raw,name):
    safe(name)
    # Raw numerical logs and public algorithm code may name license APIs or a
    # license path. Actual credential assignments/files are forbidden.
    if name.lower().endswith(('.png','.jpg','.jpeg','.pdf','.gz','.zip')):return
    text=raw.decode('utf-8',errors='replace')
    patterns=[r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
        r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{40,}',
        r'(?im)^\s*(?:WLSACCESSID|WLSSECRET|CSAPISECRET|APISECRET)\s*=\s*\S+',
        r'(?i)Bearer\s+[A-Za-z0-9._-]{30,}']
    for pattern in patterns:assert not re.search(pattern,text),('credential pattern',name,pattern)

def source_capsule():
    idle();candidate=read(OUT/'candidate_manifest.json')
    # Import only the pure graph actually used by current postverification and
    # mathematics. No root solver or runtime DLL-binding module is imported.
    for name in ('round134_read','round134_count_bound','round133_joint_check','round88_ot_epigraph'):
        importlib.import_module(name)
    helpers={}
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if not path:continue
        path=Path(path).resolve()
        if path.parent==ROOT/'scripts' and path.suffix=='.py' and path.name not in ('round134_release.py','round134_portable_check.py','round133_portable_check.py'):
            helpers[path.relative_to(ROOT).as_posix()]=sha(path)
    assert 'round100_gurobi_runtime' not in sys.modules and 'gurobipy' not in sys.modules
    files=dict(candidate['source_hashes']);files.update(helpers)
    extras=['CMakeLists.txt','.gitattributes','scripts/round130_export.cpp',
        'results/unified_exact_round94/preregistration.json']
    for name in extras:files[name]=sha(ROOT/name)
    target=OUT/'artifacts/current_source_bytes.zip';target.parent.mkdir(exist_ok=True)
    assert not target.exists()
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,digest in sorted(files.items()):
            raw=(ROOT/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
            scan(raw,name);z.writestr(name,raw)
    binding=read(WORK/'build-cache/round130/main_binding.json')
    assert binding['source']==sha(ROOT/'src/main.cpp')
    write(OUT/'source_publication.json',dict(UTC=utc(),schema='round134-exact-current-source-publication-v1',
        source_bundle=dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,members=files),
        execution_helpers=sorted(helpers),required_configuration_files=['results/unified_exact_round94/preregistration.json'],
        reused_main_source_binding=dict(source_SHA=sha(ROOT/'src/main.cpp'),binding_SHA=sha(WORK/'build-cache/round130/main_binding.json'),
            object_SHA=read(OUT/'candidate_build.json')['main_object']['SHA256'],source_matches=True),
        no_native_assets_fonts_credentials_or_foreign_full_papers=True,Optimize=0,compile=0))
    print(json.dumps(dict(source_capsule=str(target),helpers=len(helpers),native_sources=len(candidate['source_hashes']))))

def archive(name,files):
    folder=OUT/'artifacts';folder.mkdir(exist_ok=True)
    target=folder/(name+'.zip')
    index=OUT/'evidence'/(name+'.members.json.gz');index.parent.mkdir(exist_ok=True)
    files=sorted({p if p.is_absolute() else ROOT/p for p in map(Path,files)})
    members=[];reused=False
    if target.exists() and index.exists():
        # A completed current carrier is reused only after its saved member
        # identities and current authoritative files agree with its real bytes.
        with gzip.open(index,'rt',encoding='utf-8') as stream:members=json.load(stream)
        expected={m['path']:m for m in members}
        assert set(expected)=={p.relative_to(ROOT).as_posix() for p in files}
        with zipfile.ZipFile(target) as z:
            assert len(z.namelist())==len(set(z.namelist()))==len(expected) and set(z.namelist())==set(expected)
            for info in z.infolist():
                m=expected[info.filename];raw=z.read(info)
                assert len(raw)==m['bytes'] and hashlib.sha256(raw).hexdigest()==m['SHA256']==sha(ROOT/info.filename)
        reused=True
    else:
        if target.exists():
            # Preserve the exact incomplete output of the first path-transport
            # failure, rather than overwriting it or treating it as healthy.
            failure=OUT/'repair/pack_attempt01'/target.name;failure.parent.mkdir(parents=True,exist_ok=True)
            assert target.resolve().is_relative_to(ROOT.resolve()) and failure.resolve().is_relative_to(ROOT.resolve())
            assert not failure.exists();target.replace(failure)
        assert not index.exists()
        with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for path in files:
                relative=path.relative_to(ROOT).as_posix();raw=path.read_bytes();scan(raw,relative)
                z.writestr(relative,raw)
                members.append(dict(path=relative,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
        with gzip.open(index,'wt',encoding='utf-8') as stream:json.dump(members,stream,separators=(',',':'))
    # Keep uploaded files below GitHub's 100MB limit. Splitting changes only the
    # new carrier's transport; old carriers are never rewritten.
    pieces=[]
    if target.stat().st_size>48*1024*1024:
        with target.open('rb') as stream:
            part=0
            while True:
                chunk=stream.read(32*1024*1024)
                if not chunk:break
                part+=1;piece=target.with_name(target.name+f'.part{part:03}')
                if piece.exists():assert piece.read_bytes()==chunk
                else:
                    with piece.open('xb') as output:output.write(chunk)
                pieces.append(dict(path=piece.relative_to(ROOT).as_posix(),bytes=len(chunk),SHA256=sha(piece)))
        # The full local new carrier remains for recovery/preflight. Only pieces
        # will be staged when split; no deletion of authoritative raw occurs.
    else:pieces=[dict(path=target.relative_to(ROOT).as_posix(),bytes=target.stat().st_size,SHA256=sha(target))]
    return dict(name=name+'.zip',SHA256=sha(target),compressed_bytes=target.stat().st_size,
        uncompressed_bytes=sum(m['bytes'] for m in members),file_count=len(members),pieces=pieces,
        member_index=dict(path=index.relative_to(ROOT).as_posix(),SHA256=sha(index),bytes=index.stat().st_size),
        existing_completed_carrier_verified_and_reused=reused)

def pack():
    idle();assert not (OUT/'raw_archive_manifest.json').exists();records=[]
    for stage in ('C','D'):
        for group in read(OUT/f'{stage}_matrix_frozen.json')['groups']:
            folder=OUT/group['group']
            assert (Path(group['launch']['destination'])/'verification_closeout.json').exists()
            records.append(archive(f'campaign_{stage}_{group["position"]:02}',[p for p in folder.rglob('*') if p.is_file()]))
    current_progress=[]
    for stage in ('C','D'):
        for group in read(OUT/f'{stage}_matrix_frozen.json')['groups']:
            r=read(Path(group['launch']['destination'])/'result.json')
            if r.get('gurobi_progress_path'):current_progress.append(Path(r['gurobi_progress_path']))
    if current_progress:records.append(archive('current_native_progress',current_progress))
    # Fixed current-only math plus failed attempts and meters are explicitly
    # retained, without shipping any previous round's campaign.
    members=[p for name in ('math','fees','cost_segments','infra') for p in (OUT/name).rglob('*') if p.is_file() and p.suffix.lower() not in FORBIDDEN]
    records.append(archive('math_failures_and_costs',members))
    write(OUT/'raw_archive_manifest.json',dict(schema='round134-finite-current-carriers-v1',UTC=utc(),archives=records,
        raw_remains_authoritative_in_place=True,all_fixed_positions_retained=True,historical_carriers_rewritten=0))
    print(json.dumps(dict(archives=len(records),members=sum(r['file_count'] for r in records),compressed_bytes=sum(r['compressed_bytes'] for r in records))))

def manifest():
    idle();raw=read(OUT/'raw_archive_manifest.json');files={}
    exclude={'RESUME.md','export_manifest.json','public_restore_receipt.json','remote_readback.json','completion_audit.json','resource_accounting.json'}
    for p in OUT.rglob('*'):
        if not p.is_file() or p.name in exclude:continue
        rel=p.relative_to(OUT)
        if rel.parts[0] in {'campaign','fees','cost_segments','infra','math'}:continue
        if p.suffix.lower() in FORBIDDEN or '__pycache__' in p.parts:continue
        if rel.parts[0]=='artifacts' and p.name not in {'current_source_bytes.zip'}:continue
        name=p.relative_to(ROOT).as_posix();scan(p.read_bytes(),name)
        files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=None,source_path=name)
    for record in raw['archives']:
        for piece in [*record['pieces'],record['member_index']]:
            name=piece['path'];files[name]=dict(bytes=piece['bytes'],SHA256=piece['SHA256'],source_commit=None,source_path=name)
    for p in (ROOT/'scripts').glob('round134*.py'):
        name=p.relative_to(ROOT).as_posix();files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=None,source_path=name)
    # The old engine is reused byte-for-byte, and the one tiny carrier is an
    # explicit fixed dependency rather than an old whole-study restoration.
    old='scripts/round133_portable_check.py';p=ROOT/old
    files[old]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=BASE,source_path=old)
    tiny='results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip';p=ROOT/tiny
    files[tiny]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit='52b02252ba47e8228b73e071d6ed692385a4f816',source_path=tiny)
    for stage in ('C','D'):
        for group in read(OUT/f'{stage}_matrix_frozen.json')['groups']:
            name=group['launch']['panel']['input_path'];p=ROOT/name
            files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=BASE,source_path=name)
    for root in read(OUT/'math/root_plan.json')['roots']:
        name=read(OUT/'math/roots'/root['role']/'scope.json')['panel']['input_path'];p=ROOT/name
        files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=BASE,source_path=name)
    write(OUT/'export_manifest.json',dict(schema='round134-current-only-fixed-commit-recovery-v1',UTC=utc(),files=files,
        archives=raw['archives'],checker='scripts/round134_portable_check.py',
        recovery_scope='all36 current raw arms plus exact tiny and six root LP records; no historical campaigns',
        no_Optimize_compilation_or_vendor_DLL_loads=True))
    print(json.dumps(dict(files=len(files),archives=len(raw['archives']))))

if __name__=='__main__':{'source':source_capsule,'pack':pack,'manifest':manifest}[sys.argv[1]]()
