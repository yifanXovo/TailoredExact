/goal

# TailoredExact 下一轮完整任务

## Round153：量化完整整数目标上图的价值，检验统一下界增强

**日期：2026-11-04（Asia/Shanghai）。建议 Round153；编号已占用时沿实际下一轮继续。**

## 0. 本轮目标、自由度与计算容量

R152 的离线理论、oracle 和有限表达研究可以验收。它完成三域强参考、完整自由 LP、稀疏支持/补集定价、八行循环和全状态整数 RN 深化；没有生产、H 或完整 B/J。851.596856299 秒是程序计算及必要验证，不是总研究墙钟。没有花满 24 小时本身不是欠完成，但这些有限行结果尚未量化整个整数目标上图的潜力。

本轮主问题是：**在同域完整模型及相关旧强化中，整个硬资源整数 Gini-completion 上图还能提高多少界，主要困难是信息不足、方向/放置、定价还是整体耦合？**先利用已存证据排除简单原因，再通过完整 LP 与库存列耦合，取得有意义的强化值上下区间。另给已有便宜 scalar floor 一个有限的统一算法转化机会。

新增实验计算容量 **115200 秒＝32 小时**。主要投入整体价值定界与有依据的深化；可在总额内调拨、调整实现和域、提前以充分证据完成。无需花满，也不以固定八轮/六次方向用完替代研究结论。关键区间仍宽、预算充裕且有可执行改进时，应完成一轮针对性深化，再判断本阶段边界。

允许辅助模型、新变量、必要局部重构和不同实现路径。算法保持统一、数学依据明确，不按实例名、大小、历史输赢打补丁，不以运行 k 秒触发内部方法切换。离线诊断可以有正常时间上限；生产停止和调度以数学误差、有效界、支配或确定性状态/迭代规则为依据。允许普通取舍，不要求每例全胜或绝对历史最佳。

稳定 R137 GI-TBC 保持。默认 **Gurobi Seed=0、Threads=1**；进入完整算法时 H seed 独立为 **20260626**。计时实验串行，与编译、重 I/O 和 PDF 操作错开。沿用 R134 证明/数值资格，对实际新增问题定向处理，不重开已通过的 tiny-gap 工程。

---

## A. 起点、身份及本轮已有事实

| 项目 | 编写时核实的参考 |
|---|---|
| 仓库／最新 PR | yifanXovo/TailoredExact；#214，Open Draft，未合并 |
| R152 branch／head | codex/round152-resource-integer-objective；ed058861e5eb094bc22d468a71a791bf558b51ac |
| R152 fixed science | d489ec2948f079105e4532a2e06ae4eed9fcd500 |
| 临时 base | codex/round151-standalone-penalty-propagation；c6e930ffcb84f0c3801c651f28b5f7e8e2062f33 |
| 编写时 main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 稳定方法／配置 | R137 GI-TBC；scripts/paper_s2.py；config/gi_tbc_round137.json |
| R137 fixed science | e735c3447eb1443713c700942d873de1783a4a26 |
| 未改的生产 source／PE SHA | c26382d9bf1d4edde538a01c62e57ba563cf865c；fbdd7c2ece5c748e086761f2490fd901ccdaeffa29df357d2d98fd8743e1dc39 |
| Native DLL／SHA | D:\gurobi1302\win64\bin\gurobi130.dll；9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88 |
| 活动树／新增资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议 branch／目录 | codex/round153-coupled-objective-hull；results/unified_exact_round153/ |

先读适用 AGENTS.md、WORKSPACE_POLICY.md，检查实际 refs、用户修改、活动进程和保存证据。main 已吸收则从实际 main 继续；否则从核实后的 R152 继续并选择相应临时 base，不等待合并或机械回退旧 SHA。

R152 的执行 goal 与已布置的 31,133-byte 文件完全一致，SHA 为 71ca757d1c6ae1f82bd7d63319ad6445040c6893dc022a1e21a8ce41b2dd3007。独立外部审查通过全部 42 个完整 LP 保存记录（41 新＋1 复用）、274/274 调用、52 个发布定价/156 个库存 upper、43 份串行费用记录，以及 4 包/2072 成员。另 8 个覆盖资格 fixture 单列，不混入性能样本。无需重跑这些旧资格。

