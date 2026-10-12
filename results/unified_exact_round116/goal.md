/goal

# Round116：冻结四方法的跨来源评测与证明可靠性分层

你负责本地 `yifanXovo/TailoredExact` 的本轮数据准备、有限正式评测、数学核验、额外复核及新的英文 stacked Draft PR。

**唯一主目标：结束旧五角色的补测与机制归因循环，保持 ENS-C、冻结 M-B、cold P-GRB 与 P-S 全部生产算法不变，在一个事前指定的外部站点来源上完成六个新输入、四方法共24臂。判断既有优势能否转移，以及这些优势对应合法可行解、独立零证书还是可靠的非零原生证明。**

本轮是有限的跨来源证据，不是新算法开发，不是最终完整论文 benchmark。P-GRB 仍是主要 benchmark；ENS-C 仍为默认；M-B 保留 R111 有限候选身份；P-S 仍是同自付费 H 的贡献对照。允许相对 ENS/P-S 的公开取舍，不要求逐例支配，不按角色拼接赢家。

正式24臂，名义窗口50400秒。总上限 **56次保守启动 / 65000外层秒**；资格及原生参考导出子上限 **16次 / 1800秒**，包含于总额。正式每臂只启动一次。没有额外 Seed、lambda 网格、重新抽样、超窗加跑或正式重试。

## 1. 起点与本阶段已经关闭的事项

核验 PR177，分支 `codex/round115-producer-clock-attribution-closure`；本任务编写时 head：
`7eef812efb1bd3046c48e76ff6ac968de276a9b0`。

固定生产 source：`d0014a7163e3996fe120471420e56b089c9715ae`；
PE SHA256：`a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8`；
Gurobi13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

先读适用 AGENTS.md，检查远端、本地 HEAD、用户修改、RESUME、实际PE/DLL与活动进程。建议新分支 `codex/round116-external-source-frozen-evaluation`，结果目录 `results/unified_exact_round116/`。已有同身份执行按账本续接，不重复启动、不覆盖用户或历史证据、不改变权限/代理/默认算法。

定向阅读 R115 goal、final_report、measurement_policy_v2、producer_dependency_graph、current_source_qualification、physical_completion、research_phase_decision、objective_sublevel_analysis、最终review和public恢复；R114的既定claim政策；R112真实P-S模型/Start合同；R111候选规格；R109/R57纯数据生成及解析规则。只继承相关旧结论，不重读并复制全部历史载体。

必须保留这些事实：

- R115四臂全部完成；G100-R2 P-S自身Y=D，在产出约1306.537秒得到独立零目标证书，目标最优值现在已知为0。ENS/M-B/P的正目标分别约.0055284553/.0114347383/.0399421005。
- 四方法各有一条MIP调用被同域合法零见证推翻；三个正端点只保留own U与独立floor0。P-S自身native_proof_qualified也为false；其零证书不依赖受损原生界。不能把SOURCE_REDUCED_OPEN称为原生证明进展。
- 同H五角色向量ENS/P-S为W/W/L/W/L，M-B/P-S为W/W/L/T/L，均为MIXED。旧whole和R115产出时间异质，不是同一计时大benchmark。
- 旧G50 cold-P缺钟、R114 ENS超whole、R110 BLOCKED等均不追认；本轮不补这三个旧缺失比较。
- R115没有生产算法升级；phase A明确要求冻结并扩展独立覆盖。R99–100表示网格、R104资源预处理、R105–107已停止组合不重启。
- G50的最小可实现正目标beta=1837/224500已离线验证；当前严格改善需Y=D。G100 beta=299/108120小于三项正U。固定目标全车队子问题在R60/R61已有历史。上述信息不授权本轮实现target oracle、cut、分支、Start补丁或启发式。

写一页 `research_question.md`：当前缺的是外部站点来源的有限迁移证据，不是更多旧角色胜负；本轮可能支持、否定或暴露数值问题，三者均是有效研究结果。

## 2. 外部来源：只取一次官方站点元数据快照

### 2.1 预指定唯一来源

使用 Capital Bikeshare 官方 System Data 公布的GBFS站点元数据，不使用Citi Bike旧表，不使用行程/用户/自行车轨迹数据：

