/goal

# Round 110：修复实际入口栈故障，并完成冻结 M-B 原面板确认

你负责在本地 C++ 项目 `yifanXovo/TailoredExact` 完成本轮最小入口修复、资格验证、完整配对评测、独立复核和新的 stacked Draft PR。

**唯一目标：在不改变原问题、P-GRB、ENS-C 或冻结 M-B 数学与搜索规则的前提下，修复 Round109 已证实的实际主程序入口故障，然后使用同一最终 PE，完整运行原12输入/42臂面板，作出明确的候选阶段判断。** 本轮是原冻结面板的工程恢复与确认，不开发新机制，不调参，不换数据，不重开 STRUCT，不按实例选算法。主要 benchmark 仍为原 cold P-GRB；ENS-C 保持默认参考，允许候选对 ENS 有公开取舍。

正式任务仍为 **36个Seed0主臂＋6个事前指定的Seed1臂＝42臂，88200 nominal秒**。本轮独立资源上限为 **96次保守计费启动、110000外层计费秒**；正式前资格最多 **20次启动、2000外层秒**，计入总额。正常正负结果都完成全部42臂；仅真实未解决的故障、正确性或资源问题允许BLOCKED。不得把这轮变成只交修复、只交审计或只补缺失18臂的任务。

## 1. 起点、状态核验与研究边界

起点为R109 / PR #171，分支 `codex/round109-frozen-mb-geographic-evaluation`，本任务编写时最新head：
`8977da23a0be50da0ab2fceb69ad3ee04e040855`，科学payload为 `479f7a4c2d0dc121676614260c17f13b24ab9253`。其base为R108 `d11c94d81e6a2c5dcd64dad8c54b390f3cb4a027`。

R109实测PE SHA256：
`4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0`；
Gurobi13.0.2 DLL SHA256：
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。
修复后必须产生并冻结新的实际PE身份，不能把PE header/build/parser改动描述成“同PE环境恢复”。

开始时读取本地适用AGENTS.md，核验GitHub最新状态、本地HEAD、用户修改、活动进程和已有本轮记录。建议新worktree/分支 `codex/round110-entry-repair-frozen-panel-confirmation`，结果目录 `results/unified_exact_round110/`。已有本轮进度按RESUME继续，不覆盖、不重复运行已完成臂；更晚提交先审查差异，不默用过期身份。不修改用户原工作区、代理、权限或无关配置。

必须读取R109完整goal、final_report、protocol、input_manifest、generation_recipe、candidate身份/合同、reports_final、main09_stack_failure、evidence_compatibility、main06_recovery、最终有效独立审查、mechanism_correction01、paper_candidate_spec、reproduce与费用。继承R108/R100已经成立的算法、证书和类型证明，不重新做全部历史研究。

保留已成立事实：

- R109为 **BLOCKED**：24个正常正式臂覆盖8个角色；25号G100-C1/M-B在解析完成前栈溢出；26–42共17臂未启动，6个正式Seed1全未运行。不得改写成42臂完成、候选失败或Seed敏感。
- 局部M-B/P为7WIN/1TIE，ENS/P亦为7WIN/1TIE；M-B/ENS为3WIN/3TIE/2LOSS，其中G50-C1严重。原分母12不变。R108的 `SELECT_MB_FOR_BROAD_EVALUATION` 仍成立。
- 原八角色已经有性能结果。本轮准确称为“R109最初前瞻冻结面板的恢复确认”；不重新声称12个全新未见样本。候选、draw、顺序、窗口与阈值不因旧结果改变。
- 原故障为0xC00000FD；实际PE保留2MiB栈，main固定帧1,414,288 bytes，故障地址落在regex matcher；Parser的多行payload正则支持递归匹配解释。没有dump证明具体字段/完整递归深度，不将其写成已知事实或OOM。
- **采用最新纠错：G50-C1的ENS/M-B各执行3LP＋1terminal MIP。** 两者初始完整物理车队相同、U=.03252017937219731，startup约10.37秒。ENS的F=0来自call4 native_MIPSOL。旧“0 Optimize/HGA-only”叙述已由 `review/mechanism_correction01.json` 撤回，不得继承旧诊断文本作为机制结论。
- R109的P15/P17确有原生数值界矛盾；reader修复只恢复可证明的物理/界证据，没有修好引擎数值行为。原错误界、失败flag、缺失journal和unknown clocks继续保留。

