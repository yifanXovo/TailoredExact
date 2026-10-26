# 模式、生产身份与实际干预

所有新增模式默认关闭。研究模式使用既有 `--round98-state-service` 入口；
开关名沿用不代表继承旧实验结果。主 benchmark P-GRB 保持原 compact，
ENS-C 保持原 24+1 启动、闭包、VD-P/F0、AM0.08、静态 50000 行及 R68 Start。

| 模式 | 参数值 | A/B 联结 | 方向 m | p/d 声明 | 新方向状态等式 |
|---|---|---|---|---|---|
| ENS-C | off | 无 | B | I | 无 |
| R1 | aggregate | 有 | B，原方向行 | I | 无 |
| Q-I | q-integer | 有 | 消元，原系数投影 | I | 无 |
| M-B | m-binary | 有 | B，原方向行 | C | 无 |
| R2 | projected | 有 | 消元，原系数投影 | C | 无 |
| M-BL | m-binary-linked | 有 | B，原方向行 | C | 每站一行 |

x/z/s、Y/load 的类型、目标、物理边界和其他原行均继承原合同。
R1/M-B、Q-I/R2 各自严格只改变 p/d 类型；消元对照同时改变列和方向行，
不能称为纯方向二进制类型干预。M-BL 保留 M-B 全部列、类型和原行，增加
`sum_k m_ki = sum_{y<b_i} s_iy`，属于新的松弛联结。

`Round98StateService.hpp` 将投影、数量类型和新增联结分开；
`CplexBaseline.cpp` 在真实 writer 中使用这些独立 traits；
`main.cpp` 验证 CLI 并为 Q-I、M-B、M-BL 给出独立 Research99 身份。
原 R1/R2/R3 身份不改写，`Instance.hpp` 仍以 off 为默认值。

canonical LP 的完整有序字节包括变量类型，模式通过实际矩阵 SHA 进入缓存身份。
原 native adapter 捕获真实 VType，LP 后恢复捕获数组；这是继承的正确行为，
本轮补实际模型和全部 Start 列的核验，不将它称为新实现贡献。
所有 p/d 仍按原物理整数合同独立检查，包含未访问列。

线程数 1、Seed 0、Presolve Auto，原 FeasibilityTol 1e-6、IntFeasTol 1e-5、
OptimalityTol 1e-6 和零 MIP gap；R97 feedback、R96 重排、LP-G、H-ACT、
动态 cuts 关闭。没有 branching priority 或原生参数网格。
