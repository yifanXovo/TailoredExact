/goal

# TailoredExact 下一轮完整任务清单

## Round142：条件计数与公共因子的乘积一致性——加强证明来源并检验完整价值

**日期：2026-10-30。建议轮次：Round142；编号已占用时沿实际下一轮继续。**

## 0. 目标、优先级与自主权

R141 可以验收。计数子域与条件 TC2 在三个匹配域上提供了强于 Gini 中分的覆盖界；D1 在 K20 相对同版本 D0 有实质时间收益，但重要角色 RB35-T2 双端回退，完整候选仍为 research-only。稳定 R137 GI-TBC 保留，不补无决策价值的旧候选全面板或 Seed 网格。

本轮问题：**现有 count 子域虽约束了 selector 的站点计数，却没有将同一计数限制施加到公共 Gini 因子的分解中；补上这一乘积一致性，能否提高真正决定 cover 的较弱来源界，并形成值得保留的完整算法增量？**

按三步推进：

1. 整理本 goal 中的结构性解释，复用保存点，以六个既有 count 子域做有限 LP 研究。
2. 默认先试选中计数的四条产品行；必要时用全部传播计数族检查该方向的潜力。新行只进入条件来源 LP。
3. 来源有实际增量时，复用 R141 的 D1 流程测试一个统一候选；否则以数学与实验证据收束此续线。

**新增实验计算总上限8小时。** Codex 可根据实际结果调整少量诊断域、顺序、实现和一个相关小扩展；不要求用满预算或强制进入完整测试。主候选保持统一，不按实例身份或规模挑选配置。

所有未明确多 Seed 的新求解显式使用 **Gurobi Seed=0**；有限第二 Seed 为1。H seed固定20260626并单列。计时求解单线程、串行，编译、重 I/O 和 PDF 导出错开。

算法应有统一的数学或结构依据，不按实例打补丁、不按大小准备两套算法、不以运行若干秒后切换方法或 leaf 作为步骤。允许依实际支持、有效计数界和数学冗余生成或删去约束。实验 cap、物理 T 与算法规则分开。以论文可陈述的收益为目标，允许有解释力的混合表现，但拒绝重要角色或大范围严重回退。

---

## A. 起点、已验收结果与本轮不重复的工作

### A1. 实际版本与工作区

| 项目 | 编写本 goal 时核实的参考 |
|---|---|
| 仓库／前序PR | yifanXovo/TailoredExact；#203，open／Draft，未合并 |
| R141 branch／head | codex/round141-count-disjunction；dd59e0a07cde2255c4f2b3314246cb61eac431f6 |
| R141生产源码 | 0b6148c22e572e7151bb5c90b4746cb0d7f706e1 |
| R141固定science | 93db852d4fd82b91d5c8f681c80d776339f126d8 |
| 稳定入口 | scripts/paper_s2.py → config/gi_tbc_round137.json |
| R141研究入口 | scripts/paper_s2_count_disjunction.py；config/gi_tbc_count_disjunction_round141.json |
| 活动树／新资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work\ |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议branch／结果目录 | codex/round142-conditional-count-products；results/unified_exact_round142/ |

先读适用 AGENTS.md、WORKSPACE_POLICY.md，核实 refs、未提交内容、进程和资产。main已吸收所需版本时从实际main继续，否则从已核实的R141继续并以其为临时PR base；不等待合并，不机械回退参考SHA。

继承自身H、M-B/VD-P、pair-only、AM=.08、depth=8、minimum width=1e-4、AP off及R134证明政策。完整研究载体是R141 D1：stock BOTH＋旧TC＋TC2，统一最大加权弦余量选轴、LP-floor pivot。新改动默认关闭，R137–R141入口及既有开关语义保持完整。

### A2. 已完成的范围

