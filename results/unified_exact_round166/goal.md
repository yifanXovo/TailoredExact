/goal

# Round166：形成 EJOR/TRE 论文主张，研究共享库存状态的精确压缩

## 0. 目标、实际增量与预算

继承已完成的 Round165。本轮同时推进两项相互支持的工作：

1. **EJOR/TRE 成稿主线：**以“共享库存状态连接、完整精确方法及其可认证的运输决策价值”为中心，直接修改当前英文论文；从已有物理方案与合格上下界中得到新的连续权重分析，而不是再做一轮贡献清单或文档当前化。
2. **OR 深入主线：**研究一个明确的表示问题——在当前非零单向服务规则下，能否利用库存—移动—访问函数的分段仿射结构，以少量合法断点和二进制乘积层，代替逐库存值的 one-hot 表示，同时保持整数物理可行域、原目标和共同变量空间中的 LP 投影；若成立，完成一个统一 C++ 候选及有限完整方法比较。

两项都必须产生实质结果。第一项不能只交修改建议，第二项不能只交“今后值得研究”的题目。完整推导、明确反例/适用边界、可检查的模型关系和经过公平评价的候选，均可构成有价值结果；不要求预先保证加速或证明 OR 级原创性。若压缩不能按预期成立，交付确切失败条件与证据，并完成论文和决策分析；不临时换成另一条大研究线。

**选择这一方向的理由：**旧 LOG 研究减少了整数编码位，但仍保留逐库存值的连续 selector/product；本轮研究的是这些连续状态是否可以按其对外可见函数精确压缩。它与 R104 的目标保持资源行聚合、R161/R162 的连续物理产品补全不同。历史排重仍须核实这些区别，不以名称不同当作创新。局部断点凸包和 binary-product 本身使用标准析取/线性化工具；研究价值必须落在明确的联合对象、可迁移条件、完整模型嵌入与实际代价。

当前 B/GI-TBC 保持冻结。候选暂称 **C166**，默认关闭、单独命名。保持 Gini 外层、完整 own-H、有效行、原生参数与数值政策；本轮只改变声明的库存表示。**不并行启动 full/root、新 E+、额外 Seed、路线邻域或新 cut 项目。**现有 full/root 结果保留为论文中的架构证据，但不再把“外层必须独立获胜”设为所有研究方向的门槛。

### 0.1 工作容量

总科学工作容量 **16h = 57,600s**，完成即停止，不等待用满。建议目标 8–12h；容量包含定向阅读、推导、实现、全部研究计算、数据处理、直接改稿、构建及独立审阅。并行代理按共同外层工作窗口计一次；同步记录求解进程实际费用，不能把并行计算藏在“阅读时间”中。普通 Git/公开恢复传输 I/O 单列。

| 工作 | 预算安排 |
|---|---|
| 入口、历史/近邻核查、压缩推导与 C++ 实现 | 约 4h |
| 已有方案的参数/资源分析 | 约 2h |
| 新表示的结构诊断与资格检查 | 最多 1h 外层计算；独立于下列正式运行 |
| 唯一完整方法批次（条件满足后） | 6 个固定输入 × B/C166 × Seed0，名义总 cap 最多 21,600s = 6h |
| 正式运行必要核验/收束余量、直接改稿、导出、独立审阅与收尾 | 预留约 3h，其中正式批次额外核验/收束最多预约 1h，稿件与审阅至少留 2h |

分项可在 16h 内调整，但诊断不超过 1h，正式批次不超过规定的一个 12 臂矩阵。入正式批次前，须至少剩余 **9h**：按每臂 cap+300s，12 臂完整预约共 25,200s=7h，加至少 2h 稿件/审阅收尾。额外 300s 只预留核验与收束，不延长 producer/Native 的评价窗口；按实际费用入账，不把 reservation 或 watchdog 当作已消耗时间。不要为满足目标时长削短已冻结的单臂合同，也不要耗完论文/审阅预算再宣布仅实验完成。若证明/实现出现实质障碍，及时交付已有推导、反例和当前稿，不消耗预算尝试更多编码变体。

**新增反复执行的优化核心、建模、精确枚举 oracle、资格 LP/MIP driver 和完整候选均使用 C++。**Python/Node 可用于编排、日志、独立物理验算、离线有理数代数/有限交点计算、图表和文档；不使用 gurobipy 或求解器 CLI 替代 C++ 优化核心。参数分析的解析有限交点计算属于离线分析，不是新生产算法速度样本。历史 Python E+ helper 按事实保留，本轮不顺带移植或重测。

算法规则只能依赖合法输入、当前数学域与证明条件。实例名称、数据源标签、历史胜负、机器型号/速度不得进入在线决策。实验共同截止时间是评价合同，不得变为按硬件时间触发的算法切换。

## A. 本地入口、当前身份与 PR

遵守仓库 `AGENTS.md`、`WORKSPACE_POLICY` 和既有工作区约定。所有新增工作、缓存、临时件及交付在 `E:\codes\ExactEBRP-work` 内。保护原 `E:\codes\ExactEBRP`、用户文件、活动 worktree 和历史证据。

`E:\codes\ExactEBRP-work\worktrees\paper-current` 之前仍在 R155 且有未提交修改；只读检查实际状态，不 reset/stash/覆盖。优先在核实的 R165 基础上新建或接续 `E:\codes\ExactEBRP-work\worktrees\round166`，分支建议 `codex/round166-structure-and-paper`。已有同轮结果先去重接续。

任务编写时核实的身份如下；开始时一次读取远端真实 main/前序 PR/head，以实际合法更新为准：

