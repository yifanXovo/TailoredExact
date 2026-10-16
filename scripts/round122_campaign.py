"""Eight serial fixed four-method groups, no performance-driven changes."""
from round122_common import *
from round122_evidence import verify
from round121_campaign import supervised,finish_producer
from round100_idle import ensure_idle
import traceback

def execute(l,i,tick=None,t0unix=None):
    workspace();tick=time.perf_counter() if tick is None else tick;t0unix=time.time() if t0unix is None else t0unix
    identity();assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
    supervised(l,i,tick);finish_producer(l,tick,t0unix);verify(l,i)

def reservation(number):
    future=[g for g in read(OUT/'argv_freeze.json')['groups'] if g['number']>number]
    return dict(starts=5*len(future),seconds=sum(g['nominal_seconds']+g['management_reserve'] for g in future))

def billed(number,label):
    workspace();number=int(number);g=read(OUT/'argv_freeze.json')['groups'][number-1];i=read(OUT/g['campaign']/'identity.json')
    gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT' and gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
    assert i['helpers']==helpers() and i['source_hashes']==bindings()
    future=reservation(number);fee,tick=fee_begin(label,4,g['nominal_seconds']+g['management_reserve'],False,future);actual=0;code=1
    try:
        ensure_idle();identity();capacity=workspace();assert capacity['volume_free_bytes']>=read(OUT/'workspace_capacity.json')['minimum_group_start_free_bytes']
        write(fee/'capacity_before.json',capacity)
        for n,l in enumerate(i['launches'],1):
            arm_tick=tick if n==1 else time.perf_counter();arm_unix=read(fee/'launch.json')['wrapper_creation_unix'] if n==1 else time.time()
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],seed=l['seed'],t0_perf=arm_tick,t0_unix=arm_unix));actual+=1
            execute(l,i,arm_tick,arm_unix)
            write(fee/f'{n:02d}_after.json',dict(producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json'),verification_complete=True))
            assert budget()['paid_outer_seconds']+time.perf_counter()-tick+future['seconds']+(4-n)*l['cap_seconds']<=TOTAL_LIMIT
        from read_round122 import rebuild_group
        start=time.perf_counter();rebuild_group(number,OUT/'reconstruction'/f'group{number:02d}')
        write(fee/'group_verification_receipt.json',dict(seconds=time.perf_counter()-start,inside_group_outer_clock=True,
            current_core_SHA=sha(OUT/'reconstruction'/f'group{number:02d}/current_core.json'),Optimize=0));code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,False,code,actual,child_states(i['launches']))

if __name__=='__main__':billed(sys.argv[1],sys.argv[2])
