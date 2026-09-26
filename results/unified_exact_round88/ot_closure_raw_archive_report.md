# Round88 OT closure 九臂原始证据归档

**完成并逐成员验真。** 仅覆盖 `ot_closure_diagnostic_001` 内九个预注册臂及其目录顶层 20 份批次账本；未扫描、重压或更改任何既有 raw archive/index。原目录、文件、旧包与旧 manifest 均保留。源文件完整清单和每件 SHA256/字节数在 [plan](ot_closure_raw_plan.json)，归档与验回明细在 [index](ot_closure_raw_index.json)。

总计 **1,172 个源文件、1,145,438,949 字节**；十个源组按稳定相对路径分为 **37 个独立 tar.gz**，总 **160,012,329 字节**，最大 **9,531,682 字节**，严格小于 45 MiB（47,185,920 字节）。三份 47.8/49.1/59.5 MB 的 `added_rows.jsonl` 各独立成包，压后 7.67/6.98/9.53 MB。每包的 `source_group`、`part_number/count` 和 `groups[].files[]` 在索引中；重组时从 `results/unified_exact_round88` 作为成员根，解压同一臂的全部 part，再解压 `batch_ledger.tar.gz`。各 member 路径无重叠、遗漏或越界。

归档使用未修改的 [冻结 tar/hash 内核](../../scripts/round88_archive_evidence.py)（SHA256 `d357b232ceb8e14e94cbf9629d57d9f18bc2f60b1b682865042c4cdd622319f0`）和只为本次源组/超大单件分片写的 [驱动](../../scripts/round88_archive_ot_closure.py)（SHA256 `2ee2c6812ca2e9ed84d09b62449bf4e944427aeddf2af780dc15a485d066bb89`）。先单独落盘含源 SHA 的计划，再以原文件尺寸与 SHA 复核计划，逐包先核源、创建 gzip tar、核 archive SHA，随后用 `r|gz` 从成品**逐成员读出、重算字节数与 SHA**。37 包全部为 `all_member_sha256_size_equal_source`；验回 1,172 件、1,145,438,949 字节，与源清单完全一致。包括源目录下全部现存 `optimizer.log`（222）、`primal.json`（216）、`inflight.json`（9）、`supervision.json`（9）、九份外层收据和 `added_rows.jsonl`。本次目录没有单独以 `candidate` 命名的文件；相应生成行/原始状态证据已随源文件全量归档。

成本与空间见 [机器可读收据](ot_closure_archive_receipt.json)：独立 `plan` 命令外层 4.516 s；`build` 命令外层 **62.286 s**，脚本内索引落盘前 61.879 s，其中逐组源 SHA 1.290 s、压缩 56.997 s、archive SHA 0.323 s、逐成员流式验回 3.260 s。原始进程输出分别在 `ot_closure_plan.log`、`ot_closure_build.log`，外部启动至退出记录在 `ot_closure_plan_outer.json`、`ot_closure_build_outer.json`。计划 SHA256 `2f42c7729b3111981d59e2f34f1860dafb976be5c14d4076fb26e20b82d50f94`，索引 SHA256 `3b943eed16fe7509af3f2e5ac3a738c9a79a1992ea1f0d23e3e46457609fb5bd`，两阶段 exit 0，未产生失败收据。E 盘从计划时可用 106,163,666,944 字节，到构建索引前 106,003,247,104 字节，写收据后约 106,002,931,712 字节。

应由 root 提交的**精确逐文件路径**在 [OT 归档清单](ot_closure_archive_git_files.txt)：37 包、计划、索引、收据、本报告、两份过程日志、两份外部成本 JSON、重现驱动及清单自身。原 1.145 GB raw 不因本次归档而删除或移动。A2/composite 资格和三例探针原始文件另外只有三个小作用域，合计 **94 文件、1,476,326 字节**；含被 Git 忽略的 `.log` 的完整直接提交清单在 [A2/composite 清单](a2_composite_direct_commit_files.txt)，不另压缩。其他既有证据无重复入包。本归档不涉及求解、构建或新测试。

整理提交清单时首条只读 PowerShell 命令存在括号语法错误，未执行任何文件操作；更正后清单 47/95 条均解析为现存文件。此失败不影响已完成的 37 包流式验真或计划/构建成本。

Root 独立复核：37 个压缩包的 SHA256/大小均与索引相同；逐包验证状态、总文件数 1,172、源字节 1,145,438,949、压缩字节 160,012,329、成员路径唯一性/作用域与单包限制全部通过。此处独立核的是成品包身份与索引一致性；逐成员真读回由上述归档过程完成，未重复运行求解或覆盖源文件。
