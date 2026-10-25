"""Independent bounded metadata review; never import an execution helper."""
from pathlib import Path
import ast, datetime, hashlib, json, time, zipfile, zlib

ROOT = Path('E:/codes/ExactEBRP-work/worktrees/round133')
OUT = ROOT/'results/unified_exact_round133'
tick = time.perf_counter()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def actual(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT.resolve()), str(path)
    return path

expected_sources = {
    'scripts/round133_portable_check.py': '6024c92660aed5d78a6fade0f371cac4621bc822d74008296a5539319b93a37d',
    'scripts/round133_public_restore.py': 'b8062780c069e252df5306d79fc5b1c22038d1adf4f0ec229cdaddc1cbca5aa8',
    'scripts/round133_delivery_preflight.py': 'ab1df3176e01c8b5d24017e4c7a6c5175b9a2c69a2e82195fdb21ff43a80f111',
    'scripts/round133_release.py': '411958a6d79d23205ac718caed5569a24cb9cfda82253261de589ec08e212127',
    'scripts/round133_cleanup.py': '136a35cf99c66b380d2d1ee0a9c54279852cccf38ab284592f0a1488449f0072',
}
for name, value in expected_sources.items():
    assert sha(ROOT/name) == value, name
    ast.parse((ROOT/name).read_text(encoding='utf-8-sig'))

fee = OUT/'fees/delivery_portable_local_preflight_01'
receipt = read(fee/'receipt.json')
assert receipt['exit_code'] == 0 and not receipt['timeout'] and receipt['exit_observed']
assert receipt['G1_seconds'] == 0 and receipt['budget_category'] == 'postverify'
assert receipt['outer_seconds'] == 399.6160910000326
assert sha(fee/'stdout.log') == '9262592abe645cb3b3c89ce2514eb429c138d0e688a18cf364e5cf7eb79ee40a'
assert (fee/'stderr.log').stat().st_size == 0
local = read(fee/'stdout.log')
assert local['passed'] and local['local_preflight'] and not local['public_empty_root_recovery']
assert local['formal_positions'] == 22 and local['unit_positions'] == 1
assert local['unit_in_formal_or_performance_denominator'] is False
assert local['original_measured_clocks_preserved']
for key in ('Optimize','compile','native_compile','DLL_load','vendor_DLL_load','subprocess_calls','Git_calls','new_scientific_enumeration'):
    assert local[key] == 0, key
assert local['DLL_load_scope'] == 'solver/vendor only; Python runtime separately recorded'
assert [r['name'] for r in local['Python_standard_runtime_initialization']] == ['libpython3.12.dll','kernel32']

executed = OUT/'infra/portable_source_versions/local_preflight01_e35a951be.py'
assert sha(executed) == 'e35a951be774ba9219945a11f91003896c888fd3096b21b5bfe9b5ee1a9520dc'
def executable_ast(path):
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    assert isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant)
    assert isinstance(tree.body.pop(0).value.value, str)
    return ast.dump(tree, include_attributes=False)
assert executable_ast(executed) == executable_ast(ROOT/'scripts/round133_portable_check.py')

groups = []
for stage in ('D1','D3'):
    groups.extend(read(OUT/'plans'/f'{stage}_matrix_frozen.json')['groups'])
records = local['records']
assert len(records) == 23 and sum(r['formal'] for r in records) == 22
verified_links = []
for group, record in zip(groups, records[:22]):
    launch = group['launch']; directory = actual(launch['destination'])
    assert record['arm_id'] == launch['arm_id'] and record['formal'] and record['full_replay']
    assert record['actual_policy'] == '8feae approved accepted-H adapter'
    management = record['effective_management_receipt']
    assert management['identity_SHA'] == group['identity_SHA']
    for key in ('binding','success'):
        assert sha(actual(management[key+'_path'])) == management[key+'_SHA']
    assert set(management['outputs']) == {'audit.json','verification_closeout.json','arm_total_receipt.json','round133_endpoint.json'}
    for name, value in management['outputs'].items():
        assert sha(directory/name) == value, (record['arm_id'],name)
    total = read(directory/'arm_total_receipt.json')
    producer = read(directory/'producer_receipt.json')
    assert record['stored_clock']['T_produce'] == producer['T_produce']
    assert sha(directory/'producer_receipt.json') == total['producer_receipt_SHA']
    for key in ('T_verify','T_total'):
        assert record['stored_clock'][key] == total[key], (record['arm_id'],key)
    clone = record['source_rewrite_binding']
    assert clone['source_physical_model_H_Start_return_cover_source_predicates_changed'] is False
    assert len(clone['exhaustive_substitution_whitelist']) == 5
    assert all(r['count'] == 1 for r in clone['exhaustive_substitution_whitelist'])
    for row in record['compared_outputs']:
        assert sha(directory/row['name']) == row['stored_SHA']
    verified_links.append(dict(arm_id=record['arm_id'],identity_SHA=group['identity_SHA'],
        management_binding_SHA=management['binding_SHA'],management_success_SHA=management['success_SHA'],
        original_derived_files=len(record['compared_outputs']),measured_clocks=record['stored_clock']))
