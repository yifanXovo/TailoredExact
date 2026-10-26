"""Five unconditional serial groups; one attempt per fixed formal position."""
from round121_common import *
from round121_evidence import verify
import round120_campaign as prior
from round100_idle import ensure_idle
import traceback
supervised=prior.supervised;finish_producer=prior.finish_producer
def execute(l,i,tick=None,t0unix=None):
    tick=time.perf_counter() if tick is None else tick;t0unix=time.time() if t0unix is None else t0unix
    identity();assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
    supervised(l,i,tick);finish_producer(l,tick,t0unix);verify(l,i)
def reservation(number):
    future=[g for g in read(OUT/'argv_freeze.json')['groups'] if g['number']>number]
    return dict(starts=sum(len(g['methods'])+1 for g in future),seconds=sum(g['nominal_seconds']+g['management_reserve'] for g in future))
def billed(number,label):
    number=int(number);g=read(OUT/'argv_freeze.json')['groups'][number-1];i=read(OUT/g['campaign']/'identity.json')
    gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT' and gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
    assert i['helpers']==helpers() and i['source_hashes']==bindings()
    future=reservation(number);count=len(i['launches']);fee,tick=fee_begin(label,count,g['nominal_seconds']+g['management_reserve'],False,future);actual=0;code=1
    try:
        ensure_idle();identity()
        for n,l in enumerate(i['launches'],1):
            arm_tick=tick if n==1 else time.perf_counter();arm_unix=read(fee/'launch.json')['wrapper_creation_unix'] if n==1 else time.time()
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],seed=l['seed'],t0_perf=arm_tick,t0_unix=arm_unix));actual+=1
            execute(l,i,arm_tick,arm_unix)
            write(fee/f'{n:02d}_after.json',dict(producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json'),verification_complete=True))
            assert budget()['paid_outer_seconds']+time.perf_counter()-tick+future['seconds']+(count-n)*l['cap_seconds']<=48000
        from read_round121 import rebuild_group
        start=time.perf_counter();rebuild_group(number,OUT/'reconstruction'/f'group{number:02d}')
        write(fee/'group_verification_receipt.json',dict(seconds=time.perf_counter()-start,inside_group_outer_clock=True,
            current_core_SHA=sha(OUT/'reconstruction'/f'group{number:02d}/current_core.json'),Optimize=0));code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,False,code,actual)
if __name__=='__main__':billed(sys.argv[1],sys.argv[2])
