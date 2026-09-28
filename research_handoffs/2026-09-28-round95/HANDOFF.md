# R93–R95 追加三轮研究交接

本文件接续 [R92 交接](../2026-09-28/HANDOFF.md)，保留其历史事实，但以本次最终核定和最新 Git/进程状态为准。唯一源码目录仍为 `E:/codes/ExactEBRP`，远端是 `https://github.com/yifanXovo/TailoredExact.git`。本次用户授权的“不超过三轮”已经用完；本交接不授权追加实验。总体目标尚未实现，不能把完成三轮或提交 PR 当作算法成功。

## 当前判断

**ENS-C 保持保护默认；LP-G 是最值得后续确认的统一研究候选，尚不晋升。** 本轮同期 P-GRB 比较补上了一个重要证据缺口：F2、C20、B50 上 ENS-C 和 LP-G 都取得原问题数值证书，而 P-GRB 在预注册截止时均未证；U6 三者仍未证。LP-G 对 ENS-C 有两项明显认证收益、一项较小认证损失和一项短时终点损失。没有触发预注册严重门槛，但这是已用于开发/保护的四角色、单 seed，不是代表性、未适配或最终收敛确认。

两个新增数量邻域均具备可证明的结构增量，且通过微型资格；它们在固定真实见证上都没有改善原 F。因此不接入启动流程，不以新增实例、种子或组合挽救负面结果。H-ACT、A1/A2、OT/B1 的既有负面证据仍有效，不自动与 LP-G 叠加。

## 三轮结论与入口

