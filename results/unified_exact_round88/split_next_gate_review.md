# Round88 下一项区间工程候选：单独试 LP-G 分点（只读准备）

**建议只保留一个待审消融：**在 ENS-C 完整父 LP 最优且 `G` 值可用时，以该 LP 点的 `G` 作二分点；若不可用或不是严格可表示的内部点，退回原中点。仍用完整左右子 LP、原 AM `ημ≥0.08`/零严格增益/子域不可行门槛、父叶精确闭合、原子覆盖替换、depth 8、最小宽 `10⁻⁴` 与同一全程截止。独立研究身份，绝不与 C1 删除深度上限合并。本报告不准入实现或性能试验。

## 为何暂不选 C3 零增益快捷检查

数学上，完整父 LP **最优**点若逐列、逐行、目标、cutoff 与 epoch 都属于一个子 LP，且该子模型确为父松弛子集，则该子 LP 最优值等于父 LP；另一子域至少有父 LP 界，故分裂后的即时最小 LP 界不严格提升（[split_mathematics.md](split_mathematics.md)、[critical band](split_critical_band_proposal.md)）。这不能删除另一个子域，不能把单点行违反推成子域最优界，也不能替代子 LP 不可行证明。

当前 ENS-C 默认 `round49_k1_am_rc=off`（[Instance.hpp:529](../../include/Instance.hpp)）；完整父向量、基和 RC 的保留只在 `round49_active` 时请求（[PaperExternalGiniTree.cpp:1731](../../src/PaperExternalGiniTree.cpp), :3597, :6239；[GurobiBaseline.cpp:2912–2955](../../src/GurobiBaseline.cpp)）。通常仅保存标量 `G`（PaperExternalGiniTree.cpp:3634–3635；GurobiBaseline.cpp:3024–3071）。每个子叶另写 canonical LP（PaperExternalGiniTree.cpp:6193–6240），由叶区间和当前 verified UB 决定模型（:3502–3533）；`CplexBaseline.cpp:460–493,815–850,2836–2875` 表明区间可改变库存支持/列数、`G` 界、状态透视行，其余静态行也按当前域重建。故并非可凭 `G` 或聚合产品残差作廉价嵌套检查。要提前证明一个子模型可容纳完整父点，需新增全向量捕获、跨不同列集的投影映射、子 LP 全行/界/目标验证与数值余量；至少已付一侧完整构模和逐行扫描成本，尚无证据其比一次子 LP Optimize 便宜。若只保留语义检查而不能证成，应原样求两侧 LP。R87 D7 根叶及 D6 `L0.0` 记有 `adaptive_mass_no_strict_child_improvement`，F2 根叶先 `score_below_tau_native_target` 后也有零严格增益（[深度账本审计](c1_depth_cap_observation.md)）；这些是潜在节省机会，**不是**父点对子模型可行的历史证书。

## 单一 LP-G 消融的代码落点与可检验理由

原生后端在完整 LP 最优时已读全列 `X` 并导出有限的 `G`（[GurobiBaseline.cpp:3024–3071](../../src/GurobiBaseline.cpp)），controller 无需新增全向量基础设施即可取 `selected_state.round43_lp_g`。现行 split 在 [PaperExternalGiniTree.cpp:6124–6159](../../src/PaperExternalGiniTree.cpp) 用 `splitLegacyFrontierInterval` 产生中点左右域，两个子 LP 都完整求解后才调 AM（:6193–6329, :6338–6346），覆盖与深度门槛分别在 :6137–6143 和 [GiniFrontierGeometry.cpp:362–369](../../src/GiniFrontierGeometry.cpp)。变体只应替换此 first-class K1 分点来源和相应 split 点账本/合同校验（PaperExternalGiniTree.cpp:331–344,589–601）；保持其它 Round43/旧策略路径原样。计算 `p=G_LP` 必须核 `a<p<b`、有限且两子域真实共享同一浮点端点；失败即原中点，并执行严格内部与覆盖检查。不可因 `G` 接近边界而悄悄加入新的平衡阈值；较窄子域到深度 8 或宽度门槛后走原末端 MIP。缓存子叶若复用，必须核其区间/模型 SHA 与新点一致，否则重新生成；新 incumbent epoch 的旧 LP `G` 不可复用（PaperExternalGiniTree.cpp:3456–3483）。

同源已导出的 R87 根 LP 离线记录提供一个**可区分**的固定观察：D7 `L0` 域约 `[0,0.2914489735]`，原点 `G≈0.0322222366`，原中点约 `0.1457244868`；F2 `L0` 域约 `[0,0.8853483009]`，原点 `G≈0.1174378778`，原中点约 `0.4426741505`（[D7 manifest](ot_qualification_d7_audit_v4/manifest.json)、[D7 固定点](ot_d7_diagnostic_001/diagnostic/result.json)、[F2 manifest](ot_qualification_f2_l0_audit/manifest.json)、[F2 固定点](ot_f2_l0_diagnostic_001/diagnostic/result.json)）。两者的历史 AM 决策均未立即因严格子界提升而拆根；这只说明候选切点与现行中点确实不同，**不能**预言新子 LP 界、证明时间或速度优势。D6 根一侧不可行也说明分点可能改变可行域形状，绝不可从旧子 LP 界外推新子 LP 界。

数学边界：已审 mass-weighted 引理只证明 `p=G` 最大化**该父点**两侧产品行的较小原始违反量；产品若精确则两侧为零，即使违反正也可能有另一个同目标最优 LP 点。因此新点不是目标下界增益保证。验收时需看真实子 LP 最优状态、AM 决策、最终完整覆盖/原证书及总建模/LP/MIP/进程成本；截止而未闭合写 unknown。此候选仅在 native-B1 后由 root 单独决定，未运行任何代码或求解。
