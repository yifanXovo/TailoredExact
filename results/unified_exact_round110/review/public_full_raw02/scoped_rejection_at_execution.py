"""Independently audit a current scoped M-B call and its exact counterexample.

This verifier has no historical tuple authority and launches no native work.
An original physical zero/floor certificate is distinct from the withdrawn
native call/closure evidence. Every saved model and actual LP/MIP is checked.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import argparse, hashlib, json, math, re, sys, time, traceback
from round110_independent_core import Audit, ROUND, SETTINGS, TOL

def audit(a, launch, identity, proposed):
    key = [launch['number'], launch['id'], launch['seed'], launch['arm']]
    a.require(proposed['schema'] == 'round110-current-scoped-call-rejection-v1' and proposed['key'] == key and
              launch['arm'] == 'M-B' and proposed['damaged_calls'] == [4], 'current separately proved scoped M-B terminal-call class')
    a.require(proposed['production_PE_SHA'] == identity['candidate_binary_sha256'] == a.pe_sha and
              proposed['DLL_SHA'] == identity['dll_sha256'] == a.dll_sha and
              proposed['campaign_identity_SHA'] == a.sha(a.out/'campaign/identity.json'), 'actual current identities')
    for path, digest in proposed['raw_bindings'].items():
        a.require(a.sha(a.local(path)) == digest, 'actual current immutable raw '+path)
    d, p = a.local(launch['destination']), launch['panel']
    actual, raw, comp, old_audit = [a.obj(d/name) for name in ('launch.json', 'result.json', 'completion.json', 'audit.json')]
    a.require(actual['command'] == launch['command'] == proposed['command'] and actual['panel'] == p and
              actual['prereg_sha256'] == identity['prereg_sha256'], 'one frozen current original M-B argv/scenario')
    a.require(comp['returncode'] == 0 and comp['stop_reason'] == 'normal_return' and comp['within_cap'] and
              old_audit['passed'] is False and old_audit['error'] == "AssertionError('local_bound_witness_inconsistency')",
              'actual normal process; original local numerical audit failure retained')
    q = a.functions['input_file'](a.root/p['input_path'])
    a.require(a.sha(a.root/p['input_path']) == p['input_sha256'] == proposed['input_SHA'] and
              (q['V'], q['M'], q['Q']) == (p['V'], p['M'], p['Q_vector']), 'own current original physical input')
    a.require(raw['algorithm_preset'] == 'research-round99-ensc-discrete-structure-m-binary', 'actual frozen effective M-B preset')
    own = a.functions['full_physics'](q, raw['routes'], p)
    a.require(own['G'] == own['P'] == own['U'] == raw['objective'] == raw['upper_bound'] == 0 and
              own['final_inventories'] == raw['final_inventories'], 'own complete exact zero physical fleet')
    a.require(math.isfinite(p['lambda']) and p['lambda'] >= 0 and
              all(math.isfinite(w) and w >= 0 for w in q['weights'][1:]) and all(t > 0 for t in q['target'][1:]),
              'own original full-domain true G and absolute weighted penalty imply F>=0 including zero denominator convention')
    observations = a.obj(d/'observations.json')
    calls, returned, witnesses, bounds, failures = {}, {}, [], [], []
    for seq, observed in enumerate(observations, 1):
        e = observed['payload']
        blob = a.data(d/'journal'/f'event_{seq}.json')
        commit = a.txt(d/'journal'/f'event_{seq}.commit').split()
        a.require(e['sequence'] == observed['sequence'] == seq and json.loads(blob) == e and
                  hashlib.sha256(blob).hexdigest() == observed['sha256'] == commit[4] and commit[0] == 'NEJ1' and
                  int(commit[1]) == seq and int(commit[3]) == len(blob), 'every current committed journal byte/sequence/hash')
        a.require(a.near(float(commit[2]), observed['data_close_seconds'], 1e-9) and
                  a.near(observed['effective_available_seconds'], max(observed['data_close_seconds'], observed['first_observed_seconds']), 1e-9),
                  'actual committed observation availability')
        kind = e['kind']
        if kind == 'identity':
            a.require(seq == 1 and e['input_sha256'] == p['input_sha256'] and
                      (e['V'], e['M'], e['T'], e['lambda'], e['pickup_seconds'], e['drop_seconds']) ==
                      (p['V'], p['M'], p['T_seconds'], p['lambda'], 60, 60), 'current native identity')
        elif kind == 'call':
            a.require(e['call'] not in calls and e['full_original'] == 0 and
                      e['settings'] == dict(read_return_code=0, **SETTINGS, Seed=launch['seed']) and
                      e['model_scope'] == 'complete_original_compact_milp_intersected_with_static_gini_interval', 'actual distinct scoped native settings')
            calls[e['call']] = e
        elif kind == 'returned':
            a.require(e['call'] in calls and e['call'] not in returned and e['return_code'] == 0, 'actual journal returns preserved')
            returned[e['call']] = seq
        elif kind == 'witness':
            ph = a.functions['full_physics'](q, e['routes'], p)
            a.require(a.near(ph['U'], e['objective']) and a.near(ph['G'], e['G']) and a.near(ph['P'], e['P']) and
                      (e['call'] == 0 or e['call'] in calls and e['call'] not in returned), 'every own original physical journal witness')
            ph.update(sequence=seq, source=e['source'], raw_available=observed['effective_available_seconds'], call=e['call'])
            witnesses.append(ph)
        elif kind == 'bound':
            a.require(e['call'] == 4 and not e['inconsistent'] and math.isfinite(e['native_bound']), 'all actual current damaged-call raw lower claims')
            bounds.append(e)
        elif kind == 'failure':
            a.require(e['reason'] == 'local_bound_witness_inconsistency' and seq == len(observations), 'only actual final local numerical latch')
            failures.append(e)
        else:
            raise AssertionError('unknown scoped fault journal event '+kind)
    a.require(list(calls) == [1, 2, 3, 4] and set(returned) == {1, 2, 3} and len(failures) == 1 and
              calls[4]['native_preconditions'] == 1 and all(calls[i]['native_preconditions'] == 0 for i in (1, 2, 3)),
              'three actual LP returns and missing terminal-MIP journal return remain distinct')
    a.require(any(w['call'] == 4 and w['U'] == w['G'] == w['P'] == 0 for w in witnesses), 'own committed terminal-MIPSOL exact zero witness')
    root_SHA = calls[4]['model_sha256']
    a.require(root_SHA == proposed['model_SHA'] == calls[1]['model_sha256'] and
              calls[4]['lower_g'] == 0 and calls[4]['upper_g'] == calls[4]['cutoff'] and
              own['G'] >= calls[4]['lower_g'] and own['G'] <= calls[4]['upper_g'] and own['U'] <= calls[4]['cutoff'],
              'actual damaged root scope includes own exact-zero witness, with its own cutoff')
    contracts, root_model = [], None
    for path in sorted((d/'external/models').glob('*.lp')):
        digest = a.sha(path)
        m = a.model(path)
        contract = a.functions['domain_contract'](m, q, 'M-B')
        a.require(set(m['objective']) == {'G', *[f'e_{i}' for i in range(1, q['V']+1)]} and m['objective']['G'] == 1 and
                  all(a.near(m['objective'][f'e_{i}'], p['lambda']*q['weights'][i], 1e-12) for i in range(1, q['V']+1)),
                  'each saved scope preserves original own F objective')
        matched = [c for c in calls.values() if c['model_sha256'] == digest]
        a.require(matched, 'every saved model belongs to actual calls')
        for c in matched:
            a.require(a.local(c['model_path']) == path, 'call saved model exact path')
            a.functions['scope_contract'](c, m, q)
        contracts.append(dict(path=path.relative_to(a.root).as_posix(), SHA=digest, **contract))
        if digest == root_SHA:
            root_model = m
        a.cache.clear()
    a.require(len(contracts) == 3 and root_model is not None, 'all three current canonical scoped M-B models independently checked')
    by_SHA = {c['SHA']: c for c in contracts}
    ledger, lpstatus = a.rows(d/'external/paper_optimize_ledger.csv'), a.rows(d/'external/lp_status_ledger.csv')
    a.require(len(ledger) == 4 and len(lpstatus) == 3 and [r['solve_kind'] for r in ledger] == ['LP', 'LP', 'LP', 'MIP'], 'actual3LP+1terminalMIP mechanism')
    native_records = []
    for number, row in enumerate(ledger, 1):
        c, contract = calls[number], by_SHA[calls[number]['model_sha256']]
        log_path = a.local(c['native_log_path'])
        native = a.txt(log_path)
        a.require(int(row['optimize_return_code']) == 0 and row['native_status'] == 'OPTIMAL' and row['model_sha256'] == c['model_sha256'] and
                  row['leaf_id'] == c['leaf'] and a.local(row['native_log']) == log_path, 'actual captured API/model/leaf/log match per-call')
        size = re.search(r'Optimize a model with (\d+) rows, (\d+) columns', native)
        a.require(size and (int(size[1]), int(size[2])) == (contract['rows'], contract['columns']), 'native pre-presolve model size matches exact saved scope')
        types, lower = None, None
        if number <= 3:
            s = lpstatus[number-1]
            printed = re.findall(r'Optimal objective\s+([-+0-9.eE]+)', native)
            a.require(s['leaf_id'] == c['leaf'] and float(s['gamma_L']) == c['lower_g'] and float(s['gamma_U']) == c['upper_g'] and
                      all(int(s[k]) == 1 for k in ('terminal_valid', 'optimal', 'bound_available')) and
                      printed and a.near(float(printed[-1]), float(s['lower_bound'])), 'distinct successful original LP scope and final log bound')
            lower = float(s['lower_bound'])
        else:
            match = re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)', native)
            a.require(bool(match), 'actual restored native MIP type header present')
            types = dict(C=int(match[1]), I=int(match[2])-int(match[3]), B=int(match[3]))
            a.require(types == {k: contract['native_types'].get(k, 0) for k in ('C', 'I', 'B')}, 'restored actual native M-B types exactly saved continuous-p/d plus frozen A/B domain')
            final = re.findall(r'Best objective ([^,]+), best bound ([^,]+), gap ([^\n]+)', native)
            a.require(final and float(final[-1][0]) == float(final[-1][1]) == 0 and
                      'Optimal solution found (tolerance 0.00e+00)' in native, 'actual terminal native OPTIMAL/final-zero log only corroborates functional return')
            lower = float(final[-1][1])
        native_records.append(dict(call=number, leaf=c['leaf'], model_SHA=c['model_sha256'], model_path=c['model_path'],
                                   native_log_path=c['native_log_path'], native_log_SHA=a.sha(log_path), solve_kind=row['solve_kind'],
                                   native_status=row['native_status'], returned_native_log_L=lower, return_sequence=returned.get(number),
                                   returned_journal_missing=number == 4, independently_captured_actual_return_code=0,
                                   native_types=types, native_bounds_mathematically_qualified=number != 4))
    a.require(raw['external_gini_tree_optimize_count'] == 4 and raw['external_gini_tree_lp_optimize_count'] == 3 and
              raw['external_gini_tree_terminal_mip_optimize_count'] == 1 and raw['external_gini_tree_model_count'] == raw['external_gini_tree_model_free_count'] == 3 and
              raw['external_gini_tree_environment_count'] == raw['external_gini_tree_environment_free_count'] == 1 and
              raw['external_gini_tree_backend_parameter_roundtrip_valid'] and raw['external_gini_tree_lifecycle_complete'], 'actual four API calls, parameter readbacks and complete model/environment cleanup')
    backend, journal_source = a.txt(a.root/'src/GurobiBaseline.cpp'), a.txt(a.root/'src/NativeEvidenceJournal.cpp')
    a.require('out.optimize_return_code = api_.optimize(model);' in backend and
              'callback.native_evidence->returned(callback.evidence_call,out.optimize_return_code)' in backend and
              'api_.freemodel(item.second.model);' in backend and 'api_.freeenv(env_);' in backend and
              'failed_=true;' in journal_source and 'if(failed_) return;' in journal_source, 'known latch omits journal return while actual API result and cleanup are captured independently')
    phases = a.rows(d/'phases.csv')
    events = [r['event'] for r in phases]
    a.require(events.count('final_result_serialization_start') == events.count('final_result_serialization_complete') == events.count('process_exit') == 1 and
              events.index('final_result_serialization_start') < events.index('final_result_serialization_complete') < events.index('process_exit') and
              phases[-1]['detail'] == 'rc=0', 'actual serialization and normal process closure')
    a.functions['start_check'].calls = list(calls.values())
    sp = a.local(calls[4]['native_log_path']+'.round68.start.json')
    a.require(set((d/'external/native_logs').glob('*.round68.start.json')) == {sp}, 'one own current terminal native Start attempt')
    attempt, submitted = a.functions['audit_start_attempt'](d, sp, native_records[3], {root_SHA: root_model}, q, p)
    a.require(submitted is not None, 'actual complete own same-arm all-column Start submitted and checked')
    vector_path = a.local(proposed['exact_vector_path'])
    a.require(a.sha(vector_path) == proposed['exact_vector_SHA'], 'current exact scoped vector identity')
    vector = a.obj(vector_path)
    values = {n: Fraction(*v) for n, v in vector['complete_column_values'].items()}
    a.require(set(values) == set(root_model['bounds']), 'complete current scoped vector every column')
    for n, (lo, hi) in root_model['bounds'].items():
        a.require((not math.isfinite(lo) or values[n] >= Fraction(lo)) and (not math.isfinite(hi) or values[n] <= Fraction(hi)) and
                  (root_model['types'][n] == 'C' or values[n].denominator == 1), 'exact current scoped vector bound/type '+n)
    coefficient_cache = {}
    def exact_coefficient(v):
        if v not in coefficient_cache:
            coefficient_cache[v] = Fraction(v)
        return coefficient_cache[v]
    for index, (sense, rhs, terms) in enumerate(root_model['rows']):
        lhs = sum((values[n]*exact_coefficient(coefficient) for n, coefficient in terms if values[n]), Fraction(0))
        target = exact_coefficient(rhs)
        a.require(lhs == target if sense == '=' else lhs <= target if sense == '<' else lhs >= target,
                  'strict Fraction current scoped matrix row '+str(index))
    exact = sum((values[n]*exact_coefficient(coefficient) for n, coefficient in root_model['objective'].items()), Fraction(0))
    a.require(values['G'] >= Fraction(calls[4]['lower_g']) and values['G'] <= Fraction(calls[4]['upper_g']) and
              exact <= Fraction(calls[4]['cutoff']) and any(Fraction(e['native_bound']) > exact+Fraction(TOL) for e in bounds),
              'exact same scoped typed model/cutoff vector disproves actual terminal-call numerical lower claim')
    a.require(proposed['reject_all_call_native_lower_claims'] and proposed['withdraw_necessary_dependent_closures'] and
              proposed['preserved_distinct_LP_calls'] == [1, 2, 3] and proposed['qualified_L'] == proposed['own_U'] == 0 and
              proposed['certificate_from_own_exact_zero'] and proposed['qualified_L_source'] == 'independently_proved_own_original_full_domain_nonnegative_floor',
              'only current damaged terminal call lower claims/derived closures withdrawn; separate own-zero/floor certificate')
    timing = proposed['time']
    a.require(timing['exact_seconds'] is None and not (d/'whole_arm_receipt.json').exists(), 'original missing exact whole-arm time remains null')
    native_end = a.obj(d/'native_end_receipt.json')
    fee_path = a.local(proposed['original_fee_path'])
    fee_launch, fee = a.obj(fee_path/'launch.json'), a.obj(fee_path/'receipt.json')
    first, last = map(int, fee_launch['command'][4:6])
    a.require(first <= launch['number'] <= last and fee_launch['qualification'] is False and fee['exit_code'] == 1 and
              fee_launch['production_PE_SHA'] == a.pe_sha and fee_launch['DLL_SHA'] == a.dll_sha and
              fee['conservative_process_starts'] == fee_launch['conservative_process_starts'], 'original failed billed wrapper and PE/DLL provenance remain retained')
    prior = []
    for number in range(first, launch['number']):
        path = a.local(identity['launches'][number-1]['destination'])/'whole_arm_receipt.json'
        receipt = a.obj(path)
        a.require(receipt['number'] == number and path.relative_to(a.root).as_posix() in proposed['raw_bindings'], 'only disjoint preceding original whole receipts subtracted')
        prior.append(receipt['complete_seconds'])
    interval = [math.nextafter(native_end['complete_seconds_until_native_end'], -math.inf), math.nextafter(fee['outer_seconds']-sum(prior), math.inf)]
    a.require(native_end['completion_SHA'] == a.sha(d/'completion.json') and native_end['observations_SHA'] == a.sha(d/'observations.json') and
              timing['interval'] == interval and 0 < interval[0] <= interval[1] < p['cap_seconds'] and
              not timing['later_repair_engineering_in_original_interval'], 'outward original native-end/enclosing-wrapper interval; later review excluded')
    raw_bindings = dict(proposed['raw_bindings'])
    required = [d/name for name in ('launch.json', 'completion.json', 'audit.json', 'observations.json', 'result.json', 'phases.csv',
                                    'native_end_receipt.json', 'postexit_audit_receipt.json')]+[fee_path/'launch.json', fee_path/'receipt.json']
    a.require(all(path.relative_to(a.root).as_posix() in raw_bindings for path in required), 'all original lifecycle/clock files signed')
    result = dict(id=p['id'], arm='M-B', seed=launch['seed'], panel_kind=launch['panel_kind'], U=0., L=0., gap=0., relative_gap=None,
                  certificate=True, certificate_qualified=True, numbers_qualified=True, PE_SHA=a.pe_sha, DLL_SHA=a.dll_sha,
                  complete_seconds=None, complete_seconds_interval=interval, physical=own, new_physical_UBs=witnesses,
                  all_physical_witnesses=witnesses, native_records=native_records, model_contracts=contracts, starts=[submitted], start_attempts=[attempt],
                  cover=dict(independent_nonnegative_objective_floor=True, own_physical_zero=True, whole_improving_domain_covered=True,
                             all_relevant_closed=True, native_terminal_call_closure_withdrawn=True), raw_audit_passed=False,
                  normal_completion=comp, bindings=raw_bindings, actual_full_argv=actual['command'], damaged_calls=[4],
                  independently_proved_actual_return_without_journal=True,
                  rejected_raw_native_chronology=[dict(sequence=e['sequence'], raw_payload=e, native_bound_mathematically_qualified=False) for e in bounds]+[
                      dict(kind='native_final_claim', call=4, raw_final_native_L=0., returned_journal_missing=True, native_bound_mathematically_qualified=False)])
    signed = dict(decision='ACCEPT_CURRENT_SCOPED_CALL_REJECTION', current_key=key, damaged_calls=[4], preserved_distinct_LP_calls=[1, 2, 3],
                  production_PE_SHA=a.pe_sha, DLL_SHA=a.dll_sha, campaign_identity_SHA=proposed['campaign_identity_SHA'],
                  current_model_SHA=root_SHA, model_SHA=root_SHA, exact_vector_path=proposed['exact_vector_path'], exact_vector_SHA=a.sha(vector_path),
                  exact_objective=float(exact), exact_objective_fraction=[exact.numerator, exact.denominator], time=timing,
                  complete_seconds=None, complete_seconds_interval=interval, raw_bindings=raw_bindings, own_U=0., certificate_from_own_exact_zero=True,
                  original_native_flags_preserved=True, missing_returned_journal_preserved=True, independently_proved_normal_return=True,
                  reject_all_call_native_lower_claims=True, withdraw_necessary_dependent_closures=True,
                  own_complete_original_domain_floor=0., result=result, Optimize=0, native_environment=0)
    return signed, result, {root_SHA: root_model}, q

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--request', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    root, dest = Path(args.root).resolve(), Path(args.out).resolve()
    assert dest.is_relative_to(root/ROUND/'review')
    dest.mkdir(exist_ok=False)
    source, tick, error = Path(__file__).read_bytes(), time.perf_counter(), None
    (dest/'source_at_execution.py').write_bytes(source)
    def save(name, value):
        with (dest/name).open('x', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write('\n')
    save('launch.json', dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()), explicit_read_root=str(root),
                            source_SHA=hashlib.sha256(source).hexdigest(), Optimize=0, native_environment=0))
    try:
        identity = json.loads((root/ROUND/'campaign/identity.json').read_text(encoding='utf-8-sig'))
        a = Audit(root, dest, identity['candidate_binary_sha256'])
        proposed = a.obj(a.local(args.request))
        launch = next(l for l in identity['launches'] if [l['number'], l['id'], l['seed'], l['arm']] == proposed['key'])
        value, result, models, q = audit(a, launch, identity, proposed)
        value.update(completed_checks=a.checks, read_bindings=a.reads, module_bindings=a.module_bindings, source_SHA=hashlib.sha256(source).hexdigest())
    except Exception:
        error = traceback.format_exc()
        value = dict(decision='HOLD', error=error, Optimize=0, native_environment=0)
    save('audit.json', value)
    save('receipt.json', dict(exit_code=int(error is not None), engineering_elapsed_seconds=time.perf_counter()-tick,
                             source_SHA=hashlib.sha256(source).hexdigest(), audit_SHA=hashlib.sha256((dest/'audit.json').read_bytes()).hexdigest(),
                             Optimize=0, native_environment=0))
    print(json.dumps(dict(decision=value['decision'], completed_checks=value.get('completed_checks'), error=error)))
    if error:
        sys.exit(1)

if __name__ == '__main__':
    main()
