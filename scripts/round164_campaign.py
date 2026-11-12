"""Seed-parameterized, serial B/P lifecycles over the immutable R163 inputs."""
from round164_common import *
import copy, dataclasses, types

inherited=legacy_import('round133_campaign')
base_reader=legacy_import('round137_read')
finish_producer=legacy_import('round121_campaign').finish_producer
COMMON=legacy_import('round122_prepare').COMMON
OFF={'--round146-gd':'off','--round148-shared-s':'off','--round149-penalty-feedback':'off',
     '--round151-penalty-propagation':'off','--round153-root-floor':'off','--round154-proof-floor':'off',
     '--round156-rn-refinement':'off','--round143-rn':'off','--round144-projection':'off',
     '--round145-projection':'off','--round140-counts':'off','--round141-count-proof':'off',
     '--round142-count-products':'off','--round160-physical-neighborhood':'off','--round162-physical-completion':'off'}

@dataclasses.dataclass(frozen=True)
class Arm:
    input_id: str
    method: str
    gurobi_seed: int
    repeat: int = 1

    def __post_init__(self):
        assert self.method in ('B','P') and type(self.gurobi_seed) is int and self.gurobi_seed in (1,2)
        assert self.repeat==1

def tokens(command):
    result={};i=1
    while i<len(command):
        flag=command[i];assert flag.startswith('--') and flag not in result,('duplicate/invalid flag',flag)
        if flag=='--plain-baseline':result[flag]=True;i+=1
        else:
            assert i+1<len(command) and not command[i+1].startswith('--'),('missing value',flag)
            result[flag]=command[i+1];i+=2
    return result

def command(p,arm,destination):
    assert arm.input_id==p['id']
    frozen=read(OUT/'method_freeze.json')
    values=dict(exe=str(PE),input=str(ROOT/p['input_path']),T=str(p['T_seconds']),
        **{'lambda':format(p['lambda'],'.17g')},pickup_time='60',drop_time='60',native_limit=str(p['cap_seconds']-6),
        cap=str(p['cap_seconds']),seed=str(arm.gurobi_seed),result=str(destination/'result.json'),
        log=str(destination/'native.log'),phases=str(destination/'phases.csv'),external=str(destination/'external'),
        hga=str(destination/'hga.csv'),progress=str(destination/'progress.csv'),journal=str(destination/'journal'),
        destination=str(destination),fingerprint=str(p['reference']['fingerprint']),PE_SHA=PE_SHA)
    template=frozen['B']['argv'] if arm.method=='B' else frozen['P_template']
    result=[]
    for value in template:
        for key,v in values.items():value=value.replace('${'+key+'}',v)
        assert '${' not in value,value
        result.append(value)
    existing=tokens(result)
    for flag,value in OFF.items():
        if flag in existing:assert existing[flag]==value,('template unexpectedly enables a mechanism',flag)
        else:result.extend([flag,value])
    actual=tokens(result)
    assert actual['--gurobi-seed']==str(arm.gurobi_seed)
    assert '--round112-ens-start-compact' not in actual and '--round138-stock-rlt' not in actual
    assert actual['--method']==('gcap-frontier' if arm.method=='B' else 'gurobi')
    assert actual['--round127-mode']==('ms2' if arm.method=='B' else 'p')
    assert ('--plain-baseline' in actual)==(arm.method=='P')
    assert ('--algorithm-preset' in actual)==(arm.method=='B')
    assert actual['--threads']==actual['--mip-threads']=='1'
    assert all(actual[flag]==value for flag,value in OFF.items())
    return result

def make(p,arm,camp,position):
    candidate=read(OUT/'candidate_manifest.json');panel=copy.deepcopy(p)
    panel.update(gurobi_seed=arm.gurobi_seed,round138_stock_rlt=False,round146_gd=False,
        round149_penalty_feedback=False,round151_penalty_propagation=False,
        round154_method='B',round156_method=arm.method,exposed=True)
    armid=f'R164_{position:03}_{arm.input_id}_S{arm.gurobi_seed}_{arm.method}'
    d=camp/'raw'/armid
    launch=dict(number=1,group_number=position,global_launch_number=position,id=arm.input_id,
        arm='M-B' if arm.method=='B' else 'P-GRB',method='S2' if arm.method=='B' else 'P',
        R164_method=arm.method,R147_method='BASE',R154_method='B',R156_method=arm.method,
        seed=arm.gurobi_seed,gurobi_seed=arm.gurobi_seed,repeat=arm.repeat,arm_spec=dataclasses.asdict(arm),
        binary_layer='R164-common-R163-R162-PE',version='candidate',panel=panel,panel_kind=panel['panel_kind'],
        destination=str(d),command=command(panel,arm,d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,
        configuration=dict(id='q0',MIPFocus=0,Cuts=-1),arm_id=armid,stage='Round164',AM_threshold=.08)
    identity=dict(schema='round164-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=arm.gurobi_seed),
        candidate_binary=str(PE),candidate_binary_sha256=PE_SHA),prereg_sha256=sha(OUT/'protocol.json'),
        runner_sha256=sha(__file__),source_hashes=candidate['source_hashes'],candidate_binary_sha256=PE_SHA,
        dll_sha256=DLL_SHA,measured_source_commit=MEASURED_CPP,delivery_base_commit=BASE,launches=[launch],
        references={arm.input_id:p['reference']},candidate_manifest_path=str(OUT/'candidate_manifest.json'),
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),stage='Round164',
        input_manifest_SHA=INPUT_MANIFEST_SHA,no_cross_arm_information=True,H_seed=20260626,
        authoritative_arm=dataclasses.asdict(arm),Eplus=False)
    camp.mkdir(parents=True,exist_ok=False);ref=camp/'reference'/arm.input_id;ref.mkdir(parents=True)
    for name in ['build.json','original.lp']:(ref/name).hardlink_to(OUT/'qualification/references'/arm.input_id/name)
    write(camp/'identity.json',identity)
    return launch,identity

