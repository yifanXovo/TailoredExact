"""One bound-to-raw publication repair. Never runs or changes performance code.

The actual P call has correct provenance but numerically incorrect lower claims.
Reject them, retain the originals, and prove the existing own full-domain floor.
This is not a generic fallback for another instance or an engine repair.
"""
from pathlib import Path
import copy, hashlib, math, sys
import round108_reader as core
read,write,sha=core.read,core.write,core.sha
REL=Path('results/unified_exact_round109')
SIDE=REL/'campaign/reader_recovery/main05_numerical01.json'
KEY=(15,'G50-C1',0,'P-GRB')

def key(launch):return (launch['number'],launch['id'],launch['seed'],launch['arm'])

def floor(lam,weights,targets,objective,bounds):
    assert math.isfinite(lam) and lam>=0
    assert all(math.isfinite(v) and v>=0 for v in weights)
    assert targets and all(math.isfinite(v) and v>0 for v in targets)
    terms,constant=objective;assert constant==0 and terms
    assert all(n=='G' or n.startswith('e_') for n,v in terms)
    assert all(math.isfinite(v) and v>=0 and bounds[n][0]>=0 for n,v in terms)
    assert dict(terms)['G']==1
    return 0.

def scope(call,completion,command,expected,model_SHA):
    assert command==expected and completion['returncode']==0 and completion['stop_reason']=='normal_return'
    assert all(type(call[k]) in [int,bool] for k in ['full_original','native_preconditions'])
    assert completion['within_cap'] and call['call']==1 and call['full_original']==1 and call['native_preconditions']==1
    assert call['model_scope']=='complete_original_compact_milp' and call['model_sha256']==model_SHA
    settings=dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    assert call['settings']==settings

def interval(lower,upper,cap):assert math.isfinite(lower) and math.isfinite(upper) and 0<lower<=upper<cap

def selected(arm,original,proof):
    assert arm['U']==original['U'] and arm['L']==0. and arm['gap']==arm['U']
    assert arm['certificate'] is False and original['certificate'] is False
    assert arm['complete_seconds'] is None and arm['native_call_bounds_mathematically_qualified'] is False
    assert arm['lower_bound_source']=='independently_proved_own_original_full_domain_nonnegative_floor'
    interval(*arm['complete_seconds_interval'],proof['cap_seconds'])

def facts(root):
    root=Path(root).resolve();out=root/REL;ident=read(out/'campaign/identity.json');candidate=read(out/'candidate_identity.json')
    launch=ident['launches'][14];assert key(launch)==KEY
    for relative,digest in candidate['source_bindings'].items():assert sha(root/relative)==digest
    for relative,digest in ident['helpers'].items():assert sha(root/relative)==digest
    assert ident['source_hashes']==candidate['source_bindings'] and ident['helpers']==candidate['helpers']
    d=core.portable(root,launch['destination']);p=launch['panel'];obs=read(d/'observations.json')
    contract=read(out/'review/numerical_recovery_contract_review01.json')
    assert contract['decision']=='CONDITIONAL_ACCEPT_READER_ONLY_RESOLUTION'
    assert contract['candidate_identity_SHA']==sha(out/'candidate_identity.json')
    assert contract['original_performance_admission_SHA']==sha(out/'review/performance_admission.json')
    diagnostic=out/'review/cross_arm_diagnosis02/audit.json';diag=read(diagnostic)
    assert sha(diagnostic)==contract['independent_diagnosis_SHA'] and diag['decision']=='ACCEPT_DIAGNOSIS'
    assert diag['cold_exact_binary64_feasible_objective_upper']+1e-7<diag['raw_native_L']
    witness=out/'review/cross_arm_diagnosis02/exact_binary64_matrix_witness.json'
    assert sha(witness)==contract['exact_cold_matrix_witness_SHA']
    model=d/'compact.lp';model_SHA=sha(model)
    assert model_SHA==p['reference']['canonical_sha256']==contract['affected_evidence']['canonical_model_SHA']
    reference=out/'campaign/reference'/p['id']/'original.lp';assert sha(reference)==model_SHA
    calls=[v['payload'] for v in obs if v['payload']['kind']=='call'];assert len(calls)==1
    completion=read(d/'completion.json');saved=read(d/'launch.json');scope(calls[0],completion,saved['command'],launch['command'],model_SHA)
    returned=[v['payload'] for v in obs if v['payload']['kind']=='returned'];assert len(returned)==1 and returned[0]['call']==1 and returned[0]['return_code']==0
    assert not (d/'whole_arm_receipt.json').exists(),'missing original exact clock must stay missing'
    model_info,m=core.model_contract(root,p,model,'P-GRB');q=core.evidence.instance(root,p)
    value=floor(p['lambda'],q['w'][1:],q['D'][1:],m['objective'],m['bounds'])
    raw_bounds=[v['payload'] for v in obs if v['payload']['kind']=='bound'];assert raw_bounds and all(v['call']==1 for v in raw_bounds)
    assert [v['sequence'] for v in raw_bounds if v['native_bound']>1e-7]==[52,53]
    receipt=read(out/'fees/main05/receipt.json');assert receipt['exit_code']==1 and receipt['actual_native_children_with_launch']==3
    assert sha(out/'fees/main05/receipt.json')==contract['original_main05_fee_receipt_SHA']
    assert 'offline contradictory cross-arm physical/native evidence' in (out/'fees/main05/failure.txt').read_text()
    previous=[read(core.portable(root,x['destination'])/'whole_arm_receipt.json')['complete_seconds'] for x in ident['launches'][12:14]]
    lower=completion['fully_observed_end_to_end_seconds'];unrounded=receipt['outer_seconds']-sum(previous)
    upper=math.ceil(unrounded*1e6)/1e6;interval(lower,upper,launch['cap_seconds'])
    assert [lower,upper]==contract['timing']['published_interval_seconds']
    files=[out/'candidate_identity.json',out/'campaign/identity.json',out/'protocol.json',out/'input_manifest.json',out/'review/performance_admission.json',
        out/'review/numerical_recovery_contract_review01.json',diagnostic,witness,out/'review/cross_arm_diagnosis02/source_at_execution.py',
        out/'fees/main05/receipt.json',out/'fees/main05/launch.json',out/'fees/main05/failure.txt',model,reference,root/p['input_path']]
    files += [d/n for n in ['launch.json','completion.json','observations.json','result.json','audit.json','native.log']]
    files += sorted((d/'journal').glob('*'))
    files += [core.portable(root,x['destination'])/'whole_arm_receipt.json' for x in ident['launches'][12:14]]
    result=read(d/'result.json');assert result['strict_certified_original_problem'] is False
    return dict(key=list(KEY),production_PE_SHA=candidate['production_PE_SHA'],DLL_SHA=candidate['DLL_SHA'],
        original_candidate_identity_SHA=sha(out/'candidate_identity.json'),all42_native_argv=[x['command'] for x in ident['launches']],
        production_source_bindings=candidate['source_bindings'],frozen_performance_helpers=ident['helpers'],
        raw_files={v.relative_to(root).as_posix():sha(v) for v in files},
        call=1,raw_bound_sequences=[v['sequence'] for v in raw_bounds],raw_positive_bound_sequences=[52,53],
        raw_final_native_L=result['native_mip_best_bound'],rejected_all_native_bounds_from_call=True,
        qualified_L=value,qualified_L_source='independently_proved_own_original_full_domain_nonnegative_floor',
        physical_floor_proof='Y>=0,D>0: true G>=0 including original G=0 zero denominator; lambda>=0 and omega>=0 give lambda*P>=0',
        cold_floor_proof='original cold objective constant0; G/e lower bounds and every objective coefficient nonnegative',
        own_objective_floor_does_not_use_ENS_witness=True,model_domain=model_info,
        exact_complete_seconds=None,complete_seconds_interval=[lower,upper],unrounded_recorded_upper=unrounded,cap_seconds=launch['cap_seconds'],
        original_missing_whole_receipt_preserved=True,later_repair_engineering_in_original_time_interval=False,
        original_failure_preserved=True,production_search_helpers_and_argv_changed=False,solver_calls=0,
        helper_SHA=sha(Path(__file__)),reader_SHA=sha(root/'scripts/round109_reader.py'))

