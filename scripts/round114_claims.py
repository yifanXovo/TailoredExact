"""Order-independent source attribution. No solver, clipping or raw mutation."""
import math

TOL=1e-7
FAILURES={'full_bound_witness_inconsistency','local_bound_witness_inconsistency'}

class ClaimRejection(Exception):
    def __init__(self,evidence):
        super().__init__('proven_same_domain_native_claim_rejection')
        self.evidence=evidence

def in_domain(call,w):
    if call['full_original']:return True
    return (call['lower_g']-TOL<=w['G']<=call['upper_g']+TOL and w['F']<=call['cutoff']+TOL)

def reconcile(claims,witnesses):
    rejected=[]
    claims=sorted(claims,key=lambda c:(c['arm'],c['call'],c['sequence'],c['source'],c['value']))
    witnesses=sorted(witnesses,key=lambda w:(w['F'],w['G'],w['arm'],w['source'],w['available']))
    for claim in claims:
        assert math.isfinite(claim['value']) and claim['model_SHA'] and claim['domain_verified']
        call=claim['scope']
        for witness in witnesses:
            assert witness['physical_verified'] and witness['input_SHA']==claim['input_SHA']
            if in_domain(call,witness) and claim['value']>witness['F']+TOL:
                rejected.append(dict(claim,reason='full_bound_witness_inconsistency' if call['full_original'] else 'local_bound_witness_inconsistency',
                    counterexample={k:witness[k] for k in ['arm','source','F','G','input_SHA','available','physical_verified']},
                    rejected_native_kinds=['bound','OPTIMAL','INFEASIBLE','pruning','dependent_positive_certificate','dependent_cover'],
                    call_rejected_as_a_whole=True))
                break
    rejected.sort(key=lambda q:(q['arm'],q['call'],q['sequence'],q['source']))
    damaged={(q['arm'],q['call']) for q in rejected}
    return dict(rejections=rejected,damaged_calls=[dict(arm=a,call=c) for a,c in sorted(damaged)],
        all_claims=[dict(c,native_proof_qualified=(c['arm'],c['call']) not in damaged) for c in claims],
        order_independent=True,tolerance=TOL)

def missing_return_gate(f):
    """General predicates only; old IDs are fixtures, never routing keys."""
    required=['prefix_continuous','failure_terminal','failure_reason','damaged_call','actual_call_ids','journal_returned_ids',
        'explicit_not_started_ids','terminal_MIP','all_actual_calls_bound','normal_return','API_or_ledger_return_verified',
        'logs_parameters_models_cleanup_verified','serialization_process_exit_verified','own_committed_exact_zero',
        'same_domain_counterexample_verified','independent_floor0','clock_valid']
    assert all(k in f for k in required),'missing narrow return field'
    assert f['prefix_continuous'] and f['failure_terminal'] and f['failure_reason'] in FAILURES
    ids=f['actual_call_ids'];returned=f['journal_returned_ids'];bad=f['damaged_call']
    assert ids==list(range(1,len(ids)+1)) and ids and bad==ids[-1]
    assert returned==ids[:-1] and not f['explicit_not_started_ids']
    assert f['terminal_MIP'] and f['all_actual_calls_bound']
    assert all(f[k] is True for k in required if k not in ['failure_reason','damaged_call','actual_call_ids','journal_returned_ids','explicit_not_started_ids'])
    return dict(declared=len(ids),actual_Optimize=len(ids),journal_returned=len(returned),
        independently_verified_returned=len(ids),explicit_not_started=0,missing_returned_preserved=[bad],
        branch='BOUND_WITNESS_LATCH_LAST_MIP_OWN_ZERO_NORMAL_RETURN')

def qualify_endpoint(evidence,damage,normal=None):
    """Formal eligibility uses evidence saved in the arm's original whole."""
    required=['identity_verified','input_verified','model_domain_verified','journal_verified','return_verified','files_verified',
        'own_physical_verified','independent_floor0','clock_valid','necessary_closeout_complete']
    missing=[k for k in required if evidence.get(k) is not True]
    if missing or not isinstance(evidence.get('own_U'),(float,int)) or not math.isfinite(evidence['own_U']):
        return dict(formal_protocol_qualified=False,certificate_qualified=False,numbers_qualified=False,
            U=None,L=None,gap=None,certificate=None,missing_reasons=missing+(['OWN_UB_MISSING'] if evidence.get('own_U') is None else []))
    if damage:
        U=evidence['own_U'];zero=evidence['own_exact_zero'] is True
        assert not zero or U==0.
        return dict(formal_protocol_qualified=True,certificate_qualified=True,numbers_qualified=True,U=U,L=0.,gap=U,
            certificate=zero,certificate_basis='OWN_ZERO_CERTIFICATE' if zero else 'SOURCE_REDUCED_OPEN',
            endpoint_source='OWN_ZERO_CERTIFICATE' if zero else 'SOURCE_REDUCED_OPEN',source_reduced=True,
            native_proof_qualified=False,bound_source='independent_objective_floor',rejected_calls=damage)
    assert normal is not None
    return dict(normal,formal_protocol_qualified=True,certificate_qualified=True,numbers_qualified=True,
        source_reduced=False,native_proof_qualified=True,bound_source=normal.get('bound_source','qualified_native_or_inherited_floor'),rejected_calls=[])
