"""Finite current-layer public carrier, using the audited R110 safe restorer."""
import ast, gzip, hashlib, inspect, json, subprocess, tarfile, time
from pathlib import Path
import round110_public as prior

ROUND='results/unified_exact_round111'
BASE='13ed7eeb83b647f585837638ed9158b84f274d66'
for name in ('read','sha','write','exact','idle','safe','inside','new_root','split_archive','validate_carrier','recombine_carrier'):
    globals()[name]=getattr(prior,name)
SINGLE_BLOB_LIMIT=prior.SINGLE_BLOB_LIMIT;PART_BYTES=prior.PART_BYTES

def pack(root):
    idle();root=Path(root).resolve();out=root/ROUND;begin=time.perf_counter()
    package=out/'compact_evidence';package.mkdir(parents=True,exist_ok=False)
    files=set();dependencies=[]
    def add(path):
        path=inside(root,path,'file');name=path.relative_to(root).as_posix();safe(name);files.add(name)
    for path in out.rglob('*'):
        if path.is_file() and not path.is_relative_to(package) and '__pycache__' not in path.parts:
            if path.suffix.lower() not in prior.FORBIDDEN:add(path)
    candidate=read(out/'candidate_identity.json')
    for path,digest in candidate['source_bindings'].items():
        assert sha(root/path)==digest;add(root/path)
    for path,digest in candidate['helpers'].items():
        assert sha(root/path)==digest;add(root/path)
    inputs=read(out/'input_manifest.json')
    for p in inputs['roles']:
        assert sha(root/p['input_path'])==p['input_sha256'];add(root/p['input_path'])
    for campaign in ('qualification/cli01','campaign'):
        for launch in read(out/campaign/'identity.json')['launches']:
            panel=launch['panel']
            assert sha(root/panel['input_path'])==panel['input_sha256']
            add(root/panel['input_path'])
    add(root/'reference/round111_audit_counterexample.txt')
    plan=read(out/'replay_plan.json')
    oldroot=Path('E:/codes/ExactEBRP-round110').resolve()
    for sample in plan['samples']:
        for record in sample['files']:
            name=record['path'];source=inside(oldroot,oldroot/name,'file')
            assert sha(source)==record['SHA'] and source.stat().st_size==record['bytes']
            target=root/name;exact(source,target);add(target)
        launch=sample['launch'];camp=sample['campaign']
        for filename in ('original.lp','build.json'):
            name='results/unified_exact_round110/'+camp+'/reference/'+launch['id']+'/'+filename
            source=inside(oldroot,oldroot/name,'file');exact(source,root/name);add(root/name)
    for path in (root/'results/unified_exact_round110/qualification/reference').rglob('*'):
        if path.is_file():add(path)
    history=['scripts/round110_public.py','results/unified_exact_round100/mathematical_algorithm.md',
        'results/unified_exact_round108/final_report.md','results/unified_exact_round108/representation_contract.md',
        'results/unified_exact_round108/review/confirmation_L48_review01.json',
        'results/unified_exact_round108/reports_final/arms.csv','results/unified_exact_round108/reports_final/pairs.csv',
        'results/unified_exact_round108/reports_final/mechanism_summary.csv',
        'results/unified_exact_round109/review/mechanism_correction01.json',
        'results/unified_exact_round110/final_report.md','results/unified_exact_round110/paper_candidate_spec.md',
        'results/unified_exact_round110/mechanism_analysis.json','results/unified_exact_round110/review/strict_full_clock_assessment.md',
        'results/unified_exact_round110/current_numerical_evidence.md',
        'results/unified_exact_round110/structure_statistics.json','results/unified_exact_round110/source_subset_overlap.json',
        'results/unified_exact_round110/reports_final/time_partitions.csv',
        'results/unified_exact_round110/reports_final/mechanism_summary.csv']
    for name in history:
        result=subprocess.run(['git','show',BASE+':'+name],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert result.returncode==0,('missing explicit small historical authority',name)
        digest=hashlib.sha256(result.stdout).hexdigest()
        path=root/name
        if path.exists():assert sha(path)==digest
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(result.stdout)
        add(path);dependencies.append(dict(path=name,commit=BASE,sha256=digest,bytes=len(result.stdout),scope='claim/source authority, no historical main raw'))
    for path in (root/'scripts').glob('round111*.py'):add(path)
    pending=[name for name in files if name.startswith('scripts/') and name.endswith('.py')];seen=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name);tree=ast.parse((root/name).read_text(encoding='utf-8-sig'))
        modules=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):modules.update(v.name.split('.')[0] for v in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:modules.add(node.module.split('.')[0])
        for module in modules:
            path=root/'scripts'/(module+'.py')
            if path.is_file():add(path);pending.append(path.relative_to(root).as_posix())
    signed_read_dependencies={}
    for audit_path in sorted((out/'review').glob('*/audit.json'))+[out/'review/performance_admission.json']:
        audit=read(audit_path)
        for field in ('read_bindings','retained_bindings'):
            for name,digest in audit.get(field,{}).items():
                assert name in files,('missing signed explicit-root dependency',audit_path,field,name)
                assert sha(root/name)==digest,('changed signed dependency',audit_path,name)
                signed_read_dependencies[name]=digest
    records=[]
    for name in sorted(files):
        path=root/name
        if path.suffix.lower() in ('.log','.json','.jsonl'):
            raw=path.read_bytes()
            assert not any(s in raw for s in (b'Set parameter WLSSecret to value',b'Set parameter WLSAccessID to value',b'-----BEGIN PRIVATE KEY-----')),name
        records.append(dict(path=name,bytes=path.stat().st_size,sha256=sha(path)))
    write(out/'public_dependency_closure.json',dict(passed=True,files=len(records),explicit_history=dependencies,
        old_main_raw_copied=False,limited_old_seed_and_H100_fixtures=8,reader_import_closure=sorted(seen),
        all_actual_independent_read_dependencies=signed_read_dependencies,Optimize=0))
    add(out/'public_dependency_closure.json');records.append(dict(path=ROUND+'/public_dependency_closure.json',bytes=(out/'public_dependency_closure.json').stat().st_size,sha256=sha(out/'public_dependency_closure.json')))
    records.sort(key=lambda v:v['path'])
    archive=package/'evidence.tar.gz'
    with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as tar:
        for record in records:
            info=tarfile.TarInfo(record['path']);info.size=record['bytes'];info.mtime=0;info.mode=0o644
            with (root/record['path']).open('rb') as file:tar.addfile(info,file)
    parts=split_archive(archive)
    value=dict(schema='round111-limited-exact-byte-carrier-v1',archive_path='evidence.tar.gz',archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
        parts=parts,single_blob_limit_bytes=SINGLE_BLOB_LIMIT,part_bytes=PART_BYTES,files=records,
        public_dependencies=[v for v in dependencies if v['path']=='scripts/round110_public.py'],
        retained_history_authorities=dependencies,no_PE_DLL_license_or_credentials=True,old_main_raw_copied=False,
        source_bindings=candidate['source_bindings'],reader_path='scripts/round111_reader.py',reader_SHA=sha(root/'scripts/round111_reader.py'),
        restore_source_SHA=sha(__file__),evidence_layer='R110_MAIN_36_PLUS_R111_SEED_6',Optimize=0,IIS=0)
    validate_carrier(package,value);write(package/'manifest.json',value)
    write(out/'public_pack_receipt.json',dict(exit_code=0,engineering=True,seconds=time.perf_counter()-begin,files=len(records),
        archive_bytes=archive.stat().st_size,archive_SHA=sha(archive),manifest_SHA=sha(package/'manifest.json'),source_SHA=sha(__file__),Optimize=0))
    print(json.dumps(dict(files=len(records),archive_bytes=value['archive_bytes'],parts=len(parts))),flush=True)

for operation in ('export','restore'):
    source=inspect.getsource(getattr(prior,operation)).replace('scripts/round110_public.py','scripts/round111_public.py').replace('scripts/round110_final_reader.py','scripts/round111_reader.py')
    namespace=dict(vars(prior),ROUND=ROUND,__file__=__file__)
    exec(compile(source,__file__+'::inherited_'+operation,'exec'),namespace)
    globals()[operation]=namespace[operation]

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('pack','export','restore'));p.add_argument('--root');p.add_argument('--public-root');p.add_argument('--out');a=p.parse_args()
    if a.operation=='pack':pack(a.root)
    elif a.operation=='export':export(a.root,a.out)
    else:restore(a.public_root,a.out)
