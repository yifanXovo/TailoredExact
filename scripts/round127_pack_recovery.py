"""Recover finite carrier metadata after a source-option scanner false positive.

Reuses the four completed ZIPs and their public pieces byte-for-byte. The failed
support ZIP is retained and copied to a fresh attempt before appending only its
missing members. All completed carrier plaintext is streamed for SHA/CRC and a
fresh credential scan. No source, experiment, producer seal or raw is rewritten.
"""
from round127_common import *
from round127_release import BAD,FORBIDDEN,idle,scan
from pathlib import PurePosixPath
import math,re,zipfile

FROZEN={
 'training':(89679510,'c537cc98606617309d108b360560d25fba0be3ca93a28ec9ac807c1086688a33'),
 'main':(69591470,'95311472996025d016a3e428575a6395d80a264c121ec5e283932f24be8bd7ec'),
 'tiny':(9198091,'3d6313400f7d81a3962d699c0ea0208436f8851e9ab1c446c4c174cf1e4ebb87'),
 'core':(98698419,'4a282cf616e181743c7ae8d73990b2b36f16b68e37dca0bd8fe43351150ff3a7')}
PARTIAL_SHA='49e493223aa48c15eca0e72b8895269d8fa29013a9559f87acdb7bd408689e66'
PREFIX='results/unified_exact_round127/'

