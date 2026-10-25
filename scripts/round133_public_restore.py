"""One-root anonymous fixed-commit recovery of the current Round133 payload.

Transport rules derive from the passed R130 recovery (also reused for R132):
HTTPS-only System32 curl with curlrc disabled, fixed forty-hex commit, explicit
SHA/size materialization, member-index/CRC checks, and same owned root on resume.
Local/in-memory checks cover URI, ownership, exact-byte and source-ZIP contracts;
the real fixed-commit HTTPS recovery remains a separate one-root operation.

Only the 23--24 current carriers and one explicitly pinned tiny dependency are
fetched. No native asset, compiler, Git process, old checkout or local raw cache
is used. Python checker subprocesses are pure recovery helpers, not Optimize.
"""
from pathlib import Path, PurePosixPath
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import argparse, datetime, gzip, hashlib, io, json, os, re, shutil, stat
import subprocess, sys, threading, time, zipfile, zlib

OUT='results/unified_exact_round133'
MANIFEST=OUT+'/export_manifest.json'
OWNER='Round133 single fixed-science-commit public recovery'
ALLOWED_ROOT=Path('E:/codes/ExactEBRP-work/restore')
BUDGETS=dict(total=7200.,transport=1800.,semantic=3600.)
PORTABLE_SHA='6024c92660aed5d78a6fade0f371cac4621bc822d74008296a5539319b93a37d'
TINY=dict(source_commit='52b02252ba47e8228b73e071d6ed692385a4f816',
    source_path='results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip',
    target='inherited_dependencies/complete_tiny_joint_study.zip',bytes=213859,
    SHA256='d2e55d7ae5fcaf5bb0c9d39a489b589006f3a29eb350b167fd790ad399a0aac1')
