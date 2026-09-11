# Round 60 实现说明

## 共享候选与 HGA 发布

新增 `Round60Candidates`，提供不可变语义的 `VerifiedBrpCandidate`、规范 hash
去重、严格单调 `VerifiedCandidateStore`、有界确定性 BRP 构造和 solver-neutral
线性残差检查。发布门除既有原问题 verifier 外，还拒绝非法/重复车辆路线布局。

HGA 内核在每个严格 best 更新时同步复制对应已解码操作并调用可选 observer；
observer 不调用 RNG，异常会被捕获并永久禁用。runner 用共享 store 立即验证并记录
事件；截止发生时直接返回最后一个已验证快照，避免截止后的重解码。候选 ledger
写失败会放弃发布并回到原 HGA 路径。默认关闭时不安装 observer。

## Gurobi 原生候选

动态 API 新增 `GRBcbsolution` 与 `GRBgetconstrs`。候选在第一个早期 MIP 回调以及
前两个最优根 MIPNODE cut pass 尝试构造；所有异常在 `noexcept` C 边界内捕获。
候选先经原 verifier、冻结 cutoff/已发布目标严格门，再经完整变量 mapper、上下界、
类型和当前 MIP 全线性行检查。DRY 到此停止，INJECT 才调用原生 API。

return code、有限返回目标、后续完整 MIPSOL 向量相等、求解后最终整数决策相等被
分别记录，不把 return code 0 或 `GRB_INFINITY` 冒充接受。候选日志使用每次原生
调用的唯一 stem，写失败会标记路径禁用；外层树随后不再启用候选，但基础求解继续。
partial-target MIP、普通 terminal MIP 和 sibling terminal block 都使用统一配置与
聚合逻辑。

## F0、Single-H 与根采样

stable `paper-k1-am-sf` 和固定状态 runner 共用一个 canonical F0 配置函数；
D2/D3/D4 导出 LP 与 Round 59 逐字节一致。新增默认关闭的
`research-round60-f0-single-h`：保留原 HGA、相同 U 与完整 improving Gini 范围，
关闭外层 split/子 LP，只运行一次父 LP 和一次 terminal MIP。

根采样不再把 `node_count==0` 的第一次回调称为根结束。实现保存每个 root cut pass
的标量轨迹、第一/最后完整向量和至多三个非根 bucket；只有非根出现或根上最优结束
才能升级 completion 状态。采样累计时间、eligible checks、成功读取与未成功检查均
保留。

## 测试覆盖

`Round60CandidateTests` 覆盖默认关闭、共享 F0 身份、空/零目标、hash 去重、无效
候选、重复车辆、严格单调发布、异构 Q、loaded return handling、构造 work bound、
确定性、时间不相容、区间/cutoff 映射、`<=`/`>=`/`=` 残差、HGA 相同逻辑前缀、
截止快照，以及候选 ledger 写失败回退。最终全套 CTest 结果与构建日志随目录提交。
