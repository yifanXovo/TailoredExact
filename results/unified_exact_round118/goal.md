/goal

# Round118：冻结 V40 正目标确认与论文算法规格收口

你负责本地 `yifanXovo/TailoredExact` 的一次有限、前瞻冻结的研究验证，以及新的英文 stacked Draft PR。

**唯一研究问题：在一个未曾求解、数学上保证最优目标严格为正的 V40 问题上，冻结 M-B 能否相对 cold P-GRB 保持有意义的优势，并在同自付费 H 的 P-S 对照之外提供可靠的非零证明或开放端点增量？ENS-C 的收益与代价同时披露，但逐例胜过 ENS/P-S不是论文成立的隐藏条件。**

本轮只生成一个固定输入，运行四个正式臂，并把既有算法、数学证明依赖及有效实验主张整理成可用于论文的统一规格。不开发新 cut、目标库存 oracle、数量邻域、表示、branching、AM 或 solver 参数；不重复测试至得到有利结果。

- 常规范围 V≤50；本轮 V40。无 V60替代样例，无 V>60新生成、求解、资格或补测。
- 正式四臂各5400秒，名义21600秒。总限额 **20次保守启动 / 28000外层秒**；资格及参考导出子限额 **8次 / 1200秒**，计入总额。
- 每个正式臂只启动一次；cold P-GRB仍主要benchmark，ENS-C默认不变，M-B保留R111有限候选身份，P-S是贡献对照。没有按规模、实例、运行秒数或停滞分派算法。

## 1. 起点、继承与不得重开的事项

核验 PR179 / `codex/round117-security-v60-scope`。编写时head：
`71ccd3b75ca8d713018f4edd222cd4c5f0a0b962`。

固定生产source：`d0014a7163e3996fe120471420e56b089c9715ae`；
PE SHA256：`a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8`；
Gurobi13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

先读适用AGENTS.md，核对远端、原有用户修改、PID/创建时间、RESUME及实际二进制；用新worktree/分支 `codex/round118-v40-positive-objective-confirmation`，结果目录 `results/unified_exact_round118/`。有同身份已启动记录时先查账，不重新启动。更晚的安全发布元数据如不影响生产或本轮配方，可记录实际base后继承；有实质算法差异则先停止身份准入。

定向阅读R117修订goal、final_report、security_incident、safe_restore、scope_contract、paper_scope_and_evidence、next_experiment_spec及安全gate；R115产出计时与声明隔离合同；R112实际P-S合同；R100数学说明；R83统一算法规格；R116已合格四角色及其原source/生成合同。不重读或复制全部历史载体。

必须保留：

1. R117是安全与范围修订，0 native、0 Optimize，没有性能升级。当前树/安全载体已清理，不等于旧refs、PR差异、缓存或发行方凭据已清除。没有后续有效回执，不把alert1写成resolved。
2. R116原六角色仍为历史BLOCKED；旧V100位置19–24按作者范围取消，位置18保持历史技术记录。本轮不是它的补测或缩小分母后的追认。
3. 已有V20/V50四角色16臂/24对是观察后的描述层，不是本轮新证据。V20七个非零数值证书来自两个问题；V50均开放。
4. 既有范围内的G50-C1/F5等M-B/ENS损失与原C2修复价值都保留。允许合理取舍；不将“不能再输ENS”写成新准入条件。
5. R104–107已停止组合、R99–100表示网格、旧目标库存oracle研究不自动重开。原G50/G100数值风险保留，缩小论文规模不等于数值问题已修复。

## 2. 安全继承是发布要求，不再开一轮清理平台

只从R117当前安全树/新安全载体取得所需静态来源和旧权威；禁止自动恢复被替代的R116污染载体或下载完整旧HTML来满足原SHA。

复用 `scripts/publication_security.py`，最终检查实际staged字节和本轮公开载体的完整解包内容；扫描输出只含字段、位置及指纹。不要新建通用安全框架、使用真实key测试API、复制Cookie、Authorization、客户配置或把真实secret写进fixture。

R117已拟好的发行方通知、历史重写/PR影响方案属于待owner事项。未经新授权不发送通知、不关闭告警、不force-push、不删除分支/PR、不改权限或默认。科研读取和安全的新结果发布可以继续；不能为了科研便利重新传播原污染内容。

