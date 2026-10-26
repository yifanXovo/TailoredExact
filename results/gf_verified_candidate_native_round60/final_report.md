# Round 60：已验证候选发布、原生注入与关键归因

## 结论

本轮完成了端到端候选闭环，但结果不支持把 Gurobi 原生注入升为默认算法。
HGA 的事件级发布修复了 D6/D7 “截止前已有改进、截止后无法重解码”的交接漏洞，
共同逻辑前缀逐行不变，并把截止时 UB 分别从 1.075650/1.542386 降到
0.157083/0.215856。相反，固定 F0 的 D3 虽在 120 秒筛选中明显缩小 gap，
600 秒时双方都认证到同一解，但 INJECT 比 OFF 慢 154.29 秒；这是预冻结规则下的
明显回退。D4 与 D6 长配对均低于决策阈值。因此 HGA verified-event publication
值得保留为显式研究开关，native injection 保持默认关闭。

根点归因也得到更清晰的分层结论：D3/D4/D6 的最后根 Y 都是分数解，产品变量与
`G*Y` 有显著偏差。将最后根 Y 最近整数化并固定后，产品 LP 误差降到机器精度；
D3/D4 的严格路线 MIP 在原 T 不可行、只放宽 T 后可行，而 D6 在原 T 即可行。
所以这些点同时包含表示松弛和路线可实现性差异；不能再把“库存看似好”直接当成
原问题可行候选。

## 固定 F0 的 OFF / DRY / INJECT

所有配对使用相同输入、T、handling、空路线 verified simple start、完整 improving
Gini range、同一 F0 model SHA、Threads=1、Seed=0、Presolve=Auto、严格 gap 参数。
DRY 只做构造、验证、映射和残差；INJECT 才调用 `GRBcbsolution`。

| 窗口 | ID | OFF | INJECT | 候选接受 | 预冻结判定 |
|---:|---|---|---|---|---|
| 120s | D3 | LB 0.038714, UB 0.045002, abs-gap 0.006287 | LB 0.040598, UB 0.045054, abs-gap 0.004456 | 1 confirmed | gap 减少 29.13%，有意义改善 |
| 120s | D4 | 89.74s 认证 | 92.59s 认证 | 1 confirmed | 中性 |
| 120s | D6 | abs-gap 0.050379 | abs-gap 0.050379 | 1 unknown | 中性 |
| 120s | D7 | abs-gap 0.476161 | abs-gap 0.476161 | 1 unknown | 中性 |
| 600s | D3 | 316.28s 认证 | 470.56s 认证 | 1 confirmed | 慢 154.29s，明显回退 |
| 600s | D4 | 90.68s 认证 | 92.41s 认证 | 1 confirmed | 中性 |
| 600s | D6 | LB 0.145070, UB 0.158187 | LB 0.145062, UB 0.158187 | 1 unknown | gap 差 0.059%，中性 |

D3 的短窗改善没有在长窗保留；长窗认证回退是发布决策的主证据。D3 INJECT 的
Work 比 OFF 多 235.28、节点多 13090，说明已接受候选改变了后续原生搜索轨迹，
不能把差异解释成约 1 毫秒的候选构造开销。D4/D6/D7 则说明“成功提交”本身既不
等于改界，也不等于算法收益。逐行数字见 `fixed_candidate_results.csv` 和
`fixed_candidate_pairs.csv`。

## HGA 截止前事件发布

| ID | 原 HGA 截止 UB | 发布臂截止 UB | UB 改善 | 完全相同的共同代际前缀 | 发布/验证 | 验证时间 |
|---|---:|---:|---:|---:|---:|---:|
| D6 | 1.075650 | 0.157083 | 85.40% | 354 行 | 8/8 | 0.000043s |
| D7 | 1.542386 | 0.215856 | 86.01% | 565 行 | 32/32 | 0.000332s |

两臂因墙钟速度不同而完成的总代数不同，但共同 generation、best fitness 和 strict
improvement 标记逐行完全一致；单元测试还在相同 generation-stagnation 边界比较
总代数、decoder calls 和最终 fitness。observer 与候选 ledger 的任何异常都失败
关闭；日志写失败测试证明底层 HGA 逻辑不变。事件明细见 `hga_candidate_evidence.csv`。

## 原生提交与完整集成

最终 tiny native micro 在第一个 MIP 回调从数据 target 构造 F=5/24 的候选；原问题
verifier、完整变量映射、界/类型和当前模型 214 条线性行全部通过，最大 violation=0，
`GRBcbsolution` return code=0。按 [Gurobi callback API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html)
的官方语义，该位置返回 infinity 仅表示延迟处理；
求解后最终整数决策与提交向量一致，因此标为
`confirmed_submitted_integer_decision_vector_is_final_native_solution`。D3 的正式注入
还在 MIPSOL 中观察到完整向量相等。其余 return code=0 且未出现上述证据的运行都
保留为 unknown。

完整 Single-S 配对中，D1 两臂都认证零目标，INJECT 的两个提交都确认且时间差低于
1 秒；C1 的 UB 相同，INJECT 的 LB 从 0.195485 降至 0.194057，abs-gap 增加
0.001428 但相对仅 2.15%，未达到同时 5% 的回退门。final-build C2 K1-H 配对两臂
都有 1 split、1 partial-target MIP、1 terminal MIP；三个候选均被冻结 cutoff 门
拒绝，故 0 映射、0 提交，LB/UB 完全一致。partial 与 terminal 各自写唯一事件文件，
证明前者已真实接线而非仅有死代码。配对见 `full_integration_pairs.csv`。

