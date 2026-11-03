/goal

# TailoredExact 下一轮完整任务

## Round150：GD 的有限选择外确认、条件惩罚传播的 LP 检验与论文结构收束

**日期：2026-11-03（Asia/Shanghai）。建议轮次 Round150；编号已占用时沿实际下一轮继续。**

## 0. 目标与执行原则

R149 可以验收：uniform penalty feedback（PF）有效，三个匹配 LP 均报告正增量；完整算法在 K35 改善 U 和 gap，在 K20 更早找到共同最终 incumbent，但 RB35 的 U 变差，三个角色均未新增证书。因此保留研究用途是合理选择，不能称为严重回退、整族失败或毫无收益。当前没有阻止后续研究或论文组织的重大工程问题。

本轮完成两个有清楚边界的任务：

1. **主任务：固定 B＝稳定 GI-TBC、D＝B＋独立 GD，在两个未参与 GD 选择的既有 R137 配置上作匹配完整比较，确定 D 的有限论文定位。**这些配置已有公开项目结果，不是全新盲测。
2. **小额研究任务：将同一资源对偶的条件信息反馈到状态乘积，在三个匹配域各求一个新 LP，回答其是否在 R149 PF 之后继续提高优化值。**本轮结果用于决定后续研究资格，不自动展开新生产实现和完整算法面板。

同时组织一节可进入论文的统一论述：资源与分母信息如何进入表达、哪些强化严格、哪些优化收益已经测到、哪些完整方法取舍仍存在。不要以新增轮次或行族数量代替论文贡献。

新增实验外层总上限 **14400 秒＝4 小时**，允许提前收束。默认 **Gurobi Seed=0、Threads=1**，H seed 独立固定为 **20260626**。计时运行串行，与编译、重 I/O、PDF 导出错开；各完整臂支付自己的 H、构造、求解和必要验证。沿用 R134 证明政策与已接受数值标准，局部浮点容差不冒充精确有理最优性证明。

算法保持统一、数学依据明确：不按实例名、规模或已知输赢打补丁，不以运行若干秒切换算法。基于有效界、域包含或实际支配省略冗余行是允许的；实验 cap 不是算法规则。目标是实质收益和可接受取舍，不要求逐例全胜或打败所有历史变体。Codex 可在本轮问题与总预算内调整顺序、有限诊断和实现方式；额外探索先说明它能改变什么判断，避免自然扩张成另一套完整实验。

---

## A. 起点、身份与工作区

| 项目 | 编写时核实的参考 |
|---|---|
| 仓库／前序 PR | yifanXovo/TailoredExact；#211，Open Draft，未合并 |
| R149 branch／head | codex/round149-penalty-product-feedback；d33d47bb224ab3cd4eeacabc731b3fa8b16b7b2c |
| R149 fixed science | 3bb93fa2f4b8c267af8fae409864191e033c5bb2 |
| 实际生产源码 | 380a85f866bffb914036190f8ee2700ce8b55978 |
| 可复用 PE／SHA256 | E:\codes\ExactEBRP-work\build-cache\round149\ExactEBRP.exe；373efa9a596aaf02fb332685515fcfe88df1b169cbe53b295ab6027140620295 |
| Native DLL／SHA256 | D:\gurobi1302\win64\bin\gurobi130.dll；9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88 |
| R147 fixed science | a0673b683c645d35de829fa101a55cc9fc4774c7 |
| R137 fixed science／原生产源码 | e735c3447eb1443713c700942d873de1783a4a26；779713ad9a0b01edc538ecb64df9438739127be3 |
| 编写时 main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 稳定入口／配置 | scripts/paper_s2.py；config/gi_tbc_round137.json |
| D 入口／配置 | scripts/paper_s2_gd_only.py；config/gi_tbc_gd_round147.json |
| 活动树／新增资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议 branch／结果目录 | codex/round150-gd-confirmation-conditional-feedback；results/unified_exact_round150/ |

