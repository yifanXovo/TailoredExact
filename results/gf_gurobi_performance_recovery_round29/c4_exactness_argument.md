# C4 exactness argument

1. The initial intervals exactly cover the full improving Gini range.
2. Every accepted split is an exact two-child cover and replaces its parent
   atomically.
3. A complete parent LP bound is valid for the parent and may be inherited by
   its children.
4. Child bounds enter a split decision only after complete supported LP
   terminal statuses.
5. An infeasible complete child LP proves the child MIP empty.
6. LP cutoff fathoming uses only a complete valid lower bound and an
   independently verified incumbent.
7. Declining a split retains the entire parent interval and solves its MIP;
   it cannot discard a feasible point.
8. Terminal MIPs use zero relative and absolute gap and close a leaf only on
   supported exact optimal or infeasible statuses.
9. Interrupted LPs and MIPs leave their controlling coverage open.
10. The global lower bound is the minimum valid bound over complete,
    non-replaced coverage.
11. Strict certification additionally requires complete coverage, all
    relevant leaves closed, monotone valid bounds, lifecycle/resource
    symmetry, and an independently verified global incumbent.
12. In-memory model retention changes execution only. The original integer
    domain must be restored before a terminal MIP; failure invalidates the
    event and rejects certification.
