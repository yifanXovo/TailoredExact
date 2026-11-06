"""Round155 serial outer fees and immutable new-source receipts."""
from round153_common import *
import round140_common as meter

OUT = ROOT/'results/unified_exact_round155'
OLD153 = ROOT/'results/unified_exact_round153'
OLD154 = ROOT/'results/unified_exact_round154'
BASE = 'c0b64d66cb0fda36528f764e9b1264df68f45c8b'
SCIENCE154 = 'a1a3a8d1d88d0af35163e7f134bac09e1ad2077c'
SCIENCE153 = '7d64c14faac43c6f410d435dd73b5ba5e49f2f30'
SCIENCE137 = 'e735c3447eb1443713c700942d873de1783a4a26'

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round155'
    meter.LIMITS = dict(research=172800., verification=172800., native=172800.)
    meter.TOTAL_LIMIT = 172800.

def budget():
    configure(); return meter.budget()

def run(label, seconds, script, args, kind='research'):
    configure(); snapshot={}
    for source in sorted((ROOT/'scripts').glob('round155*.py')):
        digest=sha(source); path=OUT/'engineering/source_bytes'/f'{digest}.py.txt'
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists(): path.write_bytes(source.read_bytes())
        snapshot[source.relative_to(ROOT).as_posix()]=digest
    write(OUT/'engineering/source_snapshots'/f'{label}.json',
          dict(UTC=utc(),files=snapshot,fixed_dependency_base=BASE))
    code=meter.metered(label,kind,[PYTHON,'-B',ROOT/'scripts'/script,*args],
                       reservation=float(seconds),timeout=float(seconds))
    assert code==0,(label,code)

if __name__=='__main__':
    if len(sys.argv)==1: print(json.dumps(budget(),indent=2))
    else: run(sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4:])
