"""One finite safe current carrier and one actual public empty-root replay."""
from pathlib import Path
import argparse,ast,csv,gzip,hashlib,io,json,os,subprocess,sys,tarfile,time,urllib.parse,urllib.request
import round123_common as c
import publication_security as security
from round117_release import Parts
from round121_release import normalize,typed_equal
from round122_release import Joined,scan_carrier,public_manifest_bytes

ROUND='results/unified_exact_round123'
FORBIDDEN={'.exe','.dll','.lic','.pyd','.a','.o','.obj','.lib','.whl','.pyc','.html','.htm'}

def closure(root):
    pending=['read_round123']+[p.stem for p in (root/'scripts').glob('round123_*.py')]
    found=set()
    while pending:
        name=pending.pop();p=root/'scripts'/(name+'.py')
        if name in found or not p.is_file():continue
        found.add(name)
        for n in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            mods=[x.name for x in n.names] if isinstance(n,ast.Import) else [n.module] if isinstance(n,ast.ImportFrom) else []
            pending.extend(x for x in mods if x and (root/'scripts'/(x+'.py')).is_file())
    return {root/'scripts'/(n+'.py') for n in found}

def inventory(root):
    root=Path(root).resolve();out=root/ROUND;candidate=c.read(out/'candidate_identity.json');files=closure(root)
    files.add(root/'scripts/round123_watch.ps1')
    files.update(root/n for n in candidate['helpers']);files.update(root/n for n in candidate['source_bindings'])
    files.update(root/n for n in c.read(out/'public_finite_authorities.json')['paths'])
    observed=c.read(out/'reconstruction/final/dependency_reads.json')
    for name in observed['paths']:
        if name.startswith('results/') and not name.startswith(ROUND+'/'):
            assert not any(part in Path(name).parts for part in ['campaign','raw','local_raw','compact_evidence']),('Prior campaign dependency is not allowed',name)
    files.update(root/n for n in observed['paths'])
    files.update(root/p['input_path'] for p in c.read(out/'input_manifest.json')['roles']+c.read(out/'input_manifest.json')['qualification_roles'])
    excluded={'compact_evidence','delivery','restored_reconstruction'}
    later={'public_pack_receipt.json','cleanup_summary.json','delivery_summary.md'}
    for p in out.rglob('*'):
        if not p.is_file() or p.suffix.lower() in FORBIDDEN:continue
        rel=p.relative_to(out).as_posix()
        if rel in later or any(rel.startswith(n+'/') for n in excluded):continue
        files.add(p)
    for p in files:
        assert p.is_file() and p.resolve().is_relative_to(root) and not p.is_symlink() and not p.is_junction()
        assert p.suffix.lower() not in FORBIDDEN and '__pycache__' not in p.parts and 'build' not in p.relative_to(root).parts
        assert p.stat().st_size<=security.MAX_MEMBER_BYTES
    return root,out,sorted(files)

def finite_authorities(root):
    """Only the finite checked-out old contracts/tables, never a prior campaign/carrier."""
    root=Path(root).resolve();out=root/ROUND;paths=[];excluded=[]
    for folder in (root/'results').iterdir():
        if folder==out or not folder.is_dir():continue
        for p in folder.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(root).as_posix()
            assert not any(x in p.parts for x in ['campaign','compact_evidence','local_raw','raw'])
            assert p.suffix.lower() not in FORBIDDEN
            if p.stat().st_size>=2*1024*1024:
                excluded.append(dict(path=rel,SHA=c.sha(p),bytes=p.stat().st_size,reason='Large historical review/index not a current reader dependency; retain pinned source reference'))
            else:paths.append(rel)
    if (root/'WORKSPACE_POLICY.md').is_file():paths.append('WORKSPACE_POLICY.md')
    c.write(out/'public_finite_authorities.json',dict(paths=sorted(paths),excluded_large_old_authorities=excluded,scope='Finite current sparse old contracts/tables only; no prior native campaign reproduced',
        source_heads=dict(R122=c.BASE),UTC=c.utc()))

def preflight(root):
    tick=time.perf_counter();finite_authorities(root);root,out,files=inventory(root);maximum=0;csv.field_size_limit(64*1024*1024)
    for p in files:
        if p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as f:
                for row in csv.reader(f):maximum=max(maximum,max(map(len,row),default=0))
    assert maximum<64*1024*1024
    c.write(out/'public_dependency_closure.json',dict(prospective_files_excluding_this_new_receipt=len(files),
        raw_bytes=sum(p.stat().st_size for p in files),scripts=sorted(p.relative_to(root).as_posix() for p in closure(root)),
        maximum_CSV_field=maximum,CSV_capacity=64*1024*1024,one_current_three_arm_payload_plus_finite_math_and_qualification=True,
        no_prior_campaign_or_carrier=True,no_runtime_binary_license_HTML_or_credentials=True,Optimize=0,seconds=time.perf_counter()-tick))
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in files),maximum_CSV_field=maximum)))

