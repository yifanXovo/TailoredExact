"""Serial independent full runs, matched frozen R137 baselines and small pilot."""
from round138_common import *
import copy,csv,types
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round138_read import verify

CORE=['K-15-S','R-X20-S-T1','K-20-S','K-35-U','R-B35-S-T1','R-B35-S-T2','R-X35-S-T1','R-X35-S-T2']

def prepare():
    assert not (OUT/'experiment_plan.json').exists()
    old=ROOT/'results/unified_exact_round137';frozen=read(old/'matrix_frozen.json')
    by={g['launch']['id']:g for g in frozen['groups'] if g['launch']['method']=='S2' and g['launch']['seed']==0}
    table=list(csv.DictReader((old/'reports/arms.csv').open()))
    reused=[]
    for role in CORE:
        group=by[role];l=group['launch'];p=l['panel']
        row=next(r for r in table if r['role']==role and r['method']=='S2' and r['seed']=='0')
        assert row['performance_eligible']=='True' and row['native_proof_qualified']=='True'
        assert row['input_SHA']==p['input_sha256']==sha(ROOT/p['input_path'])
        assert int(row['cap'])==p['cap_seconds'] and float(row['lambda_value'])==p['lambda']
        assert float(row['T'])==p['T_seconds'] and row['PE_SHA']==read(old/'candidate_manifest.json')['production_PE_SHA']
        reused.append(dict(role=role,position=group['position'],baseline=row,launch=l,
            source_commit='e735c3447eb1443713c700942d873de1783a4a26',
            rationale='Same frozen GI-TBC PE, input, physical/objective doubles, Seed0, cap, single-thread Gurobi13.0.2/affinity4 and complete-cost convention. New off writer bridge is exact; contemporaneous K15 full baseline bridge is additionally registered.'))
    micro=json.loads(git('show','HEAD:results/unified_exact_round131/input_manifest.json'))
    micro=next(p for p in micro['roles'] if p['id']=='SM-B10-B');micro['gurobi_seed']=0
    positions=[dict(role='K-15-S',method='BASE',stage='contemporaneous-baseline-bridge',seed=0,panel=by['K-15-S']['launch']['panel'])]
    positions += [dict(role=role,method='STOCK',stage='pilot' if role in CORE[:3] else 'core-completion',seed=0,
                      panel=by[role]['launch']['panel']) for role in CORE]
    positions += [dict(role=micro['id'],method=m,stage='micro',seed=0,panel=micro) for m in ['BASE','STOCK']]
    for i,a in enumerate(positions,1):a['position']=i;a['cap_seconds']=a['panel']['cap_seconds']
    write(OUT/'baseline_reuse.json',dict(UTC=utc(),baselines=reused,
        R137_matrix_SHA=sha(old/'matrix_frozen.json'),R137_reports_SHA=sha(old/'reports/arms.csv'),
        baseline_manifest_SHA=sha(old/'candidate_manifest.json'),new_Optimize=0,
        no_new_independent_validation_set_claimed=True,baseline_public_pin='e735c3447eb1443713c700942d873de1783a4a26'))
    write(OUT/'experiment_plan.json',dict(UTC=utc(),positions=positions,core_roles=CORE,
        core_configurations=8,core_base_inputs=6,nominal_core_method_positions=16,
        reused_baseline_positions=8,new_core_candidate_positions=8,new_bridge_positions=1,new_micro_positions=2,
        new_caps_seconds=sum(a['cap_seconds'] for a in positions),nominal_core_caps_seconds=30000,
        main_candidate='GI-TBC+stock-RLT (four inventory rows; TC/AP remain off)',
        choice_basis='All four same-domain stock LPs improve original objective. TC+stock adds information on K20/RX35 but main candidate is the minimal uniform four-row mechanism.',
        conditional_Seed1='At most two result-selected roles, both methods Seed1; separately registered after Seed0',
        seed=0,H_seed=20260626,serial=True,threads=1,affinity=4,compute_limit=86400,
        pilot_stop_after_position=4,LP_plan_SHA=sha(OUT/'roots/plan.json'),
        independent_admission_required_before_full_runs=True,no_cross_arm_information=True))
    print('Registered 8 configurations / 6 inputs, 16 core method positions (8 matched R137 reused); 11 new runs including bridge and micro')

