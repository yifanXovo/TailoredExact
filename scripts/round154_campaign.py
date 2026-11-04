"""Frozen serial complete own-H B/E, plus one matched NB35 J placement arm."""
import copy,types
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round153_campaign import old_launch,SCIENCE137
from round154_read import verify
from round154_common import *
from round100_idle import ensure_idle

ROLES=['N-B35-S','K-35-U','R-B35-S-T1','N-C20-U']

def arguments(method):
    result=['--round146-gd','off','--round149-penalty-feedback','off','--round151-penalty-propagation','off',
            '--round153-root-floor','on' if method in ('E','J') else 'off',
            '--round154-proof-floor','on' if method=='E' else 'off']
    if method in ('E','J'):
        result+=['--round153-python',str(PYTHON),'--round153-helper',str(ROOT/'scripts/round153_online.py'),
                 '--round153-helper-sha',sha(ROOT/'scripts/round153_online.py'),
                 '--round153-manifest',str(OUT/'helper_manifest.json'),'--round153-manifest-sha',sha(OUT/'helper_manifest.json')]
    return result

def make_launch(role,method,camp,index,cap=None):
    manifest=inherited._candidate(OUT/'candidate_manifest.json');old=old_launch(role)
    launch=copy.deepcopy(old);panel=launch['panel'];cap=cap or launch['cap_seconds'];panel['cap_seconds']=cap
    panel.update(gurobi_seed=0,round154_method=method,round138_stock_rlt=False,round146_gd=False,
        round149_penalty_feedback=False,known=True,exposed=True,panel_kind='Round154 proof placement same producer B/E/J')
    armid=f'R154_{index:03}_{role}_S0_{method}';destination=camp/'raw'/armid
    command=[v.replace(old['destination'],str(destination)) for v in old['command']];command[0]=manifest['production_PE']
    command[command.index('--time-limit')+1]=str(cap-6)
    command[command.index('--process-wall-time-limit')+1]=str(cap);command+=arguments(method)
    launch.update(number=1,group_number=index,global_launch_number=index,method='S2' if method=='B' else method,R147_method='BASE',
        R154_method=method,seed=0,binary_layer='R154-new-same-PE',version='candidate',panel=panel,panel_kind=panel['panel_kind'],
        destination=str(destination),command=command,arm_id=armid,stage='confirmation',AM_threshold=.08,cap_seconds=cap,hard_stop_seconds=cap-2)
    identity=dict(schema='round154-own-complete-placement-v1',prereg=dict(common=dict(COMMON,gurobi_seed=0),
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
        def idle():ensure_idle();return []
        supervisor=types.SimpleNamespace(**dict(vars(inherited.supervisor),foreign_heavy_processes=idle))
        supervised=types.FunctionType(inherited.supervised.__code__,dict(vars(inherited),supervisor=supervisor))
        supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (destination/'producer_receipt.json').exists() and (destination/'producer_seal.json').exists(),'inspect unsealed producer'
    value=verify(launch,identity);write(OUT/'runtime_status.json',dict(UTC=utc(),arm_id=launch['arm_id'],arm=value['arm']))
    print(json.dumps(value['arm']),flush=True);return value

def qualify(label='proof_placement_v1',cap='120'):
    configure();camp=OUT/'qualification'/label;camp.mkdir(parents=True,exist_ok=False)
    launch,identity=make_launch('N-B35-S','E',camp,0,int(cap));value=execute(launch,identity)
    write(camp/'result.json',dict(PASS=True,not_performance_sample=True,arm=value['arm'],
          own_H=True,control=read(Path(launch['destination'])/'round154_control_audit.json')))

def freeze():
    configure();assert not budget()['unclosed'];target=OUT/'confirmation_matrix.json';assert not target.exists()
    assert read(OUT/'qualification/proof_placement_v1/result.json')['PASS']
    for role in ROLES:old_launch(role)
    specs=[(r,m) for r in ROLES for m in (['B','E','J'] if r=='N-B35-S' else ['B','E'])]
    groups=[]
    for i,(role,method) in enumerate(specs,1):
        camp=OUT/'campaign_confirmation'/f'{i:03}';camp.mkdir(parents=True,exist_ok=False)
        launch,identity=make_launch(role,method,camp,i)
        assert launch['cap_seconds']==(1200 if role=='N-C20-U' else 2400)
        groups.append(dict(position=i,group=camp.relative_to(OUT).as_posix(),arm_id=launch['arm_id'],identity_SHA=sha(camp/'identity.json'),launch=launch))
    helpers=inherited.helper_bindings()
    for name in ['round154_campaign.py','round154_read.py','round154_common.py','round153_read.py','round153_pricing.py','round151_read.py','round149_context.py','round149_read.py']:
        helpers['scripts/'+name]=sha(ROOT/'scripts'/name)
    helpers.update(read(OUT/'helper_manifest.json')['helper_dependencies'])
    write(target,dict(UTC=utc(),groups=groups,candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),helpers=helpers,
        helper_manifest_SHA=sha(OUT/'helper_manifest.json'),Seed=0,H_seed=20260626,Threads=1,affinity_mask=4,
        serial=True,all_own_H=True,nominal_core_caps=19200,roles=ROLES,
        frozen_before_any_new_complete_E_result=True,no_original_H_LP_incumbent_or_cross_arm_injection=True))

def admission():
    path=OUT/'confirmation_matrix.json';matrix=read(path);gate=read(OUT/'review/confirmation_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(path) and gate['independent_nonimplementer_review']
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json') and matrix['helper_manifest_SHA']==sha(OUT/'helper_manifest.json')
    inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
    return matrix

def arm(position):
    configure();group=admission()['groups'][int(position)-1];camp=OUT/group['group']
    assert sha(camp/'identity.json')==group['identity_SHA'];identity=read(camp/'identity.json');execute(identity['launches'][0],identity)

def complete():
    configure()
    for group in admission()['groups']:
        position=group['position']
        if (Path(group['launch']['destination'])/'verification_closeout.json').exists():continue
        cap=group['launch']['cap_seconds'];label=f'confirmation_{position:03}'
        assert not (OUT/'fees'/label).exists(),'inspect original attempt'
        write(OUT/'active_position.json',dict(UTC=utc(),position=position,fee_label=label,arm_id=group['arm_id']))
        run(label,cap+900,'round154_campaign.py',['arm',str(position)],kind='native')
    write(OUT/'confirmation_return.json',dict(UTC=utc(),budget=budget(),positions=9))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
