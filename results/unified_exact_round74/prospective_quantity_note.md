# Conditional quantity/vehicle hypothesis, not admitted or implemented

This note records deductions made while the frozen D7 experiment runs. It
does not select a new candidate, allocate experiments, or assume that JDS-X
will fail. The complete four-arm result must decide whether further primal
repair or a longer validation is more useful. Literature scope is in
literature_notes.md; generic quantity adjustment and pair insertion are known.

The archived R73 JDS-X starter uses17/23/6/0 visits on its four vehicles.
This suggests examining served-node quantity and assignment changes, but an
unused vehicle alone proves neither a feasible transfer nor an improving F.
The current constructor cannot revise served quantities; DS-X only generates
limited cross-route tail moves. Fully checking that generated neighborhood
does not cover every possible served-node transfer.

## A precise physical obstacle

Suppose an old route visits pickup u before drop v, with equal amounts q0.
Deleting both operations subtracts q0 from every old load after u and before
v, and leaves subsequent loads unchanged. Thus total pickup/drop balance
does not make deletion feasible: those intermediate loads must all be at
least q0. With unequal amounts, a nonzero suffix shift remains. Removing
stops also changes travel, which must be recomputed without assuming a
triangle inequality for an unsupported input format. A future neighborhood
requiring a feasible deletion baseline would be explicitly restricted; it
would omit reinsertion moves that repair an infeasible intermediate baseline.

For a feasible baseline route with load L_j on each leg, inserting pickup
amount x on leg a and drop amount y on leg b>=a gives the constraints

```
x <= Q - max(L[a..b])
max(L[b..end]) - Q <= y - x <= min(L[b..end])
travel_delta + (pickup_time + drop_time)*x <= T - baseline_duration
1 <= x <= initial_inventory[u]
1 <= y <= station_capacity[v] - initial_inventory[v]
```

Here u,v are absent from the baseline and their inventories have been restored
to their initial values. If they were not restored, their current baseline
inventories replace those bounds. The between-insertion load rises by x;
the suffix shifts by x-y. The formula also covers a=b, with the intermediate
pickup load checked before dropping. Handling depends on x because any
remaining cargo is unloaded at the depot. Empty departure, optional service,
single direction per station and one vehicle assignment still apply.

For equal inserted amounts x=y=q, the suffix is unchanged. This reduces to
the R73 one-dimensional qmax calculation. Enumerating all legal q and all
insertion positions after a valid deletion would produce a finite, restricted
repair neighborhood. For fixed u,v,q, F is placement-independent, so a
minimum-travel feasible placement can be selected before recomputing F.
This is a local enumeration property, not lossless restriction of the BRP.

The same-quantity transfer alone leaves final inventories and F unchanged.
A strict-F descent can therefore reject a move that only frees useful route
time. Increasing the new quantity, combining transfer with a subsequent
service change, or a precisely defined lexicographic physical tie-break are
different possible mechanisms, with different search sizes. None is selected
here. A neutral bridge must not be described as a measured objective gain.

## Coupled objective calculation

With two changed inventories, every unaffected ratio is fixed, but H changes
through both changed nodes' pairs and S can change even when total bike
inventory is conserved (unequal targets). Consequently stationwise separable
penalties or constant-S approximations cannot replace original F evaluation.
For a one-dimensional integer change q, fixed ratio-order and target-sign
segments have H=Aq+B, S=Cq+D, P=Eq+K. Where S>0,

```
F(q) = (Aq+B)/(n*(Cq+D)) + lambda*(Eq+K)
F'(q) = (A*D-B*C)/(n*(Cq+D)^2) + lambda*E
```

This explains why optimum quantity need not simply be the largest feasible
amount. Breakpoints, derivative roots and the S=0 convention would all need
careful treatment before an accelerated quantity evaluator could replace
integer enumeration. This observation is not implemented or benchmarked.

Any later implementation must publish only independently verified complete
original routes, retain the previous valid UB, and leave full proof coverage
unchanged. It needs a bounded new plan, structural correctness checks, paid
startup evidence and fresh complete comparisons. Feasibility preservation
alone is not evidence that the extra neighborhood improves exact runtime.

## Reassessment against earlier complete evidence

Targeted rereading of R67-R70 during this campaign keeps alternative choices
open. R67's logarithmic encoding has the same LP projection as one-hot VD-P,
but worsened D6 and lost C2's certificate. Fewer binary variables are therefore
not sufficient grounds to restore that encoding. R69's full-HGA VD-S has
useful D6(3600s) and D7(1200s) advantages, with disclosed timing variation;
those historical runs cannot be paired as current timing controls. They do
show that the current primal losses should not be attributed solely to the
one-hot model without supporting evidence.

Simply restoring full HGA after finite descent would reintroduce a documented
small-role risk. E7, S12 and N12 have nonzero optima; zero-target stopping
does not solve that issue. A proposed LP-certificate shortcut before HGA is
also insufficient on the existing S12 evidence: R71's DS-X root LP bound is0,
whereas its full original optimum is0.058563973126 and it certifies in2.125s.
The two child LPs do not raise the full parent bound (0 and0.0539933682444).
Thus a cheap root-LP certificate cannot explain or preserve this fast finish,
and root relative gap alone would label this easy proof as maximally open.
These observations rule out that specific justification; they do not rule
out every mathematically grounded primal/proof coordination scheme.

Sources: R67/R68/R69/R70 final_report.md and R71
local_raw/development/S12/DS-X/external/parent_child_bound_ledger.csv,
paper_optimize_ledger.csv. This is read-only historical analysis, no new
instance, solver invocation, timing correction or candidate gate.
