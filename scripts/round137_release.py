"""Current-only evidence packaging, using the existing bounded carrier format."""
from round137_common import *
import importlib, shutil, types, zipfile
import round134_release as previous

FORBIDDEN=previous.FORBIDDEN
scan=previous.scan
from concurrent.futures import ThreadPoolExecutor
import gzip

class ForwardZipSink:
    """Append standard ZIP data descriptors, avoiding a flush/seek per tiny member."""
    def __init__(self,stream):self.stream=stream
    def write(self,data):return self.stream.write(data)
    def tell(self):return self.stream.tell()
    def flush(self):return self.stream.flush()
    def seek(self,*args):raise OSError('forward-only current carrier')

def bounded_member_reads(paths):
    def load(path):
        relative=path.relative_to(ROOT).as_posix()
        raw=path.read_bytes();scan(raw,relative)
        return relative,raw
    # At most32 submitted members; pool8 performs only immutable local reads.
    with ThreadPoolExecutor(max_workers=8) as pool:
        for first in range(0,len(paths),32):
            yield from pool.map(load,paths[first:first+32])

def archive(name,files):
    folder=OUT/'artifacts';folder.mkdir(exist_ok=True)
    target=folder/(name+'.zip');index=OUT/'evidence'/(name+'.members.json.gz')
    index.parent.mkdir(exist_ok=True)
    paths=sorted({p if p.is_absolute() else ROOT/p for p in map(Path,files)})
    members=[];reused=False
    if target.exists() and index.exists():
        with gzip.open(index,'rt',encoding='utf-8') as stream:members=json.load(stream)
        expected={m['path']:m for m in members}
        assert len(expected)==len(members) and set(expected)=={p.relative_to(ROOT).as_posix() for p in paths}
        # Revalidate both archived bytes and every actual authoritative input.
        with ThreadPoolExecutor(max_workers=8) as pool:
            for first in range(0,len(paths),32):
                chunk=paths[first:first+32]
                for path,digest in zip(chunk,pool.map(sha,chunk)):
                    assert digest==expected[path.relative_to(ROOT).as_posix()]['SHA256']
        with zipfile.ZipFile(target) as z:
            assert len(z.namelist())==len(set(z.namelist()))==len(expected)
            assert set(z.namelist())==set(expected)
            for info in z.infolist():
                m=expected[info.filename];raw=z.read(info)
                assert len(raw)==m['bytes'] and hashlib.sha256(raw).hexdigest()==m['SHA256']
        reused=True
    else:
        if target.exists():
            failure=OUT/'repair/pack_attempt01'/target.name
            failure.parent.mkdir(parents=True,exist_ok=True)
            assert target.resolve().is_relative_to(OUT.resolve())
            assert failure.resolve().is_relative_to((OUT/'repair').resolve())
            assert not failure.exists()
            target.replace(failure)
        assert not index.exists()
        with target.open('xb',buffering=8*1024*1024) as stream:
            with zipfile.ZipFile(ForwardZipSink(stream),'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                for relative,raw in bounded_member_reads(paths):
                    z.writestr(relative,raw)
                    members.append(dict(path=relative,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
        with gzip.open(index,'wt',encoding='utf-8') as stream:
            json.dump(members,stream,separators=(',',':'))
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
    else:pieces=[dict(path=target.relative_to(ROOT).as_posix(),bytes=target.stat().st_size,SHA256=sha(target))]
    return dict(name=name+'.zip',SHA256=sha(target),compressed_bytes=target.stat().st_size,
        uncompressed_bytes=sum(m['bytes'] for m in members),file_count=len(members),pieces=pieces,
        member_index=dict(path=index.relative_to(ROOT).as_posix(),bytes=index.stat().st_size,SHA256=sha(index)),
        existing_completed_carrier_verified_and_reused=reused)

def idle():
    assert not budget()['unclosed']
    assert read(OUT/'reports/summary.json')['completed']==120
    assert read(OUT/'candidate_decision.json')['study_complete']

def source_capsule():
    idle();candidate=read(OUT/'candidate_manifest.json');matrix=read(OUT/'matrix_frozen.json')
    # The one-shot source capsule must contain the actually promoted and CLI-
    # checked current entry, rather than a still-historical config pointer.
    entry=read(OUT/'entry_check.json');promotion=read(OUT/'entry_promotion.json')
    assert entry['status']=='PASS_BOUNDED_ZERO_NATIVE_ENTRY_CHECK' and entry['round']==137
    assert entry['all_default_GI_launches']==28 and len(entry['all_S2_launches'])==28
    assert entry['new_Optimize']==entry['vendor_DLL_loads']==entry['formal_performance_samples_added']==0
    for key,name in [('entry_script_SHA','scripts/paper_s2.py'),('verifier_script_SHA','scripts/verify_paper_s2.py'),
        ('entry_helper_SHA','scripts/round137_entry.py'),('config_SHA','config/gi_tbc_round137.json'),
        ('legacy_config_SHA','config/paper_s2.json')]:assert entry[key]==sha(ROOT/name)
    assert entry['matrix_SHA']==sha(OUT/'matrix_frozen.json') and entry['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    assert entry['promotion_receipt_SHA']==sha(OUT/'entry_promotion.json')
    assert promotion['config_SHA']==entry['config_SHA'] and promotion['paper_entry_after_SHA']==entry['entry_script_SHA']
    assert promotion['verifier_after_SHA']==entry['verifier_script_SHA']
    helpers=dict(matrix['helpers'])
    for name,digest in helpers.items():assert sha(ROOT/name)==digest,name
    files=dict(candidate['source_hashes']);files.update(helpers)
    extras=['CMakeLists.txt','.gitattributes','config/paper_s2.json','config/gi_tbc_round137.json',
        'scripts/paper_s2.py','scripts/verify_paper_s2.py','scripts/round137_entry.py','docs/current_mainline.md','docs/paper_s2_release.md','docs/paper_review.md','docs/unified_exact_research_index.md']
    extras += [r['path'] for r in read(OUT/'infra/import_dependencies.json')['dependencies']]
    extras += ['results/unified_exact_round94/preregistration.json']
    for name in extras:files[name]=sha(ROOT/name)
    target=OUT/'artifacts/current_source_bytes.zip';target.parent.mkdir(exist_ok=True)
    assert not target.exists()
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,digest in sorted(files.items()):
            raw=(ROOT/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
            scan(raw,name);z.writestr(name,raw)
    write(OUT/'source_publication.json',dict(UTC=utc(),schema='round137-exact-current-source-v1',
        source_bundle=dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,members=files),
        execution_helpers=sorted(helpers),required_configuration_files=sorted(set(extras)),
        production_source_commit=candidate['source_commit'],
        current_entry_verification=dict(receipt='results/unified_exact_round137/entry_check.json',
            receipt_SHA=sha(OUT/'entry_check.json'),promotion='results/unified_exact_round137/entry_promotion.json',
            promotion_SHA=sha(OUT/'entry_promotion.json'),config_SHA=entry['config_SHA'],
            entry_script_SHA=entry['entry_script_SHA'],verifier_script_SHA=entry['verifier_script_SHA'],
            entry_helper_SHA=entry['entry_helper_SHA'],actual_default_CLI_vectors=28,new_Optimize=0,vendor_DLL_loads=0),
        no_native_assets_credentials_fonts_or_foreign_full_text=True,Optimize=0,compile=0))
    print(json.dumps(dict(source_files=len(files),helpers=len(helpers),capsule_bytes=target.stat().st_size)))

def pack():
    idle();assert not (OUT/'raw_archive_manifest.json').exists();records=[];inputs={};progress=[]
    for group in read(OUT/'matrix_frozen.json')['groups']:
        folder=OUT/group['group'];d=Path(group['launch']['destination'])
        assert (d/'verification_closeout.json').exists()
        records.append(archive(f'campaign_{group["position"]:03}',[p for p in folder.rglob('*') if p.is_file()]))
        p=group['launch']['panel'];inputs[p['input_path']]=ROOT/p['input_path']
        result=read(d/'result.json')
        if result.get('gurobi_progress_path'):progress.append(Path(result['gurobi_progress_path']))
    if progress:records.append(archive('current_native_progress',progress))
    records.append(archive('explicit_inputs',list(inputs.values())))
    records.append(archive('qualification_failures_costs',[p for name in ['qualification','fees','cost_segments','infra','repair']
        for p in (OUT/name).rglob('*') if p.is_file() and p.suffix.lower() not in FORBIDDEN]))
    write(OUT/'raw_archive_manifest.json',dict(schema='round137-finite-current-carriers-v1',UTC=utc(),archives=records,
        entered_positions=list(range(1,121)),registered_positions=120,all_entered_adverse_open_and_failures_retained=True,
        explicit_input_members=sorted(inputs),raw_remains_authoritative_in_place=True,historical_carriers_rewritten=0))
    print(json.dumps(dict(archives=len(records),compressed_bytes=sum(r['compressed_bytes'] for r in records))))

def manifest():
    idle();raw=read(OUT/'raw_archive_manifest.json');files={}
    publication=read(OUT/'source_publication.json');entry=publication['current_entry_verification']
    assert entry['receipt_SHA']==sha(ROOT/entry['receipt']) and entry['promotion_SHA']==sha(ROOT/entry['promotion'])
    bundle=publication['source_bundle'];assert sha(ROOT/bundle['path'])==bundle['SHA256']
    for name in ['scripts/paper_s2.py','scripts/verify_paper_s2.py','scripts/round137_entry.py',
        'config/paper_s2.json','config/gi_tbc_round137.json','docs/current_mainline.md','docs/paper_s2_release.md','docs/paper_review.md','docs/unified_exact_research_index.md']:
        assert bundle['members'][name]==sha(ROOT/name),('entry/docs changed after exact source capsule',name)
    excluded={'RESUME.md','export_manifest.json','public_restore_receipt.json','remote_readback.json',
        'completion_audit.json','resource_accounting.json','ordinary_operations.json'}
    for p in OUT.rglob('*'):
        if not p.is_file() or p.name in excluded:continue
        rel=p.relative_to(OUT)
        if rel.parts[0] in {'campaign','fees','cost_segments','infra','qualification','repair'}:continue
        if p.suffix.lower() in FORBIDDEN or '__pycache__' in p.parts:continue
        if rel.parts[0]=='artifacts' and p.name!='current_source_bytes.zip':continue
        name=p.relative_to(ROOT).as_posix();scan(p.read_bytes(),name)
        files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=None,source_path=name)
    for record in raw['archives']:
        for part in [*record['pieces'],record['member_index']]:
            files[part['path']]=dict(bytes=part['bytes'],SHA256=part['SHA256'],source_commit=None,source_path=part['path'])
    for p in (ROOT/'scripts').glob('round137*'):
        if p.suffix.lower() not in {'.py','.cpp'}:continue
        name=p.relative_to(ROOT).as_posix();scan(p.read_bytes(),name)
        files[name]=dict(bytes=p.stat().st_size,SHA256=sha(p),source_commit=None,source_path=name)
    name='scripts/round133_portable_check.py';p=ROOT/name;blob=git('show',BASE+':'+name)
    assert hashlib.sha256(blob).hexdigest()==sha(p)
    files[name]=dict(bytes=len(blob),SHA256=sha(p),source_commit=BASE,source_path=name)
    write(OUT/'export_manifest.json',dict(schema='round137-current-only-fixed-commit-recovery-v1',UTC=utc(),files=files,
        archives=raw['archives'],checker='scripts/round137_portable_check.py',formal_positions=120,
        recovery_scope='All120 current positions, exact current source/helpers,16 physical inputs, saved structural checks; no historical raw campaigns',
        fixed_dependency_Git_blob_bytes_verified=True,no_Optimize_compilation_or_vendor_DLL_loads=True))
    print(json.dumps(dict(files=len(files),archives=len(raw['archives']))))

def restore_script():
    code=(ROOT/'scripts/round135_public_restore.py').read_text(encoding='utf-8-sig')
    code=code.replace('round135','round137').replace('Round135','Round137')
    path=ROOT/'scripts/round137_public_restore.py'
    if path.exists():assert path.read_text(encoding='utf-8')==code
    else:path.write_text(code,encoding='utf-8',newline='\n')
    print('Inherited bounded public recovery driver prepared; not executed')

if __name__=='__main__':
    dict(source=source_capsule,pack=pack,manifest=manifest,**{'restore-script':restore_script})[sys.argv[1]]()
