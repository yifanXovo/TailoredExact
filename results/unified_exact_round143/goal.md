/goal

# TailoredExact 下一轮完整任务清单

## Round143：倒数归一化的 Gini 扩展式——保留整数路径结构，检验新的松弛增量

**日期：2026-10-31。建议轮次：Round143；编号已占用时沿实际下一轮继续。**

## 0. 目标、优先级与自主权

R142 可以完整验收。条件计数产品确实提高了三个较弱来源，但增量较小，ALL 没有额外信息；同 PE 下 K20 的新增时间收益很小，RB35-T2 改善而 K35 保留重要回退。因此关闭 count-proof 续线，稳定 R137 GI-TBC 继续作为论文主线，不补旧候选全表或 Seed 网格。

本轮研究一个不同的问题：**保留原路线、操作量、库存及其整数性，仅用已有库存状态 selector 构造分母倒数和归一化 Gini，能否补上旧松弛中的比例一致性，并以合理成本改善完整 GI-TBC？**

先做少量同域 LP，确认重新优化后的完整目标是否提高；有价值再实现一个统一的附加扩展式候选，简称 RN。继承最新代码与历史记录，**算法载体回到稳定 R137 配置**，不默认叠加 R138–R142 的研究机制。

新增实验计算总上限 **8 小时**，不是用满要求。Codex 可按实际信号调整少量诊断域、顺序、等价实现及一个直接相关的小扩展。没有有用信号时，完成数学和实验结论即可；不必为了完成表格进入完整运行或另开第二条生产研究线。

所有未明确多 Seed 的新求解显式使用 **Gurobi Seed=0**；可选确认使用 Seed=1。H seed 固定 20260626 并单列。计时求解单线程、串行，编译、重 I/O 和 PDF 导出错开。

算法保持统一的数学依据：不按实例身份或规模打补丁，不按运行若干秒切换方法或 leaf。允许依实际支持、有效界、数学适用域及冗余关系生成或省去约束。实验 cap 与算法规则分开。追求可写进论文的实质收益，允许有解释力的混合结果，不接受重要角色或大范围严重回退。

---

## A. 起点、验收结论与历史边界

### A1. 实际版本与工作区

| 项目 | 编写本 goal 时核实的参考 |
|---|---|
| 仓库／前序 PR | yifanXovo/TailoredExact；#204，open／Draft，未合并 |
| R142 branch／head | codex/round142-conditional-count-products；37e6c4e79c18dbca6bc4622d80a5bd8a860aa13c |
| R142 生产源码 | 9b024c451b00f84f9f1cac0905eab457cc82a5b9 |
| R142 固定 science | 61d215f1923386dbc7aa2c453d9a86b27341665d |
| 编写时 main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 稳定入口／配置 | scripts/paper_s2.py；config/gi_tbc_round137.json |
| 活动树／新资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work\ |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议 branch／结果目录 | codex/round143-reciprocal-normalization；results/unified_exact_round143/ |

先读适用 AGENTS.md、WORKSPACE_POLICY.md，核实 refs、未提交内容、进程和已有资产。main 已吸收所需版本时从实际 main 继续，否则从已核实的 R142 继续并用其作临时 PR base；不等待合并，不机械回退参考 SHA。

稳定对照保留自身 H、M-B/VD-P、pair-only、AM=.08、depth=8、minimum width=1e-4、AP off 及 R134 证明政策。R138 stock、R140 TC/TC2、R141 count disjunction、R142 CP 等研究开关按稳定配置关闭。旧入口及各历史开关语义保留，新 RN 开关默认关闭。

### A2. R142 已得到什么

- 12 个新连续 LP、12 个无 Optimize 的范围等值见证；selected 与 ALL 的最优值只差浮点尾数。三个弱侧 cover 的增量分别为 K35：0.000023810780，RB35-T2：0.000256440319，K20：0.000072175290。
- 四个正式候选位置、两个同 PE 旧 D1 对照及一个健康资格位置；49 次申报 Native Optimize 全部返回，14 个 count 来源逐一绑定。所有正式完整位置的 outer split 均为 0。
- K20 同 PE production 仅快 0.874323 秒、total 快 1.490906 秒；跨版本旧 D1 自身也明显变快，不能将其全算作 CP 收益。RB35-T2 同 PE 的 U 降低 0.056371172852、L 提高 0.001462097906；K35 相对历史 D1 双端回退，两个 hard roles 均仍被旧 TC+stock 双端支配。
- 实际保守新增实验费 7504.312010 秒，约 2.084531 小时。结束来自结果，非预算耗尽。唯一 tiny 构造错误发生在 Optimize 前，已修复并保留；没有待修的普遍 LB/UB 工程故障。
- 条件产品只在来源 LP，整数模型实际变化为来源 floor；稳定入口、旧 raw、失败和历史均保留。PR 待合并不阻塞下一轮。

