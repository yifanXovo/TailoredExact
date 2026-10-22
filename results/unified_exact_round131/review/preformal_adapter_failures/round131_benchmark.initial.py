"""R131 finite fixed-version benchmark adapter; imports never run Optimize.

The established R130 producer, verifier, and endpoint reader are rebound to
this output root. Only manifests, paths, group count, and accounting differ.
"""
from pathlib import Path
import collections, copy, datetime, hashlib, inspect, json, os, shutil
import subprocess, sys, time, types
from round130_common import sha, read, write, utc, source_bindings

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('E:/codes/ExactEBRP-work')
OUT = ROOT/'results/unified_exact_round131'
PRIOR = ROOT/'results/unified_exact_round130'
TEMP = WORK/'temp/round131'
EVIDENCE = WORK/'evidence/round131'
BASE = 'c302bae0ec128f0d4c651fb29d04cb41b491f721'
SOURCE = '7564a5415331b380e24d1ec06936dcfd56557e67'
PYTHON = Path('D:/msys64/ucrt64/bin/python.exe')
E3 = WORK/'build-cache/round130/ExactEBRP.exe'
PE_SHA = '2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
EXPORTER = WORK/'build-cache/round130/Round130ExportE3.exe'
TOTAL_LIMIT = 43200
QUAL_LIMIT = 1800

# Independently transcribed from the user contract, not from past outcomes.
SPECS = [
 ('A','SC-C15-S',126,15,2,'shortage','compact',[30,30],3600,600,'9849095e3496254fa9ea28715939b7380bd47fbaa6e998bff56c688e0e176101'),
 ('A','SC-B15-S',126,15,2,'shortage','regional',[20,40],5400,600,'b87de1a37e60cc2e7cbbf7885bac1155ac4c0b14356de7c5af92e402555474de'),
 ('A','SC-C15-B',126,15,2,'balanced','regional',[30,30],5400,600,'c0d5fc4eee62e1e454b8acde8b721640e410bf496593b14d4cbdb1ccf36f14ea'),
 ('A','SC-B20-S',126,20,2,'shortage','compact',[30,30],5400,1200,'70ebad164c3da58c52d0ad7fce651a6f4d90f54323a939d6c109a17eaffb8b3c'),
 ('A','SC-C20-S',126,20,2,'shortage','regional',[20,40],7200,1200,'5729b59070d5451750e8e0b2446b08381e5c001e96d3c3f247e57801f6dcde11'),
 ('A','SC-B20-U',126,20,2,'surplus','compact',[30,30],7200,1200,'c688de15fc31612b83885efe2e86e60f50ba57a5c5119f7e7801bf240a096bab'),
 ('B','SM-C8-S',127,8,1,'shortage','compact',[20],2400,90,'cd0c04a81c0096147d1c365eb4da02ad85397bbef2987d0b13be00628a6b3be0'),
 ('B','SM-B10-B',127,10,2,'balanced','regional',[15,25],3600,90,'32496a729183c1fa6c9837bb6a18455f8e60ea96fc8a8b803a2ddc5ae15aca8f'),
 ('C','PB-C35-U',122,35,3,'surplus','regional',[20,25,30],10800,2400,'67fa5712962980350c0b7be00abbcc4866af0fe376d0395b565ec082d36842e5'),
 ('C','PB-B35-B',122,35,3,'balanced','compact',[25,25,25],7200,2400,'41fdb57cad176be7746bb7c884f62da1643920ac2c49d75bd5235663936a5e3a')]
ORDERS = ['P S2','S2 P','S2 P','P S2','P S2','S2 P',
          'S2 P','P S2','P S2','S2 P','S2 P','P S2',
          'P S2','S2 P','S2 P','P S2','P S2','S2 P',
          'S2 P','P S2','P S2','S2 P','S2 P','P S2','P S2','S2 P']

def git(*args,cwd=ROOT):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*map(str,args)],cwd=cwd)

