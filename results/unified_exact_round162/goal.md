/goal

# Round162：旧 Gini 乘积与完整物理域的共同端点一致性——能力、有限投影与完整算法价值

## 0. 本轮目标与执行原则

继承已完成的 R161。本轮集中研究一个问题：**在原 M-B/VD-P 目标表达中，各站 shared-G products 隐含的两组端点库存，除了满足 R138 的总库存条件，是否还能同时补全为同一个完整物理连续模型中的端点？如果不能，这个缺口能否产生可保留、可付费的原目标下界增量？**

沿用旧 Gini 表达、原 penalty 和原物理模型。在 OLD+STOCK 上，为指定完整物理子系统 Q 建立共同 G 因子的端点扩展。先让全部原变量自由重优化，量化相对 OLD+STOCK 的增量；有实质信息后，将一次 root source 的合格对偶压缩成一条原变量空间的行，再检验 C++ Native 搜索和原 GI 完整流程。研究入口暂名 `E+STOCK+PC`，默认关闭。

本轮的研究对象是**Gini 乘积所条件化的物理一致性**。两端点凸化、RLT 和对偶投影都是已有工具；潜在贡献在于本 BRP 中尚未得到回答的共同物理完成条件、它与已有库存条件的差异，以及能否以有限实现成本改善完整精确算法。不要把新旗标、两份变量或一行 cut 本身当成论文创新。

总科学容量 **24h=86400s**。先做有结论的能力研究，再按证据推进真实搜索。没有要求用满预算，也不要求预先保证胜出。一次有效的严格增量、一个有解释力的无增量完成见证，或一个有充分实验的成本失败，都可以是完整研究结果。避免把工作变成历史恢复、反复审核或自动组合扫描。

算法定义对所有输入一致，不依实例名、历史胜负、规模分档、CPU 型号、机器速度或内存切换机制。实际合法支持、库存/路线数据、当前合格 incumbent 和作用域可以进入数学构造。实验窗口、统一总 deadline 和保存余量属于资源合同，不作为“若干秒后换机制”的在线策略。

**新增反复执行的算法核心与正式性能候选全部用 C++。** 包括 Q/端点模型构建、实际矩阵登记、对偶投影与数值补偿、Start 映射、行的作用域继承和在线结果处理。Python 可用于编排、离线分析、独立验证及历史共用 helper；共同旧 helper 在每个完整臂内自付。有限 Python 原型不代替 C++ 性能证据，也不要求为统一语言重写全部旧框架。

稳定 GI-TBC/B（S2/ms2）、E+ 默认及裸 CLI 兼容行为保持现状。R160 物理邻域、R161 RN 替代、R143–145 RN source 和 R139 非对称 STOCK 放置在本候选中关闭。两条带 STOCK 的正式臂统一在全部相应 LP/MIP 中使用 R138 四行。原 Gurobi Seed=0、Threads=1、正式 MIPFocus=0；完整 own-H seed=20260626。沿用合格编译政策与数值合同，不同时调 solver 参数、优化级别或 fast-math。

## A. 工作起点、最新事实与有限历史排重

工作入口：`E:\codes\ExactEBRP-work\worktrees\paper-current`。检查适用 AGENTS.md、WORKSPACE_POLICY.md、用户修改和活动进程，为本轮建立隔离 worktree。保护 `E:\codes\ExactEBRP` 和已有论文/研究树；新增 worktree、build、raw、archive、temp、restore 均置于 `E:\codes\ExactEBRP-work`。

2026-11-11（UTC+8）审查快照如下，执行时刷新：

