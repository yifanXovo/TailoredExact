"""Offline qualification of immutable v1 paid prefix with known label defect.

No reclassification as formal performance, no edits to old result/audit bytes.
The old R83 result label is admitted only with the actual explicit R98 feature,
the frozen v1 launch/model identity and successful independent actual Start audit.
"""
from round98_common import *
import round98_campaign as campaign
import round94_lpg_formal_recovery_v3 as scope

def run():
    old=OUT/'development01';q=read(old/'identity.json');records=[]
    for launch in q['launches'][:2]:
        d=Path(launch['destination']);r=read(d/'result.json');completion=read(d/'completion.json')
        observations=read(d/'observations.json');assert completion['stop_reason']=='normal_return'
        assert read(d/'launch.json')['command']==launch['command']
        assert r['algorithm_preset']=='research-round83-vds-equal-net-exchange'
        if launch['arm']=='R2':
            assert '--round98-state-service' in launch['command']
            assert 'round98_state_service_projected' in r['preset_experimental_features_enabled']
            assert read(OUT/'qualification/production_F2_R2_start.json')['passed']
        native_scope=scope.scope_receipt(launch,observations)
        assert native_scope['native_calls']==len(scope.ledger_rows(d)[1])
        a=campaign.r90.evidence.audit(ROOT,launch['panel'],observations,q['candidate_binary_sha256'])
        campaign.r90.evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],a,observations,r,'normal_return',{})
        a['parameter_readback']=scope.v2.parameter_readback(r,require_call=True,arm='ENS-C')
        folder=d/'hga.csv.exchange';initial=campaign.r90.normalize(read(folder/'initial.json'))
        a['neutral_exchange']=campaign.r90.replay_exchange(launch['panel'],folder,initial)
        assert not read(folder/'result.json')['verification_failed']
        a.update(passed=True,classification='paid production qualification only; excluded from final performance panel',
            known_label_defect=launch['arm']=='R2',original_audit_sha256=sha(d/'audit.json'),
            original_result_sha256=sha(d/'result.json'),native_scope_adapter=native_scope)
        records.append(dict(arm=launch['arm'],audit=a,optimizer_calls=native_scope['native_calls'],
            outer_seconds=completion['process_wall_seconds'],completion_sha256=sha(d/'completion.json')))
    write(OUT/'qualification/v1_paid_prefix_offline_audit.json',dict(passed=True,optimizer_calls=0,records=records,
        source_sha256=sha(__file__),scope='offline journal/physics/coverage and known identity-label diagnosis; no performance rerun'))
if __name__=='__main__':run()
