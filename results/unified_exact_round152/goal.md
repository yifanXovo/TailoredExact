/goal

# TailoredExact 下一轮完整任务

## Round152：研究硬库存资源下的整数目标上图与可计算分离

**日期：2026-11-04（Asia/Shanghai）。建议轮次 Round152；编号已占用时沿实际下一轮继续。**

## 0. 目标、自由度与预算

R151可以完整验收。GD关闭后的独立CPF在N-B35纯B根上取得真实LP增量，但同新PE完整配对的U恶化1.352554%，支持L仅改善0.231949%，signed gap扩大8.502392%；两臂均未获证。按原goal不进入N-C20及澄清槽合理。保留表达与LP成果，结束当前root-penalty实现的推广，稳定R137 GI-TBC继续作为论文算法。

本轮研究一个不同问题：**能否把硬整数库存资源与原Gini＋惩罚目标联合起来，得到超出已有AP/VD-J、相关GD/count信息的可计算下界或支持不等式，并在有价值时形成完整算法增强？**核心对象是资源可行的整数目标上图（objective epigraph），不再默认加一层CPF、恢复旧组合或重做inventory-first路由分解。

用户已明确允许后续各轮更深入尝试和更多时间预算。本轮新增实验计算容量上限为 **86400秒＝24小时**：先给数学、oracle及多域研究充分空间，再按证据进入生产与完整比较。允许在预算内调整方法、顺序、域和容量，进行有理由的结构修订；不因第一格普通损失、一个未解oracle或小根增量机械终止。也不要求花满、强制产出新默认算法，或为“阳性”追加无明确问题的测试。

算法保持统一、数学依据明确：不按实例名、大小或历史输赢打补丁，不以运行k秒触发方法切换。新的辅助模型、变量、有效oracle或局部重构可以尝试；R151的“无新列、无额外求解”是该轮cap设计的性质，不是今后永久限制。新开销必须完整支付，稳定入口与已验收结果保留。

默认 **Gurobi Seed=0、Threads=1**，H seed独立固定 **20260626**。计时实验串行，与编译、重I/O及PDF处理错开。沿用R134证明/物理验证政策，接受已合格浮点结果；真实数值问题定向修正，不为tiny差追求字面零或无限扩大工程面板。

---

## A. 起点与已有事实

| 项目 | 编写时核实的参考 |
|---|---|
| 仓库／当前PR | yifanXovo/TailoredExact；#213，Open Draft，未合并 |
| R151 branch／head | codex/round151-standalone-penalty-propagation；c6e930ffcb84f0c3801c651f28b5f7e8e2062f33 |
| R151 fixed science | 3978b0532aec965816a80556988c531bd10be0c2 |
| 实际生产源码 | c26382d9bf1d4edde538a01c62e57ba563cf865c |
| R151 PE SHA256 | fbdd7c2ece5c748e086761f2490fd901ccdaeffa29df357d2d98fd8743e1dc39 |
| PE路径 | E:\codes\ExactEBRP-work\build-cache\round151\ExactEBRP.exe |
| Native DLL／SHA256 | D:\gurobi1302\win64\bin\gurobi130.dll；9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88 |
| 稳定B／配置 | R137 GI-TBC；scripts/paper_s2.py；config/gi_tbc_round137.json |
| R137 fixed science | e735c3447eb1443713c700942d873de1783a4a26 |
| R150 fixed science | 59c4e398f385aa8525fe87a4212ed97554f093e8 |
| 编写时main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 活动树／新增资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议branch／结果目录 | codex/round152-resource-integer-objective；results/unified_exact_round152/ |

先读适用AGENTS.md、WORKSPACE_POLICY.md，检查refs、用户修改、活动进程和既有证据。main已吸收所需工作则从实际main继续，否则从核实后的R151继续并选择相应临时PR base；不等待合并，也不机械回退参考SHA。

R151实际改动为3个旧cpp接入和一个默认OFF的Round151Research.hpp。6个稳定/旧研究入口与profile字节保留。若本轮只做离线研究，不需要为了轮次号重编译生产；若进入生产，登记新源码/PE身份，完整B/J对照使用同一新PE、各自own-H，原物理模型、目标、M-B/VD-P、pair-only及AM=.08/depth8/minimum width1e-4保留。

