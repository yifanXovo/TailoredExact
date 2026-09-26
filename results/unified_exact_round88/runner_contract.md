# Round 88 首轮诊断与八例筛选：Runner 合同草案

**启动闸门。** 本文只预备执行合同，不授权立即启动性能进程。先等实现者冻结候选源码/参数/构建哈希，理论与反例、微型精确验证、物理可行性及界作用域检查由独立审查者通过；Runner 另做输入、场景、命令、可执行文件、模型元数据与完整成本身份核验。上述资格及预注册的运行顺序/输出目录落盘后，才启动 G3 性能批次。此前可读取历史数据并准备诊断，不对正在变化的二进制计正式结果。依据：`../../research_plans/ensc_optimization_plan_2026-09-26.md` 第 39–67、267–280 行。

## 固定输入与完整过程上限

共同场景：`lambda=0.15`，取/放各 60 秒，单车容量 Q 如表；T 是**原问题路线时域**，不是求解器截止。输入以仓库根目录 `E:/codes/ExactEBRP` 为相对路径基点；发射前重新核验 SHA256。表内身份来自 R83/R85/R87 协议，其中 R87 的共同参数见其 `common` 节。

| 角色 | 场景 ID；V/M/Q/T(秒) | 输入路径与 SHA256 | G3 每臂完整过程上限 |
| --- | --- | --- | ---: |
| E8 | `round39_small_easy_V12_M3_Q30_slot08_seed1167625600`；12/3/30/3600 | `reference/qualification_round39/small-easy/round39_small_easy_V12_M3_Q30_slot08_seed1167625600.txt`；`587737b9d000c1712220232a0fe957073f1f03ac649a63a4775abd9166603acd` | 120 秒 |
| S12 | `cb443_V12_regional_r1_surplus_M01_Q30_T10800`；12/1/30/10800 | `reference/citibike443-regional-v1/instances/V12/cb443_V12_regional_r1_surplus_M01_Q30.txt`；`060ee6366b2277c8427675e1a1484de7db10d2ef82a64d4e2ffa6e4695b7b626` | 120 秒 |
| D3 | `round39_small_medium_V12_M3_Q30_slot08_seed1343324363`；12/3/30/2850 | `reference/qualification_round39/small-medium/round39_small_medium_V12_M3_Q30_slot08_seed1343324363.txt`；`29e0ca2c95ec2e061aa1cc524aaf6a41bf6c4a34355dca86df6966aa8a29b6b4` | 600 秒 |
| C2 | `cb443_V20_compact_r1_surplus_M02_Q30_T01800`；20/2/30/1800 | `reference/citibike443-regional-v1/instances/V20/cb443_V20_compact_r1_surplus_M02_Q30.txt`；`1bb4898eef8e5b2535a6d1d609637528875581fa81acf120636941f285f23b60` | 600 秒 |
| D7 | `cb443_V50_regional_r1_shortage_M04_Q30_T18000`；50/4/30/18000 | `reference/citibike443-regional-v1/instances/V50/cb443_V50_regional_r1_shortage_M04_Q30.txt`；`d7dbd018331b9d5f3d84c0fd6c907560ef1fa92a2f8c153ac7d81e46a6cd4e9c` | 1200 秒 |
| U6 | `round82-unadapted-confirmation-v1_U6`；50/4/30/18000 | `reference/round82_unadapted_confirmation/U6.txt`；`1556e893376349de92f9213642d7be0005dcb44e47e037d34f77040711787e3f` | 1200 秒 |
| F5 | `round86-unadapted-varied-structures-v1_F5`；50/4/30/7200 | `reference/round86_unadapted_confirmation/F5.txt`；`5145b134f52dc573900b0b271325639fb04dc5eed37bf996f6b984f74efacc8a` | 1200 秒 |
| F6 | `round86-unadapted-varied-structures-v1_F6`；50/4/30/18000 | `reference/round86_unadapted_confirmation/F6.txt`；`aeda223c50294226f6447e2cd2a6fe023fbf22e84a67e2bfa1f61d3dba919925` | 1200 秒 |

