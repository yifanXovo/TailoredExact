"""One compact current carrier and one actual Git-export/empty-root restoration."""
from round115_common import *
import ast,gzip,io,shutil,subprocess,tarfile

class Parts(io.RawIOBase):
    def __init__(self,d):self.d=d;self.index=0;self.current=None;self.size=0;self.position=0;self.paths=[]
    def writable(self):return True
    def tell(self):return self.position
    def write(self,b):
        length=len(b);self.position+=length
        while b:
            if self.current is None:
                self.index+=1;p=self.d/f'evidence.tar.gz.part{self.index:03d}';self.current=p.open('xb');self.paths.append(p);self.size=0
            n=min(len(b),32*1024*1024-self.size);self.current.write(b[:n]);self.size+=n;b=b[n:]
            if self.size==32*1024*1024:self.current.close();self.current=None
        return length
    def finish(self):
        if self.current:self.current.close();self.current=None

def closure():
    pending=['read_round115','round115_sublevel','round115_campaign','qualify_round115','qualify_round115_post','round115_review','round115_delivery','round115_organize','round115_postreview']
    names=set()
    while pending:
        name=pending.pop();p=ROOT/'scripts'/(name+'.py')
        if name in names or not p.is_file():continue
        names.add(name)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
            imports=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            for mod in imports:
                if mod and (ROOT/'scripts'/(mod+'.py')).is_file():pending.append(mod)
    return [ROOT/'scripts'/(n+'.py') for n in sorted(names)]

def pack():
    tick=time.perf_counter();d=OUT/'compact_evidence';d.mkdir(exist_ok=False)
    files=set(closure())|{ROOT/n for n in read(OUT/'production_identity.json')['source_bindings']}
    files.update(ROOT/n for n in read(OUT/'candidate_identity.json')['helpers'])
    files.update(ROOT/n for n in ['reference/round100_confirmation/H100.txt','reference/round109_geographic/G50-C1.txt',
        'reference/round109_geographic/G100-R2.txt','results/unified_exact_round94/preregistration.json'])
    for p in OUT.rglob('*'):
        if not p.is_file() or d in p.parents or 'engineering' in p.relative_to(OUT).parts or p.name=='public_pack_receipt.json':continue
        files.add(p)
    files=sorted(files);manifest={p.relative_to(ROOT).as_posix():dict(SHA=sha(p),bytes=p.stat().st_size) for p in files}
    stream=Parts(d)
    try:
        with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|') as archive:
                for p in files:archive.add(p,arcname=p.relative_to(ROOT).as_posix(),recursive=False)
    finally:stream.finish()
    parts=[dict(path=p.relative_to(ROOT).as_posix(),SHA=sha(p),bytes=p.stat().st_size) for p in stream.paths]
    write(d/'manifest.json',dict(schema='round115-current-public-carrier-v1',files=manifest,parts=parts,
        PE_DLL_license_credentials_excluded=True,full_old_carriers_copied=False,original_worktree_fallback=False,Optimize=0))
    write(OUT/'public_dependency_closure.json',dict(scripts=[p.relative_to(ROOT).as_posix() for p in closure()],
        source_files=206,files=len(files),raw_bytes=sum(q['bytes'] for q in manifest.values()),import_configs=['results/unified_exact_round94/preregistration.json'],
        old_carrier_copied=False,independent_review_executor=False,Optimize=0))
    write(OUT/'public_pack_receipt.json',dict(seconds=time.perf_counter()-tick,files=len(files),raw_bytes=sum(q['bytes'] for q in manifest.values()),
        parts=parts,compressed_bytes=sum(q['bytes'] for q in parts),manifest_SHA=sha(d/'manifest.json'),Optimize=0,native_starts=0))
    print(json.dumps(read(OUT/'public_pack_receipt.json')),flush=True)

def restore(commit,destination):
    tick=time.perf_counter();destination=Path(destination).resolve();assert not destination.exists()
    destination.mkdir();export=OUT/'engineering/public_export01';export.mkdir(parents=True,exist_ok=False)
    target=export/'public_carrier.tar';names=['results/unified_exact_round115/compact_evidence/manifest.json']
    names+=read(OUT/'compact_evidence/manifest.json')['parts'] and [p['path'] for p in read(OUT/'compact_evidence/manifest.json')['parts']]
    subprocess.run(['git','archive','--format=tar','--output='+str(target),commit,'--',*names],cwd=ROOT,check=True)
    carrier=export/'carrier';carrier.mkdir()
    with tarfile.open(target) as archive:archive.extractall(carrier,filter='data')
    restored_manifest=read(carrier/'results/unified_exact_round115/compact_evidence/manifest.json')
    assert restored_manifest==read(OUT/'compact_evidence/manifest.json')
    combined=export/'evidence.tar.gz'
    with combined.open('xb') as output:
        for p in restored_manifest['parts']:
            source=carrier/p['path'];assert sha(source)==p['SHA']
            with source.open('rb') as sourcefile:shutil.copyfileobj(sourcefile,output,1024*1024)
    with tarfile.open(combined,'r:gz') as archive:archive.extractall(destination,filter='data')
    for n,q in restored_manifest['files'].items():assert sha(destination/n)==q['SHA']
    write(OUT/'public_export_receipt.json',dict(commit=commit,archive_SHA=sha(target),actual_git_archive=True,parts_verified=True,
        exported_unix=time.time(),Optimize=0,native_starts=0))
    write(OUT/'public_restore_receipt.json',dict(commit=commit,root=str(destination),fresh_empty_directory=True,files=len(restored_manifest['files']),
        all_manifest_hashes_equal=True,original_root_fallback=False,seconds=time.perf_counter()-tick,restored_unix=time.time(),
        receipt_does_not_cover_future_reconstruction=True,Optimize=0,native_starts=0))
    print(json.dumps(read(OUT/'public_restore_receipt.json')),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='pack':pack()
    elif sys.argv[1]=='restore':restore(sys.argv[2],sys.argv[3])
    else:raise ValueError(sys.argv[1])