先读适用 AGENTS.md、WORKSPACE_POLICY.md，核实 refs、用户修改、活动进程、原始封存与可复用 PE。main 已吸收必要内容则从实际 main 继续，否则从核实后的 R149 继续，选对应临时 PR base；不等待合并，不机械回退上述 SHA。

本轮默认**不改生产 C++、不新编译**。以同一 R149 PE 运行原 B/D 语义，PF、Shared-S、STOCK、AP 均关闭；保留 M-B/VD-P、pair-only、AM=.08、depth=8、minimum width=1e-4 与原物理目标。记录实际生产源码/PE、旧方法定义、R150 wrapper、科学与交付 commit 的不同身份。

---

## B. 已有结果与本轮要补的证据

### B1. R149 的结果应保留完整含义

| 同域诊断 | 旧 D LP | 加 PF 后数值 LP | 增加 |
|---|---:|---:|---:|
| K20 base | .236010302342365 | .237043344713575 | .001033042371211 |
| K35 base | .204187028163866 | .206104958905020 | .001917930741154 |
| RX20 base | .365004645621491 | .365603247853745 | .000598602232255 |

K35 仅加标量界的差为 −3.225086737e−7，与标量界理论冗余及旧质量标准相容。K35 PF 的保存数值 dual 与 primal 相差约 .000619046，且有约 8.92e−7 的 DualVio；不能据其求解器 OPTIMAL 或局部容差声称精确目标误差也在 1e−6 内。此边界不要求重跑旧 LP，只要求论述和新比较保留质量信息。

| 完整配对 | D 的 U／支持 L／gap% | D+PF 的 U／支持 L／gap% | 主要事实 |
|---|---|---|---|
| K35，cap2400 | .676798845196／.545729444783／19.366079 | .663239294207／.540940474850／18.439622 | U 改善2.00348%，signed gap改善6.69156%，L略降 |
| RB35-T2，cap2400 | .335883588950／.219657578677／34.603063 | .346246203574／.224643138352／35.120404 | U损失3.08518%，L改善2.26970%，未触发原严重双开放参考 |
| K20，cap1200 | .716806546278／.704552496300／1.709534 | .716806546278／.703950558029／1.793509 | 同U、无新证书，PF最终L略弱 |

K35 PF 在583.047秒达到最终更好 U；K20 PF 在131.172秒达到共同最终 U，D 为394.906秒。这是可用的 incumbent 轨迹证据，不是认证加速。六臂均开放，T_cert 均为空；K20 必要验证使 T_total 超过生产 cap，已支付并披露，不是新的工程故障。

R149 新实验总费用12060.885540600秒，build56.177043秒单列；35次 producer Native call 均返回，另有4个诊断 LP。资格夹具与零 GD reader 问题已经闭合，公开10包/133255成员及本次独立复算通过。不重新购买这些旧资格。

### B2. 当前算法定位与历史边界

稳定论文算法仍为 R137 GI-TBC。R147 D 的已有价值主要是有限角色的困难 incumbent 改善；其广泛替代地位尚未建立。R148 Shared-S、R149 PF 已给出真实表达与 LP 信息，但当前完整实现均保留研究用途。本轮两组新 B/D 配对直接补 D 的选择范围之外证据，比重复熟悉四角色的又一整套根强化实验更能改变当前采用判断。

历史中已有较强局部方案，必须保留：K20 STOCK／STOCK+GD 曾约94.261／74.916秒获证；R140 旧 TC+STOCK Seed0 在 K35 的 U/L≈.650438712/.5682885263、RB35≈.3190804927/.2339272621；R145 RN-P 的 K35≈.660923637174/.550645816146。它们附带各自范围、负结果与源码/PE差异，不能当本轮免费匹配控制，也不要求 D 逐格胜过它们。R140 的 Seed1 差异同时伴随源码、PE和运输变化，不称纯 Seed 因果实验。

