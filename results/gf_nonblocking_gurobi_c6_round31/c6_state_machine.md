# C6 state machine

| State | Complete evidence | Allowed transition |
|---|---|---|
| `OPEN_UNPROCESSED` | Exact interval and inherited bound | Complete parent LP |
| `OPEN_LP_BOUNDED` | Terminal-valid optimal parent LP | Requeue if another leaf is lower; otherwise one next-strict-frontier target, or lazy child lookahead if none exists |
| `OPEN_NATIVE_BOUNDED` | Valid native MIP bound from the launch-frozen target phase | Requeue open; on later control, lazy child lookahead |
| `CHILD_LOOKAHEAD` | Two terminal-valid complete child LPs | Atomic split, one child-bound target, or exact closure |
| `OPEN_NATIVE_BOUNDED_CHILDREN_CACHED` | Valid child target attained and complete cached child LPs | Requeue; re-evaluate current gain without recomputation |
| `ATOMIC_SPLIT` | Exact binary child coverage and current split predicate | Parent replaced, children become relevant atomically |
| `EXACT_CLOSURE` | Complete native MIP | Close only on optimality/infeasibility or verified cutoff |
| `OPEN_INTERRUPTED` | Last valid bound and intact interval | Deadline finalization; never closure |

The one frontier milestone is a state transition, not an attempt counter. It
cannot repeat on the same leaf. A child target is also a one-way transition:
after attainment its cached child pair is re-evaluated and cannot mandate a
split.
