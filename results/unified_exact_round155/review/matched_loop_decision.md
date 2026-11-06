# Matched-pool result and substantive continuation decision

All four declared short loops completed twelve iterations from their own copy
of the exact final R154 pool, supports and Q. Every accepted upper remained
qualified; changes below 1e-10 in this comparison are reported as numerical
tail differences, not a scientific gain or a relaxed stopping target.

| Domain / rule | Outer seconds | Distinct new columns | True negative new columns | New columns recorded with later weight >1e-10 | Material U/L advance |
|---|---:|---:|---:|---:|---|
| K35 first | 248.108757 | 13 | 12 | 0 | None |
| K35 bounded | 394.260630 | 156 | 155 | 0 | None |
| NC20 first | 129.536966 | 12 | 12 | 0 | None |
| NC20 bounded | 190.989626 | 109 | 109 | 0 | None |

The bounded rule uses the same inherited strengthened residual with NodeLimit
256 and PoolSolutions 20, at the same offline 120-second price allowance. It
does not identify the most negative residual with the lowest original price.
The original price, true reduced cost, target violation and duplicate status
are saved for every returned column. More columns per paid second is the
observed advantage; better used columns or a tighter complete hull is not yet
an observed advantage. Selection-LP Optimize counts are zero in both arms.
The large RMP category includes full numerical/true-completion checks and
necessary output, as well as its separately reported Native solve time.

The separate arithmetic and reconstruction reader passed four phases, all 48
price records, 15 primal checks and 16 actual model reads, with zero Optimize.
Its complete current-column minimum checks cover first/last/every16 and every
lower-improving direction; it does not falsely claim an exhaustive minimum
recalculation at every non-improving step. Every step's full Q residual, actual
price recovery, support transport and feedback were checked. The two inherited
retained upper witnesses were found and checked on the full Q.

Each arm's entire support set was subsequently replayed separately in the
original free Q. A second zero-Optimize reader checks exact equality to that
Q plus the declared rows, original variable bounds/objective, the complete
dual residual and the saved numerical LP primal. Those LP objectives are not
substituted for a complete-hull upper. Their last-bit lower changes do not
alter the above scientific conclusion. All replay and readback costs are
additional paid work, not hidden inside a pricing time or charged twice.

Choose the bounded rule for one substantive continuation in each domain. Both
inherit their own bounded-arm support replay; neither receives the competing
first arm's new columns. Reserve 28800 outer seconds per domain, with a 28200
second loop capacity and no iteration cap. The difference accommodates final
RMP refresh, endpoint evidence and process shutdown. The requested hull width
remains 1e-4. Deterministic pricing rules, original Q and source qualification
remain unchanged. Basis files are reused when present at the input phase;
starting from a support-replay artifact may require an initial fresh RMP solve,
whose full cost is included.

This is an opportunity to test sustained feedback, not a decision to declare
saturation after twelve steps. Stop at a qualified target, a concrete unresolved
price/qualification condition, or the finite offline phase allowance. Review
actual accumulated columns, weights and intervals before a single targeted
level/stabilization adjustment if stagnation persists. An early incomplete
price or failed selected direction is not evidence against the entire hull.
The eight-hour capacities can be reassigned only with an explicit evidence-based
phase decision. There is no new runtime dispatch by role name or elapsed time.

The remaining three complete E-panel arms and final audit margin remain
reserved within the 172800-second total. See deep_plan.json for the exact source,
witness, admission and budget bindings written before the substantive runs.