def environment():
    TEMP.mkdir(parents=True,exist_ok=True)
    e=dict(os.environ,TEMP=str(TEMP),TMP=str(TEMP),PYTHONDONTWRITEBYTECODE='1')
    e['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+e.get('PATH','')
    return e

def identity():
    seal=read(PRIOR/'E3_frozen.json')
    assert sha(E3)==seal['PE_SHA']==PE_SHA and sha(DLL)==DLL_SHA
    assert sha(EXPORTER)==seal['exporter_SHA'] and source_bindings()==seal['source_bindings']
    assert not git('diff',SOURCE,BASE,'--','src','include','CMakeLists.txt').strip()
    return dict(PE=str(E3),PE_SHA=PE_SHA,DLL=str(DLL),DLL_SHA=DLL_SHA,
        exporter=str(EXPORTER),exporter_SHA=seal['exporter_SHA'],source_commit=SOURCE,
        inherited_E3_seal='results/unified_exact_round130/E3_frozen.json',inherited_E3_seal_SHA=sha(PRIOR/'E3_frozen.json'),
        source_bindings=source_bindings(),production_compile=0,algorithm_change=False)

def budget():
    closed=[];unclosed=[]
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        if (p.parent/'receipt.json').exists():closed.append((read(p),read(p.parent/'receipt.json')))
        else:unclosed.append(p.parent.name)
    initial=read(OUT/'initialization.json') if (OUT/'initialization.json').exists() else {}
    paid=initial.get('preledger_outer_upper_seconds',0)+sum(r['outer_seconds'] for l,r in closed)
    return dict(paid_outer_seconds=paid,remaining_outer_seconds=TOTAL_LIMIT-paid,unclosed=unclosed,
        by_kind={k:sum(r['outer_seconds'] for l,r in closed if l['kind']==k) for k in sorted({l['kind'] for l,r in closed})},
        nested_H_LP_MIP_seconds_added=False)

def metered(label,kind,args,reservation=0,timeout=None):
    b=budget();assert not b['unclosed'],b
    assert b['remaining_outer_seconds']>=reservation,b
    if kind=='qualification':assert b['by_kind'].get(kind,0)<QUAL_LIMIT,b
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter();started=time.time()
    write(d/'launch.json',dict(UTC=utc(),kind=kind,command=list(map(str,args)),cwd=str(ROOT),budget_before=b,reservation=reservation))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        p=subprocess.Popen(list(map(str,args)),cwd=ROOT,env=environment(),stdout=so,stderr=se)
        write(d/'PID.json',dict(pid=p.pid,parent_pid=os.getpid(),launched_unix=started,command=list(map(str,args))))
        rc=p.wait(timeout=timeout)
    elapsed=time.perf_counter()-tick
    write(d/'receipt.json',dict(exit_code=rc,outer_seconds=elapsed,start_unix=started,end_unix=time.time(),exit_observed=True,nested_seconds_added=False))
    print(json.dumps(dict(label=label,exit_code=rc,outer_seconds=elapsed,budget=budget())),flush=True)
    if rc:print((d/'stderr.log').read_text(encoding='utf-8',errors='replace')[-6000:],flush=True)
    return rc

def bootstrap():
    assert not OUT.exists()
    assets=identity();OUT.mkdir(parents=True)
    shutil.copyfile(TEMP/'goal_source.txt',OUT/'goal.md')
    shutil.copyfile(TEMP/'user_dirty_baseline.json',OUT/'user_dirty_baseline.json')
    write(OUT/'initialization.json',dict(UTC=utc(),base=BASE,source=SOURCE,
        remote='https://github.com/yifanXovo/TailoredExact.git',PR192=dict(state='open',draft=True,merged=False,head=BASE),
        main_HEAD=git('rev-parse','HEAD',cwd=Path('E:/codes/ExactEBRP')).decode().strip(),
        applicable_AGENTS=[],initially_active_solvers=[],prior_R131_outputs=False,
        free_bytes=shutil.disk_usage(WORK).free,peak_increment_allowance_bytes=24*1024**3,
        peak_scope='new raw plus compressed carriers plus one recovery expansion and document intermediates; conservative allowance, not measured raw prediction',
        preledger_outer_upper_seconds=900,preledger_explanation='Conservative nonoverlapping setup/read/remote/sparse-initialization allowance; substantial child tasks are metered separately.',
        total_outer_limit=TOTAL_LIMIT,qualification_soft=900,qualification_limit=QUAL_LIMIT,assets=assets))
    roles=[]
    for layer,id,rnd,V,M,inventory,geometry,Q,T,cap,h in SPECS:
        prior=read(ROOT/f'results/unified_exact_round{rnd}/input_manifest.json')
        pool=prior['tiny_roles'] if rnd==127 else prior['roles']
        old=copy.deepcopy(next(p for p in pool if p['id']==id))
        assert [old[k] for k in ['V','M','inventory','geometry','Q_vector','T_seconds','cap_seconds']]==[V,M,inventory,geometry,Q,T,cap]
        assert sha(ROOT/old['input_path'])==old['input_sha256']==h
        p={k:v for k,v in old.items() if k not in ['method_order','group_number','gurobi_seed']}
        original=p['input_path'];dest=OUT/'inputs'/f'{id}.txt';dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(ROOT/original,dest);assert sha(dest)==h
        p.update(layer=layer,source_round=rnd,source_input_path=original,input_path=dest.relative_to(ROOT).as_posix(),
            instance_path=dest.relative_to(ROOT).as_posix(),panel_kind=dict(A='known_SC_final_version_main_benchmark',B='known_tiny_final_version_overhead',C='known_V35_final_version_scope')[layer],
            input_bytes=dest.stat().st_size,prospective_new_validation=False)
        for suffix in ['selection','landscape']:
            rel=old.get(suffix+'_path') or str(Path(original).with_name(id+'_'+suffix+'.json')).replace('\\','/')
            if (ROOT/rel).exists():
                to=OUT/'inputs'/Path(rel).name;shutil.copyfile(ROOT/rel,to)
                p[suffix+'_path']=to.relative_to(ROOT).as_posix()
                p[suffix+'_SHA']=sha(to)
        roles.append(p)
    groups=[]
    for p in roles:
        positions=[(s,1) for s in [0,1]] if p['layer']=='A' else [(s,r) for s in [0,1,2] for r in [1,2]] if p['layer']=='B' else [(0,1)]
        for seed,repeat in positions:
            number=len(groups)+1
            groups.append(dict(number=number,name=f'campaign/group{number:02d}',layer=p['layer'],role=p,seed=seed,repeat=repeat,methods=ORDERS[number-1].split(),pairs=[['S2','P']]))
    assert len(groups)==26 and sum(2*g['role']['cap_seconds'] for g in groups)==33360
    write(OUT/'input_manifest.json',dict(roles=roles,known_inputs=10,new_inputs=0,generated=0,
        scenario_semantics='service-station total inventory, excluding depot; not every station individually deficient or surplus',
        sources=['CITI','CABI'],not_factorial_not_IID_not_independent_unseen=True))
    write(OUT/'experiment_manifest.json',dict(round=131,base=BASE,source=SOURCE,groups=groups,formal_arms=52,matched_groups=26,distinct_inputs=10,
        layers=dict(A=dict(groups=12,arms=24,nominal_seconds=21600,distinct_inputs=6),B=dict(groups=12,arms=24,nominal_seconds=2160,distinct_inputs=2),C=dict(groups=2,arms=4,nominal_seconds=9600,distinct_inputs=2)),
        nominal_formal_seconds=33360,total_outer_limit=TOTAL_LIMIT,qualification_soft_seconds=900,qualification_limit_seconds=QUAL_LIMIT,
        management_reference_seconds=720,maximum_plan_seconds=35880,postprocess_recovery_allowance_seconds=7320,
        own_H_seed=20260626,Threads=1,MIPThreads=1,affinity_mask=4,shutdown_reserve=30,native_offset=6,hard_stop_offset=2,
        MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6,Presolve=-1,MIPFocus=0,Cuts=-1,
        selected_S2_fixed=True,repository_default_changed=False,production_compile=0,algorithm_changes=0,
        max_external_failure_whole_group_recoveries=1,normal_results_retry=False,extra_experiments_authorized=False,
        methods=dict(P='cold original compact --round127-mode p',S2='frozen full MS2 --round127-mode ms2'),
        materiality_AC='slower-faster >= max(10,0.10*faster); strict direction unchanged',tiny_warning='T_S2-T_P >= 10 seconds; P-only certification is a separate stronger risk',
        no_pooling_across_layers=True,certification_imputation=False,all_runs_independent=True))
    write(OUT/'E3_binding.json',assets)
    (OUT/'.gitignore').write_text('campaign/\nfees/\nqualification/references/\n',encoding='utf-8')
    (OUT/'RESUME.md').write_text('Round131 initialized. No formal native run started. Freeze complete argv and obtain independent admission before formal run. Inspect live PID/creation/argv/seal before any resume.\n',encoding='utf-8')
    print('R131_INITIALIZED 26 groups / 52 arms / 10 known inputs; Optimize=0')

def qualify():
    identity();records=[]
    # Existing native/model/Start qualification is inherited by byte identity.
    inherited=['E3_frozen.json','qualification/zero_qualification.json','qualification/native_qualification.json',
        'review/support_count_correction/addendum.json','preformal_source_provenance.json','paper_version_manifest.json']
    for n in inherited:assert (PRIOR/n).is_file(),n
    from round129_qualify import support_family
    # Explicitly exercise the corrected classifier on a cross-vehicle row.
    row=((('p_0_1',1.),('p_1_1',1.)),'<=',1.)
    assert support_family(row)=='other'
    for p in read(OUT/'input_manifest.json')['roles']:
        d=OUT/'qualification/references'/p['id']
        args=[EXPORTER,ROOT/p['input_path'],p['T_seconds'],0,0,0,'p',d]
        with (TEMP/('reference_'+p['id']+'.stdout.log')).open('xb') as so,(TEMP/('reference_'+p['id']+'.stderr.log')).open('xb') as se:
            tick=time.perf_counter();q=subprocess.run(list(map(str,args)),cwd=ROOT,env=environment(),stdout=so,stderr=se)
        assert q.returncode==0,p['id']
        b=read(d/'build.json');assert b['optimizer_calls']==0 and sha(d/'original.lp')==b['canonical_sha256']
        assert read(d/'native_metadata.json')['Optimize']==0 and read(d/'native_version.json')==dict(major=13,minor=0,technical=2)
        records.append(dict(id=p['id'],input_SHA=p['input_sha256'],command=list(map(str,args)),outer_seconds=time.perf_counter()-tick,build=b))
    write(OUT/'qualification/incremental_qualification.json',dict(UTC=utc(),assets=identity(),Optimize=0,H=0,compile=0,
        inherited={n:sha(PRIOR/n) for n in inherited},new_original_compact_references=records,
        corrected_single_vehicle_classifier='round129_qualify.support_family',cross_vehicle_unique_service_classification='other',
        final_seed2_reader='R127 actual Seed extension supports 0,1,2,3; R130 PS-only 0/1 branch is never used',
        no_new_general_qualification_platform=True,no_performance_pretest=True))
    print('INCREMENTAL_QUALIFICATION_PASS Optimize=0; 10 cold references; original E3 unchanged')

def campaign_api():
    import round130_campaign as old
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,BASE=BASE,SOURCE=SOURCE,E3=E3,EXPORTER=EXPORTER,
        metered=metered,environment=environment)
    prepare=types.FunctionType(old.prepare_group.__code__,ns,'round131_prepare_group')
    supervised=types.FunctionType(old.supervised.__code__,ns,'round131_supervised')
    reconstruct=types.FunctionType(old.reconstruct.__code__,ns,'round131_reconstruct')
    ns.update(supervised=supervised,reconstruct=reconstruct)
    source=inspect.getsource(old.execute).replace('Round130 active.','Round131 active.')
    exec(compile(source,__file__+'::inherited_execute','exec'),ns)
    return prepare,ns['execute'],reconstruct