FORBIDDEN={'.exe','.dll','.o','.obj','.a','.lib','.lic','.ttf','.otf','.woff','.woff2'}

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.pending')
    with temp.open('w',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')
    os.replace(temp,path)
def junction(path):return bool(getattr(Path(path),'is_junction',lambda:False)())
def no_links(path):
    path=Path(path)
    for node in (path,*path.parents):
        if node.exists():assert not node.is_symlink() and not junction(node),('linked recovery path',str(node))
def safe_name(name):
    assert type(name) is str and name and not any(ord(c)<32 for c in name)
    rel=PurePosixPath(name)
    assert rel.as_posix()==name and not rel.is_absolute() and '..' not in rel.parts
    assert all(part not in ('','.','..') and ':' not in part and '\\' not in part for part in rel.parts)
    assert '.git' not in rel.parts and Path(name).suffix.lower() not in FORBIDDEN,('forbidden publication path',name)
    return rel

def current_file(name):
    safe_name(name)
    return (name.startswith(OUT+'/') or
        (name.startswith('scripts/round133') and name.endswith('.py')) or
        (name.startswith('tests/round133') and name.endswith('.cpp')) or
        name in {'tests/native_evidence_journal_tests.cpp','.gitattributes','WORKSPACE_POLICY.md',
                 'results/unified_exact_round94/preregistration.json'})

def validate_resume_state(state,commit,destination,resume):
    # A PASS owner state is final even if the old receipt was removed or a
    # caller supplies a different receipt filename in the same parent folder.
    assert state['status']!='PASS', 'completed owned-root public recovery is immutable, regardless of receipt filename or existence'
    assert resume and state['commit']==commit and state['owner']==OWNER and state['initially_empty']
    assert state['destination']==str(destination)
    assert state['status'] in {'NEW','FAILED_PRESERVE_SAME_ROOT'}, 'unclosed/unknown attempt requires explicit main-agent exit audit; preserve this root'

class Limits:
    def __init__(self,prior):
        self.tick=time.perf_counter();self.phase_tick=self.tick;self.phase='transport'
        self.prior={key:float(prior.get(key,0.)) for key in BUDGETS}
        self.current=dict(transport=0.,semantic=0.)
    def spent(self,key):
        now=time.perf_counter()
        if key=='total':return self.prior[key]+now-self.tick
        return self.prior[key]+self.current[key]+(now-self.phase_tick if self.phase==key else 0.)
    def remaining(self,key):
        assert key==self.phase
        left=min(BUDGETS[key]-self.spent(key),BUDGETS['total']-self.spent('total'))
        assert left>0,('finite public recovery limit exhausted',key,self.snapshot())
        return left
    def change(self,key):
        now=time.perf_counter();self.current[self.phase]+=now-self.phase_tick
        self.phase=key;self.phase_tick=now;self.remaining(key)
    def snapshot(self):return {key:self.spent(key) for key in BUDGETS}

class Recovery:
    def __init__(self,dest,commit,attempt,limits):
        self.dest=dest;self.commit=commit;self.attempt=attempt;self.limits=limits
        self.failures=[];self.transfers=[];self.transforms=[];self.installed=[]
        self.lock=threading.Lock();self.serial=0;self.payload={};self.extracted={}
        self.curl=Path(os.environ['WINDIR'])/'System32/curl.exe'
        assert self.curl.is_file()
    def path(self,name,create=False):
        relative=safe_name(name);path=self.dest.joinpath(*relative.parts)
        no_links(path)
        assert path.absolute().is_relative_to(self.dest)
        if create:path.parent.mkdir(parents=True,exist_ok=True);no_links(path.parent)
        assert path.resolve(strict=False).is_relative_to(self.dest)
        return path
    def status(self,phase,**details):
        with self.lock:
            write(self.attempt/'status.json',dict(UTC=utc(),phase=phase,
                cumulative_seconds=self.limits.snapshot(),**details))
    def staging(self,name):
        with self.lock:self.serial+=1;number=self.serial
        parent=self.attempt/'staging';parent.mkdir(parents=True,exist_ok=True)
        return parent/f'{number:07d}_{digest(name.encode())[:20]}.partial'
    def install_stream(self,name,source,expected_bytes,expected_SHA,expected_CRC=None):
        """Only validated complete bytes enter the owned scientific root."""
        self.limits.remaining('transport');target=self.path(name,True)
        assert isinstance(expected_bytes,int) and expected_bytes>=0 and re.fullmatch('[0-9a-f]{64}',expected_SHA)
        if target.exists():
            assert target.is_file() and target.stat().st_size==expected_bytes and sha(target)==expected_SHA,('changed same-root materialization',name)
            temporary=None;output=None
        else:
            temporary=self.staging(name);output=temporary.open('xb')
        h=hashlib.sha256();count=0;crc=0
        try:
            for chunk in iter(lambda:source.read(1048576),b''):
                self.limits.remaining('transport');h.update(chunk);count+=len(chunk);crc=zlib.crc32(chunk,crc)
                assert count<=expected_bytes,('member exceeds registered size',name)
                if output:output.write(chunk)
        finally:
            if output:output.close()
        assert count==expected_bytes and h.hexdigest()==expected_SHA,('published member bytes',name)
        if expected_CRC is not None:assert (crc&0xffffffff)==expected_CRC,('ZIP CRC mismatch',name)
        if temporary:
            assert temporary.stat().st_size==expected_bytes and sha(temporary)==expected_SHA
            assert not target.exists(),'concurrent recovery writer is not permitted'
            # Both the owned root and external receipts are on the allowed E:
            # volume; no recursive move/delete or computed-directory removal.
            os.replace(temporary,target)
        self.installed.append(dict(path=name,bytes=count,SHA256=expected_SHA,
            CRC32=f'{crc&0xffffffff:08x}' if expected_CRC is not None else None,
            existing_verified_same_root=temporary is None))
        return target
    def install_bytes(self,name,data,SHA=None):
        return self.install_stream(name,io.BytesIO(data),len(data),SHA or digest(data))
    def get(self,name,commit=None):
        safe_name(name);commit=commit or self.commit
        assert re.fullmatch('[0-9a-f]{40}',commit)
        url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/'+quote(name,safe='/')
        for number in range(1,4):
            try:
                remaining=self.limits.remaining('transport');timeout=min(60.,remaining)
                assert timeout>=1
                command=[str(self.curl),'--disable','--proto','=https','--proto-redir','=https',
                    '--fail','--location','--silent','--show-error','--max-time',str(timeout),url]
                result=subprocess.run(command,capture_output=True,timeout=min(timeout+3,remaining))
                assert result.returncode==0,(result.returncode,result.stderr.decode('utf-8',errors='replace'))
                self.transfers.append(dict(path=name,commit=commit,bytes=len(result.stdout),SHA256=digest(result.stdout),
                    anonymous_public_HTTPS=True,ordinary_TLS_validation=True,curlrc_disabled=True,
                    application_credentials_supplied=False))
                return result.stdout
            except Exception as error:
                self.failures.append(dict(path=name,commit=commit,attempt=number,error=repr(error)))
                if number==3:raise
    def fetch(self,row):
        name=row['path'];path=self.path(name,True)
        if path.exists():
            assert path.stat().st_size==row['bytes'] and sha(path)==row['SHA256'],('owned-root file changed',name)
            return
        raw=self.get(name);data=raw
        if digest(data)!=row['SHA256'] and row.get('serialization','').startswith('exact bytes;'):
            lf=raw.replace(b'\r\n',b'\n')
            for candidate,mode in ((lf,'LF'),(lf.replace(b'\n',b'\r\n'),'CRLF')):
                if len(candidate)==row['bytes'] and digest(candidate)==row['SHA256']:
                    data=candidate;self.transforms.append(dict(path=name,materialization=mode,
                        transport_SHA256=digest(raw),registered_SHA256=row['SHA256'],
                        exact_hash_and_size_recovered=True));break
        assert len(data)==row['bytes'] and digest(data)==row['SHA256'],('manifest byte identity',name)
        self.install_bytes(name,data,row['SHA256'])

    def download(self):
        blob=self.get(MANIFEST);manifest=json.loads(blob)
        assert manifest['schema']=='round133-finite-current-public-export-v1'
        assert manifest['fixed_science_commit_is_required_from_caller'] and manifest['no_HEAD_or_local_raw_fallback']
        assert manifest['old_34_carriers_unchanged'] and manifest['one_owned_empty_root']
        assert manifest['Optimize']==manifest['compilation']==0
        self.install_bytes(MANIFEST,blob)
        rows=manifest['files'];assert len(rows)==manifest['file_count']
        self.payload={row['path']:row for row in rows};assert len(self.payload)==len(rows) and MANIFEST not in self.payload
        for row in rows:assert current_file(row['path']),('file outside the fixed current payload',row['path'])
        self.status('download_current_manifest_payload',files=len(rows))
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(self.fetch,row) for row in rows]
            for future in futures:future.result()
        dependencies=manifest['external_dependencies'];assert len(dependencies)==1
        tiny=dependencies[0]
        assert all(tiny[key]==value for key,value in TINY.items()),'unregistered historical recovery dependency'
        target=self.path(tiny['target'],True)
        if target.exists():assert target.stat().st_size==tiny['bytes'] and sha(target)==tiny['SHA256']
        else:
            raw=self.get(tiny['source_path'],tiny['source_commit'])
            assert len(raw)==tiny['bytes'] and digest(raw)==tiny['SHA256']
            self.install_bytes(tiny['target'],raw,tiny['SHA256'])
        return manifest

    def extract_current(self,manifest):
        archive_path=manifest['archive_manifest'];assert archive_path==OUT+'/raw_archive_manifest.json'
        assert archive_path in self.payload
        carrier_manifest=read(self.path(archive_path));assert carrier_manifest['schema']=='round133-finite-current-carriers-v1'
        groups=[]
        for stage in ('D1','D3'):groups.extend(read(self.path(OUT+f'/plans/{stage}_matrix_frozen.json'))['groups'])
        assert len(groups)==22
        formal={group['group'].replace('/','_')+'.zip':OUT+'/'+group['group']+'/' for group in groups}
        support='diagnostics_qualification_math_dependencies_closed_fees.zip'
        optional='current_native_progress.zip'
        archives=carrier_manifest['archives'];names={row['name'] for row in archives}
        assert len(names)==len(archives) and names in (set(formal)|{support},set(formal)|{support,optional})
        assert len(archives) in (23,24),'only current Round133 carriers may be restored'
        extracted=[]
        for archive in archives:
            self.status('extract_current_carrier',carrier=archive['name'])
            pieces=archive['pieces'];assert pieces and len({part['path'] for part in pieces})==len(pieces)
            for part in pieces:
                assert part['path'] in self.payload
                registered=self.payload[part['path']]
                assert part['bytes']==registered['bytes'] and part['SHA256']==registered['SHA256']
                p=self.path(part['path']);assert p.stat().st_size==part['bytes'] and sha(p)==part['SHA256']
            if len(pieces)>1:
                assert [int(re.search(r'\.part(\d+)$',part['path'])[1]) for part in pieces]==list(range(1,len(pieces)+1))
            joined_name='archive_transport/'+archive['name'];joined=self.path(joined_name,True)
            if not joined.exists():
                stage=self.staging(joined_name)
                with stage.open('xb') as output:
                    for part in pieces:
                        with self.path(part['path']).open('rb') as source:
                            for chunk in iter(lambda:source.read(1048576),b''):
                                self.limits.remaining('transport');output.write(chunk)
                assert stage.stat().st_size==archive['compressed_bytes'] and sha(stage)==archive['SHA256']
                os.replace(stage,joined)
            assert joined.stat().st_size==archive['compressed_bytes'] and sha(joined)==archive['SHA256']
            index=archive['member_index'];assert index['path'] in self.payload
            compressed=self.path(index['path']).read_bytes()
            assert len(compressed)==index['bytes'] and digest(compressed)==index['SHA256']
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as source:decoded=source.read(index['decoded_bytes']+1)
            assert len(decoded)==index['decoded_bytes'] and digest(decoded)==index['decoded_SHA256']
            members=json.loads(decoded);by={row['path']:row for row in members}
            assert len(by)==len(members)==archive['file_count']==index['members']
            assert sum(row['bytes'] for row in members)==archive['uncompressed_bytes']
            with zipfile.ZipFile(joined) as z:
                assert len(z.infolist())==len(by) and set(z.namelist())==set(by)
                for info in z.infolist():
                    name=info.filename;safe_name(name);row=by[name]
                    assert not info.is_dir() and not stat.S_ISLNK(info.external_attr>>16)
                    assert info.file_size==row['bytes']
                    if archive['name'] in formal:assert name.startswith(formal[archive['name']])
                    elif archive['name']==support:
                        assert name.startswith(OUT+'/') and PurePosixPath(name).relative_to(OUT).parts[0] in {
                            'diagnostics','qualification','math','dependencies','infra','repair','fees'}
                    else:assert name.startswith('results/gurobi_work/')
                    assert name not in self.extracted,'current carrier member appears twice'
                    with z.open(info) as source:self.install_stream(name,source,row['bytes'],row['SHA256'],info.CRC)
                    self.extracted[name]=row
            extracted.append(dict(name=archive['name'],members=len(members),SHA256=archive['SHA256'],
                member_index_SHA256=index['SHA256'],ZIP_CRC_and_member_SHA_checked=True))
        return extracted

    def source_zip(self,row,expected):
        path=self.path(row['path']);assert path.stat().st_size==row['bytes'] and sha(path)==row['SHA']
        with zipfile.ZipFile(path) as z:
            assert len(z.infolist())==len(expected) and set(z.namelist())==set(expected)
            for info in z.infolist():
                safe_name(info.filename);assert not info.is_dir() and not stat.S_ISLNK(info.external_attr>>16)
                with z.open(info) as source:self.install_stream(info.filename,source,info.file_size,expected[info.filename],info.CRC)
        return dict(path=row['path'],SHA=row['SHA'],members=len(expected),exact_member_bytes_materialized=True)

    def materialize_sources(self,manifest):
        assert manifest['source_publication']==OUT+'/source_publication.json'
        pub=read(self.path(manifest['source_publication']));candidate=read(self.path(OUT+'/candidate_manifest.json'))
        assert pub['candidate_source_bundle']==candidate['executed_source_bytes']
        expected=dict(candidate['source_hashes'])
        expected['generated/CplexBaselineResearch.cpp']=candidate['generated_research_source']['SHA']
        assert pub['candidate_source_bundle']['members']==len(expected)
        candidate_receipt=self.source_zip(pub['candidate_source_bundle'],expected)
        helpers=pub['execution_helpers'];assert isinstance(helpers['members'],dict)
        helper_receipt=self.source_zip(helpers,helpers['members'])
        loose=[]
        assert len(pub['reused_main_source_and_bindings'])==4
        for row in pub['reused_main_source_and_bindings']:
            assert row['path'] in self.payload
            p=self.path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['SHA']
            assert 'attest' in row['object_identity'].lower()
            loose.append(dict(path=row['path'],SHA=row['SHA'],role=row['role']))
        for key,row in pub['old_E3_source_dependencies'].items():
            assert key==row['source_commit']+':'+row['source_path'] and row['path'] in self.payload
            p=self.path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['SHA']
        portable=self.path('scripts/round133_portable_check.py')
        assert sha(portable)==PORTABLE_SHA,'actual approved portable entry differs; register an explicit reader amendment first'
        return dict(candidate=candidate_receipt,execution_helpers=helper_receipt,reused_main_loose=loose,
            old_E3_named_source_count=len(pub['old_E3_source_dependencies']),
            PE_DLL_object_library='historical execution attestations only; never distributed or remeasured')

