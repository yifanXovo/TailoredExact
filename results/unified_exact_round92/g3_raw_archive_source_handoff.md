# R92 G3 已付前缀原始证据归档：源码交接，尚未执行

此适配器只准备归档 `runner_handling_g3/raw/01_*` 至 `12_*` 的十二个已付完整运行目录。预注册共十六臂：smoke 四臂、rest 八臂已完成，`F5/ENS-C, F5/H-ACT, F6/H-ACT, F6/ENS-C` 未启动。rest 外层 exit 1 来自已记录的 U6 `severe_open_gap_signal` 研究停批；八次运行本身均有完成与物理审计收据。该出口不可当作第十三个失败求解，也不可强求 rest 12/12 才能保存已有证据。smoke 四行前缀受 `runner_smoke_gate.json` SHA 绑定，来源提交 `21273f691`。

适配器是 [round92_archive_handling_g3.py](../../scripts/round92_archive_handling_g3.py)，复用 SHA256 `d357b232ceb8e14e94cbf9629d57d9f18bc2f60b1b682865042c4cdd622319f0` 的冻结 `scripts/round88_archive_evidence.py`。执行时核对预注册十六臂顺序与 4+12 阶段、资格 gate、准备身份和两阶段 root lease、两份 completion/外层 receipt、U6 风险停批与最终 summary SHA、smoke 首四行 SHA、十二个 launch/destination/完成/audit/result、六对跨臂物理界。ENS-C 须无 R92 行证据；H-ACT 须有 v2 模型代数、scope、B/行数、当前 canonical 模型证明及 ledger SHA。`raw/` 下有任何遗漏或额外目录即拒绝。历史被覆写模型字节的不可用性维持原审计口径，不补造。

将来只有根签有限计算/I-O 槽、独立证据审查无身份/正确性阻断且确认没有活动 runner/solver/build 后，才可按顺序**各执行一次**：

```text
D:/msys64/ucrt64/bin/python.exe -B scripts/round92_archive_handling_g3.py plan
D:/msys64/ucrt64/bin/python.exe -B scripts/round92_archive_handling_g3.py check
D:/msys64/ucrt64/bin/python.exe -B scripts/round92_archive_handling_g3.py build
```

每条命令都须有独立外层 started/stdout/stderr/exit/墙钟收据；失败即停，保留失败和已生成前缀，不自动修改/重试。plan、check 重查 inventory 与身份；build 从源读取每文件 SHA/字节、创建分包、实际流式读回每个 tar member 复核 SHA/字节并核整包 SHA，单包严格 `<45 MiB`。原 `raw` 一律保留。根检查 plan 的 12 个源组、F5/F6 四项 `not_run`、所有实际目录、大小与分包后，才进入 check/build。索引对外部完整成本之外单列内部 source-hash、压缩、包 SHA 与成员验真时长，不能相加当额外运行成本。后续 U6 seed1/2 风险复核不在本次归档。

拟纳入 Git 的小文件（归档执行后再加 plan/check/index、每包及三命令外层收据；**不直接 add raw**）：

- `scripts/round92_archive_handling_g3.py`
- `results/unified_exact_round92/g3_raw_archive_source_handoff.md`
- `results/unified_exact_round92/preregistration_g3.json`
- `results/unified_exact_round92/g3_qualification_gate.json`
- `results/unified_exact_round92/g3_smoke_outer_001.started.json`, `.receipt.json`, `.stdout.log`, `.stderr.log`
- `results/unified_exact_round92/g3_rest_outer_001.started.json`, `.receipt.json`, `.stdout.log`, `.stderr.log`
- `results/unified_exact_round92/g3_smoke_postflight_observation.json`, `g3_rest_postflight_receipt.json`
- `results/unified_exact_round92/g3_smoke_report.md`, `g3_rest_report.md`, `g3_smoke_independent_review.md`, `g3_rest_independent_review.md`
- `results/unified_exact_round92/runner_handling_g3/identity.json`, `preflight.json`, `processes.jsonl`, `summary.jsonl`, `runtime_status.json`
- `results/unified_exact_round92/runner_handling_g3/runner_smoke_completion.json`, `runner_smoke_gate.json`, `runner_smoke_lease.json`, `runner_rest_completion.json`, `runner_rest_lease.json`, `runner_rest_risk_stop.json`
- `results/unified_exact_round92/runner_handling_g3/runner_cross_arm_{E8,S12,D3,C2,D7,U6}.json`（逐项展开精确 staging）
- 执行后 `results/unified_exact_round92/runner_handling_g3_raw_{plan,check,index}.json` 与 `runner_handling_g3_raw_archives/*.tar.gz`，以及另存的外层命令收据/日志；若失败还包括 `runner_handling_g3_raw_failure.json`。

这是一份 source-only 待审草稿：尚未调用 plan/check/build，未枚举或哈希大 raw，包数/字节数/包 SHA/真实归档成本均待批准执行后填写。归档只是保存已付证据，不表示 H-ACT 晋升。
