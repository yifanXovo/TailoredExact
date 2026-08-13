# Round 38 exactness audit

Pre-mechanism C6 equivalence: **18/18**; post-implementation explicit-off equivalence: **18/18**.

Across **42** official runs (**21** pairs), all run gates passed, with **0** false certificates and **0** certificate regressions.

| Stage | Runs | Pairs | Strict certs | False certs | Cert regressions | Child evals | Completions | Accepted splits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| smoke | 12 | 6 | 6 | 0 | 0 | 5 | 0 | 0 |
| diagnostic | 24 | 12 | 10 | 0 | 0 | 11 | 0 | 0 |
| confirmation | 6 | 3 | 0 | 0 | 0 | 3 | 0 | 0 |

Every official row passed root coverage, atomic parent-child coverage, lifecycle, global/leaf bound monotonicity, and feasibility gates. Open leaves correctly reject strict certification; completed strict certificates require all relevant leaves closed and LB >= verified UB within tolerance.
