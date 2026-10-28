"""Current-only closed-root replay using the established pure recovery engine."""
from __future__ import annotations
import argparse, collections, hashlib, importlib, inspect, json, math, pathlib, sys, time, types, zipfile
import round133_portable_check as engine

ROUND='results/unified_exact_round137'
RECORDED='E:/codes/ExactEBRP-work/worktrees/paper-current'
DERIVED=('audit.json','native_claims.json','claim_rejections.json','independent_evidence.json',
         'verification_closeout.json','arm_total_receipt.json','round135_endpoint.json')

class CurrentRoot(engine.ClosedRoot):
    def __init__(self,root):
        self.root=engine.RealPath(root).resolve(strict=True);self.recorded=pathlib.PureWindowsPath(RECORDED)
        self.sources={};self.overlay={};self.allowed_writes=set();self.attestations={}
        self.attestations_used={};self.read_paths=set();self.modules={};self.git_sources={}
        self.derived_writes=[];self.helper_members={};self.publication=None
        self.allowed_files=set();self.allowed_trees=set();self.allowed_dirs={str(self.root)}
        self.allow_tree(self.root/ROUND)

def source_publication(fs):
    pub=fs.read(ROUND+'/source_publication.json');record=pub['source_bundle'];path=fs.resolve(record['path'])
    fs.allow_file(path);assert fs.sha(path)==record['SHA256'] and path.stat().st_size==record['bytes']
    with zipfile.ZipFile(path) as z:
        assert len(z.namelist())==len(set(z.namelist()))==len(record['members'])
        assert set(z.namelist())==set(record['members'])
        for name,digest in record['members'].items():
            relative=pathlib.PurePosixPath(name)
            assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
            assert relative.suffix.lower() not in {'.exe','.dll','.o','.obj','.a','.lib','.lic','.ttf','.otf'}
            raw=z.read(name);assert hashlib.sha256(raw).hexdigest()==digest;fs.attach(name,raw)
    fs.helper_members={n:record['members'][n] for n in pub['execution_helpers']}
    candidate=fs.read(ROUND+'/candidate_manifest.json')
    for name,digest in candidate['source_hashes'].items():assert fs.sha(name)==digest
    fs.add_attestation(candidate['production_PE'],candidate['production_PE_SHA'],'recorded production PE; never opened')
    fs.add_attestation(candidate['DLL'],candidate['DLL_SHA'],'recorded native DLL; never opened')
    for name in pub['required_configuration_files']:fs.allow_file(name)
    entry_binding=pub['current_entry_verification']
    assert fs.sha(entry_binding['receipt'])==entry_binding['receipt_SHA']
    assert fs.sha(entry_binding['promotion'])==entry_binding['promotion_SHA']
    entry=fs.read(entry_binding['receipt']);promotion=fs.read(entry_binding['promotion'])
    assert entry['status']=='PASS_BOUNDED_ZERO_NATIVE_ENTRY_CHECK' and entry['round']==137
    assert entry['all_default_GI_launches']==len(entry['all_S2_launches'])==28
    assert entry['new_Optimize']==entry['vendor_DLL_loads']==entry['formal_performance_samples_added']==0
    for key,name in [('entry_script_SHA','scripts/paper_s2.py'),('verifier_script_SHA','scripts/verify_paper_s2.py'),
        ('entry_helper_SHA','scripts/round137_entry.py'),('config_SHA','config/gi_tbc_round137.json'),
        ('legacy_config_SHA','config/paper_s2.json')]:assert entry[key]==fs.sha(name)
    assert entry['candidate_manifest_SHA']==fs.sha(ROUND+'/candidate_manifest.json')
    assert entry['matrix_SHA']==fs.sha(ROUND+'/matrix_frozen.json')
    assert entry['promotion_receipt_SHA']==entry_binding['promotion_SHA']
    assert promotion['config_SHA']==entry['config_SHA'] and promotion['paper_entry_after_SHA']==entry['entry_script_SHA']
    assert promotion['verifier_after_SHA']==entry['verifier_script_SHA']
    config=fs.read('config/gi_tbc_round137.json');legacy=fs.read('config/paper_s2.json')
    assert config['historical_argv_provenance']==legacy['authority'] and entry['historical_argv_provenance_matches_immutable_legacy_authority']
    assert entry['legacy_config_SHA']==candidate['config_SHA']
    # Admit only the exact current physical/progress dependencies, including
    # known inputs outside this round; never allow whole historical trees.
    for group in fs.read(ROUND+'/matrix_frozen.json')['groups']:
        launch=group['launch'];fs.allow_file(launch['panel']['input_path'])
        assert launch['version']=='candidate' and launch['command'][0]==candidate['production_PE']
        result=fs.read(fs.resolve(launch['destination'])/'result.json')
        if result.get('gurobi_progress_path'):fs.allow_file(result['gurobi_progress_path'])
    fs.publication=pub;return pub

