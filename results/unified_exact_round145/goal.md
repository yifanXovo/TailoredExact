/goal

# TailoredExact 下一轮完整任务

## Round145：连接归一化、库存与整数计数信息，并检验紧凑表达的完整价值

**日期：2026-11-01。建议轮次 Round145；编号已占用时沿实际下一轮继续。**

## 0. 本轮目标与执行原则

R144 可以完整验收。它用一条原变量行保留了几乎全部已测 RN 根目标增量，并在 K35 获得有价值的 U／gap 改善。稳定 R137 GI-TBC 继续保留；STOCK、RN-P 等 research-only 身份不等于没有算法成果。

本轮先把已有成果整理成清楚的结构与计算结论，再回答一个新的问题：**将旧整数计数下界和物理库存预算连接到 RN 的同一个倒数因子后，是否获得旧信息简单叠加尚未表达的强化；这种信息能否继续压缩为少量原变量行，并改善完整求解？**

按以下顺序执行：

1. 完成有限历史整合，纳入 R144 的 no-PC 轨迹新发现，不重跑旧面板。
2. 先做少量匹配连续 LP，测量新的齐次化计数 NC、倒数库存乘积 TS 及其组合。
3. 有实际信息与成本价值时，只冻结一个统一的联合来源投影候选；没有有用增量时，收束新强化，改做现成 RN-P 的有限价值确认。两条完整后续是替代方案，不同时铺开两套全面板。

新增实验总上限 **28800 秒＝8 小时**，不要求用满。Codex 可根据实际观察调整少量诊断域、顺序、等价实现及条件对照；一个轻微混合端点不构成一票否决，明确无效、严重回退或成本不合算时可及时收束。

未明确多 Seed 的新求解显式使用 **Gurobi Seed=0**；后文指定的有限确认可用 Seed=1。H seed 独立固定为 20260626。计时求解单线程、串行，编译、重 I/O、PDF 导出与计时实验错开。

算法保持统一数学依据，不按实例身份／大小打补丁，不按运行若干秒切换方法或 leaf。允许按有效作用域、支持、界和数学冗余生成或省去约束。实验 cap 与算法规则分开。

---

## A. 起点、版本与主线

| 项目 | 编写时核实的参考 |
|---|---|
| 仓库／前序 PR | yifanXovo/TailoredExact；#206，Open Draft，未合并 |
| R144 branch／head | codex/round144-rn-projection；68041d6a69e14ca7cfbff4e3262ab17331bf792e |
| R144 fixed science | 24885c482f818803795cdfc98b6a7b3d1887052c |
| 实际生产源码 | 0b5858544a671722142c8450db9b88c09c9b1c72 |
| 实际 PE SHA256 | 180126ae1ecf7db892c3fbb92faa73b517d19029e9824f62cd922e0d9e277d7b |
| 编写时 main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 稳定入口／配置 | scripts/paper_s2.py；config/gi_tbc_round137.json |
| R144 入口／配置 | scripts/paper_s2_rnp.py；config/gi_tbc_rnp_round144.json |
| 活动树／新资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work\ |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议 branch／结果目录 | codex/round145-normalized-resource-consistency；results/unified_exact_round145/ |

先读适用 AGENTS.md、WORKSPACE_POLICY.md，核实 refs、用户未提交内容、进程与可用资产。main 已吸收所需版本时从实际 main 继续，否则从核实后的 R144 继续并以其为临时 PR base；不等待合并，也不机械回退参考 SHA。

算法载体保持稳定 R137：完整自身 H、M-B/VD-P、pair-only、AM=.08、depth=8、minimum width=1e-4、AP off、R134 证明政策。新正式候选以稳定 BASE 为旧模型，研究开关默认关闭。R138–R144 的入口、配置与历史结果保持原身份。

---

## B. 先形成客观阶段判断

### B1. 已有成果与尚缺证据

整理一份可供论文使用的简明结构／证据表，引用已有结果，不为填表追加求解：

