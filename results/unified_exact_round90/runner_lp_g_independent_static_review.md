# Round90 LP-G G3 runner 独立静态审查

**结论：冻结 runner 无剩余静态阻断，可进入 root 已限定的一次零 Optimize import、panel、16 条命令和 harness 身份资格；不得由此执行 `prepare`、真实模型或求解。** 审查对象为 `scripts/round90_lp_g_g3.py` SHA-256 `da04cf7481dd6f1841383a9390059297a0db51c4ce509a449d5c71725e38b1fe`，`preregistration_g3.json` SHA-256 `dbc1543d2d5b112a127151736ac54d13fe168723a9327561f65aaa81bbaf745b`，`runner_preparation.md` SHA-256 `eebd0ae1ab74643bb56690eaf4d306bba68ddb695360ec150f7eff8109e2ca4b`。我只读对照最终 `PaperExternalGiniTree.cpp` 和 `GiniFrontierGeometry.cpp` 的写入及控制流；未导入 runner、执行测试、构建、求解或 Git 操作。

同一新二进制的 ENS-C/LP-G 两臂只差 `--round90-lp-g-split false/true`，A1/B1 未开。预注册八角色共 16 命令、交替臂序、120/600/1200 秒整进程上限、四臂 smoke 与另行 lease 的十二臂 rest；门禁核七份源码、候选二进制、harness、输入和历史 P 收据。历史 P 是非配对参考。外层成本分别记 prelaunch、进程墙钟、退出后证据排空及离线审计；没有把某个内部 LP/AM 阶段截断后当正式算法。中断只消费已提交 journal，endpoint 是已观察的截尾证据。

候选账本 header/每行由 C++ 以 17 位写入并 flush；runner 的字段名和 phase/status 白名单覆盖实际 `proposal`、`child_lp_status`、`am_decision`、`realized`、`native_target_result`，并拒绝只代表缓存或模型身份失败的 `cache_check`、`child_artifact_check`。它从真实旧 helper 重算 midpoint，核同一二进制浮点端点、严格内点、子域精确覆盖、depth<8、父当前 epoch/模型 SHA；父 LP 原始标量 G 仅与当前 LP/Optimize 收据交叉核对，未声称独立 primal-G 导出。完整子 LP 对需同 epoch、各自 Optimize SHA、LP status 及精确域；同 epoch 缓存复用仍由这些先前收据核验。旧 epoch 文件被重写时，历史 LP 的 Optimize SHA 保留，当前字节无法回验会明确标为不可用；即使新模型已导出而尚未 Optimize，也不误判早先有效收据。

C6 决策按同一父叶的出现顺序关联；有限双子界的 AM 行按 decision_sequence/几何及 action 关联。原子分裂、单子收缩、双子不可行关闭的事件名与 C++ 一致。`child_disjunction` native target 按同父叶顺序关联 C6 目标值和确切 `target_reached_requeue`/`exact_closure` 状态，不会用上一轮父叶重入收据见证新决定。正常全局截止后缺子 LP/AM/交易或 native target 返回 `deadline_unknown` 会标 retained-parent unknown；异常进程中断整体标 partial unknown。完整子对后选择 exact parent closure 不被误称为已原子分裂。正常结果仍须通过原物理验证、覆盖和跨臂矛盾审计；不以账本本身替代证书。

静态审查不能验证实际 controller 的同 epoch requeue、incumbent epoch 重建是否在本次烟测出现，也不能证明 LP-G 改善子界或性能。零 Optimize 资格只检查命令/身份/解析；后续四个已预注册 E8/S12 真实烟测若无合格内点 G，应记非暴露，若时间截尾或事件缺失则记 unknown，不借未观察路径声明通过。

## AM 说明的独立数学复核（root 记录审查者消息）

Sol xhigh 随后只读核对 `am_gap_contraction_note.md`，确认 `S=eta*(eta+z)/2 <= eta*(eta+1)/2` 的单调反解及 gap 收缩推导成立。`t=0` 时还需子界不低于父界，实际立即 AM 接纳前的严格收益守门满足该条件；真实评分应使用 `t=max(0,tau-score_tolerance)`。结论只覆盖双有限子 LP 的 AM 立即分裂，不覆盖不可行收缩或 native-target 分支，不能据此移除深度 8 或承诺运行提速。审查无数学阻断，未执行计算。本节由 root 如实记录独立审查者的返回结论。
