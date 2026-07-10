# Disaggregated S-e_i Product Estimator

This family strengthens the no-improver cutoff estimator inside an enforced
S bucket.

Let:

```text
P = sum_i w_i e_i
S in [S_L,S_U]
```

For each station, introduce `T_SP_i = S*e_i` and add McCormick rows over
`S in [S_L,S_U]` and the current valid bound interval for `e_i`.

The paper-safe estimator is:

```text
H + V*lambda*sum_i w_i*T_SP_i <= V*(UB-epsilon)*S
```

For original feasible solutions, `T_SP_i = S*e_i`, so the row is the fixed
interval objective cutoff written with a disaggregated product representation.
The LP relaxation remains conservative because each `T_SP_i` is constrained by
valid McCormick envelopes over valid domains.

The option `--tailored-bc-disaggregated-sp-replace-aggregate true` suppresses
the aggregate `W_SP` estimator when the disaggregated estimator is active. This
avoids double-counting the old aggregate product formulation in ablations.

Required assumptions:

- all penalty weights `w_i` are nonnegative;
- the S bucket is enforced and logged;
- `e_i` bounds come from model-valid domains;
- diagnostic rows do not enter paper-core certificates.
