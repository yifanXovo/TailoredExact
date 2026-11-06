"""One preselected nine-arm panel, independent own H and paid own producer."""
import inspect,types
import round154_campaign as previous
from round156_read import verify
from round156_common import *

SPECS=[('R-X20-S-T1','E',1200),('R-X20-S-T1','Eplus',1200),
       ('R-B35-S-T1','E',2400),('R-B35-S-T1','Eplus',2400),
       ('N-B35-S','E',2400),('N-B35-S','Eplus',2400),
       ('R-X35-S-T2','B',7200),('R-X35-S-T2','E',7200),('R-X35-S-T2','Eplus',7200)]

def arguments(method):
    enabled=method in ('E','Eplus')
    result=['--round146-gd','off','--round149-penalty-feedback','off','--round151-penalty-propagation','off',
        '--round153-root-floor','on' if enabled else 'off','--round154-proof-floor','on' if enabled else 'off']
    if enabled:
        variant='Eplus' if method=='Eplus' else 'E'
        helper=ROOT/'scripts'/('round156_online.py' if method=='Eplus' else 'round153_online.py')
        manifest=OUT/f'helper_manifest_{variant}.json'
        result+=['--round153-python',str(PYTHON),'--round153-helper',str(helper),'--round153-helper-sha',sha(helper),
            '--round153-manifest',str(manifest),'--round153-manifest-sha',sha(manifest)]
        if method=='Eplus':result+=['--round156-rn-refinement','on']
    return result

def make(role,method,camp,index,cap):
    entry=OUT/f'helper_manifest_{"Eplus" if method=="Eplus" else "E"}.json'
    source=inspect.getsource(previous.make_launch)
    assert source.count("OUT/'helper_manifest.json'")==1
    source=source.replace("OUT/'helper_manifest.json'",'_helper_manifest_path')
    ns=dict(vars(previous),ROOT=ROOT,OUT=OUT,BASE=BASE,arguments=lambda ignored:arguments(method),_helper_manifest_path=entry)
    exec(compile(source,__file__+'::same_formal_launch','exec'),ns)
    consumer='B' if method=='B' else 'E'
    launch,identity=ns['make_launch'](role,consumer,camp,index,cap)
    original_destination=launch['destination'];armid=f'R156_{index:03}_{role}_S0_{method}'
    destination=str(camp/'raw'/armid)
    launch['command']=[v.replace(original_destination,destination) for v in launch['command']]
    launch.update(destination=destination,arm_id=armid,R156_method=method,binary_layer='R156-matched-PE')
    launch['panel'].update(round156_method=method,panel_kind='Round156 preselected paid producer panel')
    identity.update(schema='round156-uniform-own-floor-v1',launches=[launch],runner_sha256=sha(__file__),
        inventory_node_limit=16384 if method=='Eplus' else 4096,
        inventory_helper_entry='scripts/round156_online.py' if method=='Eplus' else 'scripts/round153_online.py',
        helper_manifest_SHA=sha(entry))
    write(camp/'identity.json',identity);return launch,identity

def execute(launch,identity):
    fn=types.FunctionType(previous.execute.__code__,dict(vars(previous),ROOT=ROOT,OUT=OUT,configure=configure,verify=verify))
    return fn(launch,identity)

def smoke(label,method):
    camp=OUT/'qualification'/label;camp.mkdir(parents=True,exist_ok=False)
    launch,identity=make('R-X20-S-T1',method,camp,0,120)
    result=execute(launch,identity)
    write(camp/'result.json',dict(PASS=True,method=method,arm=result['arm'],not_performance_sample=True,
        complete_lifecycle=True,independent_own_H=True,PE_SHA=sha(launch['command'][0])))

