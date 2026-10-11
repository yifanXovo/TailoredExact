/goal

# Round114：承接独立证据资格，完成 G100 四方法证据采集

你负责本地 C++ 项目 `yifanXovo/TailoredExact` 的本轮实施、有限验证、正式测量、独立复核及新 stacked Draft PR。

**唯一目标：在不改变算法和数值阈值的前提下，让可明确识别的原生下界声明失格得到正确归属和完整收尾；通过有限准入后，完成尚缺的 G100-R2 四方法采集，给出五角色后端贡献与下一阶段的明确结论。**

R110 已记录过同一 G50 cold P 的相同下界异常及同域反证，并合法使用独立全域 floor0 保留开放端点；R111 也承接了相关有限签名权威。R113 的新协议没有衔接这一已知情形，正常返回后在跨臂检查处中断。执行时遵守既定 STOP 正确，任务前置组织存在遗漏。

本轮预先明确、对四方法对称地承接“拒绝不可信原生声明、独立来源建立正式端点”的规则，不追认缺钟旧臂，不重复研究“矛盾是否存在”，不承诺定位 Gurobi 内部唯一原因，不开参数网格。前置工作仅修改必要的声明资格、异常收尾及对应 reader；生产 PE、模型、H、搜索、默认 ENS-C 不变。

正式仅 **4 个新臂 / 14400 nominal 秒**。总限额 **16 次保守启动 / 17000 外层秒**；资格子限额 **8 次 / 900 秒**，计入总额。完成固定工作或遇真正阻断后交付并停止，无正式重跑额度。

## 1. 起点、冻结身份与已成立的结果

核验 PR175 / `codex/round113-geographic-attribution-completion`。编写时 head：
`ea9410163aafd3877cdcde80e01ccd34d893f11b`；
科学 payload：`8dd38b790a4584f17aa75094f9451519e07bcdbe`。
继承生产 source：
`d0014a7163e3996fe120471420e56b089c9715ae`；
PE SHA256：
`a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8`；
Gurobi 13.0.2 DLL SHA256：
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

先读适用 AGENTS.md，核对远端、本地修改、RESUME 和活动进程。建议隔离分支 `codex/round114-bound-claim-isolation-g100`，结果目录 `results/unified_exact_round114/`。已存在同身份本轮工作则按 RESUME 接续，不覆盖 raw，不重复启动。

定向必读：R113 goal、final_report、blocking_incident、qualification、两项窄修复、生产/性能身份及 admission、postformal/whole-goal/restored 复核、numerical_policy、physical_completion、实际 cold journal/log/model、当前最终 CSV/JSON 和 next_decision；R110 `current_numerical_evidence.md` 与相关 scoped_evidence/returned_lifecycle，R111 对 main15/17/25/26 的有限承接；实际 `round113_campaign.py`、`round90` run_one/audit_launch、必要 audit、reader、NativeEvidenceJournal 的失败与返回合同。旧史仅沿这些有限已绑定权威承接，不再全面重审 PR。

保留以下结论和原始数据：

- R113 **BLOCKED**：G50 的 M-B、ENS-C、P-S 三臂合格；cold P 正常返回后下界一致性失格，缺原 whole/metrics；G100 四臂未启动。21/30 配对可评价。两后端仍 INCOMPLETE_ATTRIBUTION，ENS 为 W/W/L/W/UNEVALUABLE，M-B 为 W/W/L/T/UNEVALUABLE。
- G50 共同 H 的 F≈.0325201793721973；ENS own 严格库存零，whole=322.5586690000491；M-B/P-S own F≈.008182628062360805、whole=1777.2817804088118/1771.3991304999217，只有 station20 少1辆自行车。ENS/P-S WIN、M-B/P-S TIE、M-B/ENS severe LOSS；两个 tailored 臂均无真实 atomic split。
- cold P 的原始 U≈.2601945154521041、L=2.2806283239409983e-6 仅属诊断，不是正式性能端点或 LOSS。禁止补造旧 whole、给旧 P 采用 ENS 的解、离线减界后追认旧配对。
- R112 12 个合格原测量及18配对、R113 三个合格测量及3配对全部保留原时钟/身份。R112 partial13 不升级；R111 CONFIRMATION_SUPPORT 及 R110 旧 arm42 排除不改。
- cold P-GRB 仍主 benchmark；ENS-C 默认，统一 M-B 为研究候选，P-S 仅为归因对照。允许公开 ENS 取舍，不设逐例胜 ENS/P-S 的暗门槛。
- 不重开 R96 数量搜索、R97 反馈、R99–100 表示/单MIP网格或 R104–107 已停止机制；不加 cut、branching、H 变体、时间/Work/停滞开关、实例或规模分派。

