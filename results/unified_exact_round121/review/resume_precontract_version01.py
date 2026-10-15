"""Independent R121 authorized-resume review; never starts native/compile/Git work."""
from pathlib import Path
import ast
import builtins
import collections
import contextlib
import copy
import datetime
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import types

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/unified_exact_round121'
REVIEW = OUT/'review'
BASELINE = REVIEW/'resume_precontract_baseline.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def snapshot(directory):
    directory = Path(directory)
    return {p.relative_to(directory).as_posix(): sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def baseline():
    start = time.perf_counter()
    h100 = read(OUT/'qualification/h100/identity.json')
    preserved = {}
    for launch in h100['launches']:
        d = Path(launch['destination'])
        if launch['arm'] in ['MB-D0', 'MB-D1']:
            assert not d.exists()
            continue
        producer, seal = read(d/'producer_receipt.json'), read(d/'producer_seal.json')
        assert producer['producer_seal_SHA'] == sha(d/'producer_seal.json')
        assert all(sha(d/name) == digest for name, digest in seal['required_SHA'].items())
        preserved[launch['arm']] = dict(path=str(d), files=snapshot(d), producer=producer,
            original_audit_passed=read(d/'audit.json')['passed'],
            original_closeout=(d/'arm_total_receipt.json').exists())
    assert preserved['P-GRB']['original_audit_passed'] and preserved['P-GRB']['original_closeout']
    assert not preserved['M-B']['original_audit_passed'] and not preserved['M-B']['original_closeout']
    fees = {}
    for name in ['qualification01', 'qualification02', 'qualification03', 'qualification04']:
        d = OUT/'fees'/name
        receipt = read(d/'receipt.json')
        assert receipt['actual_exit_observed'] and receipt['exit_code'] == 1
        assert not receipt['nested_native_seconds_added']
        fees[name] = dict(files=snapshot(d), receipt=receipt, launch=read(d/'launch.json'))
    starts = sum(f['receipt']['conservative_process_starts'] for f in fees.values())
    seconds = sum(f['receipt']['outer_seconds_upper'] for f in fees.values())
    assert starts == 7 and seconds == 445.13650035858154
    for group in read(OUT/'argv_freeze.json')['groups']:
        for launch in read(OUT/group['campaign']/'identity.json')['launches']:
            assert not Path(launch['destination']).exists()
    p = read(OUT/'production_identity.json')
    assert all(sha(ROOT/name) == digest for name, digest in p['source_bindings'].items())
    assert sha(ROOT/p['production_PE_path']) == p['production_PE_SHA']
    dll = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
    assert sha(dll) == p['DLL_SHA']
    plan = dict(existing_starts=starts, existing_seconds=seconds,
        new_parent=1, new_native_children=['MB-D0', 'MB-D1'], new_starts=3, outer_cap=900,
        qualification_after_declared_starts=starts+3, qualification_after_declared_seconds=seconds+900,
        qualification_limits=[12, 1800], total_limits=[40, 48000],
        reserved_formal_starts=21, reserved_formal_seconds=37800,
        total_after_reserved_starts=starts+3+21, total_after_reserved_seconds=seconds+900+37800,
        formal_arms=16, formal_pairs=18, no_P_MB_exporter_repeat=True)
    assert plan['qualification_after_declared_starts'] <= 12 and plan['qualification_after_declared_seconds'] <= 1800
    assert plan['total_after_reserved_starts'] <= 40 and plan['total_after_reserved_seconds'] <= 48000
    result = dict(kind='independent_authorized_resume_baseline_not_an_admission',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), script_SHA=sha(__file__),
        budget_plan=plan, preserved_producers=preserved, preserved_failed_fees=fees,
        original_H100_identity=read(OUT/'qualification/h100/identity.json'),
        original_H100_identity_SHA=sha(OUT/'qualification/h100/identity.json'),
        original_argv_SHA=sha(OUT/'argv_freeze.json'), original_protocol_SHA=sha(OUT/'protocol.json'),
        original_candidate=read(OUT/'candidate_identity.json'),
        original_candidate_SHA=sha(OUT/'candidate_identity.json'),
        original_final_review_SHA=sha(REVIEW/'extra_review.json'),
        production_source_bindings=p['source_bindings'], PE_SHA=p['production_PE_SHA'], DLL_SHA=p['DLL_SHA'],
        current_perf=time.perf_counter(), current_unix=time.time(),
        final_contract_and_affected_execution_review='PENDING_IMPLEMENTATION',
        reviewer_Optimize=0, reviewer_native_starts=0, reviewer_compiles=0, reviewer_Git=0,
        seconds=time.perf_counter()-start, human_time='unknown')
    write_new(BASELINE, result)
    print(json.dumps(dict(baseline=str(BASELINE), preserved_files={a: len(v['files']) for a, v in preserved.items()},
                         budget=plan, final_contract='PENDING_IMPLEMENTATION', native_starts=0)))


