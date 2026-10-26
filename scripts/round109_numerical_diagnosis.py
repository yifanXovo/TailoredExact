"""Offline facts for the actual main05 stop; applies no recovery or solver change."""
from round109_common import ROOT, OUT, read, write, sha, budget
import round109_reader as reader
import round108_decisions as rule
from pathlib import Path
import sys

def diagnose(destination):
    ident=read(OUT/'campaign/identity.json'); endpoints={}; hashes={}; raw_bounds=[]
    for launch in ident['launches'][12:15]:
        d=reader.portable(ROOT,launch['destination']);obs=read(d/'observations.json')
        j=reader.evidence.journal(ROOT,launch['panel'],d)
        j['return_sequences']={v['payload']['call']:v['payload']['sequence'] for v in obs if v['payload']['kind']=='returned'}
        ep=reader.endpoint(ROOT,launch,ident,d,j,False)
        reader.check_native_parameters(launch,ep['result'],j)
        a=ep['arm'];a['complete_seconds']=read(d/'whole_arm_receipt.json')['complete_seconds'] if (d/'whole_arm_receipt.json').exists() else None
        endpoints[launch['arm']]=dict(arm=a,physical=reader.full_fleet(ROOT,launch['panel'],ep['result']))
        hashes[launch['arm']]={p.name:sha(p) for p in d.iterdir() if p.is_file() and p.name in ['launch.json','completion.json','result.json','audit.json','observations.json','whole_arm_receipt.json','compact.lp','native.log']}
        if launch['arm']=='P-GRB':raw_bounds=j['bounds']+j['returned_native_proofs']
    zero=endpoints['ENS-C']['physical'];assert zero['F']==zero['G']==zero['P']==0
    ownP=endpoints['P-GRB']['arm'];assert ownP['L']>rule.CLOSURE_TOL
    fee=read(OUT/'fees/main05/receipt.json')
    upper=fee['outer_seconds']-endpoints['M-B']['arm']['complete_seconds']-endpoints['ENS-C']['arm']['complete_seconds']
    d=reader.portable(ROOT,ident['launches'][14]['destination'])
    lower=read(d/'completion.json')['fully_observed_end_to_end_seconds']
    assert 0<lower<=upper<ident['launches'][14]['cap_seconds']
    p=ident['launches'][14]['panel'];q=reader.evidence.instance(ROOT,p)
    assert p['lambda']>=0 and all(w>=0 for w in q['w'][1:])
    floor=dict(ownP,L=0.,gap=ownP['U'],certificate=False)
    comparisons=[]
    for a,c in [('M-B','P-GRB'),('M-B','ENS-C'),('ENS-C','P-GRB')]:
        original=rule.pair(endpoints[a]['arm'],endpoints[c]['arm'])
        hypothetical=rule.pair(floor if a=='P-GRB' else endpoints[a]['arm'],floor if c=='P-GRB' else endpoints[c]['arm'])
        assert (original['classification'],original['severe_regression'])==(hypothetical['classification'],hypothetical['severe_regression'])
        comparisons.append(dict(candidate=a,control=c,original_raw_bound_arithmetic=original,hypothetical_separately_proven_nonnegative_floor=hypothetical,classification_unchanged=True))
    value=dict(diagnostic_only=True,resolution_applied=False,solver_calls=0,closure_tolerance_unchanged=rule.CLOSURE_TOL,
        raw_endpoints=endpoints,raw_file_hashes=hashes,P_raw_bounds=raw_bounds,
        numerical_contradiction=dict(raw_P_L=ownP['L'],independently_rebuilt_ENS_physical_F=zero['F'],beyond_frozen_tolerance=True),
        original_cold_matrix_vector_proof='pending independent reviewer; this diagnostic checks physical witness and own raw provenance only',
        P_whole_time=dict(exact_seconds=None,lower_seconds=lower,upper_seconds=upper,
            basis='closed outer wrapper minus two recorded whole-arm durations is an upper, not exact; omitted pre-arm wrapper overhead is nonnegative',
            fabricated_whole_arm_receipt=False),hypothetical_floor=dict(L=0.,source='F=nonnegative true G + nonnegative lambda times nonnegative weighted penalty; zero denominator retains G=0',native_bound_not_accepted=True),
        diagnostic_comparisons=comparisons,closed_budget=budget(),independent_contract_review_required_before_resumption=True)
    write(Path(destination)/'facts.json',value)
    print('Actual numerical contradiction independently visible in primary raw reconstruction; no resolution applied; zero solver calls.')

if __name__=='__main__':diagnose(sys.argv[1])
