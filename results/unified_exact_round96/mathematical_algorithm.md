# ENS-C / LP-G：完整数学链与本轮限定

身份：ENS-C 是保护默认，LP-G 是默认关闭的 R90 研究候选。本稿不是晋升决定。R96 外部确认拟复用 R90 二进制 `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`（源码 `a71bd53ca412e9b9e529e7237446687d360a94ce`）；R95 HEAD 不是该构建源码。以下当前行号针对 R95 HEAD，其与冻结R90相关实现的差异须在实验身份审计绑定。原始详细依据为[R91底稿](../unified_exact_round91/paper_algorithm_blueprint.md)、[R92有限性](../unified_exact_round92/controller_termination_note.md)、[R90分点](../unified_exact_round90/method_delta.md)。本稿逐项补足LP-G的控制有限性，不以旧稿的ENS结论代替。

## 1. 原模型与整数对应

站点库存整数 $0\le Y_i\le C_i$、正目标 $D_i$、非负权重 $\omega_i$、$\lambda\ge0$。车辆空载出发，一站最多一车一次非零单向操作；$Y_i=b_i+\sum_k(d_{ki}-p_{ki})$。每条路线每个前缀满足 $0\le\sum(p-d)\le Q_k$，不限制整条路线累计pickup。允许带载返仓，余车完整卸载。因此

$$t_k=\sum_{(i,j)\in R_k}t_{ij}+c_p\sum_i p_{ki}+c_d\sum_i d_{ki}+c_d L_{k,end}
=\sum_{(i,j)\in R_k}t_{ij}+(c_p+c_d)\sum_i p_{ki}\le T.$$

车辆可以空路线；站点总库存可下降。Evaluator验证仓库起讫、唯一访问、操作、整数库存、载量、时长和完整原目标，而不是只检验代理函数。

$$r_i=Y_i/D_i,\quad S=\sum_i r_i,\quad H=\sum_{i<j}|r_i-r_j|,$$
$$F(Y)=G_{true}(Y)+\lambda\sum_i\omega_i|r_i-1|,\qquad
G_{true}(Y)=\begin{cases}H/(nS)&S>0\\0&S=0.\end{cases}$$

非负比率使 $S=0\Rightarrow H=0$，且 $0\le G_{true}\le(n-1)/n$。原compact以路弧、操作、载量、时长、连通及整数库存表达物理域；P-GRB严格使用plain原compact，无VD-P、启动或额外行。ENS/LP-G以相同物理域为基础静态强化。

叶域 $[a,b]$ 内VD-P用库存one-hot变量 $s_{iy}\in\{0,1\}$，$\sum_y s_{iy}=1$，$Y_i=\sum_y ys_{iy}$，以及

$$a s_{iy}\le q_{iy}\le b s_{iy},\qquad
G-b(1-s_{iy})\le q_{iy}\le G-a(1-s_{iy}),\qquad \sum_yq_{iy}=G.$$

整数时恰有 $q_{iy}=Gs_{iy}$。令 $z_i=\sum_y yq_{iy}$、$h_{ij}\ge\pm(r_i-r_j)$、$e_i\ge\pm(r_i-1)$，加

$$n\sum_i z_i/D_i\ge\sum_{i<j}h_{ij},\qquad \min G+\lambda\sum_i\omega_i e_i.$$

这是Gini上图：$S>0$时只推出 $G\ge G_{true}$，不能把任意叶点的G认作真实Gini。反向嵌入：若物理解的真实Gini落在该叶，取 $G=G_{true}$、真实绝对值和对应one-hot，得到同目标整数模型点。S=0在含0的叶取G=0。其它叶中同库存可能只能以更高G存在，故全域覆盖是下界证明必要条件。

## 2. 静态强化与启动的实际范围

ENS-C采用R67起的VD-P、F0连通流、已有compact约束及K1/AM-SF静态强化（`PaperK1AmSf.cpp`）。时长/库存/路由有效行只缩小松弛、不能排除原整数物理解。支持时长子集rank≤3、最多50,000个，实际按车辆及子集枚举顺序截断，存在选行顺序偏置；本轮不改政策，也不从未经测试的顺序解释性能。domain_propagation_mode=iterative、rounds=2是配置字段，canonical writer实际完成数至多1，不能称执行两轮闭包。所有使用cutoff派生域的行都依赖当次已验U及模型域，不可携带到本轮独立固定路线诊断。

