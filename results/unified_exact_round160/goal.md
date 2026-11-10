/goal

# Round160：在保留可行车队的局部域中，联合优化数量、车辆归属与访问次序

## 0. 本轮目标与执行原则

继承已完成的R159。本轮只研究一个主机制：**从当前真实可行车队出发，固定块外库存与部分路线结构，在一个小型物理限制域中同时优化quantity、owner和order，直接得到可消费的原目标改善。** 完整travel、prefix load、handling和回仓卸载从建模时就参与选择；不再先挑低价resource库存，再以冷启动全车队查询尝试补救。

以当前物理见证X和释放块B定义邻域`N_B(X)`，建立并实际利用

\[
X\in N_B(X)\subseteq D_P(T).
\]

前者提供合法起点，后者使合格改善直接成为physical upper。研究重点是：能否用固定连续段压缩、原Gini目标的局部收缩和统一选块规则，以合理成本跨越现有顺序闭包的局部限制；是否值得作为GI-TBC的自付primal组件。这里的“跨越”首先指声明的子域能力和实际改善，不预先断言任何旧动作序列均无法到达新解。

总科学实验容量为**36h=129600s**，不是必须消耗的时长。主要容量投入这个物理构造；不设置全车队min-T、全level长查询或另一套cut框架作为自动后备。允许在同一机制内作一次有证据的主要修订，不要求研究前先证明必胜，也不以第一批有限UNKNOWN关闭整个方向。新物理见证、机制解释、明确局部域的负面结论均可作为诚实成果。

论文目标是一般数学定义、可复用机制、正确精确性接口与完整成本证据。选块、端口和工作容量可以依赖当前库存、路线、合法支持、几何、载荷和目标边际量；**不按实例名称、预设规模档、历史输赢、机器型号、CPU速度或内存大小分派策略，不采用“运行若干秒后换机制”规则。** 正常总deadline、退出保存margin和离线实验预算继续使用，不把它们混同在线算法的分派策略。

稳定论文主线GI-TBC/B（S2/ms2）及其正式入口保留，E+为增强参考；裸CLI的ENS-C兼容默认不是GI-TBC。新增机制使用独立、默认关闭的研究入口。它是有界局部primal优化器，完整算法的全域覆盖与证明仍由原exact engine负责。局部ObjBound、局部不可行或没有改善不进入全域proof ledger。

默认Gurobi Seed=0、Threads=1；正式完整臂own-H seed=20260626。原pair-only、AM=.08、depth8、minimum width=1e-4及已合格数值政策沿用；E+保留RN16384与R154 proof-only consumer。

**新增反复执行的算法核心采用C++，正式性能比较使用合格C++实现。** 包括本轮模型构建、选块/端口、求解callback、物理解码与在线验证回传；遵循项目现有C++/Gurobi接口、编译和数值政策，不顺便更换优化级别或fast-math。Python可用于编排、离线分析和独立核验；两臂共同的历史E+ helper可保持同版本、逐臂付费，不要求重写全部历史框架。如果确有接口障碍，可先做有限原型并说明障碍，但不能将Python原型时间当作最终C++性能结论，也不能以语言迁移代替新机制。已有数学结论不因语言不同而失效。

## A. 工作起点、最新事实与历史排重

工作入口：`E:\codes\ExactEBRP-work\worktrees\paper-current`。检查适用AGENTS.md、WORKSPACE_POLICY.md、远端状态、用户修改和实际活动进程，为R160建立隔离worktree。原项目`E:\codes\ExactEBRP`和已有论文/研究树受保护；新增worktree/build/raw/archive/temp/空根restore均位于`E:\codes\ExactEBRP-work`。

2026-11-10审查时的身份如下；执行时刷新，不把这些历史身份冒充最新远端：

