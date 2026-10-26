"""Export only proposed public parts and exact, pinned public Git dependencies."""
from round107_common import *
import hashlib

def export(destination,receipt_path=None):
    from round100_idle import ensure_idle
    ensure_idle();destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=False)
    records=[]
    def proposed(relative):
        source=ROOT/relative;target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
        with source.open('rb') as src,target.open('xb') as dst:
            while block:=src.read(1024*1024):dst.write(block)
        assert sha(source)==sha(target)
        records.append(dict(path=relative,bytes=target.stat().st_size,sha256=sha(target),source='Proposed public Round107 exact bytes'))
    def public_blob(commit,relative):
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as output:
            process=subprocess.run(['git','show',commit+':'+relative],cwd=ROOT,stdout=output,stderr=subprocess.PIPE)
        assert process.returncode==0,process.stderr.decode(errors='replace')
        records.append(dict(path=relative,bytes=target.stat().st_size,sha256=sha(target),source_commit=commit,source='Pinned existing public Git blob'))
    relative='results/unified_exact_round107/compact_evidence/'
    package=ROOT/relative;q=read(package/'manifest.json');parts=read(package/'parts_manifest.json')
    for name in ['manifest.json','parts_manifest.json']+[p['path'] for p in parts['archive_parts']]:proposed(relative+name)
    for name in ['round107_restore.py','round107_reader.py']:proposed('scripts/'+name)
    dep106,dep105=q['public_dependencies']
    old='results/unified_exact_round106/compact_evidence/'
    for name in ['manifest.json','parts_manifest.json']+[p['path'] for p in dep106['parts']]:public_blob(dep106['commit'],old+name)
    assert sha(destination/old/'manifest.json')==dep106['manifest_SHA']
    assert sha(destination/old/'parts_manifest.json')==dep106['parts_manifest_SHA']
    public_blob(dep105['commit'],dep105['path'])
    public_blob(dep106['commit'],dep105['exact_manifest_public_path'])
    assert sha(destination/dep105['path'])==dep105['archive_SHA']
    assert sha(destination/dep105['exact_manifest_public_path'])==dep105['exact_manifest_SHA']
    assert all(Path(r['path']).suffix.lower() not in ['.exe','.dll','.lic','.key','.pem','.pyc','.pdb','.obj','.o'] for r in records)
    manifest=dict(public_root=str(destination),files=records,only_proposed_public_files_and_explicit_pinned_public_dependencies=True,
        export_source_SHA=sha(__file__),round107_archive_SHA=q['archive_sha256'],Optimize_calls=0,IIS_calls=0)
    write(destination/'public_export_manifest.json',manifest)
    if receipt_path is not None:write(receipt_path,manifest)
    print(json.dumps(dict(public_root=str(destination),files=len(records),Optimize_calls=0,IIS_calls=0)))

if __name__=='__main__':export(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)
