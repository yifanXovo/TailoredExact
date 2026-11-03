/goal

# TailoredExact 下一轮完整任务

## Round151：回到稳定 GI-TBC，检验独立惩罚传播的完整算法价值

**日期：2026-11-04（Asia/Shanghai）。建议轮次 Round151；编号已占用时沿实际下一轮继续。**

## 0. 目标与执行原则

R150 可以完整验收。两个选择外配置没有增加独立 GD 的完整优势：N-C20-U 保留相同 U 和证书，但认证时间增加43.73%；N-B35-S 的 U 恶化2.24%，L仅改善0.16%。D继续保留已知局部收益与研究候选定位，稳定主线仍为 R137 GI-TBC。与此同时，CPF在三个完整匹配LP上取得了超出PF的正增量，值得有限的完整成本检验。

本轮直接回答：**不继承缺乏广泛采用依据的GD，将资源惩罚信息独立传播到稳定GI-TBC的状态乘积，能否带来有用的完整算法提升？**

定义 B＝稳定GI-TBC，P＝B＋统一惩罚反馈，C＝B＋状态条件惩罚反馈。首选完整候选为 **C，GD off**；C已包含P所需的统一cap效果，不是先叠P再叠一套重复行。先在同一个保存B根上做小额P/C比较，再冻结一个统一候选进入完整实验。若LP与成本证据明确支持较简单P，可以在完整实验之前选择P并说明理由；不要同时扩展两套完整候选，也不按实例择法。

预算上限 **14400秒＝4小时**，允许提前结束。默认 **Gurobi Seed=0、Threads=1**；H seed 独立固定为 **20260626**。计时运行串行，与编译、重I/O和PDF导出错开；完整臂支付自身H、构造、全部求解与必要验证。沿用R134证明政策及已接受数值标准，不为tiny gap追求字面零差。

算法应统一、数学依据明确，不按实例名、规模或已知输赢打补丁，不以运行若干秒触发算法切换。有效界、域包含和实际支配可以用于省略冗余行；实验cap不是线上规则。目标是可写入论文的实质收益和可接受取舍，不要求逐例全胜、绝对历史最强或一定产生新算法。Codex可在问题与总预算内调整实现、顺序和有限诊断，运行前说明新增探索能改变什么判断。

---

## A. 起点、身份与工作区

| 项目 | 编写时核实的参考 |
|---|---|
| 仓库／前序PR | yifanXovo/TailoredExact；#212，Open Draft，未合并 |
| R150 branch／head | codex/round150-gd-confirmation-conditional-feedback；7cac24abd8bfffa96a9dc7569d9a93f1697881a7 |
| R150 fixed science | 59c4e398f385aa8525fe87a4212ed97554f093e8 |
| 现有生产源码 | 380a85f866bffb914036190f8ee2700ce8b55978 |
| 可复用旧PE／SHA256 | E:\codes\ExactEBRP-work\build-cache\round149\ExactEBRP.exe；373efa9a596aaf02fb332685515fcfe88df1b169cbe53b295ab6027140620295 |
| Native DLL／SHA256 | D:\gurobi1302\win64\bin\gurobi130.dll；9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88 |
| R149 fixed science | 3bb93fa2f4b8c267af8fae409864191e033c5bb2 |
| R137 fixed science | e735c3447eb1443713c700942d873de1783a4a26 |
| 编写时main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 稳定入口／配置 | scripts/paper_s2.py；config/gi_tbc_round137.json |
| 活动树／新增资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议branch／结果目录 | codex/round151-standalone-penalty-propagation；results/unified_exact_round151/ |

先读适用AGENTS.md、WORKSPACE_POLICY.md，检查refs、用户修改、活动进程和封存证据。main已吸收所需内容则从实际main继续，否则从核实后的R150继续并选择对应临时PR base；不等待合并，不机械回退参考SHA。

R150没有改生产源码或编译。若本轮进入生产实现，登记新的源码/PE身份，关键B与候选配对使用同一新PE；R150旧B/D只作历史背景。稳定及旧研究入口、配置保留原含义。B与候选均保留完整own-H、M-B/VD-P、pair-only、AM=.08、depth8、minimum width=1e-4，AP/STOCK/Shared-S/GD关闭，原物理T和目标不变。

---

## B. 已有证据与总体研究定位

### B1. 本轮承接的R150结果

