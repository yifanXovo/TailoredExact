"""Fixed 32+4 own complete runs, serial native calls and immutable sealed arms."""
from round134_common import *
import copy,shutil
import round133_campaign as inherited
from round122_prepare import command as original_command,COMMON
from round121_campaign import finish_producer

def frozen_inputs():
    sources={}
    for rnd,key in [(130,'full_plans'),(131,'full_plans'),(132,'plans')]:
        path=ROOT/f'results/unified_exact_round{rnd}'/('D_argv_freeze.json' if rnd==132 else 'argv_freeze.json')
        for group in read(path)[key]:
            for launch in group['launches']:
                sources[launch['id']]=dict(round=rnd,manifest=path.relative_to(ROOT).as_posix(),
                    manifest_SHA=sha(path),panel=launch['panel'],launch=launch,plan=group)
    return sources

def prepare():
    assert not (OUT/'experiment_plan.json').exists()
    inputs=frozen_inputs();rows=[]
    orders=[('SM-B10-B',90,[(0,1,['P','S2']),(0,2,['S2','P']),(1,1,['S2','P']),(1,2,['P','S2'])]),
        ('K-15-S',600,[(0,1,['P','S2','PS']),(1,1,['PS','S2','P'])]),
        ('UC-B20-B',1200,[(0,1,['P','S2']),(1,1,['S2','P'])]),
        ('K-35-U',2400,[(0,1,['P','S2']),(1,1,['S2','P'])]),
        ('X-35-U',2400,[(0,1,['P','S2']),(1,1,['S2','P'])]),
        ('X-35-B',2400,[(0,1,['P','PS','S2']),(1,1,['S2','PS','P'])])]
    for role,cap,repetitions in orders:
        for seed,repeat,methods in repetitions:
            for method in methods:
                rows.append(dict(stage='C',position=len(rows)+1,role=role,seed=seed,repeat=repeat,
                    method=method,cap_seconds=cap,lambda_value=.15,input_binding=inputs[role]))
    assert len(rows)==32 and sum(r['cap_seconds'] for r in rows)==42720
    extra=[]
    for role,cap in [('K-15-S',600),('UC-B20-B',1200)]:
        for lam in (.075,.30):
            extra.append(dict(stage='D',position=len(extra)+1,role=role,seed=0,repeat=1,
                method='S2',cap_seconds=cap,lambda_value=lam,input_binding=inputs[role]))
    plan=dict(UTC=utc(),C=rows,D=extra,serial=True,threads=1,mip_threads=1,affinity_mask=4,
        all_inputs_known_not_holdout=True,method_order_fixed_before_results=True,
        no_cross_arm_seed_or_lambda_fleet_bound_tree_or_start=True,
        full_production_cap_includes_own_H_model_proof_checks_cleanup_output=True,
        postproduction_audit_separate_no_backfill=True,TC_not_in_production=True,
        default_C_cap_sum=42720,default_D_cap_sum=3600)
    write(OUT/'experiment_plan.json',plan)
    print('C32+D4 orders and exact input manifests fixed before results')

