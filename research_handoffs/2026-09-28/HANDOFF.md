# ENS-C 统一优化研究交接（草稿，待最终结果更新）

**截至 2026-09-28 已保存证据的整理，不是最终晋升决定。** 唯一后续工作目录是 `E:/codes/ExactEBRP`。完整协议以 [优化计划](../../research_plans/ensc_optimization_plan_2026-09-26.md)和[19 角色输入清单](../../research_plans/ensc_optimization_instances_2026-09-26.json)为准；本文件只给下一阶段恢复工作的必要结论和边界。当前 `/goal` 仍未完成：完成实验、归档或 PR 均不等于取得用户要求的统一算法与最终证据。

## 目标和可接受的结论

研究目标是一份**统一、可复现、正确的完整算法**，在事先声明的输入范围内，比原始 P-GRB 更稳定、更快取得**原问题、原容差下可核的数值最优证书**，同时不发生经确认的严重旧法回退或明显 P-GRB 最终劣势。P-GRB 是原始 compact 模型对照；冻结 ENS-C 与重要 K1 记录是回退保护，不是运行时任选臂。多结构、多 seed、未适配 H1–H8 和收敛复核尚需真实证据；短时 U/L/gap、根 LP 提升、模型数学有效或单个认证胜例均不能替代完整认证时间。旧 `.85/.90` 认证时间比和“两例大实例≥20%”属于有价值的**期望幅度**，不是机械硬闸；用户允许合理小幅起伏，要求重视严重回退，不愿用不可能的全例认证把研究逼入死胡同。必要证据不足就写“未决/目标未达”，不把删失当赢或无限加时。

所有正式臂需冻结输入文件及 SHA、场景 `T/λ/handling`、算法源/二进制/参数、seed、运行顺序、完整进程截止。对同一原问题审计物理可行 U、作用域正确的全局 L、覆盖、跨臂 `max L≤min U+既有容差`、证书状态和 witness 可用时刻。主要指标是算法启动至合法证书的完整 wall time；建模、24+1 启动、所有内部 LP/MIP、验证与退出都属于该臂。编译、离线审计、诊断、归档和失败前缀另列研究成本；嵌套耗时不重复相加。正常截止只有可审计的 U/L 与 unknown；被截断且未 flush 的账本缺行也不能断言未发生后续动作。Gurobi 结果是既定数值标准下的证书，不能写成严格有理对偶证明。

正式方法禁止按实例名、输入 ID、历史胜负、已知最优、事后规模阈值、机器速度或剩余预算选型；禁止给 LP/MIP/证明组件设 `k` 秒、`k Work`、改名 `credit` 的内部配额后切换、放弃或重试。允许**数学证据**触发合法停止、剪枝、收缩、分裂或重建，但需保留界作用域、子域覆盖和全部成本；全局截止只终止整次独立运行。不得逐例拼“最优算法”、挑 seed、注入旧最优或历史 UB，也不得修改原问题、评价器、benchmark 或容差。任何数学、模型身份、物理见证或数值边界疑点先停并独立复核，不能以参数/实例补丁洗掉。

## 当前完整算法如何产生证书：流程与数学边界

以已验的 [ENS-C 算法底稿](../../results/unified_exact_round91/paper_algorithm_blueprint.md)、[控制器有限性说明](../../results/unified_exact_round92/controller_termination_note.md)、[物理/模型共同包络证明](../../results/unified_exact_round92/handling_activation_physical_envelope_note.md)为准；这里只给改动时不能丢失的不变量。原目标为 `F(Y)=G_true(Y)+λP(Y)`：`r_i=Y_i/D_i`，`S=Σr_i`，`H=Σ_{i<j}|r_i−r_j|`，`S>0` 时 `G_true=H/(nS)`，`S=0` 时约定 `G_true=0`。原物理检查还要求合法车路、库存、载量各前缀、返回仓库的装卸时间与时间限制。叶模型里的 **变量 `G` 是 Gini 的上图量**：对正 `S`，有效透视行给 `G≥G_true`，不是处处等于真实 Gini；真实值在该叶区间时可取等号嵌入，若叶下端 `a>G_true`，同一库存的模型点可能只能取 `G=a`。不得把 parent LP 的 `G` 或其残差当成原物理解、合法 U 或精确分式值；零分母约定也不能直接代入除法行。VD-P 状态/透视、F0 连通、路由、时间/载量、cutoff 与实际 binary64 导出系数共同构成叶模型，不能抽掉其中一部分宣称完整证明。

