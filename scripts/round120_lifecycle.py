"""The single authorized R119 physical-tail supplement, billed to Round120."""
from round120_common import *
import traceback
def run():
    fee,tick=fee_begin('qual01_old_tail',1,120,True,dict(starts=29,seconds=37440));code=1;actual=0
    try:
        from round100_idle import ensure_idle
        ensure_idle()
        p=read(OLD/'results/unified_exact_round119/production_identity.json')
        assert sha(OLD/'build/research/round119/ExactEBRP.exe')==p['production_PE_SHA']=='e107d34ca849e3615cb812a7525ba9879e53946e04c7405d13a767786d3e06c6'
        assert sha(DLL)==p['DLL_SHA']==DLL_SHA
        for n,h in p['source_bindings'].items():assert sha(OLD/n)==h,n
        binary=OUT/'engineering/Round119LifecycleQualification.exe'
        command=[str(binary),str(OLD/'reference/round119_qualification/micro_enumeration.txt'),str(OUT/'qualification/old_tail')]
        write(fee/'child_launch.json',dict(command=command,binary_SHA=sha(binary),
            source_SHA=sha(ROOT/'tests/round119_lifecycle_qualification.cpp'),
            linked_original_core_SHA=sha(OLD/'build/research/round119/libexact_ebrp_core.a'),
            original_failed_fee_SHA=sha(OLD/'results/unified_exact_round119/fees/qual03/pending_exit_receipt.json'),Optimize=0))
        actual=1
        with (fee/'stdout.txt').open('w',encoding='utf-8') as f:
            child=subprocess.Popen(command,cwd=ROOT,env=environment(),stdout=f,stderr=subprocess.STDOUT)
            write(fee/'child_PID.json',dict(pid=child.pid,created_observed_unix=time.time()))
            try:rc=child.wait(timeout=90)
            except subprocess.TimeoutExpired:child.kill();child.wait();raise
        write(fee/'child_return.json',dict(exit_code=rc,returned_unix=time.time(),Optimize=0));assert rc==0
        events=[json.loads(s) for s in (OUT/'qualification/old_tail/physical_negative_events.jsonl').read_text().splitlines()]
        assert sum(e['kind']=='own_verified' for e in events)==1 and sum(e['kind']=='revoked' for e in events)==1
        assert read(OUT/'qualification/old_tail/lifecycle.json')['passed']
        write(OUT/'qualification/old_tail_supplement.json',dict(passed=True,Optimize=0,
            paid_round=120,original_R119_failure_preserved=True,R119_retroactive_pass=False,
            repeat_callback_revocation_legal_U=True,original_core_SHA=sha(OLD/'build/research/round119/libexact_ebrp_core.a')))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)
if __name__=='__main__':run()
