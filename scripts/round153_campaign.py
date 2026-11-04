"""Serial complete own-H B/J pairs with one frozen new PE and helper chain."""
import copy,types
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round153_read import verify
from round153_common import *
from round140_common import git
from round100_idle import ensure_idle

SCIENCE137='e735c3447eb1443713c700942d873de1783a4a26'
ROLES=['N-B35-S','K-35-U','R-B35-S-T1','N-C20-U']

def old_launch(role):
    source=read(ROOT/'results/unified_exact_round137/matrix_frozen.json')
    old=next(g['launch'] for g in source['groups'] if g['launch']['id']==role and g['launch']['method']=='S2' and g['launch']['seed']==0)
    panel=old['panel'];command=old['command']
    assert float(command[command.index('--lambda')+1])==panel['lambda']
    assert panel['pickup_seconds']==panel['drop_seconds']==60
    assert float(command[command.index('--pickup-time')+1])==float(command[command.index('--drop-time')+1])==60
    assert sha(ROOT/panel['input_path'])==panel['input_sha256']
    return old

def arguments(method):
    result=['--round146-gd','off','--round149-penalty-feedback','off','--round151-penalty-propagation','off',
            '--round153-root-floor','on' if method=='J' else 'off']
    if method=='J':
        result+=['--round153-python',str(PYTHON),'--round153-helper',str(ROOT/'scripts/round153_online.py'),
                 '--round153-helper-sha',sha(ROOT/'scripts/round153_online.py'),
                 '--round153-manifest',str(OUT/'helper_manifest.json'),'--round153-manifest-sha',sha(OUT/'helper_manifest.json')]
    return result

def make_launch(role,method,camp,index,cap=None):
    manifest=inherited._candidate(OUT/'candidate_manifest.json')
    old=old_launch(role)
    launch=copy.deepcopy(old);panel=launch['panel'];cap=cap or launch['cap_seconds']
    panel['cap_seconds']=cap
    panel.update(gurobi_seed=0,round153_method=method,round138_stock_rlt=False,round146_gd=False,
        round149_penalty_feedback=False,known=True,exposed=True,panel_kind='Round153 complete own-H B versus own-root floor J')
    armid=f'R153_{index:03}_{role}_S0_{method}';destination=camp/'raw'/armid
    command=[v.replace(old['destination'],str(destination)) for v in old['command']];command[0]=manifest['production_PE']
    command[command.index('--time-limit')+1]=str(cap-6)
    command[command.index('--process-wall-time-limit')+1]=str(cap)
    command+=arguments(method)
    launch.update(number=1,group_number=index,global_launch_number=index,method='S2' if method=='B' else 'J',R147_method='BASE',
        R153_method=method,seed=0,binary_layer='R153-new-same-PE',version='candidate',panel=panel,panel_kind=panel['panel_kind'],
        destination=str(destination),command=command,arm_id=armid,stage='confirmation',AM_threshold=.08,cap_seconds=cap,hard_stop_seconds=cap-2)
    identity=dict(schema='round153-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=0),
        candidate_binary=manifest['production_PE'],candidate_binary_sha256=manifest['production_PE_SHA']),
        prereg_sha256=sha(OUT/'production_plan.md'),runner_sha256=sha(__file__),source_hashes=manifest['source_hashes'],
        candidate_binary_sha256=manifest['production_PE_SHA'],dll_sha256=DLL_SHA,measured_source_commit=manifest['source_commit'],
        delivery_base_commit=BASE,launches=[launch],candidate_manifest_path=str(OUT/'candidate_manifest.json'),
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),stage='confirmation',no_cross_arm_information=True,
        helper_manifest_SHA=sha(OUT/'helper_manifest.json'),original_frozen_launch=old,original_fixed_science=SCIENCE137)
    write(camp/'identity.json',identity);return launch,identity

def execute(launch,identity):
    configure();destination=Path(launch['destination'])
    assert not (destination/'verification_closeout.json').exists()
    if not destination.exists():
        tick,creation=inherited.inherited.process_origin()
        # The original broad round88 interpreter-path detector also matches
        # this waiting supervisor. Preserve the established stricter idle
        # gate, excluding only actual OS ancestors, never arbitrary launchers.
        def idle():ensure_idle();return []
        supervisor=types.SimpleNamespace(**dict(vars(inherited.supervisor),foreign_heavy_processes=idle))
        supervised=types.FunctionType(inherited.supervised.__code__,dict(vars(inherited),supervisor=supervisor))
        supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (destination/'producer_receipt.json').exists() and (destination/'producer_seal.json').exists(),'Inspect unsealed producer; never rerun'
    result=verify(launch,identity)
    write(OUT/'runtime_status.json',dict(UTC=utc(),arm_id=launch['arm_id'],arm=result['arm']))
    print(json.dumps(result['arm']),flush=True)
    return result

