"""Round143 serial outer accounting; reuse the established process meter."""
import round140_common as _meter
from round140_common import (Path, ctypes, datetime, hashlib, json, math, os,
    subprocess, sys, time, utc, sha, read, write, git)

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT/'results/unified_exact_round143'
TEMP = WORK/'temp/round143'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
LP_PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DLL, DLL_SHA = _meter.DLL, _meter.DLL_SHA
BASE = '37e6c4e79c18dbca6bc4622d80a5bd8a860aa13c'
CARRIER = ROOT/'results/unified_exact_round140/artifacts/diagnostics_and_failures.zip'
CARRIER_SHA = '2cb1ab936753ce9ac26ae1f970b070b2751190af79f6a80a8b0f5d254902bf5f'

def configure():
    _meter.OUT, _meter.TEMP = OUT, TEMP
    _meter.LIMITS = dict(diagnostic=28800., native=28800.)
    _meter.TOTAL_LIMIT = 28800.

configure()
budget, metered, environment = _meter.budget, _meter.metered, _meter.environment

if __name__ == '__main__':
    if sys.argv[1] == 'budget':
        print(json.dumps(budget()))
    elif sys.argv[1] == 'status':
        print(json.dumps(_meter.light_status(sys.argv[2])))
