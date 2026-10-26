"""Frozen serial three-method execution with OS birth/exit and actual outer costs."""
from round123_common import *
from round123_evidence import verify
from round121_campaign import supervised,finish_producer
from qualify_round120 import child_creation
from round100_idle import ensure_idle
import ctypes,traceback,types

def worker(kind,label):
    workspace(); qualification=kind=='qualification'
    camp='qualification/h100_seed0' if qualification else 'campaign/group01'
    i=read(OUT/camp/'identity.json'); launches=i['launches']
    reserve=54000+360+2000 if qualification else 54000+360+1000
    fee,tick=fee_begin(label,qualification,reserve); code=1
    try:
        ensure_idle(); identity()
        assert i['helpers']==helpers() and i['source_hashes']==bindings()
        if not qualification:
            gate=read(OUT/'review/performance_admission.json')
            assert gate['decision']=='ACCEPT' and gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
        assert workspace()['volume_free_bytes']>=40*1024**3
        write(fee/'capacity_before.json',workspace())
        for n,l in enumerate(launches,1):
            assert not Path(l['destination']).exists(), 'A formal/qualification position is never rerun'
            arm_tick=tick if n==1 else time.perf_counter()
            arm_unix=read(fee/'launch.json')['wrapper_creation_unix'] if n==1 else time.time()
            assert sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],t0_perf=arm_tick,t0_unix=arm_unix))
            supervised(l,i,arm_tick); finish_producer(l,arm_tick,arm_unix); verify(l,i)
            write(fee/f'{n:02d}_after.json',dict(producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json'),verification_complete=True))
            remaining=(len(launches)-n)*l['cap_seconds']+(54000+360 if qualification else 0)
            assert budget()['paid_outer_seconds']+time.perf_counter()-tick+remaining<=TOTAL_LIMIT
            if qualification: assert budget()['qualification_seconds']+time.perf_counter()-tick<=QUAL_LIMIT
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8'); raise
    finally: fee_pending(fee,tick,code,launches)

def current_process():
    api=ctypes.WinDLL('kernel32',use_last_error=True); api.GetCurrentProcess.restype=ctypes.c_void_p
    return types.SimpleNamespace(_handle=api.GetCurrentProcess())

def controller(kind,label):
    workspace(); assert not budget()['unclosed']
    log=OUT/'controller'/label; log.mkdir(parents=True,exist_ok=False)
    cmd=[str(PYTHON),'-B','scripts/round123_runner.py','worker',kind,label]
    start=time.perf_counter(); unix=time.time()
    with (log/'stdout.log').open('xb') as so,(log/'stderr.log').open('xb') as se:
        child=subprocess.Popen(cmd,cwd=ROOT,env=environment(),stdout=so,stderr=se)
        birth=child_creation(child)
        write(log/'launch.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=birth,
            command=cmd,controller_pid=os.getpid(),controller_actual_creation_unix=child_creation(current_process())))
        code=child.wait()
    end=time.perf_counter(); ended=time.time(); fee=OUT/'fees'/label
    pending=read(fee/'pending_exit_receipt.json')
    assert pending['wrapper_pid']==child.pid and pending['exit_code']==code
    seconds=max(pending['outer_seconds_lower'],end-start,ended-birth)
    write(fee/'receipt.json',dict(pending,outer_seconds_upper=seconds,actual_exit_observed=True,
        exit_observed_unix=ended,process_creation_unix=birth,actual_exit_code=code,controller_elapsed=end-start,
        wrapper_import_creation_trailer_and_exit_included=True,native_components_not_added_twice=True,
        controller_process_count=1,controller_wait_is_nested_not_added_again=True))
    write(log/'receipt.json',dict(exit_code=code,seconds=end-start,budget=budget()))
    print(json.dumps(dict(label=label,exit_code=code,outer_seconds=seconds,budget=budget())),flush=True)
    assert code==0

if __name__=='__main__':
    if sys.argv[1]=='worker': worker(sys.argv[2],sys.argv[3])
    else: controller(sys.argv[1],sys.argv[2])
