# A2 固定路线整数数量 oracle：静态原型

状态：**仅实现与静态审查，尚未执行任何脚本、测试、py_compile、真实 endpoint 或主求解器构建**。新原型为 [round88_quantity_flow.py](E:/codes/ExactEBRP/scripts/round88_quantity_flow.py)，独立枚举微测为 [round88_quantity_flow_test.py](E:/codes/ExactEBRP/tests/round88_quantity_flow_test.py)。遵照已审 [网络提案](E:/codes/ExactEBRP/results/unified_exact_round88/a2_network_quantity_proposal.md) 和 [数学审查](E:/codes/ExactEBRP/results/unified_exact_round88/a2_network_quantity_independent_review.md)，不改 ENS-C/A1/C++、不接历史 endpoint。

原型输入逐车固定访问顺序与有向旅行矩阵，逐站含整数初存、容量、正目标和权重。空路线旅行定义为零；正式接入仍须以原 verifier 对实际空车路线复核。完整模板旅行严格要求不超过原 T；当取放时间和为正时，逐车预算为精确有理 floor 后与该车总初存取最小；和为零仍要求模板旅行合格，预算为总初存。当前已验证解还须处于这个**名义**网络域：库存界、未访问站保持原存、每车所有负载前缀、gross pickup 预算、当前访问站非零操作全部核对。原 Evaluator 固定的 `1e−7` 物理容差只用于删零站后物理门槛；一个仅凭容差可行但超出名义预算的当前解返回 `domain_rejected_current_budget`，不扩大预算。

网络有 `s→v_k` 共用取车预算、`v_k→visit_i` 取量、`visit_i→t` 放量、相邻访问负载、末站载货返库和 `t→s` 闭合弧；空路线、异构车 Q、平行残量弧均有定义。梯度用所有站（含未访问站）的精确 Fraction `S/H/P`，相等比率和目标处取符号 0；`S=0` 确定返回 `no_gradient_at_zero`，不称邻域穷尽。取弧成本 `−g_i`、放弧 `+g_i`，以分母最小公倍数扩成整数成本。零流起点上确定性 Bellman–Ford 找负残量环，按整数瓶颈增广直至无负环；没有时间、轮数或 Work 配额。返回全部原弧整数流、容量与成本以及节点势；测试从返回弧**重新**构造正容量残量图，核整数守恒、原容量、目标和每弧非负 reduced cost。相同站正取放以 `min(p,d)` 取消，库存、前缀与线性成本不变。

原点到线性最优提案按库存差的 gcd 化为 primitive 整数方向；gcd 为零返回 `no_direction`。初版完整枚举数学有限域 `t=0,…,gcd`，每点核名义网络域、删零站后的实际有向旅行、原服务/载货返库时间及固定 `1e−7` 门槛，再调用**必需**的外部原问题验证回调。只取回调确认的严格原目标 `F` 下降；同值保留先到的最小 `t`，未改善返回 `no_verified_improvement`，它只描述这条梯度线。非 metric 输入可能令删站旅行增长，候选会被实际物理复核拒绝，不能把网络可行冒充原路线可行。负环证书只证明固定模板网络的**线性**子问题最优，不证明原 `F`、完整 BRP 或正式 ENS 提速。

待可用计算槽位并经独立静态审查后，才运行纯标准库微测。测试设计含已审三站 40 态联合改量见证、目标 tie 失败见证、96 个两站/空路/双车/预算/异构成本交叉（每个独立穷举净操作和检证书）、独立平行弧、同站取放取消、异构 Q 及载货返库、未访问站仍进全局目标、非 metric 删除反例、名义预算与 `T+1e−7` 边界、零服务时间、`S=0`、gcd 0 和整段内点获选。静态设计不是已通过测试或真实性能证据。