class Semantics:
    def __init__(self,recovery):self.recovery=recovery;self.records=[]
    def run_json(self,name,command,expected_receipt=None):
        recovery=self.recovery;remaining=recovery.limits.remaining('semantic')
        stdout=recovery.attempt/(name+'.stdout.log');stderr=recovery.attempt/(name+'.stderr.log')
        assert not stdout.exists() and not stderr.exists()
        environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        environment.pop('PYTHONPATH',None);environment.pop('PYTHONHOME',None)
        tick=time.perf_counter();recovery.status('pure_semantic_replay',checker=name)
        with stdout.open('xb') as out,stderr.open('xb') as err:
            result=subprocess.run(list(map(str,command)),cwd=recovery.dest,stdout=out,stderr=err,
                timeout=remaining,env=environment)
        assert result.returncode==0,('pure public replay failed; retain same root and logs',name,result.returncode)
        value=read(expected_receipt) if expected_receipt else json.loads(stdout.read_text(encoding='utf-8'))
        record=dict(name=name,command=list(map(str,command)),return_code=result.returncode,
            stdout=str(stdout),stdout_SHA=sha(stdout),stderr=str(stderr),stderr_SHA=sha(stderr),
            seconds=time.perf_counter()-tick,receipt=value,Optimize=0,native_compilation=0)
        self.records.append(record);return value

