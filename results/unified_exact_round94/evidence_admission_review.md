# R94 同期三臂证据准入核查（执行前）

状态：只读身份与协议审查；**尚未**进行四次 P-GRB 资格 Optimize 或十二臂正式运行。范围以 [R94 计划](plan.md)为准：同一个已冻结 R90 binary 在旧开发/保护四角色上运行真实 P-GRB、ENS-C、LP-G。该小批最多回答 LP-G 是否值得继续投入，不能成为新数据确认或方法晋升证据。本文不修改历史模型/输入，也不引用历史最优 U 作为新运行信息。

## 身份：本地字节、场景与原 compact 祖先

实际读取四份仓内输入小文件，SHA256 与 R87 campaign identity、R90 prereg 一致；R90 可执行文件存在且实际 SHA256 为 `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`。下表 model fingerprint 与 canonical LP SHA 是 [R87 identity](../unified_exact_round87/campaign/identity.json)中 **zero Optimize 的历史原 compact 参考**，且 [R87 prelaunch audit](../unified_exact_round87/prelaunch_audit.json) 的这四个 fingerprint 与更早源逐项匹配；它们**尚未**证明 R90 binary 本次导出的 LP 字节相同。四次独立 P 资格必须实际导出并核对，任何不符先停、解释生产模型身份。

| 角色；新三臂 cap | 原输入与场景（λ=.15、取/放各60秒、seed0） | 输入 SHA256 | 历史 P fingerprint；compact LP SHA256；列/行 |
| --- | --- | --- | --- |
| F2；每臂900s | `reference/round86_unadapted_confirmation/F2.txt`；`round86-unadapted-varied-structures-v1_F2`，V20/M2/Q30，T3600 | `ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e` | `788240696`；`ad2ac9af96e732b9407acc39dc7a21922e092e7dd9c7d05d32513ac1ac52a23d`；1591/3689 |
| C20；每臂600s | `reference/citibike443-regional-v1/instances/V20/cb443_V20_compact_r2_shortage_M02_Q20.txt`；`cb443_V20_compact_r2_shortage_M02_Q20_T10800`，V20/M2/Q20，T10800 | `9c61e0bd65053af1a260ff599bc438db7db0284f219b94492ac2eadec085855d` | `1303462215`；`905b7e8b154b218e446b0e116f6035acd2c6b03431e910e1d0040b7171c07cc0`；1551/3629 |
| B50；每臂1800s | `reference/citibike443-regional-v1/instances/V50/cb443_V50_regional_r1_balanced_M04_Q30.txt`；`cb443_V50_regional_r1_balanced_M04_Q30_T01800`，V50/M4/Q30，T1800 | `79ca3506aac00f52268199bd88596f7a512161f5dc19b75315a4bb576d41ceb2` | `-250521169`；`0a88f594dc64ecdcd86712d8b0584b0c1bf3fe22982f35176033bbcc2d5b6b7d`；13360/35618 |
| U6；每臂1200s | `reference/round82_unadapted_confirmation/U6.txt`；`round82-unadapted-confirmation-v1_U6`，V50/M4/Q30，T18000 | `1556e893376349de92f9213642d7be0005dcb44e47e037d34f77040711787e3f` | `1831047900`；`5979ffe9f6524c2dcddb705910e1e8b6002382b3fb1ddeb8712ebfb852082998`；13340/35588 |

旧 R87/R88 P 运行与新 LP-G **不**同期；本表的 fingerprint/LP SHA 是待核模型身份，不允许把旧 P 时间当新三臂认证时间。R90 的 [G3 资格 gate](../unified_exact_round90/g3_qualification_gate.json)绑定 binary、七核心源与旧 helper；[D6 源快照核查](../unified_exact_round90/d6_tail_preparation_report.md)另外核过固定 R90 ref 的165生产 Git blobs和一份 test。当前 R94 checkout 并非 R90 编译源快照，本审查不把当前工作树源码 SHA 假充旧 binary 来源，也未再遍历165个历史对象。只有实际 R90 binary hash、冻结 old adapter 和本次资格读回共同成立，才给新三臂同构建身份。

## 十二臂唯一顺序与成本边界

| 序号 | 角色/臂 | 完整进程 cap |
| ---: | --- | ---: |
| 01–03 | F2/P-GRB → F2/ENS-C → F2/LP-G | 各900s |
| 04–06 | C20/LP-G → C20/ENS-C → C20/P-GRB | 各600s |
| 07–09 | B50/ENS-C → B50/P-GRB → B50/LP-G | 各1800s |
| 10–12 | U6/LP-G → U6/P-GRB → U6/ENS-C | 各1200s |

