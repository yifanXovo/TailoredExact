# R94 同二进制三臂确认：runner 可行性（源码/小型登记只读审查，未运行）

2026-09-28。范围仅为 [有限确认草案](lpg_confirmation_proposal.md) 的 F2/C20/B50/U6、seed 0、P-GRB/ENS-C/LP-G；这是 R94 条件准备意见，不是执行授权或新算法。当前 `E:\codes\ExactEBRP` 中只读取旧 runner、prereg、原模型源码及四份输入；未写 runner、未构建、未调用 Optimize，亦未核实时许可证/空闲机器。

## 结论与最小复用边界

冻结的 R90 `build/research/round90-lp-g-split/ExactEBRP.exe` 当前 SHA-256 实算为 `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`，与 R90 G4 登记相同。`src/main.cpp` 仍解析 `--method gurobi`、`--plain-baseline`、`--gurobi-model-export`、三项 Round24 模型/可执行绑定；`src/GurobiBaseline.cpp` 的 P 路径写 `strengthened=false` 的 canonical compact LP，原生求解不取 Tailored seed/增强模型。**无需为 P 修改生产源码**；但源码可调用只说明技术可行，最终还须冻结二进制、LP 字节与 native 资格。

最小新工作是一份独立 R94 manifest/三臂薄 harness。复用 R90 G3 的 `command_for` 两个 ENS/LP 命令、`run_one` 的整进程监督/commit 观察、`lp_g_split_evidence` 和中性交换复核；复用 R88 的 P 命令范式、`round86_native_evidence.audit/finalize_endpoint` 物理与作用域核验、三臂 `cross_arm_contradiction_check` 思路。不能直接更改旧 G3 prereg 增加 P：G3 `command_for` 无条件 `gcap-frontier`/ENS preset，`audit_launch` 按两臂解释 preset/LP 事件，`launches_for`、门与 cross-arm 固定 16 次/两臂。R88 的完整 runner 又绑定 A1、旧二进制/24 次与旧角色；只借独立函数/审计语义，不复制冻结文件或借其旧 P 时间。新 harness 必须冻结自身 SHA 与依赖读者、输入、二进制 SHA；独立存储路径，不改旧 runtime 和原始档。

**P 命令须补齐草案中未列出的证书绑定选项**：除了 `--method gurobi --plain-baseline --gurobi-model-export <arm>/compact.lp`，还需 `--round24-expected-gurobi-model-fingerprint <该角色指纹> --round24-executable-sha256 <R90 SHA> --round24-manifest-executable-sha256 <R90 SHA>`。`src/GurobiBaseline.cpp` 在严格证书判定时明确要求这两项可执行字符串一致且非空、预期模型指纹非零且匹配；缺失会使即便 native OPTIMAL 的 P 也不能给原问题严格认证。P 不带 `--algorithm-preset`、`--round90-lp-g-split`、任何 ENS/24+1/HGA/MIP start/外部 UB/cuts；保留 R88 的 `--round61-candidate-mode off` 及共同日志/证据路径。ENS-C/LP-G 沿 R90 命令，仅 split false/true；全部 1 thread、MIP thread 1、Seed 0、Presolve -1、原生相对/绝对 gap 0、完整进程 cap、native `cap-6`、硬停 `cap-2`、退出 margin 3，单槽串行。不能把三臂的时间额度当组件预算。

## 四份完全相同的原问题身份

下表输入 SHA 已对当前本地文件重新计算，与 R90 G3/G4 prereg、19 角色规划/输入审计一致；`LP SHA`/指纹来自 R87 campaign 的零 Optimize canonical export 登记（F2 又与 R86、C20/B50 与 R58 预检一致）。这些是**预期 ancestry**，不是 R90 二进制的已验证新 export。

