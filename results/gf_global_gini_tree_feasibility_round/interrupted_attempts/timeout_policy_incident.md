# Stage 2 timeout-policy incident

The first Stage 2 runner used an emergency subprocess timeout of solver budget
plus 120 seconds. The `moderate_seed3301` 900-second legacy-scheduler process
did not exit at its internal process-wall setting and was killed by that first
emergency timeout after 1020.0244446997531 seconds (`return_code=-98`). It
produced no admissible official result JSON.

While the next controlling-scheduler row was still early, the runner was
stopped. Its ten partial command/raw/log/trace artifacts are retained in the
neighboring `moderate_seed3301_controlling_900s_timeout_policy_fix/` directory
and are excluded from every comparison and certificate audit.

The runner policy was then changed to a declared 20-second teardown tolerance,
recorded in every new command manifest. Stage 2 resumed with existing complete
rows preserved. The legacy row was rerun and is represented in the official
matrix only by its final `runner_emergency_timeout` blocker at
920.0265278001316 seconds. No partial objective, bound, or certificate from
either attempt is imported.

The other three hard-case 900-second legacy rows that failed to return were
also retained as explicit blockers under the corrected policy. All official
global-tree rows returned normally through native CPLEX finalization.
