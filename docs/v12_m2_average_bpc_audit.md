# V12 M2 Average GF-RL-BPC Audit

Date: 2026-06-25

## Instance

- Path: `reference/regen_candidate_V12_M2_average.txt`
- Scope: regenerated engineering input in the local repository.
- SHA256: `0BB0416CC9540FFFBB91299D5C9ED3D6C2363906424005B1C40B4E3829DDF4F0`

No historical source file was found in `reference/` or `testdata/`; this audit
therefore records the exact regenerated candidate file and does not claim it is
the historical paper target.

## Baseline Command

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_60s.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v12_m2_average_core_60s.json
```

## 60s Paper-Core Result

| status | objective / UB | LB | gap | wall time | unresolved | invalid | open nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gcap_frontier_not_closed` | 0.719065249476 | 0.359532624738 | 0.5 | 70.1834s | 2 | 0 | 1 |

Certificate audit: passed as **noncertified**. The result is not reported as
optimal.

## 300s Paper-Core Result

| status | objective / UB | LB | gap | wall time | unresolved | invalid | open nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gcap_frontier_not_closed` | 0.719065249476 | 0.577560696100 | 0.196789586869 | 314.122s | 2 | 0 | 4 |

Certificate audit: passed as **noncertified**. The result is not reported as
optimal.

## Plateau Evidence

- `frontier_min_interval_lower_bound=0.359532624738`.
- `frontier_lower_bound_source=gamma_floor`.
- `full_certificate_rejection_reason=unresolved_intervals`.
- Controlling interval: `4:[0.359533,0.479377]`.
- Two of four relevant intervals were bound-fathomed by the
  inventory/route/Gini relaxation.
- The current run spent about 42.8624s in interval relaxation accounting:
  21.6020s on `[0,0.239688]` and 21.2605s on `[0.239688,0.359533]`.
- The controlling interval has `open_nodes=1` but `bpc_nodes=0`; the trace
  reason is `tree_not_started_before_time_limit_or_reserve`. This is a queued
  unresolved leaf, not a partially explored branch-price tree.
- The progress log reports 1,877,915 generated columns before final summary.

Trace artifacts:

- 60s progress CSV:
  `results/paper_bpc_core/progress/v12_m2_average_core_60s.csv`.
- 60s trace JSON:
  `results/paper_bpc_core/raw/v12_m2_average_core_60s.trace.json`.
- 60s interval trace CSV:
  `results/paper_bpc_core/raw/v12_m2_average_core_60s.intervals.csv`.
- 300s progress CSV:
  `results/paper_bpc_core/progress/v12_m2_average_core_300s.csv`.
- 300s trace JSON:
  `results/paper_bpc_core/raw/v12_m2_average_core_300s.trace.json`.
- 300s interval trace CSV:
  `results/paper_bpc_core/raw/v12_m2_average_core_300s.intervals.csv`.

The new trace schema exposes the active interval ledger, per-interval aggregate
tree counters when a tree starts, and aggregate global pricing counters.
It now also emits per-node and per-pricing-call arrays when a branch-price tree
actually starts. In this 60s V12 M2 row those arrays are empty because the
controlling leaf is queued but not expanded before the time/reserve stop.

## Initial Diagnosis

The 60s result is dominated by frontier coverage and relaxation time. The global
lower bound remains controlled by a gamma-floor child interval whose BPC tree
has not started before the time/reserve stop, so no certificate-safe claim can
be made. The current trace shows which interval controls the lower bound and
which intervals consumed relaxation time, but it is not yet detailed enough to
isolate duplicate columns, exact-pricing exhaustion, or branch-node quality once
the controlling leaf is actually expanded.

The 300s run raises the lower bound to 0.577560696100, but it is still
noncertified. The controlling interval `4:[0.359533,0.479377]` is queued with
an inventory/route/Gini relaxation lower bound and has not yet started a BPC
tree (`bpc_nodes=0`, `open_nodes=1`). Other explored BPC nodes remain
unresolved with `not_closed_reason=pricing_did_not_close`. Captured pricing
calls include early-negative incomplete calls and exact-label calls with about
6.52M route states and 250.8M operation states in the largest observed call.
Those calls return negative columns and therefore cannot certify pricing
closure.

An explicit completion lower-bound pruning diagnostic was run for 300s. It
recorded `completion_lb_pruned_labels=40634262` and reduced captured operation
states modestly, but the valid lower bound was weaker
(`0.464836734210` versus the baseline `0.577560696100`). The controlling split
leaf kept an inherited parent lower bound instead of recovering the stronger
inventory/route/Gini relaxation bound in time. This mixed result is why
completion-LB pruning remains an explicit diagnostic option rather than the
default `paper-bpc-core` configuration.

The next certificate-safe optimization changed the inventory/route/Gini
relaxation ordering: the no-compatibility pickup/drop relaxation now runs
before the compatibility-flow model and skips the latter if the easier model
already cutoff-fathoms the interval. This keeps the same certificate basis
while avoiding expensive redundant CPLEX calls on low-Gini split children.
With this ordering, the 300s paper-core run improves to
`LB=0.692627421486`, `UB=0.719065249476`, gap `0.036766938758`. The prior
controlling split child `[0.359532624738,0.479376832984]` is now
bound-fathomed; the remaining unresolved leaves are
`[0.479376832984,0.599221041230]` and
`[0.599221041230,0.719065249476]`, both at LB `0.692627421486`.

The first 1200s follow-up exposed a scheduling regression rather than a
certificate improvement. The solver spent about 873s in pricing and 233s in
master solves on a broad parent interval before adaptive splitting, then ended
with a child interval carrying only the inherited parent lower bound. That row
remained audit-safe and noncertified, with `LB=0.469117173935`, gap
`0.347601383495`, two unresolved intervals, and twelve open nodes.

The subsequent `--frontier-split-before-tree true` scheduling change defers
initial branch-price trees for splittable broad intervals and lets adaptive
child relaxations run first. On V12 M2 300s it remains noncertified but improves
the valid lower bound to `LB=0.696966843140`, `UB=0.719065249476`, gap
`0.0307321294594`, with two unresolved high-Gini leaves and two open nodes.
This is not a certificate shortcut: replaced parent intervals are ignored and
the active child ledger still has unresolved intervals.

Completion lower-bound pricing pruning was then retested under the current
split-before-tree scheduling. The baseline and pruning rows have the same
valid lower bound and gap:

- Baseline split-before-tree 300s:
  `LB=0.696966843140`, gap `0.0307321294594`,
  `unresolved_intervals=2`, `open_nodes=2`, pricing time `70.2706739s`.
- Split-before-tree plus completion-LB pruning 300s:
  `LB=0.696966843140`, gap `0.0307321294594`,
  `unresolved_intervals=2`, `open_nodes=2`, pricing time `90.9342476s`,
  `completion_lb_pruned_labels=20756309`.

This confirms that completion-LB pruning should remain an explicit diagnostic
option for now. It is not a reliable paper-core default because it did not
improve the certificate-relevant lower bound and was slower on this V12 M2
row.

The required split-before-tree 1200s paper-core row was then run. It improves
the valid lower bound further but still does not certify the original problem:

- `UB=0.719065249476`, `LB=0.703291904615`, gap `0.0219359020237`.
- `unresolved_intervals=1`, `open_nodes=1`, `invalid_bound_intervals=0`.
- The remaining unresolved active interval is
  `[0.479376832984,0.509337885046]`, with lower-bound source
  `focused_child_inventory_route_gini_relaxation`.
- The adjacent child `[0.509337885046,0.539298937107]` is empty/closed by the
  branch-price tree; the low- and high-Gini siblings are bound-fathomed by
  valid inventory/route/Gini relaxation bounds.
- Runtime is dominated by exact-label pricing:
  `pricing_time_seconds=821.1792326`, `master_time_seconds=191.4461219`,
  `bound_time_seconds=160.8085539`.
- The trace captures 25 BPC nodes on the controlling interval, 40 pricing calls
  for that interval, and one remaining open node. The largest exact pricing
  calls enumerate roughly 6.3M-6.5M route states and 241M-247M operation states,
  with support-duration pruning still at zero.

This row is the current best paper-core V12 M2 lower bound, but it remains a
noncertificate because one active interval has an open BPC node and exact
pricing/tree closure is incomplete.

The adaptive split-depth diagnostic shows that deeper child relaxation is more
effective than spending the same budget in the broad depth-3 tree. With
certificate-neutral depth 5, the 300s paper-core row improves to
`LB=0.706200471341`, `UB=0.719065249476`, gap `0.0178909746296`. This is
better than the previous depth-3 1200s split-before-tree row. The remaining
active leaves are `[0.494357359015,0.509337885046]`, which is queued, and
`[0.486867096000,0.494357359015]`, which has an open BPC node. The sibling
`[0.479376832984,0.486867096000]` is now bound-fathomed by the focused child
inventory/route/Gini relaxation.

This motivated changing the paper presets to default `frontier_adaptive_max_depth`
to 5 unless explicitly overridden. The change only changes work order and
ledger granularity; it does not change the certificate requirements.

The depth-5 1200s paper-core row improves again but still does not close:

- `UB=0.719065249476`, `LB=0.710439004053`, gap `0.0119964710145`.
- `unresolved_intervals=2`, `open_nodes=2`, `invalid_bound_intervals=0`.
- The active unresolved leaves are `[0.494357359015,0.509337885046]`, queued
  with an inventory/route/Gini relaxation lower bound `0.718272430646`, and
  `[0.486867096000,0.494357359015]`, with open BPC nodes and tree LB
  `0.710439004053`.
- Runtime remains pricing dominated:
  `pricing_time_seconds=795.3111719`, `master_time_seconds=173.6668023`,
  `bound_time_seconds=216.7553962`.
- The largest exact-label calls still enumerate roughly 6.3M-6.5M route states
  and 240M-247M operation states, with support-duration pruning at zero.

This is the current best V12 M2 paper-core lower bound. The remaining plateau
is no longer broad frontier coverage; it is exact BPC closure on the narrow
depth-5 child `[0.486867096000,0.494357359015]`, plus a queued sibling that is
already very close to the incumbent cutoff but not fathomed.

The depth-6 default validation improves the 300s paper-core row further:
`LB=0.713690734357`, `UB=0.719065249476`, gap `0.00747430796209`, with
`unresolved_intervals=3`, `open_nodes=3`, and `invalid_bound_intervals=0`.
The improvement is certificate-safe because it comes from replacing active
parents with exactly covering child intervals and taking valid child lower
bounds. The interval `[0.479376832984,0.486867096000]` is now bound-fathomed by
the inventory/route/Gini relaxation. The current controlling child is
`[0.490612227507,0.494357359015]`, with source
`focused_split_inherited_parent_lb`; neighboring child
`[0.486867096000,0.490612227507]` has a stronger relaxation LB but remains
queued. The 300s gap is now below one percent, but no original certificate is
claimed because the active frontier still has unresolved leaves.

The same scheduling logic was then validated at default adaptive split depth 7.
The V12 M2 300s row reaches `LB=0.715075764785`,
`UB=0.719065249476`, gap `0.00554815393275`, with
`unresolved_intervals=3`, `open_nodes=3`, and `invalid_bound_intervals=0`.
The row spends almost all time in inventory/route/Gini child bounds and only
`0.0024676s` in pricing, so the improvement is again certificate-safe frontier
ledger refinement rather than incomplete pricing closure. The instance remains
noncertified because the active frontier still has unresolved leaves.

The default adaptive split depth was increased once more to 8 because the
depth-7 ledger was still controlled by a narrow active child. The V12 M2
default depth-8 300s row improves the valid lower bound to
`LB=0.716948330538`, with `UB=0.719065249476` and gap
`0.00294398726726`. The row has `unresolved_intervals=3`,
`open_nodes=3`, and `invalid_bound_intervals=0`; it spends no time in BPC
pricing and takes its frontier lower bound from
`focused_inventory_route_gini_relaxation`. This is still not an
original-problem certificate, but it is the best current paper-core V12 M2
300s lower bound and shows that one additional certificate-neutral split level
continues to tighten the controlling region before expensive exact tree
closure.

An explicit depth-9 300s diagnostic was also tested and rejected as a default
candidate. It returned to `LB=0.715075764785`, with gap
`0.00554815393275`, `unresolved_intervals=3`, and
`invalid_bound_intervals=0`. The row is audit-safe and noncertified, but it is
worse than the depth-8 default because the extra split work does not reach the
same focused child bound within 300s. The current paper-core default therefore
stays at depth 8.

A later bound-time optimization added a continuous LP cutoff precheck before
the integer route-mask MIP used by the inventory/route/Gini relaxation. On the
60s V12 M2 row, the precheck proves the first low-Gini interval
`[0,0.239688]` cutoff-infeasible before running the integer MIP. The row
remains correctly noncertified: `UB=0.719065249476`, `LB=0.461969904320`, gap
`0.357541051168`, `unresolved_intervals=2`, and
`invalid_bound_intervals=0`. The precheck is useful for cheap low-Gini
fathoming but it does not yet improve the depth-8 300s plateau controlled by
narrow high-Gini active children.

An ungated precheck variant was tested for 300s and rejected as the default
because it spent extra CPLEX process time in middle intervals and only reached
`LB=0.715075764785`. The implemented gate restricts the precheck to low/high
Gini ranges. With that gate, the V12 M2 300s paper-core row recovers the
current best valid lower bound: `UB=0.719065249476`,
`LB=0.716948330538`, gap `0.00294398726726`, with
`unresolved_intervals=3` and `invalid_bound_intervals=0`. This is still not an
original-problem certificate; it preserves the best depth-8 lower-bound
evidence while keeping cheap cutoff-fathoming for easier outer intervals.

The next route-mask scheduling adjustment avoids solving the compatibility-flow
variant when an adaptive/focused interval relaxation has only a short CPLEX
budget (`<=2.5s`). The fallback no-compatibility model is still a valid
relaxation lower bound, and each skipped interval records
`compat_skipped=short_relaxation_budget`. This is certificate-neutral because it
may weaken a relaxation but cannot overstate a lower bound. On V12 M2 Average
300s, the row preserves the current best paper-core lower bound,
`LB=0.716948330538`, `UB=0.719065249476`, gap `0.00294398726726`, with
`unresolved_intervals=3` and `invalid_bound_intervals=0`. Runtime improves from
about `318.18s` to `311.75s`, and total bound time drops from about `290.63s`
to `284.21s`. The instance remains noncertified; the controlling region is
still the narrow child around `[0.488740,0.490612]`, with lower bound source
`focused_inventory_route_gini_relaxation`.

The next accepted runtime fix removes duplicate UB-only incumbent work. The
incumbent archive already provides a verified V12 M2 route plan with
`UB=0.719065249476`, so `paper-bpc-core` now skips the default BPC-owned
`auto` incumbent portfolio after accepting that archive incumbent. This does
not affect any lower bound or certificate condition: the archive incumbent is
still only a feasible cutoff. On the 60s row, the initial seed stage drops from
about `27s` to about `7s`, and the valid lower bound improves from
`LB=0.359532624738` to `LB=0.692095277420`. On the 300s row, the valid lower
bound improves from `LB=0.716948330538` to `LB=0.717435865864`, with
`UB=0.719065249476`, gap `0.00226597462971`, `unresolved_intervals=3`, and
`invalid_bound_intervals=0`. The instance remains noncertified because active
frontier leaves are still unresolved; the improvement is purely better
scheduling of certificate-safe relaxation work.

A later focused-relaxation budget probe set
`--frontier-focused-relax-seconds 2.5` to see whether a shorter focused pass
could reach more controlling leaves before the 300s limit. It remained
audit-safe but was worse: `LB=0.715075764785`,
`UB=0.719065249476`, gap `0.00554815393275`,
`unresolved_intervals=3`, and `invalid_bound_intervals=0`. The default
focused relaxation budget therefore remains unchanged; the plateau needs a
stronger valid relaxation or exact closure, not shorter focused relaxations.

The archive-incumbent scheduling path was then run for a 1200s V12 M2
paper-core row. It remains audit-safe and noncertified:
`UB=0.719065249476`, `LB=0.717435865864`, gap `0.00226597462971`,
`unresolved_intervals=4`, `invalid_bound_intervals=0`, and `open_nodes=30`.
The run spends `339.5201322s` in bound work, `130.9071279s` in master solves,
and `743.3654876s` in pricing, with `28,131` columns generated. Focused
intensification improves one child but leaves the controlling interval
`[0.492484793261,0.494357359015]` at inherited lower bound
`0.717435865864`. This confirms that the current V12 M2 long-run plateau is
exact BPC closure in a narrow high-Gini leaf, not a certificate-accounting
issue. No original-problem optimality is claimed.

## Required Next Work

- Use the node/pricing trace to profile exact-label pricing state explosion and
  support-duration pruning behavior.
- Identify whether the controlling interval can be bound-fathomed by stronger
  complete route-mask/inventory relaxation or must be closed by exact BPC tree.
- Plain compact CPLEX may be run only as a same-instance benchmark and optional
  verified UB source, never as BPC lower-bound proof.
