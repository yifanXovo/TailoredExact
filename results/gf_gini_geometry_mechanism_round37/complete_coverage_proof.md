# Exact complete-coverage argument for G1

G1 changes only the order and geometry of one exploratory C6 event; it does not
change the problem, proof cutoff, relaxation rows, certificate rule, or final
verifier.

1. The frozen C6 root range is partitioned into four contiguous active
   intervals. `exactIntervalCoverage` verifies the first lower endpoint, last
   upper endpoint, and every shared boundary before any leaf enters the exact
   scheduler.
2. G1 completes the LP relaxation for every initial cell that fits before the
   global deadline. It selects only an open cell with a complete optimal bound
   strictly below the verified cutoff. Incomplete, infeasible, invalid, closed,
   and cutoff cells cannot be selected.
3. The selected parent `[a,b]` is replaced by `[a,(a+b)/2]` and
   `[(a+b)/2,b]`. The generic exact-coverage checker must accept the child pair
   before either child is used.
4. Both child LPs complete before replacement. Each valid child bound is the
   maximum of its complete LP bound and inherited valid parent bound. An
   infeasible child is closed only after its complete LP proves infeasibility.
5. `splitLeafAtomically` inserts both children and marks the parent replaced in
   one scheduler operation. A failed insertion leaves no partial cover and
   fails the run closed.
6. After that one replacement, the unchanged C6 strict-frontier target,
   requeue, current-rho split, and exact-closure logic resumes. Verified
   incumbent tightening and the final independent solution verifier are
   unchanged.
7. A strict certificate is accepted only if root coverage, all recorded
   parent-child coverage, all relevant leaf closures, valid monotone bounds,
   verified UB, lifecycle balance, and the feasibility consistency gate all
   pass and the final lower bound reaches the verified upper bound.

The empirical audit covers all 22 official Round 37 runs. Root coverage and
parent-child coverage pass 22/22; all leaf and global bounds are monotone;
environment/model and optimize counters balance; all manifests validate; 6
runs are strict certificates and 16 are valid non-certificates. There are zero
false certificates.
