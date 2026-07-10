# G-S-H Product Coupling

The upper row may be installed statically or separated by the CPLEX relaxation callback. Callback mode still installs the bucket-local product variable and its four McCormick definition rows; only the `H <= V*W_GS` activation is deferred until violation. The lower/equality side remains diagnostic.

This cut family is for fixed-Gini, fixed-S-bucket Tailored-BC subproblems.

For a fixed interval `gamma_L <= G <= gamma_U` and enforced S bucket
`S_L <= S <= S_U`, introduce `W_GS = G*S` and the bucket-local McCormick
envelope over `[gamma_L,gamma_U] x [S_L,S_U]`.

For every original feasible solution under the current Gini convention,

```text
G = H / (V*S)
```

with `S > 0`, so `H = V*G*S`.  The paper-safe strengthening used by default is:

```text
H <= V*W_GS
```

The lower/equality side is implemented only behind
`--tailored-bc-gs-product-lower-row`. It is off by default. Rows labelled
`diagnostic` must not be used for paper-core certificates. A `paper-safe` lower
row requires an explicit audit of exact H semantics for the active model path.

Implemented fields:

```text
gs_product_variable_added
gs_mccormick_rows_added
gs_h_upper_rows_added
gs_h_lower_rows_added
gs_product_coupling_proof_status
```

Paper-safe scope:

- fixed Gini interval is enforced;
- S bucket is enforced and logged;
- McCormick bounds are bucket-local;
- `H <= V*W_GS` is active only when `W_GS` exists.