### A1. R151验收结果

| 内容 | B | P＝B＋uniform PF | C＝B＋CPF |
|---|---:|---:|---:|
| 同域N-B35根LP | .3278337721771161 | .33216166600112773 | .337310427549131 |
| 完整物理U | .450291503262878 | 未进入完整臂 | .456381937436932 |
| 完整支持L | .389279198209665 | — | .390182126769401 |
| relative gap | 13.549513% | — | 14.505353% |
| T_total／秒 | 2375.215976 | — | 2380.095525 |

2个新LP均全变量自由，P/C各537行、1074NZ，无旧B/N-C20根重求。C先冻结再运行。C并非全过程较差：U≤.48首次到达126.828秒，B184.578秒；但U≤.46为C1957.484秒、B1314.171秒，C全窗未达到B最终U。初始LP、打印的Native root-after-cuts和终端支持L分别报告；B有一次target、C没有，两臂均无committed split。较少节点不等于较少完整证明成本。

本轮费用4875.055581899秒，build单列57.036886100秒；正式9/9调用、资格4/4调用、独立LP2/2调用均返回。55个正式物理witness、52次严格U事件及7包/1196成员通过独立复核。scope-reader和非法固定辅助变量的测试fixture已修正，不是生产算法故障；不在R152重复修复。

---

## B. 先排除重复信息，再确定新研究缺口

### B1. 必须保留的历史定位

- R55已做VD-J/state-weighted penalty；后来penalty-cover DP未满足live前提，不能称该分支已被完整实证否定。
- R135已测试聚合AP，32位置/16配对，两方法各10个证书，结果有K35收益与若干认证减速，未采用。AP不是新机制，也不是数学无效。
- R138–142已有库存共同产品、完整阈值计数关系、count disjunction和条件共享因子；R146已有Gini–Hoover状态条件GD。阈值计数恒等式、等目标balancing lemma及R133例均不能重新包装成新贡献。
- R143–145已有归一化、源LP与原变量投影；R104已做单车必要资源hull的LP对偶压缩。强源根值与少量行未保证完整收益。
- R105–107已有整数库存/服务归属master再交给route oracle，出现master等待和物理U退化；本轮不重新布置同一分解架构。
- R133已证明service joint hull不自动给出原整数目标epigraph，固定分母也可有缺口。这个对象级困难仍值得深入，但全规模有效式/高效oracle尚未建立。

历史正面结果（STOCK证书、RN压缩和局部收益、GD困难U收益）及负面、来源和运输限制同时保留。完整论文算法的价值与新研究候选的采用分别判断。

### B2. 本次外部审查发现：旧B/CPF点有很大的已知AP遗漏

定义\(P_e=\sum_i\omega_i e_i\)，权重已包含lambda。已知AP为

\[
P_e\ge\sum_i\sum_{y\in\mathcal Y_i}h_i(y)s_{iy},
\qquad h_i(y)=\omega_i|c_i y-1|.
\tag{AP}
\]

本次只读保存模型和点、未新Optimize的计算如下：

| 保存点 | 状态加权惩罚 | 原\(P_e\) | AP违反 |
|---|---:|---:|---:|
| R150纯B N-B35初始LP点 | 2.197578269555 | .255734140505 | 1.941844129050 |
| R151 C N-B35新LP点 | 2.472949464076 | .274840264249 | 2.198109199827 |
| R150纯B N-C20初始LP点 | 1.127669954745 | .030817907529 | 1.096852047216 |

这些是分数selector混合的期望惩罚与平均库存epigraph之间的差，不是物理可行目标，也不能加到旧LP值上当新界；不是Native after-cuts点，也不代表生产bug。附件不可取时可从固定模型/完整解重算。

**新机制必须先面对已知AP信息。**对真实完整B域加入适用AP并自由重优化，作为最低强参考；再按研究关系加入适用的GD、库存/count等旧信息作有针对性的比较。不要仅因为新行切掉旧B/CPF点就宣称新发现，也不必一开始构造所有历史行的巨型合集。

R135已保存K20同域AP约.31875854261558051、K35约.27385768132726473。若恢复的目标、域、cutoff、全部旧行和变量语义确实相同，可复用原合格结果；数值相近本身不够。N-B35/N-C20若无同域AP结果，才支付新的强参考LP。离线启AP不改变主线默认，也不推翻其历史完整采用结论。