- 仓库`yifanXovo/TailoredExact`；R159为Open Draft [PR #221](https://github.com/yifanXovo/TailoredExact/pull/221)，未合并。
- R159 branch：`codex/round159-joint-quantity-ownership`；delivery head：`51473276867e802ce729aae3d4a2563ea23a8fe8`；fixed science：`a64e27f5e5668c036069c354529901803bec5a84`。
- R159 base为`codex/round158-resource-value-levels`，head `d58cbcca6d2c656a2af09d701bcd9ca0c7a07e85`；main仍为`b2b940c1e517a72e226ec60fc49ff19651737632`。
- 继承production source：`092bad58d677cd8bef934d91e11d8abff93cba83`；历史production PE SHA256：`e5efe978f33e5c812fc9a0484caaae80696e4197ae27e289b4894d586af9d7e6`。
- R159独立research PE SHA256：`9052e2c3d0403d59ae5c4d5bc3ef70d36e298ea61b46381175a5f1e193da256a`；这是研究工具，不是新生产候选。
- Gurobi 13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

若main已吸收依赖，从main开始；否则从核实后的R159 head建立stacked分支，以R159分支为Draft PR base，无需等待#221合并。若已有R160实际进展，接续该进展，避免重开重复轮次。source、实际启动的PE/DLL、science commit和delivery metadata分别记录。

先读R159的final_report、mathematical_analysis、trajectory、physical、owner_ablation、cost、decision与实际C++接口，再按下表最小回看相关历史，形成一张“已做—本轮变化—待回答”表。已有合格资料只读复用，不恢复所有历史载体、不重跑旧producer。

| 历史 | 已经做过 | R160的实质区别与复用边界 |
|---|---|---|
| R61 | 全车队min-required-time模型；固定或部分释放quantity，owner/order/load自由 | 不是首次联合物理建模；本轮以原J优化包含当前车队的小型物理域 |
| R76 / R83 | 未访站插入、single/pair quantity闭包、翻向、等净量连续块跨车交换及随后数量改进 | 复用其见证与验证；不将旧动作重命名为新机制 |
| R96 | 固定owner完整quantity，删零/翻向/压缩travel；固定owner自由次序诊断；同车块swap/reverse后再quantity闭包，正式候选回退 | 本轮在同一个子问题内同时开放quantity、owner和局部order；“先重排再调量”本身已经做过 |
| R103、R105–107 | resource hull、assignment master、physical oracle、IIS/core、MST/三站冲突、callback/frontier接入，完整结果不理想 | 不重建master→大量不可实现库存→oracle学习的大分解框架 |
| R138–156 | 多类LP增强、hull/Q反馈、完整回退；E+ proof-only定位；同标量库存floor余量很小 | 复用E+，不做旧cut/Seed/AM网格，不追同floor小数位 |
| R157–158 | 原J资源模型、联合库存/归属搜索、有限族与全level研究、自由车队completion | 不以又一个全level UNKNOWN或旧族排除作为主任务 |
| R159 | 8站quantity/owner资源块，12次调用；完整物理检查在构造之后，没有反馈进入下一块 | 本轮从真实physical parent出发，子域本身包含完整物理约束；固定段压缩与目标收缩用于控制费用 |

局部邻域、固定路径聚合、路线段载荷摘要和一般matheuristic已有文献基础，不声称首创这些概念。潜在论文增量来自本问题原非分离Gini目标、可变有符号装卸、异质车辆归属和前缀载荷在小型物理域内的组合结构，以及它对完整精确算法的真实作用。历史排重不能替代文献归属，也不要求本轮展开一项独立综述工程。

## B. R159已经回答的问题与本轮真正的未知

R159在同一原scope的关键数值为：

| 角色 | 原physical参照U | R159固定owner资源U | R159联合资源U | 继承L_I |
|---|---:|---:|---:|---:|
| RX35 | .2996694007364017 | .29453694232737326 | .29118539321285497 | .2360521029074557 |
| NB35 | .450291503262878 | .425855686698408 | .4235630179611202 | .3959564087240911 |

RX的固定owner点是继承审查C，不是R159新生产的physical解；其本轮联合增量为.003351549114518293。NB相对固定owner基线的联合增量为.002292668737287784。两者均未得到新的physical U、全域L或完整算法对照数据。

24个联合resource子问题全部Native OPTIMAL，总节点为RX31、NB246；两例联合构造外层成本合计10.64375s。512节点上限没有限制这些已解块，增加该上限不能补上缺失的物理约束。12个按gain排名选出的anchor也不构成35站完整覆盖；单站gain=0不表示该站在补偿型联合动作中无用。

真实物理障碍已有清楚证据。例如RX联合终点car0无载荷最短tour为5335.2187581s，P=13，完整时长至少6895.2187581s，超过T=6300；完整活跃集只容8次pickup。car2的固定活跃集仍P=25，而完整tour预算只容24。NB car1的无载荷tour加handling已超T，prefix约束还增加482.8031804s。因此只补prefix或只延长同一固定组合重排也没有针对主要缺口。

审查侧已补读全部13个保存的strict events：按实际active set匹配已有精确无载荷DP，再加每个事件自己的handling，均可排除其**记录中的固定Y/owner组合**。NB baseline七点由car2、RX joint两点由car2、NB joint四点由car1给出障碍；即便使用更宽guarded horizon，组内最小超时仍分别为87.0070597062s、112.0251518374s、332.0442935975s。该补核没有新Optimize/DP；不能扩大为同Y所有owner均不可行。必要时从R159 raw做一次轻量来源读回，不为这些相同组合重开completion。

唯一RX终点free-owner查询为8192nodes、零解、NODE_LIMIT/UNKNOWN，外层1329.5759356s；它没有排除整个Y。R159科学费用1438.3466243s，约92.44%用于该查询。停止该冻结协议、不空跑F是合理的；“未找到”不能写成“继续研究物理联合方向不可能有用”。

**本轮新问题：若构造始终保留合法车队，并直接用完整物理约束选择数量、归属和顺序，能否获得更温和但真实可实现的J改善？** 不要求实现R159两个最低resource端点，不把低U_R当作必须追逐的目标。资源域的旧区间和排除可作背景，不要求本轮再提高U_R或新增全域L。

## C. 一个明确、可实现的物理联合邻域

### C1. 父见证、释放块与固定外部

令X为经原验证器接受的完整车队，库存为\(\bar Y\)。B为释放站集，O为其补集。O包含所有块外站，包括未访问站；固定其库存、非零operation归属和下述连续段结构。

在每条**原父路线**上，用属于B的现有访问将outside访问分成最大连续runs；每个非空run是一个固定段。删除B访问后，仍保留它留下的段间插入口，**不要把孔两侧的outside段重新合成不可拆大段**。段保持原车、段内次序及各段间原相对次序。

B内开放原合法库存支持、所有合格车辆归属和段间访问次序，允许未访站激活、归零、翻向与跨车调量。不强制旧owner内净量守恒。非零operation必须且只能由一辆合格车服务；\(Y_i=b_i\)时不访问、无owner，不能保留零服务节点作中转。允许原空车承接B，也允许删除B后某车变空。

自由站可以插在段边界，包括depot两端，并可在同一gap中任意排序。为了让没有旧B孔的接收车也有内部端口，允许预先按统一规则再切开至多g个真实outside内部arc；每个不同切口最多新增一个段。默认\(g\le b=|B|\)，不是每车各给b个后仍宣称总g=b。

这定义的是**固定不可拆段的物理内限制域**，不是所有保持outside相对次序的路线。没有切开的段内部不允许插入。新增切口不强制插入，原arc仍可直接连接，所以不会丢失父见证。

工作scope、库存支持和目标上限从当前parent及其合格原scope派生；确认它覆盖parent。不要直接载入R159更低资源目标下的导出模型或strict cutoff，把父路线预先删掉。可以在含parent的非严格改善scope中求解，再以真实J判断严格改善。

### C2. 固定段的精确物理接口

固定段A的每站净操作为\(\delta_i=b_i-\bar Y_i\)。保存首尾端点、内部travel、pickup \(P_A\)、drop \(D_A\)，以及包含空前缀的

\[
\Delta_A=\sum_{i\in A}\delta_i,\quad
m_A=\min_{p\preceq A}\sum_{i\in p}\delta_i,\quad
M_A=\max_{p\preceq A}\sum_{i\in p}\delta_i.
\]

容量Q的车以load L进入该段，当且仅当

\[
-m_A\le L\le Q-M_A
\]

时全部内部prefix合法；出口为\(L+\Delta_A\)。段内handling为\(t_pP_A+t_dD_A\)，不能提前在每段末端卸载。整车空载出发，回仓load \(R=P-D\in[0,Q]\)，末端再收取一次\(t_dR\)，故整车handling才等于\((t_p+t_d)P\)。累计P可以大于Q；读实际\(t_p,t_d\)，不继承R159的120常数作为一般公式。

段连接有

\[
\Delta_{AB}=\Delta_A+\Delta_B,\quad
m_{AB}=\min(m_A,\Delta_A+m_B),\quad
M_{AB}=\max(M_A,\Delta_A+M_B).
\]

内部travel与连接首尾的真实arc分开计。块内净量变化必须传播到后续固定段的入口load，不能钉住旧边界load却声称已开放跨车净量改变。

优先复用现有物理建模接口，建立一个C++小MIP：强制mandatory段恰好出现于原车、段间先后正确、自由非零站唯一服务、depot到depot连通、完整load守恒与prefix、原T。保留合格的连通性/消子环约束；仅有degree和load不足以排除零净量子环。空车使用合法depot bypass；最终展开成原站点路线交给原验证器。

证明两个方向：该宏模型的合法整数路线展开后属于原物理域；声明邻域中的原路线可收缩为宏模型解。对应是路线/operation层面的，辅助连续变量不必唯一。再说明原X如何重插B访问而恢复，建立父见证嵌入。

若原本活跃的B访问数为a，固定段数至多a+M；额外g个切口后，非depot原语数至多\(2b+M+g\)。这控制局部组合模型规模，不表示预处理、输入读取、验证或总运行时间与n无关，也不声称MIP多项式。无需为此另外开发全车队subset DP或variable-quantity DP。

### C3. 保留完整原Gini的局部收缩

沿用实际绑定的\(c_i=1/D_i\)二进制系数、原H权重与原n。记\(r_i=c_iY_i\)，固定outside时预计算

\[
S_O=\sum_{j\in O}c_j\bar Y_j,\quad
A_O=\sum_{j<k,\ j,k\in O}|c_j\bar Y_j-c_k\bar Y_k|,\quad
H_O=\sum_{j\in O}h_j(\bar Y_j),
\]
\[
\psi_i(y)=\sum_{j\in O}|c_i y-c_j\bar Y_j|,
\qquad h_i(y)=\alpha_i|c_i y-1|
\]

其中\(\alpha_i\)为原接口的**已加权**系数。当前RN/R159 scope的station['omega']已含lambda，应直接使用；只有来源明确存储未加权\(\omega_i\)时才令\(\alpha_i=\lambda\omega_i\)，不能重复乘lambda。则S>0时逐点恒有

\[
J(Y)=
\frac{A_O+\sum_{i\in B}\psi_i(Y_i)
+\sum_{i<j,\ i,j\in B}|c_iY_i-c_jY_j|}
{n\left(S_O+\sum_{i\in B}c_iY_i\right)}
+H_O+\sum_{i\in B}h_i(Y_i).
\]

不能只对B计算Gini，不能漏掉未访问outside站，不能把penalty除以S。交叉pair成为一元表，只有块内pair仍是变量交互。

可直接沿用RN归一化来构造紧凑模型。设one-hot \(x_{iy}\)，\(t=1/S\)，\(w_{iy}=t x_{iy}\)，\(\rho_i=\sum_y c_i y w_{iy}\)。用合格t界、\(\sum_yw_{iy}=t\)及one-hot相应界实现整数点上的乘积关系，并设置

\[
S_Ot+\sum_{i\in B}\rho_i=1,\quad
a_{ij}\ge\pm(\rho_i-\rho_j),
\]
\[
nq\ge A_Ot+\sum_{i\in B,y}\psi_i(y)w_{iy}
+\sum_{i<j,\ i,j\in B}a_{ij}.
\]

最小化\(q+H_O+\sum h_i(y)x_{iy}\)，同时保留原总库存、合法支持、gamma和必要scope约束的正确收缩。由实际库存scope或固定outside证明S>0，再取合格t界；gamma_L=0本身不能排除S=0。若工作域允许S=0，沿用库存RN的独立zero-stock分支（如`Oracle.price`），单独评价其原J与可行性，不作除零归一化。原exact engine的R133/R134修复另行继续保留。

这给出原目标的上图表达；任意整数incumbent的辅助上图变量可能未取最小值，接受仍须重算原J。继承原系数包络、scale/中心化和数值接受政策；Native OPTIMAL、原J局部最优和有界搜索分别报告。局部lower如用于机制证明，须做相应作用域内的合格transport，不将本地bound升级为全域BRP lower。

先完成这一紧凑实现或代数等价的既有RN固定补集实现；可短暂用后者对照新接口。只有实际模型大小/构造费用需要时继续收缩，不要求维护两套长期框架。变量pair可缩至O(b²)，但one-hot数量、车队和支持大小须照实计入复杂度。

## D. 首轮实现、统一搜索规则与真正的研究执行

### D1. 少量新接口验证后，尽早做真实物理试验

只验证本轮新增内容：parent能lift到局部模型；宏段展开与完整prefix/travel/handling一致；收缩J与原J逐点一致；activation/zero/跨车净量和empty车语义正确。用少量小例枚举或一个同域未压缩对照，结合两个真实parent读回即可；复用已PASS的系数、验证器与旧资格，不另造完整审核体系。

当前duration采用已修正的`sqrt(dx*dx+dy*dy)/1.5`，不能混回旧`hypot`reader。模型数值容差与原物理接受合同分开说明；任何候选在进入后续搜索/生产incumbent前，必须通过原T、原系数和完整路线验证。若出现宏模型接受但原验证失败，修复这个接口并保留失败，不能靠扩大T或事后免费筛选制造收益。

**主要离线parent要与拟正式调用点一致。** 按F的默认位置，使用RX35、NB35当前冻结own-H及该入口既有处理后、即将交给scope/RN的完整物理车队。可以复用身份一致、保存完整的历史该时点输出做离线开发；缺失时各运行一次必要的现有C++ own-H生产并计费，无需先跑完整E+。记录来源、输入/seed/处理链和父J，不能把晚期Native解冒称own-H输出；正式F仍由每臂自行生成。

B表的两个晚期physical参照可作为更强的结构挑战：按R157 positive_control、R158 reuse_index和R159 inputs定位完整路线，对最有信息量的块作补充研究即可，不强制再做双parent全面板。既要报告相对当前parent的J改善，也要说明是否低于B表历史末态。**早期primal组件不必先打败历史长窗末态，才有资格检验其完整自付价值。** 不能只凭Y/owner宣称physical，也不能将相对较弱own-H的改善包装成新的历史best upper。

### D2. 冻结一个有覆盖意识的选块与端口规则

默认从\(b=\min(8,\#\text{可释放站})\)、总额外端口\(g\le b\)、每块NodeLimit=512开始，Seed0/Threads1。这是研究起点，不因为R159资源块已解就假定物理块也容易。选择一个明确的原问题状态驱动规则，写出伪代码、tie-break和工作容量后执行两来源；不要同时测试多个配方。

选块必须满足以下实质条件：

- anchor队列覆盖全部具有合法变化可能的站，包括未访问站和当前单站gain为零的站；在一轮开始时固定队列，改善后不反复重排剩余队列而使部分anchor永远落选。稳定站号只作tie-break或遍历次序，不据站号指定特殊机制。
- 其余b−1席可以结合原J边际、几何与当前路线/供需互补；至少保留不依赖正单站gain的邻近或补偿候选。不要沿用“gain=0使所有几何项同时归零”的退化。给出一个确定规则，避免权重网格。
- 额外端口默认按自由站对outside arc的实际插入增量排序；仅使用存在合法非零服务可能的station/vehicle组合。可按车辆轮转取其最优剩余切口、总数封顶g，防全部端口无意集中一车。旧孔与depot两端一直保留。端口在求解前固定，不按求解时间或实例名临时增加。
- 保存每块anchor、释放集、真实端口和来源parent；报告一轮anchor覆盖、unique blocks/ports及重复比例。完整anchor一轮不等于所有b站组合或所有物理邻域闭包。

离线核心任务至少在两来源的上述调用点parent上各完成一轮anchor遍历，除非实际科学预算、已发现实现错误或明确费用瓶颈阻止；发生后如实报告partial，不以任意12步宣称探索完毕。若有持续物理改善，可再做一轮；冻结一个统一pass上限或无改善停止规则。正式在线调用次数与容量在有限开发结束后统一冻结，不把离线全部探索免费搬入生产。

### D3. 同一次物理优化同时开放三个自由度

块内不先固定Y求路线再调量，也不先重排后调用旧闭包作为全部新机制。一次子问题内联动quantity、eligible owner与允许的order；outside段的完整时间和入口load必须参与选解。

用parent提供完整可行Start。对MIPSOL及最终解解码、展开、重算原J并物理验证，保存所有合格严格改善的完整Y/owner/routes与费用时间点；可按原政策跳过非改善候选，不只保存最后一个最低价点。新parent更新后重新生成对应段与outside目标表。没有改善时保留旧parent；节点/总deadline耗尽如实报告有限结果，不排除全局解。

严格改善阈值继承原接受政策（现有研究1e-10需与正式入口核对），不设置任意百分比胜出门槛。每个接受事件报告J变化、travel/handling、逐车载荷与余量、quantity/owner/active/order变化。这样能解释是旅行重组解锁装卸量、跨车净量互补、归属消除载荷障碍，还是其他具体机制，而不是只列一个新upper。

物理模型可能比资源块难。首次无改善后区分：已解的限制域确实无改善、节点未完成、块/端口没有覆盖相关联动、还是实现/目标问题。选择最有证据的一项处理；不要无差别增加所有上限，也不要用UNKNOWN要求停止整个新机制。

## E. 同一机制内的一次定向深入与有限归因

在D之后，用已有轨迹决定是否进行**一次主要、统一的修订**，例如纠正已观察到的补偿站选择、增加有依据的内部端口覆盖，或在多数物理块尚未有效搜索时调整统一节点容量。先写明哪条证据对应哪项修改，两来源同规则执行；记录前后版本，不能将改前失败混入改后冻结候选。修bug不计作研究配方，但失败与重跑费用均保留。

不要安排b=8/10/12、512/4096/16384、多个权重和多个调用时刻的笛卡尔网格。若现有块均已解而无改善，单纯增加这些块节点没有意义；优先检查邻域覆盖和所允许的物理结构。若真正瓶颈是紧凑模型/root开销，可先修正该实现，不立即转成新全车队框架。

若有物理改善，选择一两个最有信息量的事件作小型匹配对照：

1. 对确需归因重归属的事件，在相同parent、B、outside段/端口、quantity/order自由度、原J、Start与工作容量下，固定原已服务站的owner；原未访问站的activation与eligible owner在两域中保持同样开放。这是**借鉴R96 fixed-owner范式的本轮匹配控制**，不是重现全部R96。若选择沿用未访站关闭的旧控制，则明确它同时限制了activation与owner，不能作纯重归属归因。
2. 只有匹配控制仅限制旧served owner，且其合格restricted lower高于联合physical U，才证明该声明域中重归属对达到该价格必要；若控制同时关闭未访站，只能归因于这组联合限制。其余情况报告观察差异或UNKNOWN，不为获得这项证明强制长跑。不涉及旧站重归属的改善不必硬做这个对照。
3. 若主要主张是压缩节省费用，可在一个有代表性的相同物理限制域上做一次未压缩对照或语义等价检查；不要求所有实例双实现benchmark。

已有R76/R83/R96改善不归到R160。新解中多个变量变化也不自动证明任何旧闭包序列不可达。论文可以报告一次联合优化避免某个中间非改善/不可行状态，但这需要具体轨迹或清楚的局部对照，不能仅从最终新解猜测。

若两来源的真实物理研究与有依据修订均未产生可用改善，交付范围明确的负面/未知和最有解释力的阻碍；不再以R159端点的另一轮free-fleet UNKNOWN填满预算。只有出现新的信息、不同可行起点或清楚的模型理由，才建议后续另轮继续。

## F. 有可消费物理收益后，统一接入完整算法

当D/E对拟调用点parent产生经原验证的physical U改善，且实测构造/验证费用有合理利用可能时，冻结一个E+R候选。这里不要求先打败B表历史末态；早期改善是否有价值由自付完整对照回答。也不要求两个研究来源均改善或预先证明完整性能必胜；若完全没有可消费收益，则不空跑F。

优先只接一个调用位置：本臂own-H产出合法车队之后，在既有scope/RN消费该incumbent之前调用统一局部优化，随后交回原exact engine。若实际接口要求稍后接入，说明并统一冻结位置；本轮不研究多时点portfolio。输入、scope、端口、RN和Start均由本臂状态产生，自付构造、求解和在线验证；不得免费载入历史路线、审查点、离线目标表或旧certificate。

更新physical U后，按已有合同更新cutoff、scope/epoch和受影响缓存；不要求后续搜索轨迹与E+相同。局部MIP lower绝不写入全域proof。若需要迁移少量离线原型，做一次有限语义桥接即可，不重跑旧长窗；正式新在线核心仍为C++。

使用相同构建条件及公共依赖，尽量以同一生产构建的off/on入口形成fresh E+和E+R。若需不同PE，记录实际源码差异和编译条件。冻结候选源码、配置、统一容量与运行顺序后执行：

| 角色 | 算法臂 | 每臂生产总窗口 | 目的 |
|---|---|---:|---|
| R-X35-S-T2 | E+ / E+R | 7200s | 主来源的自付净收益 |
| N-B35-S | E+ / E+R | 2400s | 第二来源及规则一致性 |
| K-20-S | E+ / E+R | 1200s | 构造代价与库存/物理差 |
| R-X20-S-T1 | E+ / E+R | 1200s | 快获证场景的额外成本 |

八臂名义窗口合计24000s=6h40m；F容量10h。若沿用cap+900监护预约，八臂保守预约31200s=8h40m，它不是算法额外窗口，也不是已经发生的费用。开始面板前保留必要验证余量。

**每臂只有一个生产总deadline**，包含own-H、scope、RN/helper、新C++模型与在线验证、所有Native子调用和回传；不能再给组件另发完整窗口或沿用R159 standalone默认3600s。生产后必要验证单列\(T_{\rm verify}\)，\(T_{\rm total}=T_{\rm produce}+T_{\rm verify}\)，并与实际外层科学账闭合。

建立R160自己的八臂matrix/admit/loop。旧R156 campaign硬编码九臂、len==9与33600s，不能直接执行旧freeze/admit。K20从R137的已核S2/Seed0 manifest恢复正式输入/CLI身份，再套当前E+协议；R156对K20的helper检查不是已有正式E+臂。只验证新增launch适配，不重跑旧panel。

输入身份如下；当前四角色pickup/drop均60s，代码仍读一般值。物理T与实验窗口不同：

| 角色 | V / M | Q | 物理T | lambda | 输入SHA256 |
|---|---|---|---:|---:|---|
| R-X35-S-T2 | 35 / 3 | 20,25,30 | 6300 | .0754049775127276 | `c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2` |
| N-B35-S | 35 / 3 | 20,25,30 | 7200 | .15 | `80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98` |
| K-20-S | 20 / 2 | 30,30 | 5400 | .15 | `d1a65be4b87dead2ae351068ece3c3ce486a51c93652d778e055f2684606ea42` |
| R-X20-S-T1 | 20 / 2 | 30,30 | 4800 | .12676060979965992 | `2b467b5bb1e650a4c1e792e808dcf9575bcc76752fe378e16c838015344ddac6` |

可先做两研究来源的成对比较；若出现明确无效或严重回退，可停止其余pairs并报告partial。保留所有已启动结果，同一冻结候选不看完后调参再混报。声称四角色完整确认时必须完成四组。新机制若有价值，另建议冻结后的独立确认；本轮不自动扩展多Seed、P-GRB宽benchmark或常规B桥接。

报告physical U、raw/proof L、绝对/相对gap、T_total/T_cert、构造/求解/验证成本和调用次数；无证书时T_cert为空。四角色只支持对应范围的增量判断，不能据此宣称稳定胜过P-GRB、分布外泛化或期刊级成果已经成立。若无新完整GI-TBC/P-GRB配对数据，不改历史比较CSV；研究子问题不追加成完整算法样本。

## G. 实验容量、停止判断与论文组织

| 阶段容量 | 秒 | 小时 |
|---|---:|---:|
| 复用、数学接口与必要新资格 | 7200 | 2 |
| 联合物理邻域的核心构造与两来源试验 | 43200 | 12 |
| 同机制定向修订与有限归因 | 21600 | 6 |
| 条件完整候选与必要确认 | 36000 | 10 |
| 最终科学读回与必要核验 | 10800 | 3 |
| 失败与证据驱动调拨余量 | 10800 | 3 |
| **总科学容量** | **129600** | **36** |

这是初始分配，可按已见证据在总量内调拨并留简短理由；不要求花满，不因F跳过而自动发起另一长查询。核心18h服务同一个物理机制，而不是三个竞争方向。

R160自己的OUT/TEMP、meter、launch reservation与cost_report统一为129600s。复用旧helper经隔离adapter重定向本轮路径，防旧configure带回R156的172800s或旧轮OUT；不修改历史账和封存producer。R159及更早科学费用不重复计入。

构造、LP/MIP/DP、H/helper、在线与事后见证验证、失败和必要科学复核按实际外层调用计一次；nested Runtime/Work只分解、不再相加。编译、纯写作和公开I/O另记实耗；嵌在整理/恢复中的新科学计算仍须进科学账。计时实验、编译和大规模I/O串行，避免污染比较。预算临近用尽时保存和交付，不启动无法留下可用结果的重型调用。

最终至少回答：

- 声明的物理域具体开放了什么、固定了什么？父见证嵌入、段压缩和原J映射是否成立？
- 是否得到新的真实physical U？每次改善用了哪些quantity/owner/order联动，花费多少？
- 完整anchor遍历实际覆盖怎样？无改善属于已解局部域、有限工作未完成，还是结构选择问题？
- 相对R76/R83/R96/R159，新增能力有何直接证据，哪些仍是假设？
- 是否有值得在线自付的统一机制？若进入F，完整净收益怎样；若未进入，具体原因是什么？

论文部分更新一份项目现有研究稿或新增一个适量小节，围绕“物理可行邻域—精确压缩—原目标局部化—联合机制证据—完整自付结果”组织。包括一般命题、伪代码、实际复杂度参数、数值/精确性接口和实验限制。引用已有聚合/局部搜索文献，不能把标准摘要恒等式单独当作OR级创新；同样不因它们是标准工具而放弃研究本问题的组合结构。

不默认要求另做独立四页论文和多份PDF。若本轮实质修改TeX稿，按项目通常流程编译并检查实际输出即可；无新论文结论时写准确的有限结果和后续问题。核心研究不以额外文档数量作为完成度。

## H. 一次必要最终复核与Draft PR交付

实施阶段完成新接口的小量验证后推进研究，不为每个调用增设审批。最终从保存的输入、实际源码/模型、完整路线、原始日志和费用做一次独立读回，重点检查能改变结论的事项：物理与原J、限制域作用范围、own-state来源、生产总deadline、失败/费用完整性。已有合格事实不要求多套重复证明。

如有独立审查agent，可分数学/实现与费用两部分复核并记录真实身份；若只是同一agent的独立脚本，不冒称独立人员。复核发现实质问题先修复或收缩结论；无需为非关键格式问题重跑科学实验。

产出集中在`results/unified_exact_round160/`；C++遵循现有include/src布局，研究编排/验证使用`scripts/round160_*`或适当共享接口。文件可合并，至少保留：实际完整goal；有限历史排重与增量说明；数学/算法/工作容量；输入/source/build/runtime身份；新接口资格；完整改善点、轨迹、原始模型和日志；失败与关闭的外层费用账；decision/RESUME；条件F结果；适量论文内容；最终复核、publication、恢复与cleanup记录。没执行的阶段写明理由即可，不制造空实验。

正常commit/push，创建**英文Open Draft PR**，建议标题：

`Round160: optimize quantities and ownership in physically feasible route neighborhoods`

PR先写具体研究缺口、本轮机制、真实结果与结论范围，再写必要验证和成本。按A的实时依赖选择main或R159 stacked base；读回base/head/Open/Draft与载体链接。无需等前序PR合并；不自动merge、force-push或删除分支。有限负面也按正常流程交付。

仅打包本轮新增必要证据，旧输入/源码/载体以fixed commit、member和SHA引用。做**一次有限的本轮新增公开恢复核验**，不全历史空根重放、不重跑旧求解器。source科学快照、实测PE与后续delivery commit区分记录，避免为自引用head不断提交。

交付后按WORKSPACE_POLICY和R122约定做有界metadata screening与安全清理，不论Draft、负面或blocked。只删本轮已完成、可重建且被carrier/manifest/实际恢复覆盖的重复临时对象；保留唯一科学证据、失败、必要运行时、用户修改和仍在使用的树，旧轮删除不在本轮授权内。记录实际动作、保留项、字节估计与观察到的空间变化，零删除允许。不得改全局app/proxy/权限/model/credential设置。

## I. 固定来源与优先复用接口

这些是定位入口，不是producer执行清单。先用本地合格副本，缺失时按固定commit最小恢复。

- R159：[PR #221](https://github.com/yifanXovo/TailoredExact/pull/221)，fixed science `a64e27f5e5668c036069c354529901803bec5a84`；`results/unified_exact_round159/`的final_report、mathematical_analysis、physical_summary、owner_ablation、trajectory_analysis、cost_report、decision、source/build manifests与goal。`src/Round159JointResource.cpp`、`src/round159_research_main.cpp`和相关`scripts/round159_*`提供当前研究接口。
- R159新增载体`results/unified_exact_round159/artifacts/new_evidence.zip`，SHA256 `60cc9a5073f71d39ba9e07f8a44846fa18a77b1b336175c92912f248e4fb1270`，19760786 bytes、432 members。保存事件在baseline/joint runs，已完成物理DP在complete runs；审查补核只需要这些点与相同active set的已有无载荷结果。
- R158：[PR #220](https://github.com/yifanXovo/TailoredExact/pull/220)，science `163b1b3d0dbcc7be3a84d94108ef4a26ae9baba3`；coefficient_binding_correction、reuse_index、数学/结果。实际duration修正与单侧包络继续复用。
- R157：[PR #219](https://github.com/yifanXovo/TailoredExact/pull/219)，science `9889473a9b64c749ea8841bac1d38fec8be21d96`；inventory_sources/families中的positive_control及完整来源。
- R156：[PR #218](https://github.com/yifanXovo/TailoredExact/pull/218)，science `751de842a0264a146701de6669b1f3dd6dc764b1`；E+入口、完整臂、费用和manifest。R137输入/matrix_frozen用于四角色身份，R159 goal已列输入hash。
- 当前稳定主线：`docs/paper_s2_release.md`、`config/paper_s2.json`、研究索引、R135模型/算法说明及R133/R134修复。R61资料实际位于`results/gf_transfer_block_native_time_round61/`；R76/R83/R96/R103/R105–107按研究索引定位，不猜错目录。

| 用途 | 优先接口 | 本轮注意点 |
|---|---|---|
| 原J/RN | `round153_pricing.py::Oracle/stock_value`；`round157_floor.py::objective/original_lower` | 复用归一化和数值映射；局部objective收缩需包含所有outside |
| 物理建模/验证 | `round157_fleet.py::build/decode/verify/lift`；已有Evaluator与R61/R105接口 | 复用语义，不启动旧master/全车队长查询 |
| 已有primal闭包 | `Round76PhysicalClosure.hpp`、`Round83BlockExchange.hpp`、`Round96RouteOrder.cpp` | 明确旧能力；本轮同域owner-fixed控制不冒称重现全部R96 |
| 系数 | `round158_level.py::coefficient_package`及R158修正manifest | 原T/实际duration/handling与接受政策保持一致 |
| 固定组合诊断 | R159已合格C++DP及保存结果 | 只在新问题确有需要时调用，不重算已闭合13点 |
| 完整方法/费用 | `round156_online.py`、`round156_rn.py`及冻结manifest | 新建R160八臂调度，隔离OUT/预算，全部在线成本自付 |

文献定位仅用于准确归属：Vidal等，`A unified solution framework for multi-attribute vehicle routing problems`，EJOR 234(3), 658–673, DOI [10.1016/j.ejor.2013.09.045](https://doi.org/10.1016/j.ejor.2013.09.045)，[作者技术报告](https://www.cirrelt.ca/documentstravail/cirrelt-2013-22.pdf)；Santini、Schneider、Vidal、Vigo，`Decomposition strategies for vehicle routing heuristics`，[作者预印本](https://optimization-online.org/wp-content/uploads/2021/03/Decomposition_Strategies_for_Vehicle_Routing_Heuristics.pdf)。它们支持对序列摘要、聚合和局部域的已有背景说明，不是本轮尚未证明的性能依据。

最终明确区分：**数学上有效的局部构造、实际物理upper改善、作用域内的机制证据、完整精确算法的净收益。** 对当前新物理方向做实质研究，按证据决定继续或停止，不把有限局部结果扩大成全域结论，也不让重复审核取代算法工作。

