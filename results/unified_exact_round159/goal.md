/goal

# Round159：联合优化数量与车辆归属，辨明整数资源解的物理可实现性

## 0. 本轮目标与执行原则

本轮继承已完成的R158，不原样重跑36h的低目标常数可行性模型。核心问题是：**从合格可行车队出发，直接优化原目标，通过一个统一的数量/归属联合限制域，能否以合理成本获得更有信息量的整数资源上界，并将其中的改善转化为真实路线？阻碍转化的究竟是累计handling、车辆分配、高阶travel，还是prefix load与数量的耦合？**

只研究一个可解释、可复用的机制。短的固定owner资源优化作为基线，主要容量用于联动多个站的quantity与owner，并尽早检查代表点的物理实现。R157已有原J资源模型，R158已有联合库存/归属随机搜索；本轮不能把“改用原目标”“增加owner交换”“调用完整车队oracle”本身当成新贡献。

总科学实验容量为**36h=129600s**，不是必须消耗的时长。优先交付能改变研究判断的资源/物理区间、机制证据或有充分解释的有限负面；不要求新资源upper、全域lower、物理路线与完整算法收益四项同时成功。不通过增加报告门槛、重复历史实验或延长UNKNOWN来证明工作充分。

论文目标是具有一般数学依据、明确精确性接口和完整成本证据的算法研究。允许使用当前库存、容量、目标边际量、归属、几何与资源余量等问题数据；**不允许按实例名、预设规模类别、历史输赢、机器型号、CPU速度或内存大小分派机制，不允许运行若干秒后切换算法**。有限block大小、节点/状态/迭代容量必须采用同一规则与冻结参数；容量耗尽返回有限结果或UNKNOWN。离线研究阶段的预算和完整方法的普通总deadline正常使用，不能转化为在线时间触发策略。

稳定论文主线GI-TBC/B（S2/ms2）及其正式入口保持不变，E+作为增强参考。不得把裸CLI的ENS-C兼容默认误作GI-TBC。新候选采用独立、默认关闭的研究入口，保留原exact engine的全域覆盖、有效cutoff与proof ledger。构造子程序可以是有界局部优化；它本身不因此成为全域精确算法，不能用其失败删除全局可行解。

默认Gurobi Seed=0、Threads=1；完整臂own-H seed=20260626。原pair-only、AM=.08、depth8、minimum width=1e-4及既有数值接受政策沿用；E+保持RN16384与R154 proof-only consumer。

**实现语言约定：本轮新增的在线算法核心默认采用C++，并以通过资格验证的C++生产实现进入正式完整性能比较。** 范围包括数量/归属模型构造、反复执行的邻域/DP/分离与callback、在线completion及结果回传。在现有C++/Gurobi接口能够满足要求、正确性与集成没有实质障碍时，不因Python原型较易编写而将正式核心改为Python。沿用项目编译与数值政策，避免为了语言统一改变目标、物理条件、精度或接受规则。

Python可继续用于离线研究原型、实验编排、日志/费用整理与独立验证。复用已有复杂研究接口时可以先做Python原型，但要标明其角色及C++落地边界；已合格的共同E+依赖在对照两臂中保持一致，不要求全量重写历史框架。若本轮尚不能在预算内完成合格C++集成，可交付有限研究结论并停止进入F，不将Python原型耗时直接当作最终C++候选的提升或淘汰依据。已有数学证明、合格见证及有明确作用域的求解结果不因实现语言而失效。不得以语言迁移代替算法进展、预设C++必然更快，或扣除Python成本后宣称实测加速。

## A. 起点、历史排重与真正增量

工作入口：`E:\codes\ExactEBRP-work\worktrees\paper-current`。先核远端、适用AGENTS.md / WORKSPACE_POLICY.md、用户修改、活动进程与实际依赖。原项目树`E:\codes\ExactEBRP`受保护；为R159在work根下建立自己的隔离worktree，不将已有论文树或dirty树当作可随意reset的临时目录。

2026-11-09审查时的身份如下；执行时刷新远端，不把历史记录冒充当前状态：

- 仓库：`yifanXovo/TailoredExact`；最新已执行轮次为R158，PR #220，Open Draft、未合并。
- R158 branch：`codex/round158-resource-value-levels`；delivery head：`d58cbcca6d2c656a2af09d701bcd9ca0c7a07e85`。
- R158 fixed science：`163b1b3d0dbcc7be3a84d94108ef4a26ae9baba3`；main：`b2b940c1e517a72e226ec60fc49ff19651737632`。
- 继承production source：`092bad58d677cd8bef934d91e11d8abff93cba83`；PE SHA256：`e5efe978f33e5c812fc9a0484caaae80696e4197ae27e289b4894d586af9d7e6`；Gurobi DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

若main已吸收所需研究链，从main开始；否则从核实后的R158 head建立stacked分支，Draft PR以对应R158分支为base，无需等#220合并。science、production source、二进制和delivery head分别记录；若已有更新的R159工作，先合并已授权的实际进展，避免另起重复轮次。

