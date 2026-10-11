/goal

# Round111：等价精简 Seed 审计，完成固定六臂补充确认并收口研究阶段

你负责本地 C++ 项目 `yifanXovo/TailoredExact` 的本轮实施、完整有限评测、独立复核与新 stacked Draft PR。

**唯一目标：保持 R110 生产 PE、算法、模型、输入和求解参数不变，消除当前 Seed1 必要审计中的可证明冗余；在原完整时间口径下，一次运行原三组 Seed1 的六臂补充确认，结合不可变的 R110 主面板，作出明确的研究候选阶段判断。**

本轮不开发算法机制，不重跑42臂，不改变30秒收尾reserve，不延长cap，不以同一测试反复重跑追求通过。新增正式集合只有六臂、12600 nominal秒；预算 **24次保守启动 / 18000外层秒**，资格最多 **8次 / 600秒**，包含在总额内。

## 1. 起点与应当继承的真实结论

核验 PR172 / `codex/round110-entry-repair-frozen-panel-confirmation`。本任务编写时最新head为
`13ed7eeb83b647f585837638ed9158b84f274d66`；
实测生产修复commit为 `382cbcddc00fad4b1ed44fe8e9d9862f77cf5fba`；
冻结科学payload为 `c4efe042bc6654ccd2e14b7e0d65c904a15d3390`。
实际 PE SHA256：
`c0384284aefd5aa2acc5d885ef37b0cfad6f93d083a5feb9ee693c41a786b411`；
Gurobi13.0.2 DLL SHA256：
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

开始读取适用AGENTS.md，核对最新远端、本地HEAD、用户修改、活动进程、已有本轮记录。建议隔离分支/worktree `codex/round111-seed-block-confirmation`，结果目录 `results/unified_exact_round111/`。按RESUME续接已有进度，不覆盖旧raw或重复启动已完成正式臂；新提交先读差异，不默用过期身份。

必读R110 goal、final_report、protocol、input_manifest、candidate/production identity、repair/qualification/admission、current_numerical_evidence、strict_full_clock_assessment、reports_final、mechanism_analysis、paper_candidate_spec、最终有效独立复核与public恢复说明；定位实际wrapper与Seed审计调用链。R108/R100只读取与候选独特价值、整数等价和实际split有关的指定证据，不重做全历史研究。

不可改写的事实：

- R110的全部42原生尝试正常结束，生产入口修复成功；12个主配对完整。不是“V100未测”。
- 正式完整时钟仅41臂合格。arm42/G100-R2/Seed1/M-B：native_end累计3571.0120709999464秒，必要audit结束3600.707823600038秒，whole为3600.7215734999627秒，超过cap3600。必要audit本身耗29.69575260009151秒；删掉末尾约13.75ms写盘不能解决。原native-only within_cap=true保留，但不能用于正式准入。
- R110仍为BLOCKED，第三Seed配对UNEVALUABLE。旧arm42的自身物理UB及描述性优势不构成原协议正式WIN，不加1秒容差、不截断时间、不回填旧决定。
- 主M-B/P与ENS/P均11WIN/1TIE；M-B/ENS为5WIN/3TIE/4LOSS，G50-C1、G100-R2严重。11个P-WIN角色集合相同，不把全部收益归因于M-B增量。
- R108 C2曾有ENS/P LOSS而M-B/P WIN，说明候选有修复主要benchmark缺口的历史价值；也须保留R108 F5等代价。允许对ENS有公开取舍，不引入ENS点态支配的隐藏门槛。
- R109与R110旧状态及分母均保留。ENS-C继续默认，原cold P-GRB继续主要benchmark。

先写简短 `research_decision.md`：本轮只修复等价的外层执行方式；主证据来自R110、补充Seed证据来自R111；六臂是事前固定的完整Seed块。只复验失败角色两臂也可作为技术恢复，但本轮选择多付5400 nominal秒，使全部三组Seed判断来自同一新wrapper/准入，不再逐个补票。已见角色与重复Seed不增加独立样本量。

## 2. 修复范围：验证谓词不变，减少实际重复工作