R47–52 已有 AM 参数/机制及救援研究；R52 更正为三个严重 false-retain，且存在真正 correct-retain 负锚（父 Work≈843.456获证，强制 midpoint≈2651.321仍 capped）。R119 已测动态 incumbent 中断重建；R120–122 已有子域界与条件仿射传播；R130/R137 已有 root-only；R131 已有 budget→domain；R135 已有 AP/IND 表达关系；R133、R144–146 已分别研究整数目标缺口、RN和 GD。下一步不要重命名这些已研究内容，也不必重做 AM 调参、全 Seed 网格或全部 benchmark。

---

## C. 主任务：固定 B/D 的两组完整确认

### C1. 角色与原始配置

两角色在 R137 已测试，现应标记为 **known/exposed**；它们未用于 GD 的选择。N-B35-S 与既有 R-B35-S-T2 是不同物理输入，目标系数也不同。两者均用原 **lambda=.15**，不能复制 RB35 的 rho=1、lambda=1/Omega。

| 角色 | 数据／规模／容量 | 物理 T | 两臂及 cap | 选择理由与旧 B 背景 |
|---|---|---:|---|---|
| N-C20-U | CITI；20站/2车；Q=[30,30]；surplus、compact | 5400 | B、D，各1200s | 原B在265.529477804秒获证，U=.245505069182498；检验正目标的证书表现能否保留 |
| N-B35-S | CABI；35站/3车；Q=[20,25,30]；shortage、compact | 7200 | B、D，各2400s | 原B开放，U/L=.450291503262878/.389310601642106；检验另一物理困难输入上的U/L取舍 |

两输入 pickup/drop 均60秒。N-C20-U 的 Omega=10.477509、rho=1.57162635、initial/target/capacity=271/242/470；N-B35-S 对应18.32、2.748、211/246/502，旧离线 penalty floor=.21。

输入与固定来源：

- `results/unified_exact_round137/inputs/N-C20-U.txt`，SHA256 `93b93b6abed55cf97f8ee21ddd85fb8501554b8e4c35bb997ae75782f1f98e16`。
- `results/unified_exact_round137/inputs/N-B35-S.txt`，SHA256 `80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98`。
- 固定 science 为 A 节 R137 commit；配套 input_manifest、matrix_frozen、arms/pairs 及 selection 文件定义完整原配置。

先冻结两角色、方法与顺序，再看本轮 D 结果。每臂自身生成 own-H，不能注入 R137 最好解、旧 LP 或另一臂 incumbent。物理数据、T、lambda、H seed、Native 参数、PE/DLL与 cap 配对一致。默认先完成 N-C20-U，再完成 N-B35-S；顺序可因正常资源安排调整，已进入合格臂不因输赢临时加时或停止。

### C2. 这两组比较应回答什么

分别报告物理 U、外部支持 L、U−L、relative gap、证明状态与 T_produce/T_cert/T_verify/T_total。对于开放臂，保留 witness 轨迹和必要 Work/节点信息；不能把 cap 附近小总时差叫收敛加速。双获证比较使用同资格 T_cert，并同时给出含验证总费用。

旧 R137 的 B/P/PS 结果只作背景。本轮不补 P-GRB 网格；R147 四角色证据、R149 同 PE 的 D 控制按各自身份保留，不把不同 PE 的端点拼成新的匹配试验或用 capped 时间计算伪 speedup。

默认四个完整臂足以结束本轮主要问题。若仍有**一个会改变 D 定位的具体问题**，允许至多一组匹配澄清，总名义容量不超过4800秒：先书面说明假设、角色结构、两臂 cap 与可能改变的结论，再启动。它不是默认第三角色、不用于事后改算法救输局，也不因 CPF 阳性自动转成 CPF 完整实验。工程身份失配则针对失配处理，不能悄悄挑选重跑中最好的结果。

---

## D. 小额研究：状态条件惩罚反馈（CPF）的数学依据

这里 CPF 暂指 conditional penalty feedback，只是研究标签。先从实际保存模型读出已加权系数，令

