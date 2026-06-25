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
- Verified incumbent archive routes as upper-bound cutoffs only. When
  `paper-bpc-core` accepts a verified archive incumbent and the incumbent mode
  is the preset default `auto`, the later BPC-owned auto incumbent portfolio is
  skipped to avoid duplicate UB-only work. This changes only scheduling and
  incumbent search time; it never contributes to a lower bound or certificate.
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
