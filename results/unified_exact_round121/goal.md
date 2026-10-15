/goal

# Round121：冻结 MB-D1，完成有限的新输入确认与 Seed 风险检验

你负责 `yifanXovo/TailoredExact` 的本地执行、当前证据核对、有限确认、阶段判断及英文 stacked Draft PR。

**唯一任务：不改变 R120 的 MB-D1，检验其收益能否延伸到三个事前固定、未参与开发的 V30/V40/V50 输入，同时用固定 Seed1 对照检查 F2 认证收益与 R98-C2 主 benchmark 风险。最终决定这个冻结配置是否值得作为论文候选继续评测。**

这不是再开发一个选择器、cut、branching 或几何机制。R120 已经满足原准入，不能事后追加“必须逐例胜 M-B/ENS”的条件；也不能把 C2 的损失抹去。P-GRB 是主要 benchmark，M-B 是完整方法直接对照；D0 只在一组预定消融中出现，不是备用候选。ENS-C 仍为默认。V≤50，本轮不运行 V60/V100。

本轮固定 **16 个正式臂、18 个配对位置、3 个新问题、2 个已知问题的 Seed1 检查**；全部正常结果完成后给出一个决定。不按结果追加输入、Seed、窗口或算法修改。

资源总上限 **40 次保守启动 / 48000 外层秒**；资格子上限 **8 次 / 1800 秒**，包含于总额。正式名义窗口37200秒，五组管理预留600秒不延长单臂求解时间。正式位置最多一次，不以重试挑选性能。

## 1. 继承身份与验收范围

核验 PR182，分支 `codex/round120-native-proof-disjunction`。本任务组织时 head：
`4872eb8421e43e57ef6e3727db4cd40e1c14f935`。

冻结生产 source-before-native：`355eefd2be3fe5651195681faf7b3a63ee4032f8`；
PE SHA256：`5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba`；
Gurobi13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

先读 AGENTS.md，核对实际远端、本地用户修改、活动进程及创建时间、费用、RESUME和是否已有同身份执行。建议分支 `codex/round121-frozen-d1-confirmation`，结果目录 `results/unified_exact_round121/`。不覆盖用户工作、不改代理/权限，不默认 main 是最新研究状态。

读 R120 的 goal、final_report、mathematical_contract、core_admission、stage_decision、production/candidate identity、qualification_summary、三组实际重建结果、extra_review及恢复范围补充。R118 的完整 paper_algorithm_spec 与 R117 安全边界继续适用。只读取安全的现行版本，不恢复旧污染网页/载体。

保留事实：R120 12臂完成；F2 的 D1/D0/M-B 认证时间208.145/476.408/774.409秒；C2 D1/M-B严重LOSS、D1/P非严重LOSS、D1/D0 WIN；N40 D1对三项对照的开放U/gap为WIN，但LB略弱，仍未认证。全部D1/D0安装了一个根选择器；实际h固定/branching仍未知。阶段是 `ADVANCE_NATIVE_PROOF_DISJUNCTION_TO_CONFIRMATION`，不是默认晋级。

R119 MB-PC 保持停止。R120 的旧尾部补测已经完成，不再重开。恢复中的tuple/JSON-array比较及六个derived sidecar根路径变化已有明确补充，不能把它们误写成原始raw被替换，也不能声称展开目录在重建后全部字节不变。

## 2. 统一冻结算法与物理合同

服务站 i=1..V，排除depot0：
\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad r_i=Y_i/D_i,
\quad F=G_{\rm true}+\lambda\sum_i\omega_i|r_i-1|.
\]
沿原S=0 Gini约定；0≤Y≤C；空载出发；每站至多一车一次非零单方向整数操作；全部前缀和返仓载荷在[0,Q]；允许载车返仓并支付卸载。完整路线时长为travel+(pickup_seconds+drop_seconds)×累计pickup。Q不限制累计pickup。min_ratio不形成库存下限。

M-B保持p/d连续声明、Y/load整数、s/z/m二元与原A/B；独立ENS-Q不启用。H仍为原Seed20260626、24+1及完整closure/exchange，**改变Gurobi Seed不改变H的种子或规则**。冷P不接受H、外来U或Start。

