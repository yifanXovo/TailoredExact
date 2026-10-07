"""Exact-byte non-overwriting restoration into an exclusive empty directory."""
from round106_common import *
import hashlib, tarfile

def carrier(package,destination):
    q=read(package/'manifest.json')
    index=package/'parts_manifest.json'
    if not index.exists():return package/'evidence.tar.gz'
    parts=read(index)
    assert parts['original_manifest_SHA']==sha(package/'manifest.json')
    assert parts['archive_sha256']==q['archive_sha256'] and parts['archive_bytes']==q['archive_bytes']
    # A listed public carrier always takes precedence over the retained local
    # whole archive. Recovery therefore needs only committed byte parts.
    d=destination/'archive_carrier';d.mkdir();p=d/'evidence.tar.gz'
    combined=hashlib.sha256();size=0
    with p.open('xb') as output:
        for index,part in enumerate(parts['archive_parts'],1):
            assert part['path']==f'evidence.tar.gz.part{index:03d}'
            source=package/part['path'];actual=hashlib.sha256();length=0
            with source.open('rb') as data:
                while chunk:=data.read(1024*1024):
                    actual.update(chunk);combined.update(chunk);output.write(chunk)
                    length+=len(chunk);size+=len(chunk)
            assert length==part['bytes'] and actual.hexdigest()==part['sha256']
    assert size==q['archive_bytes'] and combined.hexdigest()==q['archive_sha256']
    return p

def unpack(archive,manifest,destination):
    q=read(manifest);assert sha(archive)==q['archive_sha256']
    expected={r['path']:r for r in q['files']};seen=set()
    with tarfile.open(archive,'r:gz') as pack:
        for member in pack:
            assert member.isfile() and member.name in expected and member.name not in seen
            p=(destination/member.name).resolve();assert p.is_relative_to(destination)
            assert member.name=='CMakeLists.txt' or member.name.startswith(('results/','reference/','scripts/','src/','include/','tests/'))
            data=pack.extractfile(member).read();r=expected[member.name]
            assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
            if p.exists():assert p.is_file() and sha(p)==r['sha256'],('different bytes',p)
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            seen.add(member.name)
    assert seen==set(expected);return len(seen)

def inherited(destination):
    destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=False)
    old=ROOT/'results/unified_exact_round105/compact_evidence'
    total=unpack(old/'evidence.tar.gz',old/'manifest.json',destination)
    add_index(destination)
    supplement=read(OUT/'r105_supplement/manifest.json')
    for record in supplement['files']:
        source=ROOT/record['recovered_path'];assert sha(source)==record['sha256']
        p=destination/record['original_path'];assert not p.exists()
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(source.read_bytes())
    write(destination/'restore_receipt.json',dict(inherited_archive_sha256=sha(old/'evidence.tar.gz'),
        old_archive_files=total,recovered_raw_ledgers=len(supplement['files']),
        supplement_manifest_sha256=sha(OUT/'r105_supplement/manifest.json'),
        source_reader_sha256=sha(__file__),Optimize_calls=0,IIS_calls=0))
    print(json.dumps(dict(restored=total,supplemental_ledgers=len(supplement['files']),Optimize_calls=0,IIS_calls=0)))

def add_index(destination):
    destination=Path(destination).resolve()
    assert destination.is_dir()
    for relative in ['results/unified_exact_round105/compact_evidence/manifest.json',
                     'results/unified_exact_round106/r105_supplement/manifest.json']:
        p=destination/relative;data=(ROOT/relative).read_bytes()
        if p.exists():assert p.read_bytes()==data,('different index bytes',p)
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

def final(destination):
    destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=False)
    package=OUT/'compact_evidence';archive=carrier(package,destination)
    new_count=unpack(archive,package/'manifest.json',destination)
    old=ROOT/'results/unified_exact_round105/compact_evidence';legacy=destination/'inherited_r105';legacy.mkdir()
    published=OUT/'r105_supplement/inherited_compact_manifest_bytes.json'
    old_manifest=published if published.exists() else old/'manifest.json'
    dependency=read(package/'manifest.json')['inherited_dependency']
    assert dependency['archive_SHA']==sha(old/'evidence.tar.gz')
    assert dependency['manifest_SHA']==sha(old_manifest)
    index=destination/'results/unified_exact_round106/compact_evidence/manifest.json'
    index.parent.mkdir(parents=True,exist_ok=True);assert not index.exists()
    index.write_bytes((package/'manifest.json').read_bytes())
    if (package/'parts_manifest.json').exists():
        (index.parent/'parts_manifest.json').write_bytes((package/'parts_manifest.json').read_bytes())
    old_count=unpack(old/'evidence.tar.gz',old_manifest,legacy)
    # Keep exact inherited public source bytes separate from this round's source.
    # No collision/overwrite of the new production source or old manifest bytes.
    for relative in ['results/unified_exact_round105/compact_evidence/manifest.json',
                     'results/unified_exact_round106/r105_supplement/manifest.json']:
        source=(old_manifest if 'round105/compact' in relative else destination/relative)
        p=legacy/relative;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(source.read_bytes())
    supplement=read(destination/'results/unified_exact_round106/r105_supplement/manifest.json')
    for record in supplement['files']:
        source=destination/record['recovered_path'];assert sha(source)==record['sha256']
        p=legacy/record['original_path'];assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(source.read_bytes())
    write(destination/'restore_receipt.json',dict(current_files=new_count,inherited_files=old_count,
        original_raw_supplement_ledgers=len(supplement['files']),Optimize_calls=0,IIS_calls=0,
        R106_archive_SHA=sha(archive),R105_archive_SHA=sha(old/'evidence.tar.gz'),
        R106_manifest_SHA=sha(package/'manifest.json'),R105_manifest_SHA=sha(old_manifest),
        inherited_manifest_public_source=old_manifest.relative_to(ROOT).as_posix(),
        restore_source_SHA=sha(__file__),reader_SHA=sha(destination/'scripts/round106_reader.py'),
        used_public_parts_only=(package/'parts_manifest.json').exists(),
        R106_parts_manifest_SHA=sha(package/'parts_manifest.json') if (package/'parts_manifest.json').exists() else None,
        public_parts=read(package/'parts_manifest.json')['archive_parts'] if (package/'parts_manifest.json').exists() else [],
        scope='Only deliverable archives/public code; inherited sources isolated to prevent byte collisions'))
    print(json.dumps(dict(restored=new_count,inherited=old_count,supplement_ledgers=len(supplement['files']),Optimize_calls=0,IIS_calls=0)))

if __name__=='__main__':
    assert sys.argv[1] in ['inherited','add-index','final']
    {'inherited':inherited,'add-index':add_index,'final':final}[sys.argv[1]](sys.argv[2])
