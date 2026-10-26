# R94 LP-G 同二进制三臂有限确认：独立协议与数学审查

**结论：有条件通过，限于一次有限研发分流，不是 LP-G 晋升资格。** [草案](lpg_confirmation_proposal.md)固定 F2、C20、B50、U6 的 seed 0、三臂、顺序与上限，确实可补上“R90 LP-G 没有同期 P-GRB”的一部分缺口；但四例均是开发兼保护输入，不是新数据，也不能代表全局均值或跨 seed 稳健性。每臂完整 `ExactEBRP` 进程 cap 依次 900/600/1800/1200 秒，最多 12 臂、13,500 **进程**秒，预检/离线审计/归档另计外层墙钟。单槽串行、按冻结顺序逐臂审计、故障/严重信号停在已付前缀、零补跑/延长/替换，使问题可证伪且资源有限。后续真正 H1–H8 必须先冻结生成器、候选和全部运行规则，再整体保留结果；当前已有 `unadapted` 文件名不赋予未见身份。

## 判定合同与解释边界

1. 主指标是从每臂完整进程启动到**原问题可用数值证书**的外层 wall。两臂都认证才计算其实际认证时间比；一臂 open 只给认证/删失关系与同截止合法 U/L，不把 cap 当认证时间。F2、B50 的旧收益是 R90 同二进制 ENS-C 对 LP-G 的开发证据（约 0.532、0.664 倍）；本批若同 cap 双认证，应完整报告新比值及方向。原计划“两例大实例 ≥20%”是强证据目标，不是临时调参或硬认证门；`t_LPG/t_ENS≤0.8` 可作保留该实践幅度的描述，`≥1` 则本批无速度收益。任何单 seed 方向都不能称已跨 seed 确认。
2. C20、F2、B50 的相对 ENS-C 及所有有资格的相对 P-GRB 双认证比较，按原计划的**非预标小实例**严重线判：`t_LPG>1.5·t_ref` **且** `t_LPG−t_ref>30 s`。若 ref 已认证而 LP-G 在同 cap open，仅在其已付删失下界 `c>1.5·t_ref` 且 `c−t_ref>30 s` 时标严重风险；未越线仍是证书丢失/未决，不能填一个伪比值。C20 旧约 12.2% 慢化须入表；若本批更差，不能因 F2/B50 正例将其平均抹掉。单次越线触发停扩与独立核误，但**不是**原计划“三次中两次同向且中位数过线”的已确认严重回退。
3. U6 或任何同 cap 双 open 只在双方有物理 U 与原问题全局 L 时计算**剩余绝对目标 gap** `g=U−L`，先核 `L≤U+原有容差`；仅容差内的微小负差可按 0 解释，超出则是正确性阻断。严重风险条件为 `g_LPG>1.5·g_ref` **且** `g_LPG−g_ref>0.01`，对 ENS-C 与可比 P 分别记录；不要把相对 gap、缺 U、作用域不全的 L 或单个 checkpoint 代入。未形成双方合法 gap 时报告不可比和各自 U/L。一般 “明显” 线是 `>1.1·g_ref` 且绝对差 `>.001`，只作研究信号；最后截止严重线不能由短暂曲线交叉取代。
4. 同期 P 的“明显劣势”要作为**预定保护信号**：若 P 已认证而 LP-G 同时认证但越上述严重线，或 LP-G open 且删失下界越线，停批核实；P 认证而 LP-G open 即使未越严重线也阻止直接晋升、结论为未决/证书丢失。P open、LP-G 认证可给同 cap 下的一侧有利删失证据，却不能写实际 P 认证时间比。P/LP-G 同时 open 只给合法 U/L/gap。F2 的历史 P 在 ≥70,647.797 秒仍被配额中断，因此 900 秒 P 臂很可能不能给双证书；本批虽是同期 P 观测，**不能许诺它会解决最终 P 速度比**。若任何 P 证据与 ENS 负例冲突，结论“未决”；结果好看也最多支持投入冻结新数据/论文资格，绝非直接晋升。

