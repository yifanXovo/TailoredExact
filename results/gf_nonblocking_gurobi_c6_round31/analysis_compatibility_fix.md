# Round 31 analysis compatibility audit

The 121 frozen short runs completed before analysis. The first invocation of
`scripts/analyze_round31_results.py` then stopped before classification because
the shared `round30_bound_trace.observed_step_auc` interface requires
`common_verified_upper_bound` as a keyword-only argument, while the new Round 31
caller passed that value positionally.

The repair changes only that call site from a positional argument to the
equivalent named argument. It changes no solver source, executable, instance,
matrix row, result, comparison rule, tolerance, or promotion gate.

Because the frozen source manifest includes the analyzer, the first conditional
Stage 6 launch correctly refused at its source-integrity preflight after
skipping the already materialized short rows. It started zero Stage 6 solves.
That refusal and its logs were preserved. The analyzer was returned to its
frozen byte state for the entire 27-row serial Stage 6 execution. Only after the
runner completed and exited was the one-line compatibility repair reapplied for
the final 148-row analysis.

This preflight event is not a solver retry, replacement, or excluded result.
All 148 official rows were executed once, returned process code 0, and were
analyzed from their recorded artifacts.