- R141有39个显式连续LP：3个父对照、24个plain/conditional count子域、6个D0/D1根、6个完整writer导出的Gini子域。
- 正式完整位置为4个D1 Seed0及K20/K35两个D0；另有2个健康资格和1个保留失败资格，无新增Seed1。所有六个正式位置都实际取得并安装了pair，均无outer split。
- K20 D1相对同PE D0节省23.689秒production；K35的U改善.011628889、L回退.000311467。RB35-T2 D1为U/L=.413773275/.227918419，不能推广。
- 新增实验约2.114小时，停止来自结果而非预算不足。R141的VType恢复／probe释放资格问题已经定向修复，非新的浮点LB/UB问题；不另开工程专项。
- 稳定入口、旧raw及失败均保留。R50/R51优先级、R62局部阈值、R88 CDF、R120–R122 Gini轴proof注入已有历史；本轮不重开它们。

### A3. 本次额外复核否定的直接续做

R141末尾提出“计数反推库存预算”。其线性界本身已被连续selector和count限制隐含。令optional站高侧质量为a_i，则

\[
Y_i\le b_i^{<}+(M_i-b_i^{<})a_i,\qquad
Y_i\ge m_i+(h_i-m_i)a_i.
\]

低侧限制 \(\sum a_i\le m-|H|\) 后，对第一式右侧求最大，只需取相应个数的最大增量；高侧最小库存同理取最小跨阈增量。因个数是整数，这个连续基数背包的极值就是原排序公式。因此不能把“补一个线性库存界”预期为新LP加强。

更关键的是：对R141三个角色、两pivot、两侧的12个conditional域复算，反推后库存区间**全部不变**：

| 角色 | 原区间＝反推后区间 |
|---|---|
| K35 | [251,326] |
| RB35-T2 | [161,236] |
| K20 | [148,208] |

24个plain/conditional位置的检查一致；stock包络和TC2计数范围也不变。故本轮不把该建议安排成新的生产任务。R140已记录的K35返库上界同目标替代点、直接安全M激活子TC2的10个分数binary延拓结果继续保留，不重复相应面板。

---

## B. 先明确标量proof注入的能力边界

设父松弛为P，两个来源松弛 \(P_i\subseteq P\) 的相同完整目标最优值为 \(\lambda_i\)，保守floor为 \(\beta_i\le\lambda_i\)。若较弱来源的一个最优点能加上对应整数b并满足D1的完整links，则

\[
\boxed{\min_i\beta_i\le z_{\rm D0}\le z_{\rm D1}\le\min_i\lambda_i.}
\]

左侧来自公共／条件floor，中间来自D1包含关系；右侧来自把较弱来源最优点直接扩展成D1可行点。

理想 \(\beta_i=\lambda_i\) 时，两个根最优值必相等。统一下调 \(\varepsilon\)、且未被cutoff截断时，二者差至多为 \(\varepsilon\)，实际序列化误差另按既有政策处理。

**最优点可扩展的前提不能省略。** R141来源只显式加入一侧count限制，D1 links还带父域另一端。当前三个较弱点已核实满足：

| 角色／较弱侧 | 保存K | D1该侧区间 |
|---|---:|---:|
| K35 high | 10.3033421624 | [9,33] |
| RB35-T2 low | 1.9808370142 | [0,5] |
| K20 low | 5.4031520881 | [0,7] |

所以R141三域D0/D1根最优值相同有结构性解释，不需要更细精度重测。本轮目标是**提高来源 \(\lambda_i\) 和完整cover**；条件floor对可行几何及Native搜索的作用仍可存在，但不再把D1单独超过D0的根最优值当验收目标。

只得到未达最优的dual bound、cutoff不可行且无primal见证、不同目标或无法扩展的点，不能直接套用上述等值结论。保留原cutoff补集、有限floor和source失效规则，不通过放宽容差制造增量。

---

## C. 数学主线：条件计数的公共因子一致性

### C1. 直接使用已有变量

VD-P已有
\[
s_{iy}\ge0,\quad \sum_y s_{iy}=1,\quad
q_{iy}=\text{state\_g}_{iy},\quad \sum_yq_{iy}=g,
\]
\[
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\qquad
Y_i=\sum_yys_{iy},\quad Z_i=\sum_yyq_{iy}.
\]