安全原始身份、当前安全字节和生产实测身份分开。历史helper原SHA仅证明历史代码；当前已阻止不安全采集的helper不能被宣称按旧SHA重新准入。本轮使用独立薄数据适配器，不解除旧采集禁用入口。

## 3. 唯一输入：先冻结配方，再生成一次

**本任务尚未生成输入，也没有预知它的最优值、实际难度、站点集合、目标总量或实际运行时间。**只预先保证下列库存规则会给出严格正目标的必要性。

输入ID `N40-R1-S`；输出目录 `reference/round118_positive/`。

|字段|固定值|
|---|---|
|V / M|40 / 4|
|地理|regional，replicate=1|
|库存|shortage，继承R57/R109/R116原生成数学|
|车辆Q|[20,25,35,40]，总容量120|
|物理作业时限T|10800秒|
|lambda / pickup / drop|0.15 / 60秒 / 60秒|
|求解Seed|0|
|四方法顺序|cold P-GRB → M-B → P-S → ENS-C|
|每臂T_produce cap|5400秒|

该T用于一个事前设定的中等规模、允许多站操作的问题；不能在看到地图、LP或H后调整。它不是保证难度或确保算法有利的参数。5400秒仅为完整实验窗口，不进入内部机制选择。

### 3.1 固定来源与散列

使用R116已冻结且R117保持不变的Capital Bikeshare静态站点数据：
`results/unified_exact_round116/source/source_station_table.csv`，其原station_information响应SHA256为
`d4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8`。

按R117安全恢复与来源映射核验表的实际SHA、865个合格ID/容量/投影坐标、稳定UTF-8排序及原三位坐标序列化。不联网重取快照，不换城市，不重做投影来改变原站点数据。

本轮FAMILY固定为：
`round118-v40-positive-proof-v1|source_sha256=d4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8`。
selection_id固定为 `cabi_r118_V40_regional_r1`。

在第一次生成之前冻结配方及适配器源码：原四锚点规则，GEOGRAPHIC_REGIMES=(compact,regional)，REPLICATES=(1,2)；regional/r1选对应原anchor槽，在2V近邻池内按原farthest-first和tie规则取V站。FAMILY贯穿原anchor、target、库存、排序和sign-repair散列材料；不能保留旧城市标签或临时改salt。selection_id在target/库存hash生成前固定。

目标比例[.44,.56]、正整数round/clip、局部库存扰动、目标总量校正、双向符号修复、权重max(.1,(D/maxD)^2)及最大值归一化/六位序列化、min_ratio兼容字段、depot质心/placeholder均继承原规则。min_ratio不增加库存下限。距离仅由原C++ Parser按已序列化points计算Euclidean/1.5；不以Python不同末位计算重写生产距离。

shortage规则：
`Delta_stock=max(40,floor(.12*sum(D)+.5))`，原生成器目标初始总量`B=max(0,sum(D)-Delta_stock)`，并保留合法原库存范围。记录实际B、Dsum和短缺量；不要把Delta_stock与实际Dsum-B在clip边界混淆。

只生成一次。不得预跑H、LP、MIP、可行性oracle或难度筛选；不得因目标太大、小、易、困难、零服务较好、长期开放而换样。进行有限静态合法性/纯生成等价检查，核验新input SHA不与已测输入相同；重复则明确DATA_IDENTITY_BLOCKED，不换盐重抽。

记录与既有四个外部子集的站点重叠。新的是一个未测问题实例，不是新城市、新原始数据来源或独立同分布样本。固定输入/源码/源SHA、物理参数与四argv之后才允许任何本轮native资格工作。

## 4. 零Optimize的正目标证明与论文解释

沿原物理语义：各车空载出发，每站至多一车一次单方向非零整数服务；最终库存0≤Y_i≤C_i，D_i为正整数且D_i≤C_i；每前缀和返仓load在[0,Q_k]；允许带载返仓并支付卸载时间。

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad r_i=Y_i/D_i,
\quad F=G_{\rm true}+\lambda\sum_i\omega_i|r_i-1|.
\]

零分母约定沿原实现；完整路线时长为travel+(pickup+drop seconds)×总pickup。Q不是累计pickup限制。站点库存总量不要求相等；含返仓载量的全系统守恒给出：

\[
B_{lo}=\max(0,B-\sum_kQ_k)\le\sum_iY_i\le B.
\]

