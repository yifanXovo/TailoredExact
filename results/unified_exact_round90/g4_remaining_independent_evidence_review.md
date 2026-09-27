# Round90 G4 剩余九角色独立证据验收

**结论：证据 PASS，无正确性、身份或执行阻断；LP-G 仍属混合的开发结果，不获晋升。** 本次只读原有小型收据、`summary.jsonl`、18 个结果/审计/参数读回摘要、9 个跨臂文件和 9 份短切点账本；未求解、构建、重放 journal、遍历模型或重新压缩。权威批次为 [`g4_remaining_report.md`](g4_remaining_report.md)（SHA-256 `e192f163f999d0f23d6e28ed43def3897748020c95f31703f5671c259dafc961`）、[`g4_remaining_table.csv`](g4_remaining_table.csv)（`9a0324b702b25d486ff6f231eda8cf5dc2286c33ba2c1f3f6da27bb0f2a7b91b`）。

## 执行、身份与原问题证据

`preregistration_g4_remaining.json` 的 N12、D4、E7、C6、C8、F1、C20、B50、S50 九角色/18 臂顺序，与 `identity.json` 的 18 条启动命令及 `summary.jsonl` 的 18 条实际结果逐项相同；每角色两臂引用相同场景、输入 SHA、T/服务时间、lambda 和整次 cap，只有预注册顺序及 `--round90-lp-g-split` 的真假不同。所有 seed 实际读回 0、线程 1、Presolve −1，控制/候选预设分别为 R83 ENS-C / R90 LP-G；18 臂返回码 0、均在各自 cap 内、各自审计 PASS。身份的候选二进制 SHA 是 `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`，冻结的 R90 七源码、runner/输入/harness SHA、源 Git 对象见 `identity.json`（自身 SHA `c248fcaa41af4d10f3a3b7f9ac86cfa22c303475e6de2f60dbf3319206231ac7`），并由准备/运行门禁核对。随后 checkout 的 HEAD/新增 R92 文件不属于此批运行身份；**不能把当前工作树称作 R90 冻结源码**。

18 份 `audit.json` 均 `passed=true`，原物理最终见证均通过时长验证，累计 103 个物理见证；原生界来源为 `complete_domain_native_evidence`。结果里的 root coverage、parent-child coverage、global-bound monotonic 均为 true。9 份 `runner_cross_arm_*.json` 均在原有 `1e-7` 矛盾门槛内 PASS，仅交叉检查有效下界与物理上界，**不合并两个算法的证书**。N12/D4/E7/F1/C20/B50 六角色共 12 臂实际数值认证；C6/C8/S50 六臂以 `round31_c6_external_gini_tree_time_limit` 结束，`relevant_leaf_open`，只有已验 U 与覆盖下的 L，没有完成证明。C20 候选的 `L−U≈1.39e−16` 是原数值容差内的舍入倒置，不是严格负 gap。以上为项目浮点/残差门禁的数值证书，并非有理对偶证明。

## 决策链与成本

九个 LP-G 原始短账本合计 **22** 次切点提案：12 个当前最优父 LP 的 G、10 个中点退回；22 次子 LP 对与 AM 均完成。仅 **6** 次有 `realized/atomic_two_child_split`：N12、C6、C8 各 1，B50 3。**7** 次 `native_target_result/parent_requeued_no_split`，其后同 epoch 子缓存再入账本，7 次 `child_lp_status/reused_identity_verified`；另 **9** 次 `am_decision/proposed_exact_parent_closure` 只是请求父 terminal MIP。所查 parent/child LP receipt 带 epoch 0、模型 SHA 与真实 Optimize 行号；没有完整历史模型字节归档。C6/C8/S50 尽管有请求，最终仍开放，绝不能把请求称为已关闭。B50 三次实际 split 中仅首个用当前 LP-G 点，其余两次用中点；F1 唯一提案也只是中点且未 split，因此不能把所有时间差直接归因新切点。

重新从 18 行表求和：原生进程完整墙钟 **14,769.767 s**；预启动 5.280 s、离线逐臂审计 3.543 s，及模型构建/读入/solver 151.526/7.517/14,477.191 s 均是嵌套分解，不能重复相加。外层一次命令从 05:41:11.945Z 至 09:47:32.051Z，**14,780.090222 s**、exit 0；`run_completion.json` 记 18/18、无失败前缀/未运行臂、内部 outer 14,779.706527 s。`g4_remaining_postrun_workflow.receipt.json` 另披露外层结束至报告/表观察的 327.083 s 经过时间，不称 CPU 时间或免费算法成本；并记录零残留与计算槽释放。报告/表、`summary.jsonl`（`950dd6ffc40101c9ff6dbcb7620ccbfc1472a74c3e3e485c7d5bd6a082b5581a`）、`run_completion.json`（`184043c3bf76f6162cfbd9af2a8bbe9cddb0644c13e1ef04d8d8dac4dacd9c7a`）、外层收据（`a076921f520475031683f1296a03220d2b871a796f0ab3cfbe05f9b7c50512bc`）与后处理所存哈希一致。未见重试、额外种子或中途重启。9 角色均未触发预注册严重停批：认证对里没有同时超过 1.5 倍与 30 s 的候选劣化；三个双截止角色的候选 gap 均未达到既定 1.5 倍且绝对差 >0.01 的恶化门槛。

## 有限 panel 判断与下一证据建议

六个双认证角色的 LP-G/ENS-C 进程时比为 N12 **1.3565**、D4 **1.0234**、E7 **1.1149**、F1 **0.9882**、C20 **1.1222**、B50 **0.6641**。B50 省 385.672 s，C20 多 41.703 s；N12 虽比值较高，只多 0.657 s。C6/C8/S50 两臂均到相同整次截止，约等的时间不是认证速度比；其 LP-G 末 gap 分别 0.092542/0.078919/0.016176，对照 0.115161/0.108827/0.016304，且 C6 候选 U 略差，不能只看 gap 称优势。已验的 G3 四双认证、四双删失，G4 优先 F2 双认证及 D6 的 ENS-C 已认证/LP-G 截止，连同本批构成预注册 seed-0 的 **11 双认证、7 双删失、1 不对称删失**，无全角色一致提速。F2 与 B50 的较大认证时间收益是真的；C2 的三种固定 seed 中两快一慢；D6 是未解决的尾部保护风险。P-GRB 仍无本批同源同期臂，不可由这些比值声称优于 P-GRB。

**建议 root 若继续界定 LP-G 而非现在晋升，可预先固定且只做一次 D6 seed 0、同一冻结 R90 二进制/输入/参数/启动、两臂各 7200 s 整次上限的成对完整运行。** 这有具体信息价值：D6 在 3600 s 是唯一“ENS-C 已证、LP-G 未证”的保护角色，LP-G 尚余约 `7.31e−4` 数值 gap；根界近不提供闭合时间保证。新双臂可在同一较长截止下界定是否完成及实际尾部代价，保留原 3600 s 的失败证据，不续接旧搜索、不设组件切片、不调整 split/AM，也不因一次成功自动晋升。其最多 14,400 s 的完整进程成本应事前接受；若 root 判该成本不值得，现有证据足以将 LP-G 暂存，理由应是混合认证时间及 D6 未闭合，**不是**几个轻微回退本身。此建议不是执行许可，且一次 D6 结果仍不能给跨种子/新数据优势或 P-GRB 性能结论。
