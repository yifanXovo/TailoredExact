# Paper-Core GF-RL-BPC Scope

The paper-facing exact algorithm is GF-RL-BPC, implemented by
`--method gcap-frontier --algorithm-preset paper-bpc-core`.

## V20 Certificate-Round Status

The V20 certificate round did not promote a new V20 paper-core preset.
`paper-bpc-core-adaptive`, `--relaxation-portfolio-mode exhaustive`, and
focused interval-closure runs remain candidate/diagnostic configurations.
Focused interval rows are not original-problem certificates unless their
coverage is safely merged into the full frontier ledger.  Canonical paper-core
still excludes archive scanning and treats every incumbent source as
upper-bound-only evidence.

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

## Interval Cutoff Oracle Status

`--method interval-cutoff-oracle` is an exact interval-local certificate module,
not a replacement for `paper-bpc-core`.  It asks whether a compact original
fixed-Gini-interval MIP has any solution with objective below the incumbent
cutoff.  Proven infeasibility can close exactly the matched frontier leaf after
`scripts\merge_interval_oracle_results.py` verifies full-ledger coverage.
Timeouts and unverified feasible MIP solutions remain diagnostic.

The V20 exact certificate round certified `high_imbalance_seed3202` through the
normal full-frontier relaxation ledger before interval-oracle merge was needed.
The oracle remains available for future unresolved leaves.

The V20 replication round reproduced `high_imbalance_seed3202` three times and
also certified `tight_T_seed3101`.  This justifies a separate paper-candidate
exact portfolio preset, `paper-exact-v20-certificate`, for further V20 stress
testing.  It is intentionally distinct from canonical `paper-bpc-core`:

- native HGA-TGBC remains UB-only;
- archive scanning remains disabled;
- fixed mip-light compact-flow relaxation with connectivity is enabled;
- exact interval cutoff oracle evidence must be merged through a full-ledger
  coverage audit;
- BPC fallback remains off by default unless exact pricing closes a focused
  interval.

The sealed paper-pipeline round adds `--paper-run-sealed true` to this preset.
Sealed rows must be generated from one command template and cannot use external
incumbents, arbitrary local archive scanning, focus-only certificates, imported
focus bounds, or known UB injection. Automatic interval-oracle closure is
allowed only for final unresolved leaves from the same full-frontier run and
only when the compact original fixed-interval cutoff MIP proves infeasibility.

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

The early paper-heuristic transition rows did not close the regenerated V12
instances.  That status has been superseded by the native HGA-TGBC migration and
relaxation scheduling/cutoff fixes.  Current audited behavior is:

| instance | row | status | UB | LB | gap | certificate basis |
|---|---|---|---:|---:|---:|---|
| V12 M1 average | paper-core 300s | not closed | 0.357200583208 | 0.332675660948 | 0.0686586848205 | one unresolved interval |
| V12 M1 average | paper-core 600s | optimal | 0.357200583208 | 0.357200583208 | 0 | relaxation-only full frontier |
| V12 M2 average | paper-core 300s | optimal | 0.718504070755 | 0.718504070755 | 0 | relaxation-only full frontier |

All rows use regenerated engineering instances, not confirmed historical paper
targets.  Archive-dependent UBs remain diagnostic-only and are not paper-core
default inputs. See `docs/benchmark_instance_policy.md`.
## Sealed Completion Scope

`paper-exact-v20-certificate` is the sealed paper-candidate portfolio preset.
It is an exact portfolio around the same Gini-frontier ledger: native HGA-TGBC
provides UB-only incumbent evidence, relaxation and interval certificates
provide lower-bound evidence, and BPC fallback is certificate-safe only when
exact pricing closes.

The sealed completion wrapper is part of the paper-run scope because it prevents
silent run exits. It may synthesize only noncertified checkpoint artifacts. It
must not synthesize optimality, merge focused interval rows without exact
coverage, or use archive/known-UB evidence.

## Sealed All-Leaf Closure Extension

The sealed closure round keeps the same paper-run restrictions and extends the
automatic interval oracle from one selected leaf to every final unresolved leaf.
The option set:

```text
--auto-interval-oracle-order all
--auto-interval-oracle-max-leaves all
--auto-interval-oracle-split-on-timeout true
```

is certificate-safe because it only adds interval-local exact cutoff MIP
attempts after a full frontier ledger has been built. A leaf is merged as closed
only with proven interval infeasibility or with a verified improving incumbent
followed by a full frontier restart. Timeout leaves remain unresolved.

This extension is allowed inside `paper-exact-v20-certificate`; it does not
change the rule that heuristic, route-pool, CPLEX, and BPC-generated incumbents
are upper bounds only. BPC fallback remains nondefault certificate evidence
unless exact pricing closes the interval.