### A3. 本轮避免重复的工作

历史已拒绝过粗分母桶、近似倒数和未经证明的整数变量整体缩放；这不是本轮“原整数变量不缩放＋已有有限状态产品”构造的实测负面结果。R88 已有 pair CDF／端点 transport，R138 已有公共因子选定资源块定理，R133 已指出整数原目标上图的混合缺口。这些成果应引用，不改名重新宣称。

不继续 count floor、CP/ALL、stock placement、阈值调参或 Seed 大网格；不自动重开 R105–R107 路线 oracle 架构。R137 的 AM no-strict-child 问题保留为后续预案，本轮不同时实现第二条生产研究线。

---

## B. 数学构造：只归一化 Gini 部分

### B1. 原量与新增量

令 c_i>0 为模型**实际加载**的库存比例系数，Y_i 为原整数库存，

\[
r_i=c_iY_i,\qquad S=\sum_i r_i,\qquad
A=\sum_{i<j}|r_i-r_j|,\qquad G_{\rm true}=\frac{A}{nS}\quad(S>0).
\]

原目标仍为 \(g+\lambda P\)，P 沿用原 penalty 表达式与原系数。已有状态列满足

\[
\sum_{y\in\mathcal Y_i}s_{iy}=1,\qquad
Y_i=\sum_y y s_{iy},\qquad s_{iy}\in\{0,1\}\text{（整数模型）}.
\]

在经证明的完整作用域 \(0<S_L\le S\le S_U\) 内，引入

\[
t\in[L_t,U_t]=[1/S_U,1/S_L],\qquad w_{iy}=t s_{iy}.
\]

用二元—连续产品的线性表达：

\[
\begin{aligned}
L_t s_{iy}&\le w_{iy}\le U_t s_{iy},\\
t-U_t(1-s_{iy})&\le w_{iy}\le t-L_t(1-s_{iy}),\\
\sum_yw_{iy}&=t \quad\text{（每站）}.
\end{aligned}\tag{RN1}
\]

在站点单纯形与质量等式下，第二行已被第一行和其他状态推出，可采用等价的紧凑实现，不必重复冗余行。新增归一化库存列与差异列：

\[
\widehat Y_i=\sum_y y w_{iy},\qquad
\sum_i c_i\widehat Y_i=1,
\tag{RN2}
\]

\[
\widehat h_{ij}\ge c_i\widehat Y_i-c_j\widehat Y_j,\qquad
\widehat h_{ij}\ge c_j\widehat Y_j-c_i\widehat Y_i,\qquad
\sum_{i<j}\widehat h_{ij}\le ng.
\tag{RN3}
\]

各差异列非负。使用独立的 \(\widehat Y\) 列，使系数仅涉及实际 c_i 与整数 y，避免额外把 c_i y 先舍入成另一套比例系数。旧 state_g、Z、h 的单位不同，不直接复用为新量。

**原路线、操作、库存及其整数约束均保留；penalty 不乘 t，原目标不变。** 本轮默认将 RN 与旧模型相交，不删旧 Gini／VD-P 或其他稳定行。

### B2. 整数等价性与可陈述的增强关系

整数 selector 下，未选状态的 w=0，站点质量等式迫使所选状态的 w=t，因此

\[
\widehat Y_i=tY_i,\qquad 1=\sum_i c_i\widehat Y_i=tS.
\]

所以 t=1/S，RN3 等价于 \(g\ge A/(nS)\)。反过来，原整数可行点可取 t=1/S、w=ts、\(\widehat Y=tY\)、\(\widehat h=t|r_i-r_j|\) 延拓。合法的非最小 epigraph g 也允许保留，不能擅自将模型内 g 改成原解计算出的 G 后越过当前 g 域。

因此附加 RN 保留原整数问题，并满足

\[
\operatorname{proj}_{\rm old}(P_{\rm old}\cap RN)\subseteq P_{\rm old}.
\]