每臂计划中的**进程墙钟**上限合计 6240 秒；三臂全重跑的进程墙钟上限合计 18,720 秒（5.2 小时）。这些数字只有在每臂必需的所有准备都落入同一计时边界时，才也是端到端上限；如有进程外且每次运行必需的预处理/模型准备，应另定覆盖它的端到端截止并把实耗计入该臂，不能伪称 18,720 秒已涵盖。候选启动、模型构建、搜索、见证验证与收尾属于该臂完整运行墙钟。开发编译、独立机制诊断、通用且预先冻结的 P 模型指纹审计、批次结束后的离线验收属于另外列账的研究成本，不冒充某臂提速。计划源：`../../research_plans/ensc_optimization_plan_2026-09-26.md` 第 52–62 行。输入身份源：`../unified_exact_round83/protocol.json`（E8）、`../unified_exact_round85/protocol.json`（S12/D3/C2）、`../unified_exact_round87/protocol.json`（D7/U6/F5/F6）。同一角色若来源协议另有旧实验 cap，以**本表的新 G3 完整过程 cap**为准；不能把旧 T、旧 cap 或别轮的运行拼接。19 个主面板输入、实际哈希和 T/lambda/handling 已在 `input_identity_audit.json` 逐项复核，全部一致；正式发射仍核对本次冻结身份。

## 诊断、命令与环境

G2 使用冻结 ENS-C LP 状态或保存的物理见证做离线/隔离诊断：启动路径独特初始和终止见证、下降贡献及成本；B1/B2 切割违背、根界增量、行列非零元、构建/分离开销；C1–C3 当前分裂建议、真实 decision/leaf ledger 和深层 fixture。诊断默认每例**整个独立诊断过程** 120 秒，输出仅为机制证据；`unknown` 是证据不足，不能自动认作 cut 无效、分裂不可能、问题不可行或正式算法切换依据。若需扩大诊断，另行登记。历史 witness/界/已知最优值只进入离线诊断，正式候选每次从原始输入开始。

当前只读确认存在：`D:/msys64/ucrt64/bin/python.exe`、`D:/msys64/ucrt64/bin/g++.exe`、`D:/gurobi1302/win64/bin`，以及 `E:/codes/ExactEBRP-round66/build/round83/v1/ExactEBRP.exe`（SHA256 `25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e`）和同目录 `Round65ReferenceBuild.exe`（SHA256 `f9456c99759c9e9e62dcf19cc13300ce55f6d30d616d0547e75026a1d68fa3c3`）。两项哈希本轮只读重新计算并与 R87 协议一致。R83 二进制可复用作冻结 ENS-C 与原始 P 对照及零 Optimize 的 P 模型指纹参考；**它不是尚未实现的 R88 候选**。新候选须在仓库内部独立 build 目录构建、资格验证并锁定哈希，不覆盖旧二进制。Gurobi 13.0.2、Windows UCRT 及运行 PATH 见 `../unified_exact_round86/reproduce.md`；命令构造范本见 `../../scripts/round83_research.py` 第 74–91 行、`../../scripts/round86_research.py` 第 92–109 行、`../../scripts/round87_research.py` 第 170–191 行。

R88 尚无可执行的正式 driver 入口，Runner 应先生成并独立审查 `scripts/round88_research.py prepare|run` 之类的**新入口**和新协议，不调用 R83/R86/R87 的正式 `run` 命令重启旧 campaign。准备阶段核验输入哈希、参考模型指纹、源/编译器/二进制与参数身份，生成每臂精确 argv、输出路径、预定执行顺序和最大总成本，零 Optimize。建议沿用历史完整命令字段：`--input --lambda --T --pickup-time --drop-time --time-limit --process-wall-time-limit --process-shutdown-margin --threads 1 --mip-threads 1 --gurobi-seed 0 --gurobi-presolve -1 --method --out --log --process-phase-ledger --external-gini-artifact-dir --primal-heuristic-generation-log --progress-log --native-evidence-dir`。P 臂 `--method gurobi --plain-baseline` 并验证原始 compact 模型指纹；冻结 ENS 臂 `--method gcap-frontier --algorithm-preset research-round83-vds-equal-net-exchange --round65-witness-audit true --round65-hga-zero-stop true`。候选臂的 preset/开关必须由完成资格的实现合同确定，不能借历史 preset 名称伪装新算法。需要按各臂 deadline 单独推导原生 time-limit 和外部 hard stop，并记录统一进程 wall 起点；R83/R86 的现成范本是 `cap-6`/`cap`/`cap-2` 与 3 秒 shutdown margin，不能将 cap 拆给内部组件。

### B1/B2 最优传输（OT）诊断的可行性边界

只读环境探针显示，`D:/msys64/ucrt64/bin/python.exe` 与 `E:/codes/ExactEBRP-round66/build/round81/plot_env/Scripts/python.exe` 均可启动，但 `import gurobipy` 均报 `ModuleNotFoundError`；此处只尝试导入，未创建模型或 Optimize。因此当前不能把 Python `gurobipy` 脚本列为现成可执行的 B1/B2 LP 诊断入口。Gurobi 13.0.2 原生运行库及 C++ 后端仍在；若采用 Python，应先以单独环境准备和只读版本核验补齐依赖，再对诊断脚本做资格审查，不把依赖准备算作算法收益。