def replay_arm(fs,reader,launch,identity):
    tick=time.perf_counter();d=fs.Path(launch['destination'])
    assert not fs.overlay and not fs.allowed_writes
    names=list(DERIVED)
    if launch['arm']=='M-B':names.append('round137_control_audit.json')
    stored={name:fs.raw(d/name) for name in names};total=fs.read(d/'arm_total_receipt.json')
    clock=importlib.import_module('round115_common').clock_evidence(d,launch)
    assert clock['T_verify']==total['T_verify'] and clock['T_total']==total['T_total']
    fs.allowed_writes={str(fs.resolve(d/name)) for name in (*names,'round134_verification_failure.json')}
    # Execute the exact published wrapper's checks and scoped model/AP adapters,
    # then obtain its unchanged full R135 verifier without invoking it yet.
    source=inspect.getsource(reader.verify);needle='return run(launch,identity)'
    assert source.count(needle)==1
    adapted=source.replace(needle,'return run')
    ns=dict(vars(reader));exec(compile(adapted,str(reader.__file__)+'::portable_factory','exec'),ns)
    configured=ns['verify'](launch,identity)
    module=types.SimpleNamespace(**dict(configured.__globals__,verify=configured))
    cloned,transport=engine.clone_replay(module,fs,total,tick)
    transport['Round137_wrapper_factory']=dict(original_SHA=engine.digest(source.encode()),
        adapted_SHA=engine.digest(adapted.encode()),only_change='Return configured original verifier for the existing clock/path/write transport; do not call it twice',
        all_actual_controls_A_B_AP_compact_and_physical_predicates_retained=True)
    try:
        output=cloned(launch,identity);compared=engine.compare_derived(fs,d,stored);e=output['arm']
        return dict(position=launch['global_launch_number'],arm_id=launch['arm_id'],method=launch['method'],seed=launch['seed'],
            certificate=e['certificate'],performance_eligible=e['performance_eligible'],U=e['U'],L=e['L'],
            original_T_produce=e['T_produce'],original_T_cert=e['T_cert'],original_T_verify=e['T_verify'],original_T_total=e['T_total'],
            compared_derived=compared,transport=transport,pure_replay_seconds=time.perf_counter()-tick)
    finally:fs.overlay.clear();fs.allowed_writes.clear()

