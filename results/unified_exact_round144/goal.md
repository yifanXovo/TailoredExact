/goal

# TailoredExact 下一轮完整任务清单

## Round144：将 RN 信息投影到原变量——保留根界并检验完整搜索成本

**日期：2026-11-01。建议轮次：Round144；编号已占用时沿实际下一轮继续。**

## 0. 目标、优先级与自主权

R143 可以验收。RN 在四个匹配连续 LP 上带来真实的完整目标提升，且超出旧 TC+stock 的信息；完整同 PE 测试中，K35 的 U 改善、L 回退，RX20-T1 收敛到相同目标但略慢。当前 RN 不晋升主线，稳定 R137 GI-TBC 保留。

本轮研究：**能否通过一次便宜的 RN 连续求解，将其有用信息投影成原 selector／g 上的结构约束，使正式 LP/MIP 不再携带 RN 附加列，并得到更好的完整计算结果？** 主候选暂称 RN-P。

先核查投影的有效性、实际保留的 LP 信息与成本，再测试一个统一候选。默认使用一条全 RN 块的对偶聚合投影行；允许根据明确观察做一个小的相关改进，不预先铺多种聚合、分组、placement 或 callback 网格。

新增实验计算总上限 **8 小时**，不要求用满。Codex 可调整少量诊断域、顺序、等价实现和条件对照。单个角色的轻微混合结果不是一票否决；综合 U、L、收敛时间、完整成本和不同资源角色判断。明确无效、严重回退或成本不合算时及时收束，不强求每例获胜。

所有未明确多 Seed 的新求解显式用 **Gurobi Seed=0**；必要的有限确认用 Seed=1。H seed 固定 20260626 并单列。计时求解单线程、串行，编译、重 I/O 和 PDF 导出错开。

算法保持统一数学依据：不按实例身份或大小打补丁，不按运行若干秒切换方法或 leaf。允许依有效作用域、支持、界和数学冗余生成或省去约束。实验 cap 与算法规则分开。

---

## A. 起点与已知结论

### A1. 版本、工作区与算法载体

| 项目 | 编写本 goal 时核实的参考 |
|---|---|
| 仓库／前序 PR | yifanXovo/TailoredExact；#205，open／Draft，未合并 |
| R143 branch／head | codex/round143-reciprocal-normalization；066fdb672b4330f4de9e9778308f07f1752152f1 |
| R143 固定 science | 516f89f2e23bfad0238c8423bfb9809c308fdec9 |
| R143 生产源码 | 85bd2304866942fd5b397970c5ef4099bb1b73fb |
| R143 PE SHA256 | eaa6dc5d0091a1f3a38a0374aeccab28e94bff94606339c62b385b48cb7d44b1 |
| 编写时 main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 稳定入口／配置 | scripts/paper_s2.py；config/gi_tbc_round137.json |
| R143 对照入口／配置 | scripts/paper_s2_rn.py；config/gi_tbc_rn_round143.json |
| 活动树／新资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work\ |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议 branch／结果目录 | codex/round144-rn-projection；results/unified_exact_round144/ |

先读适用 AGENTS.md、WORKSPACE_POLICY.md，核实 refs、未提交内容、进程和资产。main 已吸收所需版本时从实际 main 继续，否则从已核实 R143 继续并以其为临时 PR base；不等待合并，不机械回退参考 SHA。

算法载体仍为稳定 R137：自身 H、M-B/VD-P、pair-only、AM=.08、depth=8、minimum width=1e-4、AP off 及 R134 证明政策。新候选正式模型中 stock、TC/TC2、count disjunction、CP 和持久 RN 块均关闭，只新增本轮合法投影行。独立 RN 来源模型可显式使用 R143 生成器。新研究开关默认关闭，所有旧入口和开关语义保留。

### A2. R143 已完成的科学与工程范围

| 匹配域 | 旧完整 LP 目标 | RN 完整 LP 目标 | 增量 |
|---|---:|---:|---:|
| K35 BASE | .200177661949 | .228090496924 | .027912834974 |
| K35 TC+stock | .218088779014 | .228090496924 | .010001717910 |
| RX20-T1 BASE | .331594316287 | .389761616211 | .058167299925 |
| RX20-T1 TC+stock | .377557530297 | .394121978997 | .016564448700 |

四个 LP 均保留完整旧矩阵、目标、cutoff、支持和 g 域。BASE 的 t 界也带入物理库存信息；较强 TC+stock 对照确认增量不止来自这部分旧信息。

