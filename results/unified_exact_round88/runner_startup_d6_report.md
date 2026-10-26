# Round 88 A1 G2：D6 启动诊断结果

两次预注册的 startup-only 运行均完整退出、物理审计通过，且没有发现 Optimize 调用。原始输入、场景、同一冻结二进制、参数及运行顺序由 `runner_a1_startup_d6/identity.json` 固定；双臂每次都从原始输入独立启动，均获 120 秒完整过程 cap，未注入历史 UB。此次结果只比较启动构造及同样的等净交换闭包，不是 P-GRB 或完整精确算法的运行时间结果。

| D6 臂 | 完成种子 | 下降后、闭包前物理 F | 闭包后物理 UB | 进程墙钟 | 发射前计费 | 离线审计 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 同构建 ENS-C 默认路径 | 25/25 | 0.1600272806044027 | 0.15750980361456166 | 6.078 s | 0.234 s | 0.08159 s |
| A1 构造单种子 | 1/1 | 0.2612388786428369 | 0.17161162683007503 | 0.297 s | 0.235 s | 0.09462 s |

两臂 `decoded_descent_complete=true`、HGA 代数为零、原始 T 物理可行、独立构造前缀 replay 通过、等净交换闭包 replay 通过、闭包 `verification_failed=false`，外层确实收到闭包最终路线。方法都是 `primal-heuristic`、`certificate_scope=primal_heuristic_ub_only`、`strict_certified_original_problem=false`。没有 `external/` exact 模型目录；所有保留 `.log` 均无 `Optimize a model` 记录，审计观测为零 Optimize。原始细节分别见 `runner_a1_startup_d6/raw/01_D6_ENS-C/audit.json` 与 `runner_a1_startup_d6/raw/02_D6_A1/audit.json`，过程退出/耗时见各自 `completion.json`，逐步构造及闭包见各自 `hga.csv.descent.csv`、`hga.csv.joint.csv`、`hga.csv.exchange/`。

A1 这次物理 UB 比 ENS-C 高 `0.01410182321551337`，约 `8.95%`；其启动诊断的进程耗时较短。D6 因而证实单种子并非无损，但不能把这次启动时间比值宣称为完整精确法加速，也不能仅凭本例否决 A1。A1 仍是待 E8/S12 三臂烟测的消融候选；当前没有 G3 性能结论或晋级资格。

双臂进程墙钟合计 `6.375 s`；进程前 admission、资源检查和发射记录合计 `0.469 s`，故记录内运行端到端合计 `6.844 s`。运行结束后的离线物理/轨迹审计合计 `0.17621 s`，另列研究成本；准备、静态验证和人工审查也另列而不伪装为求解节省。没有 watchdog、超 cap、异常退出、审计失败或失败尝试；`runner_a1_startup_d6/runner_startup_completion.json` 记载 `all_valid=true`、`optimizer_calls=0`、失败尝试成本零。目录内 80 个原始/运行记录文件共 324,943 字节，逐文件 SHA256/大小见 `runner_startup_d6_raw_index.json`；没有复制源码或 build。此次进程结束后未再次发射 D6，也未启动 G3。