## 2. 承接已经完成的模型反证，限定尚未知的内容

这是对 R110 已知矛盾的独立再验证，不是首次发现。R110 P15/G50-C1 已有相同 U、event52/53 的相同 L 及约1.000173407530002e-12的完整模型反例；原处理拒绝该 native call 的界，凭本臂合法 UB 与独立 floor0 保留 OPEN，并使用当时实际存在的 outward clock interval。该处理不能给缺原始 whole 的 R113 cold P 补资格。

R113 公共 archive SHA：
`990207810f40a0cdd46f40caaa1925d89e19103d82292d8fba143d4698e9bfbb`，
32982912 bytes；manifest SHA：
`e2998e98164cb80b63e3afb9e96f1775a5b03ace86831c0f365d341465a15348`。

本次管理复核已从真实公共载体独立解析 cold 保存的 compact：
`campaign/raw/04_G50-C1_S0_P-GRB/compact.lp`，
SHA `3c4385055008239f0b26af749792e95eeb7ef22403ef58035a51b5e75eb16b8c`。
实际 ENS 零车队来自 `02_G50-C1_S0_ENS-C/result.json`，
SHA `10442b3cbca6fc1484f06e6bf1ec0aa17e65cb15638ba5cba06d0185305ad751`。

全部 **13326 列、35567 行**有理数逐项验证结果：

|精确解释的矩阵|构造可行目标 U|行/变量界/整数违规|
|---|---:|---|
|cold LP 的打印十进制系数|2.9256256379999997e-16|0 / 0 / 0|
|同 SHA P-S 模型实际 API binary64 读回|1.979712144217771e-16|0 / 0 / 0|

第二项矩阵为 `03_G50-C1_S0_P-S/native.log.round112.start.before.matrix.json`，SHA：
`29bbffdd02ba923fe5e47dac1b5cef21b0d05ddb1961a74401584ef3285be4c2`。
其全部行/列/系数/类型/界/目标与 cold LP 转 binary64 后一致；**不是 cold 自身未保存的 API 快照**。

随任务提供的 `round113_independent_bound_counterexample.zip` 包含独立脚本、完整向量、逐行残差及第二份独立检查。将其作为明确来源的管理审查附件导入，不冒充 R113 原报告。若附件未随任务传入，依下列构造直接做一次有限复算即可，不以缺附件要求重跑 solver：

- 原物理整数车队给 Y=D，F=0；空载出发、整数单向服务、每站最多一车、全部 prefix/Q、返仓和物理时间均检查。
- 原 compact 是 G×Y 的 bit-product 表示。取真实 ratio 行系数 a_i，令 r_i=a_i D_i，e_i=|r_i−1|，h_ij=|r_i−r_j|；取真实 Gini 行 zprod_i 的系数 b_i，令 G=(Σh_ij)/(Σb_iD_i)，zprod_i=GD_i，prod_ib=G bit_ib，其余列由原车队构造。
- 对十进制 LP 和实际 binary64 矩阵分别用有理数检查全部列、行、界、整数、目标。不能直接把 r=1/G=e=h=0 的约1e-16等式残差叫模型错误，也不能用容差通过代替精确检查。
- 绑定冷 event52（最初已越界7.578293621148189e-7，close≈136.536s）、event53、returned event82、最终 log 和 ObjBoundC readback。不要把日志附近节点当作已识别的故障节点。