同 PE 的正式完整结果：

| 角色／方法 | U | 支持 L | 相对 gap | Production／Total 秒 |
|---|---:|---:|---:|---:|
| K35 stable-off | .692854358631 | .557158765933 | .195850096067 | 2371.142459／2375.260633 |
| K35 RN | .681258498381 | .542931774252 | .203045869458 | 2371.108507／2377.137466 |
| RX20-T1 stable-off | .645325030386 | .645325030386 | 数值 0 | 22.206689／23.398734 |
| RX20-T1 RN | .645325030386 | .645325029589 | 1.24e-9 | 23.490135／24.926559 |

K35 的 U 改善约 1.674%、L 回退约 2.553%，相对 gap 增加 **0.7196 个百分点**；RX20 的生产时间增加约 1.28 秒。两者支持暂不晋升当前实现，但不能据单个负面端点断言其他角色永远没有决策价值。原 goal 允许在优先对后停止，因此 R143 仍可完整验收，无需追补旧全面板来修正措辞。

R143 共 22 次完整／资格 Native 调用及 4 次独立 LP，均返回；两次诊断工程失败发生在 Optimize 前，已修复并保留。实际新增实验费 4880.559824800 秒，约 1.355711 小时。没有需要另开修补轮的普遍数值认证问题。

### A3. 为什么优先研究表达成本

实际 Native 日志显示：

| 角色 | 预处理后列数 old→RN | 完整节点 old→RN | 完整 Work old→RN |
|---|---:|---:|---:|
| K35 | 7647→8803 | 16825→10779 | 4691.01→4999.13 |
| RX20-T1 | 1369→1646 | 2621→1620 | 29.54→34.97 |

K35 原新增 1170 列有 1156 列仍保留；RX20 原新增 354 列有 277 列保留。K35 根 simplex 迭代从 5188 增至 22953，但 root cuts 后的界也从 .42856 提高到 .44900；RN 信息没有立即被原生 cuts 抹平。平均 Work／节点增加只是描述，不能单独归因于列数，但它与规模、迭代量共同支持本轮假设。

全部正式位置 outer split 为 0。K35 的 RN 曾在约 1200／1800 秒的日志位置双端领先，最后旧方法追高 L；RX20 的 RN 还改变了实际 AM 资格路径。因此本轮继续完整窗口，保留完整方法口径，不同时修改 AM。

---

## B. 投影主线及根目标保持关系

### B1. 沿用已证明的 RN 块

设 x 为全部原变量，z 为 RN 新变量 t、w、归一化库存及归一化差异。R143 的完整来源 LP 为

\[
\min\{c^Tx+c_0:x\in P,\ Ex+Fz\ge d,\ \ell\le z\le u\}.
\tag{RN-LP}
\]

这里 P 保留原矩阵、变量界、原目标、g 域及 cutoff；RN 新列目标系数均为 0。不等式统一成 ≥，等式仍可用自由乘子。只将实际 RN 行纳入 E、F、d，不把旧目标 cutoff 或原路线行混进所谓 RN 结构行。

使用 R143 生产中已有且已证明保投影的有限界：

\[
t\in[L_t,U_t],\quad 0\le w_{iy}\le U_t,\quad
0\le\widehat Y_i\le M_iU_t,\quad 0\le\widehat h_{ij}\le1.
\]

旧独立诊断模型的部分新增列上界为无穷；本轮来源可加入这些生产 caps。不得把旧文件的无穷 UB 误当作有限数值。

### B2. 任意合法乘子都给出有效原变量约束

对 RN 行取符号正确的乘子 β：≥ 行非负，等式自由。定义

\[
a=E^T\beta,\qquad r=F^T\beta,\qquad b=d^T\beta.
\]

RN 推出 \(a^Tx+r^Tz\ge b\)。令有限盒的支持函数为

\[
\sigma_{[\ell,u]}(r)=\max_{\ell\le z\le u}r^Tz
=\sum_j\max(r_j\ell_j,r_ju_j).
\]

于是得到只含原变量的有效行

\[
\boxed{a^Tx\ge b-\sigma_{[\ell,u]}(r).}
\tag{PC}
\]

**不要求 r 在浮点中恰为 0。** 盒支持项直接吸收残余新列系数；合法性来自行组合与有效有限界，不依赖对偶最优性。RN 行仅连原 selector 和 g，所以最终 PC 不应残留 RN 新列。

