"""Bounded current proof and next-only continuation admission; zero native."""
from pathlib import Path
import argparse, hashlib, json, sys, time, traceback
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
    def save(name, obj):
        with (dest/name).open('x', encoding='utf-8', newline='\n') as f:
            json.dump(obj, f, indent=2, allow_nan=False)
            f.write('\n')
    save('launch.json', dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
                            explicit_read_root=str(root), source_SHA=hashlib.sha256(source).hexdigest(),
                            Optimize=0, native_environment=0))
    try:
        identity_path = root/ROUND/'campaign/identity.json'
        identity = json.loads(identity_path.read_text(encoding='utf-8-sig'))
        a = Audit(root, dest, identity['candidate_binary_sha256'])
        request = a.obj(a.local(args.request))
        admission = a.obj(a.out/'review/performance_admission.json')
        candidate = a.obj(a.out/'candidate_identity.json')
        a.require(request['schema'] == 'round110-next-only-same-pe-resumption-v1', 'next-only continuation class')
        a.require(admission['decision'] == 'ACCEPT' and request['production_PE_SHA'] == admission['production_PE_SHA'] == a.pe_sha and
                  request['DLL_SHA'] == admission['DLL_SHA'] == identity['dll_sha256'], 'same original admitted final PE/DLL')
        a.require(request['campaign_identity_SHA'] == admission['campaign_identity_SHA'] == a.sha(identity_path) and
                  request['candidate_identity_SHA'] == admission['candidate_identity_SHA'] == a.sha(a.out/'candidate_identity.json'),
                  'frozen original all42 campaign and candidate identities unchanged')
        a.require(a.sha(a.local(identity['prereg']['candidate_binary'])) == a.pe_sha and
                  candidate['full_argv'] == admission['all42_complete_argv'] == [l['command'] for l in identity['launches']],
                  'actual final PE bytes and all42 complete argv unchanged')
        a.require(request['performance_helpers'] == identity['helpers'] and
                  request['performance_runner_SHA'] == identity['runner_sha256'], 'same original performance helpers and runner inventory')
        for path, digest in {**identity['source_hashes'], **identity['helpers']}.items():
            a.require(a.sha(a.root/path) == digest, 'every current production/performance source unchanged '+path)
        policy = a.obj(a.out/'evidence_policy.json')
        for label, path in [('qualified_evidence_module_SHA', 'scripts/round110_evidence.py'),
                            ('qualified_reader_SHA', 'scripts/round110_reader.py')]:
            a.require(request[label] == policy['raw_bindings'][path] == a.sha(root/path), 'same pre-frozen offline evidence predicate '+path)
        rejection_path = a.local(request['current_rejection_path'])
        active = a.obj(rejection_path)
        proof_path = a.local(request['independent_audit_path'])
        proof = a.obj(proof_path)
        a.require(a.sha(rejection_path) == request['current_rejection_SHA'] and
                  a.sha(proof_path) == request['independent_audit_SHA'] == active['independent_audit_SHA'] and
                  a.local(active['independent_audit_path']) == proof_path and proof['decision'] == 'ACCEPT_CURRENT_CALL_REJECTION',
                  'activated exact independently signed current rejection')
        a.require(active['key'] == proof['current_key'] == [15, 'G50-C1', 0, 'P-GRB'] and
                  proof['campaign_identity_SHA'] == request['campaign_identity_SHA'] and
                  active['raw_bindings'] == proof['raw_bindings'], 'current call and original raw bindings unchanged since exact proof')
        for path, digest in proof['raw_bindings'].items():
            a.require(a.sha(a.local(path)) == digest, 'original current fault/raw flags/clocks immutable '+path)
        a.require(active['model_SHA'] == proof['model_SHA'] and active['time'] == proof['time'] and
                  active['exact_vector_SHA'] == proof['exact_vector_SHA'] and
                  a.sha(a.local(active['exact_vector_path'])) == proof['exact_vector_SHA'], 'same exact vector/model/original clock proof')
        readback_path = a.out/'campaign/reader_recovery/cold15_readback01/readback.json'
        readback = a.obj(readback_path)
        projected = readback['arm']
        a.require(projected['U'] == proof['own_U'] > 0 and projected['L'] == 0 and
                  projected['gap'] == projected['U'] and projected['certificate'] is False and
                  projected['complete_seconds'] is None and projected['complete_seconds_interval'] == proof['complete_seconds_interval'] and
                  projected['journal_return_missing'] is False and readback['journal_returned'] == 1 and
                  readback['rejected_claims'] == 4 and readback['native_raw_flags_preserved'] and
                  not projected['native_call_bounds_mathematically_qualified'], 'actual bounded offline projection retains positive own open state and all rejected claims')
        a.require(readback['reader_SHA'] == request['qualified_reader_SHA'] and
                  readback['evidence_SHA'] == request['qualified_evidence_module_SHA'] and
                  readback['Optimize'] == readback['native_environment'] == 0, 'actual projection used frozen zero-native readers')
        execution = a.out/'engineering/cold15_readback01'
        receipt = a.obj(execution/'receipt.json')
        a.require(receipt['exit_code'] == 0 and receipt['conservative_solver_starts'] == 0 and
                  receipt['stdout_SHA'] == a.sha(execution/'stdout.log') and receipt['stderr_SHA'] == a.sha(execution/'stderr.log'),
                  'actual bounded projection execution/source/streams closed successfully')
        for path, digest in receipt['sources'].items():
            a.require(a.sha(root/path) == digest, 'actual projection source binding '+path)
        records_path = a.out/'campaign/summary.jsonl'
        a.require(a.sha(records_path) == request['original_summary_SHA'] and request['original_summary_unchanged'],
                  'original raw summary bytes retained including invalid original endpoint')
        records = [json.loads(line) for line in a.txt(records_path).splitlines()]
        a.require(request['completed_native_numbers'] == [r['number'] for r in records] == list(range(1, 16)) and
                  request['next_native_number'] == 16 and request['never_started_numbers'] == list(range(16, 43)), 'exact next-only completed/unstarted partition')
        for rec, launch in zip(records, identity['launches']):
            d = a.local(launch['destination'])
            comp, raw_audit = a.obj(d/'completion.json'), a.obj(d/'audit.json')
            a.require(rec['number'] == launch['number'] and rec['id'] == launch['id'] and rec['arm'] == launch['arm'] and
                      rec['completion'] == comp and rec['audit_passed'] == raw_audit['passed'] is True and
                      comp['returncode'] == 0 and comp['stop_reason'] == 'normal_return' and comp['within_cap'],
                      'all fifteen original native processes returned; no rerun needed')
        remaining = identity['launches'][15:]
        a.require(all(not a.local(l['destination']).exists() for l in remaining), 'every arm16–42 remains never started')
        # The unmodified runner compares only records of the just-completed id
        # and Seed, after supervision. None of the remaining roles reuses C1/S0.
        a.require(all((l['id'], l['seed']) != ('G50-C1', 0) for l in remaining),
                  'retained original invalid endpoint cannot trigger another role comparison')
        runner = a.txt(root/'scripts/round110_campaign.py')
        a.require("if r['id']==launch['id'] and identity['launches'][r['number']-1]['seed']==launch['seed']" in runner and
                  'rec=supervised_run(launch,identity,arm_tick)' in runner, 'original cross-arm check remains offline after supervision')
        groups = []
        for group in dict.fromkeys(l['group_number'] for l in remaining):
            launches = [l for l in remaining if l['group_number'] == group]
            groups.append((launches[0]['cap_seconds'], tuple(l['arm'] for l in launches)))
        fee_records = fees(a)
        budget = a.budget(fee_records, groups, overhead=120*len(groups))
        requested_budget = request['budget']
        a.require(not requested_budget['unclosed'] and requested_budget['paid_starts'] == budget['paid_starts'] and
                  requested_budget['paid_outer_seconds'] == budget['paid_outer_seconds'] and
                  requested_budget['qualification_starts'] == budget['qualification_starts'] and
                  requested_budget['qualification_seconds'] == budget['qualification_outer_seconds'], 'all closed original outer fees billed once')
        a.require(request['remaining_fixed_reserve'] == dict(starts=budget['remaining_formal_starts'],
                  nominal_seconds=budget['remaining_nominal_seconds'], overhead_seconds=budget['remaining_overhead_seconds']) and
                  budget['remaining_formal_starts'] == 37 and budget['remaining_nominal_seconds'] == 72000,
                  'entire remaining fixed panel worst reserve fits original ceiling')
        a.require(all(request[key] for key in ('no_online_UB_Start_cut_cache_transfer', 'no_raw_flag_or_clock_rewrite',
                  'no_performance_helper_change', 'no_solver_rerun')), 'next-only scope explicitly retains original raw/native contract')
        value = dict(decision='ACCEPT_NEXT_ONLY_SAME_PE_RESUMPTION', next_native_number=16,
                     never_started_numbers=list(range(16, 43)), budget=budget, fee_records=fee_records,
                     request_SHA=a.sha(a.local(args.request)), current_rejection_SHA=a.sha(rejection_path),
                     independent_current_proof_SHA=a.sha(proof_path), bounded_projection_SHA=a.sha(readback_path),
                     original_summary_SHA=a.sha(records_path), production_PE_SHA=a.pe_sha,
                     candidate_identity_SHA=request['candidate_identity_SHA'], campaign_identity_SHA=request['campaign_identity_SHA'],
                     no_solver_rerun=True, no_summary_projection_or_raw_edits_required=True,
                     original_wrong_endpoint_retained_as_raw=True, current_qualified_P15_U=proof['own_U'],
                     current_qualified_P15_L=0., current_qualified_P15_certificate=False,
                     complete_seconds=None, complete_seconds_interval=proof['complete_seconds_interval'],
                     read_bindings=a.reads, completed_checks=a.checks, explicit_read_root=str(root),
                     Optimize=0, native_environment=0)
    except Exception:
        error = traceback.format_exc()
        value = dict(decision='HOLD', error=error, Optimize=0, native_environment=0)
    save('audit.json', value)
    save('receipt.json', dict(exit_code=int(error is not None), engineering_elapsed_seconds=time.perf_counter()-tick,
                             source_SHA=hashlib.sha256(source).hexdigest(),
                             audit_SHA=hashlib.sha256((dest/'audit.json').read_bytes()).hexdigest(), Optimize=0, native_environment=0))
    print(json.dumps(dict(decision=value['decision'], completed_checks=value.get('completed_checks'), error=error)))
    if error:
        sys.exit(1)

if __name__ == '__main__':
    main()
