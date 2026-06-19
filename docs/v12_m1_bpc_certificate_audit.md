# V12 M1 Pure-BPC Certificate Audit

Date: 2026-06-14.

Audited result: `results/closure7200_v12_m1_average_strong_bpcseed.json`.

## Certificate Decision

`audit_certified = true`.

The result is accepted as a pure full Gini-frontier route-load BPC certificate for the original EBRP objective. It is not a compact fallback, not a CPLEX-warmed diagnostic, and not restricted-pool optimality.

## Key Fields

| Field | Value |
|---|---:|
| method | 
gcap-frontier
 |
| method_scope | 
original_bpc
 |
| certificate_type | 
full_gini_frontier_route_load_bpc
 |
| status | 
optimal
 |
| objective | 
0.690938574743
 |
| lower_bound | 
0.690938574743
 |
| upper_bound | 
0.690938574743
 |
| gap | 
0
 |
| verifier_passed | 
True
 |
| unresolved_intervals | 
0
 |
| invalid_bound_intervals | 
0
 |
| open_nodes | 
0
 |
| pricing_closed_nodes | 
20
 |

## Frontier Evidence

Improved incumbent note:

```text
adaptive frontier pass 1 found improved incumbent in interval 116, objective=0.690939
```

Last retry note:

```text
adaptive pass 1 retry 1 interval 116 [0.47045,0.47045] complete=false, lower_bound_valid=true, certified_by_bound=true, empty_interval=false, has_incumbent=true, tree_lb=0.690939, interval_lb=0.690939, inventory_relax_lb=0.690939, resource_lb=0.171452, incumbent_cutoff=0.690939, early_stop_target=0.690939, nodes=15, columns=4988, pricing_calls=64, pricing_time=708.875, master_time=1456.25, bound_time=0, cuts_added=0, open_nodes=6
```

Frontier summary note:

```text
frontier certification summary: closed_intervals=0, bound_certified_intervals=72, skipped_intervals=0, unresolved_intervals=0, invalid_bound_intervals=0, final_full_objective_range=true
```

The retry note is not a closed branch-price tree certificate: it has `complete=false` and `open_nodes=6`. It found the improved incumbent, and the final proof comes from the full frontier ledger after bound-fathoming at the new incumbent cutoff. The top-level JSON has `unresolved_intervals=0`, `invalid_bound_intervals=0`, `open_nodes=0`, and `gap=0`.

## Artifact Warning

The JSON field `log_file` points to `logs/closure7200_v12_m1_average_strong_bpcseed.log`, but that file was not present during this audit. The stdout, stderr, and JSON embedded notes were present and audited. This is an artifact-preservation warning, not a certificate failure.

Full machine-readable audit: `results/v12_m1_bpc_certificate_audit.json`.
