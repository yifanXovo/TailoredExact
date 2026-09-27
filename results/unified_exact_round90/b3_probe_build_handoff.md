# B3 G2 五站处理时间取整：source-only 导出交接

本交接只固定一个独立诊断输入，不是 ENS-C 新策略或 B3 cut 的实现准入。`tests/round91_handling_rounding_probe.cpp` 尚未编译或运行，以下 API 契约均待后续零 Optimize 导出验收。原 [有限数学核查](b3_next_evidence_proposal.md) 已证明五站不等式由逐车整数处理时间取整支配；即使诊断有差，也不能把它归为独特 B3 增益。

## 真实模型来源和拟生成文件

程序只接受 `--out NEW_DIR --source-root REPO`，拒绝覆盖既存输出。它把固定输入写为真实 Hybrid GA 解析器文本 `five_station_input.txt`，由 `parseInstanceFile(..., T=5, pickup=1, drop=1)` 读回；五站全部初存/容量 2、目标/权重 1，两辆车 Q=5，6×6 有向距离全 0，λ=0.15。零距离满足当前 K1 metric 条件。没有修改正式实例或算法选项。

物理 witness 是车 0 的 `0,1,2,0` 与车 1 的 `0,3,4,0`，各访问站取 1、无送。原 `verifySolution` 必须返回完整可行、有限目标和库存 `[0,1,1,1,1,2]`；`17/60` 仅作为独立数值核对，**模型 cutoff 始终取 verifier 实际 F**。该 witness 的每车处理时间 4≤5，返仓载货由 verifier 计入卸载时间。其正 F 同时保证候选分数目标 0 不会因 cutoff 自然消失。

`SolveOptions` 从默认值出发，先设置 `main.cpp` 中 `paper-gf-tailored-bc` 基础分支遗留的五个 interval 模型标志，再调用 `configurePaperK1AmSfOverrides`（内部调用 `configurePaperK1AmSfCanonicalF0`），并按 R83 preset 指定 `round55-vd-p`；`parseRound50IntervalMipPolicy` 必须给 VD-P、无 exhaustive subset duration、无 sparse removal。`CanonicalCompactModelSpec` 复刻 `PaperExternalGiniTree.cpp:3545–3562` 的根叶：`strengthened=true`、`interval_restricted=true`、`[gamma_L,gamma_U]=[0,min(verified F,4/5)]`、验证 cutoff 行、ε=0、所解析的 VD-P/F0 policy。调用真正的 `writeCanonicalCompactModel` 输出 `canonical_L0.lp`，要求完整原 compact 模型的静态区间 scope；未手写简化 LP。没有求解器环境或 Optimize 调用。

`export_manifest.json` 预计保存解析后输入字段、witness 路径/操作/库存/G/P/F、options/spec 有效字段、必需变量名、输入/LP/二进制 SHA256、rows/columns/nonzeros、row_signature/model_scope，以及 `src/`、`include/` 所有常规文件、该导出器、`CMakeLists.txt` 的逐文件 SHA256。导出前后两次 source 清单必须相等。外部执行收据另记 Git commit/dirty 状态、完整命令、墙钟/峰值内存、退出码和目录逐文件 hash；源文件哈希只是字节身份，不等于从仓库状态独立证明 preset 生效。导出如中途失败保留目录及 stderr，不原地重跑覆盖。

**仍需验的接口边界：** `applyAlgorithmPreset` 仅在 `main.cpp` 内部可见，导出器按现有源码显式重建其对这个 LP writer 的基础标志并调用公开 K1 helper；不能在未运行时声称生成 LP 与当代 ENS-C 同字节。零 Optimize 验收须核对 manifest 的有效选项/VD-P 列、G 域、cutoff、根 F0 行、全部原输入与源码 SHA；如有基础选项遗漏，停止，不进入三臂。普通 R83 startup/GA 选项不参与此独立模型导出，也不注入已知最优值。

## 后续编译与三臂（均未获本轮执行许可）

待 R90 筛选结束、root 单独批准后，在新研究 build 目录配置同一已装工具链。届时仅新增如下诊断 target 到 CMake 并单独构建，不加入 CTest 自动运行，不编辑当前冻结 `CMakeLists.txt`：

```cmake
add_executable(Round91HandlingRoundingProbe tests/round91_handling_rounding_probe.cpp)
target_link_libraries(Round91HandlingRoundingProbe PRIVATE exact_ebrp_core)
```

构建后二进制以绝对路径调用 `Round91HandlingRoundingProbe --out <全新输出目录> --source-root E:/codes/ExactEBRP`，只作零 Optimize 导出。外部收据确认进程无 Gurobi/CPLEX Optimize 事件，输入与 LP SHA 固定，再审查是否准入三臂；不得借此启动正式 ENS-C 解算。

三臂后续可复用 `scripts/round88_ot_diagnostic.py` 中已审的 Gurobi LP `read→relax()`、全列 primal 与全原行/变量 bounds 残差保存方式，但需独立的极小诊断入口，不能把 OT 切割例程改名复用。每臂从**同一原始 LP SHA**新建连续松弛，原全部行、bounds、cutoff 和 G 区间保持；三臂均重新设目标 `maximize Σ_{i=1}^5 state_i_1`，并记录原 minimization 目标的 primal 值。A 不加行；B 加 `Σ_i p_0_i≤2`、`Σ_i p_1_i≤2`；C 只加 `Σ_i state_i_1≤4`。变量名来自 `CplexBaseline.cpp:265–280`，须检查每个变量恰有一个、state one-hot 覆盖 `{0,1,2}`、drop 上界为 0，并保存加行前后的准确模型身份。每臂保留 status、求解器容差/参数、完整 primal、**全部原行及新行**残差、所有变量 bounds 残差、逐车取量、五个 state、原目标/G/P、墙钟与资源费用。只在最优且残差合格、同源同域时比较 A/B/C；超时、不可行或数值不明标 unknown，不能将未完成值当界。统一整项外部研究截止由 root 另签，不拆内部组件预算、不自动重试。

判据固定：若 A 的认证最优值≤4，只能说**这一条**五站 cut 已被当前完整 LP 隐含；若 A>4 且 B≤4、C≤4，说明原 LP 存在逐车取整缺口，但 B 已支配 C，仍不晋级 B3 专属实现；若 B>4，优先查原库存/送量域与变量身份。任何结论仅关于此固定根 LP；不推断完整模型凸包、整数求解加速或其它实例。这里未构造 LP、未编译、未运行脚本/测试/求解。
