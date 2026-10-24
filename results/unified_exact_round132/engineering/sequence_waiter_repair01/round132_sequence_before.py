"""Continue authorized serial stages only after every preceding seal closes.

This watcher never restarts D or a failed producer. It is a same-task stage
dependency, not a recurring automation or an extra experimental allocation.
"""
from round132_common import *
from round115_common import process_origin

def sealed(groups):
    count=0
    for g in groups:
        p=OUT/g['name']/'reconstructed.json'
        if not p.exists():return False,count
        rows=read(p)['arms'];count+=len(rows)
        assert all(a['formal_protocol_qualified'] for a in rows),'Preceding evidence unqualified; stop for local repair'
    return True,count

def run():
    _,creation=process_origin()
    write(OUT/'sequence_PID.json',dict(pid=os.getpid(),actual_creation_unix=creation,command=sys.argv,UTC=utc(),
        action='wait for all60D + closed receipts, then admitted24C, then preregistered boundedE; never restart failed D'))
    dgroups=read(OUT/'experiment_plan.json')['D'];until=time.time()+42*3600
    while True:
        complete,n=sealed(dgroups)
        if complete and not budget()['unclosed']:break
        assert time.time()<until,'Dependency wait exceeded42h; inspect actual processes, no automatic retry'
        # A failed closed producer stops the sequence; a healthy/ongoing arm
        # remains untouched. No optimization occurs while waiting.
        for p in (OUT/'fees').glob('formal_D*/receipt.json'):
            assert read(p)['exit_code']==0,('D failure requires inspection',str(p))
        time.sleep(20)
    assert n==60;print('D_60_SEALS_AND_CLOSED_RECEIPTS_CONFIRMED',flush=True)
    assert read(OUT/'review/C_admission.json')['decision']=='ACCEPT'
    subprocess.run([str(PYTHON),'-B',str(ROOT/'scripts/round132_C.py'),'run'],cwd=ROOT,env=environment(),check=True)
    complete,n=sealed(read(OUT/'C_experiment_plan.json')['groups']);assert complete and n==24 and not budget()['unclosed']
    print('C_24_SEALS_AND_CLOSED_RECEIPTS_CONFIRMED',flush=True)
    assert not (OUT/'joint_results.json').exists() and not (OUT/'joint').exists()
    assert budget()['remaining_G1_seconds']>=10800
    native_python=Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
    assert metered('E_complete_tiny01','E',[native_python,'-B',ROOT/'scripts/round132_joint.py','run'],timeout=10800)==0
    write(OUT/'sequence_completion.json',dict(UTC=utc(),D_arms=60,C_arms=24,E=read(OUT/'joint_results.json')['execution'],budget=budget(),
        remaining='read-only analysis, E/C3 gate interpretation, final manuscript, independent final review, PDF QA, normal stacked Draft PR, one public recovery and owned cleanup'))
    print('AUTHORIZED_REQUIRED_EXPERIMENTS_SEALED; READ_ONLY_DELIVERY_REMAINS',flush=True)
if __name__=='__main__':run()
