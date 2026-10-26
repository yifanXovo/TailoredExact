# Round112 公共恢复根独立复核

结论为 **BLOCKED_PUBLIC_RESTORATION_VERIFIED**：公共恢复与当前数学输出闭包通过，科学状态仍是 BLOCKED。科学输入、源、参考、raw 和数学输出全部从 `F:/ExactEBRP-Round112-public01`、`F:/ExactEBRP-Round112-restored01`、`F:/ExactEBRP-Round112-rebuilt01` 实际读取；E 根只写本次新 reviewer 输出。审查进程的文件打开 guard 禁止 E 根科学读取，实际 original-root fallback 为 false，native/Optimize/compiler 为 0。

公开 4 个科学文件与实际 export/restore receipts 对应。archive 为 `82842777` bytes，SHA `f35beeef7bf8ffdd286ceda1f7166f83eb57281c79b223791f886dd0b44cb81d`；manifest SHA `daba452819ccc245a6251fc1f21e80114115ebab98aed9bc7a7c66f67c3becbf`。独立逐项哈希全新恢复根 55,916 个成员，共 `531242916` bytes，均与 manifest 一致；独立遍历 archive member headers 核对唯一成员集合与大小。没有 archive split parts；不重包、不做第二次 raw 数学重建。

206 个 production source 和 38 个 performance helper 实际字节逐项一致，原测得 commit 为 `d0014a7163e3996fe120471420e56b089c9715ae`，candidate/campaign/PE 身份与准入及后验签名一致。当前 reader SHA `63e388e63901bdebe53e19ff2d937d2cee858d990e60cd5557e05fcd62833b21` 及全部当前导入闭包均在恢复根。8 个 fresh 原模型与 build receipts、5 个继承小 reference receipts 和明确列出的历史 authorities 可从当前恢复根复核；没有把旧 full carrier 当作当前证据。

已签 postformal03 的 936 个公开读取绑定、4 个 signature 文件和 delta 的 96 个绑定全部一致。postformal 中 1 个测得 PE 绑定明确非公开排除，未声称在恢复根复验 native。原 admission 的 21 个当前公开绑定一致；另 1 个旧离线 reader 绑定 `d6240700b6b5272cf7f0bac8487101373ac2c608156a247b1de20507aff32cfc` 是资格时的历史版本，当前路径已保存后续独立复核的 BLOCKED reader。原 admission JSON 字节完整保留，但旧 reader source bytes 未声称仍在相同路径。首次 reviewer 严格一致性断言在这项版本差异处退出 1；此时全成员/源/helper/postformal/delta 字节核对已经通过。工程断言、历史缺口与显式版本解释均记录在新 JSON；没有改原 admission 或放宽生产冻结规则。

在恢复根 frozen reader 的 compare-only 进程中，实际重现默认 CSV `131072` 字段容量错误，再仅调用 `csv.field_size_limit(64 * 1024 * 1024)`，原 compare 完整通过 `619641` 个 CSV 字段及 `backend_conclusions.json` / `summary.json`。两根 39 个 core 文件（37 CSV、2 JSON）全部 byte-for-byte SHA 相同。该容量参数属于当前独立比较进程，没有修改 reader、性能 helper、raw、archive，也没有重新 rebuild raw。复验步骤是分开重建与比较：

```powershell
python -c "import sys,csv; sys.path.insert(0, r'F:/ExactEBRP-Round112-restored01/scripts'); csv.field_size_limit(64*1024*1024); import read_round112 as r; print(r.compare(r'F:/ExactEBRP-Round112-restored01/results/unified_exact_round112/reports_final', r'F:/ExactEBRP-Round112-rebuilt01'))"
```

恢复根实际 12 个完整臂 own 物理车队/整数操作/prefix 容量/站点库存/返回卸载/G/P/F 及 native-end → audit → whole 时钟另算通过，9 个 H 物理车队在 3 个完整角色一致，重建保留 6 个完整同 H 比较与完整 semantic traces。20 固定行仍是 12 qualified / 13 started / 1 interrupted / 7 unstarted；30 比较仍是 18 evaluable / 12 UNEVALUABLE，两个后端均以原 5 分母给出 INCOMPLETE_ATTRIBUTION。原有正负分类和微小 signed 负 gap 均由精确输出比较保留。

第 13 臂实际故障 raw 的 12 commits/SHA、3 own witnesses、calls 1–3 returned / call4 unreturned 和 WinError5 重新读取通过；own 数学 UB `0.008182628062360801` 合法，真实缺失的 result/completion/observations/audit/native-end/postexit/metrics/whole 均缺失。后 7 个固定位置没有 launch；partial 不被提升为正式 endpoint、lower、证书或时钟。并发 Get-Content 导致 delete-sharing 冲突仍只是可能解释，未证明唯一原因。

实际 13-case production-function qualification fault batch 和全部 closed fee receipts 在恢复根可读并一致；全部保守费用 `39 starts / 18061.35593342781` 秒，无失败退款或 nested fee。public carrier 有意不包含 PE/DLL/compiler/license；对应原测得身份是此前实际准入的签名事实。本 reviewer 不重复完整 12 native matrix/LP parser，也不激活尚未执行的数值受损恢复政策。未解决受损 claim 仍须 HOLD 和当前 affected-call proof。

新签实际读取绑定为 `review/restored_root01.json`。父任务报告的科学 payload commit `a3cac1df0ee1d4eaaeb87343508e0af31cfc3b40` 尚待后续实际远程/PR 身份核对；本签名不声称已发布或已审 Draft PR。当前全部复核进程已退出，可进行 Git 交付。