def prepare(root):
    root=Path(root).resolve();value=facts(root);write(root/SIDE,value)
    print('Immutable known-call numerical rejection/floor/time-interval sidecar; zero native work.')

def verify(root):
    root=Path(root).resolve();saved=read(root/SIDE);assert saved==facts(root),'altered or missing numerical recovery evidence must HOLD'
    return saved

def endpoint(root,launch,ident,d,j,formal,original_endpoint):
    if not formal or key(launch)!=KEY:return original_endpoint(root,launch,ident,d,j,formal)
    proof=verify(root);ep=original_endpoint(root,launch,ident,d,j,False);original=copy.deepcopy(ep['arm']);a=ep['arm']
    a.update(L=0.,gap=a['U'],complete_seconds=None,complete_seconds_interval=proof['complete_seconds_interval'],
        complete_seconds_lower=proof['complete_seconds_interval'][0],complete_seconds_upper=proof['complete_seconds_interval'][1],
        formal_performance=True,original_whole_clock_unknown=True,supervisor_legacy_seconds=ep['completion']['fully_observed_end_to_end_seconds'],
        native_call_bounds_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source'],
        certificate_basis='own_nonnegative_original_full_domain_floor_open_after_explicit_native_bound_rejection',
        numerical_reader_recovery=SIDE.as_posix(),raw_native_lower_bound_rejected=original['L'],
        later_evidence_repair_engineering_in_original_window=False)
    a['relative_gap'],a['relative_gap_null_reason']=core.decision.relative(a);selected(a,original,proof)
    ep['rejected_raw_native_chronology']=copy.deepcopy(ep['chronological_cover']);ep['chronological_cover']=[]
    ep['analytical_floor_proof']=proof
    for b in j['bounds']+j['returned_native_proofs']:
        b.update(native_bound_mathematically_qualified=False,rejection_reason='known_call_native_lower_claim_contradicted_by_exact_original_cold_feasible_vector')
    for call in j['calls'].values():call['native_bounds_mathematically_qualified']=False
    j['trace']=copy.deepcopy(j['trace'])
    for z in j['trace']:
        z.update(raw_native_L_before_rejection=z['L'],L=0.,native_bound_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source'])
    return ep

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2])
    elif sys.argv[1]=='verify':print(verify(sys.argv[2])['complete_seconds_interval'])
    else:raise ValueError(sys.argv[1])
