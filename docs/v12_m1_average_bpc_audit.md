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

## 1200s Paper-Core Result

| status | objective / UB | LB | gap | wall time | unresolved | invalid | open nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gcap_frontier_not_closed` | 0.357200583208 | 0.332675660948 | 0.0686586848205 | 1201.532s | 2 | 0 | 2 |

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
- 1200s progress CSV:
  `results/paper_bpc_core/progress/v12_m1_average_core_1200s.csv`.
- 1200s trace JSON:
  `results/paper_bpc_core/raw/v12_m1_average_core_1200s.trace.json`.
- 1200s interval trace CSV:
  `results/paper_bpc_core/raw/v12_m1_average_core_1200s.intervals.csv`.

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

After the split-before-tree scheduling fix, the same completion-LB pruning
diagnostic was rerun against the current paper-core work order. The comparison
is now apples-to-apples:

- Baseline split-before-tree 300s:
  `LB=0.331296710948`, gap `0.0725191208467`,
  `unresolved_intervals=3`, `open_nodes=3`, pricing time `66.750391s`.
- Split-before-tree plus completion-LB pruning 300s:
  `LB=0.331296710948`, gap `0.0725191208467`,
  `unresolved_intervals=3`, `open_nodes=3`, pricing time `58.9066437s`,
  `completion_lb_pruned_labels=23867430`.

The pruning is safe and does reduce some pricing work, but it does not improve
the valid global lower bound or certificate status on V12 M1 at this budget.
It remains a diagnostic option rather than a paper-core default.

The compatibility-flow relaxation ordering optimization was also checked for
300s. It is neutral on this instance: the paper-core row remains
`LB=0.268414876140`, `UB=0.357200583208`, gap `0.248559804329`, with two
unresolved leaves. The low-Gini child is cutoff-fathomed faster by the
no-compatibility relaxation, but the controlling child
`[0.178600291604,0.238133722139]` still does not receive a stronger bound
before the time limit.

The 1200s split-before-tree paper-core row improves the valid lower bound to
`0.332675660948`, but it still does not certify the instance. The active
unresolved intervals are `[0.223250364505,0.238133722139]`, which remains a
queued leaf with `tree_not_started_before_time_limit_or_reserve`, and
`[0.238133722139,0.297667152674]`, which has open BPC nodes. Runtime is now
dominated by exact-label pricing: `pricing_time_seconds=896.6435636`, compared
with `master_time_seconds=79.5333302` and `bound_time_seconds=211.0970326`.
The trace records 27 branch-price node summaries and 40 pricing-call summaries.
The largest observed pricing calls enumerate about 7.07M route states and
299.9M operation states per exact call, with negative columns still returned in
unclosed nodes. This confirms that the remaining V12 M1 bottleneck is exact
pricing/branch closure, not early frontier relaxation.

The next scheduling diagnostic increased the paper-core adaptive split depth
from 3 to 5 before starting expensive BPC trees. This is certificate-neutral:
parent intervals are replaced by exactly covering child intervals and no child
is certified unless its own bound/closure is valid. On V12 M1, the default
depth-5 300s row improves over both the old depth-3 300s row and the depth-3
1200s row:

- Depth-3 300s: `LB=0.331296710948`, gap `0.0725191208467`.
- Depth-3 1200s: `LB=0.332675660948`, gap `0.0686586848205`.
- Depth-5 300s: `LB=0.340282088370`, gap `0.0473641299419`.

The depth-5 row remains noncertified with three unresolved active leaves:
`[0.238133722139,0.267900437406]`,
`[0.223250364505,0.230692043322]`, and
`[0.230692043322,0.238133722139]`. The improvement shows that V12 M1 was
spending too much time in branch-price closure before extracting available
child relaxation bounds.

The depth-5 1200s row was then run with the preset default and the same
instance/hash. It did not improve the valid lower bound beyond the 300s
depth-5 row: `LB=0.340282088370`, `UB=0.357200583208`, gap
`0.0473641299419`, with `unresolved_intervals=3`, `open_nodes=29`, and
`invalid_bound_intervals=0`. The controlling active leaf is
`[0.230692043322,0.238133722139]`, whose lower-bound source remains
`focused_split_inherited_parent_lb`. That interval opened a BPC tree but did
not close before the time limit.

The 1200s trace is useful because it removes the earlier ambiguity about
whether the deeper split only needed more tree time. It records
`pricing_time_seconds=804.5765858`, `master_time_seconds=120.9521829`, and
`bound_time_seconds=269.381414`. The largest exact-label pricing calls still
enumerate roughly 6.8M to 6.9M route states and 291M to 297M operation states
per call, with support-duration and completion-LB pruning both at zero in the
default paper-core row. Several node relaxations close locally, but the branch
tree still has 29 open nodes at timeout. This confirms that V12 M1 now needs
certificate-safe pricing-state reduction or stronger exact branch closure on
the narrow controlling child, rather than additional broad frontier splitting.

The next code audit instrumented exact-label label dominance inside pricing.
The production-safe trace fields now include `label_dominance_comparisons`,
`label_dominance_pruned_labels`, and
`label_dominance_cross_pickup_pruned_labels` in both raw JSON and the plateau
trace aggregate. A V12 M1 300s validation row remains noncertified with the
same certificate-relevant bound (`LB=0.340282088370`, gap
`0.0473641299419`) and records `330135991` dominance comparisons and
`186012791` exact-bucket dominance prunes. The cross-pickup count is zero in
paper-core.

An attempted cross-pickup dominance rule was tested and rejected before being
kept as a default. The rule is mathematically plausible only as a sufficient
dominance check, but a naive implementation required billions of comparisons
on V12 M1 and made exact pricing calls slower rather than faster. It was
removed from the paper-core path. The retained change is diagnostic
instrumentation for the existing exact-bucket dominance, not a certificate
shortcut.

The next certificate-neutral scheduling change increased the paper-core default
adaptive split depth from 5 to 6. On V12 M1, the default 300s row now reaches
`LB=0.341121462223`, `UB=0.357200583208`, gap `0.0450142629691`, with
`unresolved_intervals=3` and `invalid_bound_intervals=0`. The previous
controlling child `[0.230692043322,0.238133722139]` is now bound-fathomed by
the inventory/route/Gini relaxation. The remaining controlling active leaves
are `[0.238133722139,0.253017079773]`,
`[0.253017079773,0.267900437406]`, and
`[0.223250364505,0.230692043322]`. No original certificate is claimed because
these leaves are still unresolved, but the valid lower bound improves again
without relying on incomplete BPC pricing closure.

The corresponding depth-6 default 1200s row improves the valid lower bound to
`LB=0.344881668930`, `UB=0.357200583208`, gap `0.0344873856805`, with
`unresolved_intervals=3`, `open_nodes=4`, and `invalid_bound_intervals=0`.
The controlling active leaf is now `[0.223250364505,0.230692043322]`. That
leaf has a valid inventory/route/Gini lower bound, opens a BPC tree with 27
nodes, and leaves one node open at timeout. The run spends
`pricing_time_seconds=778.7256487`, `master_time_seconds=119.4459118`, and
`bound_time_seconds=293.5659804`. This changes the immediate plateau diagnosis:
the first 300s are still dominated by interval relaxation and splitting, but
the extra 900s are dominated by exact-label pricing/tree closure on a narrow
leaf. No original certificate is claimed.

Because the depth-6 1200s tree work did not improve the controlling leaf enough
to close it, the paper-core default split depth was increased again to 7. The
default depth-7 300s row reaches `LB=0.344613240900`,
`UB=0.357200583208`, gap `0.035238862701`, with
`unresolved_intervals=3`, `open_nodes=3`, and `invalid_bound_intervals=0`.
This nearly matches the depth-6 1200s lower bound in about one quarter of the
time and does so without entering expensive pricing. The result is still not an
original-problem certificate, but it confirms that one more certificate-neutral
split level is currently more productive than early branch-price tree work on
V12 M1.

## Required Next Work

- Use the depth-7 interval ledger and the depth-6 1200s per-node/pricing traces to
  reduce the long focused-retry pricing calls on
  `[0.223250364505,0.230692043322]`. Candidate work should target exact
  operation-state pruning, stronger branch closure, or more frequent
  time-limit/checkpoint handling inside exact pricing, not lower-bound
  shortcuts.
- Compare against plain compact CPLEX on the same instance file/hash only as a
  benchmark, not as BPC proof.
- If compact and BPC objectives differ, fix parser/objective conventions before
  any performance claim.
