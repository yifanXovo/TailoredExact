# Tailored BC Convergence and Exactness

This document states the exactness conditions for the paper-facing `paper-gf-tailored-bc` line. The algorithm is not plain CPLEX: CPLEX manages LP relaxations, the MIP tree, and callback execution for fixed-interval compact subproblems; the proposed method contributes the Gini-frontier decomposition, interval-local relaxations, valid tailored cuts, candidate validation, branching/split policy, and audited full-ledger aggregation.

## Original Problem and Fixed-Interval Coverage

Let an incumbent with value `UB` define the incumbent-improving region of the original EBRP objective. The outer Gini-frontier controller partitions or covers that region by Gini intervals `[gamma_L, gamma_U]`.

When a parent interval is split, its children must satisfy exact coverage:

```text
[gamma_L, gamma_U] = union_j [gamma_L^j, gamma_U^j]
```

with no uncovered gap. Overlap is allowed only when ledger accounting treats duplicate coverage conservatively; no parent can be declared closed merely because one overlapping child closes. A parent interval is closed only if the parent itself is fathomed, or all children that cover it are closed, empty, or fathomed by valid evidence.

The full original problem is certified only when the final active intervals exactly cover the improving Gini range and every active interval has a valid closure source.

## Valid Lower Bounds From Relaxation

For a fixed interval `I`, let `F_I` be the original feasible set restricted to `I`, and let `R_I` be a relaxation used by the frontier or compact model. The required projection relation is:

```text
F_I subset R_I
```

For minimization, the relaxation optimum is therefore a valid lower bound:

```text
min_{x in R_I} obj(x) <= min_{x in F_I} obj(x).
```

An interval can be fathomed against incumbent `UB` only when:

```text
LB_I >= UB - tolerance.
```

The tolerance must be the audited project tolerance used by the certificate audit. A relaxation timeout without a valid bound cannot close a leaf.

## Fixed-Interval Compact Model

For a fixed Gini interval, the compact MIP/BC model is certificate-capable only to the extent that it is exact for original fixed-interval feasible solutions. If the model is exact and CPLEX proves infeasibility, the interval contains no incumbent-improving original solution. If CPLEX proves optimality and the optimal objective is at least `UB - tolerance`, the interval is fathomed.

If a compact model variant is a relaxation rather than an exact model, then its optimum is a valid lower bound only under the same projection relation above. It may support bound merging, but it cannot prove fixed-interval infeasibility of the original problem unless infeasibility is proved for the original fixed-interval model or a documented equivalent model.

## Callback Tailored Branch-And-Cut Convergence

The CPLEX-managed callback branch-and-cut is theoretically convergent under sufficient time when:

- every user cut is globally valid for the fixed-interval feasible set;
- every lazy/candidate rejection adds or references only valid constraints;
- branching priorities only guide CPLEX and never delete feasible solutions;
- any custom Gini branch creates child node regions whose union equals the parent node region;
- generated rows are finite, capped, or de-duplicated, so callbacks cannot repeatedly add the same row forever;
- CPLEX is allowed to run until exact MIP closure or infeasibility.

Under these conditions, callbacks only strengthen the search or guide branching. They do not change the set of valid integer solutions, so CPLEX's exact MIP closure remains a valid fixed-interval certificate.

Time limits affect empirical convergence, not theoretical exactness. A wrapper timeout is not a certificate. A heartbeat row is not a certificate unless it exposes a valid CPLEX best bound or another valid certificate basis for the original fixed-interval model.

## Valid Best-Bound Trajectories

For a fixed-interval compact MIP, CPLEX's global MIP best bound is a valid lower bound for that fixed interval. The bound may be used for diagnostics when it is obtained either from solver-final APIs after `CPXmipopt` returns or from CPLEX-native callback info such as `CPXCALLBACKINFO_BEST_BND`.

Checkpoint bounds are weaker as evidence than solver-final closure: they show valid lower-bound progress but do not by themselves prove interval closure unless the checkpoint bound reaches the incumbent cutoff under the audited tolerance and the parent ledger accepts that scope. Wrapper-finalized rows preserving checkpoint bounds must therefore remain noncertified unless promoted by a separate audited merge rule.

## Role of Plain CPLEX

Plain CPLEX rows are benchmark and reference rows only. They may be used to compare bound quality, runtime, or to sanity-check small fixed intervals. Their bounds and objectives are never imported into the `paper-gf-tailored-bc` ledger as paper-core evidence.
