# Round90 LP-G split 资格 001 独立收据审查

**结论：限定的零 Optimize 资格通过，无身份或收据阻断；这只准许把纯函数与非法 CLI 守门记为已执行，不证明真实 controller 的父 LP、requeue、epoch 或性能。** 我仅只读审查 `qualification_001`、签发的 lease 和 23 份证据文件；未执行测试、模型、构建、求解或 Git 操作。

`qualification_001_lease.json` 的 SHA-256 为 `e817a278cba9de584f50404c117e2782edcab525d398114dbe92c64d2f86afde`。前后记录的七份源码和五份二进制哈希均逐项吻合 lease，源码 commit 为 `b1f53bdaa2bfd15bce8232cc872b8815d7f65d9a`。`artifact_index.json` SHA-256 为 `b1f624d9040f00db31edb9bdae4696c320f335873004db26210608c30c52bef8`；我重新核对其 23 个成员均存在，字节数与 SHA-256 全部相符。报告自身 SHA-256 为 `0da58e543163dc3bfb5a685272ed320fc07f02e91401beca2a04c7a68db5e576`。

六条命令与 lease 一致且没有重试：`Round90LpGSplitTests`、`GlobalGiniTreeTests`、`Round47AdaptiveMassTests` 分别 exit 0，原始 stdout 报 3 groups、9 groups、28 checks，stderr 均为空。后三条以同一经前后核验不存在的 input sentinel 调用 `ExactEBRP.exe`：非 ENS 的 `custom` preset、ENS-C 加 A1、ENS-C 加 B1；均 exit 1，原始 stderr 首行分别给出预定的 ENS-C 限定或 A1/B1 排斥错误，未走到输入读取。各收据均记录 120 秒外层上限、未超时和正确 executable/argv；三条纯测试不含模型，三条 CLI 在参数守门返回，所以此批零 Optimize 的口径合理。后检无残留重型进程，sentinel 仍不存在。

六条启动至退出耗时之和为 **1.1513118 秒**；包住六条命令的 batch wall 为 **1.2274166 秒**，差 **0.0761048 秒**，不能相加成额外成本。原 `batch_summary.json` 的 `command_wall_seconds_sum=null` 是元数据缺项；后置 `batch_cost_reconciliation.json` 从六张原收据求和，保留原始 summary 而未重跑。前检与后检时间戳之间约 130.5 秒，但其中包括批次前后未分段记录的准备、检查或等待；不能把 1.2274166 秒称为从前检至后检的完整资格墙钟，也不能把 130.5 秒当成算法或求解耗时。此成本边界不影响本批通过结论。

下一道实际集成门应读取同一构建上的候选/默认成对收据，逐项核父 LP 点、实际切点、两子 LP、AM、原子替换、覆盖和物理证书；未观察到的 same-epoch requeue 或 epoch 失效路径如实记未观察，不从本纯资格推断已覆盖。
