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

## Required Next Work

- Run a 1200s split-before-tree paper-core row when local budget allows; the
  existing 1200s row is useful only as a scheduling-regression diagnostic.
- Use the node/pricing trace to profile exact-label pricing state explosion and
  support-duration pruning behavior.
- Identify whether the controlling interval can be bound-fathomed by stronger
  complete route-mask/inventory relaxation or must be closed by exact BPC tree.
- Plain compact CPLEX may be run only as a same-instance benchmark and optional
  verified UB source, never as BPC lower-bound proof.