在整数selector下 \(q_{iy}=gs_{iy}\)。令c_i>0为模型实际加载的目标库存倒数，r_i=c_iY_i为库存—目标库存比；阈值取自实际有限支持并保留精确dyadic含义。对物理阈值t定义
\[
K_t=\sum_{i,y:c_iy\ge t}s_{iy},\qquad
W_t=\sum_{i,y:c_iy\ge t}q_{iy}.
\]

W是现有列的表达式，不新增W变量。物理解满足 \(W_t=gK_t\)。本轮使用各count来源域已有效的 \(\ell_t\le K_t\le u_t\) 和其实际g区间，加入

\[
\begin{aligned}
W_t&\ge\alpha K_t+\ell_tg-\alpha\ell_t,\\
W_t&\ge\beta K_t+u_tg-\beta u_t,\\
W_t&\le\beta K_t+\ell_tg-\beta\ell_t,\\
W_t&\le\alpha K_t+u_tg-\alpha u_t.
\end{aligned}\tag{CP}
\]

这是计数约束与 \(g-\alpha,\beta-g\) 的标准RLT／McCormick提升。它使用跨站点的条件计数范围；不把标准乘积包络称为新理论。

当 \(\alpha<\beta\)，CP本身还推出 \(\ell_t\le K_t\le u_t\)，例如将两条含u的上下式合并得到 \((\beta-\alpha)K_t\le(\beta-\alpha)u_t\)。因此需要区分“补完整计数范围”和“补乘积一致性”的增量。固定g时CP退化为已有等式，不能据此省掉计数范围本身。

### C2. 为什么已有stock和原始count范围不够

对 \(\alpha<g<\beta\)，定义端点归一化selector
\[
s^\alpha=\frac{\beta s-q}{\beta-g},\qquad
s^\beta=\frac{q-\alpha s}{g-\alpha}.
\]

它们非负、每站和为1；令 \(\theta=(g-\alpha)/(\beta-\alpha)\)，则
\[
(s,g,q)=(1-\theta)(s^\alpha,\alpha,\alpha s^\alpha)
+\theta(s^\beta,\beta,\beta s^\beta).
\]

原始count行限制平均selector s。CP要求两个端点selector也满足同一计数范围。stock的四行约束的是端点总库存，不自动替代这些条件计数限制。端点及固定g情况用未归一化质量处理，避免除零；实现无需真的构造这些比值。

### C3. 可写入研究说明的表达关系

复用R138的选定资源块共同因子定理，不重新宣称一般凸包原理。另给出以下有限块的证明：

令 \(P_C\) 仅由每站one-hot单纯形和有限组嵌套阈值的整数计数上下界定义。该多面体是整数的。构造网络：每站输入一单位流，每个支持状态对应一条通向其比例层的选择弧；比例层沿降序链汇向sink。跨过阈值t的链弧流量正是K_t，赋整数下／上容量 \(\ell_t,u_t\)。网络流整数性及投影给出结论。

于是，对该**计数selector子块**，VD-P加所有所选计数行的CP，给出共同因子乘积的精确凸包：先用R138端点分解，再利用 \(P_C\) 的整数性。对图像q=gs上的固定g，P_C中的分数selector可以分解为同一g下的整数selector，因此连续／整数selector的乘积凸包一致。

该结论不包含加权库存预算、路线、时间、完整Gini分子和原目标的全部关系。加入这些约束后，不能声称获得完整BRP整数凸包。若同时对stock及count全部定义行作RLT，R138定理仍给出相应**连续选定资源块**的乘积凸包，不能把它提升为完整整数资源块。

还有一个有用的去冗余关系：在VD-P下，端点的阈值计数也嵌套。故
“所有父域count产品行＋选中轴的条件CP”
等价于
“所有经单调传播后的count产品行”。
ALL相对selected-only的进一步收益来自其他父域count产品约束，而不能归给一种新的独立传播原理。明确固定g时计数行保留的条件即可，不为此实现新网络算法。

### C4. 有理数严格见证

可复用下面的极小块，用Fraction核查，无需新增整数求解：

n=4，每站支持{0,1,2}、c_i=1，总库存区间[3,5]，g区间[0,3/4]。每站取
\[
s=(1/4,1/2,1/4),\qquad
q=(3/20,3/40,3/20),\qquad g=3/8.
\]