先阅读当前研究索引及下列相关结论、数学说明和实际接口，形成一张有限的“已做—本轮变化—仍未回答”表。已有合格资料只读复用，不重拉全历史载体或重跑旧producer。

| 历史 | 已经完成、必须继承的认识 | 本轮的边界 |
|---|---|---|
| R76 / R83 | 未访站插入、数量闭包、方向变化、等净量block跨车交换及随后quantity改进 | 不将这些动作重命名为新机制；新限制域需明确其额外联动自由度 |
| R96 | 固定路线/owner的完整数量优化，删零、翻向、压缩travel；固定owner自由次序及多站变化诊断 | 固定owner优化只是廉价基线，经典DP和路线completion不是新理论 |
| R103 | 完整逐车必要resource hull、分离/定价、重组和anchor加强；切掉旧点后可在相同J重组 | 不以切一个分数点或增加同类per-car rows推断目标/整算法提升 |
| R105–107 | assignment master、完整physical oracle、IIS/core、MST/三站冲突、MIPSOL及frontier接入；完整结果负面 | 不重建大分解框架，不把旧负面简单归因于oracle算得慢 |
| R138–151 | stock/count/RN/GD/PF等多轮真实LP增强及完整表现回退 | 不做旧cut组合、AM/split、Seed或开关网格 |
| R152–156 | 库存hull与完整Q反馈、proof-only E、RN16384的E+；同标量库存floor余量已很小 | 不重复K35/NC20长pricing反馈，不追同一floor的小数位；复用E+有效接口 |
| R157 | 原J资源模型、全车队completion、RX35原26向量有限排除，未形成有用全局L_R | 原J建模和自由车队oracle不是新开发目标；有限族不是全域k-best |
| R158 | 131072步联合库存/归属搜索，含库存邻接、owner移动、双owner交换、成对库存转移；完整level与physical脚本 | 旧搜索从超T低价点出发，并把低tau作为违反项、只保存J≤tau。本轮改为合格可行起点、撤低tau、联合限制域直接优化原J、保存全部合格改善点并检查物理转化 |

R158完整自由库存/归属的RX35 quarter level（J≤.2519564273646922）运行36h，258972节点、0整数点，返回TIME_LIMIT/UNKNOWN；没有排除该level，常数目标bound=0不是原J lower。Y3十成员与NB singleton的资源排除仍是有限族结果。精确1/3归属点满足raw/rounded裸LP，确认LP弱点，但不是整数资源upper，也不是新增整数cut的能力上限。R158没有新完整候选臂。

R158已修正生产duration绑定：实际采用`sqrt(dx*dx+dy*dy)/1.5`，旧reader的`hypot`不能继续混用。复用已修正系数、单侧包络和资格；旧排除向原/guarded T的转移不等于旧min-time数值与新模型完全相同。36h日志中callback约432.35s（约0.334%），不足以支持“Python是主要瓶颈，因此迁移后重跑”的安排。

**本轮预期增量**应落在统一数学状态驱动的数量/归属联合限制域、少量早期物理检查及其反馈，说明何种结构允许资源降价转成路线改善。若最终没有超出既有机制的可验证增量，应诚实关闭本轮候选，不强行包装为论文创新。

## B. 测量对象、有效界与结论边界

沿用原目标`J=G+H`，H已含lambda。令`r_i=Y_i/D_i`、`S=Σr_i`；S>0时

\[
G(Y)=\frac{\sum_{i<j}|r_i-r_j|}{nS},
\]

S=0按已修复的独立zero分支处理。当前研究根scope为gamma_L=0；所有比较必须绑定同一原改善scope、库存支持、目标权重、输入和数值覆盖合同。保留R133/R134的有效性修复，不恢复旧的inclusive-cutoff冲突或未经资格的zero shortcut。

- `D_I`：原整数库存放松域。
- `D_F`：仅去掉R157原26个已证库存向量的域；NB35取`D_F=D_I`。不因后续有限族排除悄悄改变其定义。
- `D_R(T)`：原T下，自由owner、合法单站服务/资格、逐车收支与返回容量、完整handling、至多3站tour必要条件的库存投影。
- `D_P(T)`：原物理车队可行库存投影。

\[
D_P(T)\subseteq D_R(T)\subseteq D_F\subseteq D_I,\qquad
F_I\le F_F\le F_R\le F_P.
\]

这里`D_R⊆D_F`来自已有必要资源证明，而不是仅凭“物理不可行”推断：R157两族的六个和二十个成员均被自由归属、逐车handling及1/2/3站tour模型排除；R158实际系数修正又核实整数budget及这些排除保持。复用这条证明与接口映射；`round157_floor.attach`本身不安装26个no-good，不因此要求新在线算法读取旧库存禁表。若实际改变资源条件或接受scope，须重新建立相应包含关系，不能沿用未经覆盖的域名称和结论。