所有总量和a_i只对服务站1..V计算，排除depot0。令 `a_i=lambda*w_i/D_i>0`，`delta=min(a_i)`，`s=sum(D)-B>0`。则

\[
K=\sum_i|Y_i-D_i|\ge s,\qquad F\ge\delta K\ge\delta s>0.
\]

原问题仍存在不服务、空路线的合法解；目标库存不可全部达成，不等于原问题不可行。本轮因此需要非零原域证明，不能依赖“自身零车队+floor0”作为主要成功来源。

允许另给一个有限、离线的库存惩罚必要界（不得加入生产模型或正式LB）：

\[
L_{pen}=\min\{\sum_i a_i u_i:0\le u_i\le D_i,\ u_i\in\mathbb Z,
\ \sum_i u_i=s\}.
\]

它可按a_i从小到大、tie按站号分配s个单位求得。说明为什么忽略路线的最小惩罚库存可取总量B且0≤Y≤D：从任何有盈余的可行库存，把盈余转给未达目标站会降低惩罚；总量低于B时，在目标尚未填满处增加库存也降低惩罚。目标容量前提和正权重不能遗漏。因此原F≥L_pen≥delta*s；该值是库存惩罚放松的最优值，不是原公平性+路线问题最优值，也不是新理论或新算法性能。

用少量n=2/3精确有理枚举对照；系数分别按输入十进制与parsed-binary64一致解释。正式输入只做O(V log V)算术，不展开库存或路线枚举。完整G与penalty区别、W=sum(w)、lambda*W和K同时记录。固定lambda/max-normalization不等于跨规模相同的惩罚权衡。

以上分析**不注入H/模型/Start/cutoff/在线bound，不追填正式LB或认证**；它只解释研究对象必为正目标及数学尺度。不能把新下界用于事后修补受损native claim。

## 5. 冻结四方法及真实表示

四种方法必须来自同一上述生产PE/DLL，且与R115/R116实际生产语义相同：

1. cold P-GRB：原compact原cold行为，无H、外部UB、Start、hint或新cut。
2. ENS-C：`research-round83-vds-equal-net-exchange`；完整H/VD-P/F0/AM/target/epoch/cache/cover不变。
3. P-S：原compact加 `--round112-ens-start-compact`；本臂独立支付同H，映射全部原生列，原行/界/类型/目标检查及API提交/读回；有剩余窗口则一次完整compact MIP。
4. M-B：ENS-C加 `--round98-state-service m-binary`；独立ENS-Q开关 `--round100-continuous-quantities` 保持false。

**M-B并不等于p/d仍声明整数。**按R100的实际合同，M-B的p/d为连续列，Y/load保持整数、s/z/m保持二元并含既有A/B；唯一服务、单向操作、整数Y/b使原数学可行解的操作量隐含为整数。实际运行仍按旧整数容差与完整物理回放验证。独立ENS-Q开关false不能替代真实native VType读回。P及ENS的原类型不变。

H仍为Seed20260626、24+1/R76/R83；所有方法Gurobi Seed0、Threads=mip_threads=1、PresolveAuto、MIPGap=MIPGapAbs=0、原affinity/容差/栈/编译身份，数值认证与一致性政策1e-7保持。没有新的NumericFocus/缩放/Seed网格。

全臂只有原绝对deadline；cap5400、原30秒reserve、hard-stop cap−2及TimeLimit实际传递沿原合同，不在H或新Optimize后重置。所谓k秒节点切换、Work配额、大小/库存/实例分派均不允许。

每种方法自己的H、UB、bound、Start、缓存均独立付费。比较三warm完整25种子语义、接受动作、Y与容量归属车队；同U不代替同车队。同H不成立时，完整方法对P仍按各自结果评价，但P-S后端归因必须明确不适用。

## 6. 一次有限资格，先修实际证据语义风险

复用R117安全输入与R115 measurement-v2；保持全部在线检查在T_produce内，封存后才进行串行独立T_verify，并报告同起点T_total。封存后不能重入solver或生成更好车队/新求解界；后验超过30秒不单独使产出失格。跨臂最终核验计group成本，不让后跑方法承担前臂审查费。旧时钟、旧BLOCKED和旧alert状态不改写。

