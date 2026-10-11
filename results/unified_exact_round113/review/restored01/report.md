# Round113 独立恢复根复核

决定：接受已实际执行的公共恢复和精确离线重建，科学状态维持 **BLOCKED**。初签 [report.json](E:/codes/ExactEBRP-round113/results/unified_exact_round113/review/restored01/report.json) 保留原字节；其发布差异和 science A 远端收据的待核项，由随后独立封签的 [final_supplement.json](E:/codes/ExactEBRP-round113/results/unified_exact_round113/review/restored01/final_supplement.json) 和 [易读补充](E:/codes/ExactEBRP-round113/results/unified_exact_round113/review/restored01/final_supplement.md) 关闭。

审查证据仅来自 `F:/ExactEBRP-round113-public01`、`F:/ExactEBRP-round113-restored01`，以及本次审查自身产物。未回原工作树填补依赖，未执行求解器、编译、资格测试、打包或重新导出。父代理实际空根恢复收据已核，审查员独立离线 reader 重建用时 **20.93617840006482 秒**；**63,224 个 CSV 字段、203 个 JSON 叶值**逐项完全一致。

压缩载体实际 **32,982,912 字节，0 分片**，低于 95 MiB 单文件限值，没有人为拆分。manifest、tar 与恢复文件的 **6,095 个成员**逐项 SHA/大小匹配；无重复、不安全路径、符号链接、PE、DLL、许可证文件或旧完整载体。206 项生产源码、42 项性能 helper、reader `7aecf8ae…` 与冻结身份一致。旧 12 组仅继承并核对限定的 146 份结果、审计、时钟等权威材料，未重解析旧 LP 矩阵。

恢复后仍为 **旧 12 + 新 3 合格、1 个正常返回但 POSTEXIT_VALIDATION_BLOCKED、4 个 G100 固定未启动**，21/30 配对可评价。cold P 的实际 1 次 Optimize/正常返回被保留并计费；其正式 U/L/gap、whole receipt 和完成时钟保持缺失。ENS-C 与 M-B 都是 INCOMPLETE_ATTRIBUTION，唯一下一优先级是 branch3 的有限不足解释与 STOP。没有把后验证故障判为算法 LOSS，也没有推断未知 G100 数值或隐藏分支根因。

本轮全部实际费用维持 **15 个保守启动、6,112.501114845276 秒**，包含失败资格和正式 wrapper 费用。恢复和审查产生的 Python 缓存是非权威运行产物，不在科学载体中；独立 reader 禁止使用既有项目缓存。审查防护最初对 publisher 原型不变和 Windows Python 标准库初始化的过宽断言，已在 [engineering_failures.json](E:/codes/ExactEBRP-round113/results/unified_exact_round113/review/restored01/engineering_failures.json) 留存，未产生 native 或资格启动。

初签之后的实际 publisher、Git 属性与远端 verifier 工程差异逐项披露在最终补充中。科学性能闭包和 reader 字节未改。该补充仅核 science A `8dd38b790a4584f17aa75094f9451519e07bcdbe` 的已完成观察；不声称审查员主动 live 查询，也不验证之后的 receipt 提交或未来远端 head。