| 角色 | 方法 | U | 支持L | gap% | T_cert／秒 | T_total／秒 |
|---|---|---:|---:|---:|---:|---:|
| N-C20-U | B | .245505069182 | .245505069182 | 0 | 284.812925 | 289.512449 |
| N-C20-U | D | .245505069182 | .245505049066 | .000008 | 409.372523 | 416.478758 |
| N-B35-S | B | .450291503263 | .389097919286 | 13.589771 | open | 2375.245628 |
| N-B35-S | D | .460394748354 | .389738525822 | 15.346878 | open | 2378.892966 |

N-C20的初始LP由.048357676071升到.129907632277，共同最终U却从37.188秒推迟到165.359秒，认证也变慢。N-B35初始LP由.327833772177升到.346856963718，最终U变差、支持L仅略好。根值、搜索路径、最终证据要分开；不能用“未触发严重阈值”代替采用理由。

| R150保存域 | 原PF值 | CPF值 | CPF−PF |
|---|---:|---:|---:|
| K20 | .237043344713575 | .237826346116704 | .000783001403129 |
| K35 | .206104958905020 | .206603355168264 | .000498396263243 |
| RX20 | .365603247853745 | .366724025832099 | .001120777978353 |

三个LP均为完整同域、全部变量自由；旧baseline未重求。新数值primal-dual差低于1.2e-15，但仍是浮点资格，不是有理最优性证明。K35旧PF诊断差约.000619046继续披露，新CPF数值dual高于旧保存primal，不依赖把旧dual当精确界。

R150实验费用5560.241266800秒、无新build；19个完整臂Native调用和3个独立LP均返回。7包/31703新成员、15个继承成员和两原输入完成公开恢复；本次独立复核也通过。返库卸载的附加审查helper遗漏及metadata schema假设已在同一封存证据上修正，不是需要R151再处理的生产故障。

### B2. 最近研究的价值与边界

- **稳定论文基础已存在。**R137已有完整算法、多角色比较、资源/权重变化、机制与参数实验；不重新开展一轮广泛“证明B可用”。
- **R138–142有真实库存/共同因子信息与局部证明收益。**例如K20 STOCK获证、Native侧放置归因和count条件传播；其困难角色取舍也已测试，不能视为全无价值，也不因某个局部强结果就要求统一采用。
- **R143–145有表达压缩与归因价值。**RN的根信息可保留到少量原变量行，K35有强局部结果；更强根表达仍未稳定转化为完整优势。
- **R146–150有廉价GD及资源传播成果。**GD独立于STOCK并有已知困难U收益；PF与CPF区分了标量隐含信息和产品表达信息。R150进一步收窄了D的推广范围。

保留强历史对照：K20 STOCK/Stock+GD约94.261/74.916秒获证；R140旧TC+STOCK Seed0的K35 U/L≈.650438712/.5682885263、RB35≈.3190804927/.2339272621；R145 RN-P K35≈.660923637174/.550645816146。它们的负结果、source/PE和运输差异同时保留，不是本轮免费匹配控制，也不要求新候选逐格打败全部旧变体。

已有AM调参、rescue、root-only、动态incumbent重建及条件F界传播不重复。R52更正为三个严重false-retain，同时存在父Work≈843.456获证、强制midpoint≈2651.321仍capped的正确保留负锚。R133证明过：即使service hull更强，整数目标epigraph缺口仍可存在，固定分母也不能消除该困难；CPF没有解决这个完整问题。

**本轮用一次有明确终点的完整检验收束当前根惩罚传播。**结果若仍只有LP价值，就保存结构成果与成本证据，结束当前实现的推广，不自动转入更精确条件oracle、迭代cutoff或新组合救援。后续更深研究应另有明确对象级缺口和可检验预案，不能把“还能切一个点”当作不断开新轮的充分理由。

---

## C. 独立于GD的数学构造

### C1. 资源与条件下界

在实际模型中读取已含lambda的非负权重，写成

\[
h_i(y)=\omega_i|c_i y-1|,\quad p(Y)=\sum_i h_i(Y_i),\quad
P_e=\sum_i\omega_i e_i\ge p(Y),\quad g+P_e\le U_0.
\]

连续资源放松为

\[
\mathcal R_0=\{Y:\ell_i\le Y_i\le u_i,\ B^-\le\sum_iY_i\le B\}.
\]