数学资格沿用 R90 已核 LP-G：仅当当前完整最优 parent LP 的 `G_LP` 是严格内点，才取该点作建议分裂，否则用旧中点；同一 `p` 的两子域共享端点，完整双子 LP/AM、depth 8、宽度/终端/原全局截止不变。固定 parent 点的 product 行原始违反量性质只解释该点，**不保证**任一子界严格提高、实际 atomic split、总证明提速或相对 P 优势。D6 曾两次建议、零实际 atomic split 仍认证，R94 必须分别账记 proposal、双子 LP、AM、native-target、atomic split 与终端闭合，不把请求当证书。有限停止依赖冻结有限实例/epoch 门禁、每次调用可终止或全局截止；不能由这一轮四例推出新一般收敛定理。Gurobi 证书是既定容差下的数值证书，非有理证明；R92 暴露的旧 canonical 边界限制须按固定输入原物理/模型审计披露，不能因同二进制就宣称任意实数输入完全忠实。

## 三臂实现前置条件

[runner 源审](r94_runner_feasibility.md)已核 R90 二进制现存 SHA `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`，其源码有独立原 compact `--method gurobi --plain-baseline` 路径；R90 G3 runner 却固定双臂 `gcap-frontier`，**不能直接加 P 名称**。需新薄 harness 保留冻结 R90 ENS-C/LP-G 命令，仅 split false/true；P 必须另外传 `--gurobi-model-export <新独立路径>/compact.lp`、`--round24-expected-gurobi-model-fingerprint <该角色>`、`--round24-executable-sha256 <R90 SHA>`、`--round24-manifest-executable-sha256 <R90 SHA>`，否则原 P 严格证书检查可能失效。P 绝不携带 ENS preset、24+1 启动、LP-G flag、MIP start、历史 U 或增强 cuts。四个预期 compact LP SHA/指纹来自旧 ancestry，**不等于** R90 二进制的新导出已验证；必须先以同 binary 的有成本资格验证，差异停下解释，不能静默覆盖。R90 主程序无真正零 Optimize 的 export-only 入口，不能预支免费的同二进制导出结论。

三臂均核原始数值参数的实际 native set/get 与 effective Threads=1、Seed=0、Presolve=-1、MIPGap=0、MIPGapAbs=0；正常退出和被硬停的 partial journal 各按可见证据处理。物理 witness 由原 Evaluator 对路线、库存、前缀载量、返仓时间及 F/G/P 重验；每个 L 核原问题全局作用域/覆盖/epoch，P 原 compact fingerprint/LP SHA 另核。同原题三臂 `max L≤min U+原有容差`，异常先查证书而非写性能结论。新 harness/manifest/审计依赖与固定输入/旧 binary、模型导出、原生设置和机位均须先冻结并获独立零 Optimize 命令/身份资格。primal 进一步核源码发现冻结 R90 主程序**没有 export-only 入口**；`--gurobi-model-export` 之后仍无条件调用 `GRBoptimize`，R87 的零 Optimize 导出来自另一可执行文件，不能冒充 R90 导出。若使用同 R90 binary 作四角色模型资格，可另行预注册四次独立、有成本的极短 native Optimize，例为 `--time-limit 0 --process-wall-time-limit 0 --process-shutdown-margin 0` 加外部各 15 s 整进程硬限；Gurobi 内部 TimeLimit 最小约 0.001 s，**仍是四次 Optimize、最多再占 60 进程秒**，不能算进正式 12 臂，也不能声称每次一定在硬限前完成 LP export。资格失败即停并保留前缀，不自动延长；这些调用须另获 root 准入。任何 production 修改都使旧 R90 binary 身份失效，需停止并重新三臂资格。

综上，这是一份合理的**有限同期 P 分流试验**，不是对 R90 正例的独立新数据确认。即使四例没有阻断，后续仍须原计划的三 seed 风险确认、新数据保护、K1/ENS/P 证书比较，以及用户要求的实际编译且逐页检查论文 PDF，方能讨论晋升与广泛长时 campaign。本审查只读小报告/源码，没有构建、求解、调用 Optimize、Git 或新试验。工作目录 `E:/codes/ExactEBRP`；会话日志 `C:/Users/Administrator/.codex/sessions/2026/09/28/rollout-2026-09-28T12-55-39-01a0e65e-5f9f-7b92-9e7b-975d53f9cc35.jsonl`。