def pack(root):
    tick=time.perf_counter();root,out,files=inventory(root);assert (out/'public_dependency_closure.json').exists()
    assert c.read(out/'stage_decision.json')['execution_stage']=='COMPLETE'
    assert c.read(out/'review/independent_post.json')['decision']=='ACCEPT'
    scan=security.scan_items((p.relative_to(root).as_posix(),p.read_bytes()) for p in files)
    c.write(out/'delivery/payload_scan.json',scan);assert scan['passed']
    target=out/'compact_evidence';target.mkdir(exist_ok=False);writer=Parts(target);entries={}
    try:
        with gzip.GzipFile(fileobj=writer,mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as tar:
            for p in files:
                name=p.relative_to(root).as_posix();security.Scanner.member_name(name)
                entries[name]=dict(SHA=c.sha(p),bytes=p.stat().st_size)
                info=tarfile.TarInfo(name);info.size=p.stat().st_size;info.mode=0o644;info.mtime=0
                with p.open('rb') as f:tar.addfile(info,f)
    finally:writer.finish()
    parts=[dict(path=p.relative_to(root).as_posix(),SHA=c.sha(p),bytes=p.stat().st_size) for p in writer.paths]
    c.write(target/'manifest.json',dict(schema='round123-current-safe-evidence-v1',files=entries,parts=parts,
        no_prior_campaign_or_carrier=True,finite_old_math_models_not_old_campaign=True,
        no_runtime_binary_license_HTML_or_credentials=True,original_root_fallback=False,later_delivery_receipts_outside_payload=True,Optimize=0))
    scan=scan_carrier(root,target,parts);c.write(out/'delivery/carrier_scan.json',scan);assert scan['passed'] and scan['archive_members']>=len(entries)
    c.write(out/'public_pack_receipt.json',dict(files=len(entries),raw_bytes=sum(e['bytes'] for e in entries.values()),parts=parts,
        manifest_SHA=c.sha(target/'manifest.json'),complete_decompressed_member_scan=True,Optimize=0,seconds=time.perf_counter()-tick))
    print(json.dumps(dict(files=len(entries),parts=len(parts),compressed_bytes=sum(p['bytes'] for p in parts))))

def public_export(commit,expected_manifest,archive):
    assert re_commit(commit);manifest=json.loads(expected_manifest);assert manifest['schema']=='round123-current-safe-evidence-v1'
    prefix=ROUND+'/compact_evidence/';names=[prefix+'manifest.json']+[p['path'] for p in manifest['parts']]
    assert len(names)==len(set(names)) and manifest['parts'];base='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+commit+'/'
    def get(name):
        security.Scanner.member_name(name);assert name.startswith(prefix)
        return urllib.request.urlopen(urllib.request.Request(base+urllib.parse.quote(name,safe='/'),headers={'User-Agent':'TailoredExact-Round123-public-restore'}),timeout=45)
    with get(names[0]) as response:actual=response.read(len(expected_manifest)+1)
    assert actual==expected_manifest
    fetched=[dict(path=names[0],bytes=len(actual),SHA=hashlib.sha256(actual).hexdigest())]
    class Stream:
        def __init__(self,source):self.source=source;self.count=0;self.h=hashlib.sha256()
        def read(self,n=-1):
            b=self.source.read(n);self.count+=len(b);self.h.update(b);return b
    with Path(archive).open('xb') as f,tarfile.open(fileobj=f,mode='w') as tar:
        info=tarfile.TarInfo(names[0]);info.size=len(actual);tar.addfile(info,io.BytesIO(actual))
        for part in manifest['parts']:
            assert part['path'].startswith(prefix) and 0<part['bytes']<=32*1024*1024
            with get(part['path']) as response:
                stream=Stream(response);info=tarfile.TarInfo(part['path']);info.size=part['bytes'];tar.addfile(info,stream)
                assert stream.count==part['bytes'] and stream.h.hexdigest()==part['SHA'] and response.read(1)==b''
            fetched.append(part)
    return dict(scientific_commit=commit,fetched=fetched,source='actual pinned anonymous public HTTPS manifest and carrier parts',
        application_credentials_supplied=False,local_git_archive_or_part_or_original_raw_fallback=False)

def re_commit(s):return len(s)==40 and all(x in '0123456789abcdef' for x in s)

def restore(root,commit,destination):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND;dest=Path(destination).resolve()
    assert re_commit(commit) and not dest.exists() and dest.is_relative_to((c.WORK/'restore').resolve()) and not dest.is_relative_to(root)
    for p in [dest.parent,*dest.parents]:
        if p.exists():assert not p.is_symlink() and not p.is_junction()
    exp=c.TEMP/'public-export';exp.mkdir(parents=True,exist_ok=False);archive=exp/'public_carrier.tar'
    manifest=c.read(out/'compact_evidence/manifest.json');expected=public_manifest_bytes((out/'compact_evidence/manifest.json').read_bytes())
    public=public_export(commit,expected,archive);restored=set()
    with tarfile.open(archive) as public_tar:
        raw=public_tar.extractfile(ROUND+'/compact_evidence/manifest.json').read();actual=json.loads(raw);typed_equal(actual,manifest)
        dest.mkdir(parents=True,exist_ok=False)
        with tarfile.open(fileobj=Joined(public_tar,[p['path'] for p in actual['parts']]),mode='r|gz') as tar:
            for info in tar:
                security.Scanner.member_name(info.name);assert info.isfile() and info.name not in restored
                path=(dest/info.name).resolve();assert path.is_relative_to(dest);entry=manifest['files'][info.name]
                path.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();count=0
                with tar.extractfile(info) as src,path.open('xb') as target:
                    for b in iter(lambda:src.read(1<<20),b''):target.write(b);h.update(b);count+=len(b)
                assert count==info.size==entry['bytes'] and h.hexdigest()==entry['SHA'];restored.add(info.name)
    assert restored==set(manifest['files'])
    origin=dict(scientific_commit=commit,manifest=manifest,published_manifest_SHA=hashlib.sha256(raw).hexdigest(),
        source=public['source'],fresh_empty_root=str(dest),all_member_hashes_equal=True,no_original_raw_fallback=True)
    c.write(dest/'public_restore_origin.json',origin)
    c.write(out/'delivery/public_export_restore_receipt.json',dict(scientific_commit=commit,one_actual_public_export=True,
        public_HTTP_export=public,archive=str(archive),archive_SHA=c.sha(archive),fresh_empty_root=str(dest),members=len(restored),
        all_member_hashes_equal=True,no_original_raw_fallback=True,manifest_transport='Only CRLF formatting to pinned Git LF; all typed values retained',
        Optimize=0,seconds=time.perf_counter()-tick,does_not_attest_future_replay=True))
    print(json.dumps(dict(members=len(restored),empty_root=str(dest))))

def restored_check(root):
    tick=time.perf_counter();root=Path(root).resolve();assert c.ROOT==root;out=root/ROUND
    origin=c.read(root/'public_restore_origin.json');manifest=origin['manifest'];measured=c.read(out/'initialization_receipt.json')['workspace']['execution']
    runtime=Path(sys.base_prefix).resolve();opened=set();csv.field_size_limit(64*1024*1024)
    def boundary(event,args):
        if event in ['subprocess.Popen','socket.connect']:raise AssertionError('No process/network/native solve in restored checker')
        if event=='ctypes.dlopen' and args and any(x in str(args[0]).lower() for x in ['gurobi','cplex']):raise AssertionError('No solver DLL load')
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        path=Path(os.fsdecode(args[0])).resolve();assert path.is_relative_to(root) or path.is_relative_to(runtime),('external restore read',str(path))
        if path.is_relative_to(root):opened.add(path.relative_to(root).as_posix())
    sys.addaudithook(boundary)
    import read_round123 as reader
    dest=out/'restored_reconstruction';reader.rebuild(root,dest)
    actual=c.read(dest/'current_core.json');expected=c.read(out/'reconstruction/final/current_core.json')
    typed_equal(normalize(actual,[root,measured]),normalize(expected,[root,measured]))
    import round123_history_fixture as history
    history_replay=history.check(root,write_receipt=False)
    for name,entry in manifest['files'].items():assert c.sha(root/name)==entry['SHA'],('unexpected restored member mutation',name)
    modules=[]
    for name,module in list(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        p=Path(filename).resolve()
        assert p.is_relative_to(root) or p.is_relative_to(runtime),('External imported helper',name,str(p))
        if p.is_relative_to(root):modules.append(dict(module=name,path=p.relative_to(root).as_posix()))
    c.write(root/'restored_check_receipt.json',dict(passed=True,scientific_commit=origin['scientific_commit'],formal_arms=3,pairs=3,
        research_disposition=actual['decision']['research_disposition'],typed_JSON_all_fields_arrays_types_values_and_signed_zero_equal=True,
        normalization='Only complete measured/restored root path prefixes; no rounding or dropped fields',regenerated_derived_sidecars=[],
        initial_unpack_hash_equality_distinct_from_reconstruction=True,
        compared_carrier_members_unchanged_except_listed_derivations=True,
        newly_generated_reconstruction_directory=str(dest.relative_to(root)),
        no_claim_that_all_expanded_and_newly_generated_files_are_identical=True,
        portable_history_regression=history_replay,opened_inside_root=sorted(opened),actual_local_modules=modules,
        no_original_raw_helper_runtime_binary_fallback=True,no_solver_DLL_or_Optimize=True,Optimize=0,
        boundary='Actual Python file/process/network/DLL audit; standard runtime allowed, not an OS sandbox',seconds=time.perf_counter()-tick))
    print(json.dumps(dict(passed=True,arms=3,pairs=3,stage=actual['decision']['research_disposition'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','pack','restore','restored-check']);p.add_argument('--root',default=str(c.ROOT));p.add_argument('--commit');p.add_argument('--destination');a=p.parse_args()
    if a.action=='restore':restore(a.root,a.commit,a.destination)
    elif a.action=='restored-check':restored_check(a.root)
    else:{'preflight':preflight,'pack':pack}[a.action](a.root)
