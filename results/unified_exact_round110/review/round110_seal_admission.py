"""Seal the manually reviewed actual admission, without native operations."""
from pathlib import Path
import hashlib, json, sys, time

root = Path(sys.argv[1]).resolve()
review = root/'results/unified_exact_round110/review'
audit_name = sys.argv[2] if len(sys.argv) > 2 else 'admission03'
seal_name = sys.argv[3] if len(sys.argv) > 3 else 'admission_seal01'
assert Path(audit_name).name == audit_name and Path(seal_name).name == seal_name
dest = review/seal_name
dest.mkdir(exist_ok=False)
start = time.perf_counter()
source = Path(__file__).read_bytes()
(dest/'source_at_execution.py').write_bytes(source)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path, obj):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
save(dest/'launch.json', dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
                            source_SHA=hashlib.sha256(source).hexdigest(), Optimize=0, native_environment=0))
audit_path = review/audit_name/'audit.json'
audit = load(audit_path)
assert audit['decision'] == 'ACCEPT' and audit['formal_arms_already_started'] == 0
assert audit['Optimize'] == audit['native_environment'] == 0
assert sha(review/'admission_request.json') == audit['request_SHA']
request = load(review/'admission_request.json')
finite = load(root/request['artifacts']['finite_regressions']['path'])
assert finite['passed'] and finite['checks'] == 58
for name, digest in audit['reviewer_source_bindings'].items():
    assert sha(review/name) == digest
campaign_path = root/'results/unified_exact_round110/campaign/identity.json'
assert sha(campaign_path) == audit['campaign_identity_SHA']
campaign = load(campaign_path)
assert all(not Path(launch['destination']).exists() for launch in campaign['launches'])
manifest_path = root/'results/unified_exact_round110/input_manifest.json'
manifest = load(manifest_path)
old_eligibility_path = root/'results/unified_exact_round109/review/sealed_input_eligibility.json'
old_eligibility = load(old_eligibility_path)
assert old_eligibility['decision'] == 'ACCEPT'
assert old_eligibility['eligible'] == audit['input_eligibility']
assert old_eligibility['frozen_identity_tuples'] == [
    dict(id=r['id'], input_SHA=r['input_sha256'], T_seconds=r['T_seconds'],
         **{'lambda': r['lambda']}, pickup_seconds=r['pickup_seconds'], drop_seconds=r['drop_seconds'])
    for r in manifest['roles']]
eligibility = dict(decision='ACCEPT', input_manifest_SHA=sha(manifest_path),
                   eligibility=audit['input_eligibility'], exact_main_denominator=12,
                   initial_prospective_freeze_round=109,
                   original_eligibility_path=old_eligibility_path.relative_to(root).as_posix(),
                   original_eligibility_SHA=sha(old_eligibility_path),
                   historical_observed_main_roles=[r['id'] for r in manifest['roles'][:8]],
                   historical_unobserved_main_roles=[r['id'] for r in manifest['roles'][8:]],
                   current_round_is_restoration_confirmation=True,
                   all_12_newly_unmeasured_prospective_panel=False,
                   frozen_identity_tuples=old_eligibility['frozen_identity_tuples'],
                   independent_admission_SHA=sha(audit_path), Optimize=0, native_environment=0)
save(review/'sealed_input_eligibility.json', eligibility)
with (review/'performance_admission.json').open('xb') as stream:
    stream.write(audit_path.read_bytes())
save(dest/'manual_review.json', dict(decision='ACCEPT_AND_SEALED',
    actual_admission_path=audit_path.relative_to(root).as_posix(), actual_admission_SHA=sha(audit_path),
    source_and_receipt_failures_preserved=['admission01', 'admission02'],
    failed_attempts_were_reviewer_schema_and_reference_lookup_errors=True,
    primary_policy_source_reviewed=True, primary_actual_finite_regressions_reviewed=finite['checks'],
    actual_corrected_reader_chronology_statement_reviewed=True,
    superseded_pre_formal_signature='admission_seal01/superseded_performance_admission.json',
    current_cold_rejection_scope='current exact full-original cold P only; separately signed actual proof required',
    scoped_E_B_damage_outside_class='HOLD',
    original_missing_return_flags_and_exact_clock_null_preserved=True,
    mechanism_correction='G50-C1 ENS-C and M-B each three LP plus one terminal MIP; ENS zero comes call4 MIPSOL',
    historical_role_observation_and_original_eligibility_distinguished=True,
    Optimize=0, native_environment=0))
save(dest/'receipt.json', dict(exit_code=0, decision='ACCEPT_AND_SEALED',
    engineering_elapsed_seconds=time.perf_counter()-start,
    source_SHA=hashlib.sha256(source).hexdigest(),
    performance_admission_SHA=sha(review/'performance_admission.json'),
    sealed_input_eligibility_SHA=sha(review/'sealed_input_eligibility.json'),
    manual_review_SHA=sha(dest/'manual_review.json'), Optimize=0, native_environment=0))
print(json.dumps(dict(decision='ACCEPT_AND_SEALED', completed_checks=audit['completed_checks'],
                      budget=audit['budget'], performance_admission_SHA=sha(review/'performance_admission.json'))))
