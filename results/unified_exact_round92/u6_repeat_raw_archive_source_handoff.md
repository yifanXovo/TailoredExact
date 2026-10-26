# R92 U6 seed1/2 四臂归档：仅源码交接

适配器 [round92_archive_u6_repeat.py](../../scripts/round92_archive_u6_repeat.py)只枚举 `runner_u6_repeat/seed_1/raw/01_U6_ENS-C`、`02_U6_H-ACT` 与 `seed_2/raw/01_U6_H-ACT`、`02_U6_ENS-C` 四个新付费目录；旧 seed0 目录 `runner_handling_g3/raw/11_U6_H-ACT`、`12_U6_ENS-C` 已在 G3 归档中，不重复打包。root 尚未签本次归档 plan/check/build，本交接没有执行压缩或扫描大 raw。

执行时先核冻结预注册与原 G3 runner/prereg/gate SHA、四个 global launch（seed 1/2、各自本地编号和目录）、准备身份、唯一 run lease、4/4 无失败 completion、postflight、外层命令 exit0、top summary 的 `seed + record + native_parameter_evidence` 结构。每个 top `record` 去掉新增 seed 后须与对应 seed 局部 summary 原行逐字段相同；读回 native seed 必须是 1/2，`result.json` SHA 与 readback 相同。四个 completion/audit/result、物理界和行账必须一致；ENS-C 无 R92 ledger，H-ACT 必有 v2 `proof_version`、scope、row/B 身份、当前 canonical LP 与 ledger SHA。两份 seed 内跨臂收据分别须通过；风险信号 SHA 与下述**全局**原始 summary 前缀一致。全局三 seed 统计仅引用旧 seed0，不复制它的 raw。目录多出或缺少任何新 raw 即停止。

两份 seed 风险收据的 `summary_sha256` 实际绑定的是**全局** `runner_u6_repeat/summary.jsonl` 原始字节的前 2 行、前 4 行（保留原换行），不是 seed 局部 summary 的 SHA。适配器逐行读取并要求恰好四个完整换行行，再各自核原始前缀 SHA；局部 summary 只按记录与 top `record` 对照。此处在 root 静态审查中修正，未产生失败归档尝试或成本。

独立 root 许可且计算/I-O 槽无 solver/build/runner 后，未来命令按 **plan→check→build 各恰好一次**：

```text
D:/msys64/ucrt64/bin/python.exe -B scripts/round92_archive_u6_repeat.py plan
D:/msys64/ucrt64/bin/python.exe -B scripts/round92_archive_u6_repeat.py check
D:/msys64/ucrt64/bin/python.exe -B scripts/round92_archive_u6_repeat.py build
```

每条另存完整外层 started/stdout/stderr/exit/墙钟；首错保留前缀立即停、不自修或重试。plan/check 两次重核目录及清单；build 借 SHA256 `d357b232ceb8e14e94cbf9629d57d9f18bc2f60b1b682865042c4cdd622319f0` 的冻结 R88 kernel 逐文件记录源 SHA/字节、压缩并**实际流式读回每个 member 的 SHA/字节**，包严格 `<45 MiB`。原 raw 保留，不平铺到 Git。包数、源字节、包 SHA 与外部成本只能在执行后报告，不能从本准备稿推断。四臂虽都运行结束，固定截止下的 open 仍为删失，归档不改变证书状态。

预期 Git 小路径（精确到文件；最终独立报告待实际冻结文件名后增补）：

- `scripts/round92_archive_u6_repeat.py`
- `results/unified_exact_round92/u6_repeat_raw_archive_source_handoff.md`
- `results/unified_exact_round92/preregistration_u6_repeat.json`
- `results/unified_exact_round92/u6_repeat_prepare_gate.json`
- `results/unified_exact_round92/u6_repeat_prepare_outer_001.{started.json,receipt.json,stdout.log,stderr.log}` 与 `u6_repeat_run_outer_001.{started.json,receipt.json,stdout.log,stderr.log}`（staging 时展开每个具体文件）
- `results/unified_exact_round92/runner_u6_repeat/{identity.json,preflight.json,run_started.json,run_completion.json,postflight.json,runner_u6_repeat_lease.json,summary.jsonl,three_seed_summary.json}`
- 对 seed=1、2，各 `results/unified_exact_round92/runner_u6_repeat/seed_<seed>/{summary.jsonl,processes.jsonl,runtime_status.json,runner_cross_arm_U6.json,runner_repeat_risk_signal.json}`
- 将来 `results/unified_exact_round92/runner_u6_repeat_raw_{plan,check,index}.json`；若失败再加 `runner_u6_repeat_raw_failure.json`。
- 将来包路径**仅**取已审核 `runner_u6_repeat_raw_plan.json` 的 `groups[*].archive`，要求四个唯一 `source_group` 分别为 `seed_1_01_U6_ENS-C`、`seed_1_02_U6_H-ACT`、`seed_2_01_U6_H-ACT`、`seed_2_02_U6_ENS-C`，每个 suffix 由确切 part 数生成；build 后与 index 的包路径集合、文件数和 SHA/size 逐项相符，再形成无通配符的 Git package 列表。三条外层归档收据在真实执行后按固定命名 `u6_repeat_raw_archive_{plan,check,build}_outer_001.{started.json,receipt.json,stdout.log,stderr.log}` 逐项加入。

本交接是原始证据保存准备，不是新求解、R92 晋升或 seed0 再采样。
