"""Round164 bounded orchestration; importing this module never solves."""
from pathlib import Path
import hashlib, importlib, json, os, re, sys, time
import round140_common as meter

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT/'results/unified_exact_round164'
TEMP = WORK/'temp/round164'
BASE = '8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb'
R163_SCIENCE = 'f7083ace21ad2a8bd54bed71711ceebcb97c9e8c'
MEASURED_CPP = 'e920b92e199e825ec89a2932f701861ff158e0d4'
PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
PE = WORK/'build-cache/round162/complete_v2/ExactEBRP.exe'
PE_SHA = 'fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93'
DLL, DLL_SHA = meter.DLL, meter.DLL_SHA
INPUT_MANIFEST = ROOT/'results/unified_exact_round163/input_manifest.json'
INPUT_MANIFEST_SHA = '166bc5b463fb1dd2ad5c7819b5d31c86f706abf6ffd2a11469585ca623eedb1e'
TOTAL = 57600.
sha, read, write, utc, git = meter.sha, meter.read, meter.write, meter.utc, meter.git

def configure():
    meter.OUT, meter.TEMP = OUT, TEMP
    # The allocations in protocol.json are reservations, transferable within
    # the hard overall ceiling, rather than four independent full budgets.
    meter.LIMITS = dict(qualification=TOTAL, panel=TOTAL, verification=TOTAL, repair=TOTAL)
    meter.TOTAL_LIMIT = TOTAL

def budget():
    configure()
    return meter.budget()

def metered(label, kind, args, reservation, fault_timeout):
    """Keep scientific reservation separate from inherited failure timeout.

    Native has its unchanged inner deadline/watchdog. The outer still allows
    cap+900 for technical failure, subject to the actual total science ceiling.
    A 300s per-arm reservation never grants additional Native time.
    """
    configure()
    before = budget()
    timeout = min(float(fault_timeout), before['remaining_G1_seconds']-2.)
    assert timeout > 0 and reservation <= before['remaining_G1_seconds']
    return meter.metered(label, kind, args, reservation=float(reservation), timeout=timeout, cwd=ROOT)

def materialize(name, commit=BASE):
    path=ROOT/name
    if not path.exists():
        raw=git('show',commit+':'+name)
        assert len(raw)<10000000, ('bounded metadata only',name,len(raw))
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        p=OUT/'infra/materialized.json';records=read(p) if p.exists() else []
        records.append(dict(path=name,commit=commit,SHA256=sha(path),bytes=len(raw),Optimize=0))
        write(p,records)
    return path

def legacy_import(name):
    for attempt in range(50):
        try:return importlib.import_module(name)
        except FileNotFoundError as error:
            relative=Path(error.filename).resolve().relative_to(ROOT.resolve())
            assert relative.parts[0]=='results' and re.fullmatch(r'unified_exact_round\d+',relative.parts[1])
            assert int(relative.parts[1].removeprefix('unified_exact_round'))<164
            assert relative.suffix in ('.json','.md','.csv'),relative
            materialize(relative.as_posix())
    raise RuntimeError('bounded metadata import exhausted')

def protect():
    TEMP.mkdir(parents=True,exist_ok=True);path=TEMP/'protected_original.json'
    assert not path.exists();records=[]
    for tree in [Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round163']:
        names=git('diff','--name-only','HEAD','-z',cwd=tree).decode().split('\0')
        records.append(dict(tree=str(tree),HEAD=git('rev-parse','HEAD',cwd=tree).decode().strip(),
            dirty={n:sha(tree/n) if (tree/n).is_file() else None for n in names if n}))
    write(path,records)
    write(OUT/'infra/protected_workspace_summary.json',dict(UTC=utc(),
        trees=[dict(tree=r['tree'],HEAD=r['HEAD'],dirty_tracked_files=len(r['dirty'])) for r in records],
        local_hash_inventory=str(path),user_content_published=False))

def check_protected():
    records=read(TEMP/'protected_original.json')
    for r in records:
        assert git('rev-parse','HEAD',cwd=r['tree']).decode().strip()==r['HEAD']
        for name,digest in r['dirty'].items():
            p=Path(r['tree'])/name
            assert (sha(p) if p.is_file() else None)==digest,('protected user file changed',name)
    return dict(PASS=True,trees=len(records),dirty_files=sum(len(r['dirty']) for r in records))

if __name__=='__main__':
    if len(sys.argv)==1:print(json.dumps(budget(),indent=2))
    elif sys.argv[1]=='protect':protect()
    else:sys.exit(metered(sys.argv[1],sys.argv[2],sys.argv[5:],float(sys.argv[3]),float(sys.argv[4])))
