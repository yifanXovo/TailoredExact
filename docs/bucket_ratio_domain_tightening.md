# Bucket Ratio-Domain Tightening

This note documents the paper-safe bucket-local ratio/domain cuts used by
`paper-gf-tailored-bc`.

For a fixed Gini interval with upper endpoint `gamma_U` and an enforced
S-bucket

```text
S_L <= S = sum_i r_i <= S_U,
```

the compact model has

```text
H = sum_{i<j} |r_i-r_j|,        G = H / (V S),
G <= gamma_U.
```

For any station `i`,

```text
|r_i - S/V| <= (1/V) sum_j |r_i-r_j| <= H/V <= gamma_U S.
```

Therefore every feasible point in the bucket satisfies

```text
r_i <= (1/V + gamma_U) S <= (1/V + gamma_U) S_U,
r_i >= (1/V - gamma_U) S >= (1/V - gamma_U) S_L
```

when `(1/V - gamma_U) > 0`; otherwise the lower row is omitted. The same
ratio bounds may tighten integer final inventory domains through
`Y_i = target_i r_i` using conservative `ceil`/`floor` rounding.

For a subset `A` with `a=|A|` and `R_A=sum_{i in A} r_i`,

```text
|V R_A - a S| <= H <= V gamma_U S.
```

Thus, inside an enforced S-bucket,

```text
R_A <= (a/V + gamma_U) S_U,
R_A >= (a/V - gamma_U) S_L       if a/V - gamma_U > 0.
```

These subset cuts are valid for subsets generated generically by size and are
paper-safe only when the child model enforces the bucket rows. Parent closure
still requires the S-bucket ledger audits to prove exact coverage and valid
closure of every child.

The implementation is gated by:

```text
--tailored-bc-bucket-ratio-domain-tightening true
--tailored-bc-bucket-subset-ratio-domain true
--tailored-bc-bucket-subset-ratio-max-size <1..4>
```

and audited by `scripts/audit_bucket_ratio_domain_tightening.py`.
