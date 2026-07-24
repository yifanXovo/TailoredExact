# C6 split strategy

Let `b` be the current parent bound after every previously merged native
bound. Let `B_child` be the minimum finite bound of two terminal-valid
complete child LPs, treating an infeasible child as exact empty coverage.

- If either child is infeasible, replace the parent atomically and immediately
  close the infeasible child.
- Otherwise compute
  `gain = B_child - b` and
  `normalized_gain = gain / max(verified_UB - b, tol)`.
- If `normalized_gain >= rho`, atomically split.
- If `0 < gain <=` the rho threshold, run one parent native target to
  `B_child`.
- If `gain <= tol`, retain the parent geometry and launch exact closure.

After a child target is reached, recompute the predicate against the
strengthened parent using the already complete child LP results. There is no
pending or mandatory split flag. The sole policy threshold is the unchanged
`rho=0.01`.