先写简明 `research_decision.md` 与 `repair_scope.md`：为何当前应完成原问题而非加机制；哪些修复获准、如何验证等价、哪些结果会否定修复；明确本轮三种阶段结论。工程维护和审计数量不是算法贡献。

## 2. 最小、统一的入口修复

先依据当前源码、原PE头/反汇编和实际故障记录确认具体风险，不重复制造已经有证据的旧崩溃。

**首选将 `Parser.cpp::namedBracketPayload` 中随payload长度递归匹配的 `[\s\S]*?` 提取替换为等价的迭代扫描。** 保留原匹配语义：第一次合法name/空白/等号/左括号匹配，到第一个右括号；字段缺失、空payload、字段顺序、重复/嵌入名称、换行和现有格式兼容性按原行为处理。不顺便锚定字段名、重排站点、改数据语法、加库存约束或“清理”合法旧输入。

保留原number token、`std::stod`转换、`llround`、默认weights/min_ratio、legacy max10权重处理、点坐标/距离矩阵优先级、`sqrt(dx*dx+dy*dy)/1.5`运算顺序和所有实际数值。不要改成不同归一化、不同距离公式或近似数值口径。

如该最小修复后仍有实际栈风险，先用有限的编译栈用量/反汇编/对象布局证据定位，再做必要的小范围对象存储或生命周期调整。未执行研究分支中的大临时对象不应无条件挤占共同入口，但不能未经定位重构整个20k行main、选项系统或算法模块。保持调用顺序、选项、初始化、析构、截止时间起点和异常语义。

统一的有来源控制的stack/build设置属于工程配置，若确有必要可使用并披露；不得按V、输入名、算法、Seed或测得时间设置不同栈，不使用进程注入/备用大栈入口。单纯增大栈不能替代对递归增长风险与实际输入域的说明和验证。不得换编译器/标准库/Gurobi版本、优化级别、fast-math或其它性能设置来混入第二个实验因素。

不改变writer、目标、整数声明、A/B行、分支/割、AM、startup、Start、cache、终止阈值或native参数。仅为真实入口可运行性做小修复；若需要数学/搜索规则改变，停止并报告BLOCKED，不让新的算法变体混入本轮。

所有实际修改必须列出旧/新文件与函数、理由及等价依据；新PE链接设置、实际header、编译命令、toolchain/DLL和生产源码都要绑定。如果最小修复已经足够，不继续做可选重构。

## 3. 正式前资格：覆盖同一PE的真实入口

预先冻结资格清单、真实进程图和预算；上限20启动/2000秒。既有可靠身份的证明、反例与公共reader直接继承；只验证本轮变化及R109已暴露故障，不重做历史因子格。

### 3.1 零求解解析与数学数据等价

对原12个输入逐一验证修复前后解析字段：V/M/Q、容量、initial/target、weights、兼容min_ratio、点序、每个距离元素及T/装卸参数。整数完全相等；binary64逐位等价的权威是同toolchain下的原C++ Parser与修复C++ Parser。R109的Python生成/parsed mirror可能用math.hypot，十进制LP也可能有打印舍入，不能把它们当native逐位基准；只按原已验证数值口径交叉核验，不改距离或数值来迁就mirror。绝对路径等非数学元数据单列，不能用路径变化掩盖数学差异。

可用原Parser的小型独立batch harness或已验证的R109原解析/参考数据比较；若旧正式PE无法解析V100，不能要求它先成功或用反复旧崩溃代替比较。需要运行的native测试/导出进程均计入资格。有限格式反例应覆盖本次payload提取实际改变的边界，不扩展为无关parser重写。

原inputs、source_mapping、parsed/landscape与reference数学矩阵应按精确hash复用。每个正式P模型仍需与原cold reference核对；writer和解析数据已证明一致时可继承旧参考，确需重导出时用一次零Optimize batch，不逐输入启动一套新进程。

### 3.2 最终正式PE的实际main入口

**正式arm1之前，最终PE本身必须对全部12个输入经过共同main和真实Parser，记录每个 `instance_parsing_complete` 并正常返回，且零Optimize、无heuristic、无oracle。** 单独parser harness或不同reference exporter不能代替这项资格。

