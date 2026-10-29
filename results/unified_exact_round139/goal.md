/goal

# TailoredExact 下一轮完整任务清单

## Round139：库存乘积加强的放置位置、控制路径与完整求解收益

**日期：2026-10-29（Asia/Shanghai）。建议轮次：Round139；编号已占用时沿实际下一轮继续。**

## 0. 目标、优先级与自主权

R138 已完成共享库存产品的数学研究和有限完整算法比较，可以验收。四条库存 RLT 对四个同域根均有原目标界增益，在 K15/K20 等配置有实质完整收益，但部分 n35 配置存在重要 U/L 回退，故 GI-TBC+stock-RLT 保持 research-only，R137 GI-TBC 仍是稳定入口。

本轮研究主问题：**资源一致性加强应作用于外层 LP、原生 MIP，还是二者，才能保留有价值的证明收益并减少重要回退？** 同时明确加强如何改变 AM 决策及实际原生搜索。不要预设 LP-only 必胜，也不要将本轮写成另一轮全面稳定性、AM 调参或数值修复任务。

主要交付：

1. 从已有真实调用、矩阵和日志解释 R138 收益／回退中已经能够识别的因素。
2. 给出不同统一放置方式的正确性及界传递说明，实现最小、可核实的研究配置。
3. 完成少量关键角色的放置比较；有依据时，选一个统一候选补齐现有八配置面板。
4. 形成明确的采用／继续研究／停止决定及可并入论文的研究说明。

Codex 可根据实际结果调整小范围角色、实现方式、诊断顺序和探索内容，在 **16 小时新增实验计算总上限**内自主调剂。默认主要新完整运行的名义 cap 合计约5.33小时，另有资格、有限 Seed1、探索及余量；不要求用满。

**所有未明确安排多 Seed 的新求解，显式使用 Gurobi Seed=0；有限第二 Seed 使用1。** H seed 固定20260626，单独记录。包括资格、同域 LP/MIP、完整运行和额外探索；纯离线解析不虚构 Seed。

统一算法规则应有数学或结构依据：不按实例身份打补丁、不按大小准备两套算法、不以运行若干秒后切换方法或 leaf 作为算法步骤。按外层 LP／原生整数求解的数学任务统一放置行是允许的研究方向。实验时限、物理 T 和观察性时间记录不属于算法切换规则。

正式比较先登记实际输入、物理参数、目标、版本、placement、Seed 和 cap。允许根据已观察结果选择后续实验，保留选择理由与普通不利结果；不要包装成未见独立验证集。计时求解保持单线程、串行，编译、重 I/O 与 PDF 导出错开。

---

## A. 实际起点与已经成立的事实

### A1. 继承 R138，保留稳定 GI-TBC

| 项目 | 编写本 goal 时已核参考 |
|---|---|
| 仓库 | yifanXovo/TailoredExact |
| R138 PR | #200，open／Draft，base 为 R137 分支 |
| R138 branch／head | codex/round138-shared-product-resource-coupling；d606062edddf58c13a7c3acb48e896fc787ff856 |
| R138 固定 science | 1b19897ab5819ab3b7485ddc978954b45225f361 |
| R137 PR／head | #199，open／Draft；72fdcd31716d7b4798727b4ea964b32059c630d1 |
| 当时 main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 稳定入口 | scripts/paper_s2.py → config/gi_tbc_round137.json |
| R138 独立研究入口 | scripts/paper_s2_stock_rlt.py → config/gi_tbc_stock_rlt_round138.json |
| 已修复 V2 源码 | 04506fa613446d2ef2bd19794f778909422c51fd |
| 活动树／资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work\ |
| 原受保护目录 | E:\codes\ExactEBRP，保留历史状态和用户修改 |
| 建议 branch／结果目录 | codex/round139-stock-rlt-placement；results/unified_exact_round139/ |

执行时读取适用 AGENTS.md、WORKSPACE_POLICY.md，核实 refs、未提交工作、进程和实际资产。main 已吸收 R138 时从实际 main 继续；否则从核实后的 R138 分支继续，Draft PR 临时以该分支为 base。仅吸收 R137 不代表已包含 R138。不需要为了启动研究先请求合并 #199/#200，不机械回退参考 SHA。

