# A2 固定路线数量 oracle：三例离线 endpoint 探针接入合同

状态：**只读合同，未写适配器，未运行脚本、测试、构建或探针**。仅在 [A2 微型资格](E:/codes/ExactEBRP/results/unified_exact_round88/a2_quantity_flow_prototype.md) 实际通过、独立审查和计算槽位准入后执行。历史路线只作为离线诊断输入，不进入正式 ENS-C/A1 求解或证明。

## 固定样本及身份

预选顺序为 D6、E8、S12；它们分别是已完成的 D6 启动诊断与 G3 的 E8/S12 smoke ENS-C 臂，选择依据是**角色和已验证、可重读的原始见证格式**，不是 A2 是否能改善，也不在看到 A2 输出后换例。D6 取 startup-only 的最终返回路线；E8/S12 取同一 ENS-C 运行首次已验证的 `external/initial_witness.json`。S12 初始目标与终点相同，仍保留为预选边界例，不据此删去。

| 例与来源字节 | 原输入 SHA256；场景 | 已留存的物理依据 |
| --- | --- | --- |
| [D6 ENS-C result.json](E:/codes/ExactEBRP/results/unified_exact_round88/runner_a1_startup_d6/raw/01_D6_ENS-C/result.json)，SHA256 `a8939cae620b6cdf6d20e3d2f957981bbc5144f9157b26dd5dbb5cfc91eb9c3c` | `070c2c1413840a09a264d238bdfa320ef76d293a45cab919095851afdea8c01d`；V30/M3/Q30，T=18000，取/放各60秒，λ=0.15 | [audit.json](E:/codes/ExactEBRP/results/unified_exact_round88/runner_a1_startup_d6/raw/01_D6_ENS-C/audit.json) `passed=true`、原 T 可行；C++ `verification.feasible=true`，F=0.15750980361456174；启动路径 0 Optimize。 |
| [E8 ENS-C initial_witness.json](E:/codes/ExactEBRP/results/unified_exact_round88/runner_a1_g3/raw/02_E8_ENS-C/external/initial_witness.json)，SHA256 `70534fd162bff80ad50210ad94a02a2e0e7f6c6efafd67e58a3dea32ac1faea3` | `587737b9d000c1712220232a0fe957073f1f03ac649a63a4775abd9166603acd`；V12/M3/Q30，T=3600，取/放各60秒，λ=0.15 | [audit.json](E:/codes/ExactEBRP/results/unified_exact_round88/runner_a1_g3/raw/02_E8_ENS-C/audit.json) 首个 `same_run_verified_startup`、原 T 可行，F≈0.022295597484276727；最终结果另有更优见证，不能把它混作本探针起点。 |
| [S12 ENS-C initial_witness.json](E:/codes/ExactEBRP/results/unified_exact_round88/runner_a1_g3/raw/05_S12_ENS-C/external/initial_witness.json)，SHA256 `af1a591e03c65fd81b96c4fe52b92978f09e34b9a2c2108ff807fc838225fd4b` | `060ee6366b2277c8427675e1a1484de7db10d2ef82a64d4e2ffa6e4695b7b626`；V12/M1/Q30，T=10800，取/放各60秒，λ=0.15 | [audit.json](E:/codes/ExactEBRP/results/unified_exact_round88/runner_a1_g3/raw/05_S12_ENS-C/audit.json) 首个 `same_run_verified_startup`、原 T 可行，F≈0.05856397312578515。 |

三例均来自冻结 A1 二进制 SHA256 `23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693`，每例的输入、命令和场景可由 `runner_a1_startup_d6/identity.json`、`runner_a1_g3/identity.json` 对照。此合同未替代执行时的文件哈希闸门。

## 读取与映射

原 witness 的 `routes[]` 逐车含 `vehicle`（0-based）、`nodes=[0,站号…,0]` 与 `operations=[{station,pickup,drop}]`，站号是 **1-based**；空车用 `[0,0]` 与空操作。D6 `result.json` 还含 C++ `verification.final_inventories/G/P/objective/route_duration`；E8/S12 初始 JSON 仅有 `objective,routes`，须通过下述 C++ 入口重新获取当前点完整验证，而不能从最终 `result.json` 借用其库存/目标。映射到 [Python 原型](E:/codes/ExactEBRP/scripts/round88_quantity_flow.py) 时，访问站号减一；`initial/capacities/target/weights` 的 **0 号 depot 哨兵不进入 S、H、P**。每站库存 `Y_i=b_i−pickup_i+drop_i`，未访问站保持 `b_i`；每车保持原分配与相对顺序，允许候选操作归零后删该站，不新插站或换车。反向序列化时把站索引加一，非零净取/放互斥，原顺序保留，空车完整写出。

