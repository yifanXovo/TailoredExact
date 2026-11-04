"""Round153 serial outer accounting and immutable research source snapshots."""
from pathlib import Path
import datetime, gzip, hashlib, json, math, os, subprocess, sys, time
import round140_common as meter

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT/'results/unified_exact_round153'
OLD = ROOT/'results/unified_exact_round152'
PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
BASE = 'ed058861e5eb094bc22d468a71a791bf558b51ac'
SCIENCE = 'd489ec2948f079105e4532a2e06ae4eed9fcd500'
DLL, DLL_SHA = meter.DLL, meter.DLL_SHA
sha, read, write, utc = meter.sha, meter.read, meter.write, meter.utc

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round153'
    meter.LIMITS = dict(research=115200., verification=115200., native=115200.)
    meter.TOTAL_LIMIT = 115200.

def save_gz(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(path,'wt',encoding='utf-8') as f:
        json.dump(value,f,separators=(',',':'),allow_nan=False)

def load_gz(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)

def budget():
    configure();return meter.budget()

def run(label, seconds, script, args, kind='research'):
    configure();snapshot={}
    for source in sorted((ROOT/'scripts').glob('round153*.py')):
        digest=sha(source);p=OUT/'engineering/source_bytes'/f'{digest}.py.txt'
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(source.read_bytes())
        snapshot[source.relative_to(ROOT).as_posix()]=digest
    write(OUT/'engineering/source_snapshots'/f'{label}.json',
          dict(UTC=utc(),files=snapshot,fixed_dependency_base=BASE))
    assert meter.metered(label,kind,[PYTHON,'-B',ROOT/'scripts'/script,*args],
                         reservation=float(seconds),timeout=float(seconds))==0,label

if __name__=='__main__':
    if len(sys.argv)==1:print(json.dumps(budget(),indent=2))
    else:run(sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4:])
