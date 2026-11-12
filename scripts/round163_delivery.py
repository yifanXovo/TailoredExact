"""Close actual publication/recovery metadata; no scientific producer or replay."""
from round163_common import *
import round163_report

def run():
    pub=read(OUT/'publication.json')
    recovery=read(OUT/'public_restore_receipt.json')
    cleanup=read(OUT/'cleanup_record.json')
    reviews=read(OUT/'review/identities.json')
    tables=read(OUT/'main_table_update.json')
    assert pub['state']=='open' and pub['draft'] and not pub['merged']
    assert recovery['PASS'] and recovery['members_checked']==50601 and recovery['bytes']==39888556
    assert recovery['science_commit']==pub['science_commit'] and not recovery['independent_semantic_or_performance_rerun']
    assert cleanup['PASS'] and cleanup['deleted_files']==0 and cleanup['protected_workspace']['PASS']
    assert reviews['all_three_final_reviews']=='PASS' and tables['PASS']
    assert all(t['before_rows']==85 and t['after_rows']==91 and t['added_rows']==6 and t['original_prefix_bytes_identical'] for t in tables['tables'])
    b=budget();assert not b['unclosed'] and b['G1_seconds']<72000
    assert abs(b['G1_seconds']-24697.709828344174)<1e-8
    pub.update(delivery_receipts_UTC=utc(),scientific_seconds=b['G1_seconds'],
        independent_reviews='three fresh agents: PASS; not human peer review',
        main_CSV_files_updated=2,new_B_P_pairs=6,master_rows_before=85,master_rows_after=91,
        public_recovery_PASS=True,public_new_bytes=recovery['bytes'],public_new_members=recovery['members_checked'],
        public_recovery_IO_seconds=recovery['recovery_IO_seconds'],
        public_recovery_semantic_or_performance_rerun=False,
        cleanup_PASS=True,deleted_files=cleanup['deleted_files'],deleted_bytes=cleanup['deleted_bytes'],
        observed_free_space_delta=cleanup['observed_free_space_delta'],protected_workspace=cleanup['protected_workspace'],
        receipt_SHA256={name:sha(OUT/name) for name in ['public_restore_receipt.json','cleanup_record.json','main_table_update.json','review/identities.json']})
    write(OUT/'publication.json',pub)
    state=read(OUT/'execution_state.json')
    state.update(UTC=utc(),status='SCIENCE_DELIVERED_OPEN_DRAFT_WITH_RECOVERY_AND_CLEANUP',
        primary_science_followup='Complete. No next-stage solve or new scientific run is requested.',
        final_decision_not_yet_made=False,decision_pending=False,active_position=None,
        independent_reviews_complete=True,all_fees_closed=True,formal_arms=18,
        science_commit=pub['science_commit'],PR=pub['PR'],pr_number=pub['pr_number'],
        PR_state='open',PR_draft=True,public_recovery_PASS=True,current_only_cleanup_PASS=True,
        cleanup_deleted_files=0,final_delivery_head_readback=pub['final_delivery_readback_local'])
    write(OUT/'execution_state.json',state)
    round163_report.run()
    cost=read(OUT/'cost_report.json')
    write(OUT/'publication_costs.json',dict(UTC=utc(),scientific_seconds=cost['scientific_seconds'],
        ordinary_engineering_IO_seconds=cost['separate_engineering_or_IO_seconds'],
        records=cost['separately_observed_engineering_IO'],
        metadata_screening_tool_outer_seconds=2.4309443,
        metadata_screening_outer_is_separate_from_science=True,
        nested_Runtime_Work_H_helper_not_added_twice=True))
    resume=f'''# Round163 delivered: science complete, Open Draft PR

All **18/18** formal arms and required readbacks pass. All scientific fees close at
**{cost['scientific_seconds']} / 72000s** ({cost['scientific_hours']:.6f}h).
No producer is active and no healthy producer should be rerun. Three fresh
independent agents close math/method, execution/data+CSV and stage direction
PASS; these are agent reviews, not human peer review.

Paper choice: **B remains main; E+ is a limited, uniformly defined proof
supplement**. E+ gives the real X35 final-L gain, with no extra certificate or
physical-U improvement. The finite costs, opposing C35 primal witness and
reasonable uniform-E+ alternative remain explicit. Only one next question is
identified, with R96 prior art/reuse and certification prerequisites; it has
not been executed. Released main defaults remain unchanged.

## Actual delivery and recovery

- English [Open Draft PR #{pub['pr_number']}]({pub['PR']}), base
  `{pub['base']}` at `{pub['base_sha']}`.
- Fixed science/carrier: `{pub['science_commit']}`.
- Immutable numeric CSV source: `{pub['immutable_numeric_source_commit']}`.
- Measured C++: `{pub['measured_CPP_commit']}`; PE/DLL identities are in
  [science identity](science_identity.json). No production rebuild occurred.
- Two actual GB18030 master CSVs each advance **85 to 91 rows**, with exactly
  six qualified B/P additions and the original byte prefix/header preserved.
  E+ is not substituted for B. [Actual writes](main_table_update.json),
  [full copied master](reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv),
  [named 28-column increment](reports/GI_TBC_vs_P_GRB_Round163_Increment.csv).
- [Anonymous public recovery](public_restore_receipt.json): PASS,
  {recovery['bytes']} bytes / all {recovery['members_checked']} indexed new members.
  It checks byte/member integrity without old archive, licensed runtime,
  compilation or Optimize; it is not a semantic/performance rerun.
- [Current-only metadata screening](cleanup_record.json): PASS, zero deletion,
  actual free-space delta {cleanup['observed_free_space_delta']} bytes. Both protected
  trees and their three actual initially dirty tracked files pass hash checks.
  Active worktree, unique science/failures, actual runtime dependencies and
  public recovery assets are retained. No old round or global setting is changed.

Later normal commits contain delivery receipts. The actual final local HEAD,
remote head and PR state/base/head readback is kept at
`{pub['final_delivery_readback_local']}` to avoid making a commit contain its own
hash. The indexed carrier retains its fixed packaged bytes; Git delivery
metadata can advance without repackaging or rerunning science.

## Freeze and disclosed chronology

Active worktree: `E:/codes/ExactEBRP-work/worktrees/round163`; branch
`{pub['head']}`. Main remains `{pub['main_observed_unchanged']}`;
R162 #224 remains Open Draft/unmerged at `{pub['base_sha']}`.
Recipe/method `9d8836101`, six-input seal `5d1e10f1a` and matrix/admission
`830e92cc9` precede their dependent generation/qualification/formal work.
All six first valid draws are retained; no historical mathematical-key collision
or within-source overlap between the two new selections is found.

The actual primary master was located and new IDs checked before the panel.
Its additional detailed row-to-input crosswalk was inspected after the first
arm started and completed in the final static readback. Effective legacy-weight
normalization and R57 ephemeral-pilot audit also strengthen the post-panel
history check. This ordering departure is disclosed, with no redraw or method
change; those supplementary checks are not called preregistered.

The sole tiny E+ producer was not rerun. Its unchanged helper legally falls
back when a redundant zero-total lower row is omitted; a pure scope reader
repair recognizes the implication from nonnegative Y bounds. Qualification
and independent-reader failed attempts/costs are preserved. All actual routes,
own-H/helper evidence, proof ledgers, launch/OS/fee receipts and failures are
indexed in the new-only carrier.

[Final report](final_report.md), [decision](decision.json),
[three independent reviews](review/identities.json), [publication](publication.json),
[scientific and ordinary I/O costs](cost_report.json),
[recovery scope](reproducibility.md). No further scientific work is pending.
'''
    (OUT/'RESUME.md').write_text(resume,encoding='utf-8',newline='\n')
    p=OUT/'reproducibility.md'
    old=p.read_text(encoding='utf-8')
    marker='\n## Actual delivery closeout\n'
    if marker in old:old=old.split(marker)[0]
    old+=marker+f'''
English [Open Draft PR #{pub['pr_number']}]({pub['PR']}) is open on the verified
R162 dependency branch. The fixed science/carrier snapshot is
`{pub['science_commit']}`; the immutable numeric CSV source is
`{pub['immutable_numeric_source_commit']}`. The public receipt reports PASS for
{recovery['bytes']} bytes and all {recovery['members_checked']} indexed members.
This is anonymous transport/integrity I/O only, not licensed solver execution.
Current-only screening deletes zero files/bytes and observes a free-space delta
of {cleanup['observed_free_space_delta']} bytes. Protected workspace hashes pass.
The packaged index binds its exact historical bytes; final delivery receipts
and their presentation may advance in normal Git commits without changing the
carrier or scientific endpoints. Final pushed HEAD/PR readback stays local at
`{pub['final_delivery_readback_local']}` to avoid commit self-reference.
'''
    p.write_text(old,encoding='utf-8',newline='\n')
    print(json.dumps(dict(PASS=True,PR=pub['PR'],scientific_seconds=cost['scientific_seconds'],
        separate_engineering_IO_seconds=cost['separate_engineering_or_IO_seconds'],
        public_members=recovery['members_checked'],deleted_files=cleanup['deleted_files'])))

if __name__=='__main__':run()