准入前作一次廉价、可复现的附件/实际源绑定与定向回放，纳入资格批次；不重跑整个 R113 carrier reader 或历史 LP。若与上述反证不一致，先定位具体字节/计算差异，禁止转入性能测量。

这已经排除“保存的原模型排除了该车队”“倒数打印舍入足以解释2.28e-6”“报告抄错”及单纯 ObjBound 整数舍入解释。cold 隐藏内存模型与原生 presolve/cut/LP/界维护的唯一内部原因仍未知，不擅自宣布 solver bug 已定位。

正整数库存与正 λ,w_i 给出原物理目标性质：
Y≠D ⇒ F≥δ，δ=λ min_i(w_i/D_i)，本 G50 的 δ=.006。
它说明最后1辆自行车的真实差距与微小数值界错误不同；不是所有正目标之间的公共格点间距，也不能据此把可疑 L 向上舍入到 δ。

保留原1e-7认证/一致性阈值和 FeasibilityTol/OptimalityTol=1e-6、IntFeasTol=1e-5。原生 primal/dual 容差不是目标误差上界。**不调 epsilon、不做 L−epsilon 或 min(L,外部U) 修补、不以一次更紧参数成功宣布普遍修复。** 官方数值语义参考：
https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/tolerances_scaling.html
https://docs.gurobi.com/projects/optimizer/en/current/concepts/modeling/tolerances.html

## 3. 唯一前置协议修复：声明失格与收尾正确分离

仅新增本轮 scoped helper，保留旧 helper/raw 字节。修改的是必要审计和研究记录协议，必须如实披露，不能称纯显示改动；不改生产 PE、native callback、在线树/界/终止、模型/参数或 H。

### 3.1 先明确可隔离的窄故障

仅当身份、输入、模型/域、必要 journal/commit、真实 Optimize 与返回链、物理见证及必要文件均可核验时，对**可明确证明的原生数值声明与同域合法见证不一致**返回结构化的 claim rejection。正常 returned 为通常路径；下述已有证据支持的极窄返回缺记类单列。

为每项声明保留 arm/call/sequence/model SHA/域/原值、反例来源、拒绝原因及依赖。覆盖实际 inner audit_launch/run_one 的失败出口及 outer campaign 检查，不能只改最后一条跨臂 assert。原 audit 失败记录保留，由有限合同决定独立端点资格。禁止捕获所有 AssertionError/OSError 并继续；模型、身份、物理可行性、无法确认 scope/cover、必需 I/O、未知生命周期缺失及无法分类的异常仍是 BLOCKED。

NativeEvidenceJournal 的失败 latch 可能停止后续发布。仅承接 R110 main17/plain 与 main25/tree 已证明的 **最后一个 MIP 因 bound-witness failure 缺 returned-journal、但实际正常返回且有独立 own 零证书** 类；按一般证据谓词实现，旧实例/key 只用于绑定 fixture，不能作为新臂路由条件。必须同时满足：

- 已提交前缀连续完整，末条 failure 明确为 `full_bound_witness_inconsistency` 或 `local_bound_witness_inconsistency`，并绑定当前 call、实际域及合法同域反例；仅末个实际 MIP 缺 returned，之前实调全部闭合，无后续未绑定 Optimize。
- plain 的原 API 返回/状态/真实计数，或 tree 的逐 call optimize ledger（模型/叶子/solve_kind/log/rc0），与 native 终局日志、完整参数、model/env/cleanup 计数、serialization→process_exit及真实外层 normal return 全部互证。原 native OPTIMAL/最终零仅作该已知正常返回类的佐证，不作独立证书。
- 本臂实际已提交车队经独立完整物理验证 Y=D，且独立 floor0/完整时钟成立；所有受损原生证明仍拒绝，原 missing-returned 和 raw audit=false 保留。

分别记录 declared、实际 Optimize、journal-returned、独立证据核验返回、explicit not_started 的计数。不能伪造 returned、把声明当实调，或把缺 returned 当 not_started。任一字段不齐、其他 failure/缺记类、未知额外调用均 BLOCKED；不在本轮扩大恢复范围。有限旧合同回放即可，不重做旧整套矩阵 runtime proof。

