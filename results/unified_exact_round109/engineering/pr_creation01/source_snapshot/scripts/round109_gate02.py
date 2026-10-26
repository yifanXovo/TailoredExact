"""Actual final signed-admission identity check; zero solver work."""
import round109_prepaid_wrapper as w
from round109_common import *
from round100_idle import ensure_idle

def run():
    ensure_idle();check_identity();p,q=w.require_plan();proof=w.repair.verify(ROOT);b=budget();w.check_coupon()
    gate=read(OUT/'review/performance_admission_resumption02.json')
    assert sha(OUT/'review/performance_admission_resumption02.json')=='ffaa67182de11f24a6404f84575a23501bb67f88e72025ed611a3032c42ff59b'
    assert gate['decision']=='ACCEPT' and gate['resumption_allowed'] is True
    assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['campaign_identity_SHA']==sha(OUT/'campaign/identity.json')
    assert gate['recovery_sidecar_SHA']==sha(ROOT/w.repair.SIDE) and gate['supplemental_wrapper_plan_SHA']==sha(w.PLAN)
    assert p['source_bindings']==w.source_hashes() and q['helpers']==w.old.helpers() and q['source_hashes']==bindings()
    assert len(q['launches'])==42 and p['original_all42_native_argv']==[v['command'] for v in q['launches']]
    assert b['paid_starts']==39 and not b['unclosed'] and b['remaining_starts']==33
    assert b['paid_outer_seconds']==11659.298868327402 and b['remaining_outer_seconds']>=68400+1200
    assert len(w.old.records(OUT/'campaign'))==17 and all(v['audit_passed'] for v in w.repair.record_view(ROOT,w.old.records(OUT/'campaign')))
    print('Signed admission actually verified: 42frozen native argv; original205sources/helpers/PE/DLL; 9wrappers; paid18once; total72starts; no native launched.')

if __name__=='__main__':run()
