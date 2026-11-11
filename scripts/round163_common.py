"""Round163 accounting and bounded metadata access; import never solves."""
from pathlib import Path
import datetime, hashlib, importlib, json, os, re, subprocess, sys, time
import round140_common as meter

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT/'results/unified_exact_round163'
TEMP = WORK/'temp/round163'
BASE = 'faa22ce4804f925081fd05322262b4f7261db51f'
MEASURED_CPP = 'e920b92e199e825ec89a2932f701861ff158e0d4'
PYTHON = Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
PE = WORK/'build-cache/round162/complete_v2/ExactEBRP.exe'
PE_SHA = 'fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93'
DLL, DLL_SHA = meter.DLL, meter.DLL_SHA
sha, read, write, utc, git = meter.sha, meter.read, meter.write, meter.utc, meter.git
TOTAL = 72000.

def configure():
    meter.OUT, meter.TEMP = OUT, TEMP
    meter.LIMITS = dict(qualification=TOTAL, panel=TOTAL, verification=TOTAL, repair=TOTAL)
    meter.TOTAL_LIMIT = TOTAL

def budget():
    configure()
    return meter.budget()

def metered(label, kind, args, seconds):
    configure()
    return meter.metered(label, kind, args, reservation=float(seconds), timeout=float(seconds), cwd=ROOT)

def materialize(name, commit=BASE):
    path=ROOT/name
    if not path.exists():
        raw=git('show',commit+':'+name)
        assert len(raw)<10000000, ('bounded metadata/input only',name,len(raw))
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(raw)
        p=OUT/'infra/materialized.json'
        records=read(p) if p.exists() else []
        records.append(dict(path=name,commit=commit,SHA256=sha(path),bytes=len(raw),Optimize=0))
        write(p,records)
    return path

def legacy_import(name):
    for attempt in range(50):
        try:return importlib.import_module(name)
        except FileNotFoundError as error:
            path=Path(error.filename).resolve()
            relative=path.relative_to(ROOT.resolve())
            assert re.fullmatch(r'unified_exact_round\d+',relative.parts[1]) and relative.parts[0]=='results'
            assert int(relative.parts[1].removeprefix('unified_exact_round'))<163
            assert path.suffix in ('.json','.md','.csv'), relative
            materialize(relative.as_posix())
    raise RuntimeError('bounded import metadata exhausted')

def protect():
    """Hash pre-existing dirty tracked files locally, without publishing user content."""
    TEMP.mkdir(parents=True,exist_ok=True)
    path=TEMP/'protected_original.json'
    assert not path.exists()
    records=[]
    for tree in [Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current']:
        names=git('diff','--name-only','HEAD','-z',cwd=tree).decode().split('\0')
        files={n:sha(tree/n) if (tree/n).is_file() else None for n in names if n}
        records.append(dict(tree=str(tree),HEAD=git('rev-parse','HEAD',cwd=tree).decode().strip(),dirty=files))
    write(path,records)
    write(OUT/'infra/protected_workspace_summary.json',dict(UTC=utc(),trees=[dict(tree=r['tree'],HEAD=r['HEAD'],dirty_tracked_files=len(r['dirty'])) for r in records],
        local_hash_inventory=str(path),user_content_published=False))
    print(json.dumps([dict(tree=r['tree'],dirty=len(r['dirty'])) for r in records]))

def check_protected():
    records=read(TEMP/'protected_original.json')
    for r in records:
        assert git('rev-parse','HEAD',cwd=r['tree']).decode().strip()==r['HEAD']
        for n,d in r['dirty'].items():
            p=Path(r['tree'])/n
            assert (sha(p) if p.is_file() else None)==d, ('protected user file changed',n)
    return dict(PASS=True,trees=len(records),dirty_files=sum(len(r['dirty']) for r in records))

if __name__=='__main__':
    if len(sys.argv)==1:print(json.dumps(budget(),indent=2))
    elif sys.argv[1]=='protect':protect()
    else:sys.exit(metered(sys.argv[1],sys.argv[2],sys.argv[4:],float(sys.argv[3])))
