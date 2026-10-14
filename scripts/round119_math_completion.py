"""Pure finite mathematics and read-only evidence review; no native subprocess."""
from round119_common import *
import math,itertools

def check():
    # Independently enumerate this original V2/Q1/B1 physical problem. With
    # empty departure, only pickup1 or pickup1->drop1 are legal nonempty fleets.
    fleets=[dict(route=[0,0],Y=[1,0],pickup=0,load_prefix=[0,0]),
            dict(route=[0,1,0],Y=[0,0],pickup=1,load_prefix=[0,1,1]),
            dict(route=[0,1,2,0],Y=[0,1],pickup=1,load_prefix=[0,1,0,0])]
    points=[(0,0),(1,1),(2,0)]
    for f in fleets:
        Y=f['Y'];den=2*len(Y)*sum(Y)
        f['G_true']=sum(abs(a-b) for a in Y for b in Y)/den if den else 0.0
        f['F']=f['G_true']+.15*sum(abs(y-1) for y in Y)
        f['full_seconds']=sum(math.dist(points[a],points[b]) for a,b in zip(f['route'],f['route'][1:]))+120*f['pickup']
        assert all(0<=x<=1 for x in f['load_prefix']) and f['full_seconds']<=1000
    assert [round(f['F'],12) for f in fleets]==[.65,.3,.65]
    # No claim that these deliberately false abstract bounds came from native.
    counterexample=fleets[1];claim=dict(scope=[0,.5],cutoff=.9,bound=.4)
    assert claim['scope'][0]<=counterexample['G_true']<=claim['scope'][1]
    assert counterexample['F']<=claim['cutoff'] and counterexample['F']+1e-7<claim['bound']
    # Integer Y and deterministic original F collapse repeated physical events.
    records=[];best=math.inf
    for f in [fleets[0],fleets[1],fleets[1],fleets[1]]:
        if f['F']<best-1e-9:best=f['F'];records.append((tuple(f['Y']),best))
    assert len(records)==2 and best==.3
    source=(ROOT/'src/Round119ProofContraction.cpp').read_text(encoding='utf-8')
    assert 'if(v.objective<best_upper_-1e-9)' in source
    assert source.index('for(const auto& p:proofs_)if(contradicts')<source.index('if(v.objective<best_upper_-1e-9)')
    assert 'same_scope_counterexample_all_dependencies_revoked' in source and 'if(failed())throw' in source
    assert 'if(failed())return {}' in source
    failure=(OUT/'fees/qual03/stdout.txt').read_text(encoding='utf-8').strip()
    assert failure=='physical empty witness'
    value=dict(passed=True,Optimize=0,native_processes=0,method='independent finite physical mathematics plus read-only production invariants',
        fleets=fleets,repeated_physical_events_deduplicated=True,same_scope_false_bound_counterexample=claim,
        own_U_retained_does_not_restore_rejected_proof=True,
        supplementary_native=dict(exit_code=1,state='PARTIAL_FINITE_ONLY',
            completed_before_failure=['two distinct actual scheduler atomic contractions','depth inheritance','same proof not reused','finite depth/width','complete existing cover no rebuild','both halves closure'],
            failure='test incorrectly expected empty fleet F=.3; actual empty F=.65 and pickup1 loaded return F=.3',
            corrected_source_rerun=False,later_native_physical_tests_not_claimed_passed=True),
        existing_successful_native=dict(physical_embeddings_SHA=sha(OUT/'qualification/native_contract/physical_embedding.json'),
            full_chain_admission_SHA=sha(OUT/'review/performance_admission.json')),
        limits='This is finite mathematics and source review, not a new native run or universal numerical proof.')
    write(OUT/'qualification/math_completion.json',value)
    gate=read(OUT/'review/performance_admission.json');gate['pure_math_completion_SHA']=sha(OUT/'qualification/math_completion.json')
    gate['paid_fee_labels'].append('qual03');gate['supplemental_native_failed_test_retained']=True
    gate['additional_native_qualification_closed']=True;write(OUT/'review/performance_admission.json',gate)
    print('finite mathematics and retained partial lifecycle evidence complete; no new native process')
if __name__=='__main__':check()