### 3.2 分别保留事实和资格

至少分开记录：

1. 实际执行/正常返回、必要收尾是否完成、真实完整时间；
2. own 合法车队/物理 UB、独立全域 floor0、独立 own 零证书；
3. 原生声明及其范围/依赖是否合格；
4. 正式端点、证书和配对能否评价及缺失原因。

一旦某 call 有确凿矛盾，保守拒绝该 call 的原生 bound、OPTIMAL、INFEASIBLE/剪枝关闭证明，以及依赖它的正目标证书/cover终结。保留原值与轨迹；不能换取该 call 较小的另一条界恢复信任。其他未受损调用保留自身域内资格，未经完整有效 cover 不合成为正全域界。

前瞻冻结、方法对称地允许 `SOURCE_REDUCED_OPEN`：本臂合法 own UB、原目标的独立全域 F≥0、完整真实 clock、身份/域/返回等必要证据均合格时，正式端点取独立 L=0、gap=U_own、certificate=false；同时记录 native_proof_qualified=false、被拒 call/依赖及 bound_source=independent_objective_floor。它可按原开放端点规则进入正式配对，但所有相关行/汇总须披露来源缩减，不能声称 native proof 已修复或取得原生正界优势。

这是以独立数学来源建立新的合格端点，不是截断/修补原 L、导入别臂 UB，或因 native 失格自动取得资格。缺 own 合法 UB、独立 floor 或必要身份/时钟/返回链时仍 UNEVALUABLE/BLOCKED。上述规则同等用于 P、ENS、P-S、M-B，且不追认任何旧缺钟臂。

own 严格 Y=D 的合法车队与独立 floor0 可单独成立 `OWN_ZERO_CERTIFICATE`，必须有本臂自己的见证和完整时钟；不依赖受损 native proof，也不由别臂零解代替。它仍须满足原配对和 same-H/后端曝光要求。保留无异常时原资格规则；不在本轮新增正目标证明替代器。

### 3.3 正确归属冲突，不让测试顺序决定失格对象

检查的是声明所属 call 与适用的见证域：

- full-original 全域界可对照任何独立验证的原域合法车队；全域 cover 合成界必须有完整合格依赖。
- 受限区间/叶子/cutoff 的局部界，只能由位于同一有效域的见证直接反驳；不得拿域外零车队否决合法局部界。
- 后跑 ENS 得到更好见证而揭露先跑 P 的坏界，应拒绝 P 的声明及依赖，保留 ENS 的合法记录。反向顺序给出相同最终资格。
- 别臂见证只供事后审查，不能送入在线 solver、H、Start、UB、cutoff、cache 或停机规则。

### 3.4 收尾和时钟

完整执行且只有上述结构化 claim rejection 时，仍完成本臂必要物理/身份/域/返回审计、拒绝记录、metrics、显示退化记录和费用，再实际写本轮 whole receipt；分别记录 native proof 拒绝与独立端点资格。原 cap/30秒reserve 不变，必要审计/写盘仍在真实 whole 内；超 cap 如实失格。

每个当前臂都在自身 whole 关闭前独立验证并保存 own UB、全域 floor0 及可适用的 own 零证书，即使当时尚未发现 native 冲突。运行内只做必要且已有数学依据的当前证据/同域/生命周期检查；资格期的完整矩阵有理数反证和额外内部原因研究不塞进每臂30秒reserve，也不把必须建立的当前端点移到计时外。

原已知跨臂检查仍在当前臂的收尾范围内；失败返回结构化记录，不越过必要时钟持久化。不提前取 whole，不把必要 arm-local 工作移到计时外。

所有固定臂结束后，按完整见证集合做一次离线 cohort reconciliation。它可撤销先跑臂的 native claim，并仅使用该臂原 whole 内已成立的独立证据报告 SOURCE_REDUCED_OPEN/OWN_ZERO_CERTIFICATE；不能借未来审查补当时缺失的 own 证据、重写已关闭的时钟、冒称原钟覆盖未来审查或追造 R113 旧 whole。记录每次检查实际可用的见证集合及时间层，最终配对只使用最终 reconciliation 的资格。