基线沿用完整自身 H、M-B/VD-P、pair-only、AM=.08、depth=8、minimum width=1e-4、AP off 及 R134 数值／证明政策。首轮放置比较保持 TC off。保留稳定和 R138 研究入口、冻结配置、PE及结果身份；新增研究配置默认不改变它们。

### A2. 接受并复用 R138，避免重新证明或重测

R138 已完成：连续库存产品块的公共因子凸包；指定完整 J2/J3 参考上 TC 与 stock 的互补及组合闭 gap；在所声明连续域上的 stock／shared-GS／independent-GS 条件包含关系；20个同域 LP；八配置主比较、有限 Seed1 和13页研究增量稿。

四个根的 stock 增益分别约为：K35 0.0179111、RX20-T1 0.0459632、RX35-T2 0.00703632、K20 0.00944129。完整获证数为 BASE 2/8、STOCK 3/8；K15 112.77→33.82秒，K20由cap1200 open变为101.64秒获证。RB35-T2 Seed0的 U 明显回退，Seed1方向反转；K35和RX35-T2保留相反的 U/L 端点变化。

V2 已修复新增行极小系数在 Native 导入时被丢弃的问题，方法为局部正二次幂整行缩放。七域 Native 检查和25个唯一已用V1模型／33次调用的桥接支持保留原主实验。V1主表仍是V1；V2 Seed1是有限第二 Seed兼构建确认。本轮复用修复，不开启新的全平台数值工程，也不因V2身份不同机械重跑主表。

Handling 产品已有四个保存最优点的非违反记录；其中 RX20／RX35-T2 满足可证明冗余的充分条件。普通 GS、AP/IND、AM网格以及 root-only 删除控制都有历史。本轮只读取与新问题有关的资料，不遍历或恢复全部旧 PR/raw。

### A3. 本轮必须修正的研究起点

已检查的调用结构：

| 角色 | R137 BASE | R138 STOCK |
|---|---|---|
| K15、K20、RX20-T1、RB35-T1 | 3 LP＋1 target MIP＋1 terminal MIP | 3 LP＋0 target MIP＋1 terminal MIP |
| K35、RB35-T2、RX35-T1、RX35-T2 | 3 LP＋0 target MIP＋1 terminal MIP | 3 LP＋0 target MIP＋1 terminal MIP |

八个 STOCK 都没有 split，均由 no-strict 进入 exact-close。八组 BASE/STOCK 的 H车队、H语义、初始域和目标身份相同，因此不能将正反变化解释成初始H质量不同。

R138报告提出的“120秒 target-MIP 检查首次解延迟”只是下一步建议，不是已完成实验，也不是本轮必须照做的路线。真实高成本路径首先是 **terminal/exact-close MIP**。

已有原生日志进一步显示：

- RB35-T2：STOCK首次原生改善约59秒，BASE约79秒；随后多次交叉，BASE约455秒明显改善，STOCK约591秒达到最终约0.40120后停滞，BASE到末端约0.34464。
- K20：BASE的target仅约0.33秒且没有新解；STOCK约40秒找到最终质量附近方案、98.82秒原生闭合；BASE约205秒达到最终质量附近，但末端仍未闭合。其terminal还记录了前序求解的MIP Start。

这些是日志中近似时间和原生模型目标，不是每个中间点都已独立物理验证的U。它们足以否定“首次解必然更慢”及“仅省掉target直接耗时”的简单解释，不能据此精确分摊收益来源。

---

## B. 必要数学分析与可识别的研究问题

### B1. 放置方式的正确性

令 D 为当前真实库存支持、Gini区间、物理参数等定义的域，\(X_D\) 为原整数可行完成，\(R_D\) 为现有连续松弛，\(C_D\) 为使用该域实际端点的四条库存 RLT。由R138有效性，

\[
X_D\subseteq R_D\cap C_D\subseteq R_D,
\qquad X_D\cap C_D=X_D.
\]

所以同域最小化满足

\[
L_D^{\rm base}\le L_D^{\rm stock}\le z_D^*.
\]

LP使用加强表述、MIP使用原表述仍然精确；反向放置也不改变整数可行集合。整数产品有效性不要求将辅助g强制等于真实Gini。论文中保留R138的域与连续／整数结论边界。

