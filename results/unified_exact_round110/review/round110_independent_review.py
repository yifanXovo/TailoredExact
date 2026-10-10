"""R110 independent admission and final raw review, no native calls.

Request schema is documented in admission_request_schema.md. The final review
does not read primary summaries until after its raw reconstruction has closed.
Public execution reads only its supplied restored root and distributes no PE.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, struct, sys, time, traceback
from round110_independent_core import Audit, ROUND, OLD_REVIEW, OLD_PE, DLL_SHA, TOL


class Tee:
    def __init__(self, original, stream):
        self.original, self.stream = original, stream
    def write(self, value):
        self.stream.write(value)
        return self.original.write(value)
    def flush(self):
        self.stream.flush()
        self.original.flush()


def argv_map(command):
    result = {}
    i = 1
    while i < len(command):
        key = command[i]
        assert key.startswith('--') and key not in result
        if key in ('--plain-baseline', '--round100-continuous-quantities'):
            result[key] = True
            i += 1
        else:
            assert i+1 < len(command)
            result[key] = command[i+1]
            i += 2
    return result


def pe_header(a, path):
    data = a.data(path)
    a.require(data[:2] == b'MZ', 'actual native Windows executable')
    offset = struct.unpack_from('<I', data, 0x3c)[0]
    a.require(data[offset:offset+4] == b'PE\0\0', 'actual PE signature')
    optional = offset+24
    magic = struct.unpack_from('<H', data, optional)[0]
    a.require(magic == 0x20b, 'same PE32+ production architecture')
    reserve, commit = struct.unpack_from('<QQ', data, optional+72)
    return dict(magic=magic, stack_reserve=reserve, stack_commit=commit,
                machine=struct.unpack_from('<H', data, offset+4)[0])


def artifact(a, request, label):
    ref = request['artifacts'][label]
    path = a.local(ref['path'])
    a.require(a.sha(path) == ref['SHA'], 'bound actual artifact '+label)
    value = a.obj(path)
    for name, digest in value.get('raw_bindings', {}).items():
        a.require(a.sha(a.local(name)) == digest, 'bound raw artifact '+name)
    return value


def identity(a, request, mode):
    candidate = a.obj(a.out/'candidate_identity.json')
    contract = a.obj(a.out/'candidate_contract_freeze.json')
    production = a.obj(a.out/'production_identity.json')
    campaign = a.obj(a.out/'campaign/identity.json')
    a.require(contract['production_identity_SHA'] == a.sha(a.out/'production_identity.json'),
              'frozen candidate binds actual production identity')
    a.require(candidate['production_PE_SHA'] == production['production_PE_SHA'] ==
              campaign['candidate_binary_sha256'] == a.pe_sha != OLD_PE,
              'new one final production PE differs from known old fault PE')
    a.require(candidate['DLL_SHA'] == production['DLL_SHA'] == campaign['dll_sha256'] == DLL_SHA,
              'unchanged inherited actual Gurobi DLL identity')
    a.require(candidate['source_bindings'] == contract['source_bindings'] == campaign['source_hashes'],
              'one bound final production source set')
    for name, digest in candidate['source_bindings'].items():
        a.require(a.sha(a.root/name) == digest, 'actual current production source '+name)
    for name, digest in campaign['helpers'].items():
        a.require(a.sha(a.root/name) == digest, 'actual frozen performance helper '+name)
    a.require(campaign['prereg_sha256'] == a.sha(a.out/'protocol.json'), 'current protocol SHA')
    path = a.local(request['production_PE_path'])
    a.production_path = path
    if mode == 'public':
        a.require(not path.exists() and a.dll is None, 'public evidence restoration excludes native binaries')
        restore = a.obj(a.root/'restore_receipt.json')
        a.require(restore['exit_code'] == 0 and restore['public_files_only'] and
                  not restore['original_workspace_reads'] and Path(restore['restored_root']).resolve() == a.root,
                  'actual fresh restored root access boundary')
        header = request['actual_PE_header']
    else:
        a.require(a.sha(path) == a.pe_sha and a.dll is not None and a.sha(a.dll) == DLL_SHA,
                  'actual current PE/DLL bytes independently rehashed')
        header = pe_header(a, path)
        a.require(header == request['actual_PE_header'], 'reported header equals actual PE bytes')
    return candidate, campaign, header


def panel(a, campaign, admission):
    protocol = a.obj(a.out/'protocol.json')
    manifest = a.obj(a.out/'input_manifest.json')
    old = a.obj(a.root/'results/unified_exact_round109/input_manifest.json')
    a.require(manifest['roles'] == old['roles'], 'original frozen twelve roles and exact draw identity inherited')
    a.require(protocol['formal_arms'] == 42 and protocol['nominal_seconds'] == 88200 and
              protocol['main_nominal_seconds'] == 75600 and protocol['seed_nominal_seconds'] == 12600,
              '42 current arms with exact 36+6 nominal denominators')
    a.require(protocol['maximum_starts'] == 96 and protocol['maximum_outer_seconds'] == 110000 and
              protocol['planned_formal_starts'] == 57, 'R110 authorized independent resource ceilings')
    a.require(protocol['serial'] and protocol['full_42_required_for_normal_results'] and
              protocol['no_early_performance_cancellation'], 'all normal positive and negative results complete panel')
    a.require(protocol['closure_tolerance'] == TOL and protocol['zero_objective_tolerance'] == 1e-12 and
              protocol['signed_gap_not_clipped'], 'unchanged original closure and signed numerical gap')
    old_protocol = a.obj(a.root/'results/unified_exact_round109/protocol.json')
    for field in ('support_requires', 'materiality', 'severity', 'no_best_of_two',
                  'no_cross_arm_UB_Start_route_cut_cache', 'relative_gap', 'MIXED_not_WIN'):
        a.require(protocol[field] == old_protocol[field], 'unchanged pre-fixed classification/scientific rule '+field)
    expected = [(row[0], 0, arm) for row in a.decision['PANEL'] for arm in row[9]]
    expected += [(role, 1, arm) for role, cap, methods in a.decision['SEED_CHECKS'] for arm in methods]
    launches = campaign['launches']
    a.require([(l['id'], l['panel']['gurobi_seed'], l['arm']) for l in launches] == expected,
              'exact original 42 native order and fixed Seed roles')
    a.require(sum(l['cap_seconds'] for l in launches) == 88200, 'fixed sum of actual 42 caps')
    roles = {r['id']: r for r in manifest['roles']}
    feasible = []
    for row, role in zip(a.decision['PANEL'], manifest['roles']):
        rid, n, m, geo, rep, stock, qc, physical_T, cap, methods = row
        q = [30]*m if qc == 'H' else [20, 40] if m == 2 else [20, 25, 35, 40]*(m//4)
        wanted = dict(id=rid, V=n, M=m, geometry=geo, replicate=rep, inventory=stock,
                      Q_class=qc, Q_vector=q, T_seconds=physical_T, cap_seconds=cap,
                      method_order=list(methods), pickup_seconds=60, drop_seconds=60,
                      gurobi_seed=0, panel_kind='main', **{'lambda': .15})
        a.require(all(role[k] == value for k, value in wanted.items()), 'independent frozen role '+rid)
        instance = a.functions['input_file'](a.root/role['input_path'])
        a.require(a.sha(a.root/role['input_path']) == role['input_sha256'], 'original input bytes '+rid)
        a.require((instance['V'], instance['M'], instance['Q']) == (n, m, q), 'original actual input header '+rid)
        ph = a.functions['full_physics'](instance, [], role)
        a.require(all(0 <= b <= c and d > 0 for b, c, d in
                      zip(instance['initial'][1:], instance['capacities'][1:], instance['target'][1:])),
                  'physical input and empty fleet legal '+rid)
        feasible.append(dict(id=rid, input_SHA=role['input_sha256'], empty_fleet=ph))
    old_argv = a.obj(a.root/'results/unified_exact_round109/candidate_identity.json')['full_argv']
    path_arguments = {'--out', '--log', '--process-phase-ledger', '--external-gini-artifact-dir',
                      '--primal-heuristic-generation-log', '--progress-log', '--native-evidence-dir', '--gurobi-model-export'}
    hash_metadata = {'--round24-executable-sha256', '--round24-manifest-executable-sha256'}
    for launch, original_command in zip(launches, old_argv):
        role, p = roles[launch['id']], launch['panel']
        am = argv_map(launch['command'])
        old_am = argv_map(original_command)
        a.require(set(am) == set(old_am) and all(am[key] == old_am[key] for key in am if key not in path_arguments | hash_metadata),
                  'all original native options unchanged except current raw output paths')
        for key in hash_metadata & set(am):
            a.require(am[key] == a.pe_sha and old_am[key] == OLD_PE, 'new actual PE identity metadata updated honestly')
        for key in path_arguments & set(am):
            a.require(a.local(am[key]).is_relative_to(a.local(launch['destination'])),
                      'each native evidence output remains inside its own independent arm')
        a.require(a.local(launch['command'][0]) == a.production_path,
                  'every formal argv points to the final frozen production PE')
        wanted = {'--input': role['input_path'], '--lambda': '0.15', '--T': str(role['T_seconds']),
                  '--pickup-time': '60', '--drop-time': '60', '--time-limit': str(launch['cap_seconds']-6),
                  '--process-wall-time-limit': str(launch['cap_seconds']), '--process-shutdown-margin': '30',
                  '--threads': '1', '--mip-threads': '1', '--gurobi-seed': str(p['gurobi_seed']),
                  '--gurobi-presolve': '-1'}
        a.require(all(am.get(k) == v for k, v in wanted.items()), 'unchanged actual per-arm numerical parameters')
        a.require('--round100-continuous-quantities' not in am, 'ENS-Q remains false')
        if launch['arm'] == 'P-GRB':
            a.require(am['--method'] == 'gurobi' and am.get('--plain-baseline') is True and
                      '--algorithm-preset' not in am and '--round98-state-service' not in am, 'cold original P entrance')
        else:
            a.require(am['--method'] == 'gcap-frontier' and
                      am['--algorithm-preset'] == 'research-round83-vds-equal-net-exchange' and
                      am.get('--round98-state-service') == ('m-binary' if launch['arm'] == 'M-B' else None),
                      'frozen ENS and only M-B original extra option')
        if admission:
            a.require(not a.local(launch['destination']).exists(), 'no formal measurement before independent admission')
    return launches, feasible


def fees(a):
    result = []
    for path in sorted((a.out/'fees').glob('*/launch.json')):
        launch, receipt = a.obj(path), a.obj(path.parent/'receipt.json')
        a.require(launch['conservative_process_starts'] == receipt['conservative_process_starts'],
                  'closed charge equals full planned wrapper/process tree')
        a.require(not receipt.get('nested_seconds_added', False) and not receipt.get('earlier_fee_refunded', False),
                  'no nested native seconds addition and no declared-start refund')
        a.require(receipt['outer_seconds'] >= 0 and math.isfinite(receipt['outer_seconds']), 'finite actual closed outer charge')
        result.append(dict(label=path.parent.name, outer_seconds=receipt['outer_seconds'],
                           conservative_process_starts=receipt['conservative_process_starts'],
                           qualification=launch.get('qualification', False), exit_code=receipt['exit_code'],
                           launch_SHA=a.sha(path), receipt_SHA=a.sha(path.parent/'receipt.json')))
    return result


def inherited_references(a, campaign):
    path = a.root/'results/unified_exact_round109/review/performance_admission.json'
    a.require(a.sha(path) == '93f4adf6d1ead1d18430e411828d723dcc39fe9ddfc7efd83756c907e6e92c56',
              'exact signed inherited reference admission')
    old = a.obj(path)
    a.require(old['decision'] == 'ACCEPT' and old['production_PE_SHA'] == OLD_PE,
              'old original reference qualification authority only')
    result = []
    for ref in old['references']:
        rid = ref['id']
        directory = a.out/'qualification/reference'/rid
        build = a.obj(directory/'build.json')
        digest = a.sha(directory/'original.lp')
        a.require(digest == ref['SHA'] == build['canonical_sha256'] ==
                  campaign['references'][rid]['canonical_sha256'], 'exact original native reference bytes '+rid)
        a.require(build == campaign['references'][rid] and build['optimizer_calls'] == 0 and
                  all(build[k] == ref[k] for k in ('fingerprint', 'rows', 'columns')),
                  'inherited original no-solve native reference metadata '+rid)
        result.append(dict(id=rid, SHA=digest, inherited_native_domain=ref['domain'],
                           fingerprint=build['fingerprint'], rows=build['rows'], columns=build['columns']))
    a.require([r['id'] for r in result] == [r[0] for r in a.decision['PANEL']],
              'all twelve original reference roles bound')
    return result


def actual_qualifications(a, request):
    plan = artifact(a, request, 'qualification_plan')
    a.require(plan.get('conservative_starts', plan.get('conservative_process_starts')) <= 20 and
              plan.get('outer_cap_seconds', plan.get('maximum_outer_seconds')) <= 2000,
              'qualification frozen within its separate cap')
    parser = artifact(a, request, 'parser_equivalence')
    a.require(parser['passed'] and parser['integer_fields_exact'] and
              parser.get('binary64_fields_bitwise_equal', parser.get('binary64_bitwise_equal')) and parser['Optimize'] == 0,
              'actual C++ binary64 mathematical equality and no optimizer')
    old_dump = a.local(parser.get('old_mathematical_dump', parser.get('old_dump')))
    new_dump = a.local(parser.get('new_mathematical_dump', parser.get('new_dump')))
    a.require(a.data(old_dump) == a.data(new_dump),
              'actual old/new native mathematical dumps equal byte for byte')
    dump_lines = a.txt(old_dump).splitlines()
    dump_roles = [r.split('\t')[1] for r in dump_lines if r.startswith('instance\t')]
    a.require(dump_roles == [row[0]+'.txt' for row in a.decision['PANEL']], 'all twelve actual parser dump inputs')
    cases = [r for r in dump_lines if r.startswith('case\t')]
    a.require(len(cases) == parser.get('finite_extraction_cases', len(cases)) == 16 and
              [int(r.split('\t')[1]) for r in cases] == list(range(16)) and
              parser.get('metadata_paths_separate', parser.get('metadata_separate')),
              'changed payload boundaries and isolated path metadata checked')
    build_plan = a.obj(a.out/'qualification/parser_build_plan.json')
    a.require(build_plan['Optimize'] == 0 and len(build_plan['wrappers']) == 2,
              'old/new independent C++ parser build plan')
    a.require([w['variant'] for w in build_plan['wrappers']] == ['old', 'new'], 'original then fixed parser')
    source_old = a.out/'engineering/initialization01/old_Parser.cpp'
    old_parser_SHA = a.obj(a.root/'results/unified_exact_round109/candidate_identity.json')['source_bindings']['src/Parser.cpp']
    a.require(a.sha(source_old) == old_parser_SHA and
              build_plan['wrappers'][0]['Parser_source_SHA'] == old_parser_SHA and
              build_plan['wrappers'][1]['Parser_source_SHA'] == a.sha(a.root/'src/Parser.cpp'),
              'native dumps compiled against exact original and current Parser bytes')
    commands = [w['compiler_command'] for w in build_plan['wrappers']]
    a.require(commands[0][:-3] == commands[1][:-3] and not any('-O' in word or 'fast-math' in word for word in commands[0]),
              'same inherited compiler flags in both bitwise authorities')
    a.require([int(r.split('\t')[2]) for r in dump_lines if r.startswith('instance\t')] ==
              [row[1] for row in a.decision['PANEL']], 'native dump dimensions match fixed inputs')
    for completed in parser['completed']:
        d = a.local(completed['destination'])
        launch, exit_receipt = a.obj(d/'launch.json'), a.obj(d/'raw_exit_receipt.json')
        a.require(a.sha(d/'raw_exit_receipt.json') == completed['raw_exit_receipt_SHA'] and
                  launch['PE_SHA'] == exit_receipt['PE_SHA'] == completed['PE_SHA'] and exit_receipt['exit_code'] == 0,
                  'both actual parser batch native children returned normally')
        a.require(exit_receipt['stdout_SHA'] == a.sha(d/'stdout.log') and
                  exit_receipt['stderr_SHA'] == a.sha(d/'stderr.log') and
                  'batch_complete\t12\tOptimize=0' in a.txt(d/'stderr.log'),
                  'actual parser batch stdout/stderr and full no-solve completion')
    entry = artifact(a, request, 'main_entry')
    a.require(entry['passed'] and entry['Optimize'] == 0 and not entry.get('heuristic', False) and
              not entry.get('oracle', False),
              'actual final-main zero-solve qualification')
    entry_plan = a.obj(a.out/'qualification/main_entry_plan.json')
    a.require(entry['plan_SHA'] == a.sha(a.out/'qualification/main_entry_plan.json'), 'actual entry receipt bound frozen plan')
    covered = []
    for group in entry_plan['entries']:
        d = a.local(group['destination'])
        actual, exit_receipt = a.obj(d/'launch.json'), a.obj(d/'raw_exit_receipt.json')
        a.require(actual['command'] == group['command'] and actual['PE_SHA'] == exit_receipt['PE_SHA'] == a.pe_sha and
                  exit_receipt['exit_code'] == 0, 'same final actual main command/PE and normal return')
        a.require(exit_receipt['stdout_SHA'] == a.sha(d/'stdout.log') and
                  exit_receipt['stderr_SHA'] == a.sha(d/'stderr.log'), 'actual main-entry stdout/stderr bindings')
        am = argv_map(group['command'])
        a.require(am['--method'] == 'option-consistency-test' and
                  am['--frontier-execution-mode'] == 'external-gini-tree' and
                  am['--auto-interval-oracle'] == 'false' and am['--primal-heuristic'] == 'none',
                  'recorded diagnostic argv excludes all solve paths')
        a.require(a.local(group['command'][0]) == a.production_path and
                  am['--T'] == str(group['T']) and am['--pickup-time'] == am['--drop-time'] == '60' and
                  am['--lambda'] == '0.15', 'same final PE and original physical diagnostic arguments')
        phase_rows = a.rows(d/'phases.csv')
        names = [r['detail'].removeprefix('instance=') for r in phase_rows if r['event'] == 'instance_parsing_complete']
        a.require(sorted(names) == group['expected_names'], 'each actual parser completion phase in main')
        a.require(phase_rows[-1]['event'] == 'process_exit' and phase_rows[-1]['detail'] == 'rc=0', 'actual normal process exit phase')
        for mapping in [m for m in entry_plan['path_mapping'] if m['T'] == group['T']]:
            a.require(a.sha(a.local(mapping['mapped'])) == a.sha(a.local(mapping['source'])) == mapping['SHA'],
                      'entry directory copy has exact original filename/bytes')
            a.require(Path(mapping['mapped']).name == Path(mapping['source']).name,
                      'entry input original filename retained')
        results = a.obj(d/'result.json')
        a.require(sorted(r['instance_name'] for r in results) == group['expected_names'], 'every actual diagnostic result serialized')
        role_by_name = {r['id']+'.txt': r for r in a.obj(a.out/'input_manifest.json')['roles']}
        for raw in results:
            a.require(raw['method'] == 'option-consistency-test' and raw['status'] == 'diagnostic_complete' and
                      raw['option_audit_consistent'] and raw['algorithm_preset'] == 'custom' and
                      raw['primal_heuristic'] == 'none' and raw['native_mip_mipopt_count'] == raw['gurobi_optimize_count'] == 0 and
                      not raw['auto_interval_oracle_called'], 'actual option diagnostic completed with zero native calls')
            a.require(raw['route_time_limit_seconds'] == group['T'] and
                      raw['pickup_time_seconds'] == raw['drop_time_seconds'] == 60,
                      'actual diagnostic physical timing parameters')
            a.require('automatic interval oracle bypassed by construction for native or external global-Gini-tree mode' in raw['notes'],
                      'actual postprocess branch explicitly bypassed oracle')
            role = role_by_name[raw['instance_name']]
            q = a.functions['input_file'](a.root/role['input_path'])
            ph = a.functions['full_physics'](q, raw['routes'], role)
            a.require(ph['final_inventories'] == raw['final_inventories'] and a.near(ph['U'], raw['objective']) and
                      all(not r['operations'] for r in ph['full_routes']) and
                      all(r['return_load'] == 0 for r in ph['routes']),
                      'actual empty diagnostic fleet original physical domain and objective')
        covered += names
    a.require(sorted(covered) == sorted(row[0]+'.txt' for row in a.decision['PANEL']) and len(covered) == 12,
              'all twelve actual final-main parser entries covered once')
    qi = a.obj(a.out/'qualification/cli01/identity.json')
    a.require([(l['arm'], l['panel']['gurobi_seed']) for l in qi['launches']] ==
              [('P-GRB', 0), ('ENS-C', 0), ('M-B', 0), ('P-GRB', 1), ('M-B', 1)],
              'five fixed actual functional algorithm/Seed paths')
    arms = []
    for launch in qi['launches']:
        a.require(launch['id'] == 'H100' and launch['cap_seconds'] <= 120, 'fixed known fixture and bounded CLI')
        a.require(a.local(launch['command'][0]) == a.production_path,
                  'every functional qualification uses the final production PE')
        arm, models, q = a.arm(launch, qi, False)
        arms.append(arm)
    a.require(any(c['solve_kind'] == 'LP' for arm in arms for c in arm['native_records']) and
              any(c['solve_kind'] == 'MIP' for arm in arms for c in arm['native_records']) and
              any(arm['starts'] for arm in arms), 'actual LP/MIP and applicable all-column Start path touched')
    return dict(parser=parser, main_entry=entry, functional_arms=arms, plan=plan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--mode', choices=('admission', 'final', 'public'), required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--request', default='results/unified_exact_round110/review/admission_request.json')
    ap.add_argument('--dll')
    args = ap.parse_args()
    root, destination = Path(args.root).resolve(), Path(args.out).resolve()
    assert destination.is_relative_to(root/ROUND/'review')
    destination.mkdir(parents=True, exist_ok=False)
    tick = time.perf_counter()
    error, value, a = None, {}, None
    source = Path(__file__).read_bytes()
    with (destination/'launch.json').open('x', encoding='utf-8') as f:
        json.dump(dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()), explicit_read_root=str(root),
                       source_SHA=hashlib.sha256(source).hexdigest(), mode=args.mode,
                       Optimize=0, native_environment=0), f, indent=2)
    (destination/'source_at_execution.py').write_bytes(source)
    core_source = Path(__file__).with_name('round110_independent_core.py').read_bytes()
    (destination/'core_at_execution.py').write_bytes(core_source)
    cold_source = Path(__file__).with_name('round110_independent_cold_rejection.py').read_bytes()
    (destination/'cold_rejection_at_execution.py').write_bytes(cold_source)
    scoped_source = Path(__file__).with_name('round110_independent_scoped_rejection.py').read_bytes()
    (destination/'scoped_rejection_at_execution.py').write_bytes(scoped_source)
    original_stdout, original_stderr = sys.stdout, sys.stderr
    stdout_stream = (destination/'stdout.log').open('x', encoding='utf-8', newline='\n')
    stderr_stream = (destination/'stderr.log').open('x', encoding='utf-8', newline='\n')
    sys.stdout, sys.stderr = Tee(original_stdout, stdout_stream), Tee(original_stderr, stderr_stream)
    try:
        request_path = root/args.request
        request = json.loads(request_path.read_text(encoding='utf-8-sig'))
        candidate = json.loads((root/ROUND/'candidate_identity.json').read_text(encoding='utf-8-sig'))
        a = Audit(root, destination, candidate['production_PE_SHA'], dll=args.dll)
        a.require(args.mode != 'public' or args.dll is None, 'public mode no external DLL read')
        request = a.obj(request_path)
        candidate, campaign, header = identity(a, request, args.mode)
        launches, feasibility = panel(a, campaign, args.mode == 'admission')
        references = inherited_references(a, campaign)
        qualification = actual_qualifications(a, request)
        # Finite subjects are externally executed but independently hash-bound;
        # their named rejection cases and actual historical inputs are reviewed
        # before signing. They are never applied as stale new-call sidecars.
        finite = artifact(a, request, 'finite_regressions')
        a.require(finite['passed'] and finite['Optimize'] == 0 and finite['native_environment'] == 0 and
                  all(finite['subjects'][name] for name in
                      ('actual_Seed1', 'actual_P15', 'actual_P17', 'missing_return', 'nonnegative_floor',
                       'unknown_clock', 'interval_thresholds', 'mechanism_correction01')),
                  'bounded actual inherited counterexamples and clock/type regressions pass')
        policy = artifact(a, request, 'evidence_policy')
        a.require(policy['uniform_all_methods'] and policy['raw_flags_preserved'] and
                  policy['new_calls_bind_own_models'] and policy['reject_all_damaged_call_lower_claims'] and
                  policy['withdraw_necessary_dependent_closures'] and policy['unknown_new_fault_pauses'] and
                  policy['floor_requires_own_objective_proof'] and policy['missing_exact_clock_is_null'],
                  'pre-frozen uniform evidence predicates and new fault boundary')
        repair = artifact(a, request, 'repair_evidence')
        old_bindings = a.obj(root/'results/unified_exact_round109/candidate_identity.json')['source_bindings']
        a.require(set(candidate['source_bindings']) == set(old_bindings), 'same complete production file inventory')
        changed = [name for name, digest in candidate['source_bindings'].items() if old_bindings[name] != digest]
        declared = repair.get('changed_production_files', list(repair.get('changes', {})))
        a.require(sorted(changed) == sorted(declared) == ['src/Parser.cpp'], 'every actual production delta is only located payload risk')
        old_source = a.txt(a.out/'engineering/initialization01/old_Parser.cpp')
        new_source = a.txt(a.root/'src/Parser.cpp')
        old_function = '''std::string namedBracketPayload(const std::string& text, const std::string& name) {
    const std::string pat = name + R"(\\s*=\\s*\\[([\\s\\S]*?)\\])";
    const std::regex re(pat);
    std::smatch m;
    if (!std::regex_search(text, m, re)) return {};
    return m[1].str();
}'''
        fixed_function = '''std::string namedBracketPayload(const std::string& text, const std::string& name) {
    const std::string pat = name + R"(\\s*=\\s*\\[)";
    const std::regex re(pat);
    std::smatch m;
    if (!std::regex_search(text, m, re)) return {};
    const auto begin = static_cast<std::size_t>(m.position() + m.length());
    const auto end = text.find(']', begin);
    if (end == std::string::npos) return {};
    return text.substr(begin, end - begin);
}'''
        old_lines = '\n'.join(old_source.splitlines())
        a.require(old_lines.count(old_function) == 1 and
                  old_lines.replace(old_function, fixed_function).splitlines() == new_source.splitlines(),
                  'only original prefix preserved plus first-closing-bracket iterative payload replacement')
        a.require(repair['build_flag_set'] == repair['inherited_build_flag_set'] and
                  repair['build_type'] == repair['CXX_flags'] == repair['link_flags'] == '',
                  'actual inherited unoptimized default compiler and link flags unchanged')
        expected_header = repair['PE_header']
        a.require(expected_header['PE_SHA'] == a.pe_sha and
                  expected_header['stack_reserve_bytes'] == header['stack_reserve'] == 2097152 and
                  expected_header['stack_commit_bytes'] == header['stack_commit'] and
                  int(expected_header['machine'], 16) == header['machine'],
                  'actual native stack/header bound; parser-only repair with original 2MiB reserve')
        for label in ('configure01', 'build01'):
            d = a.out/'engineering'/label
            actual_build_launch = a.obj(d/'launch.json')
            actual_build_exit = a.obj(d/'receipt.json')
            a.require(a.sha(d/'launch.json') == repair[label.removesuffix('01')+'_launch_SHA'] and
                      a.sha(d/'receipt.json') == repair[label.removesuffix('01')+'_receipt_SHA'] and
                      actual_build_exit['exit_code'] == 0, 'actual compile/configure commands completed and bound')
        fee_records = fees(a)
        remaining = [(row[8], row[9]) for row in a.decision['PANEL']]
        remaining += [(cap, methods) for role, cap, methods in a.decision['SEED_CHECKS']]
        budget = a.budget(fee_records, remaining if args.mode == 'admission' else [],
                          overhead=request['remaining_formal_overhead_seconds'] if args.mode == 'admission' else 0)
        value = dict(decision='ACCEPT', mode=args.mode, production_PE_SHA=a.pe_sha, DLL_SHA=a.dll_sha,
                     candidate_identity_SHA=a.sha(a.out/'candidate_identity.json'),
                     campaign_identity_SHA=a.sha(a.out/'campaign/identity.json'),
                     qualification_identity_SHA=a.sha(a.out/'qualification/identity.json'),
                     protocol_SHA=a.sha(a.out/'protocol.json'), actual_PE_header=header,
                     input_eligibility={r['id']: True for r in feasibility}, data_feasibility=feasibility,
                     references=references, qualification=qualification, budget=budget, fee_records=fee_records,
                     all42_complete_argv=[l['command'] for l in launches], request_SHA=a.sha(request_path),
                     module_bindings=a.module_bindings, production_edits=0, Optimize=0, native_environment=0)
        if args.mode != 'admission':
            admission = a.obj(a.out/'review/performance_admission.json')
            a.require(admission['decision'] == 'ACCEPT' and
                      admission['candidate_identity_SHA'] == value['candidate_identity_SHA'], 'actual signed admission bound current identity')
            arms = []
            for launch in launches:
                arm, models, q = a.arm(launch, campaign, True)
                arms.append(arm)
            for group in {(arm['id'], arm['seed']) for arm in arms}:
                same_problem = [arm for arm in arms if (arm['id'], arm['seed']) == group]
                a.require(max(arm['L'] for arm in same_problem) <= min(arm['U'] for arm in same_problem)+1e-7,
                          'all independently qualified same-input/Seed bounds are consistent after current call withdrawals')
            value['own_actual_arms'] = arms
            value['selection'] = a.decision['selection'](arms, value['input_eligibility'])
            a.require(value['selection']['stage'] != 'BLOCKED', 'complete exact same-PE valid42 raw reconstructed')
            value['decision'] = 'ACCEPT_INDEPENDENT_COMPLETE_PANEL'
        else:
            value['formal_arms_already_started'] = 0
    except Exception:
        error = traceback.format_exc()
        value.update(decision='HOLD', error=error, mode=args.mode, Optimize=0, native_environment=0)
    value.update(completed_checks=a.checks if a else 0, read_bindings=a.reads if a else {},
                 explicit_read_root=str(root), no_original_root_fallback=True,
                 reviewer_source_bindings={Path(__file__).name: hashlib.sha256(source).hexdigest(),
                                            'round110_independent_core.py': hashlib.sha256(core_source).hexdigest(),
                                            'round110_independent_cold_rejection.py': hashlib.sha256(cold_source).hexdigest(),
                                            'round110_independent_scoped_rejection.py': hashlib.sha256(scoped_source).hexdigest()})
    with (destination/'audit.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(decision=value['decision'], completed_checks=value['completed_checks'], error=error)))
    sys.stdout.flush()
    sys.stderr.flush()
    sys.stdout, sys.stderr = original_stdout, original_stderr
    stdout_stream.close()
    stderr_stream.close()
    receipt = dict(exit_code=int(error is not None), decision=value['decision'], cwd=str(Path.cwd()),
                   explicit_read_root=str(root), engineering_elapsed_seconds=time.perf_counter()-tick,
                   source_SHA=hashlib.sha256(source).hexdigest(),
                   core_SHA=hashlib.sha256(core_source).hexdigest(),
                   audit_SHA=hashlib.sha256((destination/'audit.json').read_bytes()).hexdigest(),
                   stdout_SHA=hashlib.sha256((destination/'stdout.log').read_bytes()).hexdigest(),
                   stderr_SHA=hashlib.sha256((destination/'stderr.log').read_bytes()).hexdigest(),
                   Optimize=0, native_environment=0)
    with (destination/'receipt.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump(receipt, f, indent=2)
        f.write('\n')
    if error:
        sys.exit(1)


if __name__ == '__main__':
    main()
