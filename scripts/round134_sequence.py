"""Continue the already fixed serial work after the initial 14 positions seal.

The waiting driver does not reserve/charge a second copy of nested native time.
Each native/build outer retains its own Round134 meter and failure evidence.
"""
from round134_common import *

def main():
    started=time.time();waiting=time.perf_counter();idle_since=None
    groups=read(OUT/'C_matrix_frozen.json')['groups'][:14]
    while not all((Path(g['launch']['destination'])/'verification_closeout.json').exists() for g in groups):
        b=budget()
        if b['unclosed']:idle_since=None
        elif idle_since is None:idle_since=time.perf_counter()
        elif time.perf_counter()-idle_since>30:
            raise RuntimeError('Initial sequence stopped before all14; inspect original failure without native retry')
        assert time.perf_counter()-waiting<6000
        time.sleep(5)
    while budget()['unclosed']:time.sleep(1)
    steps=[('E_compile',['round134_roots.py','compile']),('E_prepare',['round134_roots.py','prepare']),
        ('E_LPs',['round134_roots.py','run']),('C_remaining',['round134_campaign.py','run','C']),
        ('D_four',['round134_campaign.py','run','D']),('aggregate',['round134_analyze.py'])]
    if '--resume-after-root-runtime' in sys.argv:
        old=read(OUT/'sequence_driver_status.json')
        assert old['state']=='FAILED_PRESERVE' and old['stage']=='E_LPs'
        assert all((OUT/'math/roots'/role/f'layer{layer}/result.json').exists() for role in ('K-20-S','K-35-U') for layer in range(3))
        write(OUT/'sequence_driver_failed_root_runtime.json',old)
        steps=steps[3:] # All six healthy LPs remain sealed; never rerun them.
    for name,args in steps:
        write(OUT/'sequence_driver_status.json',dict(UTC=utc(),stage=name,state='RUNNING',started_unix=started,
            child_command=[str(PYTHON),str(ROOT/'scripts'/args[0]),*args[1:]],nested_times_not_double_charged=True))
        result=subprocess.run([PYTHON,ROOT/'scripts'/args[0],*args[1:]],cwd=ROOT,env=environment())
        if result.returncode:
            write(OUT/'sequence_driver_status.json',dict(UTC=utc(),stage=name,state='FAILED_PRESERVE',exit_code=result.returncode,
                healthy_arms_not_repeated=True,no_automatic_retry=True));raise SystemExit(result.returncode)
    write(OUT/'sequence_driver_status.json',dict(UTC=utc(),state='COMPLETE_C_D_E_NATIVE',started_unix=started,
        ended_unix=time.time(),budget=budget(),driver_elapsed_not_an_additional_native_charge=True))
    print('FIXED SERIAL C/D/E SEQUENCE COMPLETE',flush=True)
if __name__=='__main__':main()
