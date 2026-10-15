"""One bounded safe carrier, committed export and independent empty-root replay."""
from round122_common import ROOT,OUT,WORK,TEMP,read,write,sha
from pathlib import Path
import argparse,ast,csv,gzip,hashlib,io,json,subprocess,sys,tarfile,time
import publication_security as security
from round117_release import Parts
from round121_release import normalize,typed_equal
ROUND='results/unified_exact_round122'
FORBIDDEN={'.exe','.dll','.lic','.pyd','.a','.o','.obj','.lib','.whl','.pyc','.html','.htm'}

def closure(root):
    pending=['round122_release','round122_finish_report','read_round122'];found=set()
    while pending:
        name=pending.pop();p=root/'scripts'/(name+'.py')
        if name in found or not p.is_file():continue
        found.add(name)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            mods=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending.extend(m for m in mods if m and (root/'scripts'/(m+'.py')).is_file())
    return {root/'scripts'/(n+'.py') for n in found}

def inventory(root):
    root=Path(root).resolve();out=root/ROUND;candidate=read(out/'candidate_identity.json');files=closure(root)
    files.update(root/p for p in candidate['source_bindings']);files.update(root/p for p in candidate['helpers'])
    files.update(root/p for p in read(out/'bootstrap_scope.json')['finite_authority_files'])
    files.add(root/'WORKSPACE_POLICY.md')
    files.update(p for p in (root/'reference/round122_paper_benchmark').rglob('*') if p.is_file())
    for p in read(out/'input_manifest.json')['qualification_roles']:files.add(root/p['input_path'])
    excluded={'compact_evidence','delivery','restored_reconstruction'}
    later={'public_dependency_closure.json','public_pack_receipt.json','delivery_summary.md','cleanup_summary.json'}
    for p in out.rglob('*'):
        if not p.is_file() or p.suffix.lower() in FORBIDDEN:continue
        rel=p.relative_to(out).as_posix()
        if rel in later or any(rel.startswith(n+'/') for n in excluded):continue
        if rel.startswith(('review/post_formal','review/extra_review','engineering/public_export')):continue
        files.add(p)
    if (out/'public_dependency_closure.json').is_file():files.add(out/'public_dependency_closure.json')
    for p in files:
        assert p.is_file() and p.resolve().is_relative_to(root) and p.suffix.lower() not in FORBIDDEN,str(p)
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
        scripts=sorted(p.relative_to(root).as_posix() for p in closure(root)),maximum_CSV_field=maximum,CSV_capacity=64*1024*1024,
        current_raw_and_finite_safe_authorities_only=True,no_prior_campaign_or_carrier=True,runtime_binaries_license_credentials_HTML_excluded=True,
        Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in files),maximum_CSV_field=maximum)),flush=True)