优先复用现有 `--method option-consistency-test`：先读通其parseArgs、共同main、diagnostic和后处理全链，确认实际选项不会触发求解、preset覆写、auto-oracle或额外原生子进程。该模式只作资格，不参与性能。按原物理T分为3600/7200/18000三个目录组可减少进程；复制/链接时保持原文件名和精确bytes，记录路径映射，逐例核对参数。若现有路径不满足上述性质，才添加最小默认关闭的验证入口，并证明正式方法完全不受影响。

诊断中空车队仅验证 `0<=b<=C`、正target、零载荷/时间和原物理域，不给正式P/ENS/M-B注入额外Start、UB或缓存。不通过入口的合法输入不能删掉、缩小V、改Q/T或换draw。

### 3.3 实际算法和Seed功能资格

在原已知H100（V20/M2）或任务开始前已固定的等价已知fixture上，完成五个实际CLI：Seed0的P/ENS/M-B，Seed1的P/M-B；每臂cap<=120秒。至少触达原LP/MIP、适用Start/type恢复和正常终止，实际Seed及其它参数逐次读回。不要硬编码Seed0，也不要将raw的旧错误global flag静默改成true。继承R109已验证的computed-scope规则并从本轮raw重建，不复制旧sidecar身份。

正式V100仍不作短跑筛选或求解pilot；其共同入口解析、数学数据和reference建模均已在零求解资格覆盖，真正算法性能按固定正式顺序测量。

### 3.4 准入签署

用R109真实Seed1、P15/P17、missing-return/clock和mechanism纠错作为有限离线回归例，确认当前reader不会重新犯已知错误。零求解审查参数、模型、scope、物理见证和分类边界。

独立reviewer在正式arm1前签署一次 `performance_admission`，绑定最终PE、DLL、全部生产差异、资格raw、解析/模型等价、42 argv、数据和下述证据/判断规则。任何正式候选性能测量都不得先于准入；上述有限资格CLI不进入性能比较。尚未通过资格不能直接开始正式长跑；遇真实缺陷只做必要修复与受影响复核。

## 4. 原输入、42臂与完整顺序保持不变

原文件均在 `reference/round109_geographic/`。逐一绑定R109 `input_manifest.json` 中的原bytes/SHA，复制仅用于工作目录映射，绝不重新生成。坐标/容量来自同一公开443站表（442 eligible），其它字段为合成；保留源子集重叠、max归一化权重和兼容min_ratio说明。lambda=.15，pickup/drop各60秒。

H为 `[30]*M`；X为M2 `[20,40]`、M4 `[20,25,35,40]`、M8该四项重复两次。P/E/B分别原P-GRB/完整ENS-C/冻结M-B。

|组/ID|V/M|地理/rep|库存/Q|物理T秒|cap/臂秒|Seed|方法顺序|
|---|---|---|---|---:|---:|---:|---|
|1 G20-C1|20/2|compact/1|shortage/H|3600|900|0|P,E,B|
|2 G20-C2|20/2|compact/2|balanced/X|7200|900|0|E,B,P|
|3 G20-R1|20/2|regional/1|surplus/H|7200|900|0|B,P,E|
|4 G20-R2|20/2|regional/2|shortage/X|3600|900|0|P,B,E|
|5 G50-C1|50/4|compact/1|balanced/H|7200|1800|0|B,E,P|
|6 G50-C2|50/4|compact/2|surplus/X|18000|1800|0|E,P,B|
|7 G50-R1|50/4|regional/1|shortage/X|7200|1800|0|P,E,B|
|8 G50-R2|50/4|regional/2|balanced/H|18000|1800|0|E,B,P|
|9 G100-C1|100/8|compact/1|surplus/X|18000|3600|0|B,P,E|
|10 G100-C2|100/8|compact/2|shortage/H|7200|3600|0|P,B,E|
|11 G100-R1|100/8|regional/1|balanced/X|7200|3600|0|B,E,P|
|12 G100-R2|100/8|regional/2|surplus/H|18000|3600|0|E,P,B|
|13 G20-C2|同组2|同输入|同组2|7200|900|1|P,B|
|14 G50-R1|同组7|同输入|同组7|7200|1800|1|B,P|
|15 G100-R2|同组12|同输入|同组12|18000|3600|1|P,B|