def fee_boundaries():
    """Execute the current fee guard against in-memory paths and budgets only."""
    source = (ROOT/'scripts/round121_common.py').read_text(encoding='utf-8-sig')
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'fee_begin')
    assert isinstance(node.body[0], ast.ImportFrom) and node.body[0].module == 'round115_common'
    assert [n.name for n in node.body[0].names] == ['process_origin']
    node.body = node.body[1:]
    limits = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
              if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
              and n.targets[0].id in ['QUALIFICATION_MAXIMUM_STARTS', 'QUALIFICATION_MAXIMUM_SECONDS']}
    assert limits == dict(QUALIFICATION_MAXIMUM_STARTS=12, QUALIFICATION_MAXIMUM_SECONDS=1800)
    state, writes = {}, []
    class MemoryPath:
        def __truediv__(self, value):
            return self
        def exists(self):
            return state.get('directory_exists', False)
        def mkdir(self, **kwargs):
            writes.append('mkdir')
    namespace = dict(OUT=MemoryPath(), ROOT='REVIEW_MEMORY', process_origin=lambda: (100., 200.),
        budget=lambda: state['budget'], write=lambda p, v: writes.append(v),
        os=type('O', (), {'getpid': staticmethod(lambda: 0)})(),
        sys=type('S', (), {'argv': ['SYNTHETIC_FEE_GUARD']})(), utc=lambda: 'MEMORY', **limits)
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'round121_fee_guard::memory', 'exec'), namespace)
    good = dict(remaining_starts=33, remaining_outer_seconds=47554.86349964142,
                qualification_starts=7, qualification_seconds=445.13650035858154, unclosed=[])
    cases = [('current_authorized_plan', {}, True), ('exact_12_start_boundary', {'qualification_starts': 9}, True),
             ('13_starts_rejected', {'qualification_starts': 10}, False),
             ('exact_1800_seconds_boundary', {'qualification_seconds': 900}, True),
             ('1801_seconds_rejected', {'qualification_seconds': 901}, False),
             ('formal_start_reserve_preserved', {'remaining_starts': 23}, False),
             ('formal_time_reserve_preserved', {'remaining_outer_seconds': 38699}, False),
             ('unclosed_fee_rejected', {'unclosed': ['MEMORY']}, False)]
    result = []
    for name, changes, expected in cases:
        state['budget'], state['directory_exists'] = dict(good, **changes), False
        writes.clear()
        try:
            namespace['fee_begin']('MEMORY', 2, 900, True, dict(starts=21, seconds=37800))
        except AssertionError:
            actual = False
        else:
            actual = True
        assert actual == expected, name
        if not actual:
            assert not writes, 'guard writes before rejecting budget'
        result.append(dict(case=name, accepted=actual))
    return dict(cases=result, maximum_starts=12, maximum_seconds=1800,
                method='Actual current guard AST body with only process-origin import replaced by an in-memory binding; no filesystem or process launch.')


@contextlib.contextmanager
def no_process_launch():
    popen, system = subprocess.Popen, os.system
    def reject(*args, **kwargs):
        raise AssertionError('native/compiler/Git/process launch forbidden in independent review')
    subprocess.Popen, os.system = reject, reject
    try:
        yield
    finally:
        subprocess.Popen, os.system = popen, system


@contextlib.contextmanager
def no_repository_writes():
    """Independent backstop: a broken overlay cannot change the real repository."""
    path_open, regular_open, mkdir = Path.open, builtins.open, Path.mkdir
    def guarded(path, mode='r'):
        if not isinstance(path, int) and any(c in mode for c in 'wxa+'):
            actual = Path(os.path.abspath(os.fspath(path)))
            if actual.is_relative_to(ROOT):
                raise PermissionError('independent repository write backstop: '+str(actual))
        return path
    def safe_path_open(self, mode='r', *args, **kwargs):
        return path_open(guarded(self, mode), mode, *args, **kwargs)
    def safe_open(path, mode='r', *args, **kwargs):
        return regular_open(guarded(path, mode), mode, *args, **kwargs)
    def safe_mkdir(self, *args, **kwargs):
        guarded(self, 'w')
        return mkdir(self, *args, **kwargs)
    Path.open, builtins.open, Path.mkdir = safe_path_open, safe_open, safe_mkdir
    try:
        yield
    finally:
        Path.open, builtins.open, Path.mkdir = path_open, regular_open, mkdir


