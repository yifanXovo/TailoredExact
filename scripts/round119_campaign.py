"""Serial fixed three-arm groups; the native deadline never restarts."""
from round119_common import *
import inspect,types,traceback
import round115_campaign as inherited
import round90_lp_g_g3 as supervisor
from round119_prepare import COMMON
from round119_evidence import verify
from round100_idle import ensure_idle

def production_check(l,observations,c,i):
    function=types.FunctionType(inherited.production_check.__code__,dict(vars(inherited),ROOT=ROOT), 'round119_production_check')
    return function(l,observations,c,i)
def supervised(l,i,tick):
    publisher=inherited.OptionalPublisher(l);d=Path(l['destination'])
    namespace=dict(vars(supervisor),ROOT=ROOT,CAMPAIGN=d.parents[1],atomic_status=publisher,
        _arm_tick=tick,production_check=production_check)
    try:return inherited.supervisor_function(namespace)(l,i['prereg'],i)
    finally:
        if d.is_dir():write(d/'progress_publication_receipt.json',dict(publisher.receipt(),necessary_write_before_production=True,
            global_namespace_modified=False,qualification_fault_injected=False))
def finish_producer(l,tick,t0unix):
    d=Path(l['destination'])
    names=['result.json','completion.json','observations.json','phases.csv','production_checks.json','progress_publication_receipt.json','native_end_receipt.json']
    if (d/'external/round119_events.jsonl').exists():names+=['external/round119_events.jsonl']
    assert all((d/n).is_file() for n in names)
    write(d/'producer_seal.json',dict(required_SHA={n:sha(d/n) for n in names},required_outputs_closed=True,
        necessary_producer_trailer_complete=True,native_stopped_no_reentry=True,cohort_review_excluded=True))
    produced=time.perf_counter();producedunix=time.time()
    write(d/'producer_receipt.json',dict(number=l['number'],id=l['id'],arm=l['arm'],state='PRODUCED_PENDING_VERIFICATION',
        verification_passed=None,t0_perf=tick,t0_unix=t0unix,t_produce_perf=produced,t_produce_unix=producedunix,T_produce=produced-tick,
        cap_seconds=l['cap_seconds'],producer_seal_SHA=sha(d/'producer_seal.json'),required_outputs_closed=True,native_stopped_no_reentry=True,
        includes_H_models_online_checks_native_cleanup_serialization_supervision=True,
        first_arm_includes_wrapper_creation_and_import=l['number']==1 and l['panel_kind']!='qualification',
        receipt_write_is_subsequent_management_charged_in_T_verify=True))
    assert produced-tick<=l['cap_seconds'],'producer exceeded fixed original cap'
def execute(l,i,tick=None,t0unix=None):
    tick=time.perf_counter() if tick is None else tick;t0unix=time.time() if t0unix is None else t0unix
    identity();assert not Path(l['destination']).exists()
    assert sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
    supervised(l,i,tick);finish_producer(l,tick,t0unix);verify(l,i)
def reservation(group_number):
    groups=read(OUT/'argv_freeze.json')['groups'];cancel=(OUT/'confirmation_cancellation.json').exists()
    future=[g for g in groups if g['number']>group_number and not(cancel and g['conditional'])]
    return dict(starts=4*len(future),seconds=sum(g['nominal_seconds']+g['management_reserve'] for g in future))
def billed(number,label):
    number=int(number);g=read(OUT/'argv_freeze.json')['groups'][number-1]
    i=read(OUT/g['campaign']/'identity.json');future=reservation(number)
    if number==4:
        assert read(OUT/'development_admission.json')['admitted'] is True
    gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
    assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
    assert i['helpers']==helpers() and i['source_hashes']==bindings()
    fee,tick=fee_begin(label,3,g['nominal_seconds']+g['management_reserve'],False,future);code=1;actual=0
    try:
        ensure_idle();identity()
        for n,l in enumerate(i['launches'],1):
            arm_tick=tick if n==1 else time.perf_counter()
            armunix=read(fee/'launch.json')['wrapper_creation_unix'] if n==1 else time.time()
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],t0_perf=arm_tick,t0_unix=armunix))
            actual+=1;execute(l,i,arm_tick,armunix)
            write(fee/f'{n:02d}_after.json',dict(producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json'),verification_complete=True))
            outstanding=future['seconds']+(3-n)*l['cap_seconds']
            assert budget()['paid_outer_seconds']+time.perf_counter()-tick+outstanding<=48000,'insufficient fixed remaining obligations budget'
        from read_round119 import rebuild_group
        before=time.perf_counter();value=rebuild_group(number,OUT/'reconstruction'/f'group{number:02d}')
        write(fee/'group_verification_receipt.json',dict(seconds=time.perf_counter()-before,inside_group_outer_clock=True,
            current_core_SHA=sha(OUT/'reconstruction'/f'group{number:02d}'/'current_core.json'),Optimize=0,native_starts=0))
        write(fee/'administration.json',dict(nominal_seconds=g['nominal_seconds'],management_reserve=g['management_reserve'],
            actual_outer_seconds_before_exit=time.perf_counter()-tick,independent_verification_not_a_producer_window_extension=True,
            reserve_is_prospective_not_a_correctness_timeout=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,False,code,actual)
if __name__=='__main__':billed(sys.argv[1],sys.argv[2])