| 研究线 | 已有价值 | 保留的边界 |
|---|---|---|
| R137 稳定 GI-TBC | 完整算法、P-GRB／自身 H 对照、广度与机制测试、有限 Seed 确认 | 120 个注册位置不是 120 个独立实例；仍有困难开放例 |
| R138 STOCK | 所选连续资源块的共享因子凸包；stock／TC 互补；条件 stock ⊆ shared GS ⊆ projected independent GS；K15 明显提速，K20 两个已测 Seed 都新增证书 | 使用标准 RLT／析取工具；不是完整整数 BRP hull；部分 n35 端点混合 |
| R139–R142 placement／count | 解释 stock 收益的放置位置；TC2 严格块信息；条件计数与端点产品缺口；selected／ALL 的信息边界 | 旧 count-proof 的新增完整收益有限，不恢复旧 floor／placement 网格 |
| R143 RN | 真实完整 LP 增量，且超出 TC+stock；归一化与计数信息不互相覆盖 | 持久扩展列带来成本，尚非统一更快算法 |
| R144 RN-P | 一条原变量行保留已测 RN 根信息；K35 实际 U／gap 收益；相对完整 RN 的表示成本改善 | 根值保持是标准对偶及 R104 已有原理；不保证全树或全投影相同 |

R138 K20 的 STOCK 证书约为 Seed0 101.64 秒、Seed1 90.23 秒，而对应 BASE 均在 cap1200 内开放；K15 约112.77→33.82秒。Seed1 的已披露 V2 运输修复身份保留。这些是实质计算成果，不能因 release 未晋升而当作零进展。

现阶段不缺更多“每条行有效”的重复证明；需要把互补信息、一致表达和完整计算价值连起来。现稿应区分稳定算法、已验证增强候选、局部结构定理和未完成的更广性能结论，避免把所有研究开关堆成一个未经测试的算法。

### B2. R144 本轮结果与 no-PC 解释

| 角色 | OFF U／L | RN-P U／L | 结论 |
|---|---|---|---|
| K20 | .716806546278／.705363448597 | .716806546278／.705346769145 | 不发 PC；U 相同、L 微降 |
| K35 | .692854358631／.558227874949 | .660923637174／.545412294185 | U 改善4.6086%，gap减少1.9534个百分点，L回退 |
| RX20-T1 | 同一目标 .645325030386，均认证 | RN-P生产快约1.72秒 | 小幅时间观察 |
| RB35-T2 | .344642625592／.218985949603 | .362136826572／.218895658669 | 不发 PC；实际完整端点较差 |

R144 同 PE K35 完整 RN 为 U=.681258498381、L=.542931774252；RN-P 对它双端改善，terminal Work 约低9.24%，但两者均未收敛，不能称证明时间提速。

本次验收额外读取原始 RB35 两个 ZIP，确认：

- 正式矩阵、H、Start 一致；RN-P 的全部33个物理 witness payload 与 OFF 前33个一致，OFF仅多最后一个改善。
- 去掉时钟后，27条根状态、170个可匹配正节点状态一致；RN-P的42条 H日志是OFF的相同前缀。
- OFF在node6706、producer约2358.391秒得到最后 U=.344642625592；RN-P在6705个节点结束。
- 同一node6619的Native日志时间为2316／2337秒，累计速度漂移约21秒，不能全部归因于2.3388秒来源准备。

这支持“已观察到的相同搜索前缀在墙钟边界处截断”，不证明未执行的后续必然相同。原端点、费用全部保留；不要把 no-PC 差异解释成投影行破坏几何，也不要据此改判为胜或设置实例跳过规则。

K20 的实际验证时间286.74／61.69秒也保留。两侧约4.1万个 journal JSON、约97MB claims，证据规模相近；不能把完整时间节省当结构提速，也不为猜测缓存／I/O原因单开工程轮。

---

## C. 本轮数学方向：在同一个倒数因子上连接信息

### C1. 记号与齐次化计数 NC