只要仍属于完整证据下的可隔离声明失格，记录后继续固定下一臂；普通负结果亦继续。真正必要执行/模型/身份/文件/资源障碍仍安全清理并 BLOCKED。不延时、不重启、不改变算法。

### 3.5 同步补齐一个已复现的零调用字段缺口

管理审查发现：R113 的 mapped_not_started 合法 fixture 中，单独把 `gurobi_status` 或 `native_mip_status_code` 改成2，或将 `gurobi_obj_val_available` 改成true，原 gate仍接受；实际已运行臂没有走此分支，非本轮冷界事故原因。

按 Result.hpp 默认值及真实返回位置，对源支持的0 Optimize分支同时要求上述状态为0/0/false，并保持 `gurobi_lifecycle_valid=false`；只补这些相互矛盾的原生声明检查及对应有限反例。保留已支持的完整模型前耗尽、映射后明确 not_started、own startup_zero；后者自己的严格零证书仍可成立。已发生的全列 Start 提交/API读回仍检查，不把0 Optimize当作从未构建模型。不重做原13-case Start或Win32故障网格。

## 4. 有限验证、两次真实 CLI 与独立准入

资格前冻结书面 `claim_policy.md`、修改边界、预定argv和进程树。只验证以上真实风险：

- 承接第2节的实际模型/原始界反证；原15合格端点、signed gap、证书、原21配对与既有缺失理由保持。旧 clock只绑定来源；不重审全部历史模型。
- 对实际新资格函数作有限回放：同一坏界在见证之前/之后出现；拒绝归属顺序不变；同域/域外见证区别；坏call依赖的正目标/cover证明失格；有完整独立证据的 SOURCE_REDUCED_OPEN 和 own 零证书；无自身 UB/clock 则不合格；没有坏界时原判定不变；必需身份/文件/未知生命周期异常不能降格。
- 承接已签 R110 P15 的独立 floor 开放端点及 main17/25 的极窄返回缺记类，绑定有限原 raw/ledger/clock 回放一般资格函数；各造一个缺必要字段/未知 failure/域不符/额外未绑定调用的拒绝例。旧原测量不改、不重新计时，不声称本轮真实注入或复现 native 故障。
- 检查实际收尾控制流：正常；typed claim rejection后写完metrics/whole并进入下一固定臂；必要写入失败仍失败；deadline/资源保护和kill/wait仍有效。使用真实源或source-extracted假clock/child，标明mock范围，不能冒充native故障。
- 对第3.5节补有限字段反例，并保留合法0调用例通过。fixtures是合成审计证据，不是实际CLI取消了Optimize。
- 回放与真CLI分层保存。不得改旧raw伪造真实数值故障，或把注入值写成solver实际返回。

先完成并冻结全部 helper 修改、有限源码/fixture回放，再启动最终真实资格 CLI；不在最后一处小修后沿用旧 helper 的实测资格。实际 CLI 仅固定 H100 的 **P-GRB、M-B，各 cap120、Seed0**，同一继承PE及最终新性能helper：
`reference/round100_confirmation/H100.txt`，
SHA `04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71`，
V20/M2/Q=[13,21]/物理T5100。

验证真实 normal return、原模型/参数、必要journal/Start/范围/cover、own物理解、完整clock与实际外层退出费用。两CLI只作最终收尾路径的实际资格，不进入胜负表；它们不声称复现G50的数值矛盾。P-S模型/全Start/无Optimize分支的未改部分承接R113实证，只对本次修改边界回放。

独立 reviewer 核对继承206份生产源、PE/DLL、继承helper与新增闭包、确切两资格/四正式argv、输入和全部有限实际证据，签署 `performance_admission.json`。最终被测字节与签名一致，签署前无正式启动。

无必要证据支持时不得新增 solver profile、参考模型重导出、重新编译PE或延长资格。若原PE缺失或身份不符，交付BLOCKED，不用不同PE替代。正式首臂后性能helper、数值/配对资格、模型和时钟冻结；纯离线报告错误可保留raw后定向修复和复核。

