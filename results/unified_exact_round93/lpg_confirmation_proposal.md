# R93 LP-G 有限同期确认方案（仅协议草案，未运行）

日期：2026-09-28。问题只有一个：冻结的 R90 LP-G 相对 ENS-C 的正负混合表现，在纳入**同二进制、同期的原始 P-GRB** 后，是否仍值得投入冻结新数据与晋升论文。此方案不宣布 LP-G 晋升，也不将旧输入称为真正未适配确认。它不改算法、输入、容差或历史结果；本文件没有生成数据、构建或启动 Optimize。

## 已知边界

- [交接](../../research_handoffs/2026-09-28/HANDOFF.md)、[后续判断](../../research_handoffs/2026-09-28/OPTIMIZATION_NOTES.md)、[R90 G4 决定](../unified_exact_round90/g4_panel_decision.md)、[C2 三 seed](../unified_exact_round90/c2_repeat_report.md)、[D6 尾部](../unified_exact_round90/d6_tail_report.md)及[比较地图](../unified_exact_round92/benchmark_evidence_blueprint.md)共同支持：F2/B50 有同期 ENS-C 认证收益；C20、D6 有损失；C2 有反向 seed；D7/U6/F5/F6 等仍删失。旧 R87/R88 P-GRB 不是 R90 LP-G 的同期对照，不能相除出 LP-G 对 P 的时间比。H-ACT 已暂缓，不能与 LP-G 拼合。
- [原计划](../../research_plans/ensc_optimization_plan_2026-09-26.md)只给 H1–H8 八个**结构建议**，尚未冻结完整生成程序字节、seed 派生、样本选择、候选、执行顺序和失败规则。[19 角色清单](../../research_plans/ensc_optimization_instances_2026-09-26.json)明确写 `H1-H8 remain ungenerated`；仓内现有 `reference/round82_unadapted_confirmation`、`reference/round86_unadapted_confirmation` 已经用于后续开发，名字中的 `unadapted` 不是当前 LP-G 的未见证据。真正 H1–H8 必须先整体冻结候选和配方，随后一次性生成并保留所有结果，绝不能按性能再选样本。CitiBike 同坐标总体还须披露站点重叠。
- 本小批只允许得出“值得/不值得继续投入”或“未决”；不能代替多结构、新数据、多 seed 和最终长时认证。若小批有根据地支持拟晋升，广泛长时前必须交付实际编译并逐页检查的论文式 LaTeX/PDF，且在其中冻结后续范围。本批不是绕开该论文门槛的最终 campaign。

## 有限四角色与上界

全部是先验指定的**开发兼保护输入**，均取 solver seed 0；没有根据运行结果加 seed、换角色或延时。每角色 P-GRB、ENS-C、LP-G 三臂各独立完整运行，先验顺序交错，结果无论正负全部保留。上限是每臂的完整 `ExactEBRP` 进程截止，内部 LP/MIP 只继承同一截止，不分配新秒数或 Work。

| 角色（原问题身份） | 作用与旧观察 | 每臂完整 cap | 顺序 | 最多进程秒 |
| --- | --- | ---: | --- | ---: |
| F2，R86 varied，T3600 | 旧 LP-G/ENS 311.578/585.656 秒双认证的正例；旧 P 配额中断仅作背景 | 900 | P→ENS→LP-G | 2700 |
| C20，CitiBike compact V20，T10800 | 旧 LP-G/ENS 382.922/341.219 秒的认证反例 | 600 | LP-G→ENS→P | 1800 |
| B50，CitiBike regional V50，T1800 | 旧 LP-G/ENS 762.406/1148.078 秒的较大实例正例 | 1800 | ENS→P→LP-G | 5400 |
| U6，R82 varied，T18000 | 旧两臂 1200 秒均 open，检查完整进程下 U/L/gap 与 P 的删失关系 | 1200 | LP-G→P→ENS | 3600 |

固定总上界 **12 臂、13,500 进程秒（3.75 小时）**；预检、离线审计、独立复核与无损归档另记实际墙钟、文件数/字节及哈希，不把嵌套耗时再相加。按一槽串行，每臂完结并通过审计后才发下一臂。缺失、异常、杀进程、identity/数值/物理/coverage/跨臂冲突或预设严重风险信号时停在已付前缀；单 seed 风险不改写为“经确认严重回退”。不重启、补跑、移换顺序或另挑角色。若某 P 臂迟迟 open，按上限给删失和合法 U/L，不延长到“终于证明”。这四角色兼顾强正、认证负例和 open 风险；不宣称是随机样本，不能用该集合估计总体平均优势。历史 D6 7200 秒新配对已回答可否闭合，故不再次投入 D6。

## 冻结身份与可实施性

优先复用已存在、只读 SHA 核为 `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2` 的 `build/research/round90-lp-g-split/ExactEBRP.exe`，对应 R90 已锁定源身份；绝不把当前 R92 HEAD 或 H-ACT 构建代替它。正式执行前重新核该 SHA、固定七个核心源与生产 blob 身份、输入文件 SHA、Gurobi 版本/许可证、机器槽、无残留进程及足够研究额度；这些预检不授权自动运行。F2/C20/B50/U6 输入 SHA、T、lambda=.15、pickup/drop=60 由各自 R90 G3/G4 prereg 与原清单逐字绑定。所有臂线程 1、MIP 线程 1、Seed 0、Presolve -1、相同零相对/绝对 gap、相同进程 cap、`cap−6` native 时限与退出余量；每臂记录输入、命令、环境、二进制/模型 SHA 与真实 set/get 返回码和 effective 参数。