- 官方入口：`https://capitalbikeshare.com/system-data`
- 官方许可：`https://capitalbikeshare.com/data-license-agreement`
- 当前核验的官方发现入口：`https://gbfs.capitalbikeshare.com/gbfs/2.3/gbfs.json`
- 任务组织时该入口公布的英文station_information为：
  `https://gbfs.lyft.com/gbfs/2.3/dca-cabi/en/station_information.json`

**只核验到了官方入口和发现关系；尚未取得本轮完整station_information快照，不预先承诺站点数、字段完备或可达性。**执行时从当时的官方发现文档读取station_information及system_information，验证确为同一系统。普通重定向/官方发现URL变化如实记录，不跳到非官方镜像或另一个城市。

抓取前冻结 `source_recipe.json`、六角色表、版本盐和下面的筛选/排序/坐标合同；最多三次对同一官方端点的正常获取尝试，首次HTTP成功且结构有效的完整站点响应就是唯一快照。保留每次请求、状态、UTC、最终URL、响应字节/SHA256、GBFS版本/last_updated、官方许可来源。只因传输截断/无效JSON失败可以重取；不能因站点数量、地理或预期难度不满意改换快照。

按届时官方条款处理研究材料。不得绕过访问限制，不改变代理或账户权限，不抓取乘客信息；若许可允许作为非商业研究的来源附录，随本研究保留必要字节与归属，不单独经营/发布一个原始数据下载库，不使用官方logo或暗示背书。许可/接口无法满足公开可复核研究时，在任何正式/昂贵资格求解前给出DATA_OR_LICENSE_BLOCKED，无静默fallback。

### 2.2 建立一份确定性来源表

只保留静态实体站点：station_id存在，capacity为有限严格正整数且<100，坐标为有限合法WGS84；明确is_virtual_station=true的行不进入服务站集合。字段缺失/非法按事前规则排除并逐行记录，不将容量缺失填均值，不将实数capacity四舍五入。不同ID即使坐标相同也不自动合并；重复ID若物理字段相同可合并并保留全部原行，若相互冲突则阻塞源资格。

按station_id的UTF-8字节序稳定排序，再赋唯一从0开始的source_row_index。保留原ID与原行号；不把数字字符串转整数而丢失前导零。要求至少200个合格实体站点以覆盖本轮2V区域池；不足则明确DATA_BLOCKED，不降低V或重选来源。

用固定、记录版本和完整操作定义的投影，将WGS84经纬度转换为UTM18N米（EPSG:32618，always_xy）；所有源坐标需满足此投影适用范围。可以复用已验证转换器或固定本地pyproj/PROJ实现，不用手写近似替代。保存原经纬度、投影前后数值和软件版本/操作定义，服务站坐标最后按原格式保留三位小数。检查轴顺序、非有限值和明显量纲错误。当前source表有效范围不得通过算法表现事后调整。

若环境需要新数据转换依赖，优先使用现有能力；不更改生产求解环境。不能解决则在数据阶段阻塞，不能使用未经核验的米制近似偷偷继续。

## 3. 六个固定输入：改变来源，不同时改变问题或目标口径

数据版本：`round116-capital-external-v1`。所有散列材料的FAMILY使用该版本加唯一source响应SHA；其他编码、SHA排序、round/clip/调整次序保持明确且可重建。

复用R57/R109的纯数学规则，新增薄的SourceStation适配器。不能调用旧private源，也不能让旧443行断言错误地约束新系统。新路径/selection_id前缀使用本轮cabi标识，不能保留cb443标签而声称其为Citi Bike；这一前缀与source SHA均事前固定，散列材料中的所有引用同步。实际数学规则保持不变。小型等价测试对同一人工站点表比较继承函数与新适配器；不做求解或难度筛选。

