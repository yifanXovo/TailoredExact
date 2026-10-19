"""Finite raw carriers and the single public science-A file manifest."""
from round126_common import *
import csv,re,zipfile

BAD=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{30,}',
     rb'github_pat_[A-Za-z0-9_]{35,}',rb'(?i)(?:cookie|authorization)\s*:\s*(?:bearer\s+)?[A-Za-z0-9+/=_-]{24,}']
FORBIDDEN={'.exe','.dll','.lic','.key','.pem','.pfx','.p12','.ttf','.otf','.woff','.woff2','.html'}

def scan_file(path):
    assert path.suffix.lower() not in FORBIDDEN,('not a publishable research artifact',str(path))
    if path.suffix.lower()=='.pdf':assert path.name=='manuscript.pdf';return path.stat().st_size
    if path.suffix.lower() in ['.zip','.part01','.part02','.part03','.part04']:return 0
    # Scan actual source/raw bytes before compression. Keep overlap for split markers.
    previous=b'';count=0
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):
            value=previous+chunk;count+=len(chunk)
            for marker in BAD:assert not re.search(marker,value),('credential marker',str(path))
            previous=value[-256:]
    return count

def pack():
    from round100_idle import ensure_idle
    workspace();ensure_idle();identity();assert not budget()['unclosed'] or len(budget()['unclosed'])==1
    assert all((OUT/f'fees/formal{n:02d}/receipt.json').is_file() for n in range(1,7))
    target=OUT/'artifacts';target.mkdir(exist_ok=True);temp=TEMP/'archives';temp.mkdir(exist_ok=True)
    groups=[];arm_index=[];scanned=0;tick=time.perf_counter()
    def create(name,files):
        nonlocal scanned
        archive=temp/(name+'.zip');assert not archive.exists()
        raw_bytes=0
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for p in sorted(files):
                assert p.resolve().is_relative_to(ROOT.resolve()) and not p.is_symlink() and not p.is_junction()
                scanned+=scan_file(p);raw_bytes+=p.stat().st_size;z.write(p,p.relative_to(ROOT).as_posix())
        pieces=[];limit=48*1024**2
        if archive.stat().st_size<=limit:
            dst=target/archive.name;assert not dst.exists();shutil.copyfile(archive,dst)
            pieces=[dict(path=dst.relative_to(ROOT).as_posix(),bytes=dst.stat().st_size,SHA256=sha(dst))]
        else:
            with archive.open('rb') as f:
                n=1
                while data:=f.read(limit):
                    dst=target/(archive.name+f'.part{n:02d}');assert not dst.exists();dst.write_bytes(data)
                    pieces.append(dict(path=dst.relative_to(ROOT).as_posix(),bytes=len(data),SHA256=sha(dst)));n+=1
        return dict(name=archive.name,SHA256=sha(archive),compressed_bytes=archive.stat().st_size,uncompressed_bytes=raw_bytes,
            file_count=len(files),pieces=pieces,temporary_complete_archive=str(archive))
    for n in range(1,7):
        camp=OUT/f'campaign/group{n:02d}';files=[p for p in camp.rglob('*') if p.is_file()]
        files.extend(p for p in (OUT/f'reconstruction/group{n:02d}').rglob('*') if p.is_file())
        groups.append(create(f'formal_group{n:02d}',files))
        i=read(camp/'identity.json')
        for l in i['launches']:
            d=Path(l['destination']);names=['result.json','producer_seal.json','producer_receipt.json','verification_closeout.json','arm_total_receipt.json','independent_evidence.json','native_claims.json','claim_rejections.json','audit.json']
            models=[]
            for e in read(d/'observations.json'):
                c=e['payload']
                if c['kind']=='call':models.append({k:c.get(k) for k in ['call','model_path','model_sha256','full_original','lower_g','upper_g','cutoff','settings']})
            arm_index.append(dict(id=l['id'],arm=l['arm'],input_SHA=l['panel']['input_sha256'],raw_root=d.relative_to(ROOT).as_posix(),
                files={name:dict(path=(d/name).relative_to(ROOT).as_posix(),SHA256=sha(d/name)) for name in names},
                native_models=models,Start_and_fleet_sources='Complete result/own physical replay, native request/Start ledgers and journal payloads inside the same arm carrier.'))
    support=[p for p in (OUT/'qualification').rglob('*') if p.is_file()]
    for folder in sorted((OUT/'fees').iterdir()):
        if folder.is_dir() and (folder/'receipt.json').is_file():support.extend(p for p in folder.rglob('*') if p.is_file())
    groups.append(create('qualification_and_closed_fees',support))
    write(OUT/'raw_archive_manifest.json',dict(archives=groups,one_authoritative_raw=str(OUT/'campaign'),
        raw_remains_in_place=True,PE_or_DLL_copied=False,arm_index='evidence/arm_index.json',
        future_receipts_and_this_live_pack_fee_excluded=True,seconds=time.perf_counter()-tick))
    write(OUT/'evidence/arm_index.json',dict(arms=arm_index,source_commit=SOURCE,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA))
    # Also inspect the actual new document/CSV/JSON files which are published outside ZIPs.
    for p in OUT.rglob('*'):
        if p.is_file() and 'campaign' not in p.relative_to(OUT).parts and 'qualification' not in p.relative_to(OUT).parts and 'artifacts' not in p.relative_to(OUT).parts:
            scanned+=scan_file(p)
    write(OUT/'review/publication_scan.json',dict(status='PASS',actual_raw_and_text_bytes_scanned=scanned,
        forbidden_artifact_extensions=sorted(FORBIDDEN),no_credentials_or_full_webpage_scripts_headers_license_or_font_files_added=True,
        own_manuscript_PDF_only=True,scope='R126 actual raw bytes before compression plus actual new document/table metadata; historical repository content is not re-cleared.',
        archive_count=len(groups),seconds=time.perf_counter()-tick))
    print(json.dumps(dict(archives=len(groups),compressed_bytes=sum(g['compressed_bytes'] for g in groups),scanned_bytes=scanned)))