def freeze():
    build=read(OUT/'candidate_build.json');assert native_identity()['PE_SHA']==build['production']['PE_SHA']
    for name,digest in build['source_hashes'].items():assert sha(ROOT/name)==digest,name
    commit=git('rev-parse','HEAD').decode().strip()
    candidate=dict(schema='round134-frozen-production-v1',UTC=utc(),base=BASE,source_commit=commit,
        source_hashes=build['source_hashes'],production_PE=str(E3),production_PE_SHA=sha(E3),
        research_PE=str(E3),research_PE_SHA=sha(E3),research_alias_not_separate_production_algorithm=True,
        DLL=str(DLL),DLL_SHA=DLL_SHA,build_SHA=sha(OUT/'candidate_build.json'),
        proof_policy='independent exact stock zero plus complete own physical fleet; native status unchanged; other epsilon/native rules retained')
    write(OUT/'candidate_manifest.json',candidate)
    plan=read(OUT/'experiment_plan.json')
    for stage in ('C','D'):
        groups=[]
        for row in plan[stage]:
            position=row['position'];camp=OUT/f'campaign/{stage}_{position:02}'
            camp.mkdir(parents=True,exist_ok=False)
            p=copy.deepcopy(row['input_binding']['panel']);p.update(cap_seconds=row['cap_seconds'],gurobi_seed=row['seed'],
                **{'lambda':row['lambda_value']},panel_kind=f'Round134 {stage} known-role final-version')
            p['instance_path']=p['input_path']
            assert sha(ROOT/p['input_path'])==p['input_sha256']
            ref=p['reference'];source=Path(row['input_binding']['launch']['destination']).parents[1]/'reference'/p['id']
            if not source.is_dir():
                source=WORK/f"worktrees/round{row['input_binding']['round']}"/f"results/unified_exact_round{row['input_binding']['round']}/qualification/references"/p['id']
            assert source.is_dir(),str(source)
            target=camp/'reference'/p['id'];target.mkdir(parents=True)
            for name in ('original.lp','build.json'):
                shutil.copyfile(source/name,target/name)
            assert sha(target/'original.lp')==ref['canonical_sha256'] and read(target/'build.json')==ref
            method=row['method'];arm='P-GRB' if method=='P' else 'P-S' if method=='PS' else 'M-B'
            armid=f"{stage}{position:02}_{p['id']}_S{row['seed']}_R{row['repeat']}_{method}"
            d=camp/'raw'/armid
            cmd=original_command(p,'P-GRB' if method=='PS' else arm,d);cmd[0]=str(E3)
            assert float(cmd[cmd.index('--lambda')+1])==row['lambda_value']
            if method in ('P','PS'):
                for flag in ('--round24-executable-sha256','--round24-manifest-executable-sha256'):
                    cmd[cmd.index(flag)+1]=sha(E3)
            if method=='PS':cmd+=['--round112-ens-start-compact']
            else:cmd+=['--round127-mode','p' if method=='P' else 'ms2']
            launch=dict(number=1,group_number=position,global_launch_number=position,id=p['id'],arm=arm,
                method=method,seed=row['seed'],repeat=row['repeat'],binary_layer='R134',version='candidate',
                panel=p,panel_kind=p['panel_kind'],destination=str(d),cap_seconds=row['cap_seconds'],
                hard_stop_seconds=row['cap_seconds']-2,command=cmd,configuration=dict(id='q0',MIPFocus=0,Cuts=-1),arm_id=armid)
            identity=dict(schema='round134-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=row['seed']),
                candidate_binary=str(E3),candidate_binary_sha256=sha(E3)),prereg_sha256=sha(OUT/'experiment_plan.json'),
                runner_sha256=sha(__file__),source_hashes=candidate['source_hashes'],candidate_binary_sha256=sha(E3),
                dll_sha256=DLL_SHA,measured_source_commit=commit,delivery_base_commit=BASE,launches=[launch],
                references={p['id']:ref},candidate_manifest_path=str(OUT/'candidate_manifest.json'),
                candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),stage=stage,no_cross_arm_information=True,
                source_input_binding={k:v for k,v in row['input_binding'].items() if k not in ('launch','plan','panel')})
            write(camp/'identity.json',identity)
            groups.append(dict(position=position,arm_id=armid,group=f'campaign/{stage}_{position:02}',identity_SHA=sha(camp/'identity.json'),launch=launch))
        write(OUT/f'{stage}_matrix_frozen.json',dict(stage=stage,groups=groups,full_arm_count=len(groups),
            full_arm_cap_sum_seconds=sum(q['launch']['cap_seconds'] for q in groups),
            candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),experiment_plan_SHA=sha(OUT/'experiment_plan.json')))
    write(OUT/'execution_binding.json',dict(UTC=utc(),candidate_SHA=sha(OUT/'candidate_manifest.json'),
        helper_SHA={f'scripts/{n}':sha(ROOT/'scripts'/n) for n in ('round134_common.py','round134_campaign.py','round134_read.py',
            'round133_campaign.py','round133_postverify_repair.py','round133_read.py','round115_campaign.py','round121_campaign.py')},
        C_matrix_SHA=sha(OUT/'C_matrix_frozen.json'),D_matrix_SHA=sha(OUT/'D_matrix_frozen.json')))
    print('Source/PE/DLL and C32+D4 actual commands frozen')

def admission():
    binding=read(OUT/'execution_binding.json')
    assert binding['candidate_SHA']==sha(OUT/'candidate_manifest.json')
    inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in binding['helper_SHA'].items():assert sha(ROOT/name)==digest,name
    return binding

def arm(stage,position,label):
    from round134_read import verify
    admission();group=read(OUT/f'{stage}_matrix_frozen.json')['groups'][int(position)-1]
    camp=OUT/group['group'];assert sha(camp/'identity.json')==group['identity_SHA']
    identity=read(camp/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    assert not (d/'verification_closeout.json').exists()
    if not d.exists():
        tick,creation=inherited.inherited.process_origin()
        inherited.supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'inspect existing unsealed native before any action'
    started=time.perf_counter()
    try:value=verify(launch,identity)
    finally:write(OUT/'cost_segments'/label/'verification.json',dict(native_Optimize=0,seconds=time.perf_counter()-started,kind='postproduction audit'))
    write(OUT/'runtime_status.json',dict(UTC=utc(),stage=stage,position=position,arm_id=launch['arm_id'],
        certificate=value['arm']['certificate'],U=value['arm']['U'],L=value['arm']['L']))
    print(json.dumps(value['arm']),flush=True)

def run(stage,stop_after=None):
    admission()
    for group in read(OUT/f'{stage}_matrix_frozen.json')['groups']:
        if stop_after is not None and group['position']>stop_after:break
        d=Path(group['launch']['destination'])
        if (d/'verification_closeout.json').exists():continue
        label=f'{stage}_{group["position"]:02}_01'
        assert not (OUT/'fees'/label).exists(),'inspect failed/pending original; no automatic native rerun'
        assert metered(label,stage,[PYTHON,ROOT/'scripts/round134_campaign.py','arm',stage,group['position'],label],
            reservation=group['launch']['cap_seconds'],timeout=group['launch']['cap_seconds']+1800)==0
    print('Round134 serial stage returned '+stage,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','freeze','arm','run']);p.add_argument('stage',nargs='?',choices=['C','D']);p.add_argument('position',nargs='?',type=int);p.add_argument('label',nargs='?');p.add_argument('--stop-after',type=int);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='freeze':freeze()
    elif a.action=='arm':arm(a.stage,a.position,a.label)
    else:run(a.stage,a.stop_after)
