"""Single-carrier exact-byte public export/restore; stdlib only, never a solver.

Packaging/export are engineering work and must run after all native processes
have stopped. Restoration accepts only a manifest-bound plain-file archive;
the restored reader receives its root explicitly and cannot consult a worktree.
"""
import argparse, gzip, hashlib, io, json, os, subprocess, tarfile, time
from pathlib import Path

ROUND='results/unified_exact_round108'
FORBIDDEN={'.exe','.dll','.lic','.key','.pem','.pyc','.pdb','.obj','.o','.lib','.a'}
BASE='b5db3f038f64215766a54498d8acc82e384de733'

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
    for name in ['qualification','bridge01','confirmation01','fees','fee_corrections','engineering','review','reports_final']:
        add(out/name)
    for name in ['candidate_identity.json','candidate_identity_pre_wrapper_receipt01.json','candidate_contract_freeze.json',
        'generation_recipe.json','input_manifest.json','development_protocol.json','confirmation_protocol.json',
        'admission_decision.json','selection_decision.json','cancellation_decision.json','baseline.json',
        'research_decision.md','representation_contract.md']:
        if (out/name).exists():add(out/name)
    for role in read(out/'input_manifest.json')['roles']:add(root/role['input_path'])
    # Functional qualification is also rebuilt from raw physics. Its H100
    # input is not one of the seven formal-role inputs, so it must be explicit.
    for campaign in ['qualification/cli01','bridge01','confirmation01']:
        for launch in read(out/campaign/'identity.json')['launches']:
            panel=launch['panel'];path=root/panel['input_path']
            assert sha(path)==panel['input_sha256'];add(path)
    add(root/'reference/round108_confirmation')
    for name,digest in candidate['source_bindings'].items():assert sha(root/name)==digest;add(root/name)
    for name,digest in candidate['helpers'].items():assert sha(root/name)==digest;add(root/name)
    for name in ['round108_reader.py','round108_scopes.py','round108_engineering.py','round108_budget.py','round108_report.py','round108_decisions.py','round108_reader_counterexamples.py','round108_public.py',
        'round107_reader.py','round99_pure_start_audit.py','round99_common.py']:
        add(root/'scripts'/name)
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
    history=['results/unified_exact_round100/candidate_freeze.json','results/unified_exact_round100/final_report.md',
        'results/unified_exact_round100/mathematical_algorithm.md','results/unified_exact_round100/complete_results_final/summary.json',
        'results/unified_exact_round100/complete_results_final/runs.csv','results/unified_exact_round100/complete_results_final/pairs.csv',
        'results/unified_exact_round107/final_report.md','results/unified_exact_round107/reports05/arm_results.csv',
        'results/unified_exact_round107/review/final_implementation_performance_review.md',
        'results/unified_exact_round107/review/delivery_review.md',
        'results/unified_exact_round98/final_report.md','results/unified_exact_round99/final_report.md',
        'results/unified_exact_round102/final_report.md','results/unified_exact_round105/final_report.md',
        'results/unified_exact_round106/final_report.md']
    for name in history:
        process=subprocess.run(['git','show',BASE+':'+name],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert process.returncode==0,('missing explicit public historical dependency',name)
        dependencies.append(dict(commit=BASE,path=name,bytes=len(process.stdout),sha256=hashlib.sha256(process.stdout).hexdigest(),scope='historical claim dependency, no performance substitution'))
    value=dict(schema='round108-public-exact-byte-carrier-v1',archive_path='evidence.tar.gz',archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        files=records,public_dependencies=dependencies,source_snapshot='Exact measured bytes; source content is inherited R107/R100, no production change',
        no_PE_DLL_license_or_credentials=True,source_bindings=candidate['source_bindings'],
        reader_SHA=sha(root/'scripts/round108_reader.py'),restore_source_SHA=sha(__file__),
        public_math_evidence_reconstruction=True,independent_engine_performance_rerun=False,
        small_carrier_not_artificially_split=True,Optimize=0,IIS=0)
    # GitHub's 100 MiB file limit applies to the compressed blob. A larger actual
    # carrier needs a separately reviewed exact-byte part manifest; do not split
    # a small package in advance or silently lose raw models/events.
    assert value['archive_bytes']<95*1024*1024,'Actual carrier too large: preserve and explicitly prepare exact parts'
    write(package/'manifest.json',value)
    write(out/'public_pack_receipt.json',dict(command=['pack','--root',str(root)],engineering=True,exit_code=0,
        seconds=time.perf_counter()-begin,files=len(files),archive_bytes=archive.stat().st_size,
        archive_SHA=sha(archive),manifest_SHA=sha(package/'manifest.json'),source_SHA=sha(__file__),Optimize=0,IIS=0))
    print(json.dumps(dict(files=len(files),archive_bytes=value['archive_bytes'],archive_SHA=value['archive_sha256'],Optimize=0)))

def export(root,destination):
    idle();root=Path(root).resolve();destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=False)
    begin=time.perf_counter();package=root/ROUND/'compact_evidence';manifest=read(package/'manifest.json');records=[]
    for name in ['manifest.json','evidence.tar.gz']:
        rel=ROUND+'/compact_evidence/'+name;exact(root/rel,destination/rel);records.append(dict(path=rel,sha256=sha(destination/rel),bytes=(destination/rel).stat().st_size,source='Proposed public exact bytes'))
    exact(root/'scripts/round108_public.py',destination/'scripts/round108_public.py')
    records.append(dict(path='scripts/round108_public.py',sha256=sha(destination/'scripts/round108_public.py'),bytes=(destination/'scripts/round108_public.py').stat().st_size,source='Proposed public stdlib restorer'))
    for r in manifest['public_dependencies']:
        dest=destination/r['path'];dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as file:p=subprocess.run(['git','show',r['commit']+':'+r['path']],cwd=root,stdout=file,stderr=subprocess.PIPE)
        assert p.returncode==0 and sha(dest)==r['sha256'] and dest.stat().st_size==r['bytes']
        records.append(dict(r,source='Pinned public Git dependency'))
    receipt=dict(public_root=str(destination),files=records,only_proposed_public_files_and_explicit_public_dependencies=True,
        archive_SHA=manifest['archive_sha256'],source_SHA=sha(__file__),exit_code=0,engineering=True,seconds=time.perf_counter()-begin,Optimize=0,IIS=0)
    write(destination/'public_export_receipt.json',receipt);write(root/ROUND/'public_export_receipt.json',receipt)
    print(json.dumps(dict(public_root=str(destination),files=len(records),Optimize=0)))