def seed_readback(launch):
    d=Path(launch['destination']);expected=launch['arm_spec']['gurobi_seed']
    assert launch['seed']==launch['gurobi_seed']==launch['panel']['gurobi_seed']==expected
    assert tokens(launch['command'])['--gurobi-seed']==str(expected)
    calls=[r['payload'] for r in read(d/'observations.json') if r['payload']['kind']=='call']
    facts=[]
    for call in calls:
        settings=call['settings'];assert settings['read_return_code']==0
        for name,value in dict(Threads=1,Seed=expected,Presolve=-1,MIPFocus=0,Cuts=-1,MIPGap=0,MIPGapAbs=0).items():
            assert settings[name]==value,(launch['arm_id'],name,settings)
            assert settings['expected'][name]==value
        facts.append(dict(call=call.get('call'),model_SHA=call.get('model_sha256'),settings=settings))
    assert calls,'qualification requires a real Native call'
    return dict(PASS=True,expected_seed=expected,Native_calls=len(calls),all_native_call_settings=facts,
        unchanged_H_seed=20260626,producer_parameters_not_projected=True)

def verify(launch,identity):
    d=Path(launch['destination']);actual=seed_readback(launch)
    fn=types.FunctionType(base_reader.verify.__code__,dict(vars(base_reader),ROOT=ROOT,OUT=OUT,configure=configure))
    value=fn(launch,identity)
    for name in ['round138_parameters.json','round146_parameters.json','round148_parameters.json',
                 'round149_parameters.json','round151_parameters.json','round153_parameters.json',
                 'round160_parameters.json','round162_parameters.json']:
        assert not (d/name).exists(),('noncandidate mechanism active',name)
    assert not (d/'round160').exists() and not (d/'external/round162').exists()
    if launch['R164_method']=='P':
        assert read(d/'round127_parameters.json')==dict(MIPFocus=0,Cuts=-1,
            NumStart_before_optimize=0,loaded_after_presets=True,authoritative_model_environment=True)
    arm=value['arm'];arm.update(R164_method=launch['R164_method'],gurobi_seed=launch['seed'],repeat=1,
        raw_search_L=arm['L'],qualified_search_L=arm['L'],final_proof_L=arm['L'],
        state='CERT' if arm['certificate'] else 'OPEN',exposed=True,
        panel_kind='R163 cohort finite solver-seed confirmation')
    assert all(arm[key] for key in ['performance_eligible','implementation_qualified','evidence_complete'])
    write(d/'round164_seed_audit.json',actual);write(d/'round164_endpoint.json',arm)
    return value

def execute(launch,identity):
    d=Path(launch['destination']);assert not (d/'verification_closeout.json').exists()
    assert identity['prereg']['common']['gurobi_seed']==launch['seed']
    if not d.exists():
        tick,creation=inherited.inherited.process_origin()
        from round100_idle import ensure_idle
        def idle():ensure_idle();return []
        supervisor=types.SimpleNamespace(**dict(vars(inherited.supervisor),foreign_heavy_processes=idle))
        fn=types.FunctionType(inherited.supervised.__code__,dict(vars(inherited),ROOT=ROOT,OUT=OUT,supervisor=supervisor))
        fn(launch,identity,tick);finish_producer(launch,tick,creation)
    else:
        assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(), 'inspect original process; no automatic rerun'
    value=verify(launch,identity)
    if launch['group_number']:
        write(OUT/'runtime_status.json',dict(UTC=utc(),position=launch['group_number'],arm=value['arm']))
    print(json.dumps(value['arm']),flush=True)
    return value

