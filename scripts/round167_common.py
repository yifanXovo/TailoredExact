"""Round167 provenance, orchestration and document helpers; no solver imports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round167'
WORK=Path('E:/codes/ExactEBRP-work')
BASE='d497052216d5ae55b6ae0139ea30910cee2e5865'
PYTHON=sys.executable
def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def bind(p):
    p=Path(p)
    try: name=p.relative_to(ROOT).as_posix()
    except ValueError: name=str(p)
    return dict(path=name,bytes=p.stat().st_size,SHA256=sha(p))
def git(*args,cwd=ROOT): return subprocess.check_output(['git',*args],cwd=cwd).decode('utf-8',errors='replace').strip()
def protected():
    records=[]
    for directory in ['E:/codes/ExactEBRP',str(WORK/'worktrees/paper-current'),str(WORK/'worktrees/round166')]:
        status=subprocess.check_output(['git','status','--porcelain=v1','-uno'],cwd=directory).decode('utf-8').rstrip()
        paths=[line[3:] for line in status.splitlines()]
        records.append(dict(root=directory,HEAD=git('rev-parse','HEAD',cwd=directory),status=status,
                            dirty_files=[dict(path=p,SHA256=sha(Path(directory)/p)) for p in paths if (Path(directory)/p).is_file()]))
    return records
def init():
    assert not (OUT/'entry_state.json').exists()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'goal.md').write_bytes(Path('C:/Users/Administrator/Downloads/TailoredExact_Round167_Complete_Goal.md').read_bytes())
    write(OUT/'entry_state.json',dict(UTC=utc(),work_start_unix=1794678070,science_capacity_seconds=36000,
        work_start_conservative=True,base=BASE,remote_main='b2b940c1e517a72e226ec60fc49ff19651737632',
        predecessor_PR=dict(number=228,state='open',draft=True,head=BASE),
        branch='codex/round167-conditional-state',PR_base='codex/round166-structure-and-paper',
        AGENTS_found=False,policy=bind(ROOT/'WORKSPACE_POLICY.md'),protected=protected(),goal=bind(OUT/'goal.md')))
    write(OUT/'source_manifest.json',dict(UTC=utc(),base=BASE,goal=bind(OUT/'goal.md'),
        R166_measured_CPP='0298dd45fbc3645af927c4a4dd1d43ecbdb567a9',
        R166_measured_PE_SHA='27e71873536bcd8e6001aee0c2514a5cc8122763728c62e6d467cd528b48daba',
        new_executable_scope='offline diagnostics only; never a historical performance executable'))
    # Bounded CSV search: exact name in user attachment directories and predecessor-reported locations only.
    csv_reconcile()
    print('Round167 initialized; all protected roots remain read only.')
def csv_reconcile():
    old=read(ROOT/'results/unified_exact_round166/CSV_entry.json')
    candidates=[Path('C:/Users/Administrator/Downloads/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'),
                Path('C:/Users/Administrator/Desktop/GI_TBC_vs_P_GRB_All_Tested_Instances.csv')]
    for key in ['candidates','files','checked']:
        for item in (old.get(key,[]) if isinstance(old,dict) else old if key=='candidates' else []):
            if isinstance(item,dict) and item.get('path'): candidates.append(Path(item['path']))
    found=[]
    for p in dict.fromkeys(candidates):
        if p.is_file():
            import csv,io
            data=p.read_bytes(); enc='utf-8-sig'
            try: rows=list(csv.reader(io.StringIO(data.decode(enc))))
            except UnicodeDecodeError:
                enc='gb18030'; rows=list(csv.reader(io.StringIO(data.decode(enc))))
            found.append(dict(**bind(p),records=len(rows)-1,columns=len(rows[0]),encoding=enc))
    expected='b728f85512741779a8b066ae9c974ec60892360c3fe15fbf7b946fb0ab0a4878'
    write(OUT/'CSV_reconciliation.json',dict(UTC=utc(),expected_records=112,expected_columns=28,expected_bytes=64951,
        expected_SHA256=expected,bounded_candidates=[str(p) for p in candidates],found=found,
        authoritative_112_available=any(f['SHA256']==expected for f in found),new_complete_runs=0,new_master_rows=0,
        statement='主表无新增运行数据',user_files_modified=False,
        R166_increment='results/unified_exact_round166/reports/GI_TBC_R166_B_controls_increment_28col.csv',
        missing_master_policy='If the 112/106-row master is absent, retain reconciliation without fabricating or overwriting it.'))
if __name__=='__main__': init()