沿原模型记 \(r_i=c_iY_i\)、\(S=\sum_i r_i\)、\(A=\sum_{i<j}|r_i-r_j|\)，正分母域中 \(G=A/(nS)\)。selector 为 \(s_{iy}\)。在 RN 的整数扩展中，\(t=1/S\)、\(w_{iy}=t s_{iy}\)；连续来源沿 R143 的产品盒／质量关系放松，并定义 \(v_i=c_i\sum_y y w_{iy}\)，保留

\[
\sum_i v_i=1,\qquad \sum_yw_{iy}=t,\qquad
\widehat H:=\sum_{i<j}\widehat h_{ij}\le ng.
\]

令实际有限 ratio 支持的相邻阈值差为 \(\Delta_j>0\)，整数阈值计数

\[
K_j(s)=\sum_{i,y:c_i y\ge\theta_j}s_{iy},\qquad
\ell_j\le K_j\le u_j.
\]

在整数库存上，\(A=\sum_j\Delta_jK_j(n-K_j)\)。沿 R140 已验证的物理库存／支持构造取得 \(\ell_j,u_j\)，旧两类下界为

\[
K_j(n-K_j)\ge(n-u_j)K_j,
\]
\[
K_j(n-K_j)\ge\ell_ju_j+(n-\ell_j-u_j)K_j.
\]

任一聚合可写成整数有效的 \(A\ge b+\sum k_{iy}s_{iy}\)。整数扩展有 \(\widehat H\ge tA\)，乘以正 t，得到不加变量的新行

\[
\boxed{\widehat H\ge bt+\sum_{i,y}k_{iy}w_{iy}.}
\tag{NC}
\]

这是把旧 count 信息接到**同一 RN 乘积**上；旧 H 上的 TC 行并不自动约束 \(\widehat H,w\)。默认保留齐次化 TC、TC2 两条聚合。两者差为

\[
\sum_j\Delta_j\ell_j(u_jt-W_j),\qquad
W_j=\sum_{i,y:c_i y\ge\theta_j}w_{iy}.
\]

分数 \(w/t\) 未必满足整数计数上界，因此不能无条件用 NC2 替代 NC1。保留常数乘 t、负系数及实际阈值身份；不默认增加全部阈值的产品／范围行。

### C2. 倒数库存乘积 TS

设有效库存范围 \(B^-\le\tau=\sum_{i,y}ys_{iy}\le B^+\)，RN 倒数范围 \(L\le t\le U\)，\(\widehat\tau=\sum_{i,y}yw_{iy}\)。将库存预算的松弛量分别乘 \(t-L\)、\(U-t\)，得

\[
\begin{aligned}
\widehat\tau&\ge L\tau+B^-(t-L),\\
\widehat\tau&\ge U\tau+B^+(t-U),\\
\widehat\tau&\le U\tau+B^-(t-U),\\
\widehat\tau&\le L\tau+B^+(t-L).
\end{aligned}
\tag{TS}
\]

四行约束的是 t/w 端点库存一致性。R138 的旧 stock 行约束 g/state_g/Z，不能把两者混同。该构造沿用标准 RLT／共享因子端点原理，不宣称新的一般凸化方法。异质目标下，物理库存方向与 ratio 总和方向继续区别处理。

NC 两行＋TS 四行只进入来源 LP，不增加 RN 以外的新列。正分母、物理库存界、支持、当前域／cutoff的来源与作用域沿既有政策。

### C3. 已核验的严格互补参数族，以及它仍未解决什么

以下是明确的固定-selector **局部块**，不是完整路由实例或全部历史扩展。取任意 \(n\ge4\)、\(c_i=1\)、支持 \(\{0,1\}\)、库存范围 \([1,n-1]\)、\(s_{i0}=s_{i1}=1/2\)，所以 \(\tau=n/2\)；旧 g 域为 \([0,(n-1)/n]\)。令 O 包含旧 VD-P、stock、TC、TC2、Gini 和 RN。

旧块取

\[
q_{i1}=\frac{n-1}{n^2},\quad q_{i0}=g-q_{i1},\quad
J=\frac{n-1}{n},\quad H=n-1.
\]