def affected_reaudits(before):
    """Exercise the real new API against old existing audit files in system temp."""
    import round121_common as common
    import round121_reaudit as recovery
    import round115_common as clocks
    import round121_evidence as evidence
    import read_round118 as reader
    import read_round116 as inherited
    h100 = read(OUT/'qualification/h100/identity.json')
    resumed_identity = read(OUT/'qualification/resume01/identity.json')
    assert resumed_identity['launches'] == h100['launches']
    frozen_helpers = common.helpers()
    identity_cases = []
    reused_launch = h100['launches'][0]
    bad_protocol = copy.deepcopy(resumed_identity)
    bad_protocol['prereg_sha256'] = 'INCORRECT_CURRENT_AUDITOR_PROTOCOL'
    bad_helpers = copy.deepcopy(resumed_identity)
    bad_helpers['helpers'] = h100['helpers']
    bad_seed = copy.deepcopy(reused_launch)
    bad_seed['seed'] = 0
    for name, launch_case, identity_case in [
            ('wrong_current_protocol', reused_launch, bad_protocol),
            ('old_helpers_as_final_auditor', reused_launch, bad_helpers),
            ('wrong_producer_Seed', bad_seed, resumed_identity)]:
        try:
            recovery.producer_identity(launch_case, identity_case)
        except AssertionError:
            identity_cases.append(dict(case=name, rejected=True))
        else:
            raise AssertionError('producer/auditor provenance boundary accepted '+name)
    assert all(recovery.producer_identity(l, resumed_identity) is resumed_identity for l in resumed_identity['launches'][2:])
    results = []
    with tempfile.TemporaryDirectory(prefix='r121-resume-independent-') as temporary:
        temporary = Path(temporary).resolve()
        assert temporary.parent == Path(tempfile.gettempdir()).resolve() and temporary.name.startswith('r121-resume-independent-')
        for launch in h100['launches']:
            if launch['arm'] not in ['P-GRB', 'M-B']:
                continue
            raw = Path(launch['destination'])
            saved = before['preserved_producers'][launch['arm']]
            producer_identity = recovery.producer_identity(launch, resumed_identity)
            assert producer_identity == before['original_H100_identity']
            assert producer_identity['prereg_sha256'] == before['original_protocol_SHA']
            assert producer_identity['helpers'] != frozen_helpers
            assert (raw/'audit.json').exists() and snapshot(raw) == saved['files']
            replay_start = time.perf_counter()
            attempt = temporary/launch['arm']
            result = recovery.replay(launch, resumed_identity, attempt)
            assert result['passed'] and result['original_all_file_SHA'] == saved['files']
            assert result['helpers'] == frozen_helpers and result['source_bindings'] == before['production_source_bindings']
            assert result['producer_identity_SHA'] == before['original_H100_identity_SHA']
            assert result['producer_prereg_SHA'] == before['original_protocol_SHA']
            assert result['final_auditor_identity_SHA'] == sha(OUT/'qualification/resume01/identity.json')
            assert result['final_protocol_SHA'] == sha(OUT/'protocol.json')
            assert result['authorization_SHA'] == sha(OUT/'resumption/authorization01.json')
            assert result['original_T_produce'] == saved['producer']['T_produce']
            assert read(raw/'audit.json')['passed'] == saved['original_audit_passed']
            assert (raw/'arm_total_receipt.json').exists() == saved['original_closeout']
            essential = {'audit.json', 'independent_evidence.json', 'native_claims.json', 'claim_rejections.json',
                'verification_closeout.json', 'arm_total_receipt.json', 'postexit_audit_receipt.json',
                'audit_execution_metrics.json', 'round120_model_contracts.json', 'call_log_views.json',
                'round120_extended_verification.json'}
            assert essential <= result['derived_file_SHA'].keys()
            assert read(attempt/'audit.json')['passed'] is True
            with recovery.saved_view(raw, attempt):
                assert read(raw/'audit.json') == read(attempt/'audit.json')
                assert sha(raw/'audit.json') == sha(attempt/'audit.json')
                assert (raw/'arm_total_receipt.json').exists() and (raw/'arm_total_receipt.json').is_file()
                assert 'arm_total_receipt.json' in {p.name for p in raw.glob('*.json')}
                assert 'arm_total_receipt.json' in {p.name for p in raw.iterdir()}
                clock = clocks.clock_evidence(raw, launch)
                assert clock['T_produce'] == saved['producer']['T_produce']
                assert clock['T_verify'] >= replay_start-saved['producer']['t_produce_perf']
                assert abs(clock['T_total']-clock['T_produce']-clock['T_verify']) < 1e-8
                recs = collections.defaultdict(list)
                with evidence.extension():
                    item = reader.item(ROOT, launch, producer_identity, recs)
                    assert item['complete']
                    final = inherited.reconcile(item['claims'], item['ind']['witnesses'])
                    assert not final['rejections']
                    endpoint = reader.finalize(ROOT, item, final, recs)
                assert endpoint['formal_protocol_qualified'] and endpoint['T_produce'] == saved['producer']['T_produce']
            try:
                recovery.replay(launch, resumed_identity, attempt)
            except FileExistsError:
                pass
            else:
                raise AssertionError('existing attempt was not exclusive')
            with recovery.derived_view(raw, attempt):
                try:
                    (raw/'result.json').write_text('FORBIDDEN')
                except AssertionError:
                    pass
                else:
                    raise AssertionError('raw producer overwrite was allowed')
            audit_bytes = (attempt/'audit.json').read_bytes()
            (attempt/'audit.json').write_bytes(audit_bytes+b' ')
            try:
                with recovery.saved_view(raw, attempt):
                    raise RuntimeError('tampered saved view was accepted')
            except AssertionError:
                pass
            finally:
                (attempt/'audit.json').write_bytes(audit_bytes)
            assert snapshot(raw) == saved['files']
            results.append(dict(arm=launch['arm'], real_existing_original_audit_present=True,
                old_audit_passed=saved['original_audit_passed'], old_closeout_present=saved['original_closeout'],
                original_file_count=len(saved['files']), all_original_files_SHA_unchanged=True,
                actual_complete_inherited_audit_and_item_finalize_passed=True,
                original_producer_identity_SHA=result['producer_identity_SHA'],
                original_producer_prereg_SHA=result['producer_prereg_SHA'],
                current_auditor_identity_SHA=result['final_auditor_identity_SHA'],
                current_auditor_protocol_SHA=result['final_protocol_SHA'],
                original_endpoint_identity_predicate_preserved=True, provenance_negative_cases=identity_cases,
                new_audit_SHA=sha(attempt/'audit.json'), new_closeout_SHA=sha(attempt/'verification_closeout.json'),
                new_total_receipt=read(attempt/'arm_total_receipt.json'), endpoint=endpoint, clock=clock,
                derived_file_SHA=result['derived_file_SHA'], replay_seconds=result['replay_seconds'],
                old_T_produce_unchanged=True, waiting_gap_retained=True,
                saved_view_open_read_sha_stat_glob_iterdir_priorities_checked=True,
                duplicate_attempt_rejected=True, producer_overwrite_rejected=True,
                tampered_new_audit_rejected_without_fallback=True,
                test_root=str(temporary), system_temp_outputs_removed_after_review=True))
        assert common.helpers() == frozen_helpers, 'helpers changed during affected review'
        assert temporary.parent == Path(tempfile.gettempdir()).resolve() and temporary.name.startswith('r121-resume-independent-')
    assert not temporary.exists()
    return results


