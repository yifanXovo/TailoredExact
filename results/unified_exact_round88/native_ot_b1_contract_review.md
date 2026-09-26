# Round88 原生 B1 user cut：最小设计合同（只读）

**结论：值得做一次最小 native prototype 的资格验证，尚不准入正式求解或宣称更快。** 它与离线反复 LP 服务、预建全族 epigraph 有可检验的结构区别：仅在同一原生 MIP 的 `MIPNODE` 事件提交 B1 原列切割，不另建 LP 服务或 O(全族) 辅助矩阵。每次回调及求解器重优化都属于原证明成本；不存在内部秒数、Work、轮数、行数配额或实例分派。新研究身份默认关闭，现有 ENS-C 与容差保持原样。[稀疏 epigraph 决策](ot_epigraph_decision.md)尚无 D7 完成界，不能转化为 native 性能承诺。

**真实路径与 API。** ENS-C 的 `round55-vd-p` 对应 `f0-clean-none/c0-baseline`，当前未启用 CDF user cut。`PaperExternalGiniTree.cpp` 不仅在约 8201 行发起 `PaperTerminalMip`，还在约 3837、7172、7597 行发起 `PaperPartialBoundTargetMip`；最小候选若宣称覆盖原生证明 MIP，必须在这两类实际 native Optimize 中执行同一规则，普通 `PaperLpRelaxation` 不走回调。`GurobiBaseline.cpp` 约 1629 行读 canonical LP，约 2512 行注册已有合并回调。现有 R53 分离器在约 1113–1125 行只拷 `p_`,`z_` 值，并在约 1169 行早退；不能直接接 OT，也不能破坏其它 MIPNODE 观测、MIP 进度/界目标/证据回调。必须在 Optimize 前按 canonical 模型 SHA、叶 id/域、完整整数支持核唯一列索引、类型与界，以及 `state_i_y`、`r_i`、`h_i_j`、one-hot、`r` 重建和 `h≥±(r_i−r_j)` 原行；`state_g_i_y` 虽不入 B1 行，也须确认 VD-P 模型身份。对 retained 模型/partial target 再次核指纹，避免把另一叶索引复用。