生产PE与205个生产源绑定保持R110身份。不得重新编译替换PE、改Parser/栈/编译器/Gurobi/优化设置、改模型或native argv。若必须改变生产PE或算法才能完成，停止并给BLOCKED；本轮不自动扩大为42臂。

先用既有raw做离线profile，分列必要入场检查、Seed proof、模型读取/解析、变量分类、A/B行、scope/return、物理核验与写盘；不把嵌套计时相加，不把组内第二臂arm42无依据归因于first-arm历史admission。

已识别的源码线索：

`round109_seed_audit.adapter -> round109_seed_scope.qualify -> round100_campaign.adapter`。
Seed0核settings后提前返回，Seed1还执行完整model/type/A-B/scope合同。
`round108_reader.model_contract` 在每站遍历全部列并做state正则匹配；随后scope检查又可能构建同一rows的Counter。
这些是待实测量化的冗余候选，不把源码复杂度估计冒充已测耗时归因。

优先实现本轮独立的薄adapter/纯函数优化，不改写历史reader文件或其冻结证明身份：

1. 对当前模型列做一次保持原语义的分类/站点索引，替代每站重扫全部列。保留数量列后缀规则、原完整正则、重复行Counter及A/B精确条件；不能把 `state_01_*` 通过整数化名称误归入原 `state_1_*` 集合。
2. 同一臂内、同一不可变模型的纯解析/Counter可复用；键绑定完整模型内容SHA及解析器/合同版本。path、mtime、长度或旧文件名不足以授权复用。每次复用前核对当前bytes身份。
3. 每call的实际Seed/九项参数、integer/type恢复、true-G域、cutoff/epoch、返回、scope和provenance继续单独核验；不能以“同模型”缓存不同call的合法性结论。当前LP、MIP、正G右子域和被拒界调用继续区分。
4. cache在每臂结束时清空，不给另一臂复用动态模型解析、Start、UB、cut、scope结论或运行成本。静态参考/历史签名的既有合法处理保持原口径，不能漏计必要入场工作。
5. 所有当前臂必要物理/模型/范围/返回验证仍在原完整时钟内。不得仅把耗时校验移到cap外、减少必须检查的条件、改证书门槛或修改实际搜索窗口。

仅保留有实际收益且已证明输出等价的小修复。不要顺便重构整个跨轮工具链、换Python/数值库或建立一套新审计系统。优化失败也交付其原因，不能用删除检查换取通过。

## 3. 正式前资格：旧raw重放与两项实际CLI

### 3.1 固定离线等价与成本检查，零Optimize

冻结旧raw样本与比较口径后再修改实现。覆盖R110全部六个Seed1记录、两项H100 Seed1功能记录，以及P15/P17/M-B25/P26现有数值拒绝、missing-return和scope边界的有限回归证据。旧raw只读；输出写新目录。

对新旧必要audit的数学结果、接受/拒绝、实际参数、类型、A/B、scope、UB/LB/cover、未知字段和raw flags逐字段比较。仅路径、当前实现/receipt身份、本次重放耗时等非数学元数据可在事前白名单中另列；不能忽略任何决定性的差异。R110原native_end/audit_end/whole、原时间区间、正式资格与arm42 UNEVALUABLE不属于白名单，不能用新重放成本重算旧运行资格。被损坏旧记录的等价终点是原已验证拒绝/恢复政策，不要求旧false flag变true。

加入少量针对本次索引/cache变化的反例：名称/后缀边界、缺失或重复A/B行、类型改变、相同路径替换bytes、相同模型但不同Seed/call/true-G/cutoff/epoch。合法变化须重新核验，非法变化须正确拒绝。保留原Counter>=1语义：合法冗余的重复A/B行不能被新实现拒绝，缺失所需行才应拒绝。不要建立会把所有scope变化一概拒绝的假测试。

对六个正式旧Seed记录各做一次新审计fresh-process重放，并对最大已知费用的arm42再做两次，共三次arm42 fresh-process观测；从空的臂内cache开始。原旧审计至少在arm42实测一次分阶段profile，保留全部测得值，不取最佳一次。其它已有效旧输出可直接用于等价比较。

