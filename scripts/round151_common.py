"""Round151 bounded accounting; no Native loads or solves on import."""
import round140_common as _meter
from round140_common import (Path,ctypes,datetime,hashlib,json,math,os,subprocess,sys,time,utc,sha,read,write,git)
ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
OUT=ROOT/'results/unified_exact_round151'
TEMP=WORK/'temp/round151'
BUILD=WORK/'build-cache/round151'
BASE='7cac24abd8bfffa96a9dc7569d9a93f1697881a7'
SCIENCE150='59c4e398f385aa8525fe87a4212ed97554f093e8'
SCIENCE137='e735c3447eb1443713c700942d873de1783a4a26'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
LP_PYTHON=Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DLL,DLL_SHA=_meter.DLL,_meter.DLL_SHA
def configure():
    _meter.OUT,_meter.TEMP=OUT,TEMP
    _meter.LIMITS=dict(diagnostic=14400.,native=14400.)
    _meter.TOTAL_LIMIT=14400.
configure()
budget,metered,environment=_meter.budget,_meter.metered,_meter.environment
if __name__=='__main__':print(json.dumps(budget()))
