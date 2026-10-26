"""Public-only, non-overwriting exact-byte restoration; standard library only."""
import argparse,hashlib,json,tarfile
from pathlib import Path

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()
def write(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
def exact(source,destination):
    source=Path(source);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():assert destination.read_bytes()==source.read_bytes()
    else:destination.write_bytes(source.read_bytes())

def carrier(package,destination):
    q=read(package/'manifest.json');parts=read(package/'parts_manifest.json')
    assert parts['original_manifest_SHA']==sha(package/'manifest.json')
    assert parts['archive_sha256']==q['archive_sha256'] and parts['archive_bytes']==q['archive_bytes']
    destination.mkdir();archive=destination/'evidence.tar.gz';combined=hashlib.sha256();size=0
    with archive.open('xb') as output:
        for n,r in enumerate(parts['archive_parts'],1):
            assert r['path']==f'evidence.tar.gz.part{n:03d}';source=package/r['path'];h=hashlib.sha256();length=0
            with source.open('rb') as f:
                while block:=f.read(1024*1024):output.write(block);h.update(block);combined.update(block);length+=len(block);size+=len(block)
            assert length==r['bytes'] and h.hexdigest()==r['sha256']
    assert size==q['archive_bytes'] and combined.hexdigest()==q['archive_sha256']
    return archive

def unpack(archive,manifest,destination):
    q=read(manifest);assert sha(archive)==q['archive_sha256']
    expected={r['path']:r for r in q['files']};seen=set()
    assert len(expected)==len(q['files'])
    with tarfile.open(archive,'r:gz') as t:
        for member in t:
            assert member.isfile() and member.name in expected and member.name not in seen
            assert member.name=='CMakeLists.txt' or member.name.startswith(('results/','reference/','scripts/','src/','include/','tests/'))
            p=(destination/member.name).resolve();assert p.is_relative_to(destination)
            assert p.suffix.lower() not in ['.exe','.dll','.lic','.key','.pem','.pyc','.pdb','.obj','.o']
            data=t.extractfile(member).read();r=expected[member.name]
            assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
            if p.exists():assert p.is_file() and sha(p)==r['sha256']
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            seen.add(member.name)
    assert seen==set(expected);return len(seen)

def restore(public,destination):
    public=public.resolve();destination=destination.resolve();destination.mkdir(parents=True,exist_ok=False)
    package=public/'results/unified_exact_round107/compact_evidence';manifest=read(package/'manifest.json')
    archive=carrier(package,destination/'round107_carrier');new_count=unpack(archive,package/'manifest.json',destination)
    for name in ['manifest.json','parts_manifest.json']:exact(package/name,destination/'results/unified_exact_round107/compact_evidence'/name)
    dep106=manifest['public_dependencies'][0];dep105=manifest['public_dependencies'][1]
    old=public/'results/unified_exact_round106/compact_evidence'
    assert sha(old/'manifest.json')==dep106['manifest_SHA'] and sha(old/'parts_manifest.json')==dep106['parts_manifest_SHA']
    archive106=carrier(old,destination/'round106_carrier');assert sha(archive106)==dep106['archive_SHA']
    inherited=destination/'inherited_r106';inherited.mkdir();old_count=unpack(archive106,old/'manifest.json',inherited)
    for name in ['manifest.json','parts_manifest.json']:exact(old/name,inherited/'results/unified_exact_round106/compact_evidence'/name)
    archive105=public/dep105['path'];exact_manifest=public/dep105['exact_manifest_public_path']
    assert sha(archive105)==dep105['archive_SHA'] and sha(exact_manifest)==dep105['exact_manifest_SHA']
    legacy=inherited/'inherited_r105';legacy.mkdir();legacy_count=unpack(archive105,exact_manifest,legacy)
    exact(exact_manifest,legacy/'results/unified_exact_round105/compact_evidence/manifest.json')
    supplement=inherited/'results/unified_exact_round106/r105_supplement/manifest.json'
    exact(supplement,legacy/'results/unified_exact_round106/r105_supplement/manifest.json')
    for r in read(supplement)['files']:
        source=inherited/r['recovered_path'];assert sha(source)==r['sha256'];target=legacy/r['original_path']
        assert not target.exists();exact(source,target)
    receipt=dict(source_public_root=str(public),restored_root=str(destination),new_files=new_count,R106_files=old_count,R105_files=legacy_count,exact_legacy_supplement_files=len(read(supplement)['files']),round107_archive_SHA=sha(archive),round106_archive_SHA=sha(archive106),round105_archive_SHA=sha(archive105),manifest_SHA=sha(package/'manifest.json'),reader_SHA=sha(destination/'scripts/round107_reader.py'),restorer_SHA=sha(__file__),public_parts_only=True,original_workspace_reads=False,Optimize_calls=0,IIS_calls=0)
    write(destination/'restore_receipt.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--public-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();restore(a.public_root,a.out)
