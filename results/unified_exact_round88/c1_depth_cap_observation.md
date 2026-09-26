# R87 正式十臂的 C1 深度上限事实审计

只读检查 R87 保留的 D6、D7、U6、F2、F5 双臂共十次正式运行；P-GRB 不使用 ENS 的 paper-tree 深度，表中记“不适用”。**未纳入 run11 F6 ENS-C**，它不属于这十次正式数据。D6/D7/F2 正常返回，有完整的最终 `paper_leaf_ledger.csv`、LP/分裂账本与 `result.json`。U6/F5 遭 hard kill，相关 CSV 仅剩表头、无最终 paper-leaf/JSON；另有独立留存的 `native.log`、小型 LP Gurobi 日志和约 0.3–0.4 MB 的终端 MIP 日志。未扫描大型 native journal、未重放求解或界审计。逐文件大小、SHA256、路径及提取原始行在 `c1_depth_cap_provenance.json`，十行简表在 `c1_depth_cap_observation.csv`。

| ENS run | 持久化证据中的 LP 深度 | 最深已采纳 paper-tree 叶 | 可复核 split 数 | 决策/中断事实 | 运行终止 |
| --- | ---: | ---: | ---: | --- | --- |
| 02 D6 | 2（L0.0 的两个候选子 LP） | 1 | 1 | 根节点因右子不可行而 split；L0.0 后续无严格子界改进 | normal，`optimal` |
| 03 D7 | 1（根的两个候选子 LP） | 0 | 0 | `adaptive_mass_no_strict_child_improvement` | normal，原生时间上限 |
| 06 U6 | **至少 2**：`L0.0.0`、`L0.0.1` Gurobi LP 均最优 | 无最终账本，未知 | 未完整落盘，未知 | `L0.1` LP 不可行；随后 `L0.0` 终端 MIP 长时间运行 | 全程 hard stop，无最终 JSON |
| 07 F2 | 1（根的两个候选子 LP） | 0 | 0 | 先 `score_below_tau_native_target`，目标后 `no_strict_child_improvement` | normal，`optimal` |
| 10 F5 | **至少 2**：`L0.0.0`、`L0.0.1` Gurobi LP 均最优 | 无最终账本，未知 | 未完整落盘，未知 | `L0.1` LP 不可行；随后 `L0.0` 终端 MIP 长时间运行 | 全程 hard stop，无最终 JSON |

缺失 CSV 行不是执行未发生的证据。与 R87 冻结源提交逐字节无差异的 `src/PaperExternalGiniTree.cpp` 在约第 2428 行打开流、第 2793–2804 行刷新表头，第 3598–3652 行于 LP 调用返回后才写 LP 账本行；`paper_leaf_ledger.csv` 到约第 8397 行的最终序列化才创建，其他关键账本在约第 8807–8816 行统一刷新。U6/F5 的小型 `native.log` 与独立 Gurobi LP 日志却明确显示 `L0`、`L0.0`、`L0.1`、`L0.0.0`、`L0.0.1` 模型求解，后两个都是 depth 2；各自 `L0.0_terminal_mip.gurobi.log` 末尾仍有约 86,000 秒的 MIP 进展。因此先前“只到根 LP、没有 split”的推断错误，已从简表移除。U6/F5 的**完整最大深度和采纳树状态无法从丢失的最终账本恢复**；这些正面日志只给出至少 depth 2，不构成完整轨迹。

`result.json` 存在的 D6、D7、F2 均记录配置的 `external_gini_tree_contract_adaptive_max_depth=8`。它们的 `external_gini_tree_max_observed_depth=0` 不是“最深曾求解候选 LP”的字段：D6 的完整 LP 账本明确有 depth 2 候选，最终 paper-leaf 账本有 depth 1 已采纳叶。因此本审计不以该汇总字段替代 LP 和叶证据。U6/F5 没有最终配置字段；其原始命令与冻结二进制仍可追溯，但本审计不凭缺失的最终 JSON 补写配置结果。

**观察结论：**D6/D7/F2 的完整最终账本均未触及 depth 8，也未记录因该上限拒绝分裂。U6/F5 的持久化原生日志至少到 depth 2，未观察到 depth 8；但 hard kill 使最终决策/叶账本丢失，不能严格排除未持久化的更深动作或完整判定上限影响。现有证据没有**正面证明** R87 的 depth 8 限制截断了任何正式运行，也不能据此断言五臂都完全未受影响。旧 R87 的证书/删失验收依靠另行审计的物理见证和界证据，不因本次账本缺口而被推翻。今后新候选可考虑对关键 LP/分裂/叶状态逐事件 flush，当前冻结源码、runner 和二进制不改；静态历史观察不能证明未来移除上限必然更快或结果等价。