### B3. 精确最优对偶下，一条全块 PC 保持匹配根目标

假设 RN-LP 可行有界，取得精确最优原始／对偶解；β 取其中 RN 行的对偶部分，所有旧行、界和目标常数保留。新列目标为 0，其对偶列条件与互补性使最优 z* 实现相应盒支持值，即 \(r^Tz^*=\sigma_{[\ell,u]}(r)\)。将 RN 对偶部分替换成 PC，并保留旧对偶部分，就给旧模型＋PC 同一个最优下界。

另一方面，RN 最优点 x* 满足 PC，因此旧模型＋PC 的最优值不大于 RN-LP。两侧合并：

\[
\min_{x\in P,\ PC}c^Tx+c_0
=\min_{x\in P,\ \exists z:(x,z)\in RN}c^Tx+c_0.
\tag{Root}
\]

该结论只针对**同一 P、同一目标和同一作用域**。它不等于完整 RN 投影，也不保证其他目标、cutoff 或分支子域仍有相同下界，更不保证搜索更快。更窄且兼容的子域继承的是有效性，最优值保持需要另验。

R104 已有“最优对偶聚合保持同目标根值”的原变量行池版本及其局限，本轮应直接引用。这里新增的实施问题是消去 RN 连续扩展列，不能把基本 LP 对偶原理重新包装为新理论。

### B4. 数值实现不需要精确浮点消去

按实际 Native 行方向、缩放与 Pi 构造组合。符号错误的小乘子可投到合法半轴并记录；等式乘子保留合法符号。源乘子按实际 binary64 值解释，用精确算术或有向区间计算 a、r、b 与盒修正。

若理论 PC 为 a^Tx≥b_PC，实际输出系数为 \(\widehat a\)，在原变量合法界 \(l^x\le x\le u^x\) 上选择

\[
\widehat b\le b_{PC}
+\sum_k\min\{(\widehat a_k-a_k)l^x_k,
(\widehat a_k-a_k)u^x_k\},
\tag{Round}
\]

计算时盒支持取上包围，最终 ≥ 行的 RHS 向下舍入，即保持有效。删除极小系数也是系数转换，需包含在补偿里。若采用 ≤ 约定，使用等价的上向补偿公式。最终核对实际写入的行。

有限精度乘子、符号修复和补偿后的 PC 不自动满足 Root 的精确前提；需重新优化实际紧凑 LP，报告完整目标保留量、数值残差和补偿损失。不要追求所有浮点残差严格为零，也不为此新建通用 dual-repair 求解器。

---

## C. 前置离线证据、历史关系与范围

### C1. 一个可显式写出的 RN 投影族

令 v_i 为 RN 的归一化比例。对任意有效秩支撑 a，有

\[
\sum_{i<j}|v_i-v_j|\ge\sum_i a_iv_i.
\]

a 可取 \(2\operatorname{rank}_i-n-1\) 的排列，或其凸组合。对任意 η、站点乘子 λ_i，定义

\[
d_{iy}=(a_i-\eta)c_i y-\lambda_i,\quad
\kappa_{iy}=\min(L_td_{iy},U_td_{iy}),\quad
\Lambda=\sum_i\lambda_i.
\]

利用 Σv=1、每站 Σw=t 和产品界，

\[
\begin{aligned}
ng&\ge\sum_i a_iv_i\\
&=\eta+\Lambda t+\sum_{i,y}d_{iy}w_{iy}\\
&\ge\eta+\min(L_t\Lambda,U_t\Lambda)
+\sum_{i,y}\kappa_{iy}s_{iy}.
\end{aligned}\tag{Rank-PC}
\]

这是只含原 selector／g 的有效结构行。系数选取影响强度，不影响合法性；各站系数是库存状态上的两段线性函数，可用于解释归一化如何限制库存混合。它是前置见证，不要求另开一条分析型完整算法。

三站局部 Gini 松弛块取 \(c_i=1\)、各站支持 \(\{0,1\}\)、总库存区间 \([1,2]\)。旧见证在库存 1 上的 selector 质量为 \((1,1/2,0)\)，且 \(g=1/3\)。取

\[
a=(2,0,-2),\quad\eta=1,\quad\lambda=(1,-1,0),\quad
L_t=1/2,\ U_t=1,
\]

得到