\[
p(Y)=\sum_i h_i(Y_i),\qquad h_i(y)=\omega_i|c_i y-1|,
\]

\[
\mathcal R_0=\{Y:\ell_i\le Y_i\le u_i,\quad B^-\le\sum_iY_i\le B\}.
\]

原模型的 penalty epigraph 满足 \(P_e=\sum_i\omega_i e_i\ge p(Y)\)，改善 cutoff 为 \(g+P_e\le U_0\)。\(\omega_i\) 已含 lambda，不能再乘一次。R149 已从资源放松得到安全 \(\underline p_0\)，把统一上界 \(\beta_0=\min\{\gamma_U^0,\operatorname{up}(U_0-\underline p_0)\}\) 传播到所有 \(t_{iy}=g s_{iy}\) 的上端。

### D1. 复用同一对偶，按状态得到更强下界

固定 R149 实际使用的非负乘子 \(\mu,\nu\)，令

\[
a=\nu-\mu,\qquad
m_i=\min_{\ell_i\le z\le u_i}\{h_i(z)+az\},
\]

\[
d=\mu B^- -\nu B+\sum_i m_i.
\tag{1}
\]

对资源可行 Y，\(\mu(B^--\sum Y)+\nu(\sum Y-B)\le0\)，所以弱对偶给出 \(d\le\min_{\mathcal R_0}p(Y)\)。每个 \(m_i\) 只需检查盒端点与盒内折点 \(1/c_i\)（按实际零系数边界处理）。

固定已有状态 \(Y_i=y\)，定义

\[
p^*_{iy}=\min\{p(Y):Y\in\mathcal R_0,\ Y_i=y\},
\]

\[
\delta_i(y)=h_i(y)+ay-m_i\ge0,
\qquad
\boxed{d_{iy}=d+\delta_i(y)=\mu B^- -\nu B+\sum_{j\ne i}m_j+h_i(y)+ay.}
\tag{2}
\]

在条件域上用同一拉格朗日下界即得

\[
d\le d_{iy}\le p^*_{iy}.
\tag{3}
\]

全局 \(m_i,d\) 已算出后，全状态评价为 \(O(\sum_i|\mathcal Y_i|)\)，不需要逐状态 LP、逐状态重新贪心或动态 incumbent 更新。完整条件资源最优值可作少量离线 oracle，但本轮默认检验这一廉价、统一的 fixed-dual 版本。

### D2. 由条件下界得到有效乘积行

安全取值为

\[
\underline p_{iy}=\max\{\underline p_0,0,\operatorname{down}(d_{iy})\},
\qquad
\beta_{iy}=\min\{\beta_0,\operatorname{up}(U_0-\underline p_{iy})\}.
\tag{4}
\]

加入

\[
\boxed{t_{iy}\le\beta_{iy}s_{iy}.}
\tag{5}
\]

整数状态未选时 \(s=t=0\)；选中时 \(Y_i=y,t=g\)，由 cutoff 和 \(P_e\ge p(Y)\ge\underline p_{iy}\) 得 \(g\le\beta_{iy}\)。因此任何满足旧 cutoff 的整数 completion 均保留，包括原本可行的非最小 g/e completion。这里不要求 g 等于最小物理 G，也不能把 \(\min_y\beta_{iy}\) 当作全局 g 上界。

在每站已有 \(s_{iy}\ge0,\sum_y s_{iy}=1,\sum_y t_{iy}=g\) 与 \(t_{iy}\ge\gamma_L s_{iy}\) 下，(5) 给出状态依赖区间的局部 disjunction 凸包：对 \(s_{iy}>0\)，取分支值 \(g_y=t_{iy}/s_{iy}\in[\gamma_L,\beta_{iy}]\)，按权重 s 混合即可恢复该点。空分支相应排除。**这是单站状态与产品的局部表达，不是整个 BRP、跨站资源或路由的凸包。**保留全部原 PF 行，数学上新放松包含于 PF 放松；严格块关系不保证目标最优值或完整搜索严格改善。