D1只沿R120在原根首次整数Optimize之前，利用本臂自然付费且合格返回的左右根LP证明：
\[
\underline\beta_j=\max\{0,\operatorname{down}(\min(\ell_j,c_j)-10^{-7})\},
\]
再以实际保守序列化系数加入原二元h和三条行：
\[
g\ge a+(m-a)h,\quad g\le m+(b-m)h,
\quad f\ge\underline\beta_0+(\underline\beta_1-\underline\beta_0)h.
\]
D0保留同h、链接及共同标量floor。f包含实际ObjCon，任意native g不自动等于真实G。保留原物理目标保持嵌入、作用域/cutoff补集、实际端点舍入、Start、VType和完整覆盖合同。

原AM直接分裂、证明未及时齐全或H已结束时，候选按原规则不曝光；不得强制求根、额外探测或在后代补装。根已安装后的原target/terminal与必要epoch/domain行为不变。不得声称完整算法仅一次Optimize或已保留整棵原生树。

本轮不重编译生产PE，不改src/include、模型/目标、三行、舍入余量、AM、cutoff、startup、数值容差或分支参数。必要的manifest/数据与只读输出适配不改变上述行为。生产身份不可恢复或有真实数学缺陷时停止并报告，不能静默换PE。

## 3. 一项零求解的数学澄清，不增加新资格平台

R120证明的是扩展(x,h)空间非冗余，且两个完整D0/D1原目标LP最优值相同。不得改写为“原变量投影一定严格缩小”或“根LP目标提高”。

对已保存的F2/C2两份D0最大违反见证，只读计算保持全部原变量x不变时，是否可以仅重新选h使D1可行。对理想系数：
\[
h_{\min}=\max(0,(g-m)/(b-m)),\quad
h_{\max}=\min(1,(g-a)/(m-a)).
\]
目标右端的最小值在beta1≥beta0时取h_min，否则取h_max。实际判断使用完整保存行的真实系数、ObjCon及原误差标准，不把理论端点当成已序列化端点。

例如a=0,m=1,b=2,beta0=.2,beta1=1，g=.5,f=.3,h=.5违反D1，但改h=0后原(g,f)仍可扩展。正的单点扩展空间违反不自动证明原坐标被排除。

这项分析只澄清证据范围，不撤销R120原已满足的扩展空间准入，也不成为新正式测试的筛样门槛。若旧primal缺失就标明该诊断未知；不追加LP、oracle或全历史恢复来追求答案。不把解析出的新界/见证反馈正式臂。

## 4. 新输入必须先冻结，再生成一次

使用R117安全版本中的固定Capital Bikeshare站点表，不访问网页、GBFS或许可证端点：
- 源站点响应SHA：`d4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8`。
- 表SHA：`d982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa`。
- 865站点源身份沿原记录；本轮不重新投影、过滤合法站点或抓取替代快照。

新FAMILY固定为：
`round121-frozen-d1-confirmation-v1|source_sha256=d4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8`。

|新输入ID|V/M|地理/replicate|库存|Q向量|物理T|产出cap|selection_id|
|---|---|---|---|---|---:|---:|---|
|Q30-C2-B|30/3|compact/2|balanced|[20,25,30]|7200|1800|cabi_r121_V30_compact_r2|
|Q40-R2-S|40/4|regional/2|shortage|[20,25,35,40]|10800|3600|cabi_r121_V40_regional_r2|
|Q50-C2-U|50/4|compact/2|surplus|[30,30,30,30]|10800|3600|cabi_r121_V50_compact_r2|

三个文件放在 `reference/round121_confirmation/`。这三个新ID不能与旧R98-C2混用；U仅是新ID标签，库存按surplus规则，不表示所有站都在高库存区间。

薄适配复用R118的安全源加载和原R57 selection、R109 landscape数学：原四anchors、ties、compact/regional、target .44–.56、坐标3位、权重6位、总量修正、sign repair和depot centroid不变。将old.FAMILY及landscape实际VERSION/SOURCE_SHA一致设为本轮固定身份；不要直接调用会重新写回R118 FAMILY的旧wrapper后声称用了新盐。

