"""R162 complete-panel adapter. Imports never launch a producer or old freeze."""
from round162_common import *
import copy,inspect,types,importlib,re,collections

def legacy_import(name):
    for attempt in range(30):
        try:return importlib.import_module(name)
        except FileNotFoundError as error:
            path=Path(error.filename).resolve();relative=path.relative_to(ROOT.resolve());parts=relative.parts
            assert len(parts)>=3 and parts[0]=='results'
            match=re.fullmatch(r'unified_exact_round(\d+)',parts[1]);assert match and int(match[1])<162
            assert path.suffix in ('.json','.md','.csv'),relative
            raw=git('show',BASE+':'+relative.as_posix());assert len(raw)<5000000
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            receipt=OUT/'infra/legacy_import_metadata.json';records=read(receipt) if receipt.exists() else []
            records.append(dict(path=relative.as_posix(),commit=BASE,SHA256=sha(path),bytes=len(raw),reason='thin read-only import metadata; no old producer or whole carrier'))
            write(receipt,records)
    raise RuntimeError('bounded metadata import exhausted')

inherited=legacy_import('round133_campaign')
proof_reader=legacy_import('round154_read')
producer_reader=legacy_import('round156_read')
finish_producer=legacy_import('round121_campaign').finish_producer
COMMON=legacy_import('round122_prepare').COMMON

SPECS=[('R-X35-S-T2',f,7200) for f in ('Eplus','Stock','PC')]+[('N-B35-S',f,2400) for f in ('Eplus','Stock','PC')]+[
    ('K-20-S',f,1200) for f in ('Eplus','PC')]+[('R-X20-S-T1',f,1200) for f in ('Eplus','PC')]
OUTPUTS={'--out','--log','--process-phase-ledger','--external-gini-artifact-dir','--primal-heuristic-generation-log','--progress-log','--native-evidence-dir'}

def prior_launch(role):
    m=json.loads(git('show',BASE+':results/unified_exact_round137/matrix_frozen.json'))
    return next(g['launch'] for g in m['groups'] if g['launch']['id']==role and g['launch']['method']=='S2' and g['launch']['seed']==0)

def arguments(method):
    helper=ROOT/'scripts/round156_online.py';manifest=OUT/'helper_manifest_Eplus.json'
    return ['--round146-gd','off','--round149-penalty-feedback','off','--round151-penalty-propagation','off',
        '--round153-root-floor','on','--round154-proof-floor','on','--round156-rn-refinement','on',
        '--round153-python',str(PYTHON),'--round153-helper',str(helper),'--round153-helper-sha',sha(helper),
        '--round153-manifest',str(manifest),'--round153-manifest-sha',sha(manifest),'--round160-physical-neighborhood','off',
        '--round162-physical-completion',{'Eplus':'off','Stock':'stock','PC':'on'}[method]]

