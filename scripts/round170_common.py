"""R170 bounded orchestration and provenance. Importing never solves."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, io, json, os, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('E:/codes/ExactEBRP-work')
OUT=ROOT/'results/unified_exact_round170'
BASE='ff77c4e18985a55370d58a2b2731a51566a07eb8'
MEASURED='781c548b410a2749190e3f0c4b149c2ad885c054'
PE=WORK/'build-cache/round169/ExactEBRP.exe'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
PE_SHA='c6ddf0b62f1200d02a8c654fd3f278ced704130f1a8950fc1e6464b9cbb11e57'
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
SCIENCE_START=1794855003
SCIENCE_CAP=21600
BRANCH='codex/round170-reweight-confirmation'
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
def env():
    e=os.environ.copy();e['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+e['PATH'];return e
def protected():
    records=[]
    for root in [Path('E:/codes/ExactEBRP'),WORK/'worktrees/paper-current',WORK/'worktrees/round169']:
        status=subprocess.check_output(['git','status','--porcelain=v1','-uno'],cwd=root).decode('utf-8').rstrip()
        records.append(dict(root=str(root),HEAD=git('rev-parse','HEAD',cwd=root),status=status,
            files=[dict(path=l[3:],SHA256=sha(root/l[3:])) for l in status.splitlines() if (root/l[3:]).is_file()]))
    return records
def result(p):
    d=read(p);return d[0] if isinstance(d,list) else d['results'][0] if 'results' in d else d

def prepare():
    assert not (OUT/'entry_state.json').exists()
    OUT.mkdir(parents=True,exist_ok=True)
    goal=Path('C:/Users/Administrator/Downloads/TailoredExact_Round170_Complete_Goal.md')
    (OUT/'goal.md').write_bytes(goal.read_bytes())
    write(OUT/'entry_state.json',dict(UTC=utc(),science_start_epoch=SCIENCE_START,science_cap_seconds=SCIENCE_CAP,
        base=BASE,branch=BRANCH,PR_base='codex/round169-primal-reweight',main='b2b940c1e517a72e226ec60fc49ff19651737632',
        remote_PR231_open_draft=True,no_prior_round170_work=True,AGENTS_found=False,
        policy=bind(ROOT/'WORKSPACE_POLICY.md'),protected=protected(),goal=bind(OUT/'goal.md')))
    inherited=read(ROOT/'results/unified_exact_round169/candidate_manifest.json')
    assert sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    assert PE.stat().st_size==9884148
    checked=[]
    for name,digest in inherited['source_hashes'].items():
        assert sha(ROOT/name)==digest,name
        original=subprocess.check_output(['git','show',MEASURED+':'+name],cwd=ROOT)
        assert original.replace(b'\r\n',b'\n')==(ROOT/name).read_bytes().replace(b'\r\n',b'\n'),name
        checked.append(name)
    evidence={name:bind(WORK/'build-cache/round169'/name) for name in ['CMakeCache.txt','build.ninja','.ninja_log']}
    assert evidence['CMakeCache.txt']['SHA256']==inherited['build_cache']['SHA256']
    assert evidence['build.ninja']['SHA256']==inherited['build_ninja']['SHA256']
    write(OUT/'candidate_manifest.json',dict(UTC=utc(),source_commit=MEASURED,delivery_base=BASE,
        source_hashes=inherited['source_hashes'],source_bytes_checked=len(checked),PE=bind(PE),DLL=bind(DLL),
        compiler=bind('D:/msys64/ucrt64/bin/g++.exe'),compiler_version=inherited['compiler_version'],
        inherited_build_commands=inherited['build_commands'],flags=inherited['flags'],actual_build_evidence=evidence,
        four_arms_common_PE=True,rebuilt=False,inherited_manifest=bind(ROOT/'results/unified_exact_round169/candidate_manifest.json')))
    write(OUT/'source_tree_readback.json',dict(UTC=utc(),source_commit=MEASURED,source_files=len(checked),
        all_source_file_hashes_and_git_normalized_bytes_equal=True,actual_PE_DLL_and_build_bytes_verified=True,mismatches=[]))
    write(OUT/'environment_manifest.json',dict(UTC=utc(),Python=sys.version,PATH_prefix=env()['PATH'].split(';')[:2],
        PE=bind(PE),DLL=bind(DLL),Threads=1,MIPThreads=1,Native_Seeds=[1,2],H_seeds=[20260626,20260627,20260628],
        affinity_mask=4,platform=sys.platform,no_recompile=True))
    roles=[p for p in read(ROOT/'results/unified_exact_round163/input_manifest.json')['roles']
           if p['id'] in ['R163-C20-S','R163-C35-U','R163-B35-S','R163-X35-S']]
    for p in roles:
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        p.update(known_exposed_R170=True,cap_seconds=600)
        for tag,a in [('base',p['lambda']),('half',p['lambda']*.5),('double',p['lambda']*2)]:
            p[tag+'_lambda_decimal17']=format(a,'.17g');p[tag+'_lambda_binary64']=a.hex()
        ref=WORK/'worktrees/round164/results/unified_exact_round164/qualification/references'/p['id']/'build.json'
        p['compact_reference']=dict(metadata=read(ref),local_metadata=bind(ref),
            historical_delivery='de01e8fb27a954d031abac5fe99442d6c8d29d44',
            role='inherited original compact model qualification; no historical fleet reused')
    write(OUT/'inputs_frozen.json',dict(UTC=utc(),roles=roles,input_manifest=bind(ROOT/'results/unified_exact_round163/input_manifest.json'),
        H_seeds=[20260626,20260627,20260628],multipliers=[1,.5,2],complete_H_unchanged=True,
        tie_rule='strict original F improvement > 1e-10; base-first',no_H_only_screen=True,new_physical_inputs=0))
    expected='5e3303adfba0092c465b8dab3232e1ced7d0e85d8d21aa3e8398ed0d3e5880e3'
    roots=[Path('C:/Users/Administrator')/s for s in ['Downloads','Desktop','Documents']]+[WORK/'temp',WORK/'plans']
    matches=[]
    for root in roots:
        proc=subprocess.run(['rg','--files','--hidden','-g','*Round170*','-g','*round170*',
            '-g','GI_TBC_vs_P_GRB_All_Tested_Instances.csv','-g','!node_modules','-g','!.git',str(root)],
            capture_output=True,text=True)
        matches.extend(Path(s) for s in proc.stdout.splitlines() if s)
    copies=[]
    for p in matches+[WORK/'data/GI_TBC_vs_P_GRB_All_Tested_Instances.csv',
                       ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv']:
        if p.suffix.lower()!='.csv' or not p.is_file():continue
        raw=p.read_bytes()
        try:table=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))));encoding='utf-8-sig'
        except UnicodeDecodeError:table=list(csv.reader(io.StringIO(raw.decode('gb18030'))));encoding='gb18030'
        copies.append(dict(**bind(p),records=len(table)-1,columns=len(table[0]),encoding=encoding))
    found=next((x for x in copies if x['SHA256']==expected),None)
    if found:
        source=Path(found['path']);source=source if source.is_absolute() else ROOT/source
        target=WORK/'data/GI_TBC_vs_P_GRB_All_Tested_Instances.csv';target.parent.mkdir(parents=True,exist_ok=True)
        if target.is_file() and sha(target)!=expected:
            backup=target.with_name('GI_TBC_preserved_'+sha(target)[:16]+'.csv');backup.write_bytes(target.read_bytes())
        target.write_bytes(source.read_bytes())
    write(OUT/'CSV_reconciliation.json',dict(UTC=utc(),bounded_search_roots=[str(x) for x in roots],
        matching_paths=[str(x) for x in matches],found=copies,expected_records=118,expected_columns=28,
        expected_bytes=70240,expected_SHA256=expected,authoritative_118_available=found is not None,
        package_received=any(p.suffix.lower()=='.zip' for p in matches),protected_old_copies_unchanged=True,
        missing_policy='Deliver qualified mergeable increment, never fabricate old rows or relabel historical copies'))
    print('ENTRY VERIFIED: common measured PE/DLL,',len(checked),'source files;',len(roles),'inputs; CSV118:',bool(found),flush=True)

if __name__=='__main__':prepare()
