# U6 seed1/2 零 Optimize 准备收据

依据 `u6_repeat_prepare_gate.json` 与 `u6_repeat_prepare_decision.md`，仅发射一次 `D:/msys64/ucrt64/bin/python.exe -B scripts/round92_handling_u6_repeat.py prepare`。外层真实退出码 `0`，完整发射墙钟 `1.0021432` 秒（UTC `2026-09-27T19:01:54.4244752Z` 至 `19:01:55.4292198Z`）。原始 stdout/stderr 及 started/receipt 均保存在同目录 `u6_repeat_prepare_outer_001.*`，stderr 为空。

新 identity SHA256 `b9dae28417d7762dca28f8ae5a17bc9c6e2197c8538d7345a217a96f5665da6d`，preflight SHA256 `c8aa7112af498cb2da4e6527e7f3e0e27c0d7c7da6010e8837120d838856f7bc`；外层 receipt SHA256 `48990a1cada4055ae3c4bd3242bb3e96dfd6cd06ae46624e9a350e54092df072`。`optimizer_calls=0`，15 个源 pin、四条完整命令、总计划 process cap 4800 秒。实际新 seed runtime/raw 目录均不存在，未启动 native。

| 序号 | seed | 方法 | 唯一新开关 | native limit / whole cap | Threads / MIP Threads / Presolve |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | ENS-C | H-ACT=false | 1194 / 1200 s | 1 / 1 / -1 |
| 2 | 1 | H-ACT | H-ACT=true | 1194 / 1200 s | 1 / 1 / -1 |
| 3 | 2 | H-ACT | H-ACT=true | 1194 / 1200 s | 1 / 1 / -1 |
| 4 | 2 | ENS-C | H-ACT=false | 1194 / 1200 s | 1 / 1 / -1 |

四臂输入均为冻结 U6 路径，目的目录分别为 `runner_u6_repeat/seed_1/raw/01_U6_ENS-C`、`02_U6_H-ACT`、`seed_2/raw/01_U6_H-ACT`、`02_U6_ENS-C`；无旧 raw 覆盖。准备后 `Get-CimInstance` 对相关 solver/build/runner 进程筛查为空。计算槽已释放。后续 `run` 仍需根另签 identity-bound lease；本次没有运行资格。
