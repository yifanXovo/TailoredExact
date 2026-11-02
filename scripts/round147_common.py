"""Round147 serial accounting; reuse R146 production without recompilation."""
import round140_common as _meter
from round140_common import (Path, ctypes, datetime, hashlib, json, math, os,
                            subprocess, sys, time, utc, sha, read, write, git)

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT / 'results/unified_exact_round147'
OLD = ROOT / 'results/unified_exact_round146'
TEMP = WORK / 'temp/round147'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
DLL, DLL_SHA = _meter.DLL, _meter.DLL_SHA
BASE = '10bcea1bbde1eff37978e45ec23e567b384638dc'
SCIENCE146 = '8ec2aebe46398485019623d9b18a3e30617d4997'


def configure():
    _meter.OUT, _meter.TEMP = OUT, TEMP
    _meter.LIMITS = dict(diagnostic=18000., native=18000.)
    _meter.TOTAL_LIMIT = 18000.


configure()
budget, metered, environment = _meter.budget, _meter.metered, _meter.environment

if __name__ == '__main__':
    if sys.argv[1] == 'budget':
        print(json.dumps(budget()))
    elif sys.argv[1] == 'status':
        print(json.dumps(_meter.light_status(sys.argv[2])))
