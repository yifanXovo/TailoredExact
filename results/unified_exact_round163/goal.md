/goal

# Round163：GI-TBC 的阶段定型——冻结 E+ 的新配置完整确认与结构证据整合

## 0. 本轮目标与执行原则

继承已完成的 R162。本轮回答一个项目级问题：**在稳定 GI-TBC/B 之外，R154/R156 的统一 proof-only 库存下界增强 E+，是否在预先确定的新配置上产生值得保留的完整算法收益？R138–162 的研究结果，应怎样准确进入现有论文的算法选择、结构解释和结论？**

本轮做两项相互支撑的工作：一是冻结 B、E+、P-GRB，在六个未用于开发的配置上完成十八个正式运行；二是把新增证据与已有数学、完整实验和负面结果接入现有论文，给出明确的阶段选择。稳定 B 是主比较对象，E+ 是唯一增强候选。算法、输入生成规则、实验顺序和评价口径先冻结，再观察结果。

R162 已完成其能力与成本问题：NB35 有小幅真实的 full-Q LP 增量，投影能保留大部分信息，但 PC 在两个主要来源上的完整 U 均弱于控制，最终 proof L 相同。因此本轮不继续预设一个连续产品、稀疏投影或更多 source 调用。新的联合整数物理机制需要独立的可计算对象和价值依据，不在本轮凭概念扩展实现。研究收束的目标是产生新证据和明确选择，并非要求每轮发明一条 cut，也不是停止算法研究。

总科学容量 **20h=72000s**；十八臂名义生产窗口合计 **9h**。预算是上限，完成任务后停止。不为剩余额度追加机制、种子、参数或旧困难角色长跑。代码、文档与必要分析正常推进，不逐 solve 增加人工审批。

算法定义对所有合法输入一致。实例名、来源标签、历史胜负、规模分档、处理器或机器速度不能成为在线机制开关。数学域、合法支持、当前合格 incumbent 和证明作用域可以进入既有算法。下述分规模实验窗口、固定运行顺序和运行环境属于实验设计，不进入算法策略。

**新增反复执行的算法核心与正式新机制必须用 C++。** 本轮不引入新算法核心；生产 GI-TBC/P-GRB 继续使用已合格 C++ 实现。Python 可用于编排、数据生成、离线分析、独立验证，以及冻结 E+ 已有的库存 helper。该历史 helper 保持算法与容量不变，每个 E+ 臂自付全部实际费用，并如实披露混合实现。不要把冻结确认顺带变成旧 helper 的全量 C++ 移植；若确有实现错误，按受影响范围修复、保留失败和版本分界，不能把改变后的候选与原冻结面板混报。

## A. 工作起点、版本与本地条件

工作入口：`E:\codes\ExactEBRP-work\worktrees\paper-current`。检查适用 AGENTS.md、WORKSPACE_POLICY.md、用户修改和活动进程，建立隔离 worktree。保护 `E:\codes\ExactEBRP` 和已有论文/研究树；新增 worktree、build、raw、archive、temp、restore 均置于 `E:\codes\ExactEBRP-work`。

本任务依据 2026-11-11 UTC（北京时间 2026-11-12）的审查快照，执行时刷新：