条件 \(\beta_{iy}<\gamma_L\) 可以表示该状态的改善域为空，负 beta 也不必与 own-H 矛盾，因为 own-H 未必选择该状态。若遇到该边界，给出状态排除依据、保留有效 signed 行或安全省略该强化均可；不能将整个物理实例判为不可行，也不照搬 R149 全局负 beta 的错误语义。

### D3. 安全算术与既有机制的区别

本轮用纯 Python Fraction 解释实际 binary64 系数和乘子即可。不要直接用两个独立的 lower bound 做 \(\underline d-\underline m_i\)：减去下界未必给出下界。应精确评价 (2) 的 leave-one-out 表达，或用方向明确的区间/前后缀和。beta 向上运输才安全；实际不紧于旧 beta 的行省略，tiny 系数按现有运输语义安全放宽或省略整行。

R135 AP 主要提高 \(P_e\ge\sum_{i,y}h_i(y)s_{iy}\) 的惩罚 epigraph；(5) 则限制具体状态能承载多少 g 产品质量。局部例：支持 y∈{1,2}，h(y)=.4|y−1|，U0=.8、gamma_L=0、beta0=.8。点 s=(.5,.5)、Y=1.5、g=.4、t=(0,.4)、P_e=.2 满足 AP、cutoff 与 uniform PF；条件 beta2=.4，(5) 却要求 t2≤.2。它证明保留 t 坐标的局部块上 AP 不蕴含 CPF，不冒充完整 BRP 可行点或一般 AP/CPF 支配关系。相同的 (s,g,P_e,Y) 可改用 t=(.2,.2) 满足 CPF，所以实际价值仍须由完整模型中全部变量自由重优化判断。

R120–122 的条件 F 下界依赖已求子域 LP；R146 GD 的状态条件信息用于总 ratio S 的系数；R131 主要缩域；R149 使用统一 penalty floor。这里传播的是同一资源 dual 的状态代价差 \(\delta_i(y)\)。弱对偶、条件化和 disjunctive hull 都是标准思想，论文贡献应落在本问题的表达关系、低成本构造和实际证据上。

---

## E. CPF 的有限 LP 检验

### E1. 已有零求解证据

独立审查直接在 R149 新 PF 点上，用同一实际 binary64 乘子计算条件行，没有修补点或新求解：

| 保存 PF 点 | 状态数 | fixed-dual 行违反数 | 最大违反 |
|---|---:|---:|---:|
| K20 base | 451 | 15 | .019306833244 |
| K35 base | 539 | 34 | .003655840423 |
| RX20 base | 143 | 8 | .051858032938 |
| RB35 正式根，仅背景 | 566 | 5 | .001092469154 |

所查条件资源盒均可行、beta 均为正。每站把这些行求和得到的 \(g\le\sum_y\beta_{iy}s_{iy}\) 在这些点上仍有明显 slack，分离来自具体产品分配。现有证据只支持“值得检验剩余 LP 信息”，不保证 LP 新最优值提升。

### E2. 默认三个新 LP，不扩大为生产研究

直接复用 R149 fixed science 中 **K20、K35、RX20 的完整 PF model.mps、旧 result/solution/arithmetic**，保留旧 PF 行，仅追加 D 节 fixed-dual 条件产品行。新旧目标、常数、cutoff、变量域、支持和所有旧行保持一致，全部变量自由；删除新增行后逐项核对旧模型语义。原 D 与 PF 合格记录直接复用，不再求一遍旧 baseline。

默认三个位置、每次 Native LP cap120秒，Seed0/Threads1；记录实际新行/NZ、构造与读回成本、原/新目标及质量、保存解、模型 SHA、乘子和运输系数。将 **CPF−PF** 与 **PF−D** 分开，不能把既有 PF 增量再次算给 CPF。

