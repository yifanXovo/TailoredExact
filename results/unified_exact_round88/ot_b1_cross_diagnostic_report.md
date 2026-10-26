# Round 88 D7 同组 B1 行来源交叉诊断

状态：**一次预注册诊断完成，六臂均最优**。准入为 `ot_b1_cross_admission.json`；仅执行 [v4 合同](E:/codes/ExactEBRP/results/unified_exact_round88/ot_b1_cross_contract.md)中的一次 `supervise` 命令。外层监督墙钟 **96.0614/120 秒**、退出码 0，前后 manifest 与结果所记 SHA256 均为 `d1270dc11f1ed99c011028f0287f70b5bcccbbf4c56c6a8f602787f0ad311755`；六臂 Gurobi 状态均为 2（OPTIMAL），无超时、部分结果或数值无效标记。原始证据见 [supervision.json](E:/codes/ExactEBRP/results/unified_exact_round88/ot_b1_cross_diagnostic_001/supervision.json) 与 [result.json](E:/codes/ExactEBRP/results/unified_exact_round88/ot_b1_cross_diagnostic_001/diagnostic/result.json)，六份独立求解日志同目录保留。

| 固定原 LP | B1 行集 | 新行 | 最优目标 | 该臂边际墙钟 s | 求解 Work |
| --- | --- | ---: | ---: | ---: | ---: |
| parent L0 | R_parent | 1184 | 0.1882996742 | 7.5077 | 24.5665 |
| parent L0 | R_child | 1211 | 0.1906726694 | 6.5666 | 20.8067 |
| parent L0 | union | 2343 | 0.1917810802 | 27.8202 | 91.7762 |
| child L0.0 | R_parent | 1184 | 0.1893702255 | 5.3597 | 16.9191 |
| child L0.0 | R_child | 1211 | 0.1937647972 | 10.5538 | 34.7687 |
| child L0.0 | union | 2343 | 0.1943018267 | 10.1648 | 32.2643 |

两份原 LP 的历史 base 目标分别为 0.1859374766118822 和 0.18593747661188215，仅作参照，**本次未重新求 base，也未从成本扣除**。在同一 parent LP 内，使用 child 点所选 B1 行比 parent 点行高 0.002372995；在同一 child LP 内高 0.004394572。两臂的并集继续提高下界；这些是给定固定 LP 的行来源差异。B1 与 G 局部区间无关，且两份 LP 的输入、库存支持和目标相同；但本审计没有证明完整 parent/child formulation 除 G 区间外一致或凸集嵌套，所以**不能把跨 LP 的增量归因于缩窄 G**。

运行进程内共享重新验证冻结 raw 与行库、读入/审计/松弛两份 LP 计 **27.9068 秒**，其中 parent/child LP read 为 0.2354/0.2510 秒、relax 为 0.0048/0.0047 秒。六臂边际墙钟已在表中，复制/加行/Optimize 分项以及各臂约束数、非零数和内存见原始 `result.json`；外层全进程 96.0614 秒才是此次六臂共同支付的总墙钟。准备行库的独立内部成本至写完行为 25.2090 秒，外层 prepare 命令为 25.4755 秒，均未混入六臂进程。峰值工作集记录 356,376,576 字节。

只做了一轮来自两处冻结 LP 点的可靠 B1 行归因；未调 G 域、cutoff、变量支持、目标或求解容差，未使用 B2/aggregate 行，也未运行正式 ENS 方法。结果显示同组 B1 行的生成点选择本身会改变下界和成本；六臂单次诊断不能证明正式算法的净速度优势。结束后进程排查无残留 Gurobi/Python/build/compression，已释放独占计算槽位。
