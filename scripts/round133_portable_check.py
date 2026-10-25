"""Closed-root Round133 recovery: full pure replay, no native execution.

This file is deliberately independent of the execution import graph. Only main()
loads exact published helper bytes, after installing process/DLL/import guards.
It never invokes campaign.run/arm, a compiler, a solver, Git, or a subprocess.
All original source/physical/model/H/Start/return/cover/source predicates remain.
The measured clocks and native asset hashes are historical execution evidence;
new replay wall time is reported separately and never replaces a measured clock.

The explicit current-worktree preflight replayed all 22 formal positions and the
separate unit under the recorded policies. Public empty-root recovery is a
distinct mandatory operation; local-preflight success never stands in for it.
"""
from __future__ import annotations
import argparse, builtins, collections, contextlib, copy, csv, hashlib
import importlib, importlib.abc, importlib.util, inspect, io, json, linecache
import math, os, pathlib, socket, subprocess, sys, time, types, zipfile
from fractions import Fraction

PYTHON_RUNTIME_LIBRARY_LOADS=[]
CTYPES_PRELOADED='ctypes' in sys.modules
def _runtime_library_audit(event,values):
    if event!='ctypes.dlopen':return
    name=values[0] if values else None
    module=sys.modules.get('ctypes')
    initializing=bool(module is not None and getattr(getattr(module,'__spec__',None),'_initializing',False))
    python_name=f'libpython{sys.version_info.major}.{sys.version_info.minor}{sys.abiflags}.dll'
    if name is None or (initializing and name in {python_name,'kernel32'}):
        PYTHON_RUNTIME_LIBRARY_LOADS.append(dict(name=name,scope='Python/Windows standard runtime initialization'))
    else:raise AssertionError(('solver/vendor DLL loading is forbidden in recovery',name))
sys.addaudithook(_runtime_library_audit)
import ctypes

RealPath=pathlib.Path
PathBase=type(RealPath())
ORIGINAL_OPEN=io.open
ROUND='results/unified_exact_round133'
RECORDED_ROOT='E:/codes/ExactEBRP-work/worktrees/round133'
READER_SHA='933af994bf3def115d9870c33f409709d5509a1b42f7b0546645691ce1b7c80a'
ADAPTER_SHA='8feae1d544d92fba843f4836f0c685c2cf38151f20386cd2538396ac34af6640'
AMENDMENT_SHA='7501459291ac9a7a2945f0ce022f52a72d09822df21cec7eb014889f0a8e4f6b'
REPAIR_GATE_SHA='4eeb292208574a67b15124e6c6f79c8b3e1615a56c9d9fd54df294f9d92d78b2'
CANDIDATE_SHA='101e8f75d2675d1f728ddd8aa4010d0b57821218e730a7b06207239af6a997b2'
MATRIX_SHA={
    'D1':'9e638fddd2f5e99b6cadafc933c38d093ec77eb47339345b78895b2ee4070afe',
    'D3':'1f1839df95a8d2d62280aa4e4417177cd6d2829ec7618c2acdf3273893f88182',
}
UNIT_SHA='58af0ed4accf77be62616a7d6acf79dff879f67be22467cf98b3da07695e305f'
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
OLD_E3_SHA='2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
DERIVED=('audit.json','native_claims.json','claim_rejections.json','independent_evidence.json',
         'verification_closeout.json','arm_total_receipt.json','round133_endpoint.json',
         'legacy_model_scope_issue.json','legacy_model_scope_disposition.json')
NATIVE_IMPORTS={'gurobipy','gurobi','cplex','docplex','highspy','pyscipopt'}

def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def native_key(value):return str(pathlib.PureWindowsPath(str(value))).replace('\\','/').lower()

