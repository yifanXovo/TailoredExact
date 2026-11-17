/goal

# Round170：冻结目标重加权候选，确认付费收益并补齐同预算 P-GRB 比较

## 0. 目标、研究问题与有限容量

继承已完成的 Round169 / PR231。本轮不开发第二个机制，**冻结 C169 的实现、倍率、H seeds 和完整 H，检验它在另外两个 Native Seeds 上相对 B 的付费结果，并在一个 Native Seed 上保留 M 对照、加入真正同预算的冷启动 P-GRB。**同时将已有 R169 结果和新确认结果整合进当前论文，形成明确的候选去留判断。

R169 已给出足够强的继续依据：三个 n35 角色的最终原目标 U 相对 B 降低约 18.8%、14.5%、10.0%，也都优于匹配的 M；但全部 n35 仍 OPEN，C35/X35 的 qualified L 下降，C20 证时从约 211.5s 增至 219.5s，而且没有新 P。现在最需要回答的是这些付费收益能否在另外的求解轨迹下保留、是否具有实际 benchmark 价值，而不是继续调倍率或增加邻域。

本轮固定回答三个问题：

1. **重复性与代价：**在四个已知角色、Native Seeds 1/2 上，C 对 B 的 U、L、gap、证书及证时表现如何？C20 的已知证时回退是否仍存在？
2. **机制对照：**三个 n35 在 Seed1 上，C 是否仍优于同样增加两个完整 H 的 M？不能仅因 R169 的 M 初始解没有变化就删掉这个对照。
3. **benchmark 价值：**三个 n35 在 Seed1 上，B/C 与本轮真实冷启动 P 的同预算结果如何？分别说明新 B/P 配对与候选 C/P 比较，不混淆当前主线和研究候选。

**B/GI-TBC 默认保持不变；C166、D167、C169 均默认关闭。**本轮结束要做出有信息的科学判断，可以确认一个有范围的论文候选，也可以关闭其继续优化；不要求正结果，不要求所有指标同时获胜，不自动开始下一轮。Seeds1/2 和这些输入均在旧 B/P 研究中暴露过，不能称为未见 seeds、留出验证集或新物理实例。改变 Native Seed 也不增加 H 随机性样本。

### 0.1 容量和 C++ 约定

总科学工作容量 **6h = 21,600s**，目标约 5–6h，完成即停止。包含定向阅读、必要资格、实际计算、分析、有限改稿、构建和独立复核。普通 Git/公开恢复传输 I/O 单列。入口核对争取 20–30min，完整面板之后预留约 90min 给分析、复核和交付；不以等待或额外实验填满容量。

| 部分 | 固定安排 |
|---|---|
| 核心 B/C 确认 | C20、C35、B35、X35 × Native Seeds 1/2 × B/C，共 16 次 |
| M 机制对照 | 三个 n35 × Seed1 × M，共 3 次 |
| 冷启动 P-GRB | 三个 n35 × Seed1 × P，共 3 次 |
| 每次原 process cap | 全部 600s；数学路线时限 T 保持原输入值 |
| 计算名义上限 | 22 × 600 = 13,200s = 3h40min；H、建模和所有 LP/MIP 已包含在各次共同 cap 内 |
| 额外资格 | 主要复用已有证据、结合首个实际位置读回；确有接口需要时，额外资格外层最多 120s，不新开优化面板 |
| 本轮不安排 | 新 H-only screen、额外倍率/H seeds、PS/E+、其他输入、第三 Native Seed、1200/2400s 长预算 |

13,200s 是运行 cap 的名义总和，不是整个任务墙钟承诺。证书合格就正常提前结束。所有研究结果保留完整费用，不把事后独立审计时间塞进算法证时，也不把它从总研究费用中消失。

**完整 H、原目标回评、物理验证、Start 映射、实际建模与 Optimize 继续全部由 C++ 执行。**Python/Node 只做编排、只读独立复算、日志、CSV 和文稿，不代建/代求模型，不在 C++ 外壳内调用 Python 优化核心。本轮优先直接复用 R169 实测 PE，不为轮次名称、报告字段或纯 reader 修正重编译。

统一倍率、有限 H 调用数和选解规则不读取实例名、城市、历史胜负、已知 P 目标或硬件性能。实验选择与 600s 预算是研究设计，不进入算法在线分派。

## A. 本地入口、固定身份与 Draft PR