于是
\[
\tau=4,\quad J=\sum_iZ_i=3/2=g\tau,\quad
K_1=3,\ K_2=1,\quad W_1=9/10,\ W_2=3/5.
\]

取 \(H_\Sigma=5\)，每对h=5/6。该点满足局部VD-P、stock包络、旧TC（右侧2）、父TC2（右侧4）、子域 \(K_2\le1\) 的TC2（右侧5）、产品侧 \(H_\Sigma\le4J=6\)，以及所有父域count产品行。

但子域u_2=1要求 \(W_2\le g=3/8\)，被违反9/40。两个端点selector为(.1,.8,.1)和(.4,.2,.4)：各自库存为4，但后一端点的K_2=1.6违反子域计数限制1，平均selector的K_2仍为1。

这证明了所声明松弛块的严格性，即使stock乘积恰好精确、父count产品行已存在，条件CP仍有新增信息。它不是完整BRP可行见证、最优目标增量或闭gap定理；不为扩充定理强制构造新的完整tiny BRP面板。

---

## D. 从已核保存点进入有限新LP

### D1. 现有信号与范围

本次验收使用R141固定diagnostics封包，SHA256：
8552f9cbc2927e16b9f1e77f470a31651e4764c9034daa0e1fb0f04ee7a10d31。
对其count来源与相关根／投影点，并复用R140五个TC2根，完成了零Optimize代入。

五个R140根及R141当前父点均满足全域count产品行，最大残差约3.2e-15；十二个R141 conditional点按**原父域计数范围**检查也通过。因此没有理由默认安排全域count-RLT的完整新算法。

使用LP-floor子域收紧后的范围，则有：

| 来源 | 当前数值LP最优值 | 条件CP最大违反量 | 是否当前较弱侧 |
|---|---:|---:|---|
| K35 low，K≤8 | .241539945750 | .198124243227 | 否 |
| K35 high，K≥9 | .240140105053 | .414570725937 | 是 |
| RB35-T2 low，K≤5 | .146301752943 | .167523019846 | 是 |
| RB35-T2 high，K≥6 | .150566942398 | 数值0 | 否 |
| K20 low，K≤7 | .255556702786 | .228635736478 | 是 |
| K20 high，K≥8 | .268192585045 | 数值0 | 否 |

这些点的物理K已满足对应范围，新增违反来自乘积一致性。比如RB low端点计数约12.038超过5；K20 low约10超过7；K35 high的另一端点计数约8.398低于9。三组较弱侧都被分离，支持进行新LP，但违反量仍不等于目标收益。

### D2. 最小匹配比较

优先复用上述六个LP-floor来源，保留原目标、cutoff、支持、g区间、count限制、父／子TC2及stock：

- **C：计数范围对照。** 补明对应两端范围，核查旧最优点能否原目标扩展。Selected轴六点均已满足；匹配原矩阵与新行后，可据旧最优下界及同目标可行点记录“无新增Optimize的同目标见证”，不机械重跑六个相同LP。
- **S：Selected CP。** 对选中计数使用该侧有效区间，加四条CP；默认最多六个新LP。
- **ALL：全部传播计数CP。** 必要时在同六域加全部有效计数族，作为有限潜力检查，最多再六个新LP。允许按已证明的嵌套包含关系删除冗余行。

ALL也可能隐含其他阈值的线性范围，先检查保存点是否满足它们。若不满足，补少数必要range-only对照或将结论准确表述为“范围＋产品组合增量”，不把全部收益归于产品。原点仍满足新增行时，优先利用可行见证，不为填表重复优化。

ALL相对S的进一步增量可用C3的等价关系解释；无需同时再铺“父族＋selected”完整对照。若S与ALL都缺乏来源或cover增量，完成该方向的结论，不再以类似RLT的小变体延长数轮。

报告两侧原／新L、保守floor、完整min-cover、行数／非零数、构建与求解成本，以及K、W和端点计数诊断。端点计数只用于解释，靠近g端点时以无除法残差为准。

### D3. 来源增强之后的判断

