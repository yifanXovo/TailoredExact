"""Billed post-CLI qualification: actual retained evidence, no solver children."""
from round114_common import *
import traceback
import round114_campaign as campaign
import read_round114 as reader

def run(label):
    fee,tick=campaign.fee_begin(label,0,120,True);code=1;q=OUT/'qualification'/label;q.mkdir()
    try:
        check_identity();candidate=read(OUT/'candidate_identity.json')
        assert candidate['helpers']==campaign.helpers()
        assert candidate['qualification_test_SHA']==sha(ROOT/'scripts/qualify_round114.py')
        assert candidate['qualification_post_driver_SHA']==sha(__file__)
        assert candidate['offline_reader_SHA']==sha(ROOT/'scripts/read_round114.py')
        finite=sorted(p for p in (OUT/'qualification').glob('finite*/summary.json') if read(p).get('passed'))
        assert finite and read(finite[-1])['performance_helpers']==campaign.helpers()
        assert read(finite[-1])['test_SHA']==candidate['qualification_test_SHA']
        cli=OUT/'qualification/cli01';i=read(cli/'identity.json');records=campaign.records(cli)
        assert len(records)==len(i['launches'])==2 and [q['arm'] for q in records]==['P-GRB','M-B']
        assert read(cli/'qualification_trailer.json')['passed']
        summary=reader.rebuild(ROOT,q/'reports',qualification_only=True,allow_pending=True)
        rows=reader.core.rows(q/'reports/qualification_arms.csv')
        assert summary['qualified_qualification_CLI']==2 and len(rows)==2
        assert not summary['new_formal_positions'] and not summary['formal_actual_Optimize']
        actual=[]
        for l in i['launches']:
            d=Path(l['destination']);r=read(d/'result.json');ind=read(d/'independent_evidence.json')
            c=read(d/'completion.json');w=read(d/'whole_arm_receipt.json')
            assert l['seed']==0 and l['cap_seconds']==120 and w['complete_seconds']<=120
            assert c['stop_reason']=='normal_return' and c['returncode']==0
            assert ind['inside_own_whole'] and ind['independent_floor0'] and ind['own_physical_verified']
            assert ind['counts']['actual_Optimize']>0
            assert ind['counts']['actual_Optimize']==ind['counts']['independently_verified_returned']
            actual.append(dict(arm=l['arm'],input_SHA=l['panel']['input_sha256'],full_argv=l['command'],
                own_U=ind['own_U'],own_zero=ind['own_exact_zero'],actual_Optimize=ind['counts']['actual_Optimize'],
                whole_seconds=w['complete_seconds'],whole_SHA=sha(d/'whole_arm_receipt.json'),
                necessary_audit_SHA=sha(d/'audit.json'),independent_evidence_SHA=sha(d/'independent_evidence.json'),
                normal_return=True,production_PE_SHA=PE_SHA))
        write(q/'summary.json',dict(passed=True,actual_CLI=actual,OS_children=0,Optimize=0,not_performance=True,
            performance_helpers=campaign.helpers(),reader_SHA=sha(ROOT/'scripts/read_round114.py'),
            post_driver_SHA=sha(__file__),fee_still_pending_actual_driver_exit=True,
            numerical_contradiction_reproduced=False,actual_CLI_not_synthetic=True))
        assert time.perf_counter()-tick<=120
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])
