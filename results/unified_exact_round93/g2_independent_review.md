# R93 G2 固定见证独立结果审查

**审查 PASS；三份预注册见证均无收益。** 这次只检隔离的同向双站整数线 `ΔY_a=ΔY_b=t`，不是正式 ENS-C 的全局资格。D6、E8、S12 各一次完整扫描、零接受，`F_final=F_initial`；所有原 Evaluator 报物理可行的非零整数点甚至都比各自起点更差，而不只是未越过 `1e-12` 门槛。故这三份固定见证上没有可利用的原目标收益，不支持凭此 G2 将 R93 机制晋升到正式算法；不构成对其他见证或全局最优性的否定。

| 固定见证 | 已访站 / 站对 | 全部点 / 原物理可行 | 起末原 F | 最佳可行非零点 F | 单例外层秒（写收据前采样） |
|---|---:|---:|---:|---:|---:|
| D6 | 30 / 435 | 9,494 / 2,934 | 0.15750980361456174 | 0.1630914779493224 | 0.5108981 |
| E8 | 6 / 15 | 412 / 49 | 0.022295597484276734 | 0.029896028911564627 | 0.1659680 |
| S12 | 12 / 66 | 1,630 / 152 | 0.05856397312578515 | 0.06152223491409731 | 0.1897871 |

独立只读复核脚本在外层 **0.2452189 s** 内成功退出，结果见 [g2_independent_replay.json](g2_independent_replay.json)，SHA256 `26db4b1f2cd90798493090d1ef4b1ac27c3de18c7d48abc5d9d4cddf02503662`。它未调用 G2 driver、求解器或新实例：从冻结 input 的 `initial/capacities` 与原路线独立算当前库存，逐已访站对重建完整、原序的 `t` 区间及每点 `Y_a,Y_b`，和三份 `points.jsonl` **逐条完全一致**，共 11,536 点；核对每点的原物理检查标志、可行计数、负载/站/时长拒绝计数、可行点有限 F 及 `F≈G+0.15P`。全部 3,135 个可行点满足 `F_old-F_point≤1e-12`；直接找最低 F 的上述数值均比起点高。三份 `acceptances.jsonl` 均空，`passes=1`、`accepted=0`、`exhausted=true`、`deadline=false`、`verification_failed=false`；最终路线逐车/逐操作等于冻结起点，最终库存和 F/G/P 与原验最终见证及摘要吻合。

身份与费用：独立重新计算 prereg、14 项 gate 源、诊断二进制、六份 input/witness 哈希，均与 [COQUANTITY_G1_GATE.json](COQUANTITY_G1_GATE.json)、`batch_start.json` 及单例后验收据匹配；gate SHA256 `d07d1e2870bc600156784464631bf4458d5d6b4e38e40024c87a6852472d5bad`，driver SHA256 `fa67457fcb80a6b385b147bd6fda96c83593c106f8da75b471243d4bd2331c8c`。三例原生进程均退出 0、无超时，单例 `diagnostic_completed`；整批 `batch_completion.json` 为 3/3 完成。根层 [g2_outer.receipt.json](g2_outer.receipt.json) 记录 Python harness **真实退出码 0、完整 launch-to-exit 0.991145 s**，低于 360 s；三个单例各低于 120 s。表中单例数字来自写各自 outer receipt 前的外层采样，三者之和约 0.8666532 s，是整批时间的内部部分，不能当作各例各自完整 launch-to-exit，也不能再加到 0.991145 s；C++ `wall_seconds` 又嵌于单例内，不能当完整费用。批次启动前的准备、此前 G1 和本次独立复核另计。

原问题物理性和二进制数值边界：每点的负载前缀、返仓、删零后原旅行及 `T+1e-7` 由 gate 绑定的原 C++ `verifySolution` 判，末解再由 `VerifiedCandidateStore` 原验；我复核了记录、源码/二进制身份与路线/库存/目标一致性，但没有另跑 native Evaluator。`exhausted` 只说明这三份起点的声明整数邻域在实际 binary64 和 `1e-12` 接纳门下无已验改善；不宣称精确实数局部最优、旧 R73/R75/R83 联合闭包终点、正式启动性能或证书影响。G1 二站微例的正面可构造性与这次真实固定点的零收益并不矛盾。

独立工作目录 `E:/codes/ExactEBRP`；审查会话日志 `C:/Users/Administrator/.codex/sessions/2026/09/28/rollout-2026-09-28T12-55-39-01a0e65e-5f9f-7b92-9e7b-975d53f9cc35.jsonl`。
