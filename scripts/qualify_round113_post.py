"""One billed zero-native postqualification driver: full H and actual reader."""
from round113_common import *
import csv, shutil, traceback
import round113_campaign as campaign
from compare_round112_startup import compare
import read_round113 as reader

def run(label):
    fee,tick=campaign.fee_begin(label,0,120,True);code=1;out=OUT/'qualification'/label;out.mkdir()
    try:
        i=read(OUT/'qualification/cli01/identity.json');p=i['launches'][0]['panel']
        same=compare(ROOT,p,{l['arm']:Path(l['destination']) for l in i['launches'] if l['arm']!='P-GRB'})
        assert len(same['comparisons'])==2 and all(v['qualified'] for v in same['comparisons'])
        write(out/'H100_same_H.json',same)
        rebuilt=reader.rebuild(ROOT,out/'reconstruction',qualification_only=True,allow_current_qualification_fee_pending=True)
        assert rebuilt['qualified_qualification_arms']==4
        counts=[]
        for l in i['launches']:
            d=Path(l['destination']);r=read(d/'result.json');a=read(d/'audit.json');w=read(d/'whole_arm_receipt.json');progress=read(d/'progress_publication_receipt.json')
            assert a['passed'] and w['complete_seconds']<=120
            if l['arm']=='P-S':assert progress['failure_count']==1 and progress['disabled'] and progress['first_failure']['winerror']==5
            else:assert not progress['disabled']
            counts.append(dict(arm=l['arm'],whole_seconds=w['complete_seconds'],necessary_endpoint=a['endpoint'],
                native_Optimize=sum(q['payload']['kind']=='returned' for q in read(d/'observations.json')),
                display=progress,original_whole_SHA=sha(d/'whole_arm_receipt.json')))
        # Explicit scope correction for inherited aggregate labels; old summaries retained.
        write(out/'finite_summary_scope.json',dict(finite01=['real Win32 sharing','source-extracted supervisor cases','initial source-derived lifecycle fixtures'],
            finite01_final_compatibility_assertion_failed=True,finite02=['targeted old12 compatibility and small CSV restore'],
            finite03=['final changed lifecycle counter/necessary/offline fixtures only'],
            earlier_summary_coverage_booleans_describe_aggregate_coverage_not_reexecutions=True,
            no_false_native_deadline_cancellation_claim=True,actual_native_cancellation_branch_executed=False))
        write(out/'summary.json',dict(passed=True,driver_processes=1,native_children=0,Optimize=0,
            four_actual_CLI=counts,full_H_semantics_and_capacity_owned_fleets_match=True,
            H100_is_qualification_not_formal=True,same_H_SHA=sha(out/'H100_same_H.json'),
            reader_SHA=sha(ROOT/'scripts/read_round113.py'),test_SHA=sha(__file__),candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
            performance_helpers=campaign.helpers(),finite_scope_SHA=sha(out/'finite_summary_scope.json')))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])