- 仓库 `yifanXovo/TailoredExact`；R161 为 Open Draft [PR #223](https://github.com/yifanXovo/TailoredExact/pull/223)，未合并。
- R161 branch：`codex/round161-full-physical-rn`；delivery head：`dd75d7a2445dafdcd9b9c443a107a0c3ca4a15f3`；fixed science：`fcd83fdf4d8980cbfdd6a860d5fe44fb7aa98158`。
- R161 base：`codex/round160-physical-neighborhood`；其 head 为 `53e5c62fbcf6bc24898b7d5d3ecb755e4331ab0b`；main 为 `b2b940c1e517a72e226ec60fc49ff19651737632`。
- R161 core 实测 C++：`1fafb6e2a4a3569cbb312a2f94738f822d2da500`；RN-P 实测 C++：`006103fa7a3f5f7a09ff3621ee54c2c1ad7bab9f`。
- core PE SHA256：`567e8c34d578843adf19e5958c36b63dcf92bd60d75b889db1d5fd2334a34598`；RN-P PE：`52ef690873f9f4d4c71f7695c2164380647a2c8f686ec044046c1a08c0cdb0f0`。
- Gurobi 13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

若 main 已吸收所需依赖，从 main 开始；否则基于核实后的 R161 head 建立 `codex/round162-physical-g-completion`，Draft PR base 用 R161 branch，无需等待前序合并。若已有 R162 实际工作，接续去重；不要开同轮重复分支。分别记录实测源码、实际启动 PE/DLL、科学快照与最终 delivery 身份。

先读 R161 的实际 goal、final_report、decision、bridge、LP_product_diagnostics、envelope_diagnostic、费用和 C++ 实现。历史按以下入口有限回看，形成一张“已完成—本轮差异—待验证”表；不恢复整段历史、不执行旧 producer。

| 历史 | 已有实质内容 | 本轮边界与增量 |
|---|---|---|
| R54、R62 | 库存—路线有效不等式；R62 已对有限库存冲突做 Gini-RLT，并有完整付费结果 | 不能声称首次 G×物理 cut；要验证完整 Q 的共同完成条件超出 STOCK 的真实增量 |
| R63、R64、R66 | 累积 travel/handling、载荷—时间耦合、arc-load carrier 与完整实验 | 复用当前 physical carrier；不重开一个换名的 load/time flow |
| R88、R103–107 | 目标/数量图结构、单车必要 hull、oracle/IIS/master 和投影研究 | 不重做固定点分离后直接宣称收益；不扩为 master-oracle 工程 |
| R132、R133 | 联合物理服务 hull；零 G 的分数库存仍可能留下原目标差距 | 本轮并不消除所有整数目标 Jensen gap；应证明自己的无增量边界 |
| R138 | STOCK 四行、连续选定资源块的共同因子端点凸包定理；完整表现混合 | OLD+STOCK 是直接基线；一般凸化原理已有，新增对象为完整物理 Q |
| R139 | STOCK 的不同 LP/MIP 放置 | 本轮固定两条 STOCK 臂的全 LP/MIP 放置，避免再混入 placement 因素 |
| R143–145 | RN 附加、一次 root source、对偶压缩；normalized stock/计数条件 | 复用生命周期和数值投影方法，source 换为明确的物理端点对象；不启用旧 RN source |
| R153 | 共同库存—目标列、完整分母切片、定价和整数目标 lower | 库存目标分布经原 marginals 接物理域，并不自动给出 G 条件下的物理共同完成 |
| R156 | S×penalty residual 与 McCormick、incumbent penalty cap | 不把另一个 penalty product 或分母 envelope 当成新主线 |
| R159、R160 | quantity/owner 资源块、真实物理联合邻域、完整反馈回退 | 不扩大 block/node/pass 或改反馈时机作为本轮研究 |
| R161 | 完整物理 RN 替代与一次 RN-P 修订，真实有限搜索后均弱于 OLD | 回到保留旧目标信息的明确耦合缺口，不继续自动收紧 t/S |

这里的排重是仓库历史核对，不是全领域首次性的证明。准确引用相关 RLT/析取凸包文献即可，不另设综述工程。

## B. R161 的阶段结论与本轮假设

R161 确实保留了同一物理载体和原 `G+Σα_i e_i` penalty，替换旧目标模块；正库存与零库存 union 已处理。两来源均进行了 OLD / RN / RN-P 的 LP 和 900s 外层 MIP。六个 LP 为 OPTIMAL；六个 MIP 均有 716–1711 个节点、真实物理解改善，最后 TIME_LIMIT。

| 来源 | 表达 | LP lower | MIP physical U | MIP qualified L |
|---|---|---:|---:|---:|
| RX35 | OLD | .186099795447 | .401139788438118 | .210751964941072 |
| RX35 | RN | .120868897014 | .415548056887 | .179466164584 |
| RX35 | RN-P | .124676728839 | .406923269363301 | .173456239045039 |
| NB35 | OLD | .327833772177 | .463426190476191 | .388764524132733 |
| NB35 | RN | .269025714286 | .466805915424 | .365784602936 |
| NB35 | RN-P | .301013209511 | .497425087324243 | .378710952495425 |

OLD 在这些调用的终点 U/L 均更好，但不逐时支配全部轨迹。RN-P 的 LP 改善未转成终点优势。科学实耗 5455.09331771126s；未进入条件完整面板是合理停止，不需补跑。RN-P 控制复用有新导出 OLD 模型/Start 逐字节相等和共同 backend/mapper 对象身份支持，不为“同 PE”形式重跑旧调用。

保存的 RN/RN-P LP 仍允许 G=0 与不相等的原 fractional-Y ratios 同时出现。固定 S 时 RN 精确及已有 covariance/distortion 上界在数学上成立，但通用上界较宽；排除这些旧点还可能重复 R145 STOCK 信息。它们不足以直接启动更多分母分裂或 penalty 产品研究。

新的可证伪假设是：

> OLD 的局部 state/G products 允许站点分别选择“高 G 端点库存”和“低 G 端点库存”。STOCK 只检查两个端点的总库存。如果这些端点不能与原 route/owner/quantity/load/time 坐标共同形成物理连续完成，要求共同完成有可能提高原 J 的自由 LP 最优值。

R161 的两个 OLD LP 都有正 G 及非零乘积残差，因此该问题值得实际检验；这些残差本身不证明 full-Q 强化一定有效。R138 四行、原物理模型或后续自由重新混合可能已消化全部相关信息。

## C. 数学对象、有效性与无增量边界

### C1. 明确定义 Q，不混入第二种目标机制

用当前实际、未 presolve 的 OLD+STOCK native 矩阵定义物理变量向量

\[
X=(x,z,\mathrm{mode},p,d,\mathrm{load},\mathrm{ord},\mathrm{conn},Y,\mathrm{state}),
\]

具体族以真实 writer 和列登记为准。它包括弧/访问/单向服务、数量、载荷、次序、连通流、最终库存与库存 selector。构造

\[
Q=\{X:AX\le b,\ EX=f,\ \ell\le X\le u\}.
\]

Q 包含所有这些列的实际有限界，以及原模型中完整非零支持落在 X 内的行；逐族核对路线/仓库度数、唯一非零服务、空车出发、完整载荷与返仓、旅行及 handling 时间、connectivity、库存平衡、selector–Y 链接等实际启用信息。未知列/行先查源码并登记语义，不根据模糊名字匹配删除项或忽略非 X 系数。

原 `G,state_g,zprod,r,e,h,r_min,r_max,W_SP` 等目标辅助列不属于 X。**它们及其原行、原 objective、原变量类型全部保留在外层 OLD+STOCK 模型中。** `state_g` 与 `zprod` 作为既有乘积接口使用。排除 e 是为了限定研究对象；当前 e 实际也有有限界，不能声称发现了无界 penalty 漏洞。

Q 是这个明确的有界物理子系统；不称为消去全部目标辅助列后所得的精确物理投影，也不称为整数车队凸包。不得启用旧 R64/R66、额外资源 cuts 或新 penalty 等价式来偷偷增强 Q。当前列已有有限界，例如 conn/ord≤n、load≤Q_k、p/d 有原单站服务界；无需另设经验 big-M。

显式核对总库存两行及其合法含义：

\[
B=\sum_{i\ne0}b_i,\quad
\sum_iY_i=B-\sum_k R_k,\quad
0\le R_k\le Q_k,\quad
B^-=\max(0,B-\sum_kQ_k)\le\sum_iY_i\le B.
\]

仓库序列化库存不计入 B。累计 pickup 可超过车辆容量；完整 handling 仍按原 pickup/drop/返仓卸载计时。当前 S2 writer 已有原库存上下行，连同 Y 非负可直接利用。若某恢复 carrier 缺失，在两比较臂共同补入已证明的同一未提升库存行并登记，不能只给 full-Q 臂增加新原域信息。

Q 的界和常数可来自当前整个 [L,U]、inclusive cutoff c 的合格共同传播。禁止将 G、G×变量、Gini epigraph 或 `G+Σαe≤c` 本身作为 Q 行；这些继续留在外层。两个端点不分别再做 G=L/G=U 的目标传播。它们必须使用同一个 Q。

### C2. 共同 G 因子的完整端点扩展

令 `L≤G≤U` 为当前 source 的实际区间。概念上为每个 X 坐标引入 `V=GX`。对 Q 的每个不等式要求

\[
A(V-LX)\le b(G-L),\qquad
A(UX-V)\le b(U-G),
\]

等式同时提升，有限上下界也属于完整系统。对已有乘积直接链接

\[
V_{\mathrm{state}_{iy}}=\mathrm{state\_g}_{iy},\qquad
V_{Y_i}=\mathrm{zprod}_i.
\]

zprod 是 GY，不是 GY/D。使用真实加载的变量与系数，不用重新舍入的理想目标系数替换原模型。

当 L<G<U 时，

\[
X^U=\frac{V-LX}{G-L},\qquad
X^L=\frac{UX-V}{U-G}
\]

必须同时属于 Q，且原 (X,G,V) 是两个端点的凸组合。包含全部 Q 行、等式和界时，该扩展给出

\[
\operatorname{conv}\{(X,G,V):X\in Q,\ L\le G\le U,\ V=GX\}.
\]

这是标准两端点/RLT 结论在指定 Q 上的应用。给出必要性、上述充分性和端点闭包证明。L=U 时直接用 V=LX，不计算零分母。G=0、零总库存、异质目标/权重和 loaded return 都沿用原模型；该构造不需要 S>0。

**X^L、X^U 是连续 Q 中的点，可能含分数弧/owner/selector。** 不把它们称为真实整数车队，也不要求它们自身的真实 Gini 等于 L/U。G 是原 epigraph 变量；原完整整数解即使 epigraph 非最小，也可以用 V=GX 扩展。因此附加条件保留全部原整数解及原最优目标值。

### C3. 优先用缩放端点实现，控制新系数误差

推荐下列代数等价的 C++ 扩展，避免直接生成大量 L×A/U×A 新系数：

\[
\lambda_L+\lambda_U=1,\quad \lambda_L,\lambda_U\ge0,\quad
G=L\lambda_L+U\lambda_U,
\]
\[
X=\xi^L+\xi^U,
\]
\[
A\xi^e\le b\lambda_e,\quad E\xi^e=f\lambda_e,\quad
\ell\lambda_e\le \xi^e\le u\lambda_e
\quad(e=L,U).
\]

只对需要接旧产品的坐标写

\[
\mathrm{state\_g}_{iy}=L\xi^L_{\mathrm{state}_{iy}}+U\xi^U_{\mathrm{state}_{iy}},
\quad
\mathrm{zprod}_i=L\xi^L_{Y_i}+U\xi^U_{Y_i}.
\]

其他 V 不必显式建立。全部新列连续、目标系数零。旧 X 在能力 LP 中松弛，在 MIP 中继续使用原类型。两份 ξ 使用同一原 A/b，保留实际系数，行列数为 O(nnz(Q)) 规模；不要引入逐路线枚举。

可以作一次有证明的等价消元以减少列/行；它属于同一表示的工程实现，不另开双配方性能网格。若改用直接 V 形式，新增 signed 系数的舍入必须按有限盒支持做单侧补偿，不能只沿用 STOCK 的 RHS 向外取整就宣称全部有效。

对实际加载矩阵读回：新列/行登记、旧 block 不变、极小新系数未被 native 删除，以及必要的二进制幂缩放。沿用既有数值合同，不为通过样例放宽容差。

### C4. 与 STOCK 的关系及一个必须说清的极限

Q 包含总库存上下界，其共同因子提升应蕴含 R138 STOCK 四行；用同一实际 [L,U] 和原变量映射证明、读回。能力比较仍显式保留 STOCK，便于验证真正新增的物理信息。

另证明以下无增量充分条件：如果 OLD+STOCK 的一个最优 LP 点满足所有既有 `state_g=G·state`（从链接得到 `zprod=GY`），则用 V=GX 可将该点扩展到 full Q，原目标值不变；因而本 scope 的 full-Q LP 无增量。当前完整 VD-P 在 G=L 或 G=U 时强制这种既有产品一致性，所以端点最优点也适用。G=0、L=0 是一个重要特例。

这解释为何本轮不能修复 R133 的全部零 G/整数目标差距。正 G 和非零残差只提供待检验的可能性。无增量结论约束当前 scope 的 LP；不能扩张为任意子区间、任意实例或任意整数搜索都不受益。

## D. 有结论的能力试验与一次有限压缩

### D1. 最小接口资格后，立即处理真实 source

复用 R161 的 actual-matrix/registry/LP-MPS 读回框架，但不调用删除旧目标模块的转换。复用 R138 STOCK writer 与现有 backend、Evaluator、Start mapper。

新增资格只覆盖本接口：少量 tiny 中检查真实整数解的完整扩展、L=0/U 端点、L=U、零库存及 loaded return；验证 OLD 整数目标与附加模型一致。用原完整 Start 构造 ξ 或 V，检查实际全部新行与 bounds。复用原输入/物理资格，不重建历史穷举工程。必要时对最多两三个 tiny 求解或枚举，保留失败和修正。

R161 standalone writer 把 raw bound 直接记为 `global_transported_floor`；其本轮数值均低于 cutoff，所以没有推翻旧结果。若复用该入口，本轮将输出明确改为原合同的 `min(qualified_restricted_lower, cutoff)`，并分列 raw/qualified/global；无需为修正这个通用字段重跑 R161。

### D2. 首先比较原 J 的自由 LP 最优值

首先在 RX35、NB35 使用身份完整的 R161/R160 own-H/R83 parent 和完整 root carrier；作为离线开发输入复用，明确不算 fresh 完整算法。

每个来源比较：

1. **S：OLD+STOCK。**
2. **F：同一 S + 完整 Q 端点扩展。**

共用原目标、原 e penalty、physical/common rows、合法支持、[L,U]、inclusive cutoff、原输入与原参数；允许全部原 Y/selector/路线/owner/数量/载荷/目标辅助变量自由重优化。复用某个 bare OLD LP 仅作背景，前提是其实际载体身份相符；不能把相对 bare OLD 的改进算作新增物理端点信息。

每对保存原始矩阵、scope、最优 primal/dual、状态与合格 lower、G、产品残差、row/column/nnz、系数范围、Native Work/迭代、source 外层总费。初次 LP 每调用可用 300s 开发窗口；超时记为未决，不把 TIME_LIMIT 的近似 primal 当作最优无增量证据。确因同一能力问题未解，可从本阶段容量内有限延续并记录原因，不展开时间网格。

先尝试把 S 的保存最优点扩展到 F：若成功且完整核验，用该扩展可行点的原 J 上值与 S 的合格 lower 按既有精度/资格闭合，提供该 scope 的 attainment 见证，可以免去一次纯重复 F 优化。数值读回只支持相应精度下无可识别增量；精确等值须有相应代数证据。若扩展失败，只说明该点不可完成，仍须解自由 F 才能判断最优值是否提高。为读懂机制可以固定点做一次 completion LP，不能把其不可行性当成自由原 J 收益。

如果两个主要来源都没有新原 J 信息，再在 K20 做一对 S/F 能力 LP，以核对库存 floor 与物理限制差异明显的另一角色。若三者均无增量，用实际完成见证或合格原目标等值结果关闭当前能力研究；不为“缺 MIP 表”去跑巨大 full-Q MIP。若任一主要来源有实质增量，K20 与 RX20 的少量 source/投影读回用于后续一般规则和成本资格即可。

有增量时，给出一个由实际解/对偶支持的简洁解释：到底是 owner/服务耦合、载荷/连通性、完整时间还是它们的共同完成排除了旧分数机制。可以做最多一个语义明确的中间子系统或行族消融，帮助理解；不要扫描所有行族组合，也不要靠事后挑少数弧/实例调规则。

### D3. 一次 source 对偶投影，检验信息能否低成本保留

F 有真实原 J 增量后，从其合格最优 LP 的对偶构造**一条**投影行。保留原 OLD+STOCK 变量，消去全部新 ξ/λ（或 V）列。允许行中出现原 state_g/zprod、G、Y 及 route/owner/quantity/load 等物理变量；不能为了套用旧 RN projector，先把关键物理项删掉。

给出所用的标准对偶聚合事实：在精确算术、同一基线/作用域/目标、合格最优对偶下，聚合新增扩展行并消去新列得到的一条有效不等式，与原基线一起可以保留该 source 的 LP 最优值。这是针对这一原目标/作用域的最优值陈述，不是完整投影等价，更不是整个整数问题凸包。

实现中按实际行 sense 修复/检查 multiplier 符号；使用新列有限盒对残余新列系数补偿，使用原列有限界对输出系数舍入补偿。由 ℓ·λ_e≤ξ^e≤u·λ_e、0≤λ_e≤1，得到每个新端点坐标的独立盒 min(0,ℓ)≤ξ^e≤max(0,u)；这里 ξ^e=λ_e X^e，而非 λ_e 乘原混合点 X。所有补偿方向与损失读回，沿用 R144/R104 的合格模式，不直接照搬只识别 RN/selector 的固定名字代码。

然后解一次同 scope 的 **C：OLD+STOCK+PC** 自由 LP，比较 S/F/C，报告 F 增量保留了多少、数值弱化损失和实际成本。用完整矩阵和原目标检验，不能只看投影行对旧点的 violation。

若 F 的自由最优值没有增量，本轮不研究它的子集 separator；若 F 有增量而合法投影损失吃掉全部信息，允许一次有证据的等价表示/数值修订，之后作明确停止判断。不要自动改开多 row budget、反复分离、S/t 桶、RN+OLD 或 penalty 产品。

至少一个来源获得超过数值误差范围、可保留且成本可承担的增量时，推进真实 C++ Native 搜索。**不要求新 root lower 先超过 E+ 已有 inventory proof-only floor**：新物理行可能通过后续搜索产生价值，scalar floor 与 native 行的作用不同。最终仍需要完整付费结果。

### D4. 用小量真实整数搜索检验投影后的行为

预先固定两个互斥实验分支。“阳性”指同 scope 下 F 相对 S 的自由原 J 有可靠增量，且合法 PC 经重优化实际保留信息；旧点 violation 不算。

- RX35/NB35 至少一个阳性：在 RX35、NB35 各做一个 S/C whole-native matched pair。
- 只有 K20 阳性：改在 K20、NB35 各做一个 S/C pair；NB35 是预定跨来源成本/稳定性控制，不用其无增量再次否决 K20 的实质进展。

两分支都只做两个 pairs，默认每臂同一 900s 外层窗口、4096 节点开发容量，Seed0/Threads1/MIPFocus0，完整 root 改进域、同 parent 和同 Start。它们是 OLD+STOCK 与新增物理投影的对照，不是完整 GI 方法，也不是 P-GRB。所有输入执行相同 source→投影规则；若得到合格恒真行，正常不写入并登记，已付 source 成本仍计入。这里改变的是预先定义的离线采样，不是按实例切换在线算法。

C 的外层窗口包含本次 Q/source/投影/转换和 Native；不得先免费生成 cut 再给它额外 900s。离线父车队可复用，既付 source 结果可以作原理读回但不能冒充 C 本次已付生成时间。S 不付不存在的 source。编译、计时试验、大型 I/O 串行。

记录 verified U 轨迹、首次严格改善、qualified L、absolute/relative gap、Work/nodes、build/source/project/native/验证成本。输入 Start 重新被接受不计为首次改善。所有新车队按原 J、T、库存、完整 prefix loads 与返仓 handling 核验。

至多一次同一机制内的定向修订，总体不增加第二套切平面来源或控制器。若阳性来源在付费搜索中也未显示有用的端点/证明进展或成本折中，可停止完整面板；如果有值得确认的 U/L 进展或可解释的折中，则冻结一个候选进入 E。不要只凭一次 root lower 增加就宣称完整有效，也不要因根 LP 未闭 gap 就拒绝真实搜索。

## E. 统一完整候选与精简但可归因的面板

候选的固定在线流程：

**own-H/R83 → 原合法 root scope / 共用 proof-only helper → OLD+STOCK root 的一次 full-Q source → 一条合格 PC → 原 GI-TBC 控制及原 Native 求解。**

source 每完整运行至多一次，使用同一总 deadline；获取合格对偶后释放临时扩展模型，不把它遗留成正式大矩阵。正式模型只有原 STOCK 四行和一个合格 PC，无新增扩展列；保留原 AM/split/target 等既有控制，不改为 R161 的单 MIP。

两条 STOCK 臂在全部相应 LP/MIP 上统一启用 R138 STOCK，随各自合法区间生成实际四行；不启用 R139 LP-only/asymmetric placement。PC 在初始 source scope 内有效，只在原输入、行支持、[L,U]、cutoff/传播域等前提被覆盖的子域继承。更小 cutoff/子区间可在原适用证明下继承；模型重建必须生成新 hash 并按现有策略失效旧 retained handle。不能把局部行扩散到未覆盖父域，也不重复 source、重新跑 H 或增加新轮 cut 循环。

新开 `round162` registry、状态与默认关闭旗标。可复用 R144 的 once-root/capture/discard/embed 生命周期，但不打开它的 RN source，不复用其只认 RN 列的 projector。优先复用 `PaperLpRelaxation` 与 `capture_lp_primal_dual_evidence=true`。source 初期按既有 backend 在同一总 deadline 内求合格 LP；不引入按机器速度或实例名选择 source 时间的规则。

对 source 的异常/截止沿用既有证据资格：不消费未合格行，记录真实停止状态和已付成本；正常不适用的退化区间按 C2 直接处理。不得把“source 失败后切某一个强求解器”设计成新自适应算法，也不为失败强迫整个项目重新审批。未得到完整可比较运行时如实标注。

所有完整臂保留本臂自付的既有 E+ RN16384 inventory proof-only helper。其 floor 不新增进入 native 行、hint、Start 或 branch；本轮只新增 PC 的信息入口，不重开 floor placement。新 full-Q source 的 lower 只作研究诊断保存，不另作为 scalar floor 写入正式 proof ledger；source primal/dual 用于行的资格。正式 lower 从加入 PC 后的既有 LP/MIP 与原合格 helper/ledger 获得，原 proof 聚合、cutoff transport 与冲突处理继续沿用。

冻结同一 C++ 构建、配置、参数与串行顺序后，若 RX35/NB35 至少一个阳性且 D4 值得推进，采用以下最多 **10 臂**：

| 角色 | 完整算法臂 | 每臂生产总窗口 | 所回答的问题 |
|---|---|---:|---|
| R-X35-S-T2 | E+ / E+STOCK / E+STOCK+PC | 7200s | 新 PC 相对 STOCK 的增量，以及整个包相对 E+ 的价值 |
| N-B35-S | E+ / E+STOCK / E+STOCK+PC | 2400s | 第二主要来源，相同一般机制 |
| K-20-S | E+ / E+STOCK+PC | 1200s | 完整包的物理/证明收益与成本检查 |
| R-X20-S-T1 | E+ / E+STOCK+PC | 1200s | 快获证场景的完整额外成本 |

名义生产窗口总计 **33600s=9h20m**。若保留旧 cap+900 的监督预约，保守预约为 **42600s=11h50m**，在本阶段 13h 容量内；这不是给算法加时，也不是已发生费用。监督器仅保证退出/保存，不把窗口外继续搜索结果计为窗口内表现。

两个主要来源的 STOCK 控制不能省：R138 的四行虽小，却已改变完整搜索表现；历史结果不替代 fresh 控制。两个小角色只比较整包，不能单独将其改善归因为 PC。无需额外 small-STOCK、SHADOW、多 Seed 或 P-GRB 网格。

常规 10 臂分支先做两个主要来源的三臂。如果新包相对两种控制都明显不利、无继续确认价值，可停止剩余小角色并报告 partial；若声称四角色确认，应完成全部已定义 10 臂。

**K20-only 分支：**若 D2/D3 只有 K20 阳性，且 D4 的 K20 付费整数搜索值得确认，则只做 K20 的 E+ / E+STOCK / E+STOCK+PC 三臂，以及 RX20-T1 的 E+ / E+STOCK+PC 两臂，每臂仍为 1200s。共 **5 臂、6000s=1h40m** 名义窗口；cap+900 预约共 10500s=2h55m。先完成 K20 三臂，再按结果决定 RX20 保护对照。这与 10 臂分支互斥，剩余额度不触发原大面板。结论限 K20 的增量/整包判断和实际完成的 RX20 成本检查，不能声称四角色确认或改善两个 35 站困难来源。

两分支使用同一个对所有输入一致的算法配方。不得看正式结果后更改候选再混为同一冻结面板。实质 bug 仅作受影响范围的修复/作废/必要重跑，保留已付失败账。

每臂一个生产总 deadline，涵盖 H、helper、scope、source、投影、构建、全部 Native 调用与在线验证。事后必要验证单列 `T_verify`，`T_total=T_produce+T_verify`。以实际 process outer 为完整成本，nested Runtime/Work 不重复加账。正式候选不继承 D 的 4096 NodeLimit。

正式输入身份沿用已合格角色，启动前读回实际输入：

| 角色 | V/M | Q | 物理 T | lambda | 输入 SHA256 |
|---|---|---|---:|---:|---|
| R-X35-S-T2 | 35/3 | 20,25,30 | 6300 | .0754049775127276 | `c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2` |
| N-B35-S | 35/3 | 20,25,30 | 7200 | .15 | `80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98` |
| K-20-S | 20/2 | 30,30 | 5400 | .15 | `d1a65be4b87dead2ae351068ece3c3ce486a51c93652d778e055f2684606ea42` |
| R-X20-S-T1 | 20/2 | 30,30 | 4800 | .12676060979965992 | `2b467b5bb1e650a4c1e792e808dcf9575bcc76752fe378e16c838015344ddac6` |

上述 tp/td 均为 60s，代码继续读取一般数据。物理 T 与生产窗口不同。复用现有身份/费用骨架，为本轮新建 OUT/TEMP/meter/admit；不要直接执行旧轮冻结脚本造成多余实验或读写旧账。

报告 actual U、raw/qualified/proof L、gap、T_cert/T_total、各阶段成本、Native Work/nodes、失败与中断。无原 gap 关闭证书时 T_cert 留空，qualified OPEN 不等于 certified。当前有限角色/单 Seed 不支持“稳定胜过 P-GRB”的结论；若得到值得推广的候选，明确提出后续独立确认条件即可，不本轮自动扩 benchmark。

## F. 科学容量、停止判断和论文内容

| 阶段容量 | 秒 | 小时 |
|---|---:|---:|
| 有限复用、数学/新增接口资格 | 7200 | 2 |
| full-Q 能力、完成解释与一次投影 | 10800 | 3 |
| matched Native 与一次定向修订 | 7200 | 2 |
| 条件完整 10 臂及必要验证 | 46800 | 13 |
| 最后科学读回 | 3600 | 1 |
| 失败、未决问题与证据驱动调拨余量 | 10800 | 3 |
| **总科学容量** | **86400** | **24** |

阶段可依据已见证据在总量内调拨，留简短理由。新 LP/MIP、H/helper、科学核验、失败/恢复中的科学计算均计外层实际费用；普通代码编写、编译和文档不计 solver 科学费，但记录编译/I/O。所有 fee 关闭、嵌套费用去重；预算余量不是新增机制清单。

本轮要回答六个实质问题：

1. 哪些旧产品端点满足 STOCK，却不能在完整 Q 中共同完成？如果没有，保存了怎样的完成见证？
2. full-Q 与 STOCK 的确切包含关系、整数保持、端点/零域和无增量条件是什么？
3. 自由原 J 的最优值是否提高，还是只排除了一个可被重新混合替代的旧点？
4. 一条合格投影能保留多少新信息，代价与数值损失来自哪里？
5. 真实整数搜索和条件完整算法是否值得支付这笔 source 成本？相对 STOCK 与相对 E+ 分别如何？
6. 结果支持继续研究哪一个明确结构，或应在这个条件化层级停止？

写一份适量数学/算法研究节，围绕“旧 G 产品—共同端点物理完成—STOCK 差异—有限投影—完整成本”组织。正结果可形成 BRP 特有的结构命题、可解释见证与机制；负结果也应说明连续 Q 条件化的能力边界及剩余整数目标缺口。不要仅凭标准凸包公式宣称 OR 级创新，也不因基本工具成熟就拒绝研究其具体结构效应。

不要求另写数份 PDF、独立固定页数论文或重写主稿。若实质改 TeX，按已有流程编译检查。质量看数学增量、可复核证据和结论范围，不看文档数量。

## G. 最终复核、交付与本地条件

实现中的小量资格完成后推进科学工作，不逐 solve 增加审批。结束时从源码、实际矩阵、完整车队、对偶/投影、参数与费用做一次额外独立读回：

- Q 是否真为同一有界物理子系统，原 penalty/physical domain 未改变；STOCK 是否是公平直接基线。
- 完整 endpoint hull、旧 moment 链接、退化区间及整数保持是否成立；是否误把连续端点当成真实车队。
- 是否以自由原 J 最优值判断增量；未决 LP、固定点 infeasibility 和历史裸 OLD 增益是否被混称。
- 投影是否只消掉新列，保留必要原物理项；实际加载系数/单侧补偿、作用域继承和 bound transport 是否合格。
- 新核心是否 C++，实际启动身份/参数是否相符，正式臂是否自付 source/H/helper 且只有一个 deadline。
- 结论是否对应实际已启动样本，费用/失败是否完整；建议是否重复 R62、R138、R143–145、R153 或 R156。

有独立审查 agent 时可分数学/实现、实验/费用两类，记真实身份；同一 agent 的验证脚本不冒充独立人员。修复改变结论的问题或收缩结论；不为非关键格式问题重复科学实验。不要求结论必为正，但必须解决本轮核心能力问题或明确保留真正未决原因。

产出集中 `results/unified_exact_round162/`；C++ 遵循 include/src，编排/独立验证用 `scripts/round162_*` 或小型共享 adapter。文件可合理合并，至少包括：实际完整 goal、历史增量表、Q/产品数学与登记、source/build/runtime/input 身份、新资格、能力/投影/搜索结果、原始日志/完整路线、对偶与数值补偿、费用失败、decision/RESUME、条件完整面板、适量研究文字、最终复核和 publication/recovery/cleanup。

正常 commit/push，创建**英文 Open Draft PR**，建议标题：

`Round162: test full physical completion of shared Gini products beyond stock RLT`

PR 先说明具体缺口、实际完成的研究与结论，再写关键验证和费用。按 A 的实时依赖选择 main 或 R161 stacked base，读回 base/head/Open/Draft 与证据链接。无需等前序合并；不自动 merge、force-push、删除分支。负结果按正常研究流程提交，更新当前研究导航的简短入口。

只打包本轮必要新增证据，旧材料以 fixed commit/member/SHA 引用。做一次有限新增公开恢复检查，不全历史空根重放，不为了核对重跑旧 solver。科学快照、实测 PE 与后续 delivery metadata 分开；商业 DLL、许可证、凭证不发布。恢复能力如实说明，不用公开不存在的二进制声称可直接复现原 Windows 运行。

若没有新增正式稳定 GI-TBC/B 或 Plain Gurobi 样本，历史主比较 CSV 保持不变。本轮 S/F/C、E+STOCK/PC 均另表；完整作用域的研究调用不自动等于主线 benchmark。若确有符合原 schema 的新正式数据，再按原身份/去重规则更新相应表。

交付后沿用 WORKSPACE_POLICY/R122 的有界 metadata screening。只清理本轮已结束、可重建且实际恢复覆盖的重复临时对象；保留唯一科学证据、失败、运行依赖、用户修改和活动 worktree。旧轮删除不在任务内。记录实际动作与观察到的空间变化，零删除允许；不更改全局 app/proxy/model/credential/权限设置。

## H. 固定来源、复用接口与文献归属

定位入口如下，不是必须执行的 producer 清单：

- R161：[PR #223](https://github.com/yifanXovo/TailoredExact/pull/223)，fixed science `fcd83fdf4d8980cbfdd6a860d5fe44fb7aa98158`；`results/unified_exact_round161/` 的实际 goal、final_report、decision、bridge、matrix/model identities、LP_product_diagnostics、envelope_diagnostic、费用及 measured manifests；`docs/round161_native_rn.md`。
- R161 新载体 `new_evidence.zip`：48720855 bytes、2035 members、SHA256 `cc6fb46ef1c5e34de6d28e928241a4bcd3df5ffe392cfe90ab27f751378d680d`。按 member 读取；不默认完整展开约 518MB 原始模型。
- R138：`results/unified_exact_round138/mathematical_analysis.md`、final_report 和 STOCK qualified implementation；R62 的 `results/gf_passive_threshold_conflicts_round62/`；R132/R133 joint-structure/math；R143–145、R153、R156 对应数学与 final_report。以本地研究索引定位固定科学身份。
- R160：[PR #222](https://github.com/yifanXovo/TailoredExact/pull/222)；已有 own-H/source 身份及完整对照/费用骨架。仅恢复当前缺少的 parent/source，不解压大量旧 K20 临时叶文件。
- `src/Round161NativeRN.cpp`：仅复用 actual matrix/registry 框架，不能沿用删除目标块逻辑。
- `src/CplexBaseline.cpp`、`src/IntervalRowFactory.cpp`、`src/ConnectivityFlow.cpp`：原物理 writer、STOCK 与真实有限界。历史 Cplex 文件名不意味着需要另建求解器。
- `src/PaperExternalGiniTree.cpp`、`src/GurobiBaseline.cpp`、`src/MipStartMapping.cpp`：once-root source、作用域/Native/Start；复用 R144/R104 的经过验证的有限对偶投影原则，新增本轮变量登记。
- `docs/paper_s2_release.md`、`docs/current_mainline.md`、`config/gi_tbc_round137.json` 与 R133/R134 修复；E+ 为现行 R154 proof-only + R156 RN16384 配置。

基础理论归属，结合实际使用内容准确引用：

1. Balas (1985), *Disjunctive Programming and a Hierarchy of Relaxations for Discrete Optimization Problems*, SIAM J. Algebraic Discrete Methods, [DOI 10.1137/0606047](https://doi.org/10.1137/0606047)：有限多面体并的扩展凸包框架。
2. Sherali & Adams (1990), *A Hierarchy of Relaxations between the Continuous and Convex Hull Representations for Zero-One Programming Problems*, SIAM J. Discrete Mathematics 3(3), 411–430, [DOI 10.1137/0403036](https://doi.org/10.1137/0403036)：乘约束与再线性化的既有方法。
3. Sherali, Adams & Driscoll (1998), *Exploiting Special Structures in Constructing a Hierarchy of Relaxations for 0-1 Mixed Integer Problems*, Operations Research 46(3), 396–405, [DOI 10.1287/opre.46.3.396](https://doi.org/10.1287/opre.46.3.396)：利用结构选择乘法因子的既有背景。

最终清楚区分：**数学条件有效、相对 STOCK 的新信息、有限压缩是否保留信息、完整算法是否值得付费。** 在这条明确研究线上做到有结论；不要用重复审计替代实验，也不要用更多熟悉机制替代一个已经没有增量的对象。

