/goal

# Round164：冻结主线的有限 Seed 稳健性确认与论文结论收口

## 0. 本轮目标与执行原则

继承已经完成的 R163。本轮回答一个直接关系论文主张的问题：**在 R163 六个已暴露配置上，冻结 GI-TBC/B 相对冷启动 Plain Gurobi 的证书优势、可行解质量与证明下界，在预先固定的另外两个 Gurobi Seed 下是否保持？哪些是跨这三个 Seed 一致的有限观察，哪些依赖求解路径？**

完成六个配置 × Seed 1、2 × B/P 的 **24 个新正式运行**；将合格 R163 Seed0 作为有身份的历史参照，形成六个配置、每配置三个 Seed 的完整比较；据此修订维护中的论文正文和补充材料。它是已有多 Seed 研究基础上的 **R163 新 cohort 的有限稳健性闭合**，不是首次研究 Seed、不是再次未见配置验证，也不是调参找最佳 Seed。

本轮正式方法只含 B/P。R163 已支持 B 为论文主线、E+ 为单独命名的有限 proof 增强；保留 E+ 的真实正结果和代价，不重复 E+ 全面板，不把新 B/P 结果外推为 E+ 的稳健性证据。本轮不引入新机制、改变 main 默认或合并前序 PR。

两 Seed、全部六例及完整顺序一次冻结，完整执行，不因 Seed1 的胜负再决定是否运行 Seed2。科学总容量 **16h=57600s**，新正式生产窗口名义合计 **12h=43200s**。预算是上限，完成本轮目标即收口；不用余额增加第三个新 Seed、缩放预算、调 AM、挑选 E+ 或重开邻域研究。合法提前认证正常结束该臂；不逐次 solve 请求人工批准。

算法定义对全部合法输入一致。实例名、来源、历史胜负、机器型号与速度不进入在线策略。固定 Seed、运行顺序、共同环境和分规模实验窗口属于实验设计，不是实例或硬件依赖的算法开关。

**正式生产算法继续使用已合格 C++。新增反复执行的算法核心必须为 C++。** 本轮只需参数化实验编排与分析，Python 可以读取 manifest、启动 C++、分析日志和独立验证，不得用 Python 重写 B/P 的建模、搜索或启动核心再拿来比较性能。E+ 历史 Python helper 本轮不执行，也不顺带移植。

## A. 工作起点、版本与本地条件

工作入口：`E:\codes\ExactEBRP-work\worktrees\paper-current`。阅读适用 AGENTS.md、WORKSPACE_POLICY.md，检查用户修改与活动进程后建立隔离 worktree。保护 `E:\codes\ExactEBRP` 和已有研究/论文树；新 worktree、build、raw、archive、temp、restore 全部置于 `E:\codes\ExactEBRP-work`。

任务依据 2026-11-12 UTC 的审查快照，执行时刷新：