每对旧 h 为 \(2/n\)。2n个库存总量为1或n−1的二元向量等权混合可实现这些 selector／普通 pair-difference；不把它冒称整个 g-product／整数目标 epigraph 的共同混合。

旧 TC2、Gini 与 stock 给 \(n-1\le H\le nJ\le n(n-1)g\)，故 \(g\ge1/n\)，上述旧变量可达到。

RN 的 \(L=1/(n-1),U=1\)。对该固定 selector 的任意 RN 扩展，归一化给 \(\sum_iw_{i1}=1\)，质量与产品盒给 \(\sum_iw_{i0}=nt-1\ge nL/2\)，因此

\[
t\ge t_N=\frac{3n-2}{2n(n-1)}.
\]

NC2 为 \(ng\ge(n-1)t\)。TS 的第四行结合 \(\widehat\tau=1\)，则给

\[
1\le\frac{n}{2(n-1)}+(n-1)t-1,
\qquad t\ge t_S=\frac{3n-4}{2(n-1)^2}.
\]

精确最优值如下：

| 固定-selector 局部松弛 | min g |
|---|---|
| O | \(1/n\) |
| O＋TS | \(1/n\) |
| O＋NC | \((3n-2)/(2n^2)\) |
| O＋NC＋TS | \((3n-4)/(2n(n-1))\) |

达到方式：取每站 \(w_{i1}=1/n,w_{i0}=t-1/n\)；O、O＋NC 用 \(t_N\)，含 TS 的两格用 \(t_S\)。沿上述 q 构造，无 NC 时令 \(\widehat h=0\)，有 NC 时每对 \(\widehat h=2t/n\)。其余产品面、旧 stock、质量、归一化与有限 caps 均满足。两级严格增量分别为

\[
\frac{n-2}{2n^2}>0,\qquad
\frac{n-2}{2n^2(n-1)}>0.
\]

n=4时四值为 **1/4、1/4、5/16、1/3**。固定 state penalty \(P=n/2\)，故原目标 \(g+\lambda P\) 的相应最优值统一加 \(\lambda n/2\)，不换目标制造严格性。

同时，正库存二元整数点满足 \(G=(n-\tau)/n\)。在同固定 marginals 下，完整整数 Gini epigraph 凸包的最小 g 恰为 **1/2**，由上述2n点混合达到。联合松弛只有约 \(3/(2n)\)：它严格加强 O，仍没有表达全部整数目标一致性。这个边界应进入论文解释，不要求本轮重构全整数 epigraph，也不实现等目标／二元专用补丁。

全 n 结论来自代数；已完成的 Fraction 构造检查覆盖 n=4,5,6,8,10,20,35,50。复用现有证明与检查，不再铺小例枚举。它不宣称支配 R141/R142 的所有条件析取扩展。

### C4. 实际保存点的前置信号

对 NC 的 k,b，任取站点乘子 \(\lambda_i\)，记 \(\Gamma=b+\sum_i\lambda_i\)。由站点质量和产品盒，得到

\[
\boxed{ng\ge\min(L\Gamma,U\Gamma)+
\sum_{i,y}\min\{L(k_{iy}-\lambda_i),U(k_{iy}-\lambda_i)\}s_{iy}.}
\tag{NC-PC}
\]

它只含原变量，因此正违反能排除该原变量点的任何 NC 扩展，不只是某个保存 z。有限一维站点盒计算可用于选择乘子，合法性不依赖乘子最优。

本次验收以实际 binary64 输入作精确有理数解释，已得到 NC2-PC：

| R144 保存来源点 | 原变量行违反量／n |
|---|---:|
| K35 | .0862352641105 |
| RX20-T1 | .0125145224432 |
| K20，原先不发 PC | .1139059369152 |
| RB35-T2，原先不发 PC | .1340443111542 |

这些是零 Optimize 的保存点分离，**不是重优化目标增量**。这些点也违反旧 TC2，所以还必须检查强旧载体，不能只凭此表宣称超越旧信息叠加。R143 K35 的 RN＋旧TC＋stock 点也被排除，但该载体没有 TC2。