这给出连续松弛不弱化的理想包含关系，不保证每个 LP 的最优值严格提高，也不保证完整搜索更快。数值微差按现有资格政策解释，不通过改容差制造增量。

### B3. 安全分母界与零分母适用域

复用物理总库存区间 \(B^-\le\tau=\sum_iY_i\le B\)，其中 \(B^-=\max(0,B-\sum_kQ_k)\)，以及实际支持端点 \(m_i=\min\mathcal Y_i,M_i=\max\mathcal Y_i\)。令

\[
\tau_L=\max(B^-,\sum_i m_i),\qquad
\tau_U=\min(B,\sum_i M_i).
\]

对盒约束 m_i≤Y_i≤M_i 与该总库存区间，S 的连续最小值通过从 m_i 开始、按 c_i 递增补足 τ_L 得到；最大值按 c_i 递减补至 τ_U 得到。c_i>0 保证取相应总量端点。忽略支持孔洞只会放松，故所得 S_L、S_U 对原整数问题有效；无需枚举所有 S 或新增优化调用。区间不可行时沿旧流程处理，不进行倒数运算。

先按实际 c_i、有效支持与作用域，用精确算术或有向误差包围计算 S_L、S_U，再将倒数下端向下、上端向上舍入。仅对未经误差包围的普通浮点累加结果取一次外向倒数，未必覆盖累计误差；复用已有 dyadic 工具即可。不得把观测到的 S*、某个解的库存或启发式样本当全域界。

首次附加式采用统一适用规则：**有完整作用域有效的 S_L>0 才生成 RN；否则保持旧精确模型与原 S=0 约定。** 这是约束有效域判断，不按实例名称或大小选择算法。当前优先域均可从物理库存得到正下界；不为尚无价值的通用零分母分支先建一套新控制器。

若实际需要覆盖正／零两部分，允许一个有证明的统一扩展：令 δ 为二元变量，\(\delta\le\tau\le B\delta\)，\(L_t\delta\le t\le U_t\delta\)，在 [0,U_t] 上线性化 w=ts，保留每站 Σw=t，并将归一化改为 \(\sum_i c_i\widehat Y_i=\delta\)。δ=0 时库存及 t,w 为零；δ=1 时 tS=1。这里 U_t 使用合法的正整数库存分母下界，不能原样套用正域的 L_t s 下界。此项是可选精确延拓，不是本轮必做生产任务。

---

## C. 先保留两项明确的表达关系

### C1. RN 能补什么：三站严格见证

取 n=3、c_i=1、每站支持 {0,1}、总库存区间 [1,2]、旧 g 域 [0,1]。库存 1 的 selector 质量为 (1,1/2,0)，g=1/3；库存 1 的旧 g 产品取 (1/3,1/3,0)，各站其余 q 质量补足 g。令

\[
h_{12}=1/2,\quad h_{13}=1,\quad h_{23}=1/2,
\quad H_\Sigma=2,\quad J=\sum_iZ_i=2/3.
\]

该点满足旧 VD-P、stock 产品、全域 count 产品、旧 TC 和 TC2（此域 TC2 的右侧为 2）。每对至少有一个确定端点，R88 pair／端点 CDF 的下界也恰为上述 h；该支持上的 penalty 是线性的，AP 不再分离该点。

RN 中 t∈[1/2,1]，第一、三站的归一化比例分别为 t、0，归一化使第二站为 1−t。第二站零状态的 w 为 2t−1，故

\[
2t-1\ge\tfrac12\cdot\tfrac12=\tfrac14
\quad\Longrightarrow\quad t\ge\tfrac58,
\]

\[
g\ge\frac{2t}{3}\ge\frac5{12}>\frac13.
\]

这是声明的松弛子块上的严格分离，幅度 1/12。用 Fraction 复算即可，不强制新建一个完整 tiny BRP 面板。

### C2. RN 尚不能解决什么：固定分母反例

取 n=4、c_i=1、支持 {0,1}、总库存固定为 3，各站库存 1 的质量均为 3/4。RN 可取 t=1/3、w_1=1/4、w_0=1/12，各归一化比例均为 1/4，因此允许 g=0。

而旧 TC 给出 H≥3，stock 在固定总量下给出 J=3g，再由 H≤4J 得 g≥1/4。故 RN 单独不支配已有整数计数信息，也没有解决 R133 的全部整数目标混合缺口。**附加式保留旧行有直接理由；本轮不自动铺独立替换模型的比较网格。**

