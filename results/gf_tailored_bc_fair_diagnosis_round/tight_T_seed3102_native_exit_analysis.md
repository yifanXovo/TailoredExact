# tight_T_seed3102 Native Exit Analysis

Classification: `engineering_finalization_failure;callback_overhead;plain_solver_stronger_root_bound;root_bound_weakness;frontier_scheduling_problem`.

The tight-T 300/900 s post-fix engineering reproductions all finalized normally; the historical tight-T native-exit symptom did not reproduce. A separate first V12 M2 cheap-profile run raised Windows access violation `0xC0000005`. Debug symbols identified invalidation of an adaptive-frontier parent reference during child insertion. The implementation now copies the parent bound source before insertion, and the identical post-fix row certified. The original incident remains diagnostic-only.

See `native_exit_repro_summary.csv`, `native_exit_debug_log.md`, and the package-local stdout/solver logs for exact return codes and finalization evidence.
