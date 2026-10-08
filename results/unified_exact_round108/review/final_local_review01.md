独立最终本地审查 ACCEPT：`SELECT_MB_FOR_BROAD_EVALUATION`。全部 21 正式臂按同一冻结 M-B/生产 PE/DLL 完成，原始车队、模型、时序覆盖与证书独立重建；固定四角色 S12/B24/L48/N36 为 3 WIN、0 LOSS，S12 TIE。该选择只允许为同一候选投入更广评估，ENS 默认不变，未证明稳定泛化或论文资格完成。

| 角色 | M-B / P | M-B / ENS | ENS severe |
|---|---|---|---|
| F2 | WIN | LOSS | False |
| C2 | WIN | WIN | False |
| S12 | TIE | TIE | False |
| B24 | WIN | TIE | False |
| L48 | WIN | TIE | False |
| F5 | WIN | LOSS | True |
| N36 | WIN | LOSS | False |

P primary 六 WIN、S12 TIE，无 severe P/MIXED/UNEVALUABLE，F5 非 LOSS；early-impossible=false，取消 0。F2/F5/N36 对 ENS 的 LOSS 全部披露，F5 severe；ENS 优势未被加入隐藏 P veto。

N36 三臂均正常限时且无全局证：M-B own U `0.18903343435886416`、L `0.1530742203952435`、signed gap `0.03595921396362067`、relative `0.19022673997106307`，完整时间 `5371.085680300021` 秒。P U `0.28697503167264493`、L `0.15003601758156443`；ENS U `0.18251247295488404`、L `0.15323711693023456`。比较采用真实 whole-arm 回执 `5371.085680300021`，legacy supervisor `5370.405999999959` 单独保留，不替代完整计时。

实际独立重建 24 端点（3 功能资格+21正式）、961 全物理 UB 车队、68 保存模型、100 Optimize/100返回、30 submitted Start（32 mapping attempts）、108 实际检查点、12 可靠 Fstar 安全发现区间。每个 UB 独立核算原输入、库存、空车出发、整数非零单方向操作、容量前缀/返回卸载和闭合行程处理时间；完整 normalized Start 的 x/conn/p/d/z/mode/load/ord/Y/state/G 按 R100 原等 Q 稳定车号归一化逐项匹配。24 个 normalization 有限案例和原函数/调用绑定通过。

原 LP/整数模型 scope、真实 G shared cap/floor 和 objective cutoff、实际 VType、逐行 A/B、完整父子/final 分割和逐时 call.cover/native/LP 来源均核验。最终 native log 仅在正确 call/model/log 的成功 return 后供证；conditional bound 使用 min(bound,cutoff)。保存 open leaf 只有在完整 scope 已有支持且排除改进 own U 后才消解。CHILD/NEXT 部分目标分别计数；lookahead 不冒充 committed split。未建立完整 native tree 身份或 p/d 与 A/B 的因果速度分解。微小 signed gap 不剪裁、不做非法百分比；检查点缺失/退出后窗口不外推，发现区间不声称精确 native first-find。

费用由关闭的外层回执和两个保留 qualification +1 修正独立求和：46/48 starts、47514.073242100014/80000 秒；嵌套 native 秒不重复添加，末组结束后 next reserve 为 0 starts/0秒。205 生产源、20 冻结 helpers、21 完整 argv、原输入与当前实际 PE/DLL 均重哈希绑定且未改。

实际 raw 命令/source/root/exit0/receipt：`confirmation_N36_raw_audit01`；source `47cb299f4a8844ca668fab0117b035076f760041fb44ba6c4be0cd751af15adc`，audit `464a56660ab90f4e852f2ef6bc8c4a7c9614674e91c83dbb5900a7be0f9cf5fa`，101.72209049994126 工程秒。审计 JSON 在 receipt 哈希读取前封存 6,510,517 checks；receipt source/audit 的两次 root guard 后控制台 6,510,519，原审计未重写，这两项不是 native/PE 重核验。额外全表交叉 `final_local_crosscheck04` 实际 13,720 项 exit0，root/report selection SHA `ab32e14d9e8dc66c73f2b9a9b49c8d07e01aea566505177027e4f55e61d933d5` 相同；全部检查点数值、状态和安全时刻精确一致。

当前报告 writer `f3d5b5cbf8ce02882afe3e4a1e7a0b11689ceeb65bf1357438c0618882902a41` 已核对 F5 原 normalization 读者失败、24 案例、历史/current 源码/PE区分、ENS损失、受限泛化/机制披露。交叉尝试 01 的 root selection 当时未复制、02 的 Windows 分隔符键，连同源码/命令/receipt 均保留，是交付/比较读取问题，无原始证据矛盾。

新 standalone 的末组零预留和显式隔离数学模式通过 33 个实际有限案例。公共恢复仍必须实际执行：从真实新恢复 root 使用同一 SHA 源码、`--isolated-public-math --through N36`，拒绝 PE/DLL、外部证据及原根回读；仅保留真实运行 binary identity，不声称二进制重哈希或独立性能复现。此次只接受本地科学/证据结论并冻结文件供 pack，实际公共重构和草稿 PR 交付尚未审查。

Reviewer 本轮 0 Optimize/LP solve/native environment/IIS/compiler，无生产、性能 helper 或决策规则修改，无打包。所有详细 file/hash/argv 在已绑定 raw audit 的 read_bindings 和 arms 中保留；这里不重复巨大绑定表。
