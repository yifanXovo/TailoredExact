"""Reuse verified Schannel response cleanup; restrict requests to this pinned carrier."""
from pathlib import Path
import argparse,contextlib,subprocess,time,types,urllib.parse,urllib.request
import round123_common as c
import round123_release as release
from round122_public_https import Response as PriorResponse

CURL=Path('C:/Windows/System32/curl.exe')
def arguments(url,timeout,commit):
    assert release.re_commit(commit)
    base='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+commit+'/results/unified_exact_round123/compact_evidence/'
    assert url.startswith(base) and urllib.parse.urlsplit(url).scheme=='https'
    suffix=url[len(base):]
    assert suffix=='manifest.json' or suffix.startswith('evidence.tar.gz.part') and suffix.removeprefix('evidence.tar.gz.part').isdigit()
    assert '?' not in url and '#' not in url and '@' not in urllib.parse.urlsplit(url).netloc
    return [str(CURL),'--disable','--silent','--show-error','--fail','--location','--proto','=https','--proto-redir','=https',
        '--connect-timeout',str(timeout),'--max-time','600','--speed-time','45','--speed-limit','1',
        '--user-agent','TailoredExact-Round123-public-restore','--url',url]

class Response(PriorResponse):
    # The actual reviewed birth/read/hash/termination/close/wait implementation
    # is unchanged. Only its constructor's strict URL argument builder differs.
    __init__=types.FunctionType(PriorResponse.__init__.__code__,dict(PriorResponse.__init__.__globals__,arguments=arguments))

def run(commit,destination):
    c.workspace();version=subprocess.check_output([str(CURL),'--disable','--version']).decode('utf-8').splitlines()[0];assert 'Schannel' in version
    transfers=[];tick=time.perf_counter();original=urllib.request.urlopen;code=1
    try:
        urllib.request.urlopen=lambda request,timeout:Response(request,timeout,commit,transfers)
        release.restore(c.ROOT,commit,destination);code=0
    finally:
        urllib.request.urlopen=original
        c.write(c.OUT/'delivery/system_https_transfer_receipt.json',dict(scientific_commit=commit,adapter_SHA=c.sha(__file__),
            unchanged_response_implementation_SHA=c.sha(Path(PriorResponse.__init__.__code__.co_filename)),
            system_curl=str(CURL),system_curl_SHA=c.sha(CURL),version=version,transfers=transfers,
            transfer_processes=len(transfers),local_version_utility_processes=1,all_transfer_processes_exited=all(t.get('owned_transfer_process_exited') for t in transfers),
            ordinary_certificate_hostname_verification=True,curlrc_disabled=True,application_credentials_supplied=False,
            local_part_or_original_raw_fallback=False,exit_code=code,Optimize=0,seconds=time.perf_counter()-tick))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--destination',required=True);a=p.parse_args();run(a.commit,a.destination)