支持中的洞、整数性、路由与时间被放松，故它提供必要下界。使用当前臂自身root、own-U和实际系数；线上不借历史解或历史乘子。

固定一次非负资源乘子\(\mu,\nu\)，令

\[
a=\nu-\mu,\qquad m_i=\min_{\ell_i\le z\le u_i}\{h_i(z)+az\},
\qquad d=\mu B^- -\nu B+\sum_i m_i.
\tag{1}
\]

乘子可由已有有限资源分配选择，可靠性由固定乘子的保守弱对偶评价保证，不依赖近似greedy恰好最优。每个局部最小值只需盒端点和盒内折点。固定状态\(Y_i=y\)后，

\[
\delta_i(y)=h_i(y)+ay-m_i\ge0,
\qquad
d_{iy}=\mu B^- -\nu B+\sum_{j\ne i}m_j+h_i(y)+ay=d+\delta_i(y).
\tag{2}
\]

资源可行时拉格朗日约束项非正，故

\[
d\le d_{iy}\le\min\{p(Y):Y\in\mathcal R_0,Y_i=y\}.
\tag{3}
\]

这一证明没有使用GD行、Gini–Hoover不等式或STOCK。**GD是R150的历史测试载体，不是CPF有效性的前提。**但删除GD会改变连续放松；R150的CPF最优值与增量不能直接搬到B，须做下节的有限衔接。

### C2. 一个有效cap向量，不重复叠加PF/CPF

安全取值

\[
\underline p_0=\max\{0,\operatorname{down}(d)\},\quad
\underline p_{iy}=\max\{\underline p_0,0,\operatorname{down}(d_{iy})\},
\]

\[
\beta_0=\min\{\gamma_U^0,\operatorname{up}(U_0-\underline p_0)\},\qquad
\beta_{iy}=\min\{\beta_0,\operatorname{up}(U_0-\underline p_{iy})\}.
\tag{4}
\]

P在B上增加统一cap；C在B上直接增加有效条件cap：

\[
P:\ t_{iy}\le\beta_0s_{iy},\qquad
C:\ \boxed{t_{iy}\le\beta_{iy}s_{iy}}.
\tag{5}
\]

每个原状态最多一条有效新增上端行，无新列。保留原B行，不需要先加整组PF再加整组CPF。由于\(s_{iy}\ge0\)且\(\beta_{iy}\le\beta_0\)，在适用状态均被覆盖时，C条件行支配P统一行；实际运输后也要保留这一关系，而非只对理想系数作声明。

整数未选状态\(s=t=0\)；选中状态\(Y_i=y,t=g\)，由原cutoff和(3)得\(g\le\beta_{iy}\)。原本可行的非最小g/e completion也保留。该结论不要求g恰好等于物理Gini。

对每站局部块，\(s\ge0,\sum_y s_y=1,\sum_y t_y=g,\gamma_Ls_y\le t_y\le\beta_y s_y\)是状态依赖区间的凸包：对正质量取\(g_y=t_y/s_y\)，按s混合分支点即可。它不是跨站资源、路由或整数目标联合凸包；不能将\(\min_y\beta_y\)作为全局g上界。

### C3. 安全计算和子域继承

生产可复用已合格的区间算术与资源乘子选择，用保守前缀/后缀和计算(2)，总复杂度\(O(n+\sum_i|\mathcal Y_i|)\)。Python Fraction用作小额独立参考，不要求线上逐状态调用Python或求解LP。禁止从两个独立下界直接做\(\underline d-\underline m_i\)并声称结果仍为下界。

安全实现可直接取

\[
\underline d_{iy}=\operatorname{down}\left(
\underline c_0+\underline M_{<i}+\underline M_{>i}+\underline{h_i(y)+ay}
\right),
\]

其中各项分别保守评价\(c_0=\mu B^- -\nu B\)、两侧局部最小值之和及当前状态代价。

在根域计算并冻结cap向量。兼容子域保留相同输入、目标，资源可行域不超出根域，支持为根支持子集，cutoff和gamma区间不放宽。对当前子域D使用\(\min\{\gamma_U^D,\beta_{iy}^{root}\}\)，按状态判断实际收紧；本轮不动态重算乘子或因新incumbent中断重建。

三个关键边界：

