# Dispersion-coupled child-bound proof

For station ratios `r_i`, let `e_i = |r_i-1|`,
`S = sum_i r_i`, `H = sum_{i<j}|r_i-r_j|`, and `G=H/(V S)`.

For each pair, the triangle inequality gives
`|r_i-r_j| <= |r_i-1| + |r_j-1| = e_i+e_j`. Summing over all pairs counts each
`e_i` exactly `V-1` times, hence `H <= (V-1) sum_i e_i`.

In child interval I, `G >= L_I` and the factory has a valid ratio-sum lower
bound `S >= S_lower_I`. For `V>1`,

`(V-1) sum_i e_i >= H = V S G >= V S_lower_I L_I`,

so `sum_i e_i >= D_I = V L_I S_lower_I/(V-1)`.

The factory ratio interval gives valid deviation bounds
`e_i^- <= e_i <= e_i^+`. Therefore every feasible child's true e-vector is
feasible for the continuous knapsack minimizing `sum_i w_i z_i` subject to
those bounds and `sum_i z_i >= D_I`. With nonnegative weights, initializing
at lower bounds and allocating remaining deviation by nondecreasing weight
(station index breaks ties) is optimal by the standard exchange argument.
Thus `phi(I) <= sum_i w_i e_i = P`.

Since `G >= L_I` and lambda is nonnegative,
`L_I + lambda phi(I) <= G + lambda P`, so it is a lower bound on every child
solution. The parent relaxation is also a lower bound on every child subset;
the maximum of the two lower bounds remains valid. Passing that value as the
CPLEX child estimate changes search ordering only and cannot delete a feasible
solution or justify pruning by itself.

## Edge and numerical cases

- `V<=1` retains the parent estimate.
- `L_I=0`, `S_lower_I=0`, or `lambda=0` follows the same formula.
- Zero weights are filled first; tied weights use station index.
- Negative/nonfinite lambda, weights, interval endpoints, or inconsistent
  deviation domains fail closed before `makeBranch`.
- If `D_I` is below the lower-deviation sum, the lower vector is optimal; if it
  is inside the domain, deterministic fractional fill is used.
- If `D_I` exceeds the upper-deviation sum, the contradiction is instrumented
  but Round 23 retains the parent estimate and performs no candidate pruning.
- Arithmetic uses `long double`; D and every exported penalty/objective lower
  bound are rounded toward negative infinity. No benchmark-derived epsilon is
  used.

Exhaustive enumeration over small integer inventory domains verifies the
exported estimate never exceeds the exact feasible child optimum. The same
function is called for F0 and F3 because it depends only on the common factory
domain, weights, lambda, interval lower endpoint, and parent relaxation.
