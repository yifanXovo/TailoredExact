# Round139 完成交付报告

**研究决定：停止扩展 LP-only 与 MIP-only，保留 R138 BOTH 为 research-only；
R137 GI-TBC 继续作为稳定入口。** 本轮已进入的六个正式完整运行、四个资格运行
均封存。主结果、数学解释和剩余问题详见 [final_report.md](final_report.md)
及 [mathematical_analysis.md](mathematical_analysis.md)。

本轮确认：外层 LP 加强可抬高父界并消除最弱子域的边际改善，从而改变 AM
动作；更强的 LP 不保证更积极的分支决策。K20 的 MIP-only 首先保留 BASE 的
native-target 动作，随后由 stock 原生界改变下一次决策。其收益不能解释为
省掉约 0.33 秒 target，也不能解释为初始 H 更好。

三角色四格含六格旧 BASE/BOTH 参考和六格新增完整结果。MIP-only 保留 K15/K20
获证收益（34.70/100.71 秒），与 BOTH 无实质时间差，但 RB35-T2 的 U/L
仍为 0.4012002178390506/0.22918159966432358，重要回退未改善。LP-only
失去主要获证收益；RB35-T2 的 U 仅部分恢复，U/L 均未优于 BASE。没有值得升级的
新统一配置，因此未机械扩展五角色、追加新 Seed1 或启动 TC 探索。
保留的八配置面板与有限 BASE/BOTH Seed1 均沿用旧身份，不冒充非对称方案的新证据。

剩余算法问题是如何用统一且有效的资源表达保留原生证明进展，同时避免损害
incumbent 质量。实际模型重建、Start 和原生状态属于本次干预；本面板不提供
可加的耗时归因或一般性能支配结论。

交付事实如下：

- 生产源码：`6b22433f525df4d1a6ce48a70b5b6414a53aa73b`；
  固定 science：`94a275b7545eba4464a25945bbadc8b4bc896962`。
  最终九页 [manuscript.pdf](manuscript.pdf) 已经主要实现者与独立复核者逐页检查。
  V1 主测、V2 修复和旧 Seed1 身份保留，后续交付提交不重封 science 载体。
- 新增实验实际计费 **6371.821015599417 秒（1.769950282111 小时）/ 57,600 秒**，
  无未关闭费用；完整方法外层与资格/失败均计入，嵌套 H/LP/MIP/Work 不重复累计。
  [cost_report.json](cost_report.json) 单列构建、离线验证和普通交付 I/O；
  其晚期普通费用快照不改变固定实验总额。
- 英文 [Draft PR #201](https://github.com/yifanXovo/TailoredExact/pull/201) 已创建并推送。
  临时 base 为 `codex/round138-shared-product-resource-coupling`，实际 base SHA
  为 `d606062edddf58c13a7c3acb48e896fc787ff856`。
  [PR_READBACK.json](PR_READBACK.json) 是 metadata 提交
  `6d6c51c287f02fc3607dcad2b555738b2780c5af` 推送后的实际 API 快照：
  open、Draft、未 merge、head 为本轮分支。该快照不声称包含自身之后的凭据提交；
  最后凭据推送后另读回实际 head。待合并不阻塞本轮完成。
- [公开载体凭据](public_restore_receipt.json) 实际通过一次固定提交匿名读取：
  **13 个新载体、119,112 个成员、35.359274700051174 秒**。
  [晚期 metadata 凭据](public_metadata_read_receipt.json) 对提交
  `6d6c51c287f02fc3607dcad2b555738b2780c5af` 的 12 个小文件读取通过，
  用时 28.607840900076553 秒。公开纯读累计 **63.96711560012773 秒**，
  低于 1800 秒；Optimize、编译、商业 Native 资产加载、Git fallback 均为零。
  这是公开字节/成员可读性，不替代已完成的本地科学/语义审读，未重开 R137/R138 恢复。
- [清理凭据](cleanup_receipt.json) 记录 PR、公开与视觉验收之后的有限清理：
  逐文件删除本轮 18 张可重建预览 PNG，**3,821,777 文件字节**。
  观察卷空闲增加 3,854,336 字节，不将其当作精确因果分配。
  唯一 raw、失败、两版 PDF/TeX、必要 PE/DLL、构建依赖、活动树、
  旧轮和用户内容均保留。未自动 merge、force-push、删除历史分支或发送外部消息。

独立科学整合复核见 [review/final_integration.md](review/final_integration.md)；
最终交付读回见 [review/delivery_readback.md](review/delivery_readback.md)。
[RESUME.md](RESUME.md) 是后续入口：本轮没有待续原生求解，任何新研究应另设范围、
身份和费用。WORKSPACE_POLICY.md 的资产根和证据保留要求继续适用。
