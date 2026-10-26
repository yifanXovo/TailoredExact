# A1 G2/G3 串行 runner 就绪记录（2026-09-26）

准备与静态检查完成，**没有启动本轮求解进程、模型构建或 Optimize**。两套 `prepare` 各生成了独立的 `identity.json`、`preflight.json` 和精确 argv，运行根分别为 `runner_a1_startup_d6/`、`runner_a1_g3/`；不存在正式 `summary.jsonl`。本记录不是启动许可。

| 冻结物 | SHA256 |
| --- | --- |
| `../../scripts/round88_a1_g3.py` | `178e83fcb56143109d00f407af770b711a7e69c5816e63a0aa094dee8ff3eadd` |
| `../../scripts/round88_startup_diagnostic.py` | `d218f400000c82947df38d9a32830598a96e6ec94f004fedde9d8cee48eb5f0f` |
| `preregistration_a1_g3.json` | `6704d39185809b5607a2e4ab165ba497f13d4f5cd1487320a9bf60a27d95a5fa` |
| `preregistration_a1_startup_d6.json` | `c567d8dc088152d301d26bb20ec7bacbc7877a55bb8e154e3c628c06eb3b9611` |
| `runner_a1_g3/identity.json` | `82468c3375c06217116bde222158bb647f5571f111ac34f8ab709d7634862d38` |
| `runner_a1_startup_d6/identity.json` | `c6c32d1fdc8b142230a951139c516629a72f6b97111fa4ca291ae1f5f45d1941` |

A1 源码提交 `13e09e9b676e95d18bd635d37a5960903bad4113` 与二进制 SHA `23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693` 经 `prepare` 再验；协调者已完成 11/11 资格验收。19 输入 SHA、场景参数全匹配，八例执行顺序与 24 个命令在 G3 identity 中冻结。三臂使用同一 build；ENS-C 是该 build 的默认关闭 A1 控制，P-GRB 为原始 compact 对照，R83 binary 不参与配对执行。P 导出的 `compact.lp` 同时核指纹和历史规范 SHA，物理见证、全局界、交换闭包、跨臂 `max L <= min U + 1e-7` 独立复核；矛盾、严重退化信号或未知审计均停批并保留成本及原始日志。

静态 `py_compile`、两份 `dry-run` 均通过，计 `optimizer_calls=0`；D6 历史保留见证的无求解 `offline-replay` 通过：物理目标 `0.15750980361456166`，原始 T 可行，构造前缀与等净交换闭包重放均通过。这只证明 reader 接口可工作，不证明 A1 新输出或性能。

先执行 G2 D6 两臂 startup-only，每臂完整进程 cap 120 秒，不运行 P；完成后独立审查物理 UB、25/1 个种子、零 Optimize 与全程成本。随后才可启动 G3 `run-smoke`（E8、S12 各三臂）；六臂验收与协调者另发闸门后才可 `run-rest`。这些都是新的完整运行；诊断数据不注入正式臂。常规每分钟采样只落盘，不唤醒协调者。

启动前仍需独立 runner 审查、当前执行代理 Sol high/xhigh 的会话元数据核验、唯一资源 lease 与 host solver/build 排他检查。**不要仅据此文件运行。**审查通过后，协调者在相应输出根新增严格身份绑定的 lease：

```json
{"schema":"round88-a1-startup-d6-lease-v1","identity_sha256":"c6c32d1fdc8b142230a951139c516629a72f6b97111fa4ca291ae1f5f45d1941","authorized_by":"Astra","allow_startup_diagnostic":true}
```

```json
{"schema":"round88-a1-g3-lease-v1","stage":"smoke","identity_sha256":"82468c3375c06217116bde222158bb647f5571f111ac34f8ab709d7634862d38","authorized_by":"Astra","allow_optimize":true}
```

仅在上述闸门均满足后，命令依次为 `D:/msys64/ucrt64/bin/python.exe scripts/round88_startup_diagnostic.py run`、`D:/msys64/ucrt64/bin/python.exe scripts/round88_a1_g3.py run-smoke`。`run-rest` 需要独立 `rest` lease 和烟测验收签名，不能沿用 smoke lease。任何源码或脚本变更均使 identity 守卫拒绝运行，须先审查与重新准备，不覆盖已有原始目录。
