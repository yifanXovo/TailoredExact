# C0, C5, and P-GRB mechanism comparison

## Same-solver evidence

| property | P-GRB | C0-DIAG | C5-CANDIDATE |
|---|---|---|---|
| Mathematical scope | Complete compact MILP | Exact interval cover | Exact interval cover |
| Native search | One continuous Gurobi tree | Repeated leaf-local native solves | Leaf-local LP, partial MIP, and exact MIP solves |
| Scheduler | Native Gurobi | External best bound | External best bound |
| First structural action | Native presolve/root | Native parent processing | Parent LP plus two child LPs |
| Partial bound eligibility | Native continuous tree | Broad unresolved leaves | Small positive child-gain leaves only |
| Return milestone | Native completion/deadline | Fixed time quantum and attempts | Frozen child-disjunction target |
| No-gain treatment | Continues native tree | Time-quantized return | Blocking exact parent MIP |
| Target-reached treatment | Not applicable | Requeue by time policy | Mandatory delayed split |
| Paper compatibility | Benchmark | No | Yes |
| Native-state claim | Native solver owns state | None across restarts | Same model object only |

## What P-GRB retains

P-GRB keeps presolve reductions, root cuts, node relaxations, pseudocosts, and
native branching within one solver-owned tree. This produces especially
strong anytime behavior on V12 and several tight-T/high-imbalance cases.
Cross-model external scheduling must compensate for the loss of that
concentration; it cannot claim equivalent native continuation.

## What C0 teaches

C0 demonstrates that unresolved interval leaves can emit valid partial native
lower bounds, return to an external best-bound scheduler, and later receive
more processing. On the audited retained C0 rows, finite first-processing
events add 1.9233500 summed leaf-bound gain and 1.8595770 immediate global
gain.

The transferable mechanisms are:

- valid native lower-bound harvesting;
- broad eligibility across unresolved leaves;
- external best-bound interleaving;
- exact retained coverage;
- inherited valid bounds;
- verified cutoff and exact closure.

The nontransferable mechanisms are fixed 30/60/... second quanta, attempt and
retry ordinals, elapsed stagnation, and Work/node/solution controls. C0
remains an exact but non-paper-compatible performance teacher.

## What C5 established

C5 proved that backend-certified `MIP_OBJBND` milestones can replace time
quanta and remain exact. It reduced the number of terminal calls relative to
C4 and broadly beat C4. Its partial phase is nevertheless narrow, its
child-first order is often unnecessary, and it forces a split after the
parent reaches the child target.

The Round 31 forensic accounting is decisive:

- 30/55 parent LP selections were already safe to requeue;
- all remaining 25 had a finite higher frontier target;
- 86 attained C5 targets were followed by zero-current-gain delayed splits;
- 82 no-gain terminal parents consumed 98.13% of C5 terminal Work;
- 12 no-gain leaves blocked until the deadline.

## C6 transfer boundary

C6 should retain C5's valid callback-bound contract but generalize it to
every unresolved controlling leaf. The selected design direction is:

- parent-native-first;
- next-distinct-frontier or verified-cutoff target;
- target attainment means open-leaf requeue, not closure;
- child lookahead is lazy;
- the split criterion is reevaluated against the current parent bound;
- no split occurs solely because an earlier target was reached;
- no-gain leaves use the same frontier target when one exists;
- exact MIP closure occurs only when no higher scheduling milestone and no
  useful split remain.

C6 may reuse a same-leaf model object. Its correctness and performance claims
use only returned valid bounds and terminal statuses. It does not claim basis,
presolve, cut, pseudocost, incumbent, or native-tree preservation.