进入完整pilot需要实质来源信息：增量超出数值误差，并提高共同cover或一个有用的条件floor；后一种情况应说明它对实际松弛或相应计数侧的作用，不能仅抬高已经不限制cover的强侧。只有切掉保存点而同目标替代点仍存在，不足以自动启动全面板。

历史Native早期界是经验参照，不是硬性要求新LP必须超过它，也不能免费注入新运行。若增量很小、很快被原生已有界覆盖，允许直接结束。对有解释力且实现成本低的混合信号，可做有限pilot。

本轮不再以D1-over-D0根LP提升为目标，也不默认重复其网格。必要时仅用一个新根诊断确认新来源floor正确进入模型及B的夹逼关系。新来源保留旧来源全部行，理想LP界不应下降；数值微差按既有资格解释，不虚构负增量或通过改容差追求漂亮结果。

在小LP结果后冻结一个统一候选，优先S；ALL若有清楚的额外收益，可选择ALL或有数学依据的统一去冗余版本。不能为每个实例离线挑最好的产品行集合。

---

## E. 最小实现：仅加强两个条件来源

新增默认关闭的独立研究开关，建议语义为off／selected／all；保留旧R141开关及行为。只有选中的研究配置在两个R141 count probe内加入新行，**不把条件CP直接写入未受限父模型或原生MIP**。

复用当前root、选择规则、两次probe、count-local scope、物理见证侧别、cutoff补集、有限floor和source撤销。无新增列、binary、Start映射、probe数量或frontier类型。原生整数artifact仍是同一父模型＋相同b与links，区别应是新来源返回的floor系数。

实现要点：

- 直接展开已有state_g列。alpha/beta取实际来源域端点，不取观测g*。
- 精确阈值／membership沿用R140；每条约束绑定实际source支持和计数范围。
- 在现有probe行向量中加入CP后统一canonical append，使实际Native读回覆盖count、子TC2和新增CP；若分层append，合并expected-row记录，避免新SHA只检查最后一层。
- 复用R138按方向外向RHS舍入和整行正二次幂缩放：≥的RHS向下，≤的RHS向上；也可先统一改写为≥再向下舍入。删除精确零项，保留小的非零项；expected map与实际writer一致。
- 新helper或header变化实际编译所有受影响单元并记录真实source／PE；不用机械要求全项目重建，也不能直接沿用不再完整的旧对象。
- 两个新来源和其floor逐一绑定，所有在线新增构造／求解／验证计入完整方法成本。不能免费复用诊断界或别的方法结果。

资格只覆盖新风险：low/high行与常数、当前g域、Native实际系数读回、源floor绑定、条件行没有泄漏父／MIP、关闭开关后的旧行为。R141已有的scope、Start、VType恢复和失效链定向复用，不恢复全部历史raw或重跑所有旧资格。至少覆盖一个alpha>0的小域或精确代数fixture，避免根域alpha=0掩盖系数与常数错误；不因此新增完整算法网格。

---

## F. 完整算法比较

### F1. 一个候选、先四角色

来源有信号后，使用冻结配置和完整原窗口：

| 角色 | 站点／车辆 | 物理T | 目标 | 完整cap |
|---|---:|---:|---|---:|
| K-15-S | 15／2 | 3600 | lambda=.15 | 600 s |
| K-20-S | 20／2 | 5400 | lambda=.15 | 1200 s |
| K-35-U | 35／3 | 10800 | lambda=.15 | 2400 s |
| R-B35-S-T2 | 35／3 | 7200 | rho=1，lambda=1/Omega | 2400 s |

合计6600秒。建议K35／RB35-T2尽早进入，以检验重要角色表现；顺序可依资格调整。R141的K35晚至约2100秒后才出现最终U收益，不能用几分钟短跑代替hard-role完整窗口。

主要参照是**旧R141 D1**，同时保留稳定GI-TBC、stock、旧TC与R140 TC2的历史位置。旧D1与新D1的父模型、选轴、pivot、links和流程应一致；实际变化是来源模型及所得floor，不将完整收益直接归为“Native按count分支”。

### F2. 必要桥接与归因