def required_exact_replay(semantics):
    """Mandatory directed exact checks, explicitly separate from the 23-arm replay."""
    recovery=semantics.recovery
    for name in ('round133_joint_check.py','round133_d24_point_check.py'):
        relative='scripts/'+name;assert relative in recovery.payload
        assert sha(recovery.path(relative))==recovery.payload[relative]['SHA256']
    tiny=recovery.path(TINY['target'])
    assert tiny.stat().st_size==TINY['bytes'] and sha(tiny)==TINY['SHA256']
    joint_receipt=recovery.attempt/'J2_J3_exact_receipt.json'
    joint=semantics.run_json('J2_J3_exact',
        [sys.executable,'-I','-B',recovery.path('scripts/round133_joint_check.py'),
         '--carrier',tiny,'--out',joint_receipt],joint_receipt)
    assert joint['status']=='PASS' and set(joint['cases'])=={'J2','J3'}
    assert all(row['proof_status']=='EXACT_LP_AND_IP' for row in joint['cases'].values())
    d24_receipt=recovery.attempt/'D24_exact_point_receipt.json'
    d24=semantics.run_json('D24_exact_point',
        [sys.executable,'-I','-B',recovery.path('scripts/round133_d24_point_check.py'),
         '--root',recovery.dest,'--out',d24_receipt],d24_receipt)
    assert d24['status']=='PASS' and d24['Optimize']==d24['native_starts']==d24['compilation']==0
    point=d24['complete_serialized_point']
    assert point['exactly_feasible'] and (point['rows'],point['columns'],point['equalities'])==(22996,9391,601)
    assert d24['source_remains']=='REJECTED' and len(d24['saved_loaded_signed_zero_only'])==3
    return dict(J2_J3_status='PASS',J2_J3_receipt=str(joint_receipt),J2_J3_SHA=sha(joint_receipt),
        D24_status='PASS',D24_receipt=str(d24_receipt),D24_SHA=sha(d24_receipt),
        no_old_campaign_expansion_or_native_replay=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True)
    parser.add_argument('--destination',type=Path,required=True);parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',args.commit),'a fixed science commit is required, never HEAD/branch'
    original_dest=args.destination.absolute();no_links(original_dest);no_links(ALLOWED_ROOT.absolute())
    dest=original_dest.resolve();allowed=ALLOWED_ROOT.resolve();receipt=args.receipt.absolute()
    no_links(receipt);receipt=receipt.resolve()
    assert dest.is_relative_to(allowed) and dest!=allowed and not receipt.is_relative_to(dest)
    assert receipt.drive.lower()==dest.drive.lower(),'external staging/receipts must remain on the same owned volume'
    owner_path=receipt.parent/'review/round133_owned_public_recovery_root.json'
    if owner_path.exists():
        owner=read(owner_path);assert owner['science_commit']==args.commit and owner['destination']==str(dest)
    state_path=dest/'restore_state.json'
    if dest.exists() and state_path.exists():
        state=read(state_path)
        validate_resume_state(state,args.commit,dest,args.resume)
    else:
        assert not args.resume and (not dest.exists() or not any(dest.iterdir())),'only a new owned empty root may be claimed'
        dest.mkdir(parents=True,exist_ok=True);no_links(dest)
        state=dict(commit=args.commit,owner=OWNER,destination=str(dest),initially_empty=True,
            created_UTC=utc(),status='NEW',cumulative_seconds=dict(total=0.,transport=0.,semantic=0.))
        write(state_path,state)
    if not owner_path.exists():write(owner_path,dict(science_commit=args.commit,destination=str(dest),created_UTC=utc(),one_owned_root=True))
    attempts=receipt.parent/'review/public_recovery_attempts';attempts.mkdir(parents=True,exist_ok=True)
    number=1
    while (attempts/f'attempt{number:02d}').exists():number+=1
    attempt=attempts/f'attempt{number:02d}';attempt.mkdir()
    if receipt.exists():
        prior=read(receipt);assert args.resume and prior['science_commit']==args.commit and prior['destination']==str(dest)
        assert prior['status']!='PASS','completed public recovery is immutable; read its receipt rather than run a second recovery'
        shutil.copyfile(receipt,attempt/'prior_receipt.json')
    limits=Limits(state['cumulative_seconds']);recovery=Recovery(dest,args.commit,attempt,limits)
    state.update(status='RUNNING',active_attempt=str(attempt),bootstrap_SHA=sha(__file__),budgets=BUDGETS)
    write(state_path,state);success=False
    try:
        manifest=recovery.download()
        archives=recovery.extract_current(manifest)
        sources=recovery.materialize_sources(manifest)
        limits.change('semantic');semantics=Semantics(recovery)
        portable=semantics.run_json('portable_formal22_unit1',
            [sys.executable,'-I','-B',recovery.path('scripts/round133_portable_check.py'),'--root',dest])
        assert portable['passed'] and portable['formal_positions']==22 and portable['unit_positions']==1
        assert portable['unit_in_formal_or_performance_denominator'] is False
        assert portable['Optimize']==portable['compile']==portable['DLL_load']==0
        assert portable['vendor_DLL_load']==0 and portable['DLL_load_scope']=='solver/vendor only; Python runtime separately recorded'
        exact=required_exact_replay(semantics)
        assert exact['J2_J3_status']=='PASS' and exact['D24_status']=='PASS'
        write(receipt,dict(status='PASS',science_commit=args.commit,destination=str(dest),attempt=str(attempt),
            export_manifest_SHA=sha(recovery.path(MANIFEST)),files=manifest['file_count'],archives=archives,
            source_materialization=sources,semantic_checks=semantics.records,required_exact_checks=exact,
            transport_failures_preserved=recovery.failures,transfers=recovery.transfers,
            Git_text_materializations=recovery.transforms,cumulative_seconds=limits.snapshot(),
            initially_empty_owned_root=True,one_owned_root_only=True,external_attempt_receipts=True,
            anonymous_fixed_commit_public_HTTPS=True,python_isolated_mode=True,
            helper_subprocesses_are_HTTPS_or_pure_Python=True,
            no_HEAD_Git_local_raw_or_old_checkout_fallback=True,old_34_carriers_not_redone=True,
            Optimize=0,native_starts=0,compilation=0,vendor_DLL_load=0))
        success=True
        print(json.dumps(dict(status='PASS',science_commit=args.commit,archives=len(archives),
            formal_positions=22,unit_positions=1,cumulative_seconds=limits.snapshot())),flush=True)
    except BaseException as error:
        write(receipt,dict(status='FAILED_PRESERVE_SAME_ROOT',science_commit=args.commit,destination=str(dest),
            attempt=str(attempt),error=repr(error),failures=recovery.failures,transfers=recovery.transfers,
            Git_text_materializations=recovery.transforms,cumulative_seconds=limits.snapshot(),
            no_fresh_empty_root_or_native_retry=True,Optimize=0,native_starts=0,compilation=0))
        raise
    finally:
        state.update(status='PASS' if success else 'FAILED_PRESERVE_SAME_ROOT',
            cumulative_seconds=limits.snapshot(),last_attempt=str(attempt),last_receipt=str(receipt),closed_UTC=utc())
        write(state_path,state)
        shutil.copyfile(state_path,attempt/'restore_state.json')
        if receipt.exists():shutil.copyfile(receipt,attempt/'receipt.json')

if __name__=='__main__':main()
