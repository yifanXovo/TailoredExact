# Round88 A2 固定见证 endpoint 三例离线诊断

依 [A2 准入](../a2_endpoint_admission.md)，在排他计算槽内按 **D6 → E8 → S12** 各发射一次、各设整例 120s 外部截止。三例均 `diagnostic_completed`、未超时，冻结输入/见证/flow/适配器/二进制在监督前后 SHA 一致；六次原 C++ `incumbent-import-test` 回执均为 `diagnostic_complete`、导入和原物理复核成功，无候选身份错误。三例都只做 1 个完整流 oracle 轮、primitive `gcd=1` 的 1 个非起点整数候选、0 个内部物理拒绝，候选经 C++ 复核后原 F 均变差，故各以 `no_verified_improvement` 停止，终点等于起点。**这只否定本次固定模板梯度线上的严降点，不证明完整数量邻域或原问题最优，也未把历史见证导入正式 ENS-C。**

实际完整发射命令（工作目录 `E:/codes/ExactEBRP`；每个输出目录在发射前不存在；`D:/msys64/ucrt64/bin/python.exe` SHA `abf7f61b2f9106470d2fe1f3407084b3ab2ff26bb20d7c41abbfb104a8f6fd48`）：

```powershell
D:/msys64/ucrt64/bin/python.exe -B scripts/round88_quantity_probe.py supervise --case D6 --out-dir results/unified_exact_round88/a2_endpoint_diagnostic_001/D6 --whole-process-limit-seconds 120
D:/msys64/ucrt64/bin/python.exe -B scripts/round88_quantity_probe.py supervise --case E8 --out-dir results/unified_exact_round88/a2_endpoint_diagnostic_001/E8 --whole-process-limit-seconds 120
D:/msys64/ucrt64/bin/python.exe -B scripts/round88_quantity_probe.py supervise --case S12 --out-dir results/unified_exact_round88/a2_endpoint_diagnostic_001/S12 --whole-process-limit-seconds 120
```

| 例 | 起点 F = 终点 F（原 C++） | 非起点候选 F（原 C++） | 名义预算 / 负环增广 | 流 oracle / C++ 两次调用 / 诊断子进程 / 监督边界 / **外部启动至退出** 秒 |
| --- | ---: | ---: | --- | --- |
| D6 | 0.15750980361456174 | 1.4512353160750249 | `[112,113,113]` / 21 | 0.013998 / 0.030056+0.030050 / 0.154926 / 0.293036 / **0.493882** |
| E8 | 0.022295597484276734 | 0.49467702409675396 | `[19,0,0]` / 1 | 0.000232 / 0.030193+0.028572 / 0.124881 / 0.269894 / **0.492494** |
| S12 | 0.05856397312578515 | 0.6926015180204221 | `[62]` / 6 | 0.000936 / 0.029238+0.029489 / 0.124132 / 0.254630 / **0.469684** |

表中流 oracle、C++、子进程及监督是**嵌套**计时，不可相加为总成本；只有末列含外部 Python 启动至退出、预检、日志与结束序列化。每例 C++ 基线及候选分别付费，没有复用既存 E8 资格导入成本。每例 `rounds[0]` 保留全部梯度、线性差、整数成本尺度、原弧流和残量势证书，`events.jsonl` 保存逐点决策与调用耗时。线性差在三例均为负，但原 F 在具体整数候选上升；这表明局部线性方向在这三个固定点未转化为可接受原目标下降。由于 `gcd=1`，本轮没有其它内部整数点；各点均通过 Python 物理门槛，且其 C++ 回执原物理可行。

峰值内存观测：外层每 50ms 抽样的监督 Python `PeakWorkingSet64` 最大分别为 D6 **27,639,808 B**、E8 **27,947,008 B**、S12 **28,131,328 B**；抽样未撞到约 30ms 的 C++ 子进程，记录的 C++ 样本为 0，**不代表 C++ 零内存或整棵进程树的真实峰值**。原 C++ 结果字段 `memory_peak_estimate_mb` 是内部估算而非进程工作集，不与上述抽样混称。此限度影响内存成本解释，不影响六个原验证回执与 F 比较。

原始文件：每例目录 `result.json` 为完整循环及证书，`supervision.json` 为状态/前后哈希/截止，`events.jsonl` 为逐调用账，`candidates/` 下各有 `candidate_00000` 起点及 `candidate_00001` 线候选的输入 JSON、原 C++ 结果 JSON、stdout/stderr；父目录 `<CASE>.outer_launch.json`、`.outer.stdout.txt`、`.outer.stderr.txt` 为外部墙钟、抽样内存和进程退出码。[完整逐文件 SHA/字节清单](file_manifest.csv)登记了报告落盘前的 51 个原始文件，总计 591,395 字节；报告自身后续另计。无失败重试、阈值调整、输入替换、建模改动、源码改动或 Git 写入。结束时检查无相关 Python、ExactEBRP、solver/build 进程，计算槽释放给 root 调度。
