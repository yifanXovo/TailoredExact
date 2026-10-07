# Round106 独立交付审查

最终独立交付结论为 **ACCEPT**，支持 **RETAIN_COMPONENT_ONLY**。数学、实现准入、八臂负结果及最终公开载体的实际恢复/零求解复算均已通过。完整 assignment-master 候选不准入；保留默认关闭的 A/B 证书及已验证事件合同，取消三个未启动确认组符合冻结门槛，不能当作确认成功或一般化结论。最终可移植公开载体复现范围是 **fresh03**；此前成功、失败及 HOLD 身份都保留，原始性能证据与 archive 没有重写。

本审查由独立审查代理完成。第一阶段已在正式性能前签发 [performance_admission.json](performance_admission.json) 的正确性 ACCEPT，并完整阅读任务及 R105 关键资料、实现，针对性复核 R51/R52、R54、R60/R61、R62、R104。第二阶段于全部八臂结束后恢复，使用自行编写的标准库读取/数学/物理实现；没有导入生产 A/B、物理函数或工程报表读取器，没有编译、测试 exe、Optimize、IIS、原生进程或独立性能运行。

冻结生产 PE 为 `1ad7b9128288ff06eed64ac91154c1863963827c5399083b1b233a24ee2d09b4`，DLL 为 `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。交付阶段直接重新读取这两个实际文件，SHA 与资格身份相同；资格 identity SHA 为 `84928d0bbc026fc494bbf4edbe3de070276c1b63e6527c9c7dc523030ae1789f`，201 个实际生产源字节仍逐项匹配。八臂均沿用冻结 PE/输入/数值与线程设置。

## 独立检查的实际范围

[independent_delivery_check08.executed.py](independent_delivery_check08.executed.py) SHA 为 `eee008dd7c5d45ae009670a413470457d991e2c7f5913a87d7ba8272ed7b2720`，依赖仅限标准库及独立审查代理自己的 [independent_math_check05.executed.py](independent_math_check05.executed.py)，后者 SHA 为 `5a649ace202cf880c2e60d47accbebc5152e36b7412c71918871dfb1218df675`。生产计算函数没有参与复算。

[independent_delivery_check08.json](independent_delivery_check08.json) 实际 PASS，SHA 为 `cc0b0d6b541e6ffc04e1a19a4444380d7d5e72ea25a113e188e48e7a5db758fd`。它从 10695 个实际读取文件记录相对路径、来源绝对路径和 SHA，并以 `--compare` 实际逐项对照此前 06 结果成功。检查包含全部 5120 个正式原生 MIPSOL 快照、库存/车辆操作/整数映射/真实目标、全部 5117 次原生 lazy 的当前 raw 活动值、数值可靠违反、合法 Start 活动值、API 返回和事件对应；全部 103 份新结构证书（F2 的 16 EXACT+16 THRESHOLD、C2 的 71 A）独立复算；所有事件臂 startup、改进完整车队及四个控制臂最终车队均独立核验。

每个整数候选仅是同一正式输入上的完整车队/库存观测。F2 有 103 个完整车队、101 个 Y、126 个去车标物理模式及 134 个带车标签模式；C2 FULL/CORE/STRUCT 分别有 2509/148/2352 个完整车队。C2 的 Q 不同，两种车辆模式计数相同，分别 4432/365/4755。八条选出的非初始物理模式及其来源 SHA、原生提交/下一事件与资格证据层已核对；这些数字不构成独立实例数。

## 自然冲突、原生继续和新可行车队

自然 A 链来自 C2 STRUCT event5/car2，pickup 支撑 `{3,5,13,22,23,30}`、数量 `(12,6,7,8,6,8)`、总 pickup47。独立 Kruskal 对实际保守毫米秒闭包得 MST `1742919ms`，原始高精度矩阵 MST 约 `1742.9233658704326s`；实际保守证书长度 `1742.919s`，handling 加旅行下界 `7382.919s >7200s`。真实原生 row3 的 12 系数活动 `16097.514`、RHS `15914.5950001`、违反 `182.9189999`、合法 Start 活动 `10931.676`，`GRBcblazy` 返回0；同一 master 的 event6 随后出现。证明不使用错误的累计 pickup≤Q 限制；跨车兼容 A 在池中仅于当前 raw 可靠违反时提交。

自然 B 链来自 F2 STRUCT event2/car1，`{13:+5,16:-15,17:+10}`，P=D=15、Q30。独立六序检查得四序违反载荷前缀，两个合法前缀序的保守时长 `3783.997s` 与 `4073.299s`，均超3600。无载荷六闭环最短下界 `1785.584s`，加第16个 pickup 的 handling 得 `3705.584s >3600s`，严格整数预算门成立。实际 EXACT 与 THRESHOLD 活动均6、RHS5、Start 活动3、API0，event3 随后发生。全数学阈值证书有79项；当前 U0 根域实际映射 row1 有37非零，删除的 state 是该现有域固定为0的状态。阈值组同时包含车辆 z 与相应 one-hot state，不能脱离车辆归属。第一阶段已独立验证等号辅助站修复、零 handling、非平衡、已有可行序及整数所有权反例，不能由这些不满足前提的情况泛化 B。

C2 STRUCT event1555 是自然高 epigraph FEAS：原生 modelObj `0.37618561539041984` 高于独立物理 F `0.3750564072917856`。完整三车路线独立重算时长 `7188.636373432086 /7067.9364185886525 /7143.356961529368s`，所有前缀合法、站点互斥、库存/目标与全部旅行+120*pickup 一致，T7200 下可行。car0 pickup40>Q20 仍因前缀不超20而合法。车队构成新的物理 UB；API0/deferred 记录本身不证明接收。独立逐列比较 `submission_4.sol`，在后续原生 **event1559** 实际匹配，并与最终原生向量匹配。其余三次改进提交没有这种匹配，仍是物理 UB，不能冒称原生已接收。

## UNKNOWN、deadline、重复与证据层

C2 FULL 最后 event2509 为 `UNKNOWN_SAFE_INTERRUPT`，无 lazy，`unresolved_candidate=true`，`final_native_bound_qualified=false`。真实原生日志末尾有暂时 best objective `0.2227302947886`，这是未完成物理验证的候选，不能作为原问题 UB。发布 UB 保持已验证 `0.39122358434224824`；LB `0.18962603353153062` 有该未解决候选被接收之前取得的 callback global bound 支撑。最终 native incumbent/gap 不替代原问题证书。

C2 CORE 最后一次完整 oracle 先返回 native INF3，随后 IIS 在全局剩余时间耗尽时结束。实际 call442 IIS 返回时 process `1770.0003679s`，剩余为负，native IIS 时间 `19.638504s`；完整 model SHA、INF/IIS 日志和最后 FULL lazy 均已直接读取，deadline 后未启动 core-confirm。最终 event150 保留已证明 FULL 排除、无 unresolved 候选；147 次 IIS 合计 `1455.2076362s`，145 次 released-template confirmation 与各次 full/oracle 计费分开。生产按已证明 full INF 保底，没有把 deadline/UNKNOWN/IIS 提议本身升格成新 INF。

CORE 的两次重复 fleet 是 events94、95 再次遇到自己的 Start fleet，均 FEAS、无 lazy、无新 UB/submission。该正式臂实际重复 lazy 次数为0。资格测试的 scripted 重复 INF 重新 lazy 和重复 FEAS 去重是另一层；不能用正式臂重复 fleet 数量冒称重新 lazy 覆盖。自然 STRUCT 接收链、资格实际 native lazy/inner deadline、历史保留模型 replay、scripted API 及纯算术反例分别表述。

固定 Y 全车可行性诊断仍 UNKNOWN/native11、无 incumbent、无 INF、无 physical witness，一次 Optimize/零 IIS，原始 T7200、Q20/25/30、严格前缀和 loaded-return 语义不变。第一阶段已核验 R61 的零目标/Tstar≤T 形式与原固定 Y 可行性等价。该诊断没有排除 Y，没有向正式臂输送车队、缓存或 cut，也不证明库存分解不可行。

## 负结果与费用

F2 ENS 当期同 PE 实际认证，process `577.094s`、完整观测 `577.344s`；STRUCT 在 `1170.344s` 观测截止未认证，UB `0.8699780578` 比 P/ENS 的 `0.8659435203` 差。C2 五臂全部删失，P 自主 UB `0.1983028486`、ENS `0.2167930653`，均明显优于 STRUCT `0.3750564073`、FULL `0.3912235843`、CORE `0.3916208967`。不能把候选数量、cut 数、稍强 LB 或 gap 当作最终证明时间收益。A/B 自然暴露与正确性成立，但完整候选未保护 F2 ENS 认证角色，也未达到 C2 P 的可行路线质量，故独立支持 `RETAIN_COMPONENT_ONLY`。

三个确认组 F5/N36/S12 共9臂、35100 nominal seconds 未启动，取消是冻结门槛的负结果，未用反馈重抽/改变输入。confirmation protocol/recipe SHA `0a4a4017...`/`4b98cf8e...` 及三个封存输入的实际 SHA 已重新核对。没有实质性能修改或进一步调参。R104/R105 STOP 仍只约束各自实测家族；此结论也只针对冻结 events-v1 的两个输入/既定 cap，不否定所有 tailored exact 或所有 decomposition。

全部七张当前 research fee 收据与启动声明独立重算：**30 个保守计费 starts、13089.59282640001 outer seconds**。failed development_batch01 的 wrapper+8个声明但实际未启动 child 共9个 starts/.9406832s 保守计入；这不是9个已证明真实进程启动。成功 batch02 完成全部八臂。qualification、prepare、fixed-Y 与 replay 的有限 children 全计入；嵌套 native 时间不重复加到 outer fee。

当前原始 native 读取范围严格为 `qualification/`、`fixed_Y/`、`development01/raw/`，得到 **5778/5778 ahead/after、5622 raw Optimize、156 IIS、missing-after0**。四个 P/ENS 的原生 journal 实际各1/5/5/1个 call 及对应 returned，设置/模型 SHA 已直接核验，另加12得 **5634 Optimize、156 IIS**。原 reports 误纳两份旧 R105 ledger 的5636已撤回，reports02 及 reader_correction 对边界说明正确。

此前独立恢复的原 R105+66份原始 native 补件复核保留在 [inheritance_review.md](inheritance_review.md)：55 starts/12081.441783100076s，原 raw148 Optimize/37 IIS/一个 missing-after，12 P/ENS及3旧独立-review Optimize 属原冻结摘要证据层，合成163/37，不伪造旧 per-call 记录。F5 algorithm571.422与 outer572.174668 分开。独立数学/物理读取不构成独立引擎模型重建或性能复现。

## 最终公开恢复与独立复算

08检查器/执行快照/结果及依赖已在封包开始前冻结。开发草稿01—05、07的失败快照/原因保留：BOM 字节比较、原生近零值整数解释、134/126计数、全局阈值与实际域映射、null bound、误将 FEAS fleet重复当成 lazy重复。这些不会覆盖已通过结果或改写生产证据。06全量 PASS 后，08只修复 `--compare` 对运行时整数键/tuple 的 JSON 规范化并实际对照06成功。

六个公开 part 的实际长度、各自 SHA 和按顺序合成 SHA 已独立读取验证：共283820721字节，整体 `c196bb62c84d7775c239fe466b436466b327988a031c2c6f75814fca5609ec3c`；原 manifest SHA `8391081b0db0188e108fe4d84a190e518fca541f1b3ed9bcff3c3cf444bcb87e`，parts manifest SHA `7e8dc4a84052202c3cf423ecf3ce0e6a9c3d8ca455bfb5c6a724a97b195c92a9`。实际 fresh02 的收据明确仅用公开 parts，恢复45827份当前成员、1556份原 R105成员及66份补充 ledger。

本审查代理已通过 `round106_common.py independent_fresh01 300 engineering`，在 **E:/r106-fresh-02** 实际运行恢复的冻结08检查器，`--root` 和 `--compare` 均指向该隔离根内的实际文件。exit0、outer45.4077236s、零 Optimize/IIS/native；10695份读取来源全部在该新根内，没有原工作树回退，全部语义/源字节 SHA 与冻结08基线相同。新结果 SHA `d9df839771ed6700db58a9b51446309204356778535ab7331f3374012a412f98`，其成功身份保留。工程 stdlib reader 同时从实际恢复内容重建并逐字段对照 R105/R106 表通过。

fresh02 证明当时真实字节恢复/复算成功；它仍使用原 Windows CRLF manifest。旧 R105 Git blob 是 LF，而原依赖 SHA 绑定 CRLF，未来其他 checkout 可能失配。根线程保留旧文件、原 archive/manifest 与所有成功/失败收据，以新 R106 `r105_supplement/inherited_compact_manifest_bytes.json` 的精确原字节、SHA `f1975056153d4dd8fd73d3713a649f0833a5914b831c554ed9192b288b7223cd`，解决公开依赖。新增 `-text` 规则只覆盖新 R106 路径。第一次 carrier split 在生成 parts 后拒绝覆盖原 manifest 的失败保留；第二次 split 另建 parts_manifest 成功，archive 与原 manifest 都未改写。

最终实际 **E:/r106-fresh-03** 以公开六个 parts 和公开 exact-byte 旧 manifest 补件恢复，current45827/inherited1556/supp66、`used_public_parts_only=true`；恢复收据 SHA `18a1bf4cac5f56fb51da66f4e326bf16ae97dbdb926da0591e9b2a3d0ae42739`。最终公共 restorer SHA `ced99b3bbd7bdcec429fa997f8c81921583cf6b22c4351483cf89eaffd42938c`；同一 reader SHA `4c929ba80337661baef2e0dbd99ee2301e81d4e15ba9904c5b0365cc60dd1a31` 从03实际成员重建 R105/R106全部 CSV/summary并逐字段对照通过，execution SHA `ad622561b0de709dba8365a185c6e836c0348f72753c1b27cebece5f83ec2b74`。

本代理再次实际运行恢复03的同一冻结08脚本，`round106_common.py independent_fresh02 300 engineering`，exit0、outer `41.033704500005115s`。新结果 `E:/r106-fresh-03/results/unified_exact_round106/review/independent_delivery_fresh02.json` SHA **`d488dac1d65d28729ec7832b63b9364261875dff5d05088a86acef1b308d00fb`**；10695份来源全在03内、原工作区回退0，所有实际源 SHA 和全部复算语义与恢复08基线逐项相同。此次 Optimize/IIS/native 均0。工程收据 SHA `eb60947271ca1b8f144723b7c38df3db1ea7e1d69d0f399fa5a2a9c13d2dcb3b`、launch SHA `31bfc985ac3a75aa59ea2130f6b29412f1eff95c40283fbf1fd9fb96a690d4d9`。

除根线程的 index 收据外，本代理用 `git cat-file blob :path` **再次独立逐字节读取13个实际 Git index blob**：六 parts、两 manifests、四公开脚本及 exact-byte 旧 manifest 补件，均与相应 worktree 字节、长度、SHA一致。index 收据 SHA `3db50b3c2d9ea7c50eece5a768cfb6d41f3041164e465ecd9d4e564ac74444c9`。实际 Git 状态/暂存差异没有旧 R105 改动，`.gitattributes` 增量只限新 R106。公开可交付字节已明确，不仅检查了本地 manifest 或现有目录。

最终解除 HOLD，无算法、正式结果或公开恢复阻塞项。ACCEPT 只准入上述证据与组件保留结论，不准入整个候选的性能采用，不声称独立引擎性能复现。public review/recovery 收据在冻结 archive 外保存，避免循环哈希。