---

## C. 研究对象与支持行：硬资源整数目标上图

### C1. 域、真实目标与非最小completion

在当前真实模型域\(\mathcal D\)上读取支持\(\mathcal Y_i\)、已加权\(\omega_i\)、实际比率系数\(c_i>0\)、安全整数资源界\(B^-,B\)及\([\gamma_L,\gamma_U]\)。令

\[
S(Y)=\sum_i c_iY_i,\quad
A(Y)=\sum_{i<j}|c_iY_i-c_jY_j|,
\quad
G(Y)=\begin{cases}A(Y)/(nS(Y)),&S(Y)>0,\\0,&S(Y)=0.\end{cases}
\]

库存必要域可先取

\[
\mathcal R_{\mathcal D}=
\{Y_i\in\mathcal Y_i:\ B^-\le\sum_iY_i\le B,\ G(Y)\le\gamma_U\}.
\tag{1}
\]

它保留硬整数库存资源，放松路由、装载、时间及其它未纳入耦合。更强必要资源可在证明后加入；任何放松须包含原域的全部物理库存。原支持如来自cutoff/子域收缩，须绑定该scope。

对应的最低目标completion为

\[
\phi_{\mathcal D}(Y)=\max\{\gamma_L,G(Y)\}+\sum_i h_i(Y_i).
\tag{2}
\]

原合法整数completion满足\(g+P_e\ge\phi_{\mathcal D}(Y)\)。**不能错误要求\(G(Y)\ge\gamma_L\)**：物理Gini较低而模型g取较大值仍可能是合法completion。\(G(Y)>\gamma_U\)则不能在当前g区间中完成。

默认oracle不另加原目标cutoff，以较宽域给有效行，减少不必要耦合。若加入cutoff或其它条件，应相应证明和绑定；bin松弛产生的库存还须满足真实条件，才能用作该oracle的可行上界。

### C2. 联合分布与支持不等式

对库存向量Y，令\(v(Y)\)为各站one-hot selector。对给定分数边际s，研究

\[
\Theta_{\mathcal D}(s)=
\min_{\lambda\ge0}
\left\{\sum_{Y\in\mathcal R_{\mathcal D}}\lambda_Y\phi_{\mathcal D}(Y):
\sum_Y\lambda_Y=1,\ \sum_Y\lambda_Yv(Y)=s\right\}.
\tag{3}
\]

若不存在共同分布，值为\(+\infty\)，首先是资源/域投影不相容；若共同分布存在但其最小期望目标高于旧\(g+P_e\)，才是目标上图缺口。单站或两站局部耦合不保证共同多站分布存在。

给定有限状态势\(\pi_{iy}\)，定义全域pricing

\[
\alpha_{\mathcal D}(\pi)=
\min_{Y\in\mathcal R_{\mathcal D}}
\left[\phi_{\mathcal D}(Y)-\sum_i\pi_{i,Y_i}\right].
\tag{4}
\]

任意合格下界\(\underline\alpha\le\alpha_{\mathcal D}(\pi)\)都给出有效行

\[
\boxed{g+P_e\ge\underline\alpha+
\sum_i\sum_{y\in\mathcal Y_i}\pi_{iy}s_{iy}.}
\tag{5}
\]

证明：整数状态只有\(s_{i,Y_i}=1\)，(4)逐点保证右端不超过\(\phi\)，再由(2)得到(5)。故非最小g/e completion也被保留。行可用于同域或其兼容子域；不能将小子域定价行无条件上送父域。

若实际写入系数由\(\pi\)变为\(\widehat\pi\)，可用每站one-hot关系安全运输截距：\(\widehat\alpha\le\underline\alpha-\sum_i\max_y(\widehat\pi_{iy}-\pi_{iy})\)，截距向下运输；也可复用既有有限域残差校正。定价、目标常数、写入系数和域须对应，不另建通用数值修复体系。

\(\pi=0\)只有标量floor。库存oracle忽略路由，其标量floor低于完整B的LP不意味着整个上图没有价值。应将非零势支持行放回同一个完整模型，再自由重优化比较。

### C3. Pricing下界、可行上界与发现过程