事前工程准入：上述新审计重放的**每次必要postexit处理均<=15秒**；同时列出实际必要入场成本和已知native观察/退出开销，说明30秒reserve仍有明显余量。15秒仅是固定机器上的保守经验准入，不是硬实时最坏界，不是求解过程中的定时切换，不通过则不能开始六臂长跑。不声称有限观测证明Windows/IO永不超时。

如果profile表明另一个同类可证明冗余才是主因，可在本节范围内作最小修复；保留具体证据并复核受影响项。若新旧谓词无法等价，或获准修复后仍不满足经验准入，结束为BLOCKED/ENVELOPE_NOT_QUALIFIED，不启动正式长跑。

### 3.2 新wrapper的有限实际资格

复用并验证R110同一PE/DLL、原生产绑定、12输入解析/矩阵等价和入口资格，不重复编译、12次解析或整套五CLI。
仅在原固定H100（实际V20/M2）上运行Seed1的P、M-B两个CLI，每臂cap<=120秒；验证新wrapper完整走过实际Seed审计、必要LP/MIP与适用Start/type路径、完整物理核验、正常返回及全部时钟写入。不是性能样本，也不替代V100旧raw资格。

资格最多8次保守启动/600外层秒，包含于总预算。两个CLI和wrapper按实际进程图计费。原生解析/导出即使0 Optimize也计入；纯Python旧raw重放、静态分析和独立数学审核为另列工程时间。

### 3.3 一次正式准入

独立reviewer签署 `performance_admission.json`，绑定最终未变PE/DLL、生产身份、全部新helper、等价/profiling/CLI证据、原输入与六条完整argv、下面的数值/时间政策和组合阶段规则。正式arm1不得早于签署。

准入包含对R110主36臂资格的只读承接：身份、原完整时钟/区间与12配对逐项核对。15/17/25/26原表有些qualification列为空，须从合法区间及原证据显式推导当前导入资格，保留原空值；不能把空字段直接当false，也不能由native flag直接补true。不重做R110全量原始矩阵审计。

## 4. 固定六臂：同一PE、同一新wrapper、原顺序

精确复用R110 input_manifest和原37–42号launch的数据/参数，生成本轮编号1–6与旧编号映射。保持输入原bytes/SHA，不重新生成，不添加Seed。

|新编号|对应R110|角色|V/M|Q|物理T秒|Seed|方法|每臂cap秒|
|---:|---:|---|---|---|---:|---:|---|---:|
|1|37|G20-C2|20/2|20,40|7200|1|P-GRB|900|
|2|38|G20-C2|20/2|20,40|7200|1|M-B|900|
|3|39|G50-R1|50/4|20,25,35,40|7200|1|M-B|1800|
|4|40|G50-R1|50/4|20,25,35,40|7200|1|P-GRB|1800|
|5|41|G100-R2|100/8|30×8|18000|1|P-GRB|3600|
|6|42|G100-R2|100/8|30×8|18000|1|M-B|3600|

三组串行，每组一个直接wrapper、两个native children；不并行求解、编译、压缩或重型审查。总12600 nominal秒、至少9启动。路径/输出目录/轮次和新wrapper身份之外，逐项核对native argv与R110对应臂一致。

P保持原cold compact；M-B保持完整ENS框架，实际preset为 `research-round83-vds-equal-net-exchange`，仅附加 `--round98-state-service m-binary`，effective identity为 `research-round99-ensc-discrete-structure-m-binary`。`--round100-continuous-quantities` 为false。

保留VD-P/F0、24+1 startup及physical closure/handoff、AM=.08、原深宽/cover/epoch/cache/target/terminal、整数route/load/Y与二元state/assignment/direction。p/d仅声明连续，原两条A/B行不变：
\[
\sum_k(p_{ki}+d_{ki})=\sum_{y\in S_i}|b_i-y|s_{iy},
\qquad \sum_kz_{ki}=1-s_{i,b_i}.
\]
整数完整解下隐含数量整数的前提与原物理检查不变；LP不据此强行整数化。

