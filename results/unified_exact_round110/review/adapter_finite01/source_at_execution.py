"""Bounded offline checks of the R110 review adapter; not admission."""
from pathlib import Path
import argparse, hashlib, json, math, sys, time, traceback
from round110_independent_core import Audit, ROUND


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    root, dest = Path(args.root).resolve(), Path(args.out).resolve()
    assert dest.is_relative_to(root/ROUND/'review')
    dest.mkdir(parents=True, exist_ok=False)
    started, error, cases = time.perf_counter(), None, []
    source = Path(__file__).read_bytes()
    def save(name, value):
        with (dest/name).open('x', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write('\n')
    save('launch.json', dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
                            source_SHA=hashlib.sha256(source).hexdigest(),
                            Optimize=0, native_environment=0))
    (dest/'source_at_execution.py').write_bytes(source)
    (dest/'core_at_execution.py').write_bytes(Path(__file__).with_name('round110_independent_core.py').read_bytes())
    try:
        a = Audit(root, dest, 'not-a-production-identity')
        assert 'independent_main06_arm' not in a.functions['audit_arm'].__code__.co_names
        assert a.functions['independent_numerical_recovery']({}, True) is None
        cases.append('historical P15/P17 tuple adapters have no current authority')
        groups = [(r[8], r[9]) for r in a.decision['PANEL']]
        groups += [(cap, arms) for role, cap, arms in a.decision['SEED_CHECKS']]
        paid = [dict(conservative_process_starts=13, outer_seconds=650., qualification=True)]
        reserve = a.budget(paid, groups, 1800.)
        assert reserve['remaining_formal_starts'] == 57 and reserve['remaining_nominal_seconds'] == 88200
        assert reserve['max_starts'] == 96 and reserve['max_outer_seconds'] == 110000
        cases.append('new resource ceilings reserve exact57/88200 without early-stop credit')
        for label, damaged in [
                ('qualification starts', [dict(conservative_process_starts=21, outer_seconds=650., qualification=True)]),
                ('qualification seconds', [dict(conservative_process_starts=13, outer_seconds=2000.00001, qualification=True)]),
                ('total starts', [dict(conservative_process_starts=40, outer_seconds=650., qualification=False)]),
                ('total seconds', [dict(conservative_process_starts=13, outer_seconds=21801., qualification=False)])]:
            try:
                a.budget(damaged, groups, 1800.)
            except AssertionError:
                cases.append('reject excess '+label)
            else:
                raise AssertionError('invalid reserve accepted '+label)
        def arm(name, seconds, interval=None):
            result = dict(id='finite', seed=0, arm=name, U=0., L=0., gap=0., certificate=True,
                          certificate_qualified=True, numbers_qualified=True, complete_seconds=seconds)
            if interval is not None:
                result['complete_seconds_interval'] = interval
            return result
        compare = a.decision['pair']
        exact = compare(arm('M-B', 100.), arm('P-GRB', 200.))
        assert exact['classification'] == 'WIN' and not exact['severe_regression']
        cases.append('original exact certified time materiality unchanged')
        bounded = compare(arm('M-B', None, [110., 120.]), arm('P-GRB', None, [600., 650.]))
        assert bounded['classification'] == 'WIN' and bounded['entire_time_rectangle_classification_invariant']
        assert bounded['candidate_seconds'] is None and bounded['control_seconds'] is None
        assert bounded['certified_time_ratio'] is None
        cases.append('bounded times preserve null exact clocks and invariant entire rectangle')
        uncertain = compare(arm('M-B', None, [169., 171.]), arm('P-GRB', 200.))
        assert uncertain['classification'] == 'UNEVALUABLE' and uncertain['severe_regression'] is None
        cases.append('interval crossing material threshold stays UNEVALUABLE')
        value = dict(decision='ACCEPT_ADAPTER_FINITE_ONLY', checks=cases, reserve=reserve,
                     inherited_module_bindings=a.module_bindings, read_bindings=a.reads,
                     independent_performance_admission_signed=False, Optimize=0, native_environment=0)
    except Exception:
        error = traceback.format_exc()
        value = dict(decision='HOLD', error=error, checks=cases, Optimize=0, native_environment=0)
    save('audit.json', value)
    save('receipt.json', dict(exit_code=int(error is not None), cwd=str(Path.cwd()),
                              engineering_elapsed_seconds=time.perf_counter()-started,
                              source_SHA=hashlib.sha256(source).hexdigest(),
                              audit_SHA=hashlib.sha256((dest/'audit.json').read_bytes()).hexdigest(),
                              Optimize=0, native_environment=0))
    print(json.dumps(dict(decision=value['decision'], checks=len(cases), error=error)))
    if error:
        sys.exit(1)


if __name__ == '__main__':
    main()
