"""Traceable post-seal re-audit into an exclusive new derived-output view.

All raw/failed prior files stay at their original paths and are byte-checked.
The inherited complete audit and reconstruction read their new derived files
through the same view. There is no native entry point or solver import here.
"""
from round121_common import ROOT,OUT,read,write,sha,helpers,bindings,utc
from pathlib import Path
import builtins,collections,contextlib,fnmatch,os,time,traceback
from round108_reader import portable

DERIVED=frozenset(['round120_model_contracts.json','call_log_views.json','computed_seed_scope.json',
    'independent_evidence.json','native_claims.json','claim_rejections.json','audit.json',
    'audit_execution_metrics.json','postexit_audit_receipt.json','verification_closeout.json',
    'arm_total_receipt.json','round120_extended_verification.json','round120_event_contract.json'])

def file_hashes(directory):
    return {p.relative_to(directory).as_posix():sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}

def producer_identity(l,current):
    """Keep the real old producer preregistration, with final auditor binding.

    Endpoint's saved-launch SHA assertion remains unchanged. Only the two
    preserved H100 producers may use the verified original producer identity.
    New D0/D1 producers use the amended execution identity.
    """
    if l['id']!='H100' or l['arm'] not in ['P-GRB','M-B']:return current
    authorization=read(OUT/'resumption/authorization01.json');path=OUT/'qualification/h100/identity.json'
    assert sha(path)==authorization['original_H100_identity_SHA']
    auditor=OUT/'qualification/resume01/identity.json'
    assert current==read(auditor),'unbound final auditor identity supplied'
    assert current['prereg_sha256']==sha(OUT/'protocol.json')
    assert current['resume_authorization_SHA']==sha(OUT/'resumption/authorization01.json')
    assert current['original_producer_identity_SHA']==sha(path)
    assert read(OUT/'candidate_identity.json')['resumed_qualification_identity_SHA']==sha(auditor)
    old=read(path);raw=portable(ROOT,l['destination']);saved=read(raw/'launch.json')
    assert l==next(q for q in old['launches'] if q['arm']==l['arm'])
    assert current['launches']==old['launches'] and current['prereg']==old['prereg'] and current['references']==old['references']
    assert current['source_hashes']==old['source_hashes']==bindings()
    assert current['candidate_binary_sha256']==old['candidate_binary_sha256']
    assert current['dll_sha256']==old['dll_sha256'] and current['helpers']==helpers()
    assert sha(OUT/'resumption/before_resume01/protocol.json')==old['prereg_sha256']==authorization['original_protocol_SHA']
    assert saved['command']==l['command'] and saved['panel']==l['panel'] and saved['seed']==l['seed']==1
    assert saved['prereg_sha256']==old['prereg_sha256'] and saved['runner_sha256']==old['runner_sha256']
    preserved=read(OUT/'qualification/minimum_admission_plan.json')['preserved_producers'][l['arm']]
    assert sha(raw/'producer_receipt.json')==preserved['receipt_SHA'] and sha(raw/'producer_seal.json')==preserved['seal_SHA']
    return old

