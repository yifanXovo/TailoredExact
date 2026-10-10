"""Final raw reconstruction with the actual strict arm42 cap breach retained.

The admitted core and shared scientific kernel stay byte-identical. This
separate final-only adapter replaces one early timing abort with a recorded
blocking fault so all mathematical records can still be independently read.
It cannot qualify an over-cap formal arm or sign performance admission.
"""
from pathlib import Path
import ast, math
import round110_independent_core as admitted

ROUND = admitted.ROUND
VIOLATION = 'ARM42_FULL_CLOCK_EXCEEDS_FROZEN_3600_SECOND_CAP'
BASE_CORE_SHA = '2b01ac7b1d9f1cbe8da97a18ea007698ac9f584fd8c8e9735b1a46736d8f093f'
TIMING_SHA = '5ad5f09e36589b1b1c9e76e5557a29901a3630bde6591f260387e7915430655d'


class Audit(admitted.Audit):
    def _load(self):
        self.clock_evidence = {}
        super()._load()
        self.require(self.sha(Path(admitted.__file__)) == BASE_CORE_SHA,
                     'exact previously admitted current-call adapter unchanged')
        path = self.root/admitted.OLD_REVIEW/'round109_independent_kernel.py'
        tree = ast.parse(self.txt(path))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'audit_arm')
        self.require(isinstance(function.body[0], ast.If) and 'independent_main06_arm' in ast.unparse(function.body[0]),
                     'same historical tuple dispatch removed as admitted core')
        function.body = function.body[1:]
        changed = 0
        for statement in function.body:
            if (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and
                    isinstance(statement.value.func, ast.Name) and statement.value.func.id == 'require' and
                    len(statement.value.args) == 2 and 'complete arm within original cap' in ast.unparse(statement.value.args[1])):
                condition = statement.value.args[0]
                self.require(ast.unparse(condition) == "0 <= offset + 1e-09 and complete <= launch['cap_seconds']",
                             'exact single whole-clock predicate recognized')
                statement.value.args[0] = condition.values[0]
                statement.value.args[1] = ast.parse("'complete clock retains all native/pre/post work '+label", mode='eval').body
                changed += 1
        self.require(changed == 1, 'only early complete-clock abort deferred to strict final blocking adjudication')
        ast.fix_missing_locations(function)
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path)+'::retain_actual_clock_failure', 'exec'), self.functions)
        original_pair = self.decision['pair']
        original_selection = self.decision['selection']

        def pair(candidate, control):
            result = original_pair(candidate, control)
            if any(arm.get('formal_protocol_qualified') is False for arm in (candidate, control)):
                result.update(descriptive_objective_classification=result['classification'],
                              descriptive_severe_regression=result['severe_regression'],
                              classification='UNEVALUABLE', evaluable=False, severe_regression=None,
                              basis=VIOLATION, formal_protocol_qualified=False)
            return result

        original_selection.__globals__['pair'] = pair
        self.decision['pair'] = pair

        def selection(arms, eligibility, unresolved=()):
            failures = [arm for arm in arms if arm.get('formal_protocol_qualified') is False]
            result = original_selection(arms, eligibility, list(unresolved)+([VIOLATION] if failures else []))
            seeds = list(result['seed1_pairs'].values())
            evaluated_nonloss = sum(p['evaluable'] and p['classification'] != 'LOSS' for p in seeds)
            assessed = len(seeds) == 3 and all(p['evaluable'] for p in seeds)
            result.update(completed_native_formal_attempts=len(arms), qualified_formal_arms=len(arms)-len(failures),
                          all42_valid_formal=not failures and len(arms) == 42,
                          formally_evaluable_seed_pairs=sum(p['evaluable'] for p in seeds),
                          seed1_nonLOSS=evaluated_nonloss, formally_evaluable_seed_nonLOSS=evaluated_nonloss,
                          formal_Seed1_sensitivity_assessed=assessed,
                          formal_clock_violations=[dict(id=arm['id'], seed=arm['seed'], arm=arm['arm'],
                              complete_seconds=arm['complete_seconds'], cap_seconds=arm['cap_seconds'],
                              excess_seconds=arm['full_clock_cap_excess_seconds']) for arm in failures])
            if not assessed:
                result['conditions']['minimum_two_seed_nonLOSS'] = None
                result['conditions']['no_severe_seed_P'] = False if result['seed1_severe_regressions'] else None
                result['conditions']['no_WIN_to_LOSS_flip'] = False if result['seed0_WIN_to_seed1_LOSS'] else None
            if result['stage'] == 'BLOCKED':
                result['unassessed_support_conditions'] = result['reason_codes']
                result['reason_codes'] = []
            return result

        self.decision['selection'] = selection

    def arm(self, launch, identity, formal):
        result, models, q = super().arm(launch, identity, formal)
        if not formal:
            return result, models, q
        seconds = result['complete_seconds']
        cap = launch['cap_seconds']
        upper = seconds if seconds is not None else result['complete_seconds_interval'][1]
        self.require(math.isfinite(upper) and upper > 0, 'actual complete formal clock or recorded outward upper bound')
        valid = upper <= cap
        result.update(cap_seconds=cap, full_clock_within_frozen_cap=valid, formal_performance=valid,
                      formal_protocol_qualified=valid, full_clock_cap_excess_seconds=max(0., upper-cap))
        evidence = dict(number=launch['number'], id=launch['id'], seed=launch['seed'], arm=launch['arm'],
                        complete_seconds=seconds, complete_seconds_interval=result.get('complete_seconds_interval'),
                        cap_seconds=cap, formal_protocol_qualified=valid)
        if not valid:
            self.require([launch['number'], launch['id'], launch['seed'], launch['arm']] == [42, 'G100-R2', 1, 'M-B'] and
                         cap == 3600 and seconds == 3600.7215734999627,
                         'only actual known arm42 whole-clock failure retained, never admitted')
            directory = self.local(launch['destination'])
            whole = self.obj(directory/'whole_arm_receipt.json')
            native_end = self.obj(directory/'native_end_receipt.json')
            audit_end = self.obj(directory/'postexit_audit_receipt.json')
            self.require(self.sha(directory/'whole_arm_receipt.json') == TIMING_SHA and
                         whole['complete_seconds'] == seconds and
                         native_end['completion_SHA'] == self.sha(directory/'completion.json') and
                         native_end['observations_SHA'] == self.sha(directory/'observations.json') and
                         audit_end['audit_SHA'] == whole['audit_SHA'] == self.sha(directory/'audit.json') and audit_end['audit_passed'],
                         'all exact original clock receipts bind current normal native result and required audit')
            self.require(native_end['complete_seconds_until_native_end'] < cap <
                         audit_end['complete_seconds_until_audit_end'] <= seconds,
                         'required original postaudit itself crossed cap; no final-write trimming can repair it')
            fee = self.out/'fees/seed03'
            receipt = self.obj(fee/'receipt.json')
            self.require(receipt['exit_code'] == 1 and receipt['conservative_process_starts'] == 3 and
                         receipt['actual_native_children_with_launch'] == 2 and
                         'AssertionError: full arm exceeded frozen cap' in self.txt(fee/'failure.txt'),
                         'actual enclosing failed wrapper and every charged start preserved')
            result['formal_protocol_failure'] = VIOLATION
            evidence.update(blocking_reason=VIOLATION, native_end_seconds=native_end['complete_seconds_until_native_end'],
                            required_postaudit_end_seconds=audit_end['complete_seconds_until_audit_end'],
                            excess_seconds=seconds-cap, whole_receipt_SHA=TIMING_SHA,
                            raw_native_completion_within_cap=result['normal_completion']['within_cap'],
                            raw_audit_passed=True, clock_trimmed=False, performance_rerun=False)
        self.clock_evidence[launch['number']] = evidence
        return result, models, q