## 5. 唯一正式组：G100-R2 四臂，一次各自冷启动

|顺序|方法|V/M/Q|物理T|单臂cap|
|---|---|---|---:|---:|
|1|cold P-GRB|100/8/30×8|18000|3600|
|2|ENS-C|同上|18000|3600|
|3|P-S|同上|18000|3600|
|4|M-B|同上|18000|3600|

输入 `reference/round109_geographic/G100-R2.txt`，
SHA `b3f3a1270f062e9f3af64d5b00392f51821bb775818edc6cd383fcd62550618f`。
沿 R113 固定argv语义，仅输出目录/本轮helper身份改变；执行前逐项核对。

- P：真正原 compact 的 cold baseline。
- ENS-C：原 `research-round83-vds-equal-net-exchange`。
- P-S：`--round112-ens-start-compact`，独立支付当前H、一次完整原compact MIP及全列Start/API读回。
- M-B：ENS-C 加 `--round98-state-service m-binary`，effective identity `research-round99-ensc-discrete-structure-m-binary`；`--round100-continuous-quantities` 为false，实际类型按已冻结M-B语义审计。

继承 H Seed20260626、24+1/R76/R83；Gurobi Seed0、Threads=mip_threads=1、Presolve=Auto、MIPGap=MIPGapAbs=0、FeasibilityTol/OptimalityTol=1e-6、IntFeasTol=1e-5，单核 affinity及原栈/编译身份，30秒reserve、原hard-stop。lambda=.15、pickup/drop=60/60、VD-P/F0、AM=.08、target/epoch/cover不变。

每臂独立从原输入开始，不导入历史或本轮别臂车队/界/缓存，不接续旧进程。T为物理约束，cap为运算预算；不重新生成输入或按子集重归一化权重。串行运行，无并行optimizer、编译、压缩或重审。固定四臂普通正负结果与可隔离claim rejection均不改变顺序、不取消后续臂。没有新增G50、F2/C2/L48、Seed或窗口。

## 6. 必需观察及保持严格的比较

保留四臂全部实际 raw、journal/commit、返回、模型/Start/完整车队、H语义、范围/cover、own UB轨迹、原生声明与拒绝记录、审计/whole/外层费用。对所有可解释声明核对true-G/cutoff/epoch和原适用域。

same-H须比较 P-S/ENS/M-B 的完整25种子语义、接受动作、车队、库存和实际容量归属，沿原metadata排除规则；不能只比U0。H未完成、后端未曝光或Start不完整分别标记。所有车队沿原单次单向整数服务、前缀载荷/Q、带载返仓付卸载、Y∈[0,C]与物理时长检查。

优先复用现有低开销 native nodes/Work/root/end bound、调用、LP/MIP时间、实际atomic split及完整cover。真实父节点原子替换才计split，普通commit/lookahead不计；未知内部原因写unknown。不新增全树跟踪或节点切换机制。

G100零最优仍未知，只有当前实际合法零车队才建立相应认识。对每个有严格资格的开放配对报告 dU=U_X−U_C、dL=L_X−L_C、dGap=dU−dL；SOURCE_REDUCED_OPEN 使用其已独立成立的 L=0，同时在逐项及汇总标出 source_reduced/native_proof_qualified。失格项写null及原因；未取得独立端点资格的诊断 UB/floor 不能混入 WIN。不得把独立 floor 当作原生界进展或隐藏数值失格。

沿原材料性与严重性、signed数值/原1e-7政策，由继承reader的原比较符号实现：
a_U=max(.001,.01|U_C|)，a_gap=max(.001,.10|gap_C|)，a_t=max(30,.10t_C)。
仅X认证WIN；仅C认证严重LOSS；双证按whole；双未证按U/gap材料改善且无材料恶化，互有改善恶化MIXED，否则原LOSS/TIE。双证严重：至少2倍且多120秒；双未证严重：U损失至少max(.001,.05|U_C|)且gap损失至少max(.005,.25|gap_C|)。
**先过资格，再分类**；任一侧的必要正式端点资格不足则UNEVALUABLE。原生 proof 失格本身既不是算法 LOSS，也不取消已独立成立的合格开放端点或 own 零证书；native certified、source-reduced open、own-zero 三类来源分开披露。