def make(role,method,camp,index,cap):
    m=read(OUT/'complete_candidate_manifest.json');old=prior_launch(role);launch=copy.deepcopy(old)
    p=launch['panel'];inp=OUT/'inputs'/role/'instance.txt';assert sha(inp)==p['input_sha256']
    p.update(input_path=inp.relative_to(ROOT).as_posix(),instance_path=inp.relative_to(ROOT).as_posix(),cap_seconds=cap,
        gurobi_seed=0,round154_method='E',round156_method='Eplus',round160_method='Eplus',round162_method=method,
        round138_stock_rlt=method!='Eplus',round146_gd=False,round149_penalty_feedback=False,known=True,exposed=True,
        panel_kind='Round162 fresh paid complete Eplus / STOCK / PC')
    armid=f'R162_{index:03}_{role}_S0_{method}';destination=camp/'raw'/armid
    command=[v.replace(old['destination'],str(destination)) for v in old['command']];command[0]=m['production_PE']
    for flag,value in [('--input',str(inp)),('--time-limit',str(cap-6)),('--process-wall-time-limit',str(cap))]:command[command.index(flag)+1]=value
    command+=arguments(method)
    launch.update(number=1,group_number=index,global_launch_number=index,method='E',R147_method='BASE' if method=='Eplus' else 'STOCK',R154_method='E',R156_method='Eplus',
        R160_method='Eplus',R162_method=method,seed=0,binary_layer='R162-same-PE',version='candidate',panel=p,panel_kind=p['panel_kind'],
        destination=str(destination),command=command,arm_id=armid,stage='confirmation',AM_threshold=.08,cap_seconds=cap,hard_stop_seconds=cap-2)
    identity=dict(schema='round162-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=0),
        candidate_binary=m['production_PE'],candidate_binary_sha256=m['production_PE_SHA']),
        prereg_sha256=sha(OUT/'development_decision.json'),runner_sha256=sha(__file__),source_hashes=m['source_hashes'],
        candidate_binary_sha256=m['production_PE_SHA'],dll_sha256=DLL_SHA,measured_source_commit=m['source_commit'],delivery_base_commit=BASE,
        launches=[launch],candidate_manifest_path=str(OUT/'complete_candidate_manifest.json'),candidate_manifest_SHA=sha(OUT/'complete_candidate_manifest.json'),
        stage='confirmation',no_cross_arm_information=True,helper_manifest_SHA=sha(OUT/'helper_manifest_Eplus.json'),original_frozen_launch=old,
        original_fixed_science='e735c3447eb1443713c700942d873de1783a4a26',inventory_node_limit=16384,inventory_helper_entry='scripts/round156_online.py',
        R162_method=method,source_once=method=='PC',source_lower_diagnostic_only=True)
    write(camp/'identity.json',identity);return launch,identity

def pc_aliases(destination):
    """Actual model equalities certify aliases used ONLY by the old helper checker.

    The formal proof collector and all raw observations retain their actual SHA.
    The helper contributes zero Native rows. The PC and temporary full source
    have their own actual-matrix audits, independent of the helper placement.
    """
    import round108_reader as parser
    models=destination/'external/models';meta_path=models/'round153_root.json';aliases={};facts=[]
    source_dir=destination/'external/round162'
    if not meta_path.exists():return aliases,facts
    meta=read(meta_path);root=legacy_import('round149_context').unique_model(models,meta['source_SHA'])
    if (source_dir/'source.json').exists():
        s=read(source_dir/'source.json')
        if s.get('source_calls'):
            original=list(map(json.loads,(source_dir/'original_columns.jsonl').read_text().splitlines()))
            base=parser.lp_model(root);objective=dict(base['objective'][0])
            assert {v['name']:(v['lb'],v['ub'],v['type'],v['obj']) for v in original}=={
                n:(*base['bounds'][n],base['types'][n],objective.get(n,0)) for n in base['order']}
            original_rows=list(map(json.loads,(source_dir/'original_rows.jsonl').read_text().splitlines()))
            rowcounter=collections.Counter((tuple(sorted(r['terms'].items())),{'<':'<=','>':'>=','=':'='}[r['sense']],r['rhs']) for r in original_rows)
            assert rowcounter==collections.Counter(base['rows'])
            aliases[s['source_SHA256']]=meta['source_SHA'];facts.append(dict(actual=s['source_SHA256'],helper_base=meta['source_SHA'],kind='temporary full-Q source; no helper floor rows'))
    projection=read(source_dir/'compact/projection.json') if (source_dir/'compact/projection.json').exists() else None
    for receipt in models.glob('*_round162_PC.lp.scope.json'):
        scope=read(receipt)
        if not scope['applied']:continue
        assert projection and scope['root_source_SHA256']==projection['source_SHA256']
        pc=Path(str(receipt)[:-len('.scope.json')]);base_path=pc.with_name(pc.stem[:-len('_round162_PC')]+'.lp')
        b=parser.lp_model(base_path);m=parser.lp_model(pc)
        for field in ('bounds','types','objective'):assert m[field]==b[field]
        terms=projection['row']['terms'];expected={n:c for n,c in terms.items() if n in m['bounds']}
        assert all(n.startswith(('state_','state_g_')) for n in set(terms)-set(expected))
        row=(tuple(sorted(expected.items())),'<=',projection['row']['rhs'])
        assert collections.Counter(m['rows'])==collections.Counter(b['rows'])+collections.Counter([row])
        assert scope['cutoff']<=read(source_dir/'source.json')['cutoff']
        digest=sha(pc);aliases[digest]=sha(base_path);facts.append(dict(actual=digest,helper_base=sha(base_path),kind='same old matrix plus one independently registered PC row'))
    return aliases,facts