### A1. 三域真实结果与未回答部分

| 域 | 复用 B | R152 旧强参考含 RN | 最后新界 | 实际来源 |
|---|---:|---:|---:|---|
| N-B35-S | .3278337721771161 | .38673718656544753 | .3929789535186393 | 零势整数目标 floor；后续 residual row 无额外自由 LP 增量 |
| K-35-U | .20017766194929548 | .2788356429814587 | .27883564298145824 | 旧 RN 覆盖早期微增量，最后一条行无可区分根增量 |
| N-C20-U | .048357676071 | .17446526778483834 | .17473288430246972 | 全状态支持行，增量 .00026761651763138 |

这些是初始完整自由 LP，不是完整算法终端 L、物理 U 或获证时间。

- 八行循环从 strongCP2 出发；最终全状态对照重新从 strongRN/RNfloor 出发，每域只加入一条合格新行。旧八行尚未并入最终 RN 链，不能称“RN 上八轮已无用”。
- strongRN 含 RN 和两条 scaled-stock，尚未包含 R145 的 NC1、NC2、TS1–TS4。原报告已限定参考范围；补这六条是有针对性的历史排重，不推翻旧结果。
- AP 后主要保存最优点的 Pe−H_AP 在浮点零附近。不能将“惩罚 slack 吸收信息”当作已观察的失效原因。
- N-B35 零势 floor 的 LB/UB 为 .3929789535186394/.39604654895666136，6 个 bin 调用，outer 36.253653 秒。它与 R151 同角色终端 B 下界 .3892791982096647 的比较只是优先级线索，不是新完整收益。
- K35 零势以 strong=.274861988699 为阈值，库存 UB=.232944743509 已足够早退，0 次 MIP 调用；这尚未回答相对纯 B=.200177661949 的 floor 潜力。N-C20 零势库存目标近零。

---

## B. 先复用信息，再建立准确的旧强参考

### B1. 有限且必要的 R145 对照

保留 R152 同域原 B、AP/GD/stock/count/common-factor/RN 和原 cutoff、所有原变量与旧行。核查 R145 的六条适用旧联合行及其有限界，缺失时按现成生成器与实际当前域补入。

若旧 count aggregate 为
\[
A\ge b+\sum_{iy}k_{iy}s_{iy},
\]
同一 reciprocal factor 的 NC 为
\[
\widehat H\ge bt+\sum_{iy}k_{iy}w_{iy}.
\]
NC1 与 NC2 各自保留，不能无条件只留后者。

令 \(\tau=\sum_iY_i,\ \widehat\tau=\sum_i\widehat Y_i\)，
\(L\le t\le U,\ B^-\le\tau\le B\)。TS 四式为
\[
\begin{aligned}
\widehat\tau-L\tau-B^-t&\ge-LB^-,\\
\widehat\tau-U\tau-Bt&\ge-UB,\\
\widehat\tau-U\tau-B^-t&\le-UB^-,\\
\widehat\tau-L\tau-Bt&\le-LB.
\end{aligned}
\]
它们不是 R152 两条 \(B^-t\le\widehat\tau\le Bt\) 的改名。按实际作用记录有限 caps；加入 NC 后不能自动沿用纯 RN “降低辅助绝对值即可”的冗余论证。无需构造全部历史 disjunction 的巨型全集。

### B2. 已有合格行的同域并集

恢复每域旧八条 lifted row、最终 full-support row、适用 scalar floor 及其完整 pricing/scope 资格，先形成合法并集，不重新发现或重定价相同方向。

对拟加的旧行、NC/TS 或等价变换，先检查现成合格完整最优点能否扩展且满足。若旧 lower 加该点已足以夹住同一最优值，记录零求解证据即可；否则才自由重优化。新的变量、原辅助量、g、s 等不能固定来制造增量。

至少形成清楚的“旧强参考—已资格行并集—必要改写—后续完整上图区间”证据链。旧 CP 最优点只有在对当前 RN/NC/TS 全模型可行且处于所研究目标带时，才能充当当前最优面样本。