最多十二独立进程、各只一次，进程 cap 总 **13,500 秒**；全批外层真实 launch-to-exit、逐臂完整进程、预检/离线审计/归档分别记账，内部 LP/MIP/起点成本只作嵌套分解。每臂 Threads/MIP Threads=1、Seed=0、Presolve=-1、零相对/绝对 MIP gap、CPU affinity=4；正式 native 限 `cap−6`、完整进程限 `cap`、shutdown margin=3、external hard stop near `cap−2` 的旧 R90 约定要对三臂同施。新的 source-only manifest 必须逐项列出十二真实命令、路径不共用、seed/顺序/截止、source/helper/binary SHA，并在零 Optimize prepare 中逐字验证；prepare 不发射资格或正式 Optimize。

## P 的真实身份与四次资格门

P 命令必须显式 `--method gurobi --plain-baseline --gurobi-model-export <new compact.lp>`，传每输入上表的 `--round24-expected-gurobi-model-fingerprint` 及与**R90 binary SHA**相同的 `--round24-executable-sha256`、`--round24-manifest-executable-sha256`。无 ENS `--algorithm-preset`/24+1/HGA start、无 `--round90-lp-g-split`、cut 或外部 incumbent/历史 U。ENS-C/LP-G 保持[R90 G3 命令](../../scripts/round90_lp_g_g3.py)的 `gcap-frontier`、24+1、old closure、证书控制器与参数，只允许 LP-G flag false/true 变化。[R88 三臂命令/审计](../../scripts/round88_a1_g3.py)给 P 隔离和 compact export 参考；不可直接把硬编码 ENS/LP 的旧 R90 runner 改个 arm 标签当 P。

旧 R90 binary 没有“只导模型”入口。计划的四次 P 资格是按 F2/C20/B50/U6 顺序、每次整个独立诊断进程最多15秒、共最多60秒；源核过的 `--time-limit 0 --process-wall-time-limit 0 --process-shutdown-margin 0` 实际原生 TimeLimit 被 clamp 到 `.001`，**每例仍调用 Optimize 一次**。这不是正式算法的内部切片，也不是面板计时；其搜索状态只能报告资格未知/删失，不参与选型。每例需核本次 `compact.lp` 全文件 SHA 等于上表参考、fingerprint/列/行/变量域、canonical `strengthened=false`、模型读回、真实参数 set/get 与生命周期，所有四例均过才可单独准入正式批。若模型字节、fingerprint、域或原问题身份不符，停止并解释；不得重写期望指纹以放行。

## 证据适配和正式结果门

原 P 的 `GurobiBaseline.cpp` 路径将 `spec.strengthened=false` 后写 canonical compact，按原参数 `Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0` 设置并读回，且把 set/get 返回码、effective 值、模型指纹与严格 gap 参数写结果；这必须对**本次 R90 binary 的实际资格和正式返回**复验，不能只凭当前源码文字。旧 [R86 native reader](../../scripts/round86_native_evidence.py)要求每条 native call `settings` 与原容差/参数一致，并区别全局界和局部作用域；其 `finalize_endpoint` 有真实 P 分支：可接受没有合法 U 的 time-limit、保留 L 或无 L，只有原物理见证才记 U；P 要核 domain audit、fingerprint、native lifecycle、严格 gap/readback。旧 R88 P 审计还直接比较导出 `compact.lp` SHA。R90 ENS/LP 则还需 root/parent-child 覆盖、leaf 模型/epoch/cutoff、split proposal/两子 LP/AM/native-target/atomic split 的真实事件，不能把请求或过期 depth 遥测记作证明。

本轮新 adapter 应对每次正常结束及被截断臂分别保留真实 PID/exit、外层秒表与完整进程 wall、未冲洗日志的可用性界限、原物理 U/可用时刻、**全局** L/作用域、gap、证书状态、Gurobi native set/get，外加所有失败前缀。每例三臂审计 `max(合法全局 L) ≤ min(物理 U)+既定1e−7`；缺 U/L 不凭空补，跨臂最强 L/最小 U 只查矛盾，不合成单臂证书。正常 cutoff 为 unknown，未 flush 不能宣称无后续动作；P 的最优值 witness 若证书未闭合仍只是 U。只有同角色两臂**均认证**才给完整认证时间比，证书原生可用时刻和完整进程费用分别保留；一臂 open 时只报告观察下界与删失。F2/B50 正例、C20 旧负例、U6 open 及旧 C2 反向/D6 慢化全部公开，不能用本四角色更替历史证据。

异常身份/物理/全局界/覆盖/参数/进程或资源故障立即停在已付前缀。若同角色配对出现原计划的非小例严重信号，完成必要同角色对照后即停并独立审查；单 seed 只叫风险，不叫确认回退。P 已认证而 LP-G 到截止仍 open 即使未越严重时间线，也阻断晋升推断。四角色都是已开发/保护输入，新数据 H1–H8 仍未生成；本批若正面最多支持准备后续冻结与论文资格，不支持默认改动或广泛长时运行。