@contextlib.contextmanager
def derived_view(raw,attempt):
    """Overlay only the named post-seal sidecars; never redirect native data."""
    raw=Path(raw).resolve();attempt=Path(attempt).resolve()
    assert raw.is_dir() and attempt.is_dir() and not attempt.is_relative_to(raw)
    path_open,path_stat,path_mkdir,path_glob,path_iterdir,regular_open=(Path.open,Path.stat,Path.mkdir,Path.glob,Path.iterdir,builtins.open)
    writes=[]
    def absolute(value):return Path(os.path.abspath(os.fspath(value)))
    def existing(path):
        try:path_stat(path);return True
        except FileNotFoundError:return False
    def target(path,mode='r'):
        if isinstance(path,int):return path
        actual=absolute(path);writing=any(ch in mode for ch in 'wxa+')
        if actual.is_relative_to(raw):
            name=actual.relative_to(raw).as_posix()
            if writing:
                assert name in DERIVED,('immutable producer/native file write attempted',name)
                replacement=attempt/name;path_mkdir(replacement.parent,parents=True,exist_ok=True)
                writes.append(name);return replacement
            if name in DERIVED and existing(attempt/name):return attempt/name
        if writing:assert actual.is_relative_to(attempt),('unexpected audit output',str(actual))
        return path
    def safe_path_open(self,mode='r',*args,**kwargs):return path_open(target(self,mode),mode,*args,**kwargs)
    def safe_open(file,mode='r',*args,**kwargs):return regular_open(target(file,mode),mode,*args,**kwargs)
    def safe_stat(self,*args,**kwargs):return path_stat(target(self),*args,**kwargs)
    def safe_mkdir(self,*args,**kwargs):
        actual=absolute(self)
        if actual==raw:return None
        if actual.is_relative_to(raw):raise AssertionError(('audit may not create native directory',str(actual)))
        assert actual.is_relative_to(attempt),('unexpected audit directory',str(actual))
        return path_mkdir(self,*args,**kwargs)
    def merged(self,original):
        values=list(original)
        if absolute(self)==raw:
            names={p.name for p in values}
            values.extend(raw/name for name in sorted(DERIVED) if name not in names and existing(attempt/name))
        return values
    def safe_iterdir(self):return iter(merged(self,path_iterdir(self)))
    def safe_glob(self,pattern,*args,**kwargs):
        values=list(path_glob(self,pattern,*args,**kwargs))
        if absolute(self)==raw:
            names={p.name for p in values}
            values.extend(raw/name for name in sorted(DERIVED) if name not in names and fnmatch.fnmatchcase(name,pattern) and existing(attempt/name))
        return iter(values)
    Path.open,Path.stat,Path.mkdir,Path.glob,Path.iterdir,builtins.open=(safe_path_open,safe_stat,safe_mkdir,safe_glob,safe_iterdir,safe_open)
    try:yield writes
    finally:Path.open,Path.stat,Path.mkdir,Path.glob,Path.iterdir,builtins.open=(path_open,path_stat,path_mkdir,path_glob,path_iterdir,regular_open)

def replay(l,identity,attempt):
    import round121_evidence as evidence
    import read_round118 as reader
    import read_round116 as inherited
    attempt=Path(attempt);attempt.mkdir(parents=True,exist_ok=False);raw=portable(ROOT,l['destination'])
    producer_ident=producer_identity(l,identity)
    before=file_hashes(raw);producer=read(raw/'producer_receipt.json');tick=time.perf_counter()
    assert all(before[n]==h for n,h in read(raw/'producer_seal.json')['required_SHA'].items())
    assert producer['producer_seal_SHA']==before['producer_seal.json']
    write(attempt/'attempt_started.json',dict(UTC=utc(),arm=l['arm'],raw=str(raw),helpers=helpers(),source_bindings=bindings(),
        original_all_file_SHA=before,producer_receipt_SHA=before['producer_receipt.json'],producer_seal_SHA=before['producer_seal.json'],
        original_T_produce=producer['T_produce'],native_starts=0,Optimize=0,
        producer_identity_SHA=sha(OUT/'qualification/h100/identity.json'),producer_prereg_SHA=producer_ident['prereg_sha256'],
        final_auditor_identity_SHA=sha(OUT/'qualification/resume01/identity.json'),
        final_protocol_SHA=sha(OUT/'protocol.json'),authorization_SHA=sha(OUT/'resumption/authorization01.json')))
    error=None;endpoint=None
    try:
        with derived_view(raw,attempt) as writes:
            value=evidence.verify(l,producer_ident);assert value['passed'] and value['native_proof_qualified']
            recs=collections.defaultdict(list)
            with evidence.extension():
                item=reader.item(ROOT,l,producer_ident,recs);assert item['complete']
                final=inherited.reconcile(item['claims'],item['ind']['witnesses']);assert not final['rejections']
                endpoint=reader.finalize(ROOT,item,final,recs)
            assert endpoint['formal_protocol_qualified'] and endpoint['numbers_qualified'] and endpoint['actually_executed']
            assert endpoint['T_produce']==producer['T_produce']
            total=read(raw/'arm_total_receipt.json')
            assert total['T_verify']==total['t_verified_perf']-producer['t_produce_perf']
            assert total['T_total']==total['t_verified_perf']-producer['t0_perf']
    except BaseException:
        error=traceback.format_exc();(attempt/'failure.txt').write_text(error,encoding='utf-8')
    after=file_hashes(raw);assert before==after,'re-audit mutated original native/failed evidence'
    result=dict(passed=error is None,arm=l['arm'],seed=l['seed'],raw=str(raw),attempt=str(attempt),
        helpers=helpers(),source_bindings=bindings(),original_all_file_SHA=before,original_all_bytes_unchanged=True,
        producer_receipt_SHA=before['producer_receipt.json'],producer_seal_SHA=before['producer_seal.json'],
        original_T_produce=producer['T_produce'],endpoint=endpoint,derived_file_SHA=file_hashes(attempt),
        producer_identity_SHA=sha(OUT/'qualification/h100/identity.json'),producer_prereg_SHA=producer_ident['prereg_sha256'],
        final_auditor_identity_SHA=sha(OUT/'qualification/resume01/identity.json'),
        final_protocol_SHA=sha(OUT/'protocol.json'),authorization_SHA=sha(OUT/'resumption/authorization01.json'),
        exclusive_attempt=True,old_failed_audit_preserved=True,new_recovery_closeout_not_original_receipt=True,
        verification_gap_since_original_seal_not_removed=True,clock_policy_unchanged=True,
        replay_seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,error=error)
    write(attempt/'traceable_receipt.json',result)
    assert result['passed'],error
    return result