### C3. 文献位置

倒数归一化、Charnes–Cooper 变换及二元—连续产品线性化是标准工具；Gini 的归一化表达也已有文献。本轮的研究内容是：如何与本项目原整数库存／路线结构精确结合、与已有表达的强弱关系、以及完整计算收益。不得仅凭这个标准变换声称新的通用分式规划原理或期刊层级已提升。

定向核查 Charnes & Cooper (1962)、Yue／Guillén-Gosálbez／You (2013) 及 Chen & Hooker (2023) 的相关部分即可，见 J；不开展与实施无关的全面文献工程。

---

## D. 已有离线证据与有限 LP 研究

### D1. 十二个真实历史根点的新增检查

本次验收已对 R140 保存的 BASE／stock／TC+stock 根点进行零 Optimize 检查。源载体：

`results/unified_exact_round140/artifacts/diagnostics_and_failures.zip`

SHA256：`2cb1ab936753ce9ac26ae1f970b070b2751190af79f6a80a8b0f5d254902bf5f`。

成员位于 `results/unified_exact_round140/inherited/roots/{role}/`，使用 `inherited/original.lp` 的实际 c_i、`scope.json` 的物理域及 `{base|stock|tc_stock}/solution.json.gz`。随本 goal 提供的 `TailoredExact_Round143_Offline_Evidence.zip` 含便携检查器与派生证据；它是复用材料，核心构造和结果已在本 goal 中给出。

固定保存 selector 和 g 后，六点被排除：

| 角色／原模型 | 保存 g | 延拓所需 g 的已证下界 | 分离幅度 |
|---|---:|---:|---:|
| K35 BASE | .038639183378 | .055712482251 | .017073298873 |
| K35 stock | .056550300442 | .066393660802 | .009843360360 |
| K35 TC+stock | .056550300442 | .068863232858 | .012312932415 |
| RX20-T1 BASE | .100712705490 | .153711319782 | .052998614292 |
| RX20-T1 stock | .146675919500 | .153229103058 | .006553183557 |
| RX20-T1 TC+stock | .146675919500 | .156426018541 | .009750099040 |

K20、RX35-T2 的 BASE／stock／TC+stock 六点则已找到保持原点和目标的新增列延拓；按实际 c_i 重构的最大线性残差不超过 1.9e-16，归一化 Gini 行有正余量。这六点可作为数值政策下的同目标见证。只有与实际新块、界及原矩阵一致后才能沿用；不能外推到其他域或完整 MIP 表现。

严格区分：旧点被排除 ≠ 新完整 LP 最优值提高；旧点可延拓 ≠ RN 对整个模型冗余。上述证书的有理数计算解释实际 binary64 selector 和 c_i，原完整 LP 点仍是数值可行点，不宣称已取得全矩阵的有理数最优证书。

### D2. 非延拓证书的推导与复用

固定 selector 后，在给定 t 下，每站 w 满足盒界与 Σw=t。\(v_i=c_i\sum_y y w_{iy}\) 的可达区间 \([\ell_i(t),u_i(t)]\) 可用分数背包计算；归一化要求 \(\sum_i\ell_i(t)\le1\le\sum_i u_i(t)\)。

对任意排列的秩系数 \(a_i=2\operatorname{rank}_i-n-1\)，或并列秩系数的凸平均，

\[
\sum_{i<j}|v_i-v_j|\ge\sum_i a_i v_i.
\]

利用 Σv=1，对任意 η 有

\[
ng\ge \eta+\sum_i
\min\{(a_i-\eta)\ell_i(t),(a_i-\eta)u_i(t)\}.
\tag{Rank}
\]

右端分段线性。对完整可行 t 区间的两端及所有站点背包断点取最小，即得固定 selector 延拓所需 g 的有效下界。已有检查器使用 Fraction 和外向 t 端点，保存秩、η、断点数、取得下界的 t 与证书；全部断点可由原点复算。有限网格只用于寻找可行延拓或挑支撑式，不以“网格没找到”证明不可行。

复用这些证书，不再次消耗 Optimize 重做保存点排除。只有新 writer 或新支持改变块时，才补相应检查。

### D3. 新 LP 的优先顺序

