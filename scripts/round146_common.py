"""Round146 serial outer-cost ledger. No process or Native load at import."""
import round140_common as _meter
from round140_common import (Path,ctypes,datetime,hashlib,json,math,os,subprocess,sys,time,utc,sha,read,write,git)
ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
OUT=ROOT/'results/unified_exact_round146'
TEMP=WORK/'temp/round146'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
LP_PYTHON=Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
DLL,DLL_SHA=_meter.DLL,_meter.DLL_SHA
BASE='2b9740b6dde6d3d8ae0e6290c6e6531aee79b98b'
def configure():
    _meter.OUT,_meter.TEMP=OUT,TEMP
    _meter.LIMITS=dict(diagnostic=28800.,native=28800.);_meter.TOTAL_LIMIT=28800.
configure()
budget,metered,environment=_meter.budget,_meter.metered,_meter.environment
if __name__=='__main__':
    if sys.argv[1]=='budget':print(json.dumps(budget()))
    elif sys.argv[1]=='status':print(json.dumps(_meter.light_status(sys.argv[2])))
