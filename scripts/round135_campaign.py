"""Preregistered 10+22 complete S2/AP positions; the second stage is conditional."""
from round135_common import *
import copy, csv, shutil
import round133_campaign as inherited
from round122_prepare import command as original_command, COMMON
from round121_campaign import finish_producer
from round134_campaign import frozen_inputs

def prepare():
    assert not (OUT/'experiment_plan.json').exists()
    inputs=frozen_inputs()
    path='reference/hard_stress/V20_M3/high_imbalance_seed3201.txt'
    assert sha(ROOT/path)=='ce60fd4e74ad23174be2d4a08ca6e52c0043cee22f3c9b17153b9e8bbcfdbe42'
    import round108_reader as core
    p=dict(id='R55-D13',layer='protection',source='synthetic R55 original',V=20,M=3,
        inventory='high imbalance',geometry='three clusters',replicate=1,Q_vector=[30]*3,T_seconds=3600,
        cap_seconds=600,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},
        input_path=path,instance_path=path,input_sha256=sha(ROOT/path),gurobi_seed=0,
        selection_id='original_R55_D13',panel_kind='known historical protection input')
    a=core.evidence.instance(ROOT,p)
    p.update(total_initial=sum(a['b'][1:]),total_target=sum(a['D'][1:]),total_capacity=sum(a['c'][1:]),
        Omega=sum(a['w'][1:]),sum_weights=sum(a['w'][1:]),rho=.15*sum(a['w'][1:]))
    ref=OUT/'qualification/references/R55-D13'
    assert metered('D13_cold_reference','C',[BUILD/'Round135Export.exe',ROOT/path,3600,0,1,1,'p',ref],reservation=60,timeout=60)==0
    p['reference']=read(ref/'build.json')
    inputs['R55-D13']=dict(round=55,manifest='reference/hard_stress/V20_M3/manifest.csv',
        manifest_SHA=sha(ROOT/'reference/hard_stress/V20_M3/manifest.csv'),panel=p,
        launch=dict(destination=str(ref/'raw'/'unused')),reference_directory=str(ref))
    stages=dict(C=[],D=[])
    def pair(stage,role,cap,seed,repeat,order):
        for method in order:
            stages[stage].append(dict(stage=stage,position=len(stages[stage])+1,role=role,seed=seed,repeat=repeat,
                method=method,cap_seconds=cap,lambda_value=.15,input_binding=inputs[role]))
    # Micro repetitions are first so the existing reader and Start path are
    # exercised before long arms. The orders are fixed before any native result.
    pair('C','SM-B10-B',90,0,1,['S2','AP'])
    pair('C','SM-B10-B',90,0,2,['AP','S2'])
    pair('C','K-20-S',1200,0,1,['S2','AP'])
    pair('C','K-35-U',2400,0,1,['AP','S2'])
    pair('C','R55-D13',600,0,1,['S2','AP'])
    pair('D','K-20-S',1200,1,1,['AP','S2'])
    pair('D','K-35-U',2400,1,1,['S2','AP'])
    pair('D','R55-D13',600,1,1,['AP','S2'])
    for role,cap,first in [('K-15-S',600,['S2','AP']),('UC-B20-B',600,['AP','S2']),('X-35-B',300,['S2','AP'])]:
        pair('D',role,cap,0,1,first);pair('D',role,cap,1,1,list(reversed(first)))
    pair('D','SM-B10-B',90,1,1,['AP','S2'])
    pair('D','SM-B10-B',90,1,2,['S2','AP'])
    assert len(stages['C'])==10 and sum(r['cap_seconds'] for r in stages['C'])==8760
    assert len(stages['D'])==22 and sum(r['cap_seconds'] for r in stages['D'])==14760
    plan=dict(UTC=utc(),**stages,stage_names=dict(C='Stage 1',D='Conditional stage 2'),serial=True,
        threads=1,mip_threads=1,affinity_mask=4,all_inputs_known_not_holdout=True,
        method_order_fixed_before_results=True,no_cross_arm_fleet_bound_Start_or_tree=True,
        full_production_cap_includes_own_H_model_proof_checks_cleanup_output=True,
        postproduction_audit_separate_no_backfill=True,only_difference='--round135-aggregate-penalty',
        stage1_arms=10,stage2_arms=22,stage1_cap_sum=8760,stage2_cap_sum=14760,total_cap_sum=23520,
        enter_stage2='Credible full-method certificate/time/endpoint benefit without clear persistent serious regression; root/Work/node improvement alone is insufficient',
        stop='No full-method benefit or clear serious regression; preserve all entered results and explain once',
        material_time_rule='max(10s,0.10*faster certified time); micro absolute repeats',
        advance_existing_seed1_allowed_only_with_written_rationale=True)
    write(OUT/'experiment_plan.json',plan)
    print('10+22 positions fixed before native results; Stage1 8760s; Stage2 14760s')

