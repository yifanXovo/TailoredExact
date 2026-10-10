"""Read-only GitHub verification of a fixed science commit and exact carriers."""
import argparse, hashlib, json, subprocess, time
from pathlib import Path
from urllib.parse import quote

REPO='yifanXovo/TailoredExact'
ROUND='results/unified_exact_round110'
BASE='8977da23a0be50da0ab2fceb69ad3ee04e040855'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def api(path):
    return json.loads(subprocess.check_output(['gh','api',path],text=True,encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--pr',type=int,required=True);ap.add_argument('--science',required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    root=a.root.resolve();assert not a.out.exists();started=time.time()
    pr=api(f'repos/{REPO}/pulls/{a.pr}')
    assert pr['state']=='open' and pr['draft'] and pr['base']['ref']=='codex/round109-frozen-mb-geographic-evaluation'
    assert pr['base']['sha']==BASE and pr['head']['sha']==a.science
    old=api(f'repos/{REPO}/pulls/171')
    assert old['head']['sha']==BASE and old['state']=='open' and old['draft']
    assert api(f'repos/{REPO}')['private'] is False, 'Canonical unauthenticated raw transport requires this public repository'
    package=root/ROUND/'compact_evidence';manifest=read(package/'manifest.json')
    paths=[ROUND+'/'+name for name in ['final_report.md','selection_decision.json','paper_candidate_spec.md',
        'repair_scope.md','repair_evidence.json','production_identity.json','candidate_identity.json','input_manifest.json','protocol.json',
        'reports_final/summary.json','reports_final/arms.csv','reports_final/pairs.csv','reports_final/seed_pairs.csv',
        'reports_final/selection_decision.json','review/final_blocked_raw01/audit.json',
        'review/final_blocked_publication01/audit.json','compact_evidence/manifest.json']]
    paths += ['src/Parser.cpp','scripts/round110_final_reader.py','scripts/round110_public.py']
    carriers=[r['path'] for r in manifest['parts']] or [manifest['archive_path']]
    paths += [ROUND+'/compact_evidence/'+p for p in carriers]
    results=[]
    for name in paths:
        path=root/name;expected=sha(path);digest=hashlib.sha256();size=0
        remote_url=f'https://raw.githubusercontent.com/{REPO}/{a.science}/{quote(name,safe="/")}'
        command=['curl.exe','--fail','--location','--silent','--show-error',remote_url]
        child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while block:=child.stdout.read(1024*1024):digest.update(block);size+=len(block)
        error=child.stderr.read();code=child.wait()
        assert code==0,(name,error.decode(errors='replace'))
        assert size==path.stat().st_size and digest.hexdigest()==expected,(name,size,digest.hexdigest(),expected)
        results.append(dict(path=name,bytes=size,sha256=expected,remote_raw_bytes_equal=True,remote_url=remote_url))
    value=dict(schema='round110-fixed-science-remote-byte-verification-v1',PR=pr['html_url'],science_commit=a.science,
               remote_head_at_verification=pr['head']['sha'],base_commit=pr['base']['sha'],open=True,draft=True,
               historical_PR171_unchanged=True,critical_files_and_all_carrier_parts=results,
               archive_sha256=manifest['archive_sha256'],receipt_created_after_science_commit=True,
               source_SHA=sha(__file__),cwd=str(Path.cwd()),started_unix=started,ended_unix=time.time(),
               byte_transport='Canonical GitHub raw URL pinned to immutable science commit; curl stdout streamed without transformation',
               exit_code=0,Optimize=0,native_environment=0)
    with a.out.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps(dict(PR=value['PR'],science_commit=a.science,verified_files=len(results),exit_code=0)))

if __name__=='__main__':main()
