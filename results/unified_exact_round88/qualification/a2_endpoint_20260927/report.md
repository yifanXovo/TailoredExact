# Round88 A2 endpoint 资格记录（未运行完整三例探针）

资格结论：**基础资格通过，可交 root 验收；D6/E8/S12 整例 A2 探针仍未准入、未运行。** 本轮只执行标准库微测、Windows 进程树微验收和**固定 E8 初始见证的一次**冻结 C++ `incumbent-import-test`。开始和结束均检查无遗留 `round88_quantity`/ExactEBRP 相关进程，结束释放独占计算槽。未改冻结 C++、A1 runner、flow 算法、probe 算法；无 Git 操作。

环境：`D:/msys64/ucrt64/bin/python.exe`，Python `3.12.7`，SHA256 `abf7f61b2f9106470d2fe1f3407084b3ab2ff26bb20d7c41abbfb104a8f6fd48`。冻结 C++ `build/research/round88-a1/ExactEBRP.exe` SHA `23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693`。flow 原型 SHA `fdbe04bdc7b933397aac3ec4fa9d9f0b5adf99c8550c98d14e96ce89db43328d`，probe 适配层 SHA `6a06a03212dc5da954be57e7c81b5a0f67c77bea592720955dc9c2b8e3c9c77c`，执行前后均未改变。所有命令工作目录为 `E:/codes/ExactEBRP`；以下墙钟为命令进程外 PowerShell 秒表，脚本内部子阶段另列。

| 顺序 | 完整发射命令 | 结果与成本 | 原始证据 |
| --- | --- | --- | --- |
| 1 | `D:/msys64/ucrt64/bin/python.exe -B tests/round88_quantity_flow_test.py` | 初次 11 项中 1 项失败，exit 1，0.280818s | [初次日志](01_flow_tests.log)、[成本](01_flow_cost.txt) |
| 2 | 同上，修复测试断言后重跑 | **11/11 通过**，含 96 组两站独立枚举线性 oracle/残量势证书交叉，exit 0，0.281806s；unittest 内部 0.031s | [重跑日志](02_flow_tests_repaired.log)、[成本](02_flow_cost.txt) |
| 3 | `D:/msys64/ucrt64/bin/python.exe -B tests/round88_quantity_probe_test.py` | **10/10 通过**，exit 0，0.716770s；unittest 内部 0.009s | [日志](03_probe_tests.log)、[成本](03_probe_cost.txt) |
| 4 | `D:/msys64/ucrt64/bin/python.exe -B tests/round88_quantity_job_os_test.py` | **真实 Win32 Job/ready/子进程树通过**，exit 0，0.475076s | [日志](04_win32_job_os.log)、[成本](04_job_cost.txt) |
| 5 | `D:/msys64/ucrt64/bin/python.exe -B scripts/round88_quantity_import_qualify.py results/unified_exact_round88/qualification/a2_endpoint_20260927/05_e8_import` | **一次 E8 importer 通过**，exit 0，完整外部 0.276025s；脚本内部全程 0.056697s，C++ 调用 0.028948s | [控制台](05_e8_import_console.log)、[命令](05_e8_import/command.json)、[C++ 原回执](05_e8_import/cpp_result.json)、[资格摘要](05_e8_import/qualification.json)、[成本](05_e8_import_cost.txt) |

初次 flow 失败不是模型错误：测试将证书的整数成本误比为 `Σg_i(Y_i−Y_i_current)`，而网络取/放弧成本天然表示 `Σg_i(Y_i−b_i)`；`_linear_oracle` 自身和独立网络弧清单检查也采用后者。仅把测试断言修成相对初存的独立公式，原 flow 脚本未变；初次失败与修复后日志均保留。修复后测试 SHA `bfed7d572817ebb4832cf28f43a816eae1e41412bd6903283838be8048ae10b5`。

probe 10 项覆盖 points 优先/depot/1-based/空车映射、C++ 完整回执及失败 fallback、篡改路线/操作/库存/目标/场景拒绝、极窄预算 floor 不一致、非 metric 删站内部拒绝、primitive 整段严格改进/tie、预检逾限不发子进程、父进程已退出仍关闭 Job。probe 测试 SHA `3e0e3ec890d5135665a8f7f2ef892c2f9261b96383576f2267f9c5b4d2a26b11`。

真实 Windows 微验收的 fixture SHA `f74663207cb404fbc7830b44e362f946c64435fbbc0d95dfa9d720e439ddaae2`：父 Python 被 Job 收纳后，ready 前子进程未出现；ready 后子进程 pid 22904 存活，父进程 exit 0；关闭 Job 后同一子进程不再活动。fixture 在异常路径另有 `taskkill` 兜底，日志无兜底事件。它验证本机 kill-on-close/继承机制，未发射 ExactEBRP solver。

E8 单次进口脚本 SHA `241f1d1d714ce0532a1db0a0de0243be149901b8c78504dfc1a07591d0d0ffc1`，先核固定输入/witness/binary/flow SHA，保持历史路线并核序列化往返，真实发射 `command.json` 中完整参数。C++ exit 0、`diagnostic_complete`、`incumbent_import_verified=true`、`incumbent_source=incumbent-json`，完整物理/原目标 flags 和空 errors；适配层独立核对回返车辆/节点/取送、含 depot 的最终库存、源/结果路径、T/服务秒数、有限且一致的 F/G/P、与历史初始目标差 ≤ 1e−7。E8 站点最终库存为 `[17,14,21,24,31,16,11,10,12,16,16,14]`，C++ 实际旅行得预算 `[19,0,0]`，与 Python 重建 floor 相同，当前点也通过名义与内部物理检查。原 C++ 回执 SHA `fac774256d239242cd695b48763af41352447667bb0154f5d738fc89fc881fda`。此处只做一次 incumbent import/verify，没有启动原 ENS-C、A2 完整循环或三例批次。

剩余边界：三例真实完整探针的 120s 各一次准入须由 root 单独签署，且依其排他计算槽执行；本资格不证明 A2 有改进、不证明端到端 ENS 提速。输出中的 Python 物理预筛可能保守漏掉 C++ 边界可行点，因此完整探针的 `no_verified_improvement` 只能解释为该固定线/本适配域无验收改善。所有旧失败与本轮新代码/日志均保留。