经独立验证的整数资源点给`U_R=J(Y^R)`，所以

\[
0\le F_R-F_I\le U_R-L_I.
\]

若`D_R⊆D_C⊆D_I`，则`F_C≤F_R≤U_R`；这限制的是**包含同一资源域的独立标量放松**。不能据此宣称所有同源cut加入完整routing relaxation `Q`后都无收益：资源点可能无法扩展进Q，`proj(Q∩cuts)`未必包含D_R。更强travel/load信息形成的新域也须另命名、另说明包含关系。

若确需对完整Q中的联合收益作上限判断，才进行一次有明确用途的有界extension检查，并给出该组合对象的可行upper见证。涉及owner/service的cuts时，须验证与Q共享的完整resource lift；仅固定Y、让Q任选分数owner不够。Q点不是物理路线。固定`(Y,owner)`的合格不可行仅排该固定组合；只有证明physical embedding、仅固定Y且所有合法owner及所需辅助自由度均开放的合格不可行，才可能排除整个Y。UNKNOWN、数值资格失败和容量耗尽从不构成排除。本轮不强制重开完整Q-hull研究。

固定owner或有限block域记为`D_R(A,N)⊆D_R`：可行点可给全域资源upper，其ObjBound/局部最优/不可行仅属于该限制域，不能进入全域L_R或BRP proof ledger。没有找到低U_R不证明F_R高；严格资源最优值差仍需全域合格`L_R>U_I`。`U_P−U_R`只是两个见证的价格差，不是`F_P−F_R`的严格下界。

R158原研究scope的参照区间为：

| 角色 | L_I | U_I | 原粗U_R | U_P^ref |
|---|---:|---:|---:|---:|
| RX35 | .2360521029074557 | .23612171136420015 | .2996694007364017 | .2996694007364017 |
| NB35 | .3959564087240911 | .39604654895666136 | .450291503262878 | .450291503262878 |

NB35这里是对应E+来源scope，不能混入另一个7200s B臂的upper。RX35/NB35同标量库存floor最多尚余约`6.96085e-5 / 9.01402e-5`，仅为上述物理gap的约`0.1094% / 0.1659%`，不是本轮优先追逐对象。

对每个角色固定上述`U_P^ref`，报告

\[
\eta_R=\frac{U_R-L_I}{U_P^{ref}-L_I}.
\]

eta_R是同资源标量域相对于既定参照gap的区间指标，不是完整算法兑现的gap缩减。quarter/tenth等水平只作离线刻度，不是生产分派规则或统一验收阈值；不得用单个eta阈值替代实际价格、成本与物理转化判断。

## C. 复用审查侧见证与已闭合的固定owner问题

以下属于审查侧证据，不是PR #220的新成果、完整benchmark或正式候选start。按原输入与源码独立读回一次即可，无需依赖聊天附件。

从R157 `results/unified_exact_round157/inventory_families.json`的RX35 positive_control读取原物理库存与归属，保持owner；按1基站号修改站3库存6→5、站16库存6→7，两站均属vehicle=2（0基）。得到：

```text
[6,7,5,6,6,3,6,5,4,2,4,5,3,2,3,7,2,4,3,4,2,6,1,7,1,3,2,2,4,3,4,7,4,6,7]
```

\[
U_R=.29453694232737326,\qquad
J=\frac{53479593056830315041420782091893493405343450472395547}
{181571766971725310832917143964057992450020736269025280}.
\]

三车P/D为`12/12、16/16、25/25`，返回均0；至多3站必要资源时长约`5780.7600413、5844.6113321、6249.7962479`，均≤6300。审查已验证实际模型所有24153条非level行、2673列界及独立资源重建；只违反旧quarter cutoff。它将资源区间宽度降到约`.05848483942`、eta_R约`.91932291`，仍远不足以关闭资源研究。

**该点的固定Y、固定owner、任意重排问题已经闭合：**

| 车辆 | 活跃站数 | 最短travel + 完整handling | T |
|---|---:|---:|---:|
| 0 | 7 | 5854.746524678982 | 6300 |
| 1 | 11 | 6159.258006706421 | 6300 |
| 2 | 14 | 6412.088151837445 | 6300 |

此结论来自穷尽`(visited subset,last)`的load-feasible DP：固定Y/owner时，前缀载荷等于`Σ_{i∈S}(b_i−Y_i)`，与顺序无关，允许状态满足`0≤load(S)≤Q_k`；加完整handling与回仓卸载后覆盖该固定组合的全部基本路线次序。所有1296个duration与修正后的实际生产系数一致，并在共同`2^53`尺度上精确累加二进制系数。这里的精确性属于已绑定的离散系数模型及既有接受政策，不能扩大成所有欧氏实数运算的普遍符号证明。

独立无载荷TSP递推对车2得到同一最短travel：

