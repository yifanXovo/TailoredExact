"""Exact-byte evidence selection/archive. Run only with all solver arms idle."""
from round106_common import *
import gzip,io,tarfile

def selected():
    files=set()
    def add(p):
        p=Path(p).resolve();assert p.is_file() and p.is_relative_to(ROOT)
        assert p.suffix.lower() not in ['.exe','.dll','.lic','.key','.pem','.pyc']
        files.add(p)
    # Never omit calls.csv, failure receipts or earlier qualification identities.
    # Delivery prose/restore outcomes remain ordinary committed public files;
    # omitting them avoids archive self-reference after actual fresh recovery.
    omit={'final_report.md','RESUME.md','reproduce.md','delivery_review.md','delivery_review.json'}
    for p in OUT.rglob('*'):
        if not p.is_file() or 'compact_evidence' in p.parts or p.name in omit:continue
        if 'restoration' in p.parts or 'inherited_restore01' in p.parts:continue
        if p.suffix.lower() in ['.exe','.dll','.lic','.key','.pem','.pyc']:continue
        if 'engineering' in p.parts:
            fee=p
            while fee.parent!=OUT/'engineering' and fee!=OUT:fee=fee.parent
            if fee==OUT or not (fee/'receipt.json').exists():continue
        add(p)
    identity=read(OUT/'qualification/identity.json')
    for relative in identity['source_bindings']:add(ROOT/relative)
    for relative in identity['tests_SHA']:add(ROOT/relative)
    for p in (ROOT/'scripts').glob('round106*.py'):add(p)
    for camp in OUT.iterdir():
        if not (camp/'identity.json').exists():continue
        q=read(camp/'identity.json')
        if 'launches' not in q:continue
        for a in q['launches']:add(ROOT/a['panel']['input_path'])
        for helper in q['helpers']:add(ROOT/'scripts'/helper)
    for r in read(OUT/'confirmation_protocol.json')['roles']:add(ROOT/r['input_path'])
    add(ROOT/'results/unified_exact_round94/preregistration.json')
    return sorted(files)

def pack():
    from round100_idle import ensure_idle
    ensure_idle();d=OUT/'compact_evidence';d.mkdir(exist_ok=False);files=selected();manifest=[]
    archive=d/'evidence.tar.gz'
    with archive.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz,tarfile.open(fileobj=gz,mode='w|') as t:
        for p in files:
            data=p.read_bytes();name=p.relative_to(ROOT).as_posix();info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.mode=0o644
            t.addfile(info,io.BytesIO(data));manifest.append(dict(path=name,bytes=len(data),sha256=sha(p)))
    old=ROOT/'results/unified_exact_round105/compact_evidence'
    write(d/'manifest.json',dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,files=manifest,
        selection_source_SHA=sha(__file__),reader_SHA=sha(ROOT/'scripts/round106_reader.py'),
        inherited_dependency=dict(archive='results/unified_exact_round105/compact_evidence/evidence.tar.gz',archive_SHA=sha(old/'evidence.tar.gz'),manifest_SHA=sha(old/'manifest.json'),base_commit='8dc274eb34ee6d8a575f0b94b57ef04476efc0f1'),
        all_raw_calls_and_failures_retained=True,no_solver_binaries_or_licenses=True,
        omitted='Delivery prose and later actual restoration/review receipts are separately committed public files, not evidence invented before recovery. No raw native ledger is omitted.',Optimize_calls=0,IIS_calls=0))
    print(json.dumps(dict(files=len(files),compressed_bytes=archive.stat().st_size,archive_SHA=sha(archive),Optimize_calls=0,IIS_calls=0)))

def split():
    # Preserve the exact archive and its original identity; publish small
    # sequential byte parts when the whole file exceeds Git's carrier limit.
    d=OUT/'compact_evidence';archive=d/'evidence.tar.gz';q=read(d/'manifest.json')
    assert not (d/'parts_manifest.json').exists() and sha(archive)==q['archive_sha256']
    size=48*1024*1024;parts=[]
    with archive.open('rb') as source:
        index=1
        while data:=source.read(size):
            p=d/f'evidence.tar.gz.part{index:03d}'
            if p.exists():assert p.read_bytes()==data
            else:
                with p.open('xb') as output:output.write(data)
            parts.append(dict(path=p.name,bytes=len(data),sha256=sha(p)));index+=1
    assert sum(p['bytes'] for p in parts)==q['archive_bytes']
    prior=OUT/'restoration/manifest_whole_archive01.json'
    if prior.exists():assert read(prior)==q
    else:write(prior,q)
    carrier=dict(archive_parts=parts,archive_sha256=q['archive_sha256'],archive_bytes=q['archive_bytes'],
        original_manifest_SHA=sha(d/'manifest.json'),carrier_split_source_SHA=sha(__file__),
        public_carrier='Only the listed sequential byte parts and this manifest are committed; reassembly exactly matches the unchanged archive SHA. The whole local archive is not committed.')
    write(d/'parts_manifest.json',carrier)
    print(json.dumps(dict(parts=len(parts),archive_SHA=q['archive_sha256'],bytes=q['archive_bytes'],Optimize_calls=0,IIS_calls=0)))
if __name__=='__main__':
    assert sys.argv[1] in ['pack','split'];{'pack':pack,'split':split}[sys.argv[1]]()
