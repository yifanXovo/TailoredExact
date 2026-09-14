# Round65 actual algorithm contract

Stable `paper-k1-am-sf` and official plain P-GRB retain their defaults. Research
`research-round65-k1-h` pays the original full HGA in the current process;
`research-round65-k1-s` verifies the empty routes. No start is submitted. The
zero-event feature is a separate flag and ablation, disabled in architecture
screening. This file describes implemented behavior, not performance adoption.

## Controller pseudocode

1. Parse original physical input and weights. Independently verify startup UB.
   Use original nonnegative lower bound and full Gini coverage.
2. Select the controlling active domain with the inherited scheduler. Bind its
   artifact to interval, cutoff and epoch using existing Round29/31 contracts.
3. Unless this domain is marked `core_due`, admit its initial LP and midpoint
   child lookahead through one optional Work/elapsed account. Debit canonical
   construction as well as native work. Use only qualified complete LP evidence;
   no partial LP primal objective becomes a lower bound.
4. After a qualified F0 LP, optionally separate physical vehicle projections.
   PROOF operates on a continuous model copy; SPARSE also attaches selected
   valid rows to the retained native model. Return only qualified same-domain
   bounds or infeasibility of the entire strengthened LP.
5. Commit a parent-to-children replacement only after the existing atomic
   coverage and evidence checks succeed. On any unknown child or exhausted
   account retain the parent, discard speculative native child models, mark
   `core_due`, and continue with this parent's MIP. No immediate probe retry.
6. Execute the original complete-domain MIP (including the existing legitimate
   bound-target pause/resume events). Charge actual core Work and time, which
   replenish optional credit by 0.1. Merge verified UB and valid domain bounds.
7. Global LB is the minimum across the complete active frontier, including the
   original treatment of omitted non-improving domains. Stop on the unchanged
   original certificate conditions or the physical process deadline.

Admission uses seed 30 Work/30 seconds, per-call 10 Work/15 seconds and at most
half remaining work deadline. Native overshoot is debt: this is not an exact
post-call Work inequality or a guarantee of total-time non-regression. Canonical
construction and API validation consume wall time. Wall guards can change the
logical path between runs. Core search itself remains unrestricted by optional
credit; it has the global process cap. Marking a leaf core_due persists safely
under tighter incumbents and deliberately forgoes later LP probing on that leaf.

The named `credit-seed` revision instead caps each call at30 Work; total seed
credit and all time guards remain the same. `credit10` remains available for
matched attribution. This avoids discarding useful initial LP work merely
because the per-call ceiling is smaller than the remaining finite account.

## Resource service and evidence scopes

Each physical vehicle block contains q/f on station-origin arcs, including return
arcs. Empty depot departure has no q/f variable. Columns have fixed finite physical
bounds. After conditioning x/p/d/L, no row crosses vehicle blocks. RHS alone is
updated in retained auxiliary models, serially; no full-model LP export or nested
MIP callback optimizer is used. Basis is retained implicitly by the solver but no
speedup or unconditional basis reuse is claimed. Original F0 Q/T constraints and
qualified LP feasibility are the initial cheap physical screen; existing global
pool rows are checked for current violation before optimization.

The explicitly selected `release-load` revision removes q_load and B4 from the
auxiliary system and leaves all original main-model L constraints intact. It
therefore checks a relaxed x/p/d resource completion. Its cuts are global on
original solutions, but auxiliary feasibility does not validate the actual L
vector. Removing local L repair may change which Farkas ray is returned; no
claim of a stronger relaxation is made. Representation is persisted per service.

Each new Farkas combination is normalized; inequality signs are made legal and
all coefficients/residual contributions recomputed with outward rounding.
Finite auxiliary bounds compensate negative residuals. Physical original bounds
compensate stored coefficient rounding. No tolerance deletion is used. A row
must exclude the actual current point by >1e-7 and is recorded with its physical
identity, vehicle, multipliers and point. Auxiliary infeasibility alone never
excludes a Gini interval or certifies the original objective.

Global rows can move across leaves/epochs of this one physical instance. Pool
limit is64; at most8 currently violated rows per base LP and4 proof reoptimizations.
Reoptimization stops after unknown, no objective improvement (>1e-7), or reaching
the legal cutoff. Parameter or persistence failure stops optional projection.
Only complete residual-qualified proof LP evidence is exported. A zero-dual
partial bound facility is deliberately not implemented.

PROOF adds no rows/columns to main F0. SPARSE adds no columns and only selected
rows, tracked separately from canonical defining rows. It does not bypass native
additional-row guards or rebuild MIP to inject cuts. Integer types are restored
through the original backend lifecycle after optional work. The canonical SHA
identifies the immutable domain model; row_use and main_shapes identify the actual
augmented matrix. A merged proof bound is a valid bound for the same integer
domain, not necessarily the optimal value of the current sparse native LP.

## HGA reliability

The original initialization/strict-improvement observer decodes and verifies a
complete candidate using the original evaluator. Only verified F in [0,1e-12]
requests immediate termination, using the existing original certificate tolerance
and F>=0. Nonzero runs retain genetic operations, RNG and stopping rules. A failed
audit write retains the in-memory verified witness but is separately reported as
an audit failure. Candidate discovery, verification/publication, heuristic exit,
and final certification remain distinct phases. No historical candidate is read.

## Parameter and cost records

All native calls use/read back Threads1, Seed0, Presolve Auto, gaps0; auxiliary
Farkas calls additionally set DualReductions0 and InfUnbdInfo1. Repeated optimize
Work is the most recent optimize's work, debited separately. Main calls are in
paper_optimize_ledger; auxiliary and proof calls have separate launch/return
ledgers and share optional_budget. End-to-end includes HGA, generation, copying,
verification, persistence and shutdown. No runtime row/bound is provided free
from another algorithm. P-GRB runs its original native default heuristic policy.

Performance, resource feasibility, fixed-domain LP proof, retained-memory witness,
audit persistence and strict original-problem certification are distinct statuses.
Unknown never sets an infeasible flag. On permanent optional shutdown the full
original exact search and certificate path remain available.
