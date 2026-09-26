# Round89 native B1 G3 四臂 smoke 独立验收

**结论：四臂限定 smoke 证据通过，无身份、物理或覆盖阻断；不构成 rest 阶段准入或速度优势结论。** 本次只读原始收据和小型 ledger，没有重放、构建或 Optimize。

`runner_smoke_completion.json` 为 4/4、全部审计通过，外层命令一次退出 0。四臂使用同一候选二进制 SHA-256 `8d5f0ad4a3cf588875a6a3b8ac67c5bdbb2b2df54a5fd49bea56de2034a17e8d`、来源 commit `946cec5e61643964b9aa8122700e041615e67b56`；E8 两臂同一输入 SHA `587737b9d000c1712220232a0fe957073f1f03ac649a63a4775abd9166603acd`，S12 两臂同一输入 SHA `060ee6366b2277c8427675e1a1484de7db10d2ef82a64d4e2ffa6e4695b7b626`。启动命令的 T、取送服务时间、λ、线程、seed、presolve、114 秒内部 solver time 与 120 秒整进程限额同组一致；基线 `--round89-native-ot-b1 false` 落为 R83 ENS-C preset，候选 true 落为 `research-round89-ensc-native-ot-b1`。`option_audit_consistent` 为真，没有把候选误标原 ENS-C。

四臂 result 的原问题 verification 均报告 depot、单站唯一访问、载重、库存、时长、目标重算通过且 errors 为空；E8/S12 最终物理 U 分别为 `0.021337006039780566` 与 `0.05856397312578515`。外部 Gini tree 的根覆盖、父子覆盖、相关叶闭合、叶界有效与单调、生命周期、可行性一致门禁四臂全真，均零开放叶，最终 numerical L 与 U 差在 `1e−7` 原门禁内。`audit.json` 中较早观测的中断式 LB/`certificate=false` 是事件前缀，不是正常终结 endpoint；四个正常终结 endpoint 均有 `certificate=true`。E8/S12 跨臂离线矛盾检查通过，但没有合并两臂的端点作为单次运行证书。这里的下界沿用原 solver 数值认证，非有理对偶证明。

候选 E8 的两条 MIP 摘要与 Optimize ledger 唯一行及当前 canonical L0 LP SHA `e17cd84a8c8c351134ba5946176626e53c3af518107f0e21db838a6cbc410f5c` 对齐，均为原 compact MIP 与其静态 G 域；`PreCrush=1`、实读 `FeasibilityTol=1e−6`、180 审计行/66 站对。child-target MIP 没有 MIPNODE、没有提交行，属合法零暴露；terminal MIP 记录 63 MIPNODE、467 可靠行及 467 次 `GRBcbcut` API 成功、零数值跳过。候选 S12 的 terminal MIP 对齐 canonical LP SHA `35cad8bae4d941fc80ea5dd41ae5fa0c5f13a61f118a01b6a0db0f1e5e6f4dcf` 与唯一 ledger 行，`PreCrush=1`、相同容差与180行/66对，185 MIPNODE、619 可靠行/提交成功、零数值跳过。两个基线臂默认关闭 B1 且无该摘要。API 成功不证明单行永久留存，也不能把相同最优目标归因于 cuts；此 smoke 的三条摘要均为当前 canonical LP 字节已核，无历史 epoch 模型字节缺口。原始 MIP primal 的回调点未独立暴露，物理端点由原结果 verifier 与独立审计提供。

四臂 solver 进程墙钟依序为 `3.531/2.812/3.860/3.656` 秒，总计 `13.859` 秒；含预启动、离线审计与 runner 开销的单次外层墙钟为 `15.2719445` 秒，应采用后者作为本次完整 smoke 成本，不叠加内层时间。每臂正常返回且低于 120 秒，事后无残留进程。E8 候选进程短 `0.719` 秒，S12 候选长 `0.204` 秒，两例已快速封闭，不支持一般证明时间优势。后续 rest 仍需独立 lease。