默认流程先做 **24 个随机解码下降 + 1 个独立构造起点**，每个起点在定义好的有限邻域中反复严格改进，最终同已验最佳解作 R83 等净量交换和物理 closure；得到的只是合法 U。复合邻域实际只保留单路线 **top-8** 与局部组合 **top-6** 候选，耗尽该受限邻域不等于所有离散移动局部最优。完整法以验证过的 U 建立覆盖所有可能改进解之 `G_true` 的根区间，在当前 incumbent epoch 为每片闭区间 `[a,b]` 生成带有效 cutoff `κ=U` 的 canonical 原整数模型并解完整父 LP。叶下界必须对其**实际表示区域**有效；下一个开放叶按界选择。frontier/native-target 可在 lookahead 前以数学下界目标重排，不是时间片。

当控制器准许分裂时，默认取同一可表示中点，两个闭子域为 `[a,p]` 与 `[p,b]`；先核共享端点/覆盖，再分别求**完整双子 LP**。深度 `<8`、宽度 `>10^-4+10^-12` 才可分。对父界 `B`、物理 `U`、子界 `B_L,B_R`，现行 AM 取 `D=max(U−B,ε_cert,10^-12)`、`g_j=clip((B_j−B)/D,0,1)`、`η=min(g_L,g_R)`、`μ=(g_L+g_R)/2`、`S_AM=ημ`。先按已证不可行子域作双侧关闭/单侧收缩；有限子界无严格提升则请求父 terminal；否则只有 `S_AM+ε_score≥0.08` 才立即原子分裂，低于门槛则用 `min(B_L,B_R)` 做父原生 bound target。`0.08` 是归一化调度阈值，**不是**证明容差或秒/Work 份额。已接纳且评分容差明确时，两个孩子的 `U−B_j` 可由 [AM 条件收缩引理](../../results/unified_exact_round90/am_gap_contraction_note.md)给条件性上界；不涵盖不可行收缩、native target 成本，也不保证时间收益。父覆盖在事务成功前持续；target reached 只可重排，不能写作证书；终端 MIP 真正可靠结束、全部叶/根亲子覆盖及物理/界门禁通过才可称原问题数值认证。

LP-G 唯一改动是在**当前完整最优父 LP**、相同 SHA/区间/epoch、有限 `a<G_LP<b` 时取 `p=G_LP`，否则回原中点；同一 `p` 精确构造共享子端点，其余双子 LP、AM、depth/width、目标、终端证明均不变。固定 parent 点的 product 行原始违反量使 `p=G_LP` 最大化两子违反和的较小者；即使该点被两个子松弛排除，别的最优 parent 点仍可能维持旧 bound，故**不保证子界严格提高或整体更快**。子缓存须核子域/模型 SHA/incumbent epoch；旧 epoch 的标量不能复用。`proposal → 两子 LP 完整 → AM → native-target/请求终端 → 原子替换 → 实际证明闭合` 是不同事件，不能合并计数。

有限性也有前提：固定有限实例、真实 incumbent 严格改善只有有限个路线/整数库存状态、同 epoch 缓存与 milestone/terminal-restart 门禁有效，每次已发起 LP/原生调用可靠终止或由全局截止/工程门禁让**整次**运行停下。深度 8 使每 epoch 的叶 ID 有限；target requeue 后同一子界不再构成严格新收益，转父 terminal，不能无限重复同一目标。这不证明单次 Gurobi 运行时上界、多项式复杂度、去掉 depth 8 后的 LP-G 有限性，也不把 cutoff unknown 变认证。[控制器证明](../../results/unified_exact_round92/controller_termination_note.md)只覆盖其明示的默认 C6 路径与假设。`result.external_gini_tree_max_observed_depth` 曾可陈旧显示 `0`；深度用 leaf/decision ledger 核，不以该遥测字段推断无分裂。[深度核查](../../results/unified_exact_round90/depth_telemetry_followup.md)