class ClosedRoot:
    """Read-only path transport plus a small, explicit derived-JSON overlay.

    This is not a general virtual filesystem. The actual model/log/H/Start files
    stay real and read-only. Only published source bytes and the original
    verifier's named derived JSON writes can be held in memory.
    """
    def __init__(self,root,recorded_root=RECORDED_ROOT):
        self.root=RealPath(root).resolve(strict=True)
        self.recorded=pathlib.PureWindowsPath(recorded_root)
        self.sources={};self.overlay={};self.allowed_writes=set();self.attestations={}
        self.attestations_used={};self.read_paths=set();self.modules={};self.git_sources={}
        self.derived_writes=[];self.helper_members={};self.publication=None
        self.allowed_files=set();self.allowed_trees=set();self.allowed_dirs={str(self.root)}
        bootstrap=[ROUND+'/candidate_manifest.json',ROUND+'/source_publication.json',
            ROUND+'/candidate_build.json',ROUND+'/plans/D1_matrix_frozen.json',
            ROUND+'/plans/D3_matrix_frozen.json',ROUND+'/plans/postverify_handoff_repair_amendment.json',
            ROUND+'/qualification/small_native01/fixture_manifest.json',
            ROUND+'/qualification/small_native01/identity.json',
            ROUND+'/review/postverify_handoff_repair_admission.json',
            ROUND+'/review/legacy_shortcut_reader_admission.json',
            'results/unified_exact_round94/preregistration.json']
        for name in bootstrap:self.allow_file(name)

    def mapped(self,value):
        """Map only the declared execution root; unknown native paths stay opaque."""
        text=os.fspath(value)
        windows=pathlib.PureWindowsPath(text)
        if windows.is_absolute():
            try:relative=windows.relative_to(self.recorded)
            except ValueError:return text
            return str(self.root.joinpath(*relative.parts))
        return text

    def resolve(self,value):
        text=self.mapped(value);windows=pathlib.PureWindowsPath(text)
        # An unmapped Windows absolute path is never an artifact fallback.
        if windows.is_absolute() and not RealPath(text).is_absolute():
            raise AssertionError(('unpublished external path',str(value)))
        path=RealPath(text)
        if not path.is_absolute():path=self.root/path
        path=RealPath(os.path.abspath(path))
        assert path==self.root or self.root in path.parents,('outside recovery root',str(value))
        path=path.resolve(strict=False)
        assert path==self.root or self.root in path.parents,('outside recovery root',str(value))
        return path

    def relative(self,value):return self.resolve(value).relative_to(self.root).as_posix()
    def allow_file(self,value):
        path=self.resolve(value);self.allowed_files.add(str(path))
        self.allowed_dirs.update(str(parent) for parent in path.parents if parent==self.root or self.root in parent.parents)
    def allow_tree(self,value):
        path=self.resolve(value);assert path.is_dir(),('declared current evidence tree missing',str(path))
        self.allowed_trees.add(str(path));self.allowed_dirs.add(str(path))
        for item in path.rglob('*'):
            assert not item.is_symlink() and not getattr(item,'is_junction',lambda:False)(),('linked declared evidence',str(item))
            if item.is_file():
                assert item.suffix.lower() not in {'.exe','.dll','.o','.obj','.a','.lib'}
                self.allow_file(item)
            elif item.is_dir():self.allowed_dirs.add(str(item))
    def scoped(self,value,probe=False):
        path=self.resolve(value);key=str(path)
        if key in self.allowed_files or key in self.sources or key in self.overlay or key in self.allowed_writes:return path
        if probe and (key in self.allowed_dirs or any(path==RealPath(tree) or RealPath(tree) in path.parents for tree in self.allowed_trees)):
            return path
        raise AssertionError(('undeclared recovery evidence path; no old-tree fallback',self.relative(path)))
    def raw(self,value):
        path=self.scoped(value);key=str(path);self.read_paths.add(path.relative_to(self.root).as_posix())
        if key in self.overlay:return self.overlay[key]
        if key in self.sources:return self.sources[key]
        with ORIGINAL_OPEN(path,'rb') as stream:return stream.read()
    def read(self,value):return json.loads(self.raw(value).decode('utf-8-sig'))
    def sha(self,value):
        key=native_key(value)
        if key in self.attestations:
            record=self.attestations[key];self.attestations_used[key]=record
            return record['SHA']
        path=self.scoped(value);key=str(path)
        if key in self.overlay:return digest(self.overlay[key])
        if key in self.sources:return digest(self.sources[key])
        self.read_paths.add(path.relative_to(self.root).as_posix());h=hashlib.sha256()
        with ORIGINAL_OPEN(path,'rb') as stream:
            for block in iter(lambda:stream.read(1048576),b''):h.update(block)
        return h.hexdigest()
    def exists(self,value):
        path=self.scoped(value,probe=True);key=str(path)
        return key in self.overlay or key in self.sources or path.exists()
    def open(self,value,mode='r',buffering=-1,encoding=None,errors=None,newline=None,**kwargs):
        assert not any(c in mode for c in 'wax+'),('read-only recovery path',str(value),mode)
        path=self.scoped(value);key=str(path)
        self.read_paths.add(path.relative_to(self.root).as_posix())
        if key in self.overlay or key in self.sources:
            binary=io.BytesIO(self.overlay[key] if key in self.overlay else self.sources[key])
            return binary if 'b' in mode else io.TextIOWrapper(binary,encoding=encoding or 'utf-8',errors=errors or 'strict',newline=newline)
        return ORIGINAL_OPEN(path,mode,buffering=buffering,encoding=encoding,errors=errors,newline=newline,**kwargs)
    def write(self,value,data):
        path=self.resolve(value);key=str(path)
        assert key in self.allowed_writes,('unregistered virtual derived write',self.relative(path))
        raw=(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        self.overlay[key]=raw;self.derived_writes.append(dict(path=self.relative(path),SHA=digest(raw)))
    def git(self,*args,**kwargs):
        assert not kwargs and len(args)==2 and args[0]=='show',('Git is unavailable in recovery',args)
        assert args[1] in self.git_sources,('unpublished pinned source dependency',args[1])
        return self.raw(self.git_sources[args[1]])
    def portable(self,root,value):
        assert self.resolve(root)==self.root
        return self.Path(self.resolve(value))
    def attach(self,name,raw):
        relative=pathlib.PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        path=self.root.joinpath(*relative.parts);key=str(path)
        resolved=path.resolve(strict=False)
        assert resolved==self.root or self.root in resolved.parents,('source path escapes recovery root',name)
        assert key not in self.sources or self.sources[key]==raw,('duplicate source bytes',name)
        if path.is_file():assert digest(path.read_bytes())==digest(raw),('materialized source differs',name)
        self.sources[key]=raw;self.allow_file(path)
    def add_attestation(self,path,digest_value,kind):
        key=native_key(path);record=dict(recorded_path=str(path),SHA=digest_value,kind=kind,
            verification='historical execution attestation only; no local native asset opened or remeasured')
        assert key not in self.attestations or self.attestations[key]['SHA']==digest_value
        self.attestations[key]=record

    def make_path_type(self):
        fs=self
        class PortablePath(PathBase):
            def __new__(cls,*args):
                if len(args)==1:args=(fs.mapped(args[0]),)
                return super().__new__(cls,*args)
            def __truediv__(self,other):
                mapped=fs.mapped(other)
                if mapped!=os.fspath(other) or RealPath(mapped).is_absolute():return type(self)(mapped)
                return super().__truediv__(other)
            def resolve(self,strict=False):
                path=fs.resolve(str(self))
                if strict:assert fs.exists(path),('missing recovery path',str(self))
                return type(self)(path)
            def open(self,mode='r',buffering=-1,encoding=None,errors=None,newline=None):
                return fs.open(str(self),mode,buffering,encoding,errors,newline)
            def read_bytes(self):return fs.raw(str(self))
            def read_text(self,encoding=None,errors=None):
                with self.open(encoding=encoding or 'utf-8',errors=errors) as stream:return stream.read()
            def exists(self):return fs.exists(str(self))
            def is_file(self):
                path=fs.scoped(str(self),probe=True);key=str(path)
                return key in fs.overlay or key in fs.sources or path.is_file()
            def is_dir(self):return fs.scoped(str(self),probe=True).is_dir()
            def iterdir(self):return (type(self)(p) for p in fs.scoped(str(self),probe=True).iterdir())
            def glob(self,pattern):return (type(self)(p) for p in fs.scoped(str(self),probe=True).glob(pattern))
            def rglob(self,pattern):return (type(self)(p) for p in fs.scoped(str(self),probe=True).rglob(pattern))
            def mkdir(self,*args,**kwargs):raise AssertionError('recovery may not create artifact directories')
            def unlink(self,*args,**kwargs):raise AssertionError('recovery may not delete artifacts')
            def rename(self,*args,**kwargs):raise AssertionError('recovery may not rename artifacts')
            def replace(self,*args,**kwargs):raise AssertionError('recovery may not replace artifacts')
            def write_bytes(self,*args,**kwargs):raise AssertionError('only registered virtual JSON writes are allowed')
            def write_text(self,*args,**kwargs):raise AssertionError('only registered virtual JSON writes are allowed')
        self.Path=PortablePath

    def patch_module(self,module):
        namespace=vars(module)
        if 'Path' in namespace:namespace['Path']=self.Path
        if 'ROOT' in namespace:namespace['ROOT']=self.Path(self.root)
        for key in ('OUT','STAGE','CAMPAIGN'):
            value=namespace.get(key)
            if not isinstance(value,(pathlib.PurePath,str)):continue
            text=str(value).replace('\\','/')
            if 'results/' in text:namespace[key]=self.Path(self.root/text[text.index('results/'):])
        for key,function in [('read',self.read),('write',self.write),('sha',self.sha),('git',self.git),('portable',self.portable)]:
            if key in namespace:namespace[key]=function
        self.modules[module.__name__]=module

def safe_zip(fs,record):
    assert record['path'].startswith(ROUND+'/artifacts/')
    fs.allow_file(record['path'])
    path=fs.resolve(record['path']);assert fs.sha(path)==record['SHA']
    assert path.stat().st_size==record['bytes']
    result={}
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            assert not item.is_dir()
            name=pathlib.PurePosixPath(item.filename)
            assert not name.is_absolute() and '..' not in name.parts and '\\' not in item.filename
            assert item.filename not in result,('duplicate source zip member',item.filename)
            assert not item.filename.lower().endswith(('.exe','.dll','.o','.a','.obj','.lib'))
            result[item.filename]=archive.read(item)
    return result

def publication(fs):
    out=fs.root/ROUND
    candidate_path=out/'candidate_manifest.json';assert fs.sha(candidate_path)==CANDIDATE_SHA
    candidate=fs.read(candidate_path);pub=fs.read(out/'source_publication.json')
    assert pub['schema']=='round133-exact-current-execution-source-publication-v1'
    assert pub['Optimize']==pub['compile']==0 and pub['old_source_is_pinned_public_code_not_native_assets']
    matrices={}
    for stage,count in [('D1',14),('D3',8)]:
        path=out/'plans'/f'{stage}_matrix_frozen.json';assert fs.sha(path)==MATRIX_SHA[stage]
        matrix=fs.read(path);assert len(matrix['groups'])==count and matrix['candidate_manifest_SHA']==CANDIDATE_SHA
        matrices[stage]=matrix
    unit_path=out/'qualification/small_native01/fixture_manifest.json';assert fs.sha(unit_path)==UNIT_SHA
    unit=fs.read(unit_path)
    expected={}
    for manifest in [*matrices.values(),unit]:
        for name,value in manifest['helpers'].items():
            assert name not in expected or expected[name]==value
            expected[name]=value
    amendment_path=out/'plans/postverify_handoff_repair_amendment.json'
    assert fs.sha(amendment_path)==AMENDMENT_SHA
    amendment=fs.read(amendment_path)
    assert amendment['bindings']['adapter_SHA']==ADAPTER_SHA
    build_path=out/'candidate_build.json';build=fs.read(build_path)
    assert fs.sha(build_path)==amendment['bindings']['candidate_build_SHA']==candidate['build_manifest_SHA']
    expected['scripts/round133_postverify_repair.py']=ADAPTER_SHA
    expected['scripts/round133_postverify_repair_tests.py']=amendment['bindings']['fixture_driver_SHA']
    assert pub['execution_helpers']['members']==expected
    helpers=safe_zip(fs,pub['execution_helpers']);assert set(helpers)==set(expected)
    for name,raw in helpers.items():
        assert name.startswith('scripts/') and name.endswith('.py') and digest(raw)==expected[name]
        fs.attach(name,raw)
    assert expected['scripts/round133_read.py']==READER_SHA
    fs.helper_members=expected
    assert pub['candidate_source_bundle']==candidate['executed_source_bytes']
    sources=safe_zip(fs,pub['candidate_source_bundle'])
    if isinstance(pub['candidate_source_bundle'].get('members'),int):assert len(sources)==pub['candidate_source_bundle']['members']
    for name,value in candidate['source_hashes'].items():assert name in sources and digest(sources[name])==value
    for name,raw in sources.items():fs.attach(name,raw)
    roles=collections.defaultdict(dict)
    for row in pub['reused_main_source_and_bindings']:
        assert row['path'].startswith(ROUND+'/source/')
        fs.allow_file(row['path'])
        raw=fs.raw(row['path']);assert digest(raw)==row['SHA'] and len(raw)==row['bytes']
        assert 'attest' in row['object_identity'].lower()
        kind='binding' if row['path'].endswith('_main_binding.json') else 'source'
        assert kind not in roles[row['role']];roles[row['role']][kind]=(row,raw)
    assert set(roles)==set(amendment['bindings']['main_roles'])=={'production','research'}
    for role,pair in roles.items():
        assert set(pair)=={'binding','source'}
        row,source=pair['source'];binding_row,binding_raw=pair['binding']
        declared=amendment['bindings']['main_roles'][role]
        assert row['SHA']==declared['SHA'] and binding_row['SHA']==declared['existing_main_binding_SHA']
        assert json.loads(binding_raw)['source']==digest(source)
        for fragment in declared['fragments'].values():assert fragment in source.decode('utf-8-sig')
        assert build['binaries'][role]['main_object']==dict(path=declared['object_path'],SHA=declared['object_SHA'])
        fs.add_attestation(declared['object_path'],declared['object_SHA'],'historical reused main object; source bytes checked separately')
    fs.add_attestation(build['reused_archive']['path'],build['reused_archive']['SHA'],'historical linked static library')
    for key,row in pub['old_E3_source_dependencies'].items():
        assert key==row['source_commit']+':'+row['source_path']
        assert row['path']==ROUND+'/source/old_code/'+row['source_commit']+'/'+row['source_path']
        fs.allow_file(row['path'])
        raw=fs.raw(row['path']);assert digest(raw)==row['SHA'] and len(raw)==row['bytes']
        fs.git_sources[key]=row['path']
    for stage,matrix in matrices.items():
        for group in matrix['groups']:
            assert group['group'].startswith('campaign/'+stage+'_')
            fs.allow_tree(out/group['group'])
            identity_path=out/group['group']/'identity.json';assert fs.sha(identity_path)==group['identity_SHA']
            identity=fs.read(identity_path);assert identity['launches']==[group['launch']]
            launch=group['launch'];kind='historical original E3 PE' if launch['version']!='candidate' else 'historical candidate PE'
            fs.allow_file(launch['panel']['input_path'])
            if launch['version']!='candidate':
                assert identity['candidate_binary_sha256']==OLD_E3_SHA
                for name,value in identity['source_hashes'].items():
                    key=identity['measured_source_commit']+':'+name
                    assert key in fs.git_sources and fs.sha(fs.git_sources[key])==value
            else:
                role='research' if launch['method'] in ('S2R','GEOM') else 'production'
                assert launch['command'][0]==candidate[role+'_PE']
                assert identity['candidate_binary_sha256']==candidate[role+'_PE_SHA']
            fs.add_attestation(launch['command'][0],identity['candidate_binary_sha256'],kind)
            assert identity['dll_sha256']==DLL_SHA
            result=fs.read(fs.resolve(launch['destination'])/'result.json')
            if result.get('gurobi_progress_path'):
                progress=fs.resolve(result['gurobi_progress_path'])
                assert progress.is_relative_to(fs.root/'results/gurobi_work')
                fs.allow_file(progress)
    fs.allow_tree(out/'repair/postverify_handoff')
    fs.allow_tree(out/'qualification/small_native01')
    unit_identity=fs.read(out/'qualification/small_native01/identity.json')
    fs.allow_file(unit_identity['launches'][0]['panel']['input_path'])
    fs.add_attestation(unit_identity['launches'][0]['command'][0],unit_identity['candidate_binary_sha256'],'historical unit candidate PE')
    assert candidate['DLL_SHA']==DLL_SHA
    fs.add_attestation(candidate['DLL'],DLL_SHA,'historical Gurobi DLL')
    fs.publication=pub
    return candidate,matrices,unit,amendment

class HelperLoader(importlib.abc.Loader):
    def __init__(self,fs,name,relative):self.fs=fs;self.name=name;self.relative=relative
    def create_module(self,spec):return None
    def exec_module(self,module):
        raw=self.fs.sources[str(self.fs.root/self.relative)]
        filename=str(self.fs.root/self.relative)
        module.__file__=filename
        # inspect.getsource originally used Python's universal-newline text
        # reader. Keep exact byte SHA separately, but the same inspect text.
        text=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
        linecache.cache[filename]=(len(raw),None,text.splitlines(keepends=True),filename)
        exec(compile(raw,filename,'exec'),module.__dict__)
        self.fs.patch_module(module)

class HelperFinder(importlib.abc.MetaPathFinder):
    def __init__(self,fs):
        self.fs=fs
        self.names={pathlib.PurePosixPath(name).stem:name for name in fs.helper_members}
        assert len(self.names)==len(fs.helper_members)
    def find_spec(self,fullname,path=None,target=None):
        if fullname in self.names:
            return importlib.util.spec_from_loader(fullname,HelperLoader(self.fs,fullname,self.names[fullname]))
        return None

@contextlib.contextmanager
def closed_helpers(fs):
    """Load only published project bytes; prohibit process and DLL entry points."""
    fs.make_path_type();finder=HelperFinder(fs)
    assert not (NATIVE_IMPORTS & set(sys.modules))
    assert not (set(finder.names) & set(sys.modules)), 'recovery must start with a fresh project import graph'
    changed=[];original_import=builtins.__import__;stdlib=set(getattr(sys,'stdlib_module_names',()))
    pathlib_proxy=types.ModuleType('pathlib')
    pathlib_proxy.__dict__.update(vars(pathlib));pathlib_proxy.Path=fs.Path
    def forbidden(*args,**kwargs):raise AssertionError('portable checker forbids process/native/DLL/network execution')
    def replace(obj,name,value):
        if hasattr(obj,name):changed.append((obj,name,getattr(obj,name)));setattr(obj,name,value)
    def imported(name,globals=None,locals=None,fromlist=(),level=0):
        top=name.split('.')[0]
        assert top not in NATIVE_IMPORTS,('native import forbidden',name)
        caller=(globals or {}).get('__name__','')
        if caller in finder.names and name=='pathlib':return pathlib_proxy
        if not level and top not in finder.names and top not in stdlib and top not in sys.builtin_module_names:
            assert top in {'__future__'},('unpublished/nonstdlib dependency',name)
        return original_import(name,globals,locals,fromlist,level)
    try:
        sys.meta_path.insert(0,finder)
        replace(builtins,'__import__',imported)
        replace(builtins,'open',fs.open)
        for name in ('Popen','run','call','check_call','check_output'):replace(subprocess,name,forbidden)
        for name in ('system','popen','startfile','spawnl','spawnle','spawnlp','spawnlpe','spawnv','spawnve','spawnvp','spawnvpe','execv','execve','execvp','execvpe','fork','posix_spawn','posix_spawnp','open'):
            replace(os,name,forbidden)
        for name in ('CDLL','PyDLL','WinDLL','OleDLL'):replace(ctypes,name,forbidden)
        replace(ctypes,'_dlopen',forbidden)
        for name in ('LoadLibrary',):
            for loader_name in ('cdll','pydll','windll','oledll'):
                if hasattr(ctypes,loader_name):replace(getattr(ctypes,loader_name),name,forbidden)
        for loader_name in ('cdll','pydll','windll','oledll'):
            if hasattr(ctypes,loader_name):replace(getattr(ctypes,loader_name),'_dlltype',forbidden)
        replace(socket,'socket',forbidden);replace(socket,'create_connection',forbidden)
        yield
    finally:
        for obj,name,value in reversed(changed):setattr(obj,name,value)
        if finder in sys.meta_path:sys.meta_path.remove(finder)

def original_gate(fs):
    relative=ROUND+'/review/postverify_handoff_repair_admission.json'
    assert fs.sha(relative)==REPAIR_GATE_SHA
    gate=fs.read(relative)
    assert gate['decision']=='ACCEPT' and gate['adapter_SHA']==ADAPTER_SHA
    assert gate['amendment_SHA']==AMENDMENT_SHA==fs.sha(ROUND+'/plans/postverify_handoff_repair_amendment.json')
    return dict(path=str(fs.recorded/pathlib.PureWindowsPath(relative)),SHA=fs.sha(relative),
        amendment_SHA=gate['amendment_SHA'],policy=gate['policy'])

def clone_replay(reader,fs,stored_total,replay_tick):
    original=inspect.getsource(reader.verify);source=original;changes=[]
    substitutions=[
        ("tick=time.perf_counter();d=Path(launch['destination']);p=launch['panel']",
         "tick=portable_stored_total['t_verified_perf'];d=Path(launch['destination']);p=launch['panel']"),
        ("assert not (d/'verification_closeout.json').exists(),'closed verification is immutable; rebuild only aggregates it'",
         "assert (d/'verification_closeout.json').is_file(),'portable replay requires the immutable measured closeout'"),
        ('verified=time.perf_counter()',"verified=portable_stored_total['t_verified_perf']"),
        ('t_verified_unix=time.time()',"t_verified_unix=portable_stored_total['t_verified_unix']"),
        ('seconds=time.perf_counter()-tick','seconds=portable_replay_elapsed()'),
    ]
    for old,new in substitutions:
        assert source.count(old)==1,('unrecognized frozen verifier transport site',old)
        source=source.replace(old,new);changes.append(dict(before=old,after=new,count=1))
    namespace=dict(vars(reader),portable_stored_total=stored_total,
        portable_replay_elapsed=lambda:time.perf_counter()-replay_tick)
    exec(compile(source,str(fs.root/'scripts/round133_read.py')+'::portable_closed_replay','exec'),namespace)
    return namespace['verify'],dict(original_source_SHA=digest(original.encode()),cloned_source_SHA=digest(source.encode()),
        exhaustive_substitution_whitelist=changes,
        source_physical_model_H_Start_return_cover_source_predicates_changed=False,
        execution_environment_substitutions=['strict recorded-root path transport',
            'published pinned source map instead of Git',
            'historical native asset execution attestations instead of unavailable local asset remeasurement',
            'named in-memory derived JSON writes; original restored bytes retained'])

def normalized(fs,value,hash_tokens,path=()):
    if path==('audit.json','neutral_exchange_replay','offline_seconds'):
        assert type(value) in (int,float) and math.isfinite(value) and value>=0
        return '@new_independent_offline_replay_wall'
    if isinstance(value,dict):return {key:normalized(fs,item,hash_tokens,path+(key,)) for key,item in value.items()}
    if isinstance(value,list):return [normalized(fs,item,hash_tokens,path+(str(i),)) for i,item in enumerate(value)]
    if isinstance(value,str):
        if value in hash_tokens:return hash_tokens[value]
        text=value.replace('\\','/')
        old=str(fs.recorded).replace('\\','/');new=str(fs.root).replace('\\','/')
        for prefix in (old,new):
            if text.lower()==prefix.lower():return '@recovery-root'
            if text.lower().startswith(prefix.lower().rstrip('/')+'/'):return '@repo/'+text[len(prefix.rstrip('/'))+1:]
    return value

def compare_derived(fs,d,stored):
    expected={name:digest(raw) for name,raw in stored.items()}
    replay={name:fs.sha(d/name) for name in stored}
    old_tokens={value:'@derived:'+name for name,value in expected.items()}
    new_tokens={value:'@derived:'+name for name,value in replay.items()}
    compared=[]
    for name,raw in stored.items():
        assert str(fs.resolve(d/name)) in fs.overlay,('full replay did not regenerate a derived output',name)
        before=normalized(fs,json.loads(raw),old_tokens,(name,))
        after=normalized(fs,fs.read(d/name),new_tokens,(name,))
        assert before==after,('full replay semantic mismatch',name)
        compared.append(dict(name=name,stored_SHA=expected[name],virtual_replay_SHA=replay[name],
            normalized_semantics_SHA=digest(canonical(before).encode())))
    return compared

def replay_arm(fs,reader,adapter,launch,identity,formal,group=None):
    d=fs.Path(launch['destination']);replay_tick=time.perf_counter()
    assert not fs.overlay and not fs.allowed_writes
    stored={name:fs.raw(d/name) for name in DERIVED if fs.exists(d/name)}
    assert all(name in stored for name in ('audit.json','verification_closeout.json','arm_total_receipt.json','round133_endpoint.json'))
    stored_total=fs.read(d/'arm_total_receipt.json')
    # Validate the actual measured arithmetic/links before any virtual write.
    clock=importlib.import_module('round115_common').clock_evidence(d,launch)
    assert clock['T_verify']==stored_total['T_verify'] and clock['T_total']==stored_total['T_total']
    management=None
    if formal:
        assert group is not None
        management=adapter.validate_effective_receipt(d,launch,group['identity_SHA'],original_gate(fs),
            attempt_root=fs.Path(fs.root/ROUND/'repair/postverify_handoff'))
        # The actual approved adapter source is executed, not inferred from the
        # old reader's SHA. Its H/PS replacements are installed post-seal only.
        context=adapter.postseal_functions(d,d/'round133_verification_failure.json')
    else:
        assert reader.startup.reconstruct is adapter._RECONSTRUCT
        assert reader.compact_start.start_audit is adapter._START_AUDIT
        context=contextlib.nullcontext()
    fs.allowed_writes={str(fs.resolve(d/name)) for name in (*DERIVED,'round133_verification_failure.json')}
    clone=None
    try:
        with context:
            verify,clone=clone_replay(reader,fs,stored_total,replay_tick)
            result=verify(launch,identity)
        assert str(fs.resolve(d/'round133_verification_failure.json')) not in fs.overlay
        compared=compare_derived(fs,d,stored)
        arm=result['arm'];assert arm['T_produce']==clock['T_produce']
        assert arm['T_verify']==clock['T_verify'] and arm['T_total']==clock['T_total']
        return dict(arm_id=launch['arm_id'],formal=formal,full_replay=True,
            actual_policy='8feae approved accepted-H adapter' if formal else '933 frozen original unit policy',
            effective_management_receipt=management,source_rewrite_binding=clone,
            stored_clock=clock,compared_outputs=compared,
            independent_replay_wall_seconds=time.perf_counter()-replay_tick,
            implementation_qualified=arm['implementation_qualified'],certificate=arm['certificate'],
            source_reduced=arm['source_reduced'],model_scope_qualified=arm['model_scope_qualified'],
            generic_reader_performance_evidence_eligible=arm['performance_evidence_eligible'],
            role_performance_evidence_eligible=arm['performance_evidence_eligible'] if formal else False)
    finally:
        fs.overlay.clear();fs.allowed_writes.clear()

def unit_oracle(fs,reader,manifest,identity):
    base=fs.root/ROUND/'qualification/small_native01'
    assert fs.sha(base/'inventory_oracle.json')==manifest['oracle_SHA']
    oracle=fs.read(base/'inventory_oracle.json');analysis=fs.read(base/'analysis.json')
    rows=oracle['original_integer_inventories'];assert len(rows)==3
    assert {tuple(row['Y']) for row in rows}=={(0,0),(0,1),(1,0)}
    for row in rows:
        a,b=row['Y'];tau=a+b;assert tau in (0,1) and row['tau']==tau
        g=Fraction(abs(a-b),2*tau) if tau else Fraction(0)
        penalty=abs(a-1)+abs(b-1)
        assert Fraction(row['G'])==g and row['P']==penalty and Fraction(row['F'])==g+penalty
    assert min(Fraction(row['F']) for row in rows)==Fraction(3,2)
    assert oracle['exact_original_optimum']=='3/2' and oracle['initial']==[1,0]
    assert oracle['targets']==[1,1] and oracle['capacities']==[2,2] and oracle['weights']==[1,1]
    assert oracle['Q']==[1] and oracle['lambda_value']=='1' and oracle['possible_total_inventory']==[0,1]
    assert oracle['not_supplied_as_Start_incumbent_cutoff_bound_or_cache']
    assert oracle['root_relaxation_inventory']==['1/2','1/2'] and oracle['root_relaxation_objective_candidate']=='1'
    launch=identity['launches'][0];p=launch['panel'];d=fs.Path(launch['destination'])
    witnesses=[dict(objective=1.5,routes=[dict(vehicle=0,nodes=[0,0],operations=[])]),
        dict(objective=2.,routes=[dict(vehicle=0,nodes=[0,1,0],operations=[dict(station=1,pickup=1,drop=0)])])]
    physical=[reader.core.full_fleet(fs.Path(fs.root),p,w) for w in witnesses]
    assert physical[0]['F']==1.5 and physical[1]['F']==2 and physical[1]['G']==0
    assert physical[1]['return_loads']==[1] and physical[1]['maximum_duration']==120
    assert analysis['passed'] and analysis['fixture_manifest_SHA']==UNIT_SHA
    assert analysis['exact_independent_original_optimum']=='3/2'
    assert analysis['not_performance'] and analysis['performance_evidence_eligible'] is False
    assert analysis['new_performance_inputs']==0 and analysis['extra_Optimize']==0
    assert analysis['independent_no_op_loaded_return_S0_checks']==physical
    arm=fs.read(d/'round133_endpoint.json')
    assert abs(arm['U']-1.5)<=1e-7 and arm['L']<=1.5+1e-7
    assert analysis['own_U']==arm['U'] and analysis['qualified_L']==arm['L']
    controller=reader.core.evidence.controller_tables(d,fs.read(d/'result.json'))
    counts=collections.Counter(row['solve_kind'] for row in controller['controller_native'])
    assert analysis['LP_calls']==counts['LP'] and analysis['MIP_calls']==sum(v for k,v in counts.items() if k!='LP')
    return dict(fixed_inventory_vectors_checked=3,exact_inventory_lower_bound='3/2',attaining_no_op='3/2',
        loaded_return_S0_F='2',physical_checks=physical,formal_denominator_contribution=0,
        performance_evidence_eligible=False,new_enumeration_grid_or_Optimize=False)

def check(root,local_preflight=False):
    tick=time.perf_counter();fs=ClosedRoot(root)
    if local_preflight:
        assert fs.root==RealPath(__file__).resolve().parents[1]
        assert native_key(fs.root)==native_key(RECORDED_ROOT),'local preflight is limited to the explicit existing Round133 worktree'
    else:
        assert not (fs.root/'.git').exists(),'public recovery root must not contain a Git checkout'
        for path in fs.root.rglob('*'):
            assert not path.is_symlink(),('recovery artifacts may not link outside the empty root',str(path))
            if path.is_file():assert path.suffix.lower() not in {'.exe','.dll','.o','.obj','.a','.lib'},('native assets must not be distributed for recovery',str(path))
    candidate,matrices,unit,amendment=publication(fs)
    records=[]
    with closed_helpers(fs):
        reader=importlib.import_module('round133_read')
        adapter=importlib.import_module('round133_postverify_repair')
        assert fs.sha(reader.__file__)==READER_SHA and fs.sha(adapter.__file__)==ADAPTER_SHA
        for stage,matrix in matrices.items():
            for group in matrix['groups']:
                identity=fs.read(fs.root/ROUND/group['group']/'identity.json')
                records.append(replay_arm(fs,reader,adapter,group['launch'],identity,True,group))
        unit_base=fs.root/ROUND/'qualification/small_native01'
        identity_path=unit_base/'identity.json';assert fs.sha(identity_path)==unit['identity_SHA']
        unit_identity=fs.read(identity_path)
        assert unit['formal_performance'] is False and unit['new_performance_inputs']==0
        records.append(replay_arm(fs,reader,adapter,unit_identity['launches'][0],unit_identity,False))
        oracle=unit_oracle(fs,reader,unit,unit_identity)
    assert len(records)==23 and sum(row['formal'] for row in records)==22
    return dict(schema='round133-full-pure-policy-recovery-v1',passed=True,
        local_preflight=local_preflight,public_empty_root_recovery=not local_preflight,
        formal_positions=22,unit_positions=1,unit_in_formal_or_performance_denominator=False,
        records=records,unit_oracle=oracle,
        helper_archive_verified=True,actual_933_reader_and_8feae_adapter_executed=True,
        candidate_and_old_E3_source_bytes_verified=True,
        native_asset_verification='historical PE/DLL/object/library execution attestations only; none locally opened, loaded, compiled, exported or remeasured',
        zero_native_scope='No solver/vendor DLL API, native compiler, subprocess, Git process or Optimize. Python standard-library runtime and source loading are separate.',
        attestations_used=list(fs.attestations_used.values()),
        native_assets_declared=list(fs.attestations.values()),
        original_measured_clocks_preserved=True,derived_writes='captured in memory only; restored bytes never overwritten',
        Optimize=0,compile=0,native_compile=0,DLL_load=0,vendor_DLL_load=0,
        DLL_load_scope='solver/vendor only; Python runtime separately recorded',
        Python_standard_runtime_initialization=PYTHON_RUNTIME_LIBRARY_LOADS,
        ctypes_preloaded_at_checker_import=CTYPES_PRELOADED,subprocess_calls=0,Git_calls=0,
        new_scientific_enumeration=0,independent_replay_wall_seconds=time.perf_counter()-tick,
        artifact_paths_read=len(fs.read_paths),source_publication_SHA=fs.sha(fs.root/ROUND/'source_publication.json'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=RealPath,required=True)
    parser.add_argument('--local-preflight',action='store_true')
    options=parser.parse_args()
    # Print one independent report; no report/artifact file is created in root.
    result=check(options.root,options.local_preflight)
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),flush=True)

if __name__=='__main__':main()