def freeze():
    build=read(OUT/'candidate_build.json')
    assert native_identity()['PE_SHA']==build['production']['PE_SHA']
    for name,digest in build['source_hashes'].items():assert sha(ROOT/name)==digest,name
    commit=git('rev-parse','HEAD').decode().strip()
    candidate=dict(schema='round135-frozen-production-v1',UTC=utc(),base=BASE,source_commit=commit,
        source_hashes=build['source_hashes'],production_PE=str(E3),production_PE_SHA=sha(E3),
        research_PE=str(E3),research_PE_SHA=sha(E3),DLL=str(DLL),DLL_SHA=DLL_SHA,
        research_alias_not_separate_algorithm=True,default_AP=False,only_variant='one weighted aggregate penalty row',
        build_SHA=sha(OUT/'candidate_build.json'),proof_policy='Unchanged R134 complete own H, native/outer/independent-zero rules')
    write(OUT/'candidate_manifest.json',candidate)
    for stage in ('C','D'):
        groups=[]
        for row in read(OUT/'experiment_plan.json')[stage]:
            position=row['position'];camp=OUT/f'campaign/{stage}_{position:02}';camp.mkdir(parents=True,exist_ok=False)
            p=copy.deepcopy(row['input_binding']['panel']);p.update(cap_seconds=row['cap_seconds'],gurobi_seed=row['seed'],
                **{'lambda':.15},panel_kind=f'Round135 {stage} known-role AP evaluation')
            p['instance_path']=p['input_path'];assert sha(ROOT/p['input_path'])==p['input_sha256']
            binding=row['input_binding'];ref=p['reference']
            source=Path(binding['reference_directory']) if 'reference_directory' in binding else Path(binding['launch']['destination']).parents[1]/'reference'/p['id']
            if not source.is_dir():source=WORK/f"worktrees/round{binding['round']}"/f"results/unified_exact_round{binding['round']}/qualification/references"/p['id']
            assert source.is_dir(),str(source)
            target=camp/'reference'/p['id'];target.mkdir(parents=True)
            for n in ('original.lp','build.json'):shutil.copyfile(source/n,target/n)
            assert sha(target/'original.lp')==ref['canonical_sha256'] and read(target/'build.json')==ref
            variant=row['method'];armid=f"{stage}{position:02}_{p['id']}_S{row['seed']}_R{row['repeat']}_{variant}"
            d=camp/'raw'/armid;cmd=original_command(p,'M-B',d);cmd[0]=str(E3)
            cmd+=['--round127-mode','ms2']
            if variant=='AP':cmd+=['--round135-aggregate-penalty']
            launch=dict(number=1,group_number=position,global_launch_number=position,id=p['id'],arm='M-B',
                method='S2',variant=variant,seed=row['seed'],repeat=row['repeat'],binary_layer='R135',version='candidate',
                panel=p,panel_kind=p['panel_kind'],destination=str(d),cap_seconds=row['cap_seconds'],
                hard_stop_seconds=row['cap_seconds']-2,command=cmd,configuration=dict(id='q0',MIPFocus=0,Cuts=-1),arm_id=armid)
            identity=dict(schema='round135-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=row['seed']),
                candidate_binary=str(E3),candidate_binary_sha256=sha(E3)),prereg_sha256=sha(OUT/'experiment_plan.json'),
                runner_sha256=sha(__file__),source_hashes=candidate['source_hashes'],candidate_binary_sha256=sha(E3),dll_sha256=DLL_SHA,
                measured_source_commit=commit,delivery_base_commit=BASE,launches=[launch],references={p['id']:ref},
                candidate_manifest_path=str(OUT/'candidate_manifest.json'),candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),
                stage=stage,no_cross_arm_information=True,source_input_binding={k:v for k,v in binding.items() if k not in ('launch','plan','panel')})
            write(camp/'identity.json',identity)
            groups.append(dict(position=position,arm_id=armid,group=f'campaign/{stage}_{position:02}',identity_SHA=sha(camp/'identity.json'),launch=launch))
        write(OUT/f'{stage}_matrix_frozen.json',dict(stage=stage,groups=groups,full_arm_count=len(groups),
            full_arm_cap_sum_seconds=sum(q['launch']['cap_seconds'] for q in groups),
            candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),experiment_plan_SHA=sha(OUT/'experiment_plan.json')))
    write(OUT/'execution_binding.json',dict(UTC=utc(),candidate_SHA=sha(OUT/'candidate_manifest.json'),
        helper_SHA={f'scripts/{n}':sha(ROOT/'scripts'/n) for n in ('round135_common.py','round135_campaign.py','round135_read.py','round135_ap_audit.py',
            'round133_campaign.py','round133_postverify_repair.py','round133_read.py','round115_campaign.py','round121_campaign.py')},
        C_matrix_SHA=sha(OUT/'C_matrix_frozen.json'),D_matrix_SHA=sha(OUT/'D_matrix_frozen.json')))
    print('Source/PE/DLL, input, Seed, repeat, order, cap and argv fixed for all 32 positions')

