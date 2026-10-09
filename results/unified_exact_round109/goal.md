/goal

# Round 109：冻结 M-B 的地理派生扩展评测与有限 Seed 稳健性验证

你负责在本地 C++ 项目 `yifanXovo/TailoredExact` 完成本轮数据冻结、继承资格、完整配对评测、独立复核和新的 stacked draft PR。原始冷启动 P-GRB 仍是主要 benchmark，ENS-C 是完整参考算法，唯一候选为 R108 已选定的原 R100 M-B。

**本轮只回答：冻结的统一 M-B，在预先固定的更广地理派生输入和有限第二 Seed 检查中，是否仍有足够的相对 P-GRB 优势，可以收口为论文研究候选？** 本轮不开发新机制，不调参，不重开 STRUCT，不自动更换 ENS-C 默认。允许对 ENS-C 有公开、明确的取舍，不按实例挑选算法。

完整任务为 **12 个新的前瞻输入 × 3 算法 × Seed 0＝36 臂，另加事前指定 3 个输入的 P/M-B Seed 1 对照＝6 臂，总计42臂、88200 nominal秒**。总资源上限 **72次保守计费启动、100000外层计费秒**。先冻结候选、生成规则、全部场景、顺序和判断规则，再生成、核验并运行。正常正负结果均完成整套42臂，不靠途中表现换样、改模式或提前选出赢家。

## 1. 起点、已成立结论与本轮新增信息

核验 R108 / PR #170：

