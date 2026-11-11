"""Generic manifest-driven serial B/E+/cold-P launcher; never runs old panels."""
from round163_common import *
import copy, types

inherited=legacy_import('round133_campaign')
base_reader=legacy_import('round137_read')
plus_reader=legacy_import('round156_read')
finish_producer=legacy_import('round121_campaign').finish_producer
COMMON=legacy_import('round122_prepare').COMMON
OFF={'--round146-gd':'off','--round148-shared-s':'off','--round149-penalty-feedback':'off',
     '--round151-penalty-propagation':'off','--round153-root-floor':'off','--round154-proof-floor':'off',
     '--round156-rn-refinement':'off','--round143-rn':'off','--round144-projection':'off',
     '--round145-projection':'off','--round140-counts':'off','--round141-count-proof':'off',
     '--round142-count-products':'off','--round160-physical-neighborhood':'off','--round162-physical-completion':'off'}
SINGLE={'--plain-baseline'}

def tokens(command):
    result={};i=1
    while i<len(command):
        flag=command[i];assert flag.startswith('--') and flag not in result, ('duplicate/invalid flag',flag)
        if flag in SINGLE:result[flag]=True;i+=1
        else:
            assert i+1<len(command) and not command[i+1].startswith('--'), ('missing value',flag)
            result[flag]=command[i+1];i+=2
    return result

def command(p,method,destination):
    frozen=read(OUT/'method_freeze.json')
    values=dict(exe=str(PE),input=str(ROOT/p['input_path']),T=str(p['T_seconds']),
        **{'lambda':format(p['lambda'],'.17g')},pickup_time='60',drop_time='60',native_limit=str(p['cap_seconds']-6),
        cap=str(p['cap_seconds']),seed='0',result=str(destination/'result.json'),log=str(destination/'native.log'),
        phases=str(destination/'phases.csv'),external=str(destination/'external'),hga=str(destination/'hga.csv'),
        progress=str(destination/'progress.csv'),journal=str(destination/'journal'),destination=str(destination),
        fingerprint=str(p['reference']['fingerprint']),PE_SHA=PE_SHA)
    template=frozen['P_template'] if method=='P' else frozen['B' if method=='B' else 'Eplus']['argv']
    result=[]
    for value in template:
        for k,v in values.items():value=value.replace('${'+k+'}',v)
        assert '${' not in value,value
        result.append(value)
    existing=tokens(result)
    # Modify only each method's own clean template. Never derive P from E+.
    explicit=dict(OFF)
    if method=='Eplus':
        explicit.update({'--round153-root-floor':'on','--round154-proof-floor':'on','--round156-rn-refinement':'on',
            '--round153-python':str(PYTHON),'--round153-helper':str(ROOT/'scripts/round156_online.py'),
            '--round153-helper-sha':sha(ROOT/'scripts/round156_online.py'),
            '--round153-manifest':str(OUT/'helper_manifest_Eplus.json'),'--round153-manifest-sha':sha(OUT/'helper_manifest_Eplus.json')})
    for flag,value in explicit.items():
        if flag in existing:result[result.index(flag)+1]=value
        else:result.extend([flag,value])
    actual=tokens(result)
    assert '--round138-stock-rlt' not in actual and '--round112-ens-start-compact' not in actual
    assert actual['--method']==('gurobi' if method=='P' else 'gcap-frontier')
    assert actual['--round127-mode']==('p' if method=='P' else 'ms2')
    assert ('--plain-baseline' in actual)==(method=='P')
    assert ('--algorithm-preset' in actual)==(method!='P')
    assert all(actual[f]==v for f,v in explicit.items())
    return result

def make(p,method,camp,position):
    m=read(OUT/'candidate_manifest.json');panel=copy.deepcopy(p)
    panel.update(round138_stock_rlt=False,round146_gd=False,round149_penalty_feedback=False,
        round151_penalty_propagation=False,round154_method='E' if method=='Eplus' else 'B',round156_method=method)
    role=p['id'];armid=f'R163_{position:03}_{role}_S0_{method}';d=camp/'raw'/armid
    launch=dict(number=1,group_number=position,global_launch_number=position,id=role,
        arm='P-GRB' if method=='P' else 'M-B',method='P' if method=='P' else 'S2',R163_method=method,
        R147_method='BASE',R154_method='E' if method=='Eplus' else 'B',R156_method=method,seed=0,repeat=1,
        binary_layer='R163-common-R162-PE',version='candidate',panel=panel,panel_kind=panel['panel_kind'],
        destination=str(d),command=command(panel,method,d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,
        configuration=dict(id='q0',MIPFocus=0,Cuts=-1),arm_id=armid,stage='Round163',AM_threshold=.08)
    identity=dict(schema='round163-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=0),
        candidate_binary=str(PE),candidate_binary_sha256=PE_SHA),prereg_sha256=sha(OUT/'source_recipe.json'),
        runner_sha256=sha(__file__),source_hashes=m['source_hashes'],candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,
        measured_source_commit=MEASURED_CPP,delivery_base_commit=BASE,launches=[launch],references={role:p['reference']},
        candidate_manifest_path=str(OUT/'candidate_manifest.json'),candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),
        helper_manifest_SHA=sha(OUT/'helper_manifest_Eplus.json'),inventory_helper_entry='scripts/round156_online.py',
        inventory_node_limit=16384,stage='Round163',no_cross_arm_information=True,prospective_input_manifest_SHA=sha(OUT/'input_manifest.json'))
    camp.mkdir(parents=True,exist_ok=False)
    ref=camp/'reference'/role;ref.mkdir(parents=True)
    for name in ['build.json','original.lp']:(ref/name).hardlink_to(OUT/'qualification/references'/role/name)
    write(camp/'identity.json',identity)
    return launch,identity