R90 二进制含 `--method gurobi` 原始 compact 路径；[R88 三臂 runner](../../scripts/round88_a1_g3.py)已有 P 命令和原 compact fingerprint/export 审计的参考实现，[R90 G3 runner](../../scripts/round90_lp_g_g3.py)已有同二进制 ENS-C/LP-G、完整监督与 LP-G 事件审计。但 **R90 runner 当前强制双臂、`gcap-frontier` 与 ENS/LP 预设**，直接把 `P-GRB` 加进 prereg 不能变成真实 P。需写一份只服务此冻结批次的三臂 harness/manifest：P 明确 `--method gurobi --plain-baseline --gurobi-model-export compact.lp`，不得带 ENS 预设、24+1 起点、LP-G flag 或历史 U；ENS 与 LP-G 继续 R90 命令，仅 `--round90-lp-g-split false/true` 有别。P 的 canonical 原 compact fingerprint/LP SHA 要与该输入已审计 ancestry 比较；若 R90 编译导致字节变化，先独立解释且三臂重新资格，不能静默接受旧 P 身份。冻结新 harness 和 manifest 的 SHA 后，零 Optimize 的命令/身份/进程树资格、P 小资格与对应原始模型读回均须通过，再发本批。新增代码只限 harness、三臂审计适配和报告，不动生产算法或输入；若必须修改 production 才能跑真实 P，则旧 R90 二进制不能作为同构建三臂凭证，应先停止并重新冻结三臂新 binary。

## 原问题审计与可证伪判定

每臂从启动到合法原问题证书的完整 wall 为主指标，只有两臂都认证才给认证时间比；P/ENS/LP-G 三条进程各自计费。每个 witness 由原 Evaluator 复核路线、库存、各前缀载量、回仓装卸时间及原目标，记录首次**可用**时间和合法 U。每个 L 要附模型/区间/epoch/cutoff 作用域、子域覆盖和原问题全局性；审计根与叶、父子共享端点、原子替换、终端 MIP 状态，并核同一原问题 `max L≤min U+原有容差`。P 模型为原 compact，需保留 export hash、native status、bound 与原物理 witness；P 不接受候选的 MIP start/cuts/历史 UB。LP-G 分清 proposal、两子 LP、AM、native-target、实际 atomic split 与最终闭合；depth 遥测为 0 时仍查 leaf/decision ledger。Seed/Threads/Presolve/MIPGap/MIPGapAbs 必须检查**实际 native set/get 成功与读回**，不能只凭命令。正常截止是 unknown；失去 flush 的账本不能推断未发生事件。Gurobi 证书只按既定数值容差陈述，非有理证明。原始 journal、模型、日志、失败前缀保留并逐件 hash/size 归档。

先登记离线判断，绝不写入运行时选型：若 F2/B50 的同期双证书收益消失、C20 越过原计划严重信号线、或任一 P 同期已证而 LP-G 明显慢/丢证，应判不值得直接晋升或至少停止扩张并独立审查；单 seed 的一次严重信号只能列风险，不能声称“经确认”。双方 open 时只比较同 cap 的 U/L/gap，gap 比和绝对差同时满足原计划的 `>50%` 与 `>0.01` 才报严重风险，不能作认证速度结论。若正例依然真实、负例未明显扩大、没有身份/证书阻断，结论最多是“值得冻结 H1–H8 与准备论文资格”，尚非晋升。若相互矛盾或主要臂删失，明确“未决”；不跑到结论好看。C2 的既有 seed0/1/2 反向及 D6 6.22% 慢化始终进总比较表，不能被本批覆盖。之后的真正 H1–H8、新 seed、K1 保护及长时证书须独立预注册，且大规模长时先过论文 PDF 门。

## 可核的 Sol 子代理会话身份

本轮会话记录位于 `C:/Users/Administrator/.codex/sessions/2026/09/28/`。由各 rollout JSONL 的 `session_meta.payload.source.subagent.thread_spawn.agent_path` 对应角色，取首个 `turn_context.payload.model` 与 `turn_context.payload.effort` 核验，不以代理自报代替：`r93_math` 文件 `rollout-2026-09-28T12-55-39-01a0e65e-5f9f-7b92-9e7b-975d53f9cc35.jsonl` 为 `gpt-6-sol/xhigh`；`r93_primal` 的 `rollout-2026-09-28T12-55-54-01a0e65e-97dc-71f0-9de8-5ab34106bcbc.jsonl` 为 `gpt-6-sol/high`；本 `r93_evidence` 的 `rollout-2026-09-28T12-56-11-01a0e65e-d9e1-7312-8d1b-215b647da80f.jsonl` 为 `gpt-6-sol/high`。只解析这两个字段和角色路径；不转储 session 全文或全局配置。
