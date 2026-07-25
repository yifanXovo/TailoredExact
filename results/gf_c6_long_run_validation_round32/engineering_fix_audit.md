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

The corrected Stage 0 evidence then exposed an analyzer-semantics issue on
the time-limited Moderate4301 equivalence row. Round 31 reserved five seconds
of its 120-second process cap for shutdown (115 seconds of solver work);
Round 32's frozen robust runner reserves fifteen seconds (105 seconds of
solver work). Every discrete C6 record matched exactly, as did the verified
UB and certificate state, but the deadline callback LB differed by
`1.6818345520516753e-05`. A callback frontier sampled at different
engineering horizons is not a C6 mathematical decision. The general gate
now records exact final-LB equality separately and requires both endpoint
LBs to be valid, all discrete frozen decisions to match, and the UB and
certificate outcome to be identical. It does not apply an instance-specific
exception or a result-selected performance tolerance. The analyzer change
was made before official execution; the complete clean-build and Stage 0
procedure is rerun uniformly under the resulting source identity.

That rerun also exercised a native-instrumentation edge case: the trivial
P-GRB exact row certified at zero gap in 0.022 seconds after one genuine
progress callback, instead of the two callbacks observed in earlier passes.
The row is correct, but one point cannot define observed AUC. The general
trace audit now labels any valid strictly certified single-callback row
`explicit_unavailable_single_callback_strict_certificate`, passes its
correctness/availability qualification, and keeps it explicitly
AUC-ineligible. It neither fabricates a second endpoint nor interpolates a
trace. This analyzer repair also precedes official execution and triggers
the same uniform clean-build and Stage 0 invalidation discipline.

The multi-M generator generalizes only its `M` and `Q` function parameters;
the legacy M3/Q30 defaults and byte output are unchanged. No C6 predicate,
row family, geometry, target, requeue, split, exact-closure, HGA, or solver
strategy setting is changed.
