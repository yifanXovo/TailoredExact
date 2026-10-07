"""Exact-byte public carrier, executed only after all native work is idle."""
from round107_common import *
import gzip,hashlib,io,tarfile

OMIT={'final_report.md','RESUME.md','reproduce.md','delivery_review.md','delivery_review.json'}
BINARY={'.exe','.dll','.lic','.key','.pem','.pyc','.pdb','.obj','.o'}

def selected():
    files=set()
    def add(p):
        p=Path(p)
        assert p.is_file() and p.is_relative_to(ROOT) and p.suffix.lower() not in BINARY
        files.add(p)
    # Preserve all failed calls, original receipts, superseded readers and
    # qualification snapshots. Restoration outcomes are separate public files
    # written only after real execution, avoiding circular evidence claims.
    for p in OUT.rglob('*'):
        if not p.is_file() or p.suffix.lower() in BINARY:continue
        relative=p.relative_to(OUT)
        if relative.parts[0] in ['compact_evidence','restoration']:continue
        if relative.parts[0]=='engineering' and len(relative.parts)>1 and not (OUT/'engineering'/relative.parts[1]/'receipt.json').exists():continue
        if p.name in OMIT:continue
        add(p)
    identity=read(OUT/'qualification/identity.json')
    for relative in identity['source_bindings']:add(ROOT/relative)
    for p in (ROOT/'tests').glob('round10[567]_tests.cpp'):add(p)
    for p in (ROOT/'tests').glob('round107_*_tests.cpp'):add(p)
    for p in (ROOT/'scripts').glob('round107*'):
        if p.is_file() and p.suffix in ['.py','.ps1']:add(p)
    for camp in OUT.iterdir():
        if not (camp/'identity.json').exists():continue
        q=read(camp/'identity.json')
        if 'launches' not in q:continue
        for a in q['launches']:add(ROOT/a['panel']['input_path'])
        for name in q['helpers']:add(ROOT/'scripts'/name)
    for role in read(OUT/'confirmation_protocol.json')['roles']:add(ROOT/role['input_path'])
    add(ROOT/'results/unified_exact_round94/preregistration.json')
    return sorted(files)

def pack():
    from round100_idle import ensure_idle
    ensure_idle();d=OUT/'compact_evidence';d.mkdir(exist_ok=False);files=selected();records=[]
    archive=d/'evidence.tar.gz'
    with archive.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as t:
        for p in files:
            data=p.read_bytes();name=p.relative_to(ROOT).as_posix();info=tarfile.TarInfo(name)
            info.size=len(data);info.mode=0o644;info.mtime=0;t.addfile(info,io.BytesIO(data))
            records.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    dep=ROOT/'results/unified_exact_round106/compact_evidence'
    parts=read(dep/'parts_manifest.json')
    write(d/'manifest.json',dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,files=records,
        reader_SHA=sha(ROOT/'scripts/round107_reader.py'),selection_source_SHA=sha(__file__),
        public_dependencies=[dict(commit='0350dbcc60d1c68e5c499d2e9880ecc1deaf031c',path='results/unified_exact_round106/compact_evidence',manifest_SHA=sha(dep/'manifest.json'),parts_manifest_SHA=sha(dep/'parts_manifest.json'),archive_SHA=parts['archive_sha256'],parts=parts['archive_parts']),
            dict(commit='8dc274eb34ee6d8a575f0b94b57ef04476efc0f1',path='results/unified_exact_round105/compact_evidence/evidence.tar.gz',archive_SHA='fd546a17045c8f0cb886338a865df4abad3e8bfa20718bb8d253762516f45125',exact_manifest_public_path='results/unified_exact_round106/r105_supplement/inherited_compact_manifest_bytes.json',exact_manifest_SHA='f1975056153d4dd8fd73d3713a649f0833a5914b831c554ed9192b288b7223cd')],
        all_raw_native_and_failed_records_retained=True,no_PE_DLL_license_or_credentials=True,
        delivery_boundary='Final prose and actual restoration/final independent review are separately committed after execution; not invented inside the frozen archive.',Optimize_calls=0,IIS_calls=0))
    print(json.dumps(dict(files=len(files),bytes=archive.stat().st_size,archive_SHA=sha(archive),Optimize_calls=0,IIS_calls=0)))

def split():
    d=OUT/'compact_evidence';q=read(d/'manifest.json');archive=d/'evidence.tar.gz';assert sha(archive)==q['archive_sha256']
    parts=[]
    with archive.open('rb') as f:
        n=1
        while data:=f.read(48*1024*1024):
            p=d/f'evidence.tar.gz.part{n:03d}'
            with p.open('xb') as output:output.write(data)
            parts.append(dict(path=p.name,bytes=len(data),sha256=sha(p)));n+=1
    write(d/'parts_manifest.json',dict(archive_sha256=q['archive_sha256'],archive_bytes=q['archive_bytes'],original_manifest_SHA=sha(d/'manifest.json'),archive_parts=parts,split_source_SHA=sha(__file__),public_carrier='Only sequential byte parts plus both manifests; local whole archive is not published.'))
    print(json.dumps(dict(parts=len(parts),archive_SHA=q['archive_sha256'],Optimize_calls=0,IIS_calls=0)))

if __name__=='__main__':
    assert sys.argv[1] in ['pack','split']
    {'pack':pack,'split':split}[sys.argv[1]]()