36主臂nominal75600秒，6附加臂12600秒，总88200。逐组串行完成；不并行编译、压缩、重型审查或另一求解器。Seed1只检查三个固定P/M-B配对，不加入主12分母、不替代ENS Seed0、不做best-of-two。

保留R109原编号1–42便于追踪，同时明确新campaign身份。**R110自己的42臂构成唯一正式比较集合。** R109旧24臂可以单独列为历史复测背景，不能与新18臂拼接、累加成更多独立样本或择优使用。不得因新结果较差换回旧结果。

## 5. 算法、物理合同与实际参数

P保持原cold compact，ENS实际入口为 `--algorithm-preset research-round83-vds-equal-net-exchange`；M-B仅附加 `--round98-state-service m-binary`，effective identity仍为 `research-round99-ensc-discrete-structure-m-binary`。`--round100-continuous-quantities` 保持false。

完整保留VD-P/F0、原24+1 startup及物理闭包/handoff、AM=.08、原深度/宽度/覆盖、cutoff epoch、child-cache、milestone和terminal。M-B保留路线/载荷/库存整数及状态/归属/方向二元，仅解除原p/d重复整数声明并保留每站原两条联结：

$$
\sum_k(p_{ki}+d_{ki})=\sum_{y\in S_i}|b_i-y|s_{iy},
\qquad
\sum_k z_{ki}=1-s_{i,b_i}.
$$

缺失初始状态selector按固定0解释。唯一车辆、单向非零操作、整数b/Y使完整整数解的实际数量为整数库存差；此隐含整数性不适用于LP。所有quantity物理检查、等容量车辆稳定归一化及全列Start映射保持不变。

$$
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad
r_i=Y_i/D_i,\quad
F=G_{\rm true}+\lambda P,\quad
P=\sum_i\omega_i|r_i-1|,\quad
G_{\rm true}=\frac{\sum_{i<j}|r_i-r_j|}{n\sum_i r_i}.
$$

原零分母G=0但保留P。每站至多一车一次非零单向整数服务；空载出发，每个prefix/返仓载荷在[0,Q]，允许带载返仓。站点总库存减少量等于总返仓载荷。累计pickup可以超过Q；闭环旅行加装卸含返仓卸载，等于旅行加 `(pickup_seconds+drop_seconds)*sum(pickup)`。没有 `Y>=min_ratio*D` 约束。

统一Threads=1、mip_threads=1、Presolve=Auto、原FeasibilityTol/OptimalityTol/IntFeasTol、MIPGap=MIPGapAbs=0；Seed按表；沿用原单核affinity及cap内30秒全程收尾reserve。物理T、评测cap、完整观测时间分列。

不按输入/SHA/V/库存/几何/T、已知最优、墙钟、Work、停滞、节点或车辆耗时选算法。所有方法独立支付startup和自身工作，不共享UB、路线、cut或cache；P不获得ENS的Start、行、物理见证或最优值。

## 6. 预先固定数值证据与完整时间政策

本轮先冻结统一的证据规则，复用R109最终已验证实现和有限反例；不能等看到某个输赢再按tuple临时豁免。规则适用于三个方法，但不会改变其在线模型、搜索、容差或终止。