若实际LP仅求解改进域 \(f\le c\)，下界为\(\ell_{D,c}\)，不能无条件提升为更大域的界。完整域按两部分分解后，可用

\[
L_D^{\rm LP}=\min\{\ell_{D,c},c\};
\]

改进域不可行时使用cutoff补集给出的界c。沿用现有R120/R134的证据和数值政策，维护

\[
L_D=\max\{L_D^{\rm LP},L_D^{\rm MIP},L_D^{\rm inherited}\},
\]

再由完整frontier覆盖组合全局界。源域包含目标域时才可直接下传界；由子域推父域须有完整覆盖。LP外部证据不得冒充原生MIP返回的bound。无需新建另一套证明账本。

### B2. 更强LP不保证相同或更积极的AM动作

在两个子域均有限有效的情形，令父界为\(L_p\)、两子界为\(L_l,L_r\)、已验证上界为U。当前AM使用

\[
d=\max\{U-L_p,\epsilon\},\quad
r_i=\operatorname{clip}_{[0,1]}((L_i-L_p)/d),
\quad \eta=\min(r_l,r_r),\quad\mu=(r_l+r_r)/2,
\quad S_{AM}=\eta\mu.
\]

先判断是否存在严格最弱子界改善；没有则exact-close，有则再按既有阈值决定split或native-target。逻辑不可行子域沿用既有单独处理。

加强后即使\(\Delta_p,\Delta_l,\Delta_r\ge0\)，仍有

\[
(L_i+\Delta_i)-(L_p+\Delta_p)
=(L_i-L_p)+(\Delta_i-\Delta_p).
\]

因此父界提升得更多时，边际子域收益可能缩小或归零；归一化分母也改变。表述强弱关系不推出AM分数或动作的单调关系。

K20实际首个决策提供明确实例：

| 表述 | 父界 | 左子界 | 右子界 | 首个动作 |
|---|---:|---:|---:|---|
| BASE | 0.195149152441 | 0.196078259949 | 0.540770654572 | native-target |
| STOCK | 0.204590439178 | 0.204590439178 | 0.540770654572 | exact-close |

BASE的AM分数约0.00047847，小于.08；STOCK在no-strict判断已进入exact-close。本轮先解释这一实际结构交互，不通过扫tau来替代解释，也不将上述公式本身夸大为新的通用算法理论。

### B3. 两种作用位置及比较含义

| 代号 | 外层显式LP使用stock | 原生整数求解使用stock | 角色 |
|---|---:|---:|---|
| BASE / 00 | 否 | 否 | 已验收GI-TBC |
| BOTH / 11 | 是 | 是 | R138统一候选 |
| LP-only / 10 | 是 | 否 | 新候选：保留外层加强及其控制作用 |
| MIP-only / 01 | 否 | 是 | 新候选／机制对照：保留整数求解中的加强 |

这里“外层LP”是控制器显式调用的根／子域松弛；“MIP”包含target、terminal及其内部根松弛和搜索。LP-only不表示只在原生MIP内部根节点开行，MIP-only也不表示内部LP完全不含行。四格均采用全实例统一规则。

保持AM规则、H和其余组件不变，观察placement干预后的完整路径。四格可以揭示交互，但不是可加的运行时间收益分摊；前序求解状态、模型重建和Start变化要如实列出。未获证时间是截尾，不能强行填cap计算精确加速比。

LP-only也可能近似退回BASE：若两者进入相同terminal域，而后续原生界已经高于保留的stock根界，外部根界不再控制末端L。例如RB35-T2的stock根界约.12915，低于BASE末端约.21899和BOTH末端约.22918。不得预设LP-only同时继承BOTH的末端L和BASE的U。

---

## C. 最小实现与实际模型资格

新增显式研究placement，可用统一枚举或两个开关，具体接口由Codex选择。既有无stock行为和R138 all-placement行为保持可用；旧 `--round138-stock-rlt` 的语义不悄悄改变。主比较仅改变stock放置。

当前LP、target和terminal共用leaf/epoch的canonical artifact，LP结束只恢复变量类型，并不会删行。因此不能只改VType或在target路径关开关，却让terminal继续携带旧四行。

