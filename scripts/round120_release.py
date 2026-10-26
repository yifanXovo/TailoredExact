"""Current R120 safe carrier, one public export and empty-root reconstruction.

No solver import or predecessor carrier restore. Later recovery/review/remote
receipts stay outside the scientific payload they examine.
"""
from round120_common import ROOT,OUT,read,write,sha
from pathlib import Path
import argparse,ast,csv,gzip,io,json,subprocess,sys,tarfile,time
import publication_security as security
from round117_release import Parts
ROUND='results/unified_exact_round120'
FORBIDDEN={'.exe','.dll','.lic','.pyd','.a','.whl','.pyc','.html','.htm'}
def closure(root):
    pending=['read_round120','round120_finish_report','round120_release','round120_extra_review'];found=set()
    while pending:
        name=pending.pop();p=root/'scripts'/(name+'.py')
        if name in found or not p.exists():continue
        found.add(name)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending.extend(n for n in modules if n and (root/'scripts'/(n+'.py')).is_file())
    return {root/'scripts'/(name+'.py') for name in found}
def inventory(root):
    root=Path(root).resolve();out=root/ROUND;files=closure(root)
    candidate=read(out/'candidate_identity.json');files.update(root/n for n in candidate['source_bindings']);files.update(root/n for n in candidate['helpers'])
    files.update(root/'scripts'/n for n in ['round120_lifecycle.py','publication_security.py'])
    files.update(root/'tests'/n for n in ['round119_lifecycle_qualification.cpp','round120_qualification.cpp',
        'round120_qualification_support.hpp','round120_lp_diagnostics.cpp'])
    inputs=read(out/'input_manifest.json')
    for p in inputs['core_roles']+[inputs['conditional_role']]+inputs['qualification_roles']+[inputs['enum_fixture']]:files.add(root/p['input_path'])
    # Small safe schema authorities needed by inherited helpers; never a prior
    # raw campaign, full old carrier, HTML or licensed runtime.
    authorities={'preregistration.json','protocol.json','helper_paths.json','scope_contract.json','fixed_manifest.json'}
    files.update(p for p in (root/'results').glob('unified_exact_round*/*.json') if p.name in authorities and p.parent.name!='unified_exact_round120')
    for round_number,names in [(117,['publication_policy.md','safe_restore.md','scope_contract.json']),
        (118,['paper_algorithm_spec.md','paper_claim_evidence_map.md']),
        (119,['final_report.md','mathematical_contract.md','history_and_hypothesis.md','resource_summary.json','qualification/math_completion.json','review/extra_review.json'])]:
        files.update(root/f'results/unified_exact_round{round_number}'/n for n in names)
    for folder,names in [('gf_decomposition_single_tree_round41',['final_report.md','st_k2_mathematical_formulation.md']),
        ('gf_decomposition_architecture_optimization_round42',['final_report.md','generalized_segmented_formulation.md','family_a_iteration_log.md','family_b_iteration_log.md','family_c_iteration_log.md'])]:
        files.update(root/'results'/folder/n for n in names)
    excluded={'compact_evidence','delivery','restored_reconstruction'}
    later={'public_pack_receipt.json','public_dependency_closure.json','delivery_summary.md'}
    for p in out.rglob('*'):
        if not p.is_file() or p.suffix.lower() in FORBIDDEN:continue
        rel=p.relative_to(out).as_posix()
        if rel in later or any(rel.startswith(n+'/') for n in excluded):continue
        if rel.startswith(('review/extra_review','engineering/public_export')):continue
        files.add(p)
    if (out/'public_dependency_closure.json').exists():files.add(out/'public_dependency_closure.json')
    for p in files:
        assert p.is_file(),('missing finite safe dependency',str(p))
        assert p.resolve().is_relative_to(root) and p.suffix.lower() not in FORBIDDEN
        assert 'build' not in p.relative_to(root).parts and '__pycache__' not in p.parts
        assert p.stat().st_size<=security.MAX_MEMBER_BYTES
    return root,out,sorted(files)
