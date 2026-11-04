"""Round154 serial outer accounting; inherited evidence is read-only."""
from round153_common import *
import round140_common as meter

OLD153 = ROOT/'results/unified_exact_round153'
OUT = ROOT/'results/unified_exact_round154'
BASE = 'ffcfb59899611cbefa1cfe0d739cba5f9b6e5fe5'
SCIENCE153 = '7d64c14faac43c6f410d435dd73b5ba5e49f2f30'

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round154'
    meter.LIMITS = dict(research=144000., verification=144000., native=144000.)
    meter.TOTAL_LIMIT = 144000.

def budget():
    configure(); return meter.budget()

def run(label, seconds, script, args, kind='research'):
    configure(); snapshot={}
    for folder,pattern in [('scripts','round154*.py'),('include','Round154*')]:
        for source in sorted((ROOT/folder).glob(pattern)):
            digest=sha(source); p=OUT/'engineering/source_bytes'/f'{digest}.txt'
            p.parent.mkdir(parents=True,exist_ok=True)
            if not p.exists(): p.write_bytes(source.read_bytes())
            snapshot[source.relative_to(ROOT).as_posix()]=digest
    write(OUT/'engineering/source_snapshots'/f'{label}.json',
          dict(UTC=utc(),files=snapshot,fixed_dependency_base=BASE))
    rc=meter.metered(label,kind,[PYTHON,'-B',ROOT/'scripts'/script,*args],
                     reservation=float(seconds),timeout=float(seconds))
    assert rc==0,(label,rc)

if __name__=='__main__':
    if len(sys.argv)==1: print(json.dumps(budget(),indent=2))
    else: run(sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4:])