所有物理含义继承R110：每站至多一车一次非零单向整数操作；空载出发、每个prefix与返仓载荷在[0,Q]、允许带载返仓、Y在[0,C]、没有min_ratio下限。累计pickup可超过Q；含返仓卸载的闭环时间为旅行加120×累计pickup。目标仍为真实Gini of inventory-to-target ratios加lambda×weighted relative target deviation，lambda=.15、pickup/drop各60秒、原max归一化权重。

Threads=mip_threads=1、Presolve=Auto、原FeasibilityTol/OptimalityTol/IntFeasTol、MIPGap=MIPGapAbs=0、Seed1、原单核affinity与cap内30秒reserve全部不变。各臂独立支付工作，无跨臂UB/Start/cut/cache共享；不按实例、规模、库存、几何、已知最优或运行轨迹选算法。

## 5. 时间、数值和证书政策

正式前冻结政策，沿用R110最后有效规则。原始记录不可改；helper优化只改变等价计算方式。

- 完整时钟从该臂必要准入/身份检查开始，包含自身startup、全部native、callbacks、写盘、必要postexit物理/模型/scope审计和原crosscheck。保存native_end、audit_end与whole三类回执，必须如实给全程时间。native-only within_cap不覆盖whole；不把cap或legacy数值替代精确时间。
- 当前动态校验不能移出计时。未来独立研究复核、全量离线矩阵反证与公共恢复仍按既有工程口径另列，不反加旧运行时间。
- 所有UB来自该臂自身完整合法物理车队。外部或其它臂见证只能离线反证，不能成为该臂UB/Start或搜索信息。
- 原生LB仅在匹配模型、真实G域、cutoff/epoch、类型、实际返回和完整覆盖下使用。数值反证必须处于该call有效域，满足对应列/行/界/类型；域外零解不能否定正G叶界。
- 确认矛盾后拒绝该call全部native lower claims，并撤销必要依赖它的派生界、closure/删域；保留独立合法证明，重建完整覆盖。被拒MIP与其它有效LP不得混同。
- 当前输入非负目标的全域F>=0可独立使用；own精确物理F=0可认证，own U>0而仅有floor时保持未认证。拒绝原生界不表示引擎数值问题已修好。
- 缺失returned journal、原false flag、null精确时钟与失败记录保持原样。正常返回须有匹配call/model/log/API/cleanup/退出的独立证据，不能仅凭rc0推出界正确。
- 合法原始记录只能给出区间时，采用向外界；只有整个区间矩形内分类/严重性不变才能评价。超cap、unknown或不合格不填TIE，不挑端点给精确speedup。微负signed gap与百分比eligibility保持原规则。
- 已知故障类型仅在事前政策和本次记录全部条件满足、经独立核验后恢复。出现新的数学或范围缺陷先暂停；不能临时为某个输赢设计tuple豁免。

## 6. 新的分层阶段判断，旧结论不可回写

本轮唯一正式Seed集合是新六臂。旧R110六Seed记录单独保留作历史，不以旧好结果替换新差结果，不新增独立样本数。

明确标注证据层：
**R110_MAIN_36_PLUS_R111_SEED_6**。
这是同一生产算法的跨轮分层确认；主pair各自在R110的执行规范下比较，新Seedpair各自在R111同一新wrapper下比较。不能称全部42在新wrapper测得，不做跨wrapper精确speedup，不把旧all42_valid_formal改成true。

沿用原配对门槛。候选A、对照C：
\[
a_U=\max(.001,.01|U_C|),\quad
a_\Delta=\max(.001,.10|\Delta_C|),\quad
a_t=\max(30, .10t_C),\quad \Delta=U-L.
\]
仅A认证为WIN，仅C认证为严重LOSS；双证按完整时间材料性判WIN/LOSS/TIE。双未证且合格有限：UB/gap至少一项材料改善且无材料变差为WIN，反向为LOSS，双向均有为MIXED，均无为TIE；不合格或不可比较为UNEVALUABLE。
严重性保留原规则：仅C认证；或双证t_A>=2t_C且多至少120秒；或双未证UB变差至少max(.001,.05|U_C|)且gap变差至少max(.005,.25|Delta_C|)。

三个唯一终态：

