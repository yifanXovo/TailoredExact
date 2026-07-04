# CPLEX Boundary for Tailored BC

`paper-gf-tailored-bc` is intended to be a CPLEX-managed tailored branch-and-cut mode with user-cut, lazy, incumbent, and branching callbacks.

Current repository state:

- The checked-in executable is built with MinGW/g++.
- `src/CplexBaseline.cpp` generates LP/script files and invokes `cplex.exe -f ...` through a command-file process boundary.
- `src/TailoredBCCplexApi.cpp` can now load `cplex2211.dll` dynamically and use the CPLEX C API without linking against MSVC import libraries.

The current callback implementation is intentionally narrow:

- read the existing fixed-interval LP model into an in-process CPLEX environment;
- register a generic callback for relaxation, candidate, branching, and global-progress contexts;
- add one redundant paper-safe user cut `G <= gamma_U` when the `G` column exists;
- retrieve relaxation points through `CPXcallbackgetrelaxationpoint`;
- separate visit-inventory linking rows, deviation-ranked singleton/pair/triple/quad Gini subset-envelope rows, the aggregate low-Gini L1 centering row, the variable-S low-Gini centering row, conservative singleton/pair/triple subset-inventory imbalance rows, basic transfer-cutset rows, and lifted pair/triple/quad support-duration cover rows from relaxation points when violated;
- inspect candidate points and reject fixed-Gini interval, visit-inventory, Gini subset-envelope, low-Gini L1, variable-S centering, and subset-inventory numerical violations through `CPXcallbackrejectcandidate` when the corresponding valid row can be re-added safely;
- apply CPLEX branch-order priorities through `CPXcopyorder`;
- wire a one-shot Gini interval split through `CPXcallbackmakebranch` for rows that explicitly request callback Gini branching;
- count callback events and solve the model through `CPXmipopt`.

Separate from the callback-owned mechanisms, `--tailored-bc-benders-inventory-cuts diagnostic` adds aggregate receiver-set inventory capacity rows during LP model generation. That family is deliberately classified as diagnostic static strengthening, not callback evidence and not paper-core certificate evidence.

The callback package includes a diagnostic branch-smoke row that uses a multidimensional binary knapsack to test branch callback reachability.  With current settings, the row applies branch priorities, receives relaxation/candidate callbacks, enters branch context, and creates two one-shot Gini branches through `CPXcallbackmakebranch`.

This proves the callback boundary is now technically open for relaxation, candidate, and diagnostic branching contexts. It does not yet implement the full requested tailored branch-and-cut policy: independent route-plan incumbent verification/rejection, consistently useful custom Gini branches on ExactEBRP hard leaves, and decisive hard-leaf callback cut separation remain incomplete.

## Hard-Leaf Finalization Status

The next-optimization round added callback heartbeat progress logging and explicit best-bound availability fields. It also tested a CPLEX callback wall-clock abort request. On the moderate low-Gini fixed-interval leaves, callback activity continued beyond the requested native time limit and no valid CPLEX best bound was exposed before wrapper termination.

Consequently, wrapper-managed final JSON remains required for hard-leaf diagnostics. A wrapper-finalized row without a valid CPLEX final best bound is noncertified and cannot contribute paper-core lower-bound evidence.

The finalization round records the native CPLEX time-limit boundary explicitly:

- `compact_bc_native_time_limit_param_id = 1039`, the C API parameter id for `CPX_PARAM_TILIM`;
- `compact_bc_native_time_limit_seconds`, the requested CPLEX native time limit;
- `compact_bc_native_time_limit_set_rc`, the return code from setting the parameter before `CPXmipopt`;
- `compact_bc_callback_abort_requests`, the number of callback-side abort requests issued after the same wall-clock deadline was reached.

The branch-callback smoke row passes and verifies that branch callback context can be reached and that custom branch objects can be created. The hard moderate low-Gini rows still show the important empirical limitation: even with `CPX_PARAM_TILIM` set and callback-side abort requests wired into long separation/candidate loops, CPLEX may not return a final best bound before the parent process boundary stops the diagnostic worker. Such rows are deliberately classified as noncertified wrapper finalizations.

## Bound-Trajectory Round Update

The bound-trajectory round adds two CPLEX-native safeguards and diagnostics:

- `CPXsetterminate` is loaded dynamically and armed with a worker-local termination flag after the requested time limit plus grace.
- Generic callback contexts sample `CPXCALLBACKINFO_BEST_BND`, `CPXCALLBACKINFO_BEST_SOL`, and `CPXCALLBACKINFO_NODECOUNT`.

The moderate low-Gini callback workers still may not return a solver-final JSON before parent termination, but the progress CSV now contains CPLEX-native global best-bound checkpoints. These checkpoint rows are valid diagnostic lower-bound trajectory points for the fixed-interval model. They remain noncertified unless a parent ledger explicitly accepts checkpoint-bound evidence under audited rules.
