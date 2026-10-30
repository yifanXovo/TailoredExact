"""Round141 uses the audited serial outer-process meter, with a new ledger.

No solver/process/IO at import. The Round140 helper's process-local settings
are rebound only in this new entry; historical scripts/files stay unchanged.
"""
import round140_common as _meter
from round140_common import (Path, argparse, ctypes, datetime, hashlib, json,
    math, os, subprocess, sys, time, utc, sha, read, write, git)

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT/'results/unified_exact_round141'
TEMP = WORK/'temp/round141'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
LP_PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DOCUMENT_PYTHON = _meter.DOCUMENT_PYTHON
DLL, DLL_SHA = _meter.DLL, _meter.DLL_SHA
BASE = 'd00bcf41520bd5bbbdc81096165deba25eae8023'
SCIENCE140 = '15e401f794bb53e31c5848e0edabf0b4153ca678'
_meter.OUT, _meter.TEMP = OUT, TEMP
_meter.LIMITS = dict(diagnostic=3600., native=36000.)
_meter.TOTAL_LIMIT = 36000.
budget, metered, environment = _meter.budget, _meter.metered, _meter.environment
light_status = _meter.light_status

if __name__ == '__main__':
    if sys.argv[1] == 'budget':
        print(json.dumps(budget()))
    elif sys.argv[1] == 'status':
        print(json.dumps(light_status(sys.argv[2])))
    elif sys.argv[1] == 'meter':
        # label kind reservation timeout -- command ...
        assert sys.argv[6] == '--'
        sys.exit(metered(sys.argv[2], sys.argv[3], sys.argv[7:],
                        float(sys.argv[4]), float(sys.argv[5])))