旧D1可作为匹配完整方法参照，保留原source／PE和成本。结果将支持重要时间或机制结论时，补1–2个同PE旧D1桥接即可，默认预算对应K20＋一个hard role，共3600秒。若选择两个hard role需4800秒，应调剂而不静默超额。

不重新铺D0完整网格。若一项新结论确需额外对照，可从上述比较额度替换一个位置，说明它回答的问题；不能把所有可能控制都变成必跑。

完整方法独立取得自身H、根LP、两个在线来源及验证结果，不注入历史／诊断解、界、Start或树。保留输入、参数、Seed、环境、时钟与实际源身份。

### F3. 有依据才扩展

新候选在pilot中表现值得保留或需要确认的混合边界时，可补：

- RX20-T1：20／2，物理T4800，cap1200；
- RB35-T1：35／3，T4800，cap2400；
- RX35-T1：35／3，T4200，cap2400；
- RX35-T2：35／3，T6300，cap2400。

均rho=1、lambda=1/Omega。余四cap合计8400秒，主候选八配置15000秒，仍是六基础输入的八配置。

R141 D1只有四个正式角色，R140 TC2只有五个；缺失格不能推断。扩展格可先与现有稳定／stock／旧TC比较，限定归因范围，不默认补旧D1全部缺失格。重要回退明显且没有值得确认的收益时停止扩展，不按每例必须获胜判定。

只有会改变采用／停止判断时，才对一个关键角色做至多两方法的Seed1确认，上限4800秒；匹配旧参照可复用，不默认全表双Seed。

继续分别报告U、支持L、signed/relative gap、T_produce/T_cert/T_verify/T_total、Native返回bound和外部合并bound。open的T_cert为空，不以cap冒充收敛时间；probe、Work和节点用于解释，不能重复计费或代替完整性能。

---

## G. 预算与收束

| 内容 | 规划上限 |
|---|---:|
| 匹配LP、数学fixture、新行资格及短诊断 | 3600 s |
| 四角色完整pilot | 6600 s |
| 有依据时补余四角色 | 8400 s |
| 必要同PE旧D1／有限比较 | 3600 s |
| 单个关键角色条件Seed1成组确认 | 4800 s |
| 必要修正与机动余量 | 1800 s |
| **总上限** | **28800 s＝8 h** |

诊断＋pilot名义约2.83小时；主候选八配置＋诊断＋桥接额度约6.17小时。所有扩展、Seed1和余量均条件执行；可以调剂分项，不把以前未花完的预算视为应追加工作。

新完整方法按全过程外层实际计费，嵌套H／LP／MIP／Work不重复累计；资格、失败求解和探索计入新增实验。旧参考保留原完整成本但不算新计算；编译、离线分析、文稿与公开I/O另列。

工程问题定向处理，真实正确性问题修正或停用受影响候选。普通报告、reader或交付metadata修订不触发无关健康运行重跑。

若ALL也没有有用来源增量，或候选没有值得继续的完整收益，以清楚边界关闭本条count-proof续线；可指出后续需要哪类新信息，但不在本轮自动转入更多相似RLT、AM/Seed网格或一般性H重开发。

---

## H. 论文增量与独立复核

无论完整候选是否成功，本轮应组织以下可核实内容：

1. 标量floor注入的可达最优点夹逼关系，解释R141根最优值相同的范围，修正不合理的后续目标。
2. 反向库存界的连续隐含关系和实际十二域预算不变，说明为何不执行该旧建议。
3. 条件计数与公共因子端点的一致性；所选计数块的网络整数性、R138定理应用、父族／传播族关系，以及有理数严格见证。
4. 新LP的真实来源增量、完整cover、成本及完整算法正反结果，区分数学表达、点分离、优化目标和搜索表现。

标准网络流、RLT和旧R138凸包原理保持其已有地位；不将有限计数子块包装成完整BRP凸包或一般分母决策问题的全解法。稳定GI-TBC的现稿继续可用，不因研究候选未推广反复重写主算法。

复用现稿，仅更新受影响章节或研究附录。需要PDF时检查受影响页，保留正式稿与研究增量的清楚身份。

昂贵完整运行前由非主要实现者核查关键数学与writer；收尾再独立复核：

