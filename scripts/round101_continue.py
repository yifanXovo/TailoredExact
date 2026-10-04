"""Prospectively admit only original frozen, never-started arms 7--9.

The original failed row 6 remains untouched. A separately verified read-only
audit supplies its observational endpoint; this does not authorize any rerun.
"""
import json,time
import round101_campaign as campaign
import round101_recover_scope as recovery
from round101_common import *
from round100_idle import ensure_idle

def main():
    ensure_idle();q=read(recovery.CAMP/'identity.json');recovery.frozen(q);recovery.verify_preserved()
    records=recovery.records_view(recovery.CAMP)
    assert len(records)==6 and all(r['audit_passed'] for r in records)
    remaining=q['launches'][6:];assert [r['number'] for r in remaining]==[7,8,9]
    assert all(not Path(r['destination']).exists() for r in remaining)
    admission=recovery.RECOVERY/'remaining_admission.json'
    write(admission,dict(schema='round101-recovery06-never-started-admission-v1',
        original_identity_sha256=sha(recovery.CAMP/'identity.json'),
        recovery_identity_sha256=sha(recovery.RECOVERY/'identity.json'),
        recovery_audit_sha256=sha(recovery.RECOVERY/'audit.json'),
        driver_sha256=sha(__file__),recovery_reader_sha256=sha(recovery.__file__),
        remaining_original_numbers=[7,8,9],remaining_original_commands=[r['command'] for r in remaining],
        remaining_total_cap=5400,no_rerun=True,no_source_binary_parameter_input_change=True,
        registered_unix=time.time()))
    campaign.r90.CAMPAIGN=recovery.CAMP;campaign.r90.audit_launch=campaign.adapter
    for launch in remaining:
        ensure_idle();recovery.frozen(q);recovery.verify_preserved()
        assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
        record=campaign.r90.run_one(launch,q['prereg'],q);records.append(record)
        same=[r for r in records if r['id']==launch['id']]
        lowers=[r['endpoint']['L'] for r in same];uppers=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
        assert not uppers or max(lowers)<=min(uppers)+1e-7
        write(recovery.CAMP/f'cross_arm_{launch["id"]}_{len(same)}.json',dict(strongest_L=max(lowers),
            best_physical_U=min(uppers) if uppers else None,passed=True,scope='no combined certificate'))
    write(recovery.RECOVERY/'remaining_completion.json',dict(passed=True,completed=[7,8,9],
        original_failed_row_preserved=True,summary_sha256=sha(recovery.CAMP/'summary.jsonl')))

if __name__=='__main__':main()
