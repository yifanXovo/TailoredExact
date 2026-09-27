# B3 固定五站 canonical 导出：独立静态审查

审查对象为 `tests/round91_handling_rounding_probe.cpp` SHA256 `9eeef0954a1f282034594371278abdc1398427dcf4202502c75fddb365f41810` 和 `b3_probe_build_handoff.md` SHA256 `3d3543159ec2088821b7492b860bb518f3e787d64fa5e4c024cfa1535ee51826`。本次仅阅读源码；未编译、执行、导出 LP 或求解。**静态通过，可在 R90 计算结束并获单独许可后进入一次零 Optimize 导出资格；三臂 LP 诊断尚未准入。**

`main.cpp` 的 R83 调用链经 R73/R71/R70/R68/R67/R65，最终由 `paper-k1-am-sf` 先应用 `paper-gf-tailored-bc` 基础，再调公开的 `configurePaperK1AmSfOverrides`，R67 随后指定 `round55-vd-p`。探针从默认 `SolveOptions` 补齐基础分支遗留的 `interval_oracle_low_gini_tightening`、`interval_oracle_objective_cutoff_row`、`interval_oracle_symmetry_breaking` 等标志，再调同一 K1 helper、设置 R83 标签和 VD-P。实际 `writeCanonicalCompactModel` 在 `CplexBaseline.cpp:4225–4359` 将选项传给 `writeCompactLp`；其相关根 LP 选项由 K1 helper 及上述补项覆盖。基础分支的 v20/route-pool/large-compact-flow 等字段未在这个 canonical writer 中使用；`service_operation_min_handling_cuts` 属其它 bound 路径，显式设为 true 与基础 preset 一致但不改变此 LP。探针使用 `PaperExternalGiniTree.cpp:3545–3562` 的 strengthened、静态 `[0,min(F,4/5)]`、原验证 F cutoff、epsilon 0 和 VD-P/F0 policy。由于 `applyAlgorithmPreset` 不公开，这仍是源码对照，不是字节同一性的已运行证明；导出资格必须检查有效选项、行/列、G 域、cutoff、SHA 和身份。

Parser 在无 points 时读取六行零距离矩阵，权重全 1 不触发旧格式缩放；零矩阵满足 K1 对称/三角 metric 守门。两条 `0-1-2-0`、`0-3-4-0` 取货路线分别有 2 单位站点取货和 2 单位返库卸载处理，总时间 4≤5；`verifySolution` 是真正的物理门禁，预期库存 `[0,1,1,1,1,2]`。`17/60` 只作独立 F 残差收据，实际 cutoff 从 verifier 取值。建议资格验收确认该残差为数值零；代码本身没有以它作失败门禁，不影响 cutoff 的来源。初存等于容量，所以 `CplexBaseline.cpp:806–809` 的每个 drop 变量上界确为 0；变量名 `G`、`Y_i`、`state_i_y`、`p_k_i`、`d_k_i` 与真实 writer 一致。探针源码没有 solver 环境、Optimize 或手写替代 LP，失败不覆盖已有输出目录。

尚未得到实际 LP、全行审计或 A/B/C 原始点，因此只能称固定输入的导出设计与当代 canonical 路径相符，不能声称五站不等式在完整 LP 中严格增界，也不能把逐车处理时间取整行 B 蕴含五站行 C 说成完整 LP 的严格支配。后续任何三臂比较必须同一导出 LP SHA、同一 G 域及 cutoff，原全部行/变量残差合格，并分别记实际成本与未知状态。
