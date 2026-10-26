"""Exact-byte public export/restore; stdlib only, never a solver.

Packaging/export are engineering work and must run after all native processes
have stopped. Restoration accepts only a manifest-bound plain-file archive;
the restored reader receives its root explicitly and cannot consult a worktree.
"""
import argparse, gzip, hashlib, io, json, os, subprocess, tarfile, time
from pathlib import Path

ROUND='results/unified_exact_round109'
FORBIDDEN={'.exe','.dll','.lic','.key','.pem','.pyc','.pdb','.obj','.o','.lib','.a'}
BASE='d11c94d81e6a2c5dcd64dad8c54b390f3cb4a027'
SINGLE_BLOB_LIMIT=95*1024*1024
PART_BYTES=90*1024*1024

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def exact(source,dest):
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert sha(dest)==sha(source)
    else:
        with Path(source).open('rb') as f,dest.open('xb') as g:
            while block:=f.read(1024*1024):g.write(block)
    assert sha(source)==sha(dest)
def idle():
    if os.name=='nt':
        result=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True)
        assert not any('"'+name.lower()+'"' in result.lower() for name in ['ExactEBRP.exe','gurobi_cl.exe','g++.exe','cc1plus.exe','ninja.exe']), 'No packaging during performance/build'
def safe(name):
    p=Path(name);assert not p.is_absolute() and '..' not in p.parts and p.suffix.lower() not in FORBIDDEN
    assert name=='CMakeLists.txt' or name.startswith(('results/','reference/','scripts/','src/','include/','tests/'))
    assert p.name.lower() not in ['.env','gurobi.lic','license.key']

def inside(root,path,kind=None):
    root=Path(root).resolve();lexical=Path(path).absolute();resolved=lexical.resolve()
    assert resolved.is_relative_to(root) and lexical==resolved and not lexical.is_symlink()
    if kind=='file':assert resolved.is_file()
    if kind=='directory':assert resolved.is_dir()
    return resolved

def new_root(path):
    lexical=Path(path).absolute();resolved=lexical.resolve()
    assert lexical==resolved and not lexical.is_symlink() and not lexical.exists()
    resolved.mkdir(parents=True,exist_ok=False);return resolved

def split_archive(archive,limit=SINGLE_BLOB_LIMIT,part_bytes=PART_BYTES):
    """Split only an actually oversized compressed stream; never recompress."""
    archive=Path(archive);assert archive.is_file() and not archive.is_symlink()
    assert 0<part_bytes<limit and not list(archive.parent.glob(archive.name+'.part*'))
    if archive.stat().st_size<limit:return []
    records=[];offset=0
    with archive.open('rb') as source:
        while block:=source.read(part_bytes):
            index=len(records)+1;assert index<1000
            target=archive.parent/(archive.name+f'.part{index:03d}')
            with target.open('xb') as file:file.write(block)
            records.append(dict(index=index,path=target.name,offset=offset,bytes=len(block),sha256=sha(target)))
            offset+=len(block)
    assert offset==archive.stat().st_size
    return records

def validate_carrier(package,manifest,limit=SINGLE_BLOB_LIMIT,part_bytes=PART_BYTES):
    """Check canonical contiguous parts and the exact whole compressed hash."""
    lexical=Path(package).absolute();package=lexical.resolve();assert lexical==package and not lexical.is_symlink()
    name=manifest['archive_path'];assert name=='evidence.tar.gz'
    assert manifest['single_blob_limit_bytes']==limit and manifest['part_bytes']==part_bytes and 0<part_bytes<limit
    total=manifest['archive_bytes'];assert type(total) is int and total>=0
    parts=manifest['parts'];assert isinstance(parts,list)
    if parts:
        assert total>=limit and len(parts)==(total+part_bytes-1)//part_bytes and len(parts)<1000
        expected_names=[name+f'.part{i:03d}' for i in range(1,len(parts)+1)]
        assert {p.name for p in package.glob(name+'.part*')}==set(expected_names)
        expected=[]
        for index,record in enumerate(parts,1):
            offset=(index-1)*part_bytes;size=min(part_bytes,total-offset)
            assert record['index']==index and record['path']==expected_names[index-1]
            assert record['offset']==offset and record['bytes']==size and 0<size<limit
            expected.append((record['path'],size,record['sha256']))
    else:
        assert total<limit and not list(package.glob(name+'.part*'))
        expected=[(name,total,manifest['archive_sha256'])]
    combined=hashlib.sha256();seen_bytes=0;paths=[]
    for part_name,size,digest in expected:
        path=inside(package,package/part_name,'file')
        assert path.stat().st_size==size
        current=hashlib.sha256();current_bytes=0
        with path.open('rb') as file:
            while block:=file.read(1024*1024):current.update(block);combined.update(block);current_bytes+=len(block)
        assert current_bytes==size and current.hexdigest()==digest
        seen_bytes+=current_bytes;paths.append(path)
    assert seen_bytes==total and combined.hexdigest()==manifest['archive_sha256']
    return paths

