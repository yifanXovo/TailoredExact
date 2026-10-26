"""Current-only read-only replay using the established R133 closed-root engine.

The same current reader and pure accepted-H adapter execute on restored bytes.
Native assets are historical hash attestations, never opened or loaded. Derived
JSON is regenerated only in memory; measured clocks and restored raw stay fixed.
"""
from __future__ import annotations
import argparse,collections,gzip,hashlib,importlib,io,json,math,pathlib,sys,time,zipfile
from fractions import Fraction as F
import round133_portable_check as engine

ROUND='results/unified_exact_round134'
RECORDED='E:/codes/ExactEBRP-work/worktrees/round134'
DERIVED=('audit.json','native_claims.json','claim_rejections.json','independent_evidence.json',
         'verification_closeout.json','arm_total_receipt.json','round134_endpoint.json')

class CurrentRoot(engine.ClosedRoot):
    def __init__(self,root):
        self.root=engine.RealPath(root).resolve(strict=True)
        self.recorded=pathlib.PureWindowsPath(RECORDED)
        self.sources={};self.overlay={};self.allowed_writes=set();self.attestations={}
        self.attestations_used={};self.read_paths=set();self.modules={};self.git_sources={}
        self.derived_writes=[];self.helper_members={};self.publication=None
        self.allowed_files=set();self.allowed_trees=set();self.allowed_dirs={str(self.root)}
        self.allow_tree(self.root/ROUND)

def source_publication(fs):
    pub=fs.read(ROUND+'/source_publication.json');record=pub['source_bundle']
    fs.allow_file(record['path']);path=fs.resolve(record['path'])
    assert fs.sha(path)==record['SHA256'] and path.stat().st_size==record['bytes']
    with zipfile.ZipFile(path) as archive:
        assert len(archive.namelist())==len(set(archive.namelist()))==len(record['members'])
        assert set(archive.namelist())==set(record['members'])
        for name,digest in record['members'].items():
            rel=pathlib.PurePosixPath(name)
            assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name
            assert rel.suffix.lower() not in {'.exe','.dll','.o','.obj','.a','.lib','.lic','.ttf','.otf'}
            raw=archive.read(name);assert hashlib.sha256(raw).hexdigest()==digest
            fs.attach(name,raw)
    fs.helper_members={name:record['members'][name] for name in pub['execution_helpers']}
    candidate=fs.read(ROUND+'/candidate_manifest.json')
    for name,digest in candidate['source_hashes'].items():assert fs.sha(name)==digest
    fs.add_attestation(candidate['production_PE'],candidate['production_PE_SHA'],'frozen current production PE')
    fs.add_attestation(candidate['DLL'],candidate['DLL_SHA'],'unchanged production Gurobi DLL')
    for name in pub['required_configuration_files']:fs.allow_file(name)
    for stage in ('C','D'):
        matrix=fs.read(ROUND+f'/{stage}_matrix_frozen.json')
        for group in matrix['groups']:
            launch=group['launch'];fs.allow_file(launch['panel']['input_path'])
            assert launch['version']=='candidate' and launch['command'][0]==candidate['production_PE']
            result=fs.read(fs.resolve(launch['destination'])/'result.json')
            if result.get('gurobi_progress_path'):fs.allow_file(result['gurobi_progress_path'])
    fs.allow_file('results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip')
    for root in fs.read(ROUND+'/math/root_plan.json')['roots']:
        scope=fs.read(ROUND+'/math/roots/'+root['role']+'/scope.json')
        fs.allow_file(scope['panel']['input_path'])
    fs.publication=pub
    return pub

