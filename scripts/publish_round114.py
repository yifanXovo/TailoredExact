"""Exact-byte current evidence export and empty-root restore; no solver."""
import argparse,ast,gzip,hashlib,json,os,subprocess,tarfile,time
from pathlib import Path
ROUND='results/unified_exact_round114'
LIMIT=95*1024*1024
PART=90*1024*1024
FORBIDDEN={'.exe','.dll','.lic','.key','.pem','.pyc','.pdb','.obj','.o','.lib','.a'}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def safe(n):
    p=Path(n);assert not p.is_absolute() and not p.drive and '..' not in p.parts and '\\' not in n and ':' not in n
    assert p.suffix.lower() not in FORBIDDEN and p.name.lower() not in ['.env','gurobi.lic','license.key']
    assert n=='CMakeLists.txt' or n.startswith(('scripts/','src/','include/','tests/','reference/','results/'))
def inside(root,p):
    root=Path(root).resolve();p=Path(p).absolute();resolved=p.resolve()
    assert p==resolved and resolved.is_relative_to(root) and not p.is_symlink();return resolved
def new_root(p):
    p=Path(p).absolute();assert p==p.resolve() and not p.exists() and not p.is_symlink()
    p.mkdir(parents=True,exist_ok=False);return p
def exact(a,b):
    b=Path(b);b.parent.mkdir(parents=True,exist_ok=True)
    with Path(a).open('rb') as f,b.open('xb') as g:
        while block:=f.read(1024*1024):g.write(block)
    assert sha(a)==sha(b)
def idle():
    if os.name=='nt':
        data=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True).lower()
        assert not any('"'+n+'"' in data for n in ['exactebrp.exe','gurobi_cl.exe','g++.exe','cc1plus.exe','ninja.exe'])

def carriers(package,m):
    package=Path(package).resolve();assert m['archive_path']=='evidence.tar.gz'
    assert m['single_blob_limit_bytes']==LIMIT and m['part_bytes']==PART
    size=m['archive_bytes'];parts=m['parts'];expected=[]
    if parts:
        assert size>=LIMIT and len(parts)==(size+PART-1)//PART
        assert {p.name for p in package.glob('evidence.tar.gz.part*')}=={q['path'] for q in parts}
        for index,q in enumerate(parts,1):
            assert q['index']==index and q['path']==f'evidence.tar.gz.part{index:03d}' and q['offset']==(index-1)*PART
            assert q['bytes']==min(PART,size-q['offset'])<LIMIT;expected.append(q)
    else:
        assert size<LIMIT and not list(package.glob('evidence.tar.gz.part*'))
        expected=[dict(path=m['archive_path'],bytes=size,sha256=m['archive_sha256'])]
    whole=hashlib.sha256();paths=[];total=0
    for q in expected:
        p=inside(package,package/q['path']);assert p.is_file() and p.stat().st_size==q['bytes'] and sha(p)==q['sha256']
        with p.open('rb') as f:
            while b:=f.read(1024*1024):whole.update(b);total+=len(b)
        paths.append(p)
    assert total==size and whole.hexdigest()==m['archive_sha256'];return paths

