# Round89 native B1 qualification — stopped at pure gate

The signed `qualification_lease.json` (SHA-256 `bb6d7a746ae0b9fb8601721dc3249fa233d9b88bedd1c353e4a448f4645e7972`) was checked before execution. All nine admitted source hashes and both main/Micro executable hashes matched before and after the attempted stages (`identity_pre.json`, `identity_post.json`). No source file or frozen executable changed.

| Stage | Exit | Complete command wall | Evidence |
|---|---:|---:|---|
| Build only `Round53F0AndCallbackTests` and `Round55StationStateChainTests` | 0 | 1.813 s | `compile-regressions.*` |
| `Round53F0AndCallbackTests` once | 0 | 0.328 s | `pure-round53.*`; 30 cases passed |
| `Round55StationStateChainTests` once | 0 | 1.250 s | `pure-round55.*`; 58 checks passed |
| `Round89NativeOtB1Micro pure` once | **1** | 0.313 s | `pure-round89.*` |

The Round89 pure test failed with `wide actual-chain support audit failed:state_support_incomplete`. The six-state fixture sets all column upper bounds to 10, including `Y_1` and `Y_2`, while its selector support ends at inventory 5. The production identity audit correctly rejects this inconsistent fixture. This is a test-fixture blocker, not evidence of native cut performance or mathematical invalidity. The underlying code was not repaired in this lease.

Execution stopped immediately. `pure-json`, the independent Fraction oracle, and the native six-arm toy were **not launched**. Actual Optimize count is **0**, versus the maximum six permitted later in the lease. No real-instance solve occurred. No automatic retry occurred. The four outer command receipts record 3.704 s total process wall and 3.751 s total wrapper wall; the latter includes command receipt work and is the non-overlapping recorded execution cost. The source compilation is engineering cost, not an algorithm timing claim. The original stdout/stderr and command receipts are retained. A post-stop process check found no residual solver/build process; the exclusive compute slot is released.

Next action requires a new root decision and source/test identity: correct the isolated wide fixture's `Y` upper bounds, independently review the change, rebuild, and issue a fresh lease before re-running a failed stage. The existing failed receipt must remain part of the evidence.