def replay_arm(fs,reader,launch,identity):
    tick=time.perf_counter();d=fs.Path(launch['destination'])
    assert not fs.overlay and not fs.allowed_writes
    stored={name:fs.raw(d/name) for name in DERIVED}
    total=fs.read(d/'arm_total_receipt.json')
    clock=importlib.import_module('round115_common').clock_evidence(d,launch)
    assert clock['T_verify']==total['T_verify'] and clock['T_total']==total['T_total']
    fs.allowed_writes={str(fs.resolve(d/name)) for name in (*DERIVED,'round134_verification_failure.json')}
    cloned,transport=engine.clone_replay(reader,fs,total,tick)
    try:
        output=cloned(launch,identity)
        compared=engine.compare_derived(fs,d,stored)
        endpoint=output['arm']
        return dict(arm_id=launch['arm_id'],method=launch['method'],seed=launch['seed'],repeat=launch['repeat'],
            lambda_value=launch['panel']['lambda'],certificate=endpoint['certificate'],
            basis=endpoint.get('certificate_basis','qualified_paid_start_original_compact_native_certificate' if endpoint['certificate'] else 'qualified_paid_start_original_compact_open'),
            native_qualified=endpoint['native_proof_qualified'],U=endpoint['U'],L=endpoint['L'],
            original_T_produce=endpoint['T_produce'],original_T_cert=endpoint['T_cert'],
            original_T_verify=endpoint['T_verify'],original_T_total=endpoint['T_total'],
            compared_derived=compared,transport=transport,pure_replay_seconds=time.perf_counter()-tick)
    finally:fs.overlay.clear();fs.allowed_writes.clear()

def replay_math(fs):
    count=importlib.import_module('round134_count_bound')
    stored=fs.read(ROUND+'/math/tiny_exact.json')
    path=fs.resolve(ROUND+'/math/tiny_exact.json');fs.allowed_writes={str(path)}
    try:
        count.tiny();actual=fs.read(path)
        for key in ('status','cases','dependencies','carrier_SHA256','source_SHA256'):
            assert actual[key]==stored[key],('tiny exact replay differs',key)
    finally:fs.overlay.clear();fs.allowed_writes.clear()
    reader=importlib.import_module('round108_reader');roots=[]
    for role in ('K-20-S','K-35-U'):
        folder=fs.Path(fs.root/ROUND/'math/roots'/role)
        scope=fs.read(folder/'scope.json');original=reader.lp_model(folder/'current_export/original.lp')
        data=reader.evidence.instance(fs.Path(fs.root),scope['panel'])
        assert fs.sha(scope['panel']['input_path'])==scope['panel']['input_sha256']
        assert sum(data['b'][1:])==scope['panel']['total_initial']
        assert fs.sha(folder/'current_export/original.lp')==scope['current_matrix_SHA']
        assert scope['exact_current_and_old_canonical_matrix_equal'] is True
        layer_checks=[]
        for layer in range(3):
            target=folder/f'layer{layer}';c=fs.read(target/'construction.json');r=fs.read(target/'result.json')
            supports={int(i):ys for i,ys in c['supports'].items()};ratios={int(i):F(v) for i,v in c['ratio_coefficients'].items()}
            assert set(supports)==set(ratios)==set(range(1,scope['panel']['V']+1))
            assert c['B']==scope['panel']['total_initial']
            assert all(ys and all(isinstance(y,int) and 0<=y<=data['c'][i] for y in ys) for i,ys in supports.items())
            recomputed=count.count_coefficients(supports,ratios,c['B'])
            assert json.loads(json.dumps(recomputed['thresholds']))==c['thresholds'] and not recomputed['inventory_domain_infeasible']
            for i,row in c['loaded_ratio_rows'].items():
                terms=tuple(sorted((n,float(F(v))) for n,v in row['coefficients'].items()))
                assert (terms,'=',0.) in original['rows']
            for (i,y),value in recomputed['coefficients'].items():
                name=f'state_{i}_{y}'
                if not value:assert name not in c['TC_coefficients'];continue
                actual=c['TC_coefficients'][name]
                assert F(actual['exact'])==value and actual['written']==count.downward(value)
                assert F(actual['written_exact'])==F(actual['written'])<=value
            for i,ys in supports.items():
                for y in ys:
                    actual=c['old_penalty_coefficients'][f'state_{i}_{y}'];value=abs(ratios[i]*y-1)
                    assert F(actual['exact'])==value and F(actual['written'])<=value
            assert r['LP_only'] and r['MIP_Optimize']==0 and r['LP_Optimize']==1
            assert r['source_matrix_SHA']==fs.sha(folder/'current_export/original.lp')
            assert r['construction_SHA']==fs.sha(target/'construction.json')
            assert r['before']['columns']==r['after']['columns']
            if r['optimal']:
                assert r['Status']==2
                assert r['qualification']=='NUMERICAL_OPTIMAL_LP' and r['numerical_lower']==r['primal_objective']
                assert all(r['quality'][n] is not None and math.isfinite(r['quality'][n]) and 0<=r['quality'][n]<=1e-6 for n in ('ConstrVio','BoundVio','DualVio'))
            if (target/'solution.json.gz').exists():
                with gzip.open(target/'solution.json.gz','rt',encoding='utf-8') as stream:point=json.load(stream)
                added=fs.read(target/'added_rows.json');checks=[]
                for row in added:
                    lhs=math.fsum(a*point[n] for n,a in row['lhs'].items())
                    rhs=math.fsum(a*point[n] for n,a in row['rhs_coefficients'].items())
                    checks.append(dict(name=row['name'],lhs=lhs,rhs=rhs,signed_slack=lhs-rhs))
                assert checks==r['added_row_residuals']
            layer_checks.append(dict(layer=layer,numerical_lower=r['numerical_lower'],status=r['qualification'],
                exact_coefficient_regeneration=True,recorded_numerical_quality=r['quality'],
                native_numerical_optimality_not_reproved=True))
        roots.append(dict(role=role,layers=layer_checks,
            old_root_matrix_equality_is_preserved_export_attestation_not_old_matrix_replay=True))
    return dict(tiny_status=stored['status'],tiny_exact_cases=list(stored['cases']),roots=roots,
        root_scope_and_actual_coefficients_checked=True,native_Optimize=0)