K35 已有数值 primal-dual 诊断差，不能把微小新差值自动叫严格增量。若质量或目标比较确实影响判别，优先离线检查；必要时允许对其中一个新 CPF 模型最多一次额外 Optimize 作定向质量复核，仍在小额预算内，不重求旧 baseline、不增加第四个域。仍不能分辨就报告数值不确定，不为字面精确最优反复重求。其余已闭合浮点问题不重新展开。

结果无论正负都在此槽收束：

- 旧点被切、新 LP 无可分辨增量：保存替代最优点或数值边界，结束当前资格；不要把最大违反量当优化收益。
- 有实质匹配 LP 增量且构造成本小：形成后续统一 CPF 候选的准入依据，明确最有信息的下一步与风险；本轮仍不自动写 C++、生成新 PE 或启动 CPF full。
- 无法建立有效 scope 或质量：说明原因并停止相应位置，不影响独立的 B/D 主任务验收。

RB35 已保存根的筛查足够作背景，不默认增加第四个 LP；不同时做 exact-conditional 与 fixed-dual 两套矩阵、AP/STOCK/Shared-S/RN 组合或迭代多轮传播。合理的小额诊断可从未启动容量调剂，需说明新增信息。

---

## F. 最小工程路径与必要资格

### F1. B/D 复用现有生产版本

优先从 R137 `matrix_frozen.json` 复制两角色 S2 的完整参数，结合 R147 支持 BASE/GD 的冻结/执行逻辑，建立本轮窄 wrapper 或 manifest。R149 campaign 将 GD 固定为开启，不直接拿它生成 B。

- B 明确 `--round146-gd off --round149-penalty-feedback off`。
- D 明确 `--round146-gd on --round149-penalty-feedback off`。
- 两者都用 A 节同一 R149 PE，Shared-S/STOCK/AP 关闭，原 H、AM、物理 T 与目标保留。

`paper_s2_gd_only.py --exe <R149 PE>` 可以产生相应 argv，但旧 profile 中 source_commit/verified_PE 仍指旧版本；不能把该 launch 元数据直接当本轮实际身份。R150 manifest 应登记真实 R149 source/PE/DLL 与新 wrapper，并单列旧方法定义。原稳定与研究入口、配置不改字节；不靠放宽身份检查冒充同版本。

复用现有 producer、seal、closeout、物理/R134验证链。reader 可结合 R147 verify 与 R149 已合格的 first-call-SHA root_context，保留 early-closeout guard、GD零行及 own-H 已完成而无模型路径。**不预设新角色一定5次调用或2条GD行**；核实实际发生调用全部返回、绑定正确，实际行组按合格 GD 构造判断即可。

新增资格集中于四条冻结 argv、两个输入及lambda、真实PE/DLL、OFF行为和新角色实际GD行读回。无生产变动不额外编译，不补旧全套资格，也不为“暴露模型”强迫已早获证角色再求解。实际新问题只作定向修复。

### F2. CPF 保持离线 LP 路径

复用 R149 的 MPS semantics、append/readback 与 LP 质量记录，增加纯 Python 算术和条件行输出。先核查一两个代表状态的公式/系数及数学方向，再运行三个新 LP；不提前购买生产 child、缓存、Start、全调用资格。若未来进入生产，届时才按实际路径验证。

保留原始 LP/solution，所有新 artifact 另存。记录实际送入求解器的行组，不把理想完整组与 tiny 省略后的矩阵混同。来源恢复先用已有封存或固定公开成员；不加载旧 producer 来重写已关闭证据。

---

## G. 判断口径与预算

### G1. 本轮结束时必须作出的两项判断

**D 的定位：**结合 R147 已有选择结果、本轮两个角色与必要轨迹，判断 D 是否可作为一个有限统一论文增强候选继续组织。允许普通损失与可解释取舍，不要求两新角色或全部历史角色全胜；若新增证据暴露重要短板，收束主张或保持研究候选即可，不修改成按角色选择算法。稳定 B 的论文成果不因 D 未晋升而失效。