---

## C. 研究对象及可以复用的数学信息

### C1. 分解与域

沿 R152 实际支持、资源界、比率系数和权重，令
\[
\mathcal R=\{Y_i\in\mathcal Y_i:\ B^-\le\sum_iY_i\le B,\ G(Y)\le\gamma_U\},
\quad
f(Y)=\max\{\gamma_L,G(Y)\},
\]
\[
h_i(y)=\omega_i|c_i y-1|,\quad
H(s)=\sum_{iy}h_i(y)s_{iy},\quad
\phi(Y)=f(Y)+\sum_i h_i(Y_i).
\]
\(\omega_i\) 已含 lambda；\(\gamma_L\) 是模型 g 的下界，不能误作物理 Gini 下界。默认不另加目标 cutoff 到 oracle，支持若继承 cutoff 收缩则绑定该 scope。零状态按原合法条件纳入，f(0)=gamma_L。

给定兼容边际 s，
\[
\Theta(s)=H(s)+\Gamma(s),\qquad
\Gamma(s)=\min_{\lambda}\left\{\sum_Y\lambda_Yf(Y):
\sum_Y\lambda_Y=1,\ \sum_Y\lambda_Yv(Y)=s,\ \lambda\ge0\right\}.
\]
不存在共同分布时是投影不相容；存在后才讨论其最小期望 Gini。期望线性性与有限集对偶是已有理论，新意需要落在本问题的结构、非平凡比较、可计算性及实际价值上。

### C2. 直接 Gini 支持与现有 total row

R152 已资格的
\[
a\le\min_{Y\in\mathcal R}[\phi(Y)-\pi\cdot v(Y)]
\]
也满足
\[
a\le\min_{Y\in\mathcal R}[f(Y)-(\pi-h)\cdot v(Y)].
\]
故 \(\psi=\pi-h\) 给出独立有效行
\[
g\ge a+\psi\cdot s.
\tag{1}
\]
这是从定价恒等式推导，不是将两条不等式直接相减。与精确 AP 联用，(1) 推出相应 total row；反向一般不成立。实际浮点 AP 与行运输沿已有资格处理，保留旧 total 行即可避免把理想支配误当字节冗余。

scalar floor 对应原 \(\pi=0\)，即 \(\psi=-h\)。**在纯 B 的 APoff 载体上没有上述支配保证**，不能自动用直接 g 改写替换 \(g+P_e\ge L_{\rm floor}\) 并称等价。

先零求解检查已保存点；当前 AP tight 使不少有限改写可能无需新 LP。如果新旧完整模型值相同，准确解释范围，不强造放置收益。可在实际 Q 允许时研究 g 向上 completion 是否给出无损映射，但须核实 g 产品、Pe、cutoff 和全部附加行；不预设普遍等价。这项关系是低成本归因，不单独铺大实验矩阵。

### C3. 本次外部复核的新严格关系

外部审查已以 Fraction 复核 R152 三站原例，并扩展至旧 117 行＋RN＋scaled-stock＋R145 NC/TS：共 169 行、68 变量，原物理库存域不变。该结果尚不是 R152 PR 的已有主张，可按附件恢复、核对并归入本轮数学记录，不需新 Optimize。

仍取 n=3、\(c=(1,1/2,1/4)\)、\(\omega_i=1/8\)、支持 0..4、总量 2..5、\([\gamma_L,\gamma_U]=[0,3/4]\)，边际
\[
s_{11}=1,\quad s_{21}=3/4,\ s_{22}=1/4,\quad
s_{32}=s_{33}=1/2.
\]
唯一共同库存分布为 \((1,1,2),(1,1,3),(1,2,2)\)，概率分别 \(1/4,1/2,1/4\)；故
\[
H=3/32,\qquad \Gamma=161/1080,\qquad \Theta=1049/4320.
\]
强化旧参考在该固定边际的精确最小 \(g=1/9\)，目标 \(59/288\)，保留
\[
\Theta-59/288=41/1080>0.
\tag{2}
\]
一个达成扩展为 \(t=4/9\)，非零 w 为
\(w_{11}=4/9,w_{21}=1/3,w_{22}=1/9,w_{32}=w_{33}=2/9\)，
\(\widehat Y=(4/9,5/9,10/9)\)，
\(\widehat h_{12}=\widehat h_{13}=1/6,\widehat h_{23}=0\)。
原 state_g、zprod 从 g=1/10 的合法扩展按 10/9 缩放，其他原点保持。
固定边际下写 \(u=w_{22},v=w_{33}\)，归一化给 \(2t+u/2+v/4=1\)；
NC 给 \(\widehat H\ge1-3t/2\)，归一化绝对差给
\(\widehat H\ge3t-1\)。分别以 2/3、1/3 加权，得
\(\widehat H\ge1/3\)，故 \(g\ge1/9\)，上述点达到。