def preflight(root):
    tick=time.perf_counter();root,out,files=inventory(root);csv.field_size_limit(64*1024*1024);maximum=0
    for p in files:
        if p.suffix!='.csv':continue
        with p.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.reader(f):maximum=max(maximum,max(map(len,row),default=0))
    assert maximum<64*1024*1024
    write(out/'public_dependency_closure.json',dict(files=len(files),raw_bytes=sum(p.stat().st_size for p in files),
        scripts=sorted(p.relative_to(root).as_posix() for p in closure(root)),CSV_capacity=64*1024*1024,maximum_CSV_field=maximum,
        current_raw_sources_and_finite_named_authorities_only=True,previous_carriers_or_campaigns_restored=False,
        PE_DLL_license_HTML_credentials_excluded=True,later_receipts_outside_scientific_payload=True,Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(files=len(files),raw_bytes=sum(p.stat().st_size for p in files),maximum_CSV_field=maximum)),flush=True)
def pack(root):
    tick=time.perf_counter();root,out,files=inventory(root);assert (out/'public_dependency_closure.json').exists()
    report=security.scan_items((p.relative_to(root).as_posix(),p.read_bytes()) for p in files)
    write(out/'delivery/payload_scan.json',report);assert report['passed'],'actual payload security gate'
    directory=out/'compact_evidence';directory.mkdir(exist_ok=False);writer=Parts(directory);entries={}
    try:
        with gzip.GzipFile(fileobj=writer,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|') as arc:
                for p in files:
                    name=p.relative_to(root).as_posix();security.Scanner.member_name(name);data=p.read_bytes()
                    entries[name]=dict(SHA=security.sha(data),bytes=len(data));member=tarfile.TarInfo(name)
                    member.size=len(data);member.mode=0o644;member.mtime=0;arc.addfile(member,io.BytesIO(data))
    finally:writer.finish()
    parts=[dict(path=p.relative_to(root).as_posix(),SHA=sha(p),bytes=p.stat().st_size) for p in writer.paths]
    write(directory/'manifest.json',dict(schema='round120-current-safe-evidence-v1',files=entries,parts=parts,
        current_raw_sources_and_finite_named_authorities_only=True,previous_carriers_or_campaigns_restored=False,
        PE_DLL_license_credentials_HTML_excluded=True,original_root_fallback=False,later_receipts_outside_payload=True,Optimize=0))
    carrier=security.scan_items(security.file_items(root,[directory.relative_to(root).as_posix()]))
    write(out/'delivery/carrier_scan.json',carrier);assert carrier['passed']
    assert carrier['archive_members']>=len(entries),'complete decompressed carrier members were not scanned'
    write(out/'public_pack_receipt.json',dict(files=len(entries),raw_bytes=sum(v['bytes'] for v in entries.values()),parts=parts,
        manifest_SHA=sha(directory/'manifest.json'),complete_unpacked_carrier_scanned=True,Optimize=0,native_starts=0,
        engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(files=len(entries),parts=len(parts),compressed_bytes=sum(p['bytes'] for p in parts))),flush=True)
def restore(root,commit,destination):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND;dest=Path(destination).resolve()
    assert not dest.exists() and not dest.is_relative_to(root)
    export=out/'engineering/public_export01';export.mkdir(parents=True,exist_ok=False)
    manifest=read(out/'compact_evidence/manifest.json');names=[ROUND+'/compact_evidence/manifest.json']+[p['path'] for p in manifest['parts']]
    archive=export/'public_carrier.tar';subprocess.run(['git','archive','--format=tar','--output='+str(archive),commit,'--',*names],cwd=root,check=True)
    carrier=export/'carrier';carrier.mkdir()
    with tarfile.open(archive) as arc:arc.extractall(carrier,filter='data')
    published_manifest=carrier/ROUND/'compact_evidence/manifest.json'
    assert read(published_manifest)==manifest
    data=[]
    for part in manifest['parts']:
        p=(carrier/part['path']).resolve();assert p.is_relative_to(carrier)
        raw=p.read_bytes();assert len(raw)==part['bytes'] and security.sha(raw)==part['SHA'];data.append(raw)
    dest.mkdir();restored=set()
    with tarfile.open(fileobj=io.BytesIO(b''.join(data)),mode='r|gz') as arc:
        for member in arc:
            security.Scanner.member_name(member.name);assert member.isfile() and member.name not in restored
            expected=manifest['files'][member.name];raw=arc.extractfile(member).read()
            assert len(raw)==member.size==expected['bytes'] and security.sha(raw)==expected['SHA']
            p=(dest/member.name).resolve();assert p.is_relative_to(dest);p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(raw)
            restored.add(member.name)
    assert restored==set(manifest['files'])
    write(out/'delivery/public_export_receipt.json',dict(commit=commit,one_actual_public_git_archive=True,archive_SHA=sha(archive),
        manifest_SHA=sha(published_manifest),measured_worktree_manifest_SHA=sha(out/'compact_evidence/manifest.json'),
        manifest_semantics_equal=True,manifest_identity_from_actual_git_export=True,
        parts_verified=True,original_root_fallback=False,Optimize=0))
    write(out/'delivery/public_restore_receipt.json',dict(commit=commit,fresh_empty_root=str(dest),files_verified=len(restored),
        all_member_hashes_equal=True,one_restore=True,original_root_fallback=False,Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick,
        receipt_does_not_attest_future_reconstruction_or_commits=True))
    print(json.dumps(dict(restored_files=len(restored),empty_root=str(dest))),flush=True)
def normalize(value,roots):
    if isinstance(value,dict):return {k:normalize(v,roots) for k,v in value.items()}
    if isinstance(value,list):return [normalize(v,roots) for v in value]
    if isinstance(value,str):
        for root in roots:
            prefix=str(root)
            for form in [prefix,prefix.replace('\\','/'),prefix.replace('/','\\')]:
                if value.startswith(form):return '<ROOT>'+value[len(form):].replace('\\','/')
    return value
def restored_check(root):
    tick=time.perf_counter();root=Path(root).resolve();assert ROOT==root
    opened=set();runtime=Path(sys.base_prefix).resolve()
    def read_boundary(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        value=args[0].decode() if isinstance(args[0],bytes) else args[0]
        path=Path(value).resolve()
        assert path.is_relative_to(root) or path.is_relative_to(runtime),('restore attempted external file access',str(path))
        if path.is_relative_to(root):opened.add(path.relative_to(root).as_posix())
    sys.addaudithook(read_boundary)
    import read_round120 as reader
    assert reader.ROOT==root
    measured=read(root/ROUND/'initialization_receipt.json')['worktree'];values=[]
    for n in [1,2,3]:
        path=root/ROUND/f'reconstruction/group{n:02d}/current_core.json'
        if not path.exists():assert n==3 and read(root/ROUND/'N40_cancellation.json')['all_four_unrun'];continue
        expected=read(path);actual=reader.rebuild_group(n,root/ROUND/f'restored_reconstruction/group{n:02d}')
        assert normalize(actual,[root,measured])==normalize(expected,[root,measured]),('restored current core mismatch',n)
        values.append(actual)
    old=read(root/ROUND/'core_admission.json');actual=reader.admission()
    assert normalize(old,[root,measured])==normalize(actual,[root,measured])
    assert not list(root.rglob('*.exe')) and not list(root.rglob('*.dll'))
    local_modules=[]
    for name,module in list(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if not path:continue
        path=Path(path).resolve()
        if path.is_relative_to(runtime):continue
        assert path.is_relative_to(root),('restore imported external helper',name,str(path))
        local_modules.append(dict(module=name,path=path.relative_to(root).as_posix()))
    write(root/ROUND/'restored_check.json',dict(passed=True,current_groups=len(values),formal_arms=sum(len(v['arms']) for v in values),
        all_current_core_numbers_proofs_Starts_calls_H_and_pairs_equal=True,
        normalization='only measured/restored absolute root prefixes; no numerical, clock, model or logical fields removed',
        all_helpers_and_evidence_from_empty_root=True,original_worktree_fallback=False,native_PE_DLL_absent=True,
        actual_file_access_boundary_enforced=True,allowed_external_files='Python runtime and standard library only',
        current_root_opened_paths=sorted(opened),current_root_modules=local_modules,
        Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick,receipt_does_not_attest_future_commit=True))
    print(json.dumps(dict(passed=True,formal_arms=sum(len(v['arms']) for v in values))),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','pack','restore','restored-check']);p.add_argument('--root',required=True)
    p.add_argument('--commit');p.add_argument('--destination');a=p.parse_args()
    {'preflight':lambda:preflight(a.root),'pack':lambda:pack(a.root),
     'restore':lambda:restore(a.root,a.commit,a.destination),'restored-check':lambda:restored_check(a.root)}[a.mode]()
