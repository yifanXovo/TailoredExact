# G4 F2/D6 priority batch: independent evidence review

**结论：证据验收通过，可按既定 G4 协议继续；不能据此晋升 LP-G。** 本次仅只读既存报告、四条摘要、外层收据、各臂 `result.json`/`audit.json`、选定 LP/MIP 与分裂账本；未重新求解、重放审核或构建。报告 `g4_priority_report.md` SHA256 `5368e6dc99c25a1d9ae41dfe1df294df60eebf585448b9fa1eae52c5c2ca9fa3`，表 `g4_priority_table.csv` SHA256 `00a3a569c5ff651b1e5bd9c1a876b25286719da766623a3cacdf71e095ff025f`。原始 `summary.jsonl`、`run_completion.json`、外层 receipt 的 SHA256 分别为 `df5412315125b00805c608f48cc0b6a6161c2aefdae36336c45e5efba5b57984`、`0dc2bdb69d74c6dca96a52ffdcd109cbbc5d046976eacb67f49c78907f27940a`、`e177dc3b0372c1ab3fa7c13f316ff8473087d4d408af6dd1c9b8d2a1b82cd272`，与报告一致。

固定顺序确为 F2 ENS-C→LP-G、D6 LP-G→ENS-C；四臂各执行一次，均 exit 0、同一 `bac65ff3b...2f2` 二进制与七份源身份，seed 0、单线程、Presolve Auto 的原生回读通过。F2 输入 SHA `ebdf99e7...b645e`、D6 `070c2c14...1c1d`，各自两臂的场景、处理时长、λ 与 cap 相同。两角色的根 LP 模型 SHA 在同角色两臂分别同为 `a37e2165...8091` 和 `356a4653...7b89`。四份离线 audit 均通过、各有已验物理上界（F2 8/15，D6 4/4 个 witness 行）；根/亲子覆盖、界有效性为真，D6 LP-G 的 `all_relevant_leaves_closed=false` 且严格证书拒因 `relevant_leaf_open`，其余三臂闭合并取得项目数值证书。跨臂原问题界矛盾检查两角色均通过；它不合并两个臂的证书。

| 角色 | ENS-C | LP-G | 有限结论 |
| --- | --- | --- | --- |
| F2 | 585.656 s，认证，U≈L=0.865943520323 | 311.578 s，认证，U=0.8659435203229894，L=0.8659435169327837 | 同源配对耗时比 0.5320；两个原问题数值终态有效。 |
| D6 | 3447.219 s，认证，U≈L=0.157083131103174 | 3597.203 s，到全程截止仍开放，U=0.15708313110317415，L=0.15635229350613236 | 后者不是认证时间；已观察时间比认证 ENS-C 多 149.984 s、达到其 1.0435 倍，只是后续认证时间的下限。 |

点提案不能当作分裂或证明。F2 LP-G 四个合格提案（当前父 LP G 点 1、中点 fallback 3）均有完整子 LP 对和决策，前两次有 `realized` 原子双子分裂；第三次 native target 达界后父叶重排，第四次仅请求 `proposed_exact_parent_closure`，最终该臂另有实际认证。D6 LP-G 在 epoch 0 对同一 L0 两次提出 `G=0.014270143300579645`，两次均有完整子 LP 对与 AM 决策，第二次子 LP 的 SHA/epoch 与第一次相同且账本标 `reused_identity_verified`。其左/右子界为 0.13583129417005677/0.1393595889677619；首次 AM 分数 0.0404031<0.08，native target 返回 `INTERRUPTED` 且达到目标，只是 `parent_requeued_no_split`。第二次父界已升至 0.14102554667907011，旧子界无严格增益，故请求 exact-parent MIP；原子分裂数仍为零。`paper_optimize_ledger.csv` 中 L0 terminal MIP 为 `TIME_LIMIT`（3558.363 s、7618.03 Work、36864 nodes），因此请求关闭绝非实际关闭。

D6 默认 ENS-C 的相同根 LP 后使用中点 `0.078754901807280869`；其第一对中右侧 LP 不可行，C6 账本记 `atomic_parent_replaced_by_two_children`，然后在 L0.0 请求 exact closure，末端 MIP `OPTIMAL`（3408.863 s、7748.31 Work、22900 nodes）。所以 LP-G 即使零次实际分裂，提议点仍改变完整子 LP/不可行性判定、native-target 重排和末端模型/搜索路径；这些观察不构成点选择单独导致 D6 延时的因果分解。F2 的末端 MIP 亦在不同叶模型上运行，不能直接按其 Work 差额宣称通用加速。

四臂 complete-process 时间合计 7941.656 s；外层 launch-to-exit 收据为 7944.206795 s，包含启动、四臂、离线审计及收尾。`run_completion` 记 4/4、无失败尝试或未运行臂；其内层 7943.816447 s 排除 preflight，与外层定义不同。建模、读模、求解、prelaunch 和 audit 时间均为嵌套分解，不另加到外层。D6 子进程正常返回一个全局截止状态，并非进程监督失败。预注册的严重信号须同时超过 1.5 倍且晚于 30 s；D6 只有后一条件，故未触发，并应完整保留其认证丧失信号。F2 有利与 D6 删失相反，支持继续既定 G4 有限筛选，不支持总体性能、优于 P-GRB 或 LP-G 晋升结论；R87 P-GRB 仅历史非配对资料。
