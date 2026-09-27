# Round90 原始证据归档适配静态审查

**结论：`round90_archive_lp_g.py` 在限定适配范围内无静态阻断；只能在 rest runner 完全停止并释放资源后，按独立归档授权先 `plan`、审清单、再 `build`。** 本次只读脚本源码，未 import、解析执行、遍历 raw、压缩、构建、求解或操作 Git。Round90 脚本 SHA-256 为 `33fe2b5389ff840b9eaaf00e224648092e58c2851c886fbb3bba3c66805bb9bc`；对照已使用的 Round89 适配脚本 `dd93003357336262313058768ff02166c29f05cfdbca88eabd8df88171d81f11` 与未改的 `round88_archive_evidence.py`。

新路径均落在 `results/unified_exact_round90/`：`runner_lp_g_g3/raw` 输入、独立 plan/index/failure 和 `runner_lp_g_raw_archives` 输出。它把冻结内核的 `RESULTS` 仅重绑至 R90 根，归档条目仍用该根下相对路径。预注册 schema、16 条 `execution_order`、`ENS-C/LP-G` 身份、prepared identity 的 16 launches 和每条 destination 必须一致；summary 必须是 4 至 16 条原顺序前缀，前四烟测已审通过，rest completion 的已完成数、计划数、审计总状态及停止原因需与前缀吻合。失败臂要求其单独失败收据，后续不能出现已运行臂；未运行尾部单列 `not_run_arms`，缺失或空 raw 的已尝试臂也单列。raw 根只能恰好包含本前缀中实际存在的臂，额外目录、孤立失败收据或链接目录均拒绝。

`require_stopped` 同时检查 `active_run.lock` 和 ExactEBRP/Gurobi/build/Round90 runner 等进程，避免与 rest 写入并行。`plan` 和 `build` 都拒绝已有 index/output；`build` 重取 stopped 状态、身份、路径和大小清单，逐文件读取源 SHA，然后以 `xb` 创建 tar.gz，不删除或移动源 raw；中途失败保留已产文件及专门 failure 收据，不自动覆盖重试。冻结内核对源文件/链接做检查，按 36 MiB 原始分包（单个超大文件独立包），成包须小于 45 MiB，再以流式 tar 读取逐成员核名称、数量、原始长度和 SHA-256。压缩、源 hash、包 hash、流式验证各项耗时和最终 archive index 分开记录。顶层 runner ledger 未混入这些 raw 包，须另行归档提交。

静态审查不能确认目前正在写的 raw 完整或归档实际大小；归档执行时必须以最终停止后的 plan 和原始收据为准。冻结内核的 plan 记录路径/大小，最终 build 才记录源内容 SHA；若相同大小的源文件在两阶段之间变动，plan 本身不能证明字节不变，但最终 index 与压缩包会绑定并逐成员验证 build 当时的实际字节。该既有口径应如实描述，不能把 plan 称为先验内容哈希冻结。
