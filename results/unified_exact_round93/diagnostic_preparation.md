# R93 同向双站数量线：固定见证诊断准备

状态：只读资料核对与预注册。唯一可执行合同在 [coquantity_diagnostic_preregistration.json](coquantity_diagnostic_preregistration.json)；此准备**未运行** G1/G2 driver、原 C++、构建或 solver，也未生成新输入。三例是 [R88 A2 固定见证合同](../unified_exact_round88/a2_endpoint_probe_contract.md)已经预选的 D6→E8→S12，不是按本机制预期胜负挑出的历史最佳。两个 A2 代理在这三例未得到原 F 严降；[线性端点报告](../unified_exact_round88/a2_endpoint_diagnostic_001/report.md)及[复合代理决定](../unified_exact_round88/a2_composite_endpoint_decision.md)是负面背景，不给新线提供结果预测或隐含调参许可。

## 原始字节与起点

| 例 | 原输入、场景与 SHA256 | 固定见证与 SHA256 | 历史原 F 与旧闭包信息 |
| --- | --- | --- | --- |
| D6 | `reference/citibike443-regional-v1/instances/V30/cb443_V30_compact_r1_shortage_M03_Q30.txt`；`070c2c1413840a09a264d238bdfa320ef76d293a45cab919095851afdea8c01d`；V30/M3/Q30，T18000 | `results/unified_exact_round88/runner_a1_startup_d6/raw/01_D6_ENS-C/result.json`；`a8939cae620b6cdf6d20e3d2f957981bbc5144f9157b26dd5dbb5cfc91eb9c3c` | `0.15750980361456174`；`audit.json neutral_closure.passed/exhausted=true`、4 个 strict moves、0 Optimize；这是 startup-only 最终路线。 |
| E8 | `reference/qualification_round39/small-easy/round39_small_easy_V12_M3_Q30_slot08_seed1167625600.txt`；`587737b9d000c1712220232a0fe957073f1f03ac649a63a4775abd9166603acd`；V12/M3/Q30，T3600 | `results/unified_exact_round88/runner_a1_g3/raw/02_E8_ENS-C/external/initial_witness.json`；`70534fd162bff80ad50210ad94a02a2e0e7f6c6efafd67e58a3dea32ac1faea3` | `0.022295597484276734`；首个 `same_run_verified_startup`。原运行后续 neutral closure `passed/exhausted=true`、2 次等 F relocation、0 次 strict move；所选首见证**不是**后来的同路由闭包终点。 |
| S12 | `reference/citibike443-regional-v1/instances/V12/cb443_V12_regional_r1_surplus_M01_Q30.txt`；`060ee6366b2277c8427675e1a1484de7db10d2ef82a64d4e2ffa6e4695b7b626`；V12/M1/Q30，T10800 | `results/unified_exact_round88/runner_a1_g3/raw/05_S12_ENS-C/external/initial_witness.json`；`af1a591e03c65fd81b96c4fe52b92978f09e34b9a2c2108ff807fc838225fd4b` | `0.05856397312578515`；首个 `same_run_verified_startup`，neutral closure `passed/exhausted=true` 且 0 move。 |

各例取/放均 60 秒，`lambda=.15`。以上六个 SHA 已在本轮从实际小文件重新计算，和旧 [R88 prereg](../unified_exact_round88/preregistration_a1_g3.json)及 A2 合同一致；正式发射前须再算并同时绑定诊断源码/二进制。三份见证来自旧 R88 binary `23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693`，本轮只作为**离线输入**。E8/S12 `initial_witness.json` 只有 `objective,routes`，没有可直接继承的最终库存/物理明细；所有三例都由新的原 Evaluator 从输入与 routes 重新建基线，不能拿 R88 或 R90 的最优 U 作为本诊断起点，更不能送给正式 ENS-C。

## 隔离问题与待绑 driver

新机制按 [数学提案](math_research_proposal.md)的 `(a,b,t)`：目前已服务的两站 `a<b`，两站库存同加一个容量允许的整数 `t`；保留车主及访问相对顺序，净操作成零则删除站点。枚举每对的**全部**容量合法整数 `t`，对每条实际候选经原 `verifySolution`/原目标复算，重算前缀载量、载货返仓时间及旅行，严格原 F 降 `>1e-12` 才接受；整轮按最小 F、再按 `(a,b,t)` 决定唯一改进，接受后在新已验见证上重新穷尽 co 邻域，直至没有严格改进。S=0 依原目标约定，不用分式除零。未访问站库存仍纳入全站 G/P；route JSON 的站号、depot 哨兵及原 parser 坐标优先/权重语义沿用 A2 合同。任何前筛若存在也不能漏掉合格候选；日志必须包括每个 `(a,b,t)` 的验证/拒绝及对应原 F，才能判定“完整扫描”。

本 G2 **隔离 co 机制**：不在 co 接受后穿插旧 R73/R75/R76/R83 closure，也不调用 LP/MIP。旧 `neutral_exchange.exhausted` 是旧邻域在旧路线状态下的证据，不是新线的停态证明；尤其 E8 首见证和旧 neutral 终点路线不同。将来若考虑正式接入，另按已商定但尚未实现的规则冻结：完整 24+1 与既有 R76/R83 closure 先穷尽，再扫 co；co 有严格 gain 后重开旧 closure，直到共同穷尽或整次全局截止。正式规则不得设 co 模块内秒/Work/候选切片。本诊断不能声称那个完整增强算法已通过资格。