**CONFIRMATION_SUPPORT**：R110主36臂和原12配对的合格身份/证据可承接且原主门槛满足（WIN>=6、LOSS<=2、无严重P回退、各V与各geometry至少1WIN）；本轮六臂全部合格、三个Seedpair均可评价、无严重P回退、至少两个非LOSS、无R110 Seed0 WIN→R111 Seed1 LOSS；无未解决正确性/身份/范围问题，全部ENS代价已披露。

**CONFIRMATION_NOT_SUPPORTED**：本轮六臂有效完成且证据承接成立，但原性能/Seed门槛不满足。具体报告实际失败条件，不把正常LOSS、TIE或time_limit称为工程BLOCKED。正常完整运行却未得到足够数值（例如没有自身可行解）形成的UNEVALUABLE，记INSUFFICIENT_COMPARISON，不自动当工程故障；真实时钟/正确性不合格仍按下述BLOCKED。

**BLOCKED**：同PE/等价审计/经验准入、当前正确性、完整时钟或资源存在真实未解决障碍，不能形成上述完整判断。缺测条件写未评估，不写Seed敏感或实际LOSS。原生均结束不等于所有完整观察合格。

SUPPORT时冻结有范围的ENS-MB论文研究候选并给出准确收益/代价；NOT_SUPPORTED时结束这次候选确认、明确未支持的原因；BLOCKED时列出不可满足的前提与已有证据。三者都不自动改ENS默认、不合并、不授权新机制或下一轮同类重跑，也不声称统计保证或论文benchmark已经全部完成。

## 7. 只用已有证据完成研究定位

交付一张简明 `contribution_evidence_map.md`，逐项列数学/算法主张、实际源文件、已支持范围和未支持推断：

1. 原物理模型、p/d隐含整数性、A/B有效性、true-G域与完整覆盖来自历史数学；本轮审计提效是工程改进。
2. ENS框架相对cold P的收益，M-B修复R108 C2主要benchmark缺口的独特证据，以及R108 F5、R110四项ENS损失；不把11个共同P-WIN归于M-B增量。
3. 实际机制暴露：R108 L48的ENS/M-B各两次真实parent split，一次保留不可行半域的分割、一次AM正评分分割，各最多两个相关活动叶；不能把AM评分split数当全部atomic_split数。R110零实际split、最多一叶。lookahead/child-target模型不是已发生的多叶分解。
4. G50-C1两轮同Seed0反复出现相同初始完整车队、3LP+terminal MIP和one-bike gap；不是独立Seed稳定性证明，也不是HGA-only。G100-R2主要差距在own UB，零最优尚未证明。不得把全部历史失败统一归因于primal或LB；既有F2存在获得目标见证与完成认证之间的差距。
5. V100实际startup、LP、MIP成本因角色而异；固定lambda和max-normalized weights不能保证跨V权衡恒定。单源坐标/容量、合成库存/目标/车队/T、重叠子集、少量Seed限制外推。

对G50-C1/G100-R2，允许只读回放已有车队，检验明确指定的单站数量调整是否满足原物理约束；只有实际回放证实时，才能说明违反哪项后缀载荷/时间限制，不预设两角色同因。任何反事实非法车队不是新UB。lambda>0、正权重时F=0 iff Y=D；已证明Fstar=0的全局L0已经精确。AM的零最小增益推导必须保留ownU>0、零解在根/左域、两子LP可行及实际评分条件；startup零闭合和INF独立分支保留。G100-R2不得套用未证明的Fstar0。

更新 `paper_candidate_spec.md` 的阶段与证据范围，保留统一伪代码、整数等价与覆盖/终止条件。结尾至多列两个有证据、可被否定的后续研究问题，说明还缺的识别条件；不实现新cut、target-feasibility oracle、跨车算子、branching/Start/模型消融或新benchmark。不能以“再试一个机制”回避本轮明确结果。

## 8. 预算与不重复运行规则

独立总上限24启动/18000外层秒；资格8/600已包含。正式三wrapper+六children为9启动/12600 nominal秒；资格上限后计划最多17启动/13200秒，余7启动/4800秒只应对真实获准故障。实际进程图多出的driver/原生测试先计入，不借未知早停节省，不退还已声明未启动槽，native嵌套秒不重复加入wrapper费用。

