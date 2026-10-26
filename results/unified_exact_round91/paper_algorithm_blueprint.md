# ENS-C 论文算法底稿（源码与现有证明绑定，未晋升）

本底稿描述当前默认 `research-round83-vds-equal-net-exchange`（以下 ENS-C）；Round90 `--round90-lp-g-split=true` 只是单因素消融。它不是最终性能结论，也不证明这些数学工具具有文献新颖性。本文的“精确”指完整原整数模型、覆盖和求解终态的设计；实际 Gurobi 浮点状态、行残差和证书仍按项目原数值门禁解释。源码位置以 2026-09-27 主目录为准；理论细节见 [R88 split mathematics](../unified_exact_round88/split_mathematics.md)、[critical band](../unified_exact_round88/split_critical_band_proposal.md) 与 [AM lemma](../unified_exact_round90/am_gap_contraction_note.md)。

## 原问题、目标和物理语义

设车站数为 (n)，最终整数库存 (Y_i\in[0,C_i])，正目标 (D_i)，权重 (w_i\ge0)，(r_i=Y_i/D_i)，(S=\sum_i r_i)，(H=\sum_{i<j}|r_i-r_j|)。原目标是

\[
F(Y)=G(Y)+\lambda P(Y),\qquad
G(Y)=\begin{cases}H/(nS),&S>0,\\0,&S=0,\end{cases}\qquad
P(Y)=\sum_i w_i|r_i-1|.
\]

非负库存使 (S=0\Rightarrow H=0)；零分母处明确令 (G=0)，不能把 LP 中的分式行拿去除零。`src/Result.cpp:109–127` 是原目标权威计算。`src/Evaluator.cpp:24–151` 独立核每车空载出发、仓库起讫、每站最多一访、一个站不能同时取送、每前缀载量在 ([0,Q_k])、最终站库存、旅行和服务时间；返库剩余载量按放车时间卸货，所以整车时长等于旅行 (+(c_p+c_d)\sum_i p_{ki})，允许该文件规定的 `1e-7` 时长数值余量。目标只评价最终库存，旅行决定可行性。必须区分这个原物理验证与 LP 模型的松弛可行。

## 当前默认完整流程