(2) 是固定边际的结构缺口，不是完整路由严格例。原 117 行例的 global-floor gap=1/480 不能随强化参考继承；新固定点甚至高于该库存域的全局整数最小值。亦不宣称覆盖所有历史 disjunction。

可将“硬资源排除一个 2×2 状态角点，迫使共同分布，形成最低期望 Gini”的结构概括为有限命题；有价值时扩展到一个解释性参数族。无需为了数量再生成小例或把一般凸分析换名。

---

## D. 主任务：与完整 LP 耦合，给整个上图的值区间

### D1. 完整对象

令 Q 为明确登记的当前完整自由 LP：保留原路由、装载、时间、目标、cutoff 和选定旧强化；每个比较使用同一个 Q。记 \(F(x)=g+P_e\)。主研究对象可取
\[
\begin{aligned}
z_\Gamma=\min\quad &F(x)\\
\text{s.t.}\quad &x\in Q,\\
&s=\sum_{Y\in\mathcal R}\lambda_Yv(Y),\quad
\sum_Y\lambda_Y=1,\quad \lambda\ge0,\\
&g\ge\sum_Y\lambda_Yf(Y).
\end{aligned}
\tag{3}
\]
所有原变量保持自由，\(\mathcal R\) 是完整已声明库存域，不是旧活跃状态集合。

可用 total-objective 版本 \(F(x)\ge\sum_Y\lambda_Y\phi(Y)\) 作必要归因；Q 含 AP 时，Gini-completion 版本至少包含该信息。只对会改变判断的域比较两者，不默认所有实验翻倍。理论包含关系与实际浮点资格分别说明。

(3) 保留原完整路由 LP，库存 oracle 只生成表示联合分布的列/有效下界；它不是 R105–107 的整数服务 master→路由 oracle 架构，也不替换物理解搜索。R104/R144/R145 的标准对偶与压缩思想可复用，其历史完整负面也保留。

### D2. 有限列主问题与上界身份

只保留合法库存列 \(K\subset\mathcal R\) 的受限主问题（RMP）是 (3) 的内限制。其合格可行解目标 \(U_K\) 给
\[
z_\Gamma\le U_K.
\]
**这是强化 LP 值的上界，不是 BRP 物理 U，也不能倒用成 BRP 下界。**其 x 仍可能有分数路线。

列的 f(Y) 用原库存真值重算。RMP 的 Gini-link 系数可向上安全写入，或复核/修复真值 completion，确保保存 primal 对真正的 (3) 仍给上界；pricing 仍面对真正 f，并支付相应数值运输。不能未校正地用两个不同列目标拼接上下界。

复用旧合法库存列、投影分布和有兼容 completion 的原物理 Start 启动。旧分布只证明边际可实现，不保证提高期望 Gini 后仍满足完整 cutoff/辅助关系。RMP 不可行时应补列、恢复有效启动或用 Phase I；不能据此判完整上图不可行。人工变量未消除前，不能用其目标作为正常 \(U_K\)。

### D3. 全域定价与合格下界