def freeze():
    assert not (OUT/'matrix_frozen.json').exists()
    assert read(OUT/'qualification/result.json')['PASS']
    groups=[]
    for row_number,p in enumerate(read(OUT/'input_references.json')['roles'],1):
        p=dict(p,reference=read(OUT/'qualification/references'/p['id']/'build.json'))
        orders={1:['B','P'],2:['P','B']} if row_number%2 else {1:['P','B'],2:['B','P']}
        for seed in (1,2):
            for method in orders[seed]:
                arm=Arm(p['id'],method,seed);position=len(groups)+1;camp=OUT/'campaign'/f'{position:03}'
                launch,identity=make(p,arm,camp,position)
                groups.append(dict(position=position,arm=dataclasses.asdict(arm),group=camp.relative_to(OUT).as_posix(),
                    launch=launch,identity_SHA256=sha(camp/'identity.json')))
    assert len(groups)==24 and sum(g['launch']['cap_seconds'] for g in groups)==43200
    assert len({(g['arm']['input_id'],g['arm']['gurobi_seed']) for g in groups})==12
    helpers=inherited.helper_bindings()
    for name in ['scripts/round164_common.py','scripts/round164_campaign.py']:helpers[name]=sha(ROOT/name)
    write(OUT/'matrix_frozen.json',dict(UTC=utc(),groups=groups,helpers=helpers,full_arm_count=24,
        full_arm_cap_sum_seconds=43200,scientific_reservation_seconds=50400,outer_fault_timeout_margin_seconds=900,
        candidate_manifest_SHA256=sha(OUT/'candidate_manifest.json'),input_manifest_SHA256=INPUT_MANIFEST_SHA,
        input_references_SHA256=sha(OUT/'input_references.json'),method_freeze_SHA256=sha(OUT/'method_freeze.json'),
        protocol_SHA256=sha(OUT/'protocol.json'),primal_targets_SHA256=sha(OUT/'primal_targets_frozen.json'),
        qualification_SHA256=sha(OUT/'qualification/result.json'),serial=True,affinity_mask=4,Gurobi_Seeds=[1,2],
        Threads=1,MIPThreads=1,H_seed=20260626,Native_NodeLimit='unlimited',one_total_deadline=True,
        no_adverse_result_early_stop=True,no_free_cross_arm_information=True))
    print('All 24 B/P positions frozen. Commit before first formal production.')

def admission():
    matrix=read(OUT/'matrix_frozen.json')
    pinned=json.loads(git('show','HEAD:results/unified_exact_round164/matrix_frozen.json'))
    assert pinned==matrix
    for name,key in [('candidate_manifest.json','candidate_manifest_SHA256'),('input_references.json','input_references_SHA256'),
        ('method_freeze.json','method_freeze_SHA256'),('protocol.json','protocol_SHA256'),
        ('primal_targets_frozen.json','primal_targets_SHA256'),('qualification/result.json','qualification_SHA256')]:
        assert sha(OUT/name)==matrix[key],name
    assert sha(INPUT_MANIFEST)==INPUT_MANIFEST_SHA and sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
    for group in matrix['groups']:
        launch=group['launch'];assert sha(OUT/group['group']/'identity.json')==group['identity_SHA256']
        assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
        arm=Arm(**group['arm']);assert launch['command']==command(launch['panel'],arm,Path(launch['destination']))
    return matrix

def arm(position):
    group=admission()['groups'][int(position)-1]
    execute(group['launch'],read(OUT/group['group']/'identity.json'))

def panel():
    groups=admission()['groups']
    for group in groups:
        launch=group['launch'];d=Path(launch['destination'])
        if (d/'round164_endpoint.json').exists():continue
        label=f'arm_{group["position"]:03}'
        assert not (OUT/'fees'/label).exists(),'inspect failed/incomplete receipt; never automatically repeat producer'
        before=budget();future=sum(g['launch']['cap_seconds']+300 for g in groups if g['position']>=group['position'])
        assert before['remaining_G1_seconds']>=future,('insufficient total reservation; preserve missing positions',before,future)
        write(OUT/'active_position.json',dict(UTC=utc(),position=group['position'],arm_id=launch['arm_id'],
            gurobi_seed=group['arm']['gurobi_seed'],fee_label=label))
        result=metered(label,'panel',[PYTHON,'-B',ROOT/'scripts/round164_campaign.py','arm',group['position']],
            reservation=launch['cap_seconds']+300,fault_timeout=launch['cap_seconds']+900)
        assert result==0,('preserved technical failure; repair only affected position',label,result)
    write(OUT/'panel_complete.json',dict(UTC=utc(),arms=24,new_pairs=12,inputs=6,budget=budget()))

if __name__=='__main__':
    if sys.argv[1]=='arm':arm(sys.argv[2])
    else:globals()[sys.argv[1]]()
