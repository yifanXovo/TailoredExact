"""Replay only entered R135 positions and two AP roots; no native execution."""
from __future__ import annotations
import argparse, collections, gzip, hashlib, importlib, json, math, pathlib, sys, time, zipfile
import round133_portable_check as engine

ROUND='results/unified_exact_round135'
RECORDED='E:/codes/ExactEBRP-work/worktrees/round135'
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

def entered(fs):
    return set(fs.read(ROUND+'/reports/summary.json')['completed_positions'])

def source_publication(fs):
    pub=fs.read(ROUND+'/source_publication.json');record=pub['source_bundle']
    fs.allow_file(record['path']);path=fs.resolve(record['path'])
    assert fs.sha(path)==record['SHA256'] and path.stat().st_size==record['bytes']
    with zipfile.ZipFile(path) as z:
        assert len(z.namelist())==len(set(z.namelist()))==len(record['members'])
        assert set(z.namelist())==set(record['members'])
        for name,digest in record['members'].items():
            rel=pathlib.PurePosixPath(name)
            assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name
            assert rel.suffix.lower() not in {'.exe','.dll','.o','.obj','.a','.lib','.lic','.ttf','.otf'}
            raw=z.read(name);assert hashlib.sha256(raw).hexdigest()==digest
            fs.attach(name,raw)
    fs.helper_members={n:record['members'][n] for n in pub['execution_helpers']}
    candidate=fs.read(ROUND+'/candidate_manifest.json')
    for name,digest in candidate['source_hashes'].items():assert fs.sha(name)==digest
    fs.add_attestation(candidate['production_PE'],candidate['production_PE_SHA'],'frozen production PE; never opened')
    fs.add_attestation(candidate['DLL'],candidate['DLL_SHA'],'qualified native DLL; never opened')
    for name in pub['required_configuration_files']:fs.allow_file(name)
    done=entered(fs)
    for stage in ('C','D'):
        for group in fs.read(ROUND+f'/{stage}_matrix_frozen.json')['groups']:
            if f"{stage}{group['position']:02}" not in done:continue
            launch=group['launch'];fs.allow_file(launch['panel']['input_path'])
            assert launch['version']=='candidate' and launch['command'][0]==candidate['production_PE']
            result=fs.read(fs.resolve(launch['destination'])/'result.json')
            if result.get('gurobi_progress_path'):fs.allow_file(result['gurobi_progress_path'])
    for role in ('K-20-S','K-35-U'):
        scope=fs.read(ROUND+'/roots/'+role+'/inherited/scope.json')
        fs.allow_file(scope['panel']['input_path'])
    fs.publication=pub
    return pub

def replay_arm(fs,reader,launch,identity):
    tick=time.perf_counter();d=fs.Path(launch['destination'])
    assert not fs.overlay and not fs.allowed_writes
    stored={name:fs.raw(d/name) for name in DERIVED};total=fs.read(d/'arm_total_receipt.json')
    clock=importlib.import_module('round115_common').clock_evidence(d,launch)
    assert clock['T_verify']==total['T_verify'] and clock['T_total']==total['T_total']
    fs.allowed_writes={str(fs.resolve(d/name)) for name in (*DERIVED,'round134_verification_failure.json')}
    cloned,transport=engine.clone_replay(reader,fs,total,tick)
    try:
        output=cloned(launch,identity);compared=engine.compare_derived(fs,d,stored);e=output['arm']
        return dict(arm_id=launch['arm_id'],method=launch['variant'],seed=launch['seed'],repeat=launch['repeat'],
            certificate=e['certificate'],basis=e.get('certificate_basis'),U=e['U'],L=e['L'],
            original_T_produce=e['T_produce'],original_T_cert=e['T_cert'],
            original_T_verify=e['T_verify'],original_T_total=e['T_total'],
            compared_derived=compared,transport=transport,pure_replay_seconds=time.perf_counter()-tick)
    finally:fs.overlay.clear();fs.allowed_writes.clear()

