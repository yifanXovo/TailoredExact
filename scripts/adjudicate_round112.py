"""Strict current-call Fraction proof verification; no automatic floor fallback."""
from fractions import Fraction
from pathlib import Path
import math
import round108_reader as core
from round109_numerical_recovery import floor

ROUND='results/unified_exact_round112'

def verify(root,launch,sidecar):
    root=Path(root).resolve();out=root/ROUND;sidecar=core.portable(root,sidecar)
    assert sidecar.resolve().is_relative_to(root)
    s=core.read(sidecar);i=core.read(out/'campaign/identity.json');p=launch['panel']
    assert s['schema']=='round112-current-call-numerical-rejection-v1'
    assert s['key']==[launch['number'],launch['id'],0,launch['arm']]
    assert s['candidate_identity_SHA']==core.sha(out/'candidate_identity.json') and s['campaign_identity_SHA']==core.sha(out/'campaign/identity.json')
    assert s['production_PE_SHA']==i['candidate_binary_sha256'] and s['DLL_SHA']==i['dll_sha256']
    assert s['command']==launch['command'] and s['input_SHA']==core.sha(root/p['input_path'])==p['input_sha256']
    assert s['policy_SHA']==core.sha(out/'numerical_policy.md')
    for name,h in s['raw_bindings'].items():
        path=core.portable(root,name);assert path.resolve().is_relative_to(root) and core.sha(path)==h
    d=core.portable(root,launch['destination']);obs=core.read(d/'observations.json')
    call_id=s['call'];calls=[v['payload'] for v in obs if v['payload']['kind']=='call' and v['payload']['call']==call_id]
    assert len(calls)==1;call=calls[0]
    model_path=core.portable(root,call['model_path']);assert core.sha(model_path)==call['model_sha256']==s['model_SHA']
    assert call['settings']==dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    c=core.read(d/'completion.json');assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert core.read(d/'launch.json')['command']==launch['command']
    required=[d/n for n in ['completion.json','launch.json','observations.json','result.json','audit.json','native_end_receipt.json']]
    required+=[model_path,root/p['input_path']]+list((d/'journal').glob('*'))
    assert all(path.relative_to(root).as_posix() in s['raw_bindings'] for path in required)
    vector_path=core.portable(root,s['exact_vector_path']);assert vector_path.resolve().is_relative_to(root)
    assert core.sha(vector_path)==s['exact_vector_SHA']
    raw=core.read(vector_path);values={n:Fraction(*q) for n,q in raw['complete_column_values'].items()}
    m=core.lp_model(model_path);assert set(values)==set(m['bounds'])
    # This entry handles actual MIP counterexamples. LP damage needs its own
    # independently bound actual relaxed-domain reconstruction before extension.
    assert call['native_preconditions'] is True or call['native_preconditions']==1
    for n,(lo,hi) in m['bounds'].items():
        assert (not math.isfinite(lo) or values[n]>=Fraction(lo)) and (not math.isfinite(hi) or values[n]<=Fraction(hi))
        assert m['types'][n]=='C' or values[n].denominator==1
    for terms,sense,rhs in m['rows']:
        lhs=sum((values[n]*Fraction(v) for n,v in terms),Fraction(0));right=Fraction(rhs)
        assert lhs==right if sense=='=' else lhs<=right if sense=='<=' else lhs>=right
    terms,constant=m['objective'];objective=Fraction(constant)+sum((values[n]*Fraction(v) for n,v in terms),Fraction(0))
    scope={k:call[k] for k in ['full_original','lower_g','upper_g','cutoff','gmax','model_scope']}
    assert s['actual_call_scope']==scope
    physical_input=core.evidence.instance(root,p)
    ratios=[values[f'Y_{n}']/physical_input['D'][n] for n in range(1,p['V']+1)]
    ratio_sum=sum(ratios,Fraction(0))
    true_G=sum((abs(x-y) for n,x in enumerate(ratios) for y in ratios[n+1:]),Fraction(0))/(p['V']*ratio_sum) if ratio_sum else Fraction(0)
    assert Fraction(call['lower_g'])<=true_G<=Fraction(call['upper_g'])
    if not call['full_original']:assert objective<=Fraction(call['cutoff'])
    claims=[v['payload']['native_bound'] for v in obs if v['payload']['kind']=='bound' and v['payload']['call']==call_id]
    if s.get('additional_final_native_lower_claims'):
        # Final attributes are evidence only for the linked single original call.
        r=core.read(d/'result.json')
        assert call['full_original'] and len([v for v in obs if v['payload']['kind']=='call'])==1
        assert r['native_mip_best_bound_available'] and r['gurobi_optimize_count']==1
        assert s['additional_final_native_lower_claims']==[r['native_mip_best_bound']]
        claims+=s['additional_final_native_lower_claims']
    assert claims and any(Fraction(v)>objective+Fraction(1,10**7) for v in claims)
    independent_path=core.portable(root,s['independent_audit_path']);assert independent_path.resolve().is_relative_to(root)
    audit=core.read(independent_path);assert core.sha(independent_path)==s['independent_audit_SHA']
    assert audit['decision']=='ACCEPT_CURRENT_CALL_REJECTION' and audit['current_key']==s['key']
    for key in ['candidate_identity_SHA','campaign_identity_SHA','production_PE_SHA','DLL_SHA','model_SHA','raw_bindings','exact_vector_path','exact_vector_SHA','policy_SHA','call','actual_call_scope']:
        assert audit[key]==s[key],key
    assert audit['complete_actual_true_G_cutoff_domain_checked']
    assert audit['Optimize']==0 and audit['native_environment']==0
    assert s['reject_all_call_native_lower_claims'] and s['withdraw_necessary_dependent_closures']
    if call['full_original']:
        a=core.evidence.instance(root,p);qualified_L=floor(p['lambda'],a['w'][1:],a['D'][1:],m['objective'],m['bounds'])
        assert s['qualified_L']==qualified_L==0 and s['qualified_L_source']=='own_original_full_domain_nonnegative_floor'
    else:
        cover_path=core.portable(root,s['independent_cover_reconstruction_path'])
        assert core.sha(cover_path)==s['independent_cover_reconstruction_SHA']
        cover=core.read(cover_path)
        assert cover['decision']=='ACCEPT_CURRENT_COMPLETE_COVER_AFTER_CALL_REJECTION'
        assert cover['affected_call']==call_id and cover['raw_bindings']==s['raw_bindings']
        assert cover['current_key']==s['key'] and cover['rejection_audit_SHA']==s['independent_audit_SHA']
        for key in ['candidate_identity_SHA','campaign_identity_SHA','production_PE_SHA','DLL_SHA','model_SHA','policy_SHA','call','actual_call_scope']:
            assert cover[key]==s[key],key
        assert cover['complete_actual_true_G_cutoff_domain_checked']
        assert cover['rejects_all_affected_call_claims_and_dependent_closures'] and cover['independent_LP_evidence_preserved']
        assert cover['Optimize']==0 and cover['native_environment']==0
        qualified_L=cover['qualified_L'];assert math.isfinite(qualified_L) and qualified_L>=0
    return dict(sidecar=s,qualified_L=qualified_L,exact_counterexample_objective=[objective.numerator,objective.denominator],verified_current_call=True)
