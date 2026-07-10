# Structural Cut Activation Policy

This round evaluates activation policy for paper-safe structural rows inside a fixed Gini interval and a fully covered S bucket. Selection uses only generic model and relaxation metrics. Instance names, paths, seeds, archived outcomes, and known bounds are not inputs to the policy.

## G-S-H coupling

The product definition uses the bucket-local McCormick envelope for `W_GS = G*S`. The row `H <= V*W_GS` is valid because the compact formulation's pairwise difference variables satisfy `H <= V*G*S` for every original feasible point. It may be installed statically or separated as a global user cut when violated. The reverse row remains diagnostic because the compact relaxation does not establish exact equality for H at fractional points.

## Disaggregated S-P estimator

Each `T_SP_i` uses a bucket-local McCormick envelope for `S*e_i`. The estimator

```text
H + V*lambda*sum_i w_i*T_SP_i <= V*(UB-epsilon)*S
```

is a valid necessary condition for an improving solution. Static and callback activation use the same global row. Callback mode adds the row only when violated; product-definition rows remain in the model.

## Route rows

Support-duration covers use a conservative depot-cycle and handling lower bound. Directed route cutsets use the verified compact arc convention and are global valid inequalities. Root-limited modes choose candidates from a fractional root vector and add the selected rows to the final model. Callback-limited modes separate only violated rows. Cut count, subset size, and violation thresholds are generic resource controls.

## Auto diagnostic

`--tailored-bc-structural-profile auto-diagnostic` records a recommendation only. The round's decision table may use `gamma_U`, active S range, GS/SP relaxation gaps, route fractionality, model size, violation rate, and early bound gain. It does not alter paper-default behavior and is excluded from certificate evidence.
