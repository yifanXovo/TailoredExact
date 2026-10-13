"""One current safe carrier, one Git export, one fresh-root reconstruction.

Publication engineering only: no optimizer, unsafe acquisition or old carrier.
Later restore/review/remote observations are outside the scientific payload.
"""
from pathlib import Path
import argparse,ast,csv,gzip,io,json,os,shutil,subprocess,tarfile,time
import publication_security as security
from round117_release import Parts
from round118_data import ROOT,OUT,read,write,sha

ROUND='results/unified_exact_round118'
FORBIDDEN={'.exe','.dll','.lic','.pyd','.a','.whl','.pyc'}

def closure(root):
    pending=['read_round118','round118_release','round118_finish_report'];names=set()
    while pending:
        name=pending.pop();path=root/'scripts'/(name+'.py')
        if name in names or not path.is_file():continue
        names.add(name)
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            modules=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending.extend(m for m in modules if m and (root/'scripts'/(m+'.py')).is_file())
    return {root/'scripts'/(name+'.py') for name in names}

def inventory(root):
    root=Path(root).resolve();out=root/ROUND;files=closure(root)
    candidate=read(out/'candidate_identity.json');production=read(out/'production_identity.json')
    files.update(root/name for name in candidate['helpers'])
    files.update(root/name for name in production['source_bindings'])
    files.update(p for p in (root/'reference/round118_positive').rglob('*') if p.is_file())
    # Only the small static source and the actual finite V20 M-B fixture are
    # dependencies; the much larger old cold campaign is intentionally absent.
    r116=root/'results/unified_exact_round116'
    files.update(p for p in (r116/'source').rglob('*') if p.is_file())
    files.add(r116/'projection_contract.json')
    files.add(r116/'campaign/group01/identity.json')
    old=read(r116/'campaign/group01/identity.json')
    mb=next(l for l in old['launches'] if l['arm']=='M-B')
    import round108_reader as core
    files.update(p for p in core.portable(root,mb['destination']).rglob('*') if p.is_file())
    files.add(root/mb['panel']['input_path'])
    files.update(root/name for name in read(out/'finite_Start_authority.json')['members'])
    files.update(root/name for name in ['reference/round100_confirmation/H100.txt',
        'results/unified_exact_round94/preregistration.json'])
    # Accurate security/scope history is a small citation, not a copy of all
    # predecessor result bundles or source web runtime material.
    r117=root/'results/unified_exact_round117'
    files.update(r117/name for name in ['final_report.md','security_incident.md','safe_restore.md',
        'scope_contract.json','paper_scope_and_evidence.md','next_experiment_spec.md'])
    excluded={'compact_evidence','delivery','reports_blocked','safe_dependency_receipt.json'}
    later={'initial_publication_observation.json','public_pack_receipt.json','public_dependency_closure.json'}
    for path in out.rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(out).as_posix()
        if any(rel==name or rel.startswith(name+'/') for name in excluded):continue
        if rel in later or rel.startswith('engineering/public_export'):continue
        files.add(path)
    # The public dependency receipt is included if it has already been formed;
    # future receipts never claim to cover their own forthcoming Git commit.
    if (out/'public_dependency_closure.json').is_file():files.add(out/'public_dependency_closure.json')
    for path in files:
        assert path.is_file(),('required public dependency absent',str(path))
        assert path.resolve().is_relative_to(root) and path.suffix.lower() not in FORBIDDEN
        assert '__pycache__' not in path.parts and 'build' not in path.relative_to(root).parts
        assert path.stat().st_size<=security.MAX_MEMBER_BYTES,('member exceeds inherited scanner limit',str(path))
    return root,out,sorted(files)

