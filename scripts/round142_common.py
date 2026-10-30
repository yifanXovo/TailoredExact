"""Round142 serial outer-process accounting; no work or Native load at import."""
import round140_common as _meter
from round140_common import (Path, argparse, ctypes, datetime, hashlib, json,
    math, os, subprocess, sys, time, utc, sha, read, write, git)

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT/'results/unified_exact_round142'
TEMP = WORK/'temp/round142'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
LP_PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DOCUMENT_PYTHON = _meter.DOCUMENT_PYTHON
DLL, DLL_SHA = _meter.DLL, _meter.DLL_SHA
BASE = 'dd59e0a07cde2255c4f2b3314246cb61eac431f6'
SCIENCE141 = '93db852d4fd82b91d5c8f681c80d776339f126d8'
def configure():
    # Historical helper imports may bind the shared meter to their own round.
    # A new entry restores these globals only after all inherited imports.
    _meter.OUT, _meter.TEMP = OUT, TEMP
    _meter.LIMITS = dict(diagnostic=3600., native=28800.)
    _meter.TOTAL_LIMIT = 28800.
configure()
budget, metered, environment = _meter.budget, _meter.metered, _meter.environment
light_status = _meter.light_status

if __name__ == '__main__':
    if sys.argv[1] == 'budget': print(json.dumps(budget()))
    elif sys.argv[1] == 'status': print(json.dumps(light_status(sys.argv[2])))
    elif sys.argv[1] == 'meter':
        assert sys.argv[6] == '--'
        sys.exit(metered(sys.argv[2],sys.argv[3],sys.argv[7:],float(sys.argv[4]),float(sys.argv[5])))