def replay_roots(fs):
    reader=importlib.import_module('round108_reader');audit=importlib.import_module('round135_ap_audit')
    roots=[]
    for role in ('K-20-S','K-35-U'):
        folder=fs.Path(fs.root/ROUND/'roots'/role);scope=fs.read(folder/'inherited/scope.json')
        old=reader.lp_model(folder/'inherited/current_export/original.lp')
        off=reader.lp_model(folder/'off/original.lp');ap=reader.lp_model(folder/'ap/original.lp')
        assert off==old
        assert ap['bounds']==old['bounds'] and ap['types']==old['types'] and ap['objective']==old['objective']
        assert not (collections.Counter(old['rows'])-collections.Counter(ap['rows']))
        added=collections.Counter(ap['rows'])-collections.Counter(old['rows']);assert sum(added.values())==1
        data=reader.evidence.instance(fs.Path(fs.root),scope['panel'])
        assert fs.sha(scope['panel']['input_path'])==scope['panel']['input_sha256']
        offaudit=audit.contract(old,data,False);apaudit=audit.contract(ap,data,True)
        point_path=fs.resolve(folder/'LP/solution.json.gz')
        with gzip.open(point_path,'rt',encoding='utf-8') as stream:point=json.load(stream)
        maximum_row=0.
        for terms,sense,rhs in ap['rows']:
            lhs=math.fsum(c*point[n] for n,c in terms)
            violation=abs(lhs-rhs) if sense=='=' else max(0.,lhs-rhs) if sense=='<=' else max(0.,rhs-lhs)
            maximum_row=max(maximum_row,violation)
        maximum_bound=max(max(lo-point[n],point[n]-hi,0.) for n,(lo,hi) in ap['bounds'].items())
        objective=math.fsum(c*point[n] for n,c in ap['objective'][0])+ap['objective'][1]
        result=fs.read(folder/'LP/result.json')
        assert maximum_row<=1e-6 and maximum_bound<=1e-6
        assert abs(objective-result['L_AP'])<=1e-7 and result['LP_Optimize']==1 and result['MIP_Optimize']==0
        assert result['preserves_IND_gain'] and abs(result['L_AP']-result['L_IND_reused'])<=1e-7
        roots.append(dict(role=role,AP_contract=apaudit,off_contract=offaudit,max_row_violation=maximum_row,
            max_bound_violation=maximum_bound,objective=objective,recorded_quality=result['quality'],
            original_and_IND_reused=True,new_LP_Optimize_not_repeated=True,numerical_optimality_not_reproved=True))
    return dict(roots=roots,AP_exact_coefficients_and_saved_residuals_checked=True,new_Optimize=0)

def check(root,local=False):
    tick=time.perf_counter();fs=CurrentRoot(root)
    if local:assert engine.native_key(fs.root)==engine.native_key(RECORDED)
    else:assert not (fs.root/'.git').exists()
    pub=source_publication(fs);records=[];done=entered(fs)
    with engine.closed_helpers(fs):
        reader=importlib.import_module('round135_read')
        assert fs.sha(reader.__file__)==pub['source_bundle']['members']['scripts/round135_read.py']
        for stage in ('C','D'):
            for group in fs.read(ROUND+f'/{stage}_matrix_frozen.json')['groups']:
                if f"{stage}{group['position']:02}" not in done:continue
                identity=fs.read(fs.root/ROUND/group['group']/'identity.json')
                assert fs.sha(fs.root/ROUND/group['group']/'identity.json')==group['identity_SHA']
                records.append(replay_arm(fs,reader,group['launch'],identity))
        mathematics=replay_roots(fs)
        account=importlib.import_module('round135_common').budget()
        recorded=fs.read(ROUND+'/reports/summary.json')['budget']
        assert account['G1_seconds']==recorded['G1_seconds'] and not account['unclosed']
        assert account['G1_seconds']<=28800 and account['nested_H_LP_MIP_Work_not_added']
        assert account['G1_seconds']+account['separately_reported_seconds']<=28800
    assert len(records)==len(done)
    reported={r['arm_id']:r for r in fs.read(ROUND+'/reports/arms.json')}
    assert set(reported)=={r['arm_id'] for r in records}
    for r in records:
        a=reported[r['arm_id']]
        assert a['method']==r['method'] and a['certificate']==r['certificate']
        assert a['U']==r['U'] and a['L']==r['L'] and a['signed_gap']==r['U']-r['L']
        for key in ('T_produce','T_cert','T_verify','T_total'):assert a[key]==r['original_'+key]
    counts=dict(collections.Counter(r['method'] for r in records if r['certificate']))
    assert counts==fs.read(ROUND+'/reports/summary.json')['certificate_counts']
    return dict(schema='round135-current-only-public-policy-replay-v1',passed=True,local_preflight=local,
        formal_positions=len(records),registered_positions=32,not_entered_positions=32-len(records),
        records=records,mathematical_replay=mathematics,recomputed_budget=account,Optimize=0,compile=0,vendor_DLL_loads=0,
        Git_calls=0,subprocess_calls=0,original_measured_clocks_preserved=True,restored_raw_read_only=True,
        attestations_used=list(fs.attestations_used.values()),source_publication_SHA=fs.sha(ROUND+'/source_publication.json'),
        aggregate_variant_certificates_recomputed=counts,
        historical_whole_campaigns_replayed=0,seconds=time.perf_counter()-tick)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True)
    p.add_argument('--receipt',type=pathlib.Path,required=True);p.add_argument('--local-preflight',action='store_true');a=p.parse_args()
    r=check(a.root,a.local_preflight);a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,positions=r['formal_positions'],seconds=r['seconds'],Optimize=0)))
