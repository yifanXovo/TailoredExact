"""Continue the original frozen v2 panel after one exact-byte offline recovery.

No failed record is rewritten or retried. Only immutable record14 is admitted
through the named, independently reviewable recovery, with all original hashes.
"""
import sys,json
import round98_campaign as c
from round98_common import *

def run(numbers):
    camp=OUT/'development02';q=read(camp/'identity.json')
    recovery_path=OUT/'recovered_models/C3_R1/qualified_recovery.json'
    recovery=read(recovery_path);d=camp/'raw/14_R97-C3_R1'
    assert recovery['audit']['passed'] and recovery['optimizer_calls']==0
    for filename,key in [('observations.json','original_observations_sha256'),('audit.json','original_failed_audit_sha256'),
                         ('completion.json','original_completion_sha256'),('result.json','original_result_sha256')]:
        assert sha(d/filename)==recovery[key]
    assert sha(camp/'identity.json')==recovery['original_identity_sha256']
    plan=camp/'exact_recovery_continuation.json'
    metadata=dict(numbers=[15,16,17],identity_sha256=sha(camp/'identity.json'),
        recovery_sha256=sha(recovery_path),wrapper_sha256=sha(__file__),
        no_paid_rerun=True,no_original_record_rewrite=True,optimizer_calls=0)
    if plan.exists():assert read(plan)==metadata
    else:write(plan,metadata)
    for number in map(int,numbers):
        assert number in [15,16,17]
        c.ext.ensure_idle()
        assert q['source_hashes']==bindings() and q['helpers']==c.helpers()
        assert sha(ROOT/q['prereg']['candidate_binary'])==q['candidate_binary_sha256']
        assert sha(q['input_manifest'])==q['prereg_sha256']
        assert sha('D:/gurobi1302/win64/bin/gurobi130.dll')==q['dll_sha256']
        assert sha(BUILD/'Round65ReferenceBuild.exe')==q['reference_binary_sha256']
        records=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()]
        assert len(records)==number-1
        for r in records:
            assert r['audit_passed'] or (r['number']==14 and r['id']=='R97-C3' and r['arm']=='R1'
                and r['audit_error']=='AssertionError()')
        launch=q['launches'][number-1];assert not Path(launch['destination']).exists()
        assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
        c.r90.CAMPAIGN=camp;c.r90.audit_launch=c.adapter
        record=c.r90.run_one(launch,q['prereg'],q)
        same=[r for r in records+[record] if r['id']==launch['id']]
        lowers=[r['endpoint']['L'] for r in same];uppers=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
        assert not uppers or max(lowers)<=min(uppers)+1e-7
        write(camp/f'cross_arm_{launch["id"]}_{len(same)}.json',dict(strongest_L=max(lowers),
            best_physical_U=min(uppers) if uppers else None,passed=True,scope='no combined certificate'))

if __name__=='__main__':run(sys.argv[1:])
