# Cost-controlled exact proof and vehicle projection

The unchanged inventory objective is
Y_i=b_i+sum_k(d_ki-p_ki), r_i=Y_i/D_i, S=sum r_i,
H=sum_{i<j}|r_i-r_j|, F=H/(nS)+lambda sum omega_i|r_i-1|.
Original weight parsing and S=0 convention remain. Vehicles depart empty,
single nonzero unidirectional service per station, loaded return allowed;
Q bounds prefixes, not cumulative pickups. Duration is travel+(pick+drop)sum p.
The actual input supplies common T/handling and per-vehicle Q.

For a legal domain I and non-strict cutoff F<=U, F(I,U) embeds in JOINT
and hence in F0 on the same original variables. The integer q/f embedding,
conservative stored cbar/taubar/B and proof of this containment are inherited
from Round64. No new constraint removes any original route. F0 remains a
complete interval MIP when every optional task is disabled.

## Coverage and incomplete information

The existing scheduler keeps a minimum over all unreplaced relevant domains,
using maximum of valid bounds on each individual domain and the control UB for
omitted non-improving space. Children become authoritative only after the old
atomic full-coverage check. An incomplete child pair leaves the parent intact;
even a valid empty-child proof is retained as evidence rather than forcing a
recursive call. The parent then goes to exact MIP. No unknown child disappears.
After a committed pair, an empty child remains accounted by the old closure;
the survivor inherits the parent bound. Native target interruptions keep their
existing evidence semantics; terminal deadlines leave open coverage.

Optional initial/child LPs consume one shared account. Admission grants at most
min(10,30+.1 W_core-W_optional) Work and at most
min(15,30+.1 t_core-t_optional,.5 remaining) seconds. Negative credit means no
admission. Every completed call, including limit/unknown, charges actual Work;
model preparation, validation and copying charge optional wall. Overrun is debt.
This is an admission and repayment invariant, not an exact post-call hard Work
inequality: Gurobi may overshoot before reaching a deterministic stopping state.
Core Work is earned only from real exact/native-target MIP optimization. Building
a model or running another probe does not mint core Work. A state whose LP or
child lookahead is incomplete is marked core-due and cannot immediately repeat
it. No amount of unused speculative structure prevents the full-domain MIP.

Only completed qualifying LP optima/infeasibility are accepted. Interrupted
primal ObjVal is never a lower bound. The fallback is inherited LB (initially
the old safe nonnegative bound), not an invented partial-dual value. LP evidence
cache is still bound to leaf geometry, canonical hash, propagation, U and epoch;
an incumbent epoch change discards native/evidence state. The conservative
core-due flag may persist through tightening: skipping optional work is safe.

WorkLimit is per Optimize, not a cumulative continuation allowance. Every
native call explicitly sets and reads it back; core calls restore infinity.
The existing Gurobi backend already accounts Work/Runtime per call, separately
from retained-object totals. Official documentation:
[WorkLimit](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameter.WorkLimit),
[Work](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/model.html#attrwork).
Physical TimeLimit/finalization reserve still apply, and can change paths;
neither full deterministic execution nor universal performance dominance follows.

## Vehicle separation and global rows

Conditioning on v=(x,p,d,L) leaves independent vehicle q/f blocks. Each row uses
only k's q/f variables; the full feasibility matrix is their block diagonal
union. Depot departures are eliminated, returns remain. Therefore existence of
the full completion is equivalent to existence of every vehicle completion.
Inventory/cutoff constraints stay in F0; they are not silently added to an
individual physical module. At fixed v a failed completion is point exclusion,
not exclusion of the whole current interval.

Write each vehicle as Az<=b(v), equalities free, 0<=z<=u. Any normalized legal
multiplier pi (nonnegative on <= rows) yields
pi^T b(v)>=sum_j min(0,(pi^T A)_j u_j). All u are finite physical Q_k or B_ij.
Inequality multipliers are clamped before recomputing every term; equality
multipliers stay free. Neither a negative column residual nor the associated
bound contribution is discarded.

Production verification uses outward double enclosures for products and sums.
For auxiliary column enclosure [a_lo,a_hi], use min(0,a_lo*u) in the lower RHS.
For exact projected coefficient p in [p_lo,p_hi], storing c instead is made safe
by adding min(0,(c-p_hi)*u_v) to the RHS, again outward rounded. Original
physical bounds are x in [0,1], p/d in [0,station capacity], L in [0,Q_k]. No
small coefficient is threshold-deleted. Nonfinite values/unknown upper bounds
reject the row. A >1e-7 actual-point violation is required for selection. These
are numerically supported valid rows, not rational optimality certificates.

The row uses global physical data only, includes L when needed, and may be reused
across leaves/cutoff epochs on the same physical identity. Service objects keep
one matrix/model per vehicle and update only affine RHS. They retain whatever
Gurobi basis state survives the actual RHS updates; no explicit guaranteed basis
or free presolve claim. Vehicles and all reoptimizations run serially. Every
auxiliary call has Work/physical caps and is on the same optional account.

PROOF-only copies the actual current F0 LP into a separate bounded proof model;
verified rows can improve a same-domain bound or prove that whole copied domain
empty. That full-model result, not the auxiliary status, is returned to the
outer scheduler. SPARSE executes the same proof service and attaches at most
the small selected current rows to the retained native model. Per-leaf signature
tracking prevents duplicate insertion. Original types are restored by the old
LP/MIP transition. No q/f columns, callback optimizers or implicit MIP rebuilds
are added. Canonical F0 hash plus row-use ledger identifies the augmented model.

Initial implementation permits four proof LP passes, at most eight selected
rows per call and a global pool of at most64. Stop after the first completed
pass with <=1e-7 objective gain or after reaching U; no claim of full closure.
Pool reuse selects currently violated rows; it does not load all past rows.
Proof copying/reoptimization is a paid service, not preserved B&B search.

## Reliability separation

The HGA observer reads a completed cached decode and uses the original route
verifier, retaining its best in memory. An independently verified F in [0,1e-12]
meets the existing zero certificate with F>=0, and requests stop at the current
initialization/generation boundary. No RNG call, genetic operation, population,
decoder setting or positive-objective stagnation rule changes. Audit write
failure is reported separately and cannot delete the verified memory witness.
This feature has no bearing on the nonzero bound proof or projection novelty.
# Released-load revision (v4, explicitly selected)

Let A_full(v,L) denote the conditioned per-vehicle shared physical system. Delete
the equations out(q)=L and inequalities cL<=out(f), retaining q/f balances,
capacities and cq<=f. The resulting A_free(v), v=(x,p,d), admits every completion
of A_full(v,L). Thus an infeasibility certificate of A_free at v gives a valid
row on all original integer solutions; all retained multipliers also define a
legal full-matrix combination with the deleted-row multipliers zero. The finite
q/f bounds are unchanged, and no bound correction uses a fixed L value. Rows
therefore contain only x,p,d. This is a valid relaxation, not a claim that free
resource completion restores all original L-based routing constraints. The main
F0 still includes those constraints and its original L variables.

The revision can return feasible for a point excluded with fixed L; it is not
a uniformly stronger relaxation. Its rationale is proof relevance: an arbitrary
Farkas ray for the fixed-L system can spend a scarce separation round repairing
local L inconsistency with zero F-bound gain. Whether released rows improve
objective proof or integer search is an empirical question, with full costs.
