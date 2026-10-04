"""Idle-only immutable experiment/fee/default/protected-file reconciliation.

No native optimization. Complements mathematical and physical proof replays.
"""
import sys,json
import round101_campaign as campaign
import round101_recover_scope as recovery
from round101_common import *
from round100_idle import ensure_idle
from round101_budget import account

def main(label,names):
    ensure_idle();baseline=read(OUT/'baseline.json')
    assert all(sha(ROOT/p)==h for p,h in baseline['user_edit_sha256'].items())
    freeze=read(OUT/'candidate_freeze.json')
    assert freeze['source_hashes']==bindings() and sha(BUILD/'ExactEBRP.exe')==freeze['candidate_binary_sha256']
    admission=read(recovery.RECOVERY/'remaining_admission.json')
    assert admission['driver_sha256']==sha(ROOT/'scripts/round101_continue.py')
    assert admission['recovery_reader_sha256']==sha(recovery.__file__)
    assert admission['original_identity_sha256']==sha(recovery.CAMP/'identity.json')
    assert read(recovery.RECOVERY/'identity.json')['reader_sha256']==sha(recovery.__file__)
    assert sha(recovery.CAMP/'identity.json')==read(recovery.RECOVERY/'preserved_manifest.json')['original_identity_sha256']
    recovery.verify_preserved()
    assert read(recovery.RECOVERY/'remaining_completion.json')['passed']
    records=[]
    for name in names:
        camp=OUT/name;q=read(camp/'identity.json');done=recovery.records_view(camp)
        assert len(done)==len(q['launches']) and all(r['audit_passed'] for r in done)
        assert [r['number'] for r in done]==list(range(1,len(done)+1))
        assert q['helpers']==campaign.helpers() and q['runner_sha256']==sha(campaign.__file__)
        assert sha(q['input_manifest'])==q['prereg_sha256']
        assert q['dll_sha256']==sha('D:/gurobi1302/win64/bin/gurobi130.dll')
        if name in ['protection01','long01','confirmation01']:recovery.frozen(q)
        for r,launch in zip(done,q['launches']):
            d=Path(r['destination']);actual=read(d/'launch.json');c=read(d/'completion.json')
            assert all(actual[k]==v for k,v in launch.items()) and c==r['completion']
            assert c['within_cap'] and c['end_to_end_seconds']<=launch['cap_seconds']
            assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
            obs=read(d/'observations.json');assert c['committed_events']==len(obs)
            for row in obs:
                assert campaign.r90.evidence.receipt(d/'journal'/f'event_{row["sequence"]}.commit',
                    row['first_observed_seconds'],launch['cap_seconds'])==row
            audited=recovery.audit_view(d)
            scope=(audited['native_scope_adapter'] if r.get('original_audit_failed')
                else campaign.scope.scope_receipt(launch,obs))
            assert audited['native_scope_adapter']==scope and r['endpoint']==audited['endpoint']
            assert audited['committed_events']==len(obs)
            if c['stop_reason']!='normal_return':
                assert c['stop_reason']=='whole_run_hard_stop'
                assert not (d/'result.json').exists() and not r['endpoint']['certificate']
            else:
                result=read(d/'result.json')
                assert result['strict_certified_original_problem']==r['endpoint']['certificate']
            for p in (d/'external/native_logs').glob('*.round101.summary.json'):
                s=read(p);assert s['failure']=='' and s['api_ok']==s['submitted']
                if launch['arm']=='FLEET-ROOT':assert s['range']=='root' and s['tree_selected']==0
            if launch['arm']=='P-GRB':
                assert '--round101-fleet-cuts' not in launch['command']
                assert not list((d/'external/native_logs').glob('*.round101.summary.json'))
            records.append(dict(campaign=name,number=r['number'],id=r['id'],arm=r['arm'],
                committed_events=len(obs),native_calls=scope['native_calls'],
                stop_reason=c['stop_reason'],certificate=r['endpoint']['certificate'],
                recovered_original_audit=r.get('original_audit_failed',False)))
    fees=account();assert fees['within_limits'] and not fees['reserved'] and not fees['incomplete_receipt_batches']
    write(OUT/label/'summary.json',dict(passed=True,optimizer_calls=0,records=records,
        protected_user_files=baseline['user_edit_sha256'],frozen_production_binary_sha256=freeze['candidate_binary_sha256'],
        candidate_stays_default_off=True,script_sha256=sha(__file__),fee_account=fees,
        limitation='Identity, durable receipt, call scope, fees and explicit recovery audit; separate exact rank/physical witness replay and independent review required.'))
    print(json.dumps(dict(passed=True,runs=len(records),starts=fees['completed_charged_starts'],
        seconds=fees['completed_charged_seconds'],Optimize=0)))

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
