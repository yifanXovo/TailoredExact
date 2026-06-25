# Paper-Core GF-RL-BPC Scope

The paper-facing exact algorithm is GF-RL-BPC, implemented by
`--method gcap-frontier --algorithm-preset paper-bpc-core`.

## Included In Paper-Core

- Full Gini-frontier decomposition over the original improving Gini range.
- Elementary route-load columns only.
- Exact-label route-load pricing under true current RMP duals.
- Deterministic, verifier-gated paper primal heuristic incumbents as upper
  bounds only. The default is `--primal-heuristic hga-tgbc` with an explicit
  seed and bounded number of runs.
- Projection dominance in exact-safe mode.
- Movement-domain tightening, projection bounds, and penalty-domain tightening.
- Vehicle-indexed operation and transfer-flow relaxations.
- Pickup/drop compatibility-flow relaxation audit with no-compatibility-first
  cutoff skipping: either model supplies only valid lower-bound evidence. For
  very short interval relaxation budgets (`<=2.5s`), paper-core may keep the
  valid weaker no-compatibility relaxation and skip the compatibility-flow
  audit solve with `compat_skipped=short_relaxation_budget`; this can weaken a
  lower bound but cannot overstate one.
- Split-before-tree initial frontier scheduling. When adaptive splitting is
  enabled, a broad unresolved interval with a valid lower bound may be deferred
  to the split ledger before running an expensive initial branch-price tree.
  This only changes work order: replaced parent intervals are ignored in the
  final certificate ledger and exactly covered by child intervals.
- Adaptive split depth 8 by default for paper presets unless explicitly
  overridden. This is still a ledger scheduling rule, not a certificate
  shortcut: every child interval must be empty, validly bound-fathomed, or
  closed by exact BPC pricing before original-problem optimality can be
  claimed.
- Complete route-mask operation-budget cuts only when route-mask enumeration is
  complete for the active instance threshold.
- Operation-budget relaxation portfolio. Operation-budget route-mask rows are
  valid strengthening rows, but their MIP can be harder to solve within an
  interval budget. Paper-core now keeps them enabled and, when they do not
  fathom an interval, also solves the same interval with operation-budget rows
  disabled. The solver keeps the stronger valid lower bound; both models are
  relaxations of the original problem.
- Route-pool incumbent master using verified elementary columns only.
- Final-inventory and operation-mode branching.
- Full certificate ledger aggregation across all active frontier intervals.

## Excluded From Paper-Core

The following modules are not paper-core evidence and are disabled by the
`paper-bpc-core` preset:

- Compact fallback or tailored compact portfolio certificates.
- Plain CPLEX certificates, except as benchmark rows.
- Arbitrary incumbent archive scanning. Archive scanning can be enabled
  explicitly for diagnostics with `--incumbent-archive-auto true`, but it is
  labeled `diagnostic_archive`, is not paper-reproducible by default, and never
  contributes lower-bound evidence.
- Hybrid/ng-DSSR pricing.
- Two-track relaxed-RMP columns.
- Relaxed-RMP certificates.
- Large-instance diagnostic modes and incomplete route-mask lists.
- Focus-only diagnostics.
- Imported focus interval bounds.
- Frontier resume shortcuts.
- Iterative closure automation.
- Completion lower-bound pricing pruning by default. It is certificate-safe
  when enabled explicitly, but current V12 evidence is mixed, so it remains a
  tuning/diagnostic option rather than a paper-core default.

These modules may be reported as diagnostics, baselines, appendix experiments,
or upper-bound sources when clearly labeled. They must not contribute to a
paper-core BPC lower bound or original-problem certificate.

## Certificate Gate

A `gcap-frontier` result can be reported as an original-problem certificate only
when:

- `status=optimal`;
- `solves_original_objective=true`;
- `certified_original_problem=true`;
- `verifier_passed=true`;
- `lower_bound=upper_bound=objective` within tolerance;
- `gap=0`;
- `frontier_covers_all_improving_gini_values=true`;
- `frontier_range_certificate_scope=original_full_improving_range`;
- `unresolved_intervals=0`;
- `invalid_bound_intervals=0`;
- `open_nodes=0`;
- every active interval is complete, empty, or validly bound-fathomed;
- every BPC tree node used for a certificate has true-dual exact pricing
  closure;
- heuristic, archive, CPLEX, route-pool, and imported incumbent sources are
  upper bounds only and have `incumbent_source_contributes_lower_bound=false`;
- duplicate negative columns, dominance-filtered negative columns, pricing
  time limits, or unfinished pricing enumeration are not treated as closure.

The command-line result should be audited with:

```powershell
python scripts\audit_bpc_certificate.py <json-or-directory> --csv-out <audit.csv> --fail-on-error
```

The C++ diagnostic command also checks the output guard directly:

```powershell
build\ExactEBRP.exe --method certificate-basis-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\paper_core_round_next\raw\certificate_guard_fixtures.json
```

## Current Status With Paper Heuristic UB

After replacing archive scanning with the reproducible paper primal heuristic,
the regenerated V12 rows are no longer automatically closed by the stronger
archived incumbent cutoff:

| instance | row | status | UB | LB | gap | certificate basis |
|---|---|---|---:|---:|---:|---|
| V12 M1 average | paper-core heuristic 300s | not closed | 0.364375057616 | 0.354350322125 | 0.027512134218 | partial inventory/route/Gini relaxation ledger |
| V12 M2 average | paper-core heuristic 300s | not closed | 0.756165366387 | 0.688739371450 | 0.089168319437 | partial inventory/route/Gini relaxation ledger |

The previous archive-dependent V12 M2 UB `0.719065249476` remains useful as a
diagnostic target for improving the primal heuristic, but it is not a
paper-core default input. These are regenerated engineering instances, not
confirmed historical paper targets. See `docs/benchmark_instance_policy.md`.
