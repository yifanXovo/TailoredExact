"""Close publication after the one completed local independent raw42 execution.

The superseded raw execution failed only in a later comparison predicate.
All recorded input bytes are rehashed. Stored already-checked47 arm records
are reused; no model/Start/Fraction-row mathematics or solver is rerun.
"""
from pathlib import Path
import argparse, hashlib, json, sys, time, traceback
from round110_independent_final_core import Audit, VIOLATION
from round110_independent_core import ROUND
from round110_independent_final_review import Tee
import round110_independent_final_publication as publication


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--own-audit', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--dll', required=True)
    ap.add_argument('--reports', required=True)
    ap.add_argument('--document', action='append', required=True)
    args = ap.parse_args()
    root, dest = Path(args.root).resolve(), Path(args.out).resolve()
    assert dest.is_relative_to(root/ROUND/'review')
    dest.mkdir(parents=True, exist_ok=False)
    tick, error, result = time.perf_counter(), None, {}
    source = Path(__file__).read_bytes()
    helper_source = Path(publication.__file__).read_bytes()
    (dest/'source_at_execution.py').write_bytes(source)
    (dest/'publication_at_execution.py').write_bytes(helper_source)
    with (dest/'launch.json').open('x', encoding='utf-8') as f:
        json.dump(dict(argv=[sys.executable,*sys.argv], cwd=str(Path.cwd()), explicit_read_root=str(root),
                       source_SHA=hashlib.sha256(source).hexdigest(), Optimize=0, native_environment=0,
                       raw_mathematics_rebuilds=0), f, indent=2)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    stdout = (dest/'stdout.log').open('x', encoding='utf-8', newline='\n')
    stderr = (dest/'stderr.log').open('x', encoding='utf-8', newline='\n')
    sys.stdout, sys.stderr = Tee(old_stdout,stdout), Tee(old_stderr,stderr)
    a = None
    try:
        candidate = json.loads((root/ROUND/'candidate_identity.json').read_text(encoding='utf-8'))
        a = Audit(root,dest,candidate['production_PE_SHA'],dll=args.dll)
        ownpath = a.local(args.own_audit)
        own = a.obj(ownpath)
        original_receipt = a.obj(ownpath.parent/'receipt.json')
        a.require(own['decision'] == 'HOLD' and original_receipt['exit_code'] == 1 and
                  original_receipt['audit_SHA'] == a.sha(ownpath) and own['stage'] == 'BLOCKED' and
                  own['mode'] == 'final' and own['explicit_read_root'] == str(root),
                  'actual original local raw execution failed only at publication closure and was retained')
        known_error = 'AssertionError: independent publication separate actual rc0 return evidence: True / False'
        a.require(own['error'].rstrip().endswith(known_error) and 'publication.compare' in own['error'] and
                  'round110_independent_final_publication.py' in own['error'],
                  'exact concrete superseded comparison predicate, never a mathematical error')
        a.require(len(own['own_actual_arms']) == 42 and len(own['qualification']['functional_arms']) == 5 and
                  own['all42_native_attempts_reconstructed'] and own['qualified_formal_arms'] == 41 and
                  not own['all42_valid_formal'] and own['selection']['stage'] == 'BLOCKED' and
                  own['selection']['blocking_reasons'] == [VIOLATION] and len(own['formal_clock_evidence']) == 42,
                  'completed own47 mathematical records and exact strict42 clock adjudication already exist')
        filenames = {
            'round110_independent_final_review.py':'source_at_execution.py',
            'round110_independent_core.py':'core_at_execution.py',
            'round110_independent_final_core.py':'final_core_at_execution.py',
            'round110_independent_cold_rejection.py':'cold_rejection_at_execution.py',
            'round110_independent_scoped_rejection.py':'scoped_rejection_at_execution.py',
            'round110_independent_final_publication.py':'publication_at_execution.py',
        }
        for name, captured in filenames.items():
            a.require(a.sha(ownpath.parent/captured) == own['reviewer_source_bindings'][name],
                      'actual superseded execution source snapshot '+name)
            if name != 'round110_independent_final_publication.py':
                a.require(a.sha(Path(__file__).with_name(name)) == own['reviewer_source_bindings'][name],
                          'all raw-science reviewer sources unchanged since completed execution '+name)
        old_helper = a.txt(ownpath.parent/'publication_at_execution.py')
        new_helper = helper_source.decode('utf-8')
        old_statement = "            require_equal(scalar(r['actual_normal_return_from_independent_rc_source']), absent, 'separate actual rc0 return evidence')"
        new_statement = """            independently_proved = scalar(r['actual_normal_return_from_independent_rc_source'])
            a.require(isinstance(independently_proved, bool) and (not absent or independently_proved) and
                      (not independently_proved or arm['normal_completion']['returncode'] == 0),
                      'separate actual rc0 proof may coexist with returned event; every missing event requires independent proof')"""
        a.require(old_helper.count(old_statement) == 1 and old_helper.replace(old_statement,new_statement).splitlines() == new_helper.splitlines(),
                  'only exact wrong return-proof equivalence replaced; all other publication obligations unchanged')
        rehashed = 0
        helper_path = (root/ROUND/'review/round110_independent_final_publication.py').relative_to(root).as_posix()
        for name, digest in own['read_bindings'].items():
            if name == helper_path:
                a.require(digest == own['reviewer_source_bindings']['round110_independent_final_publication.py'],
                          'superseded helper bytes precisely identified and retained')
                continue
            path = Path(name)
            path = path if path.is_absolute() else root/path
            a.require(a.sha(path) == digest, 'every previously checked actual raw/model/proof byte unchanged '+name)
            rehashed += 1
        a.require(a.module_bindings == own['module_bindings'], 'same separately trusted independent mathematical kernels')
        recomputed_selection = a.decision['selection'](own['own_actual_arms'],own['input_eligibility'])
        a.require(recomputed_selection == own['selection'], 'all fixed pair/stage arithmetic agrees using already checked immutable arm records')
        published = publication.compare(a,own,a.local(args.reports),[a.local(name) for name in args.document])
        result = dict(decision='ACCEPT_INDEPENDENT_BLOCKED_COMPLETE_RAW_PANEL',stage='BLOCKED',resumption_allowed=False,
                      acceptance_of_frozen_performance_panel=False, production_PE_SHA=own['production_PE_SHA'], DLL_SHA=own['DLL_SHA'],
                      own_raw_audit_path=ownpath.relative_to(root).as_posix(),own_raw_audit_SHA=a.sha(ownpath),
                      own_raw_execution_receipt_SHA=a.sha(ownpath.parent/'receipt.json'),
                      own_raw_completed_checks=own['completed_checks'],all42_native_attempts_reconstructed=True,qualified_formal_arms=41,
                      all42_valid_formal=False,original_raw_execution_exit_code_preserved=1,
                      superseded_error='publication-only wrong equivalence between rc0 proof and missing returned event',
                      completed_raw_mathematics_reused=True,raw_mathematics_rebuilds_this_closure=0,
                      every_recorded_raw_model_proof_byte_rehashed=True,rehashed_original_bindings=rehashed,
                      selection=recomputed_selection,budget=own['budget'],formal_clock_evidence=own['formal_clock_evidence'],
                      publication_and_narrative=published,Optimize=0,native_environment=0,production_edits=0)
    except Exception:
        error=traceback.format_exc()
        result.update(decision='HOLD',error=error,Optimize=0,native_environment=0,raw_mathematics_rebuilds_this_closure=0)
    result.update(completed_checks=a.checks if a else 0,read_bindings=a.reads if a else {},explicit_read_root=str(root),
                  no_original_root_fallback=True,source_SHA=hashlib.sha256(source).hexdigest(),
                  publication_source_SHA=hashlib.sha256(helper_source).hexdigest())
    with (dest/'audit.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    print(json.dumps(dict(decision=result['decision'],completed_checks=result['completed_checks'],error=error)),flush=True)
    sys.stdout.flush();sys.stderr.flush()
    sys.stdout,sys.stderr=old_stdout,old_stderr
    stdout.close();stderr.close()
    with (dest/'receipt.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(exit_code=int(error is not None),engineering_elapsed_seconds=time.perf_counter()-tick,
                       source_SHA=hashlib.sha256(source).hexdigest(),publication_source_SHA=hashlib.sha256(helper_source).hexdigest(),
                       audit_SHA=hashlib.sha256((dest/'audit.json').read_bytes()).hexdigest(),
                       stdout_SHA=hashlib.sha256((dest/'stdout.log').read_bytes()).hexdigest(),
                       stderr_SHA=hashlib.sha256((dest/'stderr.log').read_bytes()).hexdigest(),
                       Optimize=0,native_environment=0,raw_mathematics_rebuilds=0,cwd=str(Path.cwd()),explicit_read_root=str(root)),f,indent=2)
        f.write('\n')
    if error:sys.exit(1)


if __name__ == '__main__':main()
