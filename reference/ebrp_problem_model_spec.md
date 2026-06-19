# Equity-aware Bike Repositioning Problem: Problem and Exact-Method Specification

## 1. Problem data

Stations are indexed by `i=1,...,V`; depot is index `0`. For each station:

- Capacity: `C_i`.
- Initial inventory: `Y_i^0`.
- Target inventory: `Y_i^T > 0`.
- Satisfaction weight: `w_i >= 0`.

There are `M` vehicles. Vehicle `k` has bike capacity `Q_k`. All vehicles start empty at the depot and must return to the depot. Each station can be visited by at most one vehicle. At a visited station, the vehicle may either pick up or drop off an integer number of bikes. Vehicle load must remain between `0` and `Q_k`; station inventory must remain between `0` and `C_i`. If a vehicle returns to the depot with bikes, it unloads them at the depot. The depot has infinite capacity. Each vehicle duration must be at most `T`.

Travel times/distances are `d_ij` for `i,j=0,...,V`. Pickup and drop operation times per bike are `tau_p` and `tau_d`.

## 2. Final inventory, service ratios, objective

Let `Y_i` be final inventory. Define

```math
r_i = \frac{Y_i}{Y_i^T}.
```

The Gini term is

```math
G(r)=\frac{\sum_{i=1}^V\sum_{j=1}^V |r_i-r_j|}{2V\sum_{i=1}^V r_i}
=\frac{H(r)}{V S(r)},
```

where

```math
H(r)=\sum_{1\le i<j\le V}|r_i-r_j|,\qquad S(r)=\sum_{i=1}^V r_i.
```

The satisfaction penalty is

```math
P(r)=\sum_{i=1}^V w_i |r_i-1|.
```

The original objective is

```math
\min\; G(r)+\lambda P(r).
```

## 3. Key exact reformulation ideas

### 3.1 Operation-time conservation

For vehicle `k`, let total pickup be `P_k` and station drop-off be `D_k`. Since the vehicle starts empty, the number of bikes unloaded at depot is `P_k-D_k`. Therefore total operation time is

```math
\tau_p P_k + \tau_d D_k + \tau_d(P_k-D_k)
= (\tau_p+\tau_d)P_k.
```

For `tau_p=tau_d=60`, operation time is `120 P_k`. Thus route duration can be written as

```math
\text{travel}_k + (\tau_p+\tau_d)P_k \le T.
```

This is exact, not a relaxation.

### 3.2 Fixed Gini-cap linearization

For a fixed cap `gamma`,

```math
G(r)\le \gamma
\quad\Longleftrightarrow\quad
H(r)\le V\gamma S(r).
```

Because `gamma` is constant and `H,S` are linear/piecewise-linear in final inventories, this removes the fractional Gini term from the fixed-cap subproblem.

### 3.3 Route-load columns

A route-load column `c` is a complete feasible vehicle plan:

```math
c=(A_c,R_c,q_c,\Delta_c,t_c),
```

where `A_c` is the visited station set, `R_c` is the visiting order, `q_ic` is signed operation quantity (`q_ic>0` pickup, `q_ic<0` drop-off), `Delta_ic=-q_ic` is the final-inventory change at station `i`, and `t_c<=T` is the verified route duration.

The master selects columns using binary variables `z_c`:

```math
\sum_c z_c \le M,
```

```math
\sum_{c:i\in A_c} z_c \le 1,\quad \forall i,
```

```math
Y_i = Y_i^0 + \sum_c \Delta_{ic} z_c,\quad \forall i.
```

If all feasible route-load columns are available, this master is equivalent to the original route-load feasible region.

### 3.4 Pricing certificate

For a restricted master with dual variables, the pricing problem searches for a feasible route-load column with negative reduced cost. If exact pricing proves that the minimum reduced cost is nonnegative at a branch node, the restricted master LP is equal to the full master LP at that node.

## 4. Valid cuts and branching

### 4.1 3-subset-row cut

For any station triple `S`,

```math
\sum_c \left\lfloor \frac{|A_c\cap S|}{2}\right\rfloor z_c \le 1.
```

Validity: in an integer solution, stations are disjoint across selected columns. If two selected columns each cover at least two stations in a triple, total station coverage inside the triple would be at least four, impossible with only three stations each served at most once.

### 4.2 Co-route pair branching

For pair `(i,j)`, define

```math
b_{ij}=\sum_{c:\{i,j\}\subseteq A_c}z_c.
```

In integer solutions, `b_ij in {0,1}`. Branch on

```math
b_{ij}=0 \quad\text{or}\quad b_{ij}=1.
```

This is Ryan-Foster-style branching adapted to station-disjoint route columns.

### 4.3 Lorenz/Gini cuts

If `r_(1)<=...<=r_(V)` are sorted service ratios, then

```math
H(r)=\sum_{\ell=1}^V (2\ell-V-1) r_{(\ell)}.
```

This can be used for dynamic separation of Gini numerator cuts, avoiding all pairwise absolute-difference variables for larger `V`.

## 5. Exactness requirements

An algorithm may report `certified optimal` only if:

1. The selected route operations pass independent feasibility verification.
2. The objective is independently recomputed from final inventories.
3. A global lower bound equals the incumbent within tolerance, either by a closed compact MIP, a closed branch-price tree with exact pricing at every node, or exhaustive feasible-column enumeration plus exact master MIP.

Root LP column-generation certificates alone are not enough to claim integer/global optimality.