检查点只列实际覆盖的300/600/900/1200/1800/3600及终点；只延续本臂已成立证书，不插值、倒填最终车队。发现时间用最早已验证 committed own witness 的保守可用上界，区分返回后汇总和实际见证提交，真实native首次发现未知则unknown。时间分账只作观测，不作可相减的因果份额。

本轮只产生6个新配对：ENS/P、M-B/P、P-S/P、ENS/P-S、M-B/P-S、M-B/ENS。

## 7. 分层证据与明确终态

综合层：
`R112_COMPLETE12_PLUS_R113_G50_4_PLUS_R114_G100_4`。
每行绑定所属轮次、源/helper/input和原clock，每项配对只在本轮次同角色内比较。R113那4个G100“未启动”记录留在历史执行账，不伪装成被补写。

固定五角色/30配对位置：旧21合格配对保留，加本轮6项；**最多27/30可评价**。原G50涉及cold P的3项仍UNEVALUABLE，即使四个G100全合格也不能称30项完整。最多19个合格原测量加1个旧postexit失败位置，不是20个本轮新测量。

分别报告：

- `G100_COLLECTION_COMPLETE`：4个固定臂各实际执行一次，完整执行/必要收尾证据、最终声明资格与缺失原因均已记录。某些原生proof拒绝不自动改变这个执行完成状态。
- `BLOCKED`：准入或真正必要执行/模型/身份/文件/完整时间障碍使固定收集未合格完成。保留已完成、失格与未启动位置及全部费用。
- 科学资格另列。ENS/M-B各自五角色向量以既有四项加本轮G100产生；若五项same-H、真正后端曝光及严格配对资格均满足，给 `MIXED_INCREMENT_OBSERVED`；否则仍 `INCOMPLETE_ATTRIBUTION`，列具体缺项。不得把collection complete写成attribution complete。

输出一页 `next_research_decision.md`，最终只选一个优先级：

1. G100取得必要资格、主要cold P比较仍支持既有统一候选理由：冻结M-B的独立覆盖/论文实验优先，公开ENS/P-S代价；不为mixed或ENS单项更好再找新机制。
2. G100发现材料性的主要cold P缺口并实质影响接受理由：指出一个有观测支持、可证伪的整数完成/UB/LB/认证瓶颈。未识别机制就承认不能指定改法，禁止按角色拼接赢家。
3. 仍缺严格数值或执行资格：本有限轮明确结束，区分已证明的失格、未能验证的部分和不可评价项；给出具体研究限制。不得自动进入“相同准入—相同长跑”的循环或再开一套参数网格。

这是有限归因和候选阶段判断，不是新独立地理样本、总体胜率、普遍精确证明或自动采用门槛。ENS默认、cold P主benchmark、历史支持与全部代价不改。本轮结束后不自动执行下一建议。

## 8. 预算与冻结后的停止边界

总 **16次保守启动 /17000外层秒**，资格 **8次/900秒**计入总额。
正式1个wrapper+4个child=5次；14400 nominal加120秒组级行政/真实退出预留=14520外层预算。资格按上限预留后共13次/15420秒；余3次/1580秒仅用于真实资格/工程失败，不放宽资格子限额、单臂cap或增加正式重跑。

资格所有显式driver、wrapper、OS假child、native/API进程均计启动，含0 Optimize。建议一个有限批次driver+至多2个OS假child、一个两CLI wrapper+2个native child，再一份定向资格收尾driver，共最多7次；剩余1次也在子限额内。进程内mock/线程不加进程数，时间仍计driver。不得改称工程规避资格费用。

纯离线既有证据算术、独立review、打包恢复是工程账，另列实际/未知时间；不加入solver名义计时。资格驱动的反证回放与新协议/fixture验证则计资格。嵌套时间不重复相加；声明失败槽不退，外层费用覆盖真正进程退出，不能把pending提前写成closed。

