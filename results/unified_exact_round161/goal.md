/goal

# Round161：在原物理模型上，以 RN 替代 Gini 乘积目标表达，检验完整归一化模型的求解价值

## 0. 本轮目标与执行原则

继承已完成的 R160。本轮只研究一个主机制：**保留原 M-B/VD-P 的库存、服务、路线、载荷与时间模型，用 reciprocal normalization（RN）成为 Gini 部分的唯一精确表达，替换旧 shared-G product 系统；首先用完整作用域的单个 Native MIP 检验这种表达。** 原惩罚项、物理验证与精确性合同继续沿用。

本轮问题不是“RN 能否再增加一组更强的 root cuts”，也不是“把 R160 的局部块放大到全部站点”。要回答的是：在相同物理载体、相同原目标和合法作用域上，从 `G×state` 改为 `t×state, t=1/S`，是否能改变有用的松弛、整数搜索与证明进展，形成值得继续研究的完整求解方式？

**不预设 RN-only 比原模型更小或 LP 更强。** RN-only 相对于 R143 的 old+RN 避免双套完整目标表达，但相对于原 VD-P 核心，辅助变量大致是一对一替换。两个基本 LP 在原 selector/G 投影中也不普遍支配。实际增量必须由同物理模型对照、尺寸/系数分析、原 J 的物理解与合格 lower 支持。

总科学实验容量为 **24h=86400s**，不是最低消费时长。先完成一个真实可运行的 C++ 模型与有实质搜索量的有限对照；允许在同一表达机制内作一次有证据的主要修订。根 LP 不更强不能单独终止研究，根 LP 更强也不能单独证明完整收益。没有竞争信号时保留完整负面结果，不为用满预算启动另一套机制。

论文目标是一般定义、整数等价、松弛关系和完整成本证据。**不按实例名称、历史胜负、预设规模档、机器型号、CPU 速度或内存大小切换算法；不采用“运行若干秒后改用另一机制”的策略。** 输入的合法支持、库存守恒、系数和当前合格 incumbent 可以用于数学传播；总 deadline、离线实验窗口与退出保存 margin 是资源合同，不是策略选择规则。

稳定 GI-TBC/B（S2/ms2）的正式入口与默认保持。E+ 是增强参考，保留既有 RN16384 / R154 proof-only floor；R160 物理邻域保持关闭。本轮新增独立、默认关闭的研究入口，暂名 **N-RN**。它使用全改进域的 Native branch-and-bound，不自动继承外层 GI 分裂器，也不增加 S/t 分裂器。原裸 CLI 的 ENS-C 兼容默认不等于 GI-TBC。

**新增反复执行的算法核心与正式性能候选全部使用 C++。** 包括目标块替换、RN 构建、Start 映射、新 callback/解码与在线验证回传。复用当前 C++/Gurobi 接口与编译政策，不顺便更改优化级别、fast-math、数值容差或原生参数。Python 可用于编排、离线分析和独立核验；两完整臂共同的历史 E+ helper 可以保持同版本、逐臂付费。有限 Python 原型不能代替最终 C++ 性能证据，也不要求为统一语言重写全部旧框架。

默认 Gurobi Seed=0、Threads=1；完整臂 own-H seed=20260626。Native 参数继承当前合格 PaperTerminalMip 合同（当前正式 MIPFocus=0），不要把 R160 局部 MIP 的 MIPFocus=1 搬成新正式默认。开发与正式调用逐次保存实际参数。

## A. 工作起点、最新事实与有限历史排重

工作入口：`E:\codes\ExactEBRP-work\worktrees\paper-current`。检查适用 AGENTS.md、WORKSPACE_POLICY.md、远端状态、用户修改和活动进程，为 R161 建立隔离 worktree。保护 `E:\codes\ExactEBRP` 和已有论文/研究树；新增 worktree、build、raw、archive、temp 与 restore 都放在 `E:\codes\ExactEBRP-work`。

2026-11-11（UTC+8）审查时的身份如下，执行时刷新：

