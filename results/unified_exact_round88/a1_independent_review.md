# Round 88 A1 constructive-only descent：独立只读代码审查

审查范围：相对 `HEAD=15121fdfe08a5a31eefb38bdc81fae316e611eb6` 的七个已跟踪文件差异，加新增 `tests/round88_constructive_only_cli_test.cmake`；读取的是作者仍在资格阶段的工作树，未构建、未运行测试或 solver、未修改源码。此意见是设计/静态审查，不是冻结版本验收或性能结论。差异约为 112 行新增、19 行删除（另有未跟踪 CLI 测试）。

## 结论与逐项核对

1. **默认 ENS-C 路径保留。** `SolveOptions`/`HgaTgbcOptions` 开关默认 `false`；`HybridGA.h:800` 仅在开关为真时跳过原 24 个随机/构造初始化，随后原追加构造 seed 分支仍执行。R83 预设继续指定 24，`HgaTgbcRunner.cpp` 对追加 seed 仍要求 `pop_size==24`。正常无全程截止中断时，默认仍为 24+1；旧 `Round83ExchangeDescentCliTests` 要求 25 个已完成 seed，新单元测试也要求 25。冻结后应在相同编译和输入下重跑默认 R83 轨迹对照。
2. **单路径复用同一下降与后段。** 新开关仅改变 `initialize_population()` 的成员数，`run_decoded_descent()` 的完整解码、候选枚举、严格改善、穷尽判定及缓存路径没有差异；候选生成未使用 PRNG，因此少掉前 24 个初始化随机抽样不应改变追加 seed 的逻辑下降路径。直接 GA 测试把原第 25 路与单路径逐 pass 比较邻域数、全解码数、跨路线次数、接受状态和目标。`main.cpp` 仍先支付并独立核验 Round73 构造，再进 HGA，随后同一个 Round83 equal-net exchange/physical closure 和完整 VD-P 原问题证明入口；新 CLI 测试要求 closure 穷尽、native proof ledger、严格证书及同一目标。不存在仅输出启发式目标冒充证书的新增路径。
3. **身份与来源。** 正常 `RunConfigSnapshot` 的 `algorithm_preset` 改为 `research-round88-ensc-constructive-only`，保留原始 R83 选项用于既有控制分派；阶段 label、候选 model identity、候选 source、缓存候选 source、紧急非证书 JSON 均显式带 Round88。审查初版曾发现 emergency JSON 与候选证据仍标 R83；作者在本次审查中补了 `effectiveAlgorithmIdentity()` 和来源标签，当前快照已消除该缺口。应在冻结结果中核查 `algorithm_preset`、候选 ledger、phase ledger 和异常 JSON 同时一致。
4. **非法组合保护。** CLI 只允许 R83 ENS-C 预设配新开关；直接 runner 拒绝无 joint seed、非 inter-route 下降和 generation quota；GA 层拒绝无额外 seed/非有限下降。非法布尔值由现有 `parseBoolValue` 抛错。新增 CLI 脚本覆盖正常证书、异常 JSON 身份及“Round88 开关 + 非 R83 预设”的明确拒绝；直接单元测试覆盖 runner 两种非法组合与 GA 缺 seed。
5. **终止、核验、全程截止。** 原下降每次接受需目标改善 `>1e−12`，状态有限；无改善时检查完整声明邻域后 `exhausted`，单 seed 才记 `decoded_descent_complete`。全程截止仍由 `processWorkRemainingSeconds` 传入 GA 的 absolute deadline，构造与物理 closure 也沿原 process deadline；没有新增内部秒/Work 切片。经独立物理验证且目标零时原 `round65_hga_zero_stop` 可合法提前结束，故此情形 `decoded_descent_complete=false` 不能误报为错误或当作漏查的局部最优。新测试没有单独覆盖 A1 的零值早停或 deadline 中断身份；冻结后应补证据或明确沿用已核验旧语义。
6. **测试证据边界。** `round73_constructive_seed_tests.cpp` 的单路径、25 路与实际物理解验证为核心语义测试；`round88_constructive_only_cli_test.cmake` 贯通真实 CLI、closure、native proof 与异常 JSON 身份。现有测试足以发现随机路径误保留、单 seed 未下降、未进入证明等关键错误，但只涉及微型输入，不能证明多实例的 UB/认证时间优势。正式 G3 前仍须按计划做原 ENS 与候选的同配置完整运行及全成本统计。

## 本次审查快照 SHA256

| 文件 | SHA256 |
|---|---|
| `CMakeLists.txt` | `D16586581CAF5BF610455E61220CB427E252AEA0D054054473EBC63A028E4E83` |
| `include/Instance.hpp` | `94EE602A3BBABA8B48ED47A49F6F68C4933CF5AF06AD384063698E1A782A1B21` |
| `include/HgaTgbcRunner.hpp` | `01A0A95FCD6A5D1B23206503C8CC4814B10CDEA243249970F0AA6ECAED222AE8` |
| `include/hga_tgbc/HybridGA.h` | `2AC2233743FFA883FB517C7DF70C5B29BBB420123F8A57D474434C2A6820DC62` |
| `src/main.cpp` | `38B92B0FE2152E371E4116F1E8F2B4DB3CF90D39E483A6E94FC765240F805FD2` |
| `src/HgaTgbcRunner.cpp` | `418FA40968A22196C72EB48879E7BC4A72BB8F7A570FABA99B77814248E5D8A5` |
| `tests/round73_constructive_seed_tests.cpp` | `6821A768266F328C8C404514084749AF79CE9D4D7FDF95A4895224FEE0FAFCC4` |
| `tests/round88_constructive_only_cli_test.cmake` | `C6714E9BAD068553EB4ABE0A3E0717D2F495DC6D0FC6D1B145B4C84A2BC3F9AD` |

作者提交/冻结后需以最终提交 SHA 和上述文件哈希重新比对新增差异，重审 CLI 保护、结果身份、默认 25 路与单路径轨迹，并读取资格测试的实际输出。任何不同于本表的文件内容都不在本次静态结论范围内。