采用以下符号：
\[
\mathcal L
=F(x)+a(1-\sum_Y\lambda_Y)
+\pi\cdot(s-\sum_Y\lambda_Yv(Y))
+\beta(\sum_Y\lambda_Yf(Y)-g),\quad \beta\ge0.
\]
列的 reduced cost 为
\[
\rho(Y)=\beta f(Y)-\pi\cdot v(Y)-a.
\]
若当前 RMP 的合格 dual 目标为 \(D_K\)，完整域 pricing 给
\[
L_m\le m(\pi,\beta):=
\min_{Y\in\mathcal R}[\beta f(Y)-\pi\cdot v(Y)],
\]
则将凸组合截距降低
\(\delta=\max\{0,a-L_m\}\)，即可得到全域合法 dual，因而
\[
\boxed{
D_K-\max\{0,a-L_m\}\le z_\Gamma\le U_K.
}
\tag{4}
\]
修正只出现一次，因为 \(\sum\lambda=1\)。左端使用已资格 dual，而非直接把数值 primal ObjVal 当精确 dual。原 Q 的 dual/有限界残差沿现有方法处理；已资格外松弛 LP 下界可与左端取最大值。

可行库存给 reduced-cost 上界并用于加入列；只有全域 pricing 下界能资格化 (4)。保留负价格/负 reduced cost。\(\beta=0\) 是投影方向，仍需覆盖同一资源/Gini 域，不能跳过，也不能除以 beta。

R152 normalized integer oracle 可以改为目标 \(\beta f-\pi v\)，并复用 bin/DP 作下界、对照或必要加速。没有必要为这个目标另建一套数值框架。单一势的上下界、当前 RMP primal/dual、修正量与最终区间均保存，明确是主问题退化、定价未解还是列覆盖在限制进展。

实现可统一为 \(\beta f(Y)+\sum_i d_i(Y_i)\)：本段取 d=−pi，原目标零势 floor 取 beta=1、d=h。硬总量 DP fallback 为 \(\beta\gamma_L+\min_{\rm hard\ total}\sum_i d_i(Y_i)\)，合法零状态值为 \(\beta\gamma_L+\sum_i d_i(0)\)。不能在新 Gamma 定价中误留旧 h 项，或在 beta=0 时仍加 gamma_L。

### D4. 同时获得安全支持行

上述价格直接给
\[
\boxed{\beta g-\pi\cdot s\ge L_m.}
\tag{5}
\]
保留尺度，无需在小 beta 时相除。beta>0 对应 Gini 支持；beta=0 对应库存投影，两类收益分别归因。

实际写入 \(\widehat\beta,\widehat\pi\) 时，可按有限 g 区间和 one-hot 关系取
\[
\widehat L_m\le L_m+
\min\{(\widehat\beta-\beta)\gamma_L,
      (\widehat\beta-\beta)\gamma_U\}
-\sum_i\max_y(\widehat\pi_{iy}-\pi_{iy}).
\]
使用实际定价/写入系数身份并向安全方向运输。复用现有有限域补偿；不为已合格 tiny 差追求字面零。

RMP dual 的尺度不受 R152 人为 \(|\psi|\le.05\) 限制。可以规范化、删每站冗余 link、使用合适稳定化或多列返回，但最终资格仍面对完整 R。标准列生成/对偶修正是经典工具，论文贡献不在重新命名它们。

### D5. 多边际／最优面方法的角色

若采用多个点来寻找方向，它只是候选发现方法。对近最优目标带
\(Q_\varepsilon=\{x\in Q:F(x)\le z_Q+\varepsilon\}\)，
有效行的整面最小违反为
\[
\min_{x\in Q_\varepsilon}
[L_m+\pi\cdot s-\beta g].
\tag{6}
\]
合格 lower 严格为正才排除整个该目标带。有限样本的最小违反只是 (6) 的上界；全切样本不能代替整面判断。浮点实现用有资格余量的目标带，不把浮点 ObjVal 强制等式当精确最优面。

可选 (3)–(5) 的耦合方式或等价的完整面 adversary 方式，不要求同时实现两套完整系统。需能给整体价值的可靠区间或整面证据，而非再次只输出若干点违反。

---

## E. 分层实验、深化与研究终点

### E1. 先做小而有用的实现资格

使用已有完整小域/少量针对性有限域检查：RMP 上下界方向、缺列导致的不可行、负 reduced cost、beta=0、真实库存与全域价格、直接 g 及 coefficient transport。可用完整枚举的全列 LP 作小域控制。复用 R152 已通过的 oracle、零状态、非最小 completion 和源矩阵资格，新增测试只覆盖实际新接口。

