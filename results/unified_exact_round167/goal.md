/goal

# Round167：保持条件库存信息的数字网络表示与论文重组

## 0. 目标、具体增量与预算

继承已完成的 Round166。本轮推进两个相互支持、均须产生实际成果的任务：

1. **EJOR/TRE 成稿主线：**将当前英文正文按科学主张重新组织，减少研究过程和重复限定，使“共享库存状态连接—完整精确方法—可认证的运输决策”成为清楚的主线。直接修改当前正文、附录、补充材料和 PDF，保留关键正负证据。R166 已完成的连续权重包络与资源区间直接使用，不再重算为一轮新贡献。
2. **OR 深入主线：**研究并实现一个明确的表示问题：在保持库存、移动量、访问及 Gini 乘积的共同关系时，能否用规模为 O(log(C+1)) 的数字决策图，保留任意部分库存编码位固定后的联合凸包？完成一个统一 C++ 研究原型 **D167**、完整证明和有限条件诊断，判断它是否值得后续进入完整算法比较。

本轮新增对象是**编码、服务和乘积的共同条件信息**。R166 的五支撑表示保持了原始物理 LP 投影，但独立 bit-product 层可能在部分 bit 固定后失去与服务混合的一致性。已有明确局部反例，因而本轮不是泛泛“研究为什么慢”，也不是重新跑 LOG 或 C166。决策图、网络流凸包、析取和 embedding 本身是标准工具；真正需要交付的是本项目具体联合对象的构造、适用边界、相对已有表示的严格关系和实际代价。

**冻结当前 B/GI-TBC 和 C166。**D167 仅为离线研究/资格入口中的表示原型，默认关闭；本轮不接替 B，不改 Gini 外层、own-H、原目标、物理规则、有效行或默认 Native 策略。只研究一种固定的 MSB-first 区间 DAG 和同图 f/q 流，不进行编码顺序、边界策略或多个新候选的搜索。本轮不安排新的完整 GI-TBC、P、PS、E+ 或 Seed 面板。

理论成立但实际 LP 目标无增益、模型常数过大或诊断代价偏高，均可形成有价值结论。出现实质数学/实现障碍时给出确切反例或失败条件，完成论文重组和已有研究结果，不临时开启另一条大研究线。

### 0.1 工作容量与 C++ 约定

总科学工作容量 **10h = 36,000s**，目标约 6–8h，完成即停止。包含阅读、推导、实现、计算、数据处理、改稿、构建和独立复核；并行代理按共同外层窗口计一次，实际计算费用另行完整记录。普通 Git/公开恢复传输 I/O 单列。

| 工作 | 建议安排 |
|---|---:|
| 定向历史/近邻核查、条件表示推导 | 约 3h |
| 一个 C++ DAG/同码参考实现及接口检查 | 约 2h |
| 有限诊断计算 | 最多 1h，实际 Optimize 最多 96 次 |
| 当前论文实质重组、图表和 PDF | 约 3h |
| 数据收束、独立复核与交付 | 约 1h |

允许在总容量内调整，进入诊断前为论文与复核合计保留至少 3h。不要为用满 96 次或 10h 添加实验。诊断上限包含失败、修复及内部辅助 Optimize，不是 96 个成功结果。具体矩阵和每次调用限额见 E。

**新增建模、优化、精确枚举 oracle、资格 LP/MIP driver 均使用 C++。**Python/Node 只用于编排、日志、独立离线验算、表格和文档；不使用 gurobipy、Python 优化核心或 solver CLI 替代 C++ 核心。旧轮 Python helper 按历史事实保留，不顺带移植或重测。

表示规则只依赖合法输入、当前数学域和已证明条件，不依赖实例名、数据来源、历史胜负、机器型号或测得速度。诊断时间上限属于实验管理，不进入算法切换。所有原型运行均与正式性能证据分开。

## A. 本地入口、继承身份与 PR

遵守仓库 `AGENTS.md`、`WORKSPACE_POLICY` 和既有工作区约定。所有新增工作、缓存、临时件及交付放在 `E:\codes\ExactEBRP-work` 内；保护原 `E:\codes\ExactEBRP`、用户文件、活动 worktree 和历史证据。

`E:\codes\ExactEBRP-work\worktrees\paper-current` 先前处于 R155 且有未提交修改，只读核实，不 reset/stash/覆盖。优先在核实的 R166 基础上新建或接续 `E:\codes\ExactEBRP-work\worktrees\round167`，分支建议 `codex/round167-conditional-state`。若已有同轮内容，先去重接续，不重复产生运行。

任务编写时已核实：

