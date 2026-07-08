# S-P-H Coupled Estimator

For a fixed interval and cutoff value `U = UB - epsilon`, every improving
original solution satisfies

```text
H/(V S) + lambda P <= U.
```

Because `S > 0`, this is equivalent to

```text
H + V lambda S P <= V U S.
```

The model introduces `W_SP` and constrains it by the McCormick envelope over
bucket-local bounds

```text
S in [S_L, S_U]
P in [P_L, P_U].
```

The paper-safe estimator row is

```text
H + V lambda W_SP <= V U S.
```

For original feasible solutions, `W_SP = S P`; for the relaxation, the
McCormick envelope is a valid relaxation of that product.  The row therefore
does not remove any original feasible no-improver solution and can only
strengthen the lower-bound proof model.

Rows that require exact `H = sum h_ij` lower semantics beyond the envelope are
kept diagnostic unless the exact-H audit proves they are safe in the active
model path.
