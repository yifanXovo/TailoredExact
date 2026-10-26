"""Bounded serial Round70 runs with uniform inherited measurement affinity."""
import argparse, json, os, subprocess, time
from pathlib import Path
import round61_research as runner
import round70_affinity as affinity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round70/revision2';BUILD=ROOT/'build/round70_v2';RAW=OUT/'local_raw'
runner.ROOT=ROOT;runner.OUT=OUT;runner.RAW=RAW;runner.BUILD=BUILD
runner.LEDGER=OUT/'processes.jsonl'
sha=runner.sha;write=runner.write

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def panel():return {p['id']:p for p in read(OUT/'protocol.json')['panel']}

def freeze():
    assert not (OUT/'protocol.json').exists(),'Immutable protocol already exists'
    old={p['id']:p for p in read(ROOT/'results/unified_exact_round68/protocol.json')['panel']}
    old.update({p['id']:p for p in read(ROOT/'results/unified_exact_round69/protocol.json')['panel']})
    ids=['E7','S12','N12','D3','C2','D4','D6','D7','micro','micro-zero']
    selected=[]
    for identity in ids:
        p=dict(old[identity]);p['stage']='correctness' if identity.startswith('micro') else 'development'
        p['role']='Round70 exposed development/protection; see plan.md' if p['stage']=='development' else 'Original tiny correctness only; micro-zero denotes zero handling'
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
        selected.append(p)
    q=read(OUT/'qualification.json')
    assert q['final_ctest_passed_tests']==47 and q['final_binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    assert q['tests_sha256']==sha(BUILD/'tests.log')
    for name,value in q['qualified_source'].items():assert sha(ROOT/name)==value,name
    bind=read(OUT/'affinity_qualification.json')
    assert bind['child_self_readback']['process_mask']==affinity.MASK==4
    caps=dict(E7=120,S12=120,N12=120,D3=300,C2=300,D4=300,D6=600,D7=600,micro=30,**{'micro-zero':30})
    allowed={i:['P-GRB','VD-S','DS']+(['K1-R'] if i in ['D3','D6','D7'] else []) for i in ids}
    write(OUT/'protocol.json',dict(base='b87850c474c8cb9ac45b65f881ebc629bb137f24',panel=selected,
        plan_sha256=sha(OUT/'plan.md'),mathematics_sha256=sha(OUT/'mathematics.md'),
        maximum_performance=27,maximum_micro=6,maximum_reference_exports=10,worst_case_seconds=9060,
        caps=caps,allowed_arms=allowed,arms=['P-GRB','K1-R','VD-S','DS'],
        solver=dict(version='13.0.2',Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0),
        measurement=dict(logical_processor=2,affinity_mask=4,applies_to='all complete arms and no-opt exports'),
        candidate='24 finite decoded descents before unchanged VD-S proof; all internal resource policies off',
        confirmation_opened=False,validation_scope='All roles exposed development/protection; new core condition requires fresh controls'))
    write(OUT/'build_v1.json',dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        source=q['qualified_source'],binary=sha(BUILD/'ExactEBRP.exe'),reference_binary=sha(BUILD/'Round65ReferenceBuild.exe'),
        tests=sha(BUILD/'tests.log'),qualification=sha(OUT/'qualification.json'),driver=sha(Path(__file__)),
        shared_command_helper=sha(Path(runner.__file__)),affinity_helper=sha(Path(affinity.__file__)),
        affinity_qualification=sha(OUT/'affinity_qualification.json')))

def assert_frozen():
    frozen=read(OUT/'build_v1.json');protocol=read(OUT/'protocol.json')
    assert sha(BUILD/'ExactEBRP.exe')==frozen['binary'] and sha(Path(__file__))==frozen['driver']
    assert sha(Path(runner.__file__))==frozen['shared_command_helper']
    assert sha(Path(affinity.__file__))==frozen['affinity_helper']
    assert sha(OUT/'plan.md')==protocol['plan_sha256']
    assert sha(OUT/'mathematics.md')==protocol['mathematics_sha256']
    for name,value in frozen['source'].items():assert sha(ROOT/name)==value,name
    return frozen,protocol