1. **统一身份、启动和上界。** `src/main.cpp:263–418` 的 R83 预设递归继承 R73/R71/R70、R68/R67 与 first-class K1 配置；R67 选 `round55-vd-p`，R70 设 24 个随机解码下降起点，R73 添一个先经物理验证的联合构造顺序。`src/main.cpp:8068–8150`、`src/HgaTgbcRunner.cpp:107–180` 是实际入口。`include/hga_tgbc/HybridGA.h:1309–1379` 对每个起点反复建立有限 guided 邻居、完整解码、严格改善则重启 pass，穷尽/经验证的零值/同一全局截止才停止；没有固定 pass 数，截止时不能称已穷尽。`src/main.cpp:8206–8222` 接着对最佳已验解运行 R83 等净量 block exchange 与 R76 严格物理 closure；`src/Round83BlockExchange.cpp:130–204` 只接受原 (F) 严降，或库存和 (F) 严格不变而路线时长势下降的中性移动。每个候选经 `verifySolution`，因此启动只给合法 (U)，不提供原问题下界。解码器的 top-8/top-6 限制复合邻域，不能写成穷尽所有路线/数量移动（[active count audit](../unified_exact_round88/active_count_parameter_audit.md)）。
2. **建立全局 (G) 覆盖并导出叶模型。** `src/main.cpp:12985–13012` 以经验证的 (U) 和 (G\le(n-1)/n) 建立全部可能改善该 (U) 的 (G) 区间；默认无额外用户 cap。`src/PaperK1AmSf.cpp:53–116` 设初始一个区间、first-class 外部 Gurobi 树与无分组件配额的 `round31-nonblocking-native-bound`。`src/PaperExternalGiniTree.cpp:1691,2960–3080,3499–3701` 为当前叶 ([a,b]) 和当前 incumbent epoch 写带 verified cutoff 的 canonical 原整数模型，并求其完整 LP 松弛；模型/LP SHA、域、epoch 与状态绑定。若 LP 不可行则该叶排除；有效 LP 最优值是该叶所表示区域的数值下界，不是可行上界。选择下一个开放叶按有效界（`PaperExternalGiniTree.cpp:4253–4375`）；全局原问题的下界论证还须计入已闭分支与 incumbent cutoff 排除区，不能仅取开放叶最小界。**完整子 LP 并非每次选叶都运行：**现行 C6 frontier 可先证明本叶暂不控制全局界而重排，或让原生 MIP 达到下一个严格 frontier 界目标再重排；仅允许 child lookahead 时才进入下述双子 LP（`:6080–6120`、`:3848–4155`）。这是数学界目标，不是内部秒数/Work 配额。
3. **松弛的关键结构。** `src/CplexBaseline.cpp:1495–1568,1740–1810` 保留车路弧、唯一访问/连通 F0、操作、载量及每车时长约束。`CplexBaseline.cpp:2100–2115` 写 (Y_i=b_i-\sum_kp_{ki}+\sum_kd_{ki})、(r_i=\alpha_iY_i)（导出的 `binary64` 系数 (alpha_i=\mathrm{fl}(1/D_i))）及 (e_i\ge|r_i-1|)；`:2190–2215` 写 (h_{ij}\ge\pm(r_i-r_j))。VD-P 的 `s_{iy}` 为 one-hot 库存状态，`q_{iy}` 是区间透视的 (G s_{iy})：`:835–875,2837–2885` 写 (\sum_y s_{iy}=1)、(Y_i=\sum_yys_{iy})、(\sum_yq_{iy}=G)、(z_i=\sum_yyq_{iy}) 和 ([a,b]) 透视行；`:2959–2963` 写 (n\sum_i z_i/D_i\ge\sum_{i<j}h_{ij})。`CplexBaseline.cpp:1004–1011,2973–2982` 的最小化目标及 incumbent 行分别是 (G+\lambda\sum_iw_ie_i) 与 (G+\lambda\sum_iw_ie_i\le\kappa=U-\epsilon)。当前 paper external 路径实际设置 (\epsilon=0)（`PaperExternalGiniTree.cpp:3559–3562`；`CplexBaseline.cpp:4348–4354`），不要将其它 interval oracle 的正 epsilon 混入。符号数学的整数状态下 (q_{iy}=Gs_{iy})，于是 (z_i=GY_i)；在 (S>0) 时分式行只给 (G\ge G_{true}=H/(nS))，故 (G) 是原 Gini 的上图变量。对真实 (G_{true}\in[a,b]) 的原整数解，取 (G=G_{true}) 可嵌入该叶并复现原目标；若 (G_{true}<a)，同一路线/库存可能只以 (G=a>G_{true}) 存在于该叶模型，绝不能说每个叶整数点都满足 (G=G_{true})。原约定 (S=0\Rightarrow G_{true}=0) 的解在含零的根区域取 (G=0) 嵌入。实际导出/求解的系数经 binary64 舍入，故此处是数学整数一致性及项目数值门禁下的一致性，不能当成逐位有理恒等或独立有理证书。该模型也不声称 LP 已是完整凸包。其余实际静态有效行与大小限制也属于模型，不能从这几行省略为“仅 McCormick”。
4. **允许 lookahead 后求完整子 LP 并作 AM 决定。** 默认可分条件是深度 (<8) 且宽度 (>10^{-4}+10^{-12})（`src/GiniFrontierGeometry.cpp:362–369`）。ENS-C 用同一可表示中点得到闭区间 ([a,p],[p,b])；`PaperExternalGiniTree.cpp:6170–6260` 在建立子域和覆盖检查后，将父有效界继承给两个候选子叶，求两个完整子 LP，直到均有终态才作决策（`:6340–6650`）。对父界 (B)、已验 (U)、两个有限子界 (B_L,B_R)，令 (D=\max(U-B,\varepsilon_{cert},10^{-12}))、(g_j=\operatorname{clip}((B_j-B)/D,0,1))、(\eta=\min(g_L,g_R))、(\mu=(g_L+g_R)/2)、(S_{AM}=\eta\mu)。先处理严格不可行子叶：双侧不可行可闭父，一侧不可行只收缩到另一侧；否则若 (\min(B_L,B_R)\le B+\varepsilon_{cert}) 请求父叶 exact closure；再否则 (S_{AM}+\varepsilon_{score}\ge0.08) 才立即分裂；低于门槛先对父叶运行以 (\min(B_L,B_R)) 为目标的原生 MIP。公式、数值评分容差与分支顺序在 `PaperExternalGiniTree.cpp:963–1075`，实际选择/账本在 `:6588–6935`。0.08 是归一化的双侧界收益调度阈值，既非证明容差，也非 time/Work 配额。
5. **父叶保持、原子覆盖与终端。** 未立即接纳分裂时父叶仍覆盖原域。native-bound target 由同一全局截止约束，只有原生证实下界达到目标才重排开放父叶，未把 target-reaching 记为闭合；native MIP 真正 `OPTIMAL`/`INFEASIBLE` 才闭合（`PaperExternalGiniTree.cpp:3848–4155`）。只有完整有效证据触发 `scheduler.splitLeafAtomically` 或 `scheduler.contractLeafAtomically`；失败/截止前保留父覆盖（`:7273–7467`，见原子事务与 contraction ledger）。不可分、零收益或 target 后请求父叶 terminal MIP；`PaperExternalGiniTree.cpp:1076–1105,8500–8720` 对其终态、模型指纹、原生界和物理一致性作门禁。`src/main.cpp:13060–13135` 将启动后剩余的**同一个**全局截止传给精确阶段；`PaperExternalGiniTree.cpp:3409–3419,4253–4272` 截止时保留开放覆盖并报 unknown。最终 `PaperExternalGiniTree.cpp:8760–8930` 重验 incumbent，检查根与亲子覆盖、所有相关叶闭合、叶/全局界单调、生命周期和 (U,L) 的原证书条件；只在全部成立时称原问题数值认证。账本中的 `proposed_exact_parent_closure` 或 terminal MIP 启动不是实际已认证闭合。
6. **LP-G 唯一差异。** 默认关的 Round90 标志只在当前**完整最优父 LP**、有限 `G`、相同模型 SHA/区间/incumbent epoch 且 (a<G<b) 时用 (p=G_{LP})；否则仍用中点。`src/GiniFrontierGeometry.cpp:443–488` 构造精确共享端点，`PaperExternalGiniTree.cpp:6184–6255,6340–6600` 核父模型与同 epoch 子缓存的精确身份；随后两子 LP、AM、native target、末端 MIP、深度/宽度和证书均不变。`src/main.cpp:254–260,3316–3323,3949–3953` 把它列为独立研究身份，不应混称原 ENS-C。详见 [Round90 handoff](../unified_exact_round90/lp_g_split_implementation_handoff.md)。

