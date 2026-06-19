# Tailored Exact Portfolio Protocol

Date: 2026-06-14.

## Scope

The tailored exact portfolio solves the original EBRP objective

```text
minimize G + lambda * P
```

only when one of its exact modules proves `gap=0` and the independent verifier passes. The portfolio is not a heuristic, and a positive-gap module result is never reported as optimal.

## Modules

1. `original_bpc`: full Gini-frontier route-load branch-price-and-cut (`gcap-frontier`).
2. `original_compact`: strengthened compact branch-and-cut with globally valid cuts.
3. `plain_cplex`: plain compact CPLEX benchmark.
4. `diagnostic` or `subproblem`: pricing, master, cuts, fixed-cap, restricted-pool, and incumbent-only runs.

Compact fallback certificates are original-problem certificates when their MIP gap closes, but they are not BPC certificates.

## Portfolio Flow

1. Run pure BPC with the configured BPC-owned incumbent generator, complete route-mask bounds where enabled, exact pricing, and full-frontier certificate checks.
2. If BPC returns `status=optimal`, `gap=0`, `verifier_passed=true`, `unresolved_intervals=0`, `invalid_bound_intervals=0`, and `open_nodes=0`, report:

```text
portfolio_status = optimal
portfolio_certificate_type = pure_bpc
portfolio_result_file = BPC result file
```

3. If BPC stalls, run strengthened compact branch-and-cut as an exact fallback. BPC incumbents may be used only as verified upper bounds or warm starts; BPC lower bounds and compact lower bounds are not merged unless a formal combined proof is implemented.
4. If compact branch-and-cut returns `status=optimal`, `gap=0`, and `verifier_passed=true`, report:

```text
portfolio_status = optimal
portfolio_certificate_type = compact_fallback
portfolio_result_file = compact result file
```

5. If neither module certifies, report the best verified incumbent, valid lower bound, gap, unresolved intervals, open nodes, and bottleneck. The portfolio status remains not certified.

## Runtime Reporting

Do not report compact fallback runtime as BPC runtime.

When reporting portfolio runtime, use the sum of the modules actually run under the selected protocol. Also report module runtimes separately:

```text
bpc_runtime_seconds
compact_runtime_seconds
portfolio_runtime_seconds
```

If the protocol stops after a BPC certificate, compact fallback runtime is `0` for that portfolio run even if standalone compact experiments also exist.

## Certificate Conditions

For `pure_bpc`, the certificate fields are:

```text
method_scope = original_bpc
is_bpc = true
solves_original_objective = true
status = optimal
lower_bound = upper_bound = objective
gap = 0
verifier_passed = true
unresolved_intervals = 0
invalid_bound_intervals = 0
open_nodes = 0
```

For `compact_fallback`, the certificate fields are:

```text
method_scope = original_compact
is_bpc = false
solves_original_objective = true
status = optimal
lower_bound = upper_bound = objective
gap = 0
verifier_passed = true
```

Diagnostic runs, fixed-cap subproblems, restricted path/column pools, and CPLEX-incumbent-warmed BPC diagnostics are not portfolio certificates unless wrapped by one of the exact certificate conditions above.

## Current Portfolio Status

Current target-instance status:

| Instance | Portfolio certificate | Status |
|---|---|---|
| `test_data_V10_M2_average.txt` | pure_bpc | optimal |
| `test_data_V10_M1_average.txt` | pure_bpc | optimal |
| `test_data_V10_M2_low.txt` | compact_fallback | optimal |
| `test_data_V12_M1_average.txt` | pure_bpc | optimal |
| `test_data_V12_M2_average.txt` | none | not certified |

The portfolio certifies four of the five target instances. The remaining open target is V12 M2 average.