实现可采用分别可追溯的LP/MIP artifact及显式discard／重建，或经过核实的等价最小方案。重点核查：

- 根、子域、cutoff刷新以及实际target／terminal调用中的行存在性与变量类型；加强域端点正确，无重复行。
- canonical身份、retained model和cache与实际矩阵一致；旧已求解artifact保持不可变，不能换矩阵后沿用旧SHA。
- LP下界按B1保留，MIP使用声明的矩阵；原生bound与外部合并界分开记录。
- 00/11与既有BASE/BOTH的必要等价桥接；重建、Start映射和失去模型复用的成本计入完整方法。
- Seed0在preset之后生效并覆盖原生子调用，H seed保持独立。

复用V2行系数和Native检查，不重新开发缩放策略。对新placement路径做有针对性的导出／Native读回、代表性root-child-refresh和小型完整检查即可；不得用放宽容差、补写bound或重标旧实验解决实现错误。

可借鉴历史R63的MIP-only行生命周期和R120的artifact替换／discard经验；先读实际实现。这些不是已经完成的stock placement。R137的s2-root是关闭外层probing，也不是本轮LP-only。避免大规模重构。

---

## D. 先利用现有证据，再做有限完整比较

### D1. 已有轨迹与必要的同域诊断

优先读取R137/R138的实际矩阵、AM及optimize ledger、Native日志、Start记录和最终物理解。先覆盖K20与RB35-T2，必要时补K15／K35。核对去掉四行后哪些共同矩阵、域、cutoff、H输入和实际参数相同，哪些原生调用／复用状态不同。

R138的global trace多数bound记录在Native返回后获得资格，控制器U也可能只在返回后更新；不要将它们的发布时间解释为solver首次发现解的时间。原生日志中的rounded incumbent是原生目标。正式物理U仍来自完整验证；中间向量存在时可离线验证，没有则明确该层信息未记录。

有需要才补同域整数诊断，默认最多两个角色、每角色有／无stock两种矩阵、每次约600秒，计入G预算。对准实际terminal/closure，保持真实域、cutoff及明确一致的Start政策；实际共有H Start可作为固定子问题共同输入。若采用冷启动重放，应说明它没有重现前序Native状态。无需默认去掉Start或构造未发生的target路径。

上述短测用于实现与特定机制识别，不能据120秒或600秒的单一截面判定完整优劣。已有RB35-T2多次交叉，完整候选仍按D2/D3检验。若旧证据足以回答问题，可直接进入完整pilot，不要求通过一次新固定子问题测试才准入。

尽量复用现有日志与回调；确有必要时，增补少量原生incumbent事件／对应解记录，离线验证其物理目标。记录成本必须计入，不为细轨迹建立大型新框架，也不修改原有H、Start或停止规则来制造对照。

### D2. 三角色有限放置面板

默认关键角色如下，输入、Q、T、系数与R137/R138冻结记录一致：

| 配置 | 站点／车辆 | 物理T | 目标 | 完整cap | 作用 |
|---|---:|---:|---|---:|---|
| K-15-S | 15／2 | 3600 | lambda=.15 | 600 | 获证加速、控制路径变化、低成本控制 |
| K-20-S | 20／2 | 5400 | lambda=.15 | 1200 | 最强获证收益、target→terminal变化 |
| R-B35-S-T2 | 35／3 | 7200 | rho=1，原lambda=1/Omega | 2400 | 明显U回退、两者原本均直接terminal |

优先运行LP-only；为区分作用位置，在有信息的角色补MIP-only。默认预算允许三个角色各补两个新配置：

\[
2(600+1200+2400)=8400\text{ s}=2.333\text{ h}.
\]

BASE/BOTH合格旧结果作为两格参考，不默认再跑两份完整矩阵。若某格在实际数学模型及相关调用状态上可证明等价，或已不需要它回答主问题，可以省去并记录理由；不能用未运行格声称完整四格实验。若结果显示第二新配置更有希望，允许调整优先次序。

比较初始信息、父子界／AM动作、实际target与terminal次数、模型身份与复用、各阶段成本、Native搜索及完整证书／U/L。K20的target直接成本仅约.33秒，不能把约100秒对cap1200的差异解释为节省了这么多target时间。