1. 原始API返回、log、journal、raw flags、callback bound、native status与独立物理/数学资格分列。原flag为false或缺失的returned事件不伪造；实际正常返回可由匹配call/model、rc、完整log、序列化、cleanup与进程结束共同证明，但它本身不证明bound有效。
2. 所有UB必须来自该臂自身完整合法车队；独立核验整数数量、库存、路径、prefix/return load、时间与G/P/F。已知外部/其它臂解只能作离线反证或诊断，不能成为本臂UB/Start，也不能进入搜索。
3. 具有合法scope/provenance的native bound仍可能数值错误。反证必须在被质疑call的同一有效域成立：绑定其model、true-G区间、cutoff/epoch及其它限制；物理见证须证明可合法嵌入该调用模型，完整数值向量须满足对应全部列/行/界。域外更优解不能否定合法局部LB，cold P全域反证不能自动套给ENS叶。确认矛盾后，保留并拒绝该call全部native lower claims，同时撤销以它们为必要依据的派生bound、closure/删域，再从剩余独立合法证据重建完整覆盖。不能放宽容差、剪负gap或挑一个看起来合理的最终值继续用。新运行的拒绝绑定自身模型、记录和反证，不能照抄旧PE/旧序号sidecar。
4. 原问题的 `F>=0` 是独立全域下界，前提由当前输入非负权重/lambda、真实G及原目标逐项核验。受损call只可保留其它独立合法证明/该原全域floor；作用域丢失不能被summary状态掩盖。仅有floor且own U>0时为未认证；own精确物理F=0与该floor可独立认证。它不表示原native数值错误已消失。
5. 对R109已经识别的Seed元数据、正常return缺journal、非负floor和缺失完整时钟类型，事前签署清晰predicate与有限回归。新事件必须满足全部前提并经独立核验后才可在同PE下继续；不设计永远自动接受的数值fallback。新数学矛盾、模型/解不合法、返回/范围无法证实等不在既有证明内的故障立即暂停，保留证据并按本轮预算与BLOCKED规则处理。
6. signed U-L原值保留；微负gap与relative gap eligibility沿用原规则。精确完整时间无法恢复时必须null；只在有原始记录时给向外舍入的上下界，后续修复/审查耗时不得加进原区间。时长分类和严重标志只有在整个区间矩形内均不变时可判定，否则UNEVALUABLE/unknown；不把端点叫精确时间或生成精确speedup。
7. 正常臂完整时间沿原统一口径，从准入/身份检查至自身startup、求解、必要写盘与物理结果核验完毕。研究工程审查另列。原legacy时间保留，不能为补齐表格编造时间。

提前保留每个启动和结束receipt，尽量避免原wrapper因后置审查失败丢失已经正常结束臂的时钟。此封装修复不改变求解顺序与物理/数学检查，不把跨组独立审查时间混入某一臂。

## 7. 冻结分类与唯一阶段判断

沿用R109原规则；对候选A、对照C：

$$
a_U=\max(.001,.01|U_C|),\quad
a_\Delta=\max(.001,.10|\Delta_C|),\quad
a_t=\max(30\text{秒},.10t_C),\quad \Delta=U-L.
$$

- 仅A完整认证为WIN；仅C认证为LOSS且严重。
- 双证按完整时间：减少至少a_t为WIN，增加至少a_t为LOSS，其余TIE。
- 双未证且U/L均合格有限：UB/gap至少一项材料性改善且无材料性变差为WIN；反向为LOSS；两方向都有为MIXED；均无为TIE。
- 双未证而缺少可比有限值为UNEVALUABLE，不填0或TIE。时间区间按第6节；MIXED不是WIN。
- 严重回退：仅C认证；或双证时 `t_A>=2*t_C` 且多至少120秒；或双未证时UB变差至少 `max(.001,.05*|U_C|)` **且** gap变差至少 `max(.005,.25*|Δ_C|)`。零目标、微负gap不作无意义百分比。

完整输出M-B/P、M-B/ENS、ENS/P；Seed1仅P/M-B。不得跨实例平均未归一化F、拿截尾cap当证明耗时、把重复Seed当新输入或声称统计显著性。

独立重建后唯一状态：

**BLOCKED**：完整42臂、最终同PE、原问题正确性或必要证据因真实未解决故障不能成立。性能不好、TIE多和正常time_limit不是此状态。

**BROAD_PANEL_SUPPORT**：本轮42臂完整有效、原R109最初冻结的12输入资格与原协议继承成立，并且：

- 12组主M-B/P比较均可评价，WIN>=6、LOSS<=2、严重P回退=0；
- V20/V50/V100各至少1WIN，compact/regional各至少1WIN；
- 3组Seed1均可评价、无严重P回退、至少2组非LOSS；
- 没有同一预指定角色 `Seed0 WIN → Seed1 LOSS` 翻转；
- 无未解决的数值/范围/身份问题，全部ENS损失与MIXED已披露。

**BROAD_PANEL_NOT_SUPPORTED**：42臂完整有效但未满足正面条件；给具体reason codes，如SEVERE_P_REGRESSION、TOO_MANY_P_LOSSES、INSUFFICIENT_P_WINS、MISSING_STRATUM_GAIN、SEED_SENSITIVITY、UNEVALUABLE_COMPARISON。若BLOCKED导致某条件未测，单列“未评估”，不能把缺失Seed/V100写成实际性能失败。