库存差额 delta_amount=max(V,floor(.12*sum(D)+.5))；shortage总量=max(0,sum(D)-delta_amount)，balanced=sum(D)，surplus=min(sum(C),sum(D)+delta_amount)。局部扰动按原balanced .18/其余 .30；权重沿原max归一化，lambda=.15，装卸60/60。

在生成前提交recipe、adapter和完整角色/运行表；实际sum(D)、最优值、H/LP/MIP和难度未知。每个输入只生成一次。检查容量/目标/空路线物理可行性、维度、来源和历史SHA重复；合法的易例、全零证书、困难例或不利例保留。精确重复或真实数据错误须报告，不能重抽盐、换replicate或调T/Q。

报告与旧R116/R118子集的重叠；三个实例来自同一已知来源，不是三个新城市或IID样本。新确认是未用于D1开发的新输入，不是首次接触这个城市。记录sum(w)、G、P、lambda*P；跨V的lambda*sum(w)变化不能冒充纯规模效应。

## 5. 固定运行表：16臂、18个配对

|组|角色|Gurobi Seed|产出cap|方法顺序|名义秒|
|---:|---|---:|---:|---|---:|
|1|F2|1|1200|MB-D0 → P-GRB → MB-D1 → M-B|4800|
|2|Q30-C2-B|0|1800|P-GRB → MB-D1 → M-B|5400|
|3|R98-C2|1|1800|M-B → P-GRB → MB-D1|5400|
|4|Q40-R2-S|0|3600|MB-D1 → M-B → P-GRB|10800|
|5|Q50-C2-U|0|3600|M-B → P-GRB → MB-D1|10800|

F2沿 `reference/round86_unadapted_confirmation/F2.txt`，SHA `ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e`，V20/M2/Q[30,30]/T3600。
R98-C2沿 `reference/round98_confirmation/C2.txt`，SHA `07d0964c87b534254e6bf2957911859a6a2bd73e377211728b7e65f44294fc76`，V30/M3/Q[20,25,30]/T7200。

F2保留R120六项配对；其余四组每组D1/M-B、D1/P、M-B/P，共18。D0只用于这一次固定Seed1条件信息检查，不延伸到新三组、不因结果好而被选为候选。P-S和ENS-C不另增正式臂；旧证据保留但不冒充本轮同构建对照。

Seed1是固定敏感性检查，不是调优，不能取两Seed最优值。R120 Seed0完整记录单列，不与本轮拼接精确平均时间或总体胜率。新三输入是3个问题，不是9个独立样本；两个旧Seed块也不是2个新问题。

所有方法沿同PE/DLL/机器与原affinity，Threads=mip_threads=1、PresolveAuto、MIPGap=MIPGapAbs=0、原FeasibilityTol/OptimalityTol=1e-6、IntFeasTol=1e-5和1e-7证据政策。除表中预定Gurobi Seed外无参数变化。每臂独立支付H、LP、Start和缓存，不复用跨臂证明或诊断解。

## 6. 最小实际准入，不重做上一轮原生矩阵网格

复用R120已通过的call-scoped记录器、三时钟、类型恢复、实际ObjCon和Start审计；禁止把模型Fingerprint在不同属性状态下直接要求相等。新adapter只由manifest解析角色/Seed/cap，避免旧单组路径断言。

建议一个资格父进程完成：纯source/recipe检查、一次批量零Optimize参考导出，以及H100的P/M-B/D0/D1四个Seed1实际CLI；每个固定120秒上限。H100是真实V20，不是100站。父进程、参考exporter和四个children至少6次，全部计入8次/1800秒子限额；普通纯编译和静态数学单列工程成本。

生产PE不编译；若需新输入的参考exporter，只编译只读导出入口，一次处理三个输入。正式算法仍自己取得原根证明。实际读取Seed1、其余求解参数、H种子与全H语义、p/d/h类型、三行、完整Start提交/读回、scope/返回和产出时钟。自然未曝光如实记录，不添加弱H或人工proof以使正式路径曝光。

新适配必须在有限夹具覆盖：root不安装、原AM直接split、零证书、不同Seed、正常time-limit、明确not_started、坏源证明和同日志多call。已测逻辑复用；除明确新接线外，不重做R119/R120全资格或海量旧raw恢复。