- 仓库 `yifanXovo/TailoredExact`；R163 为 [PR #225](https://github.com/yifanXovo/TailoredExact/pull/225)，Open Draft，未合并。
- R163 branch：`codex/round163-stage-confirmation`；delivery head：`8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`。
- R163 science/carrier：`f7083ace21ad2a8bd54bed71711ceebcb97c9e8c`；数值 CSV 固定来源：`4d09e6fc9ed1c34dacd11aa8c7b7d22ae9f8ebbc`。
- R163 base：`codex/round162-physical-g-completion`；main：`b2b940c1e517a72e226ec60fc49ff19651737632`。
- R163 正式实测 C++ 源仍为 `e920b92e199e825ec89a2932f701861ff158e0d4`；production PE SHA256：`fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93`。
- Gurobi 13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

若 main 已包含所需依赖，从 main 开始；否则基于核实后的 R163 head 建立 `codex/round164-seed-confirmation`，Draft PR base 使用 R163 branch，无需等待前序合并。若已有同轮工作先接续去重。分别记录实测源码、PE/DLL、科学提交和最终 delivery 身份。

优先复用原 production PE 与运行环境，不为编排修改重编译核心。如果必须重编译或环境发生实质改变，冻结共同新身份、说明差异并完成有限兼容核对；新 Seed1/2 的 B/P 必须成对同环境。R163 Seed0 的复用资格单独判定：输入/物理参数/方法/PE/DLL/计时政策一致，运行环境具有可比性，才能作为同合同三个 Seed 的合并描述；否则将其保留为历史分表，新两 Seed 的配对仍有效。不为了凑三个 Seed 自动加跑六组 Seed0。

## B. 历史排重与新增信息

先读 `docs/current_mainline.md`，R163 的 final_report、decision、完整结果、方法冻结与实现绑定，以及 R137 维护中的正文 §5.4、方法/数值政策和对应 Seed 数据。需要判断下列边界时再有限回读原材料，不全历史恢复或重跑：

| 已有研究 | 已回答的内容 | 本轮增量与边界 |
|---|---|---|
| R130–134 | 多角色、多 Seed 的完整比较；R132 已有十二输入、两个 Seed 的 B/P 广度结果 | 不声称首次稳健性研究，不把不同版本/配置/预算拼成独立总样本 |
| R137 | 四个预选配置的 Seed1 P/PS/B；另有两个角色的 AM/机制重复。K35-U 的 B/P 可行解排序在 Seed0/1 反转 | 对 R163 新 cohort 补另外两个 Seed；不重跑 R137、PS 或已有消融 |
| R138、R140 | 已知角色的 Seed1 候选确认曾发生方向反转 | 单 Seed 的相反端点不充分定位稳定瓶颈；本轮全部六例保留 |
| R62、R96、R97、R160 | 被动 primal archive、完整固定归属/顺序数量优化、原生路线反馈、物理邻域及其完整混合结果 | 不把旧算子换输入/时点/接口包装成新机制；本轮不求解 C35 的 R96 受限模型 |
| R154–156、R163 | proof-only 库存下界有真实收益；R163 E+ 在 X35 提高最终 L，但未增加证书或改善 U | 保留 E+ 为补充，新增 B/P Seed 不能替 E+ 证明稳健性 |
| R157–162 | 整数资源/物理实现、完整物理 RN、连续 Q 的真实信息及完整收益边界 | 不扩大 block/node/pass、RN 容量或重开连续 Q 微变体 |

R163 的有限事实作为已完成证据引用：B/E+ 各认证3/6，P认证1/6；B/E+ 的 U 六例相同；E+ 仅 X35 最终 proof L 从 `.3949882559151472` 提高至 `.42319954961578576`；C35 的 P U=`.09331934374779818` 优于 B U=`.12956638965196035`，同时 B 的 L 更强。六个配置当时由预先冻结配方生成，现在均已暴露。

保留 B 为主是证据权衡，不是 B 支配 E+ 的定理。E+/B 三个共同 CERT 的付费时间均数值增加；按既有 `max(10s,10%×较快时间)` 尺度，仅 C20 的约26.10s增加达到实质差异，B20约1.70s和X20约6.18s没有达到。新文稿应准确表达这一点，不把三次小数方向统称三项材料性回退。

R163 的 B35/X35 库存定价仍有约 `.0143871/.0229556` 的上下界宽度。旧 R156 的近紧库存余量不能推广到它们；这也不自动构成本轮提高 RN 容量的理由。

## C. 方法、Seed 与唯一轻量资格

### C1. 冻结 B 与冷启动 P

B 严格沿用 S2/ms2：独立自付 own-H、M-B/VD-P、pair-only、AM=.08、maximum depth=8、minimum width=1e-4、AP off、R133 inclusive cutoff/source qualification 与 R134 exact-zero proof 政策。以 R163 已实测完整 B argv、`config/gi_tbc_round137.json`、`config/paper_s2.json` 为准；裸 CLI 的兼容默认 ENS-C 不能代替 B。

P 使用原 original compact 与 Plain Gurobi 合同；入口保持 `--method gurobi --plain-baseline --round127-mode p`，cold `NumStart=0`、MIPFocus=0、Cuts=-1、Presolve=-1、requested gaps=0。不提供 B 的 H、历史解、跨 Seed/跨臂 Start、hint、bound 或 cutoff；P 自身正常启发式/cuts按原合同运行。`--round112-ens-start-compact` 属于 PS，不加入 P。

两方法 Threads=1、MIPThreads=1，其他 q0/数值政策、原生产 deadline/shutdown margin 与正式 Native 不限4096节点的合同全部不变。R138–163 研究机制和 E+ helper 保持关闭。使用两份干净模板，从实际 argv、默认语义和每次调用 readback 核实，不在带有单向开关的命令末尾追加“off”来掩盖遗留启用。

### C2. Seed 必须真正到达每个 Native 调用

Gurobi Seed 固定为1、2；B 的 own-H seed **始终为20260626**。本轮研究 Gurobi 求解路径扰动，不改变 H 的算法身份，不同时研究 H 随机性。

R163 编排存在多处 Seed0 硬编码。为本轮建立一个权威 `arm.gurobi_seed`，统一生成完整命令、launch.seed、prereg/common、matrix、reader expectation、运行目录和 CSV 字段。核对实际 `--gurobi-seed` 及 journal 中每个 LP/MIP/后继模型的 `settings.Seed`；不能只改文件名或报告标题，也不能沿用 `round163_campaign.py` 的 `values.seed='0'`、`launch.seed=0` 和 `common.gurobi_seed=0`。

适配时一并检查 `round163_preflight.py`、`round163_qualify.py`、`round163_analyze.py` 和表格导出接口的旧Seed0断言/写入。旧analyzer按 `by[id][method]` 聚合；本轮必须按 `(input_id,gurobi_seed)` 配对，并保留method/repeat/run身份，避免第二个Seed覆盖第一个。最终核24个新运行、12个新配对、6个输入，不只修改总行数常量。

Seed1/2 的不同模型并不共享同一随机轨迹。每个正式臂启动新的求解生命周期，B 重新生成并支付自己的 H；固定 H seed 不意味着可以免费复用缓存路线或外部模型。

### C3. 有限资格与冻结

复用 R163 已合格的原模型、路线核验和 journal reader；只核本轮变化引入的风险：六输入身份、lambda/T、B/P模板、全部 Seed 传递、默认关闭、预算和证据绑定。

用既有 tiny fixture 做覆盖 B/P、Seed1/2 的轻量真实参数读回，确认 B 的后继 Native 调用也承接正确 Seed；可以合并在一次小资格批次中。资格科学费用计账，但不作为正式性能样本。无需重做全部旧数学/微测、重新优化旧大 LP、或运行旧120位置的 campaign。

在首个正式运行前提交方法、输入引用、24臂完整 matrix、顺序、评价方法和资格结果。如发现真实错误，修复受影响实现并重新冻结；reader 修复不触发健康 producer 重跑。只因结果不利不得改变方法或判定规则。

## D. 六个固定输入与24臂实验

### D1. 逐字节复用 R163 输入，不重新生成

权威 `results/unified_exact_round163/input_manifest.json` 的 SHA256：
`166bc5b463fb1dd2ad5c7819b5d31c86f706abf6ffd2a11469585ca623eedb1e`。

直接引用该 manifest 的六份 `inputs/<ID>/first/instance.txt` 与来源映射，核各自完整 SHA、规范化数学 key、lambda binary64 和物理配置。保留原 R163 实例 ID；R164 只新增运行 ID。不要用新 selection_id 重新生成库存，不需要新城市、站点抽样或难度筛选。

| 位置 | 原实例 ID | 来源/库存/地理 | n/M/Q | 原物理 T/s | 每臂生产 cap/s |
|---:|---|---|---|---:|---:|
| 1 | R163-C20-S | CITI / shortage / compact | 20/2/[30,30] | 5400 | 1200 |
| 2 | R163-B20-B | CABI / balanced / regional | 20/2/[30,30] | 7200 | 1200 |
| 3 | R163-X20-S | DIVVY / shortage / compact | 20/2/[30,30] | 5400 | 1200 |
| 4 | R163-C35-U | CITI / surplus / regional | 35/3/[20,25,30] | 10800 | 2400 |
| 5 | R163-B35-S | CABI / shortage / compact | 35/3/[20,25,30] | 7200 | 2400 |
| 6 | R163-X35-S | DIVVY / shortage / regional | 35/3/[20,25,30] | 10800 | 2400 |

沿用 tp=td=60s、rho=1、各实例实际序列化 weights 和 `lambda=1/Omega` 的原17位表示。数学 T 与 solver cap 分开。R163 源 manifest 的旧 `known=false/exposed=false` 是当时快照；本轮在新运行 metadata 明确 `exposed=true`、`panel_kind=R163 cohort finite solver-seed confirmation`，不改写历史快照。

### D2. 预先固定顺序

按位置1→6串行，每例先 Seed1 的两方法、再 Seed2 的两方法：

| 配置位置 | Seed1 顺序 | Seed2 顺序 |
|---:|---|---|
| 1、3、5 | B → P | P → B |
| 2、4、6 | P → B | B → P |

所有24个位置一次登记，固定同一正常运行环境与原亲和性政策，不并行争抢资源。若机器拓扑变化，一次统一选择可用核心并记录，不逐实例选核或换机。输入实例/Seed/方法/实际构建标识组成唯一运行身份。

每臂仍是一个生产总 deadline，包含启动、H、构模、全部 Native、在线核验和收束。事后必要核验单列 `T_verify`，`T_total=T_produce+T_verify`；嵌套 Runtime/Work、H成本不能重复加入外层费用。CERT 的 `T_cert` 沿用实际合格的 paid producer-close 政策，不回填未记录的首次证书时间；OPEN 不填 cap 为收敛时间。

原 shutdown margin、outer watchdog 与 cap 的关系按 R163 合格生产合同继承。预算表中的每臂额外300s是本轮科学容量的统一预约余量，用于必要核验/收尾；**不是允许多跑300s Native，也不是随意延长故障 watchdog**。

特别检查 `round163_common.metered()`：旧wrapper用同一个 `seconds` 同时设置 `reservation` 与 `timeout`。本轮编排应显式分开科学预约和原故障timeout，不能只把旧调用参数900换成300而无意改变生产/故障计时合同；底层总科学上限仍实际执行。此项是通用编排适配，不改C++算法。

完整执行所有位置，不按早期胜负筛停。正确性错误、环境不可用或总预算不足可以中断并记录实际缺失；不把缺失算输赢。技术失败保存费用和原证据，修复后只补受影响位置，保持对应 B/P 的公平身份；不重启已健康完成的臂来改善结果。不要为补齐有利分母越过预算。

## E. 分析：必须回答的三个层次

### E1. 每个 Seed 下的完整方法竞争力

新 Seed1、Seed2 分别报告六例 B/P：CERT/OPEN、physical U、raw/qualified search L、final proof L、原 gap、T_cert、T_produce/T_verify/T_total、Native Work/nodes、H实际成本、失败与缺失。每个结果都由自己的物理见证和原问题覆盖支持；不跨 Seed 拼接更好 U/L 制造证书，也不将 E+ floor并入 B。

对配置 i、Seed s 明确列出

\[
\Delta U_{i,s}=U_{B,i,s}-U_{P,i,s},\qquad
\Delta L_{i,s}=L_{B,i,s}-L_{P,i,s}.
\]

负的 ΔU、正的 ΔL 分别有利于 B。保留双向 trade-off；不能用一个 relative gap 或含糊 Win/Lose 抹去更差的可行解或更弱的下界。数值等价/资格沿用已冻结政策，不为本轮另造有利阈值。

全部配置报告认证数。仅在同配置同 Seed 两方法都 CERT 时比较付费证书时间，并同时报告绝对差、比例及既有 `max(10s,10%×较快时间)` 实质差异尺度；明确该交集的分母。OPEN 的预算消耗不是认证时间；不删除 OPEN 后把条件时间均值说成全样本加速比。Work/nodes作搜索诊断，不替代完整付费墙钟，也不承诺硬件无关性能。

### E2. 六个配置内的有限 Seed 稳健性

对每个配置并排展示 Seed0/1/2；Seed0 标为 R163 历史实测，Seed1/2 标为本轮新增。对两方法分别报告3个 Seed 中的认证次数；对 ΔU、ΔL报告逐 Seed 值/符号以及描述性的中位数和范围。三 Seed 的中位数端点只是汇总，不是一次运行或一个新证书。

明确六个配置是六个数学输入，18组 B/P 配对是六组内重复观察；不能写成18个独立新实例、18个 IID 样本或普遍成功概率。不选每例最佳 Seed，不做缺乏数据支撑的显著性/总体分布叙事；相同 Seed 标号也不构成两模型的相同随机轨迹。

重点解释三个预登记问题，同时保留全六例：

1. R163 三个 n20 配置上的证书模式，在 Seed1/2 是否保持；认证与时间方向分别说明。
2. 三个 n35 OPEN 配置的可行/证明端点方向，在三个 Seed 间是否一致；若有变化，指出是哪一个端点，不只报 gap。
3. C35 上 P 的 U 优势是三个 Seed 均出现，还是会反转？B 的 L 优势是否仍在？这回答稳定瓶颈的证据强度，不把多 Seed 一致性当结构因果证明。

另做一项不增加求解的统一 primal 分析：在任何新增运行前，为每例冻结 `u_ref(i)=min(U_B,Seed0,U_P,Seed0)`，使用 R163 原合格物理 U及完整精度。它只是**已知可行目标**，不是已知最优值。目标仅用于离线分析，不进入任何生产参数、Start、cutoff或停止条件。从已有 journal/完整路线与可信生产时钟，记录每臂首次被保存且可核验达到该目标的时间或区间；按原目标比较尺度处理数值等价。日志只给区间/最终见证时就保留相应界或未知，不能插值成精确首次时间，不能把事后核验时钟回填成发现时钟。窗口内未观察达到记为未达到/删失，不是不可达到。六例都按同一规则，不为这一诊断新增遥测工程或重跑生产。

以本次完整观察作出可执行判断：保留 B 的哪些优势性主张、收缩哪些“稳定”措辞、哪些困难输入仍是清楚的不足。如果证据混合，给出具体范围和反例即可完成本轮；不自动再开 Seed3/4 来寻求满意结论。

### E3. 有界结构解释，不追加求解

用已保存的 C35 H、B/P final fleet 与轨迹说明“可行解次优”和“证明缺口”不同。可以重算目标的 Gini/加权 penalty、旅行/处理量、载重/返仓和改进事件；这是日志与见证分析，不启动受限 MIP、route oracle 或新 producer。

审阅已从 Seed0 原见证读出：B 的 H U约`.1744902036`，Native 继续改善到`.1295663897`；P最终约`.0933193437`。两组车队的改进同时涉及归属、顺序、数量和目标分解；车队差异不能单独归因于某一操作。B 未服务站固定 penalty约`.0114025534`，低于 P 的目标，因此仅靠这个必要项不能排除固定骨架达到目标。取其余站 target得到约`.0335925462` 的库存目标，却违反原路线时间/容量，不能当完整物理解。

若本轮需要使用这些数字，从指定原始见证有限核验并保存来源即可；不重复旧实验。新增 Seed 的原生轨迹可说明相同劣势是否持续，但不由“更好的路线”推出“喂回该路线会改善完整算法”——R96/R97 已有反例。

R96 的完整固定归属/相对顺序数量诊断仍是可用工具；它在 C35 上只能新增局部归因，本轮不将其作为新理论对象或主要研究任务。未来若研究联合车辆归属/顺序/整数服务，需要具体区别于 R62/R96/R97/R160 的计算对象和证据，本轮无需为了填满“下一轮方向”栏再造候选。

## F. 论文组织与阶段结论

维护当前权威位置，以 R137 `paper_body.md`、`mathematical_analysis.md`、`supplement.md` 和现有导航为起点；不另建第二套冲突的论文正文。

本轮应完成以下实质编辑：

- 在已有有限 Seed 研究后加入 R163 cohort 的新比较，清楚区分 R137旧面板、R163 Seed0和R164 Seed1/2；保留原实验分母、版本与不利结果。
- 主文聚焦原问题/算法、有限实证结论与重要反例。将逐轮编号流水账、SHA、发布/清理/恢复流程等移至已有复现附录/来源映射，避免把 final_report 大段复制成论文叙事。
- 准确呈现 B/E+ 的取舍、上述证书时间尺度，以及新 B35/X35 库存余量；E+ 留在其已测范围内，不能因本轮未测而删除有利结果。
- 区分原物理/整数等价、有效松弛/目标图、完整 GI 覆盖、局部数值增益与完整算法收益。保留 true Gini/epigraph、S=0、inclusive cutoff、同域max/覆盖min及原数值资格；不将标准恒等式或负结果包装为新的普适定理。
- 给出清楚的论文结论：具体哪些配置/Seed支持 B，哪些是 trade-off/回退，证书、可行解与证明端点分别说到什么程度。主线算法身份、论文推荐与 released main 身份分别列明。

具体以当前 §3.5、§6.4、§6.5、§7/§7.1 为有限整理对象，并保留 §5.4 的四配置旧 Seed 结果：§3.5保留E+目标/作用域/费用；§6.4保留库存目标图与物理服务结构的区别、LP增量与完整收益的区别；§6.5合并重复的R163结果叙述并接本轮表；§7用研究结论代替项目决策书语气。§7.1的C35/R96工作单移至研究导航/附录，主文留下尚未解决的科学问题。不要改写旧结果来迁就新结论。

本轮不设“新增 OR 定理”、固定页数或多份 PDF 配额。若实质编辑的是维护中的 TeX，按现有流程编译并核一次；若权威增补仍在 Markdown，明确历史 PDF 的版本，不宣称未更新的 PDF 已含本轮结果。论文级目标要求论证与证据一致，并不以每轮必须发明机制来验收。

## G. 科学预算、主表与产物

| 阶段 | 预约秒 | 小时 |
|---|---:|---:|
| 轻量输入/参数传递/版本资格 | 1800 | 0.5 |
| 24臂及必要核验：43200s生产名义窗口 + 24×300s统一余量 | 50400 | 14 |
| 最终独立有限读回 | 1800 | 0.5 |
| 技术失败/恢复余量 | 3600 | 1 |
| **总科学容量** | **57600** | **16** |

阶段可在总额内调拨并记录原因。300s是预约，不是每臂必耗；不再机械套用旧每臂cap+900的18h整面板预约，与本轮16h顶额冲突。实际计费为非重叠外层费用，失败和必要科学检查全保留；普通编排写作、编译、文档和I/O分别记录，不叠加嵌套求解Runtime。新正式计算完成后不利用剩余额度启动额外研究。

主要产物置于 `results/unified_exact_round164/`，按现有习惯合并文件而非追求文件数量。至少包含实际 goal、历史新增信息表、输入引用与方法/Seed冻结、24臂 matrix/argv、资格、完整日志/路线/证明、费用失败、三个 Seed 的分层比较、论文增补与有限结论、独立复核、RESUME/publication/recovery/cleanup。

维护 `GI_TBC_vs_P_GRB_All_Tested_Instances.csv`，保留原28列schema、编码、精度和历史来源。R163 PR内表为85→91行；用户维护版本另含三条历史记录，本次审阅提供的是 **88→94行** 版本。优先定位并采用随本goal提供的94行主表；若本地仅有91行版本，先做有来源的并集合并，不以91行覆盖94行，也不删除以下历史 P 为 N/A 的记录：R138 `R-B35-S-T2/Seed1/2400s`、R155 `N-B35-S/7200s`、R156 `R-X35-S-T2/7200s`。

24新臂正常完成应产生12条新 B/P 配对，基于94行表应为 **106行**。实例 ID仍为R163原ID，`Gurobi_Seed`填1/2，`重复序号`沿用其定义、一次真实运行填1，`数据轮次`按既有数值列填164；新运行数据来源用本轮固定科学提交，实例元数据来源用原R163固定manifest。实际 `lambda/.15` 不填成rho。不能把Seed0再追加一遍，也不能把同一失败重试当独立重复或将E+换名为B。

先按配置 key、Seed、重复、cap、方法身份和来源去重并核真正主表。若94行文件在本机确实不可得，保留现有真实文件，交付12行的明确增量和三条历史记录待并集说明，不凭记忆补造字段或宣称已经更新不可访问的文件。缺失/未合格位置如实标注，不填估计值；无法沿用旧 Win/Lose规则时保留端点事实并说明分类范围。

## H. 最终额外复核与 PR

科学工作和文稿完成后，另做一次独立复核，可由数学/论文、执行/数据、研究方向三条 agent 分工完成；记录真实身份，不把自己的检查脚本冒充独立人员。

复核聚焦以下会改变结论的问题：

1. 24个登记位置是否完整，Seed1/2是否实际进入全部 Native，own-H seed是否固定、各臂是否自付，生产仍为共同C++。
2. 是否复用原六输入/目标/物理T，是否将已暴露样本或三个Seed误写成独立新实例；Seed0复用资格是否真实。
3. U是否由原完整路线支持，L/证书是否覆盖原问题；OPEN、未决、近零值和失败是否保留。
4. 费用是否完整、预算是否一致，是否借用跨臂路线/下界或按结果增删方法/Seed。
5. 结论是否保留U/L相反方向和时间尺度；是否把本轮B/P结果推广给未复测E+，或把相关路线差异写成因果/新定理。
6. 主CSV是否保留历史三条和来源精度，新增12条是否实际合格；论文是否保留先前正负证据及正确分母。
7. 是否已完成有限问题并收口，而非继续复制R96、重开旧邻域或自动追加Seed。

修复结论性错误或准确收缩结论；纯文字/reader修复不重跑健康求解。复核通过后正常commit/push，创建**英文 Open Draft PR**，建议标题：

`Round164: test frozen GI-TBC seed robustness and finalize scoped paper claims`

PR先说明为何需要这次有限确认、实际新增结果和论文结论，再列关键验证/费用。按A选择main或R163 stacked base，读回base/head/Open/Draft和证据链接。无需等前序合并；不自动merge、force-push或删除分支。不利/混合结果仍正常交付。

新增证据独立打包；旧证据以fixed commit/member/SHA引用，做一次有限公开恢复检查，不全历史空根重放、不重跑旧solver。按WORKSPACE_POLICY/R122仅清理本轮已结束、可重建且恢复覆盖的重复临时对象，保护唯一科学证据、失败、依赖、用户修改与活动worktree；零删除允许。商业DLL、许可证、凭证不发布，不更改全局app/proxy/model/credential/权限设置。

## I. 固定来源与复用入口

- [R163 / PR #225](https://github.com/yifanXovo/TailoredExact/pull/225)，固定delivery `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`；`results/unified_exact_round163/{goal.md,final_report.md,decision.json,structural_synthesis.md,input_manifest.json,method_freeze.json,matrix_frozen.json,science_identity.json,reports/complete_arms.json,reports/comparisons.json,cost_report.json,main_table_update.json}`。
- R163通用接口：`scripts/round163_common.py`、`round163_campaign.py`及其reader依赖。复用接口、核Seed硬编码；不要运行会重复生成新输入或重跑十八臂的旧入口。
- R163新增carrier `new_evidence_01.zip`：39888556 bytes、50601 members，SHA256 `365d892c8d3593ddcf8c98f88fa220d96f7afb889b0b6f47ba86f09006aa3512`；按member索引读取必要证据，不默认全量展开。
- [R137 / PR #199](https://github.com/yifanXovo/TailoredExact/pull/199)：维护中的 `paper_body.md` §5.4、`mathematical_analysis.md`、`supplement.md`、`matrix_frozen.json`；`config/gi_tbc_round137.json`、`config/paper_s2.json`。四个Seed1主比较与两个角色AM/机制重复应区分。
- R132、R134、R138、R140原final_report用于多Seed历史归属；R62被动archive、R96完整固定路线、R97原生路线反馈、R160邻域的final_report/关键实现用于排重。
- `docs/paper_s2_release.md`、`docs/current_mainline.md`、R135 `model_and_algorithm_appendices.md`及R133/R134修复，负责稳定方法、原物理与证明合同。

完成标准：**24臂预登记新运行回答六配置的有限Seed稳健性问题，完整结果进入主表和现有论文，明确支持与不足，并完成独立复核和正常Draft交付。** 不要求B逐例获胜，不把一次反例变成无限修补链，也不以新机制数量替代研究质量。