ENS局部损失不是隐藏否决条件。上述是原预定科研候选门槛，不是统计保证。正面状态将冻结ENS-MB收口为论文研究候选，交付规格和有限实测主张；负面状态准确结束本次晋级判断，区分回退与证据不足。三种状态均不自动改默认、不合并、不授权新机制或追加实验。R109的BLOCKED记录不重写。

## 8. 必要机制分析：用实际轨迹识别下一步

只用本轮原始观测与已存在历史证据，不增加求解器调用：

- 初始/最终及UB流分列G、P、lambdaP、sum(weights)、站点总库存/target/返仓载荷、服务站数、每车路径/操作/旅行/处理时间。零目标的物理见证必须完整；固定lambda和max归一化不表示跨V目标权衡恒定。
- 报告真实LP/MIP、child-bound与NEXT targets、AM、实际parent split和最大相关活动叶。R109完成部分没有实际split，R108 L48有真实多叶；不同轮的暴露不能混写。使用已纠正的native_calls与timeline，不能继承旧“0 Optimize”叙述。
- 分列startup、LP、MIP/callback、模型/映射/写盘及外层成本，缺少独立计时则合并，不累加嵌套秒数。实际V100成本待本轮测得，不能预言瓶颈。
- 用已提交证据给实际覆盖的300/600/900/1800/3600检查点及可靠Fstar见证可用时间区间；不将磁盘提交时间当精确native首次发现，不外推未运行窗口。
- 所有材料性损失按 `Δ_A-Δ_C=(U_A-U_C)-(L_A-L_C)` 分解，并与实际Start、初始物理车队、调用路径和UB轨迹对应。端点分解不能独立识别p/d、A/B或branching原因。

G50-C1是事前保留的机制观察：旧两臂初始完整物理车队相同，分别按各自原模型映射Start，不推定所有native列/接受行为相同；约173–175秒到同一库存向量，仅站20比target少1；M-B那1辆返仓库存来自另一车。直接少pickup1会破坏原车辆后续prefix可行性，不能把它称为漏服务一站或可直接修复的多余pickup。新数据应检查这类可行解完成差距是否重复，不能硬编码站20或发起target-feasibility oracle/跨车新算子。

在lambda>0、各站正权重下，F=0等价于Y=D；balanced总库存又要求所有返仓载荷为0。对确有Fstar=0的角色，合法全局L=0已最优。在own U仍>0、根和左子域包含G=0零解、两子LP均可行且实际进入原AM评分的条件下，精确数学中的根/左LP界均为0，最小子域增益为0，不会由该正收益评分触发split；若startup已own U=0应直接闭合，若子域INF则仍走原独立分割/收缩分支，不能概括为“所有零最优实例都不split”。更强约束可能改变整数搜索，但不能以“继续抬高这类实例的全局LB”解释收益，也不能据此强制split。用这些原问题性质解释结果，不包装为本轮新cut或新算法。

报告至多提出两个后续优先问题，每个绑定本轮/历史具体证据、尚缺的识别条件和可否定它的结果。本轮不实现那些优化。若未发现稳定的新瓶颈，明确无需继续堆机制。

## 9. 预算、运行停止与真实故障

本轮重新授权的总额度为96保守启动、110000外层秒，独立于R109；旧51次/18618.079987913487秒保持历史，不转入新轮额度，也不转移旧未启动预付槽。

正式进程图按12组(wrapper+3children)=48次，加3个Seed组(wrapper+2children)=9次，共至少57次。资格最多20次/2000秒，则计划上限77次，余19次启动供真实故障；88200 nominal之外有21800秒覆盖资格、实际封装和必要恢复。实际多一层driver、native测试/解析/导出必须事前计入。声明的保守费用不因未启动而退款，实际启动数另列；避免再设计跨wrapper预付补槽流程。

每组前预留所有剩余正式组最坏nominal与必要收尾；未知早停节省不能预借。实际已关闭的费用如实更新。编译、静态分析、离线Python审查、打包与恢复的工程时间另列；原生资格/测试/诊断/导出及研究wrapper计入预算，native嵌套时间不与wrapper外层重复相加。没有记录的人工耗时写unknown。

**正常正负结果均完成42臂**，即使门槛已不可能或已看似达到。禁止额外Seed、替代输入、旧F2/C2桥接、窗口延长或性能择优重跑。

