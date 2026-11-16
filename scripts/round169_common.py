"""Round169 provenance/orchestration; scientific production and selection are C++."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, io, json, os, subprocess, sys, time, zipfile
ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
OUT=ROOT/'results/unified_exact_round169'
BASE='2301f9bf0a61d5fe74ee728704a820cb437d5cde'
PE=WORK/'build-cache/round169/ExactEBRP.exe'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
PYTHON=sys.executable
def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
    p=Path(p)
    try:name=p.relative_to(ROOT).as_posix()
    except ValueError:name=str(p)
    return dict(path=name,bytes=p.stat().st_size,SHA256=sha(p))
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd).decode('utf-8').strip()
def protected():
    records=[]
    for root in [Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round168']:
        status=subprocess.check_output(['git','status','--porcelain=v1','-uno'],cwd=root).decode('utf-8').rstrip()
        records.append(dict(root=str(root),HEAD=git('rev-parse','HEAD',cwd=root),status=status,
            files=[dict(path=l[3:],SHA256=sha(root/l[3:])) for l in status.splitlines() if (root/l[3:]).is_file()]))
    return records
def env():
    e=os.environ.copy();e['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+e['PATH'];return e
def initialize():
    assert not (OUT/'entry_state.json').exists()
    write(OUT/'entry_state.json',dict(UTC=utc(),science_start_epoch=1794788800,science_cap_seconds=28800,
        base=BASE,branch='codex/round169-primal-reweight',PR_base='codex/round168-route-family',
        main='b2b940c1e517a72e226ec60fc49ff19651737632',remote_PR230_open_draft=True,
        AGENTS_found=False,policy=bind(ROOT/'WORKSPACE_POLICY.md'),protected=protected(),goal=bind(OUT/'goal.md')))
    write(OUT/'source_manifest.json',dict(UTC=utc(),base=BASE,goal=bind(OUT/'goal.md'),
        historical_measured_source='e920b92e199e825ec89a2932f701861ff158e0d4',
        historical_measured_PE_SHA256='fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93'))
    expected='b728f85512741779a8b066ae9c974ec60892360c3fe15fbf7b946fb0ab0a4878'
    paths=[Path('C:/Users/Administrator/Downloads/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'),
        Path('C:/Users/Administrator/Desktop/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'),
        WORK/'data/GI_TBC_vs_P_GRB_All_Tested_Instances.csv',
        ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv']
    # One bounded attachment lookup: immediate Downloads names and matching folders only.
    attachment_names=[p.name for p in Path('C:/Users/Administrator/Downloads').iterdir() if '169' in p.name or 'GI_TBC' in p.name]
    found=[]
    for p in paths:
        if not p.is_file():continue
        raw=p.read_bytes()
        try:rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))));enc='utf-8-sig'
        except UnicodeDecodeError:rows=list(csv.reader(io.StringIO(raw.decode('gb18030'))));enc='gb18030'
        found.append(dict(**bind(p),records=len(rows)-1,columns=len(rows[0]),encoding=enc,BOM=raw.startswith(b'\xef\xbb\xbf')))
    write(OUT/'CSV_reconciliation.json',dict(UTC=utc(),bounded_candidates=[str(p) for p in paths],attachment_names=attachment_names,
        expected_records=112,expected_columns=28,expected_bytes=64951,expected_SHA256=expected,found=found,
        authoritative_112_available=any(x['SHA256']==expected for x in found),new_master_rows=0,new_P_pairs=0,
        protected_copies_unchanged=True,missing_policy='Disclose absence; never fabricate rows or install older copy as master'))
def freeze():
    assert not (OUT/'h_panel_frozen.json').exists()
    roles=read(ROOT/'results/unified_exact_round163/input_manifest.json')['roles']
    records=read(ROOT/'results/unified_exact_round166/review/data_physical_archive.json')['records']
    old=next(x for x in records if x['record_id']=='R137:B2:59')
    write(OUT/'provenance_record_schema.json',dict(record_keys=list(old),original=old['original'],archive=old.get('archive')))
    # The already recovered input is located by the source audit's exact path.
    inp_sha='c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2'
    candidates=[ROOT/old['source']['input_path']]+[ROOT/p for p in ['results/unified_exact_round137/inputs/R-X35-S-T2/first/instance.txt',
        'results/unified_exact_round166/review/inputs/'+inp_sha+'.txt']]
    candidates += list((ROOT/'results/unified_exact_round166/review').rglob('*.txt'))
    chosen=next((p for p in candidates if p.is_file() and sha(p)==inp_sha),None)
    if chosen is None:
        for p in (WORK/'worktrees/round166/results/unified_exact_round166/review').rglob('*.txt'):
            if sha(p)==inp_sha:chosen=p;break
    if chosen:
        dest=OUT/'inputs/R-X35-S-T2/instance.txt';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(chosen.read_bytes())
    else:raise RuntimeError('R166 recovered motivation input missing; inspect exact audit source map')
    roles.append(dict(id='R-X35-S-T2',input_path=dest.relative_to(ROOT).as_posix(),input_sha256=inp_sha,V=35,M=3,
        Q_vector=[20,25,30],T_seconds=6300,**{'lambda':0.0754049775127276},pickup_seconds=60,drop_seconds=60,
        inherited_physical_SHA256='1d5e47895bcda5db4281c80962f55ef694df568122adda1d8e2242615825cccc'))
    for i,p in enumerate(roles):
        assert sha(ROOT/p['input_path'])==p['input_sha256'];p['known_exposed']=True;p['can_trigger_E5']=i<6
        for tag,a in [('base',p['lambda']),('half',p['lambda']*.5),('double',p['lambda']*2)]:
            p[tag+'_lambda_decimal17']=format(a,'.17g');p[tag+'_lambda_binary64']=a.hex()
    write(OUT/'h_panel_frozen.json',dict(UTC=utc(),roles=roles,seeds=[20260626,20260627,20260628],
        path_order=['base','M_s1','M_s2','C_s1','C_s2'],multipliers=[1,1,1,.5,2],max_H_calls=35,
        shared_H_outer_cap_seconds=1200,qualification_process_outer_cap_seconds=300,
        skip_rules=['lambda=0','all station penalty weights=0','original qualified zero'],
        tie_rule='strict F improvement >1e-10; base then path order',
        gate='any of first six: all necessary H complete and original-physical-valid; C < min(B,M)-max(1e-6,0.001*max(B,1e-12))',
        no_P_Optimize_in_H_only=True,diagnostic_base_sharing_only=True))
    positions=[]
    for i,p in enumerate(roles[:6]):
        for arm in [['B','M','C'],['M','C','B'],['C','B','M']][i%3]:
            cap=300 if p['V']==20 else 600
            positions.append(dict(position=len(positions)+1,role=p['id'],arm=arm,Native_Seed=0,Threads=1,
                cap=cap,native_time_limit=cap-6,shutdown_margin=6,status='conditional_not_started'))
    write(OUT/'matrix_frozen.json',dict(UTC=utc(),status='conditional_E4_pending',positions=positions,
        nominal_process_cap_sum=8100,independent_paid_H=True,own_H_no_diagnostic_reuse=True,
        at_least_90min_science_reserve_before_launch=True))
if __name__=='__main__':
    if not (OUT/'entry_state.json').exists():initialize()
    freeze()