小域可以完整枚举(3)。实际域可用有限库存列及有界势的dual constraint generation寻找\(\pi\)：固定每站一个势为0消除平移自由，按目标尺度限制/归一化势，生成有用候选方向。势界只限制搜索能力，不影响通过(4)资格后的行有效性；无需本轮强制完整大规模列生成。

具体可解受限dual master：最大化\(a+\pi\cdot\bar s\)，对已有库存列\(Y^k\)约束\(a+\pi\cdot v(Y^k)\le\phi(Y^k)\)，并加势界与上述规范化；它只产生候选势和截距，最终截距由全域pricing的合格下界替换。

受限列master缺少其它库存约束，给出的截距不是全域安全下界。最终(5)必须使用全域pricing的合格lower bound；库存可行解只给pricing upper bound，不能倒用。势可以为负，pricing下界也可能为负，不能随手clip到0。

若已知\(L_{price}\le\alpha(\pi)\le U_{price}\)，当前点为\((\bar s,\bar\eta=\bar g+\bar P_e)\)，分别判断：

- \(L_{price}+\pi\cdot\bar s>\bar\eta\)，且差异超过已记录数值不确定性：**已证分离**。
- \(U_{price}+\pi\cdot\bar s\le\bar\eta\)：**该势方向不分离**，不推断其它势或整族无效。
- 两者之间：**oracle未决**，需要更好下界/上界或更细分母域；不能叫阴性结构结果。