- 地理选择：保持GEOGRAPHIC_REGIMES=(compact,regional)、REPLICATES=(1,2)及原四锚点规则。首锚点SHA排序，其余最远点，tie为源索引；compact取锚点近邻V站；regional在2V近邻池内进行原farthest-first选择V站。保持局部站点次序和同tie规则。不能为了获得更难/更易案例调整锚点、缩放坐标或剔除离群合法站点。
- 目标：原target_profile的容量比例[.44,.56]、散列和整数舍入，正且不超过容量。
- 初始库存：原shortage/balanced/surplus规则，delta_stock=max(V,round_half_up(.12 sumD))；分别总量sumD−delta_stock、sumD、min(sumC,sumD+delta_stock)，原局部扰动、总量校正和双向局部偏差修复保持。
- 权重：原max(.1,(D/maxD)^2)及最大值归一化、六位序列化。lambda=.15，装卸各60秒。min_ratio只保留兼容数值，绝不增加库存下限。
- 仓库：服务站已序列化坐标的算术质心、原三位小数和原placeholder；距离只由最终生产Parser按原Euclidean/1.5重建，不提供另一张竞争距离矩阵。

|组|新ID|V/M|地理/replicate|库存|Q向量|物理T|每臂cap|四方法顺序|
|---:|---|---|---|---|---|---:|---:|---|
|1|E20-C1|20/2|compact/r1|shortage|30,30|3600|900|P、P-S、ENS、M-B|
|2|E20-R2|20/2|regional/r2|balanced|20,40|7200|900|P-S、M-B、P、ENS|
|3|E50-C1|50/4|compact/r1|balanced|30,30,30,30|7200|1800|ENS、P、M-B、P-S|
|4|E50-R2|50/4|regional/r2|surplus|20,25,35,40|18000|1800|M-B、ENS、P-S、P|
|5|E100-C1|100/8|compact/r1|shortage|20,20,25,25,35,35,40,40|18000|3600|P、ENS、P-S、M-B|
|6|E100-R2|100/8|regional/r2|surplus|30,30,30,30,30,30,30,30|18000|3600|P-S、P、M-B、ENS|

P=原cold P-GRB，ENS=完整ENS-C。所有均Gurobi Seed0。以上六输入各生成一次，固定到 `reference/round116_external/`；冻结byte SHA、manifest、24个完整argv、顺序和比较政策，才允许正式测量。新名称不是新的数据来源；每输入仍来自一个共同快照，各规模可能重叠，并非六个独立城市或独立同分布样本。

冻结前核查本轮确无已测同身份实例；新输入SHA与历史输入完全重复时公开并停止数据准入，不能换盐重抽后掩盖。数据合法性检查只做解析、原数组/数量/范围、静态守恒、散列追溯与几何统计；禁止预跑LP、H、MIP，禁止检查结果后重抽、改T/Q/库存/权重、替换easy/zero/全不可达角色。首次出现生产结果后，该面板不再称未见数据。

`source_and_scope.md`必须区分：新的是站点坐标/容量来源；库存/目标/权重/车辆/T为同族合成。它检验跨来源迁移，不直接证明真实需求调度有效或一般化城市结论。

## 4. 生产算法、P-S合同与时钟保持冻结

严格取得上述PE/DLL并重新哈希，不重编译生产主程序。206生产源、原输入解析/模型/求解设置/H/Start/范围/AM均不变。若无法取得精确PE而需要新建，先报告BLOCKED；不能把新二进制冒充原身份。R115原adapter内仅适用于单组G100、固定路径或3600字样的行政断言，必须通过本轮显式manifest薄适配泛化；不能原样继承后在E20/E50失败，也不能借泛化改变native剩余时间计算。对同一人工launch记录做旧新语义对照，排除路径/组数/本轮cap字段以外的差异。

- cold P：真正原compact、原cold行为，无H/Start、外部UB/cut/hint。
- ENS-C：原 `research-round83-vds-equal-net-exchange`。
- M-B：仅加原 `--round98-state-service m-binary`，原ENS-Q选项false；不增删A/B/整数声明。
- P-S：原compact加原 `--round112-ens-start-compact`，本臂自己支付同H、映射全部列、验证原矩阵与向量并提交一次Start；常规正目标且有剩余窗口时只一次完整MIP。

H仍为原Seed20260626、24+1/R76/R83；全部方法Threads=mip_threads=1、PresolveAuto、MIPGap=MIPGapAbs=0、FeasibilityTol/OptimalityTol=1e-6、IntFeasTol=1e-5，原affinity、栈、编译和DLL身份。无时间/Work/停滞/实例/规模/地理/库存分派。不同cap只是评测窗口，算法内部不据此选择另一种机制。

完全承接R115前瞻measurement-v2：