- base 分支 `codex/round108-frozen-mb-validation`；本轮任务编写时交付 head `d11c94d81e6a2c5dcd64dad8c54b390f3cb4a027`。
- R108 实测生产源内容继承 R107 交付 `b5db3f038f64215766a54498d8acc82e384de733`；PE SHA256 `4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0`。
- 实际 Gurobi 13.0.2 DLL SHA256 `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。
- R100 原候选冻结为 `results/unified_exact_round100/candidate_freeze.json`，历史生产源 `b5d6d83bb8fc74682de6f1f6862c2e687712f4cf`；旧性能身份只作为继承证据。

开始时读取 AGENTS.md，检查 GitHub 最新 head、本地 HEAD、用户修改、活动进程和已有本轮工作。独立 worktree/分支建议 `codex/round109-frozen-mb-geographic-evaluation`，结果目录 `results/unified_exact_round109/`。真实已有进度按 RESUME 继续，不覆盖原结果或重跑已完成输入；更晚提交先记录差异，不默默沿用过期身份。不改代理、权限、网络和无关用户配置。

阅读 R108 完整 goal、`final_report.md`、`representation_contract.md`、冻结协议、`reports_final/`、最终本地/公共独立审查及 `reproduce.md`；有针对性继承 R100 数学/因子证据、R57 数据来源/生成规则和 R96 合成分布说明。不要把所有历史研究重新做一遍。

保留以下已成立结论：

1. R108 21正式臂全部完成，同PE/DLL，正式失败/重跑/取消均0；M-B/P为6 WIN、1 TIE；固定新角色 S12/B24/L48/N36 为3 WIN、0 LOSS。正确状态是 `SELECT_MB_FOR_BROAD_EVALUATION`，不是稳定泛化或论文资格已证明。
2. M-B/ENS 在F2、F5、N36为LOSS，其中F5严重；不得删去这些结果，也不得将ENS逐点支配重新变成隐藏准入条件。S12减少28.1777秒未达到冻结30秒门槛，保持TIE。
3. L48真实执行两次父域分割，其中一次AM评分split，最大同时相关活动叶为2；left NEXT证明、terminal证明、右域LP-INF及高G补集共同支持完整认证。不能只看AM表的一个split或保存叶的open标签。它不重开R107 assignment/STRUCT配置。
4. C2收益及F5/N36损失主要体现在own UB。F5 M-B较ENS的gap增加约.03104011，而LB还略强；ENS在安全观测上界559.325秒已获得.333465758，优于M-B最终.345021271。端点分解和可用时间证据不是p/d、A/B或原生分支的独立因果证明。
5. R108正式最大V=50。资格角色H100实际输入为 `20 2 [13,21]`，不能当作100站证据。本轮补充真实V100、更广来源的坐标/容量、库存/时限组合和有限Seed敏感性。

写一页 `research_decision.md`，说明这些缺口如何对应本轮任务，正面/负面结果分别改变什么决定。本轮新增的是前瞻评测与候选判断，不把旧数学性质、日志数量、恢复工具或再次运行称为新算法贡献。

## 2. 唯一算法身份、原问题合同与最小资格

优先复用 R108 已资格验证的同一PE；必须实际重哈希并核对当前生产源/调用路径。若必须重新构建，先冻结新PE，全部42臂用该PE，不用历史端点补配对。新增数据与证据脚本可以独立变更，生产算法不变。

三个实际入口保持：P为原cold compact；ENS采用 `--algorithm-preset research-round83-vds-equal-net-exchange`；M-B在同一ENS命令上附加：

```text
--round98-state-service m-binary
```

M-B输出 effective identity 为 `research-round99-ensc-discrete-structure-m-binary`，它不是可替换传入的preset。`--round100-continuous-quantities` 保持false。不换M-BL/projected/vehicle-state，不混入LP-G、R96/R97/R101–R107额外研究组件，不做M-B组合、A/B修订或新的因子格。

保留原完整ENS、VD-P/F0、24+1自付费startup与物理闭包/handoff、AM0.08、原深度/宽度/覆盖规则、cutoff epoch、child-cache、milestone和terminal。M-B保留路线/载荷/库存整数与状态/归属/方向二元，仅按R100解除p/d重复整数声明并使用原每站两条联结：

$$
\sum_k(p_{ki}+d_{ki})=\sum_{y\in S_i}|b_i-y|s_{iy},\qquad
\sum_k z_{ki}=1-s_{i,b_i}.
$$

缺失的初始状态selector按固定0解释。整数b/Y、唯一车辆和单向非零服务使实际p或d等于整数库存差，隐含整数性不依赖新增A/B；LP/child-LP的p/d允许分数。原其它行、界、容差、type恢复、Start映射与等容量车号稳定归一化全部保留。

目标与物理合同不变：

$$
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad r_i=Y_i/D_i,\quad
F=G_{\rm true}+\lambda P,\quad P=\sum_i\omega_i|r_i-1|,\quad
G_{\rm true}=\frac{\sum_{i<j}|r_i-r_j|}{n\sum_i r_i}.
$$

零分母沿用原G=0并保留penalty。车辆空载出发、每站最多一车一次非零单向整数服务；所有前缀/返仓载荷在[0,Q_k]，允许带载返仓；站点总库存等于初始总库存减返仓载荷。累计pickup可超过Q；闭环时长含旅行、站点装卸和返仓卸载，等于旅行加 `(pickup_seconds+drop_seconds)*Σpickup`。新输入不改变原欧氏距离/1.5、60/60秒处理和评估语义。

生产不按实例名/SHA/规模、几何/库存标签、物理T、已知最优值、墙钟、Work、停滞或节点/车辆耗时选择策略。实验cap与全程安全收尾只用于终止评测。P不获得ENS的Start/行/route；各臂独立支付startup，不共享UB、路线、cut或cache。

资格采用“继承＋少量真实入口”：零求解绑定R108已验证的生产函数、读回器和反例；在已知H100或既有固定fixture上实际验证P/ENS/M-B三个CLI，并在同一已知资格输入上各验证一次P/M-B的Seed=1实际读回。资格每臂≤120秒，事前最多8次保守启动、1200外层秒；规划为两个wrapper、五个实际CLI children及一个零Optimize的批量原P参考模型导出child，共8次。批量导出child在一个已有资格wrapper内完成全部12个已冻结新输入的cold reference建模/写出，不为每个输入另起native进程，不Optimize、不presolve、不生成解或传递Start。不得削弱参考矩阵核验以省启动数；实际更多driver/native进程必须加计。至少触达适用LP/MIP/Start及一个合法完整终止，不能只运行exporter。reader按每臂冻结Seed核验，不硬编码全部为0；其它startup随机设置保持原值。不要重做R108的19启动资格格，不用任何新12输入试LP求解、heuristic或性能pilot。超出资格预留需先重排本轮固定预算并记录实际原因，不增加新实验目的。

独立reviewer在首个正式臂之前签署 `performance_admission`，绑定实际PE/DLL、全部42个argv、参数、输入、协议和资格。只允许恢复上述合同的兼容/正确性修复；若需要改变数学或搜索规则，记BLOCKED，不把变体作为冻结M-B继续运行。

## 3. 公共数据来源与事前固定的生成规则

使用已公开的R57源表，不依赖 sibling Hybrid GA 目录或私有原文件：

- `results/data_generation_citibike_round57/source_station_table.csv`
- 来源commit：`d11c94d81e6a2c5dcd64dad8c54b390f3cb4a027`
- Git blob：`84fb8af5aaa9836d316820227e4f06e8cd4b1e63`
- 精确字节数：69678；SHA256：`9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0`。

表有443行，按既定 `0<C_i<100` 规则442行可选。坐标与容量使用同一 `source_station_row_index`，不要用伴随姓名/ID重配源行。R57原始两份外部文件的历史hash只作为来源记录，不声称本轮重新核验了未读取的私有bytes。

先冻结完整数据recipe与下节12行表，版本固定为 `round109-geographic-mb-evaluation-v1`。复用 `generate_citibike443_regional_v1.py` 中既定的纯生成数学：每个V的四个远离anchor、compact最近V、regional在anchor最近2V池中farthest-first选V、原tie规则、三位小数centroid depot、target profile、受控库存总量与局部正负失衡、权重、原points-only writer。将新版本作为所有anchor/target/inventory哈希材料的family前缀，replicate固定1/2；记录每个完整seed材料和选中的源行序列。不得运行R57整套历史入口或重新生成旧240文件。

允许制作小的公开表adapter：由该表构造SourceStation、调用/等价移植上述纯函数，移除 `build_landscape` 对私有来源文件重哈希的副作用，改为绑定本轮公共表。准确保存相应旧函数与新adapter的语义差异。除上述公开来源绑定、新family前缀及明列车队/时限外，不临时改target、库存、权重、点序或地理规则。

目标库存沿用容量44%–56%范围的哈希profile；shortage/surplus沿用总target的12%（至少V）总量偏移和原局部失衡/确定性总量修正，balanced总量严格相等。沿用 `ensure_both_local_signs` 的事前确定性修正，所有中间信息可追溯；它是生成定义的一部分，不是看求解结果换样。权重是按最大值归一化到1，**不是权重和归一化**。

**按真实模型核验初始可行性，禁止求解后筛样。** 原样保留R57四位小数 `min_ratio` 的生成值。当前 `Instance.hpp` 明示该字段为兼容字段；原MIP与物理evaluator不施加 \(Y_i\ge R_iD_i\) 约束。不要修改此字段以“修复”不存在的库存下限，也不要在新模型、writer或checker中引入该约束。

逐例零求解核验 \(0\le b_i\le C_i\)、\(D_i>0\) 及正T。取全车空路线、零操作、\(Y=b\)，则车辆初始载荷、所有载荷及返仓载荷、行驶和处理时间均为零，满足原问题；此可行性不依赖 `min_ratio`。该空车队只用于数据核验，不得人工作为额外Start或UB注入任一正式算法，沿用各自生产原行为。若任一臂宣称原问题全局不可行，须先审查与此已知物理见证的矛盾，不能将其当作普通性能结果或认证成功。

每个角色生成一次，立即保存输入原bytes、SHA、源行映射、完整landscape和解析结果；仅作语法/域/距离/库存/空路线的零求解验证。原合法输入容易、困难、F=0或对M-B不利都保留，不换seed、anchor、V、T、Q或库存。实现错误按同一逻辑draw修复，保留失败源/bytes；不改变合法draw。全部文件放在 `reference/round109_geographic/`，核对精确bytes和(输入SHA,T,lambda,处理时间)此前未有测量。本轮若实际已经运行，按RESUME保留它们最初冻结时的资格，不误判为新污染。

坐标/容量为真实来源派生，其余字段、depot、M/Q/T均为合成；仍是同一443站来源下的新前瞻输入，不是新城市、真实需求快照或12个独立同分布地理样本。anchor可能共享站点，公开子集重叠情况，不以降低重叠为理由换样。

## 4. 固定12个主输入、顺序和6臂Seed检查

所有正式场景lambda=.15，pickup/drop各60秒。主面板全部Seed=0。H为同容量车队 `[30]*M`；X为等总容量的异构车队：M2 `[20,40]`，M4 `[20,25,35,40]`，M8上述四项重复两次。每个V均H/X各2个、每种库存全表H/X各2个。算法不读取这些类别作模式分派。

表中C/R分别compact/regional，后缀1/2是对应replicate。P/E/B分别P-GRB/ENS-C/M-B。严格按行串行执行；全部六种方法排列各两次。

|序号/ID|V/M|地理/replicate|库存|Q类|物理T秒|cap/臂秒|方法顺序|
|---|---|---|---|---|---:|---:|---|
|1 G20-C1|20/2|compact/1|shortage|H|3600|900|P,E,B|
|2 G20-C2|20/2|compact/2|balanced|X|7200|900|E,B,P|
|3 G20-R1|20/2|regional/1|surplus|H|7200|900|B,P,E|
|4 G20-R2|20/2|regional/2|shortage|X|3600|900|P,B,E|
|5 G50-C1|50/4|compact/1|balanced|H|7200|1800|B,E,P|
|6 G50-C2|50/4|compact/2|surplus|X|18000|1800|E,P,B|
|7 G50-R1|50/4|regional/1|shortage|X|7200|1800|P,E,B|
|8 G50-R2|50/4|regional/2|balanced|H|18000|1800|E,B,P|
|9 G100-C1|100/8|compact/1|surplus|X|18000|3600|B,P,E|
|10 G100-C2|100/8|compact/2|shortage|H|7200|3600|P,B,E|
|11 G100-R1|100/8|regional/1|balanced|X|7200|3600|B,E,P|
|12 G100-R2|100/8|regional/2|surplus|H|18000|3600|E,P,B|

由此得到V20/50/100各4个、compact/regional各6个、shortage/balanced/surplus各4个，物理T覆盖3600/7200/18000秒。这是有明确覆盖范围的场景面板，不是单独识别size、horizon、geometry或heterogeneity因果效应的完整因子实验。

主面板36臂nominal：`3*(4*900+4*1800+4*3600)=75600秒`。随后固定执行以下Seed=1检查，不根据Seed=0结果改角色；输入bytes、T、cap和全部其它参数不变：

|顺序|同一输入|Seed|cap/臂|方法顺序|
|---|---|---:|---:|---|
|13|G20-C2|1|900|P,B|
|14|G50-R1|1|1800|B,P|
|15|G100-R2|1|3600|P,B|

六臂共12600 nominal秒，总计88200。它们只检查三个预指定角色中M-B对P的原生Seed敏感性，不是额外六个新输入，不支持ENS的Seed稳健性或总体随机种子稳定性。不得取best-of-two、平均后替代Seed0主结果或把6臂并入12输入的WIN分母。

## 5. 正式运行、身份与停止边界

统一Threads=1、mip_threads=1、Presolve=Auto、原FeasibilityTol/OptimalityTol/IntFeasTol、MIPGap=MIPGapAbs=0；Seed按上表。沿用R108单核运行/affinity和cap内30秒全程收尾reserve，实际native参数每次读回。物理T、求解cap、完整观测时间必须分列。性能期间不并行编译、打包、重型审查或另一求解器。

正式前绑定所有42条完整命令。逐新输入检查P确为原cold reference数学矩阵，不按方法名猜测；ENS/M-B使用当前原writer与对应VType/状态行。每臂保留自身物理UB和作用域合格的完整覆盖LB，正式组间不得共享解或知识。

**全部36主臂和6个Seed臂都必须在正常结果下完成。** M-B早期LOSS、严重回退、全是TIE、零目标易例或阶段正面门槛已不可能，都不取消其余预定组；本轮完整分布画像本身就是交付目标。禁止途中新增旧F2/C2桥接、额外seed、长时延长、另一个draw、更多变体或相同命令的择优重跑。

真实正确性/环境故障先暂停，完整保留失败、原始证据、身份和费用；只修复实际缺陷，不将性能不好称为环境问题。当前组完整重新配对的范围由故障影响决定，先确认预算容纳；若生产PE变动，任何性能阶段结论（包括BROAD_PANEL_NOT_SUPPORTED）均须使用同一最终PE的全部42臂，不能拼接旧阶段，即使修复看似很小。预算不够则BLOCKED并明确缺失工作。纯reader修复不触发性能重跑，须保留旧reader和独立证明算法/门槛未改。普通time_limit/原overall_global_deadline且有效coverage是正常截尾结果。

若发生真实OOM、行政硬停止或不可恢复故障，披露为resource/interruption结果，不冒充完整正常端点；只保留已经提交且合格的观测。不能为得到正面判断删掉该输入、降低V/M或换更易数据。

## 6. 结果口径与配对分类

继承R108的数值与分类合同，主面板以P为比较基准，另外完整报告M-B/ENS和ENS/P，不改变冻结门槛。

每臂报告own physical U、合格完整覆盖L、signed gap `Δ=U-L`、合法时relative gap、完整认证、完整观测时间和终止原因。认证依赖原全覆盖及本臂物理见证，不能由near-zero gap、一个local OPTIMAL或summary布尔值单独判定。原闭合容差内微负gap保留，不剪裁；relative gap仅在合格有限U/L且|U|超过原零目标容差时报告，否则null并说明。

对候选A与对照C，材料性尺度：

$$
a_U=\max(0.001,0.01|U_C|),\quad
a_\Delta=\max(0.001,0.10|\Delta_C|),\quad
a_t=\max(30\text{秒},0.10t_C).
$$

- 只有A完整认证：WIN；只有C完整认证：LOSS且严重回退。
- 双方认证：完整时间减少至少a_t为WIN，增加至少a_t为LOSS，否则TIE；不以目标最后几位差异否定同一数值证书。
- 双方未认证且都有合格有限U/L：UB或gap至少一项改善达到对应尺度、且无任一项达到材料性变差，为WIN；反向为LOSS；既有材料性改善又有材料性损失为MIXED；均无为TIE。所有LB变化另列，不把MIXED计为WIN。
- 双方未认证而缺少可比有限U/L：UNEVALUABLE；不填0、不伪造比例或记TIE。真实数值/证据错误按BLOCKED处理。

严重回退继承：仅C认证；或双证时 `t_A>=2*t_C` 且额外≥120秒；或双未证时UB变差至少 `max(.001,.05*|U_C|)` **且** gap变差至少 `max(.005,.25*|Δ_C|)`。补偿性MIXED仍完整公开，不能用平均或best-of掩盖。近零gap的分类使用绝对尺度，百分比描述仅在分母确有意义时使用。

认证速度只在双证时计算精确比值；单侧认证公开固定窗口收益；双截尾不推断最终认证时间，不把cap当作证明耗时。禁止跨实例平均原始未归一化F、把主面板和Seed检查混成42个独立样本、或根据这些阈值声称统计显著性。

## 7. 确定性阶段判断：支持、未支持或阻塞

以下是事前科研资源/候选规则，**不是统计定理，也不是所有同类实例稳定胜出的保证**。独立重建后生成唯一 `selection_decision.json`，按以下优先级处理：

1. **BLOCKED**：完整42臂、输入资格、同PE配对、原问题正确性或证书证据因真实未解决故障不能成立。保留所有有效结果，列明故障、预算、已做修复和缺失项；不得把普通差性能归入此状态。
2. **BROAD_PANEL_SUPPORT**：全部42臂按协议完成且有效，并同时满足下列全部条件。
3. **BROAD_PANEL_NOT_SUPPORTED**：42臂有效完成，但至少一个正面条件不满足。给出确定reason codes，可并列：`SEVERE_P_REGRESSION`、`TOO_MANY_P_LOSSES`、`INSUFFICIENT_P_WINS`、`MISSING_STRATUM_GAIN`、`SEED_SENSITIVITY`、`UNEVALUABLE_COMPARISON`。样本过易/全TIE、补偿性MIXED等通过原始分类解释，不将其一概称为算法错误。

正面条件：

- 12个Seed0主输入全部在最初冻结时具备未测资格，且12组M-B/P比较均可评价；不缩减分母。
- 主面板M-B/P：WIN≥6、LOSS≤2、严重回退=0；V20/V50/V100每个规模至少1个WIN，compact与regional各至少1个WIN。
- 三组Seed1的P/M-B比较均可评价、没有严重回退；至少2组不为LOSS，且不存在同一预指定输入 `Seed0 WIN → Seed1 LOSS` 的翻转。MIXED不充当WIN，逐种子公开；翻转阻止本轮正面稳健资格，不等于算法不正确。
- 没有未解决的数值/覆盖/身份问题；所有ENS损失和所有MIXED如实报告。

ENS的局部损失不自动否决上述P导向判断。必须另表报告ENS/P及M-B/ENS，说明M-B是否扩展了ENS的优势范围、哪些场景只是继承ENS表现、哪些损失仍然存在，不能声称M-B支配ENS或全部历史候选。

`BROAD_PANEL_SUPPORT` 的实际阶段动作是：将本冻结M-B及其完整ENS框架收口为论文研究候选，交付清晰算法规格与有限实测主张，暂停以本轮结果为由自动追加机制。本轮不切换默认、不合并主分支、不宣称完整论文benchmark已经完成。`BROAD_PANEL_NOT_SUPPORTED` 则不支持继续晋级这一候选，区分明确回退、Seed敏感性和证据不足；原R108选择记录不重写，ENS仍为默认参考。任一结论都不自动启动新变体、补抽或下一轮求解。

## 8. 必要的机制观察与后续优化依据

使用已有原始观测，不改变搜索行为，不为机制解释额外调用求解器：

- 初始/最终每个物理见证分列G、P、lambda*P、Σomega、总库存/总target/返仓载荷、服务站数、每车实际站数和处理/旅行时间。固定lambda=.15且权重max归一化时，Σomega随V变化，不能称跨V保持归一化公平/penalty权衡；不暗中改lambda/V或sum归一化。本轮lambda敏感性明确未检验。
- 列出实际模型行列/VType、LP与MIP次数、AM动作、两类partial target、实际分割与最大同时相关叶数、Start接受/跳过原因。区分lookahead与活动分解、root-infeasible contraction与评分split，保留完整true-G补集。
- 合理分区startup、LP native、MIP/callback native、模型/映射/写盘及外层审计时间；无单独计时则合并，不把嵌套秒数相加。观察大规模M-B的额外LP成本是否重复出现，但不直接认定A/B或p/d为因果根源。
- 用原已提交证据给300/600/900/1800/3600等实际覆盖检查点；短窗/提前认证后缺失的原始检查点不外推填充。已有完成证书的静态结论可继续用于认证计数，不能伪造后续运行观测。
- 对有可靠原问题Fstar的角色，给物理最优带见证的安全可用时间上界/区间及全局认证时间；不把写盘时间当精确native首次发现。未认证角色不将本轮最小UB命名为Fstar。
- 对所有材料性损失，按 `Δ_A-Δ_C=(U_A-U_C)-(L_A-L_C)` 分解端点，结合真实轨迹区分可行解不足、证明不足或两者兼有。这是结果分解，不是原生搜索因果识别。已有Start相同、LP变强或node变少均不能单独证明提速原因。

报告中可以提出至多两个后续优先问题，每个必须引用本轮或历史具体证据，说明尚缺的识别证据和怎样的结果会否定该方向。若F5/N36型损失重复出现，优先分析物理incumbent发现与整数表示的交互；不能直接跳到branch priority、更多cut或回退调度的实现。本轮不执行这些候选优化，不重新宣称历史从未测试过某机制。

## 9. 预算、完整计时与失败处理

硬上限72次保守计费启动、100000外层秒；正式nominal88200秒。按每主输入一个wrapper+三个children，12组共48次；三个Seed组各wrapper+两个children，共9次，正式至少57次。加上≤8次资格预留后仍有7次启动储备；实际实现多一层driver必须事前加计，不能沿用R108漏计后再隐瞒。

nominal是各臂评测上限之和，不是预言实际完成时间或全部费用。全程reserve包含在cap内；wrapper关闭/审计等额外外层成本据实计费。资格、必要fault recovery和封装开销共享剩余11800秒，建议资格≤1200秒。每组启动前核对已经实际关闭的费用、全部剩余正式组的最坏预留和必要收尾；不能把未知早停节省先当作预算，也不能双算native与wrapper时间。

所有正式计时从实际臂准入/身份检查开始，到startup、全部求解、必要写盘和实际物理/结果核验完成；保留原legacy supervisor时间，主比较使用统一完整观测。编译、离线reader/审查、打包/恢复是工程时间另列，性能期间不并行争用CPU。没有记录的人工/工程时间写unknown，不编造。

预算储备用于实际故障，不用于新机制、第四个Seed、追加V或延长窗口。任何重跑均保留原失败并按影响重新配对；先保证固定研究目标有资源，再运行。无法完成则按BLOCKED诚实收口，不以减小分母或删掉不利组凑出正面结论。

## 10. 交付、独立审查与可恢复性

复用R108已验证的原始证据与reader，不复制一套无必要的新审计框架。特别继承：I/B真实类型、所有quantity列、等容量稳定归一化Start、returned terminal bound与匹配log/成功return、cold P终态界、Bounds中的G域、NEXT_LEAF及完整partition discharge、原deadline正常截尾、signed gap和保守费用。

有限零求解检查只补本轮实际新增的数据adapter、42臂顺序/Seed分类和阶段门槛边界；继承的反例已有可靠身份时不重复求解。每组运行后核验其数据，最终一次完整主重建和一次独立raw复核即可；只有真实缺陷才增加修复验证，不以检查数量为交付质量目标。

必须交付：

1. `research_decision.md`、来源/adapter说明、完整generation recipe、12输入原bytes/hash/源行映射、结构统计与未测资格、42臂协议/顺序/全部argv、当前候选/源码/PE/DLL/真实CLI资格与独立admission。
2. 全42臂原始结果及可重建表：own物理UB、全覆盖LB/证书、时间/状态、初始最终目标分量、主面板三类配对、Seed1配对/翻转、分类/严重损失/分层覆盖、机制/时间分区、全部费用和失败。主面板12输入与3个重复Seed角色始终分开。
3. `selection_decision.json` 和 `final_report.md`：明确三态之一，逐条对照冻结规则，所有正负结果、适用范围、剩余缺口和预算闭合。结果好的子集不能替代全表；任何审计修复说明它修的是证据还是算法。
4. 一份简明 `paper_candidate_spec.md`：用统一符号叙述原问题、完整ENS-MB流程/伪代码、整数等价与联结、界作用域/区间覆盖/终止正确性、实际保留的结构贡献及对应历史证明来源；把通用性质、历史已测组件、本轮新增证据分开。不是完整论文或新颖性保证。候选未获支持时同样交付规格，并注明未获支持范围。
5. 独立reviewer从原始输入、完整车队、实际模型/Start/调用/覆盖/费用重建关键事实与最终决定，特别验证新V100、两种Seed、全部12分母及保存open叶的真实义务。独立不能只重新读取生产summary或复制主reader决定；复用已审计通用解析可以，但核心物理/覆盖/判断须有独立计算与清楚边界。

保留每次实际失败的源码快照、命令、stdout/stderr、exit、receipt和修复原因；发现缺失诚实披露，不能事后伪造。reader-only变化不得改变冻结性能数据与分类门槛。

公共证据按精确bytes归档，复用已有分片/manifest工具；只包含本轮必要raw、reader和明确的少量历史依赖，不重新打包R105–R108全部大归档。用已验证的确定性压缩/精确分片避免单blob超限，保存哈希。可以安全去重同字节模型但必须保持原路径/身份映射，不能只留summary。不要发PE、DLL、license或凭证。

**实际执行**新公共目录export、新空目录restore、stdlib原始数据到所有发布CSV/决定JSON的全字段比较，以及从该恢复根执行的独立复核；保留cwd/source/launch/exit/receipt，无原worktree回读。恢复必须使用明确兼容Python与原浮点口径，不能为逐位一致改数值。说明这是证据/数学恢复，不是独立引擎性能复现。无需执行第二套性能重跑。

## 11. 新 stacked draft PR 与最终收口

建立新的英文 research Draft PR，base为核验后的R108分支，建议标题 `Round109: frozen M-B geographic evaluation and seed sensitivity`。不修改旧PR结论、不合并、不改默认ENS-C或用户原文件。只提交本轮必要代码/数据/证据/说明。

PR开头直接给唯一阶段状态，解释为何需要更广输入、本轮保持什么候选、12新输入与Seed重复各是什么、全部42臂是否完成、相对P的完整收益/风险及对ENS的代价。分列物理T与求解cap，披露max-normalized权重、沿用的兼容 `min_ratio` 字段及真实库存域、同一城市来源/站点重叠、有限Seed范围、未完成认证与所有真实故障。不要写“新cut”“稳定支配”或“论文算法已完成”。

推送后实际核验远端head/base/open/draft、关键科学文件与分片字节；以最新实际状态更新RESUME和交付清单，区分实测生产源、结果交付commit和后续receipt补充，不能循环伪造当前head已包含自身证明。

最终回报：PR链接、完整性与唯一阶段决定、12主角色/3Seed组结果、最差损失、数学/物理/覆盖与公共恢复审查结论、实际资源、原默认未改及下一阶段允许声称的范围。出现普通负面结果也必须完成规定画像并明确结束；任何结果都不自动获得下一轮探索授权。
