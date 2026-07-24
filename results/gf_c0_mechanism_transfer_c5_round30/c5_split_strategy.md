# C5 split strategy

Let parent bound be \(b\), verified upper bound \(U\), complete child LP
bounds \(b_L,b_R\), certificate tolerance \(\tau=10^{-7}\), and
\(\rho=0.01\). Infeasible children are represented separately, not by a
finite sentinel.

1. If either complete child LP is infeasible, split atomically.
2. Otherwise set \(b_C=\min(b_L,b_R)\).
3. If \(b_C-b\le\tau\), decline the split and solve the exact parent MIP.
4. Let \(r=(b_C-b)/\max(U-b,\tau)\).
5. If \(r\ge\rho\), split atomically.
6. If \(0<r<\rho\), run the parent MIP to the valid dual-bound target \(b_C\).
   Exact closure closes the parent. Target attainment requeues the open
   parent; its next best-bound selection performs the delayed atomic split.

The rule is uniform and contains no family, size, seed, path, time, Work,
node, solution, retry, or attempt dispatch. The single rho was chosen before
the development matrix from the C0 split-value audit; no candidate sweep or
official-result tuning occurred.