- T_produce包括必要入场、自己的H、在线物理与模型/类型/Start验证、全部LP/MIP/callback/原scope-cover、原生cleanup/序列化、supervisor及已定义轻量最终检查；不得只报Runtime。
- 产出关闭并封存后是PENDING_VERIFICATION，不能先写passed=true。验证不重入native，不生成更好的车队/新求解下界，不倒填产出时间。
- 每臂串行完成T_verify，报告同t0的T_total；跨臂最终reconciliation另记组成本。验证耗时超过30秒不是产出超限，也不取消下一算法。
- cap内原30秒reserve和hard-stop/callback截止保持，不因外部输入新增更大搜索时间。产出超cap、必要文件损坏、真实资源故障仍如实失格。
- 同时报告总成本视图；不因较有利就切换主时间。旧轮次时钟、缺测、资格不重写。

三warm方法在每个角色比较完整H配置、25种子语义、接受动作、Y和容量归属车队，仅排除已许可的非算法元数据。H未完成或共同H已取得零，完整方法比较仍可有效，但其后端归因记H_NOT_COMPLETED或BACKEND_NOT_EXPOSED；不能用同U替代完整匹配，不为曝光额外运行。

## 5. 最小资格：一次准入，复用已经验证的审查工具

数据有效与公式/协议冻结后，只做触及的新输入入口与薄adapter资格。不要再建新审计平台、重做旧20/42臂或完整历史反例矩阵。

1. 通过现有零Optimize参考导出批次解析全部六输入，生成各角色原cold compact reference并记录实际类型/界/目标/行/列与输入参数。复用已验证辅助程序；必要重建只限同冻结模型源码的只读辅助工具，不改变生产主PE。不得把reference当已解LP或性能样本。
2. H100原fixture：`reference/round100_confirmation/H100.txt`，SHA `04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71`，实际V20/M2、Q13,21、T5100。四方法各一次cap120、Seed0，经过最终wrapper字节；检查P-S真实全列Start、原矩阵、三warm同H、在线/事后边界和实际参数。它不是V100或新面板预跑。
3. 新配对/可靠性表用少量人工records做零Optimize分类测试：自己的严格零、正U+floor0、可靠非零完整证书、一个被拒call但独立LP可保留、错域反例应拒绝、未知时间、未曝光H、同U不同车队、signed负gap。继承R114极窄missing-return与normal-not-started规则，不再放宽。
4. 验证新入口记录源、manifest/argv、原reference与report适配；生产文件全部哈希。R115有效pending/receipt实现原样继承，不在准入后移动检查或重写收据。

资格过程树与最坏声明先列入16starts/1800seconds子限额；包括actual native exporter、wrapper/child、资格post driver。纯不调用native的数据处理和离线复核按工程计费分列。不得用wrapper隐藏额外native批次。失败已声明槽不退。

准入签名绑定最终producer/helpers/reader、PE/DLL/source、raw来源及license、六输入、24argv、参考模型、所有既定政策及实际资格。具备独立执行者时使用；没有时必须准确说implementer-authored separate review，不伪称第三方复现。

## 6. 数值可靠性是独立结果维度，不是可被WIN遮盖的注脚

每臂保存自己的原生声明和资格后结果，分开记录：

- ORIGINAL_NATIVE_BOUND：有资格且未被反例推翻的调用/全域覆盖；
- INDEPENDENT_FLOOR：非负目标等原先已知下界；
- CLEAN_NONZERO_CERTIFICATE：自己的正目标车队加产出前的合格完整原域证明，数值认证而非有理B&B证明；
- OWN_ZERO_CERTIFICATE：自己的产出前严格Y=D合法车队加F>=0，无需受损native证明；
- SOURCE_REDUCED_OPEN：自己的合法正U，但相关原生证明失格，只有独立可用界；
- UNVERIFIABLE：关键物理/模型/身份/返回或范围无法核实，不能变成source-reduced。