1. **全局floor为0仍可能有条件收紧。**不能沿R149的`floor.lower>0`整组门槛屏蔽CPF。
2. **子域gamma_U≤beta0只说明统一PF冗余。**某些beta_iy仍可能更小，须逐状态判断。
3. **条件beta_iy<gamma_L只说明对应改善状态分支为空。**负条件beta不等于整个实例无解；给出有效signed行、已证明的状态排除或安全弱化即可。

beta向上运输。tiny项可安全放宽或省略条件化；若因此不能保留更强条件行，应退回有效统一cap，或明确实际已失去的包含关系，不能在纯B载体上漏掉必要uniform-only状态。已有验证过的舍入/运输策略足够，不为本轮重写通用数值层。

---

## D. 已完成的免费筛查与小额LP安排

### D1. 两个实际B根给出不同信息

本次独立审查直接解析R150纯B实际根模型、完整保存点、cutoff、状态支持、目标和资源约束，无新Optimize：

| R150纯B根 | 原合格LP值 | 当前根资源floor | 统一P点违反 | 条件C点违反 |
|---|---:|---:|---|---|
| N-B35-S | .327833772177116 | .2445 | 24状态，最大.0305402146754 | 26状态，最大.0614551559113 |
| N-C20-U | .048357676070725 | 0 | 0 | 0 |

N-B35当前root的U0=.5772179446388799，实际乘子mu=0、nu=.0075，beta0≈.332717944639，条件beta范围约[.085217944639,.332717944639]。这是当前收缩支持盒上的floor；历史`.21`来自更宽放松，不矛盾，也不能混用。

N-B35有537个状态：独立C需覆盖全部537个相对原gamma_U收紧的cap；其中472个进一步强于uniform PF。不能只复制“PF后条件增量”的472条而漏掉65个uniform-only状态。N-C20有490状态，其中470个cap可收紧，但旧合格最优点仍满足全部新行；全部beta为正。**点无违反不等于行族为空，也不等于完整搜索无作用。**

N-C20保存的合格最优点在新矩阵仍可行，按同一数值资格已足够说明无需重求该根LP来寻找增量。保留其后续完整证书成本反差，不购买一遍明知可保持旧值的LP。以上是保存浮点点与实际矩阵的资格结论，不冒充精确有理最优证书。

### D2. 只在N-B35同一根上衔接B→P→C

复用R150 N-B35纯B根的完整模型与合格旧LP值；所有旧目标、常数、cutoff、行、变量域和支持保留，全部变量在原bounds内自由优化。将保存的MIP模型作LP比较时，完整放松变量类型，并与原根LP资格语义一致，不意外保留整数列。

默认先做一个C LP。若C提供清楚的新优化信息，再做同域P LP，分开报告

\[
L_P-L_B,\qquad L_C-L_P,\qquad L_C-L_B.
\]

在实际包含关系成立时，\(Q_C\subseteq Q_P\subseteq Q_B\)，故\(L_B\le L_P\le L_C\)。若C无可分辨根增量，就没有必要为了寻找更大根增量再求P；可保存替代最优点并结束小额诊断。必要的数值检查允许在预算内定向处理，保留原标准，不重求全部旧baseline。

默认最多两个新LP、各Native cap120秒，Seed0/Threads1。保留真实MPS/解、系数、残差、数值界、行/NZ、构造与总费用，并核对删除新增行后与原模型语义一致。来源按J节固定成员恢复，不调用已关闭producer来生成替代证据。

不默认买K35、K20或第二物理域衔接，也不再测GDon/off完整因子矩阵。已有旧B点筛查可作背景，不能把其最大违反量当成新LP最优值。

### D3. 冻结唯一完整候选

优先C。P/C同域结果用于判断条件信息与成本，不设置“根值必须提升某百分比”的机械门槛：历史Native侧结果已经说明根值不能穷尽完整作用。若根增量不明显但存在具体可检验的搜索作用理由，可以进入一次预定完整B/C配对；先写明理由。

若P已给出主要信息，C无可分辨额外信息且其实际实现更复杂，可在完整结果出现前选择P作为较简单的统一候选。记录选择依据、唯一入口/参数与后续统一使用范围。下面用A表示冻结后的唯一候选（默认A=C）。既不强迫为CPF名称保留复杂度，也不在看到某个完整臂输赢后按角色换A。

---

## E. 最小生产实现与定向资格

将有效cap在当前臂首次正式Optimize前加入：

**自身H → 当前root资源/支持/权重 → 一次乘子与cap向量 → 首次正式模型 → 原根LP/probe/target/terminal。**

