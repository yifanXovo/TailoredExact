# R93 同向双站数量线 G2 固定见证诊断

按[预注册](coquantity_diagnostic_preregistration.json)及已通过的 G1 gate，仅发射一次 [G2 harness](../../scripts/round93_coquantity_diagnostic.py) 全批命令，顺序 D6→E8→S12，每例 120 秒完整诊断截止、整批至多 360 秒；没有重试、加例、加 seed、构建或正式算法接线。运行前计算槽检查无相关 solver/build/runner 进程，gate 的 binary/prereg/harness SHA 重新核对均一致。唯一发射的[外层收据](g2_outer.receipt.json)记录真实退出码 `0`、PowerShell Stopwatch 完整 launch-to-exit **0.991145 秒**，低于整批截止；外层 stdout/stderr 均为空。Python batch receipt 三例均 `diagnostic_completed`，无 timeout、verification failure 或 missing receipt。独立结果复核另行记录；本稿是作者侧报告。

| 固定见证 | 同次原 Evaluator 起点 F | 最终 F | 完整扫描整数点 / 原物理可行 | 最佳非零合法点 F（a,b,t） | 严格改善 / 接受 | 单例外层秒（写收据前采样） |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| D6 | 0.15750980361456174 | 同起点 | 9494 / 2934 | 0.1630914779493224 `(8,23,-1)` | 0 / 0 | 0.5108981 |
| E8 | 0.022295597484276734 | 同起点 | 412 / 49 | 0.029896028911564627 `(3,5,-1)` | 0 / 0 | 0.1659680 |
| S12 | 0.05856397312578515 | 同起点 | 1630 / 152 | 0.06152223491409731 `(4,9,1)` | 0 / 0 | 0.1897871 |

三例各有一次穷尽 pass，所有合法非零候选的原 F 都高于同次起点；`acceptances.jsonl` 各为空，最终见证原路线与起点一致。`points.jsonl` 全部 **11,536** 个点、**3,135** 个原物理可行点均保留；外层 harness 用输入原初存/容量和当前路线重新生成每轮完整有序 `(pass,a,b,t,Y_a,Y_b)`，核对逐点账、best/acceptance 和最终路线。`summary.json` 的 F/G/P、`final_witness.json`、真实 child exit 与外层 receipt 对接；物理与原 F 重算由已合格的 G1 原 Evaluator driver 执行，外层没有额外调用 native。每份点账、接受账、最终见证、summary、单例 receipt/stdout/stderr 及 batch/外层收据的 bytes/SHA256 集中在[机器可读证据摘要](g2_evidence_summary.json)，原文件原位保留。

完整 0.991145 秒已包含 Python harness 发射至退出、三例预检、原 driver、全部候选核验、日志与汇总；单例外层秒数和 native `wall_seconds` 是其嵌套组成，不相加。G1 资格、旧 R88 启动和本报告/独立审查成本另列；未采集原生子进程 CPU 或可靠整树峰值内存，不能填零。[独立 G2 复核](g2_independent_review.md)逐条重放 11,536 个 tuple 并验 3,135 个可行点、三份末路及原 F/G/P，结论 PASS，具体逐点结果见 [replay JSON](g2_independent_replay.json)。这三份旧开发见证上的完整**co 线**负结果不否定所有输入，也不证明接入 ENS-C 后的启动或认证速度。正式 R76/R83 closure 未在本 G2 中执行，LP-G/P-GRB 没有运行；本轮没有新合法 U 优于旧起点，更没有原问题全局 L 或最优证书。
