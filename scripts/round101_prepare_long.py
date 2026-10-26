"""Frozen candidate on the known F5 long tail, common7200 cap."""
from round101_common import *
if __name__=='__main__':
    freeze=read(OUT/'candidate_freeze.json');assert freeze['source_hashes']==bindings()
    p=dict(next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']=='F5'))
    p['cap_seconds']=7200;p['method_order']=['ENS-C',freeze['fleet_arm'],'P-GRB']
    write(OUT/'long_protocol01.json',dict(roles=[p],phase='fleet long',reference_billing='one_finite_batch',
        maximum_optimize_calls_per_arm=2048,planning_call_envelope_not_production_gate=True,
        candidate_freeze_sha256=sha(OUT/'candidate_freeze.json'),
        question='Known V50/M4 development long tail; full original P/ENS/frozen candidate comparison, no holdout claim',
        maximum_formal_starts=3,maximum_formal_seconds=21600))