def floor_contract(destination,enabled,launch,identity):
    # Same R156 producer arithmetic and R154 proof ledger. Only the helper's
    # zero-row Native placement checker receives mathematically checked aliases.
    aliases,facts=pc_aliases(destination) if launch['R162_method']=='PC' else ({},[])
    import round153_read as old
    floor_source=inspect.getsource(old.floor_contract)
    assert floor_source.count('==4096')==3
    floor_source=floor_source.replace('==4096','==16384').replace("deps['scripts/round153_online.py']","deps['scripts/round156_online.py']")
    def floor_read(path):
        value=read(path);path=Path(path)
        if path.name.endswith('.round153.native.json'):
            value=dict(value);value['actual_model_SHA']=value['model_SHA'];value['model_SHA']=aliases.get(value['model_SHA'],value['model_SHA'])
        elif path.name=='observations.json':
            value=copy.deepcopy(value)
            for e in value:
                if e['payload']['kind']=='call':
                    p=e['payload'];p['model_sha256']=aliases.get(p['model_sha256'],p['model_sha256'])
        return value
    def floor_first(models):
        call=legacy_import('round149_context').first_call(models)
        if call is not None:call=dict(call,model_sha256=aliases.get(call['model_sha256'],call['model_sha256']))
        return call
    source=inspect.getsource(proof_reader.floor_contract)
    source=source.replace('source=inspect.getsource(old.floor_contract)','source=_producer_floor_source')
    needle='ns=dict(old.floor_contract.__globals__,ROOT=ROOT,OUT=OUT,proof_only=proof_only)'
    assert source.count(needle)==1
    source=source.replace(needle,'ns=dict(old.floor_contract.__globals__,ROOT=ROOT,OUT=OUT,proof_only=proof_only,read=_floor_read,first_call=_floor_first)')
    ns=dict(vars(proof_reader),ROOT=ROOT,OUT=OUT,_producer_floor_source=floor_source,_floor_read=floor_read,_floor_first=floor_first)
    exec(compile(source,__file__+'::same_paid_helper_and_PC_placement','exec'),ns)
    value=ns['floor_contract'](destination,enabled,launch,identity)
    parameters=read(destination/'round153_parameters.json');assert parameters['node_limit']==16384
    meta=value.get('root')
    if meta:
        assert meta['node_limit']==16384 and meta['producer_rule']==parameters['producer_rule']=='RN16384_original_gap'
    value.pop('Native_same_as_B_on_same_domain',None)
    value.update(PC_aliases_for_helper_only=facts,raw_observations_changed=False,proof_collector_uses_actual_models=True,
        helper_floor_rows_remain_zero=True,PC_checked_separately=True)
    write(destination/'round162_helper_control_audit.json',value)
    return value

