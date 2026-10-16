"""Bounded independent in-memory transport/cleanup review; zero network/process mocks."""
from pathlib import Path
import ast,copy,datetime,hashlib,io,json,subprocess,time,types,urllib.parse
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt

COMMIT='9ed88cf9da87c3ceb7aebc43694f865eacbc86a7'
ADAPTER_SHA='1916691438c43218a4afbfdea190754101c9939baf6c8b676bdc55c5e9bed4d3'
def run():
    tick=time.perf_counter();path=ROOT/'scripts/round122_public_https.py';assert sha(path)==ADAPTER_SHA
    assert sha(ROOT/'scripts/round122_release.py')=='451331633e340155a49149a0a218eb3cf421bb9974e91b54d122a6c3b6090d12'
    nodes={n.name:n for n in ast.parse(path.read_text(encoding='utf-8-sig')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    ns=dict(Path=Path,CURL=Path('C:/Windows/System32/curl.exe'),urllib=types.SimpleNamespace(parse=urllib.parse),hashlib=hashlib,time=time)
    exec(compile(ast.Module(body=[nodes['arguments']],type_ignores=[]),'independent transport arguments fixture','exec'),ns)
    base='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+COMMIT+'/results/unified_exact_round122/compact_evidence/'
    cases=[]
    for suffix in ['manifest.json','evidence.tar.gz.part001','evidence.tar.gz.part006']:
        args=ns['arguments'](base+suffix,45,COMMIT)
        assert args[0]==str(ns['CURL']) and args[1]=='--disable' and args[-2:]==['--url',base+suffix]
        assert args[args.index('--proto')+1]==args[args.index('--proto-redir')+1]=='=https'
        assert not {'--insecure','-k','--config','-K','--user','-u','--netrc','--netrc-file','--cert','--key','--proxy-user'}&set(args)
        cases.append('strict_public_https_argument_'+suffix)
    invalid=[base+'../manifest.json',base+'manifest.json?token=x',base+'manifest.json#x',base+'evidence.tar.gz.partABC',
        base.replace('https://','http://'),base.replace('raw.githubusercontent.com','other.invalid')+'manifest.json',
        base.replace('/TailoredExact/','/other/')+'manifest.json',base.replace('https://','https://user:pass@')+'manifest.json']
    for j,url in enumerate(invalid):
        try:ns['arguments'](url,45,COMMIT)
        except AssertionError:cases.append('unscoped_argument_rejected_'+str(j))
        else:raise AssertionError('unscoped URL accepted')
    class Child:
        pid=7101
        def __init__(self,close_error=False,terminate_error=False,wait_timeout=False):
            self.stdout=io.BytesIO(b'known-public-byte-stream');self.stderr=io.BytesIO(b'');self.waits=[];self.terminated=False;self.killed=False;self.code=None;self.close_error=close_error;self.terminate_error=terminate_error;self.wait_timeout=wait_timeout
            if close_error:self.stdout=types.SimpleNamespace(read=lambda n:b'',close=lambda:(_ for _ in ()).throw(OSError('invented close failure')))
        def poll(self):return self.code
        def terminate(self):
            if self.terminate_error:raise OSError('invented terminate failure')
            self.terminated=True;self.code=-15
        def kill(self):self.killed=True;self.code=-9
        def wait(self,timeout=None):
            self.waits.append(timeout)
            if self.wait_timeout and len(self.waits)==1:raise subprocess.TimeoutExpired('invented curl',timeout)
            if self.code is None:self.code=0
            return self.code
    current=[]
    mock=types.SimpleNamespace(PIPE=object(),TimeoutExpired=subprocess.TimeoutExpired,Popen=lambda *a,**kw:current[-1])
    ns.update(subprocess=mock,child_creation=lambda child:1792170000.)
    exec(compile(ast.Module(body=[nodes['Response']],type_ignores=[]),'independent transport response fixture','exec'),ns)
    request=types.SimpleNamespace(full_url=base+'manifest.json',get_method=lambda:'GET',data=None,headers={'User-agent':'TailoredExact-Round122-public-restore'})
    def response(child,transfers):current.append(child);return ns['Response'](request,45,COMMIT,transfers)
    child=Child();transfers=[]
    with response(child,transfers) as r:data=r.read()
    assert child.waits==[10] and transfers[0]['owned_transfer_process_exited'] and transfers[0]['SHA256']==hashlib.sha256(data).hexdigest()
    cases.append('normal_body_stream_hash_birth_exit_record')
    child=Child();transfers=[];r=response(child,transfers)
    assert r.__exit__(RuntimeError,RuntimeError('invented body exception'),None) is False and child.terminated and child.waits==[10]
    cases.append('ordinary_body_exception_terminates_waits')
    child=Child(wait_timeout=True);transfers=[];r=response(child,transfers)
    try:r.__exit__(None,None,None)
    except AssertionError:pass
    else:raise AssertionError('killed transfer accepted')
    assert child.killed and child.waits==[10,None] and transfers[0]['owned_transfer_process_exited']
    cases.append('ordinary_wait_timeout_kills_waits_rejects')
    # Actual failure injection demonstrates the two ownership gaps, without
    # creating a process. These cases remain findings until a bounded repair.
    ns['child_creation']=lambda child:(_ for _ in ()).throw(OSError('invented birth failure'))
    child=Child();transfers=[]
    try:response(child,transfers)
    except OSError:pass
    else:raise AssertionError('birth failure not injected')
    assert not child.waits and not child.terminated and not child.killed and transfers==[]
    constructor_gap=dict(injected='child_creation raises after Popen',owned_child_wait_calls=0,owned_child_kill_or_terminate=False,transfer_receipt_missing=True)
    ns['child_creation']=lambda child:1792170000.
    gaps=[]
    for name,child,kind in [('stdout_close',Child(close_error=True),None),('terminate',Child(terminate_error=True),RuntimeError)]:
        transfers=[];r=response(child,transfers)
        try:r.__exit__(kind,RuntimeError('invented body exception') if kind else None,None)
        except OSError:pass
        else:raise AssertionError('teardown failure not injected')
        assert child.waits==[] and r.finished and not transfers[0].get('owned_transfer_process_exited')
        gaps.append(dict(injected=name+' raises before wait',owned_child_wait_calls=0,finished_flag=True,owned_exit_not_observed=True))
    failure=OUT/'delivery/public_export_attempt01_tls_failure.json';original_failure=read(failure)
    result=dict(decision='REQUIRES_OWNED_CHILD_CLEANUP_HARDENING',scope='Actual independent source and finite mock review of adapter v1 only. Healthy ongoing export is not interrupted; actual export outcome requires its completed receipts.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        script_SHA=sha(path),review_script_SHA=sha(__file__),release_helper_SHA=sha(ROOT/'scripts/round122_release.py'),scienceA=COMMIT,
        ordinary_TLS_and_hostname_checks_not_disabled=True,system_Schannel_intent_and_absolute_installed_curl_path=True,
        curlrc_disabled_before_other_options=True,no_application_credentials_in_command_or_request=True,
        strict_release_public_manifest_part_SHA_size_path_checks_unchanged=True,
        arguments_and_normal_lifecycle_finite_cases=cases,constructor_failure_actual_mock=constructor_gap,teardown_failure_actual_mocks=gaps,
        required_change='Protect all post-Popen constructor setup and guarantee owned process kill/wait even when close/poll/terminate/setup fails; preserve original source and actual-run identity.',
        actual_healthy_run='Do not interrupt or modify its loaded source. The actual seven observed births/exits/byte hashes may separately substantiate that execution; do not perform another export solely for this static repair.',
        auxiliary_process_note='run also executes one local curl --version check; transfer_utility_processes counts transfers only, so later total utility-start accounting should retain that version process separately.',
        preserved_TLS_failure_receipt_SHA=sha(failure),TLS_failure_metadata=original_failure,
        native_starts=0,Optimize=0,network_requests=0,Git_commands=0,real_subprocesses_launched_by_review=0,scientific_exports=0,scientific_restores=0,
        existing_payload_or_helper_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_https_adapter_review.json',result)

if __name__=='__main__':run()