\[
\boxed{3g\ge1-s_{1,0}+\tfrac12s_{2,0}-3s_{3,1}.}
\]

R143 旧见证的右侧为 5/4、左侧为 1，故此原空间行直接分离旧点，并要求 g≥5/12。证明不依赖优化器。

### C2. 本次验收新增的六个实际点投影见证

从 R143 保存的秩／η、支持、分母界与旧点做有限离线算术，已得到：

| 角色／旧模型 | 精确行非零项数（含 g） | 在旧点的违反量除以 n |
|---|---:|---:|
| K35 BASE | 19 | .023855359195 |
| K35 stock | 19 | .005944242131 |
| K35 TC+stock | 44 | .011385760530 |
| RX20-T1 BASE | 14 | .068505906218 |
| RX20-T1 stock | 14 | .022542692208 |
| RX20-T1 TC+stock | 14 | .022542692208 |

这些是精确解释实际 binary64 输入后的**有效行及保存点违反量**，不是重新优化后的目标增量，也不是已通过 Native 运输资格的生产行。附件同时给出经补偿的 binary64 候选，非零项数依次为 15／15／40、14／14／14；差异来自有补偿的微小项删除。系数运输可沿 B4 补偿；不得未经补偿按阈值删项。

配套 `TailoredExact_Round144_Offline_Projection_Evidence.zip` 含便携脚本与证书，可从 R143 单个 diagnostics 载体复算。本 goal 已给出完整公式、来源与结果；附件缺失时可按这些信息有限复建，不能因此阻塞，也不需重做旧优化。

R143 的四个独立 LP 和正式运行**没有保存完整行 Pi／RC 或 basis**。因此下一步最优对偶投影仍需少量新付费 RN LP；不能声称已从旧 raw 直接取得最优投影 cut。

### C3. R104 已完成的工作与本轮区别

R104 已证明对偶支持／聚合的同目标根值保持、给出分支后不等价反例，并实现有向算术与系数转换补偿。其 ACTIVE 保留根值但完整运行退化；旧 ACTIVE／SHADOW 各有 4349 个辅助 LP 和 3644 次 DP。这些负面结果必须保留。

本轮来源是 R143 新确认的 RN 信息，独立匹配 LP 求解约 .06–1.64 秒，并计划只作一次根来源准备。需要验证的是：消去持久 RN 附加列后，新的成本结构能否有利。不能推断投影必然更快，也不重启旧资源池生成流程。

首候选保留**全 RN 块聚合**。将乘子随意分组后分别作盒投影时，一般有

\[
\sigma(r_1)+\sigma(r_2)\ge\sigma(r_1+r_2),
\]

可能失去跨组消元信息，不能直接照搬 R104 原空间 GROUPED 的根等值结论。若依据实际诊断增加少量行，保留全块行或另证其根值关系；不默认研究任意分组。

---

## D. 有限 LP 研究与进入完整测试的条件

### D1. 先做两个 BASE 域

优先 K35、RX20-T1，保持各自原完整目标、cutoff、支持、g 域与旧矩阵：

1. 新解一次使用生产有限 caps 的 RN 连续来源，保存实际矩阵、X、Pi、RC、目标／质量及来源身份。
2. 由全 RN 块得到一条经过盒修正和运输补偿的 PC。
3. 在原 BASE 矩阵上加 PC，新增 RN 列数为 0，重新求解并比较实际完整目标、规模和成本。

这通常只需两个来源 LP＋两个紧凑 LP。新来源的 caps 与旧诊断保投影等价，可同时核对已保存 RN 点及原结果，不重新铺四种旧研究配置。

若有信息价值，再选 1–2 个域：一个保存的实际 Gini 子域用于检查根压缩在后继域的损失，或 RB35-T2 用于确认另一重要资源角色；必要时用一个 TC+stock 域核查较强载体。总量通常 4–8 个新 LP 足够，不要求全部选项都做。

子域来源和投影行必须尊重作用域；根 PC 可进入包含在根域中的子域，子域 PC 不能直接提升为父域行。论文中区分根值保持与后继域实际损失。

### D2. 不能只用“根目标相等”证明结构价值

标量 floor \(c^Tx+c_0\ge L_{RN}\) 也可在同目标根上复制该下界。因此除目标保留外，检查 PC 是否在原变量空间携带额外信息，例如：

- 代入已有原点／后继域点，核查 PC 与标量 floor 的活动及违反；
- 使用小的有理数块说明结构行可排除满足 floor 的点；
- 若出现真正需要区分的完整收益，再安排一个付出同样来源成本的 floor 对照。