真实不同执行者作一项前置合同审查；没有则另一方法/实现实际核对并披露，不能用一个passed字段替代。准入绑定最终文件与模型边界，随后正式实现冻结。发现需要改变生产算法的错误就BLOCKED，不临时创建“修正版确认”。

## 7. 计时、安全与数值证据

保持R115以后同一边界：T_produce包括自己的H、建模、LP/MIP、D1安装、在线完整验证、Start、原生清理和产出封存；T_verify是封存后的只读复核；T_total包含两者。原生reserve30秒不改。跨臂核验计组成本，不挂在最后一种方法上。

后验可以验证或撤销已有声明，不得求出更好的路线、新界或新LP再追填。用新见证反驳一个旧声明，必须核对相同原问题及实际区间/cutoff；兄弟/子域高界不能越域。存在来源LP反例时，依赖D1行及其搜索资格不可由own UB或floor0修复。对非依赖原生界的源失格，仅沿既有对称协议保留独立物理证据，单列其可靠性。

未知返回/模型身份/物理非法是必要资格问题；正常开放或LOSS不是BLOCKED。原生证书保持数值条件性，不声称有理精确性。公开材料只保留必要安全数据、日志、源码和有限历史依赖，不含PE/DLL、许可证、密钥、Cookie或污染HTML。当前安全扫描不代表历史告警已解决；不通知发行方、不强推历史、不自行关闭告警。

会话中断先核PID、创建时间、sealed结果和费用，不重启健康child。正式运行串行，不与编译、压缩或重型复核争用资源。全部正常结果完成16臂；只在真实正确性、安全、必要证据或预算障碍下停止并准确列出未测位置。

## 8. 冻结比较与机制解释

直接复用并独立回放R120的18个配对，证书优先、a_U=max(.001,.01|U_control|)、a_gap=max(.001,.10|gap_control|)、a_t=max(30,.10*t_control)，以及原严重条件不变。保留signed gap、零分母与资格不足的UNEVALUABLE；不能把未认证cap当最终求证时间。

双开放严重回退仍要求同时满足UB恶化≥max(.001,.05|U_control|)及gap恶化≥max(.005,.25|gap_control|)；不能仅因C2接近5%就随意四舍五入改级。普通材料性LOSS和严重LOSS都报告。

分别报告新输入层与已知Seed层。每组给U/L/gap、认证、三时钟、H/LP/MIP/安装成本、完整模型规模、实际根证明与h/Start/域身份；区分“启用flag、实际安装、扩展搜索、原生h固定/branching”。没有内部证据就unknown。

对开放端点做恒等分解 dgap=dU−dL；另列G与lambda*P。它们不是内部因果份额。D1-LB更低但U改善时明确说primal收益；相同最优车队较早出现但较晚认证时才有资格谈证明尾部。record可用时间是观测上界，不冒充内部首次发现。

按第3节给两个旧违反点的h重选分析。投影可修复不抹去R120扩展空间非冗余与完整性能证据；投影不可修复也不自动证明普遍算法优势。不得为这一分析追加原生诊断。

## 9. 唯一阶段决定：让这次确认真正收口

先区分执行 `COMPLETE/BLOCKED`。完成意味着16个预定位置都有实际记录与明确资格，没有用未执行或失格结果补位。真实同域反例单列证明风险，不把科学负结果改写成环境故障。

优先处置：
1. 出现证明来源矛盾或依赖错误剪枝：`PROOF_RELIABILITY_PRIORITY`，撤销必要来源并说明已完成/未完成范围；不得宣称性能确认通过。
2. 未解决身份、输入、资源、物理映射或必要时钟障碍：`BLOCKED`。
3. 全部执行有效后，若D1在本轮五个D1/P比较中任一严重回退，或三个新输入中至少两个D1/P LOSS，或本轮五个角色-Seed位置的D1完整证书数少于M-B：`STOP_FROZEN_D1_CONFIRMATION`。这是一项明确的整体风险合同，不是逐点M-B支配。
4. 没有上述否决，且同时满足下列有限支持条件：`ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK`。
5. 其余完整结果：`RETAIN_D1_AS_DEVELOPMENT_COMPONENT`，解释是新收益不足、曝光不足、MIXED还是Seed敏感，结束本批，不自动安排又一批“直到通过”。

