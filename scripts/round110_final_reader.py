"""Offline reconstruction retaining the actual final full-clock violation.

This version does not admit an over-cap arm. It preserves its mathematical
evidence and exact clock, makes the affected formal pair UNEVALUABLE, and
forces BLOCKED. No frozen reader, source, raw observation or cap is changed.
"""
import argparse
import inspect
from pathlib import Path
import round110_reader as frozen
import round110_scoped_evidence as current
import round109_decisions as inherited_decision

VIOLATION = 'ARM42_FULL_CLOCK_EXCEEDS_FROZEN_3600_SECOND_CAP'
TIMING_SHA = '5ad5f09e36589b1b1c9e76e5557a29901a3630bde6591f260387e7915430655d'
original_endpoint = frozen._inherited_endpoint
original_pair = frozen.decision.pair
original_selection = frozen.decision.selection


def clock_gate(launch, panel, seconds, timing, directory, formal):
    if seconds <= panel['cap_seconds']:
        return
    assert formal and (launch['number'], launch['id'], launch['seed'], launch['arm']) == (42, 'G100-R2', 1, 'M-B')
    assert panel['cap_seconds'] == 3600 and seconds == 3600.7215734999627
    assert frozen.sha(directory/'whole_arm_receipt.json') == TIMING_SHA
    audit_end = frozen.read(directory/'postexit_audit_receipt.json')
    native_end = frozen.read(directory/'native_end_receipt.json')
    assert native_end['complete_seconds_until_native_end'] < 3600
    assert 3600 < audit_end['complete_seconds_until_audit_end'] <= seconds
    assert audit_end['audit_passed'] and audit_end['audit_SHA'] == timing['audit_SHA']


source = inspect.getsource(original_endpoint)
needle = "assert t<=p['cap_seconds'],('complete arm exceeded preregistered cap',t,p['cap_seconds'])"
assert source.count(needle) == 1
namespace = dict(original_endpoint.__globals__, clock_gate=clock_gate)
exec(compile(source.replace(needle, 'clock_gate(launch,p,t,timing,d,formal)'),
             str(Path(__file__))+'::retain_invalid_full_clock', 'exec'), namespace)
mathematical_endpoint = namespace['endpoint']


def retained_endpoint(root, launch, ident, directory, journal, formal):
    result = mathematical_endpoint(root, launch, ident, directory, journal, formal)
    arm = result['arm']
    valid = not formal or arm['complete_seconds'] <= launch['cap_seconds']
    arm.update(full_clock_within_frozen_cap=valid,
               formal_performance=formal and valid,
               formal_protocol_qualified=valid,
               full_clock_cap_excess_seconds=max(0., arm['complete_seconds']-launch['cap_seconds']) if formal else 0.)
    if not valid:
        arm['formal_protocol_failure'] = VIOLATION
    return result


def pair(candidate, control):
    value = original_pair(candidate, control)
    if any(a.get('formal_protocol_qualified') is False for a in (candidate, control)):
        value.update(descriptive_objective_classification=value['classification'],
                     descriptive_severe_regression=value['severe_regression'],
                     classification='UNEVALUABLE', evaluable=False, severe_regression=None,
                     basis=VIOLATION, formal_protocol_qualified=False)
    return value


def selection(arms, roles, eligibility, unresolved=()):
    violations = [a for a in arms if a.get('formal_protocol_qualified') is False]
    result = original_selection(arms, roles, eligibility,
                                list(unresolved)+([VIOLATION] if violations else []))
    result.update(completed_native_formal_attempts=len(arms),
                  qualified_formal_arms=len(arms)-len(violations),
                  formal_clock_violations=[dict(id=a['id'],seed=a['seed'],arm=a['arm'],
                                               complete_seconds=a['complete_seconds'],cap_seconds=a['cap_seconds'],
                                               excess_seconds=a['full_clock_cap_excess_seconds']) for a in violations])
    return result


frozen._inherited_endpoint = retained_endpoint
frozen.numerical = current
frozen.decision.pair = pair
inherited_decision.pair = pair
frozen.decision.selection = selection

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    summary = frozen.rebuild(args.root, args.out)
    selected = frozen.read(args.out/'selection_decision.json')
    summary.update(primary_reader_entry_SHA=frozen.sha(Path(__file__)),
                   scoped_evidence_module_SHA=frozen.sha(args.root/'scripts/round110_scoped_evidence.py'),
                   native_normal_formal_attempts=summary['formal_arms'],
                   qualified_formal_arms=selected['qualified_formal_arms'],
                   formal_clock_violations=selected['formal_clock_violations'],
                   formal_clock_failure_preserved=True)
    import round110_report_qualifiers as qualifiers
    qualifiers.write(args.out/'summary.json', summary)
    summary = qualifiers.annotate(args.out, Path(__file__).resolve())
    print(frozen.json.dumps(summary, allow_nan=False))
    if args.compare:
        print(frozen.json.dumps(frozen.compare(args.compare, args.out), allow_nan=False))
