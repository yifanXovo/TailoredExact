"""R160's own eight-position matrix/admission/serial loop. Never runs old freeze."""
import copy,inspect,types,importlib,re
from round160_common import *

def legacy_import(name):
    """Recover only missing thin fixed-Git metadata needed by old imports."""
    for attempt in range(30):
        try:return importlib.import_module(name)
        except FileNotFoundError as error:
            path=Path(error.filename).resolve();relative=path.relative_to(ROOT.resolve())
            parts=relative.parts
            assert len(parts)>=3 and parts[0]=='results'
            match=re.fullmatch(r'unified_exact_round(\d+)',parts[1])
            assert match and int(match[1])<160 and path.suffix in ('.json','.md','.csv'),relative
            raw=git('show',BASE+':'+relative.as_posix());assert len(raw)<5000000
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            receipt=OUT/'infra/legacy_import_metadata.json'
            records=read(receipt) if receipt.exists() else []
            records.append(dict(path=relative.as_posix(),commit=BASE,SHA256=sha(path),bytes=len(raw),
                                reason='minimal read-only import metadata; no old producer/solver'))
            write(receipt,records)
    raise RuntimeError('bounded legacy metadata recovery exhausted')

inherited=legacy_import('round133_campaign')
proof_reader=legacy_import('round154_read')
producer_reader=legacy_import('round156_read')
finish_producer=legacy_import('round121_campaign').finish_producer
COMMON=legacy_import('round122_prepare').COMMON

SPECS=[('R-X35-S-T2','Eplus',7200),('R-X35-S-T2','EplusR',7200),
       ('N-B35-S','Eplus',2400),('N-B35-S','EplusR',2400),
       ('K-20-S','Eplus',1200),('K-20-S','EplusR',1200),
       ('R-X20-S-T1','Eplus',1200),('R-X20-S-T1','EplusR',1200)]
OUTPUTS={'--out','--log','--process-phase-ledger','--external-gini-artifact-dir',
         '--primal-heuristic-generation-log','--progress-log','--native-evidence-dir'}

def prior_launch(role):
    matrix=json.loads(git('show',BASE+':results/unified_exact_round137/matrix_frozen.json'))
    return next(g['launch'] for g in matrix['groups'] if g['launch']['id']==role and g['launch']['method']=='S2' and g['launch']['seed']==0)

def arguments(method):
    helper=ROOT/'scripts/round156_online.py';manifest=OUT/'helper_manifest_Eplus.json'
    return ['--round146-gd','off','--round149-penalty-feedback','off','--round151-penalty-propagation','off',
        '--round153-root-floor','on','--round154-proof-floor','on','--round156-rn-refinement','on',
        '--round153-python',str(PYTHON),'--round153-helper',str(helper),'--round153-helper-sha',sha(helper),
        '--round153-manifest',str(manifest),'--round153-manifest-sha',sha(manifest),
        '--round160-physical-neighborhood','on' if method=='EplusR' else 'off']

def make(role,method,camp,index,cap):
    manifest=read(OUT/'candidate_manifest.json');old=prior_launch(role);launch=copy.deepcopy(old)
    panel=launch['panel'];folder=OUT/'inputs'/role;folder.mkdir(parents=True,exist_ok=True)
    path=folder/'instance.txt'
    if not path.exists():path.write_bytes(git('show',BASE+':'+panel['input_path']))
    assert sha(path)==panel['input_sha256']
    panel.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),
        cap_seconds=cap,gurobi_seed=0,round154_method='E',round156_method='Eplus',round160_method=method,
        round138_stock_rlt=False,round146_gd=False,round149_penalty_feedback=False,known=True,exposed=True,
        panel_kind='Round160 fresh paid complete Eplus / EplusR')
    armid=f'R160_{index:03}_{role}_S0_{method}';destination=camp/'raw'/armid
    command=[v.replace(old['destination'],str(destination)) for v in old['command']];command[0]=manifest['production_PE']
    for flag,value in [('--input',str(path)),('--time-limit',str(cap-6)),('--process-wall-time-limit',str(cap))]:
        command[command.index(flag)+1]=value
    command+=arguments(method)
    launch.update(number=1,group_number=index,global_launch_number=index,method='E',R147_method='BASE',R154_method='E',
        R156_method='Eplus',R160_method=method,seed=0,binary_layer='R160-same-PE',version='candidate',
        panel=panel,panel_kind=panel['panel_kind'],destination=str(destination),command=command,arm_id=armid,
        stage='confirmation',AM_threshold=.08,cap_seconds=cap,hard_stop_seconds=cap-2)
    identity=dict(schema='round160-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=0),
        candidate_binary=manifest['production_PE'],candidate_binary_sha256=manifest['production_PE_SHA']),
        prereg_sha256=sha(OUT/'candidate_decision.json'),runner_sha256=sha(__file__),source_hashes=manifest['source_hashes'],
        candidate_binary_sha256=manifest['production_PE_SHA'],dll_sha256=DLL_SHA,measured_source_commit=manifest['source_commit'],
        delivery_base_commit=BASE,launches=[launch],candidate_manifest_path=str(OUT/'candidate_manifest.json'),
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),stage='confirmation',no_cross_arm_information=True,
        helper_manifest_SHA=sha(OUT/'helper_manifest_Eplus.json'),original_frozen_launch=old,
        original_fixed_science='e735c3447eb1443713c700942d873de1783a4a26',inventory_node_limit=16384,
        inventory_helper_entry='scripts/round156_online.py',R160_method=method)
    write(camp/'identity.json',identity);return launch,identity

