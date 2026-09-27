# Round 60 数学与原生回调说明

## 原问题目标与共享可行解

对最终库存 `Y_i`，令 `r_i=Y_i/D_i`、`S=sum_i r_i`、
`H=sum_{i<j}|r_i-r_j|`。本项目的原目标为

`G = H/(V*S)`（S>0，否则 0），
`P = sum_i w_i |r_i-1|`，`F = G + 0.15 P`。

`VerifiedBrpCandidate` 同时保存路线、操作、最终库存、G/P/F、来源、代次、
模型身份、时间与内容 SHA-256。`VerifiedCandidateStore` 先对规范序列化去重，
再调用原问题 verifier；只发布严格改善的不可变快照。因此候选对象和其目标
不会跨 HGA、外层区间树和 Gurobi 注入时失配。

## 轻量 BRP 候选

构造器从空车路线开始，每一步枚举“车辆、未访问站、操作量”，按完整原目标
选择严格改善操作，以 LP 的 `z_k_i + x_k_from_i` 作确定性次级排序。每个可选
移动同时检查站容量、异构车辆 Q 的装载前缀、旅行增量和
`travel + pickup_time*pickup + drop_time*(station_drop+depot_unload)`。
由流量守恒，单条路线的 handling 项等价于
`(pickup_time+drop_time)*total_pickup`，但最终仍由独立 verifier 重新逐项计算。

## 完整原生映射与残差

候选经既有语义 mapper 写出 G、r/e/h、Y、库存 bit/product、访问/模式、弧、
次序、操作量、装载和时间变量；未识别变量、区间不相容或 cutoff 不相容均
失败关闭。随后从当前 Gurobi 模型读取每个变量的类型/上下界以及全部线性行
CSR。对第 j 行计算 activity，按 `<=`、`>=`、`=` 得到 violation，并要求
`violation <= 1e-7*max(1,|activity|,|rhs|)`。存在 general constraint 时不启用
候选路径，避免声称只核过线性行便覆盖未知语义。

## `GRBcbsolution` 与接受语义

实现仅在 Gurobi 官方允许的 MIP、MIPNODE、MIPSOL 位置调用
`GRBcbsolution`。官方说明：调用必须提供与模型变量数相同的向量；MIP/MIPSOL
位置会先存储而不是立即处理，故返回 `GRB_INFINITY` 不能解释为接受失败；
MIPNODE 返回有限目标才是即时处理证据。因此本轮把 return code 0 只记为
“已提交”，有限返回目标、后续 MIPSOL 的完整向量相等、或求解后最终整数决策
向量相等才分别升级为有明确含义的确认；其余保持 `acceptance_unknown`。

官方还说明根节点的 MIPNODE 会按每个 cut pass 回调，且根完成前
`MIPNODE_NODCNT` 保持 0。因此采样保存第一和最后一个根向量、完整根标量轨迹，
只有看到非根回调才把最后根向量标为 `confirmed_complete_before_nonroot`；若求解
在根认证结束则用 `confirmed_complete_at_optimal_termination`，其他情况只称
`last_observed_root_relaxation`。参见 [Gurobi C callback API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html)
和 [callback codes](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html)。

## 固定库存乘积—路线归因

`root_relaxation_diagnostic.csv` 对第一/最后根点分别重算库存精确 Gini，报告
`delta_G=G_exact(Y)-G_model` 与 `max_i|zprod_i-G_model*Y_i|`，并按 Y、bit、访问、
模式、弧报告分数化。`product_route_diagnostic.csv` 再固定最近整数 Y 以及其唯一
bit 编码；固定 LP 的产品残差约为机器精度，故该点的产品表示已闭合。严格 MIP
随后判定是否存在同一库存的合法路线。只有 T 放宽反事实可行时，结论才限定为
“原 per-vehicle duration horizon 是障碍”，不把它扩张为全局模型结论。