def supervisor_fixture():
    """Run only the new tracked-Popen wrapper with fake child handles."""
    source = (ROOT/'scripts/round121_campaign.py').read_text(encoding='utf-8-sig')
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'supervised')
    events, receipts, captured, state = [], [], {}, {}
    class MemoryPath:
        parents = ['MEMORY_PARENT', 'MEMORY_CAMPAIGN']
        def __truediv__(self, name):
            return 'MEMORY/'+name
        def is_dir(self):
            return False
    class FakeChild:
        pid = 4242
        def kill(self):
            events.append('kill')
            if state['case'] == 'kill_error':
                raise RuntimeError('simulated kill error')
        def wait(self):
            events.append('wait')
    def popen(*args, **kwargs):
        captured['args'], captured['kwargs'] = args, kwargs
        events.append('popen')
        return FakeChild()
    def creation(child):
        events.append('creation')
        if state['case'] == 'creation_error':
            raise OSError('simulated OS creation query failure')
        return 1234567.25
    def record(path, value):
        events.append('write')
        if state['case'] in ['write_error', 'kill_error']:
            raise OSError('simulated receipt write failure')
        receipts.append((path, value))
    launch = dict(destination='MEMORY', command=['FROZEN_PE', '--gurobi-seed', '1'], seed=1)
    expected_kwargs = dict(cwd='MEMORY_ROOT', env={'UNCHANGED': 'ENV'}, stdout='MEMORY_OUT', stderr='MEMORY_ERR', creationflags=123)
    production_check = object()
    def factory(namespace):
        assert namespace['ROOT'] == 'MEMORY_ROOT' and namespace['_arm_tick'] == 99
        assert namespace['production_check'] is production_check and namespace['untouched_supervisor_binding'] == 'PRESERVED'
        def runner(actual, prereg, identity):
            assert actual == launch and prereg == {'same': 'PREREG'}
            return namespace['subprocess'].Popen(actual['command'], **expected_kwargs)
        return runner
    prior = types.SimpleNamespace(supervisor=types.SimpleNamespace(untouched_supervisor_binding='PRESERVED'),
        production_check=production_check,
        inherited=types.SimpleNamespace(OptionalPublisher=lambda l: object(), supervisor_function=factory))
    namespace = dict(Path=lambda x: MemoryPath(), prior=prior, ROOT='MEMORY_ROOT',
        subprocess=types.SimpleNamespace(Popen=popen, untouched_subprocess_binding='PRESERVED'),
        types=types, write=record, child_creation=creation, os=types.SimpleNamespace(getpid=lambda: 17),
        SOURCE='FROZEN_SOURCE', PE_SHA='FROZEN_PE_SHA')
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'round121_supervisor::fake_child_only', 'exec'), namespace)
    checked = []
    for case in ['normal', 'creation_error', 'write_error', 'kill_error']:
        state['case'] = case
        events.clear(); receipts.clear(); captured.clear()
        try:
            namespace['supervised'](launch, {'prereg': {'same': 'PREREG'}}, 99)
        except (OSError, RuntimeError):
            assert case != 'normal'
        else:
            assert case == 'normal'
        assert captured == dict(args=(launch['command'],), kwargs=expected_kwargs)
        if case == 'normal':
            assert events == ['popen', 'creation', 'write']
            assert receipts[0][1] == dict(pid=4242, parent_pid=17, actual_creation_unix=1234567.25,
                command=launch['command'], seed=1, source_commit='FROZEN_SOURCE', PE_SHA='FROZEN_PE_SHA', creation_from_live_OS_handle=True)
        else:
            assert events[-2:] == ['kill', 'wait'], (case, events)
        checked.append(dict(case=case, events=list(events), launch_arguments_unchanged=True))
    old = (ROOT/'scripts/round120_campaign.py').read_text(encoding='utf-8-sig')
    old_fn = next(n for n in ast.parse(old).body if isinstance(n, ast.FunctionDef) and n.name == 'finish_producer')
    new_fn = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'finish_producer')
    lists = [n for n in ast.walk(new_fn) if isinstance(n, ast.List) and all(isinstance(v, ast.Constant) for v in n.elts)]
    assert any('child_process_origin.json' in [v.value for v in n.elts] for n in lists)
    new_fn = ast.fix_missing_locations(new_fn)
    class RemoveChildReceipt(ast.NodeTransformer):
        def visit_List(self, node):
            node.elts = [v for v in node.elts if not isinstance(v, ast.Constant) or v.value != 'child_process_origin.json']
            return self.generic_visit(node)
    normalized_new = RemoveChildReceipt().visit(new_fn)
    assert ast.dump(old_fn, include_attributes=False) == ast.dump(normalized_new, include_attributes=False)
    return dict(cases=checked, finish_producer_AST_identical_except_added_child_receipt_in_seal=True,
        same_original_supervisor_factory_and_namespace=True, no_actual_processes=True,
        scope='New wrapper only. Existing complete R90 supervisor, original parameter/affinity/deadline/return behavior remain in the unchanged inherited factory.')


