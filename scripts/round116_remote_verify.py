"""Post-payload read-only GitHub identity/OID observation, no native execution.

Published receipts cover the observed prior head only. A final observation is
kept locally after the receipt commit is pushed, preventing self-cover claims.
"""
import argparse, json, subprocess, time
from pathlib import Path
import round108_reader as core
from read_round116 import ROUND

REPO='yifanXovo/TailoredExact'
BASE='7eef812efb1bd3046c48e76ff6ac968de276a9b0'
BRANCH='codex/round116-external-source-frozen-evaluation'
BASE_BRANCH='codex/round115-producer-clock-attribution-closure'

def command(root,args):return subprocess.check_output(args,cwd=root)
def run(root,number,destination):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND
    head=command(root,['git','rev-parse','HEAD']).decode().strip()
    def api(path):return json.loads(command(root,['gh','api','repos/'+REPO+'/'+path]))
    pr=api('pulls/'+str(number))
    assert pr['state']=='open' and pr['draft'] is True
    assert pr['head']['ref']==BRANCH and pr['head']['sha']==head
    assert pr['base']['ref']==BASE_BRANCH and pr['base']['sha']==BASE
    assert pr['head']['repo']['full_name']==pr['base']['repo']['full_name']==REPO
    head_root=api('git/trees/'+head);base_root=api('git/trees/'+BASE)
    entries={x['path']:x for x in head_root['tree']};old={x['path']:x for x in base_root['tree']}
    assert not head_root['truncated'] and not base_root['truncated']
    for name in ['src','include','CMakeLists.txt']:assert entries[name]['sha']==old[name]['sha']
    remote={}
    def collect(prefix,oid,recursive=True):
        tree=api('git/trees/'+oid+('?recursive=1' if recursive else ''))
        assert tree['truncated'] is False
        for item in tree['tree']:
            if item['type']=='blob':remote[prefix+'/'+item['path']]=item['sha']
    results=api('git/trees/'+entries['results']['sha']);r={x['path']:x for x in results['tree']}
    collect(ROUND,r['unified_exact_round116']['sha'])
    references=api('git/trees/'+entries['reference']['sha']);r={x['path']:x for x in references['tree']}
    collect('reference/round116_external',r['round116_external']['sha'])
    collect('scripts',entries['scripts']['sha'])
    raw=command(root,['git','ls-tree','-rz',head,'--',ROUND,'reference/round116_external','scripts'])
    local={}
    for record in raw.split(b'\0'):
        if not record:continue
        metadata,path=record.split(b'\t',1);mode,kind,oid=metadata.split()
        if kind==b'blob':local[path.decode()]=oid.decode()
    candidate=core.read(out/'candidate_identity.json')
    required={p for p in local if p.startswith(ROUND+'/') or p.startswith('reference/round116_external/')}
    required.update(candidate['helpers'])
    required.update(p for p in local if p.startswith('scripts/') and 'round116' in p)
    assert required and all(p in local and remote.get(p)==local[p] for p in required)
    parts=core.read(out/'compact_evidence/manifest.json')['parts']
    for p in parts:assert p['path'] in required and core.sha(root/p['path'])==p['SHA']
    required_receipts=[ROUND+'/'+n for n in ['final_report.md','paper_candidate_spec.md','research_phase_decision.json',
        'reports_final/current_core.json','reports_final/arms.csv','reports_final/pairs.csv','reports_final/numerical_reliability.csv',
        'public_export_receipt.json','public_restore_receipt.json','public_reconstruction_comparison.json','review/whole_goal01/signed_review.json']]
    assert all(p in required for p in required_receipts)
    value=dict(schema='round116-actual-remote-observation-v1',PR=pr['html_url'],state=pr['state'],draft=pr['draft'],
        title=pr['title'],head_branch=BRANCH,head_commit=head,base_branch=BASE_BRANCH,base_commit=BASE,
        scientific_payload_commit='1185a9c06c6ac4d46d1917c12f0f28d8a6275e54',
        scientific_payload_is_separate_from_later_receipts=True,
        necessary_remote_OIDs_equal=True,verified_path_count=len(required),verified_OIDs={p:local[p] for p in sorted(required)},
        remote_source_trees_equal_base={n:entries[n]['sha'] for n in ['src','include','CMakeLists.txt']},
        carrier_parts_sha256_checked_locally_and_remote_git_blob_OIDs_equal=True,
        remote_carrier_bytes_not_redownloaded_or_rehashed=True,remote_native_reproduction=False,
        covers_observed_head_only=True,does_not_cover_own_future_commit=True,
        actual_scientific_execution_stage='BLOCKED',formal_retries=0,next_round_started=False,
        checker_SHA=core.sha(__file__),observed_unix=time.time(),engineering_seconds=time.perf_counter()-tick,
        Optimize=0,native_starts=0)
    core.write(Path(destination),value)
    print(json.dumps({k:value[k] for k in ['PR','state','draft','head_commit','base_commit','verified_path_count','necessary_remote_OIDs_equal','engineering_seconds']}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--pr',type=int,required=True);parser.add_argument('--out',required=True)
    a=parser.parse_args();run(a.root,a.pr,a.out)
