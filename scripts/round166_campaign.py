"""One serial same-build B/C166 matrix; original complete producer and proof reader."""
from round166_common import *
import copy,inspect,math,os,types,traceback
import round164_common as bridge
bridge.OUT=OUT;bridge.TEMP=WORK/'temp/round166'
inherited=bridge.legacy_import('round133_campaign')
reader=bridge.legacy_import('round135_read')
old_models=bridge.legacy_import('round111_seed_audit')
finish_producer=bridge.legacy_import('round121_campaign').finish_producer
COMMON=bridge.legacy_import('round122_prepare').COMMON
PE=WORK/'build-cache/round166/ExactEBRP.exe'
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
OFF={'--round146-gd':'off','--round148-shared-s':'off','--round149-penalty-feedback':'off',
     '--round151-penalty-propagation':'off','--round153-root-floor':'off','--round154-proof-floor':'off',
     '--round156-rn-refinement':'off','--round143-rn':'off','--round144-projection':'off',
     '--round145-projection':'off','--round140-counts':'off','--round141-count-proof':'off',
     '--round142-count-products':'off','--round160-physical-neighborhood':'off','--round162-physical-completion':'off'}
def tokens(c):
    result={};i=1
    while i<len(c):
        flag=c[i];assert flag.startswith('--') and flag not in result
        if flag=='--plain-baseline':result[flag]=True;i+=1
        else:assert i+1<len(c) and not c[i+1].startswith('--');result[flag]=c[i+1];i+=2
    return result
def command(p,method,d):
    template=read(ROOT/'results/unified_exact_round163/method_freeze.json')['B']['argv']
    values=dict(exe=str(PE),input=str(ROOT/p['input_path']),T=str(p['T_seconds']),
        **{'lambda':format(p['lambda'],'.17g')},pickup_time='60',drop_time='60',native_limit=str(p['cap_seconds']-6),
        cap=str(p['cap_seconds']),seed='0',result=str(d/'result.json'),log=str(d/'native.log'),phases=str(d/'phases.csv'),
        external=str(d/'external'),hga=str(d/'hga.csv'),progress=str(d/'progress.csv'),journal=str(d/'journal'))
    result=[]
    for token in template:
        for k,v in values.items():token=token.replace('${'+k+'}',v)
        assert '${' not in token;result.append(token)
    for flag,value in OFF.items():
        actual=tokens(result)
        if flag in actual:assert actual[flag]==value
        else:result.extend([flag,value])
    result.extend(['--round166-breakpoint','on' if method=='C166' else 'off'])
    actual=tokens(result);assert actual['--round127-mode']=='ms2' and actual['--round98-state-service']=='m-binary'
    assert actual['--gurobi-seed']=='0' and actual['--threads']==actual['--mip-threads']=='1'
    return result
def candidate():
    sources={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file()}
    sources['CMakeLists.txt']=sha(ROOT/'CMakeLists.txt')
    write(OUT/'candidate_manifest.json',dict(UTC=utc(),source_commit=git('rev-parse','HEAD'),
        source_identity='commit plus exact complete source hashes; freeze requires clean source at that commit',
        source_hashes=sources,production_PE=str(PE),research_PE=str(PE),production_PE_SHA=sha(PE),research_PE_SHA=sha(PE),
        DLL=str(DLL),DLL_SHA=sha(DLL),compiler='D:/msys64/ucrt64/bin/g++.exe',compiler_SHA=sha('D:/msys64/ucrt64/bin/g++.exe'),
        cmake_cache=bind(WORK/'build-cache/round166/CMakeCache.txt'),
        B_and_C166_same_PE=True,default_candidate=False,history_PE_not_relabelled=True))
