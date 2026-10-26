"""Actual narrow remote PR/tree/OID observation; receipts never assert future pushes."""
from round115_common import ROOT, OUT, read, write, sha
import json, subprocess, sys, time

def command(args):return subprocess.check_output(args,cwd=ROOT).decode('utf-8').strip()
def api(path):return json.loads(command(['gh','api','repos/yifanXovo/TailoredExact/'+path]))

def observe(expected,label):
    tick=time.perf_counter()
    pr=json.loads(command(['gh','pr','view','177','--repo','yifanXovo/TailoredExact','--json',
        'number,url,headRefName,headRefOid,baseRefName,baseRefOid,state,isDraft,title']))
    assert pr['headRefOid']==expected and pr['headRefName']=='codex/round115-producer-clock-attribution-closure'
    assert pr['baseRefName']=='codex/round114-bound-claim-isolation-g100'
    assert pr['baseRefOid']=='e436748521cf5aabbe84a24a5e9cf3836550563c' and pr['state']=='OPEN' and pr['isDraft']
    assert pr['title']=='Round115: separate producer time from verification and close G100 backend attribution'
    refs=command(['git','ls-remote','--heads','origin',pr['headRefName'],pr['baseRefName']])
    advertised={row.split()[1]:row.split()[0] for row in refs.splitlines()}
    assert advertised['refs/heads/'+pr['headRefName']]==expected
    assert advertised['refs/heads/'+pr['baseRefName']]==pr['baseRefOid']
    commit=api('git/commits/'+expected);root_tree=commit['tree']['sha']
    assert commit['sha']==expected and root_tree==command(['git','rev-parse',expected+'^{tree}'])
    cached={}
    def tree(oid):
        if oid not in cached:
            value=api('git/trees/'+oid);assert not value.get('truncated',False)
            cached[oid]={x['path']:x for x in value['tree']}
        return cached[oid]
    def remote_oid(path):
        oid=root_tree
        for name in path.split('/'):
            entry=tree(oid)[name];oid=entry['sha']
        assert entry['type']=='blob';return oid
    names=['measurement_policy_v2.md','producer_dependency_graph.json','minimal_diff.md','protocol.json',
        'production_identity.json','candidate_identity.json','fixed_manifest.json','input_manifest.json',
        'campaign/identity.json','review/performance_admission.json','review/whole_goal01/signed_review.json',
        'review/whole_goal01/review_boundary.md','final_report.md','research_phase_decision.md','research_phase_decision.json',
        'physical_completion.json','current_source_qualification.json','formal_compact_Start.json',
        'objective_sublevel_analysis.md','objective_sublevel_analysis.json','objective_sublevel_analysis_raw.json',
        'reports_final/summary.json','reports_final/new_arms.csv','reports_final/new_pairs.csv',
        'reports_final/backend_conclusions.json','reports_final/clock_qualification.csv','reports_final/time_partitions.csv',
        'reports_final/native_counts.csv','reports_final/same_H.csv','secondary_total_pairs.csv','secondary_time_comparison.json',
        'public_export_receipt.json','public_restore_receipt.json','public_dependency_supplement.json',
        'public_dependency_supplement_receipt.json','public_dependency_incident.json','public_reconstruction_receipt.json',
        'inherited_r113/public_pack_receipt.json','public_pack_receipt.json','public_dependency_closure.json',
        'delivery_costs.json','delivery_report.md','reproduce.md','pr_body_delivery.md','RESUME.md','compact_evidence/manifest.json']
    paths=['results/unified_exact_round115/'+n for n in names]
    paths += [p['path'] for p in read(OUT/'compact_evidence/manifest.json')['parts']]
    paths += ['.gitattributes']+['scripts/'+n for n in ['round115_campaign.py','round115_common.py','round115_verify.py',
        'read_round115.py','round115_sublevel.py','round115_organize.py','round115_postreview.py','round115_delivery.py',
        'round115_dependency_repair.py','round115_review.py','qualify_round115.py','qualify_round115_post.py']]
    observed={}
    for path in paths:
        local=command(['git','rev-parse',expected+':'+path]);remote=remote_oid(path);assert local==remote,path
        observed[path]=dict(remote_OID=remote,local_OID=local,equal=True)
    assert not command(['git','diff','--name-only',pr['baseRefOid'],expected,'--','src','include','tests','CMakeLists.txt'])
    result=dict(actual_observed_unix=time.time(),seconds=time.perf_counter()-tick,PR=pr,
        advertised_refs=advertised,commit_OID=commit['sha'],root_tree_OID=root_tree,
        all_necessary_file_OIDs_equal=True,files=observed,remote_tree_reads=len(cached),
        production_source_paths_unchanged=True,scientific_payload_commit='fcf9aa4881a76bbbb26f5ec409a74ea384672886',
        authority_supplement_commit='70fd7c6fc3c3dbbb3ad218a52ebfd8ac173c42eb',
        scope='actual remote state at observation; receipt does not claim future self-publication or later HEAD',
        checker_SHA=sha(__file__),Optimize=0,native_starts=0)
    write(OUT/(label+'.json'),result)
    print(json.dumps(dict(PR=pr,files_checked=len(observed),all_OIDs_equal=True,seconds=result['seconds'])),flush=True)

if __name__=='__main__':observe(sys.argv[1],sys.argv[2])
