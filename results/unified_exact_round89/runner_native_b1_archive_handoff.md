# Round89 native B1 G3 raw archive handoff

The rest stage stopped after its D3 pair by the preregistered severe-signal rule. The archive plan bound the finalized smoke 4/4 and rest 2/12 receipts to exactly six attempted raw directories. Ten later arms are listed in the plan/index as `not_run_arms`; `absent_raw_attempts` and `empty_raw_attempts` are both empty. All six source directories remain in place. The archive build was run once after root approved the plan; it reported success and streamed **every one of 8,149 members** from its compressed package, matching source SHA-256 and byte count. There was no second decompression pass.

The immutable plan is `runner_native_b1_raw_plan.json`, SHA-256 `6e293c4c6b40d4d3db2209cb812ea80a75a9fe1c701dd82a45604ba0697cf19c`. The final index is `runner_native_b1_raw_index.json`, SHA-256 `e0a31d8bdfabe499e7721aa35570c110eff2a89495a11ec5e840dfbf12ec90c7`. Total source: 12,274,239 bytes in six raw directories; total compressed: 2,126,999 bytes in six packages. Each package is below the strict 45 MiB limit; no split was needed.

| Package under `runner_native_b1_raw_archives/` | Files | Source bytes | Package bytes | Package SHA-256 |
|---|---:|---:|---:|---|
| `01_E8_ENS-C.tar.gz` | 205 | 1,644,283 | 287,093 | `7b704860dd2d22c925a3373acb5dcbef592abc02fce31dc392150a9cb91315d6` |
| `02_E8_native-B1.tar.gz` | 159 | 1,625,254 | 283,858 | `1c8c4423b424792e6b2877c5203520ae55b301d4f731474d98c87689f3501860` |
| `03_S12_native-B1.tar.gz` | 207 | 1,025,705 | 168,408 | `c12f5ca08fb2c6ac02cea186be51fddc8459ddccddeb615721b7d37a78026486` |
| `04_S12_ENS-C.tar.gz` | 270 | 1,055,288 | 174,469 | `03e84d48536af1df85649017351d8384e0dac0e7a80cb1e479c036d4d67d8241` |
| `05_D3_ENS-C.tar.gz` | 3,273 | 3,274,262 | 575,715 | `750e9db5cf9ba0e9191b9dae71a3cd32fc26312198647b2a7247ccefa7a59ce3` |
| `06_D3_native-B1.tar.gz` | 4,035 | 3,649,447 | 637,456 | `5ba7102530e95f13622a7fc9046a580ed21425218f95638f5d90da78036c25af` |

The plan command exited 0 in 1.4678797 s outer launch-to-exit; the build exited 0 in 7.0756928 s. The 8.5435725 s sum is the complete recorded external archive-command cost; nested index/compression/verification phase times are subdivisions, not additions. The build stdout names all six verified packages, and both command stderr logs are empty. A post-build Win32 process check found no ExactEBRP, Gurobi, build, Round89 runner, or archive process.

Scoped Git file list for this evidence batch (explicit paths; do not add `runner_native_b1_g3/raw/` or use a broad glob):

```text
results/unified_exact_round89/runner_native_b1_raw_archives/01_E8_ENS-C.tar.gz
results/unified_exact_round89/runner_native_b1_raw_archives/02_E8_native-B1.tar.gz
results/unified_exact_round89/runner_native_b1_raw_archives/03_S12_native-B1.tar.gz
results/unified_exact_round89/runner_native_b1_raw_archives/04_S12_ENS-C.tar.gz
results/unified_exact_round89/runner_native_b1_raw_archives/05_D3_ENS-C.tar.gz
results/unified_exact_round89/runner_native_b1_raw_archives/06_D3_native-B1.tar.gz
results/unified_exact_round89/runner_native_b1_raw_plan.json
results/unified_exact_round89/runner_native_b1_raw_index.json
results/unified_exact_round89/runner_native_b1_archive_plan_001.outer_receipt.json
results/unified_exact_round89/runner_native_b1_archive_plan_001.stdout.log
results/unified_exact_round89/runner_native_b1_archive_plan_001.stderr.log
results/unified_exact_round89/runner_native_b1_archive_build_001.outer_receipt.json
results/unified_exact_round89/runner_native_b1_archive_build_001.stdout.log
results/unified_exact_round89/runner_native_b1_archive_build_001.stderr.log
results/unified_exact_round89/runner_native_b1_archive_handoff.md
results/unified_exact_round89/runner_native_b1_g3/identity.json
results/unified_exact_round89/runner_native_b1_g3/preflight.json
results/unified_exact_round89/runner_native_b1_g3/processes.jsonl
results/unified_exact_round89/runner_native_b1_g3/summary.jsonl
results/unified_exact_round89/runner_native_b1_g3/runtime_status.json
results/unified_exact_round89/runner_native_b1_g3/runner_smoke_completion.json
results/unified_exact_round89/runner_native_b1_g3/runner_smoke_gate.json
results/unified_exact_round89/runner_native_b1_g3/runner_smoke_lease.json
results/unified_exact_round89/runner_native_b1_g3/smoke_outer_receipt_001.json
results/unified_exact_round89/runner_native_b1_g3/smoke_outer_stdout_001.log
results/unified_exact_round89/runner_native_b1_g3/runner_smoke_summary_snapshot.jsonl
results/unified_exact_round89/runner_native_b1_g3/runner_smoke_report.md
results/unified_exact_round89/runner_native_b1_g3/runner_rest_completion.json
results/unified_exact_round89/runner_native_b1_g3/runner_rest_lease.json
results/unified_exact_round89/runner_native_b1_g3/runner_rest_risk_stop.json
results/unified_exact_round89/runner_native_b1_g3/rest_outer_receipt_001.json
results/unified_exact_round89/runner_native_b1_g3/rest_outer_stdout_001.log
results/unified_exact_round89/runner_native_b1_g3/runner_rest_stop_report.md
results/unified_exact_round89/runner_native_b1_g3/runner_cross_arm_E8.json
results/unified_exact_round89/runner_native_b1_g3/runner_cross_arm_S12.json
results/unified_exact_round89/runner_native_b1_g3/runner_cross_arm_D3.json
```

The `.log` paths may be ignored by Git and need explicit inclusion if root chooses to commit them. Source driver and historical kernel are outside this raw evidence list. Root should spot-check the six package SHA/size and index counts before committing; no further solver or archive run is needed.