def preflight(root):
    tick=time.perf_counter();root,out,files=inventory(root)
    csv.field_size_limit(64*1024*1024);maximum=0;location=None;csv_files=0
    for path in files:
        if path.suffix!='.csv':continue
        csv_files+=1
        with path.open(encoding='utf-8-sig',newline='') as file:
            for row in csv.reader(file):
                for cell in row:
                    if len(cell)>maximum:maximum=len(cell);location=path.relative_to(root).as_posix()
    assert maximum<64*1024*1024
    write(out/'public_dependency_closure.json',dict(files=len(files),raw_bytes=sum(p.stat().st_size for p in files),
        scripts=sorted(p.relative_to(root).as_posix() for p in closure(root)),source_files=len(read(out/'production_identity.json')['source_bindings']),
        current_helper_hashes=read(out/'candidate_identity.json')['helpers'],CSV_files=csv_files,
        maximum_CSV_field_characters=maximum,maximum_CSV_field_path=location,CSV_field_capacity=64*1024*1024,
        old_full_carrier_copied=False,old_cold_fixture_not_copied=True,small_safe_MB_fixture=True,
        PE_DLL_solver_license_credentials_excluded=True,original_root_fallback=False,
        later_restore_review_remote_receipts_outside_payload=True,native_starts=0,Optimize=0,
        engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(public_files=len(files),raw_bytes=sum(p.stat().st_size for p in files),maximum_CSV_field=maximum)))