1. **先做稳定 BASE 的 K35、RX20-T1 两个匹配域。** 在原保存矩阵上附加 RN，保持原目标、cutoff、支持和 g 域；比较重新优化后的完整目标，不只比较 g 分量或某个保存点。
2. 若有信号，选 1–2 个匹配 stock／TC+stock 域检查增量能否超出旧库存与计数信息。这是表达关系诊断，不将该研究配置自动带入主候选。
3. K20、RX35-T2 已有正延拓，匹配后可直接作为无新增 Optimize 的对照。若需要验证新作用域，可选一个实际 Gini 子域或 RB35-T2 域；说明它回答的问题。通常 4–6 个新 LP 已足够，不铺所有组合。

原 BASE 若没有显式 stock 行，新 t 界使用了物理库存信息，应准确标为组合增量；较强 stock／TC+stock 对照用于区分是否存在超出这类旧信息的收益。无需为每个角色再补一套机械的 bound-only 网格。

报告原／新完整目标、g 与 penalty 分量、有效分母界、行／列／非零数、构建与求解成本及资格状态。若有同目标替代点，保存它并解释原分离为何未转化为目标收益。

进入完整实现通常应有超出数值误差的实际目标增量、合理规模与成本。对一个明确、低成本且有机制依据的混合信号，允许有限 pilot；不设置脱离问题尺度的绝对提升阈值。若只剩点分离、目标不变且模型明显膨胀，则收束，不为了“找到正结果”自动改做 RN×TC2×CP 网格。

---

## E. 有信号后的最小完整实现

新增一个默认关闭的 RN 开关／独立研究入口。主候选为稳定 GI-TBC＋统一 RN 附加块；默认对它实际使用的连续与整数模型采用同一数学构造。先有有限 LP 结果，再接入 production，不预先重构整个 writer。

新增列数量为每个库存状态一个 w、每站一个归一化库存、每对一个归一化差异及一个 t；不枚举全部 S 值、不新增路线状态。允许删除已证冗余行或用清楚等价的实现节省规模，冻结后各实例统一使用。

资格集中覆盖新增风险：

- 从实际支持和物理域导出 S 界；作用域与 cutoff 沿用已有政策。父域有效界可用于子域，局部界不能泄漏到更大的域。
- 整数物理解可确定性重构 t、w、归一化库存及差异。现有 `MipStartMapping.cpp` 会拒绝未知列，必须完整接入新列，不能为方便关闭 Start 或让旧完整 Start 变成不明的部分 Start。保留模型 g 与物理 G 的区分，原 Start 的真实 G 域资格规则不变；B2 的 epigraph 延拓不授权使用域外物理 Start。
- Native 实际读回覆盖新列、类型、界、行和系数；计入新构建、求解及验证成本。新旧单位分清，使用实际 c_i；必要时采用有数学依据的正二次幂缩放，不开启普遍容差调松工程。
- 用少量正 S、固定 S、关闭适用规则的零下界域及 C 节有理数见证，核查等价性与开关关闭行为；再做一次短的实际资格运行。已有 scope、proof、失效、资源释放框架定向复用。
- 编译真实受影响单元，绑定源码和 PE。新证据、连续求解和完整运行都保留实际输入、参数、调用及返回状态。普通报告或交付 metadata 修改不触发无关健康运行重跑。

不同时修改 AM、H、分支策略或终止政策。若遇到具体工程问题，定向修复；正确性不足时停用该候选并保留稳定主线，不将本轮延伸成泛化审计平台。

---

## F. 完整算法实验：少量角色，同 PE 成对

### F1. 首批四角色

进入完整 pilot 后，每个已进入角色比较 RN 与同 PE 的 stable-off；两者都独立取得自身 H、根 LP、在线验证和完整证明，不注入历史／离线诊断解或界。

| 角色 | 站点／车辆 | 物理 T | 目标 | 每方法完整 cap |
|---|---:|---:|---|---:|
| K-20-S | 20／2 | 5400 | λ=.15 | 1200 s |
| K-35-U | 35／3 | 10800 | λ=.15 | 2400 s |
| R-X20-S-T1 | 20／2 | 4800 | ρ=1，λ=1/Ω | 1200 s |
| R-B35-S-T2 | 35／3 | 7200 | ρ=1，λ=1/Ω | 2400 s |

单方法合计 7200 秒，成对 14400 秒。沿原输入、容量、pickup/drop 与目标系数，不从表内四舍五入数反推输入。

