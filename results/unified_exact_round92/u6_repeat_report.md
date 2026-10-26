# Round92 U6 固定三 seed 风险复核

按已签 run lease 只发射一次 `D:/msys64/ucrt64/bin/python.exe -B scripts/round92_handling_u6_repeat.py run`。新 seed 1/2 四臂全部正常完成、原物理/coverage/界/同组交叉审计通过；每臂 C++ 正常结果的 Gurobi Seed requested/effective、set/get 返回码实际核为指定 1 或 2。没有重试、改阈值、增加 seed/cap、恢复 F5/F6。下表 seed 0 两臂为此前 G3 已付冻结参照，绝未重跑。本次四臂全部在 1200 秒完整进程 cap 内结束，但均未认证，秒数**不是证明收敛时间**。

| seed | 臂 | 完整 ExactEBRP 进程秒 | 物理 U | 全局 L | 剩余绝对 gap | 认证 | 行代 / 累计行 / cache hit |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 0，历史 G3 | H-ACT | 1197.140 | 0.16739628937553010 | 0.13042659716877342 | 0.036969692206756694 | 否 | 5 / 20 / 4 |
| 0，历史 G3 | ENS-C | 1197.156 | 0.15142092391739340 | 0.12905844168500294 | 0.022362482232390457 | 否 | 关闭 |
| 1，本次 | ENS-C | 1197.250 | 0.15649768651840162 | 0.12922145942037133 | 0.027276227098030292 | 否 | 关闭 |
| 1，本次 | H-ACT | 1197.172 | 0.15196026652203048 | 0.12889847442226150 | 0.023061792099768996 | 否 | 5 / 20 / 4 |
| 2，本次 | H-ACT | 1197.156 | 0.16543666334045026 | 0.12870589292558512 | 0.036730770414865140 | 否 | 5 / 20 / 4 |
| 2，本次 | ENS-C | 1197.110 | 0.15738282333418346 | 0.12890585511579030 | 0.028476968218393156 | 否 | 关闭 |

原 severe open-gap 联合线为 `gap_H > 1.5 × gap_ENS` **且** `gap_H−gap_ENS > 0.01`。seed 0 的 H-ACT 多 `0.014607209974366236`，过线；seed 1 少 `0.004214434998261296`，方向相反；seed 2 多 `0.008253802196471982`，未过线。仅 `1/3` seed 各自同时过两项阈值。三对均为同类 open，故可算冻结的中位数：`median(gap_H−1.5 gap_ENS)=-0.005984681912724596`，`median(gap_H−gap_ENS)=0.008253802196471982`；两者都未越原线，预注册结论 `risk_not_reproduced`。这表示 seed 0 严重 gap 信号在固定两次复核中没有复现；seed 2 仍有 H-ACT 较大 gap，不能写成无回退，更不能由三 seed 宣称统计显著或方法晋升。

本次四臂 native calls started/returned 均为 `6/6`，独立物理 witness 数依次 `16, 29, 4, 26`。Seed-aware adapter 对每臂全部六条**原始** call settings 严格核对应 Seed 及其它容差/参数，再仅对送入冻结 R86 reader 的内存浅副本投影 Seed=0；原 journal/receipt/observations 保持原字节，`audit.json` 记原始 call 数与投影事实。正常 C++ `result.json` 另外核 seed requested/effective 及 set/get 成功、Threads1/Presolve Auto、原 25 个 decoded descent seeds。H-ACT 两臂均有五次模型生成、20 条累计静态行、四次精确 cache hit；行账与 Optimize 模型 SHA 的连接及当前 canonical LP 身份经冻结 helper 审计。历史若重写的 LP 旧字节仍未单独归档，不能声称完整旧 epoch replay。两 seed 的 `runner_cross_arm_U6.json` 均通过原问题界不矛盾检查；跨臂界没有拼作任何单臂证书。两份 `runner_repeat_risk_signal.json` 的性能 signals 均为空，且 seed 1 的结果没有选择性阻止 seed 2。

外层 UTC `2026-09-27T19:04:40.2486587Z` 发射、`2026-09-27T20:24:38.1979562Z` 退出，真实 child exit `0`，外层完整墙钟 `4797.9466449` 秒；原 stdout/stderr/started/receipt 在顶层 `u6_repeat_run_outer_001.*`。runner 内墙钟 `4797.282400700264` 秒，四臂进程墙钟合计 `4788.688000000082` 秒，四臂含预检与离线审计的 full-attempt 合计 `4796.90800000075` 秒，其中离线审计 `7.11048709973693` 秒。外层相对 runner 增 `0.664244199736459` 秒，runner 相对臂 full-attempt 增 `0.37440069951117` 秒；这些为嵌套口径，不能相加。先前零 Optimize prepare 另耗外层 `1.0021432` 秒，seed 0 先前 G3 成本也不混入本次发射。`run_completion.json` 记 completed=4/planned=4/error=null，失败尝试零；`postflight.json` 同期核 15 源、main/core 哈希全匹配、相关残余 solver/build/runner 进程零，postflight 内耗 `0.326317900326103` 秒。计算槽已明确释放，不再开展研究运行。

小证据入口：新 runtime `runner_u6_repeat/identity.json`、`preflight.json`、`summary.jsonl`、`three_seed_summary.json`、`run_completion.json`、`postflight.json`；每个 `seed_1`/`seed_2` 的 `runner_cross_arm_U6.json`、`runner_repeat_risk_signal.json`、两臂 `raw/*/launch.json`、`completion.json`、`audit.json`、`result.json`、`native_parameter_evidence.json`，以及顶层原始 outer receipt/log。完整 journal、原始模型/Optimize/行账与所有日志保留在各自 raw 目录待归档；冻结 seed 0 身份见 `preregistration_u6_repeat.json`。