同域合法反例成立后拒绝整个坏call及其所有依赖关闭/剪枝/证书，稍后更小界不恢复该call。其它独立正确call保留。反例需属于被质疑的实际模型、true-G/cutoff/epoch；root零不自动属于positive-G叶。跨臂或历史见证只用于离线撤销，不输入另臂H、UB、Start或搜索。cohort顺序逆转应给同一资格结论。组内交叉反证只使用同一原始输入与同一物理参数的当前四臂；不得因另一个角色也有零目标就将其当成本组反例。已关闭的单臂收据不改写，后续撤销追加实际时间和依赖版本。

R115四坏call是已知风险，不是本轮新发现；无需重跑其求解或全矩阵反证。新来源上有相同风险时保留具体证据，绝不调容差/seed/NumericFocus/缩放参数来美化本轮。只能明确已确认的数值不一致，不能预写“因为Gurobi某个cut/presolve造成”。

在线错误声明可能已经影响搜索；后验保留ownU/floor不能恢复过去剪掉的分支。因而source-reduced可以参与有资格的可行解/安全gap比较，却不能统计成可靠非零精确求解或证明提速。原生证据无反例也只表示本次检查未发现矛盾，不是普遍正确性定理。

若唯一问题是能够严格隔离的bound-claim失格，其它必要证据完整，按既定策略继续后续方法；不用此理由再次让基准未执行。若错误涉及源模型可行集、类型、合法车队、作用域无法恢复或安全资源，暂停并保留真实阻塞。不得接受已证错误的正证书。

本轮开始还要完成一个有限、零Optimize的旧声明影响说明 `known_G100_claim_impact.csv`，只处理已定位的同一G100-R2原问题：R115自己的零车队已使原最优值确定为0，因此R110/R111等此前声称为该原问题全局下界的正数需追加新的矛盾说明。例如R111 Seed1 cold P曾报L=1.4605722746091694e-5。先核对input SHA、T、Q、目标系数和问题完全相同，再撤销相应全局claim的当前可信性；不得仅凭这个全局反证就断言所有局部positive-G叶界都错误或已找到内部根因。旧raw/时钟/原阶段决定不重写，附新的认知时间、依据和有限影响表；原物理UB仍自己的，旧超时不追认。仅重算受影响的已公开配对primitive，明确变化是否影响描述分类，不把旧表替换成本轮正式观测。不进行全历史矩阵重审或任何旧性能重跑。

交付 `numerical_reliability.csv`：每方法/角色的actual/returned/qualified/rejected call数，最大已证矛盾，counterexample/model/scope身份，是否曾形成依赖关闭，native_proof_qualified、certificate_source及最终可用于哪些比较。缺少反证不写contradiction=0代表数学保证；未核项目用unknown。

## 7. 观测与无需新Optimize的数学分析

每臂完整记录H/自己的全部合法UB、有限实际检查点、全域LB与cover、真实原子split、native节点/Work/迭代/可见cut统计、模型规模及系数范围、native返回、参数、类型恢复、完整Start/读回和三类时钟。昂贵全树trace不新增；公开接口未记录的内部原因保持unknown。

原问题始终：

Y_i=b_i+sum_k(d_ki-p_ki), r_i=Y_i/D_i,
F=G_true+lambda sum_i w_i|r_i-1|，G_true=H/(n sum r)（原零分母约定）。

空载出发、单站至多一车一次非零单向整数服务；Y在[0,C]；每prefix/返仓load在[0,Q]；允许带载返仓且付卸载；完整时长travel+(t_p+t_d)sum pickup。Q不是累计pickup界，不添加min_ratio限制。

只读统计同时给出W=sum w、lambda W、G、P、lambda P和库存偏差K。因为

F=G+(lambda W) * [sum_i w_i|r_i-1|/W]，

固定lambda及max-normalization并不保持跨V的总惩罚权衡。不能把所有差异都称为纯规模效应，也不能本轮偷换sum-normalized目标。

用原输入做零Optimize必要条件：
B=sum b，B_lo=max(0,B-sum Q)，B_lo<=sum Y<=B；
delta=min_i(lambda w_i/D_i)>0，K=sum|Y-D|，F>=delta K。
若目标总量不在[B_lo,B]，记录目标库存被数学排除，不能通过修改库存/车队消掉这个角色。

可继承R115 beta算术，对产出时已记录的真实整数Y重算U及beta适用性。进一步，严格改善F<U必满足K<=ceil(U/delta)-1（系数和U按一致精确有理解释；只有已明确严格比较时使用）。这只是必要库存域，不代表可路由，不能截取一种旧归属/顺序来证全车队无解。本轮这些分析只描述瓶颈，不把它变成生产收缩、剪枝、target oracle或后验更强算法证书。