开始前列出一个小型依赖表，防止R117禁用的旧抓取/生成main或R116单组/固定cap行政assert阻断本轮。只做必要manifest/路径和后验适配，不改生产PE。

### 6.1 已知复用日志风险

R116失败过的“一文件只有一个Optimize头”不是合法调用的普遍定理。它在V≤50也可能发生，不能照搬进本轮，也不能仅改成>=1。

前置实现或复用一个**只读、逐call日志视图**，覆盖健康和被拒声明两条路径及实际下游reader：

- 真实call ID/串行顺序、ledger、完整不可变model SHA、leaf/true-G区间/cutoff/可证明的epoch、日志字节段/SHA、实际返回联合绑定；每个调用和实际Optimize段一一对应。
- 参数前导、行列、LP连续化/MIP整数恢复、可用fingerprint、对应终值及API/ledger返回按本call核验。
- claims_for不能取整文件最后值代替早次调用；模型检查不能取整文件第一头代替后次；checkpoint、Start、cover及数值撤销沿同一call身份。
- 新域的下界不得反向给旧较大域，兄弟叶界不得取max当全局界；以实际coverage/cutoff合同判断。
- 无完整模型或无法唯一对应时保持UNRESOLVED，不能改成floor0就声称全部资格通过。

资格使用已有安全的V≤50单段raw和有限双段夹具。必要时只读旧V100的少量已知日志/ledger片段作为技术格式fixture，**不恢复其完整矩阵、不重新资格旧第18臂、不运行V100**。反例覆盖重复/漏段、错model/域、不同call相同值、真实未返回、合法not_started与原极窄missing-return。

这是一项通用证据缺陷修正，不是算法优化。新模块保持小范围；不得借此建设新审计平台或要求整套历史恢复。实际资格仍未解决该已知风险时，在正式前BLOCKED，不付费运行再重复同一错误。

### 6.2 实际准入工作

- 一个批次：用既有/有限重建的只读辅助导出器对新输入导出原cold reference，0 Optimize，保存实际数值行列/类型/界/目标。仅辅助程序可由冻结模型源码构建，主PE不得重编译；不借导出进行LP或H预跑。
- 一批零Optimize模型/日志/分类与时间边界测试；原已合格V≤50字段回归。正常not_started与Start已提交后无剩余窗口分别核验，不把声明次数当真实Optimize次数。
- 最终helper字节下H100两次真实CLI：P-S→M-B，各120秒、Seed0；H100是V20/M2/Q13,21/T5100，SHA `04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71`。检查真实入口、Start、同H和后验连接，不声称覆盖新V40的难度或全部epoch。
- 最终一次准入绑定PE/DLL/source、safe来源、唯一新input、四argv/顺序、helpers、数值/计时/配对规则和全部实际资格。

建议过程：有限回放driver1次，reference wrapper+exporter2次，H100 wrapper+2children3次，post/admission driver1次，合计7次；最多8次/1200秒。失败槽不退；实际额外进程必须事前计入。纯离线只读工程费用另列。不能拿总预算突破子上限。

## 7. 四臂执行与证据政策

正式顺序与第3节完全一致，每臂仅一次。角色名、结果好坏和是否接近最优不能改变顺序或策略。四臂同PE/同已冻结producer和验证helper；正式开始后不修改运行闭包并混合身份。

自己的合法车队只来自产出前的真实记录；原scope全局LB只来自本臂已形成的合格调用与完整覆盖。原目标非负floor0可沿既定政策保留，新的第4节更强分析不得倒填。

同域合法反例只撤销相应坏call及其依赖界/OPTIMAL/INFEASIBLE/剪枝关闭；后一次更小值不恢复坏call。另一角色的零见证不属于本新问题。交叉同角色核验只用于离线撤销，不给其他臂新UB/Start/缓存。

仅坏claim可严格隔离且模型/物理/返回/时钟完整时允许SOURCE_REDUCED_OPEN，不因此取消后续方法；不把它统计成可靠非零认证或原生证明收益。真实无法验证身份/模型/返回/车队、安全和必要输出错误则停止，并给精确最小缺口。正常超时开放、LOSS或独立验证耗时长不是工程失败。

本新问题已数学排除F=0；若输出own_zero，先检查输入、库存与目标重算，不以旧零证书捷径直接通过。