def manifest():
    # The manifest binds science content, finite restore dependencies and actual raw carriers.
    # It deliberately does not claim to prove future B receipts or mutable closeout bookkeeping.
    names=set()
    for p in OUT.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(OUT)
        if rel.parts[0] in ['campaign','qualification','fees','review','reconstruction']:continue
        if p.name in ['export_manifest.json','final_report.md','RESUME.md','resource_accounting.json','pdf_export.json']:continue
        names.add(p.relative_to(ROOT).as_posix())
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('*round126*.py'))
    names.update(['scripts/round122_common.py','scripts/round122_data.py','scripts/round120_common.py','scripts/round118_data.py',
        'scripts/round109_data.py','scripts/generate_citibike443_regional_v1.py',
        'results/data_generation_citibike_round57/source_station_table.csv','results/unified_exact_round116/source/snapshot.json',
        'results/unified_exact_round116/source/source_station_table.csv','results/unified_exact_round116/source/row_decisions.json',
        'results/unified_exact_round116/source/requests/station_information/01.response','results/unified_exact_round116/projection_contract.json'])
    # Complete group reconstructions travel inside the same finite raw carriers.
    files=[]
    for n in sorted(names):
        p=ROOT/n;assert p.is_file(),n
        scan_file(p)
        files.append(dict(path=n,bytes=p.stat().st_size,SHA256=sha(p),
            serialization='exact bytes; if Git text conversion intervenes, only exact-SHA-matching LF/CRLF materialization is allowed' if p.suffix in ['.py','.md','.json','.txt','.csv','.bib'] else 'exact bytes'))
    write(OUT/'export_manifest.json',dict(schema='round126-single-science-A-public-manifest-v1',files=files,
        source_recipe_SHA=sha(OUT/'source_recipe.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        raw_manifest_SHA=sha(OUT/'raw_archive_manifest.json'),no_native_software_or_old_campaign_restore=True,
        restore_checks='Six original-chain input regenerations, all twelve seals/clocks/endpoints, six pure pairs, optional document compile/text comparison',
        future_B_receipts_excluded=True,manifest_does_not_hash_itself=True))
    review_files=[p for p in (OUT/'review').rglob('*') if p.is_file()]
    for p in review_files:scan_file(p)
    write(OUT/'review/content_A_scan.json',dict(status='PASS',manifest_files_inspected=len(files),review_files_inspected=len(review_files),
        actual_raw_scan='review/publication_scan.json; every archive member was scanned before compression',
        scope='Actual finite public dependency/doc/script/carrier list and actual review files; no generic historical clearance.'))
    print(json.dumps(dict(files=len(files),payload_bytes=sum(p['bytes'] for p in files))))

if __name__=='__main__':{'pack':pack,'manifest':manifest}[sys.argv[1]]()
