# Round 22 Stage 1 freshness erratum

The source/protocol refreeze at commit `21087954f773a05c742dc6316e7b0c8fdbc78ff0` stopped its repeated Stage 1 on `stage1__moderate_seed3301__s0__120s__dense_on`: 8 of 11 checkpoint labels were fresh, below the original 9-label threshold.

The trace itself was dense and valid: 678 retained events, 674 documented read-only relaxation snapshots, 1,515 callback invocations, strict timestamps, no material raw monotonicity step, and exact final endpoint agreement. Its documented CPLEX callback clock covered 0.0167513 through 97.593879599999994 seconds. Checkpoints 5 and 45 seconds were stale because no callback-safe observation landed within the one-second heartbeat window. The 120-second checkpoint was stale because it lies 22.4063692 seconds after the last native observation; roughly 20 seconds of the total process budget were consumed by Tailored preprocessing before `CPXmipopt` and therefore do not exist on the native CPLEX callback clock.

The original absolute 9-of-11 rule incorrectly mixed native callback density with checkpoint labels beyond a run's native observation horizon. Before accepting any production row, Round 22 now freezes this Stage 1 gate:

- All 11 checkpoint labels through 120 seconds are still emitted, and later labels remain explicitly stale or not observed.
- A live row must have at least 20 non-final native observations and the arm-appropriate supported source.
- At least eight preregistered checkpoints must lie at or before the last native observation.
- Among those eligible checkpoints, at least `ceil(0.8 * eligible)` must be fresh.
- No observation time, freshness label, source, or final endpoint is changed or imputed.

This is a runner/protocol correction only. It does not change the executable algorithm, model, arm settings, callback capture, certificate semantics, or any comparison. The stopped attempt is retained under `attempts/pre_freshness_erratum_21087954`; Stage 0 and the complete Stage 1 are rerun under the next source/executable freeze before production restarts.