实际 paid-floor 使用现有证明政策承认的有效下界，不直接把浮点 primal ObjVal 当作严格下界。区分 PC 与 floor 的见证须属于所声明的旧域 P；仅展示小块时明确限定范围。

从保存点或代数即可判断时不新增 Optimize；没有严格分离见证就准确描述已知范围，不为证明普遍支配而拓展一个新理论工程。Root 不代表全几何等价。

### D3. 候选冻结

如果实际紧凑 LP 保留有用 RN 增量、补偿损失可接受且生成成本合理，冻结一个统一 RN-P 候选。精确理想等值不等于要求所有输出位完全一致；沿原数值政策报告实际差值。

若投影几乎退化为无用行、补偿抹去增量或后继域诊断显示关键信息明显丢失，可有限调整一种有根据的构造。没有具体信号时正常结束，不自动增加 all-node 分离、切割轮数网格或反复换 Seed。

---

## E. 一次根来源、正式模型不保留 RN 列

主候选从稳定 GI-TBC 出发。在当前运行自身 H 和初始根作用域已确定后，独立构造一次 RN 连续来源，提取 PC，再将其送入正式紧凑模型。来源、行构造、正式根验证及后验检查全部计费；不注入历史或诊断解／界。

默认一个完整运行只做这一次来源准备，随后沿既有规范继承到兼容的更窄作用域。正式根、target、terminal 模型保持原整数列、原 objective／penalty、原 H、AM 与证明流程；正式模型中 RN 新列为 0。不因 leaf、实例规模或运行时间动态改变表示方式。

Codex 可复用现有根 LP／canonical 准备流程，或使用一次性 RN 来源再重建紧凑根。正式控制所使用的模型、点和界须有明确身份；不能把扩展来源的句柄、fingerprint 或 Start 列映射冒充紧凑模型。

可复用的已有实现：

- `GurobiBaseline.cpp` 的 `capture_lp_primal_dual_evidence`、Pi／RC／basis 和 `readLinearModel`。仅为新来源单独启用 capture，**不启动 Round49 算法策略**。
- `include/ObjectiveResourceCompression.hpp`、`src/ObjectiveResourceCompression.cpp` 的 `resourceMultiplier`、`compressObjectiveResources` 及有向 Interval 加乘、有限界的有符号 RHS 补偿。
- 一种最小适配是：合法规范化 RN 混合行方向，将所有 RN 新列的提交系数设为 0，同时以其有效有限界补偿；这就完成盒投影。原 API／旧控制语义保持，通过小 wrapper／同级 helper 扩展即可。
- `src/Round104GurobiObjective.inc` 只供理解旧接入，不重新运行其资源 LP／DP 生成器。不要求用固定宽度整数强行精确表示所有 Pi×系数×界乘积，也不引入新数学库或通用修复平台。

资格只覆盖新风险：正确行方向与实际缩放、有限盒修正、最终运输／微小项删除补偿、整数物理解满足新行、旧完整 Start 不受损、作用域继承、正式模型没有 RN 列，以及 off 行为。用少量 Fraction fixture 与实际 Native 读回交叉核查，再做一次短的完整健康资格。

源 LP 不具备最优／有效证据时保留真实状态，不声称 Root 已实现；任何已发出的行都须通过合法性检查。已有正分母适用规则、UNKNOWN、全局预算与 proof 失效政策继续使用，不另设按硬件秒数切换的机制。

编译实际受影响单元并记录 source／PE。普通报告与交付 metadata 修订不重跑健康实验；具体工程问题定向修复，不扩大成独立工程轮。

---

## F. 完整测试：一个候选、同 PE 对照与综合判断

### F1. 核心四角色

进入完整测试后，每个已进入角色比较 RN-P 与同 PE stable-off，两者独立取得自身 H、所有在线求解和完整验证：

| 角色 | 站点／车辆 | 物理 T | 目标 | 每方法完整 cap |
|---|---:|---:|---|---:|
| K-20-S | 20／2 | 5400 | λ=.15 | 1200 s |
| K-35-U | 35／3 | 10800 | λ=.15 | 2400 s |
| R-X20-S-T1 | 20／2 | 4800 | ρ=1，λ=1/Ω | 1200 s |
| R-B35-S-T2 | 35／3 | 7200 | ρ=1，λ=1/Ω | 2400 s |

