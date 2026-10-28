"""Explicit pure replay of an already sealed producer; never repeats Optimize."""
from round137_common import *
import shutil
from round137_read import verify

def main(position):
    position=int(position);group=read(OUT/'matrix_frozen.json')['groups'][position-1]
    identity=read(OUT/group['group']/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    assert (d/'producer_seal.json').exists() and not (d/'verification_closeout.json').exists()
    names=['producer_seal.json','producer_receipt.json','result.json','completion.json','observations.json','launch.json']
    before={name:sha(d/name) for name in names};folder=OUT/'repair'/f'verification_{position:03}'
    folder.mkdir(parents=True,exist_ok=False)
    if (d/'round134_verification_failure.json').exists():
        shutil.copyfile(d/'round134_verification_failure.json',folder/'original_reader_failure.json')
    started=time.perf_counter();value=verify(launch,identity);seconds=time.perf_counter()-started
    assert before=={name:sha(d/name) for name in names}
    write(folder/'receipt.json',dict(UTC=utc(),PASS=True,position=position,Optimize=0,
        seconds=seconds,original_native_production_not_repeated=True,raw_SHA_before_and_after=before,
        fix='R135 state-AP-only contract excluded for original compact P/PS; all R134 original contracts remain',
        corrected_reader_SHA=sha(ROOT/'scripts/round137_read.py'),endpoint=value['arm'],
        timing_note='Original production and certificate clock retained. Raw T_verify/T_total retain real elapsed repair delay; pure replay work measured separately, no clock backfill.'))
    print(json.dumps(value['arm']))

if __name__=='__main__':main(sys.argv[1])
