# Round100 起点与范围

| 项目 | 已核对的事实及本轮处理 |
|---|---|
| 基线 | 本地/远端 PR161 head a11fbcdc9bbea4f5ee716c6e49df4e0fb4755dcd；R98 父 10d777d8ecf8d2aaa181f0fbe7445c266a968ef2。新分支 stacked 于 R99。 |
| 历史实测身份 | R99 v1 2458a3f7845d6a6cf6006361268aa737274ea53b；v2 4f88a8c040047597dcfe9baa4a95a087cf925a0f；交付 head 不是全部旧实测源。 |
| 默认与候选 | ENS-C 保护默认；M-B 独立研究候选、未晋升。R99 已拆开方向投影/数量类型并否定 M-BL 的统一采用，不重开网格。 |
| P 真实缺陷 | R98-C2 ENS 1800s U=.216793065 弱于 P .198302849；R99-N2 ENS .199516075 弱于 P .177364361。 |
| M-B 预算证据 | C2 1800s U/L=.194634816/.190669184 优于 P；N3 正常重跑 3600s U/L=.255944620/.214436363 也改善 P/ENS；均未证。 |
| ENS 保护损失 | M-B F2/C1 更早找到后来认证的目标，但更晚认证；F5 3600s U=.373467149 弱于 ENS .329504107。不能统一归因启动/primal。 |
| 中断 | 原 N3 的中断、未知退出时刻与保守 3600s allowance 保持历史记录；完整重跑单列；本轮全新运行不拼接。 |
| 匹配基础消融 | R98/R99 当前 writer、变量表、manifest/结果没有无 A/B 且只改 p/d 声明的身份；M-B 有 A/B。R66 更大路线/载荷替换不满足匹配条件。新增 ENS-Q。 |
| 环境 | Win/GCC14.2 UCRT64、i7-12700KF；生产 Gurobi13.0.2 原 DLL；性能串行、Threads1 Seed0 PresolveAuto 原容差零 MIPGap。 |
| 工作区 | 无 AGENTS.md、起点无活动 solver；三处用户 tracked 修改及历史 untracked 文件保留，哈希见 baseline.json。 |
| 判定 | 数学/模型合格、候选采用资格、稳定最终快于 P 三者独立；双删失不推断认证时间。 |

已完整读取 R99 final_report、mathematical_algorithm、history_increment、root_final_review、
complete_results_final/runs 与 optimal_discovery、inner_results02/runs、candidate_freeze、
reproduce 与 RESUME，并针对性回读 R98 数学/实际变量和 R87 长尾/中断范围。
