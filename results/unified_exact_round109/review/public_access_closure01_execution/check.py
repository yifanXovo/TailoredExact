"""Bind the actual fresh-root independent raw and subsequent comparison runs."""
import hashlib
import json
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

started = time.perf_counter()
root = Path('E:/codes/ExactEBRP-round109-restored01').resolve(strict=True)
review = root / 'results/unified_exact_round109/review'
out = review / 'public_access_closure01'
assert Path.cwd().resolve() == root
out.mkdir(exist_ok=False)
reads = {}

def read(p):
    p = Path(p).resolve(strict=True)
    assert p.is_relative_to(root)
    raw = p.read_bytes()
    reads[str(p)] = hashlib.sha256(raw).hexdigest()
    return raw

def obj(p):
    return json.loads(read(p).decode('utf-8-sig'))

def sha(p):
    return hashlib.sha256(read(p)).hexdigest()

raw_path = review / 'public_blocked_raw01/audit.json'
comparison_path = review / 'public_blocked_compare01/audit.json'
raw = obj(raw_path)
comparison = obj(comparison_path)
raw_receipt = obj(raw_path.parent / 'receipt.json')
compare_receipt = obj(comparison_path.parent / 'receipt.json')
raw_outer = obj(review / 'public_blocked_raw01_execution/receipt.json')
compare_outer = obj(review / 'public_blocked_compare01_execution/receipt.json')
raw_launch = obj(review / 'public_blocked_raw01_execution/launch.json')
compare_launch = obj(review / 'public_blocked_compare01_execution/launch.json')
restore = obj(root / 'restore_receipt.json')
assert raw['decision'] == 'ACCEPT_INDEPENDENT_BLOCKED'
assert comparison['decision'] == 'ACCEPT_INDEPENDENT_BLOCKED_PUBLICATION'
assert raw['stage'] == comparison['stage'] == 'BLOCKED'
assert raw['resumption_allowed'] is comparison['resumption_allowed'] is False
assert raw['public_mode'] and raw['no_original_root_fallback']
assert not raw['actual_PE_DLL_rehash']
assert raw['candidate_identity_SHA'] == '65717d291ff19b05216d9c051c5493729ff6ee464afe7eb9dd707d7c94a10730'
assert raw['campaign_identity_SHA'] == '73c3743eeff67d43f84df506b5a7f19820e8691068a7e7e9fbdb762bac1bbe5a'
assert len(raw['all42_native_argv']) == 42
assert len(raw['own_actual_arms']) == 24
assert len(raw['own_qualification']) == 5
assert len(raw['own_references']) == 12
assert [a['number'] for a in raw['unstarted17']] == list(range(26, 43))
assert raw['failed25']['scientific_endpoint'] is None
assert raw['failed25']['completion']['returncode'] == 0xC00000FD
assert sum(a['certificate'] is True for a in raw['own_actual_arms']) == 14
assert raw['science']['formal_seed1_arms_completed'] == 0
assert raw['science']['no_V100_valid_solve_endpoint']
assert raw['fees']['paid_starts'] == 51
assert raw['fees']['paid_outer_seconds'] == 18618.079987913487
assert raw['selection']['formal_seed_sensitivity_assessed'] is False
assert comparison['actual_Optimize'] == 99
assert comparison['journal_returned'] == 98
assert comparison['independently_proved_rc0_without_returned'] == 1
assert comparison['all24_endpoints_and_24pairs_agree']
assert comparison['all_models_native_calls_AM_and_physical_final_fleets_agree']
assert comparison['own_raw_audit_SHA'] == sha(raw_path)
assert not (root / 'build/research/round109-inherited-mb-v1/ExactEBRP.exe').exists()
for receipt, path, outer, launch, execution_name in (
    (raw_receipt, raw_path, raw_outer, raw_launch, 'public_blocked_raw01_execution'),
    (compare_receipt, comparison_path, compare_outer, compare_launch, 'public_blocked_compare01_execution'),
):
    assert receipt['exit_code'] == outer['exit_code'] == 0
    assert receipt['audit_SHA'] == outer['audit_SHA'] == sha(path)
    assert Path(receipt['cwd']).resolve() == Path(outer['cwd']).resolve() == root
    assert Path(receipt['explicit_read_root']).resolve() == Path(outer['explicit_read_root']).resolve() == root
    assert outer['public_mode'] and not outer['original_workspace_reads']
    assert launch['public_mode'] and not launch['original_workspace_reads']
    assert launch['argv'][0] == '-I'
    assert '--dll' not in launch['argv']
    assert receipt['Optimize'] == outer['Optimize'] == 0
    assert receipt['native_environment'] == outer['native_environments'] == 0
    assert not read(review / execution_name / 'stderr.txt')
    assert outer['stdout_SHA'] == sha(review / execution_name / 'stdout.txt')
    assert outer['stderr_SHA'] == sha(review / execution_name / 'stderr.txt')
    assert receipt['source_SHA'] == outer['source_SHA'] == sha(review / execution_name / 'source_snapshot.py')
    assert outer['launch_SHA'] == sha(review / execution_name / 'launch.json')
    assert outer['execution_source_SHA'] == sha(review / execution_name / 'run.ps1')
