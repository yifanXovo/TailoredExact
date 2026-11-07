"""Round157 serial accounting and immutable launch-source snapshots."""
from round153_common import *

OUT = ROOT/'results/unified_exact_round157'
PRIOR = WORK/'worktrees/round156'
BASE = 'e10ffd01de6cf2fa9db71ba5a51f7d9eab8efb05'
SCIENCE156 = '751de842a0264a146701de6669b1f3dd6dc764b1'
TOTAL = 216000.

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round157'
    meter.LIMITS = dict(research=TOTAL, verification=TOTAL, native=TOTAL)
    meter.TOTAL_LIMIT = TOTAL

def budget():
    configure()
    return meter.budget()

def run(label, seconds, script, args, kind='research'):
    configure()
    snapshot = {}
    for source in sorted((ROOT/'scripts').glob('round157*')):
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