def recombine_carrier(package,manifest,destination,limit=SINGLE_BLOB_LIMIT,part_bytes=PART_BYTES):
    sources=validate_carrier(package,manifest,limit,part_bytes);destination=Path(destination)
    with destination.open('xb') as output:
        for path in sources:
            with path.open('rb') as source:
                while block:=source.read(1024*1024):output.write(block)
    assert destination.stat().st_size==manifest['archive_bytes'] and sha(destination)==manifest['archive_sha256']
    return destination

def pack(root):
    idle();root=Path(root).resolve();out=root/ROUND;package=out/'compact_evidence';package.mkdir(exist_ok=False)
    begin=time.perf_counter();candidate=read(out/'candidate_identity.json');files=set()
    def add(path):
        path=Path(path)
        if path.is_relative_to(out/'engineering'):
            parts=path.relative_to(out/'engineering').parts
            if parts and parts[0].startswith('public_'):return
        if path.is_dir():
            for f in path.rglob('*'):
                if f.is_file() and '__pycache__' not in f.parts and f.suffix.lower() not in FORBIDDEN:add(f)
        else:
            assert path.is_file() and not path.is_symlink();name=path.relative_to(root).as_posix();safe(name);files.add(name)
    # Own raw evidence and the exact reports it reconstructs. Final narrative,
    # packaging/restore/reviewer receipts are separately committed supplements.
    for name in ['qualification','campaign','fees','engineering','review','reports_final','numerical_finite01',
        'main06_finite01','main06_finite02','main06_science_compare02','main06_science_compare03',
        'reports_numerical_recovery01','reports_main06_recovery01','reports_main06_affected02']:
        add(out/name)
    for name in ['candidate_identity.json','candidate_identity_pre_wrapper_receipt01.json','candidate_contract_freeze.json',
        'generation_recipe.json','input_manifest.json','protocol.json','structure_statistics.json','source_subset_overlap.json','goal.md',
        'admission_decision.json','selection_decision.json','cancellation_decision.json','baseline.json',
        'research_decision.md','representation_contract.md','source_adapter.md','evidence_compatibility.md','paper_candidate_spec.md',
        'main06_recovery.md','main09_stack_failure.md','blocked_finalization_freeze.json']:
        if (out/name).exists():add(out/name)
    for role in read(out/'input_manifest.json')['roles']:add(root/role['input_path'])
    # Functional qualification is also rebuilt from raw physics. Its V20 H100
    # input is not one of the twelve new formal-role inputs, so it must be explicit.
    for campaign in ['qualification/cli01','campaign']:
        for launch in read(out/campaign/'identity.json')['launches']:
            panel=launch['panel'];path=root/panel['input_path']
            assert sha(path)==panel['input_sha256'];add(path)
    add(root/'reference/round109_geographic')
    add(root/'results/data_generation_citibike_round57/source_station_table.csv')
    for name,digest in candidate['source_bindings'].items():assert sha(root/name)==digest;add(root/name)
    for name,digest in candidate['helpers'].items():assert sha(root/name)==digest;add(root/name)
    for name in ['round109_reader.py','round109_decisions.py','round109_public.py','round108_reader.py','round108_scopes.py','round108_decisions.py','round108_public.py','round107_reader.py','round99_pure_start_audit.py','round99_common.py']:
        add(root/'scripts'/name)
    # Include the fault-specific reader dependency and its actual finite checks.
    # Authoring/diagnosis/recovery history must remain reviewable after restoration.
    for script in sorted((root/'scripts').glob('round109*.py')):add(script)
    records=[]
    for name in sorted(files):
        p=root/name
        if p.suffix.lower() in ['.log','.json','.jsonl']:
            # Refuse publishing actual credential-setting lines. Generic native
            # license descriptions are not credentials or license file content.
            b=p.read_bytes()
            assert not any(s in b for s in [b'Set parameter WLSSecret to value',b'Set parameter WLSAccessID to value',b'-----BEGIN PRIVATE KEY-----']),name
        records.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
    archive=package/'evidence.tar.gz'
    with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as tar:
        for r in records:
            info=tarfile.TarInfo(r['path']);info.size=r['bytes'];info.mtime=0;info.mode=0o644;info.uid=info.gid=0;info.uname=info.gname=''
            with (root/r['path']).open('rb') as f:tar.addfile(info,f)
    dependencies=[]
    # Historical claims are pinned small public documents, not old raw archives.
    history=['results/unified_exact_round100/candidate_freeze.json','results/unified_exact_round100/mathematical_algorithm.md',
        'results/unified_exact_round100/final_report.md',
        'results/unified_exact_round108/final_report.md','results/unified_exact_round108/representation_contract.md',
        'results/unified_exact_round108/reproduce.md','results/unified_exact_round108/reports_final/arms.csv',
        'results/unified_exact_round108/reports_final/pairs.csv','results/unified_exact_round108/reports_final/mechanism_summary.csv',
        'results/unified_exact_round108/reports_final/selection_decision.json',
        'results/unified_exact_round108/review/final_local_review01.json',
        'results/unified_exact_round108/review/public_isolated_review01.json',
        'results/unified_exact_round108/review/confirmation_L48_review01.json']
    for name in history:
        process=subprocess.run(['git','show',BASE+':'+name],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert process.returncode==0,('missing explicit public historical dependency',name)
        dependencies.append(dict(commit=BASE,path=name,bytes=len(process.stdout),sha256=hashlib.sha256(process.stdout).hexdigest(),scope='historical claim dependency, no performance substitution'))
    parts=split_archive(archive)
    value=dict(schema='round109-public-exact-byte-carrier-v2',archive_path='evidence.tar.gz',archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        parts=parts,single_blob_limit_bytes=SINGLE_BLOB_LIMIT,part_bytes=PART_BYTES,
        files=records,public_dependencies=dependencies,source_snapshot='Exact measured bytes; source content is inherited R107/R100, no production change; inherited Seed0 journal guard has an independently qualified reader-only Seed1 sidecar',
        no_PE_DLL_license_or_credentials=True,source_bindings=candidate['source_bindings'],
        reader_SHA=sha(root/'scripts/round109_reader.py'),restore_source_SHA=sha(__file__),
        public_math_evidence_reconstruction=True,independent_engine_performance_rerun=False,
        small_carrier_not_artificially_split=not parts,large_actual_carrier_exact_parts=bool(parts),Optimize=0,IIS=0)
    carrier_paths=validate_carrier(package,value)
    write(package/'manifest.json',value)
    write(out/'public_pack_receipt.json',dict(command=['pack','--root',str(root)],engineering=True,exit_code=0,
        seconds=time.perf_counter()-begin,files=len(files),archive_bytes=archive.stat().st_size,
        archive_SHA=sha(archive),manifest_SHA=sha(package/'manifest.json'),source_SHA=sha(__file__),
        exact_part_count=len(parts),public_carrier_paths=[p.name for p in carrier_paths],Optimize=0,IIS=0))
    print(json.dumps(dict(files=len(files),archive_bytes=value['archive_bytes'],archive_SHA=value['archive_sha256'],exact_part_count=len(parts),Optimize=0)))

def export(root,destination,limit=SINGLE_BLOB_LIMIT,part_bytes=PART_BYTES):
    idle();root=Path(root).resolve();destination=new_root(destination)
    begin=time.perf_counter();package=inside(root,root/ROUND/'compact_evidence','directory')
    manifest=read(inside(root,package/'manifest.json','file'));records=[]
    script=inside(root,root/'scripts/round109_public.py','file')
    assert sha(script)==manifest['restore_source_SHA']
    carrier_paths=validate_carrier(package,manifest,limit,part_bytes)
    for name in ['manifest.json']+[p.name for p in carrier_paths]:
        rel=ROUND+'/compact_evidence/'+name;safe(rel)
        exact(inside(root,root/rel,'file'),inside(destination,destination/rel));records.append(dict(path=rel,sha256=sha(destination/rel),bytes=(destination/rel).stat().st_size,source='Proposed public exact bytes'))
    exact(script,inside(destination,destination/'scripts/round109_public.py'))
    records.append(dict(path='scripts/round109_public.py',sha256=sha(destination/'scripts/round109_public.py'),bytes=(destination/'scripts/round109_public.py').stat().st_size,source='Proposed public stdlib restorer'))
    for r in manifest['public_dependencies']:
        safe(r['path']);dest=inside(destination,destination/r['path']);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as file:p=subprocess.run(['git','show',r['commit']+':'+r['path']],cwd=root,stdout=file,stderr=subprocess.PIPE)
        assert p.returncode==0 and sha(dest)==r['sha256'] and dest.stat().st_size==r['bytes']
        records.append(dict(r,source='Pinned public Git dependency'))
    receipt=dict(public_root=str(destination),files=records,only_proposed_public_files_and_explicit_public_dependencies=True,
        archive_SHA=manifest['archive_sha256'],source_SHA=sha(__file__),exit_code=0,engineering=True,seconds=time.perf_counter()-begin,Optimize=0,IIS=0)
    write(destination/'public_export_receipt.json',receipt);write(root/ROUND/'public_export_receipt.json',receipt)
    print(json.dumps(dict(public_root=str(destination),files=len(records),Optimize=0)))

def restore(public,destination,limit=SINGLE_BLOB_LIMIT,part_bytes=PART_BYTES):
    public=Path(public).absolute();assert public==public.resolve() and not public.is_symlink() and public.is_dir()
    destination=new_root(destination);begin=time.perf_counter()
    package=inside(public,public/ROUND/'compact_evidence','directory')
    manifest=read(inside(public,package/'manifest.json','file'))
    script=inside(public,public/'scripts/round109_public.py','file')
    assert Path(__file__).resolve()==script and sha(script)==manifest['restore_source_SHA']
    dependencies=[];dependency_names=set()
    for r in manifest['public_dependencies']:
        safe(r['path']);assert r['path'] not in dependency_names;dependency_names.add(r['path'])
        source=inside(public,public/r['path'],'file');dest=inside(destination,destination/r['path'])
        assert sha(source)==r['sha256'] and source.stat().st_size==r['bytes']
        dependencies.append((r,source,dest))
    if manifest['parts']:
        archive=recombine_carrier(package,manifest,destination/'restored_public_carrier.tar.gz',limit,part_bytes)
    else:archive=validate_carrier(package,manifest,limit,part_bytes)[0]
    expected={r['path']:r for r in manifest['files']};assert len(expected)==len(manifest['files']);seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in expected and member.name not in seen;safe(member.name)
            p=inside(destination,destination/member.name)
            data=tar.extractfile(member).read();r=expected[member.name]
            assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as file:file.write(data)
            seen.add(member.name)
    assert seen==set(expected)
    for r,source,dest in dependencies:
        source=inside(public,source,'file');dest=inside(destination,dest)
        assert sha(source)==r['sha256'];exact(source,dest)
    assert sha(inside(destination,destination/'scripts/round109_reader.py','file'))==manifest['reader_SHA']
    receipt=dict(public_root=str(public),restored_root=str(destination),files=len(seen),
        archive_SHA=sha(archive),archive_bytes=manifest['archive_bytes'],exact_part_count=len(manifest['parts']),
        manifest_SHA=sha(package/'manifest.json'),reader_SHA=sha(destination/'scripts/round109_reader.py'),
        restorer_SHA=sha(__file__),original_workspace_reads=False,public_files_only=True,exit_code=0,
        seconds=time.perf_counter()-begin,engineering=True,Optimize=0,IIS=0)
    write(destination/'restore_receipt.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['pack','export','restore']);p.add_argument('--root');p.add_argument('--public-root');p.add_argument('--out');a=p.parse_args()
    if a.operation=='pack':pack(a.root)
    elif a.operation=='export':export(a.root,a.out)
    else:restore(a.public_root,a.out)