def admission():
    binding=read(OUT/'execution_binding.json')
    assert binding['candidate_SHA']==sha(OUT/'candidate_manifest.json');inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in binding['helper_SHA'].items():assert sha(ROOT/name)==digest,name
    return binding
def arm(stage,position,label):
    from round135_read import verify
    admission();group=read(OUT/f'{stage}_matrix_frozen.json')['groups'][int(position)-1]
    camp=OUT/group['group'];assert sha(camp/'identity.json')==group['identity_SHA']
    identity=read(camp/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    assert not (d/'verification_closeout.json').exists()
    if not d.exists():
        tick,creation=inherited.inherited.process_origin()
        inherited.supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'Never repeat unsealed native'
    started=time.perf_counter()
    try:value=verify(launch,identity)
    finally:write(OUT/'cost_segments'/label/'verification.json',dict(native_Optimize=0,seconds=time.perf_counter()-started,kind='postproduction audit'))
    write(OUT/'runtime_status.json',dict(UTC=utc(),stage=stage,position=position,arm_id=launch['arm_id'],
        variant=launch['variant'],certificate=value['arm']['certificate'],U=value['arm']['U'],L=value['arm']['L']))
    print(json.dumps(value['arm']),flush=True)
def run(stage,stop_after=None):
    admission()
    if stage=='D':assert read(OUT/'stage_decision.json')['enter_stage2'] is True
    for group in read(OUT/f'{stage}_matrix_frozen.json')['groups']:
        if stop_after is not None and group['position']>stop_after:break
        d=Path(group['launch']['destination'])
        if (d/'verification_closeout.json').exists():continue
        label=f'{stage}_{group["position"]:02}_01';assert not (OUT/'fees'/label).exists(),'Inspect pending/failure; never automatically repeat'
        assert metered(label,'D',[PYTHON,ROOT/'scripts/round135_campaign.py','arm',stage,group['position'],label],
            reservation=group['launch']['cap_seconds'],timeout=group['launch']['cap_seconds']+1800)==0
    print('Round135 serial stage returned '+stage,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','freeze','arm','run']);p.add_argument('stage',nargs='?',choices=['C','D']);p.add_argument('position',nargs='?',type=int);p.add_argument('label',nargs='?');p.add_argument('--stop-after',type=int);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='freeze':freeze()
    elif a.action=='arm':arm(a.stage,a.position,a.label)
    else:run(a.stage,a.stop_after)