def verify(launch,identity):
    destination=Path(launch['destination'])
    fn=types.FunctionType(proof_reader.verify.__code__,dict(vars(proof_reader),ROOT=ROOT,OUT=OUT,configure=configure,floor_contract=floor_contract))
    reader153=legacy_import('round153_read');reader147=legacy_import('round147_read')
    old153,old147=reader153.verify,reader147.verify
    checked=copy.deepcopy(launch);checked['R147_method']='BASE' if launch['R162_method']=='Eplus' else 'STOCK'
    source153=inspect.getsource(old153)
    needle="assert launch['R147_method']=='BASE' and command[command.index('--round146-gd')+1]=='off'"
    assert source153.count(needle)==1
    source153=source153.replace(needle,"assert launch['R147_method'] in ('BASE','STOCK') and command[command.index('--round146-gd')+1]=='off'")
    source147=inspect.getsource(old147)
    needle="assert ('--round138-stock-rlt' in command) == stock";assert source147.count(needle)==1
    source147=source147.replace(needle,"assert ('--round138-stock-rlt' in command or ('--round162-physical-completion' in command and command[command.index('--round162-physical-completion')+1] in ('stock','on'))) == stock")
    ns153=dict(vars(reader153));ns147=dict(vars(reader147))
    for name,source,ns in [('153',source153,ns153),('147',source147,ns147)]:
        path=destination/f'round162_reader_{name}.py.txt';path.write_text(source,encoding='utf8');exec(compile(source,str(path),'exec'),ns)
    reader153.verify=ns153['verify'];reader147.verify=ns147['verify']
    try:value=fn(checked,identity)
    finally:reader153.verify,reader147.verify=old153,old147
    assert not (destination/'round160').exists()
    method=launch['R162_method']
    if method!='Eplus':
        parameters=read(destination/'round138_parameters.json');assert parameters['stock_rlt']
        p=read(destination/'round162_parameters.json');assert p['PC']==(method=='PC') and p['stock'] and not p['NodeLimit_development_override']
    if method=='PC':
        path=destination/'external/round162_run.json'
        if path.exists():
            status=read(path);assert status['source_calls']<=1 and not status['source_lower_formal_floor'] and status['formal_new_columns']==0
            for p in destination.rglob('*.round162.native.json'):
                audit=read(p);assert audit['PASS'] and audit['NodeLimit_unlimited']
                if not audit['temporary_source']:assert audit['endpoint_columns']==0 and audit['PC_rows']<=1
    value['arm'].update(R162_method=method,stock=method!='Eplus',PC=method=='PC')
    write(destination/'round162_endpoint.json',value['arm']);return value

def execute(launch,identity):
    configure();destination=Path(launch['destination']);assert not (destination/'verification_closeout.json').exists()
    if not destination.exists():
        tick,creation=inherited.inherited.process_origin()
        from round100_idle import ensure_idle
        def idle():ensure_idle();return []
        supervisor=types.SimpleNamespace(**dict(vars(inherited.supervisor),foreign_heavy_processes=idle))
        supervised=types.FunctionType(inherited.supervised.__code__,dict(vars(inherited),ROOT=ROOT,OUT=OUT,supervisor=supervisor))
        supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (destination/'producer_receipt.json').exists() and (destination/'producer_seal.json').exists()
    value=verify(launch,identity);write(OUT/'complete_runtime_status.json',dict(UTC=utc(),arm_id=launch['arm_id'],arm=value['arm']))
    print(json.dumps(value['arm']),flush=True);return value

def smoke(method):
    camp=OUT/'qualification'/('complete_'+method);camp.mkdir(parents=True,exist_ok=False)
    launch,identity=make('N-B35-S',method,camp,0,120);value=execute(launch,identity)
    write(camp/'result.json',dict(PASS=True,not_performance_sample=True,arm=value['arm']))

def reverify_smoke(method):
    camp=OUT/'qualification'/('complete_'+method);identity=read(camp/'identity.json');launch=identity['launches'][0]
    assert (Path(launch['destination'])/'producer_seal.json').exists()
    value=execute(launch,identity)
    write(camp/'result.json',dict(PASS=True,not_performance_sample=True,readback_only=True,Optimize=0,arm=value['arm']))

def freeze():
    assert not budget()['unclosed'] and not (OUT/'complete_matrix.json').exists()
    for method in ('PC','Stock'):assert read(OUT/'qualification'/('complete_'+method)/'result.json')['PASS']
    assert read(OUT/'qualification/scope/scope_qualification.json')['PASS']
    manifest=read(OUT/'complete_candidate_manifest.json')
    assert sha(manifest['production_PE'])==manifest['production_PE_SHA']
    for name,digest in manifest['source_hashes'].items():assert sha(ROOT/name)==digest,name
    groups=[]
    for pos,(role,method,cap) in enumerate(SPECS,1):
        camp=OUT/'complete_panel'/f'{pos:03}';camp.mkdir(parents=True,exist_ok=False)
        launch,identity=make(role,method,camp,pos,cap)
        groups.append(dict(position=pos,group=camp.relative_to(OUT).as_posix(),launch=launch,identity_SHA256=sha(camp/'identity.json')))
    old=json.loads(git('show',BASE+':results/unified_exact_round160/confirmation_matrix.json'))['helpers']
    helpers={name:sha(ROOT/name) for name in old}
    for name in ('round162_campaign.py','round162_common.py','round162_full_build.py'):
        helpers['scripts/'+name]=sha(ROOT/'scripts'/name)
    write(OUT/'complete_matrix.json',dict(UTC=utc(),groups=groups,helpers=helpers,Seed=0,Threads=1,H_seed=20260626,
        nominal_seconds=33600,reservation_with_900_each=42600,serial=True,main_first_six=True,
        candidate_manifest_SHA256=sha(OUT/'complete_candidate_manifest.json'),helper_manifest_SHA256=sha(OUT/'helper_manifest_Eplus.json'),
        NodeLimit_development_override=False,one_total_deadline=True,no_free_historical_source=True,
        early_stop='After six main-role arms, stop remaining small roles only if the package is clearly adverse to both controls on both main roles without confirmation value'))

