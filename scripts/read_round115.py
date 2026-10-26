"""Thin exact specialization of R114 reconstruction, retaining its full audits."""
import argparse,csv,json
from pathlib import Path
import read_round114 as original
from round115_common import clock_evidence,LAYER
csv.field_size_limit(64*1024*1024)

def specialized_source():
    source=Path(original.__file__).read_text(encoding='utf-8').split("if __name__=='__main__':")[0]
    def change(old,new):
        nonlocal source
        assert source.count(old)==1,('reader source boundary changed',old)
        source=source.replace(old,new)
    change("ROUND='results/unified_exact_round114'","ROUND='results/unified_exact_round115'")
    change("LAYER='R112_COMPLETE12_PLUS_R113_G50_4_PLUS_R114_G100_4'",'LAYER='+repr(LAYER))
    start=source.index('def clock_evidence(');end=source.index('\ndef typed(',start)
    source=source[:start]+source[end:]
    change("sha(root/'scripts/round114_campaign.py')","sha(root/'scripts/round115_campaign.py')")
    change("required=['result.json','completion.json','audit.json','observations.json','whole_arm_receipt.json','independent_evidence.json',\n                'native_claims.json','claim_rejections.json','independent_endpoint_closeout.json']",
           "required=['result.json','completion.json','audit.json','observations.json','producer_receipt.json','producer_seal.json','production_checks.json','independent_evidence.json',\n                'native_claims.json','claim_rejections.json','verification_closeout.json','arm_total_receipt.json']")
    change("whole=read(d/'whole_arm_receipt.json');ind=read(d/'independent_evidence.json')\n            assert whole['independent_evidence_SHA']==sha(d/'independent_evidence.json')\n            assert whole['independent_closeout_SHA']==sha(d/'independent_endpoint_closeout.json')\n            assert whole['own_UB_floor_zero_evidence_written_before_whole'] and not whole['future_cohort_review_in_clock']",
           "producer=read(d/'producer_receipt.json');ind=read(d/'independent_evidence.json')\n            closeout=read(d/'verification_closeout.json')\n            assert closeout['own_evidence_SHA']==sha(d/'independent_evidence.json')\n            assert closeout['no_new_solution_or_certificate_backfilled']\n            assert read(d/'production_checks.json')['final_physical_verification']==ind['physical']\n            assert ind['created_after_producer_seal'] and not ind['inside_own_whole']")
    change("original_clock_path=(d/'whole_arm_receipt.json').relative_to(root).as_posix(),",
           "original_clock_path=(d/'producer_receipt.json').relative_to(root).as_posix(),T_produce=t,T_verify=item['clock_record']['T_verify'],T_total=item['clock_record']['T_total'],measurement_policy='v2',")
    change("own_evidence_created_inside_original_whole_only=True,future_review_charged_as_engineering=True)",
           "own_sources_sealed_before_production_only=True,future_review_charged_as_group_engineering=True,actual_reconciliation_unix=__import__('time').time())")
    change("whole_seconds=t,H_seconds=H,LP_inclusive_seconds=LP,MIP_inclusive_seconds=MIP,",
           "T_produce=t,T_verify=clock_record['T_verify'],T_total=clock_record['T_total'],H_seconds=H,LP_inclusive_seconds=LP,MIP_inclusive_seconds=MIP,")
    change("status='MIXED_INCREMENT_OBSERVED' if all(q['eligible'] for q in vector) else 'INCOMPLETE_ATTRIBUTION',",
           "status='MIXED' if all(q['eligible'] for q in vector) else 'INCOMPLETE',heterogeneous_measurement_policy=True,current_role_main_clock='T_produce',")
    source=source.replace('origin_round=114','origin_round=115').replace('new_R114_measurement','new_R115_measurement').replace('new_R114_pair','new_R115_pair')
    source=source.replace('WHOLE_ARM_CAP_EXCEEDED','PRODUCER_CAP_EXCEEDED')
    source=source.replace("sum(f['starts'] for f in fees)<=16","sum(f['starts'] for f in fees)<=24").replace("sum(f['seconds'] for f in fees)<=17000","sum(f['seconds'] for f in fees)<=20000")
    source=source.replace("sum(f['starts'] for f in fees if f['qualification'])<=8","sum(f['starts'] for f in fees if f['qualification'])<=10").replace("sum(f['seconds'] for f in fees if f['qualification'])<=900","sum(f['seconds'] for f in fees if f['qualification'])<=600")
    source=source.replace("execution_status='QUALIFICATION_ONLY'", "main_clock='T_produce',heterogeneous_measurement_policy=True,execution_stage='COMPLETE' if len(new)==4 and all(q.get('actually_executed') and q['formal_protocol_qualified'] for q in new) else 'BLOCKED',execution_status='QUALIFICATION_ONLY'")
    return source

namespace=dict(clock_evidence=clock_evidence,__file__=__file__)
exec(compile(specialized_source(),__file__+'::specialized_R114_reader','exec'),namespace)
rebuild=namespace['rebuild'];compare_original=namespace['compare']

def compare(expected,actual):
    """Actual reconciliation timestamp is a new revocation observation, not data."""
    original_read=namespace['read']
    def without_observation_time(p):
        value=original_read(p)
        if Path(p).name=='cohort_reconciliation.json':value.pop('actual_reconciliation_unix',None)
        return value
    namespace['read']=without_observation_time
    try:return compare_original(expected,actual)
    finally:namespace['read']=original_read

def diagnostics_r114(root):
    values=[];root=Path(root)
    for d in sorted((root/'results/unified_exact_round114/campaign/raw').iterdir()):
        if not (d/'whole_arm_receipt.json').is_file():continue
        p=original.read(d/'whole_arm_receipt.json');n=original.read(d/'native_end_receipt.json')
        values.append(dict(arm=p['arm'],state='PROTOCOL_DIAGNOSTIC_ONLY',original_whole=p['complete_seconds'],
            original_qualified=p['complete_seconds']<=p['cap_seconds'],native_end_diagnostic=n['complete_seconds_until_native_end'],
            producer_time_reconstructed=False,old_eligibility_unchanged=True))
    return values

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--qualification-only',action='store_true');parser.add_argument('--compare');a=parser.parse_args()
    value=rebuild(a.root,a.out,a.qualification_only)
    if a.compare:value['core_comparison']=compare(a.compare,a.out)
    print(json.dumps(value),flush=True)
