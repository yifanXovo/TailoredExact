"""Bounded v2 mock review and actual v1 transfer/export receipt cross-check.

No network, process launch, second export, decompression or all-member scan.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,io,json,subprocess,time,types,urllib.parse
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt
from post_formal_independent import typed_equal

V1='1916691438c43218a4afbfdea190754101c9939baf6c8b676bdc55c5e9bed4d3'
V2='58e71cbad072f88ae34040520355e48c6b33c95b262de2a28dc7d968cee10efe'
COMMIT='9ed88cf9da87c3ceb7aebc43694f865eacbc86a7'
def dump(n):return ast.dump(n,include_attributes=False)
def nodes(p):return {n.name:n for n in ast.parse(p.read_text(encoding='utf-8-sig')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

def run():
    tick=time.perf_counter();source=ROOT/'scripts/round122_public_https.py';old=OUT/'engineering/public_https_transport_v1.py'
    assert sha(source)==V2 and sha(old)==V1
    assert sha(ROOT/'scripts/round122_release.py')=='451331633e340155a49149a0a218eb3cf421bb9974e91b54d122a6c3b6090d12'
    previous,current=nodes(old),nodes(source)
    for name in ['arguments','system_https']:assert dump(previous[name])==dump(current[name])
    old_methods={n.name:n for n in previous['Response'].body if isinstance(n,ast.FunctionDef)}
    new_methods={n.name:n for n in current['Response'].body if isinstance(n,ast.FunctionDef)}
    for name in ['read','__enter__']:assert dump(old_methods[name])==dump(new_methods[name])
    revised=copy.deepcopy(current['run'])
    receipt_call=next(n for n in ast.walk(revised) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='dict' and any(k.arg=='local_curl_version_utility_processes' for k in n.keywords))
    extra=next(k for k in receipt_call.keywords if k.arg=='local_curl_version_utility_processes')
    assert isinstance(extra.value,ast.Constant) and extra.value.value==1
    receipt_call.keywords=[k for k in receipt_call.keywords if k.arg!='local_curl_version_utility_processes']
    assert dump(revised)==dump(previous['run'])
    init=new_methods['__init__'];unparse=ast.unparse(init)
    assert unparse.index('self.hash = hashlib.sha256()')<unparse.index('self.child = subprocess.Popen')
    protected=next(n for n in init.body if isinstance(n,ast.Try))
    assert any('child_creation(self.child)' in ast.unparse(n) for n in protected.body)
    assert 'self.close_owned(True)' in ast.unparse(protected.handlers[0])
    # Extract pure arguments and Response into a fake process namespace.
    current_child=[];calls=[]
    class Pipe:
        def __init__(self,owner,name,data=b''):self.owner=owner;self.name=name;self.data=io.BytesIO(data)
        def read(self,n=-1):self.owner.operation(self.name+'.read');return self.data.read(n)
        def close(self):self.owner.operation(self.name+'.close');self.data.close()
    class Child:
        pid=12345
        def __init__(self,fail=None):
            self.fail=dict(fail or {});self.calls=[];self.code=None
            self.stdout=Pipe(self,'stdout',b'original-pinned-public-bytes');self.stderr=Pipe(self,'stderr')
        def operation(self,name):
            self.calls.append(name)
            if self.fail.get(name,0)>0:
                self.fail[name]-=1
                if name=='wait':raise subprocess.TimeoutExpired('in-memory curl',10)
                raise OSError('in-memory '+name+' failure')
        def terminate(self):self.operation('terminate');self.code=-15
        def kill(self):self.operation('kill');self.code=-9
        def wait(self,timeout=None):
            assert timeout==10;self.operation('wait')
            if self.code is None:self.code=0
            return self.code
    mock=types.SimpleNamespace(PIPE=object(),Popen=lambda *a,**kw:current_child[-1])
    ns=dict(Path=Path,CURL=Path('C:/Windows/System32/curl.exe'),urllib=types.SimpleNamespace(parse=urllib.parse),hashlib=hashlib,time=time,subprocess=mock,
        child_creation=lambda child:1792176431.)
    for n in [current['arguments'],current['Response']]:exec(compile(ast.Module(body=[n],type_ignores=[]),'independent HTTPS cleanup fixtures','exec'),ns)
    req=types.SimpleNamespace(full_url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+COMMIT+'/results/unified_exact_round122/compact_evidence/manifest.json',get_method=lambda:'GET',data=None,headers={'User-agent':'TailoredExact-Round122-public-restore'})
    cases=[]
    def make(child,transfers):current_child.append(child);return ns['Response'](req,45,COMMIT,transfers)
    child=Child();transfers=[]
    with make(child,transfers) as r:data=r.read()
    assert child.calls[-2:]==['stderr.read','stderr.close'] and transfers[0]['owned_transfer_process_exited'] and transfers[0]['exit_code']==0
    assert transfers[0]['SHA256']==hashlib.sha256(data).hexdigest() and not transfers[0]['cleanup_errors']
    cases.append('normal_stream_unchanged_complete_exit_hash')
    ns['child_creation']=lambda child:(_ for _ in ()).throw(OSError('in-memory birth error'))
    child=Child();transfers=[]
    try:make(child,transfers)
    except OSError:pass
    else:raise AssertionError('birth injection did not fail')
    assert child.calls.count('wait')==1 and 'terminate' in child.calls and transfers[0]['owned_transfer_process_exited']
    assert transfers[0]['actual_creation_unix'] is None and transfers[0]['exit_code']==-15
    cases.append('constructor_birth_error_terminates_waits_records')
    ns['child_creation']=lambda child:1792176431.
    class BrokenList(list):
        def append(self,value):raise OSError('in-memory receipt registration failure')
    child=Child();current_child.append(child);obj=ns['Response'].__new__(ns['Response'])
    try:obj.__init__(req,45,COMMIT,BrokenList())
    except OSError:pass
    else:raise AssertionError('registration injection did not fail')
    assert obj.record['owned_transfer_process_exited'] and child.calls.count('wait')==1
    cases.append('constructor_registration_error_terminates_waits')
    fault_specs=[('close',{'stdout.close':1},None,True),('terminate',{'terminate':1},RuntimeError,False),
        ('wait',{'wait':1},None,True),('kill_then_retry',{'wait':2,'kill':1},None,True),
        ('stderr_read',{'stderr.read':1},None,True),('stderr_close',{'stderr.close':1},None,True),
        ('combined_close_terminate_wait',{'stdout.close':1,'terminate':1,'wait':1},RuntimeError,False)]
    for name,faults,kind,should_reject in fault_specs:
        child=Child(faults);transfers=[];r=make(child,transfers);rejected=False
        try:r.__exit__(kind,RuntimeError('in-memory body failure') if kind else None,None)
        except AssertionError:rejected=True
        assert rejected==should_reject and child.calls.count('wait')>=1 and transfers[0]['owned_transfer_process_exited']
        assert transfers[0]['cleanup_errors']
        cases.append(name+'_error_still_reaped_and_not_false_success')
    child=Child({'wait':3,'kill':2});transfers=[];r=make(child,transfers)
    try:r.__exit__(None,None,None)
    except AssertionError:pass
    else:raise AssertionError('permanent unreaped process falsely accepted')
    assert child.calls.count('wait')==3 and child.calls.count('kill')==2 and not transfers[0]['owned_transfer_process_exited'] and transfers[0]['exit_code'] is None
    cases.append('bounded_permanent_failure_explicitly_unreaped_rejected')
    # Bind actual V1 run to its exact preserved code and seven completed calls.
    transport_path=OUT/'delivery/system_https_transfer_receipt.json';export_path=OUT/'delivery/public_export_restore_receipt.json'
    transport,export=read(transport_path),read(export_path)
    assert transport['transport_adapter_SHA']==sha(old)==V1 and transport['release_helper_SHA']==sha(ROOT/'scripts/round122_release.py')
    assert transport['scientific_commit']==export['scientific_commit']==COMMIT
    assert transport['exit_code']==0 and transport['all_transfer_processes_exited'] and transport['solver_native_starts']==transport['Optimize']==0
    assert export['one_actual_public_carrier_export'] and export['members']==62310 and export['all_member_hashes_equal'] and export['no_original_raw_fallback']
    assert export['does_not_attest_future_replay'] and export['native_starts']==export['Optimize']==0
    public=export['public_HTTP_export'];assert not public['application_credentials_supplied'] and not public['local_git_archive_used'] and public['no_local_part_or_original_raw_fallback']
    manifest_path=OUT/'compact_evidence/manifest.json';local=manifest_path.read_bytes();public_bytes=local.replace(b'\r\n',b'\n');assert b'\r' not in public_bytes
    manifest=json.loads(public_bytes);typed_equal(json.loads(local),manifest)
    assert hashlib.sha256(local).hexdigest()==public['local_manifest_SHA'] and hashlib.sha256(public_bytes).hexdigest()==public['expected_public_manifest_SHA']
    expected=[dict(path='results/unified_exact_round122/compact_evidence/manifest.json',bytes=len(public_bytes),SHA=hashlib.sha256(public_bytes).hexdigest())]+manifest['parts']
    assert len(expected)==len(transport['transfers'])==len(public['fetched'])==transport['transfer_utility_processes']==7
    identities=[];base='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+COMMIT+'/'
    for expected_part,actual,published in zip(expected,transport['transfers'],public['fetched']):
        assert actual['url']==published['url']==base+expected_part['path']
        assert actual['bytes']==published['bytes']==expected_part['bytes'] and actual['SHA256']==published['SHA']==expected_part['SHA']
        assert actual['exit_code']==0 and actual['owned_transfer_process_exited'] and actual['stderr_bytes']==0
        assert type(actual['pid']) is int and actual['pid']>0 and type(actual['actual_creation_unix']) is float and actual['actual_creation_unix']>0
        assert actual['ordinary_certificate_and_hostname_verification'] and actual['schannel_system_trust'] and actual['curlrc_disabled'] and not actual['application_credentials_supplied']
        assert actual['seconds']>0;identities.append((actual['pid'],actual['actual_creation_unix']))
    assert len(set(identities))==7 and all(a[1]<b[1] for a,b in zip(identities,identities[1:]))
    assert sum(t['bytes'] for t in transport['transfers'])==189999156
    assert transport['seconds']>=sum(t['seconds'] for t in transport['transfers']) and transport['seconds']>=export['engineering_seconds']
    assert not transport['certificate_or_hostname_verification_disabled'] and transport['existing_system_trust_used'] and 'Schannel' in transport['system_curl_version']
    assert sha(Path(transport['system_curl']))==transport['system_curl_SHA']
    assert sha(source)==V2 and sha(old)==V1 and sha(manifest_path)==public['local_manifest_SHA']
    result=dict(decision='ACCEPT',scope='Independent bounded v2 cleanup mock review plus completed actual v1 HTTPS transfer/export/extraction receipt corroboration. Restored scientific checker scope remains pending its completed receipt.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),review_script_SHA=sha(__file__),
        current_hardened_adapter_SHA=sha(source),actual_executed_v1_preserved_SHA=sha(old),
        original_gap_review_SHA=sha(REVIEW/'post_formal_https_adapter_review.json'),
        actual_transport_receipt_SHA=sha(transport_path),actual_public_export_restore_receipt_SHA=sha(export_path),scienceA=COMMIT,
        arguments_TLS_URL_scope_AST_unchanged=True,byte_stream_read_AST_unchanged=True,strict_release_helper_unchanged=True,
        constructor_birth_and_registration_cleanup_verified=True,per_operation_close_terminate_wait_kill_retry_guards_verified=True,
        unreaped_permanent_failure_explicit_and_rejected=True,finite_cleanup_cases=cases,
        actual_completed_transfers=7,actual_unique_live_birth_exit_identities=identities,downloaded_bytes=189999156,
        each_actual_transfer_digest_size_and_URL_equal_to_published_manifest=True,all_seven_actual_exit_codes_zero_and_reaped=True,
        actual_version='V1 ran and completed; V2 cleanup repair was reviewed with mocks only, without a second export',
        actual_export_extraction_members=62310,actual_export_extraction_hash_checks_receipt_passed=True,
        original_TLS_failure_retained_SHA=sha(OUT/'delivery/public_export_attempt01_tls_failure.json'),
        utility_process_note='Seven actual transfer curl processes plus one local curl --version check; V2 now explicitly records that additional version utility.',
        no_second_export=True,restored_scientific_checker='PENDING_PARENT_COMPLETED_RECEIPT',
        limits=['This bounded review checked source equivalence, original actual seven stream receipts and their manifest hashes; it did not rehash the 190MB transport archive, decompress parts or rescan all extracted members.',
            'V1 constructor/teardown gaps remain documented; every actual V1 transfer successfully reached its recorded birth/exit0 path. No claim that unexecuted V2 produced those actual receipts.'],
        network_requests=0,real_subprocesses_launched_by_review=0,exports_or_restores_by_review=0,full_scans=0,native_starts=0,Optimize=0,
        existing_source_or_payload_member_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_https_hardening_and_export_review.json',result)

if __name__=='__main__':run()