已有严重双开放参考仍可用：U损失超过 max(.001,5%·U_B)，且 signed-gap 损失超过 max(.005,25%·gap_B)，是明确严重信号；它不是唯一质量标准，也不是低于阈值就必须采用的规则。证书保留、实质 U/L、完整费用共同判断。统计范围只覆盖实际测过配置，不宣称广泛稳健或新数据分布泛化。

**CPF 的资格：**明确停留在点分离、匹配 LP 增量、或数值未分辨哪一层。即使 LP 阳性，也只说明未来值得评估完整成本；若阴性，保存有用的结构与替代最优面证据，正常结束。两个任务的结果不互相充当成功条件。

### G2. 容量与计费

| 阶段容量 | 秒 |
|---|---:|
| 必要入口/参数/身份核查与定向资格 | 600 |
| CPF 三个 LP、条件算术与定向质量检查 | 600 |
| N-C20-U：B/D，各cap1200 | 2400 |
| N-B35-S：B/D，各cap2400 | 4800 |
| 至多一组有明确判别价值的 D 配对澄清 | 4800 |
| 失败、必要验证超窗口与外层开销余量 | 1200 |
| **总上限** | **14400＝4h** |

默认仅四个完整臂，名义生产容量7200秒；早获证按实际费用，不要求用满。各槽可在总额内调剂，启动下一项前预留完整 cap 和验证余量。澄清槽不是预订必须执行的实验，释放容量不重复计算。CPF 需要更多小额质量处理时，优先从未启动槽调剂，不挤掉已进入完整臂或悄悄扩总额。

所有新增 own-H、算术/构造、求解、资格、失败与必要后验验证按外层计费一次，嵌套 Runtime/Work 不再相加。纯离线理论/文稿、公开纯 I/O单列；默认无build，确有必要变动则单列且重申匹配身份。少量测量不完备如实披露，不用补跑搜索换秒级账面精确。

---

## H. 论文整理与独立复核

形成可并入文稿的一节与一张证据关系表，而非重写全部论文。至少清楚区分：

1. **稳定完整方法：**GI-TBC 的问题结构、严格求解框架、已有广泛实验与数值证明政策。
2. **已研究表达：**GD 的状态条件分母信息；Shared-S 的共同分母仿射族；PF 的全局惩罚信息→产品上端；CPF 的条件代价差→状态产品上端。哪些是投影中已隐含的标量界、哪些改变扩展表达，要有实际前提和推导。
3. **证据层次：**有效性/局部强弱关系、实际保存点分离、匹配 LP 增量、完整 own-H 表现；保留 K35/K20 PF 的早 incumbent 正面，也保留 RB35 的反向代价。不要把 no-promotion 写成理论无效。
4. **研究边界：**R133 整数目标缺口与连续传播并非同一困难；本轮不宣称解决全部整数 epigraph 或获得通用新凸化理论。OR级更强主张仍需后续更有解释力、可推广且具有完整算法价值的结果，不能靠增加验证数量自动取得。

完整配对启动前做一次有针对性的独立检查：两角色输入/目标、PE/flags与冻结设计正确；CPF 求解前检查 (2)–(5) 的符号、加权单位、算术方向和实际矩阵。交付时再由非主要实现者复核：

- R149 原信息与历史强/负结果未遗漏，known/exposed 与方法选择范围表述准确。
- CPF 未误用下界相减、未把条件 beta 当全局界，局部 hull 未扩称全模型 hull；新旧 LP 比较与数值边界清楚。
- B/D 控制真实匹配，原默认算法保持，调用/封存/费用闭合；没有重复baseline或隐性完整矩阵。
- 两任务能独立结束，预算加总正确，澄清会改变明确决策；没有把每例全胜设为验收条件。

发现实质问题则修正，复核通过后收束；不为已合格微小残差、排版或轻微时差再开完整求解。

---

## I. 交付、Draft PR 与有限清理