### D3. 选一个统一候选补齐八配置

若D2出现值得保留的收益或可解释的混合边界，选择一个统一配置，补其余五个角色：

| 配置 | 站点／车辆 | 物理T | 目标 | cap |
|---|---:|---:|---|---:|
| K-35-U | 35／3 | 10800 | lambda=.15 | 2400 |
| R-B35-S-T1 | 35／3 | 4800 | rho=1 | 2400 |
| R-X35-S-T1 | 35／3 | 4200 | rho=1 | 2400 |
| R-X35-S-T2 | 35／3 | 6300 | rho=1 | 2400 |
| R-X20-S-T1 | 20／2 | 4800 | rho=1 | 1200 |

新增名义cap为10,800秒／3小时。加D2最多19,200秒／5.333小时；选中候选在D2已完成的位置不重复计费或重跑。若最终保留的是已有BASE/BOTH且完整结果仍可比，直接复用，不机械补跑五角色。最终仍是八配置、六基础输入，不是新增八个独立实例。

角色是覆盖关键行为的默认骨架，可有理由地小幅调整；不要按实例选不同placement后拼成“新算法”。没有有用候选时，D3不机械执行，以研究结论和剩余问题收束。若探索产生了另一套实现，不能继承前一候选的结果身份，应重新规划其必要位置及费用。

所有完整方法独立启动并支付自身H、构建、验证、求解与在线证明成本，不导入其他方法、Seed或诊断的解、界、Start或树。旧基线仅在输入、参数、Seed、cap、算法身份、环境与计时口径确实可比时复用；否则补匹配基线，使用机动余量。

### D4. 有限第二Seed

仅对最终影响决定的最多两个角色，按基线／候选成组补Seed1；可优先覆盖主要获证收益和重要回退。已有完全匹配的BASE/BOTH Seed1可复用并保留身份；新配置须实际运行。最大额度按两角色、两方法、各2400秒计，为9600秒／2.667小时。

这是结果选定后的有限确认，不是独立验证集或分布估计。无需给四格都补Seed1，不替换Seed0不利结果。没有需要复核的新变化时可以不执行；其他探索默认Seed0。

---

## E. 允许的额外研究

预留约3小时新增计算，可与其他余量调剂。主问题清楚后，允许Codex基于数据探索一个直接相关的扩展，保留其成本和版本。

优先备选是 **TC＋stock的有限结构检验**。R138中K20相对BASE的根增量为：stock约.00944129、TC约.00747610、二者约.02939287；组合比单独增量之和多约.01247548。RX35-T2在stock上另增约.00138575，K35/RX20无额外根目标增益。

因此可先复用现有点和少量有信息子域，研究TC是否改变父子界差异或实际控制路径，再决定是否做一个小型完整pilot。K20已被stock快速闭合，根界增量不能直接等同于新增实践价值；不立即复制八配置TC矩阵。

其他探索应与观察对应，例如一个统一、结构支持的placement简化或有明确新信息的资源表达。若要改变控制器或H，应作为单独候选，先解释与历史R47/R48/R119–122及R137控制的区别，不能混入主placement比较。默认不安排新的AM网格、广泛Seed/benchmark或已缺乏信号的handling重复试验。

没有有用信号时可保留清楚的下一问题，不要求为耗尽预算另找优化。负结果应具体说明机制边界，而非仅写“继续调参”。

---

## F. 结果组织、采用决定与论文增量

按三个层次报告：

1. **表述信息：**同域LP和既有理论说明什么；不要重新宣称R138的标准RLT工具原创。
2. **实际执行：**placement如何影响AM、target／terminal、模型复用、Native搜索；哪些只有相关记录，哪些有受控比较支持。
3. **完整表现：**证书、完整时间、受支持L、验证U和正反端点；不以较小relative gap掩盖较差U或signed gap。

延续既有T_produce/T_cert/T_verify/T_total口径，未获证的T_cert为null；Native日志时间是诊断时钟。双方获证的实质时间差异沿用 \(|t_1-t_2|\ge\max\{10\mathrm{s},0.10\min(t_1,t_2)\}\)，同时提供原始数值。不得将cap当成已知收敛时间。Work、节点、根界和首次解时间用于解释，不替代完整结果。

