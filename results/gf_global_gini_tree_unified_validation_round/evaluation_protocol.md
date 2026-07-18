# Preregistered Round 22 unified evaluation protocol

This protocol and the three arm manifests are frozen before any official production comparison. Production settings cannot change in response to results.

## Fixed arms

S0 is the stable reference: one persistent global Gini tree, F0 `round20-current` connectivity flow, parent-copy child estimate, full inherited row pack, deferred child rows, native MIP start off, one environment/problem/read/`CPXmipopt`, one thread, presolve on, traditional search, native best-bound node selection, and default native cuts/probing/heuristics. S1 is identical except for F3 `normalized-start-coupled` flow. Plain is the original compact CPLEX model with one thread, presolve on, traditional search, native node selection and default native cuts/probing/heuristics. All request/read back exact-zero relative and absolute MIP gaps and enable the same dense progress policy.

No arm may inspect V, M, capacity, time limit, imbalance, route count, name, seed, path, family, known objective, or another arm's output to choose an algorithm or parameter. S0 is always F0; S1 is always F3. Plain information never enters Tailored runs. Toy enumeration is an external test oracle only.

## Stages and budgets

All solves are serial on the same machine. Native deadline is nominal process-wall budget minus `min(30, max(2, 0.02 * budget))` seconds; the reserve is for serialization/finalization. No nominal budget exceeds 3,600 seconds.

- Stage 0: clean release build; seven C++ suites; Round 20 Python regression; static model/certificate/dispatch audits; Round 21 no-rerun migration; dense mocks; toy exactness; short live plain/S0/S1 callback checks.
- Stage 1: V12_M2, moderate_seed3301, and high_imbalance_seed3202 live trajectory gates for S0, S1, and plain. Each official live row must retain at least 20 non-final native observations, emit all 11 preregistered checkpoint labels through 120 seconds, cover at least eight checkpoints at or before its last native CPLEX observation, have at least `ceil(0.8 * eligible checkpoints)` fresh within that native observation horizon, and contain the arm-appropriate documented progress source (global/local progress for plain, or the read-only snapshot subpath at the start of Tailored's relaxation context). Later checkpoints remain explicitly stale rather than being counted against native callback density; see `stage1_freshness_erratum.md`. Matched 300-second dense-on/dense-off overhead diagnostics are run for S0 and S1 on all three cases where the native pipeline remains operational. Off rows are excluded from performance tables.
- Stage 2: all eight existing instances × S0/S1/plain at 900 seconds (24 rows).
- Stage 3: all eight existing instances × S0/S1/plain at 1,800 seconds (24 rows).
- Stage 4: all six held-out instances × S0/S1/plain at 900 seconds (18 rows).
- Stage 5: conditional 3,600-second comparisons, with S0/S1/plain on every selected case. V12_M2 is selected only if a method has native status 101 but an unresolved certificate-implementation issue remains after Stage 3. Otherwise it is not selected. Exactly one existing V20 case is selected as the instance with the smallest minimum final project gap over all complete Stage-3 arm rows (ties by instance ID). Exactly one held-out V20 case is selected by the same rule over complete Stage 4 (ties by instance ID). Selection is by instance after considering every arm, never by the leading algorithm. If no row for a suite has a verified UB and valid LB, that suite contributes no Stage-5 case.

An official row is complete only when process return code is zero; executable/source/manifest/instance hashes match; expected flow and all fixed options resolve; relative/absolute parameter IDs, setter/getter codes, requested/effective values validate; lifecycle and finalization complete; native status is one of the audited outcomes; model gate passes; dense raw/final/flush/read-only fields validate; checkpoint extraction and endpoint consistency pass; and its command/environment/artifact record is retained. Failed or interrupted attempts are archived under `attempts/excluded` and never enter official tables.

Raw native bound, incumbent, and processed-node observations are never clamped, enveloped, rounded, suppressed, or repaired. The integrity table reports every monotonicity reversal, its count, and maximum full-precision step. Native callback monotonicity is a solver diagnostic, not a data-integrity premise: no reversal magnitude can itself invalidate an otherwise authoritative trace. Structural integrity remains fail-closed for non-strict timestamps, missing solver-final evidence, final-record/native-JSON endpoint mismatch, parse failures, missing files, flush/finalization failures, and hash/lifecycle violations. This policy is documented in `trajectory_monotonicity_erratum.md` and has no role in solver status, the engineering-exact certificate, the model gate, the independent verifier, objectives, final bounds, gaps, or comparisons.

## Metrics

Certificate counts are status-101 engineering-exact, status-102 tolerance-only, status-107/108 time limit, status-103 infeasible, status-115 rejected, and other rejected outcomes. Strict time is native runtime only for a valid strict row. Native objective, native LB, verified UB, recomputed objective, residuals, and gaps remain separate.

At each common checkpoint, compare fresh native LB; independently verified-UB-normalized project gap; nodes/open nodes; simplex iterations; branch counts; phase; and sibling delay. Stale and unavailable cells remain labeled. Crossings at 20%, 10%, 5%, 2%, 1%, 0.5%, and 0.1% use first observed and preceding observations as an interval. Normalized progress is `clamp(1 - project_gap, 0, 1)` and normalized AUC is its trapezoidal time integral divided by the observed horizon. Final LB, valid project gap, strict count/time, AUC, threshold crossings, robustness, and search mechanics are reported; relative gap alone is not used when UBs differ.

For paired S1-versus-S0 classification, strict certificate dominates non-strict; among two strict rows, smaller strict time is better (1e-6-second equality tolerance); otherwise higher native LB is better when both use the same comparison UB (1e-9 relative tolerance), then higher normalized AUC (1e-6 tolerance). A pair is `improve`, `regress`, `tie`, or `unavailable`. Counts are reported separately for existing and held-out suites and at each horizon.

## Predeclared stable-mainline decision

The decision is global. F3 replaces F0 only if complete existing and held-out evidence shows broad non-regression and a meaningful overall advantage in at least one primary dimension: strict-certificate count/time, final valid LB, dense bound progress, or cross-suite robustness. Broad non-regression requires no certificate-count loss in either suite, no more than one material paired regression total, regressions fewer than improvements in each suite, and no model/certificate/lifecycle/instrumentation validity failure specific to S1.

If evidence is mixed by class or suite, if F3 materially regresses multiple instances, or if the advantage is not robust, S0/F0 remains the single stable paper mainline and S1/F3 remains an exact research variant. No per-instance portfolio or dispatcher is allowed. This qualitative rule will not be rewritten after results.
