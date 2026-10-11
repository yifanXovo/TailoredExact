/goal

# Round113：隔离进度发布故障，补齐两组地理角色的同启动后端归因

你负责本地 C++ 项目 `yifanXovo/TailoredExact` 的本轮实施、有限评测、独立复核与新 stacked Draft PR。

**唯一研究目标：在保留 R112 已合格 F2/C2/L48 证据的基础上，完整测量原定缺失的 G50-C1、G100-R2 四方法对照，查明零目标整数完成代价及 V100 的 own-UB/LB 取舍，给出统一 M-B 候选下一阶段的明确优先级。**

前置工作只修复已确认的非权威进度发布耦合，以及源代码支持的正常未启动 Optimize 的必要审计边界。保持 R112 生产 PE、H、模型、算法与参数不变。本轮 **8 个新正式臂、21600 nominal 秒**；总上限 **28 次保守启动 / 26000 外层秒**，资格子上限 **12 次 / 1200 秒**，包含在总额内。完成本轮后停止，不自动实现新机制或加跑。

## 1. 起点、身份与必须保留的结论

核验 PR174 / `codex/round112-paid-start-backend-attribution`。本任务编写时 head：
`9165e69bf41d1eb323fd52b8cb4a8230dcb4edd4`。
R112 实测生产 source：`d0014a7163e3996fe120471420e56b089c9715ae`；
科学 payload：`a3cac1df0ee1d4eaaeb87343508e0af31cfc3b40`；
PE SHA256：`a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8`；
Gurobi 13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

先读适用 AGENTS.md，检查最新远端、本地修改、RESUME 和活动进程。建议隔离分支/worktree `codex/round113-geographic-attribution-completion`，结果目录 `results/unified_exact_round113/`。若已有本轮同身份工作，按 RESUME 接续；不覆盖 raw，不重复已启动正式臂。

必读 R112 goal、final_report、blocking_incident、qualification、生产/性能身份与独立 admission、postformal/final-reader/public 恢复复核、fixed_manifest、当前 reports_final、数学说明和 next_research_decision；定向阅读实际 supervisor、atomic_status、P-S 生产入口、必要 audit 和离线 reader。历史沿 R112 已绑定权威承接，只为具体问题回查 R99–100 等，不再完整重审所有 PR。

必须保留：

- R112 **BLOCKED**：12 个正式臂合格、第13臂已启动并中断、第14–20臂未启动；30 个配对位置中 18 可评价、12 UNEVALUABLE。两后端五项均为 `WIN/WIN/LOSS/UNEVALUABLE/UNEVALUABLE`，仍 `INCOMPLETE_ATTRIBUTION`。
- R112 旧 arm13 的 partial own F≈0.008182628、3 个 returned LP 和 unreturned terminal MIP 只属部分证据；不能补造终点、whole、认证，不能作为新臂免费的 Start/UB。
- 已完成 F2 的正目标认证增量、C2 的 M-B 修复、L48 的 ENS/M-B 对 P-S 非严重时间 LOSS 均有效保留。F2 相对 cold P 有证明增量，直接 X/P-S 还包含 primal 差异；C2 的 ENS/P 严重 LOSS 与 ENS/P-S WIN 必须并列。
- R111 保持 `CONFIRMATION_SUPPORT / R110_MAIN_36_PLUS_R111_SEED_6`；R110 旧 arm42 whole 超 cap，保持 BLOCKED/UNEVALUABLE。
- cold P-GRB 仍为主要 benchmark；ENS-C 仍默认，M-B 为统一研究候选，P-S 仅作归因对照。用户允许公开 ENS 取舍，不设逐例胜 ENS/P-S 的暗门槛。
- R96 数量诊断、R97 反馈、R99–100 表示/单 MIP 消融和 R104、R105–107 已 STOP 测试族不重开。没有新 cut、branching、反馈、H 变体、按时间/Work/实例分派或参数网格。

