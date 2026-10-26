"""Frozen Round69 serial protocol; all deadlines terminate the complete run."""
import argparse, json, os, subprocess, time
from pathlib import Path
import round61_research as runner

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round69';BUILD=ROOT/'build/round69';RAW=OUT/'local_raw'
runner.ROOT=ROOT;runner.OUT=OUT;runner.RAW=RAW;runner.BUILD=BUILD
runner.LEDGER=OUT/'processes.jsonl'
sha=runner.sha;write=runner.write
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def panel():return {p['id']:p for p in read(OUT/'protocol.json')['panel']}

def freeze():
    if (OUT/'protocol.json').exists():raise RuntimeError('immutable protocol exists')
    old=read(ROOT/'results/unified_exact_round68/protocol.json')['panel']
    selected=[dict(next(p for p in old if p['id']==identity)) for identity in ['D3','D6']]
    selected.append(dict(next(p for p in read(ROOT/'results/unified_exact_round66/protocol.json')['panel'] if p['id']=='E7')))
    selected.append(dict(next(p for p in read(ROOT/'results/gf_budgeted_proof_round65/protocol.json')['panel'] if p['id']=='D7')))
    import csv
    manifest=ROOT/'reference/citibike443-regional-v1/manifests/T_scenario_manifest.csv'
    historical=list(csv.DictReader(manifest.open(encoding='utf-8')))
    for identity,scenario in [('S12','cb443_V12_regional_r1_surplus_M01_Q30_T10800'),('N12','cb443_V12_regional_r2_shortage_M01_Q30_T03600')]:
        p=dict(next(r for r in historical if r['scenario_id']==scenario))
        p.update(id=identity,input_sha256=p['instance_file_sha256'],**{'lambda':.15})
        selected.append(p)
    stages=dict(D3='repeat',D6='development-long',E7='historical-validation',S12='historical-validation',N12='historical-validation',D7='historical-validation-long')
    for p in selected:
        p['stage']=stages[p['id']]
        p['role']='Frozen VD-S validation; role definitions and historical exposure in plan.md'
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
    write(OUT/'protocol.json',dict(base='07c6e899d56230920c162c14bd8b7c07a960c79f',panel=selected,
        plan_sha256=sha(OUT/'plan.md'),mathematics_sha256=sha(OUT/'mathematics.md'),
        maximum_performance=16,maximum_micro=0,worst_case_seconds=15780,
        caps=dict(D3=300,E7=120,S12=120,N12=120,D6=3600,D7=1200),stages=stages,
        solver=dict(version='13.0.2',Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0),
        candidate='Unchanged frozen Round68 VD-S; full paid HGA/AM and verified existing-witness Start',
        arms=['P-GRB','K1-R','VD-S'],confirmation_opened=False,
        validation_scope='Public historical roles, not sealed; D3/D6 explicitly design data'))
    predecessor=read(ROOT/'results/unified_exact_round68/build_v1.json')
    assert sha(BUILD/'ExactEBRP.exe')==predecessor['binary']
    assert sha(BUILD/'Round65ReferenceBuild.exe')==sha(ROOT/'build/round68/Round65ReferenceBuild.exe')
    for name,value in predecessor['source'].items():assert sha(ROOT/name)==value,name
    files=[ROOT/'CMakeLists.txt']
    files += [p for d in ['src','include','tests'] for p in (ROOT/d).rglob('*') if p.suffix in ['.cpp','.hpp','.h','.c']]
    write(OUT/'build_v1.json',dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source={str(p.relative_to(ROOT)):sha(p) for p in files},binary=sha(BUILD/'ExactEBRP.exe'),
        reference_binary=sha(BUILD/'Round65ReferenceBuild.exe'),
        tests=sha(BUILD/'tests.log'),qualification=sha(OUT/'qualification.json'),driver=sha(Path(__file__)),shared_command_helper=sha(Path(runner.__file__))))

