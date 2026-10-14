"""A final bounded zero-Optimize lifecycle process; production bytes stay frozen."""
from round119_common import *
import subprocess,traceback

def billed(label):
    fee,tick=fee_begin(label,1,120,True,dict(starts=16,seconds=36480));code=1;actual=0
    try:
        from round100_idle import ensure_idle
        ensure_idle();identity()
        binary=ROOT/'build/research/round119/Round119LifecycleQualification.exe'
        command=[str(binary),str(ROOT/'reference/round119_qualification/micro_enumeration.txt'),str(OUT/'qualification/lifecycle')]
        write(fee/'child_launch.json',dict(command=command,binary_SHA=sha(binary),source_SHA=sha(ROOT/'tests/round119_lifecycle_qualification.cpp'),
            linked_existing_core_SHA=sha(ROOT/'build/research/round119/libexact_ebrp_core.a'),production_PE_SHA=sha(PE),Optimize=0))
        actual=1
        with (fee/'stdout.txt').open('w',encoding='utf-8') as f:
            child=subprocess.Popen(command,cwd=ROOT,env=environment(),stdout=f,stderr=subprocess.STDOUT)
            write(fee/'child_PID.json',dict(pid=child.pid,created_observed_unix=time.time()))
            try:rc=child.wait(timeout=90)
            except subprocess.TimeoutExpired:child.kill();child.wait();raise
        write(fee/'child_return.json',dict(exit_code=rc,returned_unix=time.time(),Optimize=0));assert rc==0
        events=[json.loads(s) for s in (OUT/'qualification/lifecycle/physical_negative_events.jsonl').read_text(encoding='utf-8').splitlines()]
        assert sum(e['kind']=='own_verified' for e in events)==1 and sum(e['kind']=='revoked' for e in events)==1
        assert read(OUT/'qualification/lifecycle/lifecycle.json')['passed']
        gate=read(OUT/'review/performance_admission.json');gate['finite_lifecycle_supplement_SHA']=sha(OUT/'qualification/lifecycle/lifecycle.json')
        gate['paid_fee_labels'].append(label);write(OUT/'review/performance_admission.json',gate);code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)
if __name__=='__main__':billed(sys.argv[1])
