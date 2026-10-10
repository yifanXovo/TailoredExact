"""Current-only public carrier using the unchanged R110 splitter/safe restore."""
import ast, gzip, hashlib, inspect, json, subprocess, tarfile, time
from pathlib import Path
import round110_public as prior
ROUND='results/unified_exact_round112'
BASE='ded38c756a32a464bfa9800212da75778707d974'
for name in ('read','sha','write','exact','idle','safe','inside','new_root','split_archive','validate_carrier','recombine_carrier'):
    globals()[name]=getattr(prior,name)
SINGLE_BLOB_LIMIT=prior.SINGLE_BLOB_LIMIT;PART_BYTES=prior.PART_BYTES

def pack(root):
    idle();root=Path(root).resolve();out=root/ROUND;begin=time.perf_counter()
    package=out/'compact_evidence';package.mkdir(parents=True,exist_ok=False)
    files=set()
    def add(path):
        path=inside(root,path,'file');name=path.relative_to(root).as_posix();safe(name);files.add(name)
    for path in out.rglob('*'):
        if path.is_file() and not path.is_relative_to(package) and '__pycache__' not in path.parts and path.suffix.lower() not in prior.FORBIDDEN:add(path)
    candidate=read(out/'candidate_identity.json')
    for field in ('source_bindings','helpers'):
        for name,h in candidate[field].items():assert sha(root/name)==h;add(root/name)
    for name in ('read_round112','compare_round112_startup','qualify_round112_faults','adjudicate_round112','publish_round112'):add(root/'scripts'/(name+'.py'))
    for campaign in ('campaign','qualification/cli01','qualification/cli02','qualification/positive01','qualification/zero01'):
        for l in read(out/campaign/'identity.json')['launches']:
            p=l['panel'];assert sha(root/p['input_path'])==p['input_sha256'];add(root/p['input_path'])
    # Import-time preregistration is an explicit dependency, not an old raw carrier.
    add(root/'results/unified_exact_round94/preregistration.json')
    pending=[n for n in files if n.startswith('scripts/') and n.endswith('.py')];seen=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name);tree=ast.parse((root/name).read_text(encoding='utf-8-sig'));modules=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):modules.update(v.name.split('.')[0] for v in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:modules.add(node.module.split('.')[0])
        for m in modules:
            path=root/'scripts'/(m+'.py')
            if path.is_file():add(path);pending.append(path.relative_to(root).as_posix())
    records=[]
    for name in sorted(files):
        path=root/name
        if path.suffix.lower() in ('.log','.json','.jsonl','.txt'):
            raw=path.read_bytes()
            assert not any(s in raw for s in (b'Set parameter WLSSecret to value',b'Set parameter WLSAccessID to value',b'-----BEGIN PRIVATE KEY-----')),name
        records.append(dict(path=name,bytes=path.stat().st_size,sha256=sha(path)))
    dependency=dict(path='scripts/round110_public.py',commit=BASE,sha256=sha(root/'scripts/round110_public.py'),bytes=(root/'scripts/round110_public.py').stat().st_size)
    pinned=subprocess.check_output(['git','show',BASE+':'+dependency['path']],cwd=root)
    assert hashlib.sha256(pinned).hexdigest()==dependency['sha256']
    write(out/'public_dependency_closure.json',dict(passed=True,files=len(records),reader_import_closure=sorted(seen),explicit_history_authorities='history/ authority inventory',
        current_actual_raw_only=True,old_full_carriers_copied=False,PE_DLL_license_credentials_excluded=True,Optimize=0))
    add(out/'public_dependency_closure.json');records.append(dict(path=ROUND+'/public_dependency_closure.json',bytes=(out/'public_dependency_closure.json').stat().st_size,sha256=sha(out/'public_dependency_closure.json')));records.sort(key=lambda v:v['path'])
    archive=package/'evidence.tar.gz'
    with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as tar:
        for r in records:
            info=tarfile.TarInfo(r['path']);info.size=r['bytes'];info.mtime=0;info.mode=0o644
            with (root/r['path']).open('rb') as f:tar.addfile(info,f)
    parts=split_archive(archive)
    manifest=dict(schema='round112-current-exact-byte-carrier-v1',archive_path='evidence.tar.gz',archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        parts=parts,single_blob_limit_bytes=SINGLE_BLOB_LIMIT,part_bytes=PART_BYTES,files=records,public_dependencies=[dependency],
        no_PE_DLL_license_or_credentials=True,current_actual_raw_only=True,source_bindings=candidate['source_bindings'],reader_path='scripts/read_round112.py',
        reader_SHA=sha(root/'scripts/read_round112.py'),restore_source_SHA=sha(__file__),Optimize=0)
    validate_carrier(package,manifest);write(package/'manifest.json',manifest)
    write(out/'public_pack_receipt.json',dict(exit_code=0,engineering=True,seconds=time.perf_counter()-begin,files=len(records),archive_bytes=archive.stat().st_size,archive_SHA=sha(archive),manifest_SHA=sha(package/'manifest.json'),source_SHA=sha(__file__),Optimize=0))
    print(json.dumps(dict(files=len(records),archive_bytes=archive.stat().st_size,parts=len(parts))))

for operation in ('export','restore'):
    source=inspect.getsource(getattr(prior,operation)).replace('scripts/round110_public.py','scripts/publish_round112.py').replace('scripts/round110_final_reader.py','scripts/read_round112.py')
    namespace=dict(vars(prior),ROUND=ROUND,__file__=__file__)
    exec(compile(source,__file__+'::inherited_'+operation,'exec'),namespace);globals()[operation]=namespace[operation]

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('pack','export','restore'));p.add_argument('--root');p.add_argument('--public-root');p.add_argument('--out');a=p.parse_args()
    if a.operation=='pack':pack(a.root)
    elif a.operation=='export':export(a.root,a.out)
    else:restore(a.public_root,a.out)
