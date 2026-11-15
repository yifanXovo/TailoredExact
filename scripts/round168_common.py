"""Round168 provenance and I/O only. All optimization and family logic is C++."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,subprocess,sys,time,csv,io,zipfile
ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
OUT=ROOT/'results/unified_exact_round168'
BASE='0da006b442ff7e59a2a63c6700138316611b2ce2'
PYTHON=sys.executable
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def bind(p):
    p=Path(p)
    try:name=p.relative_to(ROOT).as_posix()
    except ValueError:name=str(p)
    return dict(path=name,bytes=p.stat().st_size,SHA256=sha(p))
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd).decode('utf-8').strip()
def protected():
    out=[]
    for root in [Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round167']:
        status=subprocess.check_output(['git','status','--porcelain=v1','-uno'],cwd=root).decode('utf-8').rstrip()
        out.append(dict(root=str(root),HEAD=git('rev-parse','HEAD',cwd=root),status=status,
            files=[dict(path=l[3:],SHA256=sha(root/l[3:])) for l in status.splitlines() if (root/l[3:]).is_file()]))
    return out
def initialize():
    assert not (OUT/'entry_state.json').exists()
    write(OUT/'entry_state.json',dict(UTC=utc(),work_start_UTC='2026-11-15T03:22:00+00:00',
        science_capacity_seconds=28800,diagnostic_outer_cap_seconds=5400,base=BASE,
        predecessor_PR=229,PR_base='codex/round167-conditional-state',branch='codex/round168-route-family',
        remote_main='b2b940c1e517a72e226ec60fc49ff19651737632',AGENTS_found=False,
        policy=bind(ROOT/'WORKSPACE_POLICY.md'),protected=protected(),goal=bind(OUT/'goal.md')))
    write(OUT/'source_manifest.json',dict(UTC=utc(),base=BASE,goal=bind(OUT/'goal.md'),
        historical_measured_source='e920b92e199e825ec89a2932f701861ff158e0d4',
        historical_measured_PE_SHA256='fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93',
        new_executable_scope='independent offline route families; no full controller run'))
    expected='b728f85512741779a8b066ae9c974ec60892360c3fe15fbf7b946fb0ab0a4878'
    paths=[Path('C:/Users/Administrator/Downloads/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'),
        Path('C:/Users/Administrator/Desktop/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'),
        WORK/'data/GI_TBC_vs_P_GRB_All_Tested_Instances.csv',
        ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv']
    found=[]
    for p in paths:
        if not p.is_file():continue
        raw=p.read_bytes();enc='utf-8-sig'
        try:rows=list(csv.reader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:enc='gb18030';rows=list(csv.reader(io.StringIO(raw.decode(enc))))
        found.append(dict(**bind(p),records=len(rows)-1,columns=len(rows[0]),encoding=enc,BOM=raw.startswith(b'\xef\xbb\xbf')))
    master=next((p for p in paths if p.is_file() and sha(p)==expected),None)
    if master:
        dest=WORK/'data/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'
        if dest.exists():assert sha(dest)==expected,'preserve differing user destination'
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(master.read_bytes())
    write(OUT/'CSV_reconciliation.json',dict(UTC=utc(),bounded_candidates=list(map(str,paths)),found=found,
        expected_records=112,expected_columns=28,expected_bytes=64951,expected_SHA256=expected,
        authoritative_112_available=master is not None,new_master_rows=0,new_complete_runs=0,
        statement='主表无新增运行数据',user_files_modified=False,
        inherited_reconciliation='results/unified_exact_round167/CSV_reconciliation.json',
        reliable_106_predecessor_found=False,missing_policy='No fabricated rows or substitution of protected 91/103-row copies'))
def recover():
    """Extract only prescribed result/audit members; serialize unchanged routes."""
    t=time.perf_counter();records=[];lines=[];sources=[]
    for n in [163,164]:
        carrier=WORK/f'worktrees/round{n}/results/unified_exact_round{n}/artifacts/new_evidence_01.zip'
        sources.append(bind(carrier));rows=read(ROOT/f'results/unified_exact_round{n}/reports/complete_arms.json')
        groups={g['position']:g for g in read(ROOT/f'results/unified_exact_round{n}/matrix_frozen.json')['groups']}
        with zipfile.ZipFile(carrier) as z:
            for a in rows:
                if a['id'] not in ['R163-C35-U','R163-B35-S','R163-X35-S'] or a['method'] not in ['B','P']:continue
                pos=a['position'];run=f'R{n}_{pos:03d}_{a["id"]}_S{a["seed"]}_{a["method"]}'
                prefix=f'results/unified_exact_round{n}/campaign/{pos:03d}/raw/{run}/'
                dest=OUT/'archive'/run;dest.mkdir(parents=True,exist_ok=False)
                bindings=[]
                for leaf in ['result.json','audit.json']:
                    raw=z.read(prefix+leaf);p=dest/leaf;p.write_bytes(raw)
                    bindings.append(dict(member=prefix+leaf,**bind(p)))
                d=read(dest/'result.json');audit=read(dest/'audit.json');assert sha(dest/'audit.json')==a['audit_SHA']
                assert audit['passed'] and audit['implementation_qualified'] and audit['evidence_complete']
                assert d['routes']==audit['physical']['routes']
                fleet=dest/'fleet.txt'
                with fleet.open('w',encoding='utf-8',newline='\n') as f:
                    f.write(str(len(d['routes']))+'\n')
                    for route in d['routes']:
                        ops={v['station']:v for v in route['operations']};nodes=route['nodes']
                        f.write(f'{route["vehicle"]} {len(nodes)} '+' '.join(map(str,nodes))+'\n')
                        f.write(' '.join(str(ops[i]['pickup']-ops[i]['drop']) for i in nodes[1:-1])+'\n')
                panel=groups[pos]['launch']['panel'];inp=ROOT/panel['input_path'];assert sha(inp)==a['input_SHA']
                T=d['route_time_limit_seconds'];lam=panel['lambda'];pick=d['pickup_time_seconds'];drop=d['drop_time_seconds']
                record=dict(run=run,input_id=a['id'],seed=a['seed'],method=a['method'],position=pos,round=n,
                    input=bind(inp),T=T,lambda_value=lam,pickup_seconds=pick,drop_seconds=drop,
                    expected_F=a['U'],members=bindings,carrier_SHA256=sources[-1]['SHA256'],fleet=bind(fleet),
                    historical_physical=audit['physical'],source_commit='e920b92e199e825ec89a2932f701861ff158e0d4')
                records.append(record)
                q=lambda s:json.dumps(str(s).replace('\\','/'))
                lines.append(f'{run} {a["id"]} {a["seed"]} {a["method"]} {q(inp)} {T:.17g} {lam:.17g} {pick:.17g} {drop:.17g} {q(fleet)} {a["U"]:.17g} {a["input_SHA"]} {sha(fleet)}')
    assert len(records)==18
    (OUT/'pool.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write(OUT/'archive_manifest.json',dict(UTC=utc(),records=records,carriers=sources,
        extraction_seconds=time.perf_counter()-t,ordinary_recovery_IO=True,no_new_Optimize=True,
        physical_qualification='pending C++ preflight',new_raw_only_policy='historical members referenced, not repackaged'))
    print('Recovered exact final result/audit/fleet for',len(records),'closed-pool records')
if __name__=='__main__':
    initialize();recover()