def floor_contract(destination,enabled,launch,identity):
    fn=types.FunctionType(producer_reader.floor_contract.__code__,dict(vars(producer_reader),ROOT=ROOT,OUT=OUT,configure=configure))
    return fn(destination,enabled,launch,identity)

def verify(launch,identity):
    destination=Path(launch['destination']);extra={}
    path=destination/'round160'
    if launch['R160_method']=='EplusR':
        assert path.exists()
        initial=read(path/'initial.json');final=read(path/'final.json');summary=read(path/'summary.json')
        from round160_prepare import data
        from round157_fleet import verify as physical
        d=data(launch['panel'],ROOT/launch['panel']['input_path'])
        assert physical(d,initial)['original_T_feasible'] and physical(d,final)['original_T_feasible']
        assert final['J']<=initial['J'] and summary['global_proof_changes']==0
        assert summary['nodes_per_block']==512 and summary['passes']==1
        raw=read(destination/'hga.csv.exchange/final.json')
        assert abs(raw['F']-initial['J'])<1e-12
        assert [r['nodes'] for r in raw['routes']]==[r['nodes'] for r in initial['routes']]
        scope_start=read(destination/'external/initial_witness.json')
        assert abs(scope_start['objective']-final['J'])<1e-12
        assert [r['nodes'] for r in scope_start['routes']]==[r['nodes'] for r in final['routes']]
        extra.update(local_parent_J=initial['J'],local_final_J=final['J'],local_seconds=summary['seconds'],
            local_calls=summary['calls'],local_accepted=summary['accepted'])
    else:assert not path.exists()
    # New inlet audit precedes the inherited closeout, so its actual elapsed
    # time belongs to that arm's T_verify / T_total, as well as the outer fee.
    fn=types.FunctionType(proof_reader.verify.__code__,dict(vars(proof_reader),ROOT=ROOT,OUT=OUT,configure=configure,floor_contract=floor_contract))
    base_reader=legacy_import('round135_read');original_verify=base_reader.verify
    if launch['R160_method']=='EplusR':
        source=inspect.getsource(original_verify)
        needle="assert len(initial)==1 and startup.fleet_key(p,initial[0]['routes'])==H['fleet']"
        assert source.count(needle)==1
        replacement="""assert len(initial)==1
            assert startup.fleet_key(p,read(d/'round160/initial.json')['routes'])==H['fleet']
            assert startup.fleet_key(p,initial[0]['routes'])==startup.fleet_key(p,read(d/'round160/final.json')['routes'])"""
        source=source.replace(needle,replacement)
        namespace=dict(vars(base_reader));filename=destination/'round160_inlet_reader.py.txt'
        filename.write_text(source,encoding='utf8');exec(compile(source,str(filename),'exec'),namespace)
        base_reader.verify=namespace['verify']
    try:value=fn(launch,identity)
    finally:base_reader.verify=original_verify
    value['arm'].update(R160_method=launch['R160_method'],**extra)
    write(destination/'round160_endpoint.json',value['arm']);return value

def execute(launch,identity):
    configure();destination=Path(launch['destination'])
    assert not (destination/'verification_closeout.json').exists()
    if not destination.exists():
        tick,creation=inherited.inherited.process_origin()
        from round100_idle import ensure_idle
        def idle():ensure_idle();return []
        supervisor=types.SimpleNamespace(**dict(vars(inherited.supervisor),foreign_heavy_processes=idle))
        supervised=types.FunctionType(inherited.supervised.__code__,dict(vars(inherited),supervisor=supervisor))
        supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (destination/'producer_receipt.json').exists() and (destination/'producer_seal.json').exists()
    value=verify(launch,identity);write(OUT/'runtime_status.json',dict(UTC=utc(),arm_id=launch['arm_id'],arm=value['arm']))
    print(json.dumps(value['arm']),flush=True);return value

def smoke(method):
    camp=OUT/'qualification'/('launch_'+method);camp.mkdir(parents=True,exist_ok=False)
    launch,identity=make('R-X20-S-T1',method,camp,0,120)
    result=execute(launch,identity)
    write(camp/'result.json',dict(PASS=True,not_performance_sample=True,arm=result['arm']))