启动保持24个随机解码下降起点加1个独立构造，随后原R76/R83物理闭包。top-8/top-6仅限定声明的guided复合邻域，不穷尽全邻域。严格目标改善在有限路线/整数库存状态中有限；中性移动保持库存及目标，严格降低排序后的车辆时长向量的字典序势，亦无循环。这不是全局最优或多项式复杂度证明。全程截止可提前保留最好已验解；此时不称邻域穷尽。A1/A2、OT/B1、H-ACT及R93/R95独立模块都不加入本轮LP-G配置。

## 3. 全局下界、cutoff与证书

原物理已验上界U定义当前cutoff $\kappa=U$（当前路径epsilon=0）。所有真实Gini不超过 $\min(U,(n-1)/n)$ 的可能改善解由初始根覆盖；$F>\kappa$的外区域由cutoff自身提供下界。每个保留或有有效终态的最终区域j给合法 $B_j$，则安全表达式

$$L=\min\{\kappa,\min_jB_j\}\le F^*\le U$$

来自两种情况：$F>\kappa$，或 $F\le\kappa$ 可按真实Gini嵌入至少一个覆盖叶。不可行叶取正无穷；被原子替换的父叶不能重复计入，已闭分支也不能无理由忽略。源码scheduler保留相关最终叶界，实际不逐字计算上式；epsilon=0且覆盖/叶界正确时其相关叶最小值有效。不能将旧较紧cutoff的区域界当新较松域的界。

verified incumbent只严格下降；epoch更新丢弃父LP/G/子缓存及模型，保留有集合包含依据的历史有效下界。只有物理验证、完整前沿覆盖、作用域/模型身份、界单调与原数值证书门禁共同成立才报认证。global L绝不来自受限LP或固定路线诊断的单个native bound，亦不跨算法拼接。

## 4. 控制器、AM与LP-G

每次选择控制全局界的开放叶，求当前完整最优LP；frontier规则可以先发严格更高的其它叶界作为数学target。允许lookahead时，深度<8、宽度>1e-4+1e-12才提分点，否则请求终端原生MIP。先完整求两子LP，再处理双侧/单侧不可行、无严格子增益、AM阈值或父MIP目标。不可行收缩及二子分裂均原子替换，证据不完整时父域继续覆盖。

令 $D=\max(U-B,\epsilon_{cert},10^{-12})$、$g_j=clip((B_j-B)/D,0,1)$、$\eta=\min(g_L,g_R)$、$\mu=(g_L+g_R)/2$。AM以 $\eta\mu+\epsilon_{score}\ge0.08$ 接纳即时分裂；若 $\min(B_L,B_R)\le B+\epsilon_{cert}$ 则先请求父终端MIP；否则低AM以同一个 $\min(B_L,B_R)$ 为父MIP数学target。无内部秒数/Work份额。AM接纳时的gap条件收缩不能证明成本或无截止收敛；depth/width保持原值。

LP-G唯一变化：同域、同epoch、同canonical SHA的合格完整最优父LP给有限严格内点 $\bar G$ 时用 $p=\bar G$，否则原中点。写出两个共享同一double端点的闭区间 $[a,p],[p,b]$，逐值核严格内点和相等端点，再做覆盖检查。身份失配是失败停止，不偷偷回退或重求。父G是模型上图变量。

对固定父点且统一行尺度，

$$\Phi_L(p)=\sum_{i,y}(\bar q_{iy}-p\bar s_{iy})_+,\quad
\Phi_R(p)=\sum_{i,y}(p\bar s_{iy}-\bar q_{iy})_+,$$
$$\Phi_L(p)-\Phi_R(p)=\sum_{i,y}(\bar q_{iy}-p\bar s_{iy})=n(\bar G-p).$$

左量不增、右量不减，故合格 $p=\bar G$ 平衡两侧并最大化较小违反量；共同值为 $\frac12\sum|\bar q-\bar G\bar s|$。结论仅针对这个父点和统一尺度；不保证其它最优LP点被排除、严格提升子界或改善完整MIP时间。

## 5. LP-G无无限重排的逐项核验

