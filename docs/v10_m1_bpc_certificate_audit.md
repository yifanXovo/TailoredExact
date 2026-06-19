# V10 M1 Pure-BPC Certificate Audit

Date: 2026-06-14.

Audited result: `results/closure3600_v10_m1_average_strong_bpcseed.json`.

## Certificate Decision

`audit_certified = true`.

The result is accepted as a pure full Gini-frontier route-load BPC certificate for the original EBRP objective. It is not a compact fallback, not a CPLEX-warmed diagnostic, and not restricted-pool optimality.

## Key Fields

| Field | Value |
|---|---:|
| method | gcap-frontier |
| method_scope | original_bpc |
| solves_original_objective | true |
| is_bpc | true |
| certificate_type | full_gini_frontier_route_load_bpc |
| status | optimal |
| objective | 0.49262512358 |
| lower_bound | 0.49262512358 |
| upper_bound | 0.49262512358 |
| gap | 0 |
| verifier_passed | true |
| certified_original_problem | true |
| unresolved_intervals | 0 |
| invalid_bound_intervals | 0 |
| open_nodes | 0 |
| pricing_closed_nodes | 107 |

## Frontier Evidence

Final exact-pricing retry note:

```text
adaptive pass 1 retry 1 interval 71 [0.245632,0.245636] complete=true, lower_bound_valid=true, certified_by_bound=true, empty_interval=false, has_incumbent=true, tree_lb=0.492625, interval_lb=0.492625, inventory_relax_lb=0.492624, resource_lb=0.204298, incumbent_cutoff=0.492625, early_stop_target=inf, nodes=65, columns=9761, pricing_calls=349, pricing_time=179.509, master_time=171.83, bound_time=0, cuts_added=0, open_nodes=0
```

Frontier summary note:

```text
frontier certification summary: closed_intervals=1, bound_certified_intervals=43, skipped_intervals=0, unresolved_intervals=0, invalid_bound_intervals=0, final_full_objective_range=true
```

These notes show the last live interval closed with `complete=true` and `open_nodes=0`, and the final frontier ledger has `unresolved_intervals=0`, `invalid_bound_intervals=0`, and `final_full_objective_range=true`.

## Artifact Warning

The JSON field `log_file` points to `logs/closure3600_v10_m1_average_strong_bpcseed.log`, but that file was not present during this audit. The stdout file `logs/closure3600_v10_m1_average_strong_bpcseed.stdout.txt`, stderr file `logs/closure3600_v10_m1_average_strong_bpcseed.stderr.txt`, and JSON embedded notes were present and audited.

This is an artifact-preservation warning, not a certificate failure.

Full machine-readable audit: `results/v10_m1_bpc_certificate_audit.json`.
