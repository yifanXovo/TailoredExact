# R95 数学 oracle 与固定 G2 预注册：独立审查

**纯数学 G1 oracle PASS；原 C++ Evaluator 与 R95 实现尚待独审和隔离 G1。** 独立脚本 [round95_full_block_oracle.py](../../tests/round95_full_block_oracle.py) SHA-256 `631889e8c31bb67c0209b09d61dcd5e41c56f61116f7f5dab7e5c2c75bd6b1f8`，不用生产模块、solver 或浮点目标。它用 `Fraction` 为每个小矩形点重新构造带符号操作与删零路线，逐车直接模拟载量和时长；另从原状态前缀独立形成 10/01/11 band 及逐 `δ_a` 的 `δ_b` 区间。九类 fixture 共 **310 个非原矩形点**，直接重建得到 99 个载量可行点；每一点的直接载量判断、band 判断、区间判断完全相等。首次且唯一执行 exit 0，外层 launch-to-exit 0.3142691 秒；stdout SHA `f2e0a979c12552b590cf5609c0134252c6bc214185e9fac1790fac1a1adf97ee`，收据与原 stdout/stderr 保留为 `rational_oracle_attempt_001.*`。脚本内部打印前采样 0.0132026 秒，不是完整进程成本。

强微例在零时长与正度量/处理时长两个版本均得原 `F:9/40→3/20`，最佳点 `(Y'_1,Y'_2)=(2,4)`，原 R75 两条坐标轴与等量反对角、R93 同向对角均无严格改善，空路线 `29/120` 更差。其余 fixture 覆盖 `S=0→G=0`、不同目标与权重、同车夹杂未改站、反向访问顺序、跨车车主、原操作 drop 与变号、零操作删除、返仓满载、非度量删点使路程增加，以及有理数 `T+1e−7` 正好可行和超出 `1e−8` 不可行。oracle 的有理边界不是原 C++ binary64 `nextafter` 证据，后者仍属实现 G1。

**G2 固定身份预注册 PASS，未授权运行。** [full_block_diagnostic_preregistration.json](full_block_diagnostic_preregistration.json) SHA `2773c0a159c90e7f69343a2babfa827ce061dfc26a42f2948395413fbfe70a12` 固定复制 R93 原 manifest SHA `d853322f29f91b12027f3d82229bc94afae654e90b4a63f6158b4042419106bb` 的三个完整 case 对象；我独立逐字比较 D6/E8/S12 的顺序、场景、源、参数、输入/见证路径与 SHA、历史标记，并重新哈希实际六个小输入/见证文件。每例外层上限仍 120 秒，总上限 360 秒，一例一次；未选择新见证或按 R93 结果调整上限。R95 新文仅把机制改为完整 `(a,b,u,v)` 块及精确载量 band，并明确原 Evaluator、逐点账本、截止/错误 unknown、原 R76/R83 不插入隔离下降。driver 与 binary SHA 留空，必须由 root 在源码/G1 后另立 gate 绑定；本预注册不允许运行。

前缀 band 必要充分性、删零载量等价、整数域与数值停止范围已在 [R95 数学预审](../unified_exact_round94/r95_math_preproposal_review.md)给出。尚未扫描真实 D6/E8/S12 目标或运行 native；R94 正式批次保持独立。
