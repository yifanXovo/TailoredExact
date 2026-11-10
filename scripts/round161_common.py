"""Isolated R161 accounting; importing this module never runs a producer."""
from round153_common import *
from round140_common import git

OUT=ROOT/'results/unified_exact_round161'
BUILD=WORK/'build-cache/round161'
PE=BUILD/'v1/Round161Research.exe'
if (OUT/'candidate_manifest.json').exists():PE=Path(read(OUT/'candidate_manifest.json')['research_PE'])
BASE='53e5c62fbcf6bc24898b7d5d3ecb755e4331ab0b'
TOTAL=86400.

def configure():
    meter.OUT,meter.TEMP=OUT,WORK/'temp/round161'
    meter.LIMITS=dict(research=TOTAL,verification=TOTAL,native=TOTAL)
    meter.TOTAL_LIMIT=TOTAL

def budget():
    configure();return meter.budget()

def metered(label,kind,args,seconds):
    configure()
    return meter.metered(label,kind,args,reservation=seconds,timeout=seconds,cwd=ROOT)

if __name__=='__main__':
    if len(sys.argv)==1:print(json.dumps(budget(),indent=2))
    else:sys.exit(metered(sys.argv[1],sys.argv[2],sys.argv[4:],float(sys.argv[3])))