@contextlib.contextmanager
def saved_view(raw,attempt):
    attempt=Path(attempt);r=read(attempt/'traceable_receipt.json');assert r['passed'] and r['helpers']==helpers() and r['source_bindings']==bindings()
    assert file_hashes(Path(raw))==r['original_all_file_SHA']
    assert all(sha(attempt/n)==h for n,h in r['derived_file_SHA'].items())
    with derived_view(raw,attempt):yield r

def finite_fixture(output):
    """Actual old-audit collision, new-file visibility and immutable-raw checks."""
    import tempfile
    checks=[]
    with tempfile.TemporaryDirectory(prefix='r121-recovery-fixture-') as temporary:
        root=Path(temporary).resolve()
        assert root.parent==Path(tempfile.gettempdir()).resolve() and root.name.startswith('r121-recovery-fixture-')
        raw=root/'raw';attempt=root/'new';raw.mkdir();attempt.mkdir()
        write(raw/'audit.json',dict(passed=False,error='retained prior failure'));write(raw/'result.json',dict(immutable=True))
        before=file_hashes(raw);saved_open=Path.open;saved_stat=Path.stat
        with derived_view(raw,attempt):
            with (raw/'audit.json').open('x',encoding='utf-8') as f:f.write('{"passed":true}')
            assert read(raw/'audit.json')==dict(passed=True);checks.append('existing_failed_audit_exclusive_rewrite_is_new_file')
            write(raw/'arm_total_receipt.json',dict(T_produce=1,T_verify=9,T_total=10))
            assert (raw/'arm_total_receipt.json').is_file();checks.append('new_sidecar_exists_and_is_file')
            assert 'arm_total_receipt.json' in {p.name for p in raw.glob('*.json')}
            assert 'arm_total_receipt.json' in {p.name for p in raw.iterdir()};checks.append('glob_and_iterdir_see_new_sidecar')
            assert sha(raw/'audit.json')==sha(attempt/'audit.json');checks.append('read_and_SHA_share_new_view')
            try:write(raw/'result.json',dict(immutable=False))
            except AssertionError:checks.append('native_or_sealed_output_write_rejected')
            else:raise AssertionError('native write allowed')
        assert Path.open is saved_open and Path.stat is saved_stat;checks.append('bindings_restored_after_view')
        assert file_hashes(raw)==before and read(raw/'audit.json')['passed'] is False;checks.append('all_original_failed_and_native_bytes_retained')
        assert not (raw/'arm_total_receipt.json').exists();checks.append('new_closeout_does_not_replace_original_history')
    write(output,dict(checks=checks,Optimize=0,native_starts=0))
    return checks