def make(p,method,camp,position,qualification=False):
    c=read(OUT/'candidate_manifest.json');p=copy.deepcopy(p)
    p.update(gurobi_seed=0,round137_delete_ab=False,panel_kind='qualification' if qualification else 'Round166 exposed-input representation comparison')
    armid=f'R166_{position:03}_{p["id"]}_S0_{method}';d=camp/'raw'/armid
    launch=dict(number=1,group_number=position,global_launch_number=position,id=p['id'],arm='M-B',method='S2',R166_method=method,
        seed=0,gurobi_seed=0,repeat=1,binary_layer='R166-common-new-build',version='candidate',panel=p,panel_kind=p['panel_kind'],
        destination=str(d),command=command(p,method,d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,
        configuration=dict(id='q0',MIPFocus=0,Cuts=-1),arm_id=armid,stage='Round166',AM_threshold=.08)
    camp.mkdir(parents=True,exist_ok=False)
    identity=dict(schema='round166-own-complete-lifecycle-v1',prereg=dict(common=dict(COMMON,gurobi_seed=0),candidate_binary=str(PE),candidate_binary_sha256=sha(PE)),
        prereg_sha256=sha(OUT/'research_design.md'),runner_sha256=sha(__file__),source_hashes=c['source_hashes'],candidate_binary_sha256=sha(PE),
        dll_sha256=sha(DLL),measured_source_commit=c['source_commit'],delivery_base_commit=BASE,launches=[launch],references={},
        no_cross_arm_information=True,H_seed=20260626,offline_analysis_fleets_in_production=False,stage='Round166')
    write(camp/'identity.json',identity);return launch,identity
class ArmModels(old_models.ArmModels):
    def model_contract(self,root,p,path,arm):
        digest,data=self.data(path);model=data[0]
        if not any(n.startswith('r166_t_') for n in model['order']):return super().model_contract(root,p,path,arm)
        import importlib.util
        spec=importlib.util.spec_from_file_location('round166_independent_contract',OUT/'review/data_c166_model_check.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        physical=reader.core.evidence.instance(root,p)
        fact=module.check_c166_model(model,p,physical)
        return dict(path=path.relative_to(root).as_posix(),SHA=digest,**fact),model
def normal_endpoint(launch,identity,d,j,result):
    source=inspect.getsource(reader.core.endpoint)
    source=source.replace("a=read(d/'audit.json')","a=prechecked")
    source=source.replace("assert r['algorithm_preset']==expected", "assert r['algorithm_preset']==('research-C166-breakpoint-bit' if launch.get('R166_method')=='C166' else expected)")
    ns=dict(vars(reader.core),prechecked=dict(passed=True,binary_sha256=identity['candidate_binary_sha256']))
    exec(compile(source,__file__+'::actual_representation_endpoint','exec'),ns)
    return ns['endpoint'](ROOT,launch,identity,d,j,False)
def verify(launch,identity):
    d=Path(launch['destination']);method=launch['R166_method']
    actual=read(d/'round137_parameters.json')
    assert actual==dict(split_threshold=.08,delete_ab=False,delete_cr=False,delete_cg=False,loaded_after_presets=True)
    result=read(d/'result.json')
    expected='research-C166-breakpoint-bit' if method=='C166' else 'research-round99-ensc-discrete-structure-m-binary'
    assert result['algorithm_preset']==expected
    if method=='C166':
        controls=read(d/'round166_parameters.json');assert controls['candidate']=='C166' and controls['Seed']==0 and controls['H_seed']==20260626
    else:assert not (d/'round166_parameters.json').exists()
    def ap(model,data,enabled):
        assert not enabled
        if method=='C166':
            assert not any(n.startswith(('state_','rn_','r141_','theta_')) for n in model['order'])
            return dict(enabled=False,AP_rows=0,state_weighted_penalty_not_emitted=True)
        return reader.ap_audit.contract(model,data,enabled)
    ns=dict(vars(reader),ROOT=ROOT,OUT=OUT,DLL=DLL,models=types.SimpleNamespace(ArmModels=ArmModels),
        ap_audit=types.SimpleNamespace(contract=ap),_normal_endpoint=normal_endpoint)
    value=types.FunctionType(reader.verify.__code__,ns)(launch,identity)
    arm=value['arm'];arm.update(method=method,R166_method=method,state='CERT' if arm['certificate'] else 'OPEN',source_build=identity['measured_source_commit'])
    write(d/'round166_endpoint.json',arm)
    return value
def execute(launch,identity):
    d=Path(launch['destination']);assert not (d/'round166_endpoint.json').exists()
    if not d.exists():
        tick,creation=inherited.inherited.process_origin()
        from round100_idle import ensure_idle
        def idle():ensure_idle();return []
        supervisor=types.SimpleNamespace(**dict(vars(inherited.supervisor),foreign_heavy_processes=idle))
        fn=types.FunctionType(inherited.supervised.__code__,dict(vars(inherited),ROOT=ROOT,OUT=OUT,supervisor=supervisor))
        fn(launch,identity,tick);finish_producer(launch,tick,creation)
    else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'do not rerun an unsealed producer'
    begin=time.perf_counter()
    try:value=verify(launch,identity)
    finally:
        record=dict(UTC=utc(),seconds=time.perf_counter()-begin,Optimize=0)
        path=d/'postverify_attempts.json';attempts=read(path) if path.exists() else []
        if not attempts and (d/'postverify_cost.json').exists():attempts.append(read(d/'postverify_cost.json'))
        attempts.append(record);write(path,attempts)
    print(json.dumps(value['arm']),flush=True);return value
def smoke():
    # Existing no-solver tiny objects from the fixed diagnostic list.
    for fixture,initial,T in [('nonzero',3,360),('zero',4,480)]:
        path=OUT/f'qualification/tiny/initial{initial}.txt'
        p=dict(id='qualification-'+fixture,V=2,M=1,Q_vector=[3],T_seconds=T,cap_seconds=120,
            input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),
            **{'lambda':.15},Omega=2,pickup_seconds=60,drop_seconds=60,total_initial=initial,total_target=4,total_capacity=8,
            panel_kind='qualification',source='synthetic',inventory='shortage',geometry='tiny',replicate=1,known=True,exposed=True)
        for method in ['B','C166']:
            camp=OUT/'qualification/controller'/f'{fixture}_{method}'
            if (camp/'identity.json').exists():
                identity=read(camp/'identity.json');launch=identity['launches'][0]
                if (Path(launch['destination'])/'round166_endpoint.json').exists():continue
            else:launch,identity=make(p,method,camp,0,True)
            execute(launch,identity)
def freeze():
    assert not (OUT/'matrix_frozen.json').exists()
    assert read(OUT/'qualification.json')['PASS']
    pmanifest=ROOT/'results/unified_exact_round163/input_manifest.json';groups=[]
    for i,p in enumerate(read(pmanifest)['roles']):
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        for method in (['B','C166'] if i%2==0 else ['C166','B']):
            position=len(groups)+1;camp=OUT/'campaign'/f'{position:03}'
            launch,identity=make(p,method,camp,position)
            groups.append(dict(position=position,method=method,input_id=p['id'],launch=launch,identity_SHA=sha(camp/'identity.json'),group=camp.relative_to(OUT).as_posix()))
    assert len(groups)==12 and sum(g['launch']['cap_seconds'] for g in groups)==21600
    write(OUT/'matrix_frozen.json',dict(UTC=utc(),groups=groups,candidate_manifest=bind(OUT/'candidate_manifest.json'),
        source_commit=read(OUT/'candidate_manifest.json')['source_commit'],PE_SHA=sha(PE),DLL_SHA=sha(DLL),
        input_manifest=bind(pmanifest),qualified=bind(OUT/'qualification.json'),serial=True,Threads=1,MIPThreads=1,
        H_seed=20260626,Gurobi_Seed=0,NodeLimit='unlimited',cap_sum=21600,reservation=25200,minimum_science_remaining_at_entry=32400,
        no_portfolio=True,no_cross_arm_information=True,methods=['B','C166'],new_input_count=0,new_seed_count=0,
        helper_hashes={**inherited.helper_bindings(),'scripts/round166_campaign.py':sha(__file__),
            'scripts/round166_common.py':sha(ROOT/'scripts/round166_common.py'),
            'results/unified_exact_round166/review/data_c166_model_check.py':sha(OUT/'review/data_c166_model_check.py')}))
def arm(position):
    g=read(OUT/'matrix_frozen.json')['groups'][int(position)-1]
    assert g['position']==int(position) and sha(OUT/g['group']/'identity.json')==g['identity_SHA']
    execute(g['launch'],read(OUT/g['group']/'identity.json'))
def panel():
    matrix=read(OUT/'matrix_frozen.json');c=read(OUT/'candidate_manifest.json')
    assert sha(PE)==matrix['PE_SHA'] and sha(DLL)==matrix['DLL_SHA']
    for name,digest in c['source_hashes'].items():assert sha(ROOT/name)==digest
    for name,digest in matrix['helper_hashes'].items():assert sha(ROOT/name)==digest
    start=datetime.fromisoformat(read(OUT/'entry_state.json')['work_start_UTC']).timestamp()
    assert 57600-(time.time()-start)>=32400,'preserve at least9h at formal entry'
    for g in matrix['groups']:
        l=g['launch'];d=Path(l['destination'])
        if (d/'round166_endpoint.json').exists():continue
        assert not d.exists(),'inspect existing producer; no automatic rerun'
        future=sum(x['launch']['cap_seconds']+300 for x in matrix['groups'] if x['position']>=g['position'])
        assert 57600-(time.time()-start)>=future+7200,'preserve remaining matrix and manuscript/review'
        write(OUT/'active_position.json',dict(UTC=utc(),position=g['position'],method=g['method'],id=g['input_id']))
        tick=time.perf_counter();fee=OUT/'fees'/f'{g["position"]:03}.json'
        write(fee,dict(UTC=utc(),position=g['position'],start_unix=time.time(),reservation=l['cap_seconds']+300,watchdog=l['cap_seconds']+900,
            producer_cap=l['cap_seconds'],status='RUNNING'))
        try:
            log=OUT/'fees'/f'{g["position"]:03}.log'
            env=dict(os.environ,PATH='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+os.environ['PATH'],PYTHONDONTWRITEBYTECODE='1')
            with log.open('xb') as stream:
                child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'arm',str(g['position'])],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
                birth=bridge.meter.process_birth(child.pid)
                rec=read(fee);rec.update(pid=child.pid,birth=birth,arm_wrapper_is_fresh_process=True);write(fee,rec)
                try:code=child.wait(timeout=l['cap_seconds']+900)
                except subprocess.TimeoutExpired:
                    actual=bridge.meter.process_birth(child.pid)
                    assert birth and actual and actual['creation_filetime']==birth['creation_filetime']
                    killed=subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=30)
                    write(OUT/'fees'/f'{g["position"]:03}_watchdog.json',dict(pid=child.pid,exit_code=killed.returncode,reason='fault watchdog; producer evaluation budget never extended'))
                    child.wait(timeout=30);raise
            assert code==0,('retained failed position; do not automatically rerun producer',g['position'],log)
            value=dict(arm=read(d/'round166_endpoint.json'))
        except BaseException:
            rec=read(fee);rec.update(status='FAILED',seconds=time.perf_counter()-tick);write(fee,rec);raise
        rec=read(fee);rec.update(status='COMPLETE',seconds=time.perf_counter()-tick,endpoint=bind(d/'round166_endpoint.json'));write(fee,rec)
        write(OUT/'runtime_status.json',dict(UTC=utc(),last_completed=g['position'],method=g['method'],id=g['input_id'],endpoint=value['arm']))
    write(OUT/'panel_complete.json',dict(UTC=utc(),positions=12,paired_inputs=6,PE_SHA=sha(PE)))
if __name__=='__main__':
    if sys.argv[1]=='arm':arm(sys.argv[2])
    else:globals()[sys.argv[1]]()