| 身份 | 固定参照 |
|---|---|
| 仓库 | `yifanXovo/TailoredExact` |
| 前序 | [Round165 / PR227](https://github.com/yifanXovo/TailoredExact/pull/227)，Open Draft、未合并 |
| R165 branch / delivery | `codex/round165-current-manuscript` / `239db6a80c944f1e7b5a55504ce5202ea35c2586` |
| R165 science | `88f3e33a4a88e5691f3e54eb46ccf1242e455e7d` |
| main | `b2b940c1e517a72e226ec60fc49ff19651737632` |
| R164 delivery | `de01e8fb27a954d031abac5fe99442d6c8d29d44` |
| R163 delivery | `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb` |
| R163/R164 实测 C++ source | `e920b92e199e825ec89a2932f701861ff158e0d4` |
| 历史实测 PE SHA256 | `fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93` |
| Gurobi 13.0.2 DLL SHA256 | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |

历史实测 executable 为 `build-cache\round162\complete_v2\ExactEBRP.exe`。`method_freeze.json` 内某些继承字段仍指向早期 R137 executable，不能仅凭该字段选择旧 PE；以实际 candidate/environment manifest、调用记录与 SHA 为准。

main 已完整包含依赖时从 main 开始；否则基于核实后的 R165 head，Draft PR base 取 R165 branch，无需等待合并。本轮新增源/PE 与历史实测身份分开记录。新增研究记录在 `results/unified_exact_round166/`，论文仍在 `results/unified_exact_round137/` 的维护组件中更新。只维护一套当前英文正文，不并行制造 EJOR/TRE/OR 三套全文。

## B. 定向排重与近邻核查

先读 `docs/current_mainline.md`、R165 goal/final_report/decision/contribution_positioning/author_decision_memo，以及当前正文、附录 A/B、数学 companion 和必要数据入口。R165 已完成当前 52/39 页 PDF 和组件一致性修复，不再把这些旧问题作为本轮主要任务。

仅围绕下列问题回读历史正文、实际实现或固定源成员，不重放全仓库实验：

| 历史 | 本轮必须分清的关系 |
|---|---|
| R55、R67 | aggregate McCormick、VD-P、VD-J、LOG 的已知投影与运行结果；LOG 保留全部连续状态，不能把 bit 数下降再当新发现 |
| R98–100 | 当前 A/B movement/visit 连接、方向与 vehicle-state 变体、隐式服务整数性及保护行；明确当前 B 实际启用哪一组 |
| R101–107，特别 R104 | event/rank、vehicle-state、资源 hull、dual row aggregation 与 decomposition；它们不是本轮局部联合图压缩，但可能依赖逐状态列，不能静默兼容 |
| R130、R137 | 已做 full/root、A/B/CR/CG 消融与 AM 结果；不再完整重复这些面板 |
| R132/R133、R135 | 固定正总量下的 objective-gap 反例、AP 与阈值计数结果；不能把局部 hull 称为全路由/整数目标 hull |
| R134、R137 | 已有权重、资源、物理操作与支配观察；本轮增量是完整方案档案和连续参数质量界，非首次发现已有支配关系 |
| R138–162 | 库存/资源/物理产品增强的有效域与负结果；R161/R162 的 full-Q/RN 不是本轮编码压缩 |
| R163–165 | 冻结六配置、完整结果、Seed 确认与当前成稿；不追加常规 Seed 循环 |

形成简明 `research_design.md`：具体对象、与最接近旧工作差异、拟证明命题、唯一候选、固定研究矩阵与评价指标。读到了与本轮实质等价的历史实现时，应直接复用/识别并把研究转为其尚未完成的明确比较；不得仅换名重新做，也不得无说明启动另一机制。

数学近邻复用已读 Gupte et al. (2013, DOI `10.1137/110836183`)、Köppe et al. (2008, `10.1016/j.disopt.2006.12.003`) 和 McCormick；定向补读 Vielma 的 embedding formulations（`10.1287/mnsc.2017.2856`）与 Huchette–Vielma 的 piecewise-linear formulations（`10.1287/opre.2019.1973`）中直接相关定义/构造。只就确切主张查原文，不扩大为新的 BRP 文献普查。不声称首次提出析取凸包、少断点表示或二进制乘积线性化。

期刊定位沿用官方 scope：EJOR 覆盖方法与决策，TRE 覆盖运输/库存/处理及精确优化，OR 要求至少一个重要维度具有突出贡献；不把期刊名当“新定理配额”。本轮的压缩若成立，仍需判断其相对既有工具的实际增量，不能因写成一般命题就自动宣布 OR 级创新。

## C. EJOR/TRE：新的可认证决策分析与论文主张

### C1. 固定分析对象，恢复完整物理方案

使用下列**四个已有权重配置**，不只挑选最有利的一个：

- R134：`K-15-S`、`UC-B20-B` 的已记录三种权重；
- R137：`R-B20-S-T1`、`R-X35-S-T2` 的 `rho∈{0.5,1,2}`。

逐个从固定原表和已存完整 fleet 恢复物理输入、各运行的原目标、方法/Seed、最终方案、合格全域 L、证书资格和 source。R134 至少使用已有 S2/B 的权重点；R137 使用同配置内已存在的 P/PS/B 全部合法方案，不能要求历史并未生成的臂。同一方案可以去重，但保留全部 owner/run 来源。

共享档案只用于**离线决策分析**。逐方案独立核查路线、单向非零服务、库存、载重前缀、空车出发、允许载货返回及卸货时间，重算 true Gini 与原 weighted penalty。核对各权重运行的物理域完全相同：物理 T、Q、库存/目标/容量、站点与坐标、车辆规则不能改变；原则上只改变 lambda，omega 向量与 penalty 定义固定。严格核对每个档案组内归一化权重向量 \((\omega_i/\Omega)_i\) 相同；如原 omega 仅整体同比例变化，可按实际 rho 换算，如相对权重变化则拆成不同参数族，不共用一条 \(v(\rho)\) 或跨族弦。不要把求解时的 cutoff、缩紧库存域或 g 区间当作新物理约束。

如某个完整 fleet 确实缺失，先按 manifest 定点读取现有原件；仍缺失则保留该位置和原因，不能凭舍入的 G/P 数字重造路线或执行新 solver 来填洞。其标量 L 只有在来源与全域资格可确认时才能单独使用。现有完整文件可用时应实际完成恢复，不以“附件可能缺失”为由跳过。

### C2. 建立参数化上下界，而不是把未收敛点连成 Pareto frontier

对同一固定物理域 \(\mathcal F\)，记

\[
\Omega=\sum_i\omega_i>0,\qquad p(x)=P(x)/\Omega,\qquad
\rho=\lambda\Omega,\qquad
v(\rho)=\min_{x\in\mathcal F}\{G(x)+\rho p(x)\}.
\]

使用实际载入的 lambda/weights 与可追溯全精度数；rho 是有效权重的显示与分析坐标。若历史实际 rho 与报告的 0.5/1/2 等值存在浮点差异，保留实际坐标，不按显示值强行合并。必要时在原 lambda 坐标推导后转换。数值结论继承原资格误差并向安全方向处理，不从舍入表格制造严格证书。

1. **可行方案上界：**对恢复的物理方案档案 \(\mathcal A\)，构造
   \[
   U_{\mathcal A}(\rho)=\min_{x\in\mathcal A}\{G(x)+\rho p(x)\}.
   \]
   计算分量支配、支持区间与真正的线交点；保留被支配方案和其历史归属，只在展示包络时省略。该包络是“已有可行方案中的最佳值”，不是原算法在每个 rho 的运行结果，也不是完整 Pareto frontier。
2. **安全下界：**先说明 \(v\) 是一族仿射函数的下确界，因而为凹函数。同一实际 rho 的合格全域 L 可取最大值并保留贡献源；相同坐标不组成零长度弦。对已合格全域下界 \(L_j\le v(\rho_j)\)，在 \(\rho_a<\rho_b\) 的区间 \([\rho_a,\rho_b]\) 内有
   \[
   v(\rho)\ge\frac{\rho_b-\rho}{\rho_b-\rho_a}L_a+
   \frac{\rho-\rho_a}{\rho_b-\rho_a}L_b.
   \]
   弦下界只在对应区间内使用，不能无条件外推。记所有适用弦的最大包络为 \(L_C(\rho)\)，与方案上包络一起使用即可；本轮不另开二维外近似或参数求解器项目。区间限于合格历史权重点覆盖的范围，不补跑新权重。
3. **连续区间质量保证：**给出档案包络或一条明确固定方案在指定 rho 区间上的绝对目标 regret 上界，例如 \(0\le U_{\mathcal A}(\rho)-v(\rho)\le U_{\mathcal A}(\rho)-L_C(\rho)\)。利用分段线性包络的全部真实交点/端点计算最坏间隙，不以稠密网格代替整个区间的保证。所有有效弦的区间端点、弦之间以及可行方案线之间的交点均应纳入分段；用确定性离线代数、有理数或保守区间计算，不新增 Optimize。上下界交叉或负 gap 应触发来源/误差核查，不能简单 clip 后宣布成功。

所有 L 必须是各原运行已完成 cutoff 补域/覆盖汇总后的**原物理问题全域下界**。原始局部 LP、某个 true-G 区间、native rejected source、库存子域或 cutoff 内的未补全 bound 均不能直接跨权重使用。不同权重改变 objective，不能把某个 L 当成另一权重的同一个标量下界；上式只通过明示的参数关系使用它。

这套参数优化原理是标准知识。本轮新结果是：把它应用到完整可核验的物理方案和已有证据，得到此前未报告的连续参数结论。重点检查四个配置分别呈现何种现象：相同方案的权重稳定性、真正的分量取舍、具有较小 epsilon 的连续区间保证、或仍较宽的可行搜索缺口；不预写哪一项一定成立。

### C3. 资源价值与机制解释

保留 R137 四组物理时间 T-pair，核对除 \(T_2>T_1\) 外物理域、目标与其他参数相同、可行域嵌套，然后计算完整的资源改善区间：
\[
\max\{0,L(T_1)-U(T_2)\}
\le F^*(T_1)-F^*(T_2)
\le U(T_1)-L(T_2).
\]
已有四个严格改善下界约为 `.282262/.210529/.111261/.060086`；本轮增量是统一给出两侧界、区间宽度及其决策含义，正式文字使用原全精度记录与已有资格。说明两个 n35 配置虽均 OPEN，仍能判断最优目标严格改善，也明确改善幅度尚有多大不确定性。它证明目标值变化，不是货币收益或一般边际资源价格。

从四组已存 operations 中共同解释 G/P、处理量、载货返回、库存分布及路线时间利用如何变化；不能只展示最符合直觉的一组。特别核查 B35 已存返回库存从 2 到 3、X35 从 1 到 0 的不同变化，说明更好目标未必意味着更少载货返回。区分路线描述与对最优机制的因果断言；不要因为某条路线接近用满 T 就宣称最优解中的时间约束必定紧。

R-X35-S-T2 的 rho=2 方案两个分量都优于 rho=1 旧方案，是已有发现。现在用完整 fleet 重算它在 rho=1 下的实际值并放入上述档案，量化“已知更好可行方案与原运行 incumbent 的差距”。不得回填旧 U、发现时刻或证书时间，也不得将离线拼接方案注入本轮正式 C166/B 的启动过程。

### C4. 实际改稿

以 EJOR 的精确方法主线组织一套正文，同时把资源/参数质量保证作为面向 TRE 读者也有意义的结果。在内部作者 memo 中说明两种投稿强调点即可，不生成三套全文或承诺投稿。

- 引言明确 inherited BRP 的操作语义、库存公平目标和计算困难，贡献按“表示连接—完整精确方法—计算与决策证据”组织。
- 用简明比较说明 P、PS、强化 root-only、完整 B、E+ 各自回答什么；旧对照不等于本轮新运行。C166 只有实际证明/测试结果出来后才定位为本轮新增表示候选。
- 摘要只突出最重要方法思想、结果和一项决策认识；保留一次清楚的范围说明，减少反复的 qualified/paid/finite/历史审计自述。
- 当前 GI-TBC 名称保留。标题/副标题可在 memo 中给一个与证据一致的建议，不能为标题强行制造外层加速主张。
- 把权重“可行方案集合/上下界带”与“真正最优权衡前沿”分开；公平含义维持 inventory-to-target ratio dispersion，不扩大为已验证的人口或用户公平。
- HGA-TGBC 的模型与 decoder 继承归属继续保留。优先使用实际可得的最新作者稿；只有五月稿时如实注明，不称最新、不公开私有原稿。作者顺序/发表状态等少量未知放内部 memo，不阻塞技术结果。
- 保留全部 adverse/open 结果：R137 分组分母，三 Seed 六配置的有限范围，C35 历史 P 最佳 U、X35 固定目标未达、E+ 的一处证明增益和成本，外层独立收益未建立。压缩这些内容的重复表述，而不是删除证据。

## D. OR 深入：共享库存状态的断点压缩

### D1. 明确比较对象

对站点 i，在当前 canonical interval/cutoff 的合法整数库存域
\(\mathcal Y_i=\{l_i,\ldots,u_i\}\) 与 \(g\in[\alpha,\beta]\) 上，定义
\[
m_i(y)=|b_i-y|,\qquad v_i(y)=\mathbf1\{y\ne b_i\},\qquad Z_i=gy.
\]
研究局部联合图
\[
\mathcal H_i=\operatorname{conv}\{(y,m_i(y),v_i(y),g,gy):
y\in\mathcal Y_i,\ g\in[\alpha,\beta]\}.
\]
当前 B 的 VD-P 与 A/B 的连续松弛在共同变量
\((Y_i,\sum_k(p_{ki}+d_{ki}),\sum_k z_{ki},g,Z_i)\)
上表示这一局部对象；结合原库存 balance，可以线性恢复 aggregate pickup/drop。不要额外加入当前 B 未启用的方向—state 等式、vehicle-state theta 或 state-weighted penalty。原 e_i epigraph、pairwise H、S、原目标及其他物理约束均保留。

先严格说明共同投影是什么，以及旧模型怎样投影到它。可以用一个小反例说明“独立 product hull + 独立 service hull”为什么未必等于共同库存混合；这解释当前 B 的连接作用，不作为本轮首次发现。

### D2. 拟验证的压缩命题与推广边界

候选断点集合为
\[
\mathcal K_i=\{l_i,u_i\}\cup
\bigl(\{b_i-1,b_i,b_i+1\}\cap\mathcal Y_i\bigr),
\]
去重后至多 5 个合法整数值。将 donor 区、初始状态和 receiver 区分别看作函数仿射的整数片段。检查并证明（或给出精确反例）：

\[
\mathcal H_i=
\operatorname{conv}\{(a,m_i(a),v_i(a),g,ga):
a\in\mathcal K_i,\ g\in[\alpha,\beta]\}.
\]

应给双向构造：同一仿射片段内的内部整数状态可用两端点插值，并保持同一个 g；选定端点后的 g 线段也可按端点组合。对应连续 perspective 表示为
\[
\sum_{a\in\mathcal K_i}t_{ia}=1,\quad
Y_i=\sum_a a t_{ia},\quad
M_i=\sum_a m_i(a)t_{ia},\quad V_i=\sum_a v_i(a)t_{ia},
\]
\[
\alpha t_{ia}\le q_{ia}\le\beta t_{ia},\quad
\sum_aq_{ia}=g,\quad Z_i=\sum_a a q_{ia},\qquad t_{ia}\ge0.
\]
其中 M_i、V_i 可直接作为 aggregate service/visit 表达式，不必新设列。“至多 5 个”只指这一连续断点块的支撑数；加上 D3 的整数精确层后，总编码仍为 \(O(\log C_i)\)，不能声称整个模型与容量无关。

如不额外扩大工作量，可核查一个有明确范围的紧性结论：当 \(l_i\le b_i-2\)、\(u_i\ge b_i+2\) 时，五个断点在 \((Y,M,V)\) 中都是必要的图点生成元；\(b_i\) 是唯一 \(V=0\) 点，另外四点构成 \(V=1\) 面的四个顶点。该结论只限于“从合法库存图点选取生成元”的表示类，不是任意扩展式的复杂度下界，也不独立构成 OR 原创性主张。

进一步写清可复用的条件：一个有限整数状态 y 对外只通过 y、gy 和一组分段仿射函数 \(\psi(y)\) 可见时，保留每个共同仿射片段的合法端点即可表示该局部连续凸包。所需连续支撑依赖片段数，而非原状态数。说明这是标准析取构造的具体应用/推论，并定位本项目实际新建立的对象与嵌入。

覆盖 l=u、b 在域内/域外、域只有一侧、零/固定 g、初始库存为 0/C、缩紧后不含初始状态及 empty domain。空域必须保留原 infeasibility 语义，不能把存储范围 reset 误当物理域复活。五点结论仅适用于上述函数和连续整数区间；存在孔洞或新增 state-dependent 函数时，必须重新定义合法支持与分段，不能补齐非法整数或遗漏新断点。

### D3. 凸包压缩不等于整数模型精确：保留独立乘积层

**禁止仅保留连续断点权重和整数 Y，就宣称已获得精确 gY。**例如 b=0、库存域 `{1,2,3}`、断点 `{1,3}`、g 的合法区间 `[0,1/2]`，取 Y=2、g=1/4、t_1=t_3=1/2、q_1=0、q_3=1/4，得到 Z=3/4，而 gY=1/2；服务方向、访问和 Y 均可已整数。反之，把断点 t 声明为 binary 会删除合法内部整数库存，也不正确。

本轮唯一拟实现方案：保留原 P 的**绝对 Y 二进制精确层**，避免新增 offset 编码接口：
\[
Y_i=\sum_h2^h b_{ih},\quad Z_i=\sum_h2^h w_{ih},\quad
b_{ih}\in\{0,1\},\quad w_{ih}=g b_{ih}
\]
用原有正确的 binary-continuous 产品线性化及合法区间界实现，保留当前 Y 域、服务与其余约束；再用 D2 的连续断点块替代逐值 s/q 与 A/B。固定域的数学退化可按统一代数规则处理，不基于实例名选择编码。**不再试另一种 Gray/LOG/offset/混合编码。**

分别证明：

1. 每个旧整数物理解能构造新 bit/product 与断点权重，保持原 g、原目标和所有物理列；反向通过精确 gY、原 binary 访问/方向、unique service、integer inventory 与 balance 得到相同物理可行域。
2. 记位产品层的连续松弛为 \(P_{\rm bit}^{LP}\)。其 \((Y_i,g,Z_i)\) 投影包含所有合法真图点，因而包含 \(\pi_{Y_i,g,Z_i}(\mathcal H_i)\)。位层与断点层的辅助变量分离，且只共享 \((Y_i,g,Z_i)\)，因此两层联立后在 \((Y_i,M_i,V_i,g,Z_i)\) 上的投影仍为 \(\mathcal H_i\)。不能把该投影结论误称为新整数扩展式本身 ideal，或保证分支后的界/节点数相同。
3. 全局 LP 投影相等仅在其余约束/目标对被删 s/q 的使用完全通过共同接口时成立。给出该嵌入条件及当前 B 的逐类验证；局部 hull 不是整个路线模型或整数目标 epigraph 的 hull。

记录变量、二元变量、行、非零元随容量/合法域宽度的表达式。应预期共同 LP 投影相等而规模可能下降；这里的等价针对原始建模松弛、在求解器生成额外 cuts 之前，不保证 presolve/cuts/分支轨迹相同。**不能设置“必须先提高 root L”才能进入完整比较的条件。**更小模型也不保证更快，原生分支行为改变是实测问题。

### D4. 真实实现依赖与作用边界

重点读取实际 source 中的 `CplexBaseline.cpp`（共同模型 writer）、`IntervalRowFactory.cpp`、`MipStartMapping.cpp`、`PaperExternalGiniTree.cpp`、`GurobiBaseline.cpp` 及参数/模式校验。文件名含 Cplex 不表示正式实验应改用 CPLEX。

- 当前 writer 的 `vd-p/log-vd-p/vd-j`、`m-binary`、continuous quantities 和 factory bit-row 过滤相互关联。用一个明确的新研究模式接入，不能伪装成 `vd-p` 绕过校验后遗漏 bit 列/行。
- 查清所有逐状态依赖。R135 AP、R140 count、R141 selector、R143/RN、CDF、theta、linked-direction、VD-J 等若未被证明兼容，则本轮保持它们关闭，并对不兼容组合明确报错；不能静默忽略或删除它们。主线当前本就未启用的功能不构成本轮必须完成的重构。
- 保留原物理约束、所有启用 cut/row、SCF/MTZ、原 P/e/H/S 结构及 cutoff；不借编码更换同时做方向投影、penalty 重构、资源强化或分支优先级调参。
- Start 必须完整映射到新列。绝对 bit/prod 可复用既有正确逻辑；断点 t/q 需根据合法物理 Y 在对应仿射片段内构造，并使 q=g t。完成所有列、边界、类型、行和原目标检查；不能因为旧 mapper 只支持 one-hot 而关闭 C166 的 own Start。
- LP→MIP 类型恢复、模型缓存/fingerprint、epoch/cutoff/区间标识、child/target/terminal 各路径、最终物理资格与 lower-source 资格均承认新表示身份。不复用旧矩阵的 opaque 原生状态或 proof source。
- B 默认关闭候选时，canonical 导出应保持旧语义和未受影响行；小型同域导出可做差分。新共同构建中的 B 和 C166 使用相同其他源码/参数。

理论结果先得到可检查的推导与至少一次独立数学复核，再进行正式完整批次。该复核检查具体对象/映射，不要求新增外部审批；用户已授权本轮正常研究与 Draft 交付。

## E. 有限诊断、唯一完整比较与计费

### E1. 诊断与资格：最多 1h

先固定诊断清单和调用上限，所有 Optimize 通过 C++ driver；总研究诊断 Optimize 调用最多 120 次、外层计算最多 3600s，已有独立精确小例/检查器优先复用。逐次统计实际 native Optimize，而非只统计顶层 driver/fixture；小例的内部重建、资格或枚举子调用如调用优化器也计入。建议上限分配为局部 LP 64 次（最多8配置×4表示×2个固定目标）、六 root/两 child 的成对 LP 16 次、其余 tiny/native 最多40次；可在固定清单中重新分配，但合计仍不超过120次。诊断回答等价与接口问题，不能用随机目标匹配代替代数证明。

必要内容：

- 无 solver 的整数状态/断点双向映射与上述失效小例检查；覆盖 D2 的退化情形及一个合法内部非断点库存。
- 少量固定局部 LP 比较，检查完整 one-hot joint、断点 joint、带 bit 精确层的断点 joint，以及独立 product/service 参考之间的已推导关系。目标和测试域先固定，不搜索有利 root；最多 8 个边界配置、每模型少量明确目标，预算内完成。
- 至少一个原生完整小模型实际调用 MIP，最优物理库存含非断点值；使用已有可枚举物理小例或手算最优值，不能只靠两份同源实现给出同值。另覆盖非零目标、S=0/独立零证明、loaded return 和区间/截止边界中实际受改动的路径。
- 在 R163 六固定输入上各比较一个同域 canonical root LP；再选两个按确定规则得到的 child 区间/epoch 样本验证重建。使用同一已验证 U/cutoff 的离线框架可以，但不把该框架的免费 H/已知界用于正式性能样本。报告原目标、LP qualification、signed 差值与 row/column/nonzero counts。
- 检查 source、argv/模式、DLL、Start、类型恢复和实际 native 求解参数；数值等价判断用现有资格政策与残差，不放宽旧容差。存在实质 LP 差异时先确定是否遗漏函数/行/域或发生不安全数值改变，不能把“更强”当作压缩自动成功。

### E2. 完整批次：仅 B 与 C166

在数学条件、实际 writer/Start/Native 路径及必要诊断通过后，**执行且只执行**下面一次正式批次；不要求试跑已显示加速，也不因某个输入慢就跳过该行。若候选与历史实质等价且没有本轮新的表示/问题，或未能实现声明的精确等价，则不进入该批，直接交付具体研究结论。

| 固定 R163 配置 | Seed | 两个方法 | 每方法原完整 cap |
|---|---:|---|---:|
| C20-S | 0 | B / C166 | 1200s |
| B20-B | 0 | B / C166 | 1200s |
| X20-S | 0 | B / C166 | 1200s |
| C35-U | 0 | B / C166 | 2400s |
| B35-S | 0 | B / C166 | 2400s |
| X35-S | 0 | B / C166 | 2400s |

以 R163 `input_manifest` 中完整 input ID、内容 SHA、T/lambda/weights/Q/车辆数为准，不凭这些短别名重新生成输入。全部六配置都已经暴露，本轮是编码比较，不是独立新实例验证。一次冻结 12 臂、顺序、版本、参数与评价规则；建议按固定输入顺序交替 B/C166 的先后，顺序不由历史胜负决定。

由于新增候选需要编译，共同构建本轮 B 与 C166，**运行新的成对 B 控制**。历史 R163/R164 B 只作背景，不替代这次严格配对；同一次新的 B 不因另一个 reader 出错而重跑。全部正式臂串行、Threads/MIPThreads=1，不与其他 solver 或重型计算争抢资源。沿用 Gurobi13.0.2、native 默认策略、原 numerical contract、requested gaps0；不能误带开发用的 4096 节点上限。

每个方法独立执行并支付完整 H，H seed 固定 `20260626`；Gurobi Seed0 必须传到所有 native 调用及后继模型。原 B 的 S2/ms2、M-B、pair-only、AM .08、max depth8、min width1e-4、AP off、inclusive cutoff/source/zero 政策不改。裸 CLI 的 ENS-C 默认不能冒充 B。C166 只替换 D 中的表示，维持原完整算法流程。

不使用 C 部分的跨权重档案、历史优质 fleet、其他方法解、离线 LP 或库存 lower 作为免费 Start/hint/cutoff/floor。正式运行日志、输入和候选资格可以引用历史证据，但生产搜索中的信息必须由该运行自身取得并计费。

### E3. 判断标准与成本

预先报告并最终逐项回答：

1. 整数物理投影、共同 LP 投影及全模型嵌入是否成立；缩减的变量/行/非零元和构建成本是多少？
2. 完整 CERT 数、各配置 U 和 L、完整生产/验证成本如何变化？OPEN 的 T_cert 为空，不以 cap 代替收敛时间。
3. 只在双方合格 CERT 交集报告证书时间比，注明分母；沿用 `max(10s,0.1×faster time)` 的实质差异尺度。其他小差异如实报告，不临时调阈值。
4. 若 LP 相同而 MIP 更快/更慢，依据实际构建、根处理、节点/Work 和轨迹说明观察到的差别；不能以更少变量或节点直接证明速度机制。原生分支轨迹不同不否定共同 LP 投影。
5. 允许有取舍，不设“每一个实例都必须更快”的单点否决，也不按实例挑选 B/C166 组成 portfolio。用完整面板决定：有潜力需后续确认、收益有限/混合、或不值得替代。单 Seed 结果不晋升为普遍稳健性结论。

`T_produce` 包含 H、构模、所有 native/辅助调用、在线资格和收束；必要事后核验单列 `T_verify`，完整外层费用计一次。Runtime、Work、H 子阶段等只用于解释，不与外层重复相加。物理 T 与计算 cap 分开；资源 reservation、producer deadline 与 fault watchdog 分开。已有 cap+300 reservation / cap+900 watchdog 只是调度保护，不得延长 producer 的评价预算。

健康 producer 的 reader/图表错误只读修复；保留失败文件、修复原因与费用。因真实正确性/数值资格问题中止，准确记录已执行/未执行位置；因性能不好不换 Seed、换输入、换第二编码或重新启动同样实验。所有合格、失败和未完成位置进入结果表。

## F. 合并科学结果、维护稿件与当前 PDF

保持当前权威组件：`paper_body.md`、`model_and_algorithm_appendices.md`、`mathematical_analysis.md`、`supplement.md`、`references.bib` 与 figures。复用 R165 已工作的 `scripts/round165_documents.py` 或其明确继承入口；不重跑会覆盖当前内容的旧 R137 生成器。

压缩研究完成后，根据实际证据决定进入主文/附录的程度：

- 成立的局部/全局表示结果写成准确命题，清楚区分标准构造、当前模型应用与已证明的推广条件。
- C166 有完整运行时独立命名报告，不能重写历史 B 身份，也不因一次新结果自动改 main/released default。
- 若无计算优势，保留规模/信息保持结论和真实负结果，正文不过度扩展失败过程；研究细节在补充或科研目录。
- 参数方案包络与连续区间质量界直接进入实验解释或决策分析，配一张能区分可行上包络、合格下界与原采样点的图。不得把所有曲线都画成已知精确最优曲线。
- 当前大表可放补充；正文表格用合适精度，原 binary64 与 source 保留。研究编号、hash、文献访问日志和审计过程留在复现材料，正文聚焦问题、方法与发现。

使用同一当前源生成 manuscript.md、主 PDF 与 supplement PDF；页数随内容合理变化，不以 R165 的52/39为配额。顺手把 PDF 缓存身份纳入日期、模板/header 与实际工具链，或明确本轮内容变化后强制一次正确导出，避免未来跨日缓存身份不一致。

必要 QA：维护组件—组装稿—PDF 身份一致；图表与机器可读结果一致；没有缺图/未解析引文/断裂关键引用/截断宽表/公式溢出/异常空页；实际看摘要、方法新命题、新图表、主算法与附录/参考文献连接。只对变化与具体风险补查，不重跑全部历史资格或反复渲染无差异文件。

## G. CSV、证据与可复现交付

### G1. 用户主表

已整理的权威 `GI_TBC_vs_P_GRB_All_Tested_Instances.csv` 为106行、28列、UTF-8 BOM、60,603 bytes，SHA256：
`8f39e3a23b3b6df621139cb39b4db813ca3e992da091e97251ab8337fd2b0022`。

在实际附件/配置入口做一次有限定位；有该完整版本即保留作为基准。103行 R164 工作副本不能覆盖106行主表；差的三条是 R138 R-B35-S-T2 Seed1/cap2400、R155 N-B35-S Seed0/cap7200、R156 R-X35-S-T2 Seed0/cap7200 的旧 N/A-P 记录。没有完整附件时继续完成科研，交付准确 reconciliation 与独立增量；不虚构找到原表，不反复扫盘或请求用户。

本轮参数重评、资源差值、LP/小例、C166 结果均独立成分析/变体表，不能成为“新增 GI-TBC 对 P-GRB 胜例”。若 E2 产生6条新的完整 B 控制，可按主表既有 N/A-P 语义追加并标明新的 source/build/run；P 字段保持 N/A，不借旧 P 拼成严格配对。若现有 schema 无法清楚区分重复控制与既有同 key 记录，保留独立增量和映射、不覆盖旧行；不要为容纳候选而擅改28列语义。C166 从不改称 B。

最终明确区分：新增独立物理输入数、新 Seed 数、新运行/配对记录数、新的 B/P 优势证据、离线决策结论和候选结果。正式批次若执行，本轮仍是0个新物理输入、0个新Seed、最多12个新完整运行、6个 B/C166 配对；没有新的严格 B/P 对照。未执行正式批次则通常无主表新增数据。

### G2. 必需成果

`results/unified_exact_round166/` 至少交付以下内容，可合并相邻普通记录，避免制造重复文书：

- `goal.md`、`research_design.md`、`source_manifest.json`：当前身份、排重、具体科学对象、冻结矩阵与来源；
- `compression_theory.md`：共同投影、断点命题、整数精确层、全局嵌入、适用边界/反例、规模公式和近邻归属；
- 候选 C++ 源/配置/构建与复现入口，或确切不能成立/集成的证据；
- `qualification.json`、必要小例与 LP 比较表、Start/类型/行读取检查；
- `decision_analysis.md`、物理方案档案、参数上下界/交点/区间误差数据、资源分析与相应图；
- 若 E2 执行：完整12位置结果、B/C166配对表、源/PE/DLL/命令、完整 fleet、关键轨迹、费用、失败/未完成说明；
- `contribution_positioning.md` 与 `author_decision_memo.md`：哪些内容现在支撑 EJOR/TRE，OR 深化实际新增了什么、是否还存在具体研究缺口；
- 实际修改的当前论文组件、数学/算法附录、references、组装稿和两份当前 PDF；
- `final_report.md`、`decision.json`、CSV reconciliation/真实增量、构建/QA与独立审阅结果。

阶段结论分别回答：现有 B 是否继续作为默认；C166 的数学关系、实际费用与采用建议；参数分析能证明哪些连续区间结论；当前论文的主要科学贡献及其与 HGA 的增量；OR 方向的增量属于标准工具应用、可迁移结构结果还是有证据的算法推进。不能用“完成了很多审计”代替回答。

## H. 独立复核、正常 Draft 交付与停止

在完整成果形成后安排三个实际独立复核，允许并行阅读但不与正式计时求解争抢重型计算资源：

1. **数学/模型复核：**挑战断点局部 hull、bit 精确性、共同投影与全局嵌入；检查原 A/B、e epigraph 和所有 state-dependent 接口；核对标准工具与历史差异、参数凹性/上下界方向和数值范围。
2. **实现/数据复核：**检查 C++ 新模式、所有语义列映射、LP→MIP、source/cache/epoch、同构建配对、运行矩阵/计时、方案物理验算、CSV及参数来源。
3. **研究贡献/成稿复核：**实际读当前成稿，确认 EJOR/TRE 主张已进入论文、OR 对象有真实结果；检查有没有把已知凸包压缩/参数凹性冒充一般突破、把离线档案当生产加速、或为外层/候选只保留胜例。

每份复核给出具体位置、影响和处理结果。修真实错误并定点读回；不因微小文字修订反复跑整批 solver。独立代理不可用时披露实际替代方式，不虚构 reviewer。未解决的科研限制保留，不要求把所有机制变成正结果才允许交付。

正常 commit/push，创建**英文 Open Draft PR**，建议标题：

`Round166: study compact shared-state formulations and certified decision trade-offs`

首段写清问题、实际新增知识和最终论文变化；区分理论/实现、正式运行、离线分析及主表变化。按 A 选择 main 或 R165 stacked base，读回 head/base/Open/Draft 与当前稿件链接。用户已授权此类正常工作与 Draft 交付，无需逐项再次请示。不要自动 merge、force-push、删历史分支或向外部作者/期刊发送内容。

只对本轮新增/变更的源、文稿、图与必要证据做一次公开取回/字节核验。旧 carrier 固定引用，不重下/重打包82k成员的历史集合。新 raw 对象若需要包，使用新内容专属包和 member map；不发布商业 DLL、许可证、凭证或私有前稿。区分科学提交与随后 receipt 提交，不填写尚不存在的 self-SHA。按 WORKSPACE_POLICY 仅清理本轮可重建且已恢复覆盖的重复临时件；零删除允许。

**验收必须同时看到：**一份贡献更鲜明且包含新的可认证参数结果的当前论文；针对局部状态压缩的可检查数学与实际范围结论；条件满足时一个完整 C++ 候选和固定配对结果；正确保留原 B、历史正负证据与 CSV 身份；独立复核后正常 Draft 交付。完成后停止，不自动启动 Round167。

## I. 固定来源与查阅入口

- [R165 / PR227](https://github.com/yifanXovo/TailoredExact/pull/227)，delivery `239db6a80c944f1e7b5a55504ce5202ea35c2586`；`results/unified_exact_round165/{goal.md,final_report.md,decision.json,contribution_positioning.md,author_decision_memo.md,literature_review.md,document_build.json,document_qa.json,source_manifest.json}`；`scripts/round165_documents.py`。
- 当前继承 head 的 `results/unified_exact_round137/{paper_body.md,model_and_algorithm_appendices.md,mathematical_analysis.md,supplement.md,references.bib,source_publication.json,reports/operations.json}` 及实际引用的权重/资源原表。R134 权重/operations 原证据按现有固定 source map 读取；当前 supplement S3 的舍入表只是导航。
- R55：`results/gf_k1_am_sf_station_state_chain_round55/`；R67：`results/unified_exact_round67/{final_report.md,mathematics.md,lp_projection_attribution.md}`。R98–107、R130、R132/133/135 对应 final_report/数学入口按 B 定向读取，不全量重放。
- 当前实际 writer/映射：`src/{CplexBaseline.cpp,IntervalRowFactory.cpp,MipStartMapping.cpp,PaperExternalGiniTree.cpp,GurobiBaseline.cpp}` 与相应 headers/options；`config/{gi_tbc_round137.json,paper_s2.json}`。
- [R163 / PR225](https://github.com/yifanXovo/TailoredExact/pull/225)，delivery `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`；固定六输入的 input/candidate/environment manifest、完整 B/E+/P 结果与物理方案。
- [R164 / PR226](https://github.com/yifanXovo/TailoredExact/pull/226)，delivery `de01e8fb27a954d031abac5fe99442d6c8d29d44`；数值快照 `b93a8a01ff1b7f3cbee67807be3ac6591db4767f` 下 `reports/complete_arms.json`；12行旧增量从 science `a29a70d132ecc17e18bc48a660225a6380722f45` 或 delivery 取。历史 carrier 51,931,501 bytes / 82,561 members，仅按索引取必要成员。
- 主要数学原文：[Gupte et al. 正式版](https://www.pure.ed.ac.uk/ws/files/137476899/110836183.pdf)；[Köppe et al. 作者稿](https://arxiv.org/abs/math/0603311)；[Vielma embedding 作者稿](https://juan-pablo-vielma.github.io/publications/Embedding-Formulations-and-Complexity.pdf)；[Huchette–Vielma piecewise-linear 作者稿](https://optimization-online.org/wp-content/uploads/2017/07/6148.pdf)。准确区分版本与实际读到的命题。
- 官方定位：[EJOR](https://shop.elsevier.com/journals/european-journal-of-operational-research/0377-2217)、[TRE](https://shop.elsevier.com/journals/transportation-research-part-e-logistics-and-transportation-review/1366-5545)、[OR editorial statement](https://pubsonline.informs.org/page/opre/editorial-statement)。本轮不开展投稿或对外联系。

最终回复提供本轮科学发现、B/C166实际决定、参数/资源结论、当前稿/PDF、CSV实际变化与 Draft PR 链接，清楚说明哪些问题已经得到答案，哪些具体问题仍值得继续研究。