真实故障先暂停并保留源码快照/命令/输入/PE/raw/退出/费用。只修复本轮获准的实际缺陷，先检查能否完成剩余固定目标，再恢复。纯离线reader修复不触发性能重跑；生产PE一旦在正式开始后变化，任何性能阶段结论都必须基于新最终PE的完整42臂，不拼接。预算不足则BLOCKED。不得为完成任务删掉原输入或放宽验收条件。

## 10. 交付与一次完整独立复核

复用R109最终有效reader、证据格式、分片和恢复工具。旧失败源保留并显式标superseded/active correction关系，避免旧错误叙述再次变成结论；不复制一套大而重复的新审计体系。

必须交付：

1. `research_decision.md`、`repair_scope.md`、实际故障到修复的证据、最小源码diff、解析/模型等价与最终PE实际入口资格、5个功能CLI、真实进程图/预算、独立admission。
2. 原12输入精确身份、原初前瞻冻结继承与本轮已见范围、42条完整argv及固定顺序；新生产源码/PE/DLL/build身份和R109差异。
3. 本轮全部42臂raw与可重建表：own完整车队/UB流、合格完整域LB/证书、native model/type/Start/call/scope、实际split/覆盖、time partitions/checkpoints、三类主配对/Seed1/翻转/严重损失、全部费用、失败和缺失。
4. `selection_decision.json`、`final_report.md`：唯一状态、每条门槛、完整正负结果、真实V100与Seed范围、最差损失、修复影响及局限；旧24结果另表，不并入新分母。
5. 更新 `paper_candidate_spec.md`：统一问题、ENS-MB流程/伪代码、整数等价、A/B、界scope/覆盖和终止依据；区分历史数学贡献、本轮工程修复及新增确认。正面/负面/BLOCKED均交付准确版本，不能称论文benchmark全部完成。
6. 独立reviewer从实际raw独立核对核心物理、界覆盖、数值拒绝/floor、clock、完整12/42分母、Seed、预算与最终决定；可复用可信通用解析，不能只读主summary。

逐组完成必要数据核验；最后一次完整主重建、一次独立raw/决定复核。只有具体新缺陷才追加修复验证，不以审计次数/文件量为成果。

保留必要raw与每次实际失败，精确去重可以但必须保留原模型路径/身份映射。公共包仅含本轮必要证据及少量明确历史依赖，不再打包整个R109大载体；分片遵守Git单blob限制，保存每片与合并hash，不发布PE/DLL/license/凭证。

实际执行新公共目录export、空目录restore、从恢复根到全部发布CSV/决定JSON的全字段比较，以及恢复根中的独立复核，保存cwd/source/launch/exit/receipt。无原worktree回读；用兼容Python与原浮点口径，不为逐位相等改数值。这是证据/数学恢复，不是第二轮引擎性能运行。

## 11. 新 stacked Draft PR 与最终收口

建立新的英文research Draft PR，base为核验后的R109分支，建议标题：
`Round110: repair native entry and confirm the frozen M-B panel`。

PR开头明确唯一阶段状态、入口故障与实际修复、同最终PE42臂是否完成、完整P收益/风险和ENS代价。说明这是原面板恢复确认、8角色已有旧观测、原V100/正式Seed缺口如何处理；分清物理T/cap/实际时间、原生数值错误与证据恢复、数学贡献与工程维护。

不改旧PR结论、不合并、不替换默认ENS、不修改无关用户文件。推送后实际核验远端head/base/open/draft、关键科学文件和分片字节。区分实测生产源、科学payload与后续receipt补充，不循环声称当前commit已含自己的后续验证。

最终交付前再做一次简明的**分析与任务目标复核**：实际数据是否支持最终叙述；被撤回的旧机制解释是否仍残留；阶段条件是否逐项匹配；有没有因正负结果改输入/算法/分母；有没有把未测写成失败、工程修复写成新算法、或在预算之外自动启动实验。只修正真实不一致，不新增研究范围。

最终回报PR链接、完整性、唯一决定、12主角色/3Seed组表、最差损失、修复/数学/物理/覆盖/恢复验证结论、实际资源和至多两个有证据的后续问题。获得正常完整结果时必须作出支持或未支持的明确判断；不能再以“还可多试一个机制”回避本轮收口。
