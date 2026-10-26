# Round88 A1 G3 rest 18 臂原始证据归档

已完成并验证。归档只覆盖 `runner_a1_g3/raw/07_D3_ENS-C` 至 `24_F6_A1` 的**18 个新臂**，外加同一 runner 的 13 个必要小账本（`identity/preflight/processes/summary/runtime_status/rest_completion/rest_lease` 与 D3/C2/D7/U6/F5/F6 的 cross-arm JSON）。01–06 烟测 raw 不在本索引中；既存 `runner_smoke_raw.tar.gz`（本次只读 SHA256 `c091144278928c7f1c350f439b924b1a7417493de59e94e8a217c13d5f0d0113`）未覆盖。原 raw、目录及旧归档均保留。

在压缩前单独落盘的 [准确目录/文件/字节计划](runner_rest_raw_plan.json)为 **34,147 个源文件、667,716,269 字节**，18 臂加账本共 19 个源组。文件按稳定路径顺序预分片：每片原始内容 ≤36 MiB，单个大臂的 part01/02/03 在 [索引](runner_rest_raw_index.json)中标明 `source_group`、`part_number/count` 与所有成员。全部 33 个 tar.gz 的成员路径相对 `results/unified_exact_round88`；重组时在此根目录下解压**同一臂的全部 part**，再解压 `rest_ledgers`，各成员无重叠。压缩总计 **99,254,996 字节**，最大单包 **5,038,253 字节**，全部低于 45 MiB 目标。

每个源文件的相对路径、字节数与 SHA256 均逐项写在 `runner_rest_raw_index.json` 的 `groups[].files[]`。每包先核源文件，再创建 tar.gz、核归档 SHA256，最后以 `r|gz` **从归档流读取每个成员**重算字节数与 SHA256，拒绝额外/缺失/重复/链接成员；33 包全部 `all_member_sha256_size_equal_source`，实际验证成员总数和字节数与源清单相等。任何源文件都未移动或删除。

成本：压缩构建与逐文件验证的脚本内墙钟 **65.663s**（源 SHA 15.244s、压缩 46.050s、压缩包 SHA 0.241s、流验证 4.109s；余量为清单/调度）；[外层完整命令计时](runner_rest_archive_external_cost.json) **70.056s**，exit 0；[逐包过程日志](runner_rest_archive_build.log)保留 33 条成功记录。预盘点单独约 4.175s，不并入 build。源码脚本 [round88_archive_evidence.py](../../scripts/round88_archive_evidence.py)以 `plan runner_rest` 后 `build runner_rest` 两阶段执行。可提交的逐文件精确路径见 [提交文件清单](round88_archive_git_files.txt)；其中列出的本报告、索引、计划、33 包、日志和成本均为新增证据，不要求提交原 raw。