def pack(root):
    idle();begin=time.perf_counter();root=Path(root).resolve();out=root/ROUND
    summary=read(out/'reports_final/summary.json');assert summary['execution_status']=='BLOCKED'
    assert summary['new_qualified_measurements']==1 and summary['evaluable_pairs']==21
    assert read(out/'review/postformal01/signed_review.json')['decision'] in ['ACCEPT','ACCEPT_BLOCKED_DELIVERY']
    assert read(out/'review/whole_goal01/signed_review.json')['decision']=='ACCEPT_BLOCKED_DELIVERY'
    package=out/'compact_evidence';package.mkdir(parents=True,exist_ok=False);files=set()
    def add(p):
        p=inside(root,p);assert p.is_file();n=p.relative_to(root).as_posix();safe(n);files.add(n)
    for p in out.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or p.suffix.lower() in FORBIDDEN:continue
        n=p.relative_to(out).as_posix()
        if n.startswith(('compact_evidence/','public_export01/','review/postformal01/reconstructed','review/restored01/')):continue
        if n.startswith(('public_pack_receipt','public_export_receipt','remote_','pr_','delivery_receipt','engineering/restored')):continue
        add(p)
    candidate=read(out/'candidate_identity.json')
    for field in ['source_bindings','helpers']:
        for n,h in candidate[field].items():assert sha(root/n)==h;add(root/n)
    for stem in ['round114_initialize','round114_counterexample','qualify_round114','qualify_round114_post',
        'read_round114','round114_report','round114_final_check','publish_round114','verify_round114_publication']:
        add(root/'scripts'/(stem+'.py'))
    add(root/'scripts/.gitattributes')
    for campaign in ['campaign','qualification/cli01']:
        for l in read(out/campaign/'identity.json')['launches']:
            p=l['panel'];assert sha(root/p['input_path'])==p['input_sha256'];add(root/p['input_path'])
    add(root/'results/unified_exact_round94/preregistration.json')
    pending=[n for n in files if n.startswith('scripts/') and n.endswith('.py')];seen=set()
    while pending:
        n=pending.pop()
        if n in seen:continue
        seen.add(n);tree=ast.parse((root/n).read_text(encoding='utf-8-sig'));modules=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):modules.update(q.name.split('.')[0] for q in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:modules.add(node.module.split('.')[0])
        for m in modules:
            p=root/'scripts'/(m+'.py')
            if p.is_file():add(p);pending.append(p.relative_to(root).as_posix())
    records=[]
    for n in sorted(files):
        p=root/n
        if p.suffix.lower() in ['.log','.json','.jsonl','.txt']:
            data=p.read_bytes()
            assert not any(q in data for q in [b'Set parameter WLSSecret to value',b'Set parameter WLSAccessID to value',b'-----BEGIN PRIVATE KEY-----']),n
        records.append(dict(path=n,bytes=p.stat().st_size,sha256=sha(p)))
    closure=out/'public_dependency_closure.json'
    write(closure,dict(passed=True,reader_import_closure=sorted(seen),files_before_closure=len(records),
        frozen_source_files=206,frozen_performance_helpers=47,old_full_carriers_copied=False,
        limited_history='inherited_r113 manifests/signed15+21; inherited_return_authority signed finite contracts; specified G50 counterexample',
        actual_raw_including_failures_preserved=True,PE_DLL_license_credentials_excluded=True,Optimize=0))
    records.append(dict(path=closure.relative_to(root).as_posix(),bytes=closure.stat().st_size,sha256=sha(closure)));records.sort(key=lambda q:q['path'])
    archive=package/'evidence.tar.gz'
    with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as zipped,tarfile.open(fileobj=zipped,mode='w|') as tar:
        for q in records:
            info=tarfile.TarInfo(q['path']);info.size=q['bytes'];info.mtime=0;info.mode=0o644
            with (root/q['path']).open('rb') as f:tar.addfile(info,f)
    parts=[]
    if archive.stat().st_size>=LIMIT:
        with archive.open('rb') as f:
            while b:=f.read(PART):
                k=len(parts)+1;p=package/f'evidence.tar.gz.part{k:03d}'
                with p.open('xb') as g:g.write(b)
                parts.append(dict(index=k,path=p.name,offset=(k-1)*PART,bytes=len(b),sha256=sha(p)))
    manifest=dict(schema='round114-current-and-limited-signed-history-v1',archive_path=archive.name,archive_bytes=archive.stat().st_size,
        archive_sha256=sha(archive),parts=parts,single_blob_limit_bytes=LIMIT,part_bytes=PART,files=records,
        source_bindings=candidate['source_bindings'],performance_helpers=candidate['helpers'],candidate_identity_SHA=sha(out/'candidate_identity.json'),
        admitted_reader_SHA=candidate['offline_reader_SHA'],reader_path='scripts/read_round114.py',reader_SHA=sha(root/'scripts/read_round114.py'),
        reader_delta_path=ROUND+'/reader_delta.md',restore_source_SHA=sha(__file__),old_full_carriers_copied=False,
        no_PE_DLL_license_or_credentials=True,source_CRLF_LF_actual_bytes_preserved=True,Optimize=0)
    paths=carriers(package,manifest);write(package/'manifest.json',manifest)
    write(out/'public_pack_receipt.json',dict(engineering=True,seconds=time.perf_counter()-begin,exit_code=0,files=len(records),
        archive_SHA=manifest['archive_sha256'],archive_bytes=manifest['archive_bytes'],manifest_SHA=sha(package/'manifest.json'),
        source_SHA=sha(__file__),parts=len(parts),carrier_files=[p.name for p in paths],Optimize=0))
    print(json.dumps(dict(files=len(records),archive_bytes=manifest['archive_bytes'],parts=len(parts),seconds=time.perf_counter()-begin)))

def export(root,destination):
    idle();begin=time.perf_counter();root=Path(root).resolve();destination=new_root(destination)
    package=root/ROUND/'compact_evidence';m=read(package/'manifest.json');assert sha(__file__)==m['restore_source_SHA']
    paths=carriers(package,m);copied=[]
    for p in paths+[package/'manifest.json',Path(__file__).resolve()]:
        n=p.relative_to(root).as_posix();safe(n);dest=inside(destination,destination/n);exact(p,dest)
        copied.append(dict(path=n,bytes=dest.stat().st_size,sha256=sha(dest)))
    receipt=dict(public_root=str(destination),files=copied,archive_SHA=m['archive_sha256'],manifest_SHA=sha(package/'manifest.json'),
        only_exact_public_carrier_and_self_contained_restorer=True,engineering=True,seconds=time.perf_counter()-begin,exit_code=0,Optimize=0)
    write(destination/'public_export_receipt.json',receipt);write(root/ROUND/'public_export_receipt.json',receipt);print(json.dumps(receipt))

def restore(public,destination):
    begin=time.perf_counter();public=Path(public).absolute();assert public==public.resolve() and public.is_dir() and not public.is_symlink()
    package=inside(public,public/ROUND/'compact_evidence');m=read(package/'manifest.json')
    assert Path(__file__).resolve()==public/'scripts/publish_round114.py' and sha(__file__)==m['restore_source_SHA']
    sources=carriers(package,m);destination=new_root(destination)
    if m['parts']:
        archive=destination/'restored_public_carrier.tar.gz'
        with archive.open('xb') as g:
            for p in sources:
                with p.open('rb') as f:
                    while b:=f.read(1024*1024):g.write(b)
    else:archive=sources[0]
    assert sha(archive)==m['archive_sha256'];expected={q['path']:q for q in m['files']};seen=set()
    assert len(expected)==len(m['files'])
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in expected and member.name not in seen;safe(member.name)
            dest=inside(destination,destination/member.name);q=expected[member.name];data=tar.extractfile(member).read()
            assert len(data)==q['bytes'] and hashlib.sha256(data).hexdigest()==q['sha256']
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as g:g.write(data)
            seen.add(member.name)
    assert seen==set(expected) and sha(destination/m['reader_path'])==m['reader_SHA']
    receipt=dict(restored_root=str(destination),public_root=str(public),files=len(seen),all_member_SHA_verified=True,
        archive_SHA=m['archive_sha256'],archive_bytes=m['archive_bytes'],manifest_SHA=sha(package/'manifest.json'),reader_SHA=m['reader_SHA'],
        original_workspace_reads=False,public_files_only=True,empty_root_before_extraction=True,engineering=True,
        seconds=time.perf_counter()-begin,exit_code=0,Optimize=0)
    write(destination/'restore_receipt.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['pack','export','restore']);p.add_argument('--root');p.add_argument('--public-root');p.add_argument('--out');a=p.parse_args()
    if a.operation=='pack':pack(a.root)
    elif a.operation=='export':export(a.root,a.out)
    else:restore(a.public_root,a.out)
