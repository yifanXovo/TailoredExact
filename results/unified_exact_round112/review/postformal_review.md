# Round112 实际执行与 12 个完整终点独立复核

结论：**BLOCKED**。冻结正式实验实际完成 12 个合格臂，第 13 臂 `G50-C1 / M-B` 已启动并中断，后 7 臂未启动。固定分母仍是 20 臂、30 比较位置、各后端 5 个角色。18 个位置可评价，12 个位置为 UNEVALUABLE。不能把第 13 臂的 partial 合法车队、数值日志或末次采样拼成正式 endpoint、whole clock 或证书，也不能把未启动或中断位置写成 TIE。正式臂不重跑。

冻结身份未变化：生产 source commit `d0014a7163e3996fe120471420e56b089c9715ae`，base `ded38c756a32a464bfa9800212da75778707d974`，PE `a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8`，candidate identity `a21242977b11845d34f328bf58963bc089b2b32ad89953e305d24c552751553b`，campaign identity `fac6675183c041453fe209cea225219f1c72392b9c085707ebfd704a67d699ea`。独立读取逐项核对原准入绑定的 206 个生产源和 38 个性能 helper；此前的 ACCEPT 是开始正式实验前有限资格准入，不是本轮已完成的证明。原准入、原 startup writer 拒绝及其修复证据分别保留。

本 reviewer 从实际 raw 重新计算 12 个完整臂的原实例物理车队、prefix 容量、整数操作、站点唯一性、站点库存、返回卸载与路线时限、G/P/F 和 own UB；逐项检查正常退出和 native-end → postexit audit → metrics → whole 的完整时钟。原 explicit-root reader 对完整 12 臂逐 call 的 native matrix、full-original/cutoff/true-G scope、返回 lower 与 complete cover 已独立运行成功，源 SHA `d6240700b6b5272cf7f0bac8487101373ac2c608156a247b1de20507aff32cfc`。其初始缺失行处理尚未区分实际中断；这一缺陷没有影响已完成 12 臂数学结果，新 BLOCKED reader 另作差异审查。

3 个正式 P-S Start 的 before/after 全 native matrix、全部实际 column 的界/type/Start/readback、全部行以及目标/每个原 compact 辅助变量，均由 reviewer 从该臂 own H 物理车队独立重算。等 Q 车辆类按原 mapper 的稳定“操作数降序、相同长度原 vehicle 顺序”重新编号后验证，未借用外部车队。3 个角色各 25 种子完整 H、原 seed `20260626`、24 + 1 preset 的实际 trace 及按容量分配的完整车队，在 P-S、ENS-C、M-B 间一致；每个 pair 共 6 个同 H 比較合格。完整 12 臂实际 Optimize 共 46 次，3 个 P-S 各只 1 次。

独立按预注册阈值重算 18 个比较：

| 角色 | ENS-C / P-GRB | M-B / P-GRB | P-S / P-GRB | ENS-C / P-S | M-B / P-S | M-B / ENS-C |
|---|---|---|---|---|---|---|
| F2 | WIN | WIN | LOSS | WIN | WIN | LOSS |
| R98-C2 | LOSS（严重） | WIN | LOSS（严重） | WIN | WIN | WIN |
| R108-L48 | WIN | WIN | WIN | LOSS | LOSS | TIE |

R108-L48 的 P-S whole 为 `1285.0358486000914` 秒，ENS-C 为 `1552.9688224737765`，M-B 为 `1585.4304004000733`。三者均合格证明最优，ENS-C/P-S 与 M-B/P-S 时间损失超过预注册阈值，但均未达到严重损失规则。保留 P-S 的微小负 signed gap（约 `-9.44e-16`），没有取绝对值或静默 clamp。两个后端的五位归因向量都是 `[WIN, WIN, LOSS, UNEVALUABLE, UNEVALUABLE]`，eligible 3/5，各 **INCOMPLETE_ATTRIBUTION**。这些完整角色的局部正负结果不能外推为五位总体结论。

实际故障证据是 `fees/main04/failure.txt` 中 `atomic_status` 的 `os.replace(runtime_status.json.tmp, runtime_status.json)` 抛出 `PermissionError: [WinError 5]`。现有冻结 supervisor 在这一异常的 finally 中，对仍活动 child 调用 `kill()` 和 `wait(timeout=5)`；异常随后越过 normal completion/audit/whole 写入代码。main04 实际 wrapper exit code 为 1，fee 已由退出观察关闭，reviewer 随后独立进程查询为 0 个 ExactEBRP/参考/故障批次/solver/compiler 进程。没有落盘 child return code 或 native-end receipt，因此不杜撰 child 的精确终止状态。

末次采样在约 `480.328` 秒记录 12 个已观察 committed events，available RAM 为 `14748082176` bytes、free disk 为 `38656249856` bytes；`.tmp` 保留这一新采样，旧 status 停在约 `420.312` 秒。这些记录不支持 RAM/disk safety threshold 触发。父任务报告曾并发用 PowerShell `Get-Content` 读取 status；Windows 文件 delete-sharing 冲突是可能解释。没有当时的 handle trace、访问控制或杀毒追踪，不能将这一解释写成已证明的唯一原因。

第 13 臂独立验证了 12 个 commit 的顺序、完整 bytes 和 SHA，3 个 own witness，3 个实际 M-B 模型和 4 个原 true-G/cutoff scope。实际调用 1–3 有 returned 记录，调用 4 没有；4 的日志没有终止摘要。M-B 原 A/B 行、连续 p/d 与整数 route/load/Y、binary state/direction 均符合冻结设计。partial own H 完整、车队合法；最后 committed native own witness 的原实例 `F = 0.008182628062360801` 可以作为该次执行的数学 UB，原目标非负证明给出独立 floor 0。只有单独的数学证据可保留；没有把日志中的 3 个 LP optimal 文本提升成缺少相应最终证明元数据的完整 controller/cover 证书。`paper_optimize_ledger.csv`、`lp_status_ledger.csv` 都只有 header。真实缺失包括 result、completion、observations、audit、native-end、postexit-audit、metrics、whole，均明确列出。

所有实际付费上界合计 `18061.35593342781` 秒，保守 process starts `39`：资格 `19 / 698.0634860992432`，正式已声明 `20 / 17363.292447328568`。main04 的 1 wrapper + 4 declared child slots 全部计费，只实际启动 1 child；不退还未实际运行的已声明 slots。main04 upper `481.65813398361206` 秒，包含真实 wrapper 退出观察延迟；outer fee 的 trailer 完成不等于 arm proof/whole trailer 完成。

独立复核输出为 `review/postformal03/postformal_review.json`，其 bindings 记录真实读取路径和 SHA；进程 snapshot 为同目录 `process_snapshot.json`。`postformal02` 留存一次 reviewer 报告代码 UTF-8 默认解码错误：发生在 targeted 矩阵解析之后、报告写前，仅为离线工程失败，随后显式 UTF-8 修复。没有任何 native、Optimize 或编译启动，也没有更改冻结生产/performance helper。公共恢复根及新 BLOCKED reader 的最终输出仍须实际恢复后另签复核。
