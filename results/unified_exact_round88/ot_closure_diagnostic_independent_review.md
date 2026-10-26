# OT 九臂闭包诊断独立只读验收

范围：只读检查 `ot_closure_diagnostic_report.md`、`batch_summary.json`、九份外层命令收据与监管收据、各臂最后完整 `round.json` 和其 SHA，并轻量汇总 216 份完整轮摘要；未重新 Optimize、分离、读大 LP、压缩或修改冻结脚本。结论只对九个预注册固定连续 LP 诊断成立。

**身份与计费相符。** 九份外层收据的 source/arm/exit code/wall 与 `batch_summary.json` 一致，总和 `1929.1104196 s`；各 `supervision.json` 哈希、前后 manifest SHA `6293e196160ff00e778c43be2275d8b3fe93020c5207f814dac3ce05f2a0db18`、Job 已分配和源身份稳定均核同。F2 三臂外层 exit 0、监管 `no_reliable_new_row`；D7 root/child 六臂外层 exit 124、监管 300 秒 `unknown_whole_diagnostic_deadline`，无事后重跑。监管内层合计 `1928.2047669 s` 是外层成本的一部分，不能再相加；资格阶段另有 `5.3059186 s`。原始九份最后完整轮 SHA 与摘要均相同，round 0 的基础目标也逐臂相符。

**216 轮与截止边界。** 九臂完整 `round.json` 数依次为 `65,33,56,14,11,11,9,9,8`，合计 **216**；这些轮 `status_code=2`，其摘要数值残差的总最大值为新增行 `9.5257881e−7`、原行 `6.4376824e−7`、变量界 `7.2713557e−7`，低于原有 `1e−5` 守门。216 轮的 `numeric_rejection_count`、`existing_reliably_violated_count` 汇总均为零。F2 的旧 `inflight.json` 是已完成末轮的过程 checkpoint，由最终 `round.json` 与 `result.json` 覆盖；不能据文件存在误称 F2 在途。D7 六臂相反：最后完整轮分别为索引 `13,10,10,8,8,7`，之后又加 `80,120,160,295,1118,1964` 行并启动下一次 Optimize；下一轮有日志而**没有** `round.json`。这些行和在途优化的全部成本已支付，但未产生可报告的下一 LP 目标，更非闭包终值。

**F2 未闭合。** 最后完整扫描仍分别有 `128/134/280` 个正候选。尤其 B2 的最大归一化正违背为 `0.00031532287547601437`，原 `reliable` 余量为 `0.00046926339215081425`；原始 `all_pair_rows.jsonl` 的该候选记 `violation_below_numerical_margin`、`reliable=false`，故状态只能是 `no_reliable_new_row`，不能称“无观察违背”或完整族闭包。B1/combined 的末轮正候选虽小，也同样不是观察性零违背。

表中 `OPTIMAL` ObjVal 是**沿既定 Gurobi 浮点数值标准和原/新增行残差门禁取得的最后完整固定 LP 数值目标/数值下界**，没有独立有理对偶证书，不应无条件称“已验证下界”。原报告脚注和末段现已按此口径修订。F2 的有限可靠行停机与 D7 的截止删失均不足以排序完整 B1/B2 闭包；同组短时界、轮数或用时也不证明原 ENS-C/P-GRB 全方法性能。D7 child 是历史未采纳叶，其局部 B2 行不得上提 root。

**验收结论：** 运行记录、成本、最后完整轮边界与报告主要统计相符；九臂均未取得可认证的完整族数值闭合，更没有整数最优性结论。不因性能未知而重跑或改变原数值门槛。