\[
3412.0881518374454
=30733357858340806333/9007199254740992.
\]

旧三站travel lower为3249.7962479000835。对这个固定活跃集，完整tour信息已将pickup预算从25降至24；原physical positive的P=24，总时长6292.088151837445，尚余约7.91185s；审查点P=25新增120s handling，超时约112.08815s。

因此，**不要再为这个相同Y/owner支付2-opt、自由重排MILP或另一遍大预算completion**。必要的来源绑定、轻量DP重建及positive control资格允许复用/复核。它没有排除同Y换owner，也没有排除同owner改变数量或活跃集；“纯travel已解释这个点”不意味着prefix load一般无关。后续新增自由度应放在数量与归属上，不能把经典subset DP包装为新贡献。

## D. 主任务：一个从合格点出发的联合数量/归属机制

### D1. 短的固定owner原J基线，避免重复建模

复用R157原J/RN映射与resource attach，从已有合格physical/resource点开始，撤去R158继承的过低quarter cutoff，直接最小化原J。保留原合法改善scope；不要用constant-zero objective，不要仅保存J≤旧tau的点。native objective的中心化、scale和lower transport沿用原接口，不能直接把native ObjVal/ObjBound当作原J。

用当前见证定义互斥车辆站集`A_k`。初始未归属站可暂固定`Y_i=b_i`；归属站保留原scope全部合格库存支持，允许归零、翻向、单站`|b_i−Y_i|≤Q_k`。one-hot `x_iy`下：

\[
P_k=\sum_{i\in A_k}\sum_y(b_i-y)_+x_{iy},\qquad
D_k=\sum_{i\in A_k}\sum_y(y-b_i)_+x_{iy},\qquad
0\le P_k-D_k\le Q_k.
\]

空车出发、允许带货回仓且回仓卸载计费时，

\[
t_pP_k+t_d(D_k+R_k)=(t_p+t_d)P_k,\quad R_k=P_k-D_k.
\]

`Q_k`限制前缀/返回载荷，**不能添加`P_k≤Q_k`**。

可直接复用已有active-subset编码；若轻量实现使用完整`A_k`的保守预算，令

\[
L_3(A_k)=\max_{S\subseteq A_k,\ 1\le |S|\le3}\ell(S),\qquad
(t_p+t_d)P_k+L_3(A_k)\le T.
\]

空集取0。保留所有其他原resource条件，输出再按完整D_R读回。部分站归零后仍使用完整A_k，只是更保守的**内限制**，不能宣称穷尽了删除零服务后的全部数量可行域。整数budget的floor必须沿用实际系数包络与边界接受政策，不裸舍入。

RX35初始三站预算`(16,19,25)`，原physical点P为`(12,16,24)`，故有合格可行start。两研究角色的固定owner基线合计默认控制在D阶段约2h以内，不要求跑满或证明局部最优；该离线容量不是在线触发参数。主要时间留给下述联合释放。

### D2. 冻结一种基于数学状态的联合限制域

选择**一种**基于当前handling/travel余量、原J边际影响、归属与几何的block选择规则，在一个受限子问题中联动多个站的数量和车辆归属。说明为什么它能离开已有R76/R83闭包及R158四类随机move的单步限制；不得只原样重复旧随机搜索。

把固定/释放的quantity、owner、active set及route自由度写清楚。所声明的搜索序列应能允许未服务站activation、服务归零、方向变化、跨车归属和非等净量数量联动；无需每次释放全部车辆或所有站。外部固定站的收支、服务与返回影响必须完整保留。若实际未开放某种自由度，结论明确保留该限制，不能称已检验全自由车队。

同一个规则与参数用于RX35和NB35。离线只允许为新接口做必要的有限校准，随后冻结block选择、容量、平局规则、接受准则与停止条件；不展开邻域/参数组合搜索。可用统一的节点、状态或迭代容量；它们是算法工作界，不按机器速度校准成秒数，也不证明运行时间与硬件无关。

当前最好合格点作为限制域start；无需等局部最优才接收改善。若使用不可行中间状态或penalty探索，单独标识，只有完整resource读回且原J重算通过的点可更新U_R。若采用非降价中间移动，定义有限记忆或明确的词典序潜势/停止规则，避免循环；有限终止不等于全局最优或多项式复杂度。

### D3. 提前检查物理转化，避免只积累低价资源点

在资源改善过程中选择少量原J与归属/handling结构确有信息差异的点，先做轻量固定Y/owner completion或复用已有oracle；初期每角色1–2个代表点即可。不要对每个局部点启动重型完整fleet模型。对已闭合的C节点，直接使用现有结论。

统一容量下的固定Y/owner DP若完整结束，可给该组合的最短路线/不可能性；未穷尽则UNKNOWN，不能当不可行筛掉。已有合格可行路线可独立接受。使用同一有限子程序，不引入“站数小用DP、站数大换另一主算法”的硬编码分派。