不增加source solve、额外根重优化或新列。原proof-root区间、AM几何与调度规则保留，搜索路径可因表达改变而自然变化；不要把后续路径差异当作实现错误。

R149原PF入口显式要求GD开启，embed也要求GD expected存在。因此本轮应建独立默认OFF控制/入口和自己的expected/readback，或在清楚边界内解耦实现；不能只改flags绕过旧资格，也不能伪造空GD记录。旧R149 PF、GD和稳定入口保持原行为。实际生产变动后登记新PE，并采用同新PE的B/A控制。

最低资格集中在新增风险：

- B/GDoff实际模型身份与OFF行为；新cap进入首次真实模型，model SHA、cache/backend和Native读回对应。
- 已加权单位、一次根乘子、leave-one-out方向、uniform-only状态覆盖、实际系数包含关系；与Fraction参考作有限交叉核对。
- 全局floor0但条件floor正、uniform被子域支配但部分条件cap仍有效、条件空分支、tiny/zero运输的必要边界。
- 一个代表实际模型的完整物理Start及合法非最小epigraph completion；兼容子域/支持子集与冻结根scope；保留无模型即完成own-H的合法路径。
- 真实producer调用全部返回、封存闭合、外部证明资格与费用沿用；不预设固定调用数、GD行数或实际split数。

可复用R149资源算术、行运输、R150 Fraction与实际LP检查、现有first-call-SHA reader和R134验证。仅为本轮真实差异做资格，不重做全历史面板。若确需一次短生产资格，在资格预算内运行并记录；不要额外购买一轮通用数值、日志或恢复系统改造。

---

## F. 有终点的完整实验

### F1. 首个困难角色：N-B35-S

| 项目 | 配置 |
|---|---|
| 原输入 | results/unified_exact_round137/inputs/N-B35-S.txt |
| SHA256 | 80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98 |
| 物理配置 | CABI；35站/3车；Q=[20,25,30]；shortage、compact；T7200；pickup/drop60秒 |
| 目标 | lambda=.15；Omega18.32；rho2.748 |
| 完整新臂 | 同新PE的B、A，各cap2400秒，各自own-H |

它不同于R-B35-S-T2，不能复制后者rho=1的目标。该角色当前B根有真实传播缺口，且D在本轮确认失利，可以直接判断独立传播相对稳定B是否有价值。已知/已暴露状态如实保留，不称新盲测。

冻结两臂物理数据、T、目标、H seed、Native设置与窗口，再运行；不注入旧最好解、另一臂H或历史cutoff。已进入合格完整臂不因途中输赢改变窗口。

首对按物理U、外部支持L、signed/relative gap、证书与完整费用共同判断。允许普通损失和可解释取舍；若只得到更强根值而完整结果没有可接受价值，可直接收束本轮，不自动用剩余钱去找正例。

### F2. 条件进入证书保留角色：N-C20-U

首对表现出实质收益或明确值得检验的取舍时，进入同新PE B/A，各cap1200：

- 输入 `results/unified_exact_round137/inputs/N-C20-U.txt`，SHA256 `93b93b6abed55cf97f8ee21ddd85fb8501554b8e4c35bb997ae75782f1f98e16`。
- CITI；20站/2车；Q=[30,30]；surplus、compact；T5400；pickup/drop60秒；lambda=.15，Omega10.477509，rho1.57162635。
- 这是正目标且已有B证书的成本反差；当前root没有CPF数值增量，仍可检验新增行在Native与子域中的影响。

若首对已不支持推广，且该证书角色没有会改变结论的独立问题，就不自动运行。保留证书也不等于免费：比较同资格T_cert与含验证T_total，不把小gap强行改成字面零。

### F3. 至多一个有决定价值的澄清

容量4800秒仅用于一个预先说明的问题，例如：

- 若A=C且首对有实质收益，需要判断uniform还是conditional部分影响完整结果，可补同新PE的P对照；沿用对应B/A的全部冻结配置与相同cap（N-B35为2400秒），不将澄清容量理解为延长单臂窗口。已有本轮合格B/A按原身份复用，不重跑它们。
- 需要一个结构反差才能决定有限候选定位，可选择一组B/A（每臂最多2400）。选择理由必须来自未解问题，不仅是历史哪个角色更可能赢。

