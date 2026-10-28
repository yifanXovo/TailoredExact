"""At most two result-selected roles, fresh paired complete Seed1 runs."""
from round138_common import *
import copy,csv,types,zipfile
import round138_campaign as primary
from round138_scaled_read import verify
import round108_reader as core

def prepare():
    assert not budget()['unclosed'] and read(OUT/'reports/full.json')['complete']
    assert not (OUT/'seed1_matrix_frozen.json').exists()
    selection=read(OUT/'seed1_selection.json');roles=selection['roles'];assert 1<=len(roles)<=2 and len(set(roles))==len(roles)
    matrix=read(OUT/'matrix_frozen.json');old=read(ROOT/'results/unified_exact_round137/candidate_manifest.json')
    candidate=read(OUT/'candidate_repair_manifest.json');base_template=matrix['groups'][0]['launch'];assert base_template['method']=='BASE'
    assert read(OUT/'repair/primary_native_bridge.json')['PASS'] and read(OUT/'qualification/native_coefficients.json')['PASS']
    groups=[]
    for j,role in enumerate(roles):
        chosen=next(g['launch'] for g in matrix['groups'] if g['launch']['id']==role and g['launch']['method']=='STOCK')
        methods=['BASE','STOCK'] if j%2==0 else ['STOCK','BASE']
        for method in methods:
            n=len(groups)+1;template=chosen if method=='STOCK' else base_template
            launch=copy.deepcopy(template);p=copy.deepcopy(chosen['panel']);p['gurobi_seed']=1;p['round138_stock_rlt']=method=='STOCK'
            camp=OUT/'campaign_seed1'/f'{n:03}';camp.mkdir(parents=True,exist_ok=False)
            armid=f'R138_S1_{n:03}_{role}_{method}';d=camp/'raw'/armid
            command=[x.replace(template['destination'],str(d)) for x in template['command']]
            command[0]=candidate['production_PE'] if method=='STOCK' else old['production_PE']
            def put(flag,value):command[command.index(flag)+1]=str(value)
            for flag,key in [('--input','input_path'),('--lambda','lambda'),('--T','T_seconds'),
                             ('--pickup-time','pickup_seconds'),('--drop-time','drop_seconds')]:put(flag,p[key])
            put('--gurobi-seed',1);put('--time-limit',p['cap_seconds']-6);put('--process-wall-time-limit',p['cap_seconds'])
            launch.update(id=role,method=method,seed=1,stage='limited-Seed1',panel=p,
                destination=str(d),command=command,arm_id=armid,number=1,group_number=n,
                global_launch_number=n,cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2)
            launch.update(binary_layer='R138-v2' if method=='STOCK' else 'R137',
                stock_row_transport='power-of-two-v2' if method=='STOCK' else 'baseline',
                producer_build_change_from_primary=method=='STOCK')
            sources=candidate if method=='STOCK' else old
            identity=dict(schema='round138-limited-own-complete-Seed1-v1',
                prereg=dict(common=dict(primary.COMMON,gurobi_seed=1),candidate_binary=command[0],candidate_binary_sha256=sha(command[0])),
                prereg_sha256=sha(OUT/'seed1_selection.json'),runner_sha256=sha(__file__),
                source_hashes=sources['source_hashes'],candidate_binary_sha256=sha(command[0]),dll_sha256=DLL_SHA,
                measured_source_commit=sources['source_commit'],delivery_base_commit=BASE,launches=[launch],
                stage='limited-Seed1',no_cross_arm_information=True,candidate_manifest_SHA=sha(OUT/'candidate_repair_manifest.json'))
            write(camp/'identity.json',identity)
            groups.append(dict(position=n,stage='limited-Seed1',group=camp.relative_to(OUT).as_posix(),
                identity_SHA=sha(camp/'identity.json'),arm_id=armid,launch=launch))
    assert len(groups)<=4
    write(OUT/'seed1_matrix_frozen.json',dict(UTC=utc(),groups=groups,
        selection_SHA=sha(OUT/'seed1_selection.json'),primary_matrix_SHA=sha(OUT/'matrix_frozen.json'),
        script_SHA=sha(__file__),candidate_manifest_SHA=sha(OUT/'candidate_repair_manifest.json'),
        candidate_manifest_path='results/unified_exact_round138/candidate_repair_manifest.json',
        reader_SHA=sha(ROOT/'scripts/round138_scaled_read.py'),repair_helper_SHA=sha(ROOT/'scripts/round138_repair.py'),
        primary_v1_native_bridge_SHA=sha(OUT/'repair/primary_native_bridge.json'),
        primary_v1_source_archive_record_SHA=sha(OUT/'repair/source_v1_archive.json'),
        Seed1_is_V2_build_confirmation_not_claimed_pure_Seed_only_change=True,
        caps_seconds=sum(g['launch']['cap_seconds'] for g in groups),source_and_PE_unchanged=True,
        serial=True,threads=1,affinity=4,Seed=1,H_seed=20260626,before_new_Seed1_Optimize=True))
    print('Limited paired Seed1 matrix frozen; independent admission remains required')