作者的 [R94 machine preregistration](preregistration.json) SHA256 为 `767b8abe628bb5e84c8c44ddf2b65869f44212e17bea362fc0284b4afb445774`；[R94 thin runner](../../scripts/round94_lpg_contemporary.py) 当前审查字节 SHA256 为 `5dcb3e481aef4767ee16372ef3c095c88dd36e8635e10b1184edba8669cbc587`。本审查独立解析四角色，逐项与 R87 identity 的 `fingerprint/canonical_sha256/columns/rows` 比较、重新哈希四输入、R90 binary 与计划文件，均匹配。只读加载 runner 并调用 `modules`、`validate`、`formal_launches`、`qualification_launches`，得到166份冻结源记录、按上表精确排序的12条正式命令、4条 F2/C20/B50/U6 资格命令，正式 cap 合计13,500秒、资格 cap 合计60秒；当时 campaign 目录不存在。该调用没有执行 `prepare`、创建 campaign 或启动 ExactEBRP。AST 解析通过。

静态命令审查：P 每条使用独立 `gurobi` plain baseline、原 compact 输出、固定 fingerprint 和两个二进制 SHA 绑定，明确排除 ENS preset、LP-G split、HGA/外部 incumbent；ENS-C/LP-G 每个同角色的参数串除 split 值及各自输出路径外一致。正式运行借用冻结 R90 的完整进程 supervision、截止前 committed journal 观察与物理/原问题 global-bound 审计，P 单独转入冻结 R88/R86 的原 compact 和真正 P endpoint 分支；正常返回额外核五项 native 参数 requested/effective/set/get，P 的原模型维度、域、单次 Optimize、HGA 未请求。资格代码已补上 lifecycle、method/preset、return code 及 R86 committed journal 的一次 full-original call/settings/returned 交叉核账，仍须用**实际四次诊断结果**验证；不能仅凭源码判定已合格。

时钟和删失须按原收据口径解释：正式 `process_wall_seconds` 是 wrapper 起点至子进程退出的实测值，`prelaunch_seconds`、post-exit drain/restore、offline audit 和整批调用墙钟另列；资格 `whole_process_wall_seconds` 自每例监督起点至子进程退出，资格审计及 completion 写盘另计，故需外层秒表补全资格/正式总费用。原生证书可用时刻来自已提交事件或正常 finalize，不能用 cap 或采样时刻替代。`run_one` 对硬停、资源停、异常返回分开记录；正式 adapter 在没有物理见证时保留 U 未知，在没有 global native bound 时仅用分析性的非负 L。被 kill 后未冲洗日志视为未知，既不补证书也不假称动作未发生。每次有两个同角色端点时先做原问题跨臂矛盾核查，之后再看严重信号；首次问题即停在已付前缀。当前外部源静审 **PASS，可进行零 Optimize prepare**；不是资格或正式运行的准入。

作者随后仅执行了一次零 Optimize `prepare`，真实命令退出码0、外层 PowerShell 秒表从发射至退出 **1.066536秒**。[外层收据](prepare_outer_receipt.json) SHA256 `bbd3ce4df21334301eb8e6869f464902e370ed268a1f154b546b4c998d9803e2`；[prepared identity](runner_lpg_contemporary/identity.json) `295777d61db71e084e1822295c8fa588cc9732d747f57abc4ebd454053ba0066`；[preflight](runner_lpg_contemporary/preflight.json) `4e5ebef8a9f4509e61b79854c2a31dd06cc631a53df97b4ca8da129139506d8b`；[source snapshot receipt](runner_lpg_contemporary/source_snapshot_receipt.json) `7919085ca84ae9e41b309d27d72e6daf9d1309dc938e39b8cfded2f0dc8a285d`。本审查重算四份 SHA，`require_prepared` 对实际 identity、preflight、源收据及生成命令重新校验通过。源收据报告166个旧 ref Git blobs 字节匹配；我没有再次扫描其全部内容。真实 identity 有16个互异输出目录、12个正式臂依冻结顺序及4个资格臂，正式各臂 native/whole limit 分别为 `cap−6/cap`，四资格均 `0/0/0` 且外部15秒；无资格或正式目录、started 标记及 lease。**准备证据准入 PASS；四资格 Optimize 仍需独立 root lease**。不能从 `optimizer_calls=0` 单独推断历史或未来开销；这里只指本次 prepare。

执行依赖顺序：已完成 manifest/harness 源静审与**零 Optimize prepare** → root 资格 lease → 四次真实 P 资格及独立审核 → root 十二臂 lease → 固定顺序单槽正式批 → 独立小证据复核、全成本表和停/进决定。目前止于 prepare 审核 PASS，不能越过后续门。资格后要重新核四个 `compact.lp` SHA、fingerprint/域/维度、Gurobi set/get、native journal 实际 call/return、完整进程费用及失败前缀，再明确记录资格 PASS/阻断。