def qualify(label='own_root_v1',cap=120):
    configure();camp=OUT/'qualification'/label;camp.mkdir(parents=True,exist_ok=False)
    launch,identity=make_launch('N-B35-S','J',camp,0,int(cap))
    result=execute(launch,identity)
    control=read(Path(launch['destination'])/'round153_control_audit.json')
    if int(cap)<=40:assert control['root']['global_deadline_stop'] and not control['Native_audits']
    write(camp/'result.json',dict(PASS=True,not_performance_sample=True,arm=result['arm'],own_H=True,
        actual_launch_cap=int(cap),source=control))

def profile():
    manifest=inherited._candidate(OUT/'candidate_manifest.json');p=read(ROOT/'config/gi_tbc_round137.json')
    p.update(schema='round153-own-root-floor-frozen-argv-v1',algorithm='GI-TBC plus own-root integer total-objective floor',
        round=153,source_commit=manifest['source_commit'],research_head=manifest['source_commit'],
        default_executable=manifest['production_PE'],verified_PE_SHA256=manifest['production_PE_SHA'],
        verified_DLL=str(DLL),verified_DLL_SHA256=DLL_SHA,research_profile=True,GD=False,STOCK=False,Shared_S=False,
        source_manifest='results/unified_exact_round153/candidate_manifest.json',
        parent_profile_SHA256=sha(ROOT/'config/gi_tbc_round137.json'),unique_complete_candidate='J',
        default_AM=.08,maximum_depth=8,minimum_width=.0001,pair_only=True,H_seed=20260626)
    p['argv']+=arguments('J');write(ROOT/'config/gi_tbc_root_floor_round153.json',p)

def freeze():
    configure();assert not budget()['unclosed'];target=OUT/'confirmation_matrix.json';assert not target.exists()
    manifest=inherited._candidate(OUT/'candidate_manifest.json');groups=[]
    # Validate every historical scientific setting before creating any arm.
    # RB35-T1 has its original resource-normalized lambda, not 0.15.
    for role in ROLES:old_launch(role)
    positions=[dict(role=r,method=m) for r in ROLES for m in ['B','J']]
    for i,spec in enumerate(positions,1):
        camp=OUT/'campaign_confirmation'/f'{i:03}';camp.mkdir(parents=True,exist_ok=False)
        launch,identity=make_launch(spec['role'],spec['method'],camp,i)
        assert launch['cap_seconds']==(1200 if spec['role']=='N-C20-U' else 2400)
        groups.append(dict(position=i,group=camp.relative_to(OUT).as_posix(),arm_id=launch['arm_id'],identity_SHA=sha(camp/'identity.json'),launch=launch))
    helpers=inherited.helper_bindings()
    for name in ['round153_campaign.py','round153_read.py','round153_common.py','round153_pricing.py','round151_read.py','round149_context.py','round149_read.py']:
        helpers['scripts/'+name]=sha(ROOT/'scripts'/name)
    helpers.update(read(OUT/'helper_manifest.json')['helper_dependencies'])
    write(target,dict(UTC=utc(),groups=groups,candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),helpers=helpers,
        helper_manifest_SHA=sha(OUT/'helper_manifest.json'),Seed=0,H_seed=20260626,Threads=1,affinity_mask=4,
        serial=True,all_own_H=True,nominal_core_caps=16800,roles=ROLES,
        role_selection='NB35/K35 floor opportunities; RB35-T1 routing contrast; NC20 old certificate and zero-floor contrast',
        role_selection_before_any_new_full_pair=True,no_original_H_LP_incumbent_or_cross_arm_injection=True))
    profile();print('Frozen eight complete positions; independent admission still required',flush=True)

def admission():
    path=OUT/'confirmation_matrix.json';matrix=read(path);gate=read(OUT/'review/confirmation_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(path) and gate['independent_nonimplementer_review']
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json') and matrix['helper_manifest_SHA']==sha(OUT/'helper_manifest.json')
    inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
    return matrix

def arm(position):
    configure();group=admission()['groups'][position-1];camp=OUT/group['group']
    assert sha(camp/'identity.json')==group['identity_SHA'];identity=read(camp/'identity.json')
    execute(identity['launches'][0],identity)

def run(stop_after=8):
    configure()
    for position in range(1,stop_after+1):
        group=admission()['groups'][position-1]
        if (Path(group['launch']['destination'])/'verification_closeout.json').exists():continue
        label=f'confirmation_{position:03}';assert not (OUT/'fees'/label).exists(),'Inspect existing fee before resume'
        write(OUT/'active_position.json',dict(UTC=utc(),position=position,fee_label=label,arm_id=group['arm_id']))
        cap=group['launch']['cap_seconds']
        assert meter.metered(label,'native',[PYTHON,'-B',__file__,'arm',position],cap+600,cap+1800)==0
    write(OUT/'confirmation_run_return.json',dict(UTC=utc(),budget=budget(),stop_after=stop_after))

if __name__=='__main__':
    if sys.argv[1]=='arm':arm(int(sys.argv[2]))
    elif sys.argv[1]=='run':run(int(sys.argv[2]) if len(sys.argv)>2 else 8)
    elif sys.argv[1]=='qualify':qualify(*sys.argv[2:])
    else:globals()[sys.argv[1]]()