def freeze():
    assert not (OUT/'matrix_frozen.json').exists()
    plan=read(OUT/'experiment_plan.json');build=read(OUT/'candidate_build.json')
    for name,digest in build['source_hashes'].items():assert sha(ROOT/name)==digest,name
    commit=git('rev-parse','HEAD').decode().strip()
    candidate=dict(schema='round138-shared-stock-product-v1',UTC=utc(),source_commit=commit,base=BASE,
        source_hashes=build['source_hashes'],production_PE=str(E3),production_PE_SHA=sha(E3),
        research_PE=str(E3),research_PE_SHA=sha(E3),DLL=str(DLL),DLL_SHA=DLL_SHA,
        source_build_SHA=sha(OUT/'candidate_build.json'),default_entry_unchanged=True,stock_rlt_default=False,
        baseline_config_SHA=sha(ROOT/'config/gi_tbc_round137.json'),qualification_SHA=sha(OUT/'qualification/matrix_checks.json'))
    write(OUT/'candidate_manifest.json',candidate)
    old=ROOT/'results/unified_exact_round137';oldmanifest=read(old/'candidate_manifest.json')
    template=read(old/'matrix_frozen.json')['groups'][2]['launch'];assert template['method']=='S2'
    groups=[]
    for a in plan['positions']:
        n=a['position'];p=copy.deepcopy(a['panel']);method=a['method'];p['gurobi_seed']=a['seed'];p['round138_stock_rlt']=method=='STOCK'
        p['round137_delete_ab']=False;p['panel_kind']='Round138 known research panel / explicit baseline bridge or micro'
        camp=OUT/'campaign'/f'{n:03}';camp.mkdir(parents=True,exist_ok=False)
        armid=f'R138_{n:03}_{p["id"]}_S{a["seed"]}_{method}';d=camp/'raw'/armid
        pe=E3 if method=='STOCK' else Path(oldmanifest['production_PE'])
        cmd=copy.deepcopy(template['command']);old_d=template['destination'];cmd=[x.replace(old_d,str(d)) for x in cmd]
        def put(flag,value):cmd[cmd.index(flag)+1]=str(value)
        cmd[0]=str(pe)
        for flag,key in [('--input','input_path'),('--lambda','lambda'),('--T','T_seconds'),
                         ('--pickup-time','pickup_seconds'),('--drop-time','drop_seconds')]:put(flag,p[key])
        put('--time-limit',p['cap_seconds']-6);put('--process-wall-time-limit',p['cap_seconds']);put('--gurobi-seed',a['seed'])
        if method=='STOCK':cmd.append('--round138-stock-rlt')
        launch=dict(number=1,group_number=n,global_launch_number=n,id=p['id'],arm='M-B',method=method,seed=a['seed'],repeat=1,
            binary_layer='R138' if method=='STOCK' else 'R137',version='candidate' if method=='STOCK' else 'baseline-r137',
            panel=p,panel_kind=p['panel_kind'],destination=str(d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,
            command=cmd,configuration=dict(id='q0',MIPFocus=0,Cuts=-1),arm_id=armid,stage=a['stage'],AM_threshold=.08)
        sources=candidate if method=='STOCK' else oldmanifest
        identity=dict(schema='round138-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=a['seed']),
            candidate_binary=str(pe),candidate_binary_sha256=sha(pe)),prereg_sha256=sha(OUT/'experiment_plan.json'),
            runner_sha256=sha(__file__),source_hashes=sources['source_hashes'],candidate_binary_sha256=sha(pe),dll_sha256=DLL_SHA,
            measured_source_commit=sources['source_commit'],delivery_base_commit=BASE,launches=[launch],
            candidate_manifest_path=str(OUT/'candidate_manifest.json'),candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),
            stage=a['stage'],no_cross_arm_information=True)
        write(camp/'identity.json',identity)
        groups.append(dict(position=n,stage=a['stage'],group=camp.relative_to(OUT).as_posix(),arm_id=armid,
            identity_SHA=sha(camp/'identity.json'),launch=launch))
    helpers=inherited.helper_bindings()
    write(OUT/'matrix_frozen.json',dict(UTC=utc(),groups=groups,helpers=helpers,
        source_commit=commit,experiment_plan_SHA=sha(OUT/'experiment_plan.json'),candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),
        baseline_reuse_SHA=sha(OUT/'baseline_reuse.json'),serial=True,threads=1,Seed=0,H_seed=20260626))
    print('Frozen; await independent full-matrix admission')

def admission():
    gate=read(OUT/'review/full_admission.json');assert gate['decision']=='ACCEPT'
    assert gate['matrix_SHA']==sha(OUT/'matrix_frozen.json')
    m=read(OUT/'matrix_frozen.json');assert m['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    assert m['experiment_plan_SHA']==sha(OUT/'experiment_plan.json')
    inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in m['helpers'].items():assert sha(ROOT/name)==digest,name
    return m

def arm(position,label):
    group=admission()['groups'][int(position)-1];camp=OUT/group['group']
    assert sha(camp/'identity.json')==group['identity_SHA']
    identity=read(camp/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    assert not (d/'verification_closeout.json').exists()
    if not d.exists():
        tick,creation=inherited.inherited.process_origin()
        inherited.supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'Never repeat an unsealed run'
    started=time.perf_counter()
    try:value=verify(launch,identity)
    finally:write(OUT/'cost_segments'/label/'verification.json',dict(native_Optimize=0,seconds=time.perf_counter()-started,kind='postproduction audit'))
    write(OUT/'runtime_status.json',dict(UTC=utc(),position=position,arm_id=launch['arm_id'],method=launch['method'],
        certificate=value['arm']['certificate'],U=value['arm']['U'],L=value['arm']['L']))
    print(json.dumps(value['arm']),flush=True)

def run(stop_after=4):
    for group in admission()['groups']:
        if group['position']>stop_after:break
        if (Path(group['launch']['destination'])/'verification_closeout.json').exists():continue
        label=f'arm_{group["position"]:03}'
        assert not (OUT/'fees'/label).exists(),'Inspect/resume existing fee; no automatic rerun'
        write(OUT/'active_position.json',dict(UTC=utc(),position=group['position'],arm_id=group['arm_id'],fee_label=label))
        assert metered(label,'native',[PYTHON,ROOT/'scripts/round138_campaign.py','arm',group['position'],label],
            reservation=group['launch']['cap_seconds'],timeout=group['launch']['cap_seconds']+1800)==0
    write(OUT/'run_loop_return.json',dict(UTC=utc(),stop_after=stop_after,budget=budget()))

if __name__=='__main__':
    if sys.argv[1]=='arm':arm(int(sys.argv[2]),sys.argv[3])
    elif sys.argv[1]=='run':run(int(sys.argv[2]) if len(sys.argv)>2 else 4)
    else:globals()[sys.argv[1]]()