有限支持条件：
- 三个新输入均确实在D1冻结后首次测量，三个新D1/P配对均可评价，至少2 WIN、至多1 LOSS；
- 三个新角色中至少2个D1实际安装并运行原生扩展，且至少1个已曝光角色相对M-B取得材料性WIN或新增完整证书；
- 本轮全部D1/P必要比较可评价，无上述严重风险和未补偿的总证书损失；
- 两个固定Seed1块都完成；F2的D1/D0与两项D1/MB结果逐一公开，不择优。若Seed0 WIN转Seed1 LOSS，明确标为敏感；不以额外Seed消除，也不把一次变化等同于总体概率估计。

上述计数是有限候选/资源选择标准，不是统计显著性或论文稳定优势证明。证书总数仅是有限风险账本，五个角色-Seed位置不是五个独立新样本。MB方向单项UB/gap损失不是新增隐藏否决；D0只解释条件信息，其单项损失不代替主要benchmark判断。

正面出口只支持把D1冻结为需要论文级benchmark评估的候选；不更改ENS默认、不删除M-B、也不宣称它普遍更快。若只获得开放优势，标题和摘要不能使用已获非零认证的表述。论文贡献可以组织，仍需与其真实范围相符。

## 10. 资源与失败记账

正式16 children+5 wrappers=至少21次；资格最多8次，总计划29次，距40次上限余11次。时间37200+600+1800=39600秒，距48000秒余8400秒。它供真实后验验证及有限已知问题，不授权正式重试、更多方法或新输入。

每组启动前核对剩余预算能覆盖已承诺的完整义务；不得指望未知提前认证替代预算。发生正式真实失败，保留该位置，不用第二次较好结果覆盖。生产PE或方法在正式期间必须改变时，停止同批确认，不将不同版本拼接；如需后续新研究由下一次明确授权决定。

失败声明槽不退款、native嵌套时间不再重复加；工程编译、只读数学、发布与恢复单列。未知人工时间不填零，不把纯脚本运行时间当全部研究耗时。

## 11. 交付：结果、规格、风险与复核

必要文件：原始冻结recipe/manifest/argv、16臂与18配对、三个新输入及来源映射、Seed分层表、own车队/UB流、证明与数值资格、曝光和成本、完整费用与失败、实际阶段决定、精简final_report、RESUME和复现命令。

更新统一 `paper_algorithm_spec.md` 和 `paper_claim_evidence_map.md`：保留原问题、p/d隐含整数前提、D1三行的物理嵌入与数值条件、完整覆盖。区分一般析取思想与本项目特定集成；区分R120开发成绩、新三问题、旧Seed复验和历史ENS代价。保留C2风险与所有负面数据，不写新个案筛选规则。

额外复核在分析和任务组织后实际执行：重新计算全部18对及最终门槛、检查新输入确无筛选、全部真实Seed/启动来源、至少一份新D1完整物理终点与实际三行端点、有限完整作用域、两层分母和时钟、预算与默认状态。必须使用不同执行者或另一实现/方法，不只检索源码字符串；明确未重跑原生、未覆盖的内部机制和任何资格局限。

一次安全public export和空根重建当前核心即可。复用已修好的typed JSON比较，区分tuple内存对象与存储JSON；对derived sidecar的根路径变化给出明确集合，不把它声称为所有展开字节不变。不得新增全历史载体恢复或“审计平台”作为本轮主要成果。

## 12. 英文 stacked Draft PR 与最终行动

新PR以核验的R120分支为base，不改旧PR结论，不merge、不默认晋级。建议标题：
`Round121: confirm frozen native proof disjunction on prospective instances and fixed seeds`。

正文先写本轮有限确认问题、冻结方法和唯一阶段决定，再列全部新/旧Seed结果、损失、证书范围、预算与复核边界。科学payload、实际恢复与review、后续远端回执分开，不能由一个提交证明自己的未来状态。推送后实际读取PR、base/head/draft与必要公开文件，不只报告“push成功”。

**本轮要回答“R120的新候选值得不值得成为更广论文评测对象”，不是继续让D1在每一个已知实例都赢。确认支持则进入冻结候选的论文评测和组织；不支持则结束本配置的自动扩张，保留局部贡献和明确风险。**
