"""Round150 bounded outer accounting. Importing never loads Native."""
import round140_common as _meter
from round140_common import (Path, ctypes, datetime, hashlib, json, math, os,
                            subprocess, sys, time, utc, sha, read, write, git)

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT / 'results/unified_exact_round150'
TEMP = WORK / 'temp/round150'
BASE = 'd33d47bb224ab3cd4eeacabc731b3fa8b16b7b2c'
SCIENCE149 = '3bb93fa2f4b8c267af8fae409864191e033c5bb2'
SCIENCE137 = 'e735c3447eb1443713c700942d873de1783a4a26'
SOURCE = '380a85f866bffb914036190f8ee2700ce8b55978'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
LP_PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DLL, DLL_SHA = _meter.DLL, _meter.DLL_SHA
ROLES = ['K-20-S', 'K-35-U', 'R-X20-S-T1']


def configure():
    _meter.OUT, _meter.TEMP = OUT, TEMP
    _meter.LIMITS = dict(diagnostic=14400., native=14400.)
    _meter.TOTAL_LIMIT = 14400.


configure()
budget, metered, environment = _meter.budget, _meter.metered, _meter.environment

if __name__ == '__main__':
    print(json.dumps(budget()))