def admission():
    def historical_v1(path):
        assert Path(path).resolve()==(OUT/'candidate_manifest.json').resolve()
        record=read(OUT/'repair/source_v1_archive.json');old=read(path)
        assert record['manifest_SHA']==sha(path)
        carrier=ROOT/record['carrier']['path'];assert sha(carrier)==record['carrier']['SHA256']
        with zipfile.ZipFile(carrier) as z:
            for name,digest in old['source_hashes'].items():
                assert hashlib.sha256(z.read(name)).hexdigest()==digest==record['files'][name]
        for name in ['production','research']:assert sha(old[name+'_PE'])==old[name+'_PE_SHA']
        assert sha(old['DLL'])==old['DLL_SHA']==DLL_SHA
        return old
    # The original admission code and all helper gates remain intact. Only
    # historical V1 source adjudication uses its preserved exact-byte carrier;
    # the delivered V2 source is independently checked against current files.
    api=types.SimpleNamespace(**dict(vars(primary.inherited),_candidate=historical_v1))
    check=types.FunctionType(primary.admission.__code__,dict(vars(primary),inherited=api));check()
    primary.inherited._candidate(OUT/'candidate_repair_manifest.json')
    gate=read(OUT/'review/seed1_admission.json');m=read(OUT/'seed1_matrix_frozen.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(OUT/'seed1_matrix_frozen.json')
    assert m['selection_SHA']==sha(OUT/'seed1_selection.json') and m['script_SHA']==sha(__file__)
    assert m['candidate_manifest_SHA']==sha(OUT/'candidate_repair_manifest.json')
    assert m['reader_SHA']==sha(ROOT/'scripts/round138_scaled_read.py') and m['repair_helper_SHA']==sha(ROOT/'scripts/round138_repair.py')
    assert m['primary_v1_native_bridge_SHA']==sha(OUT/'repair/primary_native_bridge.json')
    assert m['primary_v1_source_archive_record_SHA']==sha(OUT/'repair/source_v1_archive.json')
    return m

def arm(position,label):
    # Identical producer/reader/clock path; only the admitted manifest lookup differs.
    run=types.FunctionType(primary.arm.__code__,dict(vars(primary),admission=admission,verify=verify))
    return run(position,label)

def run():
    for g in admission()['groups']:
        if (Path(g['launch']['destination'])/'verification_closeout.json').exists():continue
        label=f'seed1_arm_{g["position"]:03}'
        assert not (OUT/'fees'/label).exists(),'Inspect sealed or running prior attempt; never duplicate native work'
        write(OUT/'active_position.json',dict(UTC=utc(),stage='limited-Seed1',position=g['position'],arm_id=g['arm_id'],fee_label=label))
        assert metered(label,'native',[PYTHON,ROOT/'scripts/round138_seed1.py','arm',g['position'],label],
            reservation=g['launch']['cap_seconds'],timeout=g['launch']['cap_seconds']+1800)==0

def summary():
    assert not budget()['unclosed'];arms=[]
    m=read(OUT/'seed1_matrix_frozen.json')
    for g in m['groups']:
        l=g['launch'];p=l['panel'];d=Path(l['destination']);e=read(d/'round135_endpoint.json');a=read(d/'audit.json')
        assert read(d/'verification_closeout.json')['evidence_complete']
        data=core.evidence.instance(ROOT,p);Y=a['physical']['Y'];omega=math.fsum(data['w'][1:])
        arms.append(dict(role=l['id'],method=l['method'],seed=1,certificate=e['certificate'],
            T_cert=e['T_cert'],T_produce=e['T_produce'],T_verify=e['T_verify'],T_total=e['T_total'],
            U=e['U'],L=e['L'],signed_gap=e['U']-e['L'],relative_gap=e['relative_gap'],
            G=a['physical']['G'],P_avg=a['physical']['P']/omega,S=math.fsum(Y[i]/data['D'][i] for i in range(1,p['V']+1)),
            cap=p['cap_seconds'],lambda_value=p['lambda'],T=p['T_seconds'],input_SHA=p['input_sha256'],
            PE_SHA=sha(l['command'][0]),source_commit=read(OUT/g['group']/'identity.json')['measured_source_commit'],
            performance_eligible=e['performance_eligible'],native_proof_qualified=e['native_proof_qualified'],
            H_complete=e['H_complete'],audit_SHA=sha(d/'audit.json'),endpoint_SHA=sha(d/'round135_endpoint.json')))
    selection=read(OUT/'seed1_selection.json')
    write(OUT/'reports/seed1.json',dict(UTC=utc(),arms=arms,selection_rationale=selection['rationale'],
        discussion='This is a finite conditional second-Seed check selected after the recorded Seed0 outcomes. STOCK uses the separately registered V2 coefficient-transport repair build; primary V1 model scopes were exactly bridged and none entered the changed tiny-slope branch. This is not concealed as a pure Seed-only build comparison. Both methods pay independent complete costs; no favorable repeat replaces Seed0. It does not estimate a runtime distribution or create an independent validation set.',
        matrix_SHA=sha(OUT/'seed1_matrix_frozen.json'),budget=budget(),Optimize=0,
        Optimize_field_scope='Pure summary only; complete source solves are charged in fees'))
    from round138_analyze import csv_write
    csv_write(OUT/'reports/seed1.csv',arms)
    print(json.dumps(arms))

if __name__=='__main__':
    if sys.argv[1]=='arm':arm(int(sys.argv[2]),sys.argv[3])
    else:globals()[sys.argv[1]]()