完整记录T_produce、T_verify、T_total；H、LP、MIP、写模/映射/控制残差只作记账，不从总时间中减一段推算未执行的新成绩。原生全程API Runtime不是完整算法时间。两侧均未证时不估算最终认证时间；只有两侧都认证时才给同协议精确时间比。

## 8. 结果分析和唯一研究处置

固定六对：ENS/P、M-B/P、P-S/P、ENS/P-S、M-B/P-S、M-B/ENS。主基准始终cold P，后端增量另外看同H及真实曝光的P-S对照。只有一个问题，不能报告为四个独立样本或总体WIN率。

沿原材料性：
`a_U=max(.001,.01*abs(U_C))`；`a_gap=max(.001,.10*abs(gap_C))`；`a_t=max(30,.10*t_C)`。
证书优先；双证按完整产出时间；双未证至少一个U/gap材料改善且另一项无材料恶化为WIN，反向LOSS，指标双向MIXED，其余TIE，资格缺失UNEVALUABLE。严重性沿继承规则，不clamp微小signed gap、不用近零分母制造巨大比例。

分开给：
1. 自主UB和可行解进展；
2. 同域有效LB、完整原域非零证书及最早已验证目标记录的可用时刻；
3. 实际调用/原子split与模型/搜索成本；
4. 数值声明和source reduction风险。

若所有方法已较早拥有相同终值而完成时间差异明显，支持证明完成差异；不能用日志发布时间冒充精确内部发现。若U相同而gap不同，区分LB贡献；若LB近似相同而U不同，区分primal贡献。M-B/ENS涉及表示与搜索交互，不凭一次表格声称某条A/B、某个branch或AM是唯一原因。

采用两层状态：
- `execution_stage=COMPLETE/BLOCKED`：原四臂和必要证据是否实际完成；正常未证可COMPLETE。
- 完整结束后的研究处置按以下优先级：
  A. `PROOF_RELIABILITY_PRIORITY`：出现已证同域native矛盾或错误依赖关闭。保留合法物理解和失败范围，优先一个最小正确性/数值问题，不用其他WIN遮盖。
  B. `PRIMARY_BENCHMARK_RISK_ON_THIS_ROLE`：无A，但M-B/P为材料性LOSS。描述损失的U/L/证明/成本本质；不因单例自动撤销历史支持，也不在本轮打补丁。先结合全部已冻结证据判断它是否真的影响整体候选理由，而不是把一次LOSS自动转成必须修复的点态门槛。
  C. `NONZERO_PROOF_INCREMENT_ON_THIS_ROLE`：无A/B，M-B取得合格非零完整证书，并且M-B/P及M-B/P-S均为WIN且P-S归因有资格。只确认此角色的局部证明增量，推进冻结候选论文实验组织。
  D. `LIMITED_OR_MIXED_ROLE_EVIDENCE`：其余完整结果。明确是开放端点增量、共同容易认证、增量不明显、后端代价或曝光不足；不要将开放改善强行升格为证明优势。

以上是研究处置，不是统计显著性或新默认晋级门槛。ENS/P-S的LOSS完整披露但不另作隐藏否决。无论C还是D，本轮完成后不自动补抽下一个“更合适”的输入，不自动延长本例窗口或再加Seed。BLOCKED不能写成算法否定；普通无增量不能写成BLOCKED。

## 9. 必须形成论文阶段交付，不仅交付一次胜负表

除原始结果，交付两份精炼实质文档：

### 9.1 `paper_algorithm_spec.md`

给出原问题、统一ENS/M-B算法伪代码、每个阶段的输入输出和终止正确性。清楚区分：
- G是真实库存比率的Gini还是模型上图变量；每个Start/候选如何回到原物理目标；
- p/d隐含整数性依赖唯一服务、单方向、整数b/Y；A/B有效性与其是否为必要条件；
- 每个区间/epoch的有效域、父子覆盖、cutoff补集、全局界和认证；局部最优不是全局最优；
- H与原生后端的完整成本，M-B与ENS差异，默认与研究候选身份；
- 已有数学事实、历史有效强化、通用技术与本项目可主张贡献分开。不能把常规隐含整数性、MIP Start或一般分解直接宣称全新理论。

修正R117中可能模糊的“conserve stock”和“unmet-target”：站点总量不必守恒，返仓载量补足全系统；目标是inventory-to-target ratio、双侧relative target deviation及Gini of ratios，不是仅短缺惩罚或真实租还失败需求。不能为文档好看改原问题。

