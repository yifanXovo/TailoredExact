# Round113 正式停止后的独立原始证据复核

结论为 **BLOCKED / 有限证据不足**。四个 G50 原生 child 都正常退出；只有前三臂完成全部必要 audit、跨臂检查及 whole 费用时钟。cold P 的自身必要 audit 标为 passed，但冻结的跨臂权威检查随后拒绝；不能将其原始数值升级为正式合格端点。G100 四臂固定未启动，不能推断胜负。本文不签署尚待提供的公开恢复根或后续 reader 差异。

| G50-C1 / Seed0 | 独立物理 U | 合格 L | 证书 | 原始 whole 秒 | 实际 Optimize / returned | 状态 |
|---|---:|---:|---|---:|---:|---|
| M-B | 0.008182628062360805 | 0 | open | 1777.2817804088118 | 4 / 4 | 合格完整端点 |
| ENS-C | 0 | 0 | 原问题零证书 | 322.5586690000491 | 4 / 4 | 合格完整端点 |
| P-S | 0.008182628062360805 | 0 | open | 1771.3991304999217 | 1 / 1 | 合格完整端点 |
| cold P-GRB | unknown（正式端点） | unknown（正式端点） | 无正式资格 | 缺失 | 1 / 1 | 正常返回，后验证失败 |

cold P 的原始必要 audit 仍保留 claimed `U=0.2601945154521041`、`L=2.2806283239409983e-6`、`gap=0.2601922348237802`、open。其 process 为 `1770.140000000014` 秒，原生退出 receipt、必要 postexit audit receipt 分别存在；这些时间不能替代缺失的 whole receipt。`audit_execution_metrics.json`、`whole_arm_receipt.json` 和 `fees/main01/04_after.json` 均未写出；不得在离线阶段补写或推算。

## 直接矛盾与证据边界

ENS-C 的最终 own 四车队独立重放得到 `G=P=F=0`，全 50 个非 depot 站点库存等于各自目标。四车容量为 `[30,30,30,30]`，回库载荷均为 0；最长路线时间 `7197.188309052213 <= 7200`。完整车辆、单次访问、物理整数取送、库存容量、路线载荷和时间均通过原独立物理检查。depot 的 initial=50000、target=0 不进入原目标；没有将 depot 纳入库存相等判断。原 lambda 为 0.15，权重非负，故原问题全域目标下界为 0；该合法零车队足以独立证明 ENS 的原问题零端点。

cold P 的唯一 call 声明 `full_original=1`、`native_preconditions=1`、scope=`complete_original_compact_milp`、G 范围 `[0,0.98]`。保存的 compact LP 与同角色原 canonical LP SHA 均为 `3c4385055008239f0b26af749792e95eeb7ef22403ef58035a51b5e75eb16b8c`；实际 native log 的 13326 列、35567 行和类型与当前模型相符。五项 requested/effective/set/get、Seed0、Threads1、Presolve-1、严格两个 gap=0、Gurobi13.0.2、生命周期和真实 returned 均核对。末事件82为 call1 正常 returned；最终 log/readback 与事件53均保留同一 `2.2806283239409983e-6` 下界。

该下界比 own ENS 合法零上界高 `2.2806283239409983e-6`，超过冻结 `1e-7` 容差后仍高 `2.1806283239409984e-6`。独立完整原域 bound/witness 检查拒绝，且原 wrapper 的冻结跨臂判断真实失败并 exit1。事件53的 `global_available=1`、`inconsistent=0`、reason=`full_original_native_callback` 只反映该次 journal 自身 witness 集的检查；它并未通过后续跨臂权威检查。

这证明现有 cold bound 与合法同角色零车队不兼容，并不确定数值或隐藏分支根因。未启动复现、修补 native audit、降低 L、裁剪 gap、放宽容差、借 ENS 端点修复 cold P、补造 whole，或将故障编码为算法 LOSS。先前管理读取的 event68 未序列化 F，故当时 F 明确 unknown；本次正式停止后的物理离线重放是另一次明确授权的审查。

## 三个新合格端点与调用费用

三臂完整 H 都完成 seeds1–25；P-S、ENS-C、M-B 在排除已声明的时钟/路径 metadata 后，全部 H 语义轨迹、容量分配完整车队、最终库存和目标相同。共同 H 的独立物理 F 为 `0.03252017937219731`；不将 H 时钟从完整 whole 中扣除。

P-S 真实提交一次 `GRBsetdblattrarray(Start)`，13326 列、35567 行全部检查，原 native before/after 矩阵相同，CSV/API 逐列读回、原行系数/顺序/类型/边界/目标相符；原 MIPSOL 同时观察 exact/integer vector。ENS/M-B 当前保存模型、原 scope cutoff/G 范围、M-B 冻结 A/B 约束、实际 native log 尺寸/类型、Start/readback、完整 cover 和相应终结义务均通过。M-B cover 保留一个 open leaf；ENS 已关闭相关义务。

正式实际调用总计 **10 Optimize / 10 returned：6 LP + 4 MIP**。M-B 和 ENS 各 3 LP+1 MIP，P-S 和 cold P 各 1 MIP。原 LP call 的 `native_preconditions=0` 不声明 MILP callback bound 资格；其真实 LP returned ledger 与 native terminal log另行核对，没有将该 flag 推断为未调用或伪造 bound 资格。cold 权威失败的真实调用仍计费。

七组 driver/wrapper 费用全部闭合：总 **15 个保守进程启动 / 6112.501114845276 上界秒**；资格 **10 / 470.4929027557373**；main01 **5 / 5642.008212089539**，wrapper真实 exit1，4 actual child。finite01、post01、main01 失败槽和费用保留，无退款，nested native 秒未重复加入。总28启动/26000秒及资格12/1200预算未耗尽；停止原因是当前权威屏障，不是费用不足。

## 身份、旧有限权威与审查产物

候选 SHA `303e900baf8d6dfb6f80570a9c585aded727ef66202148df2237a900eee0ba2b`、campaign、PE、DLL、206份生产源和42份性能 helper仍与已签准入身份相符。cli01与main01均使用该最终性能闭包。有限资格 finite01/02 使用审查前版本的 round113_audit.py；其后仅定向 finite03 补最终生命周期边界，原真实失败槽/版本区别已保留，不改写早期费用身份。

旧12只核对限定146份原权威文件、clock_manifest及dependency_manifest的原 SHA，不重解析旧 LP 矩阵；旧钟不变，原 partial13继续排除。四个 G100 固定目录无 launch/raw/summary/process 记录，全部标记 FIXED_UNSTARTED。

机器证据见 [report.json](report.json)、[new_raw.json](new_raw.json)、[same_H.json](same_H.json)、[zero_floor.json](zero_floor.json)、[cold_contradiction.json](cold_contradiction.json)、[fees.json](fees.json)、[unstarted.json](unstarted.json) 和 [bindings.json](bindings.json)。额外参数/version审查见 [supplement.json](supplement.json)。本审查运行的是纯 Python 离线阅读工程，native/Optimize/编译/资格及 fixture 启动均为0；仅写 review。两处 reviewer 本身的错误断言（LP/MILP flag区别和 depot目标范围）保留在 reviewer_failure01/02，不改变性能、原始证据或结论。

公开 export、空根恢复、fieldwise compare、纯离线 reader 差异及额外 whole-goal独立复核待后续提供后继续。