def prepare():
    identity();q=read(OUT/'qualification/incremental_qualification.json');assert q['Optimize']==0
    make,_,_=campaign_api();plans=[]
    for g in read(OUT/'experiment_manifest.json')['groups']:
        make(g['name'],'E3',g['role'],g['methods'],g['seed'],g['repeat'])
        path=OUT/g['name']/'identity.json';i=read(path)
        # Source seal, rather than a paper metadata commit, identifies the PE.
        i['measured_source_commit']=SOURCE
        i['runner_sha256']=sha(__file__)
        for l in i['launches']:
            l.update(group_number=g['number'],global_launch_number=2*(g['number']-1)+l['number'],evidence_layer=g['layer'])
            cmd=l['command'];cap=g['role']['cap_seconds']
            assert cmd[0]==str(E3) and cmd.count('--round127-mode')==1
            assert cmd[cmd.index('--round127-mode')+1]==dict(P='p',S2='ms2')[l['method']]
            assert not any(x in cmd for x in ['--round128-mode','--round112-ens-start-compact','--round127-p-parameters','s2-root'])
            for flag,value in [('--time-limit',cap-6),('--process-wall-time-limit',cap),('--process-shutdown-margin',30),('--gurobi-seed',g['seed']),('--threads',1),('--mip-threads',1),('--gurobi-presolve',-1)]:
                assert cmd[cmd.index(flag)+1]==str(value),(flag,value)
        write(path,i);plans.append(i)
    adapters=sorted({Path(m.__file__).resolve().relative_to(ROOT).as_posix()
        for m in list(sys.modules.values()) if getattr(m,'__file__',None)
        and Path(m.__file__).resolve().parent==ROOT/'scripts' and str(m.__file__).endswith('.py')})
    write(OUT/'argv_freeze.json',dict(UTC=utc(),full_plans=plans,formal_arms=52,typed_comparisons=26,
        PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,actual_modes=dict(P='p',S2='ms2'),Optimize=0,each_own_H_and_cold_P=True))
    manifest=read(OUT/'experiment_manifest.json')
    write(OUT/'execution_binding.json',dict(UTC=utc(),protocol_SHA=sha(OUT/'experiment_manifest.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        E3_binding_SHA=sha(OUT/'E3_binding.json'),groups={g['name']:sha(OUT/g['name']/'identity.json') for g in manifest['groups']},
        adapters={n:sha(ROOT/n) for n in adapters},serial=True,formal_methods=['P','S2'],formal_arms=52,formal_pairs=26))
    version=read(PRIOR/'paper_version_manifest.json');version.update(version='Round131',formal_results_pending=True,
        evidence_layers=dict(version['evidence_layers'],R131_A='six known SC final-version main benchmark, both Seeds',R131_B='two known tiny overhead roles, three Seeds by two repeats',R131_C='two known V35 roles, Seed0 only, 2400-second scope boundary'),
        larger_roles='Final S2 scope measured only up to V35 in R131; no final-version V50/V60 validation')
    write(OUT/'paper_version_manifest.json',version)
    config=read(PRIOR/'paper_method_config.json');config.update(exact_reproduction_commands=[dict(id=l['id'],seed=l['seed'],repeat=l['repeat'],command=l['command']) for p in plans for l in p['launches'] if l['method']=='S2'])
    config['native']['gurobi_seed']='fixed per-group 0/1 in A, 0/1/2 in B, 0 in C; no redraw'
    write(OUT/'paper_method_config.json',config)
    print('ALL_52_ARGV_FROZEN; no formal producer started')

def remaining():
    return sum(2*g['role']['cap_seconds'] for g in read(OUT/'experiment_manifest.json')['groups'] if not (OUT/g['name']/'reconstructed.json').exists())

def run():
    identity();b=read(OUT/'execution_binding.json');gate=read(OUT/'review/performance_admission.json')
    assert gate['decision']=='ACCEPT' and gate['execution_binding_SHA']==sha(OUT/'execution_binding.json')
    assert sha(OUT/'experiment_manifest.json')==b['protocol_SHA'] and sha(OUT/'input_manifest.json')==b['input_manifest_SHA']
    for n,h in b['adapters'].items():assert sha(ROOT/n)==h,n
    for g in read(OUT/'experiment_manifest.json')['groups']:
        name=g['name'];assert sha(OUT/name/'identity.json')==b['groups'][name]
        if (OUT/name/'reconstructed.json').exists():continue
        label=f'formal_group{g["number"]:02d}_01'
        assert not (OUT/'fees'/label).exists(),'Inspect existing PID/creation/argv/seal; explicit recovery or read-only closeout required'
        print(json.dumps(dict(group=name,layer=g['layer'],id=g['role']['id'],seed=g['seed'],repeat=g['repeat'],methods=g['methods'],action='START',remaining_nominal=remaining(),budget=budget())),flush=True)
        rc=metered(label,'formal',[PYTHON,ROOT/'scripts/round131_benchmark.py','group',name],reservation=remaining()+2400)
        if rc:raise SystemExit(rc)
    (OUT/'RESUME.md').write_text('Round131 all 52 fixed formal arms sealed. No extra experiment authorized. Read-only final analysis, independent review, manuscript/PDF, Draft PR, one public recovery and owned cleanup remain.\n',encoding='utf-8')
    print('ALL_52_FORMAL_ARMS_SEALED',flush=True)

def status():
    groups=read(OUT/'experiment_manifest.json')['groups'];done=[]
    for g in groups:
        p=OUT/g['name']/'reconstructed.json'
        if p.exists():done.append(dict(group=g['number'],layer=g['layer'],id=g['role']['id'],seed=g['seed'],repeat=g['repeat'],arms=[{k:a.get(k) for k in ['method','certificate','T_cert','T_produce','U','L','formal_protocol_qualified']} for a in read(p)['arms']]))
    print(json.dumps(dict(UTC=utc(),groups_complete=len(done),arms_complete=2*len(done),last=done[-1:] if done else [],runtime=read(OUT/'runtime_status.json') if (OUT/'runtime_status.json').exists() else None,budget=budget()),ensure_ascii=False))

if __name__=='__main__':
    action=sys.argv[1]
    if action=='meter':sys.exit(metered(sys.argv[2],sys.argv[3],sys.argv[4:]))
    elif action=='group':campaign_api()[1](sys.argv[2])
    else:{'bootstrap':bootstrap,'qualify':qualify,'prepare':prepare,'run':run,'status':status}[action]()