def reverify_smoke(method):
    camp=OUT/'qualification'/('launch_'+method);identity=read(camp/'identity.json')
    launch=identity['launches'][0];assert (Path(launch['destination'])/'producer_seal.json').exists()
    result=execute(launch,identity)
    write(camp/'result.json',dict(PASS=True,not_performance_sample=True,readback_recovery_only=True,
        new_Native_producer_runs=0,arm=result['arm']))

def freeze():
    configure()
    assert all(p['label']==os.environ.get('ROUND140_METERED_PARENT_LABEL') for p in budget()['unclosed'])
    assert not (OUT/'confirmation_matrix.json').exists()
    for method in ('Eplus','EplusR'):assert read(OUT/'qualification'/('launch_'+method)/'result.json')['PASS']
    groups=[]
    for index,(role,method,cap) in enumerate(SPECS,1):
        camp=OUT/'campaign_confirmation'/f'{index:03}';camp.mkdir(parents=True,exist_ok=False)
        launch,identity=make(role,method,camp,index,cap)
        groups.append(dict(position=index,group=camp.relative_to(OUT).as_posix(),launch=launch,identity_SHA=sha(camp/'identity.json')))
    helpers=read(OUT/'helper_manifest_Eplus.json')['helper_dependencies']
    for name in ('round160_campaign.py','round160_common.py','round156_read.py','round154_read.py','round153_read.py'):
        helpers['scripts/'+name]=sha(ROOT/'scripts'/name)
    write(OUT/'confirmation_matrix.json',dict(UTC=utc(),groups=groups,helpers=helpers,Seed=0,Threads=1,H_seed=20260626,
        nominal_complete_seconds=sum(s[2] for s in SPECS),reservation_with_900_each=31200,serial=True,
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),helper_manifest_SHA=sha(OUT/'helper_manifest_Eplus.json'),
        candidate_decision_SHA=sha(OUT/'candidate_decision.json'),no_free_historical_or_cross_arm_information=True))

def admit():
    m=read(OUT/'confirmation_matrix.json');assert len(m['groups'])==8 and m['nominal_complete_seconds']==24000
    hashes={'R-X35-S-T2':'c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2',
            'N-B35-S':'80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98',
            'K-20-S':'d1a65be4b87dead2ae351068ece3c3ce486a51c93652d778e055f2684606ea42',
            'R-X20-S-T1':'2b467b5bb1e650a4c1e792e808dcf9575bcc76752fe378e16c838015344ddac6'}
    facts=[]
    for g in m['groups']:
        l=g['launch'];cmd=dict(zip(l['command'][1::2],l['command'][2::2]))
        assert 2*len(cmd)+1==len(l['command'])
        assert sha(cmd['--input'])==hashes[l['id']]==l['panel']['input_sha256']
        assert float(cmd['--process-wall-time-limit'])==l['cap_seconds'] and float(cmd['--time-limit'])==l['cap_seconds']-6
        assert cmd['--round160-physical-neighborhood']==('on' if l['R160_method']=='EplusR' else 'off')
        assert cmd['--round156-rn-refinement']==cmd['--round154-proof-floor']=='on'
        assert all(Path(cmd[f]).resolve().is_relative_to(OUT.resolve()) for f in OUTPUTS)
        assert sha(OUT/g['group']/'identity.json')==g['identity_SHA'] and not Path(l['destination']).exists()
        facts.append(dict(position=g['position'],role=l['id'],method=l['R160_method'],cap=l['cap_seconds']))
    assert budget()['remaining_G1_seconds']>=m['reservation_with_900_each']+10800
    write(OUT/'review/confirmation_admission.json',dict(PASS=True,matrix_SHA=sha(OUT/'confirmation_matrix.json'),
        facts=facts,own_eight_arm_adapter=True,old_freeze_not_called=True,source_SHA=sha(__file__),Optimize=0))

def arm(position):
    configure();m=read(OUT/'confirmation_matrix.json');a=read(OUT/'review/confirmation_admission.json')
    assert a['PASS'] and a['source_SHA']==sha(__file__) and a['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    assert sha(OUT/'candidate_manifest.json')==m['candidate_manifest_SHA'] and sha(OUT/'helper_manifest_Eplus.json')==m['helper_manifest_SHA']
    for name,h in m['helpers'].items():assert sha(ROOT/name)==h,name
    g=m['groups'][int(position)-1];execute(g['launch'],read(OUT/g['group']/'identity.json'))

def panel():
    configure();m=read(OUT/'confirmation_matrix.json')
    for g in m['groups']:
        pos=g['position'];destination=Path(g['launch']['destination'])
        if (destination/'round160_endpoint.json').exists():continue
        assert not (OUT/'fees'/f'confirmation_{pos:03}').exists(),'inspect original incomplete attempt'
        write(OUT/'active_position.json',dict(UTC=utc(),position=pos,arm_id=g['launch']['arm_id']))
        run(f'confirmation_{pos:03}',g['launch']['cap_seconds']+900,'round160_campaign.py',['arm',str(pos)],kind='native')
    write(OUT/'panel_completion.json',dict(UTC=utc(),completed=8,budget=budget()))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
