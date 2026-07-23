# Moderate6301 root cause

Round 28's three watchdog terminations were pre-exact failures, not external
C3 tree failures.  The old retained trajectory proves that the primary HGA
generation loop completed, but the old process emitted no external-tree event
or result.

Round 29 phase instrumentation identifies the mechanism precisely.  The
`paper-gf-tailored-bc` preset enabled an optional local re-decode repair after
the primary HGA.  That repair launched a second HGA in generation-stagnation
mode.  The local `primal_heuristic_seconds` value did not stop this mode, so
the second HGA could consume the remaining process window.  Round 28 then
reached an external watchdog before result serialization.  Its shared
generation-log path also allowed the repair trajectory to obscure the primary
trajectory.

The repair now observes the same absolute process-entry work deadline, all
phase events are append-flushed, and C3 reports
`paper_hga_global_deadline` with return code 0 and watchdog flag
`False`.  Its last completed phase is
`process_exit`.  C4 uniformly disables the optional repair;
it reports `round29_c4_external_gini_tree_time_limit`, exact-phase-started
`True`, first-external-event
`True`, return code
0, and watchdog flag `False`.

Both paths serialize only proven information.  If exact coverage has not
started, LB=0 is the explicit conservative bound from nonnegative
`G + lambda P`; no interval-tree bound or strict certificate is fabricated.