保留全部实际进入的配置、普通不利和open结果。若用四格交互表达，只对同一口径的指标计算并说明条件；不对截尾获证时间强行做加性分解。

最终可选择：推荐一个统一placement为后续主候选；保留BOTH或新配置research-only；或停止本轮候选。采用不要求每例最佳，但要看整体收益、重要角色和回退幅度，不能仅凭一两个漂亮时间或根增益升级。R137稳定GI-TBC始终可运行，R138科学记录保持原身份。

沿用R137完整稿及R138研究增量，交付一节独立可读的机制／方法说明、B的必要证明、实际调用对照和紧凑结果表图。更新受影响章节或研究附录即可；需要PDF时使用已有装配流程检查受影响页，不重写全部论文或重做无关历史图。

明确本轮对论文贡献的推进：是否从有效资源一致性进一步得到可解释、可用的统一使用方式；哪些仍是条件性观察。不能以一次小面板声称一般性能支配或达到某期刊录用标准。

---

## G. 预算与合理收束

| 内容 | 规划额度 |
|---|---:|
| 实现资格及必要同域terminal诊断；默认最多4×600秒诊断，另留资格余量 | 3600 s = 1 h |
| D2三个角色、最多两个新placement | 8400 s = 2.333 h |
| D3一个候选补齐其余五配置 | 10,800 s = 3 h |
| D4最多两角色成组Seed1 | 9600 s = 2.667 h |
| E有依据的额外探索 | 10,800 s = 3 h |
| **上述规划上限** | **43,200 s = 12 h** |
| 匹配基线、必要修正、追加确认和机动余量 | 14,400 s = 4 h |
| **新增实验计算总上限** | **57,600 s = 16 h** |

预计实际新增计算约6–10小时，取决于提前获证、基线复用和条件块是否有必要；不要求用满。小项可调剂，不因单个分项超出而人为BLOCKED。若某次诊断须延长，应有具体信息目标并计入总额度，不据短窗口未见收益否定已有中后程信号。

新完整运行按实际外层全过程计费，嵌套H／LP／MIP不重复累计；资格、失败原生尝试和探索均计入。旧基线在比较中保留原完整成本，但不虚构新增计算。阅读、构建、离线分析、文稿／PDF和归档单列实际开销，未精确计量的人工阅读不编造小数。

完成意味着主问题得到可审阅回答、已进入的比较完整报告、版本与证据清楚、稳定入口保留。若两新placement均无可用增量，可以停止扩大；若出现有用信号，应完成有解释力的完整确认，不能只停在LP或短测。真实实现错误与必要对照缺失要处理，不能写成负研究结论。

数值／平台问题采用有界定向修复，优先复用既有工具与已封存运行，不扩成长期审计。正常文稿／派生表修改不触发无关求解重跑。

---

## H. 独立复核

在昂贵运行前由不同于主要实现者的复核者检查关键数学和placement路径，收尾再复核整合结果。复核应聚焦：

1. B1的整数有效性、cutoff补集、同域下界传递和完整覆盖正确；不将局部LP界冒充原生全局界。
2. 外层LP与原生MIP内部松弛的含义清楚，实际target和terminal均按声明放置；cache／artifact／VType无残留行或身份混淆。
3. R138 V2修复和原V1测量身份保留，关闭新功能时旧稳定与研究行为不受无关修改。
4. 机制定位与真实调用一致；没有将global trace发布时间当作首次发现时间，或把K20收益说成省了target直接耗时。
5. 2×2比较的实际格、重用格和未运行格清楚；控制路径／原生状态变化没有被省略或夸大为精确加性归因。
6. 完整候选统一、Seed0默认、资源rho和物理T正确，必要基线公平；不挑实例版本、不用有利Seed替换不利结果。
7. 8400＋10800的完整新增cap、各条件块与16小时总额无重复或遗漏；探索和合理停止保留自由度。
8. 采用决定、论文表述、实际证据和PR／清理状态一致，没有强制候选获胜、全获证、用满预算或重做旧恢复的要求。

修正发现的问题，给简明复核结论即可，不建立另一套庞大审计流程。

---

## I. 交付、Draft PR与有限收尾

