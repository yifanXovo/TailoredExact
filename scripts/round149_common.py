"""Round149 serial outer accounting; importing this module never loads Native."""
import round140_common as _meter
from round140_common import (Path, ctypes, datetime, hashlib, json, math, os,
                            subprocess, sys, time, utc, sha, read, write, git)

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT / 'results/unified_exact_round149'
TEMP = WORK / 'temp/round149'
BUILD = WORK / 'build-cache/round149'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
LP_PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DLL, DLL_SHA = _meter.DLL, _meter.DLL_SHA
BASE = 'c2130a0f3f915d1f6b2f7fcc4c383913db33e47c'
SCIENCE146 = '8ec2aebe46398485019623d9b18a3e30617d4997'
ROLES = ['K-20-S', 'K-35-U', 'R-X20-S-T1']


def configure():
    _meter.OUT, _meter.TEMP = OUT, TEMP
    _meter.LIMITS = dict(diagnostic=18000., native=18000.)
    _meter.TOTAL_LIMIT = 18000.


configure()
budget, metered, environment = _meter.budget, _meter.metered, _meter.environment

if __name__ == '__main__':
    print(json.dumps(budget()))