## split 的真实净贡献

D2/C2 的 K1-H 与 Single-H 都支付同一 HGA、使用同一 verified route state、U 和
完整 Gini 范围；Single-H 只取消 split 与子 LP，并保留一次父 LP、一次 terminal MIP。

| ID | K1-H | Single-H | 结论 |
|---|---|---|---|
| D2 | 8 splits、17 LP、1 MIP、29.35s 认证 | 0 split、1 LP、1 MIP、27.60s 认证 | split 无净收益，约慢 1.75s |
| C2（开发重分类） | 1 split、5 LP、1 partial+1 terminal MIP，gap 7.262% | 0 split、1 LP、1 terminal MIP，gap 11.788% | split 将 LB 从 0.732125 提到 0.769692，有真实收益 |

因此外层 split 既非普遍瓶颈，也非普遍有益；D2 支持 Single-H 简化，C2 支持保留
选择性 split。不能依据一个实例全局删除。逐调用证据见 `split_attribution.csv`。

## 第一/最后根点与固定库存

Gurobi 的 [callback code 文档](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html)
说明根 MIPNODE 会对每个 root cut pass 回调且 node count 在根完成前保持 0；本轮据此
修正了根完成语义。D3/D4/D6 已见非根回调，最后根向量是
`confirmed_complete_before_nonroot`；D7 未见非根且未根上认证，只称
`last_observed_root_relaxation`。

| ID/点 | Y 分数数 | `|G_exact(Y)-G_model|` | `max|zprod-GY|` |
|---|---:|---:|---:|
| D3 first / latest | 0 / 10 | 0.015679 / 0.003106 | 0.418129 / 0.111777 |
| D4 first / latest | 6 / 11 | 0.037838 / 0.038457 | 1.381003 / 1.782661 |
| D6 first / latest | 25 / 29 | 0.017284 / 0.008511 | 0.220417 / 0.260987 |
| D7 first / latest | 28 / 44 | 0.062427 / 0.016729 | 1.245948 / 0.422758 |

bit、visit、mode、arc 的分数统计也在 `root_relaxation_diagnostic.csv`。采样累计开销
分别为 D3 0.0371s、D4 0.0496s、D6 0.0116s、D7 0.00234s；完整 cut-pass 标量轨迹
见 `root_scalar_trajectory.csv`。

最近整数固定库存的结果为：

| ID | 精确固定库存 F | 固定 LP 与 F 差 | 原 T 严格 MIP | 只放宽 T |
|---|---:|---:|---|---|
| D3 | 0.04717885 | 2.1e-17 | infeasible | optimal，同 F |
| D4 | 0.39248199 | 5.6e-17 | infeasible | optimal，同 F |
| D6 | 0.16047674 | 2.8e-17 | optimal（5.51s） | 未需要 |

D3/D4 反事实只改变 T 为 1,000,000，Q、handling、访问、装载和路线次序模型不变；
所以障碍限定为原 per-vehicle route-duration horizon。由于三个 Y 都来自分数根点的
最近整数化，这一诊断只适用于明确列出的启发式库存，不冒充原根点证书。详见
`product_route_diagnostic.csv`。

## 身份、参考、测试与预算

D2/D3/D4 canonical F0 LP 与 Round 59 逐字节相同，D3/D4 的 T 分别确认为
2850/2400。最终交付二进制 SHA-256 为：

* ExactEBRP: `f41af6fe368a2808b5713c5b8db2de151365bbb273c425dae73b88ca9edd65a9`
* Round50 runner: `363c85ffe71918d7a793109f46729d564c79b7a142926a76c4af0eeea6e5edf5`

final-build 同构建参考中，D1 P-GRB/K1-H 分别约 0.085/1.566 秒并都严格认证；
C1 P-GRB/K1-H 使用相同 UB=0.261817，LB 分别 0.191743/0.197806，所有 Round 60
候选开关均 OFF。正式固定和长配对内部也各自使用完全相同的 executable hash；
最终代码审计只补了 partial-target 接线、失败日志回退和行数遥测，之后以 final-build
C2 配对及第六个 micro 验证。完整构建分段见 `build_ledger.json`。

最终 Release 构建成功，37/37 CTest 通过。52/72 个计费尝试，剩余 20；native
micro 为 6/6；最大优化器并发为 1，无 watchdog。两个失败尝试均保留计费：一次
HGA 命令含不受支持 CLI，另一次 P-GRB 在创建求解器进程前遇到 Python 参数类型；
二者修正后均有成功结果，未覆盖失败目录。详见 `budget_audit.json`、
`processes.jsonl`、`final_build.log` 和 `final_tests.log`。

## 发布判断

1. 保留 HGA verified-event publication 为默认关闭、可显式启用的研究功能；它修复
   了可验证候选的截止交接，且本轮没有改变 HGA 逻辑前缀。
2. 不把 native injection 合入 stable `paper-k1-am-sf` 或正式 P-GRB；D3 的长窗
   认证回退否决了短窗单点改善。后续若继续，应先研究何时不提交，而非扩大面板盲跑。
3. 不全局删除 split；用 D2/C2 的相反结果开发基于可审计状态的选择性门。
4. 根界后续优先处理产品表示与 route-duration 可实现性之间的接口；固定 Y 结果表明
   这两层都真实存在，单独盯 Gini 乘积残差不足以预测合法路线。

所有结论只适用于冻结面板与所列窗口，不外推为全历史面板结论。