实例原字节首行给 V/M/`Q_k`，各行给初存、容量、正目标和权重；读取必须对照 [Parser.cpp:133](E:/codes/ExactEBRP/src/Parser.cpp:133) 的语义：有完整 `points` 时**优先从坐标按 1.5 速度重建距离**，即使文本另有 `distances`；遗留权重最大值 10 的缩放也不可漏。T、取/放秒数及 λ 来自上表身份，不从问题名猜测。Python `Fraction` 梯度对已解析数值精确，不能声称与 C++ `sqrt`/double 的每一步舍入位同；完整模板旅行和预算 floor 若靠近整数门槛，必须保守判为 `domain_uncertain` 或借只读 C++ 解析实例导出核实，不能放宽 K。三例解析后的距离、`b,C,D,w,Q,T`、起点路段、全站库存与 C++ 当前验证要一致。原问题目标由 [Result.cpp:109](E:/codes/ExactEBRP/src/Result.cpp:109) 用全部 V 站的 `H/(V S)+λP`（S=0 时 G=0）定义。

## 必需的原 C++ 复核

现有 CLI **可以逐份复核任意同格式 route JSON**：`src/main.cpp:5247–5282` 的 `loadRoutesFromResultJson` 读取 `routes` 并补齐缺失空车；`src/main.cpp:9908–9973` 的 `incumbent-import-test` 用 [Evaluator.cpp:24](E:/codes/ExactEBRP/src/Evaluator.cpp:24) 的 `verifySolution(instance,routes,lambda)` 重算原库存、负载、删站后旅行、载货返库服务、G/P/F；`src/main.cpp:19828` 分派该诊断方法。未来适配器对**起点及每个整数 line 候选**在独立临时 JSON 中写 `{"routes":[...]}`，只调用冻结二进制的 `--method incumbent-import-test --input <原输入> --T <原T> --pickup-time 60 --drop-time 60 --lambda 0.15 --incumbent-json <单候选.json> --incumbent-format route_json --out <单候选结果.json>`，不指定会运行 ENS 的 preset 或其它外部 incumbent。记录每次发射、退出码、二进制/输入/候选 SHA、墙钟与原始结果；每次重新解析实例及内置 malformed-witness 自检也须计入成本。**只有 `incumbent_import_verified=true` 且结果中该候选 `verification.feasible=true`、`errors=[]`、`original_objective_recomputed=true` 才使用其 `verification.objective` 严格比较**；失败时诊断器可能退回空路线，其 `verification.feasible` 单独为真并不代表候选通过。Python 的 Fraction 目标、既存 `analyze_round61.py physical` 和 startup `offline-replay` 只作交叉检查，绝不替代此 C++ 结果或充当改进验收。

## 一次完整探针与边界

待适配器单独审查/资格后，固定顺序对三例**各运行一次**离线完整过程：核身份与起点 C++ 复核 → 在当前固定路线形成名义完整模板预算与全站梯度 → 整数负残量环 oracle 到无负环证书 → primitive 段的全部 `0…gcd` 整数点逐一由上述 C++ 原验证 → 取严格原 F 最佳改善并删零站 → 以新验证路线重建模板，重复至 `no_gradient_at_zero`、`no_direction` 或这条线 `no_verified_improvement`。无内部秒数、Work、轮数或按实例选型；相等目标不接受。每例统一**外部整进程 120 秒**研究截止，含解析、图构建、所有候选 C++ 子进程、证书、日志写入及退出，超时保留 `unknown`、已付成本与中途原始证据，不自动扩时/重试。三例单次顺序且独占计算槽位；当前合同并未批准执行。

每例记录候选/验证次数、全站初终 F/G/P、每车起终旅行/操作/总时间与载货返库、线性最优值和无负环整数/势证书、gcd/整段点数、拒绝原因、逐段/全过程墙钟、峰值内存、任何 `S=0`/tie/零方向/名义预算边界、非 metric 或舍入不确定。把输入/见证解析、首次与每次 C++ 验证、负环与线搜索、结果写入都计费；不把历史 ENS-C 启动或已有 witness 验证当免费算法成本。验证候选的 `F` 必须严格低于同次 C++ 起点 `F` 才是改善；E8/S12 可能处于接近已知最优状态，未改善不代表邻域穷尽。此过程只测固定路由联合数量机制，不继承历史最优解为正式算法起点，也不构成端到端 ENS 提速或全局证明。
