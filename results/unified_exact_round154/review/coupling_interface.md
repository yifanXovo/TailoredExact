# Round154 full-Q coupling interface: independent static review

Reviewer: `/root/review_round154`, independent of implementation.
Disposition: **ACCEPT_STATIC_COUPLING_INTERFACE**, with the two refresh-state
repairs below closed. This accepts source-level bound directions and
obligations; it does not mark an unexecuted NC20 replay, refresh, direction
selection or new result as PASS.

The reviewer read round154_coupled.py, the actual prepare/prior_override
changes in round154_targets.py, and the reused Master, support_row,
full-Q finite-bound/dual/primal and exact-text interfaces. No Optimize,
Native model load, enumeration, compiler, large pool read, replay or
new computational qualification was executed. The running admitted
K35 long price was not touched.

## Ingesting completed prices and true stocks

ingest begins from a retained result with the same role and complete
original-Q SHA. It copies all previous columns and supports, retains the
old global lower and numerical full-hull upper, and accepts only
complete-domain prices on exactly the same scope. Each price is linked
to its frozen direction SHA and the same beta/exact signed d.

Every returned stock is independently reevaluated in the original
inventory domain with true Fraction f/price. Its complete resource/Gini
feasibility, f_exact and price_exact must match before it enters the pool.
There is no support shrinking, active-state substitution, artificial
price-incumbent column or use of an auxiliary residual q as true price.

For a group with identical direction, the new price lower is the maximum
of its already qualified inherited lower and the completed fresh price
lowers. The only new direct hull lower is

    C_Q + min(a_K,qualified_full_price_lower),

maximized with the accumulated old global lower. The direction's saved
exact certificate remains a qualified original-Q certificate; selecting
a best fresh float lower does not turn its solver objective into a hull
bound. Different directions are not combined into one same-price trace.

When a fresh price improves that direction's inherited lower, the reused
support_row routine adds beta*g-pi.s>=L_price with its existing actual
binary64 one-hot/G coefficient transport. The new support is linked to
direction and price paths. All prior supports remain in the result.
A lack of new support improvement does not suppress newly returned legal
columns. Repeated input stocks are deduplicated in the retained pool.

The old numerical full-RMP upper is retained until a qualified new full
RMP improves it. A larger legal pool still admits its old feasible
distribution, so retaining that upper is valid for unchanged Q/scope.
Neither a price upper nor a fixed-certificate ceiling becomes a
full-hull upper.

## Complete free-Q support replay

replay reads the original direct Q afresh and appends all retained
objective supports. It does not fix original route/load/time/state or
other auxiliary variables. Its finite bounds come from Q before the
support append, and the exact repaired-dual residual calculation uses
those valid original bounds. This provides a valid lower for the
support-strengthened relaxation, hence for the complete inventory hull.

The numerical primal is separately required to qualify. Its support-LP
objective is saved only as support_replay.U, with an explicit statement
that it is not a complete-hull upper. The outer result keeps the prior
full-hull upper and only maximizes its lower with the qualified replay
lower. This correctly separates support complementarity from full-hull
completion and avoids a false closure using the finite support LP.

## RMP refresh and pending-column preservation

refresh builds the existing full Master on original Q and every retained
legal column. The reused Master preserves all original Q rows/variables,
all marginal links (including the check of omitted implied links), lambda
mass/nonnegativity and true completion. Its small conservative completion
margin is not a new lower source. Adding old support rows separately is
unnecessary in this RMP: a distribution over full-domain legal stocks and
the completion inequality already implies each valid price support, with
the existing row-transport qualification.

An optimal solve alone does not supply a new lower. The new code requires
Master.primal()['qualified'] before saving the current full primal,
lowering U or discharging the refresh flag. It retains prior L and
declares no new lower claim. The saved point/positive lambda stocks and
true f values allow final upper reconstruction under the inherited
numerical policy.

Two actual state-handling issues were found during this review:

1. The initial ingest reset refresh_required to whether this ingestion
   itself added columns. If its parent already held unrefreshed columns,
   a later support-only ingestion would erase that obligation.
   The repaired expression preserves prior.refresh_required OR
   newly_added_columns.
2. The initial refresh cleared the flag even if the Master primal failed
   qualification. It now asserts qualification before emitting a
   successful refresh result. An unqualified attempt cannot silently
   discharge pending columns or create a new upper.

replay copies the pending flag rather than clearing it, and it cannot
assess inventory-column usefulness by itself. Thus a final new column
remains visibly due until an eligible full Master evaluation actually
occurs.

## Preparing an updated direction and reusing its full solve

prepare accepts an explicit prior_override result, so NC20 can continue
from its paid new-column/support result instead of silently reverting
to R153's old pool and interval. It checks the same original Q SHA,
reevaluates all pool inventories and retains all previous supports and
current qualified lower/upper information.

For a fresh direction it solves the complete current RMP and requires
a qualified Master primal before selecting multipliers. That solve
already assesses every newly added column. The source now preserves its
point/stocks, consumes min(old_upper,current_qualified_RMP_objective),
and saves refreshed_pool.json with refresh_required=false, the exact
column count, current primal/witness path and no new lower claim.
This is legitimate reuse of a completed required refresh and avoids
buying a duplicate solve solely to change a flag.

The direction's inherited bounds and target calculation use the current
prior lower and this qualified upper, not the frozen R153 table.
The R153 table remains the source of an inherited default path only.
The refreshed-pool sidecar and saved primal identify any newly improved
upper; they are not a price-incumbent or finite-support upper.

The selected near-optimal zero-centered dual is still only a candidate:
the existing Master computes original-Q residual C_Q and true a_K,
and the entire current legal pool is screened for a true-stock price
upper and fixed-certificate ceiling. The target is below that ceiling
and requires meaningful improvement over the current lower. Actual
scope/coefficient/direction data must still be frozen and reviewed before
another expensive price. No favorable updated NC20 outcome is claimed
by this static acceptance.

The existing enable() call only removes Python's integer-to-text digit
limit in this worker so large exact Fraction evidence can be serialized.
It changes no arithmetic, feasible domain, solver, global installation or
production helper. This is the already qualified R153 process-local
exact-text mechanism.

## Execution, evidence and later obligations

All ingestion, LP/RMP and necessary stock validation work remains inside
the parent serial outer meter. Replay/refresh/direction solves retain
Seed0/Threads1 and complete actual-model/call/point records. This reviewer
has not run them while the long K35 price is active.

For the intended next NC20 chain, ingest both completed short-price stock
sets and improved valid supports, replay all supports in free Q, then use
the full current Master/direction preparation and its refreshed-pool result.
If a later price adds more columns, its ingestion must set/retain the
pending flag and a later full refresh is again required. If no column is
new and a saved qualified point/dual proves the same value, reuse is
permitted with its exact provenance.

Final evidence review still needs to check actual saved price/Q certificates,
column chains, support lower replay, qualified full-RMP primal uppers,
refresh discharge and unique outer costs/failures. This report is not a
PASS for data that do not yet exist and not an assertion that NC20's
hull interval narrows.

Reviewed source identities at this static pass:

- scripts/round154_coupled.py:
  8082e66361d0a8d33f6b014debf9ab073ed8e4f37b2f80ec62aa0f1f98791559.
- scripts/round154_targets.py with prior override/current-upper refresh:
  7bbaa94b8d6e5dea7ef94bcf2e9a64b65df8efa64fac364d3fbe87b7d0613de0.

A separate long-price source addendum records why prepare-only changes
do not alter the already admitted compare/K35 task or the frozen E chain.

