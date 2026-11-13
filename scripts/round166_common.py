"""Round166 bookkeeping and offline helpers; never imports a solver."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round166'
WORK=Path('E:/codes/ExactEBRP-work')
BASE='239db6a80c944f1e7b5a55504ce5202ea35c2586'
PYTHON=sys.executable
def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
    p=Path(p)
    try:name=p.relative_to(ROOT).as_posix()
    except ValueError:name=str(p)
    return dict(path=name,bytes=p.stat().st_size,SHA256=sha(p))
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd).decode('utf-8',errors='replace').strip()
def init():
    if (OUT/'entry_state.json').exists():raise RuntimeError('Do not overwrite initial entry state')
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('C:/Users/Administrator/Downloads/TailoredExact_Round166_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(source.read_bytes())
    protected=[]
    for root in ['E:/codes/ExactEBRP','E:/codes/ExactEBRP-work/worktrees/paper-current','E:/codes/ExactEBRP-work/worktrees/round165']:
        status=git('status','--porcelain=v1','-uno',cwd=root)
        files=[]
        for line in status.splitlines():
            p=Path(root)/line[3:]
            if p.is_file():files.append(dict(path=line[3:],SHA256=sha(p)))
        protected.append(dict(root=root,HEAD=git('rev-parse','HEAD',cwd=root),status=status,dirty_files=files))
    write(OUT/'entry_state.json',dict(UTC=utc(),work_start_UTC='2026-11-13T21:10:00+00:00',
        conservative_start_includes_initial_read=True,science_capacity_seconds=57600,
        base=BASE,remote_main='b2b940c1e517a72e226ec60fc49ff19651737632',
        predecessor_PR=dict(number=227,state='open',draft=True,head=BASE),
        selected_branch='codex/round166-structure-and-paper',PR_base='codex/round165-current-manuscript',
        policy=bind(ROOT/'WORKSPACE_POLICY.md'),AGENTS_found=False,protected=protected,
        all_new_paths_under=str(WORK),goal=bind(OUT/'goal.md')))
    write(OUT/'source_manifest.json',dict(UTC=utc(),base=BASE,goal=bind(OUT/'goal.md'),
        historical_measured_CPP='e920b92e199e825ec89a2932f701861ff158e0d4',
        historical_PE_SHA='fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93',
        DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88',
        new_build='pending; never substitutes historical measured identity'))
    print('Entry state saved; protected trees remain read only.')
if __name__=='__main__':init()
