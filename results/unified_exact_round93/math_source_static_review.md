# R93 同向双站线：独立源码静审

**最终源码静审：PASS，可由根准入隔离 G1 构建/测试；不代表 G1 已执行或性能有效。** 根代理发现的旧 driver 起点校验绕过问题已修：driver 现在调用 `verifyRound93StartingWitness`，其顺序是结构/参数检查 → 原 Evaluator `int` 算术域预检 → 原 `verifySolution`。直接 routine、每次扫描基线和诊断入口均使用同一保护。G1 测试源码已扩到九种独立有理 oracle 结构、真实 binary64 `nextafter(T+1e-7)` 边界、非法结构/累计整数溢出及发现改善后中途截止。此判断只来自源码静审；我未编译、未调用 native solver、未运行真实见证诊断或 Git 命令。独立有理测试和成本见 [coquantity_oracle_review.md](coquantity_oracle_review.md)。

最终受审字节 SHA256：`include/Round93CoQuantityDescent.hpp` `92656c6a27dda13b794965fdf6d49bcc38007d16b6780f0ba822f62134253ee2`；`src/Round93CoQuantityDescent.cpp` `cf3ea08852f56a10bceeb59c169ff92de4d9d8aad0914a7233985ce7da4f2012`；`tests/round93_co_quantity_tests.cpp` `b8008945cea3244978b9ff1fd40bb732d54835469c8dce430865ac8894f9edb9`；`tests/round93_co_quantity_diagnostic.cpp` `8e339616123818b7f8fbf7b2f6b69502f8ec4663efb7ad0c29b4e5126466ce8a`；`CMakeLists.txt` `81314778f2a24a5e504bca2cb8e8caece917c4139be795b3fa2ea2e59866c087`。任一字节后改须重新核相应范围。

数学身份核对：对每个当前已服务的无序站对，源码用 `lo=max(-Y_a,-Y_b)`、`hi=min(C_a-Y_a,C_b-Y_b)`，遍历从 `lo` 到 `hi` 的每个整数并略去零。当前 `Y` 在容量域内，故零在范围内，点数恰为每对 `hi-lo`。重建的原净操作为 `o_i-t`，符号转为互斥取/放，零操作同步删节点；候选保持原车主和剩余站序。每个可表示点调用原 `verifySolution`，它重新检查库存、逐车前缀、返仓载货卸车、删站后旅行、`T+1e-7` 和 `S=0` 约定下的原 `F=G+λP`。接受门为当前已验 `F` 严降超过 `1e-12`，同值按 `(a,b,t)` 排序；不存在 Gini 梯度代理或解析跳点。`exhausted` 只说明**当前数值门槛下该声明邻域**无已验严格改善，不代表精确实数局部最优或完整算法认证。

源码对上轮提出的阻断已修：所有全局截止扫描出口返回空 choice，扫描尾及接纳复验后再检查截止，部分扫描不接纳；诊断读入同时支持原 `result.json/initial_witness.json` 的操作对象和 `writeRound61Witness` 的操作三元数组，并拒绝缺失车辆；原 Evaluator 使用 `int` 累计的前缀载量、总取/放和最终库存先以 `int64` 审计，若候选超出表示域即留原见证、标 `verification_failed`、不标穷尽。`V+1` 也已在检查 `V` 后计算。这个整数域门是避免原 Evaluator 有符号溢出的失败边界，不可把其候选当物理不可行或已完成邻域搜索。`Round93CoQuantityPoint.physical_checked` 和单列拒绝数保留了该区别。

隔离边界核对：新源仅进入 `round93_co_quantity` static target，没有加入 `exact_ebrp_core` 或 `main.cpp` 的正式预设；driver 只做固定见证上的 co 下降，不调用旧 R73/R75/R83，也不提供原问题下界或证书。R88 已冻结 D6 `result.json` 与 E8/S12 `external/initial_witness.json` 均为逐车 `routes`、对象式 `operations`，与 driver 当前读法匹配；输入/见证 SHA、场景和起末原目标进入摘要，最终路线另由原 `VerifiedCandidateStore` 验收并写出。根指定二站微例在代码中保持 `F=.15→.075` 且断言旧 R76/R83 停点；其通过与否仍待真实 C++ G1 构建运行。

后续审计边界：driver 的内部 `wall_seconds` 在写 `summary.json` 之前读取，不能单独称整个进程到退出的费用；G1/G2 使用外层进程收据作完整 wall，保留失败前缀。原有 `verifySolution` 是 binary64 和既定容差标准，有理 oracle 对 `T+1e-7` 等号的结论不能替代真实边界资格。`acceptances.jsonl` 只记 `(pass,a,b,t,F)`；它可由冻结初始见证、源码物化规则和逐次原验证重放，并以最终见证核对，但 G2 前须冻结独立重放器/身份及逐接受复核，不能只据点日志断言实际接纳路线。任何将来正式接线须重新审原 R76/R83 交替势与成本，保持 24+1 启动及完整原问题数值证书路径；本次静审未核任何此类接线。