def admit():
    m=read(OUT/'complete_matrix.json');assert len(m['groups'])==10 and m['nominal_seconds']==33600
    expected={'R-X35-S-T2':'c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2',
        'N-B35-S':'80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98',
        'K-20-S':'d1a65be4b87dead2ae351068ece3c3ce486a51c93652d778e055f2684606ea42',
        'R-X20-S-T1':'2b467b5bb1e650a4c1e792e808dcf9575bcc76752fe378e16c838015344ddac6'}
    facts=[]
    for group in m['groups']:
        l=group['launch'];cmd=dict(zip(l['command'][1::2],l['command'][2::2]));assert 2*len(cmd)+1==len(l['command'])
        assert sha(cmd['--input'])==expected[l['id']]==l['panel']['input_sha256']
        assert cmd['--round162-physical-completion']=={'Eplus':'off','Stock':'stock','PC':'on'}[l['R162_method']]
        assert cmd['--round160-physical-neighborhood']=='off'
        assert cmd['--round156-rn-refinement']==cmd['--round154-proof-floor']=='on'
        assert float(cmd['--process-wall-time-limit'])==l['cap_seconds'] and float(cmd['--time-limit'])==l['cap_seconds']-6
        assert all(Path(cmd[f]).resolve().is_relative_to(OUT.resolve()) for f in OUTPUTS)
        assert sha(OUT/group['group']/'identity.json')==group['identity_SHA256'] and not Path(l['destination']).exists()
        facts.append(dict(position=group['position'],role=l['id'],method=l['R162_method'],cap=l['cap_seconds']))
    assert budget()['remaining_G1_seconds']>=42600+3600
    write(OUT/'complete_admission.json',dict(PASS=True,UTC=utc(),matrix_SHA256=sha(OUT/'complete_matrix.json'),
        source_SHA256=sha(__file__),facts=facts,old_freeze_called=False,Optimize=0))

def arm(position):
    m=read(OUT/'complete_matrix.json');gate=read(OUT/'complete_admission.json')
    assert gate['PASS'] and gate['matrix_SHA256']==sha(OUT/'complete_matrix.json') and gate['source_SHA256']==sha(__file__)
    assert m['candidate_manifest_SHA256']==sha(OUT/'complete_candidate_manifest.json') and m['helper_manifest_SHA256']==sha(OUT/'helper_manifest_Eplus.json')
    for name,digest in m['helpers'].items():assert sha(ROOT/name)==digest,name
    group=m['groups'][int(position)-1];execute(group['launch'],read(OUT/group['group']/'identity.json'))

def panel(start='1',stop='6'):
    m=read(OUT/'complete_matrix.json')
    for group in m['groups'][int(start)-1:int(stop)]:
        pos=group['position'];launch=group['launch'];dest=Path(launch['destination'])
        if (dest/'round162_endpoint.json').exists():continue
        label=f'complete_{pos:03}';assert not (OUT/'fees'/label).exists(),'inspect original incomplete process/receipt before a resume'
        write(OUT/'complete_active_position.json',dict(UTC=utc(),position=pos,arm_id=launch['arm_id']))
        assert metered(label,'native',[PYTHON,'-B',ROOT/'scripts/round162_campaign.py','arm',pos],launch['cap_seconds']+900)==0
    write(OUT/f'complete_segment_{start}_{stop}.json',dict(UTC=utc(),start=int(start),stop=int(stop),budget=budget()))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
