"""Thin post-production adapter around the unchanged R114 complete audit."""
from round115_common import read,write,sha
from pathlib import Path
import time,types
import round114_audit as inherited
from round114_claims import ClaimRejection

def independent(*args):
    value=inherited.independent(*args)
    value.update(schema='round115-postproduction-independent-evidence-v2',inside_own_whole=False,
        created_after_producer_seal=True,clock_pending_until_actual_whole=False,clock_valid=False,
        qualification_pending=True,own_source='sealed_producer_result_and_committed_own_witnesses',
        extra_after_production_solution_or_bound=False)
    return value

def verify(l,i):
    d=Path(l['destination']);p=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json')
    assert p['producer_seal_SHA']==sha(d/'producer_seal.json') and p['native_stopped_no_reentry']
    for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest
    namespace=dict(vars(inherited),independent=independent)
    adapter=types.FunctionType(inherited.adapter.__code__,namespace,'round115_postproduction_adapter')
    tick=time.perf_counter()
    try:
        value=adapter(l,read(d/'observations.json'),read(d/'completion.json'),i)
    except ClaimRejection as exc:
        value=dict(exc.evidence,status='structured_claim_rejection',claim_rejection_recorded=True)
    except Exception as exc:
        write(d/'audit.json',dict(passed=False,error=repr(exc),verification_failed=True,endpoint=None))
        raise
    value['offline_audit_seconds']=time.perf_counter()-tick
    value.update(producer_receipt_SHA=sha(d/'producer_receipt.json'),measurement_policy='v2',performed_after_production=True)
    write(d/'audit.json',value);write(d/'audit_execution_metrics.json',namespace['last_metrics'])
    write(d/'postexit_audit_receipt.json',dict(complete_seconds_until_audit_end=time.perf_counter()-p['t0_perf'],
        ended_unix=time.time(),phase='verification',not_producer_time=True))
    assert value['passed'] is True or value.get('claim_rejection_recorded') is True and value.get('independent_evidence_audit_passed') is True
    assert read(d/'independent_evidence.json')['own_U']==read(d/'production_checks.json')['final_physical_verification']['F']
    for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,('postverification mutation',name)
    write(d/'verification_closeout.json',dict(necessary_verification_complete=True,audit_SHA=sha(d/'audit.json'),
        own_evidence_SHA=sha(d/'independent_evidence.json'),claims_SHA=sha(d/'native_claims.json'),
        rejection_SHA=sha(d/'claim_rejections.json'),metrics_SHA=sha(d/'audit_execution_metrics.json'),
        producer_receipt_SHA=sha(d/'producer_receipt.json'),native_proof_qualified=value['native_proof_qualified'],
        no_new_solution_or_certificate_backfilled=True,cohort_reconciliation_deferred=True))
    verified=time.perf_counter();verified_unix=time.time()
    write(d/'arm_total_receipt.json',dict(t_verified_perf=verified,t_verified_unix=verified_unix,
        T_verify=verified-p['t_produce_perf'],T_total=verified-p['t0_perf'],
        producer_receipt_SHA=sha(d/'producer_receipt.json'),verification_closeout_SHA=sha(d/'verification_closeout.json'),
        necessary_verification_complete=True,receipt_write_is_subsequent_campaign_management=True,
        future_group_review_not_in_clock=True,main_qualification_cap_uses_T_produce=True))
    return value