其他实际统一参数仍需论文陈列：支持时长静态行 `rank≤3`、最多考虑 **50,000** 个子集（可能按枚举/车辆顺序截断静态行，既非全部数学族也非秒/Work 切片）；单根区间、默认分裂因子 2、最小宽 `10^-4`、root cut rounds 0、无动态 cut 家族。配置标签 `domain_propagation_mode=iterative, rounds=2` 不代表 canonical writer 实际执行两轮闭包，不能照标签夸大。R92 新行另有已验但受限定的物理/导出共同系数合同：用两者的下界、定向最短返仓旅行下界及覆盖原 `1e-7` Evaluator 接受行为的 outward horizon，构造 `P_k≤B_k a_k`；不改旧 duration 行或容差，不能把它的正确性扩大为旧 writer 在任意实数输入上完全忠实。详见 [R92 数值证明边界](../../results/unified_exact_round92/handling_activation_physical_envelope_note.md)。

## 已核实的阶段结果与当前候选

| 方向 | 已核实结果 | 当前处理 |
| --- | --- | --- |
| R87/R88 基线 | R87 五对正式运行：D6 ENS-C 3160.907 s 对 P-GRB 22570.062 s 双认证；F2 ENS-C 535.921 s 认证，P-GRB ≥70647.797 s 后配额中断；D7/U6/F5 双删失。R88 P-GRB/ENS-C/A1 八角色三臂早筛均作物理/界审计。 | D6/F2 是强保护依据，不推成五对均赢。R90 相对 R87/R88 P 数据为**历史、非同期**；不能直接相除作新方法 P 加速比。[R87 报告](../../results/unified_exact_round87/final_report.md)、[对照证据图](../../results/unified_exact_round92/benchmark_evidence_blueprint.md)。 |
| A1 启动 | 去掉随机 24 种子的单构造在 D6 零 Optimize 启动诊断把合法最终 UB 从 0.157509804 恶化到 0.171611627；R88 八例完整早筛并无稳定额外收敛收益，U6 最终 gap 由 0.02236 恶化到 0.03097。 | 保留冻结 ENS-C **24+1**；A1 仅作消融，不因省启动秒数宣称完整法加速，也不按实例开关。[决定](../../results/unified_exact_round88/a1_g3_decision.md)。 |
| A2 数量流 | 全线性化与保留凸惩罚的单次固定见证探针在 D6/E8/S12 均未使原目标严格下降；替代 proxy 虽可下降，不能证明分式 Gini 原目标改善。 | 两个受控方案均暂缓，保留正面数学/负面原目标证据，不再靠 seed、步长、半径或重启搜索。[决定](../../results/unified_exact_round88/a2_composite_endpoint_decision.md)。 |
| OT/Gini 库存切割 | B1/B2 有有效性与独立微资格；固定 LP 迭代闭包 F2 数值下界上升，D7 六臂在 300 s whole 诊断截止未闭合；稀疏全族 epigraph 在 F2 给约 0.5327745494，但 D7 四臂仍未完成。R89 native B1 玩具回调接线可用，正式 D3 同构建从 ENS-C 155.391 s 变为 B1 299.828 s，Work/节点亦显著上升。 | 切割的数学价值≠完整法速度；不集成 eager epigraph/迭代服务，不延长 D7 以求标签，R89 native B1 因预注册严重信号停批、保留为 default-off 研究证据。[OT 决定](../../results/unified_exact_round88/ot_epigraph_decision.md)、[B1 决定](../../results/unified_exact_round89/native_b1_decision.md)。 |
| R90 LP-G 分裂 | 只把当前最优 parent LP 的严格内点 G 用作建议分裂点，否则用旧 midpoint；仍做完整双子 LP、AM 阈值 0.08、depth 8、最小宽度 1e−4、terminal MIP 与同一全局截止。十九角色 seed0 G4 快慢混合：F2 585.656→311.578 s、B50 1148.078→762.406 s 同期认证收益；C20 341.219→382.922 s，N12/D4/E7 亦有较小损失；D7/U6/F5/F6 等短时仍 open。C2 seeds0/1/2 候选/ENS 比为 0.906/0.705/1.112，中位0.906但一组反向。 | **最值得继续检验的统一研究候选**，仍 default-off、未晋升。必须完整公开负例与删失；分裂点的定理只保证固定 parent 点的原始 product 行违反性质，不保证 LP bound 或证明速度。[G4 决定](../../results/unified_exact_round90/g4_panel_decision.md)、[C2 报告](../../results/unified_exact_round90/c2_repeat_report.md)。 |
| D6 LP-G 尾部 | 旧 G4 的 LP-G 在 3597.203 s 仍 open（U .1570831311，L .1563522935），ENS-C 3447.219 s 认证。新签署的 7200 s fresh 同构建 pair 两臂均认证：ENS-C 3448.704 s，LP-G 3663.360 s，候选慢 214.656 s、**1.06224×**，未触 1.5×且>30 s 严重线；旧删失仍保留。LP-G 两次同 epoch 点提案、双子 LP 完整、一次 native-target requeue，**没有实际 atomic split**，后请求 terminal parent MIP 并最终认证。 | D6“在7200s内能否闭合”已回答，不能把旧删失当新认证或把请求 exact-close 当证书；单 seed 不证明跨 seed 或对 P 优势。此轮不追加 D6 重跑。[报告](../../results/unified_exact_round90/d6_tail_report.md)、[独立验收](../../results/unified_exact_round90/d6_tail_independent_evidence_review.md)。 |
| R91/R92 handling | R91 实际固定 LP：C2 旅行/activation 连续行提升数值下界，整数 floor 再有约 0.00244；D3 无提升，事件不等式被普通车辆 handling 整数界解释。R92 v1 G1 暴露 raw 物理与 canonical near-unit 系数不一致的反例，已停止其性能准入。v2 用共同 raw/导出下界和 outward 物理 horizon 修复新行；Q003/Q004 **零 Optimize G1** 经独立验收，含失败 fixture 的窄修与旧 row 的边界披露。 | R92 v2 仍是**另一个统一、default-off 的候选**，不是 LP-G 组合或主线。真实完整方法 G3 尚未运行/验收（按当前保存报告）；不因 G1 有效或 C2 根界涨而宣称提速。既有 canonical duration 行对边界物理点仍有限制，v2 不修复整个旧模型；需在论文精确声明。[R91 决定](../../results/unified_exact_round91/handling_real_decision.md)、[R92 v2 G1 决定](../../results/unified_exact_round92/g1_v2_decision.md)。 |

