/goal

# Round168：判定现有路线骨架的目标可达性，确定下一项算法改进

## 0. 目标、研究增量与预算

继承已完成的 Round167。本轮回答一个具体、尚未解决的问题：**对当前 GI-TBC 保存的可行路线，允许完整联合调量、方向翻转和删去零服务后，能否达到同一物理实例已经存在的更好目标？若不能，放开访问顺序、车辆归属后，哪一层限制仍是可认证的障碍？**

这个问题直接对应 R163 留下的 C35 可行解缺口。R164 的逐站差异、目标库存投影及资源下界尚未回答整个路线家族的可达性；R165–167 的表示研究也没有回答它。R96 已实现完整 fixed-order 数量诊断，故本轮明确继承其数学语义，使用 C++ 实现当前入口。**不把 oracle 移植、一般集合包含关系或“固定路线再调量”称为新机制。**本轮争取的新增结果是当前主线上的目标可达性证据，以及有实际区分力的结构释放证书。

同时完成 EJOR/TRE 稿件的一次有限收束：修正 R167 遗留的公开阅读日志表述，把有信息的新结论放入适当位置，并形成清楚的作者决策说明。R167 已完成正文重组；本轮不再重新组织全文，也不再设置压缩词数目标。

**B/GI-TBC 保持当前统一默认，C166、D167 保持默认关闭。**本轮研究入口离线独立，不接入 own-H、AM、Gini 外层、Native 分支或在线 incumbent 回馈；不新增完整 B/P/PS/E+ 面板，不产生新的性能胜率。只研究下文一个嵌套路线家族体系，不同时开发多种局部搜索。

本轮是一次有终点的研究选择节点。明确的 HIT、EXCLUDED 或有界 UNKNOWN 都是有效结果；最终必须据此选择至多一类后续机制，或者说明该诊断方式信息效率不足并关闭继续扩展。不能默认再来一轮加时、换 Seed 或增加相似诊断。

### 0.1 工作容量与 C++ 约定

总科学工作容量 **8h = 28,800s**，目标约 4–6h，完成即停止。包括定向阅读、推导、实现、计算、数据处理、有限改稿、构建和复核；并行研究按共同外层窗口计一次，计算开销另外完整记录。普通 Git/公开恢复传输 I/O 单列。

| 工作 | 建议容量 |
|---|---:|
| 历史排重、档案恢复和路线家族证明 | 约 1.5h |
| 一个 C++ 诊断入口及小例资格 | 约 2.5h |
| 诊断计算、构模、取回与核验 | 硬上限 1.5h；实质查询 Native 配额最多 45min |
| 稿件定点修改、结果解释和作者决策 | 约 1h |
| 独立复核、数据收束和 Draft 交付 | 约 1.5h |

预算是容量，不是必须消耗的配额。进入实质查询前，至少保留 2h 用于结果解释、稿件和复核。具体调用数及计费口径见 E4。

**新增建模、优化、Start 映射、物理解码、精确枚举 oracle 和研究 driver 全部使用 C++。**可以直接调用 Gurobi C/C++ API。Python/Node 仅用于编排、日志、独立离线复算、表格和文档；不能用 C++ 外壳启动旧 Python 优化核心，也不能以 Python 生成优化模型后仅让 C++ 调用 Optimize 来满足要求。R96 的 Python/ctypes 实现作为历史参照保留，不重测其速度。

模型与将来可用的算法规则只能依赖合法输入、数学状态和已证明条件，不依赖实例名、城市、历史胜负、机器型号或测得速度。下面固定的档案位置属于已暴露的研究样本，不能转化成实例特定在线策略。时间上限用于实验管理，不进入生产算法切换。

## A. 本地入口、继承身份与 PR

遵守仓库 `AGENTS.md`、`WORKSPACE_POLICY` 和已有工作区约定。所有新工作、缓存、临时件及交付放在 `E:\codes\ExactEBRP-work` 内；保护原 `E:\codes\ExactEBRP`、用户文件、活动 worktree 和历史证据。

`E:\codes\ExactEBRP-work\worktrees\paper-current` 曾处于旧轮且有未提交修改，先只读核实，不 reset/stash/覆盖。优先在核实的 R167 基础上创建或接续 `E:\codes\ExactEBRP-work\worktrees\round168`，分支建议 `codex/round168-route-family`。已有同轮内容则按 manifest 接续，避免重复运行。

任务编写时核实的身份如下；入口再做一次有限远端/本地核对，以实际合法更新为准：

