"""Local/in-memory delivery implementation fixtures; no public recovery root.

Only the explicit current Round133 worktree is used. No transport, subprocess,
native asset, compiler or scientific rerun is started. Actual policy replay is
a separate local-preflight invocation after source_publication is produced.
"""
from pathlib import Path
import argparse, ast, copy, datetime, hashlib, io, json, os, sys, time, types, zipfile, zlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round133'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--source-contracts',action='store_true');args=parser.parse_args()
    assert ROOT==Path('E:/codes/ExactEBRP-work/worktrees/round133').resolve()
    output=args.out.resolve();assert output.is_relative_to(OUT) and not output.exists()
    tick=time.perf_counter();checks=[];runtime_libraries=[]
    def guard(event,values):
        if event.startswith('subprocess.') or event in {'socket.connect','socket.bind'}:
            raise AssertionError(('preflight prohibits process/network execution',event))
        if event=='ctypes.dlopen' and values and values[0] is not None:
            name=str(values[0])
            expected=f'libpython{sys.version_info.major}.{sys.version_info.minor}{sys.abiflags}.dll'
            module=sys.modules.get('ctypes')
            initializing=bool(module is not None and getattr(getattr(module,'__spec__',None),'_initializing',False))
            if name in {expected,'kernel32'} and initializing:
                runtime_libraries.append(name)
            else:raise AssertionError(('preflight prohibits external DLL loading',event,name))
        if event=='open' and values and isinstance(values[0],(str,bytes,os.PathLike)):
            name=os.fsdecode(values[0])
            if Path(name).suffix.lower() in {'.exe','.dll','.o','.obj','.a','.lib'}:
                raise AssertionError(('preflight prohibits native asset reads',name))
    sys.addaudithook(guard);sys.dont_write_bytecode=True
    sys.path.insert(0,str(ROOT/'scripts'))
    import round133_portable_check as portable
    import round133_public_restore as restore
    def check(name,predicate):
        assert predicate,name;checks.append(dict(name=name,passed=True))
    def rejects(name,fn):
        try:fn()
        except (AssertionError,FileNotFoundError,ValueError):
            checks.append(dict(name=name,passed=True));return
        raise AssertionError(name+' unexpectedly accepted')
    for name in ('round133_portable_check.py','round133_public_restore.py','round133_delivery_preflight.py'):
        compile((ROOT/'scripts'/name).read_bytes(),name,'exec')
    check('delivery_entries_parse_as_Python_without_native_compilation',True)
    fs=portable.ClosedRoot(ROOT);fs.make_path_type()
    virtual='results/unified_exact_round133/qualification/delivery_memory_only/fixture.json'
    blob=b'{"closed_root":true}\n';fs.attach(virtual,blob)
    check('published_memory_source_read_and_SHA',fs.read(virtual)=={'closed_root':True} and fs.sha(virtual)==hashlib.sha256(blob).hexdigest())
    check('recorded_absolute_path_maps_to_current_root',fs.Path(str(fs.recorded/virtual))==fs.Path(ROOT/virtual))
    check('root_join_with_recorded_absolute_child_does_not_escape',fs.Path(ROOT)/str(fs.recorded/virtual)==fs.Path(ROOT/virtual))
    rejects('external_old_worktree_file_never_falls_back',lambda:fs.raw('E:/codes/ExactEBRP-work/worktrees/round132/results/x.json'))
    rejects('undeclared_old_round_inside_current_root_never_falls_back',lambda:fs.raw('results/unified_exact_round132/joint/old.json'))
    fs.add_attestation('D:/gurobi1302/win64/bin/gurobi130.dll',portable.DLL_SHA,'fixture attestation only')
    check('native_DLL_SHA_is_attestation_without_open',fs.sha('D:/gurobi1302/win64/bin/gurobi130.dll')==portable.DLL_SHA)
    derived=ROOT/'results/unified_exact_round133/qualification/delivery_memory_only/derived.json'
    fs.allowed_writes={str(fs.resolve(derived))};fs.write(derived,dict(virtual=True))
    check('derived_write_is_memory_only',fs.read(derived)=={'virtual':True} and not derived.exists())
    rejects('unregistered_derived_write_is_rejected',lambda:fs.write(ROOT/'other.json',dict(x=1)))
    rejects('public_mode_rejects_current_git_worktree',lambda:portable.check(ROOT))
    rejects('local_mode_rejects_another_existing_directory',lambda:portable.check(ROOT/'results',True))
    for name in ('../escape','/absolute','C:/absolute','a\\b','a//b','x.exe','x.dll'):
        rejects('restore_rejects_unsafe_path_'+name,lambda name=name:restore.safe_name(name))
    check('only_fixed_current_payload_scope_is_admitted',restore.current_file('scripts/round133_portable_check.py') and
        restore.current_file('results/unified_exact_round94/preregistration.json') and
        not restore.current_file('results/unified_exact_round132/campaign/old.json'))
    state=dict(commit='a'*40,owner=restore.OWNER,initially_empty=True,destination=str(ROOT),status='FAILED_PRESERVE_SAME_ROOT')
    restore.validate_resume_state(state,'a'*40,ROOT,True)
    check('failed_owned_state_allows_explicit_same_root_resume',True)
    rejects('PASS_state_always_refuses_rerun_without_receipt_argument',lambda:restore.validate_resume_state(dict(state,status='PASS'),'a'*40,ROOT,True))
    rejects('RUNNING_state_needs_explicit_exit_audit',lambda:restore.validate_resume_state(dict(state,status='RUNNING'),'a'*40,ROOT,True))
    rejects('different_commit_resume_is_rejected',lambda:restore.validate_resume_state(state,'b'*40,ROOT,True))
    rejects('different_root_resume_is_rejected',lambda:restore.validate_resume_state(state,'a'*40,ROOT/'results',True))
    rejects('implicit_resume_is_rejected',lambda:restore.validate_resume_state(state,'a'*40,ROOT,False))
    class MemoryTransport(restore.Recovery):
        def __init__(self):
            self.commit='a'*40;self.curl=Path('anonymous-transport-placeholder')
            self.limits=restore.Limits({});self.failures=[];self.transfers=[]
    transport=MemoryTransport();commands=[];original_run=restore.subprocess.run
    def fake_https(command,**options):
        commands.append((command,options));return types.SimpleNamespace(returncode=0,stdout=b'published',stderr=b'')
    try:
        restore.subprocess.run=fake_https
        check('fixed_commit_HTTPS_request_uses_no_real_process',transport.get('results/unified_exact_round133/goal.md')==b'published')
        command,options=commands[0]
        check('curlrc_and_protocol_flags_match_passed_transport',command[1]=='--disable' and
            command[command.index('--proto')+1]=='=https' and command[command.index('--proto-redir')+1]=='=https' and
            '--insecure' not in command and command[-1].startswith('https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+'a'*40+'/'))
        rejects('HEAD_is_not_a_fixed_commit_transport',lambda:transport.get('safe.json','HEAD'))
    finally:restore.subprocess.run=original_run
    class MissingMemoryPath:
        def exists(self):return False
    class MemoryFetch(restore.Recovery):
        def __init__(self,data):self.data=data;self.transforms=[];self.saved={}
        def path(self,name,create=False):return MissingMemoryPath()
        def get(self,name):return self.data
        def install_bytes(self,name,data,SHA=None):
            assert restore.digest(data)==SHA;self.saved[name]=data
    expected=b'line\r\n';fetch=MemoryFetch(b'line\n')
    row=dict(path='safe.txt',bytes=len(expected),SHA256=restore.digest(expected),serialization='exact bytes; recorded text transport')
    fetch.fetch(row)
    check('only_exact_registered_CRLF_hash_is_materialized',fetch.saved['safe.txt']==expected and fetch.transforms[0]['materialization']=='CRLF')
    reformatted=MemoryFetch(b'{"x":1}\n');wanted=b'{ "x":1 }\n'
    rejects('JSON_semantic_equality_never_replaces_exact_published_bytes',lambda:reformatted.fetch(dict(row,
        path='safe.json',bytes=len(wanted),SHA256=restore.digest(wanted))))
    source_contracts=None
    if args.source_contracts:
        # Reuse the actual materialization contract against the existing source
        # publication, but drain/hash every ZIP member into memory, never create
        # a second root and never replace a current source file.
        class MemoryMaterialization(restore.Recovery):
            def __init__(self):
                self.dest=ROOT;self.payload={};self.captured={};self.records=[]
            def path(self,name,create=False):
                relative=restore.safe_name(name);path=ROOT.joinpath(*relative.parts).resolve()
                assert path.is_relative_to(ROOT);return path
            def install_stream(self,name,source,expected_bytes,expected_SHA,expected_CRC=None):
                data=source.read();assert len(data)==expected_bytes and restore.digest(data)==expected_SHA
                if expected_CRC is not None:assert (zlib.crc32(data)&0xffffffff)==expected_CRC
                self.captured[name]=data;return ROOT/name
        memory=MemoryMaterialization();pub=restore.read(OUT/'source_publication.json')
        for row in pub['reused_main_source_and_bindings']:memory.payload[row['path']]={}
        for row in pub['old_E3_source_dependencies'].values():memory.payload[row['path']]={}
        source_contracts=memory.materialize_sources(dict(source_publication=restore.OUT+'/source_publication.json'))
        check('actual_source_archives_have_complete_exact_member_sets_and_CRC',len(memory.captured)==
            pub['candidate_source_bundle']['members']+len(pub['execution_helpers']['members']))
        executed=OUT/'infra/portable_source_versions/local_preflight01_e35a951be.py'
        assert hashlib.sha256(executed.read_bytes()).hexdigest()=='e35a951be774ba9219945a11f91003896c888fd3096b21b5bfe9b5ee1a9520dc'
        def executable_AST(path):
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            if tree.body and isinstance(tree.body[0],ast.Expr) and isinstance(tree.body[0].value,ast.Constant) and isinstance(tree.body[0].value.value,str):tree.body.pop(0)
            return ast.dump(tree,include_attributes=False)
        check('final_checker_executable_AST_identical_to_actual_23_arm_preflight',
            executable_AST(executed)==executable_AST(ROOT/'scripts/round133_portable_check.py'))
    result=dict(schema='round133-local-in-memory-delivery-preflight-v1',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='PASS',checks=checks,check_count=len(checks),source_contracts=source_contracts,
        source_hashes={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in
            ('round133_portable_check.py','round133_public_restore.py','round133_delivery_preflight.py')},
        no_second_empty_recovery_root_created=True,public_network_recovery=False,
        Optimize=0,native_starts=0,compilation=0,vendor_DLL_load=0,subprocess_calls=0,
        Python_standard_runtime_ctypes_initialization=runtime_libraries,
        seconds=time.perf_counter()-tick)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,ensure_ascii=False);stream.write('\n')
    print(json.dumps(dict(status='PASS',checks=len(checks),source_contracts=bool(source_contracts),seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