- 仓库 `yifanXovo/TailoredExact`；R160 为 Open Draft [PR #222](https://github.com/yifanXovo/TailoredExact/pull/222)，未合并。
- R160 branch：`codex/round160-physical-neighborhood`；delivery head：`53e5c62fbcf6bc24898b7d5d3ecb755e4331ab0b`；fixed science：`695ea68caad088a54ebed45b7d49360d12bd0e8d`。
- R160 base：`codex/round159-joint-quantity-ownership`，head `51473276867e802ce729aae3d4a2563ea23a8fe8`；main 仍为 `b2b940c1e517a72e226ec60fc49ff19651737632`。
- R160 实测 production source：`d1da99b85219f4f0a1b5a703fc6ebf1c6dee4431`；实测 off/on 共用 PE SHA256：`dd39a3671c114a9e60d1d169bf6ffb533595f1a632cdd5876fe03f08d0e4da08`。
- R160 独立研究 v3 PE SHA256：`4616ea0d018a7f78989b3e5ad64a2e8dc3decba47f46ed4061b2c2c0b3381eb5`。后续工程构建不冒充这些性能样本。
- Gurobi 13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

若 main 已吸收依赖，从 main 开始；否则从核实后的 R160 head 建立 stacked 分支，Draft PR base 用 R160 branch，无需等 #222 合并。若已有 R161 实际工作，则接续并去重，不重开同轮。源码、实际启动 PE/DLL、科学快照与 delivery metadata 分开记录。

先读 R160 实际 goal、final_report、complete_comparison、trajectory、decision、cost 与新 C++ 核心，再按下表最小回看。形成一张“已有结果—本轮区别—待回答”的表即可；不恢复全部旧载体、不重跑旧 producer。

| 历史 | 已经完成的内容 | 对本轮的约束与增量 |
|---|---|---|
| 早期 formulation snapshot | 考虑过 Charnes–Cooper/整数缩放；当时等价与覆盖未落实，完整替代未落地；S 枚举仅有有限研究 | 不能声称从未考虑归一化；本轮以未缩放 binary selector 和连续乘积给出明确完整表达 |
| S-bucket / adaptive S-refinement / dominant S-bucket | 有完整 S 覆盖、bucket-tight envelope 与合格合并；局部桶证明不等于整个父域证明 | 改称 mean 或 t 不构成新维度；本轮不自动重开分母分裂控制器 |
| R62 | `U_control/U_archive` 分离、passive 物理见证与完整 proof handoff | 被动保存不是新主机制，不为 R160 重做 archive 框架 |
| R96 / R97 | 数量/次序物理优化、后期 Native 整数路线改进、OFF/SHADOW/FEEDBACK；微小 callback 开销仍可伴随完整回退 | 改调用时机本身不是充分的新研究问题 |
| R98–100、R135、R138 | 等价整数 formulation、M-B 与 state linkage、VD-P/VD-J/AP 的不同 LP/搜索影响 | 同 carrier 对照必须保留原 e penalty；不能悄悄加入 state-unary penalty |
| R143 | RN 叠加旧 G-product 系统，root 有增益，完整结果混合 | 本轮移除被替代目标模块，研究 RN-only；不把旧“交集更强”移用于替代 |
| R144 / R145 | RN 或联合 RN source 投影到一行，旧矩阵保留，完整结果不足以推广 | 本轮不是另一行投影或新 cut budget |
| R152–156 | inventory objective/hull 与物理模型分离；E+ 以同域 scalar floor 做 proof-only 消费 | 复用合格 floor，不追同一资源标量的小数位，不免费载入历史证书 |
| R157–159 | 低价资源库存、物理实现障碍、全车队 UNKNOWN 与 quantity/owner 资源块 | 本轮库存与完整物理路线在同一个 MIP 中选择，不再事后补救一个预选低价 Y |
| R160 | parent-containing 物理联合邻域、完整原 J、宏段压缩、八臂自付完整对照；正式表现回退 | 不增大 block/node/pass 作为本轮主任务；不把 `B=all` 当作同原 physical carrier |

归一化与二元乘积线性化有成熟文献，本轮不将其本身声明为原创。潜在论文价值在于：本 BRP 的完整整数等价、与原 G-product 的具体松弛关系、原物理载体上的可解释差异，以及是否值得形成一种完整方法。有限排重是为了避免重复，不设置独立综述工程。

## B. R160 的阶段结论与本轮真正要改变的对象

R160 的 C++ 物理域有效，已得到以下 own-H 调用点改善：

| 角色 | parent J | 局部最终 J | 接受事件 | 离线一轮 outer s |
|---|---:|---:|---:|---:|
| RX35 | .4246498451636405 | .4016200111731245 | 12 | 40.9668595 |
| NB35 | .5772179446388801 | .4900715637577154 | 22 | 65.6695970 |

两来源各完成 35 个 anchor；512→2048 节点的唯一统一修订虽然增加局部 OPTIMAL 数，两个完整 pass 的末态反而更差。它改变了后续 parent 与子问题，不能推导“同一个子问题多给节点更差”，但已否定直接扩大该容量的当前收益。

同 PE 的完整结果为：

| 角色 | E+ physical U | E+R physical U | E+ proof L | E+R proof L | 关键结论 |
|---|---:|---:|---:|---:|---|
| RX35 | .2996694007364017 | .37504347522524073 | .2360521029074557 | .2360213085176433 | U 显著回退 |
| NB35 | .450291503262878 | .4540598501089633 | .3959564087240911 | .39594377133602443 | U 回退 |
| K20 | .7168065462777502 | 相同 | .7051912783201926 | .705130725827833 | 无 U 收益 |
| RX20-T1 | .6453250303858205 | 相同 | 达到 U | 达到 U | T_cert 21.937043→36.606473s |

新增在线局部成本约为 RX 41.47s、NB 65.61s。对保存的 off 轨迹保守截去这段尾部时间，仍可保留 off 最终好解；RX/NB 首次达到相应最终 U 约在 4002.329s/1370.469s。这是只读截尾诊断，不是新反事实运行，也不能分解 Start、cutoff、scope、presolve 或分支搜索的因果份额。它说明不能把全部回退只归于少搜索了几十秒。局部 solve_outer 占约 98%，删除少量输出/构建也没有足够的量级依据。

R160 科学实耗 22022.35697s（约 6.12h），两个来源、一次修订、匹配控制和八个完整臂均已执行；36h 是容量，不是未完成的剩余任务。保留数学构造与负面证据，默认关闭是正确阶段决策。

本轮转向**被求解的完整数学表示**，不是继续向旧搜索器提供更早的不同 incumbent。仍由数据决定它是否值得发展；不宣称修改表示必然消除 Native 路径敏感性。

## C. 完整 RN 表达、同域合同与关键数学结论

### C1. 保留原物理载体和原 penalty，只替换 Gini 目标模块

使用原 M-B/VD-P 的全部实际库存、路线、唯一服务、方向、载荷、连通性、顺序、原 T 与回仓卸载语义。保留原变量类型，尤其不要同时把连续 p/d 或 vehicle-state 变量改成 binary。沿用 pair-only 物理支持与已合格原变量强化，不引入新的 route-flow/MTZ formulation。

记站点数 n，实际载入系数 `c_i=1/D_i>0`，合法库存支持 `D_i^Y`，binary one-hot 为 `x_iy`，原库存为

\[
\sum_{y\in D_i^Y}x_{iy}=1,\qquad Y_i=\sum_y yx_{iy},\qquad
S(Y)=\sum_i c_iY_i,\quad A(Y)=\sum_{i<j}|c_iY_i-c_jY_j|.
\]

原目标（S>0）为

\[
J(Y)=\frac{A(Y)}{nS(Y)}+\sum_i\alpha_i|c_iY_i-1|.
\]

`alpha_i=lambda*weights[i]` 以实际接口为准，若某导出字段已包含 lambda 则不再乘一次。**模型保留原 r_i/e_i、r_i=c_iY_i、e_i≥±(r_i−1)、现有 e 上界及目标 `G+Σ alpha_i e_i`。** 不用 `Σ_y alpha_i|c_i y−1|x_iy` 替代 e；后者整数等价，却引入另一种 LP penalty 表达，混杂本轮比较。若当前实际配置存在额外 penalty 行，两臂一致保留并注明。

优先复用 `writeCanonicalCompactModel()` 的合格 root LP 和现有 Native backend，用一个小 C++ adapter 显式替换目标块，无需重构整个 writer。按实际登记的列、行及依赖建立清单，不以宽泛名字正则删列后假定语义正确：

| 部分 | 处置 |
|---|---|
| route/load/p/d/z/m/conn/ord、Y/r/e/state、A/B、原 T、activation、物理 pair 支持与原类型 | 共用，两个 formulation 逐项一致 |
| 原 objective、cutoff、penalty floor、e/Y 域、required movement | 保留其合格原变量表达 |
| 当前仅含 r 的 centering/band 行 | 在相同完整 root scope 下原样共留，不因为推导涉及 G 就全部删除 |
| `state_g`、`zprod`、透视/重构、旧 Gini epigraph | 显式替换 |
| 专用于旧目标的 unscaled `h_ij` 及 h-dependent cap/floor/spread/estimator | 随模块移除，或证明等价转写后使用；不得直接改名为 normalized h |
| `W_SP` 等被影响辅助 | 按实际消费者闭包处理，记录保留/移除原因，不牵连无关物理行 |

目标模块包含哪些旧强化必须明示。因此“同 physical carrier”指物理变量/约束与声明的共同原变量行相同，不表示两种目标松弛的信息完全相同。本轮首版采用最小、清晰的替换，不逐项追补所有旧目标 cut。若一项旧行保留，则确认它在新 epigraph 的正确 completion 上合法，且没有留下悬空或重复乘积系统。

### C2. 正分母分支与整数精确性

在声明作用域内证明 `0<S_L≤S(Y)≤S_U`，取向外包络的

\[
t_L\le 1/S_U,\qquad t_U\ge1/S_L.
\]

引入连续变量 t、w、归一化库存 `Yhat`、归一化差值 a；G 沿用原 objective epigraph：

\[
t_L\le t\le t_U,\qquad
t_Lx_{iy}\le w_{iy}\le t_Ux_{iy},\qquad
\sum_yw_{iy}=t\quad(\forall i),
\]
\[
\widehat Y_i=\sum_y yw_{iy},\qquad
\rho_i=c_i\widehat Y_i,\qquad \sum_i\rho_i=1,
\]
\[
a_{ij}\ge\rho_i-\rho_j,\quad a_{ij}\ge\rho_j-\rho_i,\qquad
\sum_{i<j}a_{ij}\le nG.
\]

保留 binary x，不将整数 Y 或 route 变量缩放后仍宣称整数。x 为 one-hot 时，未选 w=0、所选 w=t，故 `rho_i=t*c_iY_i`，归一化推出 `tS=1`，G 的最小合法值恰为原 Gini。反向将任意合法正库存物理路线、真实 Gini 和最小 e lift 进 RN。给出这个双向整数/目标保持证明；不声称辅助变量必须唯一，也不以 Native OPTIMAL 代替代数证明。

S 界来自合法支持、原库存守恒与 fleet return 界。可复用 R143/R140 的 support 与总库存 box relaxation、实际 binary64 系数的精确求和和向外取整；不从某个好解的 S 或观察到的搜索区间猜界。原总库存必要范围是 `max(0,B−ΣQ)≤ΣY≤B`，其中 B 为初始总库存，不是累计 pickup 上限。完整 handling 为 `(tp+td)*P`，P 可以超过 Q。

若支持有空洞，使用包含它的 box 求界仍有效，但不能把 box 当成新的整数支持。实际 duration 沿用已修正的 `sqrt(dx*dx+dy*dy)/1.5` 与当前单侧数值政策，不混回旧 reader。

### C3. 零库存一般情形不能被 RN 遗漏

若原作用域结构上排除 S=0，记录证明并直接使用 C2。否则 S=0 因 c_i>0 等价于所有 Y_i=0，按原约定 G=0，目标 `J0=Σ alpha_i`；物理可行性仍由原模型决定，不因“库存为零”推断路线可行。

优先用一个明确有限 disjunction，避免把局部 R160 的 positive-only 状态冒充全域。以下单模型构造可作为通用实现：引入 binary `z0` 表示零库存，用合法总库存上界 B_U 和正库存分支的 t_L/t_U，加入

\[
1-z_0\le\sum_iY_i\le B_U(1-z_0),\quad
t_L(1-z_0)\le t\le t_U(1-z_0),
\]
\[
w_{iy}\ge0,\quad w_{iy}\le t_Ux_{iy},\quad
w_{iy}\ge t_L(x_{iy}-z_0),\quad \sum_yw_{iy}=t,
\]
\[
\sum_i c_i\widehat Y_i=1-z_0,\qquad 0\le G\le G_U(1-z_0).
\]

其余 normalized pair 行不变。z0=0 恢复 C2；z0=1 推出 Y=0、t=w=0、G=0，原 penalty 给出正确 J0。证明整数域对应，检查所有仅在正分母下成立的辅助界/行已条件化或移除。正分支本身为空或 B_U=0 时直接处理零域，不计算非法倒数。四个正式角色是否需要这个 indicator 由数学域决定，不按名字指定。

也可复用已合格的正/零两个分支实现，但必须保留完整 union coverage：未关闭零域不能消失，正域 lower 不能单独充当全域 lower。对 `J0≥own U` 的逻辑覆盖，沿用精确比较/包络和 inclusive 边界政策；仅“数值很接近”不关闭分支。不要求为实际已排除的零域增加一次 MIP。

### C4. RN-only 与旧 LP 的关系及真实模型尺寸

用小型精确算术读回以下两个 objective/stock 子块见证，或发现问题后给出修正。它们不是完整路线实例，也不需要新 solver 长跑。

1. **RN 允许而旧基本块不允许的点。** 两站 c=(1,1)、支持 {0,1}、`1≤ΣY≤2`，固定 `x_11=1/2,x_21=3/4`。取 `t=3/4`、两站 `w_i1=1/2,w_i0=1/4`，RN 有 `rho=(1/2,1/2),G=0`。旧块的原差值至少 1/4，而每站 `zprod_i≤G`，故旧 Gini 行要求 `1/4≤2(zprod_1+zprod_2)≤4G`，即 `G≥1/16`，且这个界可达。
2. **反方向采用 R143 已存三站例。** c=(1,1,1)、支持 {0,1}、`1≤ΣY≤2`、one-state mass `(1,1/2,0)`，旧块可取 `G=1/3`，RN 要求 `G≥5/12`。核对旧见证的全部声明条件，不把它说成新发现。

这说明两种基本表达在 selector/G 投影上互不支配；不能直接推为任意完整物理 LP 的 strict separation。保留共同 penalty 后，同 selector 的 e 可共用，不因 penalty 改写制造差异。R143 的 old+RN 交集以及 TC/stock 反例作为背景，不再安排新的 cut 组合网格。

若 K 为库存状态数、p=n(n−1)/2，旧基本目标约有 K 个 state_g、n 个 zprod、p 个 unscaled h；RN 约有 K 个 w、n 个 Yhat、p 个 normalized a 及一个 t。因此精确统计实际 rows/cols/nonzeros、变量类型、系数范围与 presolve 后尺寸；若使用消元，给另一表达相同代数整理机会。**不把相对于 old+RN 的缩减包装成相对于 main 的缩减。**

### C5. 为什么先用完整 Native 域，而不照搬旧 GI 分裂

原 GI 划分直接缩小 G×state 乘积的共同因子范围。RN 的共同因子变为 t，G 区间可以间接影响库存/分母，但不再直接缩小这些新乘积的 t envelope。因此本轮先使用完整初始改进域的一个 Native MIP；不同时研究 AM/分裂/target/restart 的重新设计。

构建本臂 own-H 给出的 `U0` 对应合法 inclusive scope，完整 true-G 改进域可用 `[0,min(U0,(n−1)/n)]`，原 penalty 非负，`J≤U0`。G 上界按现有单侧/向外数值政策实现，D 的 OLD/RN 共用完全相同的界；不能把这一合法全局收紧只给 RN。遵守 R133 的 inclusive 修复；不恢复“floor 接近 cutoff 就人为加 infeasible 行”的 shortcut。

代码上可保留 `CanonicalCompactModelSpec.interval_restricted=true` 以满足 M-B writer，**这里范围就是完整 root**；`incumbent_epsilon=0`。构建后走 `FixedIntervalSolveKind::PaperTerminalMip` 或等价完整 Native 接口，关闭本候选外层 AM、bound-target、split 和 restart；正式候选也不继承开发 NodeLimit。原 E+ 臂仍正常执行自己的 GI 算法。

完整 Native 求解的 raw bound 要经过现有 source/parameter/model/scope/witness qualification，再按 cutoff complement 转成全域界。例如模型覆盖完整 `J≤c` 时，合格 restricted lower ℓ 对应 floor `min(ℓ,c)`；两个不交分支先按 union 取 min，同域独立 floor 再取 max。最终与物理 U 按原 proof 合同合并。若实际证据矛盾，则停止消费该来源；除非其余独立合格来源已经闭合原 gap，否则保留 OPEN。不将 R160 的局部无效性接口直接改名为 global certificate。

## D. 一个有限、可归因的 C++ 实现与真实对照

### D1. 小量新接口资格后立即进入实际模型

新增资格只针对替换：旧/新物理块与声明共同原变量行一致；新旧 Start 对应同一完整车队；原 J/penalty 正确；positive/zero coverage；未遗漏旧行依赖。新 LP/MPS、model/domain fingerprint 与行列 registry 按替换后的实际模型生成，不沿用原 root 矩阵身份。复用现有 route mapper、Evaluator 和 R133/R134 资格，不再搭一套全项目审核框架。

现有 `MipStartMapping.cpp` 已识别 `rn_t/rn_w_/rn_Y_/rn_h_`，优先扩展这个映射。核对它在零分母情形的处理，不假定 R143 positive-only 接口已覆盖 zero。每个进入 incumbent 的新路线都按原 T、原系数与完整载荷重新验证。

用少量可穷举 tiny positive/zero 问题验证原目标最优值与物理可行集对应，再读回 RX35/NB35 两个真实 own-H parent 的完整 Start。无需重复 R160 已合格的宏段与邻域资格，本轮没有使用其物理 carrier。

### D2. 同 carrier 的 OLD / RN 比较

在 RX35、NB35 两个研究来源上，使用与拟正式调用点一致的 H/R83 后 parent，建立 **相同输入、原始 parent、支持域、原 J cutoff、physical/common rows、Native 参数与 Start 语义** 的 OLD 和 RN。可复用身份完整的旧 own-H 作为离线开发输入，明确标注不是完整性能样本；正式阶段每臂重新支付 H。

OLD 使用原目标系统；RN 按 C1 的明确替换表。两者都在完整 root scope 直接 Native 求解，不把一个 GI 多叶算法与另一个单 MIP 称为 objective-only bridge。对保留/移除的 objective-strengthening 行如实登记；观察归于整个声明的目标块替换，不声称只有一个系数发生变化。

默认开发工作如下，四个 MIP 调用构成首轮，不另设多 Seed/节点/设置网格：

| 对照 | 数量 | 工作容量 | 回答的问题 |
|---|---:|---|---|
| matched continuous LP | 2 来源 × OLD/RN | 每模型最多 300s，能合格结束就结束 | root bound、尺寸、系数与求解成本；未完成记 UNKNOWN |
| matched Native MIP | 2 来源 × OLD/RN | 统一 NodeLimit=4096，每调用 outer 总上限 900s | 实际 U/L、integer search 与 costs；限时者明确保留 censoring |

开发 MIP 不以节点数相同冒充工作量或时间相同；同时报告 Work、nodes、Runtime 与全部外层成本。保存 U/L 随时间与 Work 的进展、首个/最佳 verified U、root gap、实际节点/中断原因。从已有 fractional LP 解离线记录 t 区间与 `rho_i−t*c_iY_i`，以及 OLD 对应的 `zprod_i−G*Y_i`；这些用于解释乘积松弛，不新增 Optimize 或据此直接作因果结论。root LP 若已经在同一有资格来源里完成且可明确复用，不再重复付费；否则按表独立调用。

新物理见证记录完整 Y/owner/routes、原 J、原 T 的逐车时间与载荷。Native bound 与 global transported floor 分列。RN 若改善来自不同库存/活动集而非路线搜索，也要从真实解解释；仅看 root gap、模型列数或 MIP 节点数不足以作完整性能结论。

### D3. 至多一次同机制修订，不设置自动救援方向

首轮后只选择一个有明确证据的实现/表达问题处理，例如真实可消元的重复行、过宽但可合法收紧的 S 界、可解释的系数缩放/传输问题。所有来源采用同一规则，先写修改理由，再重做受影响的有限对照。修复真实 bug 不计配方选择，但失败与费用保留。

只做一致且目标保持的数值整理，不能通过不对称改 tolerance、penalty、presolve 或 MIPFocus 制造 formulation 收益。若旧专用强化的删除被证据指向为关键，可以将**一个有一般推导的等价/有效转写**作为唯一主要修订，并在结果中区分 RN-core 与修订版本；不进行逐行回加组合筛选。

不追加 R160 大块/多 pass、R62 archive、R97 后期反馈、assignment master、rank cut、另一套物理 flow 或 S/t 分裂作为必做后备。若实际数据暴露明确分母 envelope 瓶颈，可在结论中提出下一轮应检验的命题；仅“t 是新的乘积变量”不够成为第二阶段分裂工程。

首轮 LP 较弱但 U 搜索有实质进展，仍可继续；LP 较强但 Work/费用/物理解全面不利，不因 LP 漂亮而强制进入长面板。若两个来源经过有意义的整数搜索仍无可用 U/L 进展、成本明显不利且没有具体可修正原因，交付范围明确的负面结果。不能因一个 node-zero 启动问题就宣称数学方向无效，也不需先证明必胜才允许真实实验。

## E. 冻结一个完整候选，检验相对 E+ 的实际价值

当 D 提供值得检验的实际物理 U、合格证明进展或可说明的成本/搜索折中，冻结一个 **N-RN**：自身 H/R83 → 同源原 root carrier/既有 proof-only helper → 完整 RN 物理 MIP → 原验证与 proof 输出。只选一个版本，不按角色在 OLD/RN/GI/R160 间自动分派。

两完整臂都保留本臂自付的现有 RN16384 inventory proof-only helper。它继续读取各自 own-H 形成的合格原 root carrier，不要求理解新 RN routing matrix；N-RN 在同一 carrier 上替换目标模块。确认原 helper floor 覆盖完整改进域后，才与新合格全域搜索界取 max。floor 不进入新 native 行、hint、Start、branch 或动态 cutoff，不另开“floor placement”研究。若适配遇到实际困难，先说明并解决这个小范围 contract，不能免费复用 R160 历史 floor。

N-RN 的新解可以按 Native 正常 incumbent 机制缩小搜索；不因每次 U 改善重建外部模型、重新运行 H 或重复 helper。初始 scope 以 U0 固定并保持合法覆盖；没有原证明支持的附加行不自动消费。Native 返还与最终证书使用同一声明的原 J 合同。

用同一生产构建的独立 E+ / N-RN 入口优先形成 fresh 对照；若确需不同 PE，记录实质源码差异、共同编译条件和实际启动身份。冻结配置、版本与顺序后串行执行：

| 角色 | 算法臂 | 每臂生产总窗口 | 目的 |
|---|---|---:|---|
| R-X35-S-T2 | E+ / N-RN | 7200s | 主要困难来源的完整竞争力 |
| N-B35-S | E+ / N-RN | 2400s | 第二来源、相同一般规则 |
| K-20-S | E+ / N-RN | 1200s | 物理与库存 bound 差、潜在证明收益 |
| R-X20-S-T1 | E+ / N-RN | 1200s | 快获证场景的完整额外代价 |

八臂名义窗口合计 24000s=6h40m；如沿用 cap+900 的监护预约，保守预约 31200s=8h40m，属于 E 阶段 10h 容量，**不是算法额外时间，也不是已经发生的费用**。每臂只有一个生产总 deadline，包含 H、scope、旧 helper、模型转换/构建、全部新旧 Native 调用、在线验证与回传。事后必要验证单列 `T_verify`，`T_total=T_produce+T_verify`。

先执行两个研究来源的 pairs。若一个候选在两来源出现明确全面不利、没有继续确认价值，可停止余下 pairs，报告实际 partial；保留所有已启动结果。若声称四角色完整确认，必须执行四组，不用只读 R160 off 替代 fresh E+。不看完一个正式 pair 后改候选再混为同一面板；确有实质 bug 则明确作废范围与实际重跑费用。

这里 E+ 与 N-RN 的完整差异包含 objective representation **和外层控制方式**，不能将完整胜负全部归因于 RN 单一表达；D 的 matched whole-native bridge 提供有限的目标块归因。也不能把 N-RN 称为 Plain Gurobi：它仍使用本项目物理强化、自己的 H 和合格 proof-only 组件。

正式输入身份沿用 R160：

| 角色 | V/M | Q | 物理 T | lambda | 输入 SHA256 |
|---|---|---|---:|---:|---|
| R-X35-S-T2 | 35/3 | 20,25,30 | 6300 | .0754049775127276 | `c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2` |
| N-B35-S | 35/3 | 20,25,30 | 7200 | .15 | `80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98` |
| K-20-S | 20/2 | 30,30 | 5400 | .15 | `d1a65be4b87dead2ae351068ece3c3ce486a51c93652d778e055f2684606ea42` |
| R-X20-S-T1 | 20/2 | 30,30 | 4800 | .12676060979965992 | `2b467b5bb1e650a4c1e792e808dcf9575bcc76752fe378e16c838015344ddac6` |

这四例 pickup/drop 均为 60s，代码仍读一般 tp/td。物理 T 与实验运行窗口分开。复用 R160 的八臂身份/费用骨架后，为 R161 新建 matrix/admit/loop，隔离 OUT/TEMP/预算与新 reader；不直接运行旧 R156 九臂 freeze/admit，也不沿用 R160 的 own-H→local→scope 消费链假设。

报告 actual physical U、raw/qualified/proof L、absolute/relative gap、T_total/T_cert、root 与 Native 的 Work/nodes、各组件费用和中断原因。无证书时 T_cert 为空；`certificate_qualified` 若仅表示报告状态合格，不能当成 certified=true。当前四角色/一个 Seed 只能支持对应有限判断，不自动授权稳定推广、独立确认或“稳定胜过 P-GRB”。

本轮不自动扩多 Seed、宽 P-GRB benchmark 或常规 GI-TBC/B 桥接。若没有新的正式稳定 GI-TBC/B 与 P-GRB 数据，就不改历史主比较 CSV；E+ / N-RN 与研究子问题另表保存，不能换名追加。

## F. 科学容量、停止判断与论文内容

| 阶段容量 | 秒 | 小时 |
|---|---:|---:|
| 有限复用、数学接口与新增资格 | 7200 | 2 |
| C++ 表达实现后的模型/真实 matched 试验 | 14400 | 4 |
| 一次定向修订与有限机制分析 | 10800 | 3 |
| 条件完整候选面板及必要验证 | 36000 | 10 |
| 最终科学读回 | 7200 | 2 |
| 失败与证据驱动调拨余量 | 10800 | 3 |
| **总科学容量** | **86400** | **24** |

容量可按已见证据在总量内调拨，留简短理由；不要因 E 未进入而自动发起另一项长查询。普通代码编写、编译与文档不计为 solver 科学费用，但记录实际编译/I/O 等成本；新增 LP/MIP、H/helper、科学核验、失败与恢复中的科学计算都按外层实际调用计一次。nested Runtime、Work 与 callback validation 用于分解，不重复加账。

计时实验、编译和大规模 I/O 串行，防交叉干扰。R161 的 meter、launch reservation、OUT/TEMP 与 cost_report 都使用 86400s；旧 helper 通过隔离 adapter 重定向，不能带回 129600/172800 等旧轮预算或改写历史账。临近容量上限时保存可解释结果与失败，不启动无法留下可用记录的调用。

最终必须回答：

- 完整 RN 与原物理问题的整数/目标对应是否成立，S=0 与 cutoff 外部如何覆盖？
- 保留、移除、转写了哪些旧目标信息；penalty 与 physical carrier 是否真正共用？
- 两种 LP 的非支配见证、实际尺寸和系数状况说明什么，不能说明什么？
- matched whole-native 下，RN 的 U/L/Work/时间进展与 OLD 有何区别？
- 若进入完整面板，相对 E+ 的净效益如何，哪些变化只能归于整个方法组合？
- 是否有具体、可证伪的下一步结构问题，还是应在当前表达上停止继续投入？

更新一份适量的数学/算法研究节即可，围绕“原物理载体—RN 整数等价—旧/RN 非支配—完整 Native 方法—实测结果”组织。准确引用 Charnes–Cooper、二元乘积线性化及公平性优化文献。不要把两个小反例或一次新 formulation benchmark 单独宣称已达到 OR 级原创；它们用于找准后续理论与算法问题，也不应因基础工具已有文献就拒绝实质研究。

不默认要求独立四页论文、多份 PDF 或重写主论文。若实质修改 TeX，按现有流程编译和检查实际输出；负结果也要清楚保留命题、作用域、已付研究与合理停止理由。文档数量不代表研究完成质量。

## G. 一次额外复核、完整交付与本地条件

新接口小量资格完成后推进科学工作，不为每次求解添加审批。最终从保存的源码/模型、完整路线、参数、原始日志和费用做一次独立读回，重点检查：physical/common block 是否一致、penalty 是否被暗改、正/零覆盖、旧行依赖与单位、Start/原 J、bound scope、单 deadline、失败/费用完整性。

如有独立审查 agent，可分数学/实现与实验/费用复核，记录真实身份；同一 agent 的独立脚本不冒充独立人员。修复会改变结论的问题，或收缩对应结论；非关键格式错误不重跑科学实验。检查下一步建议是否重复 R62/R97、R143–145 或旧 S-bucket，不把一次失败自动转成另一个已知方案。

产出集中在 `results/unified_exact_round161/`。C++ 遵循 include/src 布局，编排/验证使用 `scripts/round161_*` 或小型共享 adapter。文件可合并，至少保留：实际完整 goal；历史排重与增量；数学/模型块说明；source/build/runtime/input 身份；新增资格；模型/Start/路线/日志与进展；失败与关闭费用账；decision/RESUME；条件完整结果；适量论文内容；最终复核、publication、有限恢复与 cleanup。

正常 commit/push，创建**英文 Open Draft PR**，建议标题：

`Round161: evaluate a full physical RN objective reformulation on the existing carrier`

PR 先写具体缺口、完整表达、有限实际结果与结论范围，再写必要验证和成本。按 A 的实时依赖选择 main 或 R160 stacked base；读回 base/head/Open/Draft 与载体链接。无需等待前序 PR 合并；不自动 merge、force-push 或删除分支。负面结果按正常研究流程交付。更新当前研究导航的简短 R161 入口，保留历史身份。

只打包本轮新增必要证据，旧材料以 fixed commit/member/SHA 引用。做一次有限新增公开恢复检查，不全历史空根重放、不重新求解旧模型。科学快照、实测 PE 与后续 delivery commit 分开，避免为写入自身 head 无限追加提交。商业 DLL/许可证/凭证不发布；实际运行依赖与可用本地恢复链如实记录。

交付后沿用 WORKSPACE_POLICY/R122 的有界 metadata screening 和安全清理。只清理本轮已完成、可重建且被 carrier/manifest/实际恢复覆盖的重复临时对象；保留唯一科学证据、失败、必要运行时、用户修改和活动树。旧轮删除不在本轮授权内。记录实际动作、保留项、字节估计与观察到的空间变化；零删除允许，不更改全局 app/proxy/权限/model/credential 设置。

## H. 固定来源与优先复用接口

以下是定位入口，不是 producer 执行清单。优先用本地合格副本，缺失时最小恢复：

- R160：[PR #222](https://github.com/yifanXovo/TailoredExact/pull/222)，science `695ea68caad088a54ebed45b7d49360d12bd0e8d`；`results/unified_exact_round160/` 的 goal、final_report、complete_comparison、trajectory_analysis_v1/v2、revision_decision、candidate_manifest、cost_report、carrier_manifest、final_review；`docs/round160_physical_neighborhood.md`。其 9 个本轮 zip 合计 108654294 bytes，164880 members；按具体问题选择性读回，不完整解压大量 K20 artifacts。
- R143–145：`results/unified_exact_round143/mathematical_analysis.md` 与三个 final_report，`include/Round143Research.hpp`；用现有研究索引定位对应固定科学身份。R143 证明/反例与分母界可复用，附加式入口不能冒充本轮替代模型。
- 原物理/目标 writer：`src/CplexBaseline.cpp`、`src/IntervalRowFactory.cpp`；实际 C++ 入口虽沿用历史 Cplex 文件名，当前完整 Native 调用仍走合格 Gurobi backend，勿据文件名重建求解器接口。
- Native、scope、Start：`src/GurobiBaseline.cpp`、`src/PaperExternalGiniTree.cpp`、`src/MipStartMapping.cpp` 及其现有 headers；优先复用完整 root/PaperTerminalMip 与 RN 名称映射。
- E+：R154 proof-only、R156 RN16384 与 R160 八臂脚本/manifest。当前稳定定义见 `docs/paper_s2_release.md`、`docs/current_mainline.md`、`config/gi_tbc_round137.json` 及 R133/R134 修复。
- 历史排重：`results/gf_passive_threshold_conflicts_round62/`、`results/unified_exact_round96/`、`results/unified_exact_round97/`；早期 `gf_tailored_bc_formulation_snapshot_round`、`gf_tailored_bc_s_bucket_strengthening_round`、`gf_tailored_bc_adaptive_s_refinement_round`、`gf_tailored_bc_dominant_s_bucket_round`、`gf_tailored_bc_structural_policy_round`。以实际目录/索引为准，不因缺一份旧辅助文件恢复整批历史。

文献只用于准确归属，不是本轮性能依据：

1. Charnes & Cooper (1962), *Programming with linear fractional functionals*, NRLQ 9, 181–186, [DOI 10.1002/nav.3800090303](https://doi.org/10.1002/nav.3800090303)，[CMU 原文](https://iiif.library.cmu.edu/file/Cooper_box00010_fld00009_bdl0001_doc0001/Cooper_box00010_fld00009_bdl0001_doc0001.pdf)。
2. Yue, Guillén-Gosálbez & You (2013), *Global optimization of large-scale mixed-integer linear fractional programming problems: A reformulation-linearization method and process scheduling applications*, AIChE J. 59, 4255–4272, [DOI 10.1002/aic.14185](https://doi.org/10.1002/aic.14185)。其公开摘要说明 CC 与 Glover 线性化结合；未取得全文时不冒充已核对全文定理。
3. Chen & Hooker (2023), *A guide to formulating fairness in an optimization model*, [DOI 10.1007/s10479-023-05264-y](https://doi.org/10.1007/s10479-023-05264-y)，[作者稿](https://johnhooker.tepper.cmu.edu/equityGuideAOR3post.pdf)，Gini 部分与线性化附录。

最终区分：**完整数学表达有效、matched formulation 行为、完整方法净收益、未来结构研究的条件。** 对一个明确的新问题做足量而有限的实验；以证据决定继续、修订或停止，不让重复审核或自动后备机制替代本轮研究。
