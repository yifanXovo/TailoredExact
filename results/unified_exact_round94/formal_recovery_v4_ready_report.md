# R94 formal recovery v4: offline ready

The v4 repair is prepared and independently rechecked. It compares the saved and replayed ENS audit after excluding **only** `neutral_exchange.offline_seconds`; both values must exist, be finite, and be nonnegative. All other ENS fields compare exactly, as does the full P audit. No native `Optimize` call was made. The original two paid formal arms, their failed v2 audit, the original 1,442.5685015-second outer receipt, and the failed v3 prepare remain unchanged.

Math's independent static review passed (`formal_recovery_v4_static_review.md`). The sole v4 `prepare` exited 0 with full launch-to-exit wall time **7.6757639 s**. The one read-only `require_prepared()` self-check exited 0 in **7.56911 s**. These are offline costs, separate from formal native process costs. The v4 prefix manifest contains 18,956 files and 13,743,617 bytes. It verifies the two existing F2 records and retains precisely launch numbers 3–12, 10 never-started arms, with original caps totaling 11,700 s. The recovered F2/P-GRB endpoint is U=0.8659435203229894, L=0.7577452455123087, uncertified; F2/ENS-C is U=0.8659435203229894, L=0.865943520322989, certified. These are recovered **paid-prefix** evidence, not new search results.

| Item | SHA-256 |
|---|---|
| v4 runner `scripts/round94_lpg_formal_recovery_v4.py` | `b1f8519e74e107030ac4a9ed515ddf6cdcea31b52bc8547044f85df1a2b9d1f5` |
| v4 preregistration | `e09f23878fa2b4db824f44da0f222fb97f9fc48b681e8e35d57002b7892d5c8c` |
| prepare outer receipt | `4efe4bc20db9795cd8f538ca3ceda20d026583f6b8835539adb6eddd5a75a2e9` |
| read-only self-check outer receipt | `1a6b7d11aeab029ca7ae566986c4d4fd8c8b484320557e817bc82aa99f229775` |
| v4 identity | `5f860b6d68a81e1257db3b817e81da58b53a2568b0e12e6b61f8ebd2662e562a` |
| preflight | `0ccebc06011dee82f1c212b8690f3264853696ba80c3cbf55d5187d11782570a` |
| prefix manifest | `897016e1563c186e261a13711db8e613c4e078b663fdfd3303726e9da5dec3c4` |
| P offline audit | `f7820605ecb1f289b7a03ec0cac90a361f2ad5a44c7b98189c003001014615a7` |
| ENS offline audit | `dfd34bb3fb73e2f6f4d8672986a07ef4c53778a5be085c2be21c730767f59baa` |
| prefix check | `84ba1012619765d37749a7a7366637f61260491c164c308f17258e86c25b87ac` |
| saved v3 timing-fault comparison | `88879d32754ae12e649fccd11b4c115a48f67d78acdf7206ba6e88ccfcb44ce8` |

Before any remaining native run, root must commit/pin this version and write `runner_lpg_contemporary/formal_recovery_v4/remaining_formal_lease.json` exactly as the runner checks: schema `round94-formal-recovery-remaining-lease-v4`, `authorized_by: "root"`, `allow_optimize: true`, `formal_recovery_identity_sha256: "5f860b6d68a81e1257db3b817e81da58b53a2568b0e12e6b61f8ebd2662e562a"`, `offline_prefix_check_sha256: "84ba1012619765d37749a7a7366637f61260491c164c308f17258e86c25b87ac"`, `planned_processes: 10`, and `execution_order` equal to the runner's frozen `REMAINING` list. No such lease or continuation has been run.