若要把完整active-set travel反馈到可变Y子问题，优先使用**与Y无关的合格无载荷tour lower**，并与旧L_3取max。固定旧Y的load-constrained最短travel可能在新Y下下降，不能自动作为所有新Y的必要lower。若仅将其作为过保守的primal过滤，必须明确其内限制身份、逐点验D_R，并禁止任何全域lower运输。

站归零时，旧完整A预算可保留为保守内限制；新增站或变owner时，必须更新/正确条件化resource与travel表达，不能沿用已不覆盖新集合的budget。把所有可选站无条件塞进共同superset可能排掉当前start，不能不加说明地采用。固定集合的tour bound若欲成为一般cut，还须证明activation条件、superset关系与实际系数包络；本轮不要求因此开发一整族cuts。

每次新资源点记录Y、owner、原J、逐车P/D/return、必要资源时长、active set、源码/实际模型身份和外层费用；每次物理检查另记开放自由度、状态、路线/下界、费用和资格。资源U_R与物理U_P分开维护。RX35是主要开发来源，NB35是第二来源；角色只用于离线实验安排，线上机制不得识别这些标签。

D阶段总容量10h。用短基线、统一联合限制域与少量物理反馈回答：改善来自何种自由度、哪个结构限制了转化、代价是否可能在线自付。优先用已保存轨迹或一次必要的同条件消融区分新增量，不为表格完整另开实验网格。

## E. 仅在能改变判断时，选择一条深入路径

进入较大调用前，内部记录：对象与开放scope、待改变的判断、已有证据为何支持这次调用、容量和正常保存/停止方式。无需为这些已授权研究步骤反复请求审批。D没有成功本身不构成启动长跑的理由；可以直接收束为有限负面。

E总容量8h，以下**择一深化，不全部执行**：

### E1. 优先：联合释放后有希望的物理实现

对最有信息价值的少量点，利用已有R157/R158自由车队模型，或明确的有限重分配，放开必要的owner/次序自由度。assignment作Start不等于固定owner；实际固定范围要读回。若同Y固定owner失败，只有在改变结论确有价值时才支付自由owner查询，不把全车解锁变成强制清单。

验证完整travel、唯一非零服务、前缀载荷、返回与卸载、原T、原J及全部原物理合同。得到真实路线可更新U_P；证明/UNKNOWN严格限定实际scope。若仅观察到fixed-owner不可实现，就解释其handling、tour或load原因，不将其写成全fleet不可能。

### E2. 备选：一项有独立依据的更强结构

仅当D提供具体缺失信息时，研究一项超出旧表达重排的必要条件或联合限制域。先给一般有效性、物理embedding与作用scope，再看自由重新优化后的目标或可行点生产。仅分离旧1/3点、缩小一族、减少行数或改进根LP不足以声称整算法更强。

明确它与R103逐车hull、R105–107的MST/三站/IIS/master不同之处。新域记为`D_R^+`等，不把其lower与旧域混用；其合格点若同时满足旧D_R，仍可给旧U_R。没有新结构依据就不实施这一分支。

### E3. 后备：一次有时间目标的全level研究

只有当一个明确的整level问题仍能改变决策、模型与start已经合格，才允许一次有界调用。先定义时间研究的库存域`D_I^{time}`：若保留B节固定D_I，就明确只测该scope内的条件min-time；若为无条件变量时间解释而撤去原T导出的库存域收缩，另记扩大的`D_I^{time}`，不与B节F_I/U_I区间混同。定义

\[
\Theta_R(\tau)=\min\{T^*:Y\in D_I^{time},\ J(Y)\le\tau,\ (Y,a)
\text{满足资源条件且所需时间}\le T^*\}.
\]

它应给有含义的时间上下界，而非再次支付constant-zero UNKNOWN。已知Y3超T assignment若满足tau，可以提供合法时间upper；J>tau的physical positive不能作该level可行start。若已有`U_R≤tau`，存在性已回答，不再求同level。

若声称无条件变量时间域，撤去/合法替换所有原T导出的budget、forbidden subset、删列/库存支持收缩和固定T排除；尤其不能带入只在原T证明的有限族no-good。域扩大后，原L_I或其他scope派生行只有重新证明覆盖扩大域才可保留。若仍保留固定T限制，只作相应条件模型解释。用于原T整level排除时，模型仍须覆盖原T下所有合法低J点；新点要给原U_R，则按B节原D_R另行验收。保留原J cutoff的单侧覆盖及真实J重算。

本分支最多一个tau、一次≤6h的科学外层调用，其余E容量留给必要资格与读回；不因UNKNOWN加第二个长窗口或换tau重试。合格时间lower超过原接受horizon可排该完整level，原T内整数见证给U_R；其他情况如实保留时间区间。没有与R158不同的预期信息来源，就取消本分支。

## F. 有可消费收益后，再冻结完整候选