def restore(public,destination):
    public=Path(public).resolve();destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=False)
    begin=time.perf_counter();package=public/ROUND/'compact_evidence';manifest=read(package/'manifest.json')
    archive=package/manifest['archive_path'];assert sha(archive)==manifest['archive_sha256'] and archive.stat().st_size==manifest['archive_bytes']
    expected={r['path']:r for r in manifest['files']};assert len(expected)==len(manifest['files']);seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in expected and member.name not in seen;safe(member.name)
            p=(destination/member.name).resolve();assert p.is_relative_to(destination)
            data=tar.extractfile(member).read();r=expected[member.name]
            assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as file:file.write(data)
            seen.add(member.name)
    assert seen==set(expected)
    for r in manifest['public_dependencies']:
        source=public/r['path'];assert sha(source)==r['sha256'];exact(source,destination/r['path'])
    receipt=dict(public_root=str(public),restored_root=str(destination),files=len(seen),
        archive_SHA=sha(archive),manifest_SHA=sha(package/'manifest.json'),reader_SHA=sha(destination/'scripts/round108_reader.py'),
        restorer_SHA=sha(__file__),original_workspace_reads=False,public_files_only=True,exit_code=0,
        seconds=time.perf_counter()-begin,engineering=True,Optimize=0,IIS=0)
    write(destination/'restore_receipt.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['pack','export','restore']);p.add_argument('--root');p.add_argument('--public-root');p.add_argument('--out');a=p.parse_args()
    if a.operation=='pack':pack(a.root)
    elif a.operation=='export':export(a.root,a.out)
    else:restore(a.public_root,a.out)