## 可直接引用的命题及证明边界

**命题 A（cutoff 下的覆盖与原问题下界）。** 令 (U) 为原物理已验 incumbent，当前 epoch 的目标 cutoff 为 (\kappa=U-\epsilon)，(\epsilon\ge0)。假设根 (G) 域覆盖所有目标不大于 (\kappa) 的原整数解；每次原子分裂保持父域覆盖，收缩只删除已证不可行区域；每个保留或已闭的最终区域 (j) 都有对该区域有效的下界 (B_j)，其中证实不可行区域取 (+\infty)，被替换的父叶不重复计入。则

\[
L_*:=\min\{\kappa,\ \min_{j\in\mathcal J} B_j\}\le F^*,\qquad \min\varnothing:=+\infty.
\]

这里 (\mathcal J) 同时涵盖开放叶和有有效终态证据的已闭分支。证明：任一原可行解若 (F>\kappa)，cutoff 排除区自身给下界 (\kappa)；若 (F\le\kappa)，其真实 (G_{true}) 落在至少一个最终叶区间，将该解以 (G=G_{true}) 嵌入该叶的整数模型，其区域界不超过该解目标。对所有解取最小即得结论；(S=0) 用 (G_{true}=0) 的根域。特别地，当前 ENS-C 的 (\epsilon=0) 给 (L_*=\min\{U,\min_jB_j\})：即使最优解就是 incumbent、开放叶为空或全部叶界大于 (U)，覆盖论证仍成立。若另一路径使用正 (\epsilon)，只由截止内叶闭合一般只能推出 (L_*\ge U-\epsilon)，不能在零容差下由此宣称 (L_*=U)。

