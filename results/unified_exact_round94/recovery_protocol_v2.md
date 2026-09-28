# R94 P 资格 journal 类型故障的有限恢复协议

2026-09-28。第一次且唯一一次已授权资格批次只启动 F2；其 `ExactEBRP.exe` 正常返回 0，完整进程墙钟 0.2920158999040723 秒，原生结果记录一次 Optimize。外层资格批次墙钟 0.5473849000409245 秒，含预检的 invocation 至收据写前 0.83518399996683 秒。旧 `qualification_completion.json` 以审计失败结束，C20、B50、U6 均未启动。旧身份、失败、完成收据与 F2 的 15 件 raw 文件不可改、不可重跑；任何已付前缀继续作为失败原始记录。

唯一源码缺陷是新 adapter 用 Python `is True` 判断 `full_original` 与 `native_preconditions`，而冻结 NEJ1 C++ 事件使用 JSON 整数 `1`。修复函数只接受布尔 `true` 或**类型恰为 int 的 1**，拒绝字符串、其他非零数和浮点 1.0；正式 arm 的相同 native 前置条件也作相同窄修。R86 旧 reader 的原问题域、原始 witness、global bound、commit 完整性等检查不变；模型、目标、容差、solver 及旧 P/ENS/LP 参数不变。

运行 `repair-prepare` 是**零新增 Optimize** 的版本化准备：先哈希钉住原 v1 prereg/身份/失败/完成收据、Git commit `86b295b825823c46bcd2f2ccc29fe955e72002d1` 中 v1 runner 字节，并逐文件记录及复核 F2 raw 大小/SHA。随后只读重放 F2 原三条 journal commit，要求一条 full-original native call、一个 returned、原参数 readback、model SHA/fingerprint/行列/域、生命周期、五项 set/get 与原 P 隔离；不读取 F2 极短搜索结果来选算法，也不把它计入正式比较。`recovery_v2/` 下新 identity、离线 F2 receipt 与 raw manifest 各不可覆盖。此后每次读取 v2 身份仍重新哈希旧收据和 F2 raw。

第二资格门只允许旧 v1 identity 中 **launch 2–4** 的三条原命令、原独立输出目录，顺序 C20→B50→U6，`--time-limit 0 --process-wall-time-limit 0 --process-shutdown-margin 0` 加每个外部 15 秒完整进程 cap；上限另 45 进程秒。不存在 F2 重跑、同角色替换、改 cap/seed 或新模型。其唯一准入文件路径为 `recovery_v2/remaining_qualification_lease.json`，JSON 必须**逐字段全等**：

```json
{
  "schema": "round94-recovery-remaining-qualification-lease-v2",
  "authorized_by": "root",
  "allow_optimize": true,
  "recovery_identity_sha256": "<repair-prepare 所产 identity.json 实际 SHA256>",
  "preserved_f2_audit_sha256": "<repair-prepare 所产 offline_f2_audit.json 实际 SHA256>",
  "planned_processes": 3,
  "execution_order": ["C20", "B50", "U6"]
}
```

每条新资格调用一次真实 native Optimize，并保留完整原生 journal/物理/参数收据、实际进程墙钟及失败前缀。任一失败即停；旧 F2 加三条新资格全数通过后，v2 资格总收据应分别记旧 F2 的一次和新三次、合计四个确认的 native Optimize，但不是新的四次调用。首次 F2 失败时旧收据写“confirmed 0 / total unknown”，这是当时 adapter 的保守结论；v2 离线重审提供后验确认，不回写旧收据。

正式 12 臂还需新的 `recovery_v2/formal_lease.json`，逐字段全等：

```json
{
  "schema": "round94-formal-after-recovery-lease-v2",
  "authorized_by": "root",
  "allow_optimize": true,
  "recovery_identity_sha256": "<v2 identity.json 实际 SHA256>",
  "qualification_completion_sha256": "<v2 qualification_completion.json 实际 SHA256>",
  "planned_processes": 12
}
```

正式 runner 仍复用原 identity 中 12 条命令，三臂原问题交叉 U/L 与原物理、LP-G split 审计不变；新 v2 identity 记真实修复后的 harness SHA。两道 lease 互不替代；本文件及 `repair-prepare` 都不授权新原生进程。
