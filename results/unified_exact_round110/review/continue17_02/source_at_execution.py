"""Current17 bounded projection/clock continuation review; zero native."""
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
        a.require(set(request['projection_bindings']) == {'15', '17'}, 'only two actual separately signed current calls projected')
        for number, meta in request['projection_bindings'].items():
            side_path, proof_path = a.local(meta['side_path']), a.local(meta['independent_audit_path'])
            side, proof = a.obj(side_path), a.obj(proof_path)
            a.require(a.sha(side_path) == meta['side_SHA'] and a.sha(proof_path) == meta['independent_audit_SHA'] == side['independent_audit_SHA'] and
                      a.local(side['independent_audit_path']) == proof_path and proof['decision'] == 'ACCEPT_CURRENT_CALL_REJECTION' and
                      side['key'] == proof['current_key'] == [int(number), identity['launches'][int(number)-1]['id'], 0, 'P-GRB'] and
                      side['raw_bindings'] == proof['raw_bindings'] and proof['campaign_identity_SHA'] == request['campaign_identity_SHA'],
                      'actual current signed proof and raw scope binding '+number)
            for path, digest in proof['raw_bindings'].items():
                a.require(a.sha(a.local(path)) == digest, 'original current raw/false flags/clocks immutable '+path)
            a.require(side['time'] == proof['time'] and side['model_SHA'] == proof['model_SHA'] and
                      side['exact_vector_SHA'] == proof['exact_vector_SHA'] == a.sha(a.local(side['exact_vector_path'])), 'same exact matrix/vector/original clocks '+number)
            raw = a.obj(a.local(identity['launches'][int(number)-1]['destination'])/'result.json')
            endpoint = dict(U=proof['own_U'], L=0., gap=proof['own_U'], certificate=proof['certificate_from_own_exact_zero'],
                            source='separately_signed_own_physical_endpoint_and_own_full_domain_floor', status=raw['status'])
            a.require(endpoint == request['explicit_qualified_offline_endpoints'][number], 'projection contains only own signed endpoint/floor '+number)
            cache[int(number)], proofs[int(number)] = endpoint, proof
        a.require(cache[15]['U'] > 0 and not cache[15]['certificate'] and cache[17]['U'] == 0 and cache[17]['certificate'] and
                  proofs[17]['missing_returned_journal_preserved'] and proofs[17]['result']['raw_audit_passed'] is False,
                  'current positive/open P15 and own exact-zero P17 with original missing-return/audit-false preserved')
        readback_path = a.out/'campaign/reader_recovery/cold17_readback01/readback.json'
        readback = a.obj(readback_path)
        p = readback['arm']
        a.require(p['U'] == p['L'] == p['gap'] == 0 and p['certificate'] and p['raw_audit_passed'] is False and
                  p['journal_return_missing'] and p['complete_seconds'] is None and
                  p['complete_seconds_interval'] == proofs[17]['complete_seconds_interval'] and
                  readback['journal_returned'] == 0 and readback['rejected_claims'] == 3 and
                  readback['native_raw_flags_preserved'] and readback['Optimize'] == readback['native_environment'] == 0,
                  'actual bounded primary missing-return projection preserves all original flags and unknown exact clock')
        rb = a.out/'engineering/cold17_readback01'
        receipt = a.obj(rb/'receipt.json')
        a.require(receipt['exit_code'] == 0 and receipt['conservative_solver_starts'] == 0 and
                  receipt['stdout_SHA'] == a.sha(rb/'stdout.log') and receipt['stderr_SHA'] == a.sha(rb/'stderr.log'), 'actual projection execution closed')
        summary_path = a.out/'campaign/summary.jsonl'
        a.require(a.sha(summary_path) == request['original_summary_SHA'] and request['original_summary_unchanged'], 'raw summary unmodified')
        records = [json.loads(line) for line in a.txt(summary_path).splitlines()]
        a.require([r['number'] for r in records] == request['completed_native_numbers'] == list(range(1, 18)) and
                  request['next_native_number'] == 18 and request['never_started_numbers'] == list(range(18, 43)) and
                  records[16]['audit_passed'] is False and records[16]['endpoint'] is None,
                  'exact17 completed/25 never-started partition; original failed summary row retained')
        remaining = identity['launches'][17:]
        a.require(all(not a.local(l['destination']).exists() for l in remaining), 'no arm18 or later native process started')
        wrapper_path, derived_path = a.local(request['resumed_wrapper_path']), a.local(request['derived_billed_path'])
        a.require(a.sha(wrapper_path) == request['resumed_wrapper_SHA'] and a.sha(derived_path) == request['derived_billed_SHA'], 'actual wrapper/derived source frozen')
        (dest/'resumed_wrapper_at_review.py').write_bytes(a.data(wrapper_path))
        (dest/'derived_billed_at_review.py').write_bytes(a.data(derived_path))
        original = '\n'.join(a.txt(root/'scripts/round110_campaign.py').splitlines())+'\n'
        node = next(n for n in ast.parse(original).body if isinstance(n, ast.FunctionDef) and n.name == 'billed')
        function = ast.get_source_segment(original, node)+'\n'
        changes = [
            ("all(r['audit_passed'] for r in previous)", "all(r.get('qualified_offline_audit_passed',r['audit_passed']) for r in previous)"),
            ("[sys.executable,__file__,'billed',name,str(first),str(last),label]+(['--qualification'] if qualification else [])", "[sys.executable,*sys.argv]"),
            ("qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA)",
             "qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,offline_projection=_projection_meta)"),
            ("arm_tick=time.perf_counter();check_identity();launch=identity['launches'][number-1]", "arm_tick=(_resumed_admission_tick if number==first else time.perf_counter());check_identity();launch=identity['launches'][number-1]"),
            ("    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0", "    (d/'source_snapshot/scripts/round110_resumed_campaign.py').write_bytes(_resume_source.read_bytes())\n    (d/'source_snapshot/derived_billed.py').write_text(_derived_source,encoding='utf-8')\n    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0")]
        for old, new in changes:
            a.require(function.count(old) == 1, 'each reviewed bounded replacement has one exact original location')
            function = function.replace(old, new)
        a.require(function.splitlines() == a.txt(derived_path).splitlines(), 'entire derived function differs only in five reviewed offline/receipt/clock locations')
        wrapper = '\n'.join(a.txt(wrapper_path).splitlines())+'\n'
        tree = ast.parse(wrapper)
        billed = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'billed')
        a.require(ast.unparse(billed.body[0]) == 'resumed_admission_tick = time.perf_counter()' and
                  '_resumed_admission_tick=resumed_admission_tick' in wrapper and
                  "namespace['billed'](name,first,last,label,False)" in wrapper and
                  "assert audit['request_SHA']==sha(RESUME_REQUEST)" in wrapper and
                  request['first_arm_whole_clock_includes_resumed_projection_admission'], 'first resumed arm includes all additional admission/cache work before unchanged native supervision')
        projection = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'projected_records')
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
        a.require(budget['paid_starts'] == request['budget']['paid_starts'] == 40 and
                  budget['paid_outer_seconds'] == request['budget']['paid_outer_seconds'] and not request['budget']['unclosed'] and
                  request['remaining_fixed_reserve'] == dict(starts=budget['remaining_formal_starts'], nominal_seconds=budget['remaining_nominal_seconds'],
                  overhead_seconds=budget['remaining_overhead_seconds']) and budget['remaining_formal_starts'] == 35 and budget['remaining_nominal_seconds'] == 68400,
                  'all closed fees retained, including lost18 slot, and entire remaining worst reserve fits')
        main06 = next(f for f in fee_records if f['label'] == 'main06')
        a.require(main06['conservative_process_starts'] == 4 and main06['exit_code'] == 1 and
                  request['direct_wrapper_processes'] == 1 and request['new_main06_tail_fee_starts'] == 2 and
                  request['failed_main06_four_starts_remain_paid'], 'failed four-start wrapper remains billed; new18 direct wrapper plus child adds two starts')
        value = dict(decision='ACCEPT_NEXT_ONLY_SAME_PE_RESUMPTION', next_native_number=18,
                     never_started_numbers=list(range(18, 43)), request_SHA=a.sha(a.local(args.request)),
                     resumed_wrapper_SHA=request['resumed_wrapper_SHA'], derived_billed_SHA=request['derived_billed_SHA'],
                     current_projection_bindings=request['projection_bindings'], original_summary_SHA=request['original_summary_SHA'],
                     budget=budget, fee_records=fee_records, same_actual_PE_all42_argv_and_native_helpers=True,
                     original_audit_false_missing_return_and_null_whole_clock_preserved=True,
                     first_arm_whole_clock_includes_added_admission=True, offline_projector_exec_only=True,
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
