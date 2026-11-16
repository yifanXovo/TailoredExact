/goal

# Round169：检验统一目标重加权初始化的付费价值，收束当前论文的算法结论

## 0. 目标、研究增量与工作容量

继承已完成的 Round168。本轮只检验一个尚未实施过的具体候选：**保留当前 GI-TBC/B 的完整 own-H，额外以固定的 `lambda/2`、`2*lambda` 各运行一次完整 H，把所得物理 fleet 按原始 lambda 重新验证、评价，选择原目标最好的自有 Start，再进入未改变的 B 精确搜索。**设置同样两个额外随机流、同样完整 H 但始终搜索原 lambda 的多启动对照，判断收益是否来自改变搜索目标，而非仅增加随机起点。

先做一次很小的 H-only 筛选；仅在出现预先定义的独立收益时，执行本 prompt 已经完整授权、冻结的有限 B/M/C 付费比较。筛选未通过也是完整结果，直接结束这一固定候选，不增加权重网格、搜索时长或其他机制来寻找胜例。

本轮的依据和限制必须同时保留：

- R168 说明七个保存骨架在完整固定顺序家族内达不到同输入档案目标，C35 Seed0 即使放开原 owner 内的顺序仍达不到。继续加数量、重排或放大相似条件 MIP 的信息价值已不足，关闭该扩张。
- R166 确认同物理输入 `R-X35-S-T2` 的 rho≈2 最终 fleet 在原 rho≈1 目标下优于原 rho≈1 最终 fleet，G/P 同时改善。这说明有限搜索错过了更好解，**不证明廉价多权重 H 有效**。该好 fleet 不是约 1.4 秒所选 own-H 的产物，首次发现时间尚未核实；不能用最终 `T_produce≈2371s` 充当 first-hit。
- 本轮是“统一的目标扰动能否改善这套有限物理搜索”的可证伪检验，属于实践竞争力研究。目标聚合、局部搜索与多启动已有文献；合法 fleet 的跨目标回收是基础正确性，不包装成新的 OR 理论。

**当前 B/GI-TBC 默认不变，C166、D167 和新 C169 均不默认启用。**本轮最积极的决定也只是进入以后独立的正式确认；单个 Native Seed 的小面板不足以晋升默认、宣称稳健胜过 P-GRB 或解决 OR 期刊所需的通用方法贡献。

### 0.1 有限预算与 C++ 约定

总科学工作容量 **8h = 28,800s**，目标约 4–6h，完成即停止。包括定向历史/源码阅读、推导、实现、计算、分析、有限改稿、构建及复核。容量不是最短执行时间。普通 Git/公开恢复传输 I/O 单列；进入完整面板前至少保留 90min 用于分析、复核和交付。

| 计算部分 | 硬容量与用途 |
|---|---|
| 小例和接口资格 | 总外层不超过 300s；验证实际风险，不新增一套 MIP/oracle 资格工程 |
| H-only 筛选 | 7 个原问题、每项最多 5 次完整 H，共最多 35 次；共同外层容量 1200s |
| 有条件的完整方法面板 | 六个 R163 输入 × B/M/C × Native Seed0；n20 每臂 300s、n35 每臂 600s，共 18 个位置，名义 process-cap 总和最多 8100s = 135min |
| 新完整 P/PS/E+、新权重网格、第二 Native Seed | 本轮不安排 |

实际优化提前合格认证就正常结束，不用满预算。H-only 阶段不调用 Gurobi Optimize；完整阶段按 B 的实际调用链记录全部 LP/MIP 和检查开销，不能用 18 个进程数代替实际 Optimize 次数。

**新增研究 driver、完整 H 调用、候选选择、目标回评、物理验证、Start 映射以及所有实际优化均由 C++ 实现和执行。**可直接用 Gurobi C/C++ API。Python/Node 只做编排、只读独立复算、日志、表格及文档；不得让 C++ 外壳调用 Python 优化核心，不得用 Python 代建优化模型。

统一倍率、固定有限调用数和预注册 seed 不依赖实例名、城市、历史胜负或硬件速度。实验 cap 和下述经费准入条件只管理研究预算，不能进入候选在线分派。原方法已有的全局截止时刻继续适用于整个运行，不新增按耗时、Work、停滞或已知 P 目标切换的策略。

## A. 本地入口、继承身份与 PR

遵守仓库 `AGENTS.md`、`WORKSPACE_POLICY` 及工作区约定。全部新工作、缓存、临时件和交付放在 `E:\codes\ExactEBRP-work` 内；保护原 `E:\codes\ExactEBRP`、历史证据和用户活动 worktree。

`E:\codes\ExactEBRP-work\worktrees\paper-current` 曾停留在旧轮且存在未提交修改，先只读核实，不 reset/stash/覆盖。基于核实后的 R168 创建或接续 `E:\codes\ExactEBRP-work\worktrees\round169`，建议分支 `codex/round169-primal-reweight`。已有同轮工作则按 manifest 接续，避免重复运行。

