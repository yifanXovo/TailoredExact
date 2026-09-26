# Round88 原生 OT user-cut 接口核查（只读，未准入实现）

**判断。** 可以设计为同一叶的原生 Gurobi MIP 内、事件驱动的 `MIPNODE` user-cut 分离；当前 ENS-C 并未启用该功能，现存回调也没有 B1/B2 CDF 家族。它省去外部 LP 服务反复读模/Optimize 的架构，却不保证更快：每次节点扫描、切割传输、预处理变化及求解器内部重优化均计入原证明成本。本核查没有运行任何模型、测试或六臂实验。

## 当前真实入口和列

ENS-C 经 [main.cpp:264](../../src/main.cpp) 继承 R67 VD-P，置 `external_gini_interval_mip_policy=round55-vd-p`（:336–345）；该策略在 [Round50IntervalMip.cpp:162](../../src/Round50IntervalMip.cpp) 被解析为 `station_state_formulation=vd-p`、`tailored_cut_policy=f0-clean-none`、`round53_callback_mode=c0-baseline`。冻结方法也明确动态 user-cut 回调关闭（[R83 方法:165–191](../unified_exact_round83/unified_method.md)）。证明控制器按外部叶构造 canonical LP（[PaperExternalGiniTree.cpp:3532](../../src/PaperExternalGiniTree.cpp)），所需完整 MIP 以 `PaperTerminalMip`、叶 id、`gamma_L/U`、模型 SHA/作用域进入后端（:8201–8237）；还有同框架中的部分目标 MIP，不能只接 terminal 才宣称覆盖全部原生 MIP。

后端实际以 Gurobi C API `GRBreadmodel` 加载原始 canonical 列（[GurobiBaseline.cpp:1629](../../src/GurobiBaseline.cpp)）；动态符号表已加载 `GRBcbcut` 与 `GRBcblazy`（:77–78, :216–220），每次 Optimize 注册一个合并回调（:2512–2516）。R53 路径在最优 `MIPNODE` 读取整个 `GRB_CB_MIPNODE_REL` 向量并按原始列名映射、调用 `GRBcbcut`（:1064–1148, :2447–2475），但现行分离器只拷贝 `p_`、`z_`（:1113–1125），**不能直接获得 OT 所需变量**。VD-P writer 的实际列名为 `state_i_y`（数学 (s_{iy})）、`state_g_i_y`（数学 (q_{iy})）、`h_i_j`（[CplexBaseline.cpp:272–284](../../src/CplexBaseline.cpp)）；分别是 B/C/C 列，且 one-hot、(G) 重建、透视界、库存链接在 :2836–2875。必须新建严格的完整列域/支持/索引校验，而非把 `q_` 或 `s_` 当作 LP 名称。

## 最小事件设计与正确性边界

给新默认关闭的研究身份，保持 ENS-C 现有 F0、Gini 叶覆盖、完整证明、参数与全局截止。每次**完整 MIP** 的最优 `MIPNODE` 读原列松弛点；对每站对用固定域支持算最违背 CDF 符号行，将**全部新且可靠违反**的 B1 行通过 `GRBcbcut` 提交，按模型 SHA/叶域/规范化精确系数签名去重。B2 仅以当前**外部叶**构模时冻结、确实外包该模型 `G` 域的 `[a,b]` 生成；`a=b` 转 B1。内部 MIP 节点暂时的 G 界不能生成作用于整棵外部叶的 B2 user cut；子叶 B2 亦不能回送父叶或兄弟叶。B1 虽与 G 域无关，也仍须核同源输入及库存支持。没有内部时间片、固定轮数、行数或按实例分派；求解器自然触发节点回调，原全局截止统一付费。

此处是 **user cut**：B1/B2 已对当前叶每个整数原解有效，仅强化松弛，漏加不破坏模型可行集；已有原约束仍负责整数可行性。`GRBcblazy` 是补充未显式建出的必要约束的路径，不应把它当 user-cut 的替代物。当前代码只载入 lazy 符号，搜索未见 `cblazy()` 调用或 `LazyConstraints` 设置。R52/R53 的已测切割是 support-duration `p/z` 家族，不是 CDF；R55 MC4/VD-J 是站内产品/罚项，非跨站 `h` 运输下界（[OT 提案:25](ot_compact_epigraph_proposal.md)）。Round88 B1/B2 目前仅有离线 LP 诊断/闭包证据，不存在已测原生 CDF callback。

## 工程与数值风险、待证 API

当前 ENS-C `c0-baseline` 不设置 `PreCrush`；R53 只有特定研究策略才设为 1 并回读（[Round53CallbackIsolation.cpp:5](../../src/Round53CallbackIsolation.cpp), [GurobiBaseline.cpp:2303](../../src/GurobiBaseline.cpp)）。新方案必须在作用的 MIP 上要求 `PreCrush=1`/回读和 `GRBcbcut` 可用、以原始列序传索引，并验证 user cut 未被预处理静默丢弃；这会改变求解行为/成本，不应被称为零成本接口转换。已装 Gurobi 13.0.2 C 头确认 `GRBcbcut`/`GRBcblazy` 原型及 `GRB_CB_MIPNODE_STATUS/REL`、`PreCrush`/`LazyConstraints` 常量（`D:/gurobi1302/win64/include/gurobi_c.h:284–288,700–704,1374–1381`）；本机 docs 目录没有 API 语义正文。PreCrush 对此新行的实际映射/接受性、一次 callback 多行后重复调用时序和日志中的逐行采用证据，仍需专门微型 native 验收，不能从头文件推出。

R53 cut 分支在 [GurobiBaseline.cpp:1169](../../src/GurobiBaseline.cpp) 直接 `return 0`；新路径须与后续进度、原界目标和证据回调组合，不能照搬该早退。数值上 B2 的 `(b-a)` 归一化在窄叶放大原行残差；沿用 Round88 离线工具的精确有理系数、原 LP 残差/舍入保护与不可靠即跳过语义，不能只看固定 `1e-6` 违反。全站对扫描及每节点可能产生的多行、签名池和 callback 内内存/时间都可能很大；未提交或不可靠行需留痕，不能把缺少行误报为闭包。现有 `Threads=1, Seed=0, Presolve=Auto, MIPGap=0` 及容差标准见 [R83 方法:224–229](../unified_exact_round83/unified_method.md)；新方案不应私自改它们。结论限于接口/数学可行性，不是性能或完整凸包证明。