这是通用 cutoff 情形下的安全下界表达式，不声称源码逐字计算 (L_*)。`ControllingLeafScheduler.cpp:581–608` 的 `globalLowerBound()` 实际取所有仍相关最终叶（包括已闭叶）的最小 `leaf.lower_bound`，集合空时返回 `0.0`，没有显式与 (U) 取最小。当前 (\epsilon=0)、覆盖成立且各叶界可靠时，最优原解仍有对应区域，所以相关最终叶的最小界本身也有效；这里没有据此发现一个实际错误下界。通用表达式说明为何不能只拿开放叶的最小值、脱离覆盖不变量或混入正 epsilon 路径。`PaperExternalGiniTree.cpp:3499–3524,3559–3562` 在 incumbent epoch 改变时废弃旧 cutoff 的 artifact/LP/子缓存。每个被使用的 (B_j) 必须对当前表示的区域仍有效：在相同区域上，由较松旧 cutoff 得到的可靠下界可以经集合包含关系继续继承；这不同于复用过期的父 LP 点或模型缓存。实际证书在 `ExternalGiniTree.cpp:460–495`、`PaperExternalGiniTree.cpp:8760–8930` 还要求根与亲子覆盖、所有相关叶关闭、界有效/单调、物理上界及 (L+\varepsilon_{cert}\ge U)；这些是沿用项目浮点和残差门禁的数值认证，非独立的有理下界证明。此处只厘清证明口径，不改源码记录 (L) 的规则。

**命题 B（AM 已接纳双侧 gap 的条件收缩）。** 在父/两子均为有效有限界、(U\ge B) 且 AM 非不可行分支，设 (t=\max(0,0.08-\varepsilon_{score}))。若接纳 (S_{AM}+\varepsilon_{score}\ge0.08)，则 (S_{AM}\ge t)。写 (z=\max(g_L,g_R)\le1)，故 (S_{AM}=\eta(\eta+z)/2\le\eta(\eta+1)/2)，得到

\[
g_L,g_R\ge\eta\ge\rho(t):=\frac{\sqrt{1+8t}-1}{2}.
\]

当 (t>0)，两个子叶各满足 (B_j-B\ge\rho(t)D)，从而 (\max(0,U-B_j)\le(1-\rho(t))(U-B))；在 (t=0) 时还需子域嵌套/源码严格增益检查来得出非增 gap。若 (\varepsilon_{score}=0)，(\rho(0.08)\approx0.1403124)；实际评分容差可能令该数值保证变弱甚至空泛。该命题不覆盖 infeasible contraction、native-target 或成本，也不能单独证明去掉 depth 8 后有限终止（[AM note](../unified_exact_round90/am_gap_contraction_note.md)）。

**命题 C（LP-G 对一个父 LP 点的产品残差极大化）。** 对完整 one-hot/透视块的固定父点，(\sum_y s_{iy}=1)、(\sum_yq_{iy}=G)，定义