### E2. 三域整体价值区间

优先延续 N-B35-S、K-35-U、N-C20-U，按 B 节先恢复有限强参考和旧行信息。初始目标是在至少一个主要困难域形成足以改变研究判断的 \(z_\Gamma\) 区间，再用其余角色识别结构差异；不是只追最容易出正例的域。

每域报告：

- 原 B、旧强参考、旧行并集及必要直接-g 结果；
- 全域 R、Q、库存列数量、RMP primal/合格 dual；
- pricing 的 lower/upper、修正量、累计上下值区间及费用；
- 投影兼容性与目标上图的贡献区别；
- 当前有用行放回同一完整 Q 后的自由 LP 值及构造成本。

旧合格行、库存列和矩阵可用于离线研究，不收取虚构旧费用；它们不能免费注入后续完整算法。复用 solver model/basis、合法库存候选和本轮价格信息来减少重复构造是允许的，全部新计算实际计费。

### E3. 给仍有价值的问题真正的深化空间

若区间仍宽，按瓶颈选择有根据的改进，例如：dual 稳定化/多列、whole-face 方向、R145 旧强化进入 pricing relaxation、分母或资源结构、模型复用、适用子域界继承、行/列聚合。先证明新限制必要，避免为了便宜而丢掉硬库存、Gupper 或原状态。

旧每域八行、每点六次 master、.05 半径只是有限探索设置；不作为本轮整体研究终点。可设正常计算上限管理流程，但预算仍充裕且主要区间未决时，不只因局部迭代数用完就结束。也不机械要求把每个域都解到相同微小 gap。

定界精度应足以区分研究主张，并高于继承数值不确定性；例如根据增量量级选择绝对 1e-5 至 1e-4 的目标，记录理由，允许调整。原 N-C20 增量仅约 2.68e-4，过宽区间不能认定它已被解释。若数值资格本身限制判断，如实给区间，不陷入无效 tiny-gap 整治。

有依据的终点包括：完整上图上界已接近已实现下界，剩余潜力有限；得到新的有价值全域 lower 并定位实现成本；或经过针对性深化后仍有清楚、量化的定价/耦合瓶颈。未决不叫阴性，有限域阴性不扩大为全族无效。

---

## F. 有限算法转化：先独立检查便宜 floor，再条件进入完整比较

### F1. 零势机会不依赖全上图先解完

对纯 B 的当前域，以统一数学规则检查
\[
L_0\le\min_{Y\in\mathcal R}\phi(Y)\le U_0.
\]
N-B35 旧 floor 已合格，可作离线信息；K35 相对纯 B 的阈值问题未做完，宜先补必要定价。N-C20 的近零库存 upper 可以复用来判断该方向无用，无须为对称性重跑。

明确初始 B 下界与 oracle 目标阈值：\(U_0\) 已不高于 B 的合格根值时，不能期待该标量提高当前根值；\(L_0\) 超过它时形成真实 floor 增量；中间仍未决。必要时扩到一个有结构意义的既有角色，保持同一规则，不按角色选择算法。

这个检查有小额专门容量。它能决定是否值得做统一 root-floor 候选，不把“对诊断 RN 的增量小”自动当成“对稳定 B 没价值”。

### F2. 生产接入条件及完整成本

可选择一个有依据的统一候选 J：独立 floor、少量 Gini 支持，或有清楚价值的其它实现。无需把 AP/GD/count/RN 所有诊断块都搬上线。若 source 包含这些旧增强，其 root 值不能直接归功于单条新支持；做压缩时须覆盖全部源新增行/新列残差，复用 R104/R144/R145 的完整投影原则，并实际自由重优化核对。

完整臂使用自己的 H、当前实际域、当前 source/pricing 及全部开销，不免费使用离线 floor、历史势、另一臂 incumbent 或旧 paid source。冻结统一规则后才开始完整配对。线上停止使用数学/确定性准则；离线每次 pricing 的 20/120 秒 cap 不是自动可采用的生产步骤。