## 2. 研究问题与分层设计

令 H 为当前原 ENS 24+1 构造、下降及 R76/R83 物理闭包，C 为真正原 compact。比较原 cold P、P-S=自付 H+C、ENS-C=自付 H+原完整后端、M-B=自付 H+冻结 M-B 后端。

R112 三角色已说明：完整后端有真实局部增量，也有实际代价。若剩余两项均有完整归因资格，五项描述性结果必然 mixed。**本轮不再把“是否 mixed”或“是否存在任何后端增量”当未知主问题。** 新信息是两个预定困难角色的代价、物理表现，以及它们是否改变下一研究优先级。

不重跑 F2/C2/L48，不添加正式性能 bridge。八个新臂使用同一新 wrapper，每个角色四种方法均重新从原输入独立支付全部费用；不以旧 P/ENS 或旧 partial 填入新组。

综合证据层命名为 `R112_COMPLETE12_PLUS_R113_GEO8`，逐行标明原轮次、PE/helper、输入与原 clock。旧 12 的完整时间永远来自原 receipt；新审计回放不能减去旧审计耗时、加上新耗时或制造新性能观测。每项方法配对只在其所属轮次的同角色内比较，不作跨 wrapper 同角色配对。

这是一份分层的五角色有限贡献图，不是 20 个新 wrapper 观测、R112 追认完成、新独立地理样本、总体胜率或统计显著性。保留 R112 的失败和全部实际费用。

## 3. 前置修复 A：只隔离非权威进度发布

先依据实际代码证明依赖关系。R112 使用的 supervisor 先写必要 `samples.jsonl`，再发布 `runtime_status.json`，随后推进采样节奏并执行内存/磁盘判断。原 `atomic_status` 的 `os.replace` 异常越过正常收尾，finally 杀停 child。

已知根因是非权威显示发布失败能终止权威求解生命周期；历史具体句柄持有者未知。Get-Content 并发读取只是候选原因。无需证明历史唯一持有者，不把修复扩展为 Windows IO 硬实时保证。

优先新增 R113 局部 adapter，只包住当前臂的可选状态发布：

1. 保留原正常发布及调度位置；只在该发布调用内捕获文件系统 OSError。序列化/逻辑错误不能被广泛吞掉。
2. 首次发布失败，内存保留当前臂/时间/路径/errno/winerror 和失败阶段，将本臂可选发布标记为 disabled。之后不重试、不 sleep、不因失败重新高频采样；恢复到下一臂时状态隔离并重置。
3. 失败后仍执行原必要样本记录、采样节奏更新和资源/截止检查。禁止 `except: continue` 跳过这些逻辑。
4. 使用必要的最终 audit/receipt 输出保存本臂进度退化事实，且在原 whole timestamp 前完成；必要持久化失败仍是真实故障。不可用最后的显示状态替代原始证据。
5. 保留所有权威 raw/journal/样本、身份、费用、时钟写入的错误处理，以及原 deadline、资源保护、kill/wait/finally。禁止对所有 IO 一概降级、延长 cap、改 reserve 或重新启动 native。
6. 如需 namespace 替换，严格限本臂和指定发布函数，成功/失败 finally 均恢复；不修改旧 round88/90/112 文件来追改历史，不影响另一臂或其它写入调用。

监控改为读取已提交并关闭的不可变证据/明确安全的显示接口，不再用 Get-Content 轮询活动可替换目标或活动写入日志。控制故障实验可显式持有测试文件句柄；不得修改系统 ACL、杀毒/安全设置或要求管理员权限。

Windows 可用受控 CreateFileW 句柄开放 READ/WRITE sharing、拒绝 DELETE sharing，验证旧 replace 失败类别和新路径。实际错误码照实记录，不强求一定为5，也不由该复现宣布历史唯一原因。参考 Microsoft CreateFile 的 FILE_SHARE_DELETE/delete/rename 合同：
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew

## 4. 前置修复 B：正确识别生产已支持的无剩余窗口

代码审查发现一项未影响 R112 完整 12 臂的潜在边界：P-S 可在模型/Start 映射之后 `beginCall` 已落盘、原工作窗口耗尽时写 `not_started` 并正常返回 `startup_deadline`，实际 Optimize 为0。继承 round86 audit 不认识该事件，R112 adapter 又将 call 声明数当作 Optimize 数。R112 资格已披露此路径未实际曝光；不得把它说成已发生的算法或数据错误。

沿真实生产代码与 journal schema 作最小必要审计修正，不改 PE 或人为强迫启动：

- 区分 call 声明、实际启动、returned、显式 not_started。实际启动依据原生产 phase/log/返回及结果计数联合核对，不要求或伪造原生产未输出的独立 started journal 事件；只统计真正执行的 Optimize，缺失 returned 不等于 not_started。
- 分别处理源码支持的模型前耗尽、映射后显式 not_started，以及 startup_zero。要求相应正常 completion、当前 own H 物理证据、真实 deadline/状态和必要文件完整；不由一个状态字符串无条件放行。
- 对映射后的显式 not_started，要求唯一 full-original call 声明及匹配的唯一 not_started，actual_Optimize=false、原 reason=no_remaining_original_work_window、结果 Optimize=0/status=startup_deadline。核对原序列/身份、已保存的完整原 reference/参数/矩阵、pre/post matrix、全列 Start 向量、真实一次提交及API读回。无 Optimize 不豁免这些已经发生的交接检查，也不要求只有实际 Optimize 后才产生的 lifecycle/ObjBound 字段。重复、错序、ID不符、已启动又取消、取消后有 returned/native bound/native witness 等矛盾须拒绝。
- 实际 started 的正目标 P-S 保持一完整原 compact MIP、完整 Start/API/读回/原矩阵及必要返回/范围审计；不能把不完整或失败的真实调用降格成零调用。
- 合法无 Optimize 返回保留自己 H 的 UB 与独立 floor0；已经实际发生的合法 Start 提交和API读回如实保留，但不给未启动调用原生 incumbent 采用、搜索、native LB、OPTIMAL 或 cover 功劳。若只有 H 而无后端搜索，归因记 BACKEND_NOT_EXPOSED。startup_zero 仍沿原零判据；正目标未启动不得无依据认证。
- 不扩大数值修复、删日志、补事件或修改旧 raw。若发现需要修生产时间语义、H、模型/mapper，则本最小协议不再适用，先交 BLOCKED 和证据，不自行扩大任务。

新 helper 的区别必须如实写成“进度发布隔离及正常未 Optimize 审计支持”；不能声称只改显示格式。审查生命周期入口及下游必要/离线 reader 的一致性，防止调用计数、端点、Start 或归因规则仍各说各话。

## 5. 有限准入与冻结

只做下列与两个已知风险直接相关的验证。原生产未变，不重做全部历史数学、13-case Start 网格、八 reference 原生导出或旧公共载体。

### 5.1 无求解器验证

- 从实际 source 构造受控 Windows sharing/replace 失败；旧路径失败、新发布 adapter 隔离、当前臂只记录一次失败并禁用，下一臂恢复。保留真实执行平台/错误码/句柄模式。
- 在实际 supervisor 控制流或 source-extracted 等价函数上，以受控 clock/假 child 检查：正常结束；可选发布失败后样本节奏及资源检查仍执行；真正必要样本/收尾写失败；截止或资源触发后的 kill/wait；finally 恢复。纯 mock 只能声称相应控制流覆盖，不能冒充原生 Windows 或求解器执行。
- 针对第4节真实生命周期构造有限合法/非法 journal 夹具，包括明确未启动与实际启动无返回的区别，执行实际新必要 audit 和离线判定边界；测试不额外调用 Optimize。
- 用 R112 保留 raw、已合格审计与源绑定作一次定向兼容回放：旧12端点、signed gap、证书、same-H资格、18既有配对和12缺失原因保持。只复算受改动影响的事件/审计边界及结果映射；不重新解析全部旧 LP 矩阵，不改变旧性能时钟。R112 partial13 仍拒绝为正式端点。