\[
\Phi_L(p)=\sum_{i,y}(q_{iy}-ps_{iy})_+,\quad
\Phi_R(p)=\sum_{i,y}(ps_{iy}-q_{iy})_+.
\]

左量随 (p) 不增、右量不减，差为 (n(G-p))。因此在 ([a,b]) 上 (p=G) 最大化 (\min(\Phi_L,\Phi_R))，共同值为 (\tfrac12\sum_{i,y}|q_{iy}-Gs_{iy}|)。若存在非精确乘积且父域透视行有效，则 (G) 必为严格内点、两子产品块均排除**这一父点**。若所有 (q=Gs)，此产品块在 (p=G) 下仍容纳该点；其它子模型行可能另行排除它。即便排除当前点，替代最优父点仍可能保持同一 LP 界，不能声称严格子界或更快 MIP。证明及数值前提见 [critical band](../unified_exact_round88/split_critical_band_proposal.md)；Round90 实现只读一个当前父 LP 标量 `G`，并未根据完整产品残差自行选择其它点。

**命题 D（C3 即时零收益，仅作理论边界）。** 若一个完整父 LP 最优向量、目标和每列映射在某子 LP 全部行/域/cutoff/epoch 下可行，且子 LP 真是同目标父松弛的子集，则该子 LP 最优界等于父界；另一子域界不低于父界，所以两子界最小值不严格增加。证明是父最优解给子上界、松弛嵌套给子下界。标量 `G`、聚合产品误差零或 AM 标签都不足以验证前提；ENS-C **未实现**这个 C3 快捷跳过，不能把命题写成既有运行优势（[R88 C3 review](../unified_exact_round88/split_next_gate_review.md)）。

**命题 E（受限启动下降的有限性）。** 固定有限站点、车辆、有限库存容量与一次访问约束，并排除外部截止。每个成功 decoded pass 使已解码原目标适配的 fitness 严增超过 (10^{-12})（`HybridGA.h:1343–1366`）；状态集有限，故不会无限接受严格改善；完整无改善 pass 才称当前有限 guided 集合穷尽。R83 后处理每次要么经原问题验证使 (F) 严降，要么保持库存与 (F) 并使排序后的车辆时长向量严格按字典序下降（`Round83BlockExchange.cpp:151–185`；`Round78BalancedRelocation.cpp:41–47`）。有限状态上的这组严格势也不可能无限下降。这证明代码声明的受限邻域下降终止，不证明所有可能整数/路线邻域的局部最优，更不证明全局最优；若全局截止到来，仅保留当时已验 incumbent。

固定深度 8 使不同分裂路径上的几何层数有限；完整原模型的终端 MIP 若能可靠终止，已认证闭合的正确性由命题 A。实际全算法在给定全局截止内也可能仅留下合法 (U,L) 与开放叶；不从有限深度推出多项式时间、无截止必终止，或 native-target 反复重排的独立次数上界。若只保留中点和正最小宽度而去掉深度，R88 给出额外有限几何证明；LP-G 的任意内点不享有中点宽度减半，不得将这项反事实证明挪用到 Round90。

## 必须披露的活跃设置与范围

