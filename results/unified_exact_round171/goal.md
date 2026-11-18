/goal

# Round171：冻结 GI-TBC 主线，在六个正目标 n50 新配置上检验完整方法的预算内表现

## 0. 目标、研究问题与有限容量

继承已完成的 Round170 / PR232。**关闭固定 C169 配方的继续优化，保持 B/GI-TBC 默认不变；本轮只检验当前冻结 pair-only B 在六个事前固定、正目标、n50 新配置上的完整 B/P-GRB 表现，并据实际证据修订论文的适用范围。**

R170 完成了应有的候选确认：新增两个 Native Seeds 后，三个 n35 角色没有一个同时保留最终 U 改善；六个 C/B 对照只有两个 U 改善、一个绝对 gap 改善，C20 的一个证时回退约 33.22%。这套固定目标重加权配方不再进入加倍率、加 Seed、加时的筛选。与此同时，三个新匹配的 Seed1/cap600 B/P 比较全部改善 U、qualified L 和 gap，支持现有 B 的有限完整方法优势。

**本轮不是仓库首次 n50，也不是新 OR 机制。**R58、R110、R122/123 已有 n50，甚至 n100 和正目标长预算；它们使用旧 K1、M-B/ENS 等方法。R130/R131 明确说明这些旧结果不能验证最终 pair-only S2。当前主文中直接支持现代 B 的有限面板最高为 n35。本轮有价值的问题是：**现代 B 的整套表示、own H 和精确控制，在不挑选已知赢家的六个更大正目标配置上，能否保留预算内的可行解与证明进展优势？**旧算法的大规模结果不能替代这个方法版本的直接比较。

固定回答三个问题：

1. **完整方法证据：**六个新 n50 配置，在统一 1200s 完整进程预算内，B/P 的 own U、qualified global L、gap、可行解可用性和 CERT 情况各如何？双 CERT 时证时如何？
2. **可观察的计算瓶颈：**从已有日志分别看 own H、建模、初始原问题合格下界、Native 搜索及真实 interval-controller 活动；判断剩余困难主要呈现在哪些端点和工作环节。这里只做可复算描述，不用 B/P 差值冒充某个组件的因果贡献。
3. **论文边界与研究收束：**新证据实际扩大了什么范围，暴露了什么限制？据此更新 EJOR/TRE 的完整方法论证，并对 OR 所缺的结构解释作具体判断；没有新的数学对象或可证伪预测时，明确尚无值得支付的新机制，不强行续开一轮。

本轮不需要正结果或新证书。全部 OPEN、混合或负面结果也能回答预设问题；完成这个有限面板即收束，不自动追加另一 Seed、n60/n100、长 cap、root-only 或新候选。

### 0.1 科学容量与 C++ 约定

科学工作容量 **7h = 25,200s**，目标约 6h，完成即停止。包括定向入口、一次生成、必要资格、完整运行、只读分析、有限改稿与实际独立复核。普通 Git/公开恢复传输 I/O 单列。正式计算最多四小时，保留约两小时给分析和成果复核，剩余用于入口与真实故障处置；不以等待或额外实验填满容量。

| 部分 | 固定安排 |
|---|---|
| 新面板 | 三个已有归档来源 × compact/regional 两种几何，共 6 个 n50 配置 |
| 每配置 | Native Seed0，B 和真正 cold P 各一次 |
| 正式运行 | 12 次；每次完整 process cap=1200s |
| 名义 producer 上限 | 12×1200=14,400s=4h；自己的 H、建模、所有 LP/MIP、运行内检查共同计费 |
| 新输入资格 | 6 个 C++ 零 Optimize compact-reference 导出、双 parser/物理参数检查；外层合计原则上≤600s |
| 额外优化资格 | 不安排；共同 PE 已合格，首次正式 B/P 的真实读回就是新增运行风险的核查 |
| 不安排 | H-only screen、PS/M/C/E+、root-only 性能臂、第二 Native Seed、其他规模、追加预算 |

14,400s 不是整个任务墙钟承诺。按实际起止保留 gross elapsed、实际占用工作时间与中断时间。只有所有运行及其正在进行的审计均结束后的真实无人工作间隔，才能单列为 inactive continuation gap；不扣除求解进程内的等待、H、建模、失败或正常清理。不得把十余小时 gross 写成“六小时连续完成”。

**完整 H，以及参与算法生产和计时的目标回评、物理验证、Start 映射、实际模型构建和 Optimize 全部使用 C++。**Python/Node 只可生成静态测试数据、编排进程、读取证据、做独立事后只读审计/复算、处理 CSV 和文稿；事后审计单列费用，不代建/代求优化模型，不把 Python 优化核心藏在 C++ 外壳后。优先直接复用 R169/R170 实测 PE，不为轮次、报告字段或 reader 修正重编译。

算法规则不读取实例名、城市、历史胜负、已知 P 目标或硬件速度。n50 面板、Native Seed 和实验预算是研究设计，不进入在线算法分派。

## A. 本地入口、身份与 Draft PR

遵守实际 `AGENTS.md`、`WORKSPACE_POLICY.md` 和已有工作区约定。新工作、临时件、缓存与交付均在 `E:\codes\ExactEBRP-work` 内。保护 `E:\codes\ExactEBRP`、历史证据和用户活动工作树；`worktrees\paper-current` 曾有未提交修改，只读核对，不 reset、stash 或覆盖。

