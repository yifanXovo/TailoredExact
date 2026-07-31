# V12_M2 trace root cause

Round 31 row 409 (CSV data row 409; analyzer position 411 including its
internal endpoints) reported a terminal native callback bound
`0.745321425521423` for the sole still-active leaf while the independently
verified incumbent was `0.71850407075497091`. The next native infeasible
closure correctly set the global optimum bound to the incumbent, so the CSV
aggregate fell and the trace analyzer rejected it.

The scheduler bound was not regressing and C6 did not make a different
decision. The defect was telemetry aggregation during the narrow interval
between a callback proving that the active leaf cannot beat the incumbent
and the scheduler recording its closure. The trace used only the active and
other-open-leaf minima; it omitted the already closed branch that contains
the verified feasible incumbent. For a minimization problem that incumbent
remains a candidate global optimum, so the exported global bound cannot
exceed it.

The general repair retains the native leaf-bound event and all event order.
Only `valid_global_lower_bound` is computed as the minimum of the active/open
aggregate and the verified incumbent. No row is deleted, no timestamp is
changed, and no scheduler, target, requeue, child, split, closure, or solver
decision reads this trace value. Frozen-decision equivalence and an actual
V12_M2 rerun qualify the repair before official conclusions.