- 仓库：`yifanXovo/TailoredExact`。
- 最新 R162：[PR #224](https://github.com/yifanXovo/TailoredExact/pull/224)，Open Draft，未合并；branch `codex/round162-physical-g-completion`。
- R162 delivery head：`faa22ce4804f925081fd05322262b4f7261db51f`；fixed science：`fb087d7d9a3eef5bbff250487639d89b6e794739`。
- R162 base：`codex/round161-full-physical-rn`；main：`b2b940c1e517a72e226ec60fc49ff19651737632`。
- R162 完整实验实测 C++：`e920b92e199e825ec89a2932f701861ff158e0d4`；production PE SHA256：`fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93`。
- Gurobi 13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

若 main 已吸收所需依赖，从 main 开始；否则基于核实后的 R162 head 建立 `codex/round163-stage-confirmation`，Draft PR base 使用 R162 branch，无需等待前序合并。若已有本轮工作，先接续去重，不另建重复轮次。分别记录实测源、实际启动 PE/DLL、科学提交和最终 delivery 身份。

优先复用合格 production PE 与其冻结依赖；先核实际文件，不从文件名推断身份。确需重编译时使用既有编译器、优化级别、链接和数值政策，冻结一次新的共同 PE，供三方法全部正式运行使用。记录旧新身份及有限等价核对；不同时升级 Gurobi、改变 fast-math、调 solver 参数或重写框架。

## B. 已完成研究与本轮新增内容

先读 `docs/current_mainline.md`、R137 维护中的正文/附录及 R154、R156、R162 的 final_report、decision、配置和关键实现。下表提供排重边界；按具体论断回读相关数学或实验记录，不恢复全部历史 raw，也不重跑旧 producer。

| 阶段 | 已有成果 | 本轮如何使用 |
|---|---|---|
| main / R131–137 | 原模型、M-B/VD-P、物理启动、支持行、GI 覆盖与数值资格；R137 已有 120 个注册位置、P/PS/B、AM 敏感性、四类机制对照和有限 Seed1；已有论文正文及补充材料 | 保留理论及其适用条件，复用完整基线与归因证据；不以“首次补基础消融/首次写论文”为任务 |
| R43–46、R88–90 | 区间/乘积误差、lookahead、split/timing/LP-G 等研究及有限完整反馈 | 复用适用理论与边界；不重新包装 width-based 策略 |
| R103–107、R132–133 | 物理必要域、oracle/master/投影、联合服务结构与整数目标缺口反例 | 说明库存、资源、完整车队和目标图是不同对象；不新造同类玩具反例冒充发现 |
| R138–151 | STOCK、计数、RN/投影、GD、penalty 传播具有真实局部信息；完整收益混合，多项未获统一采用 | 归纳“更强松弛与完整方法收益分离”的实际证据，保留有利及不利结果，不逐项堆进主算法 |
| R152–155 | 库存目标 hull、自由物理耦合、有效定价；E 的 proof-only 放置保留正式 Native 输入并改善合格下界；完整反馈存在 plateau | 将已有正结果和未解决边界分开；R155 已建议阶段整合，不再延长相同反馈 |
| R156 | 统一 RN16384 的 E+；RX35 相对 E 的 proof L 增量约 .0137895；同一标量库存界剩余精度很小 | E+ 是本轮唯一增强候选；本轮新增的是开发配置之外的完整确认 |
| R157–160 | 有限库存族排除、整数量/车辆资源、物理实现与邻域；局部资源/物理解收益没有成为完整算法净收益 | 解释必要域与物理实现的距离；不再扩大 block/node/pass 或重开通用 master-oracle |
| R161–162 | 原物理载体上的 RN 替代、shared-G 完整物理端点；真实搜索和完整成本均已检验 | 关闭当前连续 Q 小变体链，保留结构认识，不将其当作新默认 |

R162 关键有限结果如下，引用已封存记录，无需重复实验：

- NB35：STOCK LP `.38263390965336053`，full-Q `.38282115944497652`，一行投影 `.3827968144066860`；完整增量约 `.00018725`，投影保留约 87%。该行有 5348 个原列非零项，“一行”不等于廉价或稀疏。
- RX35：STOCK 与 full-Q 自由 LP 值相同到既定资格尺度；固定旧点不可完成不等于自由最优值提高。
- 删除端点系统中的完整车辆 duration 行使 NB35 增量消失，只支持给定其余 Q 的条件必要性；不证明时间行单独充分，不分离 travel 与 handling 的独立作用。
- 六个完整臂中，PC 的 U 对两种控制均退步，最终 proof L 相同，无新证书。按原任务停止后四臂合理。
- 科学实耗 `32682.737052299548s`，其中六完整臂约 7.97h；必要验证约 47.49s。阶段资源问题主要是重复求解的研究价值，而不是审计消耗了大部分运行费。

形成一张简洁的“既有结论—证据身份—本轮增量—不能推出什么”表，服务论文与决策。不要把上述有限负面结果写成所有未来结构强化均不可能。

## C. 三个完整方法与实现冻结

### C1. B：稳定 GI-TBC

沿用 S2/ms2：完整自付 own-H、M-B/VD-P、pair-only、AM=.08、maximum depth=8、minimum width=1e-4、AP off，以及 R133 inclusive cutoff / source qualification 和 R134 独立 exact-zero proof 政策。以 `config/gi_tbc_round137.json`、`config/paper_s2.json` 和其权威完整 argv 为入口。裸 CLI 兼容默认 ENS-C 不等于 B。

### C2. E+：唯一增强候选

严格采用 B + R154 proof-only placement + R156 固定 RN16384 producer，以 `config/gi_tbc_proof_floor_round156.json`、`helper_manifest_Eplus.json` 及已合格 R162 E+ 运行绑定为依据。保持既有 DP / RN 调用规则、节点容量、Seed、数值资格和作用域合同，不改为4096/32768，不做预算网格。

库存 lower 只进入适用的 proof ledger，不加入正式 Native 行、raw AM 输入、hint、Start 或分枝策略。正式矩阵/调度输入设计保持原意，不因此保证 B 与 E+ 的完整搜索轨迹或 U 必然相同：helper 支付、剩余时间及合法提前认证都可能影响结果。

每个 E+ 臂从其自身 fresh H 和实际作用域构建自己的 helper 输入、结果与资格。不得免费搬入旧轮下界、旧路线或别的臂的源模型。路径/manifest/input 绑定可做必要的通用适配，但只能是接口与身份适配，不能按六个实例名称选择不同算法。核对 S=0、zero objective 和无合格 floor 时既有合法返回/回退行为；不能看到 floor=0 或该例不利就换数据或新增场景开关。

已有 online helper 本身按本臂 canonical root LP、B/Bminus 与合法支持工作，不依赖旧角色白名单；R156 campaign 的 SPECS/old_launch 属于历史实验编排。为本轮编写读取六输入 manifest 的通用 launcher，绕开旧角色检索，不把新实例伪装为 RX35/NB35。helper 必须接本臂生成的合格 root LP，不能把原始实例文本直接当其模型输入。保留原 helper/依赖 SHA、RN16384、原绝对 gap1e-4、old_joint=True、DP/fallback、root-once 与全局 deadline 的真实合同。若实际环境要求修改路径/亲和性等工程绑定，应统一修改受影响的主进程和 helper，另记新 SHA 与纯工程差异并在正式面板前资格冻结；不能仍声称修改过的文件保持旧 SHA。

### C3. P：冷启动 Plain Gurobi

使用项目既有 original compact 模型与 P-GRB 合同。完整 argv 取 R137 `matrix_frozen.json` 的 P 角色，并替换本轮输入、路径、实际模型/PE 身份与预算占位项。关键入口为 `--method gurobi --plain-baseline --round127-mode p`；不使用 B 的 preset 充当 P，不免费提供 own-H 或跨臂 Start。Gurobi 自身的正常启发式与默认 cuts 仍按原合同运行。

读回 cold `NumStart=0`、q0 的 MIPFocus=0/Cuts=-1/Presolve=-1 及原 requested gaps=0。`--round112-ens-start-compact` 属于 P-S，不应出现在 P 的命令中。

### C4. 共同条件与一次轻量资格

三方法使用同一冻结 C++ PE、Gurobi 13.0.2 和运行环境。Gurobi Seed=0，Threads=1，MIPThreads=1，MIPFocus=0；其他 q0 参数、requested gaps 与数值合同沿用。B/E+ 的 own-H seed=20260626。正式 Native 不沿用开发研究中的4096 NodeLimit。串行执行，沿用已有进程亲和性和计时方式；若环境拓扑变化，则一次统一绑定可用核心并记录，不能逐实例挑机器或核心。

全部 R138–162 非本候选机制保持关闭，包括 STOCK、RN source/替代、GD、penalty feedback/propagation、R160 邻域、R162 PC 等。仅 E+ 启用其已定义 proof producer。通过实际 argv、源变化、flag/readback 核实默认关闭，不仅依赖配置标题。

从三份干净的方法模板构造 argv，不从 PC/STOCK 命令末尾追加 off 来“关闭”。例如 `--round138-stock-rlt` 是只置 true 的无值开关，B/E+/P 应完全不带它；`--round162-physical-completion` 的 stock/on 路径也不能残留。拒绝矛盾或重复参数。P 的命令从 P 模板构造，不能从 E+ 命令仅替换 method。

资格限于会影响本面板的真实风险：完整参数读回、六个新输入的独立解析、original compact 的 Optimize=0 参考矩阵/类型/目标核对、默认关闭语义与 E+ 依赖/作用域核对。使用已有 exporter/checker 与 tiny fixture；必要时只做一次极小的端到端 smoke，全部计费并与正式样本分开。不要为相同恒等式重复构建大模型或重跑旧长窗口。若共享 PE 的某路径确实不合格，先修复其真实问题再冻结，不带缺陷启动十八臂。

## D. 预先确定的六个新配置

### D1. 固定来源与配方

使用已有归档来源：CITI/R57、CABI/R116、DIVVY/R132。复用 R137 的四 anchor compact/regional 选择法、R109/R122 的确定性库存 landscape、已有 sign repair 与输入序列化。当前来源足以回答同源新配置问题，本轮不新增网络抓取或新城市生成工程。

先提交算法/依赖冻结与下列生成配方，再生成一次输入；任何 H、DP、RN 或 Optimize 均在配方与完整输入 manifest 固定之后进行。新的公共 family 固定为：

`round163-gi-tbc-eplus-prospective-v1`

每源使用 `family + '|source=' + source + '|source_sha256=' + source_identity_SHA`。每行在调用 landscape 前设置 `selection_id='r163_'+实例ID`，例如 `r163_R163-C20-S`，并冻结这一参与 landscape hash 的字段。按下表顺序生成，同源的新选择排除本轮此前已选 source rows。沿用 R137 的 `0<capacity<100` 合格池条件与原来源质量规则。

| 位置 | 实例 ID | 来源 | n | 库存型 | 地理型 | replicate | 原物理 T/s | 每方法生产 cap/s |
|---:|---|---|---:|---|---|---:|---:|---:|
| 1 | R163-C20-S | CITI | 20 | shortage | compact | 1 | 5400 | 1200 |
| 2 | R163-B20-B | CABI | 20 | balanced | regional | 1 | 7200 | 1200 |
| 3 | R163-X20-S | DIVVY | 20 | shortage | compact | 2 | 5400 | 1200 |
| 4 | R163-C35-U | CITI | 35 | surplus | regional | 2 | 10800 | 2400 |
| 5 | R163-B35-S | CABI | 35 | shortage | compact | 1 | 7200 | 2400 |
| 6 | R163-X35-S | DIVVY | 35 | shortage | regional | 2 | 10800 | 2400 |

n20 使用 M=2、Q=[30,30]；n35 使用 M=3、Q=[20,25,30]。tp=td=60s，旅行与坐标转换沿用冻结生成器；代码仍支持一般合法输入。统一 `rho=1`，从实际序列化 weights 计算 `Omega=sum_i omega_i` 与 `lambda=1/Omega`，记录实际传给 C++ 的值和精度。原物理 T 与 solver cap 是不同量。

四个 shortage 角色用于检验潜在下界增量，两个非 shortage 角色用于保留零收益时的成本与行为。三种来源、两种规模、三 compact/三 regional 是有限覆盖设计，不是完整因子实验，不能从六例分离规模/城市/几何的独立因果效应。统一 rho 也不是重新做权重敏感性。

### D2. 确定性与新颖性核对

R137 的 replicate 是既有四 anchor 的槽位，不是“多试几次选最好”：compact rep1/2 用槽0/1，regional rep1/2 用槽2/3；首 anchor 由 FAMILY/V/source-row hash 排序，后三个为既定 farthest-first。按实际代码复用，不另造随机抽样规则。保留 generation dependencies 的固定提交/SHA、source identity、selection/landscape/parsed/source mapping 和所有实际输入。

生成后仅做静态合法性与去重：容量、库存/target、非负权重与正 Omega、车辆配置、shortage 标记与既有 sign repair、坐标/时间单位、文件 hash，以及两个规范化数学数据 key。基础输入 key 包含站点属性/坐标、b/D/w、n/M/Q，但排除名称、目录、T、lambda；完整配置 key 再包含 T、lambda、tp/td。两者都核对已有 input manifests 和主比较表对应输入，避免旧基础输入只改名、顺序、T 或 lambda 就冒称新 draw。数据生成不调用求解器、H 或库存界来筛难度。

如静态错误来自实现，修复生成器并保存旧产物及原因，在任何正式计算前重新冻结。若基础输入或完整配置出现历史碰撞，仅按预先登记的确定性规则处理：给该行 family 追加 `|collision=k`，selection_id 同时追加 `_collision_k`，k从1顺增，使用原配置和同一合格池重新生成，直到静态合法且不重复；保存全部碰撞。不得因为容易、OPEN、floor=0、预计 E+ 无收益或实际胜负重抽。正确且不重复的首个输入必须保留。

本轮六个新 draw 内，同源站点选择不重叠；与历史使用的站点行可以重叠，披露其比例和身份。本面板应称为**已归档来源上的前瞻新配置确认**，不是新城市、完全独立数据分布或真实观测需求的外部验证。所有六个配置对本次算法选择都是新数据；看过结果后，它们即成为暴露样本。

## E. 十八臂完整实验与成本

按 D 表位置成组串行，组内顺序预先固定：

| 配置位置 | 方法顺序 |
|---:|---|
| 1、4 | P → B → E+ |
| 2、5 | B → E+ → P |
| 3、6 | E+ → P → B |

每个配置三方法均使用同一实际输入、目标权重、原 T、solver cap、参数与资格政策。各臂自己的 H/helper 全部自付；原冷启动 P 不支付其未使用的 H。两臂内容相同的 H 仍分别执行、付费和保存，不能因已知可重复就免费传递。

每臂只有一个生产总 deadline，覆盖进程启动、H、helper、模型构建、全部 Native 调用、在线验证与收束。沿用已合格 shutdown-margin/outer watchdog 合同，并在三方法中一致记账。嵌套 Runtime/Work 只作诊断，不再叠加为外层费用。事后必要核验单列 `T_verify`，`T_total=T_produce+T_verify`。每次启动前保留实际完整 argv、输入/模型/源码/PE/DLL 绑定；结束保存完整路线、raw journal、receipt、求解状态与证据资格。

名义窗口总和为 `3×3×1200 + 3×3×2400 = 32400s = 9h`。按每臂 cap+900s 保守预约，共 `48600s = 13.5h`，预约不是增加 solver 生产窗口。旧 RX35/NB35/K20 的长窗口不属于本轮面板，不另做 PS、AM、E4096、多个 Seed 或 T/rho 网格。

**完整执行六组三方法，不因前几例有利或不利提前筛停。** 本面板用于确认冻结方法的外推与成本，不是候选开发的晋级筛选。正确性错误、环境不可用或实际总预算耗尽可以中止，但需明确列出实际完成与缺失位置；不得将缺失值记为失败/成功，或把只完成有利子集称作六例确认。正常提前认证则按既有算法结束该臂，不要求跑满 cap。

技术失败保留原始证据与已付费用，修复后只补受影响位置。纯 reader 修复不重跑健康 producer。若改变生产 PE 或性能相关算法/producer，需重新冻结受影响比较并补足必要的对应臂；新版正式比较继续满足共同 PE 与方法合同。不能只附一段版本说明，就把受影响的新旧方法拼成同一冻结面板；未受影响控制的复用须有实际依赖与语义依据。预算不支持完整修复时如实交付未决范围，不再切换第二候选补救结论。

## F. 分析问题、阶段决策与数学组织

### F1. 三种比较各回答什么

1. **B vs P**：当前稳定完整方法在本轮六个新配置上的竞争力。
2. **E+ vs B**：统一 proof-only 库存增强的净增量与代价。
3. **E+ vs P**：增强整包的完整竞争力。

所有十八臂同时保留，不按实例选择 B/E+ 组成一个并未实现的“最优组合”。B/P 的完整优势不能单独归因于 GI 分裂；启动与机制归因引用已有 PS/消融证据，并保持其原分母与条件。

报告 physical U、raw/qualified search L、final proof L、原 gap、CERT/OPEN、T_cert、T_produce/T_verify/T_total、Native Work/nodes、H/helper 成本、失败与中断。无原 gap 关闭证书时 T_cert 留空；cap 不是收敛时间。仅在双方均获证的明确子集报告证书时间比；全六例同时报告证书数与逐例 U/L，不把删掉 OPEN 后的时间均值当全样本优越性。零值、近零值和 signed gap 沿用原资格合同，不能自行更换容差。

对 E+/B 至少解释以下可从本次日志直接得到的量：

- helper 何时返回合格 floor，耗费多少实际时间；是否被 final search L 支配。
- final proof L 相对 B 是否提高，是否促成新证书/更早证书，还是只有中途 proof 改善。
- 物理 U、证书时间和完整成本有无退步；若 U/L 方向相反，保留 trade-off，不用一个 relative gap 掩盖。
- 无收益是 floor 本身弱、原搜索已超过它、零值已获证，还是 producer 在既定容量内未解决。区分这些机制，不仅给 Win/Lose 标签。

使用原始端点与数值资格尺度说明实质变化；运行时间的小差异不在单 Seed 上解释为稳定优势。不从六例估计独立城市/规模效应，不做缺乏样本支持的显著性叙事。既有 R132/134/137 与本轮分表呈现，重复配置、Seed、不同预算和版本不当作独立样本累加。

### F2. 必须作出的阶段选择

结束时给出有依据的推荐：论文主算法继续采用 B、推荐统一 E+ 作为主方法/明确增强版本，或 B 为主而 E+ 作为适用价值有限的补充。选择依据事先固定为：正确性与证据完整性、证书取得情况、双方获证时的付费时间、未获证时的双侧端点与实际开销。不得只选择对 E+ 有利的一个指标。

不要求 E+ 在六例上逐例无任何退步才允许肯定其价值，也不能以两例 proof L 增加掩盖普遍的 U/证书损失。先完整陈述收益和代价，再说明为何取舍；给出适合论文的有限结论。六例单 Seed 不证明普遍稳定胜过 P-GRB。若结果支持统一 E+，可以明确推荐，不必再以无限追加实验推迟决策；若不支持，明确保留 B 并结束当前增强的推广尝试，不在本轮另造机制。

实验期间及本 PR 不自动改变稳定发布默认或合并前序 PR。论文推荐、研究配置身份和已发布 main 身份分别记录。下一阶段只指出一个由本轮实际瓶颈支持的问题，以及启动它需要的具体数学/计算前提；不自动附上新 cut 菜单或执行新一轮。

### F3. 将已有理论与负结果组织为一条可检查的论证链

围绕以下关系修改维护中的论文正文/补充材料，引用既有证明并核前提，必要时补真实缺口：

1. 原 BRP 物理解与整数模型的目标保持对应：空车出发、唯一非零单向服务、前缀容量、载车返仓及卸载；整数库存与唯一单向服务导致服务量隐含整性，M-B/VD-P 的共享状态连接库存目标与服务。区分真实 Gini 与 epigraph 变量；这些状态联结不是隐含整性的额外必要前提。
2. 库存域、整数资源必要域、完整物理投影与各连续产品模型的关系。只有同目标、同作用域且已有证明的放松关系才能画包含箭头；不同旧 LP 数值不能直接跨域排强弱。
3. GI 覆盖的正确性、cutoff complement、同域取 max/union 取 min、合法提前认证和有限终止条件。保留 R133/R134 修复及数值精确法的实际合同，不声称所有 positive certificates 都是有理数精确证书。
4. proof-only 放置为何能增加证明信息而保持正式 Native 表达设计；它仍需支付 producer 费用，且不保证有限时间内物理解不变。
5. 用少量已有反例与实测对照说明：旧点分离、自由 LP 增量、付费 Native 改善、完整算法收益、未见配置确认，是不同层次的证据。

说明 interval helper 的实际目标/域：对 G epigraph 区间 `[gamma_L,gamma_U]`，其库存目标为 `max(gamma_L,G_true(Y))+penalty`，并要求 `G_true(Y)≤gamma_U`；不把 true G 本身强制限在该闭区间。S=0 时按原约定 `G_true=0`。这一点在引用局部库存 bound、interval cover 或零值情形时必须保持一致。

可使用以下标准 gap 恒等式解释 R156 及后续研究，但先核所引用数值作用域一致。令库存放松最优值为 f_I*，完整物理最优值为 f_P*，合格库存区间为 [L_I,U_I]，物理 incumbent 为 U_P，且

`L_I ≤ f_I* ≤ U_I`，`f_I* ≤ f_P* ≤ U_P`。

则

`U_P−L_I = (U_P−f_P*) + (f_P*−f_I*) + (f_I*−L_I)`，

其中只有最后一项由 `U_I−L_I` 控制。R156 的同域库存余量很小，意味着继续精算同一个标量 floor 的增益有限；它不能把剩余 gap 全部归于物理耦合，因为其中也可能包含 incumbent 次优性。R162 的连续 Q 小增量也不是整数物理 gap 的上界。局部 cutoff/interval source 必须先按覆盖合同处理，不能直接当全域 f_I*。

这类恒等式、一般 RLT/凸包/误差工具是组织与解释，不包装成新一般定理。不设“必须新增一条 OR 定理”的验收指标。已有 R133 固定正总量的目标缺口、R138 共同因子 hull、R143/161 distortion 等按真实出处引用；若发现缺失前提则修正文稿与结论，不趁机引入新的在线策略。

## G. 预算与产物

| 科学阶段容量 | 秒 | 小时 |
|---|---:|---:|
| 轻量接口/语义资格与必要数据核验 | 3600 | 1 |
| 十八臂完整面板及其必要验证 | 57600 | 16 |
| 最终证据独立读回 | 3600 | 1 |
| 技术失败、恢复与证据驱动调拨余量 | 7200 | 2 |
| **总科学容量** | **72000** | **20** |

阶段可以在总额内调拨，记录理由。新 LP/MIP、H/helper、科学核验及失败/恢复中的科学计算计外层实际费用；普通代码编写、编译、资料阅读和文档不计 solver 科学费用，但记录编译与主要 I/O。重复嵌套 Runtime 不加账；全部 fee 关闭，保留失败，不用未消耗容量触发额外研究。

主要结果集中 `results/unified_exact_round163/`。按已有习惯合并文件，至少保存：实际 goal；版本/依赖/方法冻结；生成配方与六输入身份；十八臂完整 matrix/实际 argv；必要资格；原始日志、完整路线与 proof 证据；费用失败；逐例比较与阶段选择；理论/论文增补及来源映射；独立复核、RESUME、publication/recovery/cleanup。

维护既有论文正文/补充材料的权威位置；以 R137 `paper_body.md`、`mathematical_analysis.md` 和当前导航为起点定位。将 R138–162 归纳成少数直接支持算法选择的结构结果，不把二十五轮逐轮流水账塞入主文。旧稿已有实验与理论不重复生成。若实质更新 TeX，按现有流程编译一次；不新增固定页数、多个 PDF 或无用途的展示件配额。

维护的主表文件名为 `GI_TBC_vs_P_GRB_All_Tested_Instances.csv`。先在用户既有输出与项目记录中定位真实文件，不假定它已在仓库某个路径。本轮若完整生成合格新 B/P 配对，按既有 schema、去重键与状态定义追加对应行，保留历史身份和来源链接；不把 E+ 换名为 GI-TBC。另存 B/E+/P 的本轮比较表。只更新已验证数据，缺失臂如实保留，不为凑配对填估计值。若找不到原主表，交付同 schema 的明确增量文件与合并说明，不声称已经更新原文件。

原主表28列顺序如下，供缺失时构造增量使用；现有文件存在时同时保留其编码/格式与既有标签规则。`权重倍数_lambda相对0.15` 填实际 `lambda/.15`，不能因本轮 rho=1 就填1。若无法确认旧 Win/Lose 分类规则，`对比结果` 留空，在 `对比说明` 写出证书与 U/L 事实，不臆造分类阈值。

```csv
实例,站点数_不含仓库,车辆数,场景,场景代码,数据来源,空间分布,路线时限_T_秒,目标权重_lambda,权重倍数_lambda相对0.15,Gurobi_Seed,重复序号,数据轮次,求解时限_秒,GI_TBC_状态,GI_TBC_收敛时间_秒,GI_TBC_未收敛Gap_百分比,GI_TBC_LB,GI_TBC_UB,P_GRB_状态,P_GRB_收敛时间_秒,P_GRB_未收敛Gap_百分比,P_GRB_LB,P_GRB_UB,对比结果,对比说明,实验数据来源,实例元数据来源
```

## H. 最终额外复核与交付

科学工作完成后，另做一次额外复核。可用独立 agent 分数学/方法、执行/数据、阶段方向三条线；记录真实独立身份，同一 agent 的检查脚本不冒充独立人员。复核聚焦会改变结论的问题：

- 是否忠实冻结 B/E+/P，原物理/目标/资格未改变；helper 适配是否只有通用接口差异。
- 新输入是否在任何性能筛选前确定；完整数据是否新，来源/场景/权重及历史重叠是否如实披露。
- 十八臂实际输入、参数、PE/DLL 与完整自付费用是否公平，缺失/失败是否保留；新核心是否遵循 C++ 合同。
- U 是否由原完整车队重算，proof L 与证书是否覆盖原问题；有没有把 local bound、raw claim、OPEN cap 或近零值误报。
- 结论是否同时考虑证书、U/L 与费用；是否把同源新配置说成新城市或大样本普遍优势。
- 理论层次和历史归属是否正确；下一阶段建议是否重复 R137 基础工作或 R138–162 已关闭的近邻研究。
- 主 CSV 是否只新增合格 B/P 样本，论文身份与稳定 main 身份是否分开。

修复结论性错误或收缩结论；不为非关键格式改动重跑科学实验。复核通过后完成正常 commit/push，创建**英文 Open Draft PR**，建议标题：

`Round163: confirm frozen GI-TBC variants on new configurations and consolidate the research stage`

PR 先说明阶段问题、实际完成的新证据、算法推荐与范围，再给关键验证和费用。按 A 的实时依赖选择 main 或 R162 stacked base；读回 base/head/Open/Draft 与证据链接。无需等待前序合并，不自动 merge、force-push 或删除分支。正负结果均按正常研究流程交付，更新当前研究导航。

只打包本轮必要新增证据，历史材料以 fixed commit/member/SHA 引用。做一次有限的新增公开恢复检查，不全历史空根重放、不重跑旧 solver。实测 PE、科学快照与后续 delivery metadata 分开；商业 DLL、许可证与凭证不发布，对恢复能力如实说明。

交付后沿用 WORKSPACE_POLICY/R122 的有界 metadata screening。仅清理本轮已结束、可重建且实际恢复覆盖的重复临时对象，保留唯一科学证据、失败、运行依赖、用户修改和活动 worktree。旧轮删除不在任务内；零删除允许。记录实际动作和空间变化，不更改全局 app/proxy/model/credential/权限设置。

## I. 固定来源与复用入口

以下均为定位/阅读入口，不是要自动执行的 producer 清单：

- [R162 / PR #224](https://github.com/yifanXovo/TailoredExact/pull/224)；`results/unified_exact_round162/{goal.md,final_report.md,decision.json,science_identity.json,complete_candidate_manifest.json,helper_manifest_Eplus.json,reports/complete.csv,cost_report.json}`；`docs/round162_physical_completion.md`。固定 delivery 为 `faa22ce4804f925081fd05322262b4f7261db51f`。
- R162 新 carrier 为 `new_evidence_01.zip` 至 `new_evidence_06.zip`，共118443879 bytes、5332 members；按所需 member 有限读取，不默认全量展开约1.36GB。
- [R137 / PR #199](https://github.com/yifanXovo/TailoredExact/pull/199)；`results/unified_exact_round137/{final_report.md,paper_body.md,mathematical_analysis.md,input_manifest.json,matrix_frozen.json}`；`scripts/round137_setup.py`、`round137_campaign.py`、`config/gi_tbc_round137.json`。原 matrix SHA256：`26f295da36097cd662b9c2ca049ab2452f0b295dfcdb12dd4b726ff25190c894`；只复用配方/接口，不直接运行会启动旧120位置的脚本。
- [R154 / PR #216](https://github.com/yifanXovo/TailoredExact/pull/216)、[R155 / PR #217](https://github.com/yifanXovo/TailoredExact/pull/217)、[R156 / PR #218](https://github.com/yifanXovo/TailoredExact/pull/218) 的数学、final_report、candidate/helper manifests 与 `config/gi_tbc_proof_floor_round156.json`；E+ 原配置源 `092bad58d677cd8bef934d91e11d8abff93cba83`。本轮实际使用身份另行冻结，旧机器绝对路径不是算法定义。
- CITI：`results/data_generation_citibike_round57/source_station_table.csv`；CABI：`results/unified_exact_round116/source/` 及 projection contract；DIVVY：`results/unified_exact_round132/source/DIVVY/{qualified_stations.json,snapshot.json,station_information.json}`。
- 生成函数：`scripts/round122_data.py`、`round109_data.py`、`round118_data.py`、`generate_citibike443_regional_v1.py`；参考 R137 的来源适配、固定 hash、四 anchor 槽位与 once-only manifest，不新增基于结果的选择器。
- `docs/paper_s2_release.md`、`docs/current_mainline.md`、R135 `model_and_algorithm_appendices.md` 和 R133/R134 修复，负责稳定方法身份与原物理/证明合同。

本轮完成标准是：**十八臂冻结比较提供新配置证据，阶段理论和历史结果被准确整合，并据此作出可执行的论文算法选择。** 不要求候选必胜，不用重复基础实验替代新证据，也不让一次阶段审阅自动变成下一串微机制试错。
