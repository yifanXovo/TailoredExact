"""Current cold-P exact counterexample/floor proof, independent of primary code.

This is a bounded known proof class, never a tuple-based automatic fallback.
Invocation is only after a real current fault has paused the campaign. A new
scoped/mathematical/model/return fault outside these predicates HOLDs.
"""
from fractions import Fraction
from collections import Counter
from pathlib import Path
import argparse, hashlib, json, math, re, sys, time, traceback
from round110_independent_core import Audit, ROUND, SETTINGS, TOL


def audit(a, launch, identity, proposed):
    key = [launch['number'], launch['id'], launch['seed'], launch['arm']]
    a.require(launch['arm'] == 'P-GRB' and proposed['schema'] == 'round110-current-cold-call-rejection-v1' and
              proposed['key'] == key, 'current call exact cold-P class, no historical tuple authority')
    d, p = a.local(launch['destination']), launch['panel']
    a.require(proposed['production_PE_SHA'] == identity['candidate_binary_sha256'] == a.pe_sha and
              proposed['DLL_SHA'] == identity['dll_sha256'] == a.dll_sha and
              proposed['campaign_identity_SHA'] == a.sha(a.out/'campaign/identity.json'),
              'current campaign and final PE/DLL immutable identities')
    a.require(proposed['command'] == launch['command'] and
              proposed['input_SHA'] == a.sha(a.root/p['input_path']) == p['input_sha256'], 'current actual argv/input')
    for path, digest in proposed['raw_bindings'].items():
        a.require(a.sha(a.local(path)) == digest, 'current proposed raw binding '+path)
    actual, raw, comp = a.obj(d/'launch.json'), a.obj(d/'result.json'), a.obj(d/'completion.json')
    original_audit = a.obj(d/'audit.json')
    a.require(original_audit['binary_sha256'] == a.pe_sha, 'original actual observer records current production PE')
    a.require(actual['command'] == launch['command'] and actual['panel'] == p and
              actual['prereg_sha256'] == identity['prereg_sha256'], 'actual current launch and original scenario')
    a.require(comp['returncode'] == 0 and comp['stop_reason'] == 'normal_return' and comp['within_cap'],
              'current process normal complete return within original cap')
    q = a.functions['input_file'](a.root/p['input_path'])
    own = a.functions['full_physics'](q, raw['routes'], p)
    a.require(a.near(own['U'], raw['objective']) and a.near(own['U'], raw['upper_bound']) and
              own['final_inventories'] == raw['final_inventories'], 'own complete original physical integer fleet')
    model_path = d/'compact.lp'
    model_SHA = a.sha(model_path)
    a.require(model_SHA == p['reference']['canonical_sha256'] == a.sha(a.reference_path(p)),
              'current call matrix exactly original cold reference')
    m = a.model(model_path)
    domain = a.functions['domain_contract'](m, q, 'P-GRB')
    expected = {'G': 1., **{f'e_{i}': p['lambda']*q['weights'][i] for i in range(1, q['V']+1)}}
    a.require(set(m['objective']) == set(expected) and all(a.near(m['objective'][n], v, 1e-12) for n, v in expected.items()),
              'original own full-domain F objective exactly retained')
    a.require(math.isfinite(p['lambda']) and p['lambda'] >= 0 and
              all(math.isfinite(w) and w >= 0 for w in q['weights'][1:]) and
              all(target > 0 for target in q['target'][1:]) and
              all(math.isfinite(v) and v >= 0 and m['bounds'][n][0] >= 0 for n, v in m['objective'].items()),
              'separate current whole-original-domain nonnegative physical and matrix objective floor')
    observations = a.obj(d/'observations.json')
    calls, returned, failures, bounds, witnesses = [], [], [], [], []
    for seq, observed in enumerate(observations, 1):
        event = observed['payload']
        eb = a.data(d/'journal'/f'event_{seq}.json')
        commit = a.txt(d/'journal'/f'event_{seq}.commit').split()
        a.require(event['sequence'] == observed['sequence'] == seq and json.loads(eb) == event and
                  hashlib.sha256(eb).hexdigest() == observed['sha256'] == commit[4] and
                  commit[0] == 'NEJ1' and int(commit[1]) == seq and int(commit[3]) == len(eb),
                  'every original current journal event/commit intact')
        a.require(a.near(float(commit[2]), observed['data_close_seconds'], 1e-9) and
                  a.near(observed['effective_available_seconds'], max(observed['data_close_seconds'], observed['first_observed_seconds']), 1e-9),
                  'original current event availability retained')
        kind = event['kind']
        if kind == 'identity':
            a.require(seq == 1 and event['input_sha256'] == p['input_sha256'] and
                      (event['V'], event['M'], event['T'], event['lambda'], event['pickup_seconds'], event['drop_seconds']) ==
                      (p['V'], p['M'], p['T_seconds'], p['lambda'], p['pickup_seconds'], p['drop_seconds']), 'own current event identity')
        elif kind == 'call':
            calls.append(event)
        elif kind == 'returned':
            returned.append(event)
        elif kind == 'failure':
            failures.append(event)
        elif kind == 'bound':
            a.require(event['call'] == 1 and math.isfinite(event['native_bound']), 'current finite raw call lower claim')
            bounds.append(event)
        elif kind == 'witness':
            w = a.functions['full_physics'](q, event['routes'], p)
            a.require(event['call'] == 1 and a.near(w['U'], event['objective']) and
                      a.near(w['G'], event['G']) and a.near(w['P'], event['P']), 'own current physical journal UB')
            w.update(sequence=seq, source=event['source'], raw_available=observed['effective_available_seconds'])
            witnesses.append(w)
        else:
            raise AssertionError('new unsupported damaged-call event '+kind)
    a.require(len(calls) == 1 and len(returned) <= 1 and witnesses, 'one actual full cold call and own physical UB evidence')
    call = calls[0]
    a.require(call['call'] == 1 and call['full_original'] == 1 and
              call['model_scope'] == 'complete_original_compact_milp' and call['model_sha256'] == model_SHA and
              call['settings'] == dict(read_return_code=0, **SETTINGS, Seed=launch['seed']) and
              call['lower_g'] == 0 and call['upper_g'] == call['gmax'] == (q['V']-1)/q['V'] and call['cutoff'] == 0,
              'actual full original cold scope and every native setting')
    a.require(call['native_preconditions'] == (1 if launch['seed'] == 0 else 0), 'raw legacy Seed metadata preserved')
    a.require(all(e['call'] == 1 and e['return_code'] == 0 for e in returned), 'actual matching committed successful return when present')
    a.require(not failures or all(e['reason'] == 'full_bound_witness_inconsistency' for e in failures),
              'only original known numerical journal latch class; novel failure HOLDs')
    native = a.txt(d/'native.log')
    size = re.search(r'Optimize a model with (\d+) rows, (\d+) columns', native)
    types = re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)', native)
    a.require(size is not None and types is not None, 'actual complete native optimize/type header')
    actual_types = dict(C=int(types[1]), I=int(types[2])-int(types[3]), B=int(types[3]))
    saved_types = {k: Counter(m['types'].values()).get(k, 0) for k in ('C', 'I', 'B')}
    a.require((int(size[1]), int(size[2])) == (len(m['rows']), len(m['bounds'])) and actual_types == saved_types,
              'actual native all rows/columns/original integer types')
    flags = ('native_mip_evidence_available', 'native_mip_evidence_capture_complete', 'native_mip_lifecycle_valid',
             'native_mip_solver_finalization_reached', 'native_mip_problem_freed', 'native_mip_environment_closed',
             'gurobi_lifecycle_valid', 'gurobi_solver_finalization_reached', 'gurobi_native_domain_audit_passed',
             'gurobi_native_variable_bounds_match', 'gurobi_native_objective_sense_match', 'native_mip_status_code_text_consistent')
    a.require(all(raw[name] is True for name in flags), 'every original functional/native/domain/lifecycle gate')
    a.require(all(raw[name] == 0 for name in ('native_mipopt_return_code', 'gurobi_optimize_return_code',
                                             'native_mip_freeprob_return_code', 'native_mip_close_return_code')),
              'actual optimize and complete cleanup rc0 independently captured')
    counts = ('native_mip_environment_count', 'native_mip_problem_count', 'native_mip_model_read_count',
              'native_mip_mipopt_count', 'gurobi_optimize_count', 'native_mip_freeprob_count', 'native_mip_close_count')
    a.require(all(raw[name] == 1 for name in counts) and not raw['gurobi_hga_start_requested'] and
              not raw['gurobi_hga_start_submitted'] and 'Loaded user MIP start' not in native,
              'one original cold native call and no supplied or cross-arm Start')
    final = re.findall(r'Best objective ([^,]+), best bound ([^,]+), gap ([^\n]+)', native)
    a.require(final and a.near(float(final[-1][1]), raw['native_mip_best_bound']) and
              raw['native_mip_status_text'] in ('OPTIMAL', 'TIME_LIMIT'), 'actual final native log/attribute/status corroboration only')
    phase_rows = a.rows(d/'phases.csv')
    events = [r['event'] for r in phase_rows]
    required = ['plain_gurobi_optimize_launch', 'final_result_serialization_start', 'final_result_serialization_complete', 'process_exit']
    a.require(all(events.count(name) == 1 for name in required) and
              [events.index(name) for name in required] == sorted(events.index(name) for name in required) and
              phase_rows[-1]['detail'] == 'rc=0', 'actual native launch/complete serialization/process exit order')
    if not returned:
        a.require(raw['native_mip_status_text'] == 'OPTIMAL' and
                  float(final[-1][0]) == float(final[-1][1]) == raw['native_mip_best_bound'] == 0. and
                  own['U'] == own['G'] == own['P'] == 0.,
                  'known missing-return latch class requires actual native OPTIMAL/final zero and own exact physical zero')
        source = a.txt(a.root/'src/GurobiBaseline.cpp')
        journal_source = a.txt(a.root/'src/NativeEvidenceJournal.cpp')
        a.require(failures and 'result.gurobi_optimize_return_code = api.optimize(model);' in source and
                  'result.native_mipopt_return_code = result.gurobi_optimize_return_code;' in source and
                  'failed_=true;' in journal_source and 'if(failed_) return;' in journal_source,
                  'known numerical latch explains missing journal; actual API/log/cleanup/normal process proves return')
    vector_path = a.local(proposed['exact_vector_path'])
    vector = a.obj(vector_path)
    values = {n: Fraction(*v) for n, v in vector['complete_column_values'].items()}
    a.require(set(values) == set(m['bounds']), 'current exact counterexample every matrix column')
    for n, (lo, hi) in m['bounds'].items():
        a.require((not math.isfinite(lo) or values[n] >= Fraction(lo)) and
                  (not math.isfinite(hi) or values[n] <= Fraction(hi)) and
                  (m['types'][n] == 'C' or values[n].denominator == 1), 'current exact counterexample column '+n)
    for sense, rhs, terms in m['rows']:
        lhs = sum((values[n]*Fraction(coefficient) for n, coefficient in terms), Fraction(0))
        target = Fraction(rhs)
        a.require(lhs == target if sense == '=' else lhs <= target if sense == '<' else lhs >= target,
                  'current exact in-domain counterexample matrix row')
    exact = sum((values[n]*Fraction(coefficient) for n, coefficient in m['objective'].items()), Fraction(0))
    claims = [e['native_bound'] for e in bounds] + [raw['native_mip_best_bound']]
    a.require(exact >= 0 and any(Fraction(value) > exact+Fraction(TOL) for value in claims),
              'actual current lower claim strictly contradicts complete exactly feasible same-model vector')
    a.require(proposed['reject_all_call_native_lower_claims'] and proposed['withdraw_necessary_dependent_closures'] and
              proposed['qualified_L'] == 0 and proposed['qualified_L_source'] ==
              'independently_proved_own_original_full_domain_nonnegative_floor', 'all native claims rejected and separate own floor retained')
    zero = own['U'] == own['G'] == own['P'] == 0.
    a.require(proposed['own_U'] == own['U'] and proposed['certificate_from_own_exact_zero'] == zero,
              'own exact physical zero only; no imported UB/certificate')
    timing = proposed['time']
    a.require(timing['exact_seconds'] is None and not (d/'whole_arm_receipt.json').exists(), 'unknown complete clock remains honestly null')
    lo, hi = timing['interval']
    native_end = a.obj(d/'native_end_receipt.json')
    a.require(native_end['completion_SHA'] == a.sha(d/'completion.json') and
              native_end['observations_SHA'] == a.sha(d/'observations.json'), 'actual original native end timing binds raw closure')
    a.require(lo == math.nextafter(native_end['complete_seconds_until_native_end'], -math.inf) and
              0 < lo <= hi < p['cap_seconds'],
              'lower clock bound outward-derived from actual original recorded native-end duration')
    fee_directory = a.local(proposed['original_fee_path'])
    fee_launch, fee_receipt = a.obj(fee_directory/'launch.json'), a.obj(fee_directory/'receipt.json')
    first, last = map(int, fee_launch['command'][4:6])
    a.require(fee_launch['qualification'] is False and fee_launch['command'][2] == 'billed' and
              first <= launch['number'] <= last and fee_receipt['exit_code'] == 1 and
              fee_receipt['conservative_process_starts'] == fee_launch['conservative_process_starts'],
              'original failed formal wrapper retained as original timing enclosure')
    prior = []
    for number in range(first, launch['number']):
        receipt_path = a.local(identity['launches'][number-1]['destination'])/'whole_arm_receipt.json'
        receipt = a.obj(receipt_path)
        a.require(receipt['number'] == number and receipt_path.relative_to(a.root).as_posix() in proposed['raw_bindings'],
                  'every disjoint preceding original arm clock bound and subtracted once')
        prior.append(receipt['complete_seconds'])
    upper = math.nextafter(fee_receipt['outer_seconds']-sum(prior), math.inf)
    a.require(hi == upper and timing.get('later_repair_engineering_in_original_interval', False) is False,
              'outward original wrapper bound; no cap endpoint or later repair duration substituted')
    critical = ['launch.json', 'result.json', 'completion.json', 'audit.json', 'observations.json',
                'native.log', 'phases.csv', 'compact.lp', 'native_end_receipt.json', 'postexit_audit_receipt.json']
    required_paths = [d/name for name in critical]+[fee_directory/'launch.json', fee_directory/'receipt.json']
    a.require(all(path.relative_to(a.root).as_posix() in proposed['raw_bindings'] for path in required_paths),
              'all current raw lifecycle and original enclosing-clock receipts signed')
    raw_bindings = dict(proposed['raw_bindings'])
    native_record = dict(call=1, leaf='', model_SHA=model_SHA, model_path=str(model_path.relative_to(a.root)),
                         native_log_path=str((d/'native.log').relative_to(a.root)), native_log_SHA=a.sha(d/'native.log'),
                         native_status=raw['native_mip_status_text'], solve_kind='MIP', native_types=actual_types,
                         return_sequence=returned[0]['sequence'] if returned else None,
                         returned_journal_missing=not bool(returned), actual_native_return_code=0,
                         native_bounds_mathematically_qualified=False, returned_native_log_L=float(final[-1][1]))
    result = dict(id=p['id'], seed=launch['seed'], panel_kind='main' if launch['seed'] == 0 else 'seed',
                  arm='P-GRB', U=own['U'], L=0., gap=own['U'], relative_gap=None if zero else 1.,
                  numbers_qualified=True, certificate_qualified=True, certificate=zero,
                  complete_seconds=None, complete_seconds_interval=[lo, hi], PE_SHA=a.pe_sha, DLL_SHA=a.dll_sha,
                  physical=own, new_physical_UBs=witnesses, all_physical_witnesses=witnesses,
                  native_records=[native_record], model_contracts=[dict(path=str(model_path.relative_to(a.root)), SHA=model_SHA, **domain)],
                  starts=[], start_attempts=[], cover=dict(independently_proved_complete_original_objective_floor=True,
                  own_physical_zero=zero, whole_improving_domain_covered=True, all_relevant_closed=zero),
                  raw_audit_passed=original_audit['passed'], raw_status=raw['status'], normal_completion=comp,
                  bindings=raw_bindings, actual_full_argv=actual['command'], native_bounds_mathematically_qualified=False,
                  independently_proved_actual_return_without_journal=not bool(returned),
                  rejected_raw_native_chronology=[dict(sequence=e['sequence'], raw_payload=e) for e in bounds+returned])
    signed = dict(decision='ACCEPT_CURRENT_CALL_REJECTION', current_key=key,
                  production_PE_SHA=a.pe_sha, DLL_SHA=a.dll_sha, campaign_identity_SHA=proposed['campaign_identity_SHA'],
                  current_model_SHA=model_SHA, model_SHA=model_SHA, time=timing,
                  exact_vector_path=proposed['exact_vector_path'], exact_vector_SHA=a.sha(vector_path), exact_objective=float(exact),
                  complete_seconds=None, complete_seconds_interval=[lo, hi], raw_bindings=raw_bindings,
                  original_native_flags_preserved=True, missing_returned_journal_preserved=not bool(returned),
                  independently_proved_normal_return=True, reject_all_call_native_lower_claims=True,
                  own_complete_original_domain_floor=0., certificate_from_own_exact_zero=zero,
                  own_U=own['U'], result=result, Optimize=0, native_environment=0)
    return signed, result, {model_SHA: m}, q


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--request', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    root, dest = Path(args.root).resolve(), Path(args.out).resolve()
    assert dest.is_relative_to(root/ROUND/'review')
    dest.mkdir(parents=True, exist_ok=False)
    tick, error = time.perf_counter(), None
    source = Path(__file__).read_bytes()
    (dest/'source_at_execution.py').write_bytes(source)
    def save(name, value):
        with (dest/name).open('x', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write('\n')
    save('launch.json', dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
                            source_SHA=hashlib.sha256(source).hexdigest(), Optimize=0, native_environment=0))
    try:
        identity = json.loads((root/ROUND/'campaign/identity.json').read_text(encoding='utf-8-sig'))
        a = Audit(root, dest, identity['candidate_binary_sha256'])
        proposed = a.obj(a.local(args.request))
        launch = next(l for l in identity['launches'] if [l['number'], l['id'], l['seed'], l['arm']] == proposed['key'])
        value, result, models, q = audit(a, launch, identity, proposed)
        value.update(read_bindings=a.reads, completed_checks=a.checks, source_SHA=hashlib.sha256(source).hexdigest())
    except Exception:
        error = traceback.format_exc()
        value = dict(decision='HOLD', error=error, Optimize=0, native_environment=0)
    save('audit.json', value)
    save('receipt.json', dict(exit_code=int(error is not None), cwd=str(Path.cwd()),
                              engineering_elapsed_seconds=time.perf_counter()-tick,
                              source_SHA=hashlib.sha256(source).hexdigest(),
                              audit_SHA=hashlib.sha256((dest/'audit.json').read_bytes()).hexdigest(),
                              Optimize=0, native_environment=0))
    print(json.dumps(dict(decision=value['decision'], error=error)))
    if error:
        sys.exit(1)


if __name__ == '__main__':
    main()
