# Aggregate endpoint-CDF inequality: proposed additional diagnostic

Status: Astra derivation independently reviewed below; numerical validation remains pending. This is a diagnostic proposal, not an implemented or promoted algorithm. Use the notation and integer-state assumptions of ot_mathematics.md.

For each endpoint layer e in {a,b}, all stations have the same nonnegative layer mass theta_e. If theta_e>0, couple every station through one common uniform variable U and its normalized layer quantile Q_i^e(U). Every pair then attains its one-dimensional optimal-transport cost simultaneously. There is a finite atomic realization using the union of all cumulative-probability breakpoints. For theta_e=0, the layer contributes zero and needs no normalization.

Combining the two endpoint layers reconstructs every s_i, q_i and the common G. Consequently, in the isolated all-station state/product block, the minimum expected Gini numerator H is the sum over pairs of the B2 endpoint transport costs. This extends the isolated-block interpretation beyond separate pair proofs. It does not impose routing, inventory conservation or the original G=H/(nS) relationship on every atom and hence does not prove the full model's integer hull.

Let w=b-a>0 and choose any signs alpha_ijl,beta_ijl independently for the two endpoint CDF differences. Write

R(s,q)=sum_{i<j,l} Delta_ijl [(b alpha_ijl-a beta_ijl) A_ijl +(beta_ijl-alpha_ijl) B_ijl].

The pair inequalities imply w sum_{i<j} h_ij >= R(s,q). The existing Gini row n sum_i zprod_i/D_i >= sum_{i<j} h_ij therefore implies the valid aggregate inequality

n w sum_i zprod_i/D_i >= R(s,q).

At an LP point, choosing each sign from its endpoint CDF expression maximizes R over this family. One aggregate row thus separates the projected total-numerator inequality at that point without adding a row for every station pair. This may reduce matrix growth; it does not establish faster separation or solve time. At a=b use the analogous ordinary-CDF aggregate inequality n sum_i zprod_i/D_i >= sum Delta sigma A, not division by w.

This aggregate family need not replace all pair inequalities in the actual ENS formulation. h variables also appear in other generated rows (some conditional), including CplexBaseline.cpp at the original admission lines 1356,2204,2211,2234,2479,2488,2519,2532,2581,2793,3004,3070,3091,3130,3634. Further analysis is required before claiming equal full-model projection or lower-bound strength. Initially retain the original model and compare this family as an alternative/additional diagnostic arm.

Scope and numerics: all supports, endpoint bounds and signs must match the immutable source LP; B2 rows remain local to the generating interval and compatible inventory domains. Accumulation and coefficient cancellation must be verified against direct high-precision evaluation; narrow intervals use reliable row scaling without altering solver tolerances. A violated aggregate row at a fractional point is not itself a performance result.

Required independent checks: all-pair quantile-coupling construction; integer-point validity; independent tiny multi-station convex-combination oracle; a fractional strictness example; direct per-pair sum versus emitted aggregate coefficients; actual-model row audit; same-source fixed-LP comparison of base, pair B1/B2 and aggregate B1/B2 with complete diagnostic costs.

## 独立审查（Sol，2026-09-26）

**结论：所述聚合行在生成它的共同局部区间内有效；共同分位数论证也成立，但只确定隔离块的总成本下边界，不证明完整 ENS 模型或全部 `h` 向量的凸包。** 设端点层 `e` 的站点边际质量均为 `θ_e`。若 `θ_e>0`，将各站按库存比率排序、把边际除以 `θ_e`，收集所有站点归一化累计质量的断点 `0=v_0<⋯<v_K=1`。对每个开区间 `(v_{k-1},v_k)`，取各站在该区间的分位数库存状态，生成质量 `θ_e(v_k-v_{k-1})`、`G=e` 的一个联合原子。断点属于哪侧不影响质量；零质量层不生成原子。各站边际因而恰好复原。对任意站点对，这个联合耦合的投影是同序分位数耦合，达到一维 `W_1`；任何联合耦合的每一对成本又不低于其 `W_1`。故一个有限原子组合**同时**达到所有对的最小距离，总和恰为各对端点运输成本之和。此处应将 `H=∑_{i<j}h_{ij}` 理解为可调上图变量的最小总值；不能由总值结论推断任意给定 `h` 向量的完整凸包。

可手算例：三站 `D_i=1`、库存支持均为 `{0,2}`，`a=0,b=1,G=1/2`。两层质量各 `1/2`。`a` 层的三站分布依次为 `0`、`(0,2)` 各半、`2`；`b` 层依次为 `2`、`(0,2)` 各半、`0`。共同分位数给出四个质量均为 `1/4` 的原子：`G=0` 时 `(0,0,2),(0,2,2)`，`G=1` 时 `(2,0,0),(2,2,0)`。各对期望距离为 `1,2,1`，故 `H_min=4`；三个 `s_i` 却都在 `0,2` 各取半，普通 B1 总下界为零。这里 `q_1(2)=1/2`、`q_2(0)=q_2(2)=1/4`、`q_3(0)=1/2`，所以 `zprod=(1,1/2,0)`；聚合 B2 行为 `3(1)(3/2)=9/2≥4`。这些端点原子只用于隔离状态/乘积块，其中 `G=0` 的异质库存原子不满足完整 Gini 行，正说明不能把该构造当作完整模型凸包证据。

聚合代换须逐对、逐段分别取 `α=sign(bA-B)`、`β=sign(B-aA)`：每一符号行有 `(b-a)h_{ij}≥Δ[(bα-aβ)A+(β-α)B]`，求和后用真实行 `n∑_i zprod_i/D_i≥∑h_{ij}` 即得 `n(b-a)∑_i zprod_i/D_i≥R`。对 `a=b`，因 `q=a s` 且上述行退化为 `0≥0`，必须直接聚合 B1：`n∑_i zprod_i/D_i≥∑_{i<j,l}Δ_l σ_{ijl}A_{ijl}`；其右侧取最优符号时为全部对的 `W_1` 之和。真实源码的 `h` 还出现在 Gini 限值、桶/局部及其他条件行，因此删去各对切割仅留聚合行可能改变实际 LP 投影；“每次只需一条行”是该总成本不等式族的分离性质，不是整套模型等价或速度结论。

**局部作用域反例：** 三站 `D_i=1`、整数库存 `(1,1,2)`，真实 `H=2`、`S=4`、`G=H/(3S)=1/6`，故 `n∑zprod_i/D_i=2`，满足原 Gini 等式。错误地将子区间 `[a,b]=[1/2,1]` 的聚合 B2 用于这个父域合法点，两个非零距离对各有 `A=±1,B=GA`，每对右侧为 `|1-G|+|G-1/2|=7/6`。聚合右侧 `R=7/3`，左侧 `(b-a)n∑zprod_i/D_i=1`，竟删去合法点。故行必须带生成叶的 `G` 域与完整库存支持身份；父叶、兄弟叶或扩宽支持后的 LP 不能复用。独立微型枚举/运输 LP 应核对四原子的边际、三对同时最优、聚合系数逐项等于各对求和，以及该反例只在错误复用时违例；真实固定 LP 的根界与成本仍须另外诊断。
