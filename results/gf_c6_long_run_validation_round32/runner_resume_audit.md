# Round 32 runner resume audit

The Round 32 runner uses one serial global lock and one independent directory
per frozen matrix row. A completion marker is written atomically only after
the solver process exits, the result JSON parses successfully, required
traces and lifecycle files exist, console streams are flushed, and a
checksum inventory is written.

On resume, the runner recomputes the completion-marker identity and every
recorded artifact hash. A valid row is skipped. A missing, corrupt, stale, or
identity-mismatched marker causes the entire prior row directory to be moved
under `invalidated_rows/` with an explicit immutable reason before a fresh
row is launched. Incomplete watchdog evidence is retained and is never
silently overwritten.

`tests/round32_runner_trace_tests.py` exercises atomic writes, valid-row
skip qualification, checksum tamper detection, preserved invalidation,
invalidation logging, fixed shutdown/watchdog separation, and the absence of
license-location serialization. This is row-level experiment resume only.
Round 32 neither implements nor claims preservation of native Gurobi tree
state.
