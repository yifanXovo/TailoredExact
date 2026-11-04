"""Round152 isolated, serial outer accounting. No solver is imported here."""
from pathlib import Path
import datetime, gzip, hashlib, json, math, os, subprocess, sys, time
import round140_common as meter

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT/'results/unified_exact_round152'
RAW = WORK/'raw/round152'
PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DLL, DLL_SHA = meter.DLL, meter.DLL_SHA
BASE = 'c6e930ffcb84f0c3801c651f28b5f7e8e2062f33'
sha, read, write, utc = meter.sha, meter.read, meter.write, meter.utc

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round152'
    meter.LIMITS = dict(research=86400., verification=86400., native=86400.)
    meter.TOTAL_LIMIT = 86400.

def budget():
    configure()
    return meter.budget()

def save_gz(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(path,'wt',encoding='utf-8') as f: json.dump(value,f,separators=(',',':'),allow_nan=False)

def load_gz(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)

def run(label, seconds, script, args, kind='research'):
    configure()
    snapshot={}
    for source in sorted((ROOT/'scripts').glob('round152*.py')):
        digest=sha(source);p=OUT/'engineering/source_bytes'/f'{digest}.py.txt'
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(source.read_bytes())
        snapshot[source.relative_to(ROOT).as_posix()]=digest
    write(OUT/'engineering/source_snapshots'/f'{label}.json',dict(UTC=utc(),files=snapshot,fixed_dependency_base=BASE))
    assert meter.metered(label,kind,[PYTHON,'-B',ROOT/'scripts'/script,*args],
                         reservation=float(seconds),timeout=float(seconds))==0,label

if __name__=='__main__':
    if len(sys.argv)==1: print(json.dumps(budget(),indent=2))
    else: run(sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4:])