优先完成 K35／RX20-T1 匹配比较，检查历史根点信号能否转成完整收益，再按结果决定后续角色。提前收束指**不再进入剩余位置**；已进入的有效 hard-role 仍保留原完整窗口，不能用几分钟短跑替代。R142 的 RB35-T2 大部分 U 收益出现在约 1867–2229 秒，这支持保留 2400 秒窗口。

### F2. 条件扩展与有限重复

值得确认推广边界时，再补 K15（15／2、T3600、λ=.15、cap600）与 RX35-T2（35／3、T6300、ρ=1、cap2400），同样成对，共 6000 秒。前者保护容易收敛角色，后者检查保存根点可延拓时的完整行为；不强制补齐八角色旧面板。

只有会改变采用／停止判断时，才对一个关键角色做最多两方法的 Seed1 成组确认；它使用 G 节共同余量，不是额外预算。主面板仍为 Seed0，不从两个 Seed 推断运行时间分布。

### F3. 评价与归因

先看完整方法是否有可保留收益：收敛角色比较 T_produce、T_cert、T_verify、T_total；open 角色分别列 U、支持 L、signed／relative gap。open 的 T_cert 留空，不以 cap 充当收敛时间；Native 返回界与外部合并界分列。

LP 增强、Native root cuts、节点／Work、outer split、AM 决定和时间轨迹用于解释已观察结果。不能把 LP 变强自动等同于算法变强，也不能把全部运行差异归为某条新行的直接效果。所有已进入正反结果均保留。

本轮主比较为 stable-off ↔ RN。旧 stock／TC／TC2／D1／CP 可作带原身份的历史参照，不补它们的新全表；P-GRB 的论文比较复用现有资料，不重开 benchmark 收束任务。

---

## G. 预算与停止自由度

| 内容 | 规划上限 |
|---|---:|
| 数学 fixture、匹配 LP、writer 与短资格 | 3600 s |
| 首批四角色，RN＋同 PE stable-off | 14400 s |
| 有依据才补 K15／RX35-T2 成对 | 6000 s |
| 必要失败／修正、额外有用诊断、至多一组 Seed1 共用余量 | 4800 s |
| **总上限** | **28800 s＝8 h** |

可按信号调剂分项，总额不变。所有新实验按完整方法外层实际费用计入，包含资格、失败与后验验证；H／LP／MIP／Work 是内部明细，不重复加总。cap 是计划窗口，额外验证与超出窗口的实际成本从共同余量承担。旧参考不算新计算，编译、离线算术、文稿与公开 I/O 另列。

4800 秒只有一份，不同时另给失败、机动和 Seed1 各 4800。完整 Seed1 对必须在实际余额足够时才进入。没有有用 LP 增量时，允许在很少新增求解后结题；已有明确回退时不为用满预算继续扩面。

本轮可正常得到三种结果：值得后续有限扩展的统一 RN 候选；有表达增量但完整成本不合算的 research-only 结果；或同目标替代点／成本证据支持结束此方向。均需回答实际研究问题，不以“必须更快”或“每例必须赢”作为任务完成条件。

---

## H. 论文增量与独立复核

更新现稿受影响部分或研究附录即可，稳定 GI-TBC 正式稿继续保留。区分四层结果：标准构造与本项目整数等价性、严格子块关系／保存点证书、重新优化后的 LP 增量、完整算法表现。不要用前一层替代后一层。

昂贵完整运行前，由非主要实现者核查数学、实际 writer 与 Start；收尾独立检查：

1. 原目标和 penalty 未变，原整数路径未缩放；正 S 有效域、实际 c_i 与外向界正确。
2. 三站严格见证与四站限制成立；没有声称 RN 单独支配旧 TC 或给出完整整数凸包。
3. 离线正延拓与非延拓证书匹配实际块；保存点排除未冒充新 LP 最优值增量。
4. 完整载体确为 stable R137＋RN，新旧 Start 和生产返回均有实际证据；没有无意继承失败研究堆叠。
5. 对照同 PE、完整成本、默认 Seed0、所有正反位置和共同余量一致；阶段停止有合理依据。
6. 已考虑历史重叠，实验回答具体问题，没有因缺一张无决策价值的表而继续计算。

修正实质问题并给出简明结论，不新建庞大审计体系。论文可讨论的预期增量是分母归一化与整数／资源表达的互补关系及其计算价值，不能提前宣称已达到更高期刊标准。

---

## I. 交付、Draft PR 与有限清理

