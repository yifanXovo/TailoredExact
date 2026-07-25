# Round 32 engineering-fix audit

The source audit found one general trace-only issue: a native callback leaf
bound may exceed the verified incumbent immediately before leaf closure.
`writeGlobalTrace` now includes the verified incumbent in the minimization
aggregate. The active leaf value remains visible, preserving audit evidence.

The runner is hardened separately with atomic writes and completion markers,
post-exit JSON parsing, fixed shutdown and watchdog separation, required
trace checks, checksum-validated resume, preserved invalidated/partial rows,
and explicit invalidation records. These mechanisms do not enter the solver
command's mathematical decisions.

The first pre-official Stage 0 pass exposed that the completion record did
not project `suite`, `baseline_round31_run_id`, `repetition`, and `category`
from the frozen matrix. The rows and solver outputs were valid, but the
equivalence analyzer could not map its three baselines. The general metadata
projection was repaired; the runner then preserved and invalidated all 12
old Stage 0 directories on source-identity mismatch and reran the full Stage
0 matrix uniformly. No official row had started.

The multi-M generator generalizes only its `M` and `Q` function parameters;
the legacy M3/Q30 defaults and byte output are unchanged. No C6 predicate,
row family, geometry, target, requeue, split, exact-closure, HGA, or solver
strategy setting is changed.