def recover():
    idle();tick=time.perf_counter();archive_dir=TEMP/'archives';public=OUT/'artifacts'
    assert not (OUT/'raw_archive_manifest.json').exists()
    original_fee=read(OUT/'fees/finite_carrier_pack_01/receipt.json')
    assert original_fee['exit_code']==1 and original_fee['exit_observed']
    # An independent positive/negative token-boundary check, without printing any
    # credential-shaped material. The matching source option is public CLI text.
    option=b'--route-mask-support-duration-pruning'
    fake=b'sk-'+b'Z'*32
    scanner=re.compile(BAD[4])
    assert not scanner.search(option)
    assert all(scanner.search(prefix+fake) for prefix in [b'',b'"',b"'",b' ',b'=',b'\n'])
    source=OUT/'source_E0/src/main.cpp';source_bytes=source.read_bytes()
    assert sha(source)=='38aa9744ded25d494748a6dbb371db3d266b42081f173ef6f5bb723e1f758b5d'
    legacy=list(re.finditer(rb'sk-[A-Za-z0-9_-]{24,}',source_bytes))
    assert [(m.start(),m.end()-m.start()) for m in legacy]==[(7034,27),(64771,27)]
    assert all(source_bytes[m.start()-15:m.end()].endswith(option) for m in legacy)
    assert all(hashlib.sha256(m.group()).hexdigest()=='b2eeb1715c36296231973c7a8bb40b418b440d96a790badeec98c5c18fecf612' for m in legacy)
    finding=dict(status='CONFIRMED_PUBLIC_CLI_SUBSTRING_FALSE_POSITIVE',UTC=utc(),
        source=source.relative_to(ROOT).as_posix(),source_SHA256=sha(source),
        public_option=option.decode(),legacy_match_offsets=[m.start() for m in legacy],
        legacy_match_SHA256='b2eeb1715c36296231973c7a8bb40b418b440d96a790badeec98c5c18fecf612',
        scanner_correction='Negative lookbehind excludes a match embedded in an ASCII identifier or CLI option; independently delimited sk-prefixed tokens remain detected.',
        synthetic_delimiter_positive_checks=6,public_option_negative_checks=1,
        old_attempt='fees/finite_carrier_pack_01',old_fee=original_fee,
        no_source_or_scientific_evidence_changed=True)
    write(OUT/'review/packaging_scanner_finding.json',finding)
    groups=[];streamed_bytes=0;patterns=[re.compile(p) for p in BAD]
    def inventory(path,allowed_stages):
        nonlocal streamed_bytes
        members=[]
        with zipfile.ZipFile(path) as z:
            infos=z.infolist();assert len(infos)==len({i.filename for i in infos})
            for info in infos:
                rel=PurePosixPath(info.filename)
                assert not rel.is_absolute() and '..' not in rel.parts and all(':' not in p and '\\' not in p for p in rel.parts)
                assert info.filename.startswith(PREFIX) and rel.parts[2] in allowed_stages
                assert not info.is_dir() and Path(info.filename).suffix.lower() not in FORBIDDEN
                h=hashlib.sha256();tail=b'';size=0
                with z.open(info) as f:
                    while block:=f.read(1024*1024):
                        for pattern in patterns:assert not pattern.search(tail+block),('credential marker',info.filename)
                        h.update(block);tail=block[-256:];size+=len(block)
                assert size==info.file_size
                streamed_bytes+=size;members.append(dict(path=info.filename,bytes=size,SHA256=h.hexdigest()))
        return members
    def pieces(path,create):
        limit=48*1024**2;result=[]
        expected=[path.name] if path.stat().st_size<=limit else [path.name+f'.part{i:02d}' for i in range(1,math.ceil(path.stat().st_size/limit)+1)]
        if not create:assert sorted(p.name for p in public.glob(path.name+'*'))==sorted(expected)
        with path.open('rb') as stream:
            for name in expected:
                data=stream.read(limit);dst=public/name
                if create:assert not dst.exists();dst.write_bytes(data)
                assert dst.stat().st_size==len(data) and sha(dst)==hashlib.sha256(data).hexdigest()
                result.append(dict(path=dst.relative_to(ROOT).as_posix(),bytes=len(data),SHA256=sha(dst)))
            assert not stream.read(1)
        return result
    def group(path,members,create):
        return dict(name=path.name,SHA256=sha(path),compressed_bytes=path.stat().st_size,
            uncompressed_bytes=sum(m['bytes'] for m in members),file_count=len(members),
            pieces=pieces(path,create),members=members,temporary_complete_archive=str(path))
    for stage,(size,digest) in FROZEN.items():
        p=archive_dir/(stage+'.zip');assert p.stat().st_size==size and sha(p)==digest
        members=inventory(p,{stage});groups.append(group(p,members,False))
        print(json.dumps(dict(stage=stage,members=len(members),streamed_bytes=sum(m['bytes'] for m in members),ZIP_bytes_unchanged=True)),flush=True)
    partial=archive_dir/'qualification_closed_fees_original_sources.zip'
    assert partial.stat().st_size==24933358 and sha(partial)==PARTIAL_SHA
    recovery_dir=archive_dir/'recovery01';recovery_dir.mkdir(exist_ok=False)
    complete=recovery_dir/partial.name;shutil.copyfile(partial,complete)
    support=[p for p in (OUT/'qualification').rglob('*') if p.is_file()]
    support.extend(p for folder in (OUT/'fees').iterdir() if folder.is_dir() and (folder/'receipt.json').exists() for p in folder.rglob('*') if p.is_file())
    support.extend(p for p in (OUT/'source_E0').rglob('*') if p.is_file())
    expected={p.relative_to(ROOT).as_posix():p for p in support};assert len(expected)==len(support)
    with zipfile.ZipFile(complete,'a',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        existing=set(z.namelist());assert len(existing)==len(z.infolist()) and existing<=expected.keys()
        added=sorted(expected.keys()-existing)
        for name in added:scan(expected[name]);z.write(expected[name],name)
    support_members=inventory(complete,{'qualification','fees','source_E0'})
    assert {m['path'] for m in support_members}==set(expected)
    # Validate newly appended source/closed-failure records against authoritative
    # files. Existing bytes retain their original precompression scan and CRC.
    by_name={m['path']:m for m in support_members}
    assert all(by_name[name]['SHA256']==sha(expected[name]) for name in added)
    assert sha(partial)==PARTIAL_SHA
    groups.append(group(complete,support_members,True))
    index=[]
    for stage in FROZEN:
        for path in sorted((OUT/stage).glob('*/identity.json')):
            identity=read(path)
            for launch in identity['launches']:
                d=Path(launch['destination']);index.append(dict(stage=stage,id=launch['id'],method=launch['method'],seed=launch['seed'],repeat=launch['repeat'],binary_layer=launch['binary_layer'],raw_root=d.relative_to(ROOT).as_posix(),identity_SHA=sha(path),producer_receipt_SHA=sha(d/'producer_receipt.json'),result_SHA=sha(d/'result.json'),model_journal_SHA=sha(d/'observations.json')))
    assert len(index)==90 and sum(a['stage']=='training' for a in index)==36 and sum(a['stage']!='training' for a in index)==54
    assert len({a['raw_root'] for a in index})==90
    write(OUT/'raw_archive_manifest.json',dict(schema='round127-finite-carriers-v1',archives=groups,
        raw_remains_in_place=True,no_PE_DLL_license_or_historical_carrier=True,
        live_pack_fee_and_future_receipts_excluded=True,seconds=time.perf_counter()-tick,
        recovery_of_failed_pack='review/packaging_scanner_finding.json'))
    write(OUT/'evidence/arm_index.json',dict(arms=index,formal_arms=sum(a['stage']!='training' for a in index),training_arms=sum(a['stage']=='training' for a in index)))
    report=dict(status='PASS',UTC=utc(),actual_carrier_plaintext_bytes_scanned=streamed_bytes,
        forbidden_extensions=sorted(FORBIDDEN),archives=len(groups),members=sum(a['file_count'] for a in groups),
        no_native_software_or_credentials=True,full_SHA256_and_ZIP_CRC_streamed=True,
        scope='Original four completed stage ZIPs had passed precompression scan and are preserved byte-for-byte; every final carrier member is additionally decompressed, credential-scanned and SHA256 indexed with the corrected token boundary. Only missing support files were appended to a fresh copy; failed partial retained.',
        failed_partial=dict(path=str(partial),bytes=partial.stat().st_size,SHA256=PARTIAL_SHA),
        appended_support_paths=added,original_stage_ZIP_SHA256={k:v[1] for k,v in FROZEN.items()},
        original_failed_fee=original_fee,native_solver_starts=0,Optimize=0)
    write(OUT/'review/publication_scan.json',report)
    write(OUT/'review/packaging_recovery_receipt.json',dict(**report,executed_source_SHA256=sha(Path(__file__)),seconds=time.perf_counter()-tick))
    print(json.dumps(dict(status='PASS',archives=len(groups),members=report['members'],streamed_bytes=streamed_bytes,appended_support_files=len(added))),flush=True)

if __name__=='__main__':recover()