配套前置证据包给出推导、脚本、精确系数与来源。附件不可用时，按本 goal 和固定原始载体有限重建即可，不阻塞，也不重跑旧实验。该离线投影只作证明和诊断，不另开第二种完整算法，不向正式运行免费注入历史切割。

---

## D. 先做有决策价值的匹配 LP

### D1. 两个已有活动域

优先 K35、RX20-T1。复用 R144 已保存的生产有限 caps RN 连续来源，核对完整旧矩阵、原目标／penalty／常数、cutoff、支持和 g 域；不因为轮次改变而重求已经可复用的 RN 基准。

每个域新增三个连续 LP：RN＋NC、RN＋TS、RN＋NC＋TS，共 **6 个新 LP**。记录完整目标增量、G／penalty 分量、实际行列／NZ、源求解费用、质量以及新增行活动。分量变化用于解释，完整原目标仍为权威。

### D2. 强旧载体与原先 no-PC 角色

K35 再比较 **RN＋旧stock＋TC＋TC2**（记 O）。若其最优点已满足拟加入的 NC／TS，经现有数值政策核验后可作为同目标无新增量的数值见证，不为填表再求解。若有实质违反且会影响方向判断，再解 O＋NC＋TS。最多两个额外 LP 即可回答主要非重复性问题。

另选 K20 或 RB35 中一个原先 no-PC 角色，优先回答“新的联合信息是否改变原来无增量的来源根”。可复用已封存的匹配 RN source，只新解有必要的组合；除非有具体归因问题，不再补所有分格。若另一个角色确实会改变候选选择，允许在诊断预算内有限增加。

参数族已证明局部严格性；这些真实 LP 检查其实际价值。不同不互含模型的目标大小只作为同目标数值比较，不冒称全域支配。若强化只复现旧 O 的信息，准确报告；不要把旧信息换变量后的再现包装成新的交叉增益。

### D3. 紧凑信息保留与阶段决定

来源有有用增量后，从完整新增块提取一次投影，在正式旧 BASE 中加入实际运输后的原变量行，再解 1–2 个紧凑 LP，检查信息保留与代价。可按具体风险补一个已保存真实子域；不默认恢复整棵树。

典型总量约 **10–14 个新 LP**，具体取决于强载体、no-PC 与紧凑检查是否有必要；不把数量当完成指标。先完成这一有限阶段，再决定是否投入生产候选工程。

- **路线 B：**实际增量超过数值噪声，联合表达／成本有价值，且紧凑投影保留有用信息时，冻结一个统一新候选，进入 E/F。
- **路线 A：**没有有用增量或成本价值时，收束新强化，按 F3 对现成 RN-P 做有限确认，并完成成果整合。

若结果提示一个明确的小改进，可调整一次相关构造。没有具体信号时，不自动追加全部阈值、分组、反复分离、count-proof 或 AM 网格。

---

## E. 路线 B：一次联合来源，正式模型保持紧凑

候选暂称 **RN-JP**，只是研究身份。默认在当前运行自身 H 和初始根域确定后，构造稳定 BASE＋RN＋NC＋TS 来源，取得全块对偶，投影后重建正式模型。NC／TS 只存在于一次性来源，不在各 leaf 反复求解。

### E1. 投影的块必须完整

令 P 为正式 stable BASE，来源为

\[
\min\{c^Tx+c_0:x\in P,\ Ex+Fz\ge d,\ \ell\le z\le u\}.
\]

这里 E/F/d 包含**相对 P 全部新增的来源行**，包括 RN、NC、TS。若有充分理由选择再含旧 stock／TC／TC2 的统一来源，它们也属于新增块，不能免费留在 P 的对偶部分。

对合法乘子 \(\beta\)，沿 R144 作

\[
a=E^T\beta,\quad r=F^T\beta,\quad b=d^T\beta,
\qquad a^Tx\ge b-\sum_j\max(r_j\ell_j,r_ju_j).
\]

精确最优对偶、同一旧域／目标及零目标的新列给出同根值保持；浮点实现经实际重优化测量损失，不要求严格零残差。有效性与最优值保持继续分开。

