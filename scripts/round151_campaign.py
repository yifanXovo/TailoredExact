"""Frozen serial complete own-H B/C pairs, same new production PE."""
import copy
import round133_campaign as inherited
from round121_campaign import finish_producer
from round122_prepare import COMMON
from round151_read import verify
from round151_common import *
def profile():
    manifest=inherited._candidate(OUT/'candidate_manifest.json')
    p=read(ROOT/'config/gi_tbc_round137.json')
    p.update(schema='round151-standalone-penalty-frozen-argv-v1',algorithm='GI-TBC plus standalone resource-penalty state caps',
        round=151,source_commit=manifest['source_commit'],research_head=manifest['source_commit'],
        default_executable=manifest['production_PE'],verified_PE_SHA256=manifest['production_PE_SHA'],
        verified_DLL=str(DLL),verified_DLL_SHA256=DLL_SHA,research_profile=True,GD=False,STOCK=False,Shared_S=False,
        source_manifest='results/unified_exact_round151/candidate_manifest.json',
        parent_profile_SHA256=sha(ROOT/'config/gi_tbc_round137.json'),unique_complete_candidate='C',
        default_AM=.08,maximum_depth=8,minimum_width=.0001,pair_only=True,H_seed=20260626)
    p['argv']+=['--round146-gd','off','--round149-penalty-feedback','off','--round151-penalty-propagation','conditional']
    write(ROOT/'config/gi_tbc_penalty_propagation_round151.json',p)
def freeze():
    configure();assert not budget()['unclosed'];target=OUT/'confirmation_matrix.json';assert not target.exists()
    assert read(OUT/'candidate_freeze.json')['A']=='C';manifest=inherited._candidate(OUT/'candidate_manifest.json')
    source=read(ROOT/'results/unified_exact_round137/matrix_frozen.json')
    by={g['launch']['id']:g['launch'] for g in source['groups'] if g['launch']['method']=='S2' and g['launch']['seed']==0}
    positions=[dict(role=r,method=m) for r in ['N-B35-S','N-C20-U'] for m in ['B','C']];groups=[]
    for i,spec in enumerate(positions,1):
        old=by[spec['role']];launch=copy.deepcopy(old);panel=launch['panel'];method=spec['method']
        assert launch['cap_seconds']==(2400 if panel['V']==35 else 1200)
        assert panel['lambda']==.15 and panel['pickup_seconds']==panel['drop_seconds']==60
        assert sha(ROOT/panel['input_path'])==panel['input_sha256']
        panel.update(gurobi_seed=0,round151_method=method,round138_stock_rlt=False,round146_gd=False,
            round149_penalty_feedback=False,known=True,exposed=True,panel_kind='Round151 complete own-H stable B versus independent C')
        camp=OUT/'campaign_confirmation'/f'{i:03}';camp.mkdir(parents=True,exist_ok=False)
        armid=f'R151_{i:03}_{spec["role"]}_S0_{method}';destination=camp/'raw'/armid
        command=[v.replace(old['destination'],str(destination)) for v in old['command']];command[0]=manifest['production_PE']
        command+=['--round146-gd','off','--round149-penalty-feedback','off','--round151-penalty-propagation','off' if method=='B' else 'conditional']
        launch.update(number=1,group_number=i,global_launch_number=i,method='S2' if method=='B' else 'C',R147_method='BASE',
            R151_method=method,seed=0,binary_layer='R151-new-same-PE',version='candidate',panel=panel,panel_kind=panel['panel_kind'],
            destination=str(destination),command=command,arm_id=armid,stage='confirmation',AM_threshold=.08)
        identity=dict(schema='round151-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=0),
            candidate_binary=manifest['production_PE'],candidate_binary_sha256=manifest['production_PE_SHA']),
            prereg_sha256=sha(OUT/'candidate_freeze.json'),runner_sha256=sha(__file__),source_hashes=manifest['source_hashes'],
            candidate_binary_sha256=manifest['production_PE_SHA'],dll_sha256=DLL_SHA,measured_source_commit=manifest['source_commit'],
            delivery_base_commit=BASE,launches=[launch],candidate_manifest_path=str(OUT/'candidate_manifest.json'),
            candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),stage='confirmation',no_cross_arm_information=True,
            original_frozen_launch=old,original_fixed_science=SCIENCE137)
        write(camp/'identity.json',identity)
        groups.append(dict(position=i,group=camp.relative_to(OUT).as_posix(),arm_id=armid,identity_SHA=sha(camp/'identity.json'),launch=launch))
    helpers=inherited.helper_bindings()
    for name in ['round151_campaign.py','round151_read.py','round151_common.py','round151_math.py','round149_context.py','round149_read.py']:
        helpers['scripts/'+name]=sha(ROOT/'scripts'/name)
    write(target,dict(UTC=utc(),groups=groups,candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),helpers=helpers,
        candidate_freeze_SHA=sha(OUT/'candidate_freeze.json'),Seed=0,H_seed=20260626,Threads=1,affinity_mask=4,
        serial=True,all_own_H=True,first_pair_positions=[1,2],conditional_second_pair_positions=[3,4],
        second_pair_not_entered=True,clarification_not_entered=True,nominal_core_caps=7200,
        no_original_H_LP_incumbent_or_cross_arm_injection=True))
    profile();print('Frozen four planned positions; only first pair eligible after independent admission')
def admission(position):
    path=OUT/'confirmation_matrix.json';matrix=read(path);gate=read(OUT/'review/confirmation_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(path) and gate['independent_nonimplementer_review']
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    inherited._candidate(OUT/'candidate_manifest.json')
    for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
    if position>=3:
        entry=read(OUT/'certificate_pair_decision.json');assert entry['enter'] and entry['decided_after_first_pair']
    return matrix
def arm(position):
    group=admission(position)['groups'][position-1];camp=OUT/group['group']
    assert sha(camp/'identity.json')==group['identity_SHA'];identity=read(camp/'identity.json');launch=identity['launches'][0]
    destination=Path(launch['destination']);assert not (destination/'verification_closeout.json').exists()
    if not destination.exists():
        tick,creation=inherited.inherited.process_origin();inherited.supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (destination/'producer_receipt.json').exists() and (destination/'producer_seal.json').exists(),'Inspect unsealed producer; never rerun'
    result=verify(launch,identity);write(OUT/'runtime_status.json',dict(UTC=utc(),position=position,arm_id=launch['arm_id'],arm=result['arm']))
    print(json.dumps(result['arm']),flush=True)
def run(stop_after=2):
    configure()
    for position in range(1,stop_after+1):
        group=admission(position)['groups'][position-1]
        if (Path(group['launch']['destination'])/'verification_closeout.json').exists():continue
        label=f'confirmation_{position:03}';assert not (OUT/'fees'/label).exists(),'Inspect existing fee before resume'
        write(OUT/'active_position.json',dict(UTC=utc(),position=position,fee_label=label,arm_id=group['arm_id']))
        cap=group['launch']['cap_seconds']
        assert metered(label,'native',[PYTHON,'-B',__file__,'arm',position],cap+600,cap+1800)==0
    write(OUT/'confirmation_run_return.json',dict(UTC=utc(),budget=budget(),stop_after=stop_after))
if __name__=='__main__':
    if sys.argv[1]=='arm':arm(int(sys.argv[2]))
    elif sys.argv[1]=='run':run(int(sys.argv[2]) if len(sys.argv)>2 else 2)
    else:globals()[sys.argv[1]]()
