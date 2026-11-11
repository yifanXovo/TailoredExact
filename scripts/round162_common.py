"""R162 isolated serial accounting; importing never starts a producer."""
from round153_common import *
from round140_common import git

OUT = ROOT/'results/unified_exact_round162'
BUILD = WORK/'build-cache/round162'
BASE = 'dd75d7a2445dafdcd9b9c443a107a0c3ca4a15f3'
TOTAL = 86400.
PRIOR = WORK/'worktrees/round161/results/unified_exact_round161'

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round162'
    meter.LIMITS = dict(research=TOTAL, verification=TOTAL, native=TOTAL)
    meter.TOTAL_LIMIT = TOTAL

def budget():
    configure()
    return meter.budget()

def metered(label, kind, args, seconds):
    configure()
    return meter.metered(label,kind,args,reservation=float(seconds),timeout=float(seconds),cwd=ROOT)

def pe():
    return Path(read(OUT/'candidate_manifest.json')['research_PE'])

if __name__ == '__main__':
    if len(sys.argv)==1: print(json.dumps(budget(),indent=2))
    else: sys.exit(metered(sys.argv[1],sys.argv[2],sys.argv[4:],float(sys.argv[3])))