def pack(root):
    tick=time.perf_counter();root,out,files=inventory(root)
    assert (out/'public_dependency_closure.json').is_file()
    safety=security.scan_items((p.relative_to(root).as_posix(),p.read_bytes()) for p in files)
    write(out/'delivery/payload_scan.json',safety)
    assert safety['passed'],'inherited publication gate rejected actual payload; do not bypass'
    directory=out/'compact_evidence';directory.mkdir(exist_ok=False)
    writer=Parts(directory);entries={}
    try:
        with gzip.GzipFile(fileobj=writer,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|') as archive:
                for path in files:
                    name=path.relative_to(root).as_posix();security.Scanner.member_name(name)
                    data=path.read_bytes();entries[name]=dict(SHA=security.sha(data),bytes=len(data))
                    member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o644;member.mtime=0
                    archive.addfile(member,io.BytesIO(data))
    finally:writer.finish()
    parts=[dict(path=p.relative_to(root).as_posix(),SHA=sha(p),bytes=p.stat().st_size) for p in writer.paths]
    write(directory/'manifest.json',dict(schema='round118-current-safe-evidence-v1',files=entries,parts=parts,
        PE_DLL_solver_license_credentials_excluded=True,old_contaminated_carrier_dependency=False,
        full_old_carriers_copied=False,original_worktree_fallback=False,
        later_restore_review_remote_receipts_outside_scientific_payload=True,native_starts=0,Optimize=0))
    # Scan the complete actual compressed stream, not merely its file hashes.
    carrier=security.scan_items(security.file_items(root,[directory.relative_to(root).as_posix()]))
    write(out/'delivery/carrier_scan.json',carrier);assert carrier['passed']
    receipt=dict(files=len(entries),raw_bytes=sum(x['bytes'] for x in entries.values()),parts=parts,
        compressed_bytes=sum(x['bytes'] for x in parts),manifest_SHA=sha(directory/'manifest.json'),
        complete_unpacked_carrier_scanned=True,engineering_seconds=time.perf_counter()-tick,native_starts=0,Optimize=0)
    write(out/'public_pack_receipt.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='parts'}),flush=True)

def restore(root,commit,destination):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND;destination=Path(destination).resolve()
    assert root!=destination and not destination.is_relative_to(root) and not destination.exists()
    export=out/'engineering/public_export01';export.mkdir(parents=True,exist_ok=False)
    manifest=read(out/'compact_evidence/manifest.json');assert manifest['schema']=='round118-current-safe-evidence-v1'
    names=[ROUND+'/compact_evidence/manifest.json']+[p['path'] for p in manifest['parts']]
    target=export/'public_carrier.tar'
    subprocess.run(['git','archive','--format=tar','--output='+str(target),commit,'--',*names],cwd=root,check=True)
    carrier=export/'carrier';carrier.mkdir()
    with tarfile.open(target) as archive:archive.extractall(carrier,filter='data')
    exported_manifest=read(carrier/ROUND/'compact_evidence/manifest.json');assert exported_manifest==manifest
    data=[]
    for part in manifest['parts']:
        path=(carrier/part['path']).resolve();assert path.is_relative_to(carrier)
        body=path.read_bytes();assert security.sha(body)==part['SHA'] and len(body)==part['bytes'];data.append(body)
    destination.mkdir();restored=set()
    with tarfile.open(fileobj=io.BytesIO(b''.join(data)),mode='r|gz') as archive:
        for member in archive:
            security.Scanner.member_name(member.name);assert member.isfile() and member.name not in restored
            expected=manifest['files'][member.name];body=archive.extractfile(member).read()
            assert member.size==expected['bytes']==len(body) and security.sha(body)==expected['SHA']
            path=(destination/member.name).resolve();assert path.is_relative_to(destination)
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as file:file.write(body)
            restored.add(member.name)
    assert restored==set(manifest['files'])
    write(out/'delivery/public_export_receipt.json',dict(commit=commit,actual_git_archive=True,one_export=True,
        archive_SHA=sha(target),manifest_SHA=sha(out/'compact_evidence/manifest.json'),parts_verified=True,
        original_root_fallback=False,native_starts=0,Optimize=0,exported_unix=time.time()))
    receipt=dict(commit=commit,restored_root=str(destination),fresh_empty_directory=True,one_restore=True,
        files_verified=len(restored),all_manifest_hashes_equal=True,original_root_fallback=False,
        engineering_seconds=time.perf_counter()-tick,native_starts=0,Optimize=0,
        receipt_does_not_cover_future_reconstruction=True)
    write(out/'delivery/public_restore_receipt.json',receipt);print(json.dumps(receipt),flush=True)

def restored_check(root):
    """Run solely from the new root, including exported expected reports."""
    root=Path(root).resolve();tick=time.perf_counter();assert ROOT==root
    import read_round118 as reader
    formal=reader.rebuild(root,root/ROUND/'restored_reconstruction')
    expected=read(root/ROUND/'reconstruction01/current_core.json');assert formal==expected
    qualification=reader.rebuild(root,root/ROUND/'restored_qualification',True,'qualification/final')
    assert qualification==read(root/ROUND/'qualification/post03/reconstructed/current_core.json')
    # Compare in-memory generation arithmetic; do not create a second input.
    import round118_data as data
    assert data.ROOT==root
    stations=data.source_check();selected=data.selection(stations);landscape=data.landscape(selected,stations)
    assert selected==read(root/'reference/round118_positive/N40-R1-S_selection.json')
    assert landscape==read(root/'reference/round118_positive/N40-R1-S_landscape.json')
    text=data.old.instance_text(landscape,data.ROLE['M'],data.ROLE['Q_vector'][0]).splitlines()
    text[0]='40 4 '+json.dumps(data.ROLE['Q_vector'])
    expected_bytes=('\n'.join(text).rstrip()+'\n').encode()
    assert expected_bytes==(root/'reference/round118_positive/N40-R1-S.txt').read_bytes()
    report=dict(passed=True,formal_arms=4,pairs=6,qualification_arms=2,exact_current_core_equal=True,
        exact_H100_core_equal=True,source865_rows_checked=True,input_arithmetic_equal_in_memory=True,
        new_input_files_created=0,all_imports_and_scientific_dependencies_from_restored_root=True,
        original_root_fallback=False,original_worktree_files_read=0,
        native_PE_DLL_absent=True,native_starts=0,Optimize=0,engineering_seconds=time.perf_counter()-tick)
    assert not list(root.rglob('*.exe')) and not list(root.rglob('*.dll'))
    write(root/ROUND/'restored_check.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['preflight','pack','restore','restored-check'])
    parser.add_argument('--root',required=True);parser.add_argument('--commit');parser.add_argument('--destination')
    args=parser.parse_args()
    if args.mode=='preflight':preflight(args.root)
    elif args.mode=='pack':pack(args.root)
    elif args.mode=='restore':restore(args.root,args.commit,args.destination)
    else:restored_check(args.root)
