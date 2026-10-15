"""Five unconditional serial groups; one attempt per fixed formal position."""
from round121_common import *
from round121_evidence import verify
import round120_campaign as prior
from round100_idle import ensure_idle
import traceback,types
from qualify_round120 import child_creation

def supervised(l,i,tick):
    """Original supervisor with a persisted actual OS child creation receipt."""
    d=Path(l['destination']);publisher=prior.inherited.OptionalPublisher(l)
    def tracked_popen(*args,**kwargs):
        child=subprocess.Popen(*args,**kwargs)
        try:
            write(d/'child_process_origin.json',dict(pid=child.pid,parent_pid=os.getpid(),
                actual_creation_unix=child_creation(child),command=l['command'],seed=l['seed'],
                source_commit=SOURCE,PE_SHA=PE_SHA,creation_from_live_OS_handle=True))
        except BaseException:
            try:child.kill()
            finally:child.wait()
            raise
        return child
    process_api=types.SimpleNamespace(**dict(vars(subprocess),Popen=tracked_popen))
    namespace=dict(vars(prior.supervisor),ROOT=ROOT,CAMPAIGN=d.parents[1],atomic_status=publisher,
        _arm_tick=tick,production_check=prior.production_check,subprocess=process_api)
    try:return prior.inherited.supervisor_function(namespace)(l,i['prereg'],i)
    finally:
        if d.is_dir():write(d/'progress_publication_receipt.json',dict(publisher.receipt(),necessary_write_before_production=True,global_namespace_modified=False))

def finish_producer(l,tick,t0unix):
    d=Path(l['destination']);names=['result.json','completion.json','observations.json','phases.csv','production_checks.json',
        'progress_publication_receipt.json','native_end_receipt.json','child_process_origin.json']
    if (d/'external/round120_events.jsonl').exists():names+=['external/round120_events.jsonl','external/round120_root_pair.json']
    names=[n for n in names if n!='external/round120_root_pair.json' or (d/n).exists()]
    assert all((d/n).is_file() for n in names)
    write(d/'producer_seal.json',dict(required_SHA={n:sha(d/n) for n in names},required_outputs_closed=True,
        necessary_producer_trailer_complete=True,native_stopped_no_reentry=True,cohort_review_excluded=True))
    produced=time.perf_counter();producedunix=time.time()
    write(d/'producer_receipt.json',dict(number=l['number'],id=l['id'],arm=l['arm'],state='PRODUCED_PENDING_VERIFICATION',verification_passed=None,
        t0_perf=tick,t0_unix=t0unix,t_produce_perf=produced,t_produce_unix=producedunix,T_produce=produced-tick,
        cap_seconds=l['cap_seconds'],producer_seal_SHA=sha(d/'producer_seal.json'),required_outputs_closed=True,native_stopped_no_reentry=True,
        includes_H_models_installation_online_checks_callbacks_native_cleanup_serialization_supervision=True,
        first_arm_includes_wrapper_creation_and_import=l['number']==1 and l['panel_kind']!='qualification',
        receipt_write_is_subsequent_management_charged_in_T_verify=True))
    assert produced-tick<=l['cap_seconds']
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