只有产生有用途的**物理U改善或合格全域L改善**，且构造与验证费用可能合理时，才冻结一个统一候选E+R。资源upper足以支持结构研究，但不能直接代替physical incumbent或全局proof。没有可消费收益就不空跑完整面板；不设置任意百分比胜出门槛，也不要求每个实例都赢。

候选从本臂自己的own-H/当前合法状态构造quantity、owner、RN及completion，自付全部费用。禁止免费加载审查点、历史assignment/路线、离线Y3或旧certificate。离线研究可复用这些对象，正式在线机制必须能从自身状态产生所需信息。

physical upper只有通过原独立验证才进入exact engine；新全域lower遵守既有scope transport、cutoff complement及frontier覆盖合同，优先复用合格proof-only接口。更新incumbent后按原合同处理cutoff、epoch和失效缓存；不要求之后的Native/raw轨迹与E+相同。不得将限制域ObjBound接入全域proof。

正式候选按第0节采用C++新在线核心。若从Python原型迁移，或实现开销可能改变机制取舍，在现有预算内做一次必要的有限等模型桥接：核对原目标及scale、实际系数、变量/约束界与次序、Start、Gurobi版本/参数、停止工作容量和回传语义，区分模型/搜索改变与语言实现改变；模型指纹只作辅助，不替代实际语义读回。不要为桥接重跑历史长窗或整个旧面板。仅有Python原型时，可报告该实现的有限费用与研究结果，不作为最终C++候选的正式性能确认。

冻结源码/构建条件、配置、统一参数与运行顺序，再执行下表。E+与E+R尽量使用同一生产构建的off/on入口，并使用相同版本、相同实现的共同组件；既有Python共同helper可保留并逐臂如实计费，不强称整个执行链已全部C++。E+以同条件fresh臂为对照，不能拿旧表中最好的时间挑配。新候选若需独立PE，记录两者源码与差异，保留同编译条件，不谎称PE相同。

| 角色 | 算法臂 | 每臂生产总窗口 | 用途 |
|---|---|---:|---|
| R-X35-S-T2 | E+ / E+R | 7200s | 主来源的实际净收益 |
| N-B35-S | E+ / E+R | 2400s | 第二来源及规则一致性 |
| K-20-S | E+ / E+R | 1200s | 构造成本与库存/物理差 |
| R-X20-S-T1 | E+ / E+R | 1200s | 快获证场景的额外代价 |

八臂名义生产窗口合计`24000s=6h40m`，沿用R156完整生产口径：own-H、scope、RN/helper均由该臂支付并处于生产窗口内，不能给每个Native子调用再发一个完整窗口。事后必要验证另记`T_verify`，`T_total=T_produce+T_verify`；最外层调度/封装与失败费用另按科学外层账核对。

F阶段容量10h，覆盖生产、必要资格/验证与失败余量。若沿用`cap+900`的supervisor预约，它只是监护/保守预约，既不自动增加算法窗口，也不能当成已发生的实验费用。启动前确认总预算能容纳面板及验证；不足时先压缩未执行支线或按G调拨，不偷减验证或超出36h。

可以按预登记顺序先执行两个研究来源的成对比较；出现明确机制无效或严重回退时允许停止后续面板。保留所有已启动结果，标为partial，不挑正例或在看完后改参数再混入同一次冻结候选。若提出本轮四角色上的完整性能确认结论，应完成四角色对照；候选精确性依赖一般有效性、覆盖与回传证明，不能由四例实验代替。修bug后的必要重跑与旧失败都计费，不能无限重启确认。

输入及物理身份如下；pickup/drop均60s，物理T不是实验窗口，其余权重/归一化以对应manifest为准：

| 角色 | V / M | Q | 物理T | lambda | 输入SHA256 |
|---|---|---|---:|---:|---|
| R-X35-S-T2 | 35 / 3 | 20,25,30 | 6300 | .0754049775127276 | `c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2` |
| N-B35-S | 35 / 3 | 20,25,30 | 7200 | .15 | `80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98` |
| K-20-S | 20 / 2 | 30,30 | 5400 | .15 | `d1a65be4b87dead2ae351068ece3c3ce486a51c93652d778e055f2684606ea42` |
| R-X20-S-T1 | 20 / 2 | 30,30 | 4800 | .12676060979965992 | `2b467b5bb1e650a4c1e792e808dcf9575bcc76752fe378e16c838015344ddac6` |

报告physical U、raw/proof L、绝对/相对gap、T_total/T_cert、构造/求解/验证及机制调用量；没有证书则T_cert为空。无需新增多Seed、P-GRB宽benchmark或常规B桥接。该面板只能支持已知角色上的增量结论；不能据此宣称稳定胜过P-GRB、分布外泛化或达到某期刊录用标准。若候选有价值，另提出冻结机制后的独立确认需求，不在本轮自动扩张执行。

## G. 预算、阶段决策与论文产出

