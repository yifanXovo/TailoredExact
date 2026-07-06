# S-Range Denominator Refinement

This note documents the S-domain refinement added for the `paper-gf-tailored-bc` low-Gini strengthening line. Here `S = sum_i r_i` is the denominator in the fixed-interval Gini expression.

## Modes

The command line exposes:

- `--tailored-bc-s-bucket-ledger off|diagnostic|paper-safe`
- `--tailored-bc-s-bucket-count <K>`
- `--tailored-bc-s-bucket-policy uniform|adaptive-open|adaptive-snapshot|adaptive-cutoff|adaptive-hybrid`
- `--tailored-bc-s-bucket-time-budget <seconds>`
- `--tailored-bc-s-bucket-merge-audit true|false`
- `--tailored-bc-s-bucket-max-depth <D>`
- `--tailored-bc-s-bucket-min-width <eps>`
- `--tailored-bc-s-bucket-refine-top-k <K>`
- `--tailored-bc-s-bucket-refine-rule widest|worst-gap|plateau-s|hybrid`

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

## Adaptive-Open Policy

The `adaptive-open` policy starts from a uniform K4 child ledger, solves each child, and recursively splits only unresolved child buckets. The implemented runner selects open buckets by `widest`, `worst-gap`, `plateau-s`, or `hybrid` scoring. The final adaptive frontier is audited as one child cover of the original parent S-domain, not as separate local split groups. Parent closure remains invalid unless the final frontier exactly covers the parent domain and every final child closes by paper-safe evidence.

In `results/gf_tailored_bc_adaptive_s_refinement_round`, adaptive-open narrows the hard low-Gini region from the K4 child `[16.59546103547, 23.272821182835]` to the unresolved child `[18.26480107231125, 19.9341411091525]` at 300s. This is a valid diagnostic/ledger refinement, but it does not yet certify the parent because the narrowed child remains open.

## Bucket-Tight Denominator Estimator

Within a bucket, the objective lower-estimator row can use the tighter upper bound `S_U^b`:

```text
H + V * S_U^b * lambda * P <= V * S_U^b * (UB - epsilon)
```

This is valid because `S <= S_U^b` throughout the bucket. It is weaker than the nonlinear no-improver inequality but cuts no feasible improving solution under the bucket restriction.

The S*P McCormick estimator also uses bucket-local bounds. For `W_SP = S * P` with `S in [S_L^b,S_U^b]` and valid `P` bounds, the four McCormick envelope rows are valid relaxations of the bilinear product over the bucket domain. They are paper-safe only when the S and P bounds are valid model-domain bounds. Audit files `sp_mccormick_bucket_audit.csv` and `objective_estimator_cut_audit.csv` report the rows used in each tested leaf.

## Coupled Estimator Status

The lower-S guarded row is rejected for paper evidence because substituting `S_L^b` into the positive penalty term can overstate the necessary no-improver condition. The H upper cap is valid when combined with the fixed Gini upper bound but is largely dominated by the direct Gini cap and bucket S rows. H lower-bound rows remain diagnostic until the model path proves exact H semantics rather than upper-envelope slack.

## Current Evidence

In `results/gf_tailored_bc_s_bucket_strengthening_round`, paper-safe uniform K4 buckets pass exact coverage audits at 60s, 300s, and 1200s. They improve the merged bound on `moderate_seed3301` low_gini_1 up to `0.0487233640003`, but at least one child bucket remains open, so the parent is not certified by S-bucket merge.

In `results/gf_tailored_bc_adaptive_s_refinement_round`, the 3600s paper-safe K4 bucket ledger improves the best valid LB to `0.0487820084447`, leaving a gap-to-cutoff of `0.0003705442199999978`. This is progress, not certification.