若需改生产，研究开关默认 OFF、稳定入口保留；登记 source/PE/执行链。B/J 使用同一新 PE；如无需改 PE，则使用同一已核 PE 和匹配执行链，不为编号强制编译。保持原物理模型、目标、own-H、M-B/VD-P、pair-only、AM=.08/depth8/minimum width1e-4。

只为实际新行为做定向 Native 行/列/Start、scope、合法未决/退出及费用资格。遵循 R134，未合格价格不生成新界，但允许保留已有合法信息。

### F3. 条件完整面板

预留 **3 个困难 B/J 配对各 2400 秒/臂＋1 个证书配对各 1200 秒/臂**，共 16800 秒。角色按冻结机制问题选择，优先涵盖 N-B35、K35、RB35 与适当证书角色；这不是全部必跑矩阵，不根据已见完整输赢替换位置。

一个普通损失不机械关闭新方向；严重广泛回退、明显成本失控或有效性问题先解释和修正，再决定后续。已进入的合格配对按正常完整窗口完成，不混合不同候选身份。

另有 4 小时决定型容量，可用于一对各 7200 秒的较长窗口、必要的新机制/旧强化归因，或关键结构问题。先说明它能改变什么判断，不默认多 Seed 或扩大 P-GRB 网格。开放臂 T_cert 留空；共同目标轨迹、最终 U/L/gap 和总成本分开。

---

## G. 预算与计量

| 阶段容量 | 秒 | 作用 |
|---|---:|---|
| 旧强参考、旧行并集、理论关系及零求解筛查 | 7200 | 复用信息、排除直接解释 |
| 耦合主问题/定价接口与定向小域资格 | 10800 | 建立正确整体上下界 |
| 三域完整上图价值定界 | 28800 | 主要研究工作 |
| 一轮针对性结构/定价深化 | 21600 | 给重要未决充分机会 |
| 纯 B 的零势 floor 转化筛查 | 3600 | 小而独立的实际机会 |
| 条件生产资格 | 7200 | 仅进入有依据的新行为 |
| 条件完整比较 | 16800 | 3 困难＋1 证书配对 |
| 决定型长窗/归因/结构反差 | 14400 | 解决重要剩余判断 |
| 失败、验证与外层余量 | 4800 | 实际发生一次计费 |
| **总上限** | **115200＝32h** | **可调拨，不要求花满** |

新增构造、DP、定价、LP/MIP、资格、失败、own-H 和必要验证按外层计一次；嵌套 Runtime/Work 不再相加。纯理论/代码写作、文稿、公开纯 I/O、必要编译单列。启动完整臂前预留 cap 与验证余量；计时有缺项如实披露，不为秒级精度补跑。

主要资源应服务整体价值判断，而非反复短方向后写“下一轮再研究”。同时允许凭扎实区间/理论结果提前结束，无最低运行小时数，不强制生产或正面结论。

---

## H. 论文组织与阶段判断

形成清楚叙述：R152 证明库存联合目标有新信息并建立可执行 oracle；本轮进一步核实相关旧联合行后，量化其在完整路由 LP 中的实际潜力，解释有限点分离与完整目标提升的区别。

记录 \(\Theta=H+\Gamma\)、异质固定边际严格例及其范围、完整上下区间、有效支持/原变量放置、pricing 费用，必要时再给完整算法结果。标准对偶、列生成和压缩明确归属；不给一个新小例或更多求解调用预先承诺 OR 层次。

稳定 GI-TBC 论文继续组织，不等待研究支线成功。若原目标上图剩余潜力已被明确界定，下一步方向应由这个结果决定，而不是继续默认同族堆行；若仍有明显潜力，则说明最值得深入的计算或结构问题。

---

## I. 复核、交付与工作区收尾

昂贵研究或完整臂前由非主要实现者复核关键公式和设计，重点覆盖：

- 旧 NC/TS、row union 与新结果是否排重，同域 Q 是否完整自由；
- RMP upper、合格 dual lower、全域定价与真实库存的界方向；
- beta=0、负价格、缺列/Phase I、原 cutoff 与非最小 completion；
- 有限点/最优面、固定边际/自由最优值、诊断参考/稳定 B 的区别；
- 完整候选是否自付费，预算与条件槽是否适当。