### 5.2 四个实际 H100 CLI

固定 `reference/round100_confirmation/H100.txt`：
SHA `04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71`，
实际 V20/M2/Q=[13,21]/物理T=5100。
P、P-S、ENS-C、M-B，Seed0，各 cap120，使用同一继承 PE 和最终候选新 wrapper。

核查 normal return、必要 journal/模型/范围、完整时钟与外层实际退出费用；P-S 的真 H、原 compact、完整 Start 及读回；三个 H 方法的完整语义和容量归属车队一致。只把这四臂作为资格，不进入正式胜负表。

至少 P-S 这一个实际 CLI，在 child 活动期间对该资格 campaign **实际用于可选发布的状态目标**持有受控句柄，触发新路径的显示发布失败并正常完成；不能只锁一个与运行无关的测试文件。故障只作用于显示目标，测试方法与 times/receipt 明确标记；其余权威文件不得受锁。先完成无求解器故障实验再进行，避免拿正式臂探索修复。未触发就如实记未覆盖，在资格子预算内只补受影响验证，不能宣称通过。

生产 PE、DLL、206源绑定保持；不为本轮重新编译求解器。若原 PE 缺失或 SHA 不符，不能悄悄用重编译的另一 PE 代替。完整检查两个新角色输入、全部八个 argv、原参数/30秒reserve、新 helper 闭包、预算与判定。

独立 reviewer 对有限执行证据与确切变更签署 `performance_admission.json`；最终源/helper/测试与签名身份一致。签署前无正式启动。正式开始后生产/性能helper/数值/时钟/判断规则冻结。

## 6. 两组固定正式实验：8个新臂

按 R112 原未完成角色及原顺序，串行完整执行：

|新臂|角色|方法顺序|V/M|Q|物理T秒|每臂cap秒|
|---|---|---|---|---|---:|---:|
|1–4|G50-C1|M-B、ENS-C、P-S、P-GRB|50/4|30,30,30,30|7200|1800|
|5–8|G100-R2|P-GRB、ENS-C、P-S、M-B|100/8|30×8|18000|3600|

原输入：
- G50-C1：`reference/round109_geographic/G50-C1.txt`，SHA `5740d09bf218cf6921cee6e60198f673151d6426fbcb0840259647129f3c4ed5`。
- G100-R2：`reference/round109_geographic/G100-R2.txt`，SHA `b3f3a1270f062e9f3af64d5b00392f51821bb775818edc6cd383fcd62550618f`。

T 是物理约束，cap 是运行预算；不得混用、重生成库存或重新按子集最大值归一化权重。

四方法含义完全继承 R112：

- cold P：真正原 compact、原参数和原行为。
- P-S：默认关闭的 `--round112-ens-start-compact`，独立支付原 H 与完整交接、一次原 compact MIP；保留 own UB，原 absolute deadline。与其它研究机制互斥。
- ENS-C：原 `research-round83-vds-equal-net-exchange`。
- M-B：ENS-C 加 `--round98-state-service m-binary`，effective identity `research-round99-ensc-discrete-structure-m-binary`；`--round100-continuous-quantities` 为false。

原 H Seed20260626、24+1及全部下降/闭包配置不变；求解器 Seed0，Threads=mip_threads=1，Presolve=Auto，MIPGap=MIPGapAbs=0，FeasibilityTol/OptimalityTol=1e-6，IntFeasTol=1e-5，原单核 affinity/编译器/栈，原30秒收尾reserve。lambda=.15、pickup/drop=60/60。原 VD-P/F0、AM=.08、target、epoch、cover、类型恢复和合法 Start 不改。