def contract_bindings(before):
    import round121_common as common
    candidate = read(OUT/'candidate_identity.json')
    frozen = read(OUT/'resumption/final_freeze01.json')
    authorization = read(OUT/'resumption/authorization01.json')
    resumed = read(OUT/'qualification/resume01/identity.json')
    actual_helpers, actual_sources = common.helpers(), common.bindings()
    assert len(actual_helpers) == 89 and len(actual_sources) == 216
    assert actual_sources == before['production_source_bindings'] == candidate['source_bindings'] == frozen['source_bindings'] == resumed['source_hashes']
    assert actual_helpers == candidate['helpers'] == frozen['helpers'] == resumed['helpers']
    assert all(sha(ROOT/name) == digest for name, digest in actual_helpers.items())
    assert all(sha(ROOT/name) == digest for name, digest in actual_sources.items())
    assert common.identity()['production_PE_SHA'] == before['PE_SHA'] and sha(common.DLL) == before['DLL_SHA']
    immutable_math = ['scripts/round121_data.py', 'scripts/round121_decision.py', 'scripts/round121_evidence.py',
                      'scripts/read_round121.py', 'scripts/round121_reference.cpp']
    old_helpers = before['original_candidate']['helpers']
    changes = {name: dict(before=old_helpers.get(name), after=digest) for name, digest in actual_helpers.items() if old_helpers.get(name) != digest}
    assert set(changes) <= {'scripts/round121_common.py', 'scripts/round121_prepare.py', 'scripts/round121_campaign.py',
                            'scripts/qualify_round121.py', 'scripts/round121_fixtures.py', 'scripts/round121_reaudit.py'}
    assert all(actual_helpers[name] == old_helpers[name] for name in immutable_math)
    assert sha(OUT/'argv_freeze.json') == before['original_argv_SHA'] == authorization['formal_argv_SHA'] == frozen['formal_argv_SHA']
    assert sha(OUT/'input_manifest.json') == authorization['input_manifest_SHA'] == frozen['input_manifest_SHA'] == candidate['input_manifest_SHA']
    assert sha(OUT/'qualification/h100/identity.json') == before['original_H100_identity_SHA'] == authorization['original_H100_identity_SHA'] == frozen['original_H100_identity_SHA']
    assert resumed['launches'] == before['original_H100_identity']['launches']
    assert resumed['prereg'] == before['original_H100_identity']['prereg']
    assert resumed['original_producer_identity_SHA'] == before['original_H100_identity_SHA']
    assert sha(OUT/'qualification/resume01/identity.json') == candidate['resumed_qualification_identity_SHA'] == frozen['resume_identity_SHA']
    assert sha(OUT/'resumption/authorization01.json') == candidate['resumption_authorization_SHA'] == resumed['resume_authorization_SHA'] == frozen['authorization_SHA']
    assert sha(OUT/'candidate_identity.json') == frozen['candidate_identity_SHA']
    assert sha(OUT/'protocol.json') == frozen['protocol_SHA'] == candidate['protocol_SHA'] == resumed['prereg_sha256']
    protocol = read(OUT/'protocol.json')
    assert (protocol['maximum_starts'], protocol['maximum_outer_seconds'], protocol['qualification_maximum_starts'], protocol['qualification_maximum_seconds']) == (40, 48000, 12, 1800)
    assert protocol['qualification_start_amendment']['SHA'] == frozen['authorization_SHA']
    original_protocol = dict(protocol)
    del original_protocol['qualification_start_amendment']
    original_protocol['qualification_maximum_starts'] = 8
    original_protocol_path = OUT/'resumption/before_resume01/protocol.json'
    assert sha(original_protocol_path) == before['original_protocol_SHA'] == authorization['original_protocol_SHA']
    assert original_protocol == read(original_protocol_path)
    policy_path = OUT/'measurement_policy_v2.md'
    original_policy_path = OUT/'resumption/before_resume01/measurement_policy_v2.md'
    assert sha(original_policy_path) == before['original_H100_identity']['measurement_policy_SHA']
    assert policy_path.read_text(encoding='utf-8').startswith(original_policy_path.read_text(encoding='utf-8'))
    assert resumed['measurement_policy_SHA'] == sha(policy_path)
    assert authorization['previous_qualification_starts'] == 8 and authorization['new_qualification_starts'] == 12
    assert (authorization['qualification_seconds'], authorization['total_starts'], authorization['total_seconds']) == (1800, 40, 48000)
    assert authorization['proposed_new_native_children'] == ['MB-D0', 'MB-D1'] and authorization['proposed_outer_cap'] == 900
    assert authorization['formal_arms'] == 16 and authorization['formal_pairs'] == 18 and authorization['no_formal_retry']
    count = 0
    argv = read(OUT/'argv_freeze.json')
    for group in argv['groups']:
        identity_path = OUT/group['campaign']/'identity.json'
        identity = read(identity_path)
        plan = next(v for v in argv['plans'] if v['name'] == group['campaign'])
        assert identity['helpers'] == actual_helpers and identity['source_hashes'] == actual_sources
        assert identity['measurement_policy_SHA'] == sha(policy_path)
        assert sha(identity_path) == candidate['campaign_identities'][group['campaign']]
        for launch, declared in zip(identity['launches'], plan['launches']):
            expected_command = list(declared['command'])
            for index, value in enumerate(expected_command):
                if value == 'REFERENCE_FINGERPRINT':
                    assert launch['arm'] == 'P-GRB' and expected_command[index-1] == '--round24-expected-gurobi-model-fingerprint'
                    expected_command[index] = str(launch['panel']['reference']['fingerprint'])
            assert launch['command'] == expected_command
            reference = OUT/'qualification/reference'/launch['id']
            assert read(reference/'build.json') == launch['panel']['reference']
            assert sha(reference/'original.lp') == launch['panel']['reference']['canonical_sha256']
            assert not Path(launch['destination']).exists()
            count += 1
    assert count == 16
    assert not (OUT/'review/performance_admission.json').exists()
    assert not any((OUT/'qualification/resume01/recovery').glob('*'))
    assert all(not Path(l['destination']).exists() for l in resumed['launches'][2:])
    assert sha(REVIEW/'extra_review.json') == before['original_final_review_SHA']
    for name, saved in before['preserved_failed_fees'].items():
        assert snapshot(OUT/'fees'/name) == saved['files']
        assert authorization['existing_fee_SHA'][name] == saved['files']['receipt.json']
    budget = common.budget()
    assert budget['paid_starts'] == budget['qualification_starts'] == 7
    assert budget['paid_outer_seconds'] == budget['qualification_seconds'] == 445.13650035858154 and not budget['unclosed']
    return dict(helpers=actual_helpers, source_bindings=actual_sources, changes_from_prior_blocked_contract=changes,
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'), protocol_SHA=sha(OUT/'protocol.json'),
        argv_SHA=sha(OUT/'argv_freeze.json'), input_manifest_SHA=sha(OUT/'input_manifest.json'),
        resume_identity_SHA=sha(OUT/'qualification/resume01/identity.json'), authorization_SHA=sha(OUT/'resumption/authorization01.json'),
        final_freeze_SHA=sha(OUT/'resumption/final_freeze01.json'),
        original_H100_identity_SHA=before['original_H100_identity_SHA'], mathematical_and_inherited_audit_helpers_unchanged=True,
        frozen_reference_placeholder_resolved_only_from_bound_zero_Optimize_canonical_reference=True,
        original_protocol_exact_SHA_preserved_authorized_limit_and_amendment_only_semantic_delta=True,
        original_protocol_SHA=sha(original_protocol_path), measurement_policy_SHA=sha(policy_path),
        original_measurement_policy_SHA=sha(original_policy_path), original_policy_retained_and_only_authorization_appended=True,
        preserved_failed_fees=4, raw_D0_D1_and_all16_formal_NOT_STARTED=True,
        qualification_start_command=[str(common.PYTHON), str(ROOT/'scripts/qualify_round121.py'), 'qualification05', '--resume-four-cli'])


