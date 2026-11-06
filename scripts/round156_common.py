"""Round156 serial outer accounting; inherited runtime remains read-only."""
from round153_common import *
import round140_common as meter

OUT = ROOT/'results/unified_exact_round156'
PRIOR = WORK/'worktrees/paper-current'
BASE = '5675acd0da875b4c7ac51f145ec151ee5c14d68a'
SCIENCE155 = '1a73c0fad8fd7298e04920efc482072d191dfb97'
SCIENCE154 = 'a1a3a8d1d88d0af35163e7f134bac09e1ad2077c'

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round156'
    meter.LIMITS = dict(research=172800., verification=172800., native=172800.)
    meter.TOTAL_LIMIT = 172800.

def budget():
    configure()
    return meter.budget()

def run(label, seconds, script, args, kind='research'):
    configure()
    snapshot = {}
    for source in sorted((ROOT/'scripts').glob('round156*')):
        if not source.is_file(): continue
        digest = sha(source)
        target = OUT/'engineering/source_bytes'/f'{digest}.txt'
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists(): target.write_bytes(source.read_bytes())
        snapshot[source.relative_to(ROOT).as_posix()] = digest
    write(OUT/'engineering/source_snapshots'/f'{label}.json',
          dict(UTC=utc(), files=snapshot, fixed_dependency_base=BASE))
    code = meter.metered(label, kind, [PYTHON, '-B', ROOT/'scripts'/script, *args],
                         reservation=float(seconds), timeout=float(seconds), cwd=ROOT)
    assert code == 0, (label, code)

if __name__ == '__main__':
    if len(sys.argv) == 1: print(json.dumps(budget(), indent=2))
    else: run(sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4:])