| 轮次 | 问题与结果 | 处理 |
| --- | --- | --- |
| R93 | 两站同向整数库存下降。微例突破旧坐标/等量转移停点；D6/E8/S12 共穷尽 11,536 候选，3,135 物理可行，接受 0。完整诊断外层 0.991145 秒。 | 资格通过、真实见证零收益，独立模块保留，不集成。[决定](../../results/unified_exact_round93/root_decision.md) · [PR155](https://github.com/yifanXovo/TailoredExact/pull/155) |
| R94 | 冻结 R90 同一二进制、四角色、seed0、12 臂同期 P/ENS/LP-G 比较。全部完成并通过独立证据审查，详见下表。 | 保留 LP-G 研究资格，不晋升、不延长、不追加 seed。[决定](../../results/unified_exact_round94/root_decision.md) · [独立审查](../../results/unified_exact_round94/independent_final_review.md) · [PR156](https://github.com/yifanXovo/TailoredExact/pull/156) |
| R95 | 完整两站独立库存块，加精确整数载量域。微例比 R93 更强；固定三见证 419,717 矩形点，剪除 344,310，原 Evaluator 检查 75,407，接受 0。完整诊断外层 2.4100342 秒。 | 第三轮关闭，不集成、不加例。[决定](../../results/unified_exact_round95/root_decision.md) · [独立审查](../../results/unified_exact_round95/g2_independent_review.md) · [PR157](https://github.com/yifanXovo/TailoredExact/pull/157) |

R93/R95 的 D6 来自旧 startup 最终闭包；E8 是首次 startup 见证，**不是**后来两次中性移动后的终点；S12 是首次 startup、后续中性移动为零。它们是固定诊断输入，不能用于正式运行的历史 warm start。负面结论只针对声明邻域和这些见证，不是全局最优或全部启动方法无效的证明。

## R94 同期结果

表中秒数均为完整正式进程时间；“未证”对应删失，不能用作已经收敛的时间或与候选作精确收敛比。

| 角色 | P-GRB 秒/状态 | ENS-C 秒/状态 | LP-G 秒/状态 | LP-G 相对 ENS-C |
| --- | --- | --- | --- | --- |
| F2 | 897.172 / 未证 | 544.265 / 已证 | 292.250 / 已证 | 快 46.3% |
| C20 | 597.219 / 未证 | 314.907 / 已证 | 356.031 / 已证 | 慢 13.1%（41.124 秒） |
| B50 | 1797.156 / 未证 | 1069.266 / 已证 | 715.156 / 已证 | 快 33.1% |
| U6 | 1197.125 / 未证 | 1197.172 / 未证 | 1197.141 / 未证 | gap 大 11.85%，差 0.0026493691 |

U6 的 `(U,L,绝对gap)` 分别为 P `(0.2140770394,0.1251452598,0.0889317795)`、ENS `(0.1514209239,0.1290584417,0.0223624822)`、LP-G `(0.1539367476,0.1289248963,0.0250118514)`。完整精度、所有臂、输入身份、顺序及数值微差见 [机器摘要](../../results/unified_exact_round94/formal_evidence_summary_v4.json)和[作者报告](../../results/unified_exact_round94/formal_results_v4_report.md)。C20 的一个负有符号 gap 仅约 `−1.39e−16`，是原数值标准内端点舍入，不改容差。

冻结顺序为 F2 P→ENS→LP（各 900s），C20 LP→ENS→P（各 600s），B50 ENS→P→LP（各 1800s），U6 LP→P→ENS（各 1200s）。Thread/MIPThread1、seed0、Presolve−1、双 gap 参数0，场景与原容差冻结。P 是 plain 原 compact，无 ENS/HGA/历史 UB 或候选 cuts。任何严重阈值只监督独立研究是否继续，不进入正式算法。

12 臂共 60 次已返回 native 调用：42 次受限 LP、14 次受限 MIP、4 次完整原模型 P。LP 的 0/0 scope 标志是冻结源码设计，不可发布 global native bound；MIP/global 证据需要前提、覆盖与物理见证。全部 304 行物理 witness、终点、七份跨臂界检查及五参数/九项 readback 通过独立审查。

LP-G 共 13 个分点提案，其中 6 个实际 parent LP 内点、7 个中点回退；只有 F2/B50 各一次 LP-G 点真正形成原子分裂，另三次实际分裂来自中点回退。C20/U6 虽有 LP-G 点提案，却没有实际分裂。不能把点提案、目标达到、请求终结当成实际分裂或证书，也不能由相关性推断运行时间因果。

## 数学与算法不变量

完整 ENS-C 骨架、AM 公式、终止假设和原模型限制见 [旧交接的算法节](../2026-09-28/HANDOFF.md)、[算法底稿](../../results/unified_exact_round91/paper_algorithm_blueprint.md)和[有限性说明](../../results/unified_exact_round92/controller_termination_note.md)。本次没有改生产算法：24 个随机启动 + 1 个独立构造、top-8/top-6、R76/R83 物理闭包、AM0.08、depth8、最小宽1e−4、支持时长 rank≤3/最多50,000子集均保持。单一 whole-run 截止不等于组件预算。

原目标 `F=G_true+λP`，`r_i=Y_i/D_i, S=Σr_i, H=Σ_{i<j}|r_i−r_j|`，正 S 时 `G_true=H/(nS)`，S=0 则约定0。模型变量 G 为上图量，不等于任意叶点的真实 Gini。物理 U 必须由原 Evaluator 验证；global L 来自覆盖与合法作用域，不从 LP 数字或不同算法取最好值拼接。

R93/R95 的有限下降只依赖有限离散状态、严格原 F 改善和每次扫描完成；不声称连续梯度收敛、全局最优或多项式复杂度。R95 固定已服务站 a,b 的归属/顺序，令 `δa=u−Ya, δb=v−Yb`，原前缀载量 L 变为 `L−σaδa−σbδb`。按 10/01/11 分组，原全部载量约束当且仅当 `max(L−Q)≤σaδa+σbδb≤min L`。与库存范围相交后，每个 u 对应完整整数 v 区间。删零节点只去掉重复载量前缀；旅行、非度量删点、装卸和返仓时间仍逐候选用原 Evaluator 核验。截止途中丢弃未完整扫描的 best；整数域/非有限异常 fail-closed，不能算不可行点后继续声称穷尽。这是精确邻域域刻画，未经文献证明不得宣称新型全局 cut。

## 历史结果不能被新胜例覆盖

- R90 LP-G 原 19 角色中 F2/B50 有明显正面证据，C20 有损失；C2 seed2 反向。D6 旧 3600s 候选未证，新 7200s fresh pair ENS3448.704/LP3663.360 秒均证，LP慢6.22%，且该次没有实际分裂。旧删失保留，无需再重答已回答的尾部问题。
- A1 去掉24随机起点损伤 D6 UB，U6 gap 恶化；A2 两种数量 proxy 在固定三见证无原 F 收益。R93/R95 又表明单纯扩充两站数量方向不能自动带来当前真实闭包收益。
- OT/Gini cuts 有有效性和根松弛提升；R89 native B1 的 D3 约155.391→299.828 秒严重慢化，故暂缓。有效不等式不保证更快求解。
- R92 H-ACT 有原物理/raw-emitted共同包络证明及资格；D7 短时有益，但 U6 seed0 触发严重 gap 线，固定 seed1/2 复核未复现严重联合门槛，seed2仍回退。H-ACT继续暂缓，不能说无风险，更不能自动组合。
- 旧 canonical near-unit duration 的边界限制尚在：R92只修复新行，不证明旧 writer 对任意实数输入完全物理忠实。未来修该问题需独立正确性项目、所有对照共同重新冻结，不能暗改问题或容差制造优势。

## 身份、成本与原始材料

R94 使用 `build/research/round90-lp-g-split/ExactEBRP.exe`，SHA `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`，对应旧 Git ref `a71bd53ca412e9b9e529e7237446687d360a94ce` 的166个已核 blob。当前 R95 工作树不是该二进制源码快照。R95 driver SHA `a69114b730fe6f65cdc6d519dd2f9b6cf753903b89608b174316cd0e5a7cf1a7`；当前 core SHA `29cb167a388e1a76bd544131bf59684be3950f92f13ecdb755525644f596de12` 与旧隔离构建相同。工具链为 GCC14.2 UCRT/Gurobi13.0.2，build type为空，不称 Release。

R94 正式外层两次合计 **10190.272415 秒**，嵌套12进程 **10174.86 秒**，不可相加。资格/恢复已知完整外层合并后的仪器化总额至少 **10219.0611129 秒**，尚不包含独立复核与最终归档；失败的 v3 只读自检缺完整可靠计时，明确保留 unknown，不能伪造精确研究总成本。三类工程修复是 JSON int/bool 适配、LP/MIP作用域适配、离线重放计时字段语义比较；均不改算法、证书标准，不重跑已付费正式臂。原失败记录完整保留。

R95 configure/build/G1 一次共35.0365452秒，唯一G2外层2.4100342秒，归档外层0.5073221秒，另有oracle/validate/独立复核收据。R93完整build wall未采集，初次工具返回30.007秒仅运行前缀，不能写作完整build成本。详见各轮成本说明。

R95原raw35文件、23,140,787B，ZIP2,486,021B，逐member验证35/35；[交付说明](../../results/unified_exact_round95/g2_archive_delivery.md)、[清单](../../results/unified_exact_round95/full_block_g2_raw_manifest.json)。R93小raw直接提交。R94的[归档交接](../../results/unified_exact_round94/archive_v4/archive_handoff.md)和[分片清单](../../results/unified_exact_round94/archive_v4/archive_parts_manifest.json)覆盖全部12臂、资格、失败和恢复；最终核定见下文。原raw全部保留。

## 执行与恢复

Astra统筹、数学终审、准入/淘汰及Git；Sol high作者/运行/常规监控，Sol xhigh独立数学/源码/证据审查。本次客户端会话model/effort已核并保存于[身份记录](../../results/unified_exact_round93/agent_identity_verification.json)，不声称可独立证明不可见的后端权重。只用一个代码目录、一个重计算槽，同机性能串行；正常运行由worker等待，不每分钟唤醒root。

保留3个原有dirty文件、stash `0db4ef815976416edc800beba479f015a97895cd` 和历史untracked目录，禁止`git add .`或批量清理。三个文件为 `results/gf_compact_bc_round/handling_convention_test/handling_convention.json`、`results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv`、`results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json`。

下一次仅在用户恢复授权后，先读本交接、[研究判断](OPTIMIZATION_NOTES.md)、[完整继续prompt](CONTINUE_PROMPT.md)，检查最新Git/PR/活动进程/额度、小型decision与收据。不自动复用旧lease、不重复本次负面诊断、不增加第四轮。若未来拟晋升并进入广泛长时测试，必须先提交完整论文式LaTeX和实际编译、逐页核查的PDF，准确报告全部正负与删失；本次没有作出这种晋升决定。

## FINAL_UPDATE：根代理最终核定

- R93、R94、R95三轮均已结束，独立审查通过。R93/R95零真实见证收益，R94混合正负；保持ENS-C默认、LP-G研究候选。本次没有剩余实验许可，没有晋升或广泛长时测试。整体科学目标未达，交付后按用户三轮停止要求暂停，不标complete。
- R94全部证据归档136,691个唯一member、431,133,063原始字节，逐member路径/大小/SHA/CRC通过。ZIP为113,905,614B，SHA `f16239464f23c80ec146743f6d4b3622022d3509afa304378b1bfe38e393fcb7`；Git交付四个有序分片，原ZIP和raw留本地。根另核四片SHA、拼接SHA/大小、manifest身份和唯一member计数通过：[根检查](../../results/unified_exact_round94/archive_v4/root_package_check.stdout.json)。归档完整外层85.2064936秒，切片0.4002033秒，根包装核验0.5627618秒，均另列研究交付成本，无重跑。
- R94最终结果及归档提交 `1683dd13a` 已推送；R95隔离源码/负面证据提交 `b9229848f` 已推送，其分支已合并完整R94结果（合并锚 `eaac02320ac77eab221eca49d63fdbc607f9288e`）。当前最终目录是 `codex/round95-full-block-descent`。本handoff的后续提交通过 `git log -1 -- research_handoffs/2026-09-28-round95/HANDOFF.md` 查询，避免自引用。
- GitHub核验PR155、PR156、PR157均OPEN/DRAFT，分别依次base于R92、R93、R94分支；旧PR未关闭或合并。所有写入始终在原ExactEBRP目录，没有新代码副本或worktree。最终核验只剩三个原有dirty tracked文件；stash `0db4ef815976416edc800beba479f015a97895cd` 保留，历史untracked不清理。
- OS检查没有相关solver/build/runner/archive进程。执行者已结束，计算槽空闲。最后可见账户7日窗口为42%已用、58%剩余；停止原因是三轮上限，不是额度耗尽，未来恢复时重新读取。
- 独立Sol xhigh已一次审查根R94决定及三份交接文件，无实质更正，19个当时本地链接均存在。根补入的最终Git/归档/进程事实由实际工具复核；不再开启数学、代码或实验任务。