每臂从零开始，不接续旧中断 child，不导入历史车队/UB/cut/cache，也不跨本轮臂共享。即使先出现零目标，后续方法仍独立从输入运行；外部已知最优值只作事后解释，不能作为在线 Stop/Start。

普通 time_limit、负结果或 native 未报告新 Start incumbent 都照常完成两个组；不得按表现取消后组。真正未解决的权威执行/数学/身份/完整时间障碍按第9节停止。每个正式臂只启动一次。

## 7. 必须得到的观测、物理解释与比较

沿 R112 已验证 reader/数值政策生成当前八臂完整证据：必要入场/H、全量物理车队、原模型/全列Start、实际原生参数/调用/返回、true-G/cutoff/epoch和cover、own UB 流、合格 LB、所有必要后审计/写盘/whole 与实际外层退出费用。每臂显示退化事件单独记录，不影响权威资格。

same-H 资格必须核验当前 P-S/ENS/M-B 的25种子确定性语义、接受动作、完整车队与库存，保留原实际车辆容量/归属，只允许原等容量规范化。元数据差异沿已声明规则排除，不能只比 U0。H未完成、Start不匹配、后端未曝光分别标 reason。

保留空载出发、单站至多一车一次非零单向整数操作、每个prefix/返仓载荷[0,Q]、允许带载返仓及付卸载时间；Q不是累计pickup上限，Y在[0,C]，没有min_ratio库存下限。原 F/G/P、零分母与数值政策继承，所有自己的车队按原输入独立重算。

实际 LP/MIP 数和时间、native nodes/Work/root/end bounds、原日志已有 cut 计数、真实 atomic split、模型/控制/写盘残差按现有低开销证据记录。未知写unknown，不新增昂贵全树追踪。只有具备实际原子父节点替换及完整cover提交证据的事件才计为split；普通journal commit与lookahead model不计。非MIP/MIP时间差是观测账目，不可当可相减的因果改进量。

固定检查点300/600/900/1200/1800/3600中只列实际覆盖者及真实终点。自己的已证证书可延续；未证提前退出不插值，不把终点车队倒填。目标发现只报本臂最早已验证 committed own witness 的可用上界；原生真正首次发现不知则unknown。

### 7.1 G50-C1：零最优整数完成

正lambda/权重下 F=0 iff Y=D；已有合法零见证使全局 floor0 精确。明确报告每种方法是否取得 own零车队、库存剩余偏差、原始数量/车辆归属/载荷prefix，以及首次已验证零车队可用上界和完整认证时间。

相同完整 H 后，某后端取得零而 P-S 未取得，可认定本窗口整数完成增量；反向则是整数完成代价。两者均零时区分发现与完整认证时间；共同H已零时后端未曝光。不得把“仍无零车队”解释为可以抬高合法全局floor解决。

可对实际最终合法车队作少量确定性物理核查，例如一个被明确指认的数量改动是否违反后续prefix；不调用额外求解器、不做新的数量搜索/邻域扫描。只能说明该具体改动的可行性，不能据此断言整个MIP的隐藏根因。

### 7.2 G100-R2：零最优尚未知道

对每一合格开放配对报告
\[
dU=U_X-U_C,\quad dL=L_X-L_C,\quad d\Delta=dU-dL,\quad \Delta=U-L.
\]
据实际数值区分终局差异来自UB、LB或两侧，不新增任意百分比“primal主导”门槛。

只有新实际合法零车队才建立该输入新的零最优认识；正目标证书仍需原完整范围与数值资格。不能预设此角色属于G50的零目标机制。

### 7.3 配对规则不变

每角色固定六类：ENS/P、M-B/P、P-S/P、ENS/P-S、M-B/P-S、M-B/ENS，共12新配对；另列18个旧合格配对的固定来源，形成30个有来源的位置。

