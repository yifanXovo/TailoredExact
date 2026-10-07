"""Exact-byte non-overwriting restoration into an exclusive empty directory."""
from round106_common import *
import hashlib, tarfile

def unpack(archive,manifest,destination):
    q=read(manifest);assert sha(archive)==q['archive_sha256']
    expected={r['path']:r for r in q['files']};seen=set()
    with tarfile.open(archive,'r:gz') as pack:
        for member in pack:
            assert member.isfile() and member.name in expected and member.name not in seen
            p=(destination/member.name).resolve();assert p.is_relative_to(destination)
            assert member.name.startswith(('results/','reference/','scripts/','src/','include/'))
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

if __name__=='__main__':
    assert sys.argv[1] in ['inherited','add-index']
    (inherited if sys.argv[1]=='inherited' else add_index)(sys.argv[2])
