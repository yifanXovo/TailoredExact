"""One billed actual H100 reconstruction and full H/Start check, no native."""
from round116_common import *
import traceback
import round116_campaign as campaign
import read_round116 as reader

def run(label):
    fee,tick=campaign.fee_begin(label,0,60,True);code=1
    try:
        summary=reader.rebuild(ROOT,OUT/'qualification'/label/'reconstructed',True,True)
        assert summary['qualified_qualification_CLI']==4
        core=read(OUT/'qualification'/label/'reconstructed/current_core.json')
        assert all(h['qualified'] for h in core['same_H'])
        i=read(OUT/'qualification/cli01/identity.json');ps=next(l for l in i['launches'] if l['arm']=='P-S')
        d=Path(ps['destination']);assert (d/'result.json.round112.startup.json').is_file()
        import round112_audit
        Start=round112_audit.start_audit(ROOT,ps['panel'],d)
        write(OUT/'qualification'/label/'actual_Start.json',Start)
        write(OUT/'qualification'/label/'summary.json',dict(passed=True,actual_CLI=4,complete_same_H=True,full_original_Start=True,
            production_PE_SHA=PE_SHA,helpers=campaign.helpers(),driver_processes=1,OS_children=0,Optimize=0))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])
