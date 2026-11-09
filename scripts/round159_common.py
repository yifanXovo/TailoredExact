"""Isolated Round159 accounting. Importing historical helpers launches nothing."""
from round153_common import *

OUT = ROOT/'results/unified_exact_round159'
TOTAL = 129600.
BASE = 'd58cbcca6d2c656a2af09d701bcd9ca0c7a07e85'
BUILD = WORK/'build-cache/round159'
PE = BUILD/'Round159Research.exe'

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round159'
    meter.LIMITS = dict(research=TOTAL, verification=TOTAL, native=TOTAL)
    meter.TOTAL_LIMIT = TOTAL

def budget():
    configure()
    return meter.budget()

def run(label, seconds, script, args=(), kind='research'):
    configure()
    files = list((ROOT/'scripts').glob('round159_*.py'))
    files += list((ROOT/'src').glob('*159*'))+list((ROOT/'include').glob('*159*'))
    snapshot = {}
    for p in files:
        digest=sha(p); dest=OUT/'engineering/source_bytes'/f'{digest}.txt'
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists(): dest.write_bytes(p.read_bytes())
        snapshot[p.relative_to(ROOT).as_posix()]=digest
    write(OUT/'engineering/source_snapshots'/f'{label}.json',dict(UTC=utc(),files=snapshot,base=BASE))
    command=[PYTHON,'-B',ROOT/'scripts'/script,*args]
    rc=meter.metered(label,kind,command,reservation=float(seconds),timeout=float(seconds),cwd=ROOT)
    assert rc==0,(label,rc)

if __name__=='__main__':
    if len(sys.argv)==1: print(json.dumps(budget(),indent=2))
    else: run(sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4:])