def execute(cmd,dest,identity,cap,kind='performance',solver_calls=1):
    # Same write-ahead / serial / full-process protocol as Round61, with this
    # stage's declared limits instead of inheriting its historical four micros.
    if dest.exists():raise RuntimeError('refusing to overwrite '+str(dest))
    charged=kind!='build-only';ledger=runner.entries();count=sum(e['charged'] for e in ledger)
    protocol=read(OUT/'protocol.json')
    if charged:
        key='maximum_micro' if kind=='native-micro' else 'maximum_performance'
        assert sum(e['kind']==kind for e in ledger)<protocol[key],'resource plan exhausted'
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        dest.mkdir(parents=True)
        record=dict(identity,command=list(map(str,cmd)),executable_sha256=sha(cmd[0]),cap_seconds=cap,
            kind=kind,charged=charged,charged_number=count+1 if charged else None,
            solver_calls_planned=solver_calls,started_unix=time.time(),destination=str(dest.relative_to(ROOT)))
        write(dest/'launch.json',record)
        with runner.LEDGER.open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
        env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
        start=time.monotonic()
        with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
            process=subprocess.Popen(list(map(str,cmd)),cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            watchdog=False
            try:code=process.wait(timeout=cap+10)
            except subprocess.TimeoutExpired:process.kill();process.wait();code=process.returncode;watchdog=True
        wall=time.monotonic()-start
        write(dest/'completion.json',dict(returncode=code,wall_seconds=wall,watchdog=watchdog,
            within_budget=wall<=cap,solver_calls_planned=solver_calls))
        print(identity,'code',code,'wall',round(wall,3),'charged',count+int(charged),flush=True)
        if code or watchdog:raise RuntimeError('failed charged run '+str(dest))
    finally:lock.unlink()

def refbuild(ids):
    assert sha(BUILD/'Round65ReferenceBuild.exe')==read(OUT/'build_v1.json')['reference_binary']
    fingerprints=read(OUT/'fingerprints.json') if (OUT/'fingerprints.json').exists() else {}
    previous=read(ROOT/'results/unified_exact_round66/fingerprints.json');previous.update(read(ROOT/'results/unified_exact_round68/fingerprints.json'))
    for identity in ids:
        p=panel()[identity];dest=RAW/'reference_build'/identity
        execute([BUILD/'Round65ReferenceBuild.exe',p['instance_path'],p['T_seconds'],p['pickup_seconds'],
            p['drop_seconds'],p['lambda'],dest],dest,dict(id=identity,arm='reference-build',stage='reference-build'),30,'build-only',0)
        b=read(dest/'build.json');assert b['optimizer_calls']==0
        if identity in previous:assert b['fingerprint']==previous[identity]['fingerprint']
        fingerprints[identity]=b;write(OUT/'fingerprints.json',fingerprints)

def run(ids,arms,cap,stage):
    protocol=read(OUT/'protocol.json');frozen=read(OUT/'build_v1.json')
    assert sha(BUILD/'ExactEBRP.exe')==frozen['binary'] and sha(Path(__file__))==frozen['driver']
    assert sha(Path(runner.__file__))==frozen['shared_command_helper']
    assert sha(OUT/'plan.md')==protocol['plan_sha256']
    assert sha(OUT/'mathematics.md')==protocol['mathematics_sha256']
    for name,value in frozen['source'].items():assert sha(ROOT/name)==value,name
    for identity in ids:
        p=panel()[identity];assert sha(ROOT/p['instance_path'])==p['input_sha256']
        assert cap==protocol['caps'][identity] and stage==protocol['stages'][identity]
        for arm in arms:
            assert arm in protocol['arms']
            assert identity!='D3' or arm=='VD-S','Only the declared candidate repeat is opened'
            dest=RAW/stage/identity/arm
            if arm=='P-GRB':
                cmd=[BUILD/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],'--T',p['T_seconds'],
                    '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--time-limit',cap-6,
                    '--process-wall-time-limit',cap,'--process-shutdown-margin',3,'--threads',1,'--mip-threads',1,
                    '--gurobi-seed',0,'--gurobi-presolve',-1,'--method','gurobi','--plain-baseline',
                    '--out',dest/'result.json','--log',dest/'native.log','--process-phase-ledger',dest/'phases.csv',
                    '--gurobi-model-export',dest/'compact.lp','--round24-expected-gurobi-model-fingerprint',
                    read(OUT/'fingerprints.json')[identity]['fingerprint'],'--round24-executable-sha256',frozen['binary'],
                    '--round24-manifest-executable-sha256',frozen['binary']]
            else:
                preset={'K1-R':'research-round65-k1-h','VD-P':'research-round67-vdp','VD-S':'research-round68-vdp-start'}[arm]
                cmd=runner.full_command(p,dest,preset,'off',cap)+['--round65-witness-audit','true',
                    '--ub-event-log',dest/'ub_events.csv','--round65-hga-zero-stop','true',
                    '--round60-hga-candidate-log',dest/'hga_events.csv']
            execute(cmd,dest,dict(id=identity,arm=arm,stage=stage,scope='original_problem',
                build=sha(OUT/'build_v1.json'),input_sha256=p['input_sha256']),cap,
                'native-micro' if identity.startswith('micro') else 'performance','all actual native calls in ledger')
            result=read(dest/'result.json')
            if 'failed' in result.get('status',''):raise RuntimeError(result['status'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','refbuild','run'])
    ap.add_argument('--ids',nargs='+',default=[]);ap.add_argument('--arms',nargs='+',default=['P-GRB','K1-R','VD-S'])
    ap.add_argument('--cap',type=int,default=300);ap.add_argument('--stage',default='development')
    a=ap.parse_args()
    if a.action=='freeze':freeze()
    elif a.action=='refbuild':refbuild(a.ids)
    else:run(a.ids,a.arms,a.cap,a.stage)
