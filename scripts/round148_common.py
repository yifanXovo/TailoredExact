"""Round148 finite, serial outer accounting. Import never loads Native."""
import round140_common as _meter
from round140_common import (Path, ctypes, datetime, hashlib, json, math, os,
                            subprocess, sys, time, utc, sha, read, write, git)

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT / 'results/unified_exact_round148'
TEMP = WORK / 'temp/round148'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
LP_PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DLL, DLL_SHA = _meter.DLL, _meter.DLL_SHA
BASE = 'b0481ad63d557b1ec36994a74bfb372793f40d7f'
SCIENCE146 = '8ec2aebe46398485019623d9b18a3e30617d4997'
ROLES = [('K-20-S', 'base'), ('K-20-S', 'joint'), ('K-20-S', 'stock'),
         ('K-35-U', 'base'), ('R-X20-S-T1', 'base')]


def configure():
    _meter.OUT, _meter.TEMP = OUT, TEMP
    _meter.LIMITS = dict(diagnostic=18000., native=18000.)
    _meter.TOTAL_LIMIT = 18000.


configure()
budget, metered, environment = _meter.budget, _meter.metered, _meter.environment

if __name__ == '__main__':
    print(json.dumps(budget()))
