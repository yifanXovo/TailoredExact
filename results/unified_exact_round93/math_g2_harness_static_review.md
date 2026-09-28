# R93 G2 监督脚本独立静审

结论：**源码静审 PASS，可供 root 冻结 gate 并单独决定 G2 发射；没有运行任何真实固定见证/native driver。** 受审 `scripts/round93_coquantity_diagnostic.py` SHA256 为 `79a1440e6690e0299211149457cf112cfcaae9c79d5985133dd37f5b8000cd09`，预注册 JSON SHA256 为 `d853322f29f91b12027f3d82229bc94afae654e90b4a63f6158b4042419106bb`。脚本或预注册变字节须重新审对应范围。独立工作目录 `E:/codes/ExactEBRP`。

只读 `validate` 运行一次，退出码 0、外层 PowerShell Stopwatch **0.1687415 s**、`native_launched=false`；其输出重新核了 D6/E8/S12 六个 input/witness SHA，与预注册相符。未执行脚本 `run`、G2 driver、Optimize、Gurobi 或正式 ENS-C。先前隔离 G1 独立收据见 [g1_independent_evidence_review.md](g1_independent_evidence_review.md)。

脚本 `run` 先检查冻结次序、场景、见证路线数、源/见证哈希、独立 G1 gate 的二进制及源码哈希；单次 D6→E8→S12，每例 120 s、全批 360 s，从预检计时，不重试、不改例。Windows wrapper 在 job 分配后才收到启动旗；kill-on-close 和超时清树将截止后的结果标 unknown。原生退出码非零、缺收据、`verification_failed` 或未穷尽均不能成为完成结果。单例收据写后仍复测截止；整批完整 launch-to-exit 墙钟/真实退出码由 root 的外层 Stopwatch 收据作最终判定，不能把内部写盘前采样时间当完整费用，也不能用超时掩盖已记录身份/正确性/资源故障。

完整性审计从原 input 的 `initial/capacities`、冻结初始见证与逐次接受路线，逐 pass 独立枚举有序全量 `(pass,a,b,t,Y_a,Y_b)`，逐条与 `points.jsonl` 对照；强制 `passes=accepted+1`、接受轮连续、末轮无严格原 F 改善。按 `F` 最小和 `(a,b,t)` 决胜重建接受点，17 位往返 double 的接受/最终 F 精确核对；每轮接受依规则改两站净操作、删零站，末路与新原验见证逐项对照。每个未接纳点的候选路线也可由当轮路线与该点元组唯一重构，已在 [diagnostic_preparation.md](diagnostic_preparation.md) 的 G2 前协议中明写，不必每行重复大路线。外层不自称重新实现原物理 Evaluator，物理/F 数值仍依赖 G1 已核二进制；此静审不证明任何三例实际穷尽或收益。

本次可复现会话日志 `C:/Users/Administrator/.codex/sessions/2026/09/28/rollout-2026-09-28T12-55-39-01a0e65e-5f9f-7b92-9e7b-975d53f9cc35.jsonl`。