不默认同时做P归因和第三角色，不因候选阴性自动转入GD/STOCK/Shared-S组合。默认不补P-GRB网格、额外Seed、长时收敛、大实例或AM阈值面板；这些属于之后明确的论文实验计划。

澄清后可以提出较简单P的有限推荐，但不改变已冻结的A、不替换其核心配对，按实际覆盖范围陈述证据。

---

## G. 指标、采用判断与预算

分别报告四层证据：整数有效性/局部表达关系、保存点分离、匹配LP值、完整own-H算法结果。初始LP、Native root-after-cuts与终端外部支持L分开。开放臂T_cert为空，cap附近总时差不称加速；不同最终U的首次取得时间不当作共同目标速度比较。

保留已有witness轨迹、Work、simplex、节点、AM target/split记录解释观察，不新建全面因果归因系统。不同source/PE的旧结果保留为历史，不能混成当轮控制或独立新样本。

采用可以是：

1. **B载体上的表达/LP结果成立，完整价值不足：**保留理论与实验，关闭当前根惩罚传播的完整推广；稳定B继续作为论文算法。
2. **完整收益实质且取舍合理：**推荐一个统一有限增强候选，明确实际覆盖范围、证书成本与未解问题；不自动替换稳定默认或宣称广泛稳健。
3. **较简单P更有依据：**按正式前冻结或有限归因的实际证据收束到简单统一方法，不为条件化标签夸大贡献；局部一次对照不能直接充当广泛采用资格。

不要求每例全胜。原严重双开放参考可沿用：U损失超过max(.001,5%·U_B)，且signed-gap损失超过max(.005,25%·gap_B)，是明确严重信号；低于阈值不是采用的充分理由。无论阳性或阴性，本轮都要给出结束判断。

| 阶段容量 | 秒 |
|---|---:|
| 同域P/C衔接LP、必要实现算术及定向资格 | 1200 |
| N-B35-S：B/A各cap2400 | 4800 |
| 条件N-C20-U：B/A各cap1200 | 2400 |
| 至多一个明确决定型澄清 | 4800 |
| 失败、验证超窗口与外层余量 | 1200 |
| **总上限** | **14400＝4h** |

容量可调拨，不要求花满。默认最多四个核心完整臂；早获证按真实费用，启动新项前预留完整cap与验证余量。释放容量不重复计算；没有进入的澄清不计已花费用。

所有新增own-H、算术/构造、求解、资格、失败与必要后验验证按外层计一次，内部Runtime/Work不重加。纯理论/文稿、公开纯I/O及必要编译单列。计量不完备如实说明，不为追求秒级账面精确补跑搜索。

---

## H. 论文组织与总体阶段审视

更新一节可进入论文的统一叙述和一张证据表，无需重写全部稿件：

1. 稳定B解决什么原问题、已有完整算法与benchmark证据是什么。
2. 全局资源对偶如何给出条件代价差，如何在不依赖GD的情况下进入已有状态产品；C与P的包含关系及实际运输边界。
3. 根表达、初始LP和完整有限搜索的区别；用R150 GD“根显著更强而完整表现更差”及本轮结果给出具体边界，不作唯一因果归因。
4. 最近R138–150已有库存证明收益、Native放置、RN压缩、GD局部收益和PF/CPF表达成果；同时尚未解决R133整数目标一致性及全路由—装载—时间耦合。

本文有论文基础与研究空间，不意味着每轮必须产生新的默认算法。对于更高层次主张，关注结构解释、算法机制及可复核完整收益；不将推广到所有分母含决策变量问题设为必要条件，也不把更多valid rows或更多实验数量自动等同于更高期刊贡献。

本轮结束时明确后续选择：有用则将有限候选纳入论文并按需要安排最终大规模/长时实验；无充分完整价值则结束当前传播实现的优化链，将已知结果组织成文。更深研究可另行针对真实整数目标/联合资源缺口提出预案，先证明非重复、可分离且能影响目标，避免未经分析的大规模重构。

---

## I. 独立复核、交付与工作区收尾

昂贵完整运行前由非主要实现者核查：

- 新B载体、GDoff契约和实际scope正确；不继承旧CPF-after-PF的缺状态行组。
- (1)–(5)符号/单位/舍入与真实模型一致，floor0、子域支配和条件空分支处理正确；原整数completion和Start保留。
- LP对照只有必要新信息，N-C20根不重求；新PE B/A与源身份匹配，预算和条件进入合理。

