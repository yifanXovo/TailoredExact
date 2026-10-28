"""Narrow independent saved-source/result amendment check. No native execution."""
from pathlib import Path
import hashlib,json,math,sys
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round137'
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'scripts'))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    current=read(OUT/'matrix_frozen.json');old=read(OUT/'infra/matrix_before_compact_reader_fix.json')
    x,y=json.loads(json.dumps(current)),json.loads(json.dumps(old))
    assert x['helpers'].pop('scripts/round137_read.py')==sha(ROOT/'scripts/round137_read.py')
    y['helpers'].pop('scripts/round137_read.py')
    assert x==y,'Amendment may change only the scoped reader helper binding'
    assert sha(OUT/'matrix_frozen.json')=='26f295da36097cd662b9c2ca049ab2452f0b295dfcdb12dd4b726ff25190c894'
    for name in ['experiment_plan','input_manifest','candidate_manifest']:
        assert current[name+'_SHA']==sha(OUT/(name+'.json'))
    candidate=read(OUT/'candidate_manifest.json')
    assert candidate['production_PE_SHA']==sha(candidate['production_PE'])
    for path,digest in candidate['source_hashes'].items():assert sha(ROOT/path)==digest,path
    for path,digest in current['helpers'].items():assert sha(ROOT/path)==digest,path
    group=current['groups'][0];identity=read(OUT/group['group']/'identity.json')
    assert sha(OUT/group['group']/'identity.json')==group['identity_SHA']
    launch=group['launch'];assert launch==identity['launches'][0]
    d=Path(launch['destination']);repair=read(OUT/'repair/verification_001/receipt.json')
    assert repair['PASS'] and repair['Optimize']==0 and repair['original_native_production_not_repeated']
    assert repair['corrected_reader_SHA']==sha(ROOT/'scripts/round137_read.py')
    for name,digest in repair['raw_SHA_before_and_after'].items():assert sha(d/name)==digest,name
    producer=read(d/'producer_receipt.json');close=read(d/'verification_closeout.json')
    assert producer['native_stopped_no_reentry'] and producer['T_produce']<=launch['cap_seconds']
    assert close['necessary_verification_complete'] and close['implementation_qualified']
    assert close['producer_receipt_SHA']==sha(d/'producer_receipt.json')
    assert close['audit_SHA']==sha(d/'audit.json')
    audit=read(d/'audit.json');endpoint=read(d/'round135_endpoint.json')
    assert audit['passed'] and audit['evidence_complete'] and audit['Optimize']==0
    assert not audit['source_rejections']
    assert endpoint==repair['endpoint']
    assert endpoint['performance_eligible'] and endpoint['native_proof_qualified']
    assert not endpoint['certificate'] and endpoint['T_cert'] is None
    assert endpoint['T_produce']==producer['T_produce']
    assert math.isclose(endpoint['T_total'],endpoint['T_produce']+endpoint['T_verify'],abs_tol=1e-9)
    assert endpoint['T_verify']>repair['seconds'],'Keep real repair delay; no clock backfill'
    import round108_reader as core
    import round137_read
    physical=core.full_fleet(ROOT,launch['panel'],read(d/'result.json'))
    assert physical==audit['physical']
    assert abs(physical['F']-endpoint['U'])<=1e-12
    model_path=d/'compact.lp'
    assert sha(model_path)==launch['panel']['reference']['canonical_sha256']
    context=round137_read.ArmModels();fact,model=context.model_contract(ROOT,launch['panel'],model_path,'P-GRB')
    assert fact['quantity_type']=='I' and fact['frozen_A_B_rows_checked']==0
    assert not any(n.startswith('state_') for n in model['order'])
    context.clear()
    ap=audit['model_contracts'][0]['model']['AP_contract']
    assert ap['not_applicable_original_compact'] and ap['original_R134_contracts_retained'] and not ap['enabled']
    quality=audit['native_quality'][0];event_path=d/'journal'/f'event_{quality["sequence"]}.json'
    event=read(event_path);commit=event_path.with_suffix('.commit').read_text().split()
    assert commit[0]=='NEJ1' and int(commit[1])==quality['sequence']
    assert int(commit[3])==len(event_path.read_bytes()) and commit[4]==sha(event_path)
    assert event['kind']=='native_quality' and event['call']==1 and event['native_status']==9
    assert event['optimize_return_code']==0 and event['solution_count_read_return_code']==0
    assert event['ObjBoundC']==endpoint['L']
    assert quality['ObjBoundC']==event['ObjBoundC'] and quality['ObjVal']==event['ObjVal']
    fees=[(p,read(p)) for p in (OUT/'fees').glob('*/launch.json')]
    native=[(p,l) for p,l in fees if l['kind'] in ('native','diagnostic')]
    assert len(native)==1 and native[0][0].parent.name=='arm_001'
    fee=read(native[0][0].parent/'receipt.json')
    assert fee['exit_code']==1 and fee['exit_observed'] and not fee['timeout']
    assert sum(Path(g['launch']['destination']).exists() for g in current['groups'])==1
    result=dict(PASS=True,matrix_SHA=sha(OUT/'matrix_frozen.json'),only_reader_helper_binding_changed=True,
        production_source_commit=candidate['source_commit'],PE_SHA=candidate['production_PE_SHA'],
        actual_compact_canonical_and_integer_types=True,AP_inapplicable_only_original_compact=True,
        original_six_raw_hashes_unchanged=True,original_producer_not_repeated=True,
        actual_physical_fleet_replayed=True,actual_committed_native_quality_bound_checked=True,
        first_P=dict(U=endpoint['U'],L=endpoint['L'],certificate=False,T_cert=None,
            T_produce=endpoint['T_produce'],T_verify=endpoint['T_verify'],T_total=endpoint['T_total']),
        charged_native_seconds=fee['G1_seconds'],repair_replay_seconds=repair['seconds'],
        reviewer_Optimize=0,reviewer_compilation=0,reviewer_commercial_native_loads=0)
    (OUT/'review/compact_reader_amendment_evidence.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