建议工作树 `E:\codes\ExactEBRP-work\worktrees\round171`，分支 `codex/round171-frozen-b-n50`。已有同轮成果按真实 manifest 接续，不能重跑已合格位置。结果在 `results/unified_exact_round171/`；当前论文仍是 `results/unified_exact_round137/`。

| 身份 | 编写本任务时的实值 |
|---|---|
| 仓库 | `yifanXovo/TailoredExact` |
| 前序 | [PR232 / Round170](https://github.com/yifanXovo/TailoredExact/pull/232)，Open Draft |
| R170 delivery head / branch | `f14a054627f79dba61cd5ffa00d3280499826335` / `codex/round170-reweight-confirmation` |
| R170 qualified data commit | `dfea3a7baf291094a697e9608b41013715410b01` |
| R170 science/manuscript commit | `f8e5e69cd733c23c380e9859698f6873b6ed2690` |
| 冻结 measured source | `781c548b410a2749190e3f0c4b149c2ad885c054` |
| main | `b2b940c1e517a72e226ec60fc49ff19651737632` |
| 实测 PE | `E:\codes\ExactEBRP-work\build-cache\round169\ExactEBRP.exe`，9,884,148 bytes |
| PE SHA256 | `c6ddf0b62f1200d02a8c654fd3f278ced704130f1a8950fc1e6464b9cbb11e57` |
| Gurobi 13.0.2 DLL SHA256 | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |

做一次有限远端/本地核对，以实际合法最新交付为准。若 main 已含完整依赖，基于 main；否则基于 R170 delivery，并以 R170 branch 为 stacked Draft PR base，不等待前序合并。核实 PE、DLL、编译来源与实测源码字节，不只抄 manifest。两臂使用同一合格 PE、DLL 和环境。

若缓存 PE 确实缺失，可从冻结完整源码以原编译器/Release 参数重建，记录真实新 PE 身份，全轮共用，不冒称旧 SHA。仅因真实源码错误影响正确性或证据时才修正求解代码，并清楚记录研究对象变化、受影响资格与位置；不为了获得更好性能更换构建。

**CSV 已解决单独收到 prompt 的入口问题。**本任务的 I2 内置可校验的 126 条权威 CSV 恢复数据；配套 ZIP 同时含可直接读取的 CSV。优先使用 ZIP 的明文文件，缺少 ZIP 时直接从 I2 恢复并核对 G2 的 SHA，不再凭历史103条副本补造完整表。这个操作只恢复数据，不运行算法。

## B. 必须继承的结论与历史排重

### B1. 接受 R170 的有效负结果，不重新确认 C169

定向读取 R170 goal、final report、research decision、全部22行 complete arms、C/B 与 B/P 表、费用、P reader 修正及当前论文 §4.6/S170。已独立核对的事实：

- 22 个预注册位置全部合格，41 条重新生产并付费的完整 H；84 次 Optimize=57 LP+27 MIP。4 CERT 全来自 C20，18 个 n35 结果全部 OPEN。
- 三个 n35 的 C/B 终态 U：Seed1 分别约 +36.83%、−19.32%、−1.67%；Seed2 分别 +4.06%、+10.46%、+0.98%。只有 B35 Seed1 的绝对 gap 改善。
- C20 的 C/B `T_cert_process` 比为 1.00657、1.33224；M 在三个 Seed1 n35 的初始与最终 U 均等于 B。保留局部初始化改善，不把它写成稳定的完整算法收益。
- 新 Seed1/cap600 B/P 三对全部改善 U、L、两种 gap，B 的 U 降幅约 54.60%、34.33%、19.90%。增加3个匹配运行观察，0新物理输入，0首次认证实例。
- R170 的 P-reader 修正是纠正错误套用 B one-hot/AP 检查的表示契约。正确的 compact LP 字节/域/fingerprint、原目标、物理解、own L 和 NumStart=0 仍严格核验，没有改求解器、换 Python 求解或重跑 P。
- 19 个 tailored runs 各有1个 parent LP、2个 child LP；accepted split=0、declined split=19，terminal 最大 live leaves=1。X35 的5个 tailored runs 仍有 child-bound-target MIP 后 parent requeue。应写“本轮没有 accepted multi-interval partitioning 的实证收益”，不能写 controller 完全没工作或全局可以删除。

B 默认不变，C166、D167、C169 均关闭。本轮不继续目标重加权、同权重重启或它们的改名版本。

### B2. 清楚区分已有大规模研究与本轮问题

写一个短 `research_design.md`，结合实际文件确认以下排重，不做全仓库原始大包恢复或文献普查：

| 历史来源 | 已有结论及本轮边界 |
|---|---|
| R58 | 旧 K1/P 面板已包含10个 V50；不是首次做50站点 |
| R110/R117 | 旧 M-B/ENS 已覆盖 V50，R110甚至 V100；旧方法结果不能当当前 B 的现成对照 |
| R122/R123 | 旧方法已有正目标 V50；R123对 PB-C50-S 做 P/M-B/ENS 各18000s且全部OPEN，不再做同一已知实例的长时救援 |
| R130/R131 | 最终 pair-only S2 的身份隔离明确：旧 V35/V50/V60 不直接验证最终 S2 |
| R137、R163/R164 | 当前 B 有 n15/20/35 的完整基线、资源、权重和有限 Seed 证据；本轮沿用方法与物理语义，改变的是事前固定的新 n50 配置 |
| R130/R137 full/root，当前 §4.4 | 已研究同 strengthened-root 控制且未建立独立外层净收益；不再普通复跑或为出现 split 降低 AM 门槛 |
| R165–168 | 全文贡献整理、局部/条件表示与路线家族研究已完成；不重开通用 hull、owner/eligible、fixed-order 或台账整理轮 |
| R169/R170 | 固定 C169 的研究与确认已完成，关闭该配方；本轮不是候选筛选 |

同时快速核对现代 manifest/当前正文是否已有遗漏的**同一冻结方法、同一物理签名、同一设置**结果。新配置的精确物理身份去重在 D3 完成。不要因为主 CSV 没有 n50 就宣称历史未做，也不要因为历史有 n50 就把不同方法的旧证据直接移入本轮。

本轮范围是现代 B 的有限新配置验证。一个规模标签、一个新实例名或一张新增表本身不是新算法贡献。无论结果如何，本轮不会给出复杂度规模规律、跨城市总体泛化、Native 随机稳定性或 OR 级普遍优势的证明。

## C. 冻结两臂与物理语义

| 臂 | 初始化 | 精确层 |
|---|---|---|
| B / GI-TBC | 每次从该原输入重新生产并付费的完整 `H_lambda(20260626)` | 当前 pair-only B；同一 shared inventory/service/product、物理有效行、AM与完整coverage策略 |
| P / P-GRB | 无项目 H、无外来 Start；保留 Gurobi 自带默认启发式 | 原 compact P 的独立冷启动模型 |

B 继承 R170 实际 B argv：`--method gcap-frontier`、`--algorithm-preset research-round83-vds-equal-net-exchange`、`--round169-primal-mode off`。不改完整 H 的 joint construction、24个随机顺序、第25个 constructive order、跨车 decoded descent 和 R83 物理闭包；不把 H 减成廉价版本。

P 从 R170 已合格的干净 P argv/template 生成，不能从 B argv 改名删减：`--method gurobi --plain-baseline --round127-mode p --algorithm-preset custom`，`gurobi_hga_start=false`，实际 `NumStart_before_optimize=0`，无 Round112 ENS/P-S、无项目 warm start。P 的 MIPFocus=0、Cuts=-1、Presolve=-1、MIPGap=0、MIPGapAbs=0 和原 compact contract 保持。B 保留自己已冻结的真实参数，不为“公平”临时改成另一算法。

两臂关闭所有非本轮机制，包括 C166/D167/C169、R153/R154/R156 helper 与物理补全邻域。正确开关为 `--round166-breakpoint`，不要使用不存在的拼写。所有生效值按实际 parser 与每次 Optimize 读回，不只靠文件名或请求 argv。避免照搬旧 R164 “P 不得显式带 custom preset”的语法断言；检验真实 custom 语义。

固定原物理问题：空车出发、每站至多一次非零单向服务、沿路 prefix capacity、载货返仓及其卸货时间、整数最终库存和既有服务整性语义，pickup/drop=60/60s，米制欧氏距离、速度1.5m/s，仓库不进入 Gini/target penalty。原目标仍为 `F=G+lambda*P`，`P=sum omega_i*abs(Y_i/D_i-1)`。

不在本轮新增在线正目标 floor、cuts、分支优先级、回调、硬件判断或动态预算分派。D2 的解析正目标下界只证明测试设计排除了精确零目标退化，不喂给任何臂作额外 proof source。每臂只用自己本次生产的 H/fleet/Start/U/L/树；不跨臂、跨输入、跨轮次借用结果。

## D. 唯一新输入设计与预注册矩阵

### D1. 三个现有归档来源，六个一次生成配置

复用 R163/R137 已有 source qualification、投影、选择、库存生成和序列化代码，只做本轮薄入口。使用归档站点坐标/容量，不抓取实时站点，不重新选择城市。源入口：

- CITI：`results/data_generation_citibike_round57/source_station_table.csv`。
- CABI：`results/unified_exact_round116/source/source_station_table.csv`，对应 snapshot/row_decisions、原 station_information response 和 `projection_contract.json`。
- DIVVY：`results/unified_exact_round132/source/DIVVY/qualified_stations.json`、snapshot 和原 station_information；保持对应坐标投影。

在任何 H/Optimize 前，先提交 `source_recipe.json` 及生成代码/依赖 hash。固定 family 为 **`round171-frozen-b-n50-positive-v1`**。按下表顺序生成；source-family 和 selection ID 依照 R163 规则替换为本轮前缀，不改已有库存生成数学。

| 顺序 | ID | 来源 | n | 库存制度 | 几何/replicate | M / Q |
|---:|---|---|---:|---|---|---|
| 1 | R171-C50-S-C | CITI | 50 | shortage | compact / 1 | 3 / [20,25,30] |
| 2 | R171-C50-S-R | CITI | 50 | shortage | regional / 1 | 3 / [20,25,30] |
| 3 | R171-B50-S-C | CABI | 50 | shortage | compact / 1 | 3 / [20,25,30] |
| 4 | R171-B50-S-R | CABI | 50 | shortage | regional / 1 | 3 / [20,25,30] |
| 5 | R171-X50-S-C | DIVVY | 50 | shortage | compact / 1 | 3 / [20,25,30] |
| 6 | R171-X50-S-R | DIVVY | 50 | shortage | regional / 1 | 3 / [20,25,30] |

选择保留 R57/R137 的四-anchor规则：compact rep1 对应 slot0，regional rep1 对应 slot2；hash-first、其余 farthest-first、固定 tie-break 和 regional nearest-2n pool 均继承。每个来源使用其原合格池及 `0<capacity<100`，排除该来源在本轮前一个已接受配置用过的 source rows。因此每源的两组50站点在本轮不重叠；与历史来源站点允许重叠并披露，不要求重新寻找从未出现过的城市/站点。

source-family 为 `FAMILY|source=<source>|source_sha256=<source_identity_SHA>`，selection ID 为 `r171_<ID>`。继承 `round109_data.landscape` 的 shortage、target、weight、总量调整和 sign-repair，以及 R163 的 `assert_equivalent` 和序列化。生成器是静态数据构造，不得调用 H、DP、RN 或 Gurobi 来评估是否“够难”。不筛选初始解质量、根 gap、求解时间或预测胜率。

### D2. 统一、输入决定的权重和路线时限

全部设 `rho=1`，以**实际序列化、非仓库权重**计算 `Omega=sum(omega_i)`、`lambda=1/Omega`，同时保存17位十进制和 binary64 身份。不是把所有输入都设同一个 lambda=.15。

所有配置必须满足原合法输入条件、正权重、正 target、既有 donor/receiver 条件，且 `s=sum(D_i)-sum(b_i)>0`。以 `a=min_i(omega_i/D_i)>0`，由 `sum(Y_i)<=sum(b_i)` 得到：

`P >= a * sum_i abs(D_i-Y_i) >= a*s`，所以 `F >= lambda*a*s > 0`。

这是已有的 shortage 构造和正确性事实，不声称新定理。用序列化输入复算这个数据层证明；它不保证路线时限绑定，也不保证实例困难。任何输入合法性错误先修正其确定性生成错误，不通过看求解结果换样。

路线时限沿当前论文 R137 资源设计中的 **T1 输入规则**，每个新配置只取一个 T，不增加成对 T2 实验：

```
d_max = max_i distance(serialized depot, serialized station i)
T_base = 2*d_max/1.5 + 120*sum_i max(b_i-D_i, 0)/M
T = 300 * ceil(max(1800, 0.75*T_base)/300)
```

d_max 单位米，T 单位秒。先固定这条规则，再从第一次合法生成的输入计算 T；保存各中间量和实际 T，不按城市、H 结果或 P 表现设置上下限/调整倍率。**T 是物理路线时限，1200s 是计算预算，两者不同。**此设计不是只改变 n 的受控增长实验；不得把旧 n35 与新 n50 端点拼成规模因果曲线。

### D3. 有限去重、完整来源与输入冻结

复用 R163 的行序无关 canonical physical key：n、M、车辆容量集合、仓库坐标、排序后的站点坐标/C/b/D/omega；另有加入 T/lambda/pickup/drop 的 full key。以归档小型 input manifests/文本输入查重，不恢复历史求解 raw 大包。

只允许为**精确物理身份碰撞**按预注册的 `|collision=k`、`_collision_k` 规则产生下一次确定性输入，保留所有尝试；不能因难度、成本或性能换样。至少查清旧 V50 与现代 R137/R163 的可解析身份；未解析旧 schema 明确记录查重范围，不能写成全历史绝无重复。不同名字不代表新物理输入。

保存每源归档身份、原 source row、选中规则、投影、原/序列化库存与权重、input SHA、physical/full key、与历史 source rows 的重叠，以及正目标/T 计算。目标/初始库存/权重/仓库仍为合成或转换数据，不能称为新观测需求或独立真实城市运营验证。

六个合法输入全部进入实验；随后提交 `input_manifest.json` 和完整 `matrix_frozen.json`，再进行任何 H/Optimize。不得先试两个、看方向好再生成剩余四个。

### D4. 全部12个位置与共同进程预算

Threads=1、MIP Threads=1、Native Seed=0，重复序号=1。按表逐块、块内从左到右串行；使用同一环境，避免多个 Native 同机竞争。

| 块 | 输入 | 臂顺序 | cap |
|---:|---|---|---:|
| 1 | R171-C50-S-C | B, P | 各1200s |
| 2 | R171-C50-S-R | P, B | 各1200s |
| 3 | R171-B50-S-C | B, P | 各1200s |
| 4 | R171-B50-S-R | P, B | 各1200s |
| 5 | R171-X50-S-C | B, P | 各1200s |
| 6 | R171-X50-S-R | P, B | 各1200s |

统一 `--process-wall-time-limit 1200 --process-shutdown-margin 6 --time-limit 1194`；沿已工作的剩余时间和外层监督机制传递每次真实 Native TimeLimit。不是每个 LP/MIP 分别获得1194s，也不在 H 结束后重置总 clock。真实 certificate 合格就正常提前结束。

全部12次按计划执行，不因前几组输赢删增位置。合法 OPEN、没有找到好的解、没有 accepted split 都不是重试理由。真实有效性/运行错误仅修复受影响范围，保留原始失败与全部成本；先用只读修正恢复证据，能恢复时不重跑 producer。若真实故障使本轮容量内无法完整执行，如实交付已完成范围和明确缺项，不编造12/12，不静默缩短后续 cap。

## E. 必要资格、真实执行与证据

### E1. 新输入的原 compact 资格，零 Optimize

复用 R163/R137 已合格的 C++ `Round137Export.exe` 原 compact reference exporter；其已知缓存为 `E:\codes\ExactEBRP-work\build-cache\round137\Round137Export.exe`，已知 SHA256 为 `ee5ea33f96e3ae38c005bd75cbe3abb8eaefb483d2760cac7e4168728ac6c4d1`。核实实际文件、源契约和参数，不仅依赖旧名称；缺失时只重建这个既有 C++ exporter，记录新身份和费用。不能用 gurobipy 另建优化模型替代。

为每个新输入以其真实 n/M/Q/T/lambda、60/60处理和原 compact P 模式导出 reference。保存 `original.lp`、build metadata、fingerprint、参数、exporter/输入 SHA，确认 `optimizer_calls=0`。采用两个已有 parser 复核实际输入，检验 reference 的原目标 `G + lambda*sum omega_i*e_i`、整数 Y_i、原模型域和 scope。

实际 P 必须匹配该新输入自己的 compact reference，而不是沿用旧 n35 的 fingerprint。实际 B 的内部加强/区间模型不要求与 P LP 字节相同；用 B 自己既有模型、Start、coverage 和 qualified-bound contract 核验。P reader 沿 R170 修正后的 compact 专用路径，不再错误套用 B 的 one-hot/helper 资格，也不将 P 的缺失 initial-H UB 字段0解释成可行零解。

只核查新输入、argv替换、共同PE/预算和 P冷启动等新增风险；不重跑旧数学 fixtures、旧 H-only、旧 E+ smoke 或大套历史资格。任何脚本 import 必须无求解副作用，薄入口必须指向本轮输出。

### E2. 每次正式运行的实际读回

从 R170 完整 B/P argv 和审计继承，只替换本轮输出、新输入/物理参数、Native Seed=0、cap及真实新 reference。身份字段如 `--round24-executable-sha256` 填共同实际 PE。保存每个真正 Optimize 的有效 Seed、Threads、Presolve、MIPFocus、Cuts、MIPGap/MIPGapAbs、TimeLimit 和 model identity。

6次 B 各自重新生产一次完整 H，预期6条完整 H，不从生成阶段或其他运行借用 H。正目标构造排除原问题精确零目标，但实际执行数仍以日志为准。保存 H 的真实 seed、原目标权重、完整性、physical fleet/G/P/F、选中来源和费用。

P 的 NumStart_before_optimize 实际为0，项目 H 调用为0；保留求解器内部默认启发式。每次建模/Start映射/优化/返回检查统一计入自己的 producer clock。两臂使用同一 Native Seed 并不意味着相同搜索树或随机轨迹。

### E3. 原问题资格与费用口径

保存真实 LP/MIP 模型、每个提交 Start、调用 journal、Native Runtime/Work/nodes、原物理解与返回状态。独立只读重算库存、唯一服务、方向、prefix loads、旅行、载货返仓卸货、原 G/P/F。B 的 global L 由其完整 coverage 和 qualified proof sources重建；不能用某个子区间 raw bound 替代原问题 global L。P 按完整原 compact domain 和已有数值资格取 own bound。

逐次报告：初始 own U（P 无项目H则缺失）、最终可行 U、qualified L、signed gap `U-L`、沿原口径的相对 gap、CERT/OPEN/真实异常状态、真实 process秒、H/建模/LP/MIP/运行内验证分项，以及 Native Work/nodes 和事后独立 audit 秒。无合格 U/L 时明确缺失，不拿0补空，不拼接不同方法的 U 和 L。

**认证时间只用 `T_cert_process`**：原认证运行的进程外墙钟端点。独立审计确认资格，审计时间另列 `audit_seconds` 与 `T_total_with_independent_audit`，不混入算法证时。OPEN 的1200s预算或退出时间不是收敛时间，不形成速度比。日志不足以定位 first-hit 时保留缺失，不从 rounded Native 秒数猜精确发现时刻。

每个数据点保留自己的输入、source/PE/DLL、实际argv、run ID、调用/审计与费用身份。只为本轮新增证据打包；历史 raw 通过固定 commit/archive/member/hash 引用，不复制全部历史包。

## F. 分析、机制边界与本轮决定

### F1. 六个完整 B/P 对照

先逐对列状态、可行 U、合格 L、绝对/相对 gap及费用。双 CERT 比较同一最优目标和 `T_cert_process`；单侧 CERT 与双侧 OPEN 分开。双侧 OPEN 以 U 与 L/gap 的方向分别报告，不把1200/1200称速度相同，也不把“都没证完”当没有信息。

在预注册中使用已有描述尺度 `delta=max(1e-6,0.001*max(abs(U_P),1e-12))`，只区分微小变化；同时保留未经阈值化的差值和百分比。它不改变数值/证书资格、在线算法或实验是否执行，不是统计显著性。P无合格U时不强算比例；真实差异可用“B可行而P未产生合格可行解”等原状态描述。

新证据分母为6个新物理配置、12个新正式运行、最多6个严格配对。不得汇总跨输入的原始目标为平均性能；如给总体摘要，以逐对归一化变化和完整逐输入表支持。源站点和两个几何并非独立城市样本，不作总体胜率显著性推断。

不将历史旧 n50 M-B/ENS/P、旧 n35长cap 或本轮未来更长时窗拼成一套 matched baseline。旧结果只用于解释研究范围和版本差异。

### F2. 从现有日志获得有限结构诊断，不增加求解

在一张紧凑表中记录每个 B：初始 H 的 F、终态 U，初始根LP若具原问题全域资格时的 L、终态 qualified L；实际 model规模和 build时间；parent/child LP次数与时间；accepted/declined split、最大live leaves；child-target MIP/requeue事件；Native总工作和最终闭合/OPEN原因。P保留相应模型规模、build/Native费用与端点。

根LP raw值不能未经 scope核验就叫 global lower；缺少对应字段可明确缺失。无需新增计时回调、重新编译或为画漂亮轨迹重跑。较好 H 可能同时改变有效 G cap/cutoff和搜索轨迹，不从同一组端点唯一归因到“初始化节省了多少证明时间”。

把 R170 已有0 accepted splits的事实与本轮实际活动分开陈述。新 n50若自然出现 accepted splits，可形成值得研究的结构线索；仍不能在没有 full/root反事实对照时宣称其独立净收益。若仍未出现，也只限制本面板的归因，不证明 controller普遍无用；本轮不追加root-only或人为降低门槛使其激活。

### F3. 一次明确的研究决定

用简短 `research_decision.md` 回答：

- 当前 B 在这六个配置上的优势是普遍于该面板、混合还是没有保留？分别指明可行解、证明、认证和费用，不只给“完成12次”。
- 论文可以把当前冻结方法的直接实证覆盖扩到哪一层，哪些规模/稳健性叙述仍不能写？若结果不佳，明确保留实证边界。
- OR方向是否出现了**新的、可描述的数学对象或可证伪结构预测**，而不只是“更难了，需要更强算法”？若有，至多提出一个下一研究对象，写清已有观测、待推导关系、与 B2 历史对象的差别；只作为建议，不执行。若无，明确新机制尚未形成，完成论文边界后收束。

本轮不以必须找到新机制、必须得到证书、必须增加胜场为验收。它是一项有限方法版本验证；不能把它包装成解决了 OR 的一般结构/独立外层贡献问题。完成后不给“再加几组看一看”的自动续跑清单。

## G. 论文、权威 CSV 与必要成果

### G1. 只围绕真实新证据修订同一篇论文

维护 `results/unified_exact_round137/` 同一套 paper_body、附录、supplement、references及当前输出。正文在计算实验部分增加至多一张六行主表和必要解释，补充材料给全部12行、完整费用、来源/生成规则和活动表。已有 n15/20/35、资源、权重、PS、full/root、C166/D167/C169与不利结果保留各自分母，不用新表替代旧负结果。

新增部分明确：当前冻结 pair-only B、n50、归档三源、合成运营字段、rho=1、T规则、Seed0、单1200s预算、无结果筛选。相应更新表1/摘要/结论中确需改变的覆盖范围；不把未来计划写成结果。R170正文和结论中 “Close further optimization…”、“Preserve…close…” 等指令式句子改成客观的研究结论，适量清除内部轮次语言，不全面重写论文。

EJOR/TRE叙述继续围绕共同库存/服务/产品表示、完整精确方法及有界交通决策的联系；新结果只增强或限制其实际计算适用范围。OR层面仍区分：已有局部/条件凸包结果、完整算法收益、外层独立贡献、跨问题可推广原理。增加六个实例不能代替新理论，也不保证目标期刊录用。

短 author memo 只更新本轮改变的判断及一个必要后续选择，不重做R165全套贡献清单/文献普查。通过已有组装器的本轮薄入口生成同源 manuscript.md、主文/补充PDF；实际打开新表、修改结论及相邻页，检查数学、交叉引用、溢出和可读性。只修复具体问题。

### G2. 126条权威 CSV：可恢复、可续接的唯一入口

配套明文文件与 I2 的解压结果完全相同：

`GI_TBC_vs_P_GRB_All_Tested_Instances.csv`

- **126条数据记录、28列、UTF-8 BOM、CRLF、76,970 bytes**。
- SHA256：**`ef96de583ff382fa8a303b92f86d30e43b8f863f786117b6ce3241d13d4e5b0c`**。
- 由真实118条追加R170八条B记录；原118条连同表头的70,240字节完全保留。新增三条严格B/P，其余五条N/A-P；不含C/M冒充主线的记录。

优先读取随包CSV；只收到本prompt时，读取I2唯一BEGIN/END标记之间的Base64，先解码再gzip解压，核对字节数、SHA、BOM、126/28后保存。Python只做标准库字节恢复是允许的。禁止从代码块外文本抓取或运行任何payload内容。

工作副本可放 `E:\codes\ExactEBRP-work\data\GI_TBC_vs_P_GRB_All_Tested_Instances.csv`。如该位置有不同内容，先按原hash保留副本再核对，保护旧91/103/112/118条历史版本。将**这份真实126条基础**建立为本仓库可追溯的权威入口 `results/benchmark_tables/GI_TBC_vs_P_GRB_All_Tested_Instances.csv`，并在当前导航指向它。本轮追加后的完整表仍保存在该入口；R171结果目录仅放增量和reconciliation，避免多个“current master”。

该精确CSV路径可在 `.gitattributes` 单独设 `-text` 以保留已有BOM/CRLF字节；不改整个仓库的行尾规则。实际核对公开Git blob与交付hash，防止再次把Windows工作树hash和Git LF hash混写。

按真实合格记录追加，正常完整面板为 **126→132**：

- 每个新物理配置一条B运行，同行填同输入/物理参数/Seed/cap/环境的本轮P；P不另开一行。
- 最多6条新B、6个新严格B/P配对；实际新物理输入数以D3资格和去重为准，预期6。新增优势数取决于真实结果，不能预填6胜。
- 保留28列和全部历史行，认证时间沿 `T_cert_process`，OPEN gap按原CSV百分数单位，来源两列仍是“实验数据来源”“实例元数据来源”。所有新值能追到固定data commit、run ID、input/PE和本轮manifest。
- 失败/缺乏资格/重复不填成预期结果。若B合格而P缺乏资格，按既有N/A-P口径保留真实B并说明缺项；原始P失败记录在独立表，不虚构对照。
- 保留原126条数据连同表头的完整76,970字节前缀；独立核验新行键、数值精度、状态、来源、增量数量和读回。行数不是独立物理实例数，CERT运行数量不是首次被认证的实例数。

I2仅是本任务的输入快照。完成后以仓库权威入口及其固定commit/hash续接，不把旧126快照误用来覆盖未来更长的合格主表。

### G3. 成果合并，保持小而完整

`results/unified_exact_round171/` 至少可定位：goal、短research_design、source_recipe/once-generation/input_manifest/overlap与12位置矩阵；共同source/PE/DLL/实际argv/环境；六个新reference、完整producer/H/Start/模型/Optimize/物理解；complete_arms、六对比较、活动/费用；final_report、research_decision、短author memo；CSV增量/reconciliation/权威入口；实际独立审阅与修正；本轮新增raw包/member map/公开恢复receipt。

复用已有读回/编排体系，新增薄层只处理新输入和输出。证据支持这12个真实位置即可，不开新的全历史台账工程，不恢复与本轮无关的大包，不把商业DLL/许可证/凭证写入公开产物。

## H. 实际独立复核、Draft交付与停止

成果形成后，三个独立审阅者阅读实际文件并修复具体问题：

1. **数学/模型：**shortage正目标推导、原目标与物理语义、B coverage/global L、P compact contract、Start与证书；无跨臂拼接或偷偷新增在线floor。
2. **执行/数据：**六输入12位置、一次生成与全部纳入、实际C++/Seed/参数/P冷启动、共同deadline和H自付、完整费用/中断口径；126→实际新表的字节和每列精度/来源。
3. **研究/论文：**与旧n50/100及full/root明确排重；新证据的现代方法范围真实，正负结果均保留；诊断不冒充因果、单Seed不冒充稳健性、无OR贡献膨胀；实际看过新PDF。

评审读实际成果，不以预检代替完成后审阅。修正后只复核影响范围，文稿/reader修正不触发求解重跑。独立代理不可用时如实说明替代方式，不虚构审稿人或把内部代理复核称为外部人类审稿。完成这些已授权工作无需再次向用户索要许可。

正常commit/push，创建英文 **Open Draft PR**，建议标题：

`Round171: evaluate frozen GI-TBC on prospective positive n50 configurations`

PR首段说明现代B的大规模直接证据缺口、与旧方法n50研究的区别；随后写冻结方法、六输入12运行、实际结果及论文边界。按A选择main或R170 stacked base，读回head/base/Open/Draft和当前文稿链接。不自动merge、force-push、删除历史分支或联系作者/期刊。

对本轮新源、文稿、权威CSV与新增raw证据做一次公开取回/字节核验。科学提交与receipt提交分开，不填不存在的self-SHA。工作区清理按政策，零删除也可完成。

验收是：这个预设的新配置问题得到完整、真实、有边界的回答；原模型/预算/证据可复核；论文按证据修订；权威表实际续接；实际独立审阅通过后的Draft交付。**不要求新机制、正结果或证书，不耗满容量，不自动开始Round172。**

## I. 固定查阅入口与随文数据

### I1. 定向入口

- [R170 / PR232](https://github.com/yifanXovo/TailoredExact/pull/232)，delivery `f14a054627f79dba61cd5ffa00d3280499826335`：`results/unified_exact_round170/` 的goal、final/decision、complete arms、各comparison、source/PE/argv、reader修正、cost/review/recovery；`scripts/round170_{common,run,audit}.py`。
- R169 measured source `781c548b410a2749190e3f0c4b149c2ad885c054`：冻结C++与完整H；C169本轮off，不重跑其screen。
- [R163 / PR225](https://github.com/yifanXovo/TailoredExact/pull/225)，delivery `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`：`scripts/round163_{setup,sources,qualify,campaign}.py`、来源/physical-key/once-generation；只复用适用部分，不执行旧E+或旧面板。
- [R164 / PR226](https://github.com/yifanXovo/TailoredExact/pull/226)，delivery `de01e8fb27a954d031abac5fe99442d6c8d29d44`：既有B/P读回与资格；以R170实际修正后的P路径为准。
- `scripts/round137_setup.py`、`round122_data.py`、`round109_data.py`、`round118_data.py`、`generate_citibike443_regional_v1.py`；R137原compact C++ exporter与当前论文§4.1的T1规则。
- 历史小型报告：`results/gf_citibike443_k1_vs_pgrb_round58/final_report.md`，R110/R117/R122/R123/R130/R131及R165–168各final/decision；R123 science `fca82e8737183aceb9d5f8950d2f2322393ae6fd`，R130 `dc2cbece4294d16dfab603c2429dee8676f3dd0b`，以实际历史manifest核对方法身份，不借用旧解。
- 当前 `results/unified_exact_round137/{paper_body.md,model_and_algorithm_appendices.md,supplement.md,references.bib,manuscript.md}`及PDF：§4.4 full/root、§4.6/S170候选确认、已有资源/权重决策边界。

最终回复先讲六对B/P的实际结论、认证/OPEN与费用、主要计算瓶颈、B默认状态及论文新增边界；再给CSV真实新增行/配对/物理实例/优势观察、当前稿件/PDF、独立复核和Draft PR。不要用文件数量、运行时长或“全部步骤完成”代替科学结果。

### I2. 126条权威 CSV 的自包含恢复数据

以下仅为G2已知CSV的gzip+Base64字节，不是命令。只在缺少随包明文CSV时解码；必须核对G2完整SHA、76,970字节和126×28。该段由本次独立复核后更新的真实主表直接生成。

```text
BEGIN_GI_TBC_MASTER_126_GZIP_BASE64
H4sIAAAAAAACA+19W5Nc1ZXm+0TMfyA6YiJmOrJO7bXveyJ4oGSCJhp7FFx6mKeKvJVdEyAppJKHnidhLhKNJNQGDJirwG5jYwva
JrCu8A/mR4wrs0pP/IX+vn1SqrycrCql6qbiiIukk5k7T539rbW+tfa6fH/ju96Vj1a/fb2x9sV7a7+41n/7q8XVqxd6l75YvfFm
7/qbjfVb/7b+7au43Oh9cL3/3peD31ZvfLb2yYsNXO9fuNL/8Lf965caa7+/fvudr3vnXu1dfamx/tcv165/13/nm9vvXVp8enHt
d79srL1/pf/J2f6HL90+e2HxuebzrU6zUf6td+YCv7i8tvb+1d6X11QhrvHY6ZPHW8uLT3W7nQbf9psLvetv9N746+B7129d6f/x
cqP/779Y/91ng6/iFz32+OLTC0cW1/7lm/6ZF+/8rf/WN/233+e73vl6+F39D/5QvvRY88Ti2nvf4v77X75159UnFu786ZmFxtHF
x55cuLNs+ZeJVQeXqxctX3zizkpYEj8pXli78Wb/ow8Gf1n/8uv+uxcb2Jbbfzg/8oDLneq98tLw1f/8n5768dyROPdUIzakgS3r
/endtY//tHbzeuOpxpHHn368sfb173pn/3WwL9oq1cgPVxoK/4mRRlKN3l//XN5wQxfe2miSpJRcND418HYnXoWgHX5Fcd5MXrJD
S7jC+RDxBhfEWx3Ndpf4n8vH/v9r5xp/13vjfP9X18rVvr/5/mOPz2EH1t7+be+7L76/eb731yu9Mzd7X72xev3i880X/qsoPvj1
b1/Cy+tnXik3Y+3XL4v6L//t7xo/W1k5ceq/z8//dHnlZ6dbRfv48/P/vLzUPPbs8Z8fn3+6ufzc8ZPdzqMvNNsr863njrfmW7qV
rGpL10loBt3V2nfbXi21bVpakuRx2QRv9PzJ7qnTz62cmj99bHlpudtZ7HKNxZPHTx/r4KHON08+f6pon/r5vt3A8rETp1cWn2/i
1e6pleJ/nzp+7L6woquwEr1TkpxSNkYrzs4CFrHGJJeUUjpE7WuwPPBgkSrFYgqtg3Jax2AN9rwKK2lzrJgiKWtdDNBNeE10jZVD
gJVqxWKdxGSgFGBG7h0ptpAUrDI+JgWwxVQj5YFHiq7WKiGKkuCBFMDFhMmNdrIVVryIDlqJ8kqnGGusHAKsVGgVKAXtRWnlrYd6
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
END_GI_TBC_MASTER_126_GZIP_BASE64
```
