# R95 完整两站块：独立源码静审

**修订后源字节静审 PASS，可由 root 决定隔离 build/G1；尚无编译或原 C++ 运行证据。** 审查对象 SHA-256：header `20150387b81db8287d44a959e9716274dff2f18586fd0014398b5bf200470573`，实现 `279eaf94fb769aab8cb89472ee3c698a25eb551f521a715c9af2a7cd859de5bb`，独立 diagnostic `300c1359a845f92f6e28966b808042ff01a315f1cd91ffe913a8611061a4cc8a`，C++ tests `080a4cbd928b7bc957d8888790e819c4c5814d81924df0e274792676e405850d`，CMake `aa85e10cc3738c8e44f1d99a3aa174ca542515d765ace9ed49262d933bfc1b27`。CMake 只增孤立目标，未接生产求解入口；作者旧 handoff 须以这两个新哈希更新。

原始见证先经结构、尺寸、有限输入及 Evaluator `int` 累加/库存域守卫，再调用原 `verifySolution`。每对已服务站读取固定原路线的前缀载量，按 10/01/11 交集构造 band；`inventoryInterval` 对每个 `u` 用库存界与 10/01/11 band 得到精确 `v` 区间，排除的仅是载量不可能点与不变原点。固定车主、同车先后顺序、跨车（无 11 组）和删零节点时，`q'_i=q_i−δ_i` 给出的前缀恒等式与源码符号一致；删零仅移除重复载量前缀。所有保留点均构造有符号操作/存活路线，先检查 Evaluator 整数域，再由原 Evaluator 检原目标、库存、实际距离、处理和返仓时间；整数域外直接置验证失败并中止，未伪报穷尽。矩形、band、每个 `u` 区间、载量拒点和 Evaluator 点数有分层账本；计数加法设溢出保护。

每点接受使用重算 binary64 原 `F_old−F_new>1e−12`，全扫描取最低 F 和 `(a,b,u,v)` 字典序定序。扫描内所有截止出口返回空选择；完整扫描后及正式接受前再查截止，故已发现但未完成扫描的 best 不会提交。接受前重新物理验证且核相同目标；截止/整数域/非有限原目标/复验故障不设 exhausted。第一次静审后作者发现有限输入参数仍可使候选目标溢出；修订源码对 `!original_objective_recomputed` 先记点 `nonfinite_original_F`，设 `verification_failed` 并中止，不会继续到假穷尽。新测试以有限 `DBL_MAX` 权重、`lambda=2` 构造基线 F=0、首个载量可行改量 F=∞ 的具体触发。有限状态下完整扫描的严格数值下降成立，但“穷尽”仅限该固定已服务两站邻域和 1e−12 门槛。诊断无 R73/R75/R83 调用、无 solver 或实例开关。

作者 G1 测试源码直接重建每个小矩形候选载量，与实际扫描集合逐点比较，覆盖同车正/逆序、跨车、删零、改号与非度量时长；强微例两版核实际 R76/R83/R93 停点而完整块选 `(2,4)`。另设 `S=0`、异目标/权重、返仓处理、`nextafter(T+1e−7)`、域溢出和发现 best 后截止。初审时发现临界测试把 pickup 单位按含返仓卸车计算却令 drop 时间为零；作者已将临界 fixture 的 pickup 与 drop 均设为 `requested/8`：原路线两个 pickup 加返仓两单位耗 `requested/2`，待测候选四 pickup 加返仓四单位恰耗 `requested`，三种 nextafter 方向才有预期意义。最终源码字节已包含修复；测试是否实际通过仍待 G1。

Diagnostic 先执行同一受守卫的原见证验证，生成 `bands/intervals/points/acceptances/final_witness/summary` 收据；`summary.wall_seconds` 是写自身前采样，完整成本须以后续外层 launch-to-exit 收据为准。部分截止、失败和原 `F` 收据须按独立 harness 另核。独立有理 oracle 与固定 G2 身份预注册见 [数学与预注册审查](math_oracle_and_prereg_review.md)；二者不替代原 C++ binary64 G1，也不准入真实 D6/E8/S12 或正式算法接线。