def verify(launch,identity):
    method=launch['R163_method'];d=Path(launch['destination'])
    reader=plus_reader if method=='Eplus' else base_reader
    fn=types.FunctionType(reader.verify.__code__,dict(vars(reader),ROOT=ROOT,OUT=OUT,configure=configure))
    # The frozen helper may reject an omitted redundant zero-total lower row.
    # Its legal no-floor fallback is retained. The offline scope checker can
    # prove that row directly from nonnegative Y bounds, without altering any
    # model/source SHA, producer, floor or Native observation.
    reader153=legacy_import('round153_read');original_scope=reader153.scope_from_model
    implied=[]
    def audited_scope(model,bminus,b):
        names=[n for n in model['order'] if re.fullmatch(r'Y_\d+',n)]
        row=(tuple(sorted((n,1.) for n in names)),'>=',0.)
        if bminus==0 and row not in model['rows']:
            assert names and all(model['bounds'][n][0]>=0 for n in names)
            model=dict(model,rows=list(model['rows'])+[row]);implied.append(dict(Bminus=0,Y=names,lower_bounds_nonnegative=True))
        return original_scope(model,bminus,b)
    reader153.scope_from_model=audited_scope
    try:value=fn(launch,identity)
    finally:reader153.scope_from_model=original_scope
    if implied:write(d/'round163_implied_zero_total_reader.json',dict(PASS=True,offline_only=True,Native_model_unchanged=True,helper_unchanged=True,facts=implied))
    # The inherited audit already recomputes every fleet, full own H/Starts,
    # original compact reference, source qualification, cover and exact zero.
    for name in ['round138_parameters.json','round146_parameters.json','round148_parameters.json','round149_parameters.json',
                 'round151_parameters.json','round160_parameters.json','round162_parameters.json']:
        assert not (d/name).exists(), ('noncandidate mechanism active',name)
    assert not (d/'round160').exists() and not (d/'external/round162').exists()
    if method!='Eplus':assert not (d/'round153_parameters.json').exists()
    arm=value['arm'];r=read(d/'result.json')
    arm.update(R163_method=method,prospective_id=launch['id'],raw_search_L=arm.get('raw_search_L',arm['L']),
        final_proof_L=arm['L'],state='CERT' if arm['certificate'] else 'OPEN',
        helper_seconds=0.,helper_qualified=False,helper_floor=None,helper_return_reason='method does not use helper')
    root=d/'external/models/round153_root.json'
    if method=='Eplus' and root.exists():
        meta=read(root)
        helper=d/'external/round153_floor/result.json'
        h=read(helper) if helper.exists() else {}
        arm.update(helper_seconds=meta.get('helper_seconds',h.get('seconds',0)),helper_qualified=meta['qualified'],
            helper_floor=meta['lower'] if meta['qualified'] else None,helper_return_reason=(
                'qualified floor' if meta['qualified'] else 'global deadline' if meta.get('global_deadline_stop') else 'no qualified floor'),
            helper_root_SHA=meta['source_SHA'],helper_exit=meta.get('helper_exit'))
    elif method=='Eplus':arm['helper_return_reason']='no canonical root required before legal termination'
    assert arm['performance_eligible'] and arm['implementation_qualified'] and arm['evidence_complete']
    assert arm['T_cert'] is not None if arm['certificate'] else arm['T_cert'] is None
    write(d/'round163_endpoint.json',arm)
    return value