官方 Gurobi C 文档规定 [`GRBcbcut`](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html#c.GRBcbcut) 只可在 `GRB_CB_MIPNODE` 调用，切割不得排除满足原约束的整数解；[`MIPNODE_REL`](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html) 仅在该节点 `STATUS=GRB_OPTIMAL` 时读取，返回点**不保证**对用户原模型可行。故非最优节点只记录跳过；最优节点取完整原列向量，值非有限则跳过并留因，**不**把其原行残差当 solver 错误或作为切割有效性的前提。根节点可能在多个 cut pass 重复回调。设 [`PreCrush=1`](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameterprecrush) 并回读，记录其对 native 成本的影响；这有助原列 cut 映射，但 `GRBcbcut` 返回 0 只记 `submitted_api_ok`，不证明该行已成为永久活跃的内部约束。不能将后来再次可靠违反同一已提交行当数值错误；单次 callback 内按规范化原行去重，跨 callback 可重提并分别记日志。不要改 `CutPasses`、原生容差或其它参数来隐含配额，也不用 lazy constraint 代替 user cut。

**代数有效性与浮点外包（原有理支持推导，仅作参照；生产首选见下段）。** 对固定完整支持的有理阈值 `t_l`、宽度 `Δ_l>0` 和任意 `σ_l∈[-1,1]`，原列 B1 行为

`h_ij ≥ Σ_l Δ_l σ_l(Σ_{y/D_i≤t_l}state_i_y − Σ_{y/D_j≤t_l}state_j_y)`。

对 one-hot 两站整数点，右端不超过 `|y_i/D_i−y_j/D_j|`；这与当前节点的 G 上下界及回调点是否原模型可行无关。`σ` 可由浮点 CDF 的正负选取，零可固定为 `+1`（或 0）；即使符号非最违背，该行仍有效，只是可能较弱。每对每个最优节点至多形成其当前点的一条符号行，提交所有**可靠违反**的不同 pair 行，不设额外数量上限。

不能直接把上述有理行浮点化。实际 `CplexBaseline.cpp` 约 2854 行以 binary64 `y/D_i` 写 `r_i` 重建，原 MIP 的整数点只由该**实际导出系数** `\tilde t_{iy}` 和 `h≥|r_i−r_j|` 约束。令精确比率 `t_{iy}=y/D_i`，签名行展开的有理状态系数为 `c^*_{iy},c^*_{jy}`，提交的 binary64 系数为 `\hat c`。在读入的 canonical 模型上独立核真实 `r` 链及 `h` 两向行，取

`δ_model=max_y|t_iy−\tilde t_iy| + max_y|t_jy−\tilde t_jy|`，
`δ_coeff=max_y|c^*_iy−\hat c_iy| + max_y|c^*_jy−\hat c_jy|`。

于是每个**精确满足实际浮点系数 MIP 约束**的 one-hot 整数点都有 `h_ij−Σ\hat c state ≥ −(δ_model+δ_coeff)`：第一项由两端比率与原 `h` 行的三角不等式，第二项由各站恰选一个状态。两项须用有理数/精确 binary64 值或可证明向外区间求上界，提交 RHS 向 `−∞` 舍入；若索引、有限性或外包计算失败，跳过该行并留可审计原因，不能退回无保护的系数。回调活动值也用 binary64 输入的精确 dyadic 点积或有向舍入区间：若 `U` 为活动值上界、`r_d` 为实际提交的 RHS，则至少要求 `r_d−U` 严格大于回读的、未修改的 native `FeasibilityTol`（当前 `1e−6`；若行被显式等比例缩放，按同一比例换算），才标为 `reliably_violated`。这并非 Gurobi 内部接纳保证，也不是新选型参数或 benchmark 容差调整。即使可靠违反，也只证明此回调点对已提交浮点行的算术违背，不保证 Gurobi 接纳/保留它。Gurobi 对近容差的整数候选仍须原物理验证，不把代数有效性误称浮点整数证书。

**首选简化：直接以实际 canonical `r` 链支持构造 B1。** 将审计后的 `r_i−Σ_y\tilde t_{iy}state_i_y=0` 中每个有限 binary64 `\tilde t` 视为**精确 dyadic**，以其真实数值排序并合并相等值（含 `+0/−0`）；不同名义 `y/D_i` 即使碰撞也保留各自 one-hot 列，只共用阈值。取两站并集 `v_0<⋯<v_m`，`Δ_k=v_{k+1}−v_k` 的精确 dyadic 值；任何 `σ_k∈[-1,1]` 的 CDF 符号行在 one-hot 点的右端至多为 `|\tilde t_{iy}−\tilde t_{jz}|=|r_i−r_j|≤h_ij`。因此**不再需要 `δ_model`**；这与实际导出 MIP 的完整 B1 族代数等价，而不是声称精确有理 `y/D` 物理距离逐位相同。原 `r` 系数为 1、RHS 为 0、两个 `h` 下界行、所有支持列与有限的 `r` 上下界都必须从**实际读入模型**核定；与声称的支持/界不符即拒绝启用。若并集只有一个点，则无区间、无有用 cut。任何节点点的原行残差仍不能用来否定此全局有效性。

可一趟**倒序后缀**生成全部展开系数：令 `R_m=0`，对 `k=m−1,…,0` 取 `R_k=R_{k+1}+σ_kΔ_k`；位于 `v_k` 的 `i` 状态系数为 `+R_k`、`j` 状态为 `−R_k`。这是 `Σ_{l≥k}σ_lΔ_l`，直接等于该状态进入的全部 CDF 段系数，复杂度对合并支持长度为线性；重复支持取同一 `R_k`。不必在生产路径把 `y/D` 转成有理数。计算时从两个实际 binary64 端点差开始，令每次减法、带符号相加的结果用 `nextafter(·,−∞/+∞)` 构成向外区间；负号交换区间端点。要求 IEEE binary64 正常舍入、无 `fast-math`/flush-to-zero、每步及最终系数有限且未溢出，否则不提交并记原因。对所选提交 binary64 `\hat c`，由系数包围区间求每列误差上界 `e_y≥|\hat c_y−c^*_y|`，再取 `δ_coeff=max_{y∈Y_i}e_y+max_{z∈Y_j}e_z` 的向上界，并把 RHS 以向 `−∞` 舍入的 `−δ_coeff` 提交。one-hot 使两站每站恰有一个误差项，故这是对**实际 MIP**每个精确可行整数点的充分外包。回调活动值同样按实际提交系数与节点 binary64 向外计算，并沿用上段可靠违背门禁。符号可由普通浮点累计选出：错误符号只减弱分离，不损害行有效性；非有限值、算术失效或极近容差则跳过，不能把跳过称为切割族闭合。

独立无求解 oracle 应从 `Fraction.from_float(\tilde t)` 构造**实际 dyadic**支持，枚举小规模所有整数状态与 `±1` 符号，令 `h=|\tilde t_i−\tilde t_j|` 检验提交 binary64 行加保守 RHS 从不切掉它；逐项把一趟后缀区间同直接精确 dyadic 段和比较。另测同值碰撞、相邻 binary64 阈值、`±0`、单点支持、有限 `r` 界拒绝、溢出/非有限跳过及人为原行不可行的 callback 点。精确 `y/D` 只作解释参照，不能作为该 native 行有效性 oracle 的模型系数。

**最小资格与风险。** 先做无 solver 的小支持精确枚举：每个符号行、非二进制精确比率的导出系数、重复阈值/零段、满/空 CDF、保守 RHS 和人工非原模型可行的浮点节点向量均须通过独立 oracle。随后一个隔离的原生两站 MIP 同时跑“无 cut/原列静态 B1/回调 B1”，核三者原整数最优与物理验证一致、回调点可违反、`PreCrush` 回读、实际 `GRBcbcut` 返回码、root 多次 MIPNODE 时序和 cut 再提行为；如无合格 MIPNODE 事件则资格为不适用而非通过。静态调用链和微型运行要分别证实 terminal 与 partial-bound MIP 均接入，普通 LP 不接入，原全局 deadline/证据及完整成本计费不变。若数值外包不可证明、原生回调未产生可审计有效切割，或成本过高，应停止此方向；一次 API 成功或一次根界改善都不等于正式 ENS-C 多实例运行优势。
