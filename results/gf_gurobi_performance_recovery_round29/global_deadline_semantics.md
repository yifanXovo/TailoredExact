# Unified process deadline semantics

Round 29 defines one monotonic absolute deadline from process entry:

`D_nominal = process_entry + process_wall_time_limit`.

A fixed five-second engineering shutdown margin defines the last instant at
which mathematical work may start or continue:

`D_work = D_nominal - 5 seconds`.

The margin is used only for interrupt propagation, native resource release,
ledger flushes, result serialization, and process exit. It never selects a
leaf, evaluates a split, changes a threshold, or supplies a bound.

Argument parsing, instance parsing, primary HGA, optional local repair,
decoding, independent verification, improving-range construction, row and
connectivity preparation, model construction, every LP, every terminal MIP,
cleanup, and JSON serialization are charged to the same process clock.
Native solvers receive the remaining duration to `D_work`; they do not receive
a newly independent experiment budget.

Every process phase is appended to a CSV ledger and flushed immediately.
Only observed events are written. A missing event after abnormal termination
is not inferred.

If `D_work` is reached before the exact tree starts:

- `exact_phase_started=false`;
- no external-tree lower bound or lifecycle claim is emitted;
- an independently verified incumbent is retained only as a valid UB;
- the only lower bound is zero, justified by the nonnegative objective
  `G + lambda P`;
- strict certification is rejected;
- a valid time-limit JSON is serialized during the shutdown margin.

If the deadline interrupts an LP or terminal MIP, the controlling leaf remains
open. Only a complete terminal LP status may contribute an LP bound, and only
a supported exact terminal-MIP status may close a leaf.