def pack(root):
    tick=time.perf_counter();root,out,files=inventory(root);assert (out/'public_dependency_closure.json').is_file()
    scan=security.scan_items((p.relative_to(root).as_posix(),p.read_bytes()) for p in files)
    write(out/'delivery/payload_scan.json',scan);assert scan['passed'],'actual payload scan failed'
    target=out/'compact_evidence';target.mkdir(exist_ok=False);writer=Parts(target);entries={}
    try:
        with gzip.GzipFile(fileobj=writer,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|') as arc:
                for p in files:
                    name=p.relative_to(root).as_posix();security.Scanner.member_name(name)
                    entries[name]=dict(SHA=sha(p),bytes=p.stat().st_size)
                    member=tarfile.TarInfo(name);member.size=p.stat().st_size;member.mode=0o644;member.mtime=0
                    with p.open('rb') as f:arc.addfile(member,f)
    finally:writer.finish()
    parts=[dict(path=p.relative_to(root).as_posix(),SHA=sha(p),bytes=p.stat().st_size) for p in writer.paths]
    write(target/'manifest.json',dict(schema='round122-current-safe-evidence-v1',files=entries,parts=parts,
        current_raw_and_finite_safe_authorities_only=True,no_prior_campaign_or_carrier=True,
        runtime_binaries_license_credentials_HTML_excluded=True,original_root_fallback=False,later_receipts_outside_payload=True,Optimize=0))
    scan=security.scan_items(security.file_items(root,[target.relative_to(root).as_posix()]))
    write(out/'delivery/carrier_scan.json',scan);assert scan['passed'] and scan['archive_members']>=len(entries)
    write(out/'public_pack_receipt.json',dict(files=len(entries),raw_bytes=sum(v['bytes'] for v in entries.values()),parts=parts,
        manifest_SHA=sha(target/'manifest.json'),complete_decompressed_member_scan=True,Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(files=len(entries),parts=len(parts),bytes=sum(p['bytes'] for p in parts))),flush=True)

class Joined:
    def __init__(self,archive,names):self.archive=archive;self.names=iter(names);self.stream=None
    def read(self,n=-1):
        out=[];left=n
        while left!=0:
            if self.stream is None:
                try:self.stream=self.archive.extractfile(next(self.names))
                except StopIteration:break
            data=self.stream.read(left)
            if data:
                out.append(data)
                if left>0:left-=len(data)
            else:self.stream.close();self.stream=None
        return b''.join(out)

def restore(root,commit,destination):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND;dest=Path(destination).resolve()
    assert not dest.exists() and dest.is_relative_to((WORK/'restore').resolve()) and not dest.is_relative_to(root)
    for p in [dest.parent,*dest.parents]:
        if p.exists():assert not p.is_symlink() and not p.is_junction()
    export=TEMP/'public-export';export.mkdir(parents=True,exist_ok=False)
    manifest=read(out/'compact_evidence/manifest.json');names=[ROUND+'/compact_evidence/manifest.json']+[p['path'] for p in manifest['parts']]
    archive=export/'public_carrier.tar'
    subprocess.run(['git','archive','--format=tar','--output='+str(archive),commit,'--',*names],cwd=root,check=True)
    restored=set()
    with tarfile.open(archive) as published:
        raw_manifest=published.extractfile(names[0]).read();actual=json.loads(raw_manifest);assert actual==manifest
        for part in actual['parts']:
            h=hashlib.sha256();count=0
            with published.extractfile(part['path']) as f:
                for data in iter(lambda:f.read(1024*1024),b''):h.update(data);count+=len(data)
            assert count==part['bytes'] and h.hexdigest()==part['SHA']
        dest.mkdir(parents=True,exist_ok=False)
        with tarfile.open(fileobj=Joined(published,[p['path'] for p in actual['parts']]),mode='r|gz') as arc:
            for member in arc:
                security.Scanner.member_name(member.name);assert member.isfile() and member.name not in restored
                expected=actual['files'][member.name];path=(dest/member.name).resolve();assert path.is_relative_to(dest)
                path.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();count=0
                with arc.extractfile(member) as src,path.open('xb') as target:
                    for data in iter(lambda:src.read(1024*1024),b''):target.write(data);h.update(data);count+=len(data)
                assert count==member.size==expected['bytes'] and h.hexdigest()==expected['SHA']
                restored.add(member.name)
    assert restored==set(manifest['files'])
    write(dest/'public_restore_origin.json',dict(scientific_commit=commit,published_manifest_SHA=security.sha(raw_manifest),
        manifest=manifest,fresh_empty_root=str(dest),all_member_hashes_equal=True,source='actual committed safe carrier export',no_original_raw_fallback=True))
    write(out/'delivery/public_export_restore_receipt.json',dict(scientific_commit=commit,one_actual_git_archive=True,archive=str(archive),archive_SHA=sha(archive),
        fresh_empty_root=str(dest),members=len(restored),all_member_hashes_equal=True,no_original_raw_fallback=True,
        Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick,does_not_attest_future_replay=True))
    print(json.dumps(dict(members=len(restored),empty_root=str(dest))),flush=True)

def restored_check(root):
    tick=time.perf_counter();root=Path(root).resolve();assert ROOT==root;out=root/ROUND
    origin=read(root/'public_restore_origin.json');manifest=origin['manifest'];measured=read(out/'initialization_receipt.json')['workspace']['execution']
    runtime=Path(sys.base_prefix).resolve();opened=set()
    def boundary(event,args):
        if event in ['subprocess.Popen','socket.connect']:raise AssertionError('native/process/network forbidden in restored replay')
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        path=Path(os_decode(args[0])).resolve()
        assert path.is_relative_to(root) or path.is_relative_to(runtime),('external restore access',str(path))
        if path.is_relative_to(root):opened.add(path.relative_to(root).as_posix())
    sys.addaudithook(boundary);csv.field_size_limit(64*1024*1024)
    import read_round122 as reader
    from round122_decision import decide
    assert reader.ROOT==root
    values=[]
    for n in range(1,9):
        dest=out/'restored_reconstruction'/f'group{n:02d}';reader.rebuild_group(n,dest)
        actual=read(dest/'current_core.json');expected=read(out/f'reconstruction/group{n:02d}/current_core.json')
        typed_equal(normalize(actual,[root,measured]),normalize(expected,[root,measured]));values.append(actual)
    stage=decide(values,True,proof_risk=any(v['adjudication']['rejections'] for v in values))
    typed_equal(stage,read(out/'stage_decision.json'))
    pairs=[p for v in values for p in v['pairs']];typed_equal(pairs,read(out/'all48_pairs.json'))
    # Check every stored arm with the explicit, purely editorial legacy-panel annotation.
    arms=[dict(a,legacy_panel_formal_flag=a.get('formal_performance'),formal_performance=True,seed=v['group']['seed'],
        group_number=v['group']['number'],source=v['group']['source'],panel_kind=v['group']['panel_kind']) for v in values for a in v['arms']]
    typed_equal(normalize(arms,[root,measured]),normalize(read(out/'all32_arms.json'),[root,measured]))
    changes=[]
    for name,entry in manifest['files'].items():
        path=root/name;digest=sha(path)
        if digest==entry['SHA']:continue
        assert path.name=='round120_event_contract.json',('unexpected restored-byte mutation',name)
        group=int(name.split('/campaign/group',1)[1][:2])
        expected=read(out/f'reconstruction/group{group:02d}/current_core.json')
        actual=read(path);saved=next(e for e in expected['mechanism'] if e.get('events_SHA')==actual.get('events_SHA'))
        saved={k:v for k,v in saved.items() if k!='arm'}
        typed_equal(normalize(actual,[root,measured]),normalize(saved,[root,measured]))
        changes.append(dict(path=name,unpacked_SHA=entry['SHA'],reconstructed_SHA=digest,only_normalized_root_paths_differ=True))
    write(root/'restored_check_receipt.json',dict(passed=True,scientific_commit=origin['scientific_commit'],fresh_empty_root=str(root),
        formal_arms=32,pairs=48,stage=stage['stage'],typed_JSON_all_fields_values_arrays_and_signed_zero_equal=True,
        normalization='only complete measured/restored root path component prefixes; no rounding/field removal',
        regenerated_derived_sidecars=changes,all_other_carrier_members_byte_unchanged=True,opened_inside_root=sorted(opened),
        no_original_raw_helper_or_runtime_binary_fallback=True,boundary='Python open/module/process/network audit; not an OS sandbox; standard runtime prefix allowed',
        Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(passed=True,arms=32,pairs=48,stage=stage['stage'],sidecars=len(changes))),flush=True)

def os_decode(x):return x.decode() if isinstance(x,bytes) else x

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','pack','restore','restored-check']);parser.add_argument('--root',default='.')
    parser.add_argument('--commit');parser.add_argument('--destination');args=parser.parse_args()
    if args.action=='restore':restore(args.root,args.commit,args.destination)
    elif args.action=='restored-check':restored_check(args.root)
    else:{'preflight':preflight,'pack':pack}[args.action](args.root)