def check():
    tick = time.perf_counter()
    before = read(BASELINE)
    with no_process_launch(), no_repository_writes():
        bindings = contract_bindings(before)
        fees = fee_boundaries()
        supervisor = supervisor_fixture()
        reaudits = affected_reaudits(before)
        assert bindings == contract_bindings(before)
    result = dict(decision='ACCEPT', scope='One resumed qualification parent and only real D0/D1 Seed1 children; no formal/performance admission',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), reviewer='real different executor',
        script_SHA=sha(__file__), baseline_SHA=sha(BASELINE), **bindings,
        budget_plan=before['budget_plan'], fee_guard_memory_execution=fees, supervisor_fake_child_execution=supervisor,
        actual_existing_P_MB_affected_reaudits=reaudits,
        old_raw_failed_audits_producer_receipts_seals_and_fees_unchanged=True,
        T_produce_original_and_full_waiting_gap_in_T_verify=True,
        corrected_engineering_findings=[dict(path='review/'+p.name, SHA=sha(p)) for p in sorted(REVIEW.glob('resume_precontract_finding*.json'))],
        D0_D1_actual_Seed1_qualification='PENDING_NOT_EXECUTED',
        formal16_and_pairs18='PENDING_NOT_EXECUTED',
        original_scientific_confirmation='INCOMPLETE_PENDING_ACTUAL_QUALIFICATION_AND_ALL_FORMAL_RESULTS',
        limitations=['Affected checks use real P/MB evidence and final inherited audit predicates, with outputs in deleted system temp attempts; they do not replace the future persistent recovery receipts.',
            'The new supervisor was exercised with fake handles only; actual new child PID/OS creation/affinity/seal/clock facts remain necessary after launch.',
            'D0/D1 native settings, actual matrices/three rows/Start/physical endpoint and full-H equality must pass in the billed new qualification; no installed exposure is manufactured.',
            'No new route, bound, LP, native Optimize, production source change, compile or Git action occurred; all prior failures and the earlier blocked scientific state remain historical evidence.'],
        reviewer_native_starts=0, reviewer_Optimize=0, reviewer_compiles=0, reviewer_Git=0,
        seconds=time.perf_counter()-tick, human_time='unknown')
    write_new(REVIEW/'resume_precontract.json', result)
    lines = ['# R121 resumed qualification independent pre-contract review', '',
        '**Decision: ACCEPT for the single resumed qualification parent and D0/D1 children only.** Formal admission and the scientific confirmation remain pending.', '',
        'The explicit continuation changes cumulative qualification starts from 8 to 12; qualification time stays 1800 seconds and total stays 40 starts/48000 seconds. The reviewed plan is 7 existing starts/445.1365003586 seconds plus one parent/two children capped at 900 seconds: qualification at most 10/1345.1365003586. Reserving the unchanged formal 21 starts/37800 seconds gives 31/39145.1365003586 overall.', '',
        'The current guard passed finite memory-only checks at both exact limits and rejected excess/unclosed/insufficient-formal-reserve cases. The original frozen argv, roles, input manifest, all source bindings, PE/DLL and old H100 identity are unchanged. The exact original protocol SHA is preserved in a saved copy; its only semantic changes are the authorized qualification limit and amendment metadata. The measurement policy retains all prior text and appends the authorization. The final helper/candidate/protocol/resume identity/authorization hashes are in the JSON.', '',
        'The final re-audit implementation was actually called with the resumed identity against the real existing P and MB audit files. Each full inherited audit, item/finalize and saved-view readback passed using exclusive system-temp attempts. All 479 P and 2130 MB original files, including old failed audit and original producer clocks/seals, and every old failed fee file remain byte-identical. New audit/closeout/total receipts were used by read, SHA, stat, glob and iterdir. Duplicate attempts, immutable producer writes and a tampered saved audit were rejected. Temporary outputs were deleted and do not substitute for the required persistent recovery.', '',
        'T_produce stays exactly 90.6787239999976 seconds for P and 89.60989649999829 for MB. T_verify extends from each original seal to the new verification end, retaining the entire waiting gap; T_total retains T_produce+T_verify. This old waiting interval is not charged again as new native or outer-parent time.', '',
        'The new supervisor wrapper passed fake-child normal, OS creation-query failure, birth-receipt write failure and kill-error cleanup checks; launch arguments were unchanged and wait occurred on every failure. Its producer-closeout AST equals the inherited function after removing only the additional child-origin file from the seal list. No native child was launched by this review.', '',
        '**Still required:** real D0/D1 Seed1 CLI evidence, all unchanged native/model/Start/scope/physical/three-row/H checks, persistent P/MB recovery receipts, actual parent exit and fee closure; only then may the separate formal gate authorize 16 formal positions and 18 pairs. The original scientific confirmation is incomplete. A different-executor full extra review remains required after all analysis/results.', '',
        'Scope limits: zero native starts/Optimize/compile/Git; no production or original raw/fee/gate files modified. Earlier pre-contract and extra-review reports were retained.', '']
    with (REVIEW/'resume_precontract.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(json.dumps(dict(decision='ACCEPT', scope=result['scope'], actual_affected_arms=[r['arm'] for r in reaudits],
        helpers=len(bindings['helpers']), sources=len(bindings['source_bindings']), seconds=result['seconds'], native_starts=0, Optimize=0)))


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ['baseline', 'check']
    baseline() if sys.argv[1] == 'baseline' else check()