formal = records[:22]; unit = records[22]
assert all(r['implementation_qualified'] and r['model_scope_qualified'] for r in formal)
assert sum(r['certificate'] for r in formal) == 16
assert sum(r['source_reduced'] for r in formal) == 1
assert sum(r['role_performance_evidence_eligible'] for r in formal) == 21
assert not unit['formal'] and unit['full_replay'] and unit['certificate']
assert unit['actual_policy'] == '933 frozen original unit policy'
assert unit['role_performance_evidence_eligible'] is False
assert local['unit_oracle']['exact_inventory_lower_bound'] == '3/2'
assert local['unit_oracle']['formal_denominator_contribution'] == 0

pub = read(OUT/'source_publication.json')
assert sha(OUT/'source_publication.json') == local['source_publication_SHA'] == '2a6ca115e28c1ef06daa66cd1d363dda2ef64747fbefcdbc647220fe1eccc329'
candidate = read(OUT/'candidate_manifest.json')
source_expected = dict(candidate['source_hashes'])
source_expected['generated/CplexBaselineResearch.cpp'] = candidate['generated_research_source']['SHA']
zip_receipts = []
for row, expected in ((pub['candidate_source_bundle'],source_expected),
                      (pub['execution_helpers'],pub['execution_helpers']['members'])):
    path = ROOT/row['path']
    assert sha(path) == row['SHA'] and path.stat().st_size == row['bytes']
    with zipfile.ZipFile(path) as archive:
        assert len(archive.infolist()) == len(expected) and set(archive.namelist()) == set(expected)
        for info in archive.infolist():
            raw = archive.read(info)
            assert hashlib.sha256(raw).hexdigest() == expected[info.filename]
            assert zlib.crc32(raw)&0xffffffff == info.CRC
    zip_receipts.append(dict(path=row['path'],SHA=row['SHA'],members=len(expected),CRC_and_member_SHA_verified=True))
assert len(source_expected) == 110 and len(pub['execution_helpers']['members']) == 89
for row in pub['reused_main_source_and_bindings']:
    path = actual(ROOT/row['path'])
    assert sha(path) == row['SHA'] and path.stat().st_size == row['bytes']
assert len(pub['reused_main_source_and_bindings']) == 4
for key,row in pub['old_E3_source_dependencies'].items():
    assert key == row['source_commit']+':'+row['source_path']
    path = actual(ROOT/row['path'])
    assert sha(path) == row['SHA'] and path.stat().st_size == row['bytes']
assert len(pub['old_E3_source_dependencies']) == 217

preflight = OUT/'qualification/delivery_python_preflight_05.json'
assert sha(preflight) == '4c0d58fe8c8b614d637cfd07096bbda32d6b3625d108d9cd58750fd31f44fae7'
p = read(preflight)
assert p['status'] == 'PASS' and p['check_count'] == 32 and len(p['checks']) == 32
assert all(row['passed'] for row in p['checks'])
for name,value in p['source_hashes'].items(): assert sha(ROOT/'scripts'/name) == value
d24 = OUT/'qualification/D24_portable_point_replay_04.json'
assert sha(d24) == '964f6d9d2d6eb25de7cba78e76721dafd3e6d069aee9128ab2eaaab2ebc798dd'
d = read(d24)
assert d['status'] == 'PASS' and d['source_remains'] == 'REJECTED'
assert d['complete_serialized_point']['exactly_feasible']
assert len(d['saved_loaded_signed_zero_only']) == 3
assert d['Optimize'] == d['native_starts'] == d['compilation'] == 0

