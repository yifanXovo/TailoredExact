"""One real paid wrapper: one finite CLI child, admission pause, then all8 arms.

The upfront count is 1+1+8=10. The pause is charged in the same outer receipt;
it creates no algorithm or solver restart. Separate confirmation can still
reserve 1+9=10, keeping the aggregate within72 after the retained failures.
"""
from round107_common import *
from round107_cli_qualification import run as qualify
from round107_campaign import batch,helpers
from round100_idle import ensure_idle

def run():
    ensure_idle();b=budget();assert not b['unclosed']
    assert b['remaining_starts']>=20 and b['remaining_outer_seconds']>=12000+35100+2000,b
    name='cli_and_development03';d=OUT/'fees'/name;d.mkdir(parents=True,exist_ok=False)
    control=OUT/'campaign_control'/name;control.mkdir(parents=True,exist_ok=False)
    pe=sha(BUILD/'ExactEBRP.exe');sources=bindings();dll=sha(DLL)
    write(d/'launch.json',dict(command=[sys.executable,__file__],engineering=False,
        conservative_process_starts=10,declared_native_children=9,actual_wrapper_processes=1,
        maximum_CLI_children=1,maximum_formal_children=8,cap_seconds=14035,
        maximum_admission_pause_seconds=1800,budget_before=b,source_bindings=sources,
        production_PE_SHA=pe,DLL_SHA=dll,helper_SHA=helpers(),
        future_confirmation_reservation=dict(conservative_starts=10,nominal_seconds=35100),
        accounting='One actual Python wrapper plus one CLI child and eight formal children, reserved before first child. Waiting is included in outer_seconds.'))
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));tick=time.perf_counter();code=0
    try:
        write(control/'01_CLI_before.json',dict(phase='CLI_QUALIFICATION',production_PE_SHA=pe))
        qualify('cli02',shared_wrapper=True)
        write(control/'02_CLI_after.json',dict(phase='WAITING_INDEPENDENT_ADMISSION',qualification_SHA=sha(OUT/'qualification/cli02/qualification.json'),
            native_child_closed=True,production_PE_SHA=pe))
        print('Actual production CLI passed; waiting for independent admission before any formal child.',flush=True)
        pause=time.perf_counter()
        while not (control/'release.json').exists():
            if (control/'abort.json').exists():raise RuntimeError(read(control/'abort.json'))
            assert time.perf_counter()-pause<1800,'independent admission pause limit'
            time.sleep(1)
        release=read(control/'release.json');assert release['campaign']=='development03'
        assert release['production_PE_SHA']==pe and sha(BUILD/'ExactEBRP.exe')==pe
        assert bindings()==sources and sha(DLL)==dll
        q=read(OUT/'development03/identity.json');gate=read(OUT/'review/performance_admission.json')
        assert release['campaign_identity_SHA']==sha(OUT/'development03/identity.json')
        assert gate['decision']=='ACCEPT' and gate['production_PE_SHA']==pe
        assert sha(OUT/'qualification/identity.json')==gate['qualification_identity_SHA']
        assert len(q['launches'])==8 and all(a['stage']=='development03' for a in q['launches'])
        write(control/'03_formal_before.json',dict(phase='FORMAL_FULL_EIGHT',admission_pause_seconds=time.perf_counter()-pause,
            campaign_identity_SHA=sha(OUT/'development03/identity.json'),admission_SHA=sha(OUT/'review/performance_admission.json')))
        batch('development03',1,8,'all_eight')
        write(control/'04_formal_after.json',dict(phase='COMPLETE',formal_children=8,qualification_children=1))
    except BaseException:code=1;raise
    finally:
        write(d/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick,engineering=False,
            conservative_process_starts=10,stop_reason='normal_return' if code==0 else 'retained_CLI_or_campaign_failure'))

if __name__=='__main__':run()