前提：有限物理实例；每个被启动的完整LP/MIP调用最终返回被接受的终态，或全程截止/工程失败停止运行；模型与账本操作有限完成；strict verified incumbent改进来自有限整数路线状态。结论是控制调度有限，不是native运行时间上界。

1. 有限epoch：只在已验目标比U小超过1e-9时增长epoch。有限离散状态排除无限增长。一个实际树深度≤8、二子/单子原子替换不复活父ID，固定epoch的实际树至多511个ID。LP-G没有中点减半性质，本证明不使用该性质。
2. 固定epoch父点稳定：`solveLp`在lp_complete且lp_epoch相同时直接复用（当前`PaperExternalGiniTree.cpp:3711`）。G由该次完整LP返回保存（3776起），不会随parent native bound变化重选LP最优点。6290起在消费前核当前域、artifact epoch、磁盘SHA、LP SHA/域；helper确定性地选同一G或同一中点。因而同epoch的分点稳定，不靠浮点状态有限。
3. 同epoch子证据稳定：6443起仅在c6_children_ready时复用，6455起逐子核ID/父ID/索引/深度、精确域、LP/artifact epoch、最优或不可行终态、SHA及磁盘。失配失败终止，不产生无限重新求解。6718起将完整children缓存；native child target重排（7568起）不清缓存。复用提升child.lower_bound的继承项，但AM实际继续读runtime[child].lp，不改变缓存LP目标t。
4. target成功是离散进展：native有效界先合并 $B'=\max(B,b_{native})$（4130附近），成功谓词 $b_{native}+tol\ge t$（4195起）。下次同子LP给相同t，$B'+tol\ge t$触发无严格增益并请求terminal（1070起）。不需要下界每次增加固定正量。frontier target仅能成功一次，因为c6_frontier_milestone_reached置true后不在同叶复位（4204）；即使两类target交错也有限。
5. epoch失效：ensureArtifact在3580起丢弃旧backend/artifact、LP/SHA、G可用标记、children与terminal标记。同叶可在新epoch重新进入，但epoch数有限。frontier标记未被清除，不会增加无限路径。旧域同ID模型不能绕过LP-G身份门禁。
6. terminal启动在固定epoch至多一次（8618检查、8633设置）；OPTIMAL/INFEASIBLE与工程门禁闭合，否则截止/失败停止。非控制叶重排只能由本次新LP提升改变排序；稳定缓存不能反复在同状态提升界造成无限自环。

因此最后一个epoch内有限ID、有限新LP和阶段标记、稳定child目标与terminal门禁阻止无限重排。真实原生调用若永不结束，证明前提不成立；全程截止给unknown，不是认证。提案、子LP结果、target达到、请求terminal、原子分裂、最终证书必须单独计数。R94 C20/U6无实际分裂也可改变parent target，所以不能把所有时间差归因于树小。

## 6. 数值边界与待绑定项目

本项目采用binary64和Gurobi数值证书，零请求gap不等于严格有理证书。旧writer `addTerm`删去绝对值≤1e-12项，`writeExpr`把距±1≤1e-12的系数打印为±1；R92仅修复H-ACT新行，不能扩写为任意实数物理忠实。固定路线诊断的新writer只省去精确0，所有非零系数17位打印，绝不省略近1系数。

本轮六输入为整数库存/目标/容量、六位正权重、三位坐标、整数T及60/60处理时间。此输入约束排除了near-unit处理系数与极小原目标权重，但不能单凭输入范围宣称所有derived leaf行无近零项：分点/界来自求解器。外部正式准入仍需实际原compact参考导出、目标/时长系数检查与派生行数值作用域记录；如果发现影响拟测模型正确性的差异，必须独立最小修复并对三臂共同重冻。本稿不提前声称该待核项目已通过，不修改容差。

## 7. 新诊断与未来候选的独立身份

[固定路线协议](fixed_route_protocol.md)覆盖可删零、可翻向、多站协调、实际压缩旅行的全部数量域。其最优/下界只限R，不能证明原问题全局最优。125库存微型枚举同时检验物理和模型映射（包含删点、方向反转及S=0代数状态），原六见证全部映射通过；一次Gurobi微型结果与枚举最优一致。实际长尾结果、后续有限邻域原型与端到端对照另记，不将诊断时限机制直接纳入算法。