| 身份 | 编写任务时已核实的参照 |
|---|---|
| 仓库 | `yifanXovo/TailoredExact` |
| 前序 | [Round168 / PR230](https://github.com/yifanXovo/TailoredExact/pull/230)，Open Draft |
| R168 branch / delivery | `codex/round168-route-family` / `2301f9bf0a61d5fe74ee728704a820cb437d5cde` |
| R168 science | `80937e346de14048fc63163172727f4ca265515d` |
| R168 独立路线家族研究 PE SHA256 | `d699f6d92e6a392d83d828bd015d13e9c79bf32fc35f8b61d654e9cf33024449` |
| R167 delivery | `0da006b442ff7e59a2a63c6700138316611b2ce2` |
| main | `b2b940c1e517a72e226ec60fc49ff19651737632` |
| R163/R164 历史性能 source / PE | `e920b92e199e825ec89a2932f701861ff158e0d4` / `fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93` |
| 已知 Gurobi 13.0.2 DLL SHA256 | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |

入口做一次有限远端/本地核对，以合法最新更新为准。main 已包含完整依赖时从 main 开始，否则基于 R168 head，Draft PR base 取 R168 branch，无需等待前序合并。R168 的独立路线家族 executable 不是完整 B 性能 executable，不能拿它的身份替代本轮构建。

本轮记录放在 `results/unified_exact_round169/`；当前论文继续维护 `results/unified_exact_round137/` 的权威组件。本轮需要新构建完整 B/M/C 的共同 C++ executable，记录实际 source tree、编译器/命令、PE、DLL、参数及每次调用，不只抄继承的 `method_freeze.json`。

## B. 继承结论、有限排重与原文定位

### B1. R168 已完成的事实不重新计算

读取 R168 `goal.md`、`final_report.md`、`research_decision.md`、`route_family_theory.md`、结果/费用、实际 C++ 和当前稿相应段落：

- 11 个位置包括 7 个非平凡 order 排除、C35 Seed0 owner 排除、2 个免费自达标 HIT、1 个 eligible UNKNOWN；不是 11 个新实例或算法性能比较。
- 15 次 Optimize = 6 次 tiny + 9 次实质查询；8 次实质查询取得合格排除证据后提前结束，eligible 用完约 300s。Native 总时长约 436.828s，科学收束约 2332s，较快完成与任务规则一致。
- C35 owner 安全 L≈0.09339833077738849 高于统一 theta≈0.09331944374779841；故要达到此档案目标，必须改变至少一个旧已服务站的 owner，或服务旧 E 外站点。没有证明哪个动作充分，也没有证明必须服务 station18。
- C35 owner 见证将 F 从约 0.12956639 降到 0.11512887，尚不如已有 B Seed1 或档案 P；X35 两次小改善也未刷新同输入档案最好解。主线、优势实例和权威性能 CSV 均无增量。
- eligible 原始 Native lower≈0.03359255 因 incumbent 行残差约 7.9124e-7 超过预冻结的 1e-7 接纳门槛而未接纳；安全 L=0、U≈0.11512887 的 UNKNOWN 合法。即使接受 raw lower，也远未达到目标，因此不为这个数值接纳问题重跑。

本轮只需澄清 R168 理论末尾一句过宽表述：模型/API/映射失败不能伪装成科学 UNKNOWN；但有效模型的某个 Native lower 未通过数值接纳时，可以保留合法物理 U 和已知数学 L，报告明确的 UNKNOWN。保留原实验、raw bound 和判定，不改门槛、不改写历史。

### B2. 候选的具体历史差异

先读 `docs/current_mainline.md` 和当前实际 H 调用链，再定向核对下表，形成一份短 `research_design.md`。不重新遍历全部历史、不重跑旧面板。

| 先例 | 必须继承的边界 |
|---|---|
| R67–74，尤其 R73 | 原 H 已有 24 随机顺序和第 25 个 constructive order；新增随机启动本身不是全新原理，完整 H 不能缩成裸 runner |
| R75–83 | 当前数量、插入、跨车/平衡块及 equal-net 物理闭包均保留；不同时换邻域 |
| R88 | constructive-only 廉价化有实际回退；不能删原 24 个起点为新候选补贴预算 |
| R96/R97 | 更好启动/低成本合法反馈仍可能使完整方法变差；H-only 收益不等于算法收益 |
| R105–107 | assignment master、全物理 oracle、full/IIS conflicts、负 literal 和 frontier 已实际实现且完整结果不利；不重开普通 owner/no-good 框架 |
| R134/R137/R166 | 离线解不同 lambda、再跨权重回评，区别于同一次原目标运行内自付生产并回收 fleet；旧最终好解不能免费移作 Start |
| R159/R160 | 大小受限的数量/owner/order 联合物理邻域已尝试；不把放大 block 当本轮新机制 |
| R165–168 与早期 BPC 修复轮 | 不继续相同条件表示、eligible 加时或没有新定价结构的 route-column 重启；论文贡献表/发布入口已有成果，不另做整轮重写 |

审阅时尚未发现“同一次原目标求解中，按固定额外搜索权重生产完整 own-H，再回收原目标”的实现。入口只需针对这项结论复查最新更新；若实际发现完全等价且合格的旧实验，复用结果，指出等价处，不换名重做。

### B3. 至少一项已读原文先例

定向阅读 Paquete and Stützle (2003), *A Two-Phase Local Search for the Biobjective Traveling Salesman Problem*，作者稿 [PDF](https://iridia.ulb.ac.be/~stuetzle/publications/EMO03.pdf) 的 §2 / Algorithm 1 及与主张相关的实现说明。其改变聚合权重、串联局部搜索和归档是直接先例，不能声称本轮首次用权重多样化。该文目标是近似 Pareto 集，本轮只优化一个固定原 F，且采用两次独立额外 H，不照搬其链式方法名称。

如需第二项，Jaszkiewicz (2002), *Genetic local search for multi-objective combinatorial optimization*, EJOR 137(1):50–71，DOI `10.1016/S0377-2217(01)00104-7`，§6.1 的随机 utility 与局部搜索可说明更广的先例。没有必要另做文献普查。内部记录实际阅读版本/节，公开正文正常陈述方法关系。

## C. 唯一候选、对照与正确性

### C1. 固定定义

令原目标为 `F_lambda(x)=G(x)+lambda*P(x)`。输入物理可行集、站点权重、目标库存、T、Q、距离、装卸、空载出发和载货返回规则均保持不变。令 `H_a(s)` 表示当前 B 的**完整** own-H，在搜索权重 a、初始化 seed s 下产生的终态最佳物理 fleet。

固定 `s0=20260626`、`s1=20260627`、`s2=20260628`；额外调用顺序按 s1、s2。不得按结果重选 seed 或交换倍率。

| 臂 | 自有 H 候选池 | 交给原目标精确搜索的 Start |
|---|---|---|
| B | `H_lambda(s0)` | 原 B 的选定 fleet |
| M169，简称 M | `H_lambda(s0), H_lambda(s1), H_lambda(s2)` | 按原 F 选最好者 |
| C169，简称 C | `H_lambda(s0), H_(lambda/2)(s1), H_(2*lambda)(s2)` | 按原 F 选最好者 |

每次额外调用均从合法原输入独立生成自己的 constructive 与随机顺序，不接收另一条路径、旧 P/B 或诊断阶段的 fleet。只回收每次完整 H 返回的实际终态 fleet；不承诺保留搜索路径中原目标最好的全部中间候选。本轮不新增原 lambda 的二次 polishing、callback 回馈、参数网格或跨运行候选池。

lambda=0 或惩罚在所有合法库存上恒为零的输入，对 M/C 统一退化为 B，不做目标等价的额外路径。后一条件用输入可证明的简单充分条件（例如全部惩罚权重为零）识别，不求解额外优化问题。lambda>0 时，两正倍率不改变 F=0 的物理含义；发现原目标经原证明策略合格的零解可沿用 B 提前结束。所有退化/跳过都在冻结设计中定义，不按实例临时省工作。

候选接受沿用原 F 的既有数值容差和确定性 tie 规则；完全平局优先原 B，再按固定路径顺序。E 中的材料性阈值仅决定是否值得支付下一阶段实验，不用于在线拒绝真实的小改善。

### C2. 只证明必要的三个性质

写清楚一个短 `method_note.md`：

1. **可行域不变的解转移。** 若 x 是任一搜索权重下实际生成、经原输入验证的物理 fleet，则 x 也是原问题可行解；其原目标 UB 为 `G(x)+lambda*P(x)`。不得把另目标的 reported objective 当成原 F。
2. **初始化阶段 UB 不劣。** 在相同完整 base H 已得到且返回候选有效时，B fleet 始终在 M/C 池中，因此选定初始 `U_M<=U_B`、`U_C<=U_B`。这不保证完整同 cap 运行的终态 U、L、gap 或证明时间不劣，因为额外 H 要付费，Start 会改变后续搜索轨迹。
3. **原精确搜索的正确性继承。** 进入 B 时原 lambda、物理输入、原目标 cutoff、coverage/proof ledger、g 域/库存收缩依据和资格策略全部恢复/重建，唯一新输入是自有、原目标合格的 UB/Start。不得转移异目标 lower、cutoff、收缩域、树、证书或缓存的目标数值。

G、P 同时改善的档案 fleet 反映旧有限搜索的不足，不是已精确得到的 Pareto 曲线上出现“更优原解”。这些性质属于正确性解释，不另写成 OR 新定理。

### C3. 对照实际回答什么

分别报告：

`Delta_restart = F_B - F_M`，`Delta_weight = F_M - F_C`。

C 只胜 B、未胜 M 时，不能把收益归于改变权重。相同两个额外 seeds、同样两个完整 H 调用，控制的是有限多启动结构；各权重的邻域路径、decoded checks、物理检查与 CPU 时间仍可不同，不能写成工作量完全相等。

同一输入的 H seed 固定，因此反复改变 Gurobi Seed 并不会构成 H 的独立重复。H-only 每个原问题只做一条 B/M/C 比较；Native Seed0 完整面板也只提供筛选证据，不作统计稳健性宣称。

## D. 档案线索和冻结的七个原问题

### D1. 零 solver 的来源补全

只在本地已存在的 R137 carriers 中读取 rho≈0.5/1/2 三个 B(S2) 的 H 物理解、必要 audit 与 rho≈2 journal，按原 rho≈1 重新评价 H，并记录最终好 fleet 首次 accepted witness 的来源/时间（能够恢复时）。

准确动机输入为 `R-X35-S-T2`：input SHA256 `c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2`，physical SHA256 `1d5e47895bcda5db4281c80962f55ef694df568122adda1d8e2242615825cccc`，T=6300、Q=[20,25,30]、pickup/drop=60s、原 lambda=`0.0754049775127276`。它**不是**下表的 R163-X35-S（其输入、T、lambda 都不同）。

三份原 H/运行定位为 R137 campaign 068、059、071；各自的 rho、arm 和成员前缀以 `matrix_frozen.json`/carrier map 实值核对，不仅依编号猜测。rho≈2 最终 fleet 来源 `R137:B3:71`，carrier `results/unified_exact_round137/artifacts/campaign_071.zip`，SHA256 `650e20df10ae98a455500a609879e11465e90ae44cf12cd0d97a42b5bb9d189d`，成员前缀 `results/unified_exact_round137/campaign/071/raw/R137_071_R-X35-S-T2-rho2_S0_S2/`；audit SHA256 `039c398ff410f0ba0cf30bd06e5e0843a5f288ab8e388376a1f8e7164025d86e`。

已知 rho≈2 初始 own-H/root cutoff≈0.6497055906824541，最终原 rho≈2 F≈0.5245527536064684；后者在原 rho≈1 为 0.3365058164688021，优于旧原 rho≈1 的 0.40327199886285475。不能把约 2370.96s producer 端点作为首次发现时间，也不能声称已经知道是 target MIP 或 terminal MIP 首先生成。

该来源补全限于必要成员，约 15–20min。旧大包本地缺失时不反复下载全集来追 first-hit，保持未知；使用 R166 已恢复、哈希验证的物理输入进行 H-only 检验即可。没有便宜历史 H 收益不阻塞这次最多 35 次 H 的新假设检验，但不能据此直接跳过筛选进入 Native。恢复的旧解只供分析，绝不进入新运行。

### D2. 六个当前角色与一个动机角色

不重新生成或筛选输入，全部为已经暴露的已知配置，不称 prospective holdout。R163 输入原路径均为 `results/unified_exact_round163/inputs/<ID>/first/instance.txt`，完整物理参数读其 `input_manifest.json` 和实际 argv。

| 原问题 | input SHA256 | 数学 T | 原 lambda |
|---|---|---:|---:|
| R163-C20-S | `cdf6943983c8f2bbd932cb7a3bf3e6645d828b9f651806c4514b6d9a13b865ca` | 5400 | 0.10787606377934943 |
| R163-B20-B | `1101972093cf4e0cfba3470236876048cb26e7e7b924439c7ade6e65a30a28c4` | 7200 | 0.10176615156032952 |
| R163-X20-S | `749674d7000925c032a619ad1b067cbdcaef0b1cdfd3267228b5d9a379b4a0da` | 5400 | 0.13297872340425532 |
| R163-C35-U | `fb9d881dba6d0d07c59c48a683d2b2543f3effeae593306e28d79875cdcc20d7` | 10800 | 0.11068496171019777 |
| R163-B35-S | `8f644c76508a54443e280fe03833f15131989d55184bdfca21b56223f69c17b1` | 7200 | 0.10810343336504369 |
| R163-X35-S | `5804470a50da77c2da43ca5654b85e22f0e82459ef556d4d4d75e52e3a87daa9` | 10800 | 0.092888243831640058 |
| R-X35-S-T2（R137，原 rho≈1） | `c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2` | 6300 | 0.0754049775127276 |

n20 为两车 Q=[30,30]，n35 为三车 Q=[20,25,30]；全部继承原每站权重、库存/target/capacity、距离计算和 60/60s 装卸参数。输入 hash 与外部参数共同定义问题，短别名不能替代身份。冻结十进制17位与实际 binary64 lambda、倍率结果及所有运行参数。

第七个只用于动机核查和 H 机制表，不进入本轮完整面板，也不能仅凭它获益触发完整面板。该区别在看结果前固定。

## E. C++ 实现、少量资格与实验执行

### E1. 正确复用完整 H，处理已发现的真实接口风险

在完整程序中增加显式、默认关闭的研究入口，例如 `--round169-primal-mode off|multistart|reweight`，另有只执行同一初始化实现的 H-only 入口。实际命名可适应已有 parser，但冻结清楚；不要复制一套与真实 B 脱节的优化器。

1. **完整 H 入口。** 当前 `main.cpp::runPaperPrimalHeuristic` 在 Round83→73→71 preset 链中，先做 Round73 joint position/quantity insertion，再用其作为第 25 个 constructive order，执行 24 个随机顺序的有限 interroute decoded descent，以及当前已启用的 R83 物理闭包。仅调用 `runHgaTgbcNative` 不等于完整 H。抽取/包装现有完整入口，保留全部生效 flags；每次只改变声明的 search lambda、H seed 和独立输出路径。该入口按 `algorithm_preset` 字符串直接判断 joint/R83 分支，因此保持 B 已解析的 `research-round83-vds-equal-net-exchange` preset 名，用独立 research flag/arm identity 区分 M/C；不能换成一个未识别的新 preset 而悄悄跳过这些阶段。
2. **preset 会覆盖 seed。** 当前 `--primal-heuristic-seed` 的值可能被后续 `applyAlgorithmPreset` / `configurePaperK1AmSfOverrides` 重设为 20260626。先完成原 preset，再复制有效 options 给每条研究 H，在调用前明确设置并读回 s1/s2 和搜索 lambda。不能只附加 CLI 参数便声称对照已生效。B off 路径保持原语义。
3. **避免递归和串线。** 包装器调用的是一次 base-H 原语，不递归触发整个 M/C；额外调用不再套用会覆盖 seed 的 preset。每条路径的日志、joint-seed、候选、export-incumbent 和缓存身份隔离，返回结果不能覆盖 base-H 的历史字段。
4. **恢复全局目标参数。** `set_greedy_objective_params` 设置全局 lambda/scaling；用已有 getter 和 RAII 或等效可靠机制恢复，异常/早停同样生效。核对缓存是否存未加权量及完整输入签名，不把不同目标下已计算的 F/cache 或候选语义混用。H 子调用串行，不能在共享全局目标状态时并行运行。
5. **分离搜索与评价。** 每条路径记录 `search_lambda`、`evaluation_lambda`、H seed、原输入/物理 SHA、完整性和 fleet SHA。先经原 C++ physical verifier 回算原 G/P/F，再进入 original-objective store；把 search objective 保留在独立字段。原 B 精确层只接收重建的原目标 verification/UB/Start。
6. **共同截止。** 额外 H、转换/检查、日志、模型构建、全部 LP/MIP 和最终验证都占同一原 process cap，不重置 clock，不在生成额外 H 后重新给 B 满额时间。H 自然按原有限闭包结束，唯一运行时截止是继承的 whole-run deadline。截止时只保留已合格的自身 fleet，完整性如实标注。
7. **默认保护。** B off 的 preset、H seed、物理模型、proof policy、AM/controller、C166/D167 状态均保持原样。新增候选只改变初始化；输入取值、搜索顺序选择和接纳规则不得读取实例 ID、历史目标 tau、旧 P/B fleet 或历史胜负表。

### E2. 有针对性的资格

不新造大规模 tiny 枚举或重跑历史 MIP。用少量现有物理 fixtures 和首次真实 H 调用验证以下风险，合并日志而非重复整套测试：

- off 包装调用与原 base-H 在相同输入/options 下具有同一物理 fleet、G/P/F 和有效种子/完整闭包语义；一次有代表性的非零输入即可，时间不作历史速度比较。
- 同一 s1 或 s2 下，C/M 初始 24 个随机顺序的生成身份一致；constructive 顺序允许因搜索 lambda 变化。s0/s1/s2 的有效值实际读回，不是从请求 argv 推断。
- 执行异目标 H 后，再对原参数回评同一非平凡 fixture，F 与预期一致；检查 greedy 全局恢复、异常/早停清理和不跨路径污染。
- 覆盖 lambda=0/全零惩罚、原目标合格零解、空路线/载货返回与至少一个 G、P 均非零的回评。使用既有 checker 独立核对一个新 fleet 的全部库存、前缀载荷、压缩旅行、返回卸货和原目标。

资格阶段不需新 Optimize；若发现确切实现错误，修复后只重做受影响的资格/位置，错误运行保留且成本计入。不要把实现失败当阴性研究结果，也不要为追求完全一致的墙钟而反复重测。

### E3. H-only：最多 35 次完整 H

按 D2 表顺序执行，每项新跑 base-H 一次、额外原 lambda 两次、额外半/双 lambda 两次。H-only 表允许共享该项新生成的 base-H 供 B/M/C 原目标集合比较；明确这是诊断复用，不是三臂实测总时间。最多 35 次，合法零解/退化跳过要写原因。

每项保存五个实际终态 fleet（执行时）、search/evaluation objective、G/P、有效 seed、完整 H 组成/完成标记、调用耗时、decoded checks、物理闭包工作计数、验证费用及最终 B/M/C 所选来源。调用次数相同不代表工作量相同。

同时比较所选 C/M 与本项 base-H 的服务集合、车辆归属、访问顺序、库存及方向变化。相同属性车辆的纯重标号不算结构改变；可对本项目最多三车枚举兼容重标号核对。该比较是结果描述，不据此在线选策略，也不声称某项变化是收益的独立因果。

R168 证书绑定的是旧的最终 B 父 fleet；本轮 base-H 通常不是该父 fleet。只有输入和完整 family 定义/父 fleet 身份确实对应时才可引用相应排除结论，不能把旧证书套到任意新初始化。

### E4. 唯一进入完整阶段的条件

在读取结果前冻结：对每个六 R163 角色定义

`delta_i = max(1e-6, 0.001 * max(F_B,i, 1e-12))`。

若至少一个角色有全部必要 H 完成、原物理验证合格，且 `F_C,i < min(F_B,i,F_M,i) - delta_i`，则执行 E5 **全部固定位置**；否则不执行新完整求解，交付 `stop_fixed_reweight_candidate`。第七个 R137 动机角色不单独触发。数值小于 delta 的真实改善仍如实保留，仅不足以触发本轮后续支出。

delta 是统一预注册的研究经费门槛，不是统计显著性、不保证收益可重复、更不进入算法。真实错误先修；缺失/未完成不能伪装成通过。不得增加倍率、再挑 seed、添加 polishing 或延长 H-only 窗口来挽救未通过的固定配方。

### E5. 有条件的完整 B/M/C 付费面板

H-only 通过后无需再向用户申请许可，直接完成已授权面板：D2 的六 R163 输入、B/M/C 三臂、各 Native Seed0、Threads=1，使用同一新构建及相同 solver 参数/资格策略。n20 统一原 process cap=300s，n35=600s；数学路线时限 T 与这些运行 cap 完全不同，保持 D2 的原值。

从 R163/R164 当前 B 的真实 argv 继承完整 preset、状态/服务表示、pair-only、AM/proof 与 margin 规则，按新 cap 一致调整剩余时间/终止余量，预先写出每个实际数值。原 time-limit、process-wall limit、shutdown margin 之间的关系不能照抄 2400s 常数。三臂同一 cap 和同一计时起点，超时、验证、source rejection 与 crash 都按真实状态记录。

每条完整运行从头生成并支付自己的 H；**不得读取 E3 的 H 结果、旧 fleet、旧 Start 或其他臂输出**。B 跑 1 次 H，M/C 各最多 3 次；B off、M/C 处在共同 executable，不能将新 C 的时间与旧机器/旧 PE 的 B 时间直接配对。

冻结运行顺序：六角色依次使用 `B,M,C`、`M,C,B`、`C,B,M`、`B,M,C`、`M,C,B`、`C,B,M`。各运行顺序完成，不在同一机器并发 Native 竞争资源。合法证书提前结束；一个位置失败不通过补跑多个 seeds 找替代，必要纠错重跑单独计费、保留失败记录，总容量不扩大。

记录原 F 的初始 U、终态 true U、qualified global L、绝对 gap、原定义相对 gap、证书资格/耗时、总 process 时间、各 H/构模/LP/MIP/验证费用、Work/节点和实质 Start 是否改变。比较 C 对 B **以及** C 对 M；U/L/gap 不相容的优劣不能压成单一“赢”。没有足够证书时报告共同预算质量，不把 OPEN 时间当证书时间。

这 18 个位置是新短预算筛选，不等于 R163/R164 的 1200/2400s 结果复验，也不增加 P-GRB 胜率证据。保留全部负面/平局，尤其 n20 保护角色中 B 已认证但 M/C 未认证的情形。完成即停止，不自动追加第二 Native Seed、大 cap 或新 P/PS/E+。

## F. 解释层次与本轮唯一决定

报告按以下顺序回答：

1. 固定倍率额外 H 是否产生原目标收益？`Delta_restart` 与 `Delta_weight` 各多大？收益是否只来自 R137 动机位置，还是出现于当前六角色？
2. 所需新物理解是否改变 E/owner/order，是否仅调量？描述实际 fleet，不把 R168 的必要条件当成本轮算法成功证明。
3. 每条路径实际付出了多少完整 H 工作和时间？若 C 与 M 不同，说明是路径差异，不能隐去。
4. 若完整面板执行，C 的初始化优势是否在付费后保留，是否改善原目标终态/证书，并且是否超过 M？若 M 已解释收益，就撤回“重加权有效”的解释。
5. 据此给出一个决定：关闭本固定候选；保留原始解作用但不继续完整集成；或建议以后进行独立、有限的正式确认。最后一种至少需要明确的端到端收益，不能仅凭一个 H 变好或某个 LP/Work 数字。任何决定均保留 B 默认。

由于只有已暴露输入和 Native Seed0，本轮不宣称普遍、统计稳健或外部数据推广。也不要求每个位置都赢才允许承认局部有价值的信号；重要的是准确指出收益、代价、反例和下一步是否值得。

OR 方向的结论必须坦率：本轮若成功，首先是实践算法增量；若失败，则当前资料仍不支持新的通用结构算法。记录尚缺的可推广机制/理论证据，不用再造普通 NP-hardness 证明、放大 MIP 或为凑下一轮提出未排重的分解框架。EJOR/TRE 成稿评阅可与将来的算法探索分开推进，不无限等待下一次性能改善。

## G. 稿件、权威 CSV 与必要成果

### G1. 有限且有信息的论文更新

保留当前六节组织和既有正负结果，维护同一套 `results/unified_exact_round137/` 源。R168 已完成原文定位与正文收束，不重复贡献表、全文压缩、审计清单或发布工程。

若 H-only 无实质增量，正文最多补一句有信息的边界说明，完整七项 H 表/费用放补充或研究 note，不强行增加新正文节。若完整面板执行且有价值，在既有结果/讨论中加入一个紧凑 B/M/C 表及解释，明确 short-cap、known roles、Seed0、default-off 和相同目标下的付费比较。当前 B/P 主要结果不改写、不重新计算胜率。

EJOR 强调已经支持的共同库存状态、服务/目标关联与完整精确方法；TRE 保留已建立的资源/权重可认证决策区间；OR 不以已知 scalarization 思想冒充新理论。作者决定 memo 仅补本轮实际改变的判断，不重复上轮整份话术。

落实 B1 的一句 UNKNOWN 文字澄清。检查 README、`docs/current_mainline.md`、`docs/paper_s2_release.md`/`docs/paper_review.md` 指向的“当前稿件/研究决定”是否仍停在 R165；仅更新确实过期的导航与研究身份，既有生产性能 source/PE 的历史身份保留。

复用已工作的文档组装器，但用 R169 薄入口/参数化，不原样调用硬编码 R168 OUT/temp/schema/current_round 的脚本。生成同源组装稿与当前主/补充 PDF；定点查看发生变化的文字、表、公式和相邻页，无需重绘未变图表。

### G2. 112 条权威主表与本轮增量规则

本任务配套 ZIP 内含权威 `GI_TBC_vs_P_GRB_All_Tested_Instances.csv`，**112 条数据记录、28 列、UTF-8 BOM、64,951 bytes**，SHA256：

`b728f85512741779a8b066ae9c974ec60892360c3fe15fbf7b946fb0ab0a4878`

入口从本次解压目录读取并核对，工作副本放 `E:\codes\ExactEBRP-work\data\GI_TBC_vs_P_GRB_All_Tested_Instances.csv`。已有不同内容先保留核对；保护 Desktop 的旧 91 条和仓库历史 103 条副本。只做一次有限来源查找，不再次因附件遗漏陷入扫盘；没有可靠原始表时披露缺失，不凭总数造行。

112 是历史运行记录数，不是 112 个独立输入/严格配对。R167/R168 没有新增完整 B/P 记录，故本任务入口提供的是同一权威版本，不是新增优势证据。

- **E5 未执行：**H-only、来源回评和小例均不属于完整性能样本，CSV 新增 0 条，保留原字节。
- **E5 执行：**按照 R166 已有“B-only、无同轮 P、N/A-P”先例，仅对实际取得完整来源/结束状态的本轮 B 控制记录逐条追加；若六项均合格，则 112→118。实际缺失、失败或无法完整重建的项不凭预期数量造行，另记 reconciliation。
- M/C 用独立 `complete_arms.json/.csv`，不得写进 GI_TBC 列冒充现行 B；不得用旧 1200/2400s P 数据与本轮 300/600s B 拼成配对，也不得把 N/A-P 新行计为新优势实例。

保留原 28 列和全部旧行；新行沿用 `P_GRB_状态=无配对结果`、`对比结果=N/A`，在说明中写 `N/A-P`、新 source/PE、实际 cap、Native Seed0、完整 run ID 与固定证据链接。更新后给出实际行数/hash，并提供本轮权威工作文件；未变化则明确说明未变，不制造版本增量。研究 H 表另存，不混入主表。

### G3. 最小必要交付

允许合并相邻记录，避免重复文书。`results/unified_exact_round169/` 至少应能定位：

- `goal.md`、简洁 `research_design.md`、`method_note.md`；真实源码/构建/环境/candidate manifest；
- `weight_provenance.json`：旧 H 回评与 final first-hit 的已知/未知，不补造时间；
- 预先冻结的 `h_panel_frozen.json`、有效 seed/倍率/参数和 E4 条件、18 位置的 `matrix_frozen.json`（若未执行也标记 not-triggered）；
- C++ 统一实现、定点资格记录、七项 H 原始 fleet/日志及 `h_results.json/.csv`、完整费用；
- 若触发 E5，全部 18 个位置状态、实际 Optimize journal、原目标物理解/证据和 `complete_arms.json/.csv`；未触发则不造空的运行结果；
- `research_decision.md`、`final_report.md`、`decision.json`、有限作者 memo/稿件修改、两份当前 PDF、CSV reconciliation/实际权威文件位置；
- 三项独立复核及修正记录、单个本轮新增证据包与精确 member map。

最终报告先说新动作有没有付费价值、为什么继续或停止，再给支撑数据；不要以审计文件数量或运行时长作为科研成功。

## H. 独立复核、Draft 交付与停止

实际成果形成后并行做三个独立复核，审阅真实代码和文件：

1. **数学/目标语义：**物理可行域不变、异目标 fleet 回收、原 G/P/F、保留 B 的初始 UB 性质与终态不保证、原目标精确搜索/证书隔离，R168 证书作用域正确。
2. **实现/数据/费用：**完整 C++ H 而非裸 runner、preset 后有效 seed、无递归、全局 lambda/scaling/缓存恢复、独立路径日志、全部费用及共同 deadline、H-only 无 Optimize、E5 无免费复用、18 位置与 CSV 准确状态。
3. **研究/论文：**与 R73/R88/R96/R97、离线权重实验和已读 scalarization 先例的差异；C 对 M 的解释、触发条件未事后改变、单 Seed/已暴露面板的结论范围、无 OR 夸大与无新 P 胜率暗示。

记录具体问题及修复，修复后只读回必要部分。审阅属于完成任务，不是新增用户审批；独立代理不可用时如实说明替代核验，不虚构 reviewer。负面结论同样正常交付。

正常 commit/push，创建英文 **Open Draft PR**，建议标题：

`Round169: test paid objective-diversified initialization against matched multistart`

PR 首段说明原问题的有限可行解搜索缺口、唯一候选与 M 对照、实际 H/完整结果和研究决定。按 A 使用 main 或 R168 stacked base，读回 head/base/Open/Draft 和稿件链接。不自动 merge、force-push、删除历史分支或联系作者/期刊。

仅对本轮新增/修改源、文稿和必要证据做一次公开取回/字节核验。旧 raw 通过固定 archive/member/hash 引用，不重打包历史全集。新 raw 使用本轮专属包；不发布商业 DLL、许可证、凭证或私有前稿。科学提交和 receipt 提交分开，不填写尚不存在的 self-SHA；清理遵守工作区政策，零删除允许。

验收是：一个清楚冻结、真实 C++ 完整 H 的唯一候选及公平 M；七原问题上的诚实筛选；条件满足则完成全部付费面板；据此继续或停止的明确判断；有限论文修正；B 默认保留；CSV 按真实运行增量处理；独立复核后 Draft 交付。**不要求正结果、不要求耗满时间、不自动开始 Round170。**

## I. 固定查阅入口

- [R168 / PR230](https://github.com/yifanXovo/TailoredExact/pull/230)，delivery `2301f9bf0a61d5fe74ee728704a820cb437d5cde`：`results/unified_exact_round168/` 的目标/报告/决定、路线家族理论与结果、实际 `src/round168_route_family.cpp`、成本/审阅和当前论文。
- [R166 / PR228](https://github.com/yifanXovo/TailoredExact/pull/228)，delivery `d497052216d5ae55b6ae0139ea30910cee2e5865`：`results/unified_exact_round166/decision_analysis.md`、`results/unified_exact_round166/analysis/X35_offline_improvement.json`、该轮 `review/{data_physical_archive.json,data_recover.py}`、六输入完整 B/C166 记录及 CSV 增量来源。
- [R163 / PR225](https://github.com/yifanXovo/TailoredExact/pull/225)，delivery `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`：`results/unified_exact_round163/{input_manifest.json,matrix_frozen.json,final_report.md}`、固定 inputs、真实 argv/构建/费用。
- [R164 / PR226](https://github.com/yifanXovo/TailoredExact/pull/226)，delivery `de01e8fb27a954d031abac5fe99442d6c8d29d44`：全部 Seed1/2 档案、历史 member map 与物理目标；仅分析继承，不作为本轮免费 Start。
- `results/unified_exact_round137/matrix_frozen.json`、campaign 059/068/071 的 carrier map/audit/H/journal；当前论文 `paper_body.md`、`model_and_algorithm_appendices.md`、`supplement.md`、`references.bib`、`manuscript.md` 与 PDF。
- 当前完整 H：`src/main.cpp::runPaperPrimalHeuristic`、preset/`configurePaperK1AmSfOverrides`、`src/HgaTgbcRunner.cpp`、`include/HgaTgbcRunner.hpp`、`include/hga_tgbc/HybridGA.h`、实际 GreedyMethods 与 R73/R83 实现；按调用依赖读，不因 legacy HGA 名字误写为当前有 genetic generations。
- R73/R88/R96/R97/R105–107/R159–160 的相关最终报告与源；[Paquete–Stützle 作者原文](https://iridia.ulb.ac.be/~stuetzle/publications/EMO03.pdf)。

最终回复提供科学结论、H 的 C/M 分解、完整阶段是否执行及实际付费结果、B 默认状态、CSV 新增记录和新增 P 配对数、稿件/PDF、独立复核与 Draft PR。若 H 筛选未通过，明确说明本轮已完成并关闭固定候选，而非留下等待许可的半成品。