交付本goal、最小代码／配置差异、数学与历史关系说明、实际矩阵和位置清单、必要raw与汇总、计费、研究决定、增量稿、独立复核和续跑入口。合并重复报告，重视内容而非文件数量。新证据绑定实际源码／PE、输入、配置和原生参数；旧依赖用固定提交和必要成员。

正常提交并推送新分支，创建英文Draft PR，建议标题：

**Round139: study inventory-product placement across LP control and native MIP search**

main未吸收R138时以codex/round138-shared-product-resource-coupling为临时base；已吸收时用实际main。读回实际base/head及交付状态。本任务不自动merge、force-push、删除历史分支、发送邮件或投稿；待合并状态不阻塞本轮研究。

对本轮必要新载体做一次有限公开读取核对，普通I/O与纯读检查建议累计30分钟内收束；不触发Optimize、编译或商业原生资产加载。明确区分本地科学／语义检查与公开字节／成员可读性。失败可在原根续传并如实记录，缺文件或错误发布应定向修复。没有理由重开已完成R138载体检查或R137全public语义恢复。

显式继承WORKSPACE_POLICY：所有新build/raw/temp/restore资产位于E:\codes\ExactEBRP-work；PR交付后对本轮已完成、可重建的临时／重复对象有限清理。先满足相应证据保留和必要公开核对条件，保留唯一raw、失败、用户内容、必要PE/DLL与仍有依赖的树；旧轮不删除。记录实际删除／保留项和字节，零删除也可接受。

最终报告回答：本轮确认了什么交互、四格实际表现如何、是否得到值得采用的统一配置、重要回退是否改善、剩余数学／算法问题是什么，以及实际成本和交付状态。无需再启动一轮泛泛稳定性证明来替代决定。

---

## J. 最小资料索引

R138固定审查参考：

https://github.com/yifanXovo/TailoredExact/tree/d606062edddf58c13a7c3acb48e896fc787ff856

R138科学载体固定提交：

https://github.com/yifanXovo/TailoredExact/tree/1b19897ab5819ab3b7485ddc978954b45225f361/results/unified_exact_round138

- **当前入口／工作区：**WORKSPACE_POLICY.md；docs/current_mainline.md、round138_research.md、paper_s2_release.md、unified_exact_research_index.md。
- **R138科学与表格：**results/unified_exact_round138/ 下的 final_report.md、mathematical_analysis.md、candidate_decision.json、baseline_reuse.json、seed1_selection.json；同目录reports/下的LP.json、new_arms.csv、pairs.csv、full.json、trajectory_scope.json、trajectories.csv、AM/及Seed1结果。
- **R138实际身份／修复：**candidate_manifest.json、candidate_repair_manifest.json、source_publication.json、qualification/native_coefficients.json、repair_matrix_checks.json、repair/primary_native_bridge.json、review/、carrier_manifest.json。
- **最有信息的原始载体：**R138 artifacts/campaign_004.zip（K20）、campaign_007.zip（RB35-T2）；R137固定science e735c3447eb1443713c700942d873de1783a4a26 下 artifacts/campaign_012.zip（K20）、campaign_052.zip（RB35-T2）。读取实际 external/native_logs/、adaptive_mass_decision_ledger.csv、paper_optimize_ledger.csv、Start／参数／audit及模型成员，按manifest取必要内容。
- **实际调用链：**src/PaperExternalGiniTree.cpp、GurobiBaseline.cpp、CplexBaseline.cpp、PaperK1AmSf.cpp、IntervalRowFactory.cpp；include/Round138Research.hpp、Round127Research.hpp；相应launcher／profile。以当前代码和实际请求为准。
- **历史区别：**R63的MIP-only行生命周期；R120的mathematical_contract及artifact替换；R47/R48与R119–122控制研究；R134 TC；R135 AP/IND；R137机制控制。通过research index定位相关文件，不批量重做历史。
- **稿源：**R137完整paper_body/model_and_algorithm_appendices/supplement及R138 manuscript.md、mathematical_analysis.md；不从历史根Manuscript误起步。

**本轮成功标准：明确共享库存产品加强怎样影响外层决策与原生搜索，并以有限完整实验决定一种统一使用方式是否值得保留；即使不升级主线，也应留下可用于论文的明确机制关系与后续研究边界。**
