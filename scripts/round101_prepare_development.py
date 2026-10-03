"""One uniform post-isolation candidate; original P/ENS on two fixed roles."""
import sys
from round101_common import *
if __name__=='__main__':
    fleet=sys.argv[1];assert fleet in ['FLEET-ROOT','FLEET-SUBMIT']
    isolation=[__import__('json').loads(x) for x in (OUT/'isolation01/summary.jsonl').read_text().splitlines()]
    assert len(isolation)==6 and all(r['audit_passed'] for r in isolation)
    roles=[]
    for p in read(OUT/'development_inputs.json')['roles']:
        if p['id'] not in ['R98-C2','R99-N2']:continue
        p=dict(p);p['cap_seconds']=1800
        p['method_order']=['P-GRB','ENS-C',fleet] if p['id']=='R98-C2' else ['ENS-C',fleet,'P-GRB']
        roles.append(p)
    assert len(roles)==2
    write(OUT/'development_protocol01.json',dict(roles=roles,phase='fleet development',
        reference_billing='one_finite_batch',maximum_optimize_calls_per_arm=2048,
        planning_call_envelope_not_production_gate=True,fleet_arm=fleet,
        selection_evidence_sha256=sha(OUT/'isolation01/summary.jsonl'),
        question='Uniform execution candidate on actual ENS-vs-P weakness and heterogeneous primal/proof tradeoff. No per-case best-arm dispatch or historical/cross-arm inputs.',
        maximum_formal_starts=6,maximum_formal_seconds=10800))
