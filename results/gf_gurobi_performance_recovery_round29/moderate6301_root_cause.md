# Moderate6301 root cause

Round 28's three watchdog terminations were pre-exact failures, not evidence of
a C3 external-tree failure. The retained HGA trajectory proves that generation
work completed, but no external-tree event, result JSON, or external artifact
directory was emitted.

Round 29 phase instrumentation identifies the mechanism: the optional local
re-decode repair starts a second generation-stagnation HGA after the primary
HGA. Its nominal local seconds value did not terminate generation-stagnation
mode. The repair could therefore consume the remaining process window, and
the external watchdog then prevented cleanup and result serialization. The
old shared generation-log destination could also overwrite the primary
trajectory with this repair trajectory.

The unified absolute deadline now reaches both HGA invocations, and every
completed phase is append-flushed. C3 serializes a valid pre-exact result when
the repair reaches the work deadline. C4 uniformly disables the redundant
repair. In the retained 60-second development run, C3 did not enter the exact
tree, while C4 entered it and launched its first LP. The full 300-second
Stage 0 transition ledger will supply the final phase-by-phase gate.

If exact coverage does not start, the result contains only an independently
verified UB (when verification completed), explicit
`exact_phase_started=false`, conservative LB=0 from nonnegative
`G + lambda P`, and a rejected strict certificate. No interval-tree bound is
inferred or fabricated.
