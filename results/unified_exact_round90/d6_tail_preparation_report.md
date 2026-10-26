# D6 tail: one zero-Optimize preparation

The root-signed prepare gate SHA-256 `12bc23dc98c1a34734dab2b1d82d8cd015b7041c6da479d9ccdae7bbdc5ca582` admitted one command: `D:/msys64/ucrt64/bin/python.exe scripts/round90_lp_g_d6_tail.py prepare`. It exited 0 after **0.8119156 s full external launch-to-exit wall**; stdout reports `optimizer_calls=0`, stderr is empty. The nested in-wrapper measurement before the preflight write is 0.6300663 s and must not be added to the external wall. No Optimize, solver, build, second preparation or run occurred.

The new `source_snapshot_receipt.json` contains **166 unique Git blobs**, 5,032,131 source bytes, with valid object IDs and all SHA-256 values equal to their pinned expected bytes: 165 production-manifest entries plus the separately pinned `tests/round90_lp_g_split_tests.cpp` (`2dd4582bb757624228fb610a2c9b3cc55fec0b84dca892601ecc1bec83a58d4d`). Seven critical Round90 source identities are accounted for. The frozen binary `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`, D6 input, eight harness files, source manifest and root gate also matched their pinned hashes. This byte audit uses immutable Git ref `a71bd53ca412e9b9e529e7237446687d360a94ce`; it does not require the current Round92 checkout to match Round90.

Prepared identity has exactly two fresh D6 launches in the fixed order ENS-C then LP-G, seed 0. Each command has `--time-limit 7194`, `--process-wall-time-limit 7200`, wrapper hard stop 7198, one thread, Presolve Auto and the same preset request; the sole method toggle is `--round90-lp-g-split=false/true`. Both A1 and B1 flags are absent. No `d6_tail_run_lease.json`, `run_started.json`, raw destination or active lock exists. This preparation does not authorize execution; root must sign an identity-pinned two-arm lease after checking these receipts.

| Preserved artifact | SHA-256 |
|---|---|
| `runner_lp_g_d6_tail/source_snapshot_receipt.json` | `e7c8a64430f869daa8772802c444d22110aaa84aa9b800ac9c222999ccf8b333` |
| `runner_lp_g_d6_tail/identity.json` | `1ffde40351d04ea5c93b66a5310f4a11dc1402909718a6d60b20e1b8e13e5ceb` |
| `runner_lp_g_d6_tail/preflight.json` | `41417ee88096cb4f807786430397c1e6bce3aa35f5a0a497be5ff6f146db788f` |
| `d6_tail_prepare_outer_001.started.json` | `c6607edbb07180761f496055c28bc798ca436297661df4939b7cf64380e96798` |
| `d6_tail_prepare_outer_001.receipt.json` | `2c4b665570a5aff5ea99584a0e1e16397e59f8dbafcc3029cc866e06e1141936` |
| `d6_tail_prepare_outer_001.stdout.log` | `f84d20e6096dcc07f03208727fa1b136f167e67c4f8f8910a36441f32e9cd042` |
| `d6_tail_prepare_outer_001.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

No residual solver/build/Python diagnostic process remained after the command. The exclusive compute slot was explicitly released to root for Round92 G1 before this report was written. All seven artifacts above are small and can be staged directly; no new raw evidence exists yet.
