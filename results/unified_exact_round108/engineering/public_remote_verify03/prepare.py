"""Use Windows Schannel HTTPS for binary byte streaming; retain the gh failure."""
import hashlib,json,sys,time
from pathlib import Path
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
here=Path(__file__).resolve().parent;root=here.parents[3]
old=root/'results/unified_exact_round108/engineering/public_remote_verify02/verify.py'
start=time.perf_counter();data=old.read_bytes();text=data.decode('utf-8')
needle="download_command=[GH,'api',f'repos/{REPO}/contents/{path}?ref={head}','-H','Accept: application/vnd.github.raw+json']"
replacement="download_command=['C:/Windows/System32/curl.exe','--fail','--silent','--show-error','--location','--proto','=https','--proto-redir','=https','--max-time','180',item['download_url']]"
assert text.count(needle)==1
with (here/'verify.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(text.replace(needle,replacement))
with (here/'failed_verify02_source.py').open('xb') as stream:stream.write(data)
assert sha(old)==sha(here/'failed_verify02_source.py')
stderr=root/'results/unified_exact_round108/engineering/public_remote_verify02/phase02/download_evidence.tar.gz.part001.stderr.log'
assert stderr.read_bytes()==b'transform: short source buffer\n'
failure=dict(actual_command=[sys.executable,str(old),'--root',str(root),'--pr-number','170',
    '--head','ea14ac7b1762e360fb564b46a47946539f10b2bf','--label','phase02',
    '--isolated-review','results/unified_exact_round108/review/public_isolated_review01.json'],
    exit_code=1,source_SHA=sha(old),download_exit_code=1,stderr_SHA=sha(stderr),
    error='gh raw binary response transform: short source buffer',exact_script_failure_elapsed_seconds=None,
    repair='Existing Windows curl 8.13.0 Schannel HTTPS raw streaming, without --insecure or any CA/proxy/network changes',
    prior_secure_HEAD_check=dict(exit_code=0,HTTP_status=200,part001_content_length=94371840),
    engineering=True,Optimize=0,IIS=0,conservative_solver_starts=0)
with (here/'failed_verify02_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(failure,stream,indent=2);stream.write('\n')
receipt=dict(command=[sys.executable,str(Path(__file__).resolve())],exit_code=0,seconds=time.perf_counter()-start,
    source_SHA=sha(__file__),old_source_exact_preserved=True,original_source_SHA=sha(old),
    corrected_source_SHA=sha(here/'verify.py'),engineering=True,Optimize=0,IIS=0)
with (here/'prepare_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
print(json.dumps(dict(exit_code=0,corrected_source_SHA=receipt['corrected_source_SHA'])))