**实现注意：R144 的 project 目前只遍历 rn.rows。必须将 NC／TS 纳入显式完整来源清单。**旧 R143 Native audit 按旧 RN 生成器／前缀核对，新增行不能因换前缀而漏审计。使用小 wrapper／同级生成器即可，保留旧接口和身份。

TS 涉及旧 Y；最终 PC 可含原 Y、selector、G 等合法原变量。可用既有精确线性关系消去 Y，也可保留它，不为“只含 selector”做无效转换。正式模型不增加 RN 辅助列。

### E2. 最小必要资格

复用 R144 的有限盒、有向补偿、Start、source restore/discard、正式控制隔离与作用域机制。定向覆盖：

- NC 常数乘 t、负系数、实际 count 范围／支持／ratio 系数；TS 的正确库存单位和 L/U。
- 来源全部新增行及实际 Native 系数、方向、缩放、有限界、零新列目标；最终投影行的运输／删项补偿。
- 整数物理解满足来源新行与投影行；完整 Start、source 与正式模型身份、零投影、compatible 子域继承、off 行为。
- 正式 LP／target／terminal 没有持久 RN 列，来源所有计算进入实际费用，但来源 point/bound/handle 不冒充正式控制证据。

采用少量精确 fixture 与实际读回，再做一次短完整健康资格；只为具体发现定向修正，不新建通用数值修复或大审计系统。沿已有正分母／UNKNOWN／证明政策，失败不得被当作有效下界。编译实际受影响单元并绑定 source/PE；报告或 metadata 修改不触发重跑健康实验。

---

## F. 完整实验与采用判断

### F1. 路线 B 的核心四角色

每个已进入角色比较 RN-JP 与**同 PE stable-off**，各自付出完整 H、来源、正式搜索与验证。

| 角色 | 站点／车辆 | 物理 T | 原目标 | 每方法 cap |
|---|---:|---:|---|---:|
| K-20-S | 20／2 | 5400 | λ=.15 | 1200 s |
| K-35-U | 35／3 | 10800 | λ=.15 | 2400 s |
| R-X20-S-T1 | 20／2 | 4800 | ρ=1，λ=1/Ω | 1200 s |
| R-B35-S-T2 | 35／3 | 7200 | ρ=1，λ=1/Ω | 2400 s |

单方法7200秒，成对14400秒。输入容量、pickup/drop、原权重和精确目标系数沿既有实例，不从表中舍入数重建。

可先 K35 与一个能检验新增信息的角色，再继续不同资源角色。轻微 mixed 可以继续；重要真实回退或明确无效可停止。已进入的有效 hard-role 保留完整窗口。

### F2. 仅做有明确目的的条件对照

- **旧 RN-P 桥接：**预留一次 K35 cap2400 的同 PE R144 RN-P，判断联合信息是否比当前紧凑投影本身更有用，而不只比较稳定 BASE。另一个角色的桥接仅在改变归因／决策时从未用额度调剂。无需再默认加入持久 full-RN。
- **条件边界：**K15（15／2、T3600、λ=.15、cap600）与 RX35-T2（35／3、T6300、ρ=1、cap2400）可各做新候选／stable 成对，共6000秒。
- **有限 Seed 或 floor：**只有具体相反结果会改变采用／归因判断时进入。Seed1 组、paid-floor 或额外桥接从同一剩余额度调剂，不另增预算，不铺全面板。

### F3. 路线 A：现成 RN-P 的有限确认

若 D 阶段不支持新候选，直接复用 R144 已验证入口／PE，不为新报告重新构建算法。

优先一个 **K35 Seed1 的 OFF／RN-P 成对完整测试**，cap2400各一次，共4800秒，检查现有主要活动角色收益是否保留。RB35 的 Seed1 pair（再4800秒）只在会影响采用判断时进入；若问题是同一搜索的墙钟边缘敏感性，也可改用明确标注的同 Seed0重复，而不同时再做两组。