def mathematical_checks(fs):
    core=importlib.import_module('round108_reader');manifest=fs.read(ROUND+'/input_manifest.json');rows=manifest['roles']
    assert len(rows)==20 and len({p['input_sha256'] for p in rows})==16
    resource=[p for p in rows if p['module']=='B2'];floors=[]
    for p in resource:
        a=core.evidence.instance(fs.Path(fs.root),p);s=sum(a['D'][1:])-sum(a['b'][1:])
        omega=sum(a['w'][1:]);assert s>0 and min(a['w'][1:])>0
        floor=p['lambda']*min(a['w'][i]/a['D'][i] for i in range(1,p['V']+1))*s
        assert abs(floor-p['positive_objective_floor'])<=1e-12 and abs(p['lambda']*omega-1)<=1e-12
        floors.append(dict(role=p['id'],shortage=s,Omega=omega,positive_floor=floor))
    T_design=[]
    for base in sorted({p['base_id'] for p in resource}):
        pp=sorted([p for p in resource if p['base_id']==base],key=lambda p:p['T_seconds'])
        assert len(pp)==2 and pp[0]['T_seconds']<pp[1]['T_seconds']
        for key in ['input_path','input_sha256','lambda','Q_vector','pickup_seconds','drop_seconds']:assert pp[0][key]==pp[1][key]
        data=core.evidence.instance(fs.Path(fs.root),pp[0]);p0=pp[0]
        radius=max(math.hypot(data['xy'][i][0]-data['xy'][0][0],data['xy'][i][1]-data['xy'][0][1]) for i in range(1,p0['V']+1))
        surplus=sum(max(data['b'][i]-data['D'][i],0) for i in range(1,p0['V']+1))
        T_base=2*radius/1.5+120*surplus/p0['M']
        T1=300*math.ceil(max(1800,.75*T_base)/300);T2=300*math.ceil(1.5*T1/300)
        assert [p['T_seconds'] for p in pp]==[T1,T2]
        T_design.append(dict(base=base,maximum_depot_radius=radius,positive_initial_surplus=surplus,M=p0['M'],
            T_base=T_base,T1=T1,T2=T2,uses_serialized_inputs_not_solver_outcomes=True))
    groups=fs.read(ROUND+'/matrix_frozen.json')['groups']
    weighted_roles={g['launch']['panel']['physical_configuration_id'] for g in groups if g['stage']=='B3'}
    assert weighted_roles=={'R-B20-S-T1','R-X35-S-T2'}
    weighted={}
    for group in groups:
        p=group['launch']['panel']
        if group['stage']=='B3' or group['stage']=='B2' and p['id'] in weighted_roles:
            weighted[p['input_sha256'],p['T_seconds'],p['lambda']]=p
    assert len(weighted)==6
    weight_points=[]
    for p in sorted(weighted.values(),key=lambda p:(p['V'],p['rho'])):
        data=core.evidence.instance(fs.Path(fs.root),p);omega=sum(data['w'][1:])
        shortage=sum(data['D'][1:])-sum(data['b'][1:]);assert shortage>0 and min(data['w'][1:])>0
        rho=p['lambda']*omega;floor=p['lambda']*min(data['w'][i]/data['D'][i] for i in range(1,p['V']+1))*shortage
        assert p['rho'] in [.5,1,2] and abs(rho-p['rho'])<=1e-12
        assert abs(omega-p['Omega'])<=1e-12 and abs(floor-p['positive_objective_floor'])<=1e-12
        weight_points.append(dict(role=p['id'],rho=rho,Omega=omega,T=p['T_seconds'],shortage=shortage,positive_floor=floor))
    root=fs.Path(fs.root/ROUND/'qualification/matrices_v2')
    baseline=core.lp_model(root/'off/original.lp');assert baseline==core.lp_model(root/'historical-off/original.lp')
    before=collections.Counter(baseline['rows']);deltas={}
    for variant in ['no-ab','no-cr','no-cg']:
        m=core.lp_model(root/variant/'original.lp');removed=before-collections.Counter(m['rows'])
        assert not (collections.Counter(m['rows'])-before) and removed
        assert m['objective']==baseline['objective']
        for n in m['order']:assert m['bounds'][n]==baseline['bounds'][n] and m['types'][n]==baseline['types'][n]
        if variant=='no-ab':assert sum(removed.values())==30 and set(m['order'])==set(baseline['order'])
        deltas[variant]=sum(removed.values())
    return dict(positive_floors=floors,transparent_T_design=T_design,effective_weight_points=weight_points,
        dual_T_same_other_data=True,default_off_equals_accepted=True,deletion_row_counts=deltas,Optimize=0)