| 身份 | 固定参照 |
|---|---|
| 仓库 | `yifanXovo/TailoredExact` |
| 前序 | [Round166 / PR228](https://github.com/yifanXovo/TailoredExact/pull/228)，Open Draft，尚未合并 |
| R166 branch / delivery | `codex/round166-structure-and-paper` / `d497052216d5ae55b6ae0139ea30910cee2e5865` |
| R166 science | `c0e263ed7eddba350a401dd83d81ef7048ee21cd` |
| R166 实测 C++ source | `0298dd45fbc3645af927c4a4dd1d43ecbdb567a9` |
| R166 实测 PE SHA256 | `27e71873536bcd8e6001aee0c2514a5cc8122763728c62e6d467cd528b48daba` |
| Gurobi 13.0.2 DLL SHA256 | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |
| R165 delivery / PR base | `239db6a80c944f1e7b5a55504ce5202ea35c2586` / `codex/round165-current-manuscript` |
| main | `b2b940c1e517a72e226ec60fc49ff19651737632` |
| 历史 R163/R164 实测 source | `e920b92e199e825ec89a2932f701861ff158e0d4` |
| 历史实测 PE SHA256 | `fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93` |

入口一次读取远端真实 main、前序 PR/head 和本地状态；以实际合法更新为准。main 已包含全部依赖则从 main 开始，否则基于核实后的 R166 head，Draft PR base 取 R166 branch，无需等待合并。不要仅凭继承的 `method_freeze.json` 选择旧 executable；使用实际 candidate/environment manifest、调用记录和 SHA。

本轮研究记录放在 `results/unified_exact_round167/`；当前论文继续维护 `results/unified_exact_round137/` 中的权威组件。只维护一套当前英文稿。记录新的源、构建命令、编译器、PE/DLL 身份；诊断构建不能冒充旧性能样本的 executable。

## B. 已知结论、历史排重与近邻

### B1. 已完成的 R166 结论

先读 R166 的 `goal.md`、`final_report.md`、`decision.json`、`compression_theory.md`、`research_design.md`、`decision_analysis.md`、`qualification.json`、实际 C++ 实现和当前论文。以下事实属于已完成结果：

- C166 的至多五个支撑点保持声明接口的原始联合 LP 投影；独立 absolute-bit 层恢复整数乘积精确性。八个 canonical LP 对的最大数值差为约 3.33e-16。
- 同构建、各自支付 own-H 的六配置 Seed0 比较中，B 为 3/6 CERT，C166 为 2/6。C20 在 C166 下 OPEN；X20 的完整证书时间由 125.30s 增至 544.90s，约 4.35 倍。C35/B35 的 U 有改善但 L 退化，X35 的 U/L 均退化；因此保留 B。
- X20 的额外成本主要落在 Native 搜索，不是 writer 时间。该观察尚不能证明具体 bit branching 是实际退化的原因，presolve、root cuts、分支轨迹也可能改变。
- 新 B 六组 U/L 与 R163 Seed0 相同，未发现超过既定尺度的运行退化；这是有限重复确认，不是新的独立实例优势。
- 已恢复并物理验证 50 份完整 fleet，完成四族连续权重质量界和四组资源改善双侧区间。R166 没有新增严格 B/P 配对。

本轮不得再把这些旧结果列为新实验。C166 完整六行比较及所有不利方向应保留在论文中。

### B2. 定向排重

读 `docs/current_mainline.md` 和下列直接相关材料/代码，不重放全仓库历史：

| 历史 | 本轮区别与必须继承的边界 |
|---|---|
| R55/R67 | VD-P/VD-J/LOG 与共同投影；LOG 已减少整数位但保留全量连续 state/product，是最近参考。旧 LOG 的 offset code y-l 与本轮 absolute code y 不可直接按同 bit 下标比较 |
| R98–100 | 当前 movement/visit、M-B、隐式服务整数性和实际启用行；本轮沿用共同接口，不加入未启用的方向/vehicle-state 连接 |
| R101–107，尤其 R104 | event/rank、资源池与 dual row aggregation 的对象；目标保持资源行聚合不是本轮 stock-code 联合网络 |
| R132/R133/R135 | 局部产品 hull 与整数目标/完整路线 hull 的差异仍然存在；不把条件库存结论扩展为全 BRP hull |
| R138–162 | 资源、库存和物理产品补全的适用域与负结果；不重复 full-Q/RN 或开发新 cut |
| R163–166 | 已暴露六配置、Seed 结果、C166 数学与负面完整比较、已完成参数分析；不追加常规重复批次 |

形成一份紧凑 `research_design.md`：具体对象、最近历史实现差别、拟证明命题、唯一原型、冻结矩阵及判断标准。找到实质等价的旧实现时直接复用并识别尚未完成的比较，不能换名重做。

### B3. 文献边界

定向阅读以下原文中的相关定义/构造，不展开新的 BRP 文献普查：

1. Huchette–Vielma，piecewise-linear/embedding formulations，DOI `10.1287/opre.2019.1973`，作者稿 §3.2 的 branching behavior。已有文献说明理想/强 root 表示不自动保证有效分支，不把这一一般观察称为本项目首创。
2. Behle (2007)，*Binary Decision Diagrams and Integer Programming*，§4.1、Theorem 4.1：路径流与 level equations 的凸包投影；可用 van Hoeve (2024) tutorial §6 补充网络表示及规模背景。
3. Balas，*Projection, lifting and extended formulation in integer and combinatorial optimization*，§5、Theorem 5.1：析取凸包构造。明确本轮端点流分解与标准工具的关系。
4. Muldoon–Adams–Sherali (2013)，DOI `10.1016/j.orl.2012.10.005`：有界整数 absolute base-2/lexicographic hull 的最近参照。只读到摘要/引言时如实记录，不声称已逐定理排重全文。

使用原文与实际读到的内容。内部文献 memo 保存版本和阅读范围，公开论文不放检索日志。DAG、网络流 ideality、端点混合和 bit encoding 均有成熟来源；本轮贡献应落在**具体共同库存/服务/乘积对象、部分编码固定后的关系、紧凑实现和实际诊断**。不要把一般命题或标准技巧自动称为 OR 级突破。

## C. EJOR/TRE：实际重组当前论文

### C1. 以主张组织正文

R166 当前正文按 whitespace 口径约 13,505 词，§5–§6 约占 64%；主/补充 PDF 为 60/44 页。问题是历史试验不断追加、解释重复，并非缺少又一张贡献清单。

编辑目标为 **约 7,500–9,000 词的正文**，同一统计口径前后对照。这是本轮编辑目标，不是未经核实的期刊硬性字数限制。可以有合理偏差，不能为达标删掉关键定义、证据或使算法无法理解。

建议按下列六部分重组，可依据论证衔接调整标题：

| 部分 | 主要内容 | 大致词数 |
|---|---|---:|
| Introduction and related work | 运营问题、联合困难、最近方法、三项可支持的贡献 | 900–1100 |
| Problem and shared-state formulation | 物理语义、目标、共同库存连接、原始与条件表示的准确关系 | 1100–1400 |
| Complete GI-TBC method | own-H、当前启用行、区间覆盖、AM、资格与终止、主算法 | 1300–1600 |
| Computational evidence | 一次说明实验/数值协议；完整性能、有限 Seed、机制和表示比较 | 2000–2300 |
| Certified transportation decisions | 连续权重质量界、资源双侧区间及其决策意义 | 1000–1200 |
| Conclusions | 成果、范围、重要未解决问题 | 400–600 |

摘要先说明主方法思想、主要计算证据和一种决策认识。C166 的详细失利计数与单配置 1e-7 数字放正文；摘要可以用一句准确概括强/紧凑表示与计算效率之间的区别。标题建议放作者 memo，GI-TBC 名称保留，不暗示外层独立加速已经得到证明。

正文保留一处完整的时间/数值政策，之后引用它；将重复的版本身份、qualification 过程、逐轮流水、逐 AM role 轨迹和大 Seed 明细移入有导航的补充材料。不得只删重复段落后仍保留原来割裂的结构。

### C2. 必须保留的科学内容

- 解释特殊 BRP 的非零单向服务、库存 balance、空载出发、允许载货返回及卸货时间；公平解释限于 inventory-to-target ratio dispersion。
- 明确 P、PS、强化 root-only、完整 B、E+ 各回答什么；同一历史记录不重复计数，cohort、Seed 和 joint-CERT 分母清楚。
- 保留主 B/P/PS 面板、C35 的历史反转、所有相关 n35 OPEN、E+ 的证明增益及费用，以及 full/root 尚未建立外层独立净收益的结论。
- 保留 C166 六行完整结果：CERT/OPEN、U、L 和有定义的证书时间；不能只留下规模下降或两个 U 改善。
- 保留四组资源双侧区间，四族参数全区间质量界及现有参数图。引用原全精度数据，主表适度舍入；不能将档案包络称为完整 Pareto frontier，也不能把离线重评价回填为旧算法 incumbent/时间。
- HGA-TGBC 的问题/decoder 继承归属继续明确。使用实际可取得的作者稿，不称未取得的更新稿为已读；少量作者/发表状态待确认项留内部 memo，不阻塞技术改稿。

R166 参数/资源结果已完成，本轮只做必要的表文一致性核对和编辑整合。资源改善下界为正不意味着其幅度已精确确定；B35/X35 较宽区间及返回量变化方向不同的事实均保留。

### C3. 本轮结构结果如何进入论文

把 D 中得到的条件反例、命题或原型结论并入现有表示讨论，正文新增内容约 **300–500 词**、一个紧凑命题或有解释力的小示意即可；通过重组腾出篇幅，不再新增一整章研究流水。完整证明、诊断、边界和代码写入本轮研究 note/附录。

只有局部表示/LP 诊断时，按这一层次报告，不称为完整 GI-TBC 加速。即便 D167 未形成运行优势，论文重组仍应完成。内部 `author_decision_memo.md` 分别说明 EJOR 的方法贡献、TRE 的运输决策含义、OR 方向实际新增与尚缺证据；不另写三套全文。

## D. OR 深入：条件库存联合表示

### D1. 精确对象与同码比较

对站点 i，省略下标，合法整数域为 D=[l,u]∩Z，0≤l≤u≤C；初始库存为 b∈[0,C]∩Z，g∈[α,β]⊆[0,1]。记

    m(y)=|b-y|,  v(y)=1[y≠b],  X=(Y,M,V,g,Z),  Z=gY.

M、V 分别对应共同模型的 aggregate pickup+drop 和 aggregate visits。使用 **absolute y** 的 d 位二进制码 c(y)，d=max(1,bit_width(C))，避免浮点 log 在二的幂处造成位数错误。定义

    H(D)=conv{(y,m(y),v(y),g,gy): y∈D, g∈[α,β]},
    E(D)=conv{(y,m(y),v(y),g,gy,c(y),g c(y)): y∈D, g∈[α,β]}.

共同编码列为 δ=c(y)、w=g c(y)。本轮比较三种表示：

1. **C166：**现有五支撑 joint hull 加独立 absolute-bit product 层，不修改。
2. **R_abs：**全库存状态的同码参考。对所有 y∈D 使用连续 s_y、q_y，Σs=1，Σq=g，αs_y≤q_y≤βs_y；Y、M、V 由 s 重构，Z 由 q 重构，并明确加入 δ_h=Σc_h(y)s_y、w_h=Σc_h(y)q_y。它是 E(D) 的枚举参考，不是原 B 的实际分支策略。
3. **D167：**下述同一 DAG 上的 f/q 表示。

其余全模型行只通过共同物理接口使用被替换的状态；e epigraph、pairwise H、S、原目标、SCF/MTZ、physical time、cutoff 及当前有效行保留。固定部分 δ 时，所有其他未声明固定的物理和辅助变量仍自由，不用某个已求得 LP 点固定它们。

旧 LOG 使用 offset y-l，不能把它的第 h 位直接当作 absolute y 的第 h 位。若引用其实现，要显式转换/重建同码参考。也不能仅以 min/max 收紧 Y 来表示有断洞的条件域。

### D2. 先验证一个严格反例

取 D={0,1,2,3,4}、b=2、g∈[0,1/2]，固定最低位 δ_0=1。合法库存为 {1,3}，所以真实条件联合凸包满足 M=V=1。

C166 却可取：

    t_2=1, q_2=1/4;
    Y=2, M=V=0, g=1/4, Z=1/2;
    (δ_0,δ_1,δ_2)=(1,1/2,0);
    (w_0,w_1,w_2)=(1/4,1/8,0).

逐行核对五支撑、bit 重构和当前全局/区间 product 约束。这个点揭示独立 bit 层与服务混合之间的条件信息损失；它不否定 C166 的整数正确性或原始物理投影，也不证明 Gurobi 在 X20 实际访问过该条件域。

对任意固定集合 F 及 bit 取值 a，定义 D(F)={y∈D:c_h(y)=a_h, h∈F}。证明：只看 X 的条件 hull 时，donor 区合法最小/最大值、合法初始状态及 receiver 区合法最小/最大值仍给出至多五个支撑，即使 D(F) 有断洞也成立；断洞内部的整数成员资格须由 code/合法路径保留。这个条件支撑结论可作手算 oracle，不能误当作完整 E(D(F)) 的至多五点表示。

### D3. 唯一构造：MSB-first 区间 DAG 上的 f/q 流

将 D 分为三个互斥非空部分：donor [l,min(u,b-1)]、初始 singleton {b}（若合法）、receiver [max(l,b+1),u]。空部分省略。

对每个合法整数区间建立 MSB→LSB 分层 DAG。状态记录前缀是否仍紧于下界、上界，每层至多四种 tightness 状态，每个状态尝试 bit 0/1；只保留符合上下界且可达终点的边。所有成功路径恰好读取全部 d 位，每个合法 y 对应唯一路径。各服务部分通过独立入口边接共同 source/sink，不在中途混合不同服务片段。只能做保持标签/成本的确定性清理，不搜索变量顺序或先枚举全部库存再声称 log 构建。

令 A 为图的节点—边关联矩阵，e 为 source +1、sink -1 的单位流 balance。对同一组边使用 mass flow f 和 G-weighted flow q：

    A f = e,
    A q = g e,
    f ≥ 0,
    α f ≤ q ≤ β f,
    α ≤ g ≤ β.

**两套流都必须满足逐节点守恒。**不能只给每条边产品包络而省略 q 守恒。实现可以删掉一条线性相关守恒行，但必须说明其等价性。

定义路径成本向量 a_Y、a_M、a_V：Y 为各 bit-one 边的 2^h 之和；donor 的 M=b-Y，receiver 的 M=Y-b，初始 M=0；常数通过相应入口边计入，V 在 donor/receiver 入口取 1，其余为 0。使用

    Y=a_Yᵀf,  M=a_Mᵀf,  V=a_Vᵀf,  Z=a_Yᵀq,
    δ_h=Σ{f_e: e 是第 h 位的 bit-one 边},
    w_h=Σ{q_e: e 是第 h 位的 bit-one 边}.

入口/终端边不误算为编码位。w 可作为共同诊断列或按代数消去；不得用另一个独立 q 分配重构 Z。D167 的整数精确性由共同路径及 δ 整数性实现，不需要另加独立旧 product 层作为第二机制；若保留冗余行必须明确标注并证明其冗余，规模比较保持同一口径。

固定此 f/q 实现。端点双层流只用于证明，不再实现为第二个时间候选。合法物理 Start 的映射为：沿 y 的唯一路径设 f=1、q=g，其余为 0；δ、w 及所有原物理列据此恢复。这避免在很窄的 Gini 区间里计算端点权重造成数值放大。

### D4. 必须完成的证明

1. **合法路径和规模。**每个合法 y 有且仅有一条路径，反向不存在越界库存；固定仿射片段数 r 时，节点/边/新增变量/行/非零元为 O(r log(C+1))。明确常数和系数编码长度。任意洞集合或任意 state-dependent 函数不能无条件视为固定 r。
2. **增强共同投影。**D167 在 (X,δ,w) 上的投影恰为 E(D)，与 R_abs 相同。α<β 时可用

       f^α=(βf-q)/(β-α),  f^β=(q-αf)/(β-α)

   得到两套非负端点流；它们的 source 质量之和为 1，分别按路径分解。反向由合法库存与端点混合构造 f/q。α=β 时直接 q=αf、g=α，单独证明；实现不依赖除以 β-α。
3. **任意部分 bit 固定。**利用每个成功路径每层恰选一个 bit 和非负流，固定 δ_h∈{0,1} 自动排除不一致路径，故相应投影为 E(D(F))，物理投影为 H(D(F))。空 D(F) 应为不可行，全位固定/单库存/零容量域均覆盖。
4. **整数精确性。**全部 δ 整数时，所有正流路径对应同一合法库存，得到正确 M、V、Z=gY。给出与原物理模型双向映射，并保留原有服务整数性论证的前提。
5. **与 C166 的关系。**R_abs 与 D167 的增强投影相同；它包含的点在 C166 有扩展，因此任意相同 bit 固定后的物理 LP 可行域包含关系成立，可严格。F 为空时物理投影三者相同。全模型结论依赖外部约束仅使用已声明接口，须逐类核实。

局部网络的 ideality 不扩展为完整 BRP ideality。这里的条件保证是**指定 absolute bits 的任意部分固定**，不是所有可能的 Native 分支行：例如仅添加 Y≤r 不自动等于对截断库存域重建 hull。若已知 child 的 g 区间或库存域变化，需用其实际 α/β、合法域构建对应表示；不能继续用旧 q 边界却宣称对新域完整。canonical Gini child 是离线固定数学域，不等于捕获了某个 Native 节点。

### D5. 实现边界与可复现入口

优先以独立 C++ 研究 driver 和明确命名的诊断表示接入当前 canonical writer，不要求本轮接入完整外层 controller、target/terminal 生命周期或在线回调。不得将未完成的完整集成说成已验证算法。

- 读取实际 `CplexBaseline.cpp`、`Round166Research.hpp`、`round166_qualification.cpp`、`IntervalRowFactory.cpp`、`MipStartMapping.cpp`、`GurobiBaseline.cpp` 与相关选项。文件名含 Cplex 不意味着改用 CPLEX。
- 准确替换声明的 s/q 或 t/q/bit 编码块，保留所有共同物理行和原目标。R_abs 的 s/q 为连续参考；tiny MIP 中采用明确整数 δ 和原物理整数类型，不悄悄保留旧 s 的整数性改变比较对象。
- AP、count、RN、CDF、theta、linked-direction、VD-J 等额外 state-dependent 功能本轮不启用；研究入口遇到未证明兼容的组合应明确报错，不静默删行。无需重构主线当前本未启用的全部功能。
- Start 按真实列名、边编号、bound、类型、行和原目标验算；原始合法内部库存、loaded return、窄/固定 g 域均涵盖实际变化。
- LP→MIP 类型恢复、诊断缓存/fingerprint、scope/cutoff/区间身份准确。模型身份不一致的旧 opaque Native 状态不能复用。
- B 和 C166 默认路径保持原语义。对一个既有 canonical 物理块做无 solver 导出差分，验证未受影响行，不为此再跑六组 B 完整控制。
- 计算每站及全局的变量、二元变量、行、非零元、构建时间和 memory/文件大小（已有可得项即可）。理论 log 规模不保证实际规模较小，窄域常数开销可能使 D167 比 one-hot 更大。

## E. 固定有限诊断与判断标准

### E1. 总量、计数和顺序

在首次新 Optimize 前冻结 `diagnostic_manifest.json`，包含全部输入 SHA、canonical frame、表示、bit mask、目标、顺序、源/PE、Native 参数和上限。

总计 **最多 96 次实际 Native Optimize，最多 3600s 诊断外层计算**。所有诊断串行；每个诊断窗口包含模型构建、写入、求解和必要在线资格，多个窗口累加，不把失败或辅助调用藏到实现时间。代码编译、人工推导/编辑另入总科学窗口。无 solver 的小域枚举也计实际诊断计算费用，但不增加 Optimize 次数。

固定分配为：72 个 canonical LP 位置、12 个局部 LP、4 个 tiny MIP，另最多 8 次仅用于必要边界/技术修复的调用。保留槽位不是额外机制/输入搜索。每个位置实际启动的内部 Optimize 逐次计数；不能由 wrapper 的一次执行代替内部次数。

canonical LP 每次 Native TimeLimit≤20s；局部 LP≤5s；tiny/必要修复调用≤60s，并受剩余外层预算约束。保持 Threads/MIPThreads=1、Seed0、MIPGap=0、MIPGapAbs=0、NodeLimit=∞（不得继承开发节点上限）、原数值容差和资格政策；其余策略固定为当前 Native 默认。纯 LP 明确放松所有整数类型，不能把 MIP root cuts 后的界当 raw LP。遇到超时/资格失败保留结果，不能把未证明 optimum 当 LP 等价证据。

先完成代数/代码审阅和少量局部检查，再进入 canonical 矩阵。足够验证后停止，不用满保留次数；不因结果无增益扩展矩阵。健康 producer 的 reader/表格错误只读修复，不重跑求解。

### E2. 72 个 canonical LP 位置

使用 R166 已存的六 root 和两个 child frame：

- `R163-C20-S_root`、`R163-B20-B_root`、`R163-X20-S_root`；
- `R163-C35-U_root`、`R163-B35-S_root`、`R163-X35-S_root`；
- `R163-C20-S_child`、`R163-B20-B_child`。

以 R166 `qualification/LP_pairs.json`、其原 argv/模型及输入 manifest 为准，恢复实际合法域、U/cutoff、[α,β]、原目标与全部共同物理行。不根据短别名重新生成输入。历史合法 U 用作这个离线固定 frame 的定义，不注入任何新的生产性能样本。

每个 frame 比较 **3 个固定条件层级 × R_abs/C166/D167**。所有站点采用对应表示，但只对按以下规则选定的一个站点增加条件：

1. 选合法库存数量最大的站点，平手取原站点最小 index；不使用历史胜负、LP 值或求解时长。
2. F0：不固定编码。
3. F1：从最低位开始找在 D 中同时出现 0/1 的第一位 h。若 b∈D，固定为与 c_h(b) 相反的值；否则固定为 0。两值均出现，所以该选择非空。
4. F2：在 D(F1) 上，从最低未固定的位开始找同时出现 0/1 的第一位 k；若 b∈D(F1)，取与初始位相反的值，否则取 0，并保留 F1。
5. 无可分位时，保留该层级并登记 `degenerate/redundant`：没有 F1 时用空 mask；没有第二位时 F2=F1。可直接复用相同矩阵/求解结果并标出同一 solve ID，不另调用、不把重复层级当独立证据。

上述 masks 由原整数域的无 solver 逻辑确定，进入 Optimize 前写完全部八个 frame 的条件。全局物理模型在某条件下不可行是合法结果，必须保留，不能换位/换站点；空域和非法码由 E3 专门覆盖。这里只是确定性构造的条件 scopes，不声称它们是实际搜索中遇到的节点。

R_abs 的固定可通过 δ 等式，或把不兼容状态的 s/q 置零表达；两者需证明一致。不能仅用条件集合的 min/max 收紧 Y，因为会填平断洞。C166 只固定相同 absolute δ，其他连续支撑自由；不得为它另加条件 hull 后仍称原 C166。

报告全部72位置（含数学不可行、冗余复用、失败和未执行），每个位置至少有状态、原目标/L、资格、mask/合法库存数、共同块身份、规模、构建和 Native Runtime/Work/外层费用。若已存 C166 F0 与当前矩阵、目标、域及参数逐项相同，可复用其合格数值/身份并标为历史控制；不把旧时长与新表示组成严格时间加速结论。需要同构建数值控制时可在72上限内重做 F0，不增加另一个 B 面板。

在合格最小化 LP 下检查：F0 的物理目标三者相同；条件层级应有 L_D167=L_R_abs≥L_C166（按原数值资格判断）。这些 L 仅是对应 frame/mask 子域的 LP 界，不能直接作为原问题全域证书。不预写一定出现严格目标差：其他全模型约束可能遮蔽局部信息损失。若目标相同，仍报告严格局部反例、增强投影关系、尺寸和费用；不能搜索更有利 mask 来制造增益。

### E3. 局部、边界与 tiny 检查

先用 C++ 无 solver 检查合法路径、f/q 双向映射和小域部分编码：覆盖 C=0、l=u、b 不在域、单侧域、两侧域、含洞条件、空条件、全位固定、α=β=0、α=β>0 及窄非零区间。小容量穷举只作为实现检查，不能代替一般证明；无需重跑 R166 全部 4550 域的旧检查。

12 个局部 LP 为下列 4 域/目标 × 3 表示，均为先验固定：

| 局部位置 | D、b、g 域与 mask | 目标及预期关系 |
|---|---|---|
| L1 | D=0..4，b=2，g∈[0,1/2]，δ0=1 | min M；C166 可为0，R_abs/D167为1 |
| L2 | 同 L1，另固定 g=1/4 | min V；C166 可为0，R_abs/D167为1 |
| L3 | D=0..8，b=4，g∈[1/8,1/2]，δ0=1、δ1=0 | min M；合法库存{1,5}，R_abs/D167为1，C166按实测，不预写正差 |
| L4 | D=0..4，b=2，g∈[1/4,1/4]，δ0=1 | min M；固定g退化域，R_abs/D167为1 |

L2 的附加 g 等式是相同条件下的局部实验，不能据它宣称所有 g 子域自动更新。其余边界优先用精确枚举/行残差完成；只有实际需要 solver 才使用保留槽位。

4 个 tiny MIP：复用 R166 已有可手工/独立枚举核对的非零、内部库存且含 loaded return 的完整物理小例，以及已有 S=0 固定库存小例（`qualification/tiny/S0_B`、`S0_C166` 的原物理输入）；各跑 R_abs/D167 一次。S=0 与独立零证明分开，明确此次真正受改动的模型路径，复用未改 controller 的既有零证明证据，不为凑覆盖重跑整条 controller。按当前行逐项检查完整 Start 和 LP→MIP 类型恢复，记录真实 optimum/资格和 C++ oracle 来源。不能只凭两份同源模型同值宣称正确。

### E4. 本轮要回答的科学问题

1. 反例、E(D) 投影及任意部分 bit 固定命题是否成立？相较旧 LOG 和 C166，新对象到底多保留了什么？
2. 原型是否忠实实现这一对象、保持原物理接口和整数精确性？复杂度公式与实际尺寸是否一致？
3. 在固定真实 frames 中，条件信息是否改变原目标 LP 下界，改变多少、覆盖哪些位置？零变化及不可行位置同样报告。
4. 规模/构建/诊断求解的实际代价是否使后续完整集成有合理研究动机？小 LP 时间只能作诊断，不能外推为完整算法速度。
5. 给出明确下一步决定：值得另轮完整集成比较；结构成立但当前实现成本/实际增量有限；或有确切障碍暂不继续。不要因暂未加速就否定数学结果，也不要仅凭 O(log C) 或更强条件 hull 自动安排大实验。

不捕获/重放整棵 Native 树，不做 branching priority 调参或节点回调研究；这些不是本轮回答定义问题所必需。没有新增完整 B/P 运行，因此本轮不更新其胜率、证书时间或普遍稳健性结论。

## F. 当前稿、证据与 PDF

直接维护 `results/unified_exact_round137/` 中的 `paper_body.md`、`model_and_algorithm_appendices.md`、`mathematical_analysis.md`、`supplement.md`、`references.bib` 和 figures。复用已工作的 `scripts/round166_documents.py` 或明确继承入口，不运行会覆盖当前修改的旧 R137 生成器。

按 C 真正重组正文与补充；移出的科学明细保持可定位，建立紧凑 claim→表/证明/原结果映射。正文/参考文献中的内部检索日志、hash、轮次流水迁至研究材料；不编造未读文献的模型关系。新增图最多一幅直接解释共同路径或条件反例的图，已有参数图和主算法框按新结构保留。

从同一当前源生成组装稿和主/补充两份 PDF。记录实际词数、页数与构建身份，但不设页数配额。检查图表/机器结果一致、公式和引用可用、宽表不截断、无异常空页；实际查看摘要、新表示段、主算法、主结果与资源/参数表，以及附录/参考文献连接。只针对本轮变化和具体风险补查，不反复渲染无差异文件。

## G. CSV 与科研成果

### G1. 用户权威主表

与本任务一同提供的 `GI_TBC_vs_P_GRB_All_Tested_Instances.csv` 已为 **112 条记录、28 列、UTF-8 BOM、64,951 bytes**，SHA256：

`b728f85512741779a8b066ae9c974ec60892360c3fe15fbf7b946fb0ab0a4878`

它在旧106条记录上追加 R166 的6条 B 控制；原106条逐字节前缀和原表头保留。新增记录均是既有物理输入、Seed0 的新运行，P 状态为“无配对结果”、P 数值留空、比较为 N/A；没有新增独立输入、Seed 或严格 B/P 优势证据。R166 原增量的两列来源表头为空，合并时按原28列位置映射到“实验数据来源”“实例元数据来源”；C35 场景显示用旧主表术语“库存盈余”，数值未改。

入口做一次有限定位。112条版本可用即作基准，不用旧103/106条覆盖。若只找到106条版本，其 SHA 为 `8f39e3a23b3b6df621139cb39b4db813ca3e992da091e97251ab8337fd2b0022`、60,603 bytes，可与 R166 `reports/GI_TBC_R166_B_controls_increment_28col.csv` 核对合并；所有旧行和来源必须保留。若完整主表仍未取得，交付 reconciliation 与准确增量状态，继续科研，不反复扫盘或虚构文件存在。

本轮 D167、局部/条件 LP、tiny MIP、旧数据重新展示均不是新的完整 GI-TBC/P 性能记录，预期主表新增 **0 条**。若实际未运行完整方法，明确写“主表无新增运行数据”；原型诊断独立成表。112是记录数，不是112个独立物理实例，也不是112个严格 B/P 配对。

### G2. 必需成果

`results/unified_exact_round167/` 至少提供：

- `goal.md`、`research_design.md`、`source_manifest.json`、冻结的 `diagnostic_manifest.json`；
- `conditional_state_theory.md`：反例、H/E 对象、DAG 构造、证明、规模、边界、与历史/文献的准确关系；
- 一个 C++ D167 和 R_abs 诊断实现、构建/运行入口、来源与 PE/DLL 身份；若遇实质障碍则给出确切可复查证据；
- 资格结果、完整位置表、局部/tiny oracle、原始模型/日志/Start 检查、费用与失败/复用说明；
- `manuscript_restructure.md`：前后词数/结构、移入补充的内容、关键主张到证据的映射；
- 实际修改的论文组件、组装稿和两份当前 PDF；
- `author_decision_memo.md`、`final_report.md`、`decision.json`、CSV reconciliation、独立复核和处理记录。

相邻普通记录可以合并，避免交付重复文书。最终结论分别回答：B 是否仍保持默认；D167 的数学/实现/实际诊断价值；是否值得后续完整比较；正文是否真正更清楚精练；EJOR/TRE 现有贡献与 OR 方向实际增量。不能用“完成很多审计”代替科学结论。

## H. 独立复核、正常 Draft 交付与停止

成果形成后执行三个实际独立复核，允许并行阅读：

1. **数学/模型：**挑战反例、E(D) 投影、f/q 守恒、α=β、任意部分 bit 固定、整数精确性、全模型接口与复杂度；核对 R_abs 与旧 LOG 的码差及标准文献归属。
2. **实现/数据：**读实际 C++、合法路径、Start/类型/行映射、共同块差分、全部矩阵位置及实际 Optimize/时间；核查失败、复用和 CSV 语义，不以两个同源结果相等代替独立验证。
3. **贡献/论文：**实际读修改后的稿件，检查中心论证、必要正负证据、参数/资源解释、篇幅转移与引用；确认没有把局部条件结果写成实际搜索因果、完整加速或一般 OR 突破。

记录具体问题位置、影响和处理，修正真实错误后定点读回。审阅不是新增用户审批；普通可逆研究和 Draft 交付已获授权。独立代理不可用时披露实际替代方式，不虚构 reviewer。未解决的研究局限如实保留，不要求所有结果都为正才完成交付。

正常 commit/push，创建英文 **Open Draft PR**，建议标题：

`Round167: preserve conditional stock information and consolidate the manuscript`

首段说明科学问题、实际得到的条件表示结果、诊断结论和正文重组；区分标准工具、项目增量与待验证性能。按 A 选择 main 或 R166 stacked base，读回 head/base/Open/Draft 和当前稿件链接。不自动 merge、force-push、删除历史分支或向外部作者/期刊发送内容。

只对本轮新增/变更的源、文稿、图和必要证据做一次公开取回/字节核验。旧 carrier 用固定引用和必要成员，不重下/重打包历史全集；新的 raw 若需打包，使用本轮专属包/member map。不发布商业 DLL、许可证、凭证或私有前稿。科学提交与随后 receipt 提交分开，不填写尚不存在的 self-SHA。清理遵守工作区政策，零删除允许。

**验收须同时看到：**一套实际重组的当前论文；明确、可检查的条件联合表示结果；一个有限 C++ 原型及诚实的诊断结论，或确切失败证据；保留 B、C166 历史正负证据和主表身份；独立复核后正常 Draft 交付。完成后停止，不自动开始 Round168，不擅自追加完整运行。

## I. 固定查阅入口

- [R166 / PR228](https://github.com/yifanXovo/TailoredExact/pull/228)，delivery `d497052216d5ae55b6ae0139ea30910cee2e5865`；`results/unified_exact_round166/` 的报告、理论、资格、分析、review、source/candidate/environment manifest；`reports/{complete_arms.json,pairs.json,qualified_LP_sizes.csv,native_calls.csv,GI_TBC_R166_B_controls_increment_28col.csv}`；`qualification/{LP_pairs.json,B_unchanged.json,tiny/}`。
- 同一 head 的 `src/{CplexBaseline.cpp,GurobiBaseline.cpp,MipStartMapping.cpp,Round50IntervalMip.cpp,main.cpp,round166_qualification.cpp}`、`include/Round166Research.hpp` 及实际配置入口；其他被调用 writer/factory/header 按依赖读取。
- 当前论文：`results/unified_exact_round137/{paper_body.md,model_and_algorithm_appendices.md,mathematical_analysis.md,supplement.md,references.bib,manuscript.md}` 及 figures；`scripts/round166_documents.py`。
- [R165 / PR227](https://github.com/yifanXovo/TailoredExact/pull/227)，delivery `239db6a80c944f1e7b5a55504ce5202ea35c2586`；[R163 / PR225](https://github.com/yifanXovo/TailoredExact/pull/225)，delivery `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`，固定六输入的实际 input manifest；R164 Seed 完整结果作为既有证据。
- R55 `results/gf_k1_am_sf_station_state_chain_round55/`；R67 `results/unified_exact_round67/{final_report.md,mathematics.md,lp_projection_attribution.md}`；R104、R132/R133、R98–100 等按 B2 定向读取实际正文与源，不重做完整历史普查。
- [Huchette–Vielma 作者稿](https://optimization-online.org/wp-content/uploads/2017/07/6148.pdf)；[Behle thesis](https://people.mpi-inf.mpg.de/alumni/d1/2019/behle/publications/behle_thesis.pdf)；[Balas extended formulation 原文](https://www3.diism.unisi.it/~agnetis/projlift.pdf)；[Muldoon–Adams–Sherali 出版页](https://www.sciencedirect.com/science/article/abs/pii/S0167637712001290)；[van Hoeve tutorial](https://www.andrew.cmu.edu/user/vanhoeve/papers/DD_TutORial.pdf)。准确记录版本与实际阅读范围。

最终回复提供科学发现、B/D167 的明确决定、有限诊断与费用、当前稿/PDF、CSV 实际变化和 Draft PR 链接，说明本轮已经回答了什么、哪些具体证据才会支持后续完整算法比较。