| 阶段容量 | 秒 | 小时 |
|---|---:|---:|
| 复用、数学接口与必要新资格 | 7200 | 2 |
| 联合quantity/owner主研究及早期物理检查 | 36000 | 10 |
| 一条有依据的深入路径 | 28800 | 8 |
| 条件完整候选与必要确认 | 36000 | 10 |
| 最终科学读回与必要核验 | 10800 | 3 |
| 失败与证据驱动的调拨余量 | 10800 | 3 |
| **总科学容量** | **129600** | **36** |

构造、LP/MIP/DP、H/helper、失败、见证验证与必要科学复核按实际外层调用计一次；nested Runtime/Work只分解、不重复相加。编译、纯写作和公开I/O分列实耗，不伪装为科学实验或据此声称36h是整个任务的日历时长上限。新的科学计算即使嵌在“整理/恢复”脚本中也须计入科学账。

Round159自己的meter、launch reservation、剩余容量检查与cost_report统一使用129600s。不得直接继承R156的172800s或旧Round159的259200s设置；只调整本轮配置，不修改历史脚本与封存账本。R158已发生的37.054594h属于旧成本，不再计入本轮36h。监护预约与实际费用分别记账，全方法deadline、正常退出/保存margin等成熟生命周期控制继续复用，不将其误改成禁止的机制切换。

阶段为初始容量，不是强制耗时。可在总量内根据实际证据调拨，并记录改动与理由；不得默认恢复到72h。F无候选时可留空；其余量也不自动变成另一个长UNKNOWN。资格、保存与必要验证不能为榨出更多Optimize而省略。预算临近用尽时优先保存、核验和交付，不启动无法留下可用结果的新重型调用。

本轮至少回答下列并列问题，未解决项明确写UNKNOWN及作用域：

- 是否得到新的合格U_R？与固定owner基线、旧参照相比，价格改善与真实成本各是多少？
- 联合数量/归属新增了什么能力？资源到物理的差距由哪些已验证结构解释，哪些仍是推测？
- 是否得到真实U_P或全域L收益？限制域最优、固定owner失败与全域证明是否严格区分？
- 是否存在值得在线自付的统一机制？若没有，哪条已执行证据支持停止，什么新信息才值得再开？

论文小节围绕“库存下界—整数资源域—物理实现”组织，给出一般域关系、机制/伪代码、接受与精确性接口、实际复杂度/工作容量、至少第二来源的同规则证据和完整成本。对资源upper能力上限保留完整Q的前提；对fixed-A预算保留内限制身份；对DP/TSP与旧数量/交换方法明确归属。理论结论、审查侧证据、本轮实验、尚待验证假设分开写。

既有handling恒等式、原J模型、经典DP和owner交换不是本轮新理论。可发表的潜在增量来自新的联合结构解释或可复用机制及其收益，不能预先承诺一定获得。若结果有限或负面，写准确的边界与反例/失败机制即可；稳定GI-TBC正文与历史证据整理继续推进，不等待支线必胜。

## H. 必要复核、工作区与Draft PR交付

主要计算前，检查新限制域的包含方向、原J映射、原T/系数、start合法性、active/owner变化、保存和回传接口。只对实际新增接口做必要positive/negative/boundary验证，复用已PASS的旧资格，不重建无关测试或审核系统。

最终从保存的输入、实际源码/模型、Y/owner/路线、日志和费用独立读回。若有独立审查agent，记录真实身份与意见；若只是同一agent的独立脚本/读回，不冒称独立人员审稿。发现资格问题先修复或收缩结论，负面和失败保留。相同事实不要求多套重复证明。

新增产出集中在`results/unified_exact_round159/`；新增C++生产实现遵循现有include/src布局，研究原型、编排与校验脚本使用`scripts/round159_*`或现有合适的共享接口。旧producer的OUT、TEMP、预算和计时器不能沿用到R159；特别检查旧`round158_common`的72h容量与输出根，使用隔离adapter，不执行旧producer覆写历史。

可合并组织文件，至少交付：实际完整goal；有限历史排重/增量表；数学与算法说明；输入/source/model/PE身份；资源upper链、物理/level结果及限制scope；科学费用与失败；停止/继续判断；条件完整结果（若进入）；论文小节及主张边界；最终复核、公开恢复与cleanup记录；`RESUME.md`。未执行的分支写清“不进入及理由”，无需造空实验。

按用户授权正常commit/push并创建**英文Draft PR**，建议标题：

`Round159: study joint quantities, ownership and physical realization`

PR说明先写研究缺口、实质新增、实际结果与结论限制，再列必要验证和费用。按A的实际依赖选择main或核实后的R158 stacked base；读回base/head/Open/Draft和载体链接。无需等待前序PR合并，不自动merge、force-push或删除分支；没有新科学收益也可正常交付有解释的负面Draft PR。

