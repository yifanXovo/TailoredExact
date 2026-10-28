"""Preregister, freeze and serially execute the finite Round137 matrix."""
from round137_common import *
import collections, copy
import round133_campaign as inherited
from round122_prepare import command as original_command, COMMON
from round121_campaign import finish_producer

VARIANTS=['S2R','NO_AB','NO_CR','NO_CG']

def prepare():
    assert not (OUT/'experiment_plan.json').exists()
    inputs=read(OUT/'input_manifest.json');by={p['id']:p for p in inputs['roles']};arms=[]
    orders=[['P','PS','S2'],['PS','S2','P'],['S2','P','PS']]
    def add(stage,p,method,seed=0,tau=.08):
        panel=copy.deepcopy(p);panel['gurobi_seed']=seed
        arms.append(dict(position=len(arms)+1,stage=stage,role=p['id'],method=method,seed=seed,repeat=1,
            cap_seconds=p['cap_seconds'],AM_threshold=tau,panel=panel,results=None))
    for stage in ['B1','B2']:
        for j,p in enumerate(q for q in inputs['roles'] if q['module']==stage):
            for method in orders[j%3]:add(stage,p,method)
    for j,role in enumerate(['R-B20-S-T1','R-X35-S-T2']):
        for rho in [.5,2.]:
            p=copy.deepcopy(by[role]);p.update(id=role+f'-rho{rho:g}',physical_configuration_id=role,rho=rho,
                positive_objective_floor=rho*p['positive_objective_floor'],**{'lambda':rho/p['Omega']})
            for method in orders[j%3]:add('B3',p,method)
    for role in ['K-15-S','K-20-S','UC-B20-B','K-35-U']:
        for tau,method in [(.04,'AM004'),(.16,'AM016')]:add('C1',by[role],method,tau=tau)
    for j,role in enumerate(['K-15-S','UC-B20-B','K-20-S','K-35-U']):
        for method in VARIANTS[j%4:]+VARIANTS[:j%4]:add('C2',by[role],method)
    for j,role in enumerate(['K-15-S','UC-B20-B','R-B20-S-T1','K-35-U']):
        for method in orders[j%3]:add('D2-main',by[role],method,seed=1)
    for role in ['K-15-S','UC-B20-B']:
        for tau,method in [(.04,'AM004'),(.16,'AM016')]:add('D2-AM',by[role],method,seed=1,tau=tau)
        for method in VARIANTS:add('D2-mechanism',by[role],method,seed=1)
    assert len(arms)==120 and sum(a['cap_seconds'] for a in arms)==174600
    stages={s:dict(positions=sum(a['stage']==s for a in arms),caps=sum(a['cap_seconds'] for a in arms if a['stage']==s)) for s in dict.fromkeys(a['stage'] for a in arms)}
    write(OUT/'experiment_plan.json',dict(UTC=utc(),arms=arms,stages=stages,total_positions=120,total_caps_seconds=174600,
        reserve_seconds=41400,limit_seconds=216000,serial=True,threads=1,mip_threads=1,affinity_mask=4,
        default_AM=.08,default_AP=False,pair_only=True,H_seed=20260626,
        source_recipe_SHA=sha(OUT/'source_recipe.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        baseline_sharing='C1/C2 Seed0 defaults are the four corresponding B1/S2 rows; D2-AM/mechanism defaults are matching D2-main/S2; B3 rho1 uses B2',
        historical_reuse='R132/R134/R135 remain separately reported historical evidence; four same-build control baselines and absent matched full triplets require new runs, rather than relabel old PE/source timings',
        no_cross_arm_seed_or_weight_information=True,ordinary_adverse_or_open_never_replaced=True,
        no_new_mechanism_TC_AP_or_tuning_grid=True,postverification_separate_no_backfill=True))
    print(json.dumps(stages))

def references():
    plan=read(OUT/'experiment_plan.json');seen={}
    for row in plan['arms']:
        p=row['panel'];key=p['id']
        if key in seen:
            assert seen[key]['T_seconds']==p['T_seconds'] and seen[key]['lambda']==p['lambda'];continue
        seen[key]=p;dest=OUT/'qualification/references'/key
        assert not dest.exists()
        assert metered('reference_'+key,'engineering',[BUILD/'Round137Export.exe',ROOT/p['input_path'],
            p['T_seconds'],0,0,0,'p',dest,p['lambda'],'off'],timeout=60)==0
    write(OUT/'qualification/references.json',{name:read(OUT/'qualification/references'/name/'build.json') for name in seen})
    print(f'{len(seen)} compact references; Optimize=0')

def freeze():
    assert not (OUT/'matrix_frozen.json').exists()
    plan=read(OUT/'experiment_plan.json');build=read(OUT/'candidate_build.json')
    for name,digest in build['source_hashes'].items():assert sha(ROOT/name)==digest,name
    commit=git('rev-parse','HEAD').decode().strip();groups=[]
    candidate=dict(schema='round137-frozen-production-v1',UTC=utc(),source_commit=commit,base=BASE,
        source_hashes=build['source_hashes'],production_PE=str(E3),production_PE_SHA=sha(E3),
        research_PE=str(E3),research_PE_SHA=sha(E3),DLL=str(DLL),DLL_SHA=DLL_SHA,
        default_AM=.08,default_AP=False,config_SHA=sha(ROOT/'config/paper_s2.json'),
        scope='GI-TBC ms2 default-off; one declared research switch per variant',
        default_off_matrix_check_SHA=sha(OUT/'qualification/matrix_checks.json'))
    write(OUT/'candidate_manifest.json',candidate)
    for row in plan['arms']:
        n=row['position'];p=copy.deepcopy(row['panel']);method=row['method']
        p['reference']=read(OUT/'qualification/references'/p['id']/'build.json')
        p['round137_delete_ab']=method=='NO_AB';p['panel_kind']=f'Round137 {row["stage"]} preselected finite panel'
        camp=OUT/'campaign'/f'{n:03}';camp.mkdir(parents=True,exist_ok=False)
        target=camp/'reference'/p['id'];target.mkdir(parents=True)
        for name in ['original.lp','build.json']:
            (target/name).hardlink_to(OUT/'qualification/references'/p['id']/name)
        arm='P-GRB' if method=='P' else 'P-S' if method=='PS' else 'M-B'
        armid=f'R137_{n:03}_{p["id"]}_S{row["seed"]}_{method}';d=camp/'raw'/armid
        cmd=original_command(p,'P-GRB' if method=='PS' else arm,d);cmd[0]=str(E3)
        for flag in ['--round24-executable-sha256','--round24-manifest-executable-sha256']:
            if flag in cmd:cmd[cmd.index(flag)+1]=sha(E3)
        if method=='PS':cmd+=['--round112-ens-start-compact']
        else:cmd+=['--round127-mode','p' if method=='P' else 's2-root' if method=='S2R' else 'ms2']
        if method.startswith('NO_'):cmd+=['--round137-delete-'+method[3:].lower()]
        if method.startswith('AM'):cmd+=['--round137-am-threshold',str(row['AM_threshold'])]
        launch=dict(number=1,group_number=n,global_launch_number=n,id=p['id'],arm=arm,method=method,
            seed=row['seed'],repeat=1,binary_layer='R137',version='candidate',panel=p,panel_kind=p['panel_kind'],
            destination=str(d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,
            command=cmd,configuration=dict(id='q0',MIPFocus=0,Cuts=-1),arm_id=armid,
            stage=row['stage'],AM_threshold=row['AM_threshold'])
        identity=dict(schema='round137-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=row['seed']),
            candidate_binary=str(E3),candidate_binary_sha256=sha(E3)),prereg_sha256=sha(OUT/'experiment_plan.json'),
            runner_sha256=sha(__file__),source_hashes=candidate['source_hashes'],candidate_binary_sha256=sha(E3),
            dll_sha256=DLL_SHA,measured_source_commit=commit,delivery_base_commit=BASE,launches=[launch],
            references={p['id']:p['reference']},candidate_manifest_path=str(OUT/'candidate_manifest.json'),
            candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),stage=row['stage'],no_cross_arm_information=True)
        write(camp/'identity.json',identity)
        groups.append(dict(position=n,stage=row['stage'],group=camp.relative_to(OUT).as_posix(),
            arm_id=armid,identity_SHA=sha(camp/'identity.json'),launch=launch))
    import round137_read
    helpers=inherited.helper_bindings()
    write(OUT/'matrix_frozen.json',dict(UTC=utc(),groups=groups,full_arm_count=len(groups),
        full_arm_cap_sum_seconds=sum(g['launch']['cap_seconds'] for g in groups),
        experiment_plan_SHA=sha(OUT/'experiment_plan.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),helpers=helpers,serial=True,
        threads=1,mip_threads=1,affinity_mask=4,no_performance_results_before_freeze=True))
    print('120 positions frozen; expensive native admission remains pending independent review')

def admission():
    manifest=read(OUT/'matrix_frozen.json');gate=read(OUT/'review/matrix_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(OUT/'matrix_frozen.json')
    assert manifest['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    assert manifest['experiment_plan_SHA']==sha(OUT/'experiment_plan.json')
    assert manifest['input_manifest_SHA']==sha(OUT/'input_manifest.json')
    inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in manifest['helpers'].items():assert sha(ROOT/name)==digest,name
    return manifest

def arm(position,label):
    from round137_read import verify
    group=admission()['groups'][int(position)-1];camp=OUT/group['group']
    assert sha(camp/'identity.json')==group['identity_SHA']
    identity=read(camp/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    assert not (d/'verification_closeout.json').exists()
    if not d.exists():
        tick,creation=inherited.inherited.process_origin()
        inherited.supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'Inspect unsealed process; never repeat healthy solve'
    started=time.perf_counter()
    try:value=verify(launch,identity)
    finally:write(OUT/'cost_segments'/label/'verification.json',dict(native_Optimize=0,seconds=time.perf_counter()-started,kind='postproduction audit'))
    write(OUT/'runtime_status.json',dict(UTC=utc(),position=position,arm_id=launch['arm_id'],stage=launch['stage'],
        method=launch['method'],certificate=value['arm']['certificate'],U=value['arm']['U'],L=value['arm']['L']))
    print(json.dumps(value['arm']),flush=True)

def run(stop_after=120):
    for group in admission()['groups']:
        if group['position']>stop_after:break
        d=Path(group['launch']['destination'])
        if (d/'verification_closeout.json').exists():continue
        label=f'arm_{group["position"]:03}';assert not (OUT/'fees'/label).exists(),'Existing arm fee: inspect/resume explicitly, never retry Optimize'
        write(OUT/'active_position.json',dict(UTC=utc(),position=group['position'],stage=group['stage'],
            arm_id=group['arm_id'],fee_label=label))
        assert metered(label,'native',[PYTHON,ROOT/'scripts/round137_campaign.py','arm',group['position'],label],
            reservation=group['launch']['cap_seconds'],timeout=group['launch']['cap_seconds']+1800)==0
    write(OUT/'run_loop_return.json',dict(UTC=utc(),stop_after=stop_after,budget=budget()))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','references','freeze','arm','run']);p.add_argument('position',nargs='?',type=int);p.add_argument('label',nargs='?');p.add_argument('--stop-after',type=int,default=120);a=p.parse_args()
    if a.action=='arm':arm(a.position,a.label)
    elif a.action=='run':run(a.stop_after)
    else:globals()[a.action]()