for audit in (raw, comparison):
    assert all(Path(p).resolve().is_relative_to(root) for p in audit['read_bindings'])
assert str(root / 'restore_receipt.json') in raw['read_bindings']
assert raw['read_bindings'][str(root / 'restore_receipt.json')] == sha(root / 'restore_receipt.json')
assert restore['exit_code'] == 0 and restore['public_files_only'] and not restore['original_workspace_reads']
assert Path(restore['restored_root']).resolve() == root
assert restore['archive_SHA'] == '7b0f694bb39fe8cca87b86f169c02dcac0af78fce383e79df4e08243b6c937a0'
assert restore['manifest_SHA'] == 'ac8222330273107e834d31e769591df97ba52e251dbfaf3366ddf54686b017c1'
assert restore['files'] == 155250 and restore['exact_part_count'] == 2
assert sha(root / 'results/unified_exact_round109/reproduce.md') == '72288803dc595e34f607e3f4b1750a090668d7de2c525a1a733662871c57eda2'
assert sha(review / 'narrative_review01/audit.json') == '7863adfcb61e32db47736f1ffc91675529ec524e75fbe3a0912c620f915fda71'
value = dict(
    decision='ACCEPT_FRESH_ROOT_INDEPENDENT_BLOCKED_PUBLICATION',
    stage='BLOCKED', resumption_allowed=False,
    actual_utc=datetime.now(timezone.utc).isoformat(), cwd=str(Path.cwd()),
    explicit_read_root=str(root), restore_receipt_SHA=sha(root / 'restore_receipt.json'),
    archive_SHA=restore['archive_SHA'], manifest_SHA=restore['manifest_SHA'],
    actual_restored_files=restore['files'], actual_exact_parts=restore['exact_part_count'],
    own_raw_audit_SHA=sha(raw_path), own_raw_receipt_SHA=sha(raw_path.parent / 'receipt.json'),
    own_raw_outer_receipt_SHA=sha(review / 'public_blocked_raw01_execution/receipt.json'),
    own_comparison_audit_SHA=sha(comparison_path),
    own_comparison_receipt_SHA=sha(comparison_path.parent / 'receipt.json'),
    own_comparison_outer_receipt_SHA=sha(review / 'public_blocked_compare01_execution/receipt.json'),
    all_guarded_evidence_read_bindings_below_fresh_restored_root=True,
    raw_guarded_read_bindings=len(raw['read_bindings']),
    comparison_guarded_read_bindings=len(comparison['read_bindings']),
    no_original_root_fallback=True, original_workspace_reads=False,
    isolated_python=True, DLL_argument=None, PE_opened_this_public_review=False,
    no_claim_of_new_public_PE_or_engine_performance_measurement=True,
    all42_argv_and_12_reference_bindings_retained=True,
    valid_formal_arms=24, certified_formal_arms=14, open_formal_arms=10,
    qualified_CLI_arms=5, failed_formal_numbers=[25],
    unstarted_formal_numbers=list(range(26, 43)), formal_Seed1_arms_unmeasured=6,
    V100_performance_unassessed=True, own_pair_counts=raw['science']['own_pair_counts'],
    actual_Optimize_prior_evidence=99, journal_returns_prior_evidence=98,
    independently_proved_actual_rc0_without_returned=1,
    actual_reviewer_checks=raw['completed_checks'],
    paid_starts=51, paid_outer_seconds=18618.079987913487,
    own_raw_outer_seconds=raw_outer['elapsed_seconds'],
    own_comparison_outer_seconds=compare_outer['elapsed_seconds'],
    raw_rebuilds_this_closure=0, Optimize=0, native_environment=0, production_edits=0,
    read_bindings=reads, source_SHA=sha(__file__),
    engineering_elapsed_seconds=time.perf_counter()-started,
)
(out / 'audit.json').write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
(out / 'source_at_execution.py').write_bytes(read(__file__))
(out / 'launch.json').write_text(json.dumps(dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=value['source_SHA']),indent=2)+'\n',encoding='utf-8')
(out / 'receipt.json').write_text(json.dumps(dict(exit_code=0, audit_SHA=sha(out/'audit.json'), source_SHA=value['source_SHA'], engineering_elapsed_seconds=time.perf_counter()-started, Optimize=0, native_environment=0,cwd=str(Path.cwd()),explicit_read_root=str(root)),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(decision=value['decision'], raw_checks=value['actual_reviewer_checks'], raw_read_bindings=value['raw_guarded_read_bindings'], Optimize=0)))
