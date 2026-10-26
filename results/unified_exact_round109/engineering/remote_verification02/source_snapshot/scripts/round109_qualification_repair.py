"""Retain the failed no-child wrapper and refreeze only its path-variable repair."""
from round109_common import *
import round109_campaign as campaign
import shutil

def main():
    d=OUT/'engineering/qualification_wrapper_repair01';d.mkdir(parents=True,exist_ok=False)
    failure=read(OUT/'fees/qualification_cli01/receipt.json')
    assert failure['exit_code']==1 and failure['actual_native_children_with_launch']==0
    assert not (OUT/'qualification/cli01/summary.jsonl').exists()
    for name in ['campaign','qualification/cli01']:
        path=OUT/name/'identity.json';q=read(path)
        assert not any(Path(x['destination']).exists() for x in q['launches'])
        backup=d/(name.replace('/','_')+'_identity_before.json');shutil.copyfile(path,backup)
        q.update(runner_sha256=sha(ROOT/'scripts/round109_campaign.py'),helpers=campaign.helpers())
        path.unlink();write(path,q)
    path=OUT/'candidate_identity.json';candidate=read(path);shutil.copyfile(path,d/'candidate_identity_before.json')
    candidate.update(helpers=campaign.helpers(),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),planned_total_starts=71,
        starts_reserve=1,qualification_conservative_starts_with_failure=14,
        no_child_wrapper_failure_SHA=sha(OUT/'fees/qualification_cli01/receipt.json'),wrapper_compatibility_repair_only=True)
    path.unlink();write(path,candidate)
    write(d/'repair.json',dict(reason='helper snapshot loop reused name, overwriting campaign path before the first native child',
        correction='rename loop variable helper_name',old_source_SHA=sha(OUT/'fees/qualification_cli01/source_snapshot/scripts/round109_campaign.py'),
        new_source_SHA=sha(ROOT/'scripts/round109_campaign.py'),failure_receipt_SHA=sha(OUT/'fees/qualification_cli01/receipt.json'),
        algorithm_parameters_or_rules_changed=False,production_PE_unchanged=True,all_42_argv_unchanged=True,
        original_qualification_reserve=8,revised_qualification_conservative_starts=14,formal_starts=57,total_planned_starts=71,
        hard_limit=72,remaining_start_reserve=1,qualification_outer_seconds_cap_unchanged=1200,
        no_native_rerun=True,conservative_failure_child_declaration_not_refunded=True,budget_before_retry=budget()))
    print('retained no-child wrapper failure; pure variable-name repair; all42 argv unchanged; planned71/72 starts')

if __name__=='__main__':main()