若某角色有自己的合法零车队，后续“未找到零”的差异主要按整数完成解读；若没有零证据，则不能因balanced/surplus标签断言最优为零。非零认证角色分别报告首个已验证目标值记录的可用时刻与完整产出认证；不将日志打印时刻当精确内部首次发现。

对open配对分解 dGap=dU−dL，保留正负；LB稍好不能掩盖UB严重损失。source-reduced的floor进展不能冒充engine进展。

## 8. 完整比较、证明轴和唯一阶段决定

每角色固定六对：ENS/P、M-B/P、P-S/P、ENS/P-S、M-B/P-S、M-B/ENS，共36个位置。每臂own证据独立，所有配对仅限同角色、同新协议、同PE。

沿继承材料性：a_U=max(.001,.01|U_C|)，a_gap=max(.001,.10|gap_C|)，a_t=max(30,.10t_C)。证书优先；双证按产出时间；双未证以UB/gap至少一项材料改善且无材料恶化为WIN，反向LOSS，指标双向为MIXED，其余TIE。缺少合格数据为UNEVALUABLE；数值tiny负signed gap不clamp、不用于失真百分比。严重规则同R115：仅control证书；双证至少2倍且多120秒；双未证UB恶化>=max(.001,.05|U_C|)且gap恶化>=max(.005,.25|gap_C|)。总时间作为次要视图完整保留。

ENS/P-S与M-B/P-S还需完整同H及实际后端曝光；逐项记不适用原因。共同H直接解完零问题不得把启动墙钟差归给后端。

先分开报告三个轴：

1. `execution_stage=COMPLETE/BLOCKED`：24臂实际完整和全部必要资格。普通LOSS、TIE、正常无新解、source-reduced不单独构成执行失败；真实无法复核和数据/环境/资源障碍才BLOCKED。
2. 每方法vsP的六项向量和全部严重损失；后端vsP-S六项向量及eligible分母。全部有资格才给POSITIVE_ONLY_OBSERVED/NO_POSITIVE_INCREMENT_OBSERVED/MIXED_INCREMENT_OBSERVED，否则INCOMPLETE_ATTRIBUTION。不得用部分结果替代六角色分母。
3. `proof_evidence`：分别统计可靠非零完整证书、独立零证书、可靠正LB开放结果、source-reduced与不可核验。无已知矛盾不等于数值普遍可靠；own零证书不能给受损native加分。

完整结束后，按以下顺序选择一个资源/研究处置；这是事前下一阶段规则，不覆盖R111、不宣称统计显著、不自动改默认：

A. **PROOF_RELIABILITY_PRIORITY**：新24臂出现已证明的同域原生claim矛盾（任意方法，包括P），或已确认依赖它的错误关闭。保留有效物理解比较，列明受影响范围；下一阶段优先一个最小可复现数学/数值问题，不凭WIN数写成“已稳定完成精确算法验证”。本轮不调参、不重跑或实现修复。
B. **PRIMARY_BENCHMARK_GAP_IDENTIFIED**：没有A，但M-B出现定义的严重P回退，或至少两项材料性P方向LOSS。优先一个由实际UB/LB/成本/证明区别支持的主要缺口；合理局部取舍仍允许，不要求每角色胜ENS/P-S。
C. **LIMITED_EXTERNAL_SUPPORT**：没有A/B，六组M-B/P均可评价，至少3WIN、至多1LOSS，V50/V100合计至少一项WIN，并且本轮M-B至少一项可靠非零完整原问题证书。冻结为具有本面板范围的论文研究候选，优先实验写作与后续预注册完整benchmark，不再为了ENS/P-S局部损失马上加机制。
D. **EXTERNAL_EVIDENCE_LIMITED_OR_MIXED**：完整执行的其余情况。区分样本过易/全部零、未证而有primal收益、收益有限、后端未曝光或指标混合。列出哪些证据已足够、唯一缺什么；不得默认再抽一批直到门槛通过。