def execute(cmd,dest,identity,cap,kind='performance',solver_calls=1):
    if dest.exists():raise RuntimeError('Refusing to overwrite '+str(dest))
    assert not (ROOT/'results/unified_exact_round69/active_run.lock').exists()
    entries=runner.entries();charged=kind!='build-only';count=sum(e['charged'] for e in entries)
    protocol=read(OUT/'protocol.json')
    key={'performance':'maximum_performance','native-micro':'maximum_micro','build-only':'maximum_reference_exports'}[kind]
    assert sum(e['kind']==kind for e in entries)<protocol[key],'Declared resource plan exhausted'
    lock=OUT/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        dest.mkdir(parents=True)
        record=dict(identity,command=list(map(str,cmd)),executable_sha256=sha(cmd[0]),cap_seconds=cap,
            kind=kind,charged=charged,charged_number=count+1 if charged else None,
            solver_calls_planned=solver_calls,started_unix=time.time(),destination=str(dest.relative_to(ROOT)),
            declared_affinity_mask=affinity.MASK)
        write(dest/'launch.json',record)
        with runner.LEDGER.open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
        env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
        started=time.monotonic();process=None;watchdog=False;error=None;code=1
        try:
            with affinity.inherited_core() as binding:
                with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
                    process=subprocess.Popen(list(map(str,cmd)),cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                    observed=affinity.read_masks(process.pid)
                    assert observed['process_mask']==affinity.MASK,'Owned child did not inherit declared affinity'
                    write(dest/'affinity.json',dict(binding=binding,child_pid=process.pid,child_readback=observed,
                        scope='Measurement condition only; no unrelated process was changed'))
                    try:code=process.wait(timeout=cap+10)
                    except subprocess.TimeoutExpired:
                        process.kill();process.wait();code=process.returncode;watchdog=True
        except Exception as exc:
            error=str(exc);code=1
            if process is not None and process.poll() is None:process.kill();process.wait()
        wall=time.monotonic()-started
        write(dest/'completion.json',dict(returncode=code,wall_seconds=wall,watchdog=watchdog,
            within_budget=wall<=cap,solver_calls_planned=solver_calls,supervisor_error=error,
            restored_launcher=affinity.read_masks()))
        print(identity,'code',code,'wall',round(wall,3),'charged',count+int(charged),flush=True)
        if code or watchdog or wall>cap:raise RuntimeError('Failed charged/qualification run '+str(dest)+': '+str(error))
    finally:lock.unlink()

def refbuild(ids):
    frozen,_=assert_frozen();assert sha(BUILD/'Round65ReferenceBuild.exe')==frozen['reference_binary']
    fingerprints=read(OUT/'fingerprints.json') if (OUT/'fingerprints.json').exists() else {}
    previous=read(ROOT/'results/unified_exact_round68/fingerprints.json')
    previous.update(read(ROOT/'results/unified_exact_round69/fingerprints.json'))
    for identity in ids:
        p=panel()[identity];dest=RAW/'reference_build'/identity
        execute([BUILD/'Round65ReferenceBuild.exe',p['instance_path'],p['T_seconds'],p['pickup_seconds'],
            p['drop_seconds'],p['lambda'],dest],dest,dict(id=identity,arm='reference-build',stage='reference-build'),30,'build-only',0)
        data=read(dest/'build.json');assert data['optimizer_calls']==0
        if identity in previous:assert data['fingerprint']==previous[identity]['fingerprint']
        fingerprints[identity]=data;write(OUT/'fingerprints.json',fingerprints)

def run(ids,arms,cap,stage):
    frozen,protocol=assert_frozen()
    assert len(ids)==len(set(ids)) and len(arms)==len(set(arms))
    for identity in ids:
        p=panel()[identity];assert sha(ROOT/p['instance_path'])==p['input_sha256']
        assert cap==protocol['caps'][identity] and stage==p['stage']
        for arm in arms:
            assert arm in protocol['allowed_arms'][identity]
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
                preset={'K1-R':'research-round65-k1-h','VD-S':'research-round68-vdp-start','DS':'research-round70-vds-descent'}[arm]
                cmd=runner.full_command(p,dest,preset,'off',cap)+['--round65-witness-audit','true',
                    '--ub-event-log',dest/'ub_events.csv','--round65-hga-zero-stop','true',
                    '--round60-hga-candidate-log',dest/'hga_events.csv']
            execute(cmd,dest,dict(id=identity,arm=arm,stage=stage,scope='original_problem',
                build=sha(OUT/'build_v1.json'),input_sha256=p['input_sha256']),cap,
                'native-micro' if identity.startswith('micro') else 'performance','all actual native calls in ledger')
            result=read(dest/'result.json')
            if any(token in result.get('status','') for token in ['failed','invalid','error']):raise RuntimeError(result['status'])
            if arm!='P-GRB':
                assert result['external_gini_tree_root_coverage_valid'] and result['external_gini_tree_parent_child_coverage_valid'],result['status']
            if arm=='DS':assert result['hga_stop_mode']=='decoded-descent' and result['hga_total_generations']==0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','refbuild','run'])
    parser.add_argument('--ids',nargs='+',default=[]);parser.add_argument('--arms',nargs='+',default=['P-GRB','VD-S','DS'])
    parser.add_argument('--cap',type=int,default=300);parser.add_argument('--stage',default='development')
    args=parser.parse_args()
    if args.action=='freeze':freeze()
    elif args.action=='refbuild':refbuild(args.ids)
    else:run(args.ids,args.arms,args.cap,args.stage)