已有原生 `E:/codes/ExactEBRP/build/official-round53-5b1e7d5bb/Round50IntervalMipExperiment.exe` 可作**历史固定区间模型**探针。源码 `../../src/round50_interval_mip_main.cpp` 第 166–210、1247–1264 行允许 `--mode lp`，输出 `lp_result.json`、`lp_variable_evidence.csv`（含 primal_value）与 `lp_constraint_evidence.csv`；既有固定状态和 `canonical_model.lp` 见 `../gf_k1_interval_mip_vnext_round50/fixed_interval_state_manifest.csv`、`../gf_k1_interval_mip_vnext_round50/state_reconstruction/models/D1/`。它自行构建 K1/旧 fixed-interval 规范模型、需要区间与 cutoff，**不能直接载入 R87 ENS-C 的 LP，也不能把其 LP 向量当作当前 ENS 松弛**。本轮没有启动该可执行文件。

当前冻结 ENS-C 可复用的只读模型例子：`E:/codes/ExactEBRP-round87-runtime/campaign/local_raw/03_D7_ENS-C/external/models/L0.lp`，同目录还有子区间 LP；`.../03_D7_ENS-C/result.json`、`external/initial_witness.json`、`external/native_0_witness.json`、`hga.csv.descent.csv` 保存结果/物理或启动见证，P 原始 compact 对照为 `.../04_D7_P-GRB/compact.lp`。D6、U6、F2、F5 另有同型原始目录。LP 文件是冻结模型快照，见证是整数物理解；目前未确认 R87 raw 中存在与这些 ENS LP 精确同模型同状态、带 `s_iy`/`q_iy` 分数值的已验收最优 LP 原始向量。B1/B2 可先对模型结构与保存见证做零求解解析、反例和整数有效性核验；真实松弛违背、根界增量和切割成本仍须取得**身份匹配的 LP 解**，由新受审原生诊断或确认可用的 Python 环境产生，再与无切割对照完整计费。历史 frozen LP/见证只作开发诊断输入，不能带入正式性能臂。

## 串行执行与证据交付

只设一名 Runner 对性能进程与构建时段负责；同机正式 solver 串行，不与另一 solver、构建、重审计、压缩或绘图争资源。三臂每例均独立从合法原始输入启动，使用相同 Gurobi 版本、线程 1、solver seed 0、Presolve Auto、认证容差、亲和性和场景参数。每臂所需的全部 LP、MIP、启发式、验证、模型重建及进程启动均完整计费；P 不接收候选 Start/cuts/历史界。若某臂每次运行都必须在进程外生成模型或导出参考文件，该准备从该臂端到端计时起点纳入，双方使用一致边界并同时报告进程墙钟与端到端墙钟。一次性的公共冻结模型指纹核验可单列审计成本，但不得掩盖实际每次运行必需的准备。每臂只有一个完整全局截止；原生调用最多继承该 deadline，禁止组件级秒数/Work 配额、到时换组件、重启拼轨迹或按 ID 选择算法。

轻量常规采样由 Runner 自行落盘，记录物理可行 UB、同运行有效全局 LB、gap、证书状态、首次合法可用时刻、阶段成本、原始日志/见证/账本哈希；采样和 `runtime_status` 不是正式终点或证书。进程存活、普通 gap 变化、下一条已预注册运行的启动不唤醒 Astra。只在批次完成、正确性/证据异常、预注册停止条件、资源故障或合同无法执行时汇报。中断与异常保留原始目录及删失终点；不重跑覆盖、不从不同过程拼 U/L、不将缺 U 写作 0。有限诊断 `unknown` 继续标为未决，不能用作正常选型。正式端点经独立物理见证/界作用域与全计费审查后才用于晋级；只复用身份可比的历史记录作开发筛选，并明确不等同新一轮配对重复。

Runner 自身模型/effort 在正式委派前按本地会话 `turn_context` 记录核实，与预定 Sol high/xhigh 一致；旧核验示例及其边界见 `../../research_plans/agent_workspace_verification_2026-09-26.json`、`../../research_plans/ensc_optimization_plan_2026-09-26.md` 第 242–264 行。记录层核验不能证明服务端不透明路由，但不应只凭代理自报。交付 `run_manifest.json`、全部原始结果与失败/删失账本、完整 U/L/gap/认证时间表、成本账本、独立验收结果及 PASS/FAIL/INCONCLUSIVE 决定；保护旧结果，Round 88 使用独立输出目录。