全部新增worktree/build/raw/archive/temp/空根restore位于`E:\codes\ExactEBRP-work`。只读复用已有合格解释器、软件和PE/DLL；保护`E:\codes\ExactEBRP`、用户修改、活动树、历史唯一证据，不改全局app/proxy/权限/model/credential设置。计时实验、编译与大规模I/O串行，避免计时污染。旧RUNNING/FAILED记录不是当前进程证明，不自动恢复/重跑旧任务。

仅打包新增必要证据，旧输入/源码/大载体以fixed commit、member及SHA引用。完成**一次有限的新增公开恢复核验**，无需全历史空根重放。PR交付后，不论Draft/负面/blocked，都按WORKSPACE_POLICY和R122约定做有限metadata screening：只清理本轮已完成、可重建且被carrier/manifest/实际恢复覆盖的重复临时对象；保留唯一科学证据、失败、必要运行文件及仍在用的树。旧轮删除不在本轮授权内。记录真实动作、保留项、字节估计和观察到的空间变化，零删除允许。

## I. 固定来源与复用接口

以下是定位资料的入口，不是要求逐个运行的producer清单。以最新已核实源码接口为准；先用本地合格副本，缺失时按固定commit最小恢复。

- 当前稳定主线：`docs/paper_s2_release.md`、`config/paper_s2.json`、研究索引、R135模型/算法附录及R133/R134修复说明。
- R158：[PR #220](https://github.com/yifanXovo/TailoredExact/pull/220)，fixed science `163b1b3d0dbcc7be3a84d94108ef4a26ae9baba3`；`results/unified_exact_round158/`的final_report、mathematical_analysis、intervals、decisions、coefficient_binding_correction、source_manifest、reuse_index、cost_report、reports、manuscript与artifacts。delivery metadata按实际head。
- R157：[PR #219](https://github.com/yifanXovo/TailoredExact/pull/219)，fixed science `9889473a9b64c749ea8841bac1d38fec8be21d96`；`results/unified_exact_round157/inventory_sources.json`、`inventory_families.json`、数学说明与final_report。positive_control内含原physical witness，优先使用，不为C节重建恢复整个大包。
- R156：[PR #218](https://github.com/yifanXovo/TailoredExact/pull/218)，fixed science `751de842a0264a146701de6669b1f3dd6dc764b1`；E+完整臂、费用与冻结入口。RX35原witness位于`complete_arm_009.zip`内`results/unified_exact_round156/campaign_confirmation/009/raw/R156_009_R-X35-S-T2_S0_Eplus/external/native_0_witness.json`，SHA `05fa35a9a3d515d0764f7d88943bd31b4d5a493c134bea76eb2a63f203bd6a05`；NB35见R158 reuse_index。
- C节input可定位`results/unified_exact_round137/inputs/R-X35-S.txt`，SHA见F。R158修正coefficient package SHA为`931e6d6b59d97d6bc17976d59a889f5f68e2ed25e26b71a20a5b85f4a6537166`，对应实际duration来源模型SHA `c7ce593e01494b8d5f531959fbd3bf230748bcc9abfe7a236dcffe81cec6e493`；按coefficient_binding_correction/reuse_index定位已有包。C节整数、归属来源、递推和精确travel值已足够独立重建，不要求外部审查附件。
- 历史排重的重点原文：`results/unified_exact_round76/`、`round83/`、`round96/`、`round103/`、`round105/`至`round107/`的final_report/数学说明；实际目录统一为`unified_exact_roundN`。另读当前索引所指R138–158结论；旧hull、master、数值包络不重新实现。

| 用途 | 优先复用的接口/资料 | 注意事项 |
|---|---|---|
| 现有物理闭包 | `Round76PhysicalClosure.hpp`、`Round83BlockExchange.hpp`、R96既有实现 | 不把旧改善归到新增机制；R96多站射线不等同完整quantity模型 |
| 原J与RN/resource映射 | `round153_pricing.py::Oracle`；`round157_floor.py::objective/original_lower/attach/lifted`；`round157_inventory.py::value` | 保留scale、中心化、单侧覆盖；restricted lower不全域运输 |
| 实际系数与resource读回 | `round158_level.py::coefficient_package/envelope/budgets/extract`；`round158_resource.py::arithmetic`；`round158_review.py::full_lift` | `level.build`继承tau且objective=0，不能原样拿来作D；finite-member专用读回适配实际新点 |
| 物理completion | `round157_fleet.py::build/decode/verify/lift`、`round158_physical.py`，以及已合格R61/R105 oracle接口 | 复用建模/验证，不启动旧master/IIS循环；fixed与free owner分别记录 |
| 完整E+与费用 | `round156_online.py`、`round156_rn.py`、`round156_campaign.py`及冻结manifest | 生产总窗口自付；验证另计；不免费使用离线证据 |

最终始终区分四类成果：**有效整数资源见证、真实物理路线、全域证明、完整算法净收益**。按保存证据决定结论；无论成功或负面，都不把限制域、已知角色或特定机器上的现象扩大成未经证明的普遍主张。
