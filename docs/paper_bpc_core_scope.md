# Paper-Core GF-RL-BPC Scope

The paper-facing exact algorithm is GF-RL-BPC, implemented by
`--method gcap-frontier --algorithm-preset paper-bpc-core`.

## Included In Paper-Core

- Full Gini-frontier decomposition over the original improving Gini range.
- Elementary route-load columns only.
- Exact-label route-load pricing under true current RMP duals.
- Verified route-load incumbents as upper bounds only.
- Projection dominance in exact-safe mode.
- Movement-domain tightening, projection bounds, and penalty-domain tightening.
- Vehicle-indexed operation and transfer-flow relaxations.
- Complete route-mask operation-budget cuts only when route-mask enumeration is
  complete for the active instance threshold.
- Route-pool incumbent master using verified elementary columns only.
- Final-inventory and operation-mode branching.
- Full certificate ledger aggregation across all active frontier intervals.

## Excluded From Paper-Core

The following modules are not paper-core evidence and are disabled by the
`paper-bpc-core` preset:

- Compact fallback or tailored compact portfolio certificates.
- Plain CPLEX certificates, except as benchmark rows.
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
- duplicate negative columns, dominance-filtered negative columns, pricing
  time limits, or unfinished pricing enumeration are not treated as closure.

The command-line result should be audited with:

```powershell
python scripts\audit_bpc_certificate.py <json-or-directory> --csv-out <audit.csv> --fail-on-error
```
