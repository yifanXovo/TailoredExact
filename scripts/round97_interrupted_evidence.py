"""Analysis-only validation of the exact acknowledged development02 arm5.

Does not relax launch/audit rules, repair results or authorize other failures.
Call only from idle offline reporting; the original raw evidence is immutable.
"""
from pathlib import Path
from round97_campaign_v2 import ROOT, OUT, read, sha

ACK=OUT/'development02/hard_stop05_acknowledgement.json'


def validate_outcome(launch,audit,receipt):
    raw=Path(launch['destination']).resolve()
    assert audit['passed'] and receipt['within_cap']
    if receipt['stop_reason']=='normal_return':
        assert receipt['returncode']==0 and (raw/'result.json').exists()
        result=read(raw/'result.json')
        count=result['gurobi_optimize_count'] if launch['arm']=='P-GRB' else result['external_gini_tree_optimize_count']
        assert count==audit['native_calls_started']==audit['native_calls_returned']
        return result,[]
    expected=OUT/'development02/raw/05_D7_P-GRB'
    assert raw==expected.resolve() and (launch['number'],launch['id'],launch['arm'])==(5,'D7','P-GRB')
    acknowledgement=read(ACK)
    for path,expected_hash in acknowledgement['source_bindings'].items():
        assert sha(ROOT/path)==expected_hash,path
    assert receipt==acknowledgement['completion'] and audit['endpoint']==acknowledgement['endpoint']
    assert receipt['stop_reason']=='whole_run_hard_stop' and receipt['returncode']!=0
    assert audit['endpoint']['source']=='interrupted_committed_evidence'
    assert not audit['endpoint']['certificate'] and not (raw/'result.json').exists()
    assert audit['native_calls_started']==1 and audit['native_calls_returned']==0
    assert acknowledgement['verified_complete_optimize_count'] is None
    return None,[ACK]


def certificate_status(endpoint,result):
    if result is None:return 'unobserved_interrupted'
    return 'certified_at_normal_return' if endpoint['certificate'] else 'not_certified_at_normal_return'
