# Round92 H-ACT G3 rest：预注册风险停止

本批按 `runner_rest_lease.json` 仅发射一次 `D:/msys64/ucrt64/bin/python.exe -B scripts/round92_handling_g3.py run-rest`。D3、C2、D7、U6 的八臂均完成原物理、coverage、参数及同组交叉审计；U6 两臂均未认证，H-ACT 的剩余绝对 gap `0.036969692206756694`，ENS-C 为 `0.022362482232390457`，差 `0.014607209974366237`、比值约 `1.653`，触发预注册 `severe_open_gap_signal`。runner 按合同立即停止，F5/F6 四臂未启动。该信号只说明此固定配对在 1200 秒截止时较差，不是普遍性能结论。D7/U6 未认证，不能用接近截止的运行秒数声称证明速度相同。

| 序号 | 角色 | 臂 | 完整 ExactEBRP 进程秒 | U | L | 认证 | 审计 | H-ACT 行代/累计行/cache hit |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 5 | D3 | ENS-C | 140.703 | 0.04500155005562836 | 0.04500155005562838 | 是 | 通过 | 关闭 |
| 6 | D3 | H-ACT | 148.125 | 0.04500155005562836 | 0.04500155005562831 | 是 | 通过 | 3 / 9 / 2 |
| 7 | C2 | H-ACT | 128.172 | 0.8299634131717752 | 0.8299634131717740 | 是 | 通过 | 5 / 10 / 4 |
| 8 | C2 | ENS-C | 115.828 | 0.8299634131717752 | 0.8299634131717741 | 是 | 通过 | 关闭 |
| 9 | D7 | ENS-C | 1197.141 | 0.23660241228050372 | 0.20335723151531615 | 否 | 通过 | 关闭 |
| 10 | D7 | H-ACT | 1197.125 | 0.22372455873338280 | 0.20463924789062530 | 否 | 通过 | 3 / 12 / 2 |
| 11 | U6 | H-ACT | 1197.140 | 0.16739628937553010 | 0.13042659716877342 | 否 | 通过 | 5 / 20 / 4 |
| 12 | U6 | ENS-C | 1197.156 | 0.15142092391739340 | 0.12905844168500294 | 否 | 通过 | 关闭 |
| 13 | F5 | ENS-C | — | — | — | 未运行 | — | — |
| 14 | F5 | H-ACT | — | — | — | 未运行 | — | — |
| 15 | F6 | H-ACT | — | — | — | 未运行 | — | — |
| 16 | F6 | ENS-C | — | — | — | 未运行 | — | — |

D3 两臂都认证同一目标，H-ACT 证明耗时比 ENS-C 多 `7.422` 秒（`1.05275×`）；C2 多 `12.344` 秒（`1.10657×`），为已认证配对的最大时间回退。D7 两臂截止未认证，H-ACT 的 U 低 `0.01287785355`、L 高 `0.00128201638`；U6 则 H-ACT 的 U 高 `0.01597536546`、L 高 `0.00136815548`，净 gap 更大。未按单项较优点择取。四组 `runner_cross_arm_*.json` 均 `passed=true`，仅核原问题界不矛盾，不合并臂的终点。

八臂 native call started/returned 依次为 `5/5, 5/5, 7/7, 7/7, 4/4, 4/4, 6/6, 6/6`；各臂物理 witness 数依次为 `8, 14, 10, 8, 30, 16, 13, 18`，审核通过。H-ACT 四臂行账为完整 `complete_model_generation_evidence`，共 16 次模型生成、51 条累计行、12 次复用；正常结果的行代与 `paper_optimize_ledger.csv` 按模型 SHA 连接，当前 canonical LP SHA 已核对。旧 epoch 若覆盖，旧 LP 字节未单独归档，不能事后独立重放旧字节。每臂 `result.json` 均为正常返回；外部树 root/child coverage、backend parameter roundtrip、原物理 endpoint 和默认关身份由原审计核对。八臂中的 time-limit 是算法自身在整次截止内正常收束，不表示证书。

完整外层发射 `2026-09-27T17:10:12.3311265Z`，退出 `2026-09-27T18:39:02.5193222Z`，墙钟 `5330.1855362` 秒、child exit `1`（预注册风险停止）；原始 stdout/stderr 在 `g3_rest_outer_001.*.log`。runner 内整阶段 `5330.016` 秒，八臂 process wall 合计 `5321.390` 秒，八臂连准备/离线审计的 full-attempt 合计 `5329.876` 秒，其中离线审计合计 `6.1242655` 秒；这些是嵌套口径，不得相加。外层相对 runner 的 `0.1695362` 秒和 runner 相对臂 full-attempt 的 `0.1400` 秒是剩余调度/发射/收尾成本。未发射的四臂成本为零，不从原计划总 cap 推算实际支出。

同期 postflight 原始收据 `g3_rest_postflight_receipt.json`：15 份源文件与冻结哈希逐项一致，main SHA `767d2cbfa50f332a8b9cd6fa3f01888509509b11c2444100d7cafd63bc204b9b`、core SHA `29cb167a388e1a76bd544131bf59684be3950f92f13ecdb755525644f596de12` 一致；`Get-CimInstance` 核相关 solver/build/runner 残余进程 0。检查耗时 `0.6430167` 秒，在上述外层 runner 发射成本之后，单列。源码身份、原始各臂、完整审计与风险账均保持原位，未重试、延期、构建或归档。

证据入口：`runner_handling_g3/summary.jsonl` 第 5–12 行、四份 `runner_cross_arm_*.json`、`runner_rest_completion.json`、`runner_rest_risk_stop.json`、各 `raw/05_*` 至 `raw/12_*` 的 `completion.json`/`audit.json`/`result.json`/原始日志，以及顶层 `g3_rest_outer_001.receipt.json`、`g3_rest_postflight_receipt.json`。计算槽已在 postflight 后明确释放。