交付本 goal、冻结配置/身份、实际进入的 B/D 结果与轨迹、CPF 数学和匹配 LP 证据、费用、采用/不采用结论、论文小节、独立复核及 RESUME。可合并文件，按信息完整性验收。保留所有已进入运行、失败与必要原始证据；旧大包用固定 commit 与成员hash引用，不重复整仓历史。

正常提交、推送，创建英文 Draft PR，建议标题：

**Round150: confirm standalone GD and screen conditional penalty feedback**

按实际吸收状态选 main 或核实后的 R149 临时 base，读回 base/head、Draft与交付状态。不自动merge、force-push或删除旧分支，不因等待合并阻塞本轮。当前是研究与论文定位任务，不借此再开全项目main合并/历史清理轮。

对必要新增公开载体做一次有限字节/成员恢复即可，纯 I/O建议累计30分钟内收束；不触发Optimize、编译或商业Native，不为恢复再次购买旧性能。附件不可取时按J节固定来源和公式继续。

**继承 WORKSPACE_POLICY：**所有新build/raw/temp/restore均在 `E:\codes\ExactEBRP-work`；保护 `E:\codes\ExactEBRP` 与用户修改。仅清理本轮已完成、可重建且有公开恢复覆盖的临时/重复对象，保留唯一raw、失败、必要运行资产、活动树和旧历史。记录保留/删除及字节，零删除可接受。

---

## J. 最小资料索引

- 当前PR：https://github.com/yifanXovo/TailoredExact/pull/211
- R149固定science：https://github.com/yifanXovo/TailoredExact/tree/3bb93fa2f4b8c267af8fae409864191e033c5bb2/results/unified_exact_round149
- R149：goal.md、final_report.md、mathematical_analysis.md、LP_report.md、candidate_decision.json、candidate_manifest.json、cost_report.json、carrier_manifest.json、RESUME.md；reports/full.json、reports/verified_U_trajectories.csv。
- CPF三基线来自R149 `artifacts/diagnostics_qualification_failures.zip`，SHA256 `09a128897c372e3c46c98af18418852080348c639fea03c843d22aec865b332e`；成员为 `results/unified_exact_round149/LP/K-20-S_PF/`、`K-35-U_PF/`、`R-X20-S-T1_PF/` 下model/result/solution/arithmetic。
- RB35 PF根背景来自R149 `artifacts/campaign_rb35_002.zip`，SHA256 `ce6d6a0222aeb732baa3b1fae1fe1eb1a956edbdf27ef392beeb4e1e3dfdc630`。
- R137固定science：https://github.com/yifanXovo/TailoredExact/tree/e735c3447eb1443713c700942d873de1783a4a26/results/unified_exact_round137 。读该目录下 input_manifest.json、matrix_frozen.json、reports/arms.csv、reports/pairs.csv及inputs中的两原输入；以原输入SHA为准，不另生成替代实例。
- R147固定science：https://github.com/yifanXovo/TailoredExact/tree/a0673b683c645d35de829fa101a55cc9fc4774c7/results/unified_exact_round147 。实现参考位于仓库根scripts：scripts/round147_campaign.py支持BASE/GD；使用R149版本的scripts/round149_context.py与scripts/round149_lp.py，分别提供first-call-SHA语义与匹配MPS路径。
- 历史：R47–52、R119–122、R130–137、R140、R144–148最终报告；docs/current_mainline.md、docs/unified_exact_research_index.md、WORKSPACE_POLICY.md。
- 本次外部审查附件：TailoredExact_Round149_Stage_Review.md；TailoredExact_Round150_Review_Evidence.zip。包内独立math/experiment/engineering复算脚本与回执、零求解CPF筛查和恢复索引；不依赖附件中的旧绝对路径，按README指定归档路径即可复核。

**成功标准：用有限完整比较明确D的论文定位，用三个同域LP判断条件资源信息是否还有可用的表达增量，并将已知数学与算法证据组织清楚。结果支持采用、限制主张或停止某条机制，都可以完成本轮；不以一定产出新算法作为验收条件。**
