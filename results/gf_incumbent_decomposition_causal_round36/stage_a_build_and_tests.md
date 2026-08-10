# Round 36 Stage A build and tests

Gate passed: **True**.

- Clean Release Gurobi build: True
- C++ tests: 15/15 passed
- Python protocol/regression scripts: 21/21 passed
- Frozen-C6/default-off/HH decision-hash comparisons: 14, all passed: True
- Executable SHA-256: `52b85f0e9f1f89fc09e08866c1901a787abd0e7d24c2f02e4e5f8337f48ddbe8`

The baseline audit covers initial intervals, complete LP bounds, controlling
leaves, native targets, split decisions, closure order, and the final
objective/certificate. A failed item blocks Stage B.