- B的最优点扩展前提、floor/数值边界，没有继续要求不可能的D1-over-D0根增量；
- CP方向、常数、当前g域、count域及parent/child范围正确；
- 网络整数性和乘积凸包只针对声明子块，未推广到加权库存／完整路线；
- selected／ALL与range-only的归因成立；同目标旧点按证据复用；
- 新行只在来源模型，完整floor对应实际新call/SHA，旧入口与流程保留；
- 全部已进入正反结果、完整成本、默认Seed0及必要桥接一致，预算无重复；
- 条件块有停止自由度，没有为了完成表格强制开第二条生产线。

修正实质问题，给出简明复核结论即可，不建立新的庞大审计体系。

---

## I. 交付、Draft PR与有限清理

交付本goal、最小代码／配置差异、数学与历史关系说明、匹配LP／完整表、必要raw和来源绑定、计费、采用决定、增量稿、独立复核及续跑入口。重复报告可合并，内容完整比文件数量重要。

正常提交、推送研究分支并创建英文Draft PR，建议标题：

**Round142: strengthen count-local proof sources with shared-factor consistency**

main未吸收R141时，以codex/round141-count-disjunction为临时base；已吸收时用实际main。读回base/head与交付状态。不自动merge、force-push、删除历史分支、发送邮件或投稿；待合并不阻塞研究完成。

必要新载体做一次有限公开字节／成员读取，纯I/O建议累计30分钟内收束，不触发Optimize、编译或商业Native加载。区分本地科学／语义验收与公开可读性，失败定向处理，不重开旧轮全历史恢复。

**显式继承WORKSPACE_POLICY两项要求：**全部新build/raw/temp/restore资产位于E:\codes\ExactEBRP-work；PR交付后进行本轮有限清理。仅在证据保留和公开核对条件满足后，删除已完成且可重建的临时／重复对象。保留唯一raw、失败、用户内容、必要PE/DLL及仍需使用的树；不删除旧轮。记录删除／保留和实际字节，零删除可接受。

最终报告回答：条件计数乘积是否确实补上松弛自由度，较弱来源及完整cover提高多少，是否产生完整方法收益，哪些重要回退保留，花费多少，建议采用／research-only／结束该续线中的哪一种。

---

## J. 最小资料索引

- R141 PR：https://github.com/yifanXovo/TailoredExact/pull/203
- R141固定science：https://github.com/yifanXovo/TailoredExact/tree/93db852d4fd82b91d5c8f681c80d776339f126d8/results/unified_exact_round141
- 核心记录：final_report.md、mathematical_analysis.md、LP_report.md、candidate_decision.json、reports/LP_positions.json、LP.csv、projection.csv、new_arms.csv、full.json、review/selection.json及最终整合复核。
- R141诊断载体：artifacts/diagnostics_and_failures.zip；取domains各角色的scope/additions及LP中lp_floor low/high conditional的result、模型与solution.json.gz，核对实际成员身份，不从四舍五入报告重建参数。
- R141实现：include/Round141Research.hpp；src/PaperExternalGiniTree.cpp、GurobiBaseline.cpp、NativeEvidenceJournal.cpp、MipStartMapping.cpp；round141Probe／Append及实际Native expected rows。
- VD-P与成熟writer：src/CplexBaseline.cpp中的state_g、g/product reconstruction；R138 stock writer；include/Round140Research.hpp的精确阈值与计数；scripts/round140_math.py、round141_math.py、round141_lp.py。
- R138既有理论：https://github.com/yifanXovo/TailoredExact/blob/1b19897ab5819ab3b7485ddc978954b45225f361/results/unified_exact_round138/mathematical_analysis.md ，特别是第3节选定资源块凸包及其范围。
- 工作区／稳定入口：WORKSPACE_POLICY.md；docs/current_mainline.md、round141_research.md、unified_exact_research_index.md及R137稳定配置。只定向读取需要的历史，不恢复全部旧raw。

**本轮成功标准：把已定位的条件计数乘积缺口转化为可核实的来源加强，明确其表达能力和实际收益；有信号才进入一个统一完整候选，无信号则及时形成结论，稳定主线持续可用。**