遵守仓库 `AGENTS.md`、`WORKSPACE_POLICY` 和已有工作区约定。新工作、临时件、缓存与交付均在 `E:\codes\ExactEBRP-work` 内。保护原 `E:\codes\ExactEBRP`、历史证据和用户活动 worktree。`worktrees\paper-current` 曾有未提交修改，只读核对，不 reset、stash 或覆盖。

建议工作树 `E:\codes\ExactEBRP-work\worktrees\round170`，分支 `codex/round170-reweight-confirmation`。已有同轮成果按实际 manifest 接续，不重复运行已合格位置。

| 身份 | 编写本任务时的实值 |
|---|---|
| 仓库 | `yifanXovo/TailoredExact` |
| 前序 | [PR231 / Round169](https://github.com/yifanXovo/TailoredExact/pull/231)，Open Draft |
| R169 delivery head / branch | `ff77c4e18985a55370d58a2b2731a51566a07eb8` / `codex/round169-primal-reweight` |
| R169 measured source commit | `781c548b410a2749190e3f0c4b149c2ad885c054` |
| R169 qualified data commit | `c9fcb1f1ee8a2ea07004ad6162831f4bcf01443a` |
| R169 science/manuscript commit | `b86cef9917a9fd526ca89bcbdad4b667008c7eab` |
| R168 delivery | `2301f9bf0a61d5fe74ee728704a820cb437d5cde` |
| main | `b2b940c1e517a72e226ec60fc49ff19651737632` |
| 实测 PE | `E:\codes\ExactEBRP-work\build-cache\round169\ExactEBRP.exe`，9,884,148 bytes |
| PE SHA256 | `c6ddf0b62f1200d02a8c654fd3f278ced704130f1a8950fc1e6464b9cbb11e57` |
| Gurobi 13.0.2 DLL SHA256 | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |

入口做一次有限远端/本地核对，吸收合法的新交付，以实际状态为准。若 main 已包含完整 R169 依赖，从 main 建分支；否则基于 R169 delivery，Draft PR base 为 R169 branch，无需等待其合并。本轮目录为 `results/unified_exact_round170/`，当前论文继续维护 `results/unified_exact_round137/`。

核实旧实测 PE、DLL、编译来源和现有文件完整性即可，不能只抄 `method_freeze.json`。四臂使用同一个合格 PE、同一 DLL/环境。若原 PE 本地缺失，可从同一已冻结完整源码、同一编译器/Release 参数重建，记录真实新 PE 身份并让本轮所有臂共同使用；不得假称新二进制等于旧 SHA。若有确实影响求解或证据有效性的源码错误，先修复、记录差异，只重做受影响资格与位置，失败成本保留；纯报告字段不属于这种理由。

## B. 必须继承的结论与有限排重

### B1. R169 已完成，直接继承，不重新做筛选

定向读取 R169 的 `goal.md`、`final_report.md`、`method_note.md`、`engineering_notes.md`、`research_decision.md`、`h_results`、`complete_arms`、`cost_report`、实际 C++ 与当前论文相应部分。独立复核已确认：

- 7 项共 35 条完整 H 全部完成；正式六角色中 4 项跨过预注册门槛，第七动机角色也改善但不能触发正式面板。H-only 外层约 25.044s、零 Optimize。
- 全部 18 个 B/M/C 位置完成，完整阶段另付 42 条 H；93 次实际 Optimize = 66 LP + 27 MIP，9 CERT + 9 OPEN。process 总时长约 6371.947s，科学收束约 9621.979s。
- C35/B35/X35 的 C 终态 U 分别约 0.120201245、0.187861163、0.466514935。C35/X35 的 qualified L 比 B/M 低，B35 略高。C20 三臂同一最优值，但 C 约 219.512s，B 约 211.482s、M 约 211.052s。
- M 在全部七项 H-only 中选到与 B 相同的原目标初始解。不过完整 X35 的 M 比 B 更好：0.511546413 对 0.518363903。原始日志显示同 Start、同模型及相同搜索前缀，M 终端走到 948 nodes、B 940 nodes，M 在后续节点得到额外 incumbents。这是有限搜索进度/截止差异，不能说成 M 的 H 重启改好了初始解，也不能据此删去 M 对照。
- 当前主线不变，没有新 P。R169 新增六条真实 B 控制运行，不增加物理实例数或 P 优势数。

`selection.json` 的 `necessary_H_complete` 是五路径诊断字段，普通三路径 M/C 会显示 false。完整阶段正确资格应由所需路径数、每路径完成/验证标志和 `complete_arm_initialization` 判断；已验证的 full rows 均合格。将这个区别写进 reader/schema 说明，不为这个已知元数据语义问题重编译、重跑或误判未完成。

### B2. 只读查清本轮真正需要的先例

形成短 `research_design.md`，按已有结论排除重复工作：

| 历史来源 | 对本轮的直接含义 |
|---|---|
| R73–83、R88 | 完整 H 已包含 joint construction、24 随机顺序、第 25 个 constructive order、跨车 decoded descent 和 R83 物理闭包；不删减、不另造廉价 H |
| R96/R97 | 更好的初始化并不保证付费完整算法更快；本轮检验终态与证时 |
| R105–107、R159/160 | 已有 assignment/oracle/conflict 和联合物理邻域尝试，不重开普通 owner/no-good 或放大 block |
| R163/R164 | 同六输入和 Native Seeds1/2 已暴露；沿用严格 C++ B/P 参数、原模型资格和读回方式，不把旧大 cap 数据伪作本轮对照 |
| R165–168 | 条件数量/顺序/owner 家族研究与证据已完成；不重跑 eligible、不把旧父 fleet 的证书套到新 H |
| R169 | 本轮是固定候选的确认，不是把已有多权重 H 改名再做一次新机制 |

R169 已补全 R137 跨权重旧终态好解来源；不再次恢复旧大包追 first-hit，不把旧 fleet 作为新 Start。Paquete–Stützle 等目标聚合/局部搜索原文先例和当前参考文献已经建立，不重新做文献普查，不声称权重扰动本身是新的 OR 原理。

R164/当前论文中 C20 的 B 在 Native Seeds1/2 证时约为 354.388/341.810s（旧 1200s cap）。所以本轮 C20 同样用 600s，避免沿用 300s 后主要得到两边 OPEN。此处只解释预算的事前选择；新 600s 运行仍有自己的轨迹，不能把旧大 cap 证时当本轮结果。

## C. 固定四臂与正确性边界

设原目标 `F_lambda(x)=G(x)+lambda*P(x)`。令 `H_a(s)` 为 R169 实现的完整 H 在搜索权重 a、H seed s 下返回的真实终态 fleet。固定 `s0=20260626`、`s1=20260627`、`s2=20260628`。

| 臂 | 本次自己生产的初始化 | 后续求解 |
|---|---|---|
| B | `H_lambda(s0)` | 未改变的 GI-TBC/B |
| M | `H_lambda(s0), H_lambda(s1), H_lambda(s2)`，按原 F 选最好 | 同一 B 精确层 |
| C | `H_lambda(s0), H_(lambda/2)(s1), H_(2*lambda)(s2)`，按原 F 选最好 | 同一 B 精确层 |
| P | 无用户 H、无外来 Start，沿用合格的 Plain Gurobi 紧凑模型 | 原 P-GRB 冷启动；保留求解器自身默认启发式 |

B 的 `--round169-primal-mode off`，M 为 `multistart`，C 为 `reweight`；不启用 H-only panel。B/M/C 保留 B 的真实 preset `research-round83-vds-equal-net-exchange`，不换成不能触发完整 H 分支的新名字；P 使用 E1 的 custom 入口。H seeds 在 preset 生效后按 R169 方式实际设置/读回；Native Seed 仅改变 Gurobi 搜索，不重写 H seeds。

每条 H 独立从原输入开始，额外调用顺序固定 s1、s2，不输入其他路径、其他臂、R169 或档案的 fleet。每条候选用原 C++ physical verifier 重新计算原 G/P/F，确定性严格改善/平局优先 base 的规则照旧。lambda=0、全部惩罚权重为零、原目标合格零解等既有退化规则继承，不扩展成实例识别开关。无原目标二次 polishing、跨运行候选池或额外 callback 反馈。

原 lambda、global Greedy/scaling、物理输入和精确层均恢复/保持原义。只传递原目标合格的 UB/Start，不传异目标 lower、cutoff、压缩域、树或证书。B 的 proof/coverage、AM、service/target/link、数值资格及默认参数不改变。

“B fleet 在池中，因此完整初始化后的 U 不劣”仍成立；它不保证相同总预算的终态 U、L、gap、证时不劣。本轮不重复证明这些基础性质，只引用已核对的实际实现，并核验新运行没有违反它们。

## D. 唯一输入面板与运行顺序

### D1. 四个已经暴露的原问题

输入仍在 `results/unified_exact_round163/inputs/<ID>/first/instance.txt`。实际物理参数由 R163 `input_manifest.json`、输入文件和真实 argv 联合定义。

| 原问题 | input SHA256 | 数学 T | 原 lambda | 车辆 Q |
|---|---|---:|---:|---|
| R163-C20-S | `cdf6943983c8f2bbd932cb7a3bf3e6645d828b9f651806c4514b6d9a13b865ca` | 5400 | 0.10787606377934943 | [30,30] |
| R163-C35-U | `fb9d881dba6d0d07c59c48a683d2b2543f3effeae593306e28d79875cdcc20d7` | 10800 | 0.11068496171019777 | [20,25,30] |
| R163-B35-S | `8f644c76508a54443e280fe03833f15131989d55184bdfca21b56223f69c17b1` | 7200 | 0.10810343336504369 | [20,25,30] |
| R163-X35-S | `5804470a50da77c2da43ca5654b85e22f0e82459ef556d4d4d75e52e3a87daa9` | 10800 | 0.092888243831640058 | [20,25,30] |

pickup/drop 均为 60/60s，其余库存、target、capacity、站点权重、距离和车辆规则完全继承。保存 17 位十进制和实际 binary64 lambda/倍率，不依赖显示舍入。C20 是证时保护角色，三个 n35 覆盖 R169 全部困难角色正信号；选择已知结果角色的性质必须公开。

本轮不再跑 B20/X20：R169 的 M/C 均保留 base H，完整求解同一最优值，关键搜索工作也相同，当前新增一个 seed 的信息价值低。第七个 R137 动机角色不进入此确认。这个有限选择不支持“全部六角色或新实例均稳健”的结论。

### D2. 预先冻结全部 22 个位置

Threads=1、MIP Threads=1。按下表逐块、块内从左到右串行执行，运行前写入 `matrix_frozen.json`，不得看结果后交换顺序或删增位置。

| 块 | 角色 | Native Seed | 臂顺序 | 次数 |
|---:|---|---:|---|---:|
| 1 | C20 | 1 | B, C | 2 |
| 2 | C35 | 1 | M, P, C, B | 4 |
| 3 | B35 | 1 | C, B, P, M | 4 |
| 4 | X35 | 1 | P, M, B, C | 4 |
| 5 | C20 | 2 | C, B | 2 |
| 6 | C35 | 2 | B, C | 2 |
| 7 | B35 | 2 | C, B | 2 |
| 8 | X35 | 2 | B, C | 2 |
| 合计 | 四个角色 | 1、2 | B=8，C=8，M=3，P=3 | 22 |

统一 `--process-wall-time-limit 600`、`--process-shutdown-margin 6`、`--time-limit 594`，沿 R169 已工作的剩余预算和外层监督规则生成每次实际 Native TimeLimit；不是为每个子 MIP 重发 594s。所有 H、回评、Start、建模、LP/MIP、运行内最终检查共享同一进程时钟和截止。外层监督安全边界沿现有实现读回，禁止在完成 H 后重置总 clock。

预注册的 22 次全部执行，无新的 H-only 筛选门槛，也不因某个位置输了而省掉对照。只因真实运行/有效性错误修复受影响位置，记录失败与重试成本；不为了求更好结果重跑同一位置。串行运行，避免同机同时运行多个 Native 争抢资源。

## E. 实际执行、有限资格与证据

### E1. 复用实测实现和真实参数

从 R169 的实际完整 B/M/C argv、`candidate_manifest.json`、`source_tree_readback.json`、有效参数和独立审计入口继承。仅改变本轮输出路径、D2 的 Native Seed/cap 和声明的臂。逐次读回每个真正 Optimize 调用的 Seed、Threads、Presolve、MIPFocus、Cuts、MIPGap/MIPGapAbs 等，不能只验证请求 argv。

新 P 从 R163/R164 已合格的干净 `P_template` 生成，不从 B argv 改名或减删。在共同 R169 PE 上调用：`--method gurobi`、`--plain-baseline`、`--round127-mode p`、`--algorithm-preset custom`，原 P 的 MIPFocus=0、Cuts=-1、Presolve=-1、MIPGap=0、MIPGapAbs=0 和相同物理模型约定继承。`NumStart_before_optimize=0` 实际读回，`gurobi_hga_start=false`，无 Round112 ENS/P-S；P 不运行自定义 H、C169、AM 或任何外来 warm start，Gurobi 原有内部启发式保持默认。`--round24-executable-sha256` 等身份字段必须填本轮实际共同 PE，不能照搬旧 R163 PE SHA。

相应薄编排/argv 审计允许 P 显式使用 custom；旧 R164 脚本有“P 不带 `--algorithm-preset`”的语法断言（当时依赖默认 custom），不能原样沿用这条断言来拒绝等价的显式设置。验证 P 的实际生效值为 custom，而不是通过移除审计规避检查。

各研究开关按 R169 的实际 parser 关闭，包括 C166/D167；已知正确 flag 是 `--round166-breakpoint`，不要再次使用不存在的 `--round166-joint-breakpoint`。不把 B 的额外 cuts/搜索机制塞入 P 以制造所谓公平。P 与 B/C 使用各自公开冻结的方法定义、同一物理目标、同一输入、环境、Native Seed 和总预算。

模型物理签名和原目标语义相同不意味着 B 内部每个子模型与 P 的 LP 字节相同。对 P 采用已有 compact reference 的模型资格；对 B/M/C 采用已有 frontier/proof/coverage 读回。避免用错误的“所有模型 hash 必须相同”约束阻断合法实验。

### E2. 首次运行即可完成的必要资格

优先复用 R169 已验证的完整 H、RAII、随机流、物理回评和零解 fixtures，不再跑 35 路 H-only。只核查本轮新增风险：新 Native Seeds 是否实际传到所有 Optimize，P 是否真的 cold、共同 PE/输入/时钟是否正确，以及 reader 是否正确区分 full-arm 与 panel 完整性。

在每个完整 B/M/C 运行中重新生产、支付自己的 H。预期 B 共 8 次完整 H，C 共 24 次、M 共 9 次，合计最多 41 次；若既有合法退化/截止发生，按真实执行说明，不能填满预期数。不得读 R169 的保存 H/Start，也不得把 Seed1 的 H 文件免费喂给 Seed2。

保存每条 H 的有效 seed、search/evaluation lambda、完整性、原物理 fleet/G/P/F、random-order identity、选择来源和时间。比较相同原输入下新的 H 与 R169，理论上固定配方应稳定；若不一致，查清有效参数、RNG、物理输入或 deadline 的真实原因，不靠重复调用挑回旧结果。来自完整调用的这些记录已经足够验证初始化，无需额外重复。

### E3. 费用、证书与最小证据

沿现有 journal 保存每次 LP/MIP 的实际模型、Start、调用参数、Native Runtime/Work/nodes、commit/return 和 qualified bound 来源。原物理解要能独立回算库存、prefix loads、压缩旅行、载货返回卸货和原目标。完整方法的 L 必须对应其原问题的合格 coverage/证据，不能拿某个子 MIP 的 raw bound 冒充 global L。

一次独立只读审计逐条核对新行，不重优化。报告每次的：初始原 U，终态 true U，qualified L，绝对/相对 gap，CERT/OPEN/真实异常状态，证时或删失状态，外层 process 秒、H/建模/LP/MIP/运行内检查费用，Native Work/nodes，以及独立事后审计费用。41 是预期 H 调用数，不是 Optimize 次数；实际 Optimize 总数单独逐条统计。

认证时间统一采用既有权威表的 **`T_cert_process`**，即已合格认证运行的进程外墙钟端点。独立审计确认资格，审计耗时另列 `audit_seconds`、`T_total_with_independent_audit`，不与算法证时混用。OPEN 的 600s 预算或实际退出时间不是证时，也不是“600s 已收敛”。输出缓冲导致 first-hit 无法精确定位时明确缺失，不从 rounded Native 时间猜一个精确全局发现时刻。

可以从已有日志零 solver 地画或列少量轨迹/证据进度，但本轮主要比较冻结端点。不要新增计时回调或重编译来获取非必要轨迹，更不要把 600s 端点推称 1200/2400s 持久性。

## F. 分析、解释和本轮收束决定

### F1. 三个预先分开的比较问题

1. **核心 C/B：**四角色 × 两 Seeds，逐对比较。三个 n35 的主要数值是原目标 U 和绝对 gap `U-L`，同时展示 L、相对 gap 与状态；C20 主要看是否同一目标合格认证及证时，同时保留全部 endpoint。
2. **机制 C/M：**仅三个 n35、Seed1。分别列初始化 `F_B-F_M`、`F_M-F_C` 和完整终态 C/M 的 U/L/gap/费用。若 M 再次在相同初始 Start 下终态改善，可查已有日志解释进度差别；不能把额外 H 数相等称为实际计算工作完全相等。
3. **benchmark：**仅三个 n35、Seed1，分别做 B/P 和 C/P。B/P 才进入当前主线权威对比；C/P 是另列候选结果。P 的某指标胜过 C 时保留，不用 B、C、M、P 之间取最小 U/最大 L 拼一个不存在的方法。

在 `matrix_frozen.json` 中预先固定描述“材料性变化”的统一尺度 `delta=max(1e-6,0.001*max(abs(U_reference),1e-12))`，不根据结果更改；reference 分别为 B/M/P 的合格 U，原始差值与百分比同时保留。delta 只帮助区分很小的数值变化，不改变解/证书资格、在线选择或实验执行，不称统计显著性。没有合格 reference U 时不强行计算比例。

不把 U 改善、L 变差压成单个“赢”，不要求全部 L 不下降才承认 primal 价值。证时比只在两边合格认证时计算；单侧 CERT 与双侧 OPEN 分开报告，不给未收敛项虚构速度比。跨物理输入不汇总原始目标值；如给跨角色摘要，使用逐对归一化变化及范围，并保留逐输入/seed 表。

### F2. 结论范围不能扩张

R169 Seed0 可以作为单独历史行帮助解释，但新确认结论以本轮新配对为准。尤其 C20 原 Seed0 cap=300，本轮=600，不合并成同预算三 seed 均值。三个 n35 的旧 Seed0 同为600也保留运行轮次身份，不用历史结果替代缺少的新 M/P Seed2。

本轮 C/B 有两个新 Native Seeds，C/M 和 C/P 只有 Seed1。四个角色已暴露，且按既有正/负信号选取；不宣称全六角色、总体统计稳健、新输入泛化或长预算优势。对重复 seed 仅作有限求解轨迹确认，不伪造置信区间、显著性检验或独立样本数。

### F3. 给出一次明确且有内容的决定

结果形成后，用一个短 `research_decision.md` 说明：

- 收益是否在两个新 Native Seeds 中保留，覆盖哪些角色，代价和反例是什么；
- 在实际比较过的 Seed1 上，M 能否解释 C 的完整收益；
- 同预算 P 面前，C 增加了哪些有价值的 U/证书/gap 表现，或者仍没有实践优势；
- 据此将固定 C169 作为“已在这些角色确认的论文研究候选”、仅保留为初始化现象/局部结果，或关闭其继续优化。不要用模糊的“继续多跑一些”代替决定。

不设置要求全部指标占优的苛刻晋升门槛，也不因一两处正例自动升为默认。B 默认本轮仍保留。若结果有实质价值，明确当前可写入论文的贡献和仍缺的外部有效性证据；若结果不支持继续，交付负面/混合结果并收束，不再追加倍率、H seed、第三 Native Seed 或长 cap 挽救。下一步只提出一个有依据的建议，不自动启动，也不把进一步确认当成永无止境的默认流程。

## G. 论文、CSV 和必要成果

### G1. EJOR/TRE 与 OR 的真实增量

维护同一套 `results/unified_exact_round137/` 权威源。R169 的结果段和 Table 11 目前位于 Conclusions 尾部：本轮将其与新结果定点整合到既有计算实验节（如 §4.3/4.4 的合适位置），结论只保留对应研究判断，不继续按轮次在结论堆表。正文用至多一个紧凑结果表（必要时两个 panel），完整分输入/seed/费用/负面结果放补充；不删除旧 B/P 主要表、adverse controls 或旧证据边界。

方法描述冻结 C169；新表清楚区分 B、M、C、P，标注 cap、Native Seeds、原目标、default-off、已暴露角色和 M/P 缺失的 cells。不要将内部流程用语如“下一轮有限确认”直接当作论文贡献陈述。若本轮为阴性或混合结果，也如实写进相应边界段，不强行新增章节或漂亮胜率。

EJOR/TRE 主线可以因此加强完整方法的计算贡献与可解释的 primal/proof 取舍。OR 所需的一般结构或可推广机制仍须单独成立：现成 scalarization/multistart 思想、正确的 fleet 回收、三组短预算好结果不自动构成新的 OR 理论。本轮不为期刊目标附加未经成熟推导的新算法，不重复贡献矩阵或全文重写；作者 memo 仅更新本轮实际改变的判断。

复用已工作的组装器，通过 R170 薄入口/参数化处理 OUT、临时目录和当前轮次，避免运行硬编码旧轮脚本。生成同源 `manuscript.md`、当前主文和补充 PDF，定点检查修改段、表、交叉引用和相邻页。更新确实过期的 README/current_mainline/paper 导航，保留既有生产 source/PE 的历史身份。

### G2. 118 条权威 CSV 是明确入口

本任务配套 `TailoredExact_Round170_Package.zip` 内含权威 `GI_TBC_vs_P_GRB_All_Tested_Instances.csv`，**118 条数据记录、28 列、UTF-8 BOM、70,240 bytes**，SHA256：

`5e3303adfba0092c465b8dab3232e1ced7d0e85d8d21aa3e8398ed0d3e5880e3`

请将配套 ZIP 一并放到本地并解压；入口优先读取本次解压目录的 CSV，核对后将工作副本放到 `E:\codes\ExactEBRP-work\data\GI_TBC_vs_P_GRB_All_Tested_Instances.csv`。不同内容的已有文件先保留再核对，保护 Desktop 旧91条、仓库历史103条和此前112条版本。

118 条由此前112条加 R169 六条 B-only 记录构成，旧112条连同表头逐字节保持。R169 原增量的三个 CERT 时间已统一成 `T_cert_process`（211.4824220999144、2.8507301001809537、124.53611769992858s）；其独立事后审计时间保留在来源/核对映射中。表头最后两列沿权威表为“实验数据来源”“实例元数据来源”，metadata 指向固定 R163 input manifest；原 raw 增量及逐项规范化映射随包提供，不改写历史 GitHub 原文件。

入口只做一次有限来源查找。确实未收到本包时，在 final 明确缺失并交付可合并增量，不凭118计数造旧行，也不拿旧103条冒充权威完整表；但应先认真检查本次附件/解压路径，避免再次遗漏已经提供的文件。

本轮按实际合格记录追加：

- 8 条新 B（四角色 × Seeds1/2）是最多8条新记录；全部合格且不重复时，118→126。
- 三个 n35 Seed1 的 B 行填入本轮同输入/参数/Seed/cap/环境的 P，对应 **最多3个新严格 B/P 配对**。P 不再单独另开一行。
- C20 Seed1/2 与三个 n35 Seed2 共5条没有新 P，沿 `P_GRB_状态=无配对结果`、`对比结果=N/A`、说明 `N/A-P`。不借旧大 cap P 凑配对。
- 8 条 C 与3条 M 留在独立 `complete_arms`/candidate 对比文件；C/P 表另存，不能覆盖主表 GI_TBC 列、冒充默认算法或增加 B/P 胜数。
- 保留旧28列及全部旧行；run ID、Round、Native Seed、cap、原输入/物理签名、source/PE 和固定来源链接可追溯。认证时间沿 E3 同一口径，OPEN gap 单位保持原表百分数惯例。

118/126 都是运行记录数，不是独立物理输入数。最终报告实际新增 B 行、有效 P 配对、新物理输入（本设计为0）、逐指标结果和真正新增优势证据；有3个新配对也不代表3个新胜例。失败、证据不完整或重复记录不填成预期结果，逐项 reconciliation。

### G3. 合并记录，保持交付最小且完整

`results/unified_exact_round170/` 至少可定位：

- `goal.md`、短 `research_design.md`、冻结参数/矩阵、共同 source/PE/DLL/实际 argv/环境；
- 薄编排与只读审计实现；22个位置真实状态、H/Start/模型/Optimize journal/原物理解与有效性读回；
- `complete_arms.json/.csv`、逐对 C/B、C/M、B/P、C/P 比较及分阶段完整费用；
- `research_decision.md`、`final_report.md`、短作者 memo、实际稿件/PDF；
- CSV 原始输入 hash、增量/更新后权威文件、逐行 reconciliation/时钟口径；
- 三项实际独立评审与修正记录；单个本轮新增 raw 包、精确 member map 和公开交付 receipt。

不新增全历史台账、重复读回体系或独立资格工程。只有本轮新增 raw 重新打包，历史证据用固定 commit/archive/member/hash 引用，不搬运旧大包全集。

## H. 实际成果的独立复核、Draft 交付与停止

实际文件形成后，进行三个独立审阅并修复具体问题：

1. **数学/目标语义：**原目标 fleet、Start 与 qualified global L；C169 正确性继承和终态无支配保证；P 原问题定义正确；无跨臂拼接证书。
2. **执行/数据/费用：**22位置、真实 Native Seeds、相同 PE/环境、P cold、每次自付 H、共同截止、完整 Optimize/费用；CSV118基础、最多8新增/3配对、CERT时间和OPEN单位准确。
3. **研究/论文：**三种比较问题分开；M/P仅Seed1、四个暴露角色和600s范围真实；负面 L/C20证时保留；原文先例、期刊贡献与去留判断不夸大；表移入实验节并实际查看新PDF。

评审读取实际文件，不以预检代替完成后审阅。修正后只读回影响范围，不因文书更新重跑求解。独立代理不可用时如实说明替代核验，不虚构 reviewer。评审属于任务完成，无需再向用户申请一次许可。

正常 commit/push，创建英文 **Open Draft PR**，建议标题：

`Round170: confirm fixed reweighted initialization with matched cold Gurobi controls`

PR 首段说清单Seed正信号需要确认的实际问题，随后交代固定方法、22次面板、付费终态/证时/新P结果和决定。按 A 选择 main 或 R169 stacked base，读回 head/base/Open/Draft 以及当前文稿链接。不自动 merge、force-push、删除历史分支或联系作者/期刊。

对本轮新源、文稿和必要证据做一次公开取回/字节验证。科学提交与 receipt 提交分开，不填尚不存在的 self-SHA。不发布商业 DLL、许可证、凭证或私有稿；工作区清理按政策，零删除也可完成交付。

验收是：固定 C169 在两个另外的 Native Seeds 上的真实 C/B 付费确认；一个Seed上有用的 M 和新 cold-P；预算/原目标/证据完整；明确去留与有限论文整合；CSV按实际追加；独立复核后 Draft 交付。**不要求候选获胜、不耗满时间、不默认推广，也不自动开始 Round171。**

## I. 固定查阅入口

- [R169 / PR231](https://github.com/yifanXovo/TailoredExact/pull/231)，delivery `ff77c4e18985a55370d58a2b2731a51566a07eb8`：`results/unified_exact_round169/` 的 goal/final/method/engineering/research decision、H和完整结果、参数/源码/费用/复核及raw/member map；实际 `src/Round169Primal.inc`、`src/main.cpp`、`src/HgaTgbcRunner.cpp` 和相关 H headers。
- [R164 / PR226](https://github.com/yifanXovo/TailoredExact/pull/226)，delivery `de01e8fb27a954d031abac5fe99442d6c8d29d44`：`scripts/round164_campaign.py`、B/P 模板、实际每个 Optimize 参数/冷启动证据、C20 Seed1/2 旧证时；不作为本轮免费控制结果。
- [R163 / PR225](https://github.com/yifanXovo/TailoredExact/pull/225)，delivery `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`：固定 inputs、`input_manifest.json`、原模型资格和物理语义。
- [R168 / PR230](https://github.com/yifanXovo/TailoredExact/pull/230)，delivery `2301f9bf0a61d5fe74ee728704a820cb437d5cde`，及 [R166 / PR228](https://github.com/yifanXovo/TailoredExact/pull/228)：只读继承与当前问题直接相关的研究边界，不重跑已经结束的路线家族/离线来源研究。
- 当前稿件 `results/unified_exact_round137/{paper_body.md,model_and_algorithm_appendices.md,supplement.md,references.bib,manuscript.md}` 与对应 PDF；R169的 Table11/S169 和既有 scalarization 原文引用。
- 本任务 ZIP 的118条权威CSV、R169规范化映射、独立R169复核与本prompt完成后复核记录。

最终回复先给本轮科学结论：C/B重复性、C/M解释、B/P与C/P实际结果、证时与下界代价、候选去留及B默认状态。随后给实际CSV增量/配对/胜例、稿件/PDF、独立复核和Draft PR。不要用文件数量、运行时间或“所有步骤完成”代替研究结果。