| 角色 | 输入相对路径、SHA-256 | scenario；T；完整每臂 cap；顺序 | 预期 compact LP SHA-256；Gurobi fingerprint |
|---|---|---|---|
| F2 | `reference/round86_unadapted_confirmation/F2.txt` `ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e` | `round86-unadapted-varied-structures-v1_F2`；3600；900；P→ENS→LP-G | `ad2ac9af96e732b9407acc39dc7a21922e092e7dd9c7d05d32513ac1ac52a23d`；788240696 |
| C20 | `reference/citibike443-regional-v1/instances/V20/cb443_V20_compact_r2_shortage_M02_Q20.txt` `9c61e0bd65053af1a260ff599bc438db7db0284f219b94492ac2eadec085855d` | `cb443_V20_compact_r2_shortage_M02_Q20_T10800`；10800；600；LP-G→ENS→P | `905b7e8b154b218e446b0e116f6035acd2c6b03431e910e1d0040b7171c07cc0`；1303462215 |
| B50 | `reference/citibike443-regional-v1/instances/V50/cb443_V50_regional_r1_balanced_M04_Q30.txt` `79ca3506aac00f52268199bd88596f7a512161f5dc19b75315a4bb576d41ceb2` | `cb443_V50_regional_r1_balanced_M04_Q30_T01800`；1800；1800；ENS→P→LP-G | `0a88f594dc64ecdcd86712d8b0584b0c1bf3fe22982f35176033bbcc2d5b6b7d`；-250521169 |
| U6 | `reference/round82_unadapted_confirmation/U6.txt` `1556e893376349de92f9213642d7be0005dcb44e47e037d34f77040711787e3f` | `round82-unadapted-confirmation-v1_U6`；18000；1200；LP-G→P→ENS | `5979ffe9f6524c2dcddb705910e1e8b6002382b3fb1ddeb8712ebfb852082998`；1831047900 |

全部 `lambda=0.15`、pickup/drop 各 60 秒、seed 0。R94 的 cap/顺序特意不同于历史 R90 F2=600、C20=1200、B50=3600；须写进新 prereg，不覆写旧配置。12 臂总上界 13,500 个**进程**秒；预检/离线审计/归档另记完整墙钟。

## 原生设置与 U/L 审计可复用性

P 的 `solveGurobiBaseline` 对 Threads=1、Seed=0、Presolve=-1、MIPGap=0、MIPGapAbs=0 都执行 set/get；模型读入后再从 model environment 读回，结果含 requested/effective/set/get return code。其 `configuration_valid` 与严格证书又核线程、Seed、Presolve、两 gap 与原生时间限制。ENS/LP 的 R90 G4 `native_parameters` 核 normal result 中 Seed/Threads/Presolve 的 requested、effective 和 set/get=0；R86 journal reader 在每个完整 native call 的 `settings` 中核 Threads/Seed/Presolve/两 gap 与容差。R94 还应对三臂正常结果直接核 **五项** requested/effective/set/get；截止无 `result.json` 时只能凭已提交 journal 的实际 `native_preconditions/settings` 称已观测，不能用命令替代 readback，也不能从无 flush 推断从未发生。

R86 reader 已用独立 `analyze_round61.physical` 重算每个提交 witness 的原 T、G/P/F，并用 call scope 的 full-original 或 cover/leaf/cutoff 重放全局 bound；正常结果的最终 witness 再物理核验。P 可无 incumbent：保留 `U=null`、合法 ObjBoundC/global L、`time_limit` 未认证。三臂同一原问题用 R88 的 `max L <= min physical U + 1e-7` 冲突检查；不把他臂 U/L 合并成某臂端点。LP-G 继续核 proposal→两子 LP→AM→native target→atomic split 与叶/decision ledger，即使 depth 遥测为零。终止原因、完整进程墙钟、首次可用时间、commit 时刻、raw/模型/日志 hash 和大小均随臂保存；异常或账本缺口停在已付前缀，不能把 open 判为认证。

## 发跑前有限资格与阻断

