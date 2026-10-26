# Round75 admission: physical quantity descent

Base: closed Round74 final ac06e8a4efc3203db55fd64795ed89d1528c9322,
draft PR135, freshly verified open/draft/unmerged. Owned branch:
codex/round75-physical-quantity-descent. Original dirty worktree untouched.
Overall research goal is active and unmet. No defaults or main merge.

## Defect and hypothesis

R74 JDS-X has severe D7 regression against P at 1200s: absolute gaps
.121030952 versus .080034387; K1-R retains .017914353. Better starter and
more served stations do not imply a better complete result. K1's UB advantage
is largely Gini, whose ratio sum is not conserved by ordinary inventory transfers.
The existing constructor cannot revise served quantities; its extra descent
seed generated no cross-route candidates. R73 small gains remain important.

Test whether finite direct original-objective quantity revision of the best
JDS-X physical starter cheaply improves its inventory distribution. New
default-off preset research-round75-vds-quantity-descent (QDS-X) inherits the
same constructor, all 24 random descent seeds and the 25th constructive seed,
then performs best-improvement quantity descent before unchanged VD-S proof.
It does not enable full HGA, resource scheduling or a different formulation.

For each currently served station i, signed operation s_i = pickup - drop.
Enumerate every integer single change s_i += t; also every unordered served
pair (i,j), s_i += t, s_j -= t. Both signs of t are included. Pairs may belong
to one or different vehicles. Station stock bounds and all affected load
prefixes determine finite ranges. Sign flips are permitted; zero operations
remove their physical stop. Recompute travel for such deletions, including
adjacent deletions and nonmetric travel. Handling change uses
(c_pick+c_drop) times the change in total positive operations. Loaded returns
and cumulative pickups above Q remain legal.

Rank feasible candidates by the full original F, with deterministic station/
delta ties. Recompute coupled S/H/P; no stationwise or constant-S surrogate.
An O(V) two-inventory objective update may be used only with full-formula
crosschecks and near-cancellation recomputation. Verify the selected complete
physical witness before every accepted strict improvement. Use inherited
heuristic improvement 1e-12 and objective crosscheck 1e-10; do not change
solver/feasibility/certificate tolerances. A numerical mismatch is an explicit
failure retaining the prior witness, never a new UB. Finite integer inventory
states and strict descent imply termination apart from the whole-run deadline.
No neutral relocation or new-station insertion belongs to this neighborhood.

This is a heuristic neighborhood restriction, not a restriction of the exact
BRP domain. Full proof coverage/model/Start validation are inherited unchanged.
All costs are paid. No instance IDs, historical optima, elapsed-time slices,
Work limits, per-component restarts or machine-dependent gates enter QDS-X.
The sole global deadline ends the entire run. Generic quantity repair is known;
R74 literature_notes.md records relevant primary precedents and model differences.
Performance, engineering correctness and theoretical novelty remain separate.

## Bounded resources before execution

1. Implement one module and actual preset/metadata path. Add an independent
   small exhaustive materialize-and-verify oracle over the declared single/pair
   neighborhood, including unequal capacities/targets, stock limits, loaded
   returns, cumulative pickups above Q, direction flips, zero stops, adjacent
   deletions, cross-vehicle suffix constraints, nonmetric travel, zero handling,
   S=0 and a whole-run deadline. Add actual native CLI preset/default-isolation
   qualification. Reuse the existing 54-test suite.
2. Admit one fresh isolated full qualification batch, plus at most two repair
   revisions if correctness/build failures require them. Never overwrite failed
   build/test identities. Each batch: configure <=60s, build <=600s, serial
   tests <=600s, <=90 actual Optimize calls (existing native fixtures included).
   These are qualification experiment limits, not candidate policies. No
   optimizer runs alongside compilation/heavy audits. Count actual calls and
   full wall costs, including failures. New tests may be native fixtures; no
   performance claim follows from passing tests.
3. If qualification passes, five exposed startup roles D3/C2/D4/D6/D7 with
   fresh JDS-X and QDS-X on this same new binary: exactly ten heuristic-only
   runs, each whole-process cap <=30s, total <=300s, zero Optimize. Freeze
   input/build/command/seed identities and observer cost first. Compare the
   complete original physical objective and total startup time; preserve
   first-24 logical paths and all starting/final witnesses. No historical route
   enters the actual candidate.
4. Inspect quality, candidate counts, accepted moves and costs before admitting
   any complete performance runs. No 300/1200/3600/7200s full campaign or
   independent confirmation is allocated now. A material startup gain is only
   reason to test the full method, not a performance conclusion. If quantity
   repair is weak, reconsider fleet assignment/core structure rather than
   adding an unbounded parameter search.

Frozen practical criteria remain R71/R74: both-certified V<=12 and both<60s,
material >2s AND20%, severe >5s AND50%; other both-certified material >10s
AND15%, severe >30s AND50%; both-open absolute gap material >.001 AND10%,
severe regression >.01 AND50%. Certification gains/losses separately. No
per-point fastest-K1 veto. Independent generalization is not claimed on this
exposed panel. A later full campaign needs a separately frozen allocation and
fresh P controls on the current binary.

## Acceptance and publication

Check actual neighborhood/physical semantics, default isolation, full proof
compatibility and original witness mapping. Preserve every failed attempt and
negative result. Deliver a concise final report, algorithm/math, source/build/
input/command identities, machine-readable results/witnesses, costs and a new
independent draft PR once a substantive result is available. A microtest-only
checkpoint is not a completed optimization stage. No new algorithm is assumed
successful before execution; D7 repair and independent confirmation remain open.