候选X、对照C，沿原：
\[
a_U=\max(.001,.01|U_C|),\quad
a_\Delta=\max(.001,.10|\Delta_C|),\quad
a_t=\max(30,.10t_C).
\]
仅X认证WIN，仅C认证严重LOSS；双证按whole时间材料性；双未证至少一项U/gap材料改善且无材料变差为WIN，反向LOSS，同时改善和变差MIXED，其余TIE。缺失/不合格UNEVALUABLE。双证严重损失沿时间至少2倍且多120秒；双未证沿U损失至少max(.001,.05|U_C|)且gap损失至少max(.005,.25|Delta_C|)。不变更原边界比较符号或interval政策。

保留signed微负gap、null/error与受损claim拒绝；原1e-7完整数值认证不写成有理数最优证明。任何已证矛盾只按原当前call/真实域/独立证据拒绝，不能以历史硬编码sidecar放行；独立LP与floor分开。离线reader修正保留原raw、差异与复核，不重跑性能，不伪造原缺失clock。

## 8. 明确终态与唯一下一优先级

执行状态与研究结论分开：

- `GEOGRAPHIC_ATTRIBUTION_COMPLETE`：固定8臂均按准入身份执行并形成合格完整时钟/权威证据，当前表、12新配对及明确不足原因可重建。
- `BLOCKED`：真实正确性、身份、执行、完整时间或资源障碍使固定工作未合格完成。记录所有已完成臂、partial与未启动原因，不把故障当算法LOSS。

对 ENS、M-B 分别保留5角色向量，逐项绑定 R112 或 R113。任何项缺少相同完整H、真正后端曝光或可比较资格，仍为 `INCOMPLETE_ATTRIBUTION`，保留具体不足；普通不足不自动算工程故障。五项均有资格则按原规则给 `MIXED_INCREMENT_OBSERVED`，因为既有W/W/L已成立。不为追求完整标签追加窗口、Seed或复测。

用 `geographic_bottleneck_assessment.md` 明确给出两角色各自的整数完成/UB/LB/认证时间观察；用一页 `next_research_decision.md` 选择**一个**后续优先级：

1. 主要 cold P 对比与既有统一 M-B 接受依据仍保持：下一阶段优先冻结候选的独立覆盖/论文实验，公开所有 ENS/P-S 代价。mixed或单项P-S更快本身不触发继续找新机制。
2. 新证据出现明确、材料性的主要 cold P 缺口，确实影响候选的原接受理由：指出具体角色、指标、严重性和可证伪的一个瓶颈问题，优先验证/修复该问题。对ENS/P-S的单独损失不能自动触发此分支；没有证据识别机制就明确目前不能指定新改动。
3. 当前执行或必要归因证据仍不足：结论为有限不足，准确指出缺什么、已知正负信息保留；不自动再开完整20臂、资格循环或长跑。

这些是研究优先级，不是新候选采用门槛。不能用各角色不同方法赢家拼成一个算法；不抹去R111支持，不因控制P-S变强而移动主要benchmark。下一轮建议不在本轮实施，不切默认、不自动晋级。

## 9. 预算、必要停止与可恢复交付

总限额28保守启动/26000外层秒；资格原生/辅助测试12次/1200秒包含在内。正式至少2wrapper+8child=10次，21600 nominal秒；每组另留120秒外层行政/关闭费用，总240秒，不是单臂cap额外求解时间。资格按上限预留后，计划22次/23040秒；余6次/2960秒仅供真实资格/工程故障，不放宽资格子上限，也无正式重跑额度。

资格显式启动的全部driver、wrapper、实际OS假child和句柄holder进程均计入12次/1200秒子上限及总额，包括Python、无Gurobi或0 Optimize进程；嵌套进程加启动数但不重复相加外层时间。进程内mock对象/线程不增加进程启动数，执行时间仍在资格driver内。事前用有限批次合并夹具并列明进程树；例如一个无求解器driver加至多5个OS child，与一个H100 wrapper加4个native child共11次，剩余1次也受原子预算约束。不可通过改称工程探针规避资格计费。纯离线历史算术/审查/打包等非资格工作另列工程时间。所有费用关闭覆盖真实wrapper退出；失败声明槽不退，未知费用取可证明的向外上界，不得提前把pending写成最终费用。