单方法 7200 秒，成对 14400 秒。沿原输入、容量、pickup/drop 与精确目标系数，不从报告舍入值重建输入。

可先完成 K35／RX20-T1。若结果为成本可控的轻微混合，优先继续 RB35-T2，检验另一重要资源角色；不因 K35 单个端点略差就认定其余位置无决策价值。明确严重回退、资格失败，或有明确的无效／成本不合算证据时可停止。已进入的有效 hard-role 保留完整窗口，不能用几分钟短跑替代。

### F2. 有目的的补充对照

- **完整 RN 桥接：**预留 K35 cap2400 的同 PE R143 全 RN 对照，以区分“去掉持久 RN 列后是否改善”与“只相对 stable 改善”。已有历史 RN 可作参照；重要归因需要时再执行此桥接，不自动给每个角色补第三方法。
- **条件扩展：**K15（15／2、T3600、λ=.15、cap600）和 RX35-T2（35／3、T6300、ρ=1、cap2400）各做 RN-P／stable 成对，共6000秒，用于容易角色与不同库存混合的边界确认。
- **额外控制／Seed：**仅当会改变采用、归因或停止判断时，补一个 paid-floor 对照、另一 RN 桥接或一个关键角色的 Seed1 成组确认，从未用额度调剂，不另增预算。默认不做多 Seed。

### F3. 判断标准

报告 U、支持 L、signed／relative gap、T_produce／T_cert／T_verify／T_total。open 的 T_cert 为空；Native 返回界与外部合并界分列。节点、Work、simplex、presolved 规模、AM 决定和轨迹解释已观察结果，不能用少节点或等根界替代完整收益。

采用判断看有限面板的整体价值、实质收益与重要回退，不要求每例获胜，也不接受大范围或重要角色的严重退化。轻微 mixed 可保留为值得研究的边界；应说明哪些进一步测量会改变判断，而非机械断言任何新结果都无价值。

没有有用完整收益时，以明确的信息保留／成本／子域损失结论收束本次投影试验。保留 RN 与 RN-P 的不同研究身份，不把一次投影结果外推为整个归一化方向永久无效。

---

## G. 预算与计费

| 内容 | 规划上限 |
|---|---:|
| 投影推导 fixture、来源／紧凑 LP、writer 与短资格 | 3600 s |
| 核心四角色 RN-P／stable-off 成对 | 14400 s |
| 有归因需要时的 K35 同 PE 完整 RN 桥接 | 2400 s |
| 条件 K15／RX35-T2 成对扩展 | 6000 s |
| 失败、必要修正及额外有用控制的共用余量 | 2400 s |
| **总上限** | **28800 s＝8 h** |

分项可调剂，总额不变；可选 Seed1 也在这一个总额内，须实际余额足够。不能把未用预算视为应追加的实验，也不能将同一余量分配多次。

完整方法按外层实际费用计入，包含来源、资格、失败与后验验证；嵌套 H／LP／MIP／Work 不重复加总。cap 是计划窗口，超出窗口的实际验证等成本由余量承担。旧参考不算新计算，编译、离线算术、文稿与公开 I/O 另列。

---

## H. 论文组织与独立复核

更新现稿受影响部分或研究附录，稳定 GI-TBC 正式稿继续保留。本轮应说明：RN 的表达信息、原空间结构投影、同根目标与不同后继几何、以及完整成本的关系。标准对偶、盒支持与 R104 已有成果保持其原有地位。

昂贵完整运行前由非主要实现者复核关键推导与 writer；收尾再检查：

1. PC 的符号、等式乘子、实际行缩放、有限新列界和盒支持修正正确；原目标与 penalty 不变。
2. Root 的最优对偶／同域前提明确，未声称完整 RN 投影、任意分组等价或全树等界。
3. 浮点残差和系数删除有有效补偿，实际紧凑 LP 目标保留得到测量；旧 raw 缺 Pi 的事实没有被掩盖。
4. 正式模型确实没有 RN 新列，来源独立计费，原 Start、作用域与缓存身份完整。
5. 全部已进入结果、同 PE 对照、默认 Seed0 与完整成本一致；预算无重复，混合结果不被一票否决。
6. 没有重新运行 R104 旧资源生成器、计数续线、AM 网格或无决策价值的旧全面板。

修正实质问题，给简明结论即可，不新建庞大审计体系。根界增强或压缩定理本身不等于主线已升级；完整实测决定本轮贡献的计算范围。

