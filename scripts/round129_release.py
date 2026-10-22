"""Current-round lossless carriers and finite publication closure; no solver."""
from round129_common import *
from round127_release import scan,idle,script_closure
import zipfile,gzip,ast

def pack():
    idle();assert not (OUT/'raw_archive_manifest.json').exists(),'preserve the completed carrier'
    assert all((OUT/g['name']/'reconstructed.json').exists() for g in read(OUT/'experiment_manifest.json')['groups'])
    target=OUT/'artifacts';target.mkdir(exist_ok=True)
    temp=TEMP/'archives';temp.mkdir(parents=True,exist_ok=False)
    plans=[(f'formal_group{g["number"]:02d}',[p for p in (OUT/g['name']).rglob('*') if p.is_file()]) for g in read(OUT/'experiment_manifest.json')['groups']]
    support=[p for p in (OUT/'qualification').rglob('*') if p.is_file()]
    support.extend(p for folder in (OUT/'fees').iterdir() if folder.is_dir() and (folder/'receipt.json').exists() for p in folder.rglob('*') if p.is_file())
    plans.append(('qualification_closed_fees',support))
    raw=sum(p.stat().st_size for _,files in plans for p in files);free=shutil.disk_usage(WORK).free
    upper=raw+sum(len(files) for _,files in plans)*2048+1024**3
    required=raw+6*upper+2*1024**3
    write(OUT/'review/packing_space_check.json',dict(UTC=utc(),status='PASS' if free>=required else 'INSUFFICIENT_SPACE',
        free_bytes=free,logical_current_raw_bytes=raw,conservative_additional_peak_bytes=required,no_measured_reclamation_claim=True))
    assert free>=required
    archives=[];scanned=0
    for label,files in plans:
        complete=temp/(label+'.zip');members=[]
        with zipfile.ZipFile(complete,'x',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for p in sorted(set(files)):
                scanned+=scan(p);member=p.relative_to(ROOT).as_posix()
                members.append(dict(path=member,bytes=p.stat().st_size,SHA256=sha(p)));z.write(p,member)
        decoded=json.dumps(members,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        index=OUT/'evidence'/(label+'.members.json.gz');index.parent.mkdir(exist_ok=True)
        index.write_bytes(gzip.compress(decoded,mtime=0))
        pieces=[]
        with complete.open('rb') as f:
            n=1
            while data:=f.read(48*1024**2):
                filename=complete.name if complete.stat().st_size<=48*1024**2 else complete.name+f'.part{n:02d}'
                p=target/filename;assert not p.exists();p.write_bytes(data)
                pieces.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=len(data),SHA256=sha(p)));n+=1
        archives.append(dict(name=complete.name,SHA256=sha(complete),compressed_bytes=complete.stat().st_size,
            uncompressed_bytes=sum(m['bytes'] for m in members),file_count=len(members),pieces=pieces,
            member_index=dict(format='gzip-json-utf8-list-v1',path=index.relative_to(ROOT).as_posix(),SHA256=sha(index),bytes=index.stat().st_size,
                decoded_SHA256=hashlib.sha256(decoded).hexdigest(),decoded_bytes=len(decoded),members=len(members)),
            temporary_complete_archive=str(complete)))
    write(OUT/'raw_archive_manifest.json',dict(schema='round129-finite-carriers-v1',archives=archives,
        raw_remains_authoritative_in_place=True,no_PE_DLL_license_fonts_historical_campaigns=True,live_pack_fee_and_future_receipts_excluded=True))
    write(OUT/'review/publication_scan.json',dict(status='PASS',actual_precompression_bytes_scanned=scanned,
        actual_archives=len(archives),scope='Every actual current carrier member before compression, with inherited credential and forbidden-extension scan'))
    print(json.dumps(dict(archives=len(archives),compressed_bytes=sum(a['compressed_bytes'] for a in archives),raw_bytes=raw,scanned_bytes=scanned)))

def manifest():
    idle();assert (OUT/'raw_archive_manifest.json').exists()
    files={p for p in OUT.iterdir() if p.is_file() and p.name!='export_manifest.json' and p.suffix!='.log'}
    files.update(p for folder in ['review','tables','evidence','inputs'] for p in (OUT/folder).rglob('*') if p.is_file())
    files.update(ROOT/p for p in read(OUT/'E2_identity.json')['source_bindings'])
    files.update(ROOT/p['input_path'] for p in read(OUT/'input_manifest.json')['roles'])
    for p in read(OUT/'source_recipe.json')['source_asset_bindings']:files.add(ROOT/p)
    for p in ['reference/round106_confirmation/S12.txt','reference/round98_confirmation/C2.txt']:
        files.add(ROOT/p)
    for a in read(OUT/'raw_archive_manifest.json')['archives']:
        files.update(ROOT/p['path'] for p in a['pieces'])
    starts=[p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round129_*.py')]
    files.update(ROOT/p for p in script_closure(starts))
    files.add(ROOT/'scripts/round128_export.cpp')
    files.add(ROOT/'scripts/round129_cleanup.ps1')
    files.add(ROOT/'results/unified_exact_round94/preregistration.json')
    for n in ['goal.md','final_report.md','arms.csv','pairs.csv','method_matrix.md','md_root_contract.md','E2_frozen.json']:
        files.add(ROOT/'results/unified_exact_round128'/n)
    for n in ['method_matrix.md','E1_frozen.json']:
        files.add(ROOT/'results/unified_exact_round127'/n)
    entries=[]
    for p in sorted(files):
        scan(p);entries.append(dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=p.stat().st_size,
            serialization='exact bytes; inherited Git text transport may require hash-checked LF/CRLF materialization'))
    write(OUT/'export_manifest.json',dict(schema='round129-current-only-export-v1',base_commit=BASE,
        files=entries,file_count=len(entries),archive_manifest='results/unified_exact_round129/raw_archive_manifest.json',
        no_native_software_licenses_fonts_or_external_full_papers=True,one_empty_root_recovery_only=True,
        no_historical_raw_carrier_recovered=True))
    print(json.dumps(dict(export_files=len(entries),bytes=sum(e['bytes'] for e in entries))))

if __name__=='__main__':{'pack':pack,'manifest':manifest}[sys.argv[1]]()