def freeze():
    configure();assert not (OUT/'confirmation_matrix.json').exists()
    decision=read(OUT/'candidate_decision.json');assert decision['selected']=='RN16384_original_gap'
    for method in ('B','E','Eplus'):
        assert read(OUT/f'qualification/smoke_{method}_v1/result.json')['PASS']
    groups=[]
    for index,(role,method,cap) in enumerate(SPECS,1):
        camp=OUT/'campaign_confirmation'/f'{index:03}';camp.mkdir(parents=True,exist_ok=False)
        launch,identity=make(role,method,camp,index,cap)
        groups.append(dict(position=index,group=camp.relative_to(OUT).as_posix(),identity_SHA=sha(camp/'identity.json'),launch=launch))
    helpers=previous.inherited.helper_bindings()
    for variant in ('E','Eplus'):helpers.update(read(OUT/f'helper_manifest_{variant}.json')['helper_dependencies'])
    for name in ('round156_campaign.py','round156_read.py','round156_common.py','round154_read.py','round153_read.py','round154_campaign.py'):
        helpers['scripts/'+name]=sha(ROOT/'scripts'/name)
    write(OUT/'confirmation_matrix.json',dict(UTC=utc(),groups=groups,helpers=helpers,
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),candidate_decision_SHA=sha(OUT/'candidate_decision.json'),
        helper_manifests={v:sha(OUT/f'helper_manifest_{v}.json') for v in ('E','Eplus')},
        nominal_complete_seconds=sum(x[2] for x in SPECS),Seed=0,Threads=1,H_seed=20260626,
        serial=True,all_own_H=True,no_offline_or_cross_arm_information=True,
        frozen_before_any_complete_panel_result=True,default_promotion=False))
    print(json.dumps(dict(frozen=True,arms=len(groups),seconds=sum(x[2] for x in SPECS))),flush=True)

def admit():
    matrix=read(OUT/'confirmation_matrix.json');facts=[]
    outputs={'--out','--log','--process-phase-ledger','--external-gini-artifact-dir','--primal-heuristic-generation-log','--progress-log','--native-evidence-dir'}
    for g in matrix['groups']:
        launch=g['launch'];identity=read(OUT/g['group']/'identity.json');method=launch['R156_method']
        assert sha(OUT/g['group']/'identity.json')==g['identity_SHA'] and identity['launches']==[launch]
        old=previous.old_launch(launch['id']);original=dict(zip(old['command'][1::2],old['command'][2::2]))
        cmd=dict(zip(launch['command'][1::2],launch['command'][2::2]));assert 2*len(cmd)+1==len(launch['command'])
        for flag,value in original.items():
            if flag not in outputs|{'--time-limit','--process-wall-time-limit'}:assert cmd[flag]==value,(flag,cmd[flag],value)
        assert float(cmd['--time-limit'])==launch['cap_seconds']-6 and float(cmd['--process-wall-time-limit'])==launch['cap_seconds']
        assert all(Path(cmd[k]).resolve().is_relative_to(OUT.resolve()) for k in outputs)
        assert cmd['--round153-root-floor']==cmd['--round154-proof-floor']==('off' if method=='B' else 'on')
        assert cmd.get('--round156-rn-refinement','off')==('on' if method=='Eplus' else 'off')
        assert sha(launch['command'][0])==identity['candidate_binary_sha256']==read(OUT/'candidate_manifest.json')['production_PE_SHA']
        assert launch['AM_threshold']==.08 and launch['seed']==0 and not Path(launch['destination']).exists()
        facts.append(dict(role=launch['id'],method=method,cap=launch['cap_seconds'],own_H=True,original_physical_identity_preserved=True))
    assert len(facts)==9 and matrix['nominal_complete_seconds']==33600
    for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
    write(OUT/'review/confirmation_admission.json',dict(decision='ACCEPT',matrix_SHA=sha(OUT/'confirmation_matrix.json'),
        source_SHA=sha(__file__),facts=facts,independent_argv_reconstruction=True,nonimplementer_agent_review=False,Optimize=0))
    print(json.dumps(dict(admitted=True,arms=len(facts))),flush=True)

def arm(position):
    configure();matrix=read(OUT/'confirmation_matrix.json');gate=read(OUT/'review/confirmation_admission.json')
    assert gate['decision']=='ACCEPT' and gate['source_SHA']==sha(__file__) and gate['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
    g=matrix['groups'][int(position)-1];camp=OUT/g['group'];assert sha(camp/'identity.json')==g['identity_SHA']
    execute(g['launch'],read(camp/'identity.json'))

def one(position):
    position=int(position);g=read(OUT/'confirmation_matrix.json')['groups'][position-1]
    write(OUT/'active_position.json',dict(UTC=utc(),position=position,arm_id=g['launch']['arm_id']))
    run(f'confirmation_{position:03}',g['launch']['cap_seconds']+900,'round156_campaign.py',['arm',str(position)],kind='native')

def panel():
    for position in range(1,10):one(position)
    write(OUT/'panel_completion.json',dict(UTC=utc(),completed=9,budget=budget()))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
