# Round89 native-B1 G3 smoke — four-arm receipt

The single admitted command `D:/msys64/ucrt64/bin/python.exe scripts/round89_native_b1_g3.py run-smoke` returned exit 0. Outer wall was 15.2719445 s; the four solver-process walls sum to 13.8590000 s. Exact command, UTC start/finish and exit are in `smoke_outer_receipt_001.json`; complete stdout is preserved in `smoke_outer_stdout_001.log`. The runner's `runner_smoke_completion.json` records 4/4 complete, all audits passed and no stop reason. Each arm returned normally below its 120 s whole-process cap; original physical/evidence and cross-arm audits passed.

| Role | Arm | Process wall (s) | Verified U | Valid L | Certificate | Native-B1 callback evidence |
|---|---|---:|---:|---:|---|---|
| E8 | ENS-C | 3.531 | 0.021337006039780566 | 0.021337006039780573 | yes | default off |
| E8 | native-B1 | 2.812 | 0.021337006039780566 | 0.02133700603978047 | yes | 2/2 MIP summaries; 63 MIPNODE calls; 467 reliable rows / API-success submissions |
| S12 | native-B1 | 3.860 | 0.05856397312578515 | 0.05856397312578488 | yes | 1/1 MIP summary; 185 MIPNODE calls; 619 reliable rows / API-success submissions |
| S12 | ENS-C | 3.656 | 0.05856397312578515 | 0.05856397312578488 | yes | default off |

All three native-B1 summaries match unique Optimize ledger rows and the current canonical LP SHA. There was no epoch-overwritten source LP in these two cases. `GRBcbcut` API success does not establish solver retention or causal bound gain; both roles certified the same objective in both arms. E8 B1 was 0.719 s faster by solver-process wall, while S12 B1 was 0.204 s slower, so these easy solved smoke cases do not establish a general speed effect. `runner_cross_arm_E8.json` and `runner_cross_arm_S12.json` both pass within the original-problem tolerance, without merging endpoints.

After completion, an OS process query found no matching ExactEBRP, Gurobi, build or Round89 runner process. The computation slot was released. The rest stage remains unleased; this report does not authorize it.
