# Round88 OT B1 cross 准备尝试与行库归档

已完成并验证。归档覆盖 `ot_b1_cross_preparation`（v1）、`_v2`、`_v3`、`_v4` **四份原目录全部文件**，含四版各自 `row_bank.json`、manifest，以及 v3/v4 的 `preparation_timing.json`；另独立存放 4 份准备合同/资格/独立审查/准入小账。v1–v3 是保留的加严前尝试，不能替代 v4 执行身份；不删除、不覆盖任一原目录或既有 OT 归档。

压缩前 [准确计划](cross_prep_plan.json)：**14 个源文件、21,079,675 字节**，五个源组各自一个 tar.gz。压缩合计 **3,665,672 字节**，最大单包 **914,862 字节**，均低于 45 MiB。包内路径相对 `results/unified_exact_round88`；在该根目录解压五包可复原原四目录与四份小账，组间无重叠。[索引](cross_prep_index.json)逐源文件保存相对路径、原字节数、SHA256，逐包保存 SHA256 与耗时；从五份 tar.gz 的流逐成员重算 SHA256/大小并与源清单完全相等，拒绝缺失、额外、重复或非普通文件。

准备成本与失败证据原样保留：v3 `preparation_timing.json` 记行库写完 **25.4603011s**；冻结 v4 记至行库写完 **25.2090177s**，另据 [既存资格记录](ot_qualification_b1_cross.md)的外部命令计时为 **25.4755013s**（含随后 timing/manifest/退出），零 Optimize。v1/v2 目录没有单独 timing 文件，故不补造成本；其行库与 manifest 原字节均在包内，可检验其与 v4 的差异。四版修订背景在 [独立审查](ot_b1_cross_independent_review.md)与合同中保留。

本次**归档本身**的脚本内墙钟 **2.655s**（源 SHA 0.022s、压缩 2.544s、包 SHA 0.024s、流验证 0.064s）；[外层完整计时](cross_prep_archive_external_cost.json) **2.848s**、exit 0；[逐包日志](cross_prep_archive_build.log)留存。预盘点单独约 0.085s。使用 [同一归档脚本](../../scripts/round88_archive_evidence.py)的 `plan cross_prep` 与 `build cross_prep`。可提交的精确路径见 [提交文件清单](round88_archive_git_files.txt)；不要求重复提交未改原准备目录。
