"""One frozen two-method group; unchanged R121 producer and R122 verification."""
from round126_common import *
from round121_campaign import supervised,finish_producer
from round122_evidence import verify
from round115_common import process_origin
from round100_idle import ensure_idle
import traceback

def execute_group(n):
    workspace();tick,creation=process_origin();identity();n=int(n)
    gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
    assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
    i=read(OUT/f'campaign/group{n:02d}/identity.json');assert i['helpers']==helpers() and i['source_hashes']==bindings()
    ensure_idle();assert shutil.disk_usage(WORK).free>=read(OUT/'workspace_capacity.json')['minimum_group_start_free_bytes']
    receipt=OUT/f'campaign/group{n:02d}/group_start.json';assert not receipt.exists()
    write(receipt,dict(UTC=utc(),wrapper_pid=os.getpid(),wrapper_creation_unix=creation,source=SOURCE,
        no_retries=True,gate_SHA=sha(OUT/'review/performance_admission.json'),budget=budget()))
    try:
        for position,l in enumerate(i['launches'],1):
            at=tick if position==1 else time.perf_counter();au=creation if position==1 else time.time()
            assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            identity();supervised(l,i,at);finish_producer(l,at,au);verify(l,i)
        from read_round126 import rebuild_group
        gtime=time.perf_counter();value=rebuild_group(n,OUT/f'reconstruction/group{n:02d}')
        write(OUT/f'campaign/group{n:02d}/group_verification.json',dict(seconds=time.perf_counter()-gtime,Optimize=0,
            current_core_SHA=sha(OUT/f'reconstruction/group{n:02d}/current_core.json'),inside_group_outer_clock=True))
        print(json.dumps(dict(group=n,pair=value['pair'])),flush=True)
    except BaseException:
        (OUT/f'campaign/group{n:02d}/failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise

if __name__=='__main__':execute_group(sys.argv[1])