上述两种确定结果也可作为定价的数学停止条件：已经得到有效分离时不必继续追求最优截距；已证该势方向不分离时可换方向。若势变为\(\pi'\)，旧下界不能原样复用；同一域上可安全修正为

\[
\alpha(\pi')\ge L_{price}(\pi)
-\sum_i\max_{y\in\mathcal Y_i}(\pi'_{iy}-\pi_{iy}).
\]

旧库存可行点可重新评分作为新upper；实际采用时仍区分新势、域与目标身份。

先用一元费用的整数总量DP研究仅“支持＋硬库存预算”的投影，可作为低成本归因对照；它不自动处理Gini区间、路由或完整目标。必要时再用同一\(\mathcal R_{\mathcal D}\)的零目标分离区分域投影与目标信息。明确每项结果究竟来自旧AP、整数资源相容性、Gini区间，还是新的目标联合性。

### C4. 为什么不能只把硬资源乘子化

R133风格的四站域\(Y_i\in\{0,1,2\},\sum Y_i\le3\)，\(h_i=\lambda|Y_i-1|\)，\(\lambda\approx.15\)。硬资源原整数目标最优为\(1/4+\lambda\approx.40\)。若只将总量约束乘子化，所有\(\nu\ge0\)都有

\[
q(\nu)=\min_Y[F(Y)+\nu(\sum_iY_i-3)]
\le\min\{4\lambda-3\nu,\nu\}\le\lambda,
\]

两个上界由全0与全1库存给出。取\(\nu=\lambda\)，由
\(\sum|Y_i-1|+\sum Y_i=4+2\sum(Y_i-1)_+\)可知\(q(\lambda)=\lambda\)。因此仅资源对偶仍留下1/4缺口。

这是已有目标困难的设计反例，不是超越GD/count的新严格性证明；相关正库存二值族可能已由GD闭合。本轮应寻找并核实对适用旧强参考仍严格的实例/结构，不能复述该例就宣布突破。

---

## D. 一条可执行的oracle预案：分母区间＋硬资源整数模型

Codex可以采用更好的等价/有效实现，但先建立清楚的参考oracle，不必先编写复杂专用图割算法。

### D1. 正分母覆盖与每bin模型

对实际支持内全部正S建立有限覆盖\([\ell_b,u_b]\)，\(0<\ell_b\le u_b\)。安全界来自当前支持及资源；不通过目标分母的LCM枚举所有精确有理S。覆盖可以按几何宽度或当前下界不确定性细化，不能遗漏尚未证明空的bin。

每bin用one-hot整数选择\(x_{iy}\)，保留

\[
Y_i=\sum_y yx_{iy},\quad\sum_yx_{iy}=1,\quad
B^-\le\sum_iY_i\le B,\quad \ell_b\le S(Y)\le u_b.
\]

令\(a_{ij}\ge c_iY_i-c_jY_j\)、\(a_{ij}\ge c_jY_j-c_iY_i\)，\(A' =\sum_{i<j}a_{ij}\)。取

\[
q\ge\gamma_L,\qquad q\ge A'/(nu_b),\qquad
A'\le n\gamma_U S(Y),
\]

最小化

\[
H_b=q+\sum_{i,y}\bigl(h_i(y)-\pi_{iy}\bigr)x_{iy}.
\tag{6}
\]

该模型不含route列和G*S乘积，约有\(\sum_i|\mathcal Y_i|\)个选择二进制及\(O(n^2)\)连续变量。N-B35约537个状态，而不是完整路由模型的全部列。\(A'\)可以取真实绝对差之和；上限行恰好保留必要\(G(Y)\le\gamma_U\)条件。原\(\gamma_L\)必须通过max语义保留，不能把它变成物理Gini下限。

取得各bin的合格下界\(L_b\)，则

\[
\underline\alpha=\min_b L_b
\tag{7}
\]

是正S部分pricing的下界。证明为空的bin可移除；未完成bin必须保留有效下界，不能仅对已完成/有好结果的bin取最小值。

未求bin也可先用安全有限界\(\gamma_L+\sum_i\min_y[h_i(y)-\pi_{iy}]\)，或在更宽硬库存域上做一元费用DP进一步收紧；它们允许忽略bin/Gini约束来放松，但不能错误提高下界。后续逐bin改进，不因某bin尚未求解而遗漏全域覆盖。

由于\(c_i>0,Y_i\ge0\)，S=0只可能Y=0。若该状态属于oracle域，另行加入其精确表达\(\gamma_L+\sum_i h_i(0)-\sum_i\pi_{i0}\)参加全域最小值；不能忽略零库存，也不能在\(\gamma_L>0\)时把其代价写成只有惩罚。

整数库存候选按真实\(\phi(Y)-\pi\cdot v(Y)\)重算，给pricing上界；它尚未满足完整路由/时间，不能用作BRP的物理U。

### D2. 分母近似误差与求解误差分开

在正S bin内，令\(g_{max}=\min\{\gamma_U,(n-1)/n\}\)。则

\[
0\le G(Y)-A(Y)/(nu_b)
=G(Y)(1-S(Y)/u_b)
\le g_{max}(1-\ell_b/u_b).
\]

\(\max\{\gamma_L,\cdot\}\)不扩大差，惩罚与势项相消，因此

\[
0\le[\phi(Y)-\pi\cdot v(Y)]-H_b(Y)
\le\varepsilon_b:=g_{max}(1-\ell_b/u_b).
\tag{8}
\]

这里\(H_b(Y)\)指辅助量取最小合法值的surrogate。实际oracle误差还包含bin整数求解gap；单列分母近似、MIP gap、定价上下界及数值资格，不能用(8)抹掉尚未解决的整数优化误差。

优先细化会限制全域lower/分离判断的域，或改善其整数模型；不按时钟在若干秒后切换算法。离线诊断有正常wall cap；未来线上规则应按数学误差、支配、收敛证据或确定性状态/迭代条件定义。整次完整算法的全局实验时间窗仍允许。

### D3. 专用结构作为有依据的深化选项

绝对比率差在有序标签上具有Monge/子模结构；固定分母系数时，一元代价＋两两绝对差可联系经典图割工具。可研究图表示、资源对偶下界、图割分支定界或其它专用pricing，减少参考MILP的成本。

图割并非新通用理论；Ishikawa(2003)、Kolmogorov–Zabih(2004)为可查的经典来源。硬库存/S约束以及\(\gamma_L>0\)时的max项不能自动交给一个裸min-cut解决。仅资源Lagrangian/min-cut可作为有效下界和机制对照，不能冒充已消除C4的缺口。若参考MILP已有足够成本与信息，不必为使用图割而重写。

---

## E. 分层研究与实验安排

### E1. 小域正确性与非重复关系

用现有完整小域及少量有明确目的的生成域，核对(1)–(8)、非最小completion、零状态、势的符号、bin覆盖和子域运输。R133只作为已知控制；新增严格例应针对当前适用AP/GD/count等参考，并给完整可行扩展或精确小域求解，不能只比较两个标量公式。

优先回答：硬资源与平均资源是否不同；差异是投影相容性还是目标上图；等/异质目标、资源紧度或分母范围分别影响什么。不要扩成所有边界组合的测试工程。

### E2. 真实保存域上的强参考与新信息

建议先覆盖三种角色：N-B35-S（本轮困难、资源floor正）、K-35-U（历史surplus困难域）、N-C20-U（CPF根无增量但正目标证书）。可按实际保存证据调整；输入、目标、域与选择理由在新结果前记录。

先恢复合格B模型/点与旧AP结果，补必要强参考LP；在自由重优化后的点上研究零势floor、资源投影与非零势上图支持。不重求已合格同域baseline，不将旧scope的方向或值冒作当前域结果。

根据未解问题扩展到K20（STOCK证书强锚）、RB35（历史重要回退锚）、RX20（零目标/边界）中的适当域，优先复用保存根或实际子域。初始设计约3个物理域，必要时扩到约6个；这不是硬性数目或新盲测声明。至少形成跨结构的判断，避免只在最容易出现正例的旧点上研究。

每个实际域保留：原B与强参考值、AP等旧信息、oracle域/势、上下界与bin误差、已证分离/方向阴性/未决、加入新行后的完整自由LP值、构造/定价/LP费用、行列规模。原cutoff和所有旧变量自由，不能固定g、s、t或其它辅助量制造增量。

### E3. 给一次真正的深化机会

根据观察，把主要预算用于一个有依据的瓶颈，而不是第一格无增量就结束：

- 信息强但pricing下界慢：改善MILP/Monge下界/分母细化/势选择与复用，保留硬资源语义。
- 成本低但只重现旧AP或资源投影：改变支持方向或研究更有解释力的联合目标缺口，不换名重复旧结果。
- 标量floor弱：检验非零势支持行；低标量值不能否定全上图。
- 下界未决：明确求解预算与结构瓶颈，允许在总量内延长关键域或做一轮结构修订，不能将未决报告为数学阴性。
- 已证新信息但当前表达昂贵：研究少量支持行、原变量运输或域继承；根值压缩不自动意味着全树等价。

若多域强参考已显示当前对象没有有用剩余信息，或明确不可承受，完整记录这项结论即可。进一步转向不同对象需说明证据，不自动追加所有新方向。

---

## F. 条件生产实现与完整算法检验

只有在得到超出相关旧信息、成本有合理希望的机制后进入生产。离线理论/对象级结论可以完整交付，不强求新入口。

若进入，冻结一个统一候选J，明确它是否保留AP/GD等旧行、怎样生成新势/下界、何时停止生成、在哪些兼容域复用。可有实际需要的辅助变量/求解；全部费用由本臂支付。完整臂从自身H和当前实际模型出发，不注入历史最好解、历史cutoff、离线已付费方向或另一臂结果。

旧AP/GD仅为诊断强参考，并不自动成为线上组件。若最终组合确实含这些旧强化，B/J完整收益首先归于整个组合；新机制的增量采用必要的同PE旧强化对照澄清，不以B默认APoff制造“新机制独占收益”的解释。

最低新资格覆盖实际公式与模型单位、pricing上下界方向、全域bin覆盖/零状态、非最小completion、原Start、新行/列Native读回及scope、default OFF和旧入口、合法超时/未决时不产生无资格界。复用既有R134与封存链；没有出现的通用故障不展开为全面系统重写。

建议完整容量为 **3个困难B/J配对各2400秒/臂＋1个证书B/J配对各1200秒/臂**，共16800秒。具体角色由已冻结的结构问题确定，优先覆盖N-B35、K35、RB35和适当证书角色；不按已见完整输赢替换格子。

进入一个合格配对后按正常窗口完成。首个普通损失不自动否决整个研究；结合多域证据与轨迹决定后续。若出现明确严重回退、成本失控或有效性问题，应先解释和定向修正，避免盲目完成无信息面板。方法变更后建立新身份/配对，不与旧版本混算。

另有决定型容量可用于一个较长窗口（例如B/J各7200秒）、新机制对旧强化的完整归因，或一个实质结构反差。使用前写明能改变什么判断；不同时默认展开多Seed、P-GRB大网格和各种组合。Seed0为默认，不为新轮次自动翻倍。

---

## G. 预算、指标与研究结论

| 阶段容量 | 秒 | 作用 |
|---|---:|---|
| 数学小域、参考oracle与定向资格 | 7200 | 建立正确对象和可执行工具 |
| 强参考及多域oracle/表达诊断 | 14400 | 分清旧信息、未决和真实增量 |
| 一轮有依据的结构深化 | 21600 | 给关键机制充分研究空间 |
| 条件生产资格 | 7200 | 仅支付真实新实现风险 |
| 条件完整比较 | 16800 | 3困难配对＋1证书配对容量 |
| 决定型长窗/归因/结构反差 | 14400 | 解决关键剩余不确定性 |
| 失败、验证及外层余量 | 4800 | 含必要复核和已发生失败 |
| **总上限** | **86400＝24h** | **可调拨、可提前完成** |

常规前8–12小时应能形成一份有内容的结构/oracle/表达研究；生产与完整槽不必全部进入。可将释放容量合理转给仍有清楚价值的研究问题，记录调整理由，不要求为了格式花满每槽。

新增程序构造、枚举/DP/定价、LP/MIP、资格、失败、own-H及必要验证按外层计一次，内部Runtime/Work不重复加；纯理论/代码写作、文稿、公开纯I/O和必要编译单列。启动新完整臂前预留其完整cap和验证余量；计量不完备如实披露，不为秒级账面精度补跑。

分别报告：

1. 有效性、域/目标关系与对旧表达的严格性；
2. oracle是否求到了足以判断的上下界、代价和误差来源；
3. 实际完整LP增量；
4. 若进入生产，完整物理U、支持L、signed/relative gap、证书与总费用。

保留共同目标轨迹、Work、节点、simplex及AM路径。开放臂T_cert为空；不同最终U的首次取得时间不称共同目标加速；初始LP和Native root-after-cuts不代替终端支持L。

允许普通取舍，不要求每例全胜或绝对历史最优。原严重双开放参考可沿用为提示：U损失超过max(.001,5%·U_B)，且signed-gap损失超过max(.005,25%·gap_B)。它不是唯一采用条件，也不是整族有效性判断。

本轮可验收的主要结果包括：新的非重复结构关系及其范围；实际强参考上的新上图信息和可计算性；有用的完整统一候选；或者明确定位仍存缺口/计算瓶颈且有充分证据的阶段结论。不能把未解oracle称已证无效，也不能把一个新的LP正例直接称完整算法突破。

---

## H. 论文与阶段组织

形成一份可进入论文研究章节的叙述：稳定GI-TBC已有完整优势；R138–151的有效表达、局部收益和完整边界；本轮针对的是硬资源整数目标联合性，和单站传播、单车hull、旧inventory-routing分解有什么区别。

用一张证据表说明“旧AP/资源投影／新目标信息／oracle费用／完整表现”，同时保留失败和未决。图割、LP对偶、Lagrangian和有限支持分离使用已有理论时明确归属；新意应体现在本问题结构、非平凡关系、可计算机制与实际价值，不以工具换名或调用数衡量。

稳定论文可以同步整理，不等待新候选成功。更大研究预算用于深化有根据的缺口，不以一轮结果预先承诺OR层次，也不将推广到所有含决策分母问题设为必要条件。

---

## I. 额外复核、交付与工作区收尾

在昂贵研究/完整臂前，由非主要实现者复核关键推导和实验设计：

- 是否重做AP、GD、count、R104或R105–107；强参考是否同域、全部变量自由；
- \(\gamma_L\)非最小completion、pricing下界方向、负势/负截距、零状态和所有分母bin是否处理正确；
- 受限列master与pricing上下界是否混用，新的支持行是否真正对原整数completion有效；
- 预算是否支付全部当前计算，完整控制是否同PE/同目标/同窗口，调整是否改变了原问题。

交付前再核数学、数据、版本、费用与主张。问题按实际影响定向修正，不为已合格微小差值或未知假想风险无限补测。复核通过后给出本轮阶段判断和下一步最有价值的问题。

交付goal、历史排重/数学报告、oracle与实例域说明、实际实验/失败/未决、源身份和费用、研究结论、论文小节、独立复核及RESUME；进入生产时才交付生产候选/profile。可合并文档，按信息完整性验收。

正常提交推送并创建英文Draft PR，建议标题：

**Round152: study resource-feasible integer objective epigraphs**

按实际吸收状态选择main或核实后的R151临时base，读回base/head/Draft状态。不自动merge、force-push或删除旧分支。本轮不包含全项目历史清理。

**显式继承WORKSPACE_POLICY：**新增build/raw/temp/restore全部在`E:\codes\ExactEBRP-work`，保护`E:\codes\ExactEBRP`及用户修改。仅清理本轮已完成、可重建、已由公开恢复覆盖的临时/重复对象；保留唯一raw、失败、必要PE/DLL、活动树和旧历史。记录实际删除/保留，零删除可接受。

只打包新增必要证据，旧大包按固定commit/member hash引用；对新公开载体做一次有限恢复，不触发旧producer或求解。公开I/O问题不变成重跑旧性能的理由。

---

## J. 最小资料索引

- PR213：https://github.com/yifanXovo/TailoredExact/pull/213
- R151固定science：https://github.com/yifanXovo/TailoredExact/tree/3978b0532aec965816a80556988c531bd10be0c2/results/unified_exact_round151
- 当前目录关键文件：final_report.md、mathematical_analysis.md、LP_report.md、candidate_decision.json、candidate_manifest.json、candidate_freeze.json、confirmation_matrix.json、reports/full.json、reports/verified_U_trajectories.csv、cost_report.json、carrier_manifest.json、reuse_index.json、RESUME.md。
- R151正式B包：artifacts/campaign_confirmation_001.zip；SHA256 `04850db28e3a959055b3ba2aeb571c9e3296fdf48f057cfb389bebc6efa558c9`。正式C包002：`4d45ce820aea9a46af4ac020f97505359cc4d61acdabad82b5b63ed7a1e4a880`。
- R151诊断包：artifacts/diagnostics_qualification_failures_and_fees.zip；SHA256 `346ae7321247aa04089a72fd561915ba89b16e8ef02cb251fa04485378da405e`。003/004包只有未进入位置的identity，不能计作完整结果。
- 两个原B根按R151 reuse_index恢复自R150固定science；N-B35包003 SHA `952018137b3e8c4cd5cd53f9bf2230885fc4428810b90810fffdda5fa71fd5f1`；N-C20包001 SHA `5abb5c3111ed7388b4c4da163e78c8e77edb7ce884480aa00909d4aa119c12dd`。
- 原输入与目标：R137 input_manifest.json、matrix_frozen.json；N-B35-S仍为lambda=.15、T7200、35站/3车、Q=[20,25,30]，不同于旧R-B35-S-T2/rho1；N-C20-U为lambda=.15、T5400、20站/2车、Q=[30,30]。
- 历史：R133 joint_objective_gap_note.md；R135 ap_math_and_history.md/final_report.md；R55 station_state_convex_hull_proof.md、station_state_exactness_proof.md、penalty_budget_validity.md、penalty_cover_validity.md、penalty_cover_dp_design.md及penalty_cover_final_decision.json；R138–151数学/最终报告；R103–107数学与完整负结果；docs/current_mainline.md和unified_exact_research_index.md。
- 可复用实现：现有LP/MPS读取、实际矩阵/Start/物理验证、R134证明政策、独立费用封存；Round151Research.hpp仅作已完成cap机制参考，不要求把新oracle塞进旧接口。
- 经典来源：Ishikawa (2003), Exact optimization for Markov random fields with convex priors, https://hfs.w.waseda.jp/MRF.pdf；Kolmogorov & Zabih (2004), What Energy Functions Can Be Minimized via Graph Cuts?, https://www.cs.cornell.edu/~rdz/Papers/KZ-PAMI04.pdf。它们不自动解决本项目硬资源和分式目标。
- 本次外部审查附件：TailoredExact_Round151_Stage_Review.md、TailoredExact_Round152_Review_Evidence.zip。含R151独立复算、AP旧信息筛查及资源对偶反例；附件不可取可按上述固定原档和公式继续，无需等待或重跑旧完整实验。

**成功标准：在保留稳定论文算法的同时，弄清硬资源整数目标是否提供了超出既有表达、可计算且值得利用的新信息；有依据地推进理论、oracle或完整算法中的至少一层，准确记录其边界。**
