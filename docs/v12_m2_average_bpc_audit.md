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

## Required Next Work

- Run 1200s paper-core rows after the certificate guard when local budget
  allows.
- Use the node/pricing trace to profile exact-label pricing state explosion and
  support-duration pruning behavior.
- Identify whether the controlling interval can be bound-fathomed by stronger
  complete route-mask/inventory relaxation or must be closed by exact BPC tree.
- Plain compact CPLEX may be run only as a same-instance benchmark and optional
  verified UB source, never as BPC lower-bound proof.