1. 先冻结新 manifest/harness/审计依赖字节、上述四输入、R90 二进制及 R90 资格源身份；零 Optimize dry-run 生成 12 条命令并机械断言 P 仅 plain compact、ENS/LP 只差 split，cap/顺序/参数/路径/一次性目录正确。旧七源 SHA 是 R90 冻结快照，不证明当前工作树与旧二进制相同；以二进制 SHA 和旧资格收据为准。
2. 不覆盖旧模型。P 小资格要用**同一冻结 R90 二进制**导出四个 canonical LP、记录每个文件 SHA/行列/原生 model fingerprint/domain audit，与上表 ancestry 逐项比较，并测试五项 native set/get 和 Round24 绑定；`--gurobi-model-export` 本身通常随 P 求解流程，不能把这项说成已完成零 Optimize。若只可经一次带极小 native 限时生成，必须预先单列为有成本的资格调用，不能混入 12 臂；若 LP 字节或指纹不同，停下解释模型等价性并重新资格，不能强行采用旧指纹或静默重设基准。
3. 独立审查新三臂 audit adapter，特别是 P 被 hard-stop、无 incumbent、无 final result、partial journal，及 LP-G root/leaf 账本；检查 Gurobi 13.0.2、许可证/路径、core affinity、磁盘/内存/无重叠 solver，确认源/二进制/manifest/资格哈希与单槽资源门。全部通过后才可单独授权运行；每臂审计通过方发下一臂，失败前缀及额外资格成本保留，不补跑/换例。

静态证据入口：`scripts/round88_a1_g3.py` 的 `command_for/audit_launch/cross_arm_contradiction_check`；`scripts/round90_lp_g_g3.py` 的 `command_for/audit_launch/run_one`；`scripts/round90_lp_g_g4_priority.py` 的 `native_parameters`；`scripts/round86_native_evidence.py` 的 `audit/finalize_endpoint`；`src/GurobiBaseline.cpp` 的 `solveGurobiBaseline`；`results/unified_exact_round87/campaign/identity.json` 的 `references`；R90 三份 prereg。当前结论是**有明确可复用路径，尚未取得 R94 发跑资格**。

### 补充：冻结 R90 `ExactEBRP.exe` 的零 Optimize 导出入口审查

R90 主程序未见 `--export-only`、`--method lp` 或其他 canonical compact **仅导出**分支。`src/main.cpp` 将 `--method gurobi` 直接分派给 `solveGurobiBaseline`；其中 `--gurobi-model-export` 只指定 LP 路径，写 LP、启动 Gurobi、读模型/指纹/域与参数后，仍无条件走到 `api.optimize(model)`。因此**不能把 R90 主程序的 P 导出写成零 Optimize 资格**。R87 `scripts/round87_research.py::prepare` 的九次零 Optimize export 实际调用独立的 `Round65ReferenceBuild.exe`；`src/round65_reference_build.cpp` 只 `writeCanonicalCompactModel`、`GRBreadmodel`、读 `Fingerprint/NumVars/NumConstrs`，自身没有 `GRBoptimize`，但 R90 冻结目录只存在 `ExactEBRP.exe`、没有这一已冻结且同构建的 reference 可执行文件。旧 R87 reference 只做 ancestry，不证明 R90 二进制本次 export。

若要维持冻结 R90 主二进制且避免再建第二程序，有限资格应事先登记为**四个独立诊断进程、每个外部完整进程上限 15 秒、每个至多一次 native Optimize**，仅用于原 compact 身份/原生参数读回，任何 U/L/时间不进正式三臂比较。可用同一 P 命令（含原模型导出、seed/thread/presolve、Round24 三绑定）但 `--time-limit 0 --process-wall-time-limit 0 --process-shutdown-margin 0`，另以 15 秒外部 watchdog 控制整个进程；`ProcessPhaseLedger::nominalBudget` 在两项内部 limit 都为 0 时不开共同 deadline，`solveGurobiBaseline` 两次 `TimeLimit` 设置及 Optimize 前设置均把 0 clamp 为 **0.001 秒**，然后确实调用 `api.optimize(model)` 一次。若把 `--process-wall-time-limit 15` 同时传入，则 Optimize 前会改为当时**剩余约 15 秒**，不再是 0.001 秒；故不能这样写诊断命令。资格失败/被外部杀时保存 LP/日志/partial journal 并停止；只有正常返回的 result 与 LP SHA、fingerprint、native domain、五项 set/get 全部通过才放行。四次 Optimize 和全部外层墙钟、失败前缀必须单独计费，不得称作零 Optimize 或正式配对臂。此处仅静态核源码语义，未实际发出任何进程。
