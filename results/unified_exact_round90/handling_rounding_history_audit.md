# 逐车处理时间取整：有限历史差异审计（仅源码/既存报告）

**结论。** `∑_i p_ki≤⌊T/(t_pick+t_drop)⌋` 的数学预算早已在仓库使用，不能称新发现；本轮限定的源码与历史报告中，尚未找到它作为两条逐车静态行直接写进当前 ENS-C 的 VD-P canonical compact LP 或对此精确两行的同源测试。当前模型写的是逐车未取整时长 `travel_k+c∑p_ki≤T`（`src/CplexBaseline.cpp:1800–1808`），另有未取整全车队行 `c∑_{k,i}p_ki≤MT`（`:2168–2185`）。因此已准备的唯一五站 G2 是**架构/LP 缺口核查**，不是新数学、新 B3 cut 或性能预告。

| 已有机制 | 源码与已测范围 | 与拟诊断两行的关系 |
| --- | --- | --- |
| 早期资源下界、route-mask | `src/Bounds.cpp:451–540,803–813` 已求 `∑_k⌊T/c⌋` 并用于资源/库存松弛；`:1640–1645` 在该**另一个**松弛加总 pickup 上界。`:1077–1119,2204–2227` 按完整 route mask 的旅行下界求 `⌊(T−cycle_lb)/c⌋`，用 mask 选择变量约束车辆 pickup。`docs/attempt_log.md:1232–1292` 记录 Round 7/8 工程与 V12 测量。 | 已直接试过整数取整预算，甚至带 mask 旅行下界；但在 route-mask/BPC 结构，非 ENS-C 原 compact LP 的两条 `p_k_i` 行。`docs/attempt_log.md:2472–2484` 明说这些有效的 mask operation-budget 行曾使关键松弛 MIP 更难、给出较弱的时限界，后用开/关两松弛的组合保留较强合法界；不能把这段负面速度结果移植为“两行必慢”，也不能无视它。 |
| R63 时间资源 | `src/Round63TimeResource.cpp:83–160,173–222` 的 `W=N`/singleton `simple` 行、全子集显式流/闭包、MIPNODE user cuts 与根行，使用连续 `c p` 及有向最短路，**未对 pickup 总量取整数 floor**；`results/gf_cumulative_time_resource_round63/mathematics.md` 明言无 floor-rounded integer capacities。`final_report.md` 记录 D4 root LP 0.09395→simple 0.25688、explicit 0.26294，但 D4 完整 MIP explicit/root 较 OFF 慢 51.4%/34.7%；动态 cut D7 gap 变差、D4 无净增益，C2 root 与 root-dry 的生命周期效应另分。 | R63 不是拟议的两条静态整数取整行：其 simple 行也有 fractional activation 和累计旅行/服务，full closure 与 callback 成本远大于两行。已有正 LP/负全程的混合教训不能重命名为本 G2 的实测。 |
| R54/R55 与 R62 | R54 `inventory_route_cut_validity_proof.md` 的 IR-IN/OUT 是净库存与边界弧上的 `Q_k`，R54 `final_report.md` 记 IR1 固定区间根界常改善、却在 D1/D13 丢证书并未晋级。R55 `final_report.md` 的 VD-P 是库存状态乘积表示；pair/triple support 在其 162 次诊断无活动或单独根界贡献，penalty cover 因先决门槛未进入实测。R62 `src/Round62Thresholds.cpp:88–110` 已用 `⌊(T−往返最短路)/c⌋` 限定**单站事件数量**，`final_report.md` 的投影收益/回退属于事件冲突架构。 | 都使用过处理/旅行/整数数量，但没有证明五站两条逐车 pickup 行已在 ENS-C LP 隐含；R54 的 `Q_k` 边界流不能误写成整条路线累计 pickup≤Q。 |

**可证的均匀旅行加强。** 设 `c=t_pick+t_drop>0`，所有有向弧旅行非负且有已验证的有向最短路下界 `d̲`；固定车辆 `k` 的任一物理正取车路线必访问某站 `i`，故路线旅行至少 `d̲(0,i)+d̲(i,0)`。取全站的保守 `ℓ_min=min_i[d̲(0,i)+d̲(i,0)]≥0`（若有已证明的可服务站集合，也可只在该集合取 min），于是

`c·P_k+ℓ_min≤T`，整数 `P_k=∑_i p_ki` 给 `P_k≤B=max(0,⌊(T−ℓ_min)/c⌋)`。若 `T<ℓ_min`，不应把负数 B 强加给空车；正取车路线不可能存在，故仅得 `P_k=0`。`src/Evaluator.cpp:106–116` 计入返仓余车卸载，保证 `c·P_k` 即使带货返仓仍成立；额外访问/送车只增加非负旅行或已纳入的处理成本，不能削弱下界。这个证明从未用 `P_k≤Q_k`，Q 只约束每个载荷前缀。若 `c=0`、距离无有限有效下界或数值向上误取 ℓ/B，须停用相应强化或作保守定向舍入，不能照抄公式。

若希望按车辆 activation 透视，当前 compact 源码 `CplexBaseline.cpp:1493–1505` 有整数 depot 出度 `a_k=∑_{j≥1}x_{k,0,j}∈{0,1}`、返回平衡和上界 1。在**完整原物理路线**上，`a_k=0` 意味着无服务、`P_k=0`；正服务意味着 `a_k=1`，所以 `P_k≤B a_k` 也整数有效，LP 中可能强于无条件行。空路线、零取放或零服务访问均不得被误认为须付 `ℓ_min`；若模型允许与 depot 脱离的整数子巡回，须先由既有连通/载荷合同排除后才把透视行宣称对模型有效。选全站 `ℓ_min` 可以允许任何额外访问和有向非 metric 输入的最短路径中转；不能用直接边之和当任意非 metric 路径下界。五站诊断所有旅行 0，故 `ℓ_min=0`，自然加强退化为先前两行，不增设第四臂。

**证据边界。** 没有对全 Git 历史或文献做穷举；结论仅依据上述当前源码和既存 R54/R55/R62/R63、Round 7/8 报告。更早或未归档的相同 compact 两行试验仍可能存在，不能从本审计证明“从未做过”。当前不修改 [五站导出草案](../../tests/round91_handling_rounding_probe.cpp) 或 [G2 交接](b3_probe_build_handoff.md)，不新增算法/输入/参数矩阵，也未构建或运行诊断。
