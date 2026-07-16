# Round 20 final report

## Outcome

Round 20 diagnosed the persistent-tree regression, fixed an inherited-state
memory defect, implemented every required switch and audit, and evaluated the
only proved scalable missing formulation family. The selected research arm is
`root_flow_only`, but it is **not promoted as the default** because the
eight-instance 900-second matrix contains one genuine regression
(`moderate_seed3301`). The recommended outcome is one further optimization
round followed by held-out random-instance testing.

All fresh production rows use executable SHA-256
`8f4832870148f8bd086a8d86ecda553da24801e9575b51412fa02d0414e4988b`.
The C++ test executable hash is
`fad6b4d151d440ab0bee0d19e02cc1e4713d589c67f5fb6b1262ea0d77e2af7a`.

## Mathematical exactness

The authoritative objective remains
`F = G + lambda * sum_i(w_i e_i)`. Positive targets, nonnegative finite
weights and nonnegative finite lambda are enforced. The factory-domain child
estimate is exactly the proved
`max(parent relaxation, L_I + lambda * weighted deviation lower bound)`;
infeasible/invalid domains fail closed. Exact incremental delta omits only
identical canonical rows and bounds; no dominance rule is used.

The root connectivity flow is a single-commodity O(MV^2) extended relaxation.
For every original route, the flow on a used arc equals the number of visited
stations downstream, proving projection feasibility. It has no route-mask
enumeration, route pool, V tier, seed/path logic, heuristic-zero cap, auxiliary
production solve, or plain-CPLEX information channel.

All 21 fail-closed exactness audits passed, including objective identity, toy
estimate bounds, diagnostic-relaxation bounds, inheritance, sibling isolation,
post-row state, delta equivalence, eager presolve compatibility, complete
MIP-start mapping, Round 19 coverage/lifecycle/finalization, no false
optimality, and root-flow projection/cardinality.

## Implementation correctness

The same binary exposes baseline `parent-copy/full-inherited-pack/deferred`,
`factory-domain`, `exact-incremental-delta`, eager rows, native verified MIP
start, and root connectivity flow. Every official global-tree run retains one
environment, one problem, one model read, one `CPXmipopt`, one native deadline,
traditional search, presolve on, one thread, and native final best bound.

Round 20 added explicit pre-row/awaiting-post-row/ready states. It also marks
actual Gini children so ordinary CPLEX descendants no longer contaminate
sibling statistics. Canonical inheritance state is immutable and shared;
copy-on-write occurs only for interval changes. Ambiguous deepest ordinary-node
state matches fail closed. This removes the observed metadata OOM without
weakening or deleting inherited constraints.

Mechanical tests passed: C++ 8 groups, Python 6 groups, negative-lambda
rejection and the prohibited-logic source scan.

## Forensic findings and causal evidence

The old interval model and compact global child are not identical. On V20 the
legacy model has 3,033 variables/24,250 rows/215,457 nonzeros versus about
2,124/10,616/62,010 for the compact child. Its scalable missing family is
single-commodity `fcb` route connectivity; other legacy-only route-mask/pool
families are excluded as non-unified.

All fresh Round 19 baseline sibling estimates tied. Maximum sibling delays
were 163.73 seconds on tight3101 and 165.30 seconds on high3202. The critical
high3202 child was never processed in the 300-second window. Deferred child
rows were correctly reoptimized and lifted observable relaxations, but eager
gates did not isolate a consistent speed gain. Factory-domain barely
discriminated siblings. Delta substantially reduced duplicate rows and API
time but had mixed bound/open-node effects. The full numbered causal answers
are in `root_cause_classification.md`.

## Performance

At 900 seconds, selected root flow versus exact Round 19 baseline was:

| Instance | Baseline LB / gap | Selected LB / gap | Result |
|---|---:|---:|---|
| tight_T_seed3101 | 0.017790 / 83.41% | 0.040398 / 62.33% | improved |
| high_imbalance_seed3202 | 1.623216 / 7.21% | 1.711326 / 2.17% | improved |
| high_imbalance_seed3201 | 2.302700 / 5.76% | 2.361672 / 3.34% | improved |
| moderate_seed3302 | 0.139455 / 28.72% | 0.143978 / 26.41% | improved |
| tight_T_seed3102 | 0.511665 / 14.82% | 0.549882 / 8.46% | improved |
| moderate_seed3301 | 0.046558 / 5.28% | 0.044972 / 8.51% | regressed |
| V12_M1 | 0.357201 / 0 | 0.357201 / 0 | certificate preserved |
| V12_M2 | 0.718504 / 0 | 0.718504 / 0 | certificate preserved |

At 1,800 seconds, selected root flow had a better valid LB and smaller gap than
fresh plain CPLEX on all four required comparisons:

| Instance | Selected LB / gap | Plain LB / gap |
|---|---:|---:|
| tight_T_seed3101 | 0.044356 / 58.64% | 0.020128 / 85.04% |
| high_imbalance_seed3202 | 1.732033 / 0.99% | 1.196922 / 31.93% |
| moderate_seed3302 | 0.145808 / 25.47% | 0.120950 / 43.60% |
| tight_T_seed3102 | 0.555471 / 7.53% | 0.484891 / 20.21% |

None certified at 1,800 seconds, so no unobserved time-to-zero is inferred.

## Certificates and noncertified bounds

V12_M1 and V12_M2 retained exact, independently verified certificates at
0.357200583208 and 0.718504070755 in both global-tree arms. Every other value
reported above is a valid native lower bound paired with a verified incumbent,
not an optimality claim. Positive-gap runs are never serialized as optimal.

## Engineering blockers and limitations

- The critical high3202 deferred child remained open but unprocessed, so its
  post-row relaxation is honestly `not_observed` rather than synthesized.
- Eager timing and native MIP start passed correctness gates but lacked
  consistent causal performance evidence and were not combined into the
  selected portfolio.
- The plain moderate3302 Stage 3 solver used a native 1,800-second limit but
  returned after 1,818.1 seconds wall-clock including shutdown/finalization.
  This wrapper overrun is retained and disclosed; it is benchmark-only and
  contributes no Tailored certificate or state.
- Interrupted/retried attempts are retained under `interrupted/`; none enters
  a fresh numerical table.
- GitHub CLI was unavailable in this environment; publication therefore uses
  ordinary non-force `git push` with local/tracking/live SHA verification.
- Eight instances do not establish stable general superiority.

## Artifact policy and recommended next step

The package retains commands, raw JSON, complete logs, traces, diagnostic
models, fingerprints, interrupted attempts, summaries and audits. CSV traces
larger than 256 KiB and LP exports are stored as `.gz`; summary/audit CSVs stay
plain. Manifest paths name the original files, so append `.gz` where the plain
artifact was compressed. The final package is about 394 MiB, and its largest
file is 9.35 MiB.

Do not enable root flow by default yet. In the next round, keep it as an exact
optional arm and target the remaining queue-order/formulation interaction,
especially moderate3301 non-regression, without adding unproved estimates or
non-unified legacy families. Then run a preregistered held-out random suite;
only that evidence can support a stable-superiority claim.