| 身份 | 固定参照 |
|---|---|
| 仓库 | `yifanXovo/TailoredExact` |
| 前序 | [Round167 / PR229](https://github.com/yifanXovo/TailoredExact/pull/229)，Open Draft |
| R167 branch / delivery | `codex/round167-conditional-state` / `0da006b442ff7e59a2a63c6700138316611b2ce2` |
| R167 science | `e2fce9c98324fefc5ce1b7bba06f7152f680c3bd` |
| R167 研究 PE SHA256 | `26fe2d74d92e0d998966f73085b3a321007e39ea674ff4e2b8655f8414515f12` |
| R166 delivery | `d497052216d5ae55b6ae0139ea30910cee2e5865` |
| main | `b2b940c1e517a72e226ec60fc49ff19651737632` |
| R163/R164 历史性能实测 source | `e920b92e199e825ec89a2932f701861ff158e0d4` |
| 历史性能 PE SHA256 | `fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93` |
| 当前已知 Gurobi 13.0.2 DLL SHA256 | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |

main 已包含完整依赖时从 main 开始，否则基于核实后的 R167 head，Draft PR base 取 R167 branch，无需等前序合并。源/PE 身份依据实际 candidate、构建及调用记录，不仅依据继承的 `method_freeze.json`。

本轮记录放在 `results/unified_exact_round168/`。当前论文继续维护 `results/unified_exact_round137/` 的权威组件，不另建一套全文。研究 executable 使用独立名称，例如 `Round168RouteFamily.exe`；记录 C++ 源、构建命令、编译器、PE/DLL 和参数身份，不冒充旧 B/P 性能 executable。

## B. 已知结论、历史排重与文献边界

### B1. 已完成的 R167 不重复做

读取 R167 的目标、报告、决定、条件理论、实际 C++、费用和当前论文。以下结论作为继承事实：

- D167 同图 f/q 网络准确表示增强的库存/服务/Gini 乘积/absolute-code 联合凸包，保持任意部分 absolute-bit 固定后的共同信息；与同码枚举参考 R_abs 等价。五支撑只适用于所声明的物理投影，不是任意增强编码对象的五点表示。
- 88 次实际 Optimize 全部合格；24 组三表示比较中 D167/R_abs 目标最大差约 `2.22e-16`。16 个条件比较中仅 3 个严格提高原目标 LP 界，其余 13 个未增益；这是条件 scopes，不是 16 个独立实例或算法胜率。
- 所有实际 D167 矩阵比 R_abs 更大。C20 root 的 R_abs/D167 为 3344/4216 列、6885/8991 行。临时 one-hot carrier 使端到端准备仍有线性状态成本，但 24 个 canonical 构建总时间 R_abs/D167 约为 26.260/26.804s，尚不是已证实的大成本来源。
- 因此保留数学结果和离线原型，当前不安排 D167 完整集成、重新跑大面板或专门一轮移除 carrier/调整 DAG 常数。
- 正文实际从约 13,505 降至 9,003 whitespace words；主 PDF 53 页含完整附录，补充 55 页。B、C166 默认及性能主表未改变，无新增完整 B/P 记录。

R166 已完成的权重包络、资源双侧区间、C166 六行正负比较继续使用，不重新计算为本轮贡献。

### B2. 只做与本题相关的历史排重

先读 `docs/current_mainline.md`，再定向读取以下实际报告与相关源。形成紧凑 `research_design.md`，说明“继承什么、这次还缺什么、为什么不是重做”。不要重新遍历全部历史 PR 或重跑旧面板。

| 历史 | 必须核对的具体关系 |
|---|---|
| R76–83，尤其数量修复、跨车/路线邻域 | 区分有限邻域和本轮完整受限家族；不得把旧失败邻域换名后再次作为新机制 |
| R96 | 完整 fixed-order 数量诊断已允许删零、方向翻转和真实压缩旅行；六个保存状态各有 300s 上限，F5 final 曾取得 restricted certificate，另一项 fixed-owner/free-order 查询约 298s 为 UNKNOWN。直接继承模型语义和反例，不宣称首次固定路线精确调量 |
| R97 | 离线可行改善到在线回馈的混合/负面结果；本轮离线 HIT 不能自动证明在线付费值得 |
| R98–107 | 当前 B 的服务/库存连接及路线、资源分解边界；识别哪项是 whole-family，哪项只是局部/聚合模型 |
| R159–160 | 保存点上的 primal/quantity completion 与有界邻域结论；不能误当作全库存、全顺序家族排除证书 |
| R163–164 | 当前六配置/Seeds 完整档案，以及 C35 具体未解问题；复用已验证 fleet 和 R164 失败投影，不能把投影失败写成所有调量失败 |
| R165–167 | 表示与论文工作已完成，不重复开启同类诊断 |

特别核对 R163 结尾提出的 C35 B Seed0 整骨架问题是否在其他合法最新更新中已被回答。**若发现同输入、同家族、同目标口径的合格结果，直接复用对应位置，不重跑。**若只有不同父 fleet、窄 Gini/库存域或小邻域，准确说明区别。

### B3. 两项最近原文，限定阅读范围

定向阅读而非扩展文献普查：

1. Erdoğan, Laporte and Wolfler Calvo (2014), *The static bicycle relocation problem with demand intervals*, EJOR 238(2), 451–457，DOI `10.1016/j.ejor.2014.04.013`。作者稿 §2 的固定路线最小费用网络是重要先例；其 demand intervals、单车与目标/装卸约定不同，不能直接推出当前 Gini 加惩罚的多车联合问题可按车分解或多项式可解。
2. Szeto and Shui (2018), *Exact loading and unloading strategies for the static multi-vehicle bike repositioning problem*, TRB 109, 176–211，DOI `10.1016/j.trb.2018.01.007`。阅读问题定义和 loading/unloading subproblem 中与主张直接相关的条件；其 demand dissatisfaction/服务时间层级目标及 depot 规则不同，不能直接移植最优贪心结论。

内部 memo 记录版本与实际读到的节/命题，公开正文用正常文献定位，不写“只看过摘要、未读全文”等研究过程日志。新的方法主张要针对真实目标耦合、完整家族或有效证书；一般固定路线优化及网络工具均有先例。

## C. 数学问题：三个嵌套的完整路线家族

### C1. 父解与允许服务集合

对一个物理验证合格的父 fleet `p`，保留原始输入、车辆属性、目标参数和资源限制。对车 k，令 `π_k` 为父解按访问顺序排列的非零服务站序列，`E_k` 为其站点集合，`E=union E_k`。零服务节点规范化删除；depot 不计入 E。

用当前项目原目标 `F(y)=G(y)+lambda*P(y)`，其中 G、P、库存到目标比、权重及 S=0 约定完全继承原模型。以下所有家族均允许：

- 原允许服务站任取合法整数库存 `0..C_i`，pickup/drop 方向可改变；
- 当 `y_i=b_i` 时不服务并从路线删去，按保留节点重新计算真实旅行；
- 非 E 站固定 `y_i=b_i`，不访问、不操作；
- 空载出发、各前缀载荷在 `[0,Q_k]`、非零单向服务、访问唯一性、原 depot/连通性规则；
- 允许载货返回，返回卸货与站点装卸均按原物理时间计入；保留所有原车辆及合法空路线；
- 所有车辆的数量**联合优化**，Gini/惩罚用整个系统的最终库存计算。

E 是允许服务集合，**不是要求所有原站点继续访问的集合**。不能固定原数量、方向、末载荷、原总旅行时间或 Gini 值来代替整个家族。

定义：

| 家族 | 保留的结构限制 | 可以改变的结构 |
|---|---|---|
| `F_order(p)` | 服务站仍归原车；每车保留站点构成 `π_k` 的子序列 | 所有合法数量、方向及零服务删除 |
| `F_owner(p)` | 站点仍只能由原 owner 服务 | 每车可任意重排其允许服务站，同时改变数量/方向/是否服务 |
| `F_eligible(p)` | 只允许服务 E 内站点 | 车辆归属、访问顺序、数量/方向及是否服务均自由 |

证明 `F_order ⊆ F_owner ⊆ F_eligible ⊆ F_full`，三者都包含原父 fleet。车辆标签与输入对齐；档案 fleet 的整车重标号只允许在所有相关车辆属性兼容时进行，不把标签变化本身当作物理 owner 改变。去重不要求复杂的跨车对称性识别。

三个家族均使用**完整原始合法 g 域和库存支持**。不能直接复制 R166/R167 child frame 的 g 区间、已缩库存域或 incumbent cutoff；这些会错误缩小家族。最简做法是最小化完整原目标、保留原父解 Start，并以证据达到目标时提前结束，不添加 target cutoff 来排除父解。

### C2. 模型与物理家族的双向对应

给出可检查的模型说明，并证明：

1. 每个家族物理 fleet 都能映射为模型可行整数点，原目标一致；
2. 每个模型可行整数点均能解码为该家族内的合法物理 fleet，辅助 epigraph 不能产生低于物理目标的伪解；
3. 删零后真正连接相邻保留站点，不能把父路径旅行常数留在时间行中；
4. 全局库存目标不按车分解。若采用资源时间恒等式，要从空载出发和返回卸货推导，而不是遗漏 return load。固定统一装卸秒数时可核查 `站点装卸 + 返回卸货 = (pickup_seconds + drop_seconds) * 总pickup` 的适用条件；不适用时直接用原物理式；
5. S=0、空车、单站、方向翻转、删站跳弧、载货返回、容量/时间边界均有完整定义。

允许继承 R96 的 DAG 路线模型来实现 F_order，F_owner/F_eligible 复用当前已合格的 B 物理 writer 并加入明确限制。优先一个共享数据/目标/物理检查入口，不另写三个互不相认的优化器。复用 B 时只保留对整个家族有效的行与原目标，不把叶域或旧 cutoff 搬入；本轮不加入 C166/D167 作为第二研究因素。

### C3. 可达性与障碍证书

令 `v_j=min{F(x):x in F_j}`，经资格检查的受限下界和物理可行上界分别为 `L_j,U_j`。父解 `F_p` 始终保留为合法上界，因此

    L_j <= v_j <= U_j <= F_p,
    v_order >= v_owner >= v_eligible >= F*_full.

在求解前统一冻结数值政策。目标原值为 D2 中的 tau，建议用既有 `1e-7` 目标比较尺度定义 `theta=tau+1e-7`；采用当前更严格政策也可以，但须在 manifest 说明并统一使用，不事后改阈值。受限 L 必须通过当前 bound 资格和方向保护，不能直接把任意日志数当作可靠下界。每项同时保存 tau、theta、原始 bound、安全 L 和真实 F。

- **HIT：**存在经物理验算且 `F<=theta` 的家族内 fleet。已有见证即可，无需再证明家族最优。
- **EXCLUDED：**合格 `L>theta`。证明该完整家族中没有达到所声明阈值的解。
- **UNKNOWN：**其余情况；包括改进但未达标、没有改进、限时、下界仍低。错误/缺档另列，不装成科学 UNKNOWN。

HIT/EXCLUDED 是按已声明数值政策的结论，不冒充符号精确证书。通过同样政策报告可实现调量潜力区间 `[F_p-U_order, F_p-L_order]`，及该家族相对目标的最小障碍 `max(0,v_order-theta)` 的上下界 `[max(0,L_order-theta),max(0,U_order-theta)]`。如安全 L 含非有限值，按真实可定义范围报告，不制造有限区间。

受限下界不是原问题全域下界，不得写回 B 的 L 或当作全局 CERT。窄域的可行见证可以向超域传递；超域的合格下界可以向子域传递，反方向均不成立。保存原始 L/U 与传播后结果及来源；限时原始 bounds 不一定数值单调，不得人为修表。

## D. 固定档案、目标与免费前置检查

### D1. 三个物理输入、九个父 fleet

使用 R163 输入与 R163/R164 的 **B 最终 fleet，Seeds 0/1/2**。不是九个独立物理实例，也不是九次新完整算法运行。

| 输入 | input SHA256 | 原 T（秒） | lambda |
|---|---|---:|---:|
| `R163-C35-U` | `fb9d881dba6d0d07c59c48a683d2b2543f3effeae593306e28d79875cdcc20d7` | 10800 | 0.11068496171019777 |
| `R163-B35-S` | `8f644c76508a54443e280fe03833f15131989d55184bdfca21b56223f69c17b1` | 7200 | 0.10810343336504369 |
| `R163-X35-S` | `5804470a50da77c2da43ca5654b85e22f0e82459ef556d4d4d75e52e3a87daa9` | 10800 | 0.092888243831640058 |

其余 Q、容量、初始/目标库存、权重、距离和装卸参数从固定输入、实际 argv/manifest 读取，不能按短别名重新生成输入。Seed0 来自 R163；Seeds1/2 来自 R164。恢复最终实际 fleet，而非 H、未完成 Native incumbent 或某个方便取得的中间点。

任务安排前已从原 carrier 的 `result.json` / `audit.json` 核实九份父解可恢复，实际 audit hash 与 `complete_arms.json` 一致。直接按下表定位，不重新搜索父状态：

| 输入 | Seed0 run ID | Seed1 run ID | Seed2 run ID |
|---|---|---|---|
| C35-U | `R163_011_R163-C35-U_S0_B` | `R164_014_R163-C35-U_S1_B` | `R164_015_R163-C35-U_S2_B` |
| B35-S | `R163_013_R163-B35-S_S0_B` | `R164_017_R163-B35-S_S1_B` | `R164_020_R163-B35-S_S2_B` |
| X35-S | `R163_018_R163-X35-S_S0_B` | `R164_022_R163-X35-S_S1_B` | `R164_023_R163-X35-S_S2_B` |

成员根为 `results/unified_exact_round{163或164}/campaign/{run内三位编号}/raw/{完整run ID}/`；对应 carrier 是该轮 `artifacts/new_evidence_01.zip`。本地已有恢复件优先直接使用，只核对必要成员，不重下全集。

### D2. 统一档案目标

对每个输入，目标取 **R163/R164 的 B/P、Seeds0/1/2 这六份最终档案中，经当前原物理检查确认的最小 F**。这个封闭池和规则在任何新 Optimize 前冻结，三个 Seed 的父骨架共用一个目标，避免换目标使结果易看。预期如下：

| 输入 | 冻结目标 tau（预期复算值） | 目标来源 | B Seed0 / Seed1 / Seed2 的既有 F |
|---|---:|---|---|
| C35-U | 0.09331934374779818 | P Seed0 | 0.12956638965196035 / 0.10742986645444105 / 0.10808393649972804 |
| B35-S | 0.167746351588456 | B Seed1 | 0.19429031110944756 / 0.167746351588456 / 0.17427665216447524 |
| X35-S | 0.45747531701601785 | B Seed0 | 0.45747531701601785 / 0.46845018939924166 / 0.4606676342525399 |

表中为查验锚点；保留解析浮点全精度及原 fleet hash，以物理复算冻结值为准。超出既定数值尺度的差异先查明来源，不用更换目标掩盖。该 tau 是已知可行目标，不是已知最优值。

至少 B35 Seed1 和 X35 Seed0 的父解已达目标，直接记录 HIT，不调用 solver。其余最多七个 F_order 位置尚需判断，后续免费检查可能进一步减少。

### D3. 去重与已有见证检查

进入实质查询前完成，全部由 C++ 做物理/成员/映射核心检查，无 Optimize：

1. 绑定九份父 fleet、18份 B/P 目标池的输入/物理参数/fleet/来源；已有合格 R166 fleet 恢复材料可作载体，但不能改变 D2 的封闭目标池。对目标池逐一检查原物理可行性和 F。
2. 按输入与原目标参数、车辆属性和各车有序 eligible 序列定义 F_order 的身份。数量和方向不同但相同序列的父解属于同一家族，只求一次，保留全部父/Seed 行。取该家族已有最小合法 F 的父解作 Start，平手按固定来源序，不按运行效果挑选。
3. 检查所有已达 theta 的档案 fleet 是否属于各已登记家族；属于即直接 HIT。不能只把“父解本人达标”当作唯一免求解情形。
4. 将已达目标见证的库存向量映射到父解原 owner 和原顺序，删去零服务并允许翻向，直接计算真实旅行、载荷和时间。非 E 库存必须等于 b；映射合法则 F_order 已 HIT，即使见证原路线不同。失败只否定这次库存嵌入，不排除其他库存。R164 已有相同映射与失败检查时复用，并核对身份，不重算成新发现。
5. 记录合法整车重标号、家族去重、直接见证和库存重嵌入的具体来源。若父 fleet 原本不可行或无法恢复，作为数据缺项报告，不换成更好看的父解。

为 `C35-U / B / Seed0` 另登记 F_owner、F_eligible 两个位置。若父 eligible 集恰好覆盖全部站，F_eligible 即完整问题，已有 tau 见证已经证明 HIT；直接使用它，不发起伪装成诊断的完整 B 求解。若没有覆盖全部站，则如实记录 E 外站与目标见证的关系；已有目标 fleet 不属于 E 不能证明 F_eligible EXCLUDED。

任务安排前的只读预核已经发现：九个 F_order 家族互不相同；C35 Seed0 的 B 服务 34 站、唯一不服务站为 18，P Seed0 服务 34 站、唯一不服务站为 4，P 在站点 18 执行 pickup=8，故该 P fleet 不属于 B 的 F_eligible。把三份目标库存嵌入九份原骨架也只通过两个自达标位置：其余位置因 E 外库存变化，或真实载荷/时间不合格而失败。此处仅用于证明任务不是已知可达问题的重复求解，**不证明七个家族 EXCLUDED**；本地可在新的 C++ 入口中一次性核对并记录，不把它们再当新研究发现。

## E. C++ 实现、资格与有限查询

### E1. 一个统一研究入口

实现并记录如下能力：

- 从固定输入/fleet/参数读取家族，构建原目标精确受限模型；
- `order / owner / eligible` 三个显式 scope，共用物理语义和 checker；
- 父 fleet 的完整 Start 双向映射、行残差和整数类型检查；
- 求解后导出原始模型/参数/日志、完整 fleet、真实 F/G/P、每车旅行/装卸/末载荷/最大前缀载荷、受限界与资格；
- 不接入 B 生产路径，记录每次实际 Optimize 的 begin/end/call_id；任何内部辅助 Optimize 均计费。

实际包含原父解是必要检查，但不足以证明覆盖整个家族；仍须完成 C2 双向证明和小例枚举。不能以两个同源模型算出同值代替独立 oracle。

### E2. 少量、真正独立的资格

使用 C++ 精确枚举，构造两个小物理实例，建议最多 4 站、容量最多 3、两车；三个家族均按其完整定义枚举库存、允许的排列/分配和删零。在实质查询前冻结实例与预期值。实例不用于算法性能宣传。

这里完整枚举保证离散候选空间无遗漏；涉及距离/目标系数时，复用已有精确算术或可靠区间检查，或者明确报告“完整枚举加既定浮点数值资格”，不把双精度枚举自动称为符号精确最优证书。不增加新的测试面板。

两个实例应共同覆盖：非零目标与内部库存、方向翻转、删站跳弧、空车、至少一份合法 loaded-return 解，以及能触发容量或时间边界的错误候选。S=0 的目标和映射可以在同一枚举空间单独检查，不为覆盖一个词额外运行完整控制器。

在这两个既有 tiny 实例内，还须构造并枚举检查至少一个 `F_owner` 内但 `F_order` 外的可行见证，以及一个 `F_eligible` 内但 `F_owner` 外的可行见证，并映射到对应模型做行核对，确认较大域接受、较小域的结构约束排除。能形成严格最优值分离更好，但不要求为此搜索许多小例。这样可以检查顺序/owner 释放确实生效，不能仅凭三个 scope 恰好同值通过资格。无额外 Optimize 配额。

每个实例的三个家族各一次 C++ MIP，与独立枚举的家族 optimum/成员关系比较，**共 6 次 tiny Optimize，每次最多 60s**。允许最多 4 次资格修复调用，每次最多 60s，只解决具体失败，不添加新研究对象。纯 C++ 枚举、Start/行核对和旧证据复用优先，不写镜像实现式冗余测试。

若资格揭示实质错误，修正后定点重查；未解决时不执行依赖它的实质查询，提交可复查障碍和已完成的数学/文稿工作，不临时换另一套算法。

### E3. 查询位置、顺序与停止

完整表保留 **11 个位置**：九个父解的 F_order，以及 C35 Seed0 的两个释放域。自达标两项必然无需新求解；其余经去重、历史复用、成员检查和包含关系传播后，**最多 9 次实质 Optimize**。

先处理 **C35 Seed0 的 F_order、F_owner、F_eligible**，保护本轮最有解释力的三层问题；再按 C35 Seeds1/2、B35 Seeds0/1/2、X35 Seeds0/1/2 的固定顺序处理其余 F_order。自达标、见证复用和去重位置按下述规则跳过；不因结果有利而换位置或换 parent，总配额不增加。

若较小域已 HIT，超域沿用同一合法 fleet，登记 `witness_reuse`，不再 Optimize。F_owner 已 HIT 时 F_eligible 同理。若较小域 UNKNOWN，仍可按登记顺序查询上层，所得可达性只是充分证据，不能反推较小域 EXCLUDED。已有等价历史结果按同样规则复用。

每项最小化完整原目标，使用合格父解/本家族既有合法解作 Start。固定 Gurobi `Threads=1`、`Seed=0`、`MIPGap=0`、`MIPGapAbs=0`，其余 Native 策略采用当前默认；数值容差沿用合格入口并写入 manifest，不能按位置调参。这里的 Seed0 是诊断 solver Seed，不能误记为重新运行父 B 的 Seed。

每个实质家族位置最多 **300s Native 配额**，且每个家族只能有一个累计配额。使用统一的目标证据停止：找到合格 HIT 或取得合格 EXCLUDED 即收束，目标问题已经回答时不为证明 optimum 继续耗时。可以使用 C++ 中明确记录的停止参数/回调实现，最终仍按物理验算和安全 bound 判定；未通过验算的候选不算 HIT。到 cap 保留 UNKNOWN，不追加 Seed 或延长该位置。

### E4. 统一预算与计数

- 实质查询最多 **9 次 Optimize、2700s Native 配额**；失败/修复重跑也占此调用数和该家族累计 300s，不转入资格槽增配额。
- tiny/资格最多 **10 次 Optimize、600s Native 配额**，含上述六次及最多四次修复。
- 本轮研究新 Optimize 总数最多 **19 次**。所有调用（包括没有留下可用结果的调用）均计数，未用预算不转化成新家族。
- 整个诊断工作外层硬上限 **5400s**，包含构模、Start、读取、Native、核验、必要修复及诊断管理；记录实际 Native Runtime/Work 与外层成本，避免重复相加。Native 可能有收尾超时，按实际消耗计入剩余外层容量，不据此扩充研究位置。
- 档案下载/恢复的普通 I/O 单列；物理验算、去重及数学计算仍属于科学容量，不藏在“免费”字样后。这里“免费前置”仅指无 Optimize。

这些查询是离线诊断，不需要重新支付/运行 own-H；不能据其时间宣称完整算法加速。历史 P/B fleet 只用于问题定义、合法 Start 或见证，不回填旧运行的 incumbent、target 到达时间或主表。

## F. 结果解释与后续唯一决定

### F1. 必须给出的结果表

11 个预登记位置全部保留，包括 HIT/EXCLUDED/UNKNOWN、历史复用、同家族去重、包含关系继承、失败和未执行。至少包含输入/父 Seed/family 身份、原 F、tau/theta、原始 bound/安全 L/真实 U、判定及数值政策、来源 solve_id、规模、Native 和外层成本。

对每个有新合法 fleet 的位置报告 G/P 变化、库存改变量、删零/翻向、顺序和 owner 变化、载荷/时间。它们解释见证如何达成目标，不自动代表 Native 搜索因果。

严格按以下边界解释：

| 证据 | 可以得出的结论 |
|---|---|
| F_order HIT | 该父骨架在完整合法调量范围内可以达到档案目标；不能单凭离线代价/目标知识认定在线付费值得 |
| F_order EXCLUDED，F_owner HIT | 保持旧 eligible 和 owner 时，离开原相对顺序是必要的，允许重排并联合调量已足够；不是全局所有达标方案都必须重排 |
| F_owner EXCLUDED，F_eligible HIT | 保持旧 eligible 时，至少一个站的车辆归属必须改变；见证可同时改变顺序和数量，不能说“只改 owner”已足够 |
| F_eligible EXCLUDED | 任一达标物理方案必须服务至少一个原 eligible 外站点；仅删站、调量、重排和换 owner 均不足 |
| 任一较小域 UNKNOWN | 不据此声称相应结构改变必要；较大域 HIT 只证明该释放足够 |

C35 的两个释放域只针对 Seed0 这个父骨架。七个潜在非平凡 F_order 位置仍来自三个已暴露输入内的骨架差异；不报告成跨实例泛化比例，也不把它们视为独立样本做显著性检验。

### F2. 用证据选择下一步，而不是自动再诊断

完成后给出一个明确的 `research_decision.md`：

1. 若存在有实质目标改善的 F_order HIT，说明原骨架内仍有联合数量空间；对照 R76–83/R96–97/R159–160，指出现有方法具体漏掉了什么完整动作/耦合条件。只有找到确切增量，才提出一个**统一、own-state、付费计入完整运行**的后续候选；档案目标及 P fleet 不得成为未来算法 oracle。
2. 若出现合格的 order/owner 或 owner/eligible 跨层分离，优先选择其直接指向的单一结构动作类别，并给出为何旧邻域不足、完整方法如何合法调用、预期收益会在哪个可观测量出现。单独更大搜索域本身不是新算法贡献。
3. 若 F_eligible 被排除，下一步应关注允许激活原服务集合外站点的统一机制；不能继续只在旧集合内加数量射线或局部交换。
4. 若多数潜在非平凡位置 UNKNOWN，且 C35 没有合格的跨层区分，结论是**当前条件 MIP 的信息效率不足以支持继续扩大这组诊断**。关闭自动加时、换 Seed、扩输入的路线，保存现有区间和局限。此项不抹去已获得的具体正面证据：例如 C35 F_order 已 HIT 时，仍可按第1项评估一个有确切历史增量的机制；没有这类依据时，将近期工作重心转回当前成稿与新的实质结构思想。
5. 结果混合时说明证据强弱，至多推荐一种后续机制或明确不推荐，不能把四个类别都排成下一轮清单。

本轮不执行这个后续完整方法 pilot。研究建议应写出一个可检验假设、与最近历史的差别和有限验证条件，避免以“继续探索”结束；也不要求凭诊断结果编造 OR 级突破。

## G. EJOR/TRE 稿件、CSV 和必需成果

### G1. 有限稿件收束

当前英文稿已经重组。直接修正 `paper_body.md` §1.1 中类似 “accessible abstracts … unread complete formulations” 的内部阅读日志式表述：以实际读到的文献条件和本项目适用范围写正常学术叙述；阅读范围继续在内部 memo 透明记录，不编造等价、优越或首创主张。

保留当前 B/P/PS、C35 反转、相关 n35 OPEN、E+ 收益与费用、full/root 尚未建立独立外层净收益、C166 六行负面完整比较、D167 的三个条件增益/更大矩阵，以及既有权重包络和资源双侧区间。它们不在本轮重新计算。

若新结果有清楚的 HIT/EXCLUDED 或跨层分离，正文最多增加一个约 200–350 词的紧凑解释段，并视价值配置一张小表；完整模型、证书区间和全部位置放补充/本轮研究 note。多数 UNKNOWN 时不强行往正文加新章节，结果保留在研究材料。不能继续堆叠科研流水。

更新一份 `author_decision_memo.md`，分别说明：EJOR 可支持的共同库存状态与完整精确方法贡献；TRE 可支持的可认证资源/目标权重决策含义；OR 方向本轮实际获得的结构证据与仍缺的通用方法贡献。建议保持一套稿件并进入作者/共同作者的实质评阅，不让继续算法探索无限推迟成稿。这里只交付内部建议，不联系他人、不投稿。

继承当前已工作的渲染/组装实现，但**不要原样执行硬编码 R167 身份的 `scripts/round167_documents.py`**。该脚本使用 R167 OUT/temp/schema/current_round、source manifest/author memo 链接，并限定正文表1..10。新增一个薄的 R168 入口或恰当参数化，使本轮 build/QA/temp/manifest 身份写入 R168，既有 R167 证据保持原样；若确实增加正文小表，同步更新合法表号检查。无需重写整个文档系统。

从同一当前源生成组装稿及主/补充 PDF。记录实际词数/页数，定点查看发生变化的正文段、表、公式、引用和相邻页；没有变化的参数图与历史大表不反复重绘。

### G2. 112 条权威主表的入口收束

本任务配套提供的 `GI_TBC_vs_P_GRB_All_Tested_Instances.csv` 应为 **112 条数据记录、28 列、UTF-8 BOM、64,951 bytes**，SHA256：

`b728f85512741779a8b066ae9c974ec60892360c3fe15fbf7b946fb0ab0a4878`

R167 无新增完整 B/P 记录，这个版本未改变。112 是历史运行记录数，不是 112 个独立输入或 112 个严格 B/P 配对。

执行入口一次有限查找附件/已知工作路径；核实后将字节一致的权威工作副本放入 `E:\codes\ExactEBRP-work\data\GI_TBC_vs_P_GRB_All_Tested_Instances.csv`，记录来源、hash 和计数。目标路径已有不同内容时先保留并核对，不覆盖用户已有文件。保护 Desktop 的旧91条及仓库历史103条版本，不把它们当权威新表覆盖回去。

若附件未传入本地，记录缺失并使用已知来源做 reconciliation；不要反复扫盘，不虚构已获得112条，也不让这一项阻塞科研。已找到106条旧主表时可依 R167 G1 的既有来源核对 R166 六条增量恢复，必须保留旧行和原28列。只有找到可靠完整来源才能补齐，不能凭总数合成历史记录。

本轮所有路线家族查询、tiny MIP、档案再评价均不是新完整 GI-TBC/P 性能样本，主表预期新增 **0 条**。保留权威主表字节，不添加新优势行。另用 `route_family_results.csv` 保存本轮诊断，表头明确 restricted scope/档案 parent/非性能比较。

### G3. 科研成果

`results/unified_exact_round168/` 至少包含下列实际成果，相邻记录允许合并，避免重复文书：

- `goal.md`、`research_design.md`、source/candidate/environment manifest；
- `route_family_theory.md`：家族精确定义、双向模型/物理对应、目标证书和结论边界；
- 一个 C++ 研究入口、构建/运行说明及完整来源身份；
- 预先冻结的 `target_manifest.json`、`family_manifest.json`：父 fleet/目标池/输入绑定、全精度目标、去重、免费见证检查、11位置、参数与配额；
- tiny 独立枚举及 MIP 资格、实际模型/完整 Start/日志/新 fleet 与物理验算、全部位置 JSON/CSV、费用及失败/复用记录；
- `research_decision.md`、`author_decision_memo.md`、`final_report.md`、`decision.json`；
- 稿件定点修改、同源组装稿和两份当前 PDF；CSV reconciliation；独立复核及处理记录。

最终报告先回答研究问题，而不是先列审计数量：现有骨架能否达到目标、是否出现结构障碍/释放证据、哪项后续机制值得或不值得做、B 是否仍保持默认、论文与主表实际变化。

## H. 独立复核、正常 Draft 交付与停止

成果形成后做三个实际独立复核，可以并行：

1. **数学/模型：**完整家族而非邻域；可选 eligible、全 g/库存域、删零压缩旅行、载荷/返回卸货、S=0、所有车辆的目标耦合；双向对应、受限界方向和跨层必要/充分结论。
2. **实现/数据：**读实际 C++，核对不是 Python 优化外壳；独立小例、Start/类型/残差、父 fleet 和目标池身份、去重/见证复用、全部调用与费用、11位置、CSV 零新增和真实主表入口状态。
3. **研究/论文：**对照 R96/R97 及最近 primal 历史，检查确切增量、是否有信息、后续单一决定是否被证据支持；公开稿没有阅读日志、虚假泛化、离线结果回填或新的完整加速宣称。

记录具体问题、影响和修正，修正后只做必要的定点读回。审阅是完成工作的一部分，不是新增用户审批。独立代理不可用时披露替代核验方式，不虚构 reviewer。负面结论和研究局限按真实状态交付，不要求每项为正才算完成。

正常 commit/push，创建英文 **Open Draft PR**，建议标题：

`Round168: certify route-family target attainability and identify the next mechanism`

PR 首段说明当前可行解缺口、继承的固定路线方法、实际得到的判别/区间及研究选择；列明没有新增完整性能面板。按 A 使用 main 或 R167 stacked base，读回 head/base/Open/Draft 和稿件链接。不自动 merge、force-push、删除历史分支或向作者/期刊发消息。

仅对本轮新增/修改的源、文稿和必要证据做一次公开取回/字节核验。旧 raw 按固定 archive/member/hash 引用并按需恢复，不重新打包/下载历史全集。新 raw 使用本轮专属包/member map，不发布商业 DLL、许可证、凭证或私有前稿。科学提交与后续 receipt 提交分开，不填写尚不存在的 self-SHA；清理遵守工作区政策，零删除允许。

验收应看到：一个定义完整、C++ 实现且小例合格的路线家族入口；固定目标和全部位置的诚实判别/区间；有依据的下一项研究决定；有限稿件修正；B 默认与主表身份保留；独立复核后正常 Draft 交付。出现真实数学或实现障碍时交付确切证据和已完成成果，不改成重复大实验。

完成即停止，**不自动开始 Round169，不擅自执行推荐的完整方法 pilot**。

## I. 固定查阅入口

- [R167 / PR229](https://github.com/yifanXovo/TailoredExact/pull/229)，delivery `0da006b442ff7e59a2a63c6700138316611b2ce2`：`results/unified_exact_round167/` 的 `goal.md`、`final_report.md`、`decision.json`、`conditional_state_theory.md`、诊断/费用/CSV/review；实际 `src/round167_research.cpp`、`include/Round167ConditionalState.hpp`。
- [R166 / PR228](https://github.com/yifanXovo/TailoredExact/pull/228)，delivery `d497052216d5ae55b6ae0139ea30910cee2e5865`：原 physical checker、fleet recovery/materialization、参数/资源结果；相关 source/writer/factory 按调用依赖读，不把其 qualification frame 直接当本轮完整家族。
- [R163 / PR225](https://github.com/yifanXovo/TailoredExact/pull/225)，delivery `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`：`results/unified_exact_round163/{input_manifest.json,final_report.md,structural_synthesis.md}`，三个 n35 的 `inputs/*/first/instance.txt`，实际 campaign/raw carrier map。
- [R164 / PR226](https://github.com/yifanXovo/TailoredExact/pull/226)，delivery `de01e8fb27a954d031abac5fe99442d6c8d29d44`：`results/unified_exact_round164/{final_report.md,primal_targets_frozen.json,structural_synthesis.json,historical_member_access.json}`、`reports/{complete_arms.json,three_seed_arms.json,primal_target_arrival.json}`，Seed1/2 实际 raw/fleet/audit；以 carrier/member map 精确定位。
- R96：`results/unified_exact_round96/{final_report.md,fixed_route_protocol.md,fixed_route_report.md,fixed_route_cases.json,fixed_route_results.csv,fixed_route_audit.json,primal_final_decision.md}`、`reorder_F5_final/`、`reorder_qualification/`；`scripts/round96_fixed_route.py` 及其实际物理 checker 依赖。R97、R76–83、R159–160 按 B2 定向读。
- 当前稿：`results/unified_exact_round137/{paper_body.md,model_and_algorithm_appendices.md,mathematical_analysis.md,supplement.md,references.bib,manuscript.md}` 和当前 PDF/figures，复用最新已工作的文档构建入口。
- [Erdoğan–Laporte–Wolfler Calvo 作者稿](https://purehost.bath.ac.uk/ws/portalfiles/portal/87724146/bike_repositioning_post_refereeing.pdf)；[Szeto–Shui 作者稿](https://hub.hku.hk/bitstream/10722/259227/1/content.pdf)。

最终回复提供实际科学结果与条件解释、明确研究决定、完整位置/费用摘要、当前稿/PDF、CSV 实际变化和 Draft PR 链接。清楚区分已经证明/找到的事实、尚未判定的位置，以及将来完整方法才需要验证的收益。
