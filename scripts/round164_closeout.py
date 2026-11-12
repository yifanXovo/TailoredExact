"""Close actual publication/recovery evidence; no optimizer or scientific replay."""
from round164_common import *
import csv,gzip,io

SCIENCE='a29a70d132ecc17e18bc48a660225a6380722f45'
NUMERIC='b93a8a01ff1b7f3cbee67807be3ac6591db4767f'

def run():
    b=budget();assert not b['unclosed'] and b['G1_seconds']<=TOTAL
    identity=read(OUT/'science_identity.json');assert identity['PASS'] and len(identity['all_24_positions'])==24
    assert identity['healthy_producers_repeated']==0 and identity['all_three_Seed_H_semantics_equal']
    assert not git('diff','--name-only',BASE,'--','src','include','config').decode().splitlines()
    assert read(OUT/'panel_complete.json')['arms']==24
    assert read(OUT/'reports/summary.json')['total_within_input_pairs']==18
    assert read(OUT/'Seed0_reuse_qualification.json')['PASS']
    reviews=read(OUT/'review/identities.json')
    assert reviews['all_three_final_reviews']=='PASS' and len(reviews['reviewers'])==3
    assert len({a['agent_id'] for a in reviews['reviewers']})==3
    for a in reviews['reviewers']:assert sha(OUT/a['report'])==a['SHA256']
    source=read(OUT/'table_source_binding.json')
    assert source['fixed_numeric_science_commit']==NUMERIC and sha(OUT/'reports/complete_arms.json')==source['numerical_report_SHA256']
    master=read(OUT/'main_table_update.json');assert master['PASS'] and master['added_pairs']==12
    assert master['source_rows']==91 and master['working_master_rows']==103 and not master['external_actual_writes']
    working=OUT/master['working_master_path'].split('results/unified_exact_round164/',1)[1]
    for t in read(OUT/'main_table_final_discovery.json')['tables']:
        original=Path(t['path']);assert sha(original)==t['SHA256']
        assert working.read_bytes().startswith(original.read_bytes())
    increment=list(csv.reader(io.StringIO((OUT/master['canonical_increment']).read_text(encoding='utf-8-sig'),newline='')))
    assert len(increment)==13 and all(len(r)==28 for r in increment)
    p=read(OUT/'publication.json');assert p['state']=='open' and p['draft'] and not p['merged']
    assert p['base']=='codex/round163-stage-confirmation' and p['science_carrier_commit']==SCIENCE
    recovery=read(OUT/'public_restore_receipt.json');assert recovery['PASS'] and recovery['science_commit']==SCIENCE
    carrier=read(OUT/'carrier_manifest.json');assert recovery['bytes']==carrier['bytes'] and recovery['members_checked']==carrier['members']
    assert recovery['old_raw_archives_downloaded']==0 and recovery['Optimize']==0 and recovery['compilation']==0
    assert recovery['excluded_old_reference_members_checked']==len(carrier['inherited_reference_duplicates_excluded'])==70
    assert git('show',SCIENCE+':results/unified_exact_round164/carrier_manifest.json')==(OUT/'carrier_manifest.json').read_bytes()
    clean=read(OUT/'cleanup_record.json');assert clean['PASS'] and clean['deleted_files']==clean['deleted_bytes']==0
    protected=check_protected();assert protected==clean['protected_workspace']
    assert sha(OUT/'goal.md')==sha(Path('C:/Users/Administrator/Downloads/TailoredExact_Round164_Complete_Goal.md'))
    publication=dict(p,recovery='PASS',cleanup='PASS',independent_final_reviews='PASS',
        numeric_science_commit=NUMERIC,science_carrier_commit=SCIENCE,
        delivery_identity_policy='normal commit containing this record; literal final head read back in the PR body and local post-push observation, avoiding a self-hash loop')
    write(OUT/'publication.json',publication)
    decision=read(OUT/'decision.json');decision.update(publication_status='Open Draft PR226; anonymous recovery PASS; zero-delete cleanup PASS',
        science_carrier_commit=SCIENCE,scientific_seconds=b['G1_seconds'],scientific_capacity_seconds=TOTAL,
        further_study_started=False,required_science_remaining=False)
    write(OUT/'decision.json',decision)
    report=OUT/'final_report.md';text=report.read_text(encoding='utf-8')
    text=text.replace('The remaining work is normal Draft\npublication, new-only carrier/member hashes, bounded anonymous public\nrecovery and zero-delete cleanup; those later states are not claimed yet.',
        'Actual publication, recovery and cleanup evidence is closed below.')
    marker='## Actual publication and delivery closeout'
    text=text.split(marker)[0].rstrip()+f'''\n\n{marker}

[English Open Draft PR226](https://github.com/yifanXovo/TailoredExact/pull/226)
is observed open/draft on base `codex/round163-stage-confirmation`, whose
head remains `{BASE}`. Main still lacks that dependency and predecessor
PR225 remains Open Draft/unmerged. The normal science/carrier push and
actual API readback observe head `{SCIENCE}`. Later normal delivery
commits record these receipts; no merge, force push or branch deletion occurs.

The [new-only carrier](carrier_manifest.json) has {carrier['bytes']} bytes and
{carrier['members']} members, SHA256 `{carrier['archives'][0]['SHA256']}`.
All 210 Git-tracked payload members match the science commit bytes; new raw
is held in the indexed archive. Seventy old reference duplicates are bound
by the fixed R163 commit/member/SHA, with the four new tiny-qualification
reference files retained as new. Packaging takes
{carrier['packaging_IO_seconds']} s of ordinary I/O, outside science.

[Anonymous public recovery](public_restore_receipt.json) is PASS against
immutable `{SCIENCE}`: all {recovery['bytes']} bytes and all
{recovery['members_checked']} members match; four bounded old public metadata
files, 102 historical access references and 70 excluded old reference bindings
are checked against the fixed public index. Recovery takes
{recovery['recovery_IO_seconds']} s of separate ordinary I/O. No old raw
archive, commercial runtime, compile or Optimize is downloaded/executed.
This is byte/member recovery, not a licensed semantic/performance rerun.
The initial MSYS Python TLS-chain failure is retained in
[recovery failures](recovery_failures.json), including 0 downloaded bytes and
0.9643931 s of ordinary failed transport. Existing Windows CPython succeeds
with normal certificate verification in a new explicit attempt directory;
global certificates, proxy, credentials and permissions are unchanged.

[Current-only cleanup](cleanup_record.json) deletes 0 files/0 bytes and
observes free bytes {clean['observed_free_bytes_before']} before/after,
delta 0. Protected checks pass for three trees and three originally dirty
tracked files. Unique science, failures, user files, active worktree,
runtime dependencies and recovery assets remain intact.

[Completion audit](completion_audit.json) maps every goal requirement to
actual evidence and hashes. Measured C++ `{MEASURED_CPP}`, preregistration
`bb69cb2f5e7d48ef71dd974edf32744728340c27`, numerical source `{NUMERIC}`,
science/carrier `{SCIENCE}`, and the normal later delivery head are distinct.
The final literal delivery HEAD is read back after its push and recorded in
the PR body and local post-push observation, avoiding commit self-reference.
The finite scientific study is closed with no additional Seed or mechanism.
'''
    report.write_text(text,encoding='utf-8',newline='\n')
    resume=f'''# Round164 delivery record

Status: SCIENCE_AND_PUBLISHED_DRAFT_CLOSEOUT_COMPLETE.

All 24 registered new B/P producers complete. Twelve new pairs plus six
historical Seed0 pairs describe six mathematical inputs. At each Seed B
certifies 3/6 and P 1/6; all n35 runs remain OPEN. B35/X35 have favorable B
U/L throughout; C35 primal signs are +/−/− and proof signs +/+/+.
The maintained R137 body/math/supplement and navigation contain the scoped
conclusions; historical §5.4 is unchanged and the old PDF is historical.

Three actual independent final agents PASS; see review/identities.json.
Science is {b['G1_seconds']}/57600 s, including both retained scientific
failures and one 365.3231065273285 s parallel review window. No healthy
producer or successful endpoint analysis is replayed. No spare-budget study.

The two real 91-row GB18030 user masters remain unchanged. Deliverables are
an exact 12-pair increment and 103-row working master with original 28 columns
and byte prefix. The three historical N/A-P records specified by the goal
remain pending union into the unavailable 94-row user version; no 106-row
file is falsely claimed updated. See main_table_reconciliation.md.

Open Draft PR226: https://github.com/yifanXovo/TailoredExact/pull/226
Base: codex/round163-stage-confirmation, predecessor225 Open Draft/unmerged.
Original C++: {MEASURED_CPP}; unchanged qualified PE/DLL and defaults.
Preproduction: bb69cb2f5e7d48ef71dd974edf32744728340c27.
Immutable new numerical source: {NUMERIC}.
Science/carrier: {SCIENCE}.
Worktree: E:/codes/ExactEBRP-work/worktrees/round164.
Branch: codex/round164-seed-confirmation.

Public anonymous recovery PASS: {carrier['bytes']} bytes /{carrier['members']}
members, four bounded old metadata files, 102 old access references and 70
old reference bindings; no old raw archive, runtime or Optimize. The initial
MSYS TLS failure is preserved and normal Windows CPython verification passes.
Cleanup PASS: 0 files/0 bytes deleted, free-space delta 0, three protected trees
and three dirty tracked-file hashes unchanged. Unique evidence and runtimes
remain. No merge, force push, branch deletion or global settings change.

This normal receipt commit is the later delivery identity. Its literal HEAD
is read back after push in the PR body and the local file
E:/codes/ExactEBRP-work/temp/round164/final_delivery_observation.json;
do not add a self-referential commit solely to write its own hash.
No further solve, source replay or historical restore is needed.
'''
    (OUT/'RESUME.md').write_text(resume,encoding='utf-8',newline='\n')
    requirements=[line.split('|')[1].strip() for line in (OUT/'completion_requirements.md').read_text(encoding='utf-8').splitlines()
        if line.startswith('| ') and not line.startswith('| Requirement')]
    catalog=[
        ['science_identity.json','cleanup_record.json','infra/protected_workspace_summary.json','publication_base_qualification.json'],
        ['historical_increment.md','historical_source_map.json','review/research_direction.md'],
        ['input_references.json','matrix_frozen.json','pre_panel_admission.json'],
        ['method_freeze.json','candidate_manifest.json','review/execution_data.md'],
        ['science_identity.json','matrix_frozen.json','qualification/result.json','review/execution_data.md'],
        ['qualification/result.json','qualification/native_tiny_panel.json','pre_panel_admission.json','science_identity.json'],
        ['panel_complete.json','matrix_frozen.json','science_identity.json','execution_dispositions.json'],
        ['protocol.json','cost_report.json','execution_dispositions.json','review/execution_data.md'],
        ['reports/three_seed_arms.json','science_identity.json','review/math_paper.md','review/execution_data.md'],
        ['reports/complete_arms.json','reports/comparisons.json','reports/summary.json'],
        ['reports/three_seed_comparisons.json','reports/seed_evidence.md','review/math_paper.md'],
        ['Seed0_reuse_qualification.json','historical_member_access.json','review/execution_data.md'],
        ['reports/within_configuration.json','reports/summary.json','review/research_direction.md'],
        ['primal_targets_frozen.json','target_clock_contract.json','reports/primal_target_arrival.json','review/math_paper.md'],
        ['structural_synthesis.json','structural_member_sources.json','review/math_paper.md'],
        ['results/unified_exact_round137/paper_body.md','results/unified_exact_round137/mathematical_analysis.md','results/unified_exact_round137/supplement.md','research_navigation.md','review/research_direction.md'],
        ['results/unified_exact_round137/paper_body.md','results/unified_exact_round137/supplement.md','review/math_paper.md'],
        ['results/unified_exact_round137/paper_body.md','results/unified_exact_round137/supplement.md','review/research_direction.md'],
        ['main_table_update.json','main_table_reconciliation.md','table_source_binding.json','reports/GI_TBC_vs_P_GRB_Round164_Increment.csv','reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv','review/execution_data.md'],
        ['review/identities.json','review/math_paper.md','review/execution_data.md','review/research_direction.md'],
        ['carrier_manifest.json','public_restore_receipt.json','recovery_failures.json','infra/publication_exclusion_scan.json'],
        ['publication.json','publication_base_qualification.json','public_restore_receipt.json'],
        ['final_report.md','decision.json','RESUME.md','cost_report.json','cleanup_record.json','public_restore_receipt.json'],
    ]
    assert len(requirements)==len(catalog)==23
    proofs=[]
    for requirement,names in zip(requirements,catalog):
        evidence=[]
        for name in names:
            path=ROOT/name if name.startswith('results/') else OUT/name
            assert path.is_file(),path
            evidence.append(dict(path=path.relative_to(ROOT).as_posix(),SHA256=sha(path),bytes=path.stat().st_size))
        proofs.append(dict(requirement=requirement,status='proved',evidence=evidence))
    write(OUT/'completion_audit.json',dict(UTC=utc(),all_goal_requirements_proved=True,requirement_count=23,
        incomplete_required_science=0,missing_formal_positions=0,conclusion_changing_findings=0,proofs=proofs,
        mathematical_inputs=6,new_formal_arms=24,new_pairs=12,total_within_input_pairs=18,
        scientific_seconds=b['G1_seconds'],scientific_capacity_seconds=TOTAL,unused_scientific_seconds=b['remaining_G1_seconds'],
        numeric_science_commit=NUMERIC,science_carrier_commit=SCIENCE,PR=226,state='open',draft=True,
        observed_published_science_head=SCIENCE,master_fallback='91 originals preserved; exact12 increment/103 working copy; three unavailable historical records pending union, as goal authorizes',
        protected_workspace=protected,final_delivery_identity='containing normal receipt commit, final post-push PR head recorded outside Git to avoid self-reference',
        goal_may_complete_only_after_final_normal_push_and_matching_PR_HEAD_readback=True,
        no_new_Optimize_or_licensed_performance_rerun=True))
    print(json.dumps(dict(PASS=True,proved_requirements=len(proofs),science_seconds=b['G1_seconds'],publication='Open Draft226',recovery=True,cleanup=True)))

if __name__=='__main__':run()
