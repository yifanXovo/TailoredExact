"""Current cold26 bounded projection/clock continuation review; zero native.

The exact model arithmetic was independently signed before this bounded
review. This rechecks all signed bytes, the actual projection and remaining
fees without another costly partial-panel scan.
"""
from pathlib import Path
import argparse, ast, copy, hashlib, json, sys, time, traceback
from round110_independent_core import Audit, ROUND
from round110_independent_review import fees

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--request', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    root, dest = Path(args.root).resolve(), Path(args.out).resolve()
    assert dest.is_relative_to(root/ROUND/'review')
    dest.mkdir(exist_ok=False)
    source = Path(__file__).read_bytes()
    (dest/'source_at_execution.py').write_bytes(source)
    tick, error = time.perf_counter(), None
    def save(name, value):
        with (dest/name).open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write('\n')
    save('launch.json', dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
                            source_SHA=hashlib.sha256(source).hexdigest(), explicit_read_root=str(root),
                            Optimize=0, native_environment=0))
    try:
        identity_path = root/ROUND/'campaign/identity.json'
        identity = json.loads(identity_path.read_text(encoding='utf-8-sig'))
        a = Audit(root, dest, identity['candidate_binary_sha256'])
        request = a.obj(a.local(args.request))
        admission = a.obj(a.out/'review/performance_admission.json')
        candidate = a.obj(a.out/'candidate_identity.json')
        a.require(request['schema'] == 'round110-next-only-offline-projection-v1' and
                  request['campaign_identity_SHA'] == admission['campaign_identity_SHA'] == a.sha(identity_path) and
                  request['candidate_identity_SHA'] == admission['candidate_identity_SHA'] == a.sha(a.out/'candidate_identity.json') and
                  request['production_PE_SHA'] == admission['production_PE_SHA'] == a.pe_sha and
                  request['DLL_SHA'] == admission['DLL_SHA'] == identity['dll_sha256'], 'exact originally admitted final PE/campaign/candidate')
        a.require(a.sha(a.local(identity['prereg']['candidate_binary'])) == a.pe_sha and
                  candidate['full_argv'] == admission['all42_complete_argv'] == [l['command'] for l in identity['launches']],
                  'actual PE and every frozen argv unchanged')
        a.require(request['performance_helpers'] == identity['helpers'] and
                  request['performance_runner_SHA'] == identity['runner_sha256'], 'same frozen native helpers/runner inventory')
        for path, digest in {**identity['source_hashes'], **identity['helpers']}.items():
            a.require(a.sha(root/path) == digest, 'actual original production/performance bytes '+path)
        cache, proofs = {}, {}
        a.require(set(request['projection_bindings']) == {'15', '17', '25', '26'}, 'only four actual separately signed current calls projected')
        for number, meta in request['projection_bindings'].items():
            side_path, proof_path = a.local(meta['side_path']), a.local(meta['independent_audit_path'])
            side, proof = a.obj(side_path), a.obj(proof_path)
            a.require(a.sha(side_path) == meta['side_SHA'] and a.sha(proof_path) == meta['independent_audit_SHA'] == side['independent_audit_SHA'] and
                      a.local(side['independent_audit_path']) == proof_path and
                      proof['decision'] == ('ACCEPT_CURRENT_SCOPED_CALL_REJECTION' if number == '25' else 'ACCEPT_CURRENT_CALL_REJECTION') and
                      side['key'] == proof['current_key'] == [int(number), identity['launches'][int(number)-1]['id'], 0, 'M-B' if number == '25' else 'P-GRB'] and
                      side['raw_bindings'] == proof['raw_bindings'] and proof['campaign_identity_SHA'] == request['campaign_identity_SHA'],
                      'actual current signed proof and raw scope binding '+number)
            for path, digest in proof['raw_bindings'].items():
                a.require(a.sha(a.local(path)) == digest, 'original current raw/false flags/clocks immutable '+path)
            a.require(side['time'] == proof['time'] and side['model_SHA'] == proof['model_SHA'] and
                      side['exact_vector_SHA'] == proof['exact_vector_SHA'] == a.sha(a.local(side['exact_vector_path'])) and
                      side['own_U'] == proof['own_U'] and side['qualified_L'] == proof['own_complete_original_domain_floor'] == 0 and
                      side['certificate_from_own_exact_zero'] == proof['certificate_from_own_exact_zero'],
                      'same exact matrix/vector/original clocks and own signed endpoint '+number)
            raw = a.obj(a.local(identity['launches'][int(number)-1]['destination'])/'result.json')
            endpoint = dict(U=proof['own_U'], L=0., gap=proof['own_U'], certificate=proof['certificate_from_own_exact_zero'],
                            source='separately_signed_own_physical_endpoint_and_own_full_domain_floor', status=raw['status'])
            a.require(endpoint == request['explicit_qualified_offline_endpoints'][number], 'projection contains only own signed endpoint/floor '+number)
            cache[int(number)], proofs[int(number)] = endpoint, proof
            if number == '25':
                a.require(side['schema'] == 'round110-current-scoped-call-rejection-v1' and
                          proof['damaged_calls'] == side['damaged_calls'] == [4] and
                          proof['preserved_distinct_LP_calls'] == side['preserved_distinct_LP_calls'] == [1, 2, 3] and
                          proof['reject_all_call_native_lower_claims'] and proof['withdraw_necessary_dependent_closures'] and
                          proof['own_complete_original_domain_floor'] == side['qualified_L'] == proof['own_U'] == 0 and
                          proof['certificate_from_own_exact_zero'] and proof['original_native_flags_preserved'] and
                          proof['missing_returned_journal_preserved'] and proof['result']['raw_audit_passed'] is False,
                          'only actual current scoped call4 rejected; distinct LPs retained and own zero/floor certificate separate')
        a.require(cache[26]['U'] > 0 and not cache[26]['certificate'] and cache[26]['L'] == 0 and
                  proofs[26]['result']['raw_audit_passed'] is True and not proofs[26]['missing_returned_journal_preserved'],
                  'current cold26 retains own positive/open endpoint, original passed audit and actual returned journal')
        a.require(cache[15]['U'] > 0 and not cache[15]['certificate'] and cache[17]['U'] == 0 and cache[17]['certificate'] and
                  proofs[17]['missing_returned_journal_preserved'] and proofs[17]['result']['raw_audit_passed'] is False,
                  'current positive/open P15 and own exact-zero P17 with original missing-return/audit-false preserved')
        prior_scope_request = a.obj(a.out/'campaign/reader_recovery/continue25_04/request.json')
        readback_path = a.local(prior_scope_request['scoped_readback_path'])
        readback = a.obj(readback_path)
        p = readback['arm']
        a.require(p['U'] == p['L'] == p['gap'] == 0 and p['certificate'] and p['raw_audit_passed'] is False and
                  p['journal_return_missing'] and p['complete_seconds'] is None and
                  p['complete_seconds_interval'] == proofs[25]['complete_seconds_interval'] and
                  readback['journal_started'] == 4 and readback['journal_returned'] == 3 and
                  len(readback['rejected_claims']) == 3 and all(c['call'] == 4 and c['native_bound_mathematically_qualified'] is False for c in readback['rejected_claims']) and
                  [q['call'] for q in readback['preserved_LP_proofs']] == [1, 2, 3] and
                  readback['current_raw_cover']['native_call4_closure_withdrawn'] and
                  all(q['necessary_dependent_native_closure_withdrawn'] and not q['native_closure_mathematically_qualified'] for q in readback['current_raw_cover']['leaves']) and
                  readback['native_raw_flags_preserved'] and readback['Optimize'] == readback['native_environment'] == 0,
                  'actual bounded primary missing-return projection preserves all original flags and unknown exact clock')
        for row in readback['current_raw_cover']['timeline']:
            if row['event_type'] in ('native_root_processing_bound', 'terminal_mip_closure', 'incumbent_improvement', 'finalization'):
                a.require(row['raw_native_claim_mathematically_qualified'] is False and row['necessary_dependent_native_closure_withdrawn'],
                          'every damaged-call native lower/final cover claim withdrawn; own witness validity remains separate')
        rb = a.local(prior_scope_request['scoped_readback_execution_path'])
        receipt = a.obj(rb/'receipt.json')
        a.require(receipt['exit_code'] == 0 and receipt['conservative_solver_starts'] == 0 and
                  receipt['stdout_SHA'] == a.sha(rb/'stdout.log') and receipt['stderr_SHA'] == a.sha(rb/'stderr.log'), 'actual projection execution closed')
        cold_readback = a.obj(a.local(request['cold_readback_path']))
        c = cold_readback['arm']
        a.require(c['U'] == c['gap'] == proofs[26]['own_U'] and c['L'] == 0 and not c['certificate'] and
                  c['numbers_qualified'] and c['certificate_qualified'] and c['raw_audit_passed'] is True and
                  not c['journal_return_missing'] and c['complete_seconds'] is None and
                  c['complete_seconds_interval'] == proofs[26]['complete_seconds_interval'] and
                  c['native_call_bounds_mathematically_qualified'] is False and
                  cold_readback['journal_started'] == cold_readback['journal_returned'] == 1 and cold_readback['rejected_claims'] == 6 and
                  cold_readback['native_raw_flags_preserved'] and cold_readback['Optimize'] == cold_readback['native_environment'] == 0,
                  'actual cold26 readback preserves own positive/open state and complete original return while rejecting all six lower claims')
        rb26 = a.local(request['cold_readback_execution_path'])
        rr26 = a.obj(rb26/'receipt.json')
        a.require(rr26['exit_code'] == 0 and rr26['conservative_solver_starts'] == 0 and
                  rr26['stdout_SHA'] == a.sha(rb26/'stdout.log') and rr26['stderr_SHA'] == a.sha(rb26/'stderr.log'),
                  'actual current cold26 offline readback completed normally')
        summary_path = a.out/'campaign/summary.jsonl'
        a.require(a.sha(summary_path) == request['original_summary_SHA'] and request['original_summary_unchanged'], 'raw summary unmodified')
        records = [json.loads(line) for line in a.txt(summary_path).splitlines()]
        a.require([r['number'] for r in records] == request['completed_native_numbers'] == list(range(1, 27)) and
                  request['next_native_number'] == 27 and request['never_started_numbers'] == list(range(27, 43)) and
                  all(records[n-1]['audit_passed'] is False and records[n-1]['endpoint'] is None for n in (17, 25)),
                  'exact26 completed/16 never-started partition; original failed summary rows retained')
        a.require(records[25]['audit_passed'] is True and records[25]['endpoint']['L'] > 0,
                  'raw26 passed audit and original wrong native lower endpoint retained')
        remaining = identity['launches'][26:]
        a.require(all(not a.local(l['destination']).exists() for l in remaining), 'no arm27 or later native process started')
        wrapper_path, derived_path = a.local(request['resumed_wrapper_path']), a.local(request['derived_billed_path'])
        a.require(a.sha(wrapper_path) == request['resumed_wrapper_SHA'] and a.sha(derived_path) == request['derived_billed_SHA'], 'actual wrapper/derived source frozen')
        (dest/'resumed_wrapper_at_review.py').write_bytes(a.data(wrapper_path))
        (dest/'derived_billed_at_review.py').write_bytes(a.data(derived_path))
        prior_path = a.local(request['prior_resumed_wrapper_path'])
        prior_admission = a.obj(a.out/'review/continue17_02/audit.json')
        a.require(a.sha(prior_path) == request['prior_resumed_wrapper_SHA'] == prior_admission['resumed_wrapper_SHA'],
                  'prior admitted P15/P17 wrapper bytes unchanged')
        scoped_path = a.local(request['scoped_resumed_wrapper_path'])
        a.require(a.sha(scoped_path) == request['scoped_resumed_wrapper_SHA'] == prior_scope_request['resumed_wrapper_SHA'] and
                  request['scoped_evidence_SHA'] == prior_scope_request['scoped_evidence_SHA'] and
                  request['current_primary_entry_SHA'] == prior_scope_request['current_primary_entry_SHA'],
                  'prior admitted scoped wrapper/evidence/current primary bytes remain unchanged')
        for name in ('scoped_evidence', 'current_primary_entry', 'cold_runtime'):
            path = a.local(request[name+'_path'])
            a.require(a.sha(path) == request[name+'_SHA'], 'new separately bound offline '+name)
            (dest/(name+'_at_review.py')).write_bytes(a.data(path))
        evidence = a.txt(a.local(request['scoped_evidence_path']))
        a.require("a['decision']=='ACCEPT_CURRENT_SCOPED_CALL_REJECTION'" in evidence and
                  "==[25,'G100-C1',0,'M-B']" in evidence and
                  "s['damaged_calls']==[4]" in evidence and "s['preserved_distinct_LP_calls']==[1,2,3]" in evidence and
                  evidence.index("for relative,digest in s['raw_bindings'].items()") < evidence.index('if verified_key in _checked_scoped_bytes:return s') and
                  "core.sha(audit)==s['independent_audit_SHA']" in evidence and
                  "str(root),core.sha(root/side_path(launch)),s['independent_audit_SHA']" in evidence and
                  's=verify_signed_scope_binding(root,launch,d)' in evidence,
                  'bounded scoped dispatch verifies exact current signed bytes before per-process cache reuse')
        gate_node = next(n for n in ast.parse(evidence).body if isinstance(n, ast.FunctionDef) and n.name == 'verify_signed_scope_binding')
        gate = ast.get_source_segment(evidence, gate_node)
        a.require('model_contract(' not in gate and 'model_scope_contract(' not in gate and 'Fraction(' not in gate and
                  "a['own_complete_original_domain_floor']==s['qualified_L']==0." in gate and
                  "located(root,s['exact_vector_path'])" in gate and "s['raw_bindings']" in gate,
                  'runtime scoped gate checks the signed own endpoint and all raw/model/vector bytes without repeated matrix arithmetic')
        cold_binding = a.txt(a.local(request['cold_runtime_path']))
        a.require("==[26,'G100-C1',0,'P-GRB']" in cold_binding and
                  "a['decision']=='ACCEPT_CURRENT_CALL_REJECTION'" in cold_binding and
                  "for relative,digest in s['raw_bindings'].items()" in cold_binding and
                  "core.sha(audit)==s['independent_audit_SHA']" in cold_binding and
                  "s['model_SHA']==p['reference']['canonical_sha256']" in cold_binding and
                  "core.sha(located(root,s['exact_vector_path']))==s['exact_vector_SHA']" in cold_binding and
                  'model_contract(' not in cold_binding and 'Fraction(' not in cold_binding,
                  'new runtime cold26 gate verifies explicit current signed proof and all original matrix/vector bytes without arithmetic or native work')
        original = '\n'.join(a.txt(root/'scripts/round110_campaign.py').splitlines())+'\n'
        node = next(n for n in ast.parse(original).body if isinstance(n, ast.FunctionDef) and n.name == 'billed')
        function = ast.get_source_segment(original, node)+'\n'
        changes = [
            ("all(r['audit_passed'] for r in previous)", "all(r.get('qualified_offline_audit_passed',r['audit_passed']) for r in previous)"),
            ("[sys.executable,__file__,'billed',name,str(first),str(last),label]+(['--qualification'] if qualification else [])", "[sys.executable,*sys.argv]"),
            ("qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA)",
             "qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,offline_projection=_projection_meta)"),
            ("arm_tick=time.perf_counter();check_identity();launch=identity['launches'][number-1]", "arm_tick=(_resumed_admission_tick if number==first else time.perf_counter());check_identity();launch=identity['launches'][number-1]"),
            ("    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0", "    (d/'source_snapshot/scripts/round110_cold26_resumed_campaign.py').write_bytes(_resume_source.read_bytes())\n    (d/'source_snapshot/scripts/round110_cold_runtime.py').write_bytes(_cold_source.read_bytes())\n    (d/'source_snapshot/scripts/round110_scoped_resumed_campaign.py').write_bytes(_scoped_prior_source.read_bytes())\n    (d/'source_snapshot/scripts/round110_scoped_evidence.py').write_bytes(_scoped_source.read_bytes())\n    (d/'source_snapshot/scripts/round110_resumed_campaign.py').write_bytes(_prior_source.read_bytes())\n    (d/'source_snapshot/derived_billed.py').write_text(_derived_source,encoding='utf-8')\n    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0")]
        for old, new in changes:
            a.require(function.count(old) == 1, 'each reviewed bounded replacement has one exact original location')
            function = function.replace(old, new)
        a.require(function.splitlines() == a.txt(derived_path).splitlines(), 'entire derived function differs only in five reviewed offline/receipt/clock locations')
        wrapper = '\n'.join(a.txt(wrapper_path).splitlines())+'\n'
        tree = ast.parse(wrapper)
        billed = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'billed')
        a.require(ast.unparse(billed.body[0]) == 'admission_tick = time.perf_counter()' and
                  '_resumed_admission_tick=admission_tick' in wrapper and
                  "namespace['billed'](name,first,last,label,False)" in wrapper and
                  "audit['request_SHA']==sha(RESUME_REQUEST)" in wrapper and
                  request['first_arm_whole_clock_includes_resumed_projection_admission'], 'first resumed arm includes all additional admission/cache work before unchanged native supervision')
        a.require('for number in [15,17,25,26]:' in wrapper and 'frozen.records=lambda camp:prior.projected_records(camp,cache)' in wrapper and
                  "request['next_native_number']<=first<=last<=42" in wrapper and
                  'evidence.verify_signed_scope_binding(ROOT,launch,d) if number==25' in wrapper and
                  'cold_runtime.verify_signed_cold_binding(ROOT,launch,d) if number==26' in wrapper,
                  'new wrapper only reads four separately signed current endpoints and gates never-started continuation')
        runtime = a.obj(a.local(request['cold_runtime_gate_path']))
        rt = a.local(request['cold_runtime_gate_execution_path'])
        rt_receipt = a.obj(rt/'receipt.json')
        a.require(runtime['cache'] == request['explicit_qualified_offline_endpoints'] and
                  runtime['projection_bindings'] == request['projection_bindings'] and
                  runtime['wrapper_SHA'] == request['resumed_wrapper_SHA'] and
                  runtime['scoped_evidence_SHA'] == request['scoped_evidence_SHA'] and
                  runtime['cold_runtime_SHA'] == request['cold_runtime_SHA'] and
                  0 < runtime['actual_cache_admission_seconds'] < 30 and runtime['full_matrix_arithmetic_remains_offline'] and
                  runtime['Optimize'] == runtime['native_environment'] == 0 and
                  rt_receipt['exit_code'] == 0 and rt_receipt['conservative_solver_starts'] == 0 and
                  rt_receipt['stdout_SHA'] == a.sha(rt/'stdout.log') and rt_receipt['stderr_SHA'] == a.sha(rt/'stderr.log'),
                  'actual fresh-process runtime admission fits unchanged shutdown reserve; full matrix proof remains offline')
        prior_tree = ast.parse(a.txt(prior_path))
        projection = next(n for n in prior_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'projected_records')
        namespace = dict(Path=Path, OUT=a.out, copy=copy, _raw_records=lambda camp: records)
        exec(compile(ast.Module(body=[projection], type_ignores=[]), str(wrapper_path)+'::read_only_projector', 'exec'), namespace)
        rows = namespace['projected_records'](a.out/'campaign', cache)
        for raw, projected in zip(records, rows):
            if raw['number'] not in cache:
                a.require(raw == projected, 'every other original record unchanged by projection')
            else:
                a.require(projected['audit_passed'] == raw['audit_passed'] and projected['original_raw_audit_passed'] == raw['audit_passed'] and
                          projected['original_raw_endpoint'] == raw['endpoint'] and projected['endpoint'] == cache[raw['number']] and
                          projected['qualified_offline_audit_passed'] is True, 'actual in-memory projector retains raw fields and explicitly qualifies only signed endpoint')
        a.require(all(r.get('qualified_offline_audit_passed', r['audit_passed']) for r in rows) and
                  a.sha(summary_path) == request['original_summary_SHA'], 'offline previous gate qualified without raw-summary write')
        groups = []
        for group in dict.fromkeys(l['group_number'] for l in remaining):
            launches = [l for l in remaining if l['group_number'] == group]
            groups.append((launches[0]['cap_seconds'], tuple(l['arm'] for l in launches)))
        fee_records = fees(a)
        budget = a.budget(fee_records, groups, overhead=120*len(groups))
        a.require(budget['paid_starts'] == request['budget']['paid_starts'] == 57 and
                  budget['paid_outer_seconds'] == request['budget']['paid_outer_seconds'] and not request['budget']['unclosed'] and
                  request['remaining_fixed_reserve'] == dict(starts=budget['remaining_formal_starts'], nominal_seconds=budget['remaining_nominal_seconds'],
                  overhead_seconds=budget['remaining_overhead_seconds']) and budget['remaining_formal_starts'] == 23 and budget['remaining_nominal_seconds'] == 48600,
                  'all closed fees retained, including repeatedly lost27 slots, and entire remaining worst reserve fits')
        main09 = next(f for f in fee_records if f['label'] == 'main09_tail01')
        a.require(main09['conservative_process_starts'] == 3 and main09['exit_code'] == 1 and
                  request['direct_wrapper_processes'] == 1 and request['new_main09_tail02_fee_starts'] == 2 and
                  request['failed_main09_tail01_three_starts_remain_paid'], 'failed three-start wrapper remains billed; new27 direct wrapper plus child adds two starts')
        value = dict(decision='ACCEPT_NEXT_ONLY_SAME_PE_RESUMPTION', next_native_number=27,
                     never_started_numbers=list(range(27, 43)), request_SHA=a.sha(a.local(args.request)),
                     resumed_wrapper_SHA=request['resumed_wrapper_SHA'], derived_billed_SHA=request['derived_billed_SHA'],
                     current_projection_bindings=request['projection_bindings'], original_summary_SHA=request['original_summary_SHA'],
                     budget=budget, fee_records=fee_records, same_actual_PE_all42_argv_and_native_helpers=True,
                     original_audit_false_missing_return_and_null_whole_clock_preserved=True,
                     first_arm_whole_clock_includes_added_admission=True, offline_projector_exec_only=True,
                     runtime_cache_admission_seconds=runtime['actual_cache_admission_seconds'],
                     no_native_supervisor_or_solver_parameter_change=True, no_online_UB_Start_cut_cache_transfer=True,
                     completed_checks=a.checks, read_bindings=a.reads, Optimize=0, native_environment=0)
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