正式开始前核对余额可覆盖全部固定未启动臂及组级预留；正式每臂只启动一次。任意剩余预算不兑换Seed/长窗/重跑。未合格的算法、数值或身份修改不得在正式中途进行后拼接结果；新问题超出已签结构化隔离范围则如实BLOCKED。

## 9. 可恢复交付与范围控制

交付 goal/RESUME、声明合同与数学反证、最小diff/源依赖、有限资格原件、两CLI、确切身份/独立admission、四正式位置raw与状态、各层claim/whole/费用、same-H、6新配对、分层30位置与两向量、final_report、单一next_decision。

保留新bad claim全部raw，不把它藏到不存在的失败臂。current-call声明、own零、native证书、最终配对各自有可追溯来源；最终reconciliation独立重算顺序不敏感。

载体只装本轮必要证据、管理反证及重建旧15/旧G50失败位置所需的有限已签权威；不复制完整R112/R113载体，不重新解析无关旧LP。反证所需的指定G50旧模型/车队是明确有限依赖，不能伪称新测量。恢复从恢复根重建，无原worktree回读填补。

实际做一次public export、空根restore、核心CSV/JSON逐字段比较和独立恢复根复核。复用64MiB CSV field limit和既有恢复经验；准入前用小依赖检查避免最后才发现缺文件。源字节与CRLF/LF区别按实际manifest记录，不把原Git归一化差异改写为性能变化。archive按真实大小：低于95MiB不人为分片；确超上限才按既有可验证manifest方案处理。排除PE/DLL/license/凭证。

科学payload先提交；之后真实恢复与远端验证receipt另提交。只验证已存在的提交，不声称验证未来包含自身的head，不为事后工程receipt重跑native或重打科学包。修正纯离线reader/比较器错误须保留旧字节、diff、失败receipt与定向独立复核。

## 10. Stacked Draft PR 与额外整体复核

新英文 research Draft PR，base 为核验后的 R113 分支。建议：
`Round114: isolate rejected bound claims and complete G100 attribution sampling`。

首段明确执行状态、4新臂/6新配对完整性、严格资格及来源、五角色结论、主要cold P结果、全部代价和唯一下一优先级。说明本轮承接 R110/R111 已有独立 floor/窄返回类，改变审计/收尾协议而未改算法/PE；原R113仍BLOCKED、旧P无whole、G50对P的3项仍失格。已证原模型反证、未知native内部原因、未修复的数值范围分别说明；任何 source-reduced WIN 同时披露，不冒充原生数值修复。

推送后实际核对远端head/base/OPEN/DRAFT、必要科学文件与真实archive对象；不改旧PR结论，不合并、不替换默认、不修改无关用户文件或环境权限。

在组织/结果分析完成后再额外独立复核：

- 是否承接 R110 已知异常与独立端点规则，准确承认 R113 任务前置遗漏，未重复长跑寻找同一个矛盾？
- 是否只隔离明确的claim拒绝，返回缺记仅接受完整互证的既有极窄类，其他缺journal/身份/模型/I/O仍失败？
- 是否把拒绝归给真实来源且处理局部域、依赖和先后顺序，未伤及产生反例的合法臂？
- 是否保留原始坏界与依赖，独立 floor/own UB/own 零均在各自原钟内成立；方法对称地使用并披露 SOURCE_REDUCED_OPEN，既未修补native值，也未增加无必要的 blanket 配对禁令？
- 是否完成全部必要当前审计后真实写whole，未追造旧钟或声称覆盖未来复核？
- 是否只有预定两资格CLI及4正式臂，严格预算/冻结/各臂一次？
- 是否保留旧15、原21配对、G50三个缺项与所有历史代价，未混成20新测量？
- 是否区分收集完成与归因完整，以cold P和论文候选目标作唯一下一决策，未滑回无限机制/资格循环？

只修真实缺漏。最终回报PR链接、执行和科学双状态、实际测量/配对/声明资格、G100的UB/LB/整数完成观察、完整费用、真实恢复、独立复核与下一优先级。到此停止。