def check(root,local=False):
    tick=time.perf_counter();fs=CurrentRoot(root)
    if local:assert engine.native_key(fs.root)==engine.native_key(RECORDED)
    else:assert not (fs.root/'.git').exists()
    pub=source_publication(fs);records=[];matrix=fs.read(ROUND+'/matrix_frozen.json')
    assert matrix['candidate_manifest_SHA']==fs.sha(ROUND+'/candidate_manifest.json')
    assert matrix['experiment_plan_SHA']==fs.sha(ROUND+'/experiment_plan.json')
    assert matrix['input_manifest_SHA']==fs.sha(ROUND+'/input_manifest.json')
    for name,digest in matrix['helpers'].items():
        assert pub['source_bundle']['members'][name]==digest and fs.sha(name)==digest
    with engine.closed_helpers(fs):
        reader=importlib.import_module('round137_read')
        assert fs.sha(reader.__file__)==pub['source_bundle']['members']['scripts/round137_read.py']
        for group in matrix['groups']:
            path=fs.root/ROUND/group['group']/'identity.json'
            assert fs.sha(path)==group['identity_SHA'];identity=fs.read(path)
            assert identity['launches']==[group['launch']]
            assert identity['candidate_manifest_SHA']==matrix['candidate_manifest_SHA']
            assert identity['prereg_sha256']==matrix['experiment_plan_SHA']
            records.append(replay_arm(fs,reader,group['launch'],identity))
        mathematics=mathematical_checks(fs)
        account=importlib.import_module('round137_common').budget()
        recorded=fs.read(ROUND+'/reports/summary.json')['budget']
        assert account['G1_seconds']==recorded['G1_seconds'] and not account['unclosed']
        assert account['G1_seconds']<=216000 and account['nested_H_LP_MIP_Work_not_added']
    reported={r['arm_id']:r for r in fs.read(ROUND+'/reports/arms.json')}
    assert len(records)==len(reported)==120 and {r['arm_id'] for r in records}==set(reported)
    for r in records:
        a=reported[r['arm_id']]
        for key in ['method','certificate','performance_eligible','U','L']:assert a[key]==r[key]
        assert a['signed_gap']==r['U']-r['L']
        for key in ['T_produce','T_cert','T_verify','T_total']:assert a[key]==r['original_'+key]
    summary=fs.read(ROUND+'/reports/summary.json');plan=fs.read(ROUND+'/experiment_plan.json')
    assert summary['registered']==summary['completed']==120 and not summary['missing']
    assert set(summary['completed_positions'])==set(range(1,121))
    assert sum(g['launch']['cap_seconds'] for g in matrix['groups'])==plan['total_caps_seconds']==174600
    objective_keys={(g['launch']['panel']['input_sha256'],g['launch']['panel']['T_seconds'],g['launch']['panel']['lambda']) for g in matrix['groups']}
    assert len(objective_keys)==summary['objective_configurations']==24
    for stage,planned in plan['stages'].items():
        current=[r for r in records if matrix['groups'][r['position']-1]['stage']==stage]
        assert len(current)==planned['positions']==summary['stages'][stage]['completed']
        counts=dict(collections.Counter(r['method'] for r in current if r['certificate'] and r['performance_eligible']))
        assert counts==summary['stages'][stage]['certificates']
    return dict(schema='round137-finite-current-only-public-replay-v1',passed=True,local_preflight=local,
        formal_positions=120,registered_positions=120,records=records,mathematical_replay=mathematics,
        recomputed_budget=account,Optimize=0,compile=0,vendor_DLL_loads=0,Git_calls=0,subprocess_calls=0,
        original_measured_clocks_preserved=True,restored_raw_read_only=True,historical_whole_campaigns_replayed=0,
        source_publication_SHA=fs.sha(ROUND+'/source_publication.json'),attestations_used=list(fs.attestations_used.values()),
        seconds=time.perf_counter()-tick)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);p.add_argument('--local-preflight',action='store_true');a=p.parse_args()
    result=check(a.root,a.local_preflight);a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,positions=result['formal_positions'],seconds=result['seconds'],Optimize=0)))
