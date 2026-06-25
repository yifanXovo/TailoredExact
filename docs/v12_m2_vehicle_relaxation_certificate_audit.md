# V12 M2 Vehicle-Relaxation Certificate Audit

## Reproduction

Instance: `E:\codes\ExactEBRP\reference\regen_candidate_V12_M2_average.txt`

SHA256: `0BB0416CC9540FFFBB91299D5C9ED3D6C2363906424005B1C40B4E3829DDF4F0`

Internal instance hash: `52a1bbf5593d7d3f`

Command: `results/paper_core_round_next/commands.md`, row
`v12_m2_vehicle_relaxation_repro_1200s`.

Reproduced result:

| row | status | objective | LB | UB | gap | runtime | certified |
|---|---|---:|---:|---:|---:|---:|---|
| custom vehicle-relaxation repro | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 0 | 716.3878663 | true |

The certificate audit over `results/paper_core_round_next/raw` reports zero
failures.

## Certificate Basis

The reproduced custom row and the integrated paper-core rows are not BPC-tree
certificates. They are relaxation-only frontier certificates. Exact pricing
closure is not required because every final active interval is bound-fathomed
by the inventory/route/Gini relaxation stack.

Final V12 M2 paper-core 300s ledger:

| interval | range | status | LB | certificate basis | pricing required |
|---:|---|---|---:|---|---|
| 0 | [0, 0.179766312369] | bound_fathomed | 0.719065249476 | inventory_route_gini_relaxation_fathomed | false |
| 1 | [0.179766312369, 0.359532624738] | bound_fathomed | 0.719065249476 | inventory_route_gini_relaxation_fathomed | false |
| 3 | [0.539298937107, 0.719065249476] | bound_fathomed | 0.719065249476 | inventory_route_gini_relaxation_fathomed | false |
| 4 | [0.359532624738, 0.449415780923] | bound_fathomed | 0.719065249476 | inventory_route_gini_relaxation_fathomed | false |
| 6 | [0.449415780923, 0.494357359015] | bound_fathomed | 0.719065249476 | inventory_route_gini_relaxation_fathomed | false |
| 7 | [0.494357359015, 0.539298937107] | bound_fathomed | 0.719065249476 | inventory_route_gini_relaxation_fathomed | false |

Parent intervals 2 and 5 are replaced by children and are not part of the final
certificate ledger.

## Why Pricing Closure Is False

The custom repro has `pricing_closure_certified_exact=false` and a negative
remaining reduced cost. This does not invalidate the certificate, because
`frontier_tree_closed_interval_count=0` and no final interval uses
`pricing_closed_bpc_tree` as its certificate basis.

## Paper-Core Integration Result

After adding the operation-budget relaxation portfolio, `paper-bpc-core`
certifies the same regenerated V12 M2 instance without custom flags:

| row | status | objective | LB | UB | runtime | unresolved | open nodes |
|---|---|---:|---:|---:|---:|---:|---:|
| V12 M2 paper-core 300s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 217.7839095 | 0 | 0 |
| V12 M2 paper-core 1200s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 215.7528562 | 0 | 0 |

Both rows pass `scripts/audit_bpc_certificate.py --fail-on-error`.

