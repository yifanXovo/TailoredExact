"""Use installed Windows Schannel trust for the unchanged strict public reader.

MSYS Python on this host has no CA file or Windows-root enumeration.  This
adapter supplies the same byte-stream API through system curl with ordinary
certificate/hostname checks, no curlrc/application credentials and only pinned
public URLs.  The release helper still verifies every byte count and digest.
"""
from pathlib import Path
import argparse,contextlib,hashlib,json,subprocess,time,urllib.parse,urllib.request
import round122_common as common
import round122_release as release
from qualify_round120 import child_creation

CURL=Path('C:/Windows/System32/curl.exe')

def arguments(url,timeout,commit):
    base='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+commit+'/results/unified_exact_round122/compact_evidence/'
    assert len(commit)==40 and all(c in '0123456789abcdef' for c in commit)
    assert url.startswith(base) and urllib.parse.urlsplit(url).scheme=='https'
    suffix=url[len(base):]
    assert suffix=='manifest.json' or suffix.startswith('evidence.tar.gz.part') and suffix.removeprefix('evidence.tar.gz.part').isdigit()
    assert '?' not in url and '#' not in url and '@' not in urllib.parse.urlsplit(url).netloc
    return [str(CURL),'--disable','--silent','--show-error','--fail','--location',
        '--proto','=https','--proto-redir','=https','--connect-timeout',str(timeout),
        '--max-time','600','--speed-time','45','--speed-limit','1',
        '--user-agent','TailoredExact-Round122-public-restore','--url',url]

class Response:
    def __init__(self,request,timeout,commit,transfers):
        assert request.get_method()=='GET' and request.data is None
        assert {k.lower() for k in request.headers}=={'user-agent'}
        self.command=arguments(request.full_url,timeout,commit);self.started=time.perf_counter()
        self.hash=hashlib.sha256();self.finished=False
        self.child=subprocess.Popen(self.command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.record=dict(url=request.full_url,pid=self.child.pid,actual_creation_unix=None,
            bytes=0,SHA256=None,exit_code=None,ordinary_certificate_and_hostname_verification=True,
            schannel_system_trust=True,curlrc_disabled=True,application_credentials_supplied=False)
        try:
            transfers.append(self.record)
            self.record['actual_creation_unix']=child_creation(self.child)
        except BaseException:
            self.close_owned(True)
            raise
    def read(self,n=-1):
        data=self.child.stdout.read(n);self.hash.update(data);self.record['bytes']+=len(data);return data
    def __enter__(self):return self
    def close_owned(self,abort):
        errors=[]
        def attempt(label,operation):
            try:return operation()
            except BaseException as exc:
                errors.append(dict(operation=label,error_class=type(exc).__name__))
                return None
        attempt('stdout.close',self.child.stdout.close)
        if abort:attempt('terminate',self.child.terminate)
        code=attempt('wait',lambda:self.child.wait(timeout=10))
        if code is None:
            attempt('kill',self.child.kill)
            code=attempt('wait_after_kill',lambda:self.child.wait(timeout=10))
        if code is None:
            attempt('kill_retry',self.child.kill)
            code=attempt('wait_retry',lambda:self.child.wait(timeout=10))
        error=attempt('stderr.read',self.child.stderr.read) if code is not None else b''
        attempt('stderr.close',self.child.stderr.close)
        self.record.update(exit_code=code,SHA256=self.hash.hexdigest(),seconds=time.perf_counter()-self.started,
            stderr_bytes=len(error or b''),owned_transfer_process_exited=code is not None,cleanup_errors=errors)
        self.finished=True
        assert code is not None,('owned HTTPS transfer could not be reaped',self.child.pid,errors)
        return code,error or b'',errors
    def __exit__(self,kind,value,tb):
        code,error,errors=self.close_owned(kind is not None)
        assert kind is not None or code==0,('verified HTTPS transfer failed',code,error.decode('utf-8',errors='replace')[:1000])
        assert kind is not None or not errors,('HTTPS transfer cleanup encountered errors',errors)
        return False

@contextlib.contextmanager
def system_https(commit,transfers):
    original=urllib.request.urlopen
    urllib.request.urlopen=lambda request,timeout:Response(request,timeout,commit,transfers)
    try:yield
    finally:urllib.request.urlopen=original

def run(commit,destination):
    common.workspace();version=subprocess.check_output([str(CURL),'--disable','--version']).decode('utf-8').splitlines()[0]
    assert 'Schannel' in version
    transfers=[];tick=time.perf_counter();code=1
    try:
        with system_https(commit,transfers):release.restore(common.ROOT,commit,destination)
        code=0
    finally:
        common.write(common.OUT/'delivery/system_https_transfer_receipt.json',dict(scientific_commit=commit,
            transport_adapter_SHA=common.sha(__file__),release_helper_SHA=common.sha(common.ROOT/'scripts/round122_release.py'),
            system_curl=str(CURL),system_curl_SHA=common.sha(CURL),system_curl_version=version,
            existing_system_trust_used=True,certificate_or_hostname_verification_disabled=False,
            application_credentials_supplied=False,local_part_or_original_raw_fallback=False,
            transfers=transfers,transfer_utility_processes=len(transfers),local_curl_version_utility_processes=1,
            all_transfer_processes_exited=all(t.get('owned_transfer_process_exited') for t in transfers),
            solver_native_starts=0,Optimize=0,exit_code=code,seconds=time.perf_counter()-tick,
            failed_attempt01='MSYS Python missing CA file; TLS verification failed before receiving manifest bytes; original failure retained.'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);parser.add_argument('--destination',required=True);args=parser.parse_args()
    run(args.commit,args.destination)
