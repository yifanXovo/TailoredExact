"""Current-only evidence carriers and source bytes; no old campaign restoration."""
from round135_common import *
import gzip, importlib, shutil, zipfile
import round134_release as old
FORBIDDEN=old.FORBIDDEN
scan=old.scan
archive=type(old.archive)(old.archive.__code__,dict(vars(old),OUT=OUT))
def idle():
    assert not budget()['unclosed']
    assert read(OUT/'candidate_decision.json')['study_complete'] is True
def source_capsule():
    idle();candidate=read(OUT/'candidate_manifest.json')
    importlib.import_module('round135_read')
    helpers={}
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if not path:continue
        path=Path(path).resolve()
        if path.parent==ROOT/'scripts' and path.suffix=='.py' and not any(t in path.name for t in ('release','portable_check','public_restore')):
            helpers[path.relative_to(ROOT).as_posix()]=sha(path)
    assert 'round100_gurobi_runtime' not in sys.modules and 'gurobipy' not in sys.modules
    files=dict(candidate['source_hashes']);files.update(helpers)
    for n in ('CMakeLists.txt','.gitattributes','results/unified_exact_round94/preregistration.json'):files[n]=sha(ROOT/n)
    target=OUT/'artifacts/current_source_bytes.zip';target.parent.mkdir(exist_ok=True);assert not target.exists()
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,digest in sorted(files.items()):
            raw=(ROOT/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
            scan(raw,name);z.writestr(name,raw)
    write(OUT/'source_publication.json',dict(UTC=utc(),schema='round135-exact-current-source-publication-v1',
        source_bundle=dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,members=files),
        execution_helpers=sorted(helpers),required_configuration_files=['results/unified_exact_round94/preregistration.json'],
        main_recompiled=True,main_source_SHA=sha(ROOT/'src/main.cpp'),main_object_SHA=sha(BUILD/'main.o'),
        no_native_assets_credentials_fonts_or_author_manuscript=True,Optimize=0,compile=0))
    print(json.dumps(dict(helpers=len(helpers),source_capsule=str(target))))
def pack():
    idle();assert not (OUT/'raw_archive_manifest.json').exists();records=[];progress=[]
    done=set(read(OUT/'reports/summary.json')['completed_positions'])
    for stage in ('C','D'):
        for group in read(OUT/f'{stage}_matrix_frozen.json')['groups']:
            if f"{stage}{group['position']:02}" not in done:continue
            folder=OUT/group['group'];d=Path(group['launch']['destination'])
            assert (d/'verification_closeout.json').exists()
            records.append(archive(f'campaign_{stage}_{group["position"]:02}',[p for p in folder.rglob('*') if p.is_file()]))
            result=read(d/'result.json')
            if result.get('gurobi_progress_path'):progress.append(Path(result['gurobi_progress_path']))
    if progress:records.append(archive('current_native_progress',progress))
    transport=read(OUT/'repair/helper_byte_transport.json')
    explicit=[r['path'] for r in transport.get('input_differences',[])]
    if explicit:
        records.append(archive('explicit_input_dependencies',[ROOT/n for n in explicit]))
    members=[p for name in ('roots','fees','cost_segments','infra','repair') for p in (OUT/name).rglob('*') if p.is_file() and p.suffix.lower() not in FORBIDDEN]
    records.append(archive('AP_roots_failures_and_costs',members))
    write(OUT/'raw_archive_manifest.json',dict(schema='round135-finite-current-carriers-v1',UTC=utc(),archives=records,
        entered_positions=sorted(done),registered_positions=32,all_entered_positions_retained=True,
        explicit_original_input_members=explicit,
        raw_remains_authoritative_in_place=True,historical_carriers_rewritten=0))
    print(json.dumps(dict(archives=len(records),compressed_bytes=sum(r['compressed_bytes'] for r in records))))
def manifest():
    idle();raw=read(OUT/'raw_archive_manifest.json');files={}
    excluded={'RESUME.md','RESUME.json','export_manifest.json','public_restore_receipt.json','remote_readback.json',
        'completion_audit.json','resource_accounting.json'}
    for p in OUT.rglob('*'):
        if not p.is_file() or p.name in excluded:continue
        rel=p.relative_to(OUT)
        if rel.parts[0] in {'campaign','fees','cost_segments','infra','roots','repair'}:continue
        if p.suffix.lower() in FORBIDDEN or '__pycache__' in p.parts:continue
        if rel.parts[0]=='artifacts' and p.name!='current_source_bytes.zip':continue
        name=p.relative_to(ROOT).as_posix();scan(p.read_bytes(),name)
        files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=None,source_path=name)
    for record in raw['archives']:
        for part in [*record['pieces'],record['member_index']]:
            files[part['path']]=dict(bytes=part['bytes'],SHA256=part['SHA256'],source_commit=None,source_path=part['path'])
    for p in (ROOT/'scripts').glob('round135*'):
        if p.suffix.lower() not in {'.py','.cpp'}:continue
        name=p.relative_to(ROOT).as_posix();files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=None,source_path=name)
    engine='scripts/round133_portable_check.py';p=ROOT/engine
    files[engine]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=BASE,source_path=engine)
    for role in read(OUT/'input_provenance.json'):
        name=role['input_path'];p=ROOT/name
        if name in raw.get('explicit_original_input_members',[]):continue
        files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=BASE,source_path=name)
    for name,item in files.items():
        if item['source_commit']:
            blob=git('show',f"{item['source_commit']}:{item['source_path']}")
            assert len(blob)==item['bytes'] and hashlib.sha256(blob).hexdigest()==item['SHA256'],name
    summary=read(OUT/'reports/summary.json')
    write(OUT/'export_manifest.json',dict(schema='round135-current-only-fixed-commit-recovery-v1',UTC=utc(),files=files,
        archives=raw['archives'],checker='scripts/round135_portable_check.py',formal_positions=summary['completed'],
        recovery_scope='All entered current arms and two AP roots; saved original/IND dependencies only; no historical campaigns',
        fixed_dependency_Git_blob_bytes_verified=True,
        no_Optimize_compilation_or_vendor_DLL_loads=True))
    print(json.dumps(dict(files=len(files),archives=len(raw['archives']))))
if __name__=='__main__':{'source':source_capsule,'pack':pack,'manifest':manifest}[sys.argv[1]]()