若BLOCKED，报告最小受影响范围和已完成局部证据，不评为A–D完整面板结论。各条件的阈值只是有限研究资源决策，不是概率结论。P-S没有隐藏否决权；ENS损失公开；不按角色挑P-S/ENS/MB混成一个统一算法。

## 9. 固定资源、运行纪律与故障边界

24臂名义秒：8×900+8×1800+8×3600=50400。
六个组wrapper加24children至少30次保守启动；每组另留120秒管理预算共720，不增加各臂native时限。资格按上限16/1800，计划46次/52920秒，距离总56/65000剩10次/12080秒；用于实际后验审查及有限真实资格问题，不是额外性能额度。

每组开始前确认余量覆盖所有未开始正式窗口与管理预留。所有实际新增driver/exporter/资格原生子进程先计账，失败声明槽不退，native嵌套时间不重复加。独立纯数据/审查/公开恢复工程时间分列，未知人工时间不写零。正式组外层费用从创建至真实退出，验证时间也包含；不在尾部完成前提前关闭费用。

正式每臂最多启动一次；普通正负完成六组，不能见好就停或见坏换样。正式前源码/PE、producer/helpers/reader政策冻结；必要纯离线报告bug修正不改原sealed包，保留旧版本和精准diff/重审，不启动性能重测。正式必须修改生产或性能测量合同则本轮不能混合身份补完，报告BLOCKED。

原生运行串行，与压缩/编译/重型审查隔离；每臂验证完成后再下一个native。进度文件保持非权威隔离，必要输出/资源/终止监督不能失效。会话消失先核对具体PID和完成文件，不假定进程失败或重复启动。

## 10. 交付与额外复核、英文 stacked Draft PR

最少充分交付：

- research_question；官方source/许可/一次快照/排除与坐标转换、六输入source mapping、纯生成等价与冻结配方；
- 生产身份、最终24argv/顺序、薄adapter差异、原参考模型、资格/实际准入；
- 所有产出包、own完整车队/轨迹、模型/Start/types/参数/返回/scope/cover、三时间、claim撤销及来源；
- 24终点、36配对、same-H、证明可靠性、实际split/成本、严重损失、客观结构/目标尺度表；
- final_report、paper_candidate_spec更新、单一A–D阶段决定或BLOCKED、费用/失败/限制；
- 原始source只作为有许可的本研究附录，明确外部系统无背书，禁止公开native PE/DLL/license/凭证、无关用户文件。

复用既有恢复/比较工具，先查显式依赖闭包和CSV容量，不复制全历史载体。打包本轮必要raw及少量已签旧权威，实际一次公开export、全新空目录restore，从恢复根重建全部当前核心字段并比较。缺一个小型历史依赖只按已签Git字节补该项，禁止反复重包以代替科研。记录实际范围，不把hash或自审称成第三方原生复现。

建议英文Draft标题：
`Round116: evaluate frozen exact backends on an external station source`
Base为核验的R115分支。PR先给24臂完整性、六输入来源及合成边界、主要P结果、P-S后端取舍、数值证明可靠性、三时钟、预算、实际恢复和唯一阶段决定。保持旧PR结论、不合并、不修改默认、不自动执行下一轮。

完整分析和任务/报告组织后必须额外复核一次：

1. 是否只改变数据来源而偷改目标/物理/生产PE，或对新数据做过结果筛选？
2. 官方snapshot/许可/投影/容量/ID是否可重建，数据是新来源但是否错误声称六个独立城市或真实需求？
3. 是否四方法独立支付H，实际原compact与Start合法，无跨臂UB或缓存？
4. 是否仍将在线检查留在产出时间，并对后验成本完整披露，未追认旧数据？
5. 是否用source-reduced WIN掩盖错误原生界，是否正确区别自己的零证书与可靠非零证明？
6. 是否把beta/K必要条件当成可路由、全局格点、新算法或新证书，是否遗漏库存总量和系数精确性？
7. 是否24臂/36对/源资格/预算/停止条件齐全，是否由实际结果选择唯一优先级而非继续无条件开轮？

准确说明复核执行者与范围；只有实际第三方才称第三方。最终推送后核对远端head/base/open/draft及必要文档/载体OID；科学payload与后续receipt分开，回执不声称验证包含自己的未来commit。交付真实阶段结果后停止。