---

## I. 交付、Draft PR 与有限清理

交付本 goal、最小代码／配置差异、数学与历史关系、投影证书与实际行、匹配 LP／完整结果、必要 raw／source 绑定、成本、采用决定、增量稿、独立复核和续跑入口。重复报告可合并，内容完整优先于文件数量。

正常提交、推送研究分支并创建英文 Draft PR，建议标题：

**Round144: project reciprocal-normalized Gini information into the original model**

main 未吸收 R143 时以 `codex/round143-reciprocal-normalization` 为临时 base，已吸收时用实际 main；读回 base/head 与交付状态。不自动 merge、force-push、删除历史分支、发送邮件或投稿。待合并不阻塞研究完成。

必要新载体做一次有限公开字节／成员读取，纯 I/O 建议累计30分钟内收束，不触发 Optimize、编译或商业 Native 加载；本地科学验收与公开可读性分开，不重开旧轮全历史恢复。

**显式继承 WORKSPACE_POLICY 两项要求：**全部新 build/raw/temp/restore 资产位于 `E:\codes\ExactEBRP-work`；PR 交付后进行本轮有限清理。仅在证据保留及公开核对条件满足后删除本轮已完成、可重建的临时／重复对象。保留唯一 raw、失败、用户内容、必要 PE/DLL 和仍需使用的树；不删除旧轮。记录实际删除／保留及字节，零删除可接受。

最终报告回答：投影保留了多少 RN 信息，是否超出标量 floor，持久模型与完整成本改变多少，哪些角色获得收益／回退，以及继续、research-only 或结束本次表示试验的理由。

---

## J. 最小资料索引

- R143 PR：https://github.com/yifanXovo/TailoredExact/pull/205
- R143 固定 science：https://github.com/yifanXovo/TailoredExact/tree/516f89f2e23bfad0238c8423bfb9809c308fdec9/results/unified_exact_round143
- 核心记录：final_report.md、mathematical_analysis.md、LP_report.md、candidate_decision.json、reports/LP.json、full.json、same_PE_pairs.csv、review/stage_decision.json 与最终科学／交付复核。
- R143 diagnostics 载体：`results/unified_exact_round143/artifacts/diagnostics_and_failures.zip`，SHA256 `b4afa7de3a9f7b3844ab76b24c8082b1ea05db92c4a27118708c98b9085246b3`。其中含 domains/*/RN.json、math/offline_point_checks.json、inherited/roots/* 保存点及四个新 LP 的模型／解；来源无需恢复整个历史。
- R143 四个完整 pilot：artifacts/campaign_pilot_001.zip 至 004.zip，分别为 K35 off／RN、RX20-T1 off／RN；实际 Native 日志、父子域与 AM 记录用于比较，不将日志时钟冒充正式完整时钟。
- R143 实现：include/Round143Research.hpp；src/CplexBaseline.cpp、GurobiBaseline.cpp、MipStartMapping.cpp、PaperExternalGiniTree.cpp；scripts/round143_lp.py、round143_math.py、round143_offline.py。
- R104 数学：https://github.com/yifanXovo/TailoredExact/blob/aa1d0e5b268cf95442b3713b2af8fc505974f6c2/results/unified_exact_round104/mathematical_algorithm.md
- R104 结果：https://github.com/yifanXovo/TailoredExact/blob/aa1d0e5b268cf95442b3713b2af8fc505974f6c2/results/unified_exact_round104/final_report.md
- R104 可复用代码：include/ObjectiveResourceCompression.hpp；src/ObjectiveResourceCompression.cpp、round104_compress_main.cpp、Round104GurobiObjective.inc。当前 R143 源载体仍保留它们；先定向读取，勿启动旧生成流程。
- 原理论定位：R88 pair CDF／端点 transport；R133 原目标混合缺口；R138 公共因子资源块；R143 已核对的 Charnes–Cooper、Yue 等及 Chen–Hooker 文献。无需重做全面文献工程。
- 工作区与主线：WORKSPACE_POLICY.md；docs/current_mainline.md、docs/unified_exact_research_index.md；config/gi_tbc_round137.json。

**本轮成功标准：以有证据的模型成本问题为起点，判断少量原变量结构行能否保留有用 RN 信息并改善完整求解；数学与计算证据分层，允许合理混合结果，稳定 GI-TBC 持续可用。**