此外，R88/R90 大 raw 已采用无损包与逐 member SHA/size 核验；D6 tail 两包保留 21,516 文件、47,875,550 原始字节、7,813,698 压缩字节，失败 plan 前缀与两份日期转换收据都保留。[D6 归档交接](../../results/unified_exact_round90/d6_tail_archive_handoff.md)。这保证字节可复核，不为候选制造新性能结论。

## 身份、分支和证据入口

- 冻结 ENS-C 源提交 `4496078f25c0cdad1cf7a5c39835fd23121e8978`；R87 同构建二进制 SHA `25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e`。R88 三臂研究二进制 `23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693`。[R87 协议](../../results/unified_exact_round87/protocol.json)、[R88 入口](../../results/unified_exact_round88/admission.md)。
- R90 LP-G 二进制 `build/research/round90-lp-g-split/ExactEBRP.exe` SHA `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`。D6 tail 的 `identity.json` 固定旧 Git ref `a71bd53ca412e9b9e529e7237446687d360a94ce`、165 production blob+另一个 pinned test、七核心源码、输入及 harness；后续 R92 工作树不是该二进制的源码快照。R90 全部 G3/G4 与 D6 tail 结果入口为 `results/unified_exact_round90/`。
- R92 v2 G1 的 provisional 主二进制 `build/research/round92-handling-activation/ExactEBRP.exe` SHA `767d2cbfa50f332a8b9cd6fa3f01888509509b11c2444100d7cafd63bc204b9b`；core SHA `29cb167a388e1a76bd544131bf59684be3950f92f13ecdb755525644f596de12`，Q004 测试修复提交 `a0e35a221c770f71ef19c405edf9af73e43d93d7`。实际构建 `CMAKE_BUILD_TYPE` 为空，不能称 Release。[G1 独立审查](../../results/unified_exact_round92/g1_v2_independent_evidence_review.md)、[G3 源准备](../../results/unified_exact_round92/g3_runner_preparation.md)。
- 已知按轮 stacked draft PR 为 [R87 PR149](https://github.com/yifanXovo/TailoredExact/pull/149)、[R88 PR150](https://github.com/yifanXovo/TailoredExact/pull/150)、[R89 PR151](https://github.com/yifanXovo/TailoredExact/pull/151)、[R90 PR152](https://github.com/yifanXovo/TailoredExact/pull/152)、[R91 PR153](https://github.com/yifanXovo/TailoredExact/pull/153)、[R92 PR154](https://github.com/yifanXovo/TailoredExact/pull/154)。根已确认 D6 归档提交 `3d7b8130a`；其余最终 HEAD/PR 状态待 FINAL_UPDATE 核实。PR 存在或推送不代表默认方法变更，更不代表 `/goal` 完成。

## 恢复顺序与本次预算上界

1. 根代理先填文末 FINAL_UPDATE，检查最新 Git/PR、活动进程、独占计算槽、用户授权、剩余额度、保存的失败前缀和 R92 G3 gate/lease。不得从旧摘要猜当前正在运行的批次；只读现有小收据，不再重扫大 journal。
2. 在 R92 v2 数学/物理/身份边界不变、独立静态审查与零 Optimize prepare 成立后，最多做**已预注册的 R92 有限完整方法筛选**：先 E8/S12 四臂 smoke，经完整物理、row/LP 身份、覆盖、跨臂与风险审计，再决定其余六角色；同构建 ENS-C 对照和单一 whole-run 截止。若未暴露新行或发现有效性疑点，分别记 nonexposure/阻断，不擅自调参重跑。
3. **本次恢复预算**只允许 R92 筛选及**一轮真正必要的预声明验证**（例如被结果触发的成对波动复核），不是 R92 后无限新变体/长跑。**在剩余额度接近 20% 前停止新增实验**，优先留给独立审查、无损归档、最终比较表和下一次交接。若额度读数不可用，按保守停止而不是假设余额充足。后续只有用户另行授权才能改变本次上界；本文件不能充当永久自动续跑许可。已完成的必要批次仍须正确记账和保存；不能为凑 110 次继续跑。
4. 先比较 LP-G 与独立 R92 的正负证据、最差退化和 P 历史边界，决定“保留哪个**统一候选**继续验证”或“暂时均不晋升”。禁止按角色拼二者或添加 A1/B1 的逐例开关。若候选达到有根据的晋升资格，在启动广泛长时收敛与任何稳定主线默认变更前，必须先交付完整论文式 **LaTeX 源文件和实际编译、逐页检查的 PDF**：问题、算法/参数、终止与证书证明、数学/数值作用域、正负/删失实例、P/ENS/K1 比较、全部成本和有限晋升范围。此草稿交接阶段不需为了形式强造 PDF。然后冻结新数据/seed/长时协议，再做必要的完整收敛复核。未达到资格则交付诚实的失败/未决结论和可复现材料；**不得把 `/goal` 标为 complete，用户要求暂停时可以标 paused**。

## FINAL_UPDATE（根代理在最终交接前填写；当前未知不得臆造）

- [ ] R92 v2 G3：静态审查、零 Optimize prepare、smoke/rest 是否获 lease；实际每臂 U/L/证书/时间、row 暴露、失败/未运行、独立验收和最终决定：**待填**。
- [ ] 本次唯一必要验证（若被触发）：预声明假设、角色/seed、完整截止、正负与删失、是否执行；若未执行明确写未运行：**待填**。
- [ ] D6 归档及本 handoff 的最终 commit、R92 PR URL/状态、当前 HEAD/分支与冻结源码/二进制身份是否变化：**待填**。
- [ ] `/goal` 当前状态、账户额度实际剩余百分比与 20% 停止点、当前计算槽/进程、尚未启动的任务清单：**待填**。
- [ ] LaTeX/PDF 是否已编译和逐页核查，最终 P-GRB 同期比较、新 H1–H8、长时认证范围是否已冻结并执行；若否保持未完成：**待填**。