当前 raw 已给出匹配前缀证据，不需要为“证明它没加行”再求解。不要给被选中的不利例单独延长到刚好出现下一解，也不把诊断时钟替代完整 wall 结果。若一个有限确认已经足以判断，可收束；必要的缺失角色从 F2 或未用预算选择。

路线 A 与 B 默认择一进入完整阶段。确有新发现时，可用一项明确有决策价值的对照替换尚未进入的工作，但不在跑完一个完整面板后自动追加另一个。

### F4. 评价方式

完整报告 U、支持 L、signed／relative gap、T_produce／T_cert／T_verify／T_total，开放的 T_cert 为空。Native返回界与外部合并界分列。节点、Work、simplex、presolve、AM和轨迹解释观察，不以少节点或等根值代替完整收益。

接受有实质收益且无大范围／重要严重回退的统一候选，不要求每个实例获胜。no-PC 端点、活动切割引起的路径变化、普通完整时间波动分清，但任何实测负面结果都保留。若建议晋升，给出有限证据支持范围；稳定入口仍保留，不自动覆写历史版本。

---

## G. 预算

| 内容 | 规划上限 |
|---|---:|
| 有限 LP、必要实现／writer 资格与短健康测试 | 3600 s |
| 路线 B 核心四角色成对；或路线 A 的有限确认 | 14400 s |
| 有归因需要时的 K35 同 PE 旧 RN-P 桥接 | 2400 s |
| 条件 K15／RX35-T2 成对边界，或更有价值的确认 | 6000 s |
| 失败、必要修正及额外控制的共用余量 | 2400 s |
| **总上限** | **28800 s＝8 h** |

分项可调剂，总额不变。路线 A 的一组／两组 hard-role pairs 是4800／9600秒，包含在第二行，不另加。条件 Seed 或其他对照只能使用实际未占用余额；余量不得重复分配。

按外层实际费用计入来源、资格、失败及必要后验验证，嵌套 H／LP／MIP／Work 不重复加总。cap 是计划窗口，验证等实际超出部分由余额承担。编译、离线精确算术、文稿及公开 I/O 单列。未用预算不是补实验的理由。

---

## H. 论文组织与复核

本轮文稿应形成统一叙述：原共同因子的资源一致性、整数计数信息、倒数归一化、二者的联合表达与紧凑投影。保留 standard RLT／duality 的归属；参数族说明严格互补及剩余整数目标缺口，实际 LP 说明模型信息，完整实验决定算法价值。

将 STOCK 的重复证书收益、RN-P 的已有完整收益写入阶段总结，不以未晋升抹去；明确原 R141/R142 计数证明支线已经回答了什么，不恢复旧流水线。稳定 GI-TBC 正式稿继续保留，必要时形成一份可并入主稿的结构／结果章节，而不是只追加互不衔接的轮次附录。

在昂贵完整运行前，由非主要实现者复核推导及来源 writer；收尾再复核：

1. NC、TS 的有效性、符号、常数和单位；参数族上下界与达到点；所有定理的局部范围。
2. 保存 z 违反、原 x 分离、重优化完整目标增量、完整收益四层没有混淆；强旧载体信息未遗漏。
3. 联合来源所有新增行进入投影与实际 Native 审计；same-root 原理没有误用为全树保持。
4. 当前 H／Start／scope／缓存／source隔离和完整计费正确；数值损失不过度修补。
5. R144 no-PC 解释与原结果同时保留；同 PE／Seed／预算与实际证据一致；没有两套完整面板或一个负端点否决。

修正实质问题并给简明结论即可，不新建庞大审计体系。若本轮最终无新的完整收益，应明确已解决的问题、剩余障碍与是否停止这一联合表达试验，避免自动接着增加更多同族行。

---

## I. 交付、Draft PR 与有限清理

交付本 goal、阶段结构／证据总结、必要数学和实际行、最小代码／配置差异、匹配 LP 与全部已进入完整结果、成本、采用决定、source/raw绑定、增量稿、独立复核和续跑入口。重复报告可合并，内容完整优先于文件数量。

