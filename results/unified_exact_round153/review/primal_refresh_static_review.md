# Conditional complete-Q primal refresh: independent static review

Disposition: `ACCEPT_CONDITIONAL_ONE_COMPLETE_Q_PRIMAL_REFRESH`.
The root must first observe that the final price supplied genuinely new
legal columns whose effect on the retained upper has not been recomputed.
The activation condition is an external research decision, not a test
implemented inside this generic refresh entry. No refresh is authorized
merely because a time allowance remains.

Accepted sequence: complete the already registered per-role support_close,
then, if justified, execute one refresh as that role's **final current
phase**. Do not subsequently pass its result through support_close/refine
without separately correcting those copy-writers' phase-specific refresh
flags. The root explicitly chose this final-phase restriction, so no
active refinement or previously accepted attribution source was changed.

The subsequently read `primal_refresh_plan.json` fixes at most one refresh
per activated role, 180 seconds of Native LP time and a 400-second outer
reservation. The final decision must record the actual new-column trigger
or the reason for skipping. The selected support evidence remains the
preceding support_close result; no support transfer is rerun after refresh.

This review inspected source only. It did not run the refresh, Native,
Optimize, model reads, a proof replay, qualification, reports, or any
unmetered numerical test. No upper improvement is asserted here.

## Source bindings

| Source | SHA256 |
| --- | --- |
| `results/unified_exact_round153/primal_refresh_plan.json` | `286380a3fd0cef557945e0d00747ad932668241781e3fdf63c47d814e7616c86` |
| `scripts/round153_refresh.py` | `e46992a131c56474b84859233130ca37d1318c4e6bd094e41e1935046063a160` |
| `scripts/round153_reports.py` | `9275262b4fd84b9c4b9dcdd4330d568bc05d4cb66d1cf2a111fa5dc5c166671b` |
| `scripts/round153_audit.py` with refresh metadata branch | `ca0abd92e5f10f9f68e22530915d970090d9ad8d2d86bd0d47b9ff41eb06d07c` |
| `scripts/round153_coupled.py` unchanged Master | `7bdb6eb0957f4f9571a0d728ad07e30f055e3a301d0952e7310fc9ce509ee6c9` |
| `scripts/round153_lp.py` reused LP interface | `18280fe215da42838e8e04f1a4cee6ee611685e734d3de31667559f2fb468340` |
| `scripts/round153_exact_worker.py` unchanged runtime helper | `f40ea001ea1a56bc2eb11536aa49574e2606356098751653a365d0030497d40d` |

## Mathematical behavior and qualification

The entry binds the role, exact saved scope and Q SHA to the current
reference. It rejects duplicate columns and rechecks every stock through
the unchanged Master.add/true-stock path. It reads original complete Q,
leaves its original variables free, adds the existing qualified restricted
inventory mixture, and performs one LP optimization. It does not invoke
pricing, create a dual certificate, use an LP objective as a lower, or
change the saved lower/supports. Its upper is on the strengthened LP
value, not a physical routing incumbent or rational primal certificate.

The reused Master.primal check includes complete model residuals and
bounds, lambda mass/nonnegativity, every state marginal, and Fraction
true-completion slack. The 1e-8 completion safety margin and inherited
numerical feasibility policy remain unchanged. The refresh accepts a new
U only when that complete check qualifies and the objective is strictly
smaller than the retained U. Prior lower/supports and all columns remain
in the new result; no artificial Phase-I objective supplies an upper.

The source requires the existing primal qualification's Master and stock
source hashes to match, and requires exact_text_v1 PASS on the unchanged
runtime helper before calling its process-local enable(). This changes
decimal serialization limits, not arithmetic. Invoke refresh **directly
through common.run**: it performs its own qualified enable() call. Do not
send it through exact_worker.execute, whose allowlist intentionally does
not contain this new filename. No worker source change or repeat of the
already qualified Master/oracle is needed.

## Timeout and witness handling

Native statuses OPTIMAL and TIME_LIMIT are admitted for this primal-only
purpose. A TIME_LIMIT with no solution leaves primal=None and retains the
prior upper exactly. A returned but unqualified point also leaves the
prior upper. A feasible qualified point may improve the upper even when
the LP was not solved to optimality; optimality is unnecessary for a
primal upper. Other statuses fail closed rather than create a new bound.
An external outer kill/exception is a retained failed run, not the normal
TIME_LIMIT fallback result; the prior phase remains available.

For an improved U, the entry writes best_primal.json.gz with the original
point, stock identities, weights, true f values and complete qualification
record. The solve folder also retains model/call/return/solution evidence
through the existing LP interface. The fresh plan binds the prior result
SHA and qualification hashes. For an unchanged U, prior_results retains
the ancestor witness chain. The existing final audit's witnesses()
recursion can find either the new witness or the correct prior one.

The final selected endpoint is still independently checked against actual
Q, lambda mass, nonnegativity, all marginals and true f. A saved boolean
alone is not its final qualification. The new metadata branch does not
replace those checks.

## Report and finite-audit integration

The report's direct CLI mapping of `role,label,...` to the refresh phase
is correct. It records primal_refresh_only, the diagnostic RMP objective,
and nullable primal qualification separately from the retained upper.
No-solution gives null qualification; an unqualified returned point gives
false. A displayed RMP objective is not itself an accepted U. The phase's
one outer fee remains the sole additive charge; the helper, LP Runtime,
Work and inherited seconds are not added again. Refresh records are not
listed as new prices or discovery sweeps.

The added finite-audit branch binds the prior SHA, Q and scope, exact
column sequence/count, unchanged lower/supports, no-new-lower/no-pricing
flags, and nonincreasing upper. It binds the saved Native status to the
return record. An updated upper requires a solution, qualified primal,
existing best witness, strict improvement and matching saved objective;
otherwise U must equal the prior U. It adds no Native model read or
Optimize. If no refresh is executed, its result list remains empty.

The fresh refresh result correctly clears local iteration, discovery and
refinement lists while preserving ancestry. The final-phase ordering
restriction above prevents a subsequent copy-writer from mislabeling a
support/refinement phase as this refresh. A future change to that ordering
would require the small metadata ownership correction before execution.

No remaining source-level mathematical or execution blocker was found
within this bounded interface. The actual conditional trigger, registered
cap and outer reservation, serial execution, successful return and final
evidence qualification remain the root's execution responsibilities.
