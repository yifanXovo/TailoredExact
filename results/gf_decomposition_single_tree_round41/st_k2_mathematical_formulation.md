# Static K2 mathematical formulation

## Geometry and base model

Let the complete strict-improver range be `[gamma_L,gamma_U]` and let `tau=(gamma_L+gamma_U)/2`. Define `I_1=[gamma_L,tau]` and `I_2=[tau,gamma_U]`. Their union is the root range and their intersection is only `tau` (or the same zero-width interval in the degenerate case).

The base is the complete compact original MILP with the verified incumbent cutoff and all strengthening valid over the root range. Let `R_k` be the complete existing interval-row-factory pack for `I_k`. Infeasible factory domains fix their selector to zero.

## ST-K2-I

Introduce `z_k in {0,1}` and impose

```text
z_1 + z_2 = 1,
G >= sum_k l_k z_k,
G <= sum_k u_k z_k,
Y_i >= sum_k Y_iL_k z_k,
Y_i <= sum_k Y_iU_k z_k,
S >= sum_k S_Lk z_k,
S <= sum_k S_Uk z_k,
P >= sum_k P_Lk z_k,
P <= sum_k P_Uk z_k.
```

Every remaining row `a^T x sense r` in `R_k` is imposed by the static indicator `z_k=1 -> a^T x sense r`. There are no arbitrary activation constants.

## ST-K2-P-Core

In addition to the exact selector aggregation, introduce `G_k`, and for every inventory expansion bit `b_j` and its original product `q_j=G b_j`, introduce continuous `w_jk,q_jk`:

```text
sum_k G_k = G
l_k z_k <= G_k <= u_k z_k

0 <= w_jk <= z_k
w_jk <= b_j
w_jk >= z_k + b_j - 1
sum_k w_jk = b_j

l_k w_jk <= q_jk <= u_k w_jk
q_jk >= G_k - u_k (z_k-w_jk)
q_jk <= G_k - l_k (z_k-w_jk)
sum_k q_jk = q_j.
```

The original interval-tight McCormick rows are removed from `R_k`; every other interval-local family remains indicator activated.

### Product exactness proposition

At an integer selector, exclusivity gives one active segment `h`. For `k != h`, the bounds force `G_k=w_jk=q_jk=0`. For `h`, `G_h=G`, the four binary-product inequalities force `w_jh=b_j`, and the four perspective inequalities force `q_jh=G_h b_j` for either binary value of `b_j`. Aggregation therefore gives `q_j=G b_j`. This proves integer product equivalence; it does not prove equality of continuous relaxations.

## ST-K2-P-Extended

Extended adds selected copies `S_k=z_k S`, `P_k=z_k P`, and `H_k=z_k H`, using their global safe bounds and segment-specific valid bounds. For a generic original `x in [L,U]` and selected-domain `[L_k,U_k]`, `x_k` satisfies

```text
L_k z_k <= x_k <= U_k z_k
x - U(1-z_k) <= x_k <= x - L(1-z_k)
sum_k x_k = x.
```

It then imposes the segment direct-Gini rows

```text
H_k <= V u_k S_k,
H_k >= V l_k S_k,
```

the selected objective estimator and penalty lower bound, and one `WSP_k` McCormick envelope over the segment bounds on `(S_k,P_k)` followed by the selected SP estimator. The same fixed pack is used on every instance. Routing and stationwise decision variables remain shared.

## Size formulas

Let `B` be the total number of original inventory bits, `K=2`, and `F_k` the number of interval-local factory rows for segment `k`.

- I adds `K` binaries, selector/G/Y aggregation rows, and `sum_k F_k` indicators.
- Core adds `K(1+2B)` continuous variables, `G` aggregation/bounds, `7KB` perspective inequalities, and `2B` aggregation equalities; it removes the corresponding tight-product indicators.
- Extended adds `4K` continuous variables, four-envelope rows for each of `S_k,P_k,H_k`, the direct/estimator/penalty/SP pack, and three copy-sum equalities; it removes the replaced indicators.

Empirical original and presolved counts are reported separately because Gurobi may reformulate indicators during presolve.

## Uniform relaxation diagnostics

For every original bit relation, the reported ambiguity is the requested root-domain McCormick width

```text
max(0, min(u b, G-l(1-b)) - max(l b, G-u(1-b))).
```

For every segment perspective relation it analogously reports

```text
L_jk = max(l_k w_jk, G_k-u_k(z_k-w_jk))
U_jk = min(u_k w_jk, G_k-l_k(z_k-w_jk))
A_seg = sum_jk max(0,U_jk-L_jk).
```

This is an envelope-width diagnostic, not the residual of the chosen `q_jk`. Group fractionality is `sum 4x(1-x)` after clipping each relaxed binary-domain value to `[0,1]`.

## Certificate proposition

For any original feasible strict improver, choose a segment containing its `G`; at the shared midpoint either selector is valid. Set the selected auxiliaries to the corresponding products/copies. All rows are valid, so the static formulation contains the solution. Conversely, any integer static solution has exactly one active segment, satisfies its complete row-factory pack and the unchanged original compact MILP, and projects to an original feasible solution. Thus the integer optimum equals the original optimum under the verified cutoff. Certification still requires native zero-gap optimality and independent original-problem verification.
