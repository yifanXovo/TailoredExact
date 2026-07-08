# Bucket Integer Inventory Domain Tightening

This note documents the paper-safe bucket-local final-inventory tightening used
by `paper-gf-tailored-bc`.

Inside a fixed Gini interval and an enforced S bucket,

```text
gamma_U fixed
S_L <= S = sum_i r_i <= S_U
```

the fixed-interval Gini cap implies, for every station `i`,

```text
|r_i - S/V| <= gamma_U S.
```

Therefore every feasible original solution in the bucket satisfies

```text
r_i <= (1/V + gamma_U) S_U
r_i >= (1/V - gamma_U) S_L, when 1/V - gamma_U > 0.
```

The model convention uses integer final inventory `Y_i` and
`r_i = Y_i / target_i` with `target_i > 0`, so the ratio bounds imply the
conservative integer bounds

```text
Y_i <= floor(target_i * r_i^U)
Y_i >= ceil(target_i * r_i^L).
```

These bounds are intersected with capacity and any already-valid inventory
domains.  They are active for paper evidence only when the S-bucket rows are
actually enforced and the bucket scope is labelled `paper-safe`.

The implementation reports:

```text
bucket_integer_inventory_bounds_tightened
bucket_integer_inventory_rows_added
bucket_integer_inventory_lower_bounds_tightened
bucket_integer_inventory_upper_bounds_tightened
bucket_integer_inventory_domain_proof_status
```

and is audited by `scripts/audit_bucket_integer_inventory_domain.py`.
