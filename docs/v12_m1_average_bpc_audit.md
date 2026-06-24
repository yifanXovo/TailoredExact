# V12 M1 Average GF-RL-BPC Audit

Date: 2026-06-25

## Instance

- Path: `reference/regen_candidate_V12_M1_average.txt`
- Scope: regenerated engineering input in the local repository.
- SHA256: `E395CFEF336D3407A65F04D7E201AA29AC844A08AFF25D1991CE6983E5E9508D`

No historical source file was found in `reference/` or `testdata/`; this audit
therefore records the exact regenerated candidate file and does not claim it is
the historical paper target.

## Baseline Command

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_60s.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v12_m1_average_core_60s.json
```

## 60s Paper-Core Result

| status | objective / UB | LB | gap | wall time | unresolved | invalid | open nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gcap_frontier_not_closed` | 0.357200583208 | 0.178600291604 | 0.5 | 78.2769s | 2 | 0 | 1 |

Certificate audit: passed as **noncertified**. The result is not reported as
optimal.

## 300s Paper-Core Result

| status | objective / UB | LB | gap | wall time | unresolved | invalid | open nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gcap_frontier_not_closed` | 0.357200583208 | 0.268414876140 | 0.248559804329 | 318.484s | 2 | 0 | 5 |

Certificate audit: passed as **noncertified**. The result is not reported as
optimal.

## Plateau Evidence

- `frontier_min_interval_lower_bound=0.178600291604`.
- `frontier_lower_bound_source=gamma_floor`.
- `full_certificate_rejection_reason=unresolved_intervals`.
- Controlling interval: `4:[0.1786,0.238134]`.
- Two of four relevant intervals were bound-fathomed by the
  inventory/route/Gini relaxation.
- The current run spent about 50.9984s in interval relaxation accounting:
  28.1590s on `[0,0.119067]` and 22.8394s on `[0.119067,0.1786]`.
- The controlling interval has `open_nodes=1` but `bpc_nodes=0`; the trace
  reason is `tree_not_started_before_time_limit_or_reserve`. This is a queued
  unresolved leaf, not a partially explored branch-price tree.
- The progress log reports 1,133,538 generated columns before final summary;
  these appear dominated by incumbent/route-pool generation and available
  interval work, not closed branch-price nodes.

Trace artifacts:

- 60s progress CSV:
  `results/paper_bpc_core/progress/v12_m1_average_core_60s.csv`.
- 300s progress CSV:
  `results/paper_bpc_core/progress/v12_m1_average_core_300s.csv`.
- 20s trace validation JSON:
  `results/paper_bpc_core/raw/v12_m1_average_core_trace_20s.trace.json`.
- 20s interval trace CSV:
  `results/paper_bpc_core/raw/v12_m1_average_core_trace_20s.intervals.csv`.
- 60s trace JSON:
  `results/paper_bpc_core/raw/v12_m1_average_core_60s.trace.json`.
- 60s interval trace CSV:
  `results/paper_bpc_core/raw/v12_m1_average_core_60s.intervals.csv`.
- 300s trace JSON:
  `results/paper_bpc_core/raw/v12_m1_average_core_300s.trace.json`.
- 300s interval trace CSV:
  `results/paper_bpc_core/raw/v12_m1_average_core_300s.intervals.csv`.

The new trace schema currently exposes the active interval ledger, per-interval
aggregate tree counters when a tree starts, and aggregate global pricing
counters. It now also emits per-node and per-pricing-call arrays when a
branch-price tree actually starts. In this 60s V12 M1 row those arrays are
empty because the controlling leaf is queued but not expanded before the
time/reserve stop.

## Initial Diagnosis

The 60s run is not a pricing-closure certificate problem yet: the controlling
interval remains at the gamma-floor lower bound and the branch-price tree for
that leaf has not started before the time/reserve stop. The immediate
bottleneck is frontier scheduling/time allocation plus expensive complete
inventory/route/Gini relaxation on earlier intervals, not a completed BPC tree
with a negative-pricing contradiction.

The 300s run starts BPC trees and raises the valid lower bound to
0.268414876140, but it still does not close. The controlling leaf
`4:[0.1786,0.238134]` inherits the parent lower bound after adaptive splitting
and is still queued (`bpc_nodes=0`, `open_nodes=1`). Two explored branch-price
nodes remain unresolved with `not_closed_reason=pricing_did_not_close`.
Captured pricing calls are exact-label and expensive: the largest observed
call enumerates about 7.07M route states and 299.9M operation states in about
25.9s, returning negative columns. Pricing, not RMP solving, dominates the
started BPC work.

An explicit completion lower-bound pruning diagnostic was also run for 300s.
It is certificate-safe but not part of the default paper-core preset. On this
instance it reached the same LB/gap as the baseline 300s row, with
`completion_lb_pruned_labels=51756831` and captured operation states reduced
from about 1.48B to 1.11B. The row still has unresolved intervals and pricing
timeouts, so it does not change the certificate status.

The compatibility-flow relaxation ordering optimization was also checked for
300s. It is neutral on this instance: the paper-core row remains
`LB=0.268414876140`, `UB=0.357200583208`, gap `0.248559804329`, with two
unresolved leaves. The low-Gini child is cutoff-fathomed faster by the
no-compatibility relaxation, but the controlling child
`[0.178600291604,0.238133722139]` still does not receive a stronger bound
before the time limit.

## Required Next Work

- Run 1200s paper-core rows with the new certificate audit when local budget
  allows.
- Use the per-node and per-pricing-call trace records to identify whether
  exact-label pricing can be tightened with certificate-safe pruning.
- Compare against plain compact CPLEX on the same instance file/hash only as a
  benchmark, not as BPC proof.
- If compact and BPC objectives differ, fix parser/objective conventions before
  any performance claim.