def check(root,local=False,through=None):
    tick=time.perf_counter();fs=CurrentRoot(root)
    if local:assert engine.native_key(fs.root)==engine.native_key(RECORDED)
    else:assert not (fs.root/'.git').exists()
    pub=source_publication(fs);records=[]
    with engine.closed_helpers(fs):
        reader=importlib.import_module('round134_read')
        assert fs.sha(reader.__file__)==pub['source_bundle']['members']['scripts/round134_read.py']
        for stage in ('C','D'):
            for group in fs.read(ROUND+f'/{stage}_matrix_frozen.json')['groups']:
                if through is not None and (stage!='C' or group['position']>through):continue
                identity=fs.read(fs.root/ROUND/group['group']/'identity.json')
                assert fs.sha(fs.root/ROUND/group['group']/'identity.json')==group['identity_SHA']
                records.append(replay_arm(fs,reader,group['launch'],identity))
        mathematics=replay_math(fs) if through is None else None
    if through is None:assert len(records)==36
    return dict(schema='round134-current-only-public-policy-replay-v1',passed=True,
        local_preflight=local,partial_preflight_through=through,formal_positions=len(records),records=records,
        mathematical_replay=mathematics,Optimize=0,compile=0,vendor_DLL_loads=0,Git_calls=0,subprocess_calls=0,
        original_measured_clocks_preserved=True,restored_raw_read_only=True,
        attestations_used=list(fs.attestations_used.values()),source_publication_SHA=fs.sha(ROUND+'/source_publication.json'),
        historical_whole_campaigns_replayed=0,seconds=time.perf_counter()-tick)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True)
    p.add_argument('--local-preflight',action='store_true');p.add_argument('--through',type=int);a=p.parse_args()
    result=check(a.root,a.local_preflight,a.through)
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,positions=result['formal_positions'],seconds=result['seconds'],Optimize=0)))