交付前再核数学、数据、scope、版本、费用和主张，定向关闭实际问题。原已合格 tiny 差、未出现的假想风险不扩成整套工程重写。

交付 goal、历史排重与数学报告、完整对象/定价说明、实际区间与结果（含失败/未决）、费用/源身份、论文小节、独立复核及 RESUME。仅在进入生产时交候选入口/profile。文件可合并，按信息完整性验收。

正常提交推送、创建英文 Draft PR，建议标题：

**Round153: bound the coupled integer objective hull and assess root-floor enhancement**

按实际吸收状态选择 main 或核实后的 R152 临时 base，读回 base/head/Draft。无须等待前 PR merge；不自动 merge、force-push 或删除旧分支。

**显式继承 WORKSPACE_POLICY：**所有新增 build/raw/temp/restore 在 E:\codes\ExactEBRP-work；保护 E:\codes\ExactEBRP、用户修改及历史。PR 后只清理本轮已完成、可重建、已由公开恢复覆盖的临时/重复对象；保留唯一 raw、失败、必要 PE/DLL、活动树和旧历史。记录实际删除/保留，零删除可以接受，不进行全项目历史清理。

只打包新增必要证据，旧大包按固定 commit/member hash 引用。对新公开载体做一次有限恢复，不触发旧 producer 或重跑性能。公开 I/O 问题不变成重跑旧实验的理由。

---

## J. 最小来源索引

- PR214：https://github.com/yifanXovo/TailoredExact/pull/214
- R152 fixed science：https://github.com/yifanXovo/TailoredExact/tree/d489ec2948f079105e4532a2e06ae4eed9fcd500/results/unified_exact_round152
- 核心：goal.md、final_report.md、mathematical_analysis.md、preanalysis.md、deepening_plan.md、candidate_decision.json、domains.json、source_manifest.json、cost_report.json、reports/LP_results.json、reports/pricing_results.json、reports/final_table.json、review/exact_small_theorem.md、RESUME.md。
- 实现：scripts/round152_lp.py、cycle.py、global.py、discover.py、normalized.py、oracle.py、projection.py、math.py；上述简称均带 round152_ 前缀。
- 新档（均在 artifacts/）：research_N-B35-S.zip，SHA db8f78b005763573fd56c2bc19542a7559489c7f8b8f2638c39dcac529347d01；research_K-35-U.zip，SHA 4ba536ffe5183b520ace83af191e1b7eb844d09883ca77637f068519e1688d22；research_N-C20-U.zip，SHA b0e2f5e1c093816759dd5839ef28338138bf701102940057052d0efe0b66acb7；qualification_failures_and_fees.zip，SHA c508887df98f402b7b3048b4cbdd652968015b652c97676f2859f8a8975b3006。各自 .members.json.gz 与 carrier_manifest.json 给固定成员。
- 历史：R145 mathematical_analysis.md、scripts/round145_math.py；R143 RN 数学与有限界；R104、R144/145 完整源投影；R105–107 旧分解完整边界；R55/R135 AP；R133/R146 旧小域与 GD；docs/current_mainline.md、unified_exact_research_index.md。
- 经典理论：Dantzig & Wolfe (1960), Decomposition Principle for Linear Programs, Operations Research 8(1):101–111, https://doi.org/10.1287/opre.8.1.101；Desrosiers, Lübbecke, Desaulniers & Gauthier, Branch-and-Price, GERAD G-2024-36, §3.2 的受限主问题/定价界，https://www.gerad.ca/papers/G-2024-36.pdf。使用既有工具，不作为本项目新通用理论。
- 本次外部复核附件：TailoredExact_Round152_Stage_Review.md、TailoredExact_Round153_Review_Evidence.zip。含原始独立复算、169 行严格扩展、直接 Γ/RMP 推导及最终 goal 复核；附件不可取可按固定原档和本文公式继续，无需等待或重跑旧完整实验。

**成功标准：在准确继承历史结果和保持稳定主线的前提下，量化完整整数目标结构在原完整松弛中的可用价值，给仍有价值的问题足够深化空间，并对便宜、统一的实际增强作有依据的取舍。**

