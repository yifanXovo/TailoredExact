"""Unchanged R154 production/reader with six newly frozen own-H lifecycles."""
import copy, types
import round154_campaign as previous
import round154_read as reader
from round155_common import *

ROLES=[('N-B35-S',7200),('R-X35-S-T2',7200),('R-X20-S-T1',1200)]

def bound_functions():
    arguments=types.FunctionType(previous.arguments.__code__,dict(vars(previous),OUT=OUT))
    make=types.FunctionType(previous.make_launch.__code__,dict(vars(previous),OUT=OUT,BASE=BASE,arguments=arguments))
    floor=types.FunctionType(reader.floor_contract.__code__,dict(vars(reader),OUT=OUT))
    verify=types.FunctionType(reader.verify.__code__,dict(vars(reader),OUT=OUT,configure=configure,floor_contract=floor))
    execute=types.FunctionType(previous.execute.__code__,dict(vars(previous),OUT=OUT,configure=configure,verify=verify))
    return make,execute

def freeze():
    configure(); assert not (OUT/'confirmation_matrix.json').exists()
    for name in ('candidate_manifest.json','helper_manifest.json'):
        (OUT/name).write_bytes((OLD154/name).read_bytes())
    (OUT/'production_plan.md').write_text(
        '# Round155 production panel\n\nUnchanged R154 PE, proof-only E and R153 own-floor producer.\n'
        'NB35 B/E7200; R-X35-S-T2 B/E7200; R-X20-S-T1 B/E1200.\n'
        'Seed0 Threads1 own-H20260626 pair-only AM=.08 depth8 width1e-4.\n'
        'Each arm pays its own H/helper. No offline or cross-arm injection.\n'
        'See preanalysis.md, goal.md and production_identity.json.\n',encoding='utf-8')
    assert read(OLD154/'qualification/proof_placement_v1/result.json')['PASS']
    make,_=bound_functions(); groups=[]
    for role,cap in ROLES:
        for method in ('B','E'):
            position=len(groups)+1; camp=OUT/'campaign_confirmation'/f'{position:03}'
            camp.mkdir(parents=True,exist_ok=False)
            launch,identity=make(role,method,camp,position,cap)
            old_destination=launch['destination']; armid=launch['arm_id'].replace('R154_','R155_',1)
            destination=str(camp/'raw'/armid)
            launch['command']=[v.replace(old_destination,destination) for v in launch['command']]
            launch.update(arm_id=armid,destination=destination,binary_layer='R154-unchanged-same-PE',round155_method=method)
            launch['panel'].update(panel_kind='Round155 frozen persistent E validation',round155_method=method)
            identity.update(schema='round155-same-producer-own-complete-v1',launches=[launch],runner_sha256=sha(__file__),
                production_qualification=str(OLD154/'qualification/proof_placement_v1/result.json'),
                production_qualification_SHA=sha(OLD154/'qualification/proof_placement_v1/result.json'))
            write(camp/'identity.json',identity)
            groups.append(dict(position=position,group=camp.relative_to(OUT).as_posix(),identity_SHA=sha(camp/'identity.json'),launch=launch))
    helpers=previous.inherited.helper_bindings()
    helpers.update(read(OUT/'helper_manifest.json')['helper_dependencies'])
    for name in ['round154_campaign.py','round154_read.py','round155_campaign.py','round155_common.py']:
        helpers['scripts/'+name]=sha(ROOT/'scripts'/name)
    write(OUT/'confirmation_matrix.json',dict(UTC=utc(),groups=groups,helpers=helpers,nominal_complete_seconds=31200,
        Seed=0,Threads=1,H_seed=20260626,serial=True,all_own_H=True,
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),helper_manifest_SHA=sha(OUT/'helper_manifest.json'),
        frozen_before_any_new_complete_result=True,no_offline_or_cross_arm_information=True))
    print(json.dumps(dict(frozen=True,arms=len(groups),seconds=31200)),flush=True)

def admit():
    """Separate readback of every argv against original identities and entry."""
    matrix=read(OUT/'confirmation_matrix.json'); facts=[]
    output={'--out','--log','--process-phase-ledger','--external-gini-artifact-dir',
            '--primal-heuristic-generation-log','--progress-log','--native-evidence-dir'}
    for group in matrix['groups']:
        camp=OUT/group['group'];identity=read(camp/'identity.json');launch=group['launch']
        assert sha(camp/'identity.json')==group['identity_SHA'] and launch==identity['launches'][0]
        role=launch['id'];method=launch['R154_method'];cap=dict(ROLES)[role]
        original=previous.old_launch(role)
        old=dict(zip(original['command'][1::2],original['command'][2::2]))
        cmd=dict(zip(launch['command'][1::2],launch['command'][2::2]))
        assert 2*len(cmd)+1==len(launch['command'])
        for flag,value in old.items():
            if flag not in output|{'--time-limit','--process-wall-time-limit'}:
                assert cmd[flag]==value,(role,flag)
        assert float(cmd['--time-limit'])==cap-6 and float(cmd['--process-wall-time-limit'])==cap
        assert launch['cap_seconds']==cap and launch['hard_stop_seconds']==cap-2
        assert cmd['--round153-root-floor']==cmd['--round154-proof-floor']==('on' if method=='E' else 'off')
        assert all(Path(cmd[k]).resolve().is_relative_to(OUT.resolve()) for k in output)
        assert not Path(launch['destination']).exists()
        candidate=previous.inherited._candidate(OUT/'candidate_manifest.json')
        assert sha(launch['command'][0])==candidate['production_PE_SHA']==identity['candidate_binary_sha256']
        assert launch['AM_threshold']==.08 and launch['seed']==0
        # Original profile/preset owns the unchanged pair-only AM rules.
        assert sha(ROOT/'config/gi_tbc_round137.json')==read(ROOT/'config/gi_tbc_proof_floor_round154.json')['parent_profile_SHA256']
        facts.append(dict(role=role,method=method,cap=cap,original_semantics_preserved=True,own_H=True))
    for name,digest in matrix['helpers'].items(): assert sha(ROOT/name)==digest,name
    write(OUT/'review/confirmation_admission.json',dict(decision='ACCEPT',matrix_SHA=sha(OUT/'confirmation_matrix.json'),
        independent_argv_reconstruction=True,nonimplementer_agent_review=False,review_method='separate readback against fixed R137 argv and R154 qualifications',
        source_SHA=sha(__file__),facts=facts,Optimize=0,no_CPP_or_producer_change=True))
    print(json.dumps(dict(admitted=True,arms=len(facts))),flush=True)

def arm(position):
    configure(); gate=read(OUT/'review/confirmation_admission.json')
    assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(__file__)
    assert gate['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    matrix=read(OUT/'confirmation_matrix.json')
    for name,digest in matrix['helpers'].items(): assert sha(ROOT/name)==digest,name
    group=matrix['groups'][int(position)-1];camp=OUT/group['group']
    assert sha(camp/'identity.json')==group['identity_SHA']
    _,execute=bound_functions();execute(group['launch'],read(camp/'identity.json'))

def one(position):
    position=int(position);group=read(OUT/'confirmation_matrix.json')['groups'][position-1]
    write(OUT/'active_position.json',dict(UTC=utc(),stage='complete_E',position=position,arm_id=group['launch']['arm_id']))
    run(f'confirmation_{position:03}',group['launch']['cap_seconds']+900,'round155_campaign.py',['arm',str(position)],kind='native')

if __name__=='__main__': globals()[sys.argv[1]](*sys.argv[2:])
