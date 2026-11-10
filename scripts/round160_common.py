"""Round160 isolated serial outer accounting; imports never launch solvers."""
from round153_common import *
from round140_common import git

OUT = ROOT/'results/unified_exact_round160'
TOTAL = 129600.
BASE = '51473276867e802ce729aae3d4a2563ea23a8fe8'
BUILD = WORK/'build-cache/round160'
PE = BUILD/'Round160Research.exe'

def configure():
    meter.OUT, meter.TEMP = OUT, WORK/'temp/round160'
    meter.LIMITS = dict(research=TOTAL, verification=TOTAL, native=TOTAL)
    meter.TOTAL_LIMIT = TOTAL

def budget():
    configure()
    return meter.budget()

def snapshot(label):
    files=list((ROOT/'scripts').glob('round160_*'))
    files+=list((ROOT/'src').glob('*160*'))+list((ROOT/'include').glob('*160*'))
    files+=[ROOT/'CMakeLists.txt',ROOT/'src/main.cpp']
    result={}
    for p in files:
        digest=sha(p);dest=OUT/'engineering/source_bytes'/f'{digest}.txt'
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes(p.read_bytes())
        result[p.relative_to(ROOT).as_posix()]=digest
    write(OUT/'engineering/source_snapshots'/f'{label}.json',dict(UTC=utc(),base=BASE,files=result))

def run(label,seconds,script,args=(),kind='research'):
    configure();snapshot(label)
    rc=meter.metered(label,kind,[PYTHON,'-B',ROOT/'scripts'/script,*args],reservation=float(seconds),timeout=float(seconds),cwd=ROOT)
    assert rc==0,(label,rc)

def metadata():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('C:/Users/Administrator/Downloads/TailoredExact_Round160_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(source.read_bytes())
    facts=[]
    for tree in (Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round156',WORK/'worktrees/round157',WORK/'worktrees/round158',WORK/'worktrees/round159'):
        status=git('status','--short','--untracked-files=no','-z',cwd=tree).decode()
        names=[v[3:] for v in status.split(chr(0)) if v]
        dirty={n:dict(SHA256=sha(tree/n),bytes=(tree/n).stat().st_size) for n in names if n and (tree/n).is_file()}
        untracked=git('ls-files','--others','--exclude-standard','-z',cwd=tree).decode().split(chr(0))
        facts.append(dict(tree=str(tree),head=git('rev-parse','HEAD',cwd=tree).decode().strip(),tracked_dirty=dirty,
                          untracked_count=sum(bool(n) for n in untracked),
                          untracked_inventory_SHA=hashlib.sha256(chr(0).join(untracked).encode()).hexdigest()))
    write(OUT/'infra/protected_initial.json',dict(UTC=utc(),trees=facts))
    assert not git('ls-files','*AGENTS.md',cwd=ROOT).strip()
    write(OUT/'infra/entry.json',dict(UTC=utc(),base=BASE,main=git('rev-parse','origin/main',cwd=ROOT).decode().strip(),
        origin=git('remote','get-url','origin',cwd=ROOT).decode().strip(),branch=git('branch','--show-current',cwd=ROOT).decode().strip(),
        worktree=str(ROOT),policy_SHA=sha(ROOT/'WORKSPACE_POLICY.md'),TOTAL=TOTAL,goal_SHA=sha(OUT/'goal.md'),
        old_producers_run=0,previous_R160_found=False,R159_Open_Draft=True,
        active_process_inventory='Initial CIM inventory found no Python/Exact/Gurobi/compiler processes',
        AGENTS='No applicable ancestor or tracked AGENTS.md found',volume_free_bytes=142014791680))

if __name__=='__main__':
    if len(sys.argv)==1:print(json.dumps(budget(),indent=2))
    elif sys.argv[1]=='metadata':metadata()
    else:run(sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4:])
