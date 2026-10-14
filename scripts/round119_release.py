"""Current-only safe scientific carrier, one export, and empty-root rebuild.

Publication engineering never loads a solver or restores a predecessor carrier.
Actual recovery, extra-review and remote receipts remain outside this payload.
"""
from round119_support import ROOT,OUT,read,write,sha
from pathlib import Path
import argparse,ast,csv,gzip,io,json,subprocess,tarfile,time
import publication_security as security
from round117_release import Parts

ROUND='results/unified_exact_round119'
FORBIDDEN={'.exe','.dll','.lic','.pyd','.a','.whl','.pyc','.html','.htm'}

def closure(root):
    pending=['read_round119','round119_release','round119_finish_report','round119_extra_review'];names=set()
    while pending:
        name=pending.pop();p=root/'scripts'/(name+'.py')
        if name in names or not p.is_file():continue
        names.add(name)
        for n in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules=[x.name for x in n.names] if isinstance(n,ast.Import) else [n.module] if isinstance(n,ast.ImportFrom) else []
            pending.extend(m for m in modules if m and (root/'scripts'/(m+'.py')).is_file())
    return {root/'scripts'/(n+'.py') for n in names}

def inventory(root):
    root=Path(root).resolve();out=root/ROUND;files=closure(root)
    candidate=read(out/'candidate_identity.json');production=read(out/'production_identity.json')
    files.update(root/n for n in candidate['helpers']);files.update(root/n for n in production['source_bindings'])
    inputs=read(out/'input_manifest.json')
    roles=inputs['development_roles']+[inputs['conditional_confirmation_role']]+inputs['qualification_roles']
    files.update(root/p['input_path'] for p in roles);files.add(root/inputs['enum_fixture']['input_path'])
    files.update(root/n for n in ['tests/round119_lifecycle_qualification.cpp','scripts/qualify_round119_lifecycle.py',
        'scripts/round119_math_completion.py','scripts/round119_reference_repair.py'])
    # Small schema/identity authorities required by inherited import/contract
    # code; this does not copy an old raw campaign or any old full carrier.
    names={'preregistration.json','protocol.json','helper_paths.json','scope_contract.json','fixed_manifest.json'}
    files.update(p for p in (root/'results').glob('unified_exact_round*/*.json') if p.name in names and p.parent.name!=Path(ROUND).name)
    for r,names2 in [('117',['publication_policy.md','final_report.md','scope_contract.json','safe_restore.md']),
                     ('118',['paper_algorithm_spec.md','paper_claim_evidence_map.md','final_report.md'])]:
        files.update(root/f'results/unified_exact_round{r}'/n for n in names2)
    # Only the explicitly cited R118 replay authorities and its actual right-LP
    # models, rather than the complete four-arm historical campaign.
    old=root/'results/unified_exact_round118'
    files.add(old/'reconstruction01/own_UB_flow.csv')
    for row in read(out/'preflight_replay.json')['arms']:
        stem='02_N40-R1-S_S0_M-B' if row['arm']=='M-B' else '04_N40-R1-S_S0_ENS-C'
        d=old/'campaign/raw'/stem
        files.update(d/n for n in ['producer_receipt.json','launch.json','observations.json','completion.json',
            'native_end_receipt.json','process_start_marker.json','external/lp_status_ledger.csv'])
        import round108_reader as core
        files.add(core.portable(root,row['source_scope']['model_path']))
    excluded={'compact_evidence','delivery','restored_reconstruction'}
    later={'public_pack_receipt.json','public_dependency_closure.json','initial_publication_observation.json','delivery_summary.md'}
    for p in out.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(out).as_posix()
        if any(rel==n or rel.startswith(n+'/') for n in excluded):continue
        if rel in later or rel.startswith(('engineering/public_export','review/extra_review')):continue
        files.add(p)
    if (out/'public_dependency_closure.json').is_file():files.add(out/'public_dependency_closure.json')
    for p in files:
        assert p.is_file(),('missing required current dependency',str(p))
        assert p.resolve().is_relative_to(root) and p.suffix.lower() not in FORBIDDEN
        assert '__pycache__' not in p.parts and 'build' not in p.relative_to(root).parts
        assert p.stat().st_size<=security.MAX_MEMBER_BYTES
    return root,out,sorted(files)