交付本 goal、最小代码／配置差异、数学与历史关系说明、匹配 LP／完整结果、必要 raw 和来源绑定、成本、采用决定、增量稿、独立复核及续跑入口。离线证据可直接纳入本轮并注明来自本次验收，不重跑其旧优化；合并重复报告，完整内容优先于文件数量。

正常提交、推送研究分支并创建英文 Draft PR，建议标题：

**Round143: test a reciprocal-normalized Gini lift on the stable GI-TBC formulation**

main 未吸收 R142 时以 `codex/round142-conditional-count-products` 为临时 base，已吸收时用实际 main；读回 base/head 与交付状态。不自动 merge、force-push、删除历史分支、发送邮件或投稿。待合并不阻塞研究完成。

必要新载体做一次有限公开字节／成员读取，纯 I/O 建议累计 30 分钟内收束，不触发 Optimize、编译或商业 Native 加载。区分本地科学／语义验收与公开可读性，定向处理失败，不恢复全部旧轮。

**显式继承 WORKSPACE_POLICY 两项要求：**全部新 build/raw/temp/restore 资产位于 `E:\codes\ExactEBRP-work`；PR 交付后进行本轮有限清理。仅在证据保留和公开核对条件满足后删除本轮已完成、可重建的临时／重复对象。保留唯一 raw、失败、用户内容、必要 PE/DLL 和仍需使用的树；不删除旧轮。记录实际删除／保留及字节，零删除可接受。

最终报告明确：RN 补上什么比例自由度，旧点分离是否变成完整 LP 提升，新增规模和成本多少，完整方法的收益／回退是什么，以及继续／research-only／结束的理由。

---

## J. 最小资料索引

- R142 PR：https://github.com/yifanXovo/TailoredExact/pull/204
- R142 固定 science：https://github.com/yifanXovo/TailoredExact/tree/61d215f1923386dbc7aa2c453d9a86b27341665d/results/unified_exact_round142
- R142 核心：final_report.md、mathematical_analysis.md、LP_report.md、candidate_decision.json、reports/full.json、new_arms.csv、same_PE_bridges.csv、最终科学／整合复核。
- R140 保存点载体：https://github.com/yifanXovo/TailoredExact/blob/37e6c4e79c18dbca6bc4622d80a5bd8a860aa13c/results/unified_exact_round140/artifacts/diagnostics_and_failures.zip ，使用 D1 中 SHA 和成员，不从报告舍入值重建。
- 原分式方案历史：https://github.com/yifanXovo/TailoredExact/blob/37e6c4e79c18dbca6bc4622d80a5bd8a860aa13c/results/gf_tailored_bc_formulation_snapshot_round/alternative_formulation_rejection_notes.csv
- 历史理论：R88 pair CDF／端点 transport；`results/unified_exact_round133/joint_objective_gap_note.md`；R138 `mathematical_analysis.md`；R140 TC/TC2；R137 `final_report.md` 的参数／机制部分及 R126 `historical_attribution.md`。按实际目录索引定位需要的部分。
- 实现入口：`src/CplexBaseline.cpp` 的 state_g、比例、原 Gini 与 writer；`src/MipStartMapping.cpp`；`src/NativeEvidenceJournal.cpp`；`src/PaperExternalGiniTree.cpp`；成熟 R138 附加行和现有 LP 载体工具。
- 工作区与主线：WORKSPACE_POLICY.md、docs/current_mainline.md、docs/unified_exact_research_index.md、config/gi_tbc_round137.json。
- Charnes, A. & Cooper, W. W. (1962), *Programming with linear fractional functionals*, Naval Research Logistics Quarterly 9, 181–186. https://doi.org/10.1002/nav.3800090303
- Yue, D., Guillén-Gosálbez, G. & You, F. (2013), *Global optimization of large-scale mixed-integer linear fractional programming problems: A reformulation-linearization method and process scheduling applications*, AIChE Journal 59, 4255–4272. https://doi.org/10.1002/aic.14185
- Chen, V. X. & Hooker, J. N. (2023), *A guide to formulating fairness in an optimization model*, Annals of Operations Research 326, 581–619. https://doi.org/10.1007/s10479-023-05264-y ；作者公开稿：https://johnhooker.tepper.cmu.edu/equityGuideAOR3post.pdf

**本轮成功标准：以一个具有整数等价性、不同于已关闭计数续线的表达方向，检验是否存在可用的松弛与完整算法收益；有证据再投入完整实现，无信号及时收束，稳定 GI-TBC 持续可用。**
