# Round 52 tailored-cut architecture

The implementation is split into three layers. `CutCandidate`, `CutSeparator`, and `CutManager` are solver-independent C++ code. `Round52GurobiCutAdapter` is the only layer that maps canonical variable names to Gurobi column indices and calls an injected `GRBcbcut` submitter. The canonical base model keeps every feasibility constraint; no user cut is treated as a lazy constraint.

## Candidate contract

A candidate records its family, global/local validity, sparse row, sense, right-hand side, raw and scaled violation, scale, canonical row and LHS signatures, interval and node context, support, vehicle block, and derivation metadata. Normalization combines equal variables, drops exact zero coefficients, sorts by canonical variable name, converts `>=` to `<=`, and uses exact hexadecimal floating-point representations after max-coefficient normalization.

## Separator contract

The separator receives the instance, current LP values, effective lower and upper bounds, the model-variable mapping, interval identity, node context, support-rank limit, and certificate tolerance. It enumerates every support of ranks two through the frozen maximum, computes an exact depot-to-depot permutation lower bound, validates every required value and bound, and returns candidates without using a solver API.

## Manager contract

The manager applies the strict certificate test `raw_violation > epsilon_cert * scale`, rejects invalid rows, exact duplicates and only provable same-normalized-LHS dominance, then deterministically ranks by vehicle, decreasing scaled violation, and canonical signature. `VehicleBlockMaximum` submits at most one row per vehicle in a callback. Successfully submitted global rows enter a per-model canonical pool. Beginning a different model clears both pool and telemetry, preventing cross-model leakage. Telemetry accounts for generated, violated, selected, submitted, added, rejected, callback, family, vehicle, and pool outcomes.

## Gurobi lifecycle

The named F3/F4 policies alone activate the callback. The backend dynamically loads and verifies `GRBcbcut` and also audits `GRBcblazy`, sets and reads back `PreCrush=1`, registers the common progress/user-cut callback, and separates only when `where == GRB_CB_MIPNODE` and `MIPNODE_STATUS == GRB_OPTIMAL`. F3 accepts root callbacks only; F4 is the separately named tree-scope experimental policy. The adapter refuses local and equality rows, rejects missing mappings, and records each native return code. Callback exceptions are caught, counted, disable further tailored separation for that solve, and never escape through the C callback boundary. Such a solve fails the engineering gate while retaining the native solver evidence.

Historical policy names remain callback-off. F0 removes the target static family, F1 emits rank-two/rank-three rows with the historical loose coefficient, F2 emits the same supports with the tight route lower bound, and F3 uses no static target rows and adds them dynamically through `GRBcbcut`.