| 设置 | 当前作用与来源 |
| --- | --- |
| 起点 24+1、统一 seed 规则 | R70 的 24 随机解码起点加 R73 的一个验过的构造起点；`src/main.cpp:307–335,8068–8150`、`src/HgaTgbcRunner.cpp:107–180`。不是每个实例按效果选起点数。 |
| 有限邻域 top-8/top-6；严格改善约 (10^{-12}) | 单原子枚举后仅保留各路线八个、本地组合六个候选供跨路线复合；`src/hga_tgbc/HgaTgbcGreedy.cpp:601–602,1682–1771`，`include/hga_tgbc/HybridGA.h:1309–1379`。声明此受限邻域的耗尽，不声明全离散邻域最优。 |
| 单根区间、中点、分裂因子 2、AM (\tau=0.08)、深度 8、最小宽 (10^{-4})、父叶 exact closure | `src/PaperK1AmSf.cpp:53–66`、`include/Instance.hpp:178–188`、`src/GiniFrontierGeometry.cpp:362–369`。LP-G 只换合格分点且保持深度/宽度。 |
| VD-P、静态 compact 行、F0 连通流 | `src/main.cpp:338–352`、`src/PaperK1AmSf.cpp:68–116`、`src/Round50IntervalMip.cpp:162–169`、`src/CplexBaseline.cpp:1518–1568,2837–2963`。模型包含时间、载量与截止，而非独立 Gini 子问题。 |
| 支持时长 rank≤3、最多考虑 50,000 个子集 | `src/PaperK1AmSf.cpp:78–80`、`src/CplexBaseline.cpp:1910–1969`；实际 canonical export 路径绕开资源适配关闭支路。50,000 会按枚举/车辆顺序截断静态行，并非数学族必然值或时间切片；见 [参数审计](../unified_exact_round88/active_count_parameter_audit.md)。 |
| `domain_propagation_mode=iterative`, `rounds=2` | 配置标签在 `src/PaperK1AmSf.cpp:76–77`，但该 canonical writer 没有真正执行两轮域传播；`src/CplexBaseline.cpp:5095–5098` 的完成数最多 1。论文不能称两轮闭包。 |
| root cut rounds 0、dynamic cut families none、native target policy existing-K1、全局截止 | `src/PaperK1AmSf.cpp:63–69,112–115`；native target 是数学下界目标，非按秒/Work 的服务份额。研究 runner 的进程 cap/Seed 0/单线程/Presolve Auto 与算法内部规则分开记录。 |

数值深度遥测仍有已知漏洞：`result.external_gini_tree_max_observed_depth` 可陈旧为 0，最终深度图须从 leaf/decision ledger 核，不可直接引用该字段（[R90 depth note](../unified_exact_round90/depth_telemetry_followup.md)）。别把“提出切点”“完整子 LP”“AM 选择”“原子替换”“请求父 exact closure”“实际 MIP 关闭”合并成同一事件。

## 论文证据尚缺

已完成的开发证据只链接：[R88 A1](../unified_exact_round88/a1_g3_decision.md)、[A2](../unified_exact_round88/a2_composite_endpoint_decision.md)、[OT closure](../unified_exact_round88/ot_closure_decision.md) 与 [epigraph](../unified_exact_round88/ot_epigraph_decision.md)、[R89 native B1 非晋升](../unified_exact_round89/native_b1_decision.md)、[R90 G3 混合结果](../unified_exact_round90/lp_g_g3_decision.md)与 [C2 seed 波动复核](../unified_exact_round90/c2_repeat_decision.md)、[R91 handling 数值诊断](decision.md)。本稿未纳入 F2/D6 在途优先保护批次；任何 G4 余项/全部角色、正式 P-GRB 同期认证、新数据、全成本和最终实例范围的结论均待证。默认 ENS-C 若最终满足计划的同源身份、原问题证书、当代 P-GRB/K1 对照、保护集、独立新数据与负例/删失完整披露，仍可成为候选；当前 LP-G 的 C2 有利与其余混合/删失结果绝不足以称稳定优于 P-GRB。

晋升前还需固定算法/环境/参数/输入、对所有预注册臂按全过程费用记录启动、构模、LP、partial/terminal MIP、验证与失败尝试；报告证书失败、数值拒绝和未完成叶，不从界增量推运行优势。形式化证明须逐条注明模型有效行、整数一致性、覆盖、数值求解假设；理论部分区分既有 Gini/透视/分支思想与本工程的特定组合，不因本地未找到文献就主张首创。用户要求的论文式 LaTeX 源、实际编译并目视检查的 PDF，以及晋升/长时实验冻结协议仍未交付；本 Markdown 仅供写作，不能替代它们。
