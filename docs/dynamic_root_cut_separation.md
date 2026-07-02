# Dynamic Root Cut Separation

The CLI accepts `--compact-bc-root-cut-rounds`, `--compact-bc-root-cut-time-limit`, `--compact-bc-dynamic-cut-families`, and `--compact-bc-root-probe`. The current command-file CPLEX integration does not expose a callback or fractional root solution import path inside the C++ runner, so no dynamic cuts are added beyond the static valid families.

Rows with root rounds in this round are diagnostic and record the requested root-round metadata. Paper certificates do not rely on unimplemented dynamic separation. The next implementation step is either a CPLEX callback/user-cut interface or an LP-probe export/parse/add-cut loop.