正常提交、推送研究分支并创建英文 Draft PR，建议标题：

**Round145: couple inventory and threshold-count information within reciprocal normalization**

main 未吸收 R144 时以其研究分支为临时 base，已吸收时使用实际 main；读回 base/head、Draft 与交付状态。不自动 merge、force-push、删除历史分支、发送邮件或投稿。等待合并不阻塞科学完成。

只对必要新载体作一次有限公开字节／成员读取，纯 I/O 建议累计30分钟内收束，不触发 Optimize、编译或商业 Native 加载；不重开旧轮全历史恢复。

**显式继承 WORKSPACE_POLICY 两项要求：**全部新 build/raw/temp/restore 资产位于 `E:\codes\ExactEBRP-work`；PR 交付后进行本轮有限清理。仅在证据保留及公开核对条件满足后删除本轮已完成、可重建的临时／重复对象。保留唯一 raw、失败、用户内容、必要 PE/DLL 和仍需使用的树；不删除旧轮。记录实际删除／保留与字节，零删除可接受。

最终说明：当前研究资产有哪些，新增联合表达保留了多少有用信息，是否超过强旧载体，完整结果改善／回退在哪里，以及下一步是推荐统一候选、保留研究成果，还是结束这次尝试。

---

## J. 最小资料索引

- R144 PR：https://github.com/yifanXovo/TailoredExact/pull/206
- R144固定science：https://github.com/yifanXovo/TailoredExact/tree/24885c482f818803795cdfc98b6a7b3d1887052c/results/unified_exact_round144
- 核心：final_report.md、mathematical_analysis.md、candidate_decision.json、reports/LP.json、full.json、same_PE_pairs.csv、same_PE_RN_bridges.csv、verified_U_trajectories.csv、cost_report.json、review/及RESUME.md。
- R144 diagnostics：artifacts/diagnostics_and_failures.zip，SHA256 `639d7c7c67a74c785f579b8516d7833efe564c84258d4c356d7cc485a88ac8ee`。
- RB35原始对：campaign_resource_001.zip（OFF，SHA256 `6ae830195acbcacd8eb8360b79626c14a425938242500caae9991286cb164f0c`），002.zip（RN-P，`8554859b67c3749599c818b93fdb33a39f7ca658a21da1fe23793a2818750d24`）。读取实际物理witness、native_logs、source与formal记录；时钟口径分开。
- R144投影：include/Round144Research.hpp；include/ObjectiveResourceCompression.hpp；src/ObjectiveResourceCompression.cpp、PaperExternalGiniTree.cpp、GurobiBaseline.cpp；scripts/round144_lp.py、round144_project.cpp、round144_read.py。
- RN与前置数据：R143固定science `516f89f2e23bfad0238c8423bfb9809c308fdec9`；include/Round143Research.hpp；mathematical_analysis.md；diagnostics SHA256 `b4afa7de3a9f7b3844ab76b24c8082b1ea05db92c4a27118708c98b9085246b3`。
- 计数／资源：R138 mathematical_analysis.md、final_report.md及其V2身份；R140 mathematical_analysis.md、实际TC／TC2生成器；R141/R142数学与结果边界。优先复用原构造，不启动旧count-proof实验。
- 对偶历史：R104 fixed science `aa1d0e5b268cf95442b3713b2af8fc505974f6c2` 的 mathematical_algorithm.md／final_report.md。
- 更早结构：R132–R133 joint service与原目标混合缺口；R134 TC；R137正式报告及现稿。
- 本次审查与前置证据：`TailoredExact_Round144_Stage_Review.md`、`TailoredExact_Round145_Preliminary_Evidence.zip`；不是生产历史输入或免费切割池。
- 工作区与主线：WORKSPACE_POLICY.md；docs/current_mainline.md、docs/unified_exact_research_index.md；config/gi_tbc_round137.json。

**成功标准：把已获得的算法收益与结构关系准确组织起来，用有限的新计算判断统一的归一化资源／计数表达是否值得进入完整算法；不追求每例全胜，不把工程确认或切割数量当研究目标。**