def execute(launch,identity):
    d=Path(launch['destination']);assert not (d/'verification_closeout.json').exists()
    if not d.exists():
        tick,creation=inherited.inherited.process_origin()
        from round100_idle import ensure_idle
        def idle():ensure_idle();return []
        supervisor=types.SimpleNamespace(**dict(vars(inherited.supervisor),foreign_heavy_processes=idle))
        fn=types.FunctionType(inherited.supervised.__code__,dict(vars(inherited),ROOT=ROOT,OUT=OUT,supervisor=supervisor))
        fn(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(), 'inspect unsealed original process; no automatic rerun'
    value=verify(launch,identity)
    write(OUT/'runtime_status.json',dict(UTC=utc(),position=launch['group_number'],arm=value['arm']))
    print(json.dumps(value['arm']),flush=True)
    return value

def smoke():
    # The one end-to-end smoke uses a tiny fixture, separate from the panel.
    p=read(OUT/'qualification/smoke_panel.json')
    l,i=make(p,'Eplus',OUT/'qualification/smoke',0)
    value=execute(l,i)
    write(OUT/'qualification/smoke_result.json',dict(PASS=True,not_performance_sample=True,arm=value['arm']))

def reverify_smoke():
    camp=OUT/'qualification/smoke';i=read(camp/'identity.json');l=i['launches'][0]
    value=execute(l,i)
    write(OUT/'qualification/smoke_result.json',dict(PASS=True,not_performance_sample=True,reader_repair_only=True,Optimize=0,arm=value['arm']))

def freeze():
    assert not (OUT/'matrix_frozen.json').exists()
    assert read(OUT/'qualification/result.json')['PASS'] and read(OUT/'qualification/smoke_result.json')['PASS']
    p=read(OUT/'input_manifest.json');recipe=read(OUT/'source_recipe.json');groups=[]
    for row,order in zip(p['roles'],recipe['method_orders']):
        row=copy.deepcopy(row);row['reference']=read(OUT/'qualification/references'/row['id']/'build.json')
        for method in order:
            position=len(groups)+1;camp=OUT/'campaign'/f'{position:03}'
            l,i=make(row,method,camp,position)
            groups.append(dict(position=position,group=camp.relative_to(OUT).as_posix(),launch=l,identity_SHA256=sha(camp/'identity.json')))
    assert len(groups)==18 and sum(g['launch']['cap_seconds'] for g in groups)==32400
    helpers=inherited.helper_bindings()
    for name in ['scripts/round163_common.py','scripts/round163_campaign.py']:helpers[name]=sha(ROOT/name)
    write(OUT/'matrix_frozen.json',dict(UTC=utc(),groups=groups,helpers=helpers,full_arm_count=18,full_arm_cap_sum_seconds=32400,
        candidate_manifest_SHA256=sha(OUT/'candidate_manifest.json'),input_manifest_SHA256=sha(OUT/'input_manifest.json'),
        helper_manifest_SHA256=sha(OUT/'helper_manifest_Eplus.json'),method_freeze_SHA256=sha(OUT/'method_freeze.json'),
        serial=True,affinity_mask=4,Seed=0,Threads=1,MIPThreads=1,H_seed=20260626,Native_NodeLimit='unlimited',
        one_total_deadline=True,no_adverse_result_early_stop=True,no_free_cross_arm_information=True))
    print('All 18 positions frozen; commit and qualification admission precede first production.')

def admission():
    matrix=read(OUT/'matrix_frozen.json')
    assert json.loads(git('show','HEAD:results/unified_exact_round163/matrix_frozen.json'))==matrix
    assert matrix['candidate_manifest_SHA256']==sha(OUT/'candidate_manifest.json')
    assert matrix['input_manifest_SHA256']==sha(OUT/'input_manifest.json')
    assert matrix['helper_manifest_SHA256']==sha(OUT/'helper_manifest_Eplus.json')
    assert matrix['method_freeze_SHA256']==sha(OUT/'method_freeze.json')
    assert sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    for n,h in matrix['helpers'].items():assert sha(ROOT/n)==h,n
    for g in matrix['groups']:
        assert sha(OUT/g['group']/'identity.json')==g['identity_SHA256']
        l=g['launch'];assert sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
        tokens(l['command'])
    return matrix

def arm(position):
    group=admission()['groups'][int(position)-1]
    execute(group['launch'],read(OUT/group['group']/'identity.json'))

def panel():
    for g in admission()['groups']:
        l=g['launch'];d=Path(l['destination'])
        if (d/'round163_endpoint.json').exists():continue
        label=f'arm_{g["position"]:03}'
        assert not (OUT/'fees'/label).exists(), 'inspect failed/incomplete receipt; do not automatically repeat a producer'
        write(OUT/'active_position.json',dict(UTC=utc(),position=g['position'],arm_id=l['arm_id'],fee_label=label))
        result=metered(label,'panel',[PYTHON,'-B',ROOT/'scripts/round163_campaign.py','arm',g['position']],l['cap_seconds']+900)
        assert result==0, ('retained technical failure; repair only affected work',label,result)
    write(OUT/'panel_complete.json',dict(UTC=utc(),arms=18,budget=budget()))

if __name__=='__main__':
    if sys.argv[1]=='arm':arm(sys.argv[2])
    else:globals()[sys.argv[1]]()