def preflight(root):
    tick=time.perf_counter();root,out,files=inventory(root);csv.field_size_limit(64*1024*1024)
    maximum=0;location=None;count=0
    for p in files:
        if p.suffix!='.csv':continue
        count+=1
        with p.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.reader(f):
                for cell in row:
                    if len(cell)>maximum:maximum=len(cell);location=p.relative_to(root).as_posix()
    assert maximum<64*1024*1024
    write(out/'public_dependency_closure.json',dict(files=len(files),raw_bytes=sum(p.stat().st_size for p in files),
        scripts=sorted(p.relative_to(root).as_posix() for p in closure(root)),source_files=len(read(out/'production_identity.json')['source_bindings']),
        CSV_files=count,maximum_CSV_field_characters=maximum,maximum_CSV_field_path=location,CSV_field_capacity=64*1024*1024,
        only_current_panel_and_small_named_authorities=True,full_old_carriers_copied=False,old_polluted_carrier_or_HTML=False,
        PE_DLL_license_credentials_excluded=True,original_root_fallback=False,later_receipts_outside_scientific_payload=True,
        Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(files=len(files),raw_bytes=sum(p.stat().st_size for p in files),maximum_CSV_field=maximum)))

def pack(root):
    tick=time.perf_counter();root,out,files=inventory(root);assert (out/'public_dependency_closure.json').is_file()
    report=security.scan_items((p.relative_to(root).as_posix(),p.read_bytes()) for p in files)
    write(out/'delivery/payload_scan.json',report);assert report['passed'],'actual payload failed inherited security gate'
    directory=out/'compact_evidence';directory.mkdir(exist_ok=False);writer=Parts(directory);entries={}
    try:
        with gzip.GzipFile(fileobj=writer,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|') as arc:
                for p in files:
                    name=p.relative_to(root).as_posix();security.Scanner.member_name(name);data=p.read_bytes()
                    entries[name]=dict(SHA=security.sha(data),bytes=len(data))
                    m=tarfile.TarInfo(name);m.size=len(data);m.mode=0o644;m.mtime=0;arc.addfile(m,io.BytesIO(data))
    finally:writer.finish()
    parts=[dict(path=p.relative_to(root).as_posix(),SHA=sha(p),bytes=p.stat().st_size) for p in writer.paths]
    write(directory/'manifest.json',dict(schema='round119-current-safe-evidence-v1',files=entries,parts=parts,
        only_current_raw_and_named_safe_authorities=True,full_old_carriers_copied=False,original_root_fallback=False,
        PE_DLL_license_credentials_polluted_HTML_excluded=True,later_receipts_outside_scientific_payload=True,Optimize=0,native_starts=0))
    carrier=security.scan_items(security.file_items(root,[directory.relative_to(root).as_posix()]))
    write(out/'delivery/carrier_scan.json',carrier);assert carrier['passed']
    receipt=dict(files=len(entries),raw_bytes=sum(v['bytes'] for v in entries.values()),parts=parts,
        compressed_bytes=sum(v['bytes'] for v in parts),manifest_SHA=sha(directory/'manifest.json'),
        complete_actual_unpacked_carrier_scanned=True,engineering_seconds=time.perf_counter()-tick,Optimize=0,native_starts=0)
    write(out/'public_pack_receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='parts'}),flush=True)

def restore(root,commit,destination):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND;dest=Path(destination).resolve()
    assert not dest.exists() and dest!=root and not dest.is_relative_to(root)
    export=out/'engineering/public_export01';export.mkdir(parents=True,exist_ok=False)
    manifest=read(out/'compact_evidence/manifest.json');assert manifest['schema']=='round119-current-safe-evidence-v1'
    names=[ROUND+'/compact_evidence/manifest.json']+[p['path'] for p in manifest['parts']]
    archive=export/'public_carrier.tar'
    subprocess.run(['git','archive','--format=tar','--output='+str(archive),commit,'--',*names],cwd=root,check=True)
    carrier=export/'carrier';carrier.mkdir()
    with tarfile.open(archive) as arc:arc.extractall(carrier,filter='data')
    assert read(carrier/ROUND/'compact_evidence/manifest.json')==manifest
    data=[]
    for part in manifest['parts']:
        p=(carrier/part['path']).resolve();assert p.is_relative_to(carrier)
        raw=p.read_bytes();assert len(raw)==part['bytes'] and security.sha(raw)==part['SHA'];data.append(raw)
    dest.mkdir();restored=set()
    with tarfile.open(fileobj=io.BytesIO(b''.join(data)),mode='r|gz') as arc:
        for m in arc:
            security.Scanner.member_name(m.name);assert m.isfile() and m.name not in restored
            expected=manifest['files'][m.name];raw=arc.extractfile(m).read()
            assert m.size==len(raw)==expected['bytes'] and security.sha(raw)==expected['SHA']
            p=(dest/m.name).resolve();assert p.is_relative_to(dest);p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(raw)
            restored.add(m.name)
    assert restored==set(manifest['files'])
    write(out/'delivery/public_export_receipt.json',dict(commit=commit,one_actual_git_archive=True,archive_SHA=sha(archive),
        manifest_SHA=sha(out/'compact_evidence/manifest.json'),parts_verified=True,original_root_fallback=False,Optimize=0,native_starts=0))
    receipt=dict(commit=commit,fresh_empty_root=str(dest),files_verified=len(restored),all_member_hashes_equal=True,
        original_root_fallback=False,one_restore=True,engineering_seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        receipt_does_not_cover_future_reconstruction_or_commits=True)
    write(out/'delivery/public_restore_receipt.json',receipt);print(json.dumps(receipt),flush=True)

def restored_check(root):
    root=Path(root).resolve();assert ROOT==root;tick=time.perf_counter()
    import read_round119 as reader
    assert reader.ROOT==root
    values=[]
    for n in [1,2,3,4]:
        expected=root/ROUND/'reconstruction'/f'group{n:02d}'/'current_core.json'
        if not expected.exists():
            assert n==4 and read(root/ROUND/'confirmation_cancellation.json')['all_three_unrun'];continue
        actual=reader.rebuild_group(n,root/ROUND/'restored_reconstruction'/f'group{n:02d}')
        assert actual==read(expected),('restored current core differs',n);values.append(actual)
    expected_gate=read(root/ROUND/'development_admission.json')
    assert reader.development_admission()==expected_gate
    assert not list(root.rglob('*.exe')) and not list(root.rglob('*.dll'))
    report=dict(passed=True,current_groups=len(values),formal_arms=sum(len(v['arms']) for v in values),
        exact_current_core_equal=True,development_gate_equal=True,all_imports_and_evidence_from_restored_root=True,
        original_root_fallback=False,original_worktree_files_read=0,native_PE_DLL_absent=True,Optimize=0,native_starts=0,
        engineering_seconds=time.perf_counter()-tick,receipt_does_not_attest_future_commit=True)
    write(root/ROUND/'restored_check.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','pack','restore','restored-check'])
    p.add_argument('--root',required=True);p.add_argument('--commit');p.add_argument('--destination');a=p.parse_args()
    if a.mode=='preflight':preflight(a.root)
    elif a.mode=='pack':pack(a.root)
    elif a.mode=='restore':restore(a.root,a.commit,a.destination)
    else:restored_check(a.root)
