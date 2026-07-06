# S-Range Denominator Refinement

This note documents the S-domain refinement added for the `paper-gf-tailored-bc` low-Gini strengthening round. Here `S = sum_i r_i` is the denominator in the fixed-interval Gini expression.

## Modes

The command line exposes:

- `--tailored-bc-s-bucket-ledger off|diagnostic|paper-safe`
- `--tailored-bc-s-bucket-count <K>`
- `--tailored-bc-s-bucket-policy uniform|adaptive-snapshot|adaptive-cutoff|adaptive-hybrid`
- `--tailored-bc-s-bucket-time-budget <seconds>`
- `--tailored-bc-s-bucket-merge-audit true|false`

The default is off. Diagnostic buckets may be used for bound diagnosis, but not as paper-core certificate evidence. Paper-safe buckets may contribute only through complete audited parent coverage and valid child certificates.

## Parent S-Domain

For each fixed Gini interval, the compact model computes a valid parent domain `[parent_S_L,parent_S_U]` from target-ratio variables and the intersection of capacity, penalty-domain, movement-reachability, and model-domain bounds. Result JSONs record:

- `parent_S_L`
- `parent_S_U`
- `S_domain_source`
- `S_domain_proof_status`
- `S_domain_audit_passed`

The proof status must be `valid_interval_from_model_domain_bounds` before any S-bucket ledger can be treated as paper-safe.

## Bucket Ledger Semantics

A paper-safe bucket ledger partitions the parent S-domain into child leaves `[S_L^b,S_U^b]`. Each child adds:

```text
S_L^b <= S <= S_U^b
```

and solves the same original fixed-Gini interval model restricted to that S-bucket. The parent interval can close by S-bucket merge only if:

1. child buckets exactly cover `[parent_S_L,parent_S_U]`;
2. no child extends outside the parent domain;
3. no child buckets overlap except at shared endpoints;
4. every child is closed by a valid compact-BC bound or infeasibility proof;
5. no child uses diagnostic-only evidence, checkpoints, plain CPLEX benchmark bounds, archive incumbents, known UB injection, or BPC evidence.

These rules are enforced by `scripts/audit_s_bucket_coverage.py` and `scripts/audit_s_bucket_ledger_merge.py`.

## Bucket-Tight Denominator Estimator

Within a bucket, the objective lower-estimator row can use the tighter upper bound `S_U^b`:

```text
H + V * S_U^b * lambda * P <= V * S_U^b * (UB - epsilon)
```

This is valid because `S <= S_U^b` throughout the bucket. It is weaker than the nonlinear no-improver inequality but cuts no feasible improving solution under the bucket restriction.

The S*P McCormick estimator also uses bucket-local bounds. For `W_SP = S * P` with `S in [S_L^b,S_U^b]` and valid `P` bounds, the four McCormick envelope rows are valid relaxations of the bilinear product over the bucket domain. They are paper-safe only when the S and P bounds are valid model-domain bounds. Audit files `sp_mccormick_bucket_audit.csv` and `objective_estimator_cut_audit.csv` report the rows used in each tested leaf.

## Diagnostic Policies

Adaptive bucket policies are currently diagnostic unless their coverage and merge semantics are explicitly promoted and audited. They are useful to inspect where denominator weakness occurs, but they cannot close a parent interval in paper-core results.

## Current Evidence

In `results/gf_tailored_bc_s_bucket_strengthening_round`, paper-safe uniform K4 buckets pass exact coverage audits at 60s, 300s, and 1200s. They improve the merged bound on `moderate_seed3301` low_gini_1 up to `0.0487233640003`, but at least one child bucket remains open, so the parent is not certified by S-bucket merge.