每组前确保剩余全部固定正式臂的nominal与必要封装空间仍足够。正常正负表现都跑完六臂；不以达标或无法达标提前结束。真实未解决故障暂停，保留raw、退出、源码与费用；若只是离线reader问题且原测量合格，在预算内修复证据后可续未启动臂，不重跑性能。

**正式臂每个只启动一次。** 超cap保留真实无效结果，不换Seed、不只补M-B、不延时、不追加第二套六臂。正式开始后，生产PE与已准入的性能wrapper/helper实现、当前计时工作量及数学/时间谓词均冻结；即使仅是等价提速，也不能在六臂中途更换实测wrapper身份。必须改变这些内容时，本轮不能拼接或自动重启，交BLOCKED并明确未完成项。获准的纯离线证据修复不改变实测身份。

记录资格、正式、离线工程的真实进程与时间，未知人工耗时写unknown。工程工作应复用当前可靠工具；只有明确新缺陷才追加受影响复核，不能再以审计次数/百万检查数/大载体规模当研究成果。

## 9. 交付、公共恢复与一次完整独立复核

必须交付：

- research_decision、实际审计成本profile、最小helper diff、原/新谓词等价与反例、经验余量与两CLI、独立正式admission。
- 原PE/DLL/生产身份，新wrapper/helpers与六完整argv、原输入SHA、固定顺序、全部raw/receipt/费用；原native flags和真实错误完整保留。
- 新六臂own完整车队/UB流、合格LB/证书/cover、calls/模型/type/Start/Seed、native/audit/whole时间、三Seed配对与翻转；异常/null/区间字段口径一致。
- R110主12比较的明确只读导入表与provenance；新旧Seed分表；selection_decision.json、final_report.md、contribution_evidence_map与paper_candidate_spec。
- 独立reviewer从本轮实际raw重算六臂核心物理、scope/cover、拒界/floor、完整clock、Seed分类及组合决定；对R110主证据核对固定来源与原合格资格，不声称重新完成其470MB全量raw审计。

公共包只纳入本轮六臂及审计等价所需的有限旧fixtures/明确依赖；R110旧主证据按固定commit、SHA、已执行审查与必要表导入，不再复制整个R110载体。先检查依赖闭包和缺失文件，再打包，避免导出后才发现遗漏历史authority。复用现有去重/分片/恢复工具，不发布PE/DLL/license/凭证。

实际完成一次新的export、空目录restore、从恢复根重建并逐字段比较本轮CSV/JSON、恢复根独立raw/组合决定复核，保存实际cwd/source/launch/exit/receipt，不回读原worktree。必要历史依赖精确声明；继承部分与本轮重算部分明确区分。只有实际失败才修复并重做受影响步骤，不循环全量重审。

## 10. 新 stacked Draft PR 与最终额外复核

新英文research Draft PR，base为核验后的R110分支，建议标题：
`Round111: qualify audit overhead and confirm the fixed Seed block`。

PR开头写唯一状态和证据层 `R110_MAIN_36_PLUS_R111_SEED_6`，解释为何旧R110仍BLOCKED、为什么只重固定Seed块、哪些工程改动保持谓词/PE不变。报告新六完整性、三pair、最差P/ENS风险、当前论文研究阶段、实际资源和局限。

不修改旧PR结论，不合并，不替换默认ENS，不修改用户无关文件/代理/权限。推送后实际核验远端head/base/open/draft和必要科学文件/分片身份，区分科学payload与后续receipt，不循环声称commit已包含自己的后续验证。

最终交付前额外进行一次分析与目标复核：数据是否支持阶段结论；旧无效arm42是否仍无效；有没有新旧择优、跨wrapper精确speedup、遗漏ENS代价、未经证明的zero optimum/AM/因果主张；有没有把验证工作移出cap、把工程提效写成算法贡献、或自动新增求解任务。只修正实际不一致。

最终回报PR链接、新六完整性、唯一阶段、三Seed配对、继承主结果与代价、修复/等价/物理/范围/恢复结论、费用，以及至多两个有证据的后续问题。完成可评价结果就明确支持或未支持；真实BLOCKED则说明哪项前提失效，结束本轮有限计划。

