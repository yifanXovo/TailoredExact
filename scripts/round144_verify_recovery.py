"""Verify a sealed producer after a reader-only fix; never reenter Native."""
from round144_read import verify
from round144_common import *
configure()
def run(batch,position):
    label=f'{batch}_{position}_reader_recovery'
    assert metered(label,'diagnostic',[PYTHON,'-B',__file__,'verify',batch,position],120,180)==0
def recover(batch,position):
    g=read(OUT/f'{batch}_matrix.json')['groups'][int(position)-1];identity=read(OUT/g['group']/'identity.json');l=g['launch'];d=Path(l['destination'])
    assert sha(OUT/g['group']/'identity.json')==g['identity_SHA']
    assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists() and not (d/'verification_closeout.json').exists()
    before=sha(d/'producer_seal.json');tick=time.perf_counter();value=verify(l,identity)
    assert sha(d/'producer_seal.json')==before
    write(OUT/'engineering'/(f'{batch}_{position}_reader_recovery.json'),dict(UTC=utc(),batch=batch,position=position,
        producer_seal_SHA=before,producer_repeated=False,Native_load=0,Optimize=0,seconds=time.perf_counter()-tick,
        changed_helpers={p:sha(ROOT/p) for p in ['scripts/round118_call_logs.py','scripts/round144_read.py']},endpoint=value['arm'],
        delayed_qualification_verification_latency_retained_in_T_total=True))
    print(json.dumps(value['arm']),flush=True)
if __name__=='__main__':
    if sys.argv[1]=='run':run(sys.argv[2],sys.argv[3])
    else:recover(sys.argv[2],sys.argv[3])
