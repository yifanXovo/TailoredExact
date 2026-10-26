"""One current-only carrier, one Git export, one fresh-root restoration.

No native optimization or original-root reader fallback. Parts and extraction
reuse the existing Round115 implementation; old performance carriers are not
included. Later actual restore/review/remote receipts are outside this payload.
"""
import argparse, ast, csv, gzip, io, json, shutil, subprocess, tarfile, time
from pathlib import Path
import round108_reader as core
from read_round116 import ROUND
from round115_delivery import Parts

def closure(root):
    pending=['read_round116','read_round116_reporting','round116_analysis','round116_report','round116_blocked','round116_impact',
        'round116_source_check','round116_final_review','round116_restore_check','round116_evidence_organize','round116_delivery','round116_review',
        'round116_campaign','round116_data','round116_prepare','qualify_round116','qualify_round116_post']
    names=set()
    while pending:
        name=pending.pop();p=root/'scripts'/(name+'.py')
        if name in names or not p.is_file():continue
        names.add(name)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending += [m for m in modules if m and (root/'scripts'/(m+'.py')).is_file()]
    return [root/'scripts'/(n+'.py') for n in sorted(names)]

def inventory(root):
    root=Path(root).resolve();out=root/ROUND
    files=set(closure(root))
    files.update(root/n for n in core.read(out/'candidate_identity.json')['helpers'])
    files.update(root/n for n in core.read(out/'production_identity.json')['source_bindings'])
    files.update((root/'reference/round116_external').rglob('*'))
    files.update(root/n for n in ['reference/round100_confirmation/H100.txt',
        'reference/round109_geographic/G100-R2.txt','results/unified_exact_round94/preregistration.json'])
    excluded={'compact_evidence','reconstruction01','reconstruction02','engineering','review/whole_goal01'}
    for p in out.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(out).as_posix()
        if any(rel==n or rel.startswith(n+'/') for n in excluded):continue
        if rel.startswith('public_') or rel.startswith('publication_') or rel.startswith('remote_'):continue
        files.add(p)
    # Preserve the one offline engineering failure and exact previous version,
    # and known environment incidents, without intermediate exports/temp blobs.
    for p in (out/'engineering').rglob('*'):
        if p.is_file() and not any(x in p.relative_to(out/'engineering').parts for x in ['public_export01','carrier']):
            files.add(p)
    files={p for p in files if p.is_file()}
    for p in files:
        assert root in p.parents and p.suffix.lower() not in ['.exe','.dll','.lic','.pyd','.a','.whl'],('forbidden binary/license',p)
        assert '__pycache__' not in p.parts and 'build' not in p.relative_to(root).parts,('non-source dependency',p)
    return root,out,sorted(files)

def preflight(root):
    tick=time.perf_counter();root,out,files=inventory(root)
    csv.field_size_limit(64*1024*1024)
    max_field=0;max_field_path=None;csv_files=0
    for p in files:
        if p.suffix!='.csv':continue
        csv_files+=1
        with p.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.reader(f):
                for value in row:
                    if len(value)>max_field:max_field=len(value);max_field_path=p.relative_to(root).as_posix()
    assert max_field<64*1024*1024
    value=dict(scripts=[p.relative_to(root).as_posix() for p in closure(root)],
        source_files=206,files=len(files),raw_bytes=sum(p.stat().st_size for p in files),
        required_import_configs=['results/unified_exact_round94/preregistration.json'],
        required_old_inputs=['reference/round100_confirmation/H100.txt','reference/round109_geographic/G100-R2.txt'],
        CSV_field_capacity=64*1024*1024,actual_maximum_CSV_field_characters=max_field,
        actual_maximum_CSV_field_path=max_field_path,CSV_files_read=csv_files,
        old_carrier_copied=False,native_PE_DLL_license_credentials_excluded=True,
        later_restore_review_remote_receipts_excluded=True,original_root_fallback=False,
        Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick)
    core.write(out/'public_dependency_closure.json',value)
    print(json.dumps(value),flush=True)

def pack(root):
    tick=time.perf_counter();root,out,files=inventory(root)
    assert (out/'public_dependency_closure.json').is_file()
    d=out/'compact_evidence';d.mkdir(exist_ok=False)
    manifest={p.relative_to(root).as_posix():dict(SHA=core.sha(p),bytes=p.stat().st_size) for p in files}
    stream=Parts(d)
    try:
        with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|') as archive:
                for p in files:archive.add(p,arcname=p.relative_to(root).as_posix(),recursive=False)
    finally:stream.finish()
    parts=[dict(path=p.relative_to(root).as_posix(),SHA=core.sha(p),bytes=p.stat().st_size) for p in stream.paths]
    core.write(d/'manifest.json',dict(schema='round116-current-public-carrier-v1',files=manifest,parts=parts,
        PE_DLL_license_credentials_excluded=True,full_old_carriers_copied=False,
        original_worktree_fallback=False,later_receipts_outside_scientific_payload=True,Optimize=0))
    value=dict(files=len(files),raw_bytes=sum(q['bytes'] for q in manifest.values()),parts=parts,
        compressed_bytes=sum(q['bytes'] for q in parts),manifest_SHA=core.sha(d/'manifest.json'),
        Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick)
    core.write(out/'public_pack_receipt.json',value)
    print(json.dumps({k:v for k,v in value.items() if k!='parts'}),flush=True)

def restore(root,commit,destination):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND
    destination=Path(destination).resolve();assert not destination.exists()
    destination.mkdir();export=out/'engineering/public_export01';export.mkdir(parents=True,exist_ok=False)
    manifest=core.read(out/'compact_evidence/manifest.json')
    names=[ROUND+'/compact_evidence/manifest.json']+[p['path'] for p in manifest['parts']]
    target=export/'public_carrier.tar'
    subprocess.run(['git','archive','--format=tar','--output='+str(target),commit,'--',*names],cwd=root,check=True)
    carrier=export/'carrier';carrier.mkdir()
    with tarfile.open(target) as archive:archive.extractall(carrier,filter='data')
    restored_manifest=core.read(carrier/ROUND/'compact_evidence/manifest.json');assert restored_manifest==manifest
    combined=export/'evidence.tar.gz'
    with combined.open('xb') as output:
        for p in manifest['parts']:
            source=carrier/p['path'];assert core.sha(source)==p['SHA']
            with source.open('rb') as f:shutil.copyfileobj(f,output,1024*1024)
    with tarfile.open(combined,'r:gz') as archive:archive.extractall(destination,filter='data')
    for n,q in manifest['files'].items():assert core.sha(destination/n)==q['SHA']
    core.write(out/'public_export_receipt.json',dict(commit=commit,archive_SHA=core.sha(target),
        actual_git_archive=True,one_export=True,parts_verified=True,exported_unix=time.time(),Optimize=0,native_starts=0))
    value=dict(commit=commit,root=str(destination),fresh_empty_directory=True,one_restore=True,
        files=len(manifest['files']),all_manifest_hashes_equal=True,original_root_fallback=False,
        engineering_seconds=time.perf_counter()-tick,restored_unix=time.time(),
        receipt_does_not_cover_future_reconstruction=True,Optimize=0,native_starts=0)
    core.write(out/'public_restore_receipt.json',value);print(json.dumps(value),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['preflight','pack','restore']);parser.add_argument('--root',required=True)
    parser.add_argument('--commit');parser.add_argument('--destination');a=parser.parse_args()
    if a.mode=='preflight':preflight(a.root)
    elif a.mode=='pack':pack(a.root)
    else:restore(a.root,a.commit,a.destination)