result = dict(schema='round133-independent-delivery-tool-and-local-replay-review-v1',
    UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='/root/reliability_review',
    primary_delivery_launcher='/root',decision='ACCEPT_SOURCE_REVIEW_AND_ACTUAL_LOCAL_REPLAY_ONLY',
    source_hashes=expected_sources,executed_portable_SHA=sha(executed),executable_AST_identical=True,
    local_full_replay=dict(stdout_SHA=sha(fee/'stdout.log'),fee_receipt_SHA=sha(fee/'receipt.json'),
        outer_seconds=receipt['outer_seconds'],formal_positions=22,unit_positions=1,
        formal_implementation_qualified=22,formal_certificates=16,formal_qualified_open=5,
        formal_source_rejected_safe_open=1,unit_in_formal_or_performance_denominator=False,
        original_measured_clocks_preserved=True,scientific_predicates_reexecuted=True,
        native_assets='PE/DLL/object/library historical execution attestations; never locally remeasured',
        standard_runtime_initialization=local['Python_standard_runtime_initialization']),
    management_and_output_links=verified_links,source_publication_SHA=sha(OUT/'source_publication.json'),
    exact_source_bundles=zip_receipts,reused_main_sources_and_bindings=4,old_named_source_bytes=217,
    source_contract_preflight_SHA=sha(preflight),source_contract_checks=32,D24_guard_replay_SHA=sha(d24),
    portable_source_review=[
        'Only five exhaustive verifier substitutions change path/closed-replay timing transport; original science predicates remain.',
        'Formal replay executes actual pinned 8fe adapter H/PS postseal context plus original 933 verifier; unit executes original 933 policy.',
        'Named derived JSON outputs remain in memory; normalized comparisons change only roots, derived hash links and independent offline replay wall.',
        'Explicit scoped allowlist forbids old-round/current-worktree fallback masking a missing published dependency.',
        'Project imports are pinned source bytes; vendor imports, process, network and vendor DLL entry are blocked; two standard runtime loads are separately disclosed.'
    ],
    public_restore_source_review=[
        'Current fixed-commit HTTPS only; curlrc disabled, ordinary TLS, exact SHA/size text materialization; no HEAD/Git/local-cache fallback.',
        'Only 22 formal carriers, current support and optional progress plus one fixed 213859-byte tiny joint carrier.',
        'Owned empty root, link/traversal checks and external same-volume staging; failed attempts may resume only same root/commit; state PASS unconditionally refuses rerun.',
        'Exact source member sets/SHA/CRC and loose main/old named source checks; final portable SHA is hard-pinned.',
        'Full22+unit1, exact J2/J3 and exact D24/saved-loaded-bits checks are all mandatory before PASS.'
    ],
    cleanup_source_review=dict(status='STATIC_GUARDS_ACCEPTED_EXECUTION_PENDING',
        reviewed_SHA=expected_sources['scripts/round133_cleanup.py'],
        requirements=['Actual public receipt PASS plus independent post-public review with exact receipt SHA.',
            'Owned restored root matches original owner/commit/state; every file belongs to exact manifest/source/carrier/dependency/state set and is SHA/size checked.',
            'Recursive deletion is limited to verified owned recovery root under explicit WORK/restore; original unique current raw and failures remain.',
            'Other removed paths are only resolved TEMP/archives complete duplicates backed by retained hash-checked pieces and hash-recorded TEMP/pdf PNG/final-PDF duplicates.',
            'Pre-delete plan is outside removed targets; one Python filesystem API; actual logical bytes and volume free-space change are distinct.',
            'Final cleanup receipt prevents repetition; old rounds, original/user trees and required PE/DLL assets are retained.']),
    public_recovery_state='PENDING_ACTUAL_PUBLIC_RECOVERY',cleanup_state='PENDING_ACTUAL_PUBLIC_PASS_AND_INDEPENDENT_POST_PUBLIC_GATE',
    PDF_QA_state='PENDING_SEPARATE_ACTUAL_QA',final_delivery_state='PENDING_AFTER_PUBLIC_REMOTE_AND_CLEANUP',
    no_public_or_cleanup_acceptance_implied=True,Optimize=0,native_starts=0,compilation=0,
    full_23_replay_repeated_by_this_review=False,metadata_review_seconds=time.perf_counter()-tick)
target = OUT/'review/delivery_tools_local_review.json'
assert not target.exists()
target.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(decision=result['decision'],receipt=str(target),SHA=sha(target),
    formal=22,unit=1,source_members=[110,89],old_code=217,seconds=result['metadata_review_seconds'])))
