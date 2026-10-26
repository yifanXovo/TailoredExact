# Round90 LP-G split: bounded pure qualification 001

The six commands admitted by `../qualification_001_lease.json` all met their expected outcome. Three pure tests passed; three invalid CLI combinations exited nonzero with the prescribed Round90 validation message. This is a zero-Optimize qualification of geometry/cache helpers and CLI rejection only. It does not establish the live controller's parent-LP/requeue/epoch behavior or performance.

| Command | Exit | Whole command wall (s) | Observed outcome |
|---|---:|---:|---|
| `Round90LpGSplitTests` | 0 | 0.0761766 | 3 groups passed |
| `GlobalGiniTreeTests` | 0 | 0.1563913 | 9 groups passed |
| `Round47AdaptiveMassTests` | 0 | 0.3442892 | 28 checks passed |
| non-ENS `custom` + Round90 | 1 | 0.4555441 | Requires ENS-C Round83 gcap-frontier |
| ENS-C Round83 + Round90 + A1 | 1 | 0.0594213 | A1/B1 combination rejected |
| ENS-C Round83 + Round90 + B1 | 1 | 0.0594893 | A1/B1 combination rejected |

All commands had a 120 s outer cap and no timeout. The three CLI invocations used the verified absent `results/unified_exact_round90/__nonexistent_cli_sentinel__.txt`; they failed at parameter validation. No real model or solver was launched. The six per-command launch-to-exit wall times sum to **1.1513118 s**. The enclosing batch wall was **1.2274166 s**, including **0.0761048 s** of wrapper overhead. The original `batch_summary.json` has a null command-sum field due to a metadata aggregation error; `batch_cost_reconciliation.json` adds the sum from immutable individual receipts without rerunning commands or altering that summary. These nested times are not added again to the batch cost.

`preflight.json` and `postflight.json` match the signed lease for all seven source and five binary SHA-256 identities. The CLI sentinel remained absent, and the final host check found no ExactEBRP, Gurobi, build, or Round90 Python worker. Exact executable paths and argv, exit codes, raw stdout/stderr, supervision details, and individual costs are in the six numbered `*.receipt.json` and paired stream files. No build, source edit, test retry, or real-instance Optimize occurred in this qualification.
