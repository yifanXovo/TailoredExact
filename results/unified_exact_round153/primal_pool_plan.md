# Conditional feasible-column diagnostic

This is an offline research extension under goal E3, not a change to the
frozen oracle, production candidate or admitted eight-arm panel. It remains
conditional on independent static review and a paid small-interface check.

The K35 long price raised the complete-hull lower to .2826236515522649.
The first near-optimal zero-center iterations have numerical RMP-minus-D_K
differences near 1.1e-7, but price corrections between .0135 and .0172.
They add only 7–14 legal columns per 300-second price. The current feasible
master upper is near .28748. NC20's saved direction is already priced to
width 1.11e-6, yet the hull interval remains .00728 wide before the registered
near-optimal phase. These observations motivate a separate primal-column
test: can a larger inexpensive pool improve the upper appreciably?

The same rule applies to both unresolved roles. From the current master,
take up to 16 positive-weight inventories by weight and 16 existing stocks
by current price, with deterministic tuple tie-breaking. For each, enumerate
every allowed one-site change and every two-site change that preserves
total stock, over all sites and all allowed step sizes. The ordinary hard
total and support checks remain. A floating Gini/price score orders candidates
only. Each selected stock must pass the existing Fraction true-domain and
true-f check, including Gupper. Up to 64 candidates per start and 512 new
true negative-cost columns per sweep enter the unchanged complete master.

Independent review added a complementary mechanism. For the same positive
parent columns, enumerate all one- and two-site crossovers between every
pair. Each crossover keeps the pair's state marginals exactly. Rank at most
64 candidate pairs after checking both integer hard totals. Rank these
by the floating estimated reduction in expected f,
using the smaller parent weight; then check both children and their strict
f-sum reduction with Fraction. Keep both children, even if one has
nonnegative individual reduced cost. A child already in K needs no duplicate.
These contribute at most 128 further columns, for at most 640 per sweep.
The estimated improvements of overlapping parent pairs are never added or
reported as an attainable primal gain. Only the reoptimized master qualifies U.

All original Q variables, rows, cutoff and objective stay free. The existing
master's numerical primal qualification supplies any improved upper on the
strengthened LP value. This is not a physical routing upper. The previous
qualified lower and supports are copied without improvement. Failure to find
a new selected heuristic column does not imply even exact local exhaustion,
complete pricing or column-generation convergence. A normal
offline cap also yields an explicitly unresolved checkpoint.
Meeting the already registered absolute interval target (K35 1e-4,
NC20 1e-5) stops this diagnostic without further discovery.

The conditional allowance is 1200 seconds of internal work per role, with
1600 seconds reserved at the serial outer boundary. It follows the existing
registered queue, unless a separately documented mathematical checkpoint
changes the research sequence. It will not run concurrently with Native,
and the eight admitted full arms will not be shortened or altered. Roles
whose value interval has already met its registered accuracy need no probe.

The small-interface qualification enumerates the new neighborhood rule on
the already used three finite domains, covering fixed/holed supports, legal
zero, signed costs and beta=0. It checks floating candidate order against
true price, and verifies every selected stock exactly. It introduces no
new solver qualification; the unchanged Master/upper policy is reused.
Final verification checks inherited lower/scope/source identities, all added
stocks and selected complete-Q primal uppers. Discovery counts and paid
master calls are reported separately from full-domain prices. A nonoptimal
master may still contribute a qualified primal upper before the phase stops.

Single-site and two-site quantity neighborhoods are conventional local
search. Historical R75 quantity descent and R76 physical closure already
used related changes for physical-route incumbents. Here the candidates are
inventory-distribution columns in a complete free routing relaxation; neither
the neighborhood nor classical heuristic pricing is claimed as new general
theory. The paired marginal identity is an elementary distribution exchange.

## Observed serialization failure and bounded recovery

The small interface qualification passed 6592 checks, 100 marginal-pair
checks and eight accepted complementary pairs, with no Native Optimize,
in .2587716002 outer seconds. The initial K35 probe then completed 15
sweeps and expanded the legal pool from 1114 to 8794 columns. Its only
upper change was about 2e-12, which is not material progress. The next LP
returned, but formatting the exact expected-f Fraction exceeded Python's
4300-digit integer-to-text limit. The outer attempt closed with exit 1
after 280.0080882 seconds. Its partial records, pending sweep artifacts,
source and fee are retained; its raw RUNNING decision is not rewritten
as a completed diagnostic. The automatic afterqueue stopped before NC20.

The recovery plan is primal_recovery_plan.json. A separate metered worker
disabled that decimal conversion limit only within its process, after
an exact large-Fraction text/JSON/gzip roundtrip qualification. It
changes neither the Fraction arithmetic nor the frozen Master/pricer or
qualified discovery source. K35 resumes from the saved 8794-column pool
for 900 internal seconds (1300 outer reserved); NC20 retains its original
1200 internal seconds (1600 outer reserved). New fee labels and a separate
K35 result directory preserve the failed attempt. All new computation,
including recovery qualification, is serial and charged. The final exact
audit can use the same runtime wrapper without changing its algebra.

The exact-text qualification passed in .1146233000 outer seconds, including
a 10002-character Fraction roundtrip, with no Native call. K35 recovery
then completed 49 additional sweeps in 873.2554402 outer seconds, reaching
33882 legal columns and U=.28732616330431715. NC20 completed 106 sweeps in
1178.8796639 seconds, reaching 54187 columns and U=.1899568005655939.
Neither upper improved materially; both qualified lowers were unchanged.
The new stocks and the completed primal witnesses remain available, without
an exhaustive-neighborhood or full-pricing claim.

After successful probe receipts, the paid fixed-direction screen read
the explicit role/result/fee mapping in the recovery plan. The original
afterqueue FAILED_STOPPED status remains historical evidence. Neither
the serialization repair nor the new screen asserts a scientific outcome
or automatically started another long price. The screen's actual direction
comparison and independently accepted followthrough are recorded in
post_primal_deepening_plan.json and deepening_plan.md.