交付前再次核对数学、原始数据、费用、版本与论文主张；重点避免把更强根界当作完整优势，把研究only父方案的改进当作稳定B提升，或把普通损失自动否决。实质问题定向修正，通过后收束，不因已合格微小数值差再开完整运行。

交付goal、数学/阶段报告、唯一生产候选及profile（若已进入生产）、实际进入的LP与完整结果、原始证据/失败、费用与身份、采用结论、论文小节、独立复核及RESUME。文件可合并，按信息完整性验收。

正常提交推送，创建英文Draft PR，建议标题：

**Round151: evaluate standalone resource-penalty propagation against stable GI-TBC**

根据实际吸收状态选择main或核实后的R150临时base；读回base/head、Draft与交付状态。不自动merge、force-push或删除旧分支，不借本轮再开全项目清理。

仅打包新增必要证据，旧大包以固定commit/member hash引用。对新公开载体作一次有限字节/成员恢复，纯I/O建议累计30分钟内收束，不触发Optimize、Native或编译。附件不可取时依J节固定来源和公式继续，不重跑旧性能。

**显式继承WORKSPACE_POLICY：**新增build/raw/temp/restore全部在`E:\codes\ExactEBRP-work`；保护`E:\codes\ExactEBRP`与用户修改。交付后只清理本轮已完成、可重建且已由公开恢复覆盖的临时/重复对象，保留唯一raw、失败、必要运行资产、活动树与旧历史。记录删除/保留及字节，零删除可接受。

---

## J. 最小资料索引

- 当前PR：https://github.com/yifanXovo/TailoredExact/pull/212
- R150固定science：https://github.com/yifanXovo/TailoredExact/tree/59c4e398f385aa8525fe87a4212ed97554f093e8/results/unified_exact_round150
- 该目录：final_report.md、mathematical_analysis.md、LP_report.md、candidate_decision.json、candidate_manifest.json、confirmation_matrix.json、cost_report.json、carrier_manifest.json、reuse_index.json、RESUME.md；reports/full.json、reports/verified_U_trajectories.csv、reports/R147_selection.json。
- 纯B N-B35原始包：artifacts/campaign_confirmation_003.zip，SHA256 `952018137b3e8c4cd5cd53f9bf2230885fc4428810b90810fffdda5fa71fd5f1`。
- 纯B N-C20原始包：artifacts/campaign_confirmation_001.zip，SHA256 `5abb5c3111ed7388b4c4da163e78c8e77edb7ce884480aa00909d4aa119c12dd`。
- R150 CPF档：artifacts/CPF_diagnostics_and_fees.zip，SHA256 `43b14a1945b47be32e3e1118de6fe61e96f09872dfe878e4d0d45c5fb629f196`。其原PF来源为R149固定science的artifacts/diagnostics_qualification_failures.zip，SHA256 `09a128897c372e3c46c98af18418852080348c639fea03c843d22aec865b332e`。
- 两原输入、目标与S2向量：R137固定science的results/unified_exact_round137/input_manifest.json、matrix_frozen.json、inputs/N-B35-S.txt、inputs/N-C20-U.txt；保持原SHA，不生成替代实例。
- 实现：include/Round149Research.hpp的floor/原uniform-only限制；scripts/round150_math.py的Fraction参考；scripts/round150_lp.py的完整MPS资格；scripts/round150_campaign.py/read.py的冻结/身份/first-call语义；src/main.cpp、src/PaperExternalGiniTree.cpp、src/GurobiBaseline.cpp的旧PF入口与接入。新研究入口可独立实现，不改变旧标志含义。
- 历史：docs/current_mainline.md、docs/unified_exact_research_index.md、R133 joint_objective_gap_note.md与R138–150最终报告；WORKSPACE_POLICY.md。
- 本次交付：TailoredExact_Round150_Stage_Review.md；TailoredExact_Round151_Review_Evidence.zip。包内数学复算保留两个实际纯B根的模型/解身份、全行残差、P/CPF筛查与条件系数；恢复索引说明原档与脚本参数。不要把外部审查的零求解筛查写成R150新增实验。

**成功标准：明确资源惩罚传播能否作为一个独立、统一、数学清楚且完整成本合理的稳定B增强，并准确收束当前研究链。有效采用、有限候选、只有表达价值或停止推广，都是可验收的结论。**
