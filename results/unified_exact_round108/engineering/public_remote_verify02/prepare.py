"""Retain the Python CA failure and use the existing verified gh HTTPS client."""
import hashlib,json,sys,time
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
here=Path(__file__).resolve().parent;root=here.parents[3]
old=root/'results/unified_exact_round108/engineering/public_remote_verify01/verify.py'
start=time.perf_counter();source=old.read_bytes()
needle='''        with urllib.request.urlopen(item['download_url'], timeout=60) as response:
            while block:=response.read(1024*1024):
                digest.update(block); size+=len(block)
                if item['name']!='manifest.json':combined.update(block)
'''
replacement='''        download_command=[GH,'api',f'repos/{REPO}/contents/{path}?ref={head}','-H','Accept: application/vnd.github.raw+json']
        download_begin=time.perf_counter();download_stderr=here/('download_'+item['name']+'.stderr.log')
        with download_stderr.open('xb') as errors:
            process=subprocess.Popen(download_command,cwd=root,stdout=subprocess.PIPE,stderr=errors)
            while block:=process.stdout.read(1024*1024):
                digest.update(block);size+=len(block)
                if item['name']!='manifest.json':combined.update(block)
            code=process.wait(timeout=120)
        commands.append(dict(command=download_command,exit_code=code,seconds=time.perf_counter()-download_begin,
            stdout_SHA=digest.hexdigest(),stdout_bytes=size,stderr_SHA=sha(download_stderr),
            raw_streamed=True,TLS_verification_not_disabled=True))
        assert code==0,(download_command,code,download_stderr.read_text(errors='replace'))
'''
text=source.decode('utf-8');assert text.count(needle)==1
text=text.replace(needle,replacement).replace(', urllib.request','')
with (here/'verify.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
with (here/'failed_verify01_source.py').open('xb') as stream:stream.write(source)
assert sha(old)==sha(here/'failed_verify01_source.py')
failure=dict(actual_command=[sys.executable,str(old),'--root',str(root),'--pr-number','170',
    '--head','ea14ac7b1762e360fb564b46a47946539f10b2bf','--label','phase01',
    '--isolated-review','results/unified_exact_round108/review/public_isolated_review01.json'],
    exit_code=1,source_SHA=sha(old),failed_operation='First raw carrier download via urllib HTTPS',
    error='ssl.SSLCertVerificationError: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate',
    exact_script_failure_elapsed_seconds=None,full_stdout_stderr_file_capture_available=False,
    retained_prior_artifacts='public_remote_verify01/phase01 launch and actual PR/R107 metadata',
    completed_before_failure=['remote head/base/draft','latest R107','exact PR body/report tables','critical public files exact API bytes','carrier remote tree identity'],
    repair='Use existing gh HTTPS client with raw content media type; do not change CA, proxy, network config or disable TLS verification',
    engineering=True,Optimize=0,IIS=0,conservative_solver_starts=0)
with (here/'failed_verify01_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(failure,stream,indent=2);stream.write('\n')
receipt=dict(command=[sys.executable,str(Path(__file__).resolve())],exit_code=0,seconds=time.perf_counter()-start,
    source_SHA=sha(__file__),original_source_SHA=sha(old),corrected_source_SHA=sha(here/'verify.py'),
    old_source_exact_preserved=True,engineering=True,Optimize=0,IIS=0)
with (here/'prepare_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
print(json.dumps(dict(exit_code=0,corrected_source_SHA=receipt['corrected_source_SHA'])))
