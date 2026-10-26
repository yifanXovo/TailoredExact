"""One actual-evidence H100 reconstruction driver; no child or Optimize."""
from round115_common import *
import traceback
import round115_campaign as campaign
import read_round115 as reader
from compare_round112_startup import compare

def run(label):
    fee,tick=campaign.fee_begin(label,0,30,True);code=1
    try:
        result=reader.rebuild(ROOT,OUT/'qualification'/label/'reconstructed',True,True)
        i=read(OUT/'qualification/cli01/identity.json');by={l['arm']:Path(l['destination']) for l in i['launches']}
        h=compare(ROOT,i['launches'][0]['panel'],{m:by[m] for m in ['P-S','ENS-C','M-B']})
        assert all(q['qualified'] for q in h['comparisons']) and result['qualified_qualification_CLI']==4
        write(OUT/'qualification'/label/'same_H.json',h)
        write(OUT/'qualification'/label/'summary.json',dict(passed=True,actual_CLI=4,real_SameH=True,
            production_PE_SHA=PE_SHA,final_helpers=campaign.helpers(),driver_processes=1,OS_children=0,Optimize=0))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])
