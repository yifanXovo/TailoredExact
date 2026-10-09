"""Post-pack document/closed-receipt review; no new raw or public execution."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import time

started = time.perf_counter()
root = Path('E:/codes/ExactEBRP-round109').resolve(strict=True)
evidence = root / 'results/unified_exact_round109'
destination = evidence / 'review/postpack_delivery_review01'
assert Path.cwd().resolve() == root
destination.mkdir(exist_ok=False)
reads = {}

def read(relative):
    path = (evidence / relative).resolve(strict=True)
    assert path.is_relative_to(root)
    content = path.read_bytes()
    reads[relative] = hashlib.sha256(content).hexdigest()
    return content

def obj(relative):
    return json.loads(read(relative).decode('utf-8-sig'))

def sha(relative):
    return hashlib.sha256(read(relative)).hexdigest()

names = ['final_report.md', 'README.md', 'delivery_checklist.md', 'RESUME.md', 'public_validation.md', 'PR_BODY.md']
documents = {name: read(name).decode('utf-8-sig').replace('\r\n', '\n') for name in names}
snapshots = destination / 'document_snapshot'
snapshots.mkdir()
for name in names:
    (snapshots / name).write_bytes(read(name))
resume_current = documents['RESUME.md'].split('## Historical chronological entries (superseded)', 1)[0]
assert '**BLOCKED**' in resume_current
assert 'No native resumption or new-PE panel is authorized.' in resume_current
assert '24 normal formal arms' in resume_current and 'arm25' in resume_current and '17 unstarted' in resume_current
assert 'original12 main roles/3 Seed groups' in resume_current
assert 'all6 formal Seed1 arms and V100' in resume_current
assert 'all CLOSED/ACCEPT' in resume_current
assert 'No final stage decision exists yet' not in resume_current
assert '<!-- BEGIN HISTORICAL LOG -->' in documents['RESUME.md'] and '<!-- END HISTORICAL LOG -->' in documents['RESUME.md']
assert 'They are not instructions to resume or relaunch old commands.' in documents['RESUME.md']
assert '- [ ] New English stacked OPEN draft PR' in documents['delivery_checklist.md']
assert 'post-push verification' in documents['public_validation.md']
for name in names:
    assert 'BLOCKED' in documents[name]
    assert 'Seed1' in documents[name]
    assert '18618.079987913487' in documents[name]
assert '**Stage: BLOCKED.**' in documents['final_report.md']
assert '7WIN/1TIE/0LOSS' in documents['final_report.md']
assert '3WIN/3TIE/2LOSS, one severe' in documents['final_report.md']
assert '**G50-C1 M-B versus ENS**' in documents['final_report.md']
assert 'micro-positive objective1.000173407530002e-12' in documents['final_report.md']
assert 'all three report JSON files' in documents['README.md']
assert 'all6 formal Seed1 arms remain unmeasured' in documents['delivery_checklist.md']
assert 'All six formal Seed1 arms are unmeasured.' in documents['PR_BODY.md']
assert 'Formal V100 and Seed1 performance remain unresolved.' in documents['PR_BODY.md']
assert 'ENS-C remains the default' in documents['README.md'] and 'ENS-C remains the default' in documents['PR_BODY.md']
assert '3,742,772' in documents['final_report.md'] and '3,742,772' in documents['public_validation.md']
assert all(name in documents['public_validation.md'] for name in ['inherited_raw_summary.json', 'selection_decision.json', 'summary.json'])

pack = obj('public_pack_receipt.json')
export = obj('public_export_receipt.json')
restore = obj('public_restore_receipt.json')
archive_SHA = '7b0f694bb39fe8cca87b86f169c02dcac0af78fce383e79df4e08243b6c937a0'
manifest_SHA = 'ac8222330273107e834d31e769591df97ba52e251dbfaf3366ddf54686b017c1'
for receipt in (pack, restore):
    assert receipt['exit_code'] == 0
    assert receipt['archive_SHA'] == archive_SHA and receipt['manifest_SHA'] == manifest_SHA
    assert receipt['files'] == 155250 and receipt['archive_bytes'] == 185942661 and receipt['exact_part_count'] == 2
assert export['exit_code'] == 0
assert restore['public_files_only'] and not restore['original_workspace_reads']
assert Path(restore['restored_root']).name == 'ExactEBRP-round109-restored01'
assert Path(restore['public_root']).name == 'ExactEBRP-round109-public01'
for name in ['final_report.md', 'README.md', 'public_validation.md']:
    assert archive_SHA in documents[name] and manifest_SHA in documents[name]
engineering_seconds = {}
for run in ['public_pack03', 'public_export01', 'public_restore01', 'public_rebuild01']:
    prefix = 'engineering/' + run + '/'
    receipt = obj(prefix + 'receipt.json')
    assert receipt['exit_code'] == 0 and receipt['engineering'] is True and receipt['conservative_solver_starts'] == 0
    assert receipt['stdout_SHA'] == sha(prefix + 'stdout.log')
    assert receipt['stderr_SHA'] == sha(prefix + 'stderr.log') and not read(prefix + 'stderr.log')
    obj(prefix + 'launch.json')
    if 'source_SHA' in receipt:
        assert receipt['source_SHA'] == sha(prefix + 'execution_source.py')
    engineering_seconds[run] = receipt['seconds']
assert engineering_seconds['public_rebuild01'] == 642.1021036000457
rebuild_launch = obj('engineering/public_rebuild01/launch.json')
assert Path(rebuild_launch['cwd']).name == Path(rebuild_launch['source_root']).name == 'ExactEBRP-round109-restored01'
assert rebuild_launch['original_worktree_data_reads'] is False
assert rebuild_launch['Optimize'] == rebuild_launch['conservative_solver_starts'] == 0
assert '--compare' in rebuild_launch['command'] and '--root' in rebuild_launch['command']
rebuild_lines = read('engineering/public_rebuild01/stdout.log').decode('utf-8-sig').splitlines()
comparison = json.loads(rebuild_lines[-1])
assert comparison == dict(passed=True, exact_csv_fields_compared=3742772, exact_JSON_files_compared=['inherited_raw_summary.json', 'selection_decision.json', 'summary.json'])
summary = json.loads(rebuild_lines[-2])
assert summary['stage'] == 'BLOCKED' and summary['formal_arms'] == 24 and summary['failed_formal_arms'] == 1
assert summary['formal_seed1_arms_completed'] == 0 and summary['frozen_main_denominator'] == 12 and summary['frozen_seed_groups'] == 3
assert summary['conservative_starts'] == 51 and summary['outer_solver_fee_seconds'] == 18618.079987913487

public = obj('review/public_access_closure01/audit.json')
assert sha('review/public_access_closure01/audit.json') == 'cd4ac4110bd602a62241d7d7650cf7267d9f1de3a39cdb5a46843407aa2f7eb9'
assert public['decision'] == 'ACCEPT_FRESH_ROOT_INDEPENDENT_BLOCKED_PUBLICATION' and public['stage'] == 'BLOCKED' and public['resumption_allowed'] is False
assert public['all_guarded_evidence_read_bindings_below_fresh_restored_root'] and public['no_original_root_fallback'] and not public['original_workspace_reads']
assert public['raw_guarded_read_bindings'] == 152529 and public['comparison_guarded_read_bindings'] == 40
assert public['formal_Seed1_arms_unmeasured'] == 6 and public['V100_performance_unassessed']
assert public['valid_formal_arms'] == 24 and public['certified_formal_arms'] == 14 and public['open_formal_arms'] == 10
assert public['failed_formal_numbers'] == [25] and public['unstarted_formal_numbers'] == list(range(26, 43))
assert public['all42_argv_and_12_reference_bindings_retained']
assert public['archive_SHA'] == archive_SHA and public['manifest_SHA'] == manifest_SHA
expected_pairs = {
    'M-B/P-GRB': dict(WIN=7, TIE=1, severe_regressions=0),
    'M-B/ENS-C': dict(WIN=3, TIE=3, LOSS=2, severe_regressions=1),
    'ENS-C/P-GRB': dict(WIN=7, TIE=1, severe_regressions=0),
}
assert public['own_pair_counts'] == expected_pairs
for run in ['public_blocked_raw01', 'public_blocked_compare01', 'public_access_closure01']:
    prefix = 'review/' + run + '_execution/'
    receipt = obj(prefix + 'receipt.json')
    assert receipt['exit_code'] == 0 and receipt['Optimize'] == receipt['native_environments'] == 0
    assert receipt['public_mode'] and not receipt['original_workspace_reads']
    assert Path(receipt['cwd']).name == Path(receipt['explicit_read_root']).name == 'ExactEBRP-round109-restored01'
    assert receipt['stdout_SHA'] == sha(prefix + 'stdout.txt')
    assert receipt['stderr_SHA'] == sha(prefix + 'stderr.txt') and not read(prefix + 'stderr.txt')
    assert receipt['audit_SHA'] == sha('review/' + run + '/audit.json')
    assert receipt['launch_SHA'] == sha(prefix + 'launch.json')
    source_name = 'check.py' if run == 'public_access_closure01' else 'source_snapshot.py'
    assert receipt['source_SHA'] == sha(prefix + source_name)
    assert receipt['execution_source_SHA'] == sha(prefix + 'run.ps1')
    engineering_seconds[run] = receipt['elapsed_seconds']
selection = obj('selection_decision.json')
assert selection['stage'] == 'BLOCKED' and selection['completed_formal_seed1_arms'] == 0 and selection['formal_seed_sensitivity_assessed'] is False
assert sha('selection_decision.json') == sha('reports_final/selection_decision.json')
source_path = Path(__file__).resolve(strict=True)
assert source_path.is_relative_to(root)
source_bytes = source_path.read_bytes()
source_SHA = hashlib.sha256(source_bytes).hexdigest()
value = dict(
    decision='ACCEPT_POSTPACK_DELIVERY_NARRATIVE', stage='BLOCKED', resumption_allowed=False,
    actual_utc=datetime.now(timezone.utc).isoformat(), cwd=str(Path.cwd()), explicit_read_root=str(root),
    phase='Lightweight post-pack authoring-document and copied closed-receipt review; earlier isolated public reconstruction provenance remains unchanged.',
    corrected_RESUME_current_entry_and_preserved_history=True,
    valid_formal_arms=24, failed_formal_numbers=[25], unstarted_formal_numbers=list(range(26,43)),
    frozen_main_denominator=12, frozen_seed_groups=3, formal_Seed1_unmeasured=6, V100_performance_unassessed=True,
    partial_pair_counts=expected_pairs, worst_loss='G50-C1 M-B/ENS-C severe',
    exact_csv_fields_prior_public_comparison=3742772,
    exact_report_JSON_files_prior_public_comparison=comparison['exact_JSON_files_compared'],
    prior_public_all_guarded_evidence_reads_only_fresh_root=True,
    archive_SHA=archive_SHA, manifest_SHA=manifest_SHA, carrier_files=155250, exact_parts=2,
    paid_starts=51, paid_outer_seconds=18618.079987913487, default_ENS_changed=False,
    production_or_scientific_sources_edited=False, carrier_edited=False, new_raw_rebuilds=0,
    Optimize=0, native_environment=0, remote_PR_creation_and_pinned_verification_not_yet_claimed=True,
    no_circular_post_push_verification_claim=True, engineering_seconds_bound=engineering_seconds,
    read_bindings=reads, source_SHA=source_SHA,
    engineering_elapsed_seconds=time.perf_counter()-started,
)
(destination / 'audit.json').write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
(destination / 'source_at_execution.py').write_bytes(source_bytes)
(destination / 'launch.json').write_text(json.dumps(dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=source_SHA),indent=2)+'\n',encoding='utf-8')
(destination / 'receipt.json').write_text(json.dumps(dict(exit_code=0,audit_SHA=hashlib.sha256((destination/'audit.json').read_bytes()).hexdigest(),source_SHA=source_SHA,engineering_elapsed_seconds=time.perf_counter()-started,Optimize=0,native_environment=0,cwd=str(Path.cwd()),explicit_read_root=str(root)),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(decision=value['decision'], stage=value['stage'], exact_csv_fields=3742772, new_raw_rebuilds=0, Optimize=0)))