每组前检查余额足够覆盖全部未开始固定臂及外层预留。正式每臂最多一次；早停省下的预算不转成新Seed、长窗或重跑。正式期间不并行优化器、编译、压缩或重型审查；资格中的受控状态句柄持有是唯一专门声明的并发故障刺激，不改变算法工作。

正式开始前若准入失败，在剩余有限资格内只修受影响问题；正式开始后禁止改PE/performance helper/时钟/数值/判定再拼接。可选状态故障按已准入策略继续并留证；真正权威失败安全清理并BLOCKED。离线纯reader/比较错误可基于原raw定向修正与独立复核，不再启动native。

交付至少包含：goal与RESUME、两项窄修复的依赖证明和diff、实际故障/生命周期资格、四CLI、源/PE/DLL/helper/input/argv身份与独立admission、全部八臂actual raw/Start/车队/scope/cover/clock/费用、same-H、12新配对、带来源的五角色贡献图、两角色物理解释、final_report和单一next_decision。

公共载体只打包本轮必要证据，以及重建综合图所需的旧12有限权威/源绑定/原结果与签名；依赖清单明确历史raw是否被重审。不要复制完整R112或更早载体来放大交付。恢复脚本从恢复根重建新八臂和固定继承图，不回读原worktree补洞。

实际完成一次新export、空目录restore、恢复根核心CSV/JSON逐字段比较和独立复核。复用已知CSV大字段兼容设置，先在无native的小恢复检查中确认依赖与field limit；不等待最后才发现旧错误。保留PE/DLL/license/凭证排除，archive按真实大小处理，不人为分片。生产/科学payload与之后产生的恢复/remote receipts分开提交，不声称验证未来自身提交。

## 10. Stacked Draft PR 与额外复核

创建英文 research Draft PR，base 为核验后的 R112 分支。建议标题：
`Round113: complete the missing geographic matched-start comparisons`。

PR首段说明执行状态、8新臂完整性、两个后端分层结论、主要cold P比较、明确下一优先级。说明原R112仍BLOCKED、旧13不补造、旧12保留原身份，本轮不是20新测量。披露进度失败隔离及未Optimize审计修正，确认生产PE/算法不变；列所有正负、最坏代价、预算和真实恢复限制。

推送后实际核对远端head/base/OPEN/DRAFT、必要科学文件与真实载体对象；不修改旧PR结论、不合并、不替换默认、不动无关用户文件或环境权限。

任务组织和结果分析完成后，再额外复核：

- 是否保留有效旧12而只测预定8臂，每项配对均来自同轮同角色？
- 是否把非权威显示与权威证据隔离，显示异常后原采样节奏/资源/截止保护仍执行？
- 是否真实覆盖Win32故障类别，且未声称知道旧唯一句柄原因？
- 是否严分call声明/started/returned/not_started，不用缺失返回冒充正常未启动？
- 是否保留完整计时、own H与Start、原矩阵/参数/域/cover和数值资格？
- 是否正确区分G50已知零、G100未知零、primal与proof，以及观测时间账目和因果？
- 是否仍把cold P当主要benchmark，接受公开ENS取舍，没有P-S暗门槛或按角色拼赢家？
- 是否提出一个有证据的下一优先级，并在本有限阶段停止？

只修复真实缺漏。最终回报PR链接、8新臂/12新配对与分层30位置完整性、两角色的关键结果、分别的五角色后端结论、主要P优势与全部代价、费用、实际恢复结果和明确下一优先级。真实BLOCKED时报告足够证据与已完成观察，不伪称全部实验完成，不自动重试。