### 9.2 `paper_claim_evidence_map.md` 与简短后续实验规格

以“可主张/仅有限观察/尚未知”对应到实际同身份结果和数学证明，保留F2/C2/L48/G50/F5及外部正负证据的原范围。新一个V40结果不与旧异质时钟合并成总体speedup，不证明V50稳定性或Seed泛化。V100只作必要历史共同风险注记，不成为下一阶段完成条件。

最后给出一个有限后续优先级：正确性问题、主要P缺口、或冻结候选的预注册论文benchmark。实验规格只规划真正仍缺的范围和资源原则，本轮不执行第二批。若本例全开放，说明尚未验证的非零证明能力，并结束本任务；不得无限以“再找一个问题”代替阶段收口。

## 10. 资源和运行纪律

正式4×5400=21600秒，至少1wrapper+4children=5次启动。资格按上限8次/1200秒加单组管理预留120秒，计划13次/22920秒；距离总20次/28000秒，尚有7次/5080秒用于必要串行验证及有限准入故障，不授权正式性能重试或增加native窗口。

所有已声明失败槽永久计费；嵌套native/H/验证不重复相加。外层退出有观察区间就按继承保守口径记账，未知人工时间不填零。每组启动前保留足够预算覆盖未执行正式窗口和必要检查；不依赖猜测“会早停”透支资源。

原生运行不与编译/压缩/重型复核并发。会话中断先核对PID、创建时间、已封存文件和费用，不重复启动健康或已完成进程。optional progress沿原非权威隔离，必要资源保护仍有效。

## 11. 实际安全交付与英文 stacked Draft PR

交付唯一新input/来源映射/生成盐/模型reference、资格与准入、四个原产出包及必要call/Start/模型/类型/参数/返回/cover证据、六对结果和三时间、own车队/目标记录、费用与失败、数学分析、论文规格/证据图、final_report/RESUME和研究处置。

只打包当前必要安全raw和少量已签安全权威；不得复制整个旧载体。R117安全来源依赖可精确引用，不重新公开原HTML或凭据；小型静态源和输入可作为有许可研究附录。PE/DLL/license/credentials、受限临时副本不发布。

实际staged文件及完整载体通过R117gate；一次公开export和新空目录restore，重建当前核心字段并比较，记录真实范围。用新的数据/脚本就绑定新的身份，不冒充旧admission。无原工作树fallback，无“仅哈希通过就证明原生最优”的说法。

建议标题：`Round118: confirm frozen backends on one positive-objective V40 instance`。
Base为核验的R117安全分支；普通stacked Draft PR，不向main混入累计历史，不合并或改变默认，不远端重写历史。仍有历史安全风险就保留R117的准确限定，不能称整段Git历史无secret。

科学payload与实际恢复/审查/远端回执分开；核对真实head/base/open/draft及必要文件OID。回执不宣称验证自身未来提交。

## 12. 用户要求的额外复核与终点

组织完完整分析和交付后，额外复核一次：
1. 新输入是否生成前冻结、无难度筛选，只有一个V40、没有V60/V100补位？
2. 正目标下界是否使用真实库存总量、D/C/正权重前提，未把目标不可达说成原问题无解或将离线界注入结果？
3. 实际M-B VType、独立ENS-Q flag、原P-S矩阵/完整Start和同H是否准确？
4. 调用日志是否逐call/model/scope归属，没有简单放宽assert、跨epoch借界或要求完整恢复范围外V100？
5. 三类时间、原生窗口、安全扫描、旧raw和数值撤销是否保持；没有凭后验新车队/界倒填？
6. 主要P与P-S增量、ENS取舍是否分开；未隐藏损失或把四方法当四个独立问题？
7. 四臂/六对/预算和终态是否闭合，交付是否真的形成论文算法规格而非仅一份新审计报告？

有真实独立执行者时使用；否则如实说明是实现者的单独复核步骤/独立检查脚本，不声称第三方或原生性能复现。只修实际缺漏，不以复核为由重跑性能或增加样本。

**本轮必须结束于：一次有明确结论的V40正目标对照、统一可引用的论文算法规格，以及唯一后续研究处置。安全维护与证据修复是前置支持，不再替代算法研究目标。**