[primal worker](primal_mechanism_proposal.md)暂拟 driver 入口形如 `Round93CoQuantityDiagnostic --input PATH --witness PATH --T NUM --pickup-time NUM --drop-time NUM --lambda NUM --out-dir NEW_DIR`；这是接口预案，**不是已构建命令**。最终 source、binary、CLI 和 SHA 尚未产生/绑定，须由 root 的独立 G1 资格和新 gate 文件确认后才可落成真实命令。预检需覆盖手算反例、原 Evaluator 数值与物理边界、D6 result 与 E8/S12 initial 两种 route JSON、失败/timeout 前缀、输出完整性及 process-tree cleanup。不能因临时 driver 与预案不符就静默改预注册样本或验收规则。

## 截止、证据与解释

只一次 D6→E8→S12；每例完整外部诊断 120 秒，含启动、hash、解析、基线重验、每条候选、重复扫描、日志 flush、退出及后代清理，三例截止上界合计 **360 秒**。如一次达到外部截止，保留已提交前缀，结果记 `unknown`；可继续下一**预定**独立例，不能补同例时间。身份、数学/物理正确性、receipt 丢失或资源失败则停批独立复核。没有因为无正面结果而新增角色、seed、步长、半径、重启或代理。

每例应逐一存：原 witness 路由/库存/物理/F/G/P；每 pass 的扫描总数、有效数、无效原因、最佳合法严格 ΔF；每个 `(a,b,t)` 的原 Evaluator receipt；接受序列/最终路由与 `finalF`；穷尽或截断的确切时刻；完整外层墙钟/原生子调用/日志与内存可观测范围。若没有完整账本，不能宣称邻域穷尽；若有一个新合法 U，只能说固定见证局部下降，不能用它当完整算法的证书或与 P-GRB 认证时间比较。三例无改善是这三个固定点的负面机制证据，不是否定所有输入的定理。研发准备、G1、三例实际运行、独立审查与归档的外层成本分别记，不把嵌套时间相加或把旧 ENS-C 启动算成本轮免费加速。

## 已写但未发射的 G2 监督入口

[scripts/round93_coquantity_diagnostic.py](../../scripts/round93_coquantity_diagnostic.py) 的 `validate` 子命令已只读通过，重新核了三例输入/见证 SHA 并解析逐车 route 数；Python `ast.parse` 也通过。二者不调用原 C++。真实发射入口只有一次全批 `run`：

```powershell
D:/msys64/ucrt64/bin/python.exe -B scripts/round93_coquantity_diagnostic.py run --qualification-gate results/unified_exact_round93/COQUANTITY_G1_GATE.json --out-dir results/unified_exact_round93/runner_coquantity_g2
```

该命令现在**不可执行**：上面的 gate 文件名只是待 root 指定的占位路径，独立 G1 资格与二进制未在本准备中绑定。正式 gate 必须是 `round93-coquantity-g1-qualified-driver-v1`、`status=qualified`，含本预注册 SHA、`driver_binary:{path,sha256}` 及 `source_sha256` 映射，至少覆盖 `src/Round93CoQuantityDescent.cpp`、`include/Round93CoQuantityDescent.hpp`、`tests/round93_co_quantity_diagnostic.cpp`、本 Python harness。所有路径限仓内、逐项在发射前和后核 SHA。root 必须把实际 G1 的独立静审/动态资格结论与这份 gate 对齐，不能把 JSON `qualified` 字串本身当资格。既有输出路径一律拒绝，禁止 resume/覆盖。

监督脚本固定 D6→E8→S12，每例只生成一次原 driver CLI：`--input --witness --T --pickup-time --drop-time --lambda --out-dir --whole-run-seconds`。外部从预检开始计时，单例 120 秒、全批 360 秒；其内部 whole-run 参数只继承剩余整例截止，不分配组件时间。Windows 下先将等待旗的 Python 包装进 kill-on-close Job，写旗后才启动原 driver，超时关闭整棵进程树；stdout/stderr、真实退出码和外层 wall 写独立收据。driver 内 `wall_seconds` 在 summary 写出之前采样，因此**外层收据**才是完整启动至退出权威口径。监视器的 CPU 秒仅计 Python 自身；子进程 CPU 在此 stdlib 入口不可直接观测，标为未知，绝不写零。

`points.jsonl` 每个整数点保存 pass、`a,b,t`、物理/目标 flags、拒绝原因及可用的 F/G/P；`acceptances.jsonl` 保存严格接纳；原 C++ `summary.json` 给起末 F/G/P、计数和穷尽状态，`final_witness.json` 由原 `VerifiedCandidateStore` 再验。外层从原输入 `initial/capacities` 与每轮已接受路线**独立生成应有的完整 `(pass,a,b,t,Y_a,Y_b)` 有序列表**，逐条对照 points，要求 `passes=accepted+1`、前面各 pass 均接受且最后一轮无严格改进；再按最小 F 与 `(a,b,t)` 复核所选接纳，从原固定路线依次应用操作、删零站，与最终路线逐项对照。每点的候选路线可由当轮起点和 `(a,b,t)` 唯一重建，不在每行复制整条路线；原 F/物理仍依赖 G1 合格 driver 的原 Evaluator，外层不额外运行 C++。若硬杀前账本未 flush，`unknown`，不推断接受数或穷尽；identity/物理/重建冲突、driver `verification_failed` 或资源故障优先标为阻断，即使同时接近截止也不掩盖为普通 timeout。普通整例超时可以继续下一份**预定**见证，不能重试本例。单例收据是写收据前状态，`batch_completion.json` 汇总其后复核；最终整批 launch-to-exit 由 root 的外层 PowerShell Stopwatch 与真实退出码收据核定，若跨 360 秒仍判 unknown，不能用内层写盘前的完成标签覆盖。
