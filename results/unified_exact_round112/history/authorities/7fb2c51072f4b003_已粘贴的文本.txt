/goal

# Round112：同自付费 ENS 启动的原 compact 对照与精确后端贡献检验

你负责本地 C++ 项目 `yifanXovo/TailoredExact` 的本轮实施、有限完整评测、独立复核与新 stacked Draft PR。

**唯一目标：构造一个严格限定的归因对照 P-S，使原始 compact 后端独立支付并接收当前 ENS 的完整物理启动；在固定五角色、四方法的完整比较中，判断 ENS-C 与 M-B 各自在相同启动基础上还有什么实际后端增量。**

本轮交付明确的贡献判定及后续优先级，不开发新 cut、branching、反馈或表示组合。cold P-GRB 仍是主要 benchmark，P-S 是新增对照。ENS-C 默认与 R111 的候选支持结论保持原身份。新增正式集合 **20 臂、40800 nominal 秒**；总限额 **56 次保守启动 / 48000 外层秒**，资格及原生 reference/export 最多 **20 次 / 1800 秒**，包含在总额内。

## 1. 起点、历史与任务边界

核验 PR173 / `codex/round111-seed-block-confirmation`。本任务编写时最新 head：
`ded38c756a32a464bfa9800212da75778707d974`；
R111 科学 payload：`b92b27c895043af669e64ae32ef0b232262c3244`。
R110/R111 原 PE SHA256：
`c0384284aefd5aa2acc5d885ef37b0cfad6f93d083a5feb9ee693c41a786b411`；
Gurobi 13.0.2 DLL SHA256：
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

开始读取适用 AGENTS.md，核对最新远端、本地 HEAD、用户修改、已有本轮记录和活动进程。建议隔离分支/worktree `codex/round112-paid-start-backend-attribution`，结果目录 `results/unified_exact_round112/`。按 RESUME 续接，不覆盖旧 raw，不重复启动已完成正式臂。

必读 R111 goal、final_report、contribution_evidence_map、paper_candidate_spec、最终 admission/qualification 差异、完整时钟、reports_final、独立复核及 public 恢复说明；R110 的主结果/数值政策；R108 的 F2/C2/L48 原输入与实际 split；当前 ENS 启动、原 compact writer/求解入口、完整 Start mapper 和证据 reader。

针对性核对 R31 的旧 HGA-Start、R36 的 incumbent/geometry、R59 的 simple/Single/F0 归因、R64 的 warm/cold，以及 R88、R93、R95–100 的数量、反馈和表示实验。写一页 `research_question.md`，说明哪些已有实验可直接继承、当前匹配的 ENS 启动→原 compact 完整对照缺在哪里。已有 HGA 对照不等于本项；也不能声称首次发明 warm start。若远端已有本轮同身份完成记录，按 RESUME 承接；不能换名重复执行。

必须保留：

- R111 是 `CONFIRMATION_SUPPORT / R110_MAIN_36_PLUS_R111_SEED_6`。新六臂完整合格，三 Seed pair 为 TIE/WIN/WIN；不是 42 次新 wrapper 观测，也未增加独立地理样本。
- R110 仍 BLOCKED；旧 arm42 whole=3600.7215734999627>3600，仍 UNEVALUABLE。
- R110 ENS/P 与 M-B/P 均 11WIN/1TIE，且是同十一角色；M-B/ENS 为 5WIN/3TIE/4LOSS，G50-C1、G100-R2 严重。
- R108 C2 有 ENS/P LOSS、M-B/P WIN 的独特修复；F5 等代价仍保留。用户允许相对 ENS 的公开取舍，不设置 ENS 或 P-S 的逐例统治门槛。
- R99–100 已完成数量类型/方向/状态联结消融；R96 有固定路线数量诊断，R97 已测 incumbent 反馈，R104 和 R105–107 各自测试族已有 STOP。不能用本轮重开这些路线。
- R111 时钟修复已完成有限资格。本轮承接其有效执行方式和诚实限制，不再追求 Windows/IO 硬实时保证。

## 2. 可识别的问题：完整后端增量

记 H 为原 ENS 24+1 构造、下降及 R76/R83 物理闭包，C 为原始 compact 后端，E/B 分别为 ENS-C/M-B 的完整后端。本轮比较：

|方法|独立自付费启动|后端|作用|
|---|---|---|---|
|P-GRB|原 cold P 行为|原 compact|主要 benchmark|
|P-S|同一 H|原 compact，一次完整 Start|新增归因对照|
|ENS-C|原 H|原 VD-P/F0、AM、完整 ENS|当前默认参照|
|M-B|原 H|完整 ENS 加冻结 M-B 表示|R111 研究候选|

待检验主张：**相同自付费 H 后，完整 E/B 是否仍在正目标证明、C2 benchmark 缺口或已知取舍角色上提供材料性增量？**

E/P-S、B/P-S 是完整后端组合的对比，包含表示、域、LP/lookahead、target、Start 映射与后续搜索交互；不是 AM 单因素因果试验。P-S/P 衡量增加同 H、合法车队交接及其必要处理的净效果，不等于无成本的纯 Start 效果。禁止用“ENS 总时间减去启动”推算反事实，禁止将收益强行拆成可加百分比。

这是已暴露角色上的有限机制面板，不是独立确认集，不用于估计总体胜率或宣称统计显著性。本轮不追加新地理、lambda、Seed 或长窗网格。

## 3. P-S 的唯一实现规格

新增默认关闭且明确隔离的研究入口，例如 `--round112-ens-start-compact`。拒绝与 HGA-Start、外部 ENS 树、M-B、其它研究 cut/feedback/模型选项混用。保持原 P、ENS、M-B 的默认与实际执行路径；允许为接入而作必要的最小函数提取，不顺便重构。

### 3.1 自己产生并支付 H

P-S 从原始输入、原 ENS 启动 seed/参数开始，实际调用同一套 24+1、构造、下降、闭包和完整物理验证。完整费用从本臂必要入场工作开始；不得免费导入另一臂或历史的车队、UB、缓存、Start、cut。

保存 H 的实际入口/完成时间、路径/接受动作、原库存与完整车队，以及交接时 U0/G/P。正常穷尽的 P-S、ENS、M-B 应得到相同启动轨迹和同一物理车队，比较须保持实际车辆容量/归属；只允许原等容量车辆对称规范化。比较确定性语义字段（seed、逻辑步骤、接受动作、整数操作、库存/车队），时间戳、文件路径、方法标签等合法不同元数据另存并事前列明；不要求原CSV逐字节相同。不能只因 U0 相同就声称起点相同。

如果原全局截止导致某臂 H 未完成，保留其实际结果，不强迫额外启动，也不以另一臂补齐。该角色的“相同完整启动”归因资格须单独标注；无时间原因的确定性轨迹差异先排查实现，不把它当后端效应。确认实现偏离H合同则BLOCKED；仍无法证明匹配则记START_MISMATCH/归因不足，不能选择性忽略差异字段。

### 3.2 原 compact 与完整 Start

H 得到正目标合法车队后，构建并运行**真正的原 cold P compact 模型**。原数值行、列序、变量界/类型、目标/常数、原 exhaustive-block 策略、原参数与 native defaults 均保留。

不得添加 ENS 的状态行、F0、A/B、true-G 子域、cutoff 派生行/变量界、外部 LP/子 LP、AM、bound-target 暂停、研究 cuts/hints/priorities，亦不手设 Cutoff、BestObjStop、BestBdStop 或 StartNodeLimit。求解器因 Start 自己产生 incumbent/presolve/search 变化是被测效应，应如实保留。

可复用当前 `solveGurobiBaseline` 与 `mapVerifiedRoutesToCanonicalModel` 能力；现有 `gurobi_hga_start` 产生的是 HGA，不可改标签冒充 H。必须核查 mapper 实际支持原 compact 的所有辅助量。H调用配置与cold compact模型/求解配置明确隔离，防止为H启用的ENS强化flags泄漏到compact；共同输入、物理/数值参数和同一进程绝对deadline保持一致，切换函数不能重新起计时。

在 Optimize 之前完成：

1. 保存与本角色 fresh 原 P reference 相同的 canonical 模型；提交 Start 前后核对数值矩阵、界、类型、目标均不变。名字/路径元数据与数值区别单列，不能仅凭一个不完整 fingerprint 宣称等价。
2. 将本臂完整物理车队映射到**全部实际原生列**，包括未访问列、空车、车辆归属、载荷/次序、库存、比率及原 compact 辅助列。异构车不可按位置压缩后错配 Q。
3. 按原容差核对完整向量的有限性、类型、界、全部行和原目标，提交一次完整 Start，实际原生读回并记录 API、向量、日志。外部 Start 验证不能依靠原生修补隐藏漏列。
4. 非零且正常进入后端时，仅一次原 compact 完整 MIP Optimize；不先跑一个免费的 LP/presolve 诊断、不暂停重启、不补第二个 Start。必要的原生内部 presolve/heuristics 保持默认。

正确提交但原生未报告新 incumbent，不等于 API 失败；记录 accepted/rejected/no-new-incumbent/unknown 的实际证据。不能把日志未提及当零次接受，也不强迫设置参数使其接受。数学/映射/API/必需证据错误不得悄悄退回 cold 模式冒充合格 P-S。

### 3.3 own UB 与精确性

本臂 H 的合法完整车队自可用时起就是 own UB，即便 native 没有新解也必须保留。后端返回取本臂所有合法车队中的最好 U，不能因原始 P reader 只认识 native 解而丢掉 H 的 UB。所有新增 native 车队仍独立重算原物理目标；不接受别臂 UB。

当原 H 按原物理零判据取得 F=0，P-S 与 ENS 一样可用 own 零见证加全域 F>=0 结束，标记 `startup_zero`、native未曝光，无需强迫 MIP。该数学判据不是实例分派。不要为了好看人为提高本轮零容差；精确库存条件与实际浮点记录分开保留。其它情形沿原全程 deadline 求解；H完成后若工作窗口已耗尽，正常返回已有own UB与合格界，不启动必将越界的新MIP，不重置native allowance为完整cap。

原 compact 的合格全局 LB 与 own 物理 UB 按原数值政策组成结果；不把 warm Start 本身当 LB，不把模型局部 OPTIMAL 或 rc0 当无条件全局证明。任何已证数值矛盾拒绝受损调用的所有 native lower claims 及依赖结论，保留独立合法 floor/证明。

## 4. 数学说明与有限资格，先准入后正式

写简明 `mathematical_algorithm.md`，证明 P-S 只增加合法 primal 信息，不改变原物理整数问题与精确后端。保持空载出发、单站至多一车一次非零单向操作、每个 prefix/返仓载荷在[0,Q]、允许带载返仓、Y在[0,C]；Q 不是累计 pickup 上限，没有 min_ratio 库存下限。

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad r_i=Y_i/D_i,\quad
F=\frac{\sum_{i<j}|r_i-r_j|}{n\sum_i r_i}
+\lambda\sum_i\omega_i|r_i-1|.
\]
零分母沿原 evaluator；完整路线时间仍为旅行加 \((t_p+t_d)\sum_i p_{ki}\)，含返仓卸载。本轮 lambda=.15、pickup/drop=60/60、原输入 max-normalized 权重不变。

说明 lambda>0 且权重正时 F=0 iff Y=D。G50-C1 已有零目标证据，合法全局 L0 已精确，不能指望抬高它解决丢证；G100-R2 零最优尚未证明。M-B 的 p/d 隐含整数性、A/B、true-G scope 与完整 cover 继承，不重做表示网格。

资格总上限20启动/1800外层秒，包括所有原生 reference/export/测试，即使0 Optimize也计费；纯 Python 算术、源码审查与保留 raw 重放另列工程时间。只做本次新增/触及路径的必要验证：

- 从最终候选构建有限批量导出五角色原 P reference，与继承原始 reference 核对；证实 P-S 模型和原 P 数值一致。继承原生产参数、Parser 修复和 Start 基础合同，不重跑全部历史测试。
- 少量独立物理/全列映射反例：非零目标、零目标、空车、loaded return、异构 Q、未访问数量、缺列/非有限/超界/类型/行不合格、提交或回读失败。只能宣称实际执行的路径。
- 固定 H100：`reference/round100_confirmation/H100.txt`，实际 V20/M2/Q13,21/T5100，原 SHA `04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71`；四方法 Seed0 各 cap120 的实际 CLI。至少验证 P-S 真 H、原 compact、全列 Start、实际 MIP、own UB、正常返回和完整时钟；对P-S/ENS/M-B独立核对H配置、seed、确定性动作与完整车队匹配，元数据差异按3.1节处理。不是性能样本，不为追求认证延时。
- 复用仓库已有正目标微型见证5/24，P/P-S 各 cap60，核验当前入口的真实全局认证；另一个已知零目标微型 P-S cap60，核验 own-zero 结束及0 Optimize。微型的输入/实际物理参数先冻结，不把“zero handling”误称“zero objective”。
- 检查最终 wrapper 的 necessary audit/输出/qualification trailer 全部落在正确时钟和费用内，复用 R111 有效方式。原验证语义、原30秒 reserve 不改；不以把新 Start/物理验证搬到 cap 外提速。无需重做 R111 全部八次旧 raw envelope。

独立 reviewer 签署 `performance_admission.json`，绑定最终生产源/编译器/PE/DLL、全部性能 helper、资格结果、五输入、20完整argv/顺序、时间/数值政策及第7节判定。正式臂1不得早于签署。

本轮 P-S 需要新生产接入，因此四方法正式臂使用**同一新冻结 PE**；ENS、M-B、cold P 的实际算法/矩阵须验证与继承定义一致。旧 R108–111 结果只作历史定位，不能代替任何本轮正式臂或作为同构建精确计时对照。

## 5. 固定五角色、20臂，完整执行正负结果

全为 Seed0，严格按下表串行；每组一个直接 wrapper、四个独立 native/算法子进程。第一至四组平衡位置，第五组顺序也在任何结果前固定。没有额外 Seed、按表现延时或替换角色。

|组|角色与用途|V/M|Q|物理T秒|每臂cap秒|本组顺序|
|---:|---|---|---|---:|---:|---|
|1|F2：非零目标、发现与证明尾部分离|20/2|30,30|3600|1200|P、P-S、ENS、M-B|
|2|R98-C2：M-B曾修复ENS/P缺口|30/3|20,25,30|7200|1800|P-S、M-B、P、ENS|
|3|R108-L48：历史实际分裂与多叶曝光|48/4|30×4|18000|1800|ENS、P、M-B、P-S|
|4|G50-C1：已知零最优、M-B丢证|50/4|30×4|7200|1800|M-B、ENS、P-S、P|
|5|G100-R2：V100、own UB取舍|100/8|30×8|18000|3600|P、ENS、P-S、M-B|

输入原 bytes/SHA：

|角色|仓库路径|SHA256|
|---|---|---|
|F2|`reference/round86_unadapted_confirmation/F2.txt`|`ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e`|
|R98-C2|`reference/round98_confirmation/C2.txt`|`07d0964c87b534254e6bf2957911859a6a2bd73e377211728b7e65f44294fc76`|
|R108-L48|`reference/round108_confirmation/L48.txt`|`8ce2bceb8de415a1ff62ea78790456ee54e3542ce57714a7a53505d30ea54755`|
|G50-C1|`reference/round109_geographic/G50-C1.txt`|`5740d09bf218cf6921cee6e60198f673151d6426fbcb0840259647129f3c4ed5`|
|G100-R2|`reference/round109_geographic/G100-R2.txt`|`b3f3a1270f062e9f3af64d5b00392f51821bb775818edc6cd383fcd62550618f`|

核对原 manifest 和当前磁盘；不能因为同叫 C2/F2 而读另一轮同名实例。T 是物理约束，cap 是研究窗口，不得混用或重生成库存。

ENS 原 preset `research-round83-vds-equal-net-exchange`；M-B 只加 `--round98-state-service m-binary`，effective identity 为 `research-round99-ensc-discrete-structure-m-binary`；`--round100-continuous-quantities` 为false。保留24+1、VD-P/F0、AM=.08、原深宽/cover/epoch/cache/target/terminal、原类型恢复和合法 Start。

全部方法 Threads=mip_threads=1、Seed0、Presolve=Auto、MIPGap=MIPGapAbs=0、FeasibilityTol/OptimalityTol=1e-6、IntFeasTol=1e-5，保留原单核affinity、编译配置/栈和30秒收尾reserve。不同 cap 仅定义评测窗口，不进入算法分派。禁止节点k秒切换、Work/停滞阈值、实例/规模/库存/历史SHA dispatch。

## 6. 实际观测与正确性

每臂记录必要入场、H、模型/Start、LP/MIP、返回、必要 postexit 审计、最终写盘及 whole clock。正式性能以完整 cap 为准，native-only within_cap 不代替 whole。必要工作先完成再盖相应时间戳；外层费用覆盖真实 wrapper 退出。不同阶段的嵌套时间不能重复相加。

最少充分输出：

- 自己的初始完整车队/U0与全部合法 UB 流，native 与 startup 来源分开；完整物理回放。
- 当前模型、所有实际 calls/返回、实际参数/type、完整 Start 及读回、true-G/cutoff/epoch、LB及cover义务。P-S全域与ENS子域各按自身模型验证。
- native root/end bounds、nodes/Work/iterations、实际 cut 类别计数、真实 LP/MIP 分配及 parent atomic split。未记录者写unknown；不新增昂贵的全树追踪，也不由日志推断隐藏分支因果。
- startup、LP、MIP及必要封装成本；有可靠目标证书时才回溯“本臂达到该目标的首个已验证可用记录”，与完整认证时间分开。未知 native 真正首次发现时刻不能伪造。
- 固定检查点300/600/900/1200/1800/3600中实际覆盖者，以及每臂真实终点。已证自身证书可延续；未证提前正常退出不能插值到 cap，最后车队不能倒填。
- same-H trace/车队配对资格、六类方法比较、原始缺失/失败/签名及费用。

沿 R110/R111 最后有效数值政策。外部见证仅可在离线且满足当前全部列/行/界/类型/域时反证 native claim，不作为该臂 UB/Start。正G子域不能被域外零解反证；受损 MIP 不连带抹掉独立合法 LP。未知/超cap不能记TIE，微负signed gap保持，完整覆盖认证使用原1e-7政策，不改变容差；原生数值认证不称为独立有理数最优证明。

若仅离线 reader 出错，保留 raw，用新版本复算并证明差异，不重测性能。新的数学/范围/身份错误先停依赖任务，不能按输赢临时豁免。普通 time_limit、无材料改善或 Start未形成新incumbent不是工程故障。

## 7. 事前冻结的比较与明确阶段结果

对每角色固定输出六类配对：ENS/P、M-B/P、P-S/P、ENS/P-S、M-B/P-S、M-B/ENS，共30个配对位置。先给 U/L/signed gap/证书/完整时间和未评估原因，再给分类；不跨角色平均原始 F，不用平均数掩盖严重损失，不以各角色赢家拼成算法。

沿用 R111 材料性，候选A、对照C：
\[
a_U=\max(.001,.01|U_C|),\quad
a_\Delta=\max(.001,.10|\Delta_C|),\quad
a_t=\max(30,.10t_C),\quad \Delta=U-L.
\]
仅A认证为WIN，仅C认证为严重LOSS；双证按完整时间材料性；双未证且数值合格，至少一项U/gap材料改善而无材料变差为WIN，反向LOSS，同时改善和变差为MIXED，否则TIE。未知或不可比较为UNEVALUABLE。严重双证沿 t_A>=2t_C 且差>=120；严重双未证沿 U损失>=max(.001,.05|U_C|) 且gap损失>=max(.005,.25|Delta_C|)。合法时间区间仅在整个区间分类不变时可评价，保留区间而不制造精确speedup。

**唯一轮次状态**：

- `ATTRIBUTION_COMPLETE`：固定20臂已按冻结身份完成，正确性与完整时间合格，所需证据可重建；按下面规则分别给两个后端结论。正常不足比较可以形成明确的不足结论，不把“没赢”当BLOCKED。
- `BLOCKED`：真实数学/同构建/执行/时间/资源障碍使固定任务无法完整完成。写明受影响臂、已有观察和未识别问题，不择优拼接，不自动追加性能尝试。

对 X=ENS、M-B **各自**保留五项 X/P-S 分类向量，并按下列互斥规则给一个描述性增量结论。只有相同完整 H/车队且正式可比较的记录才有相同启动归因资格；记合格分类数为W/L/T/M（M为MIXED）：

另核实际后端曝光。若共同H已产生零目标而相应方法提前结束，保留完整方法的时间/证书配对，但该后端归因项记 `BACKEND_NOT_EXPOSED`，按下述不完整归因处理；不能把启动墙钟差记成后端WIN/LOSS。正目标但无剩余工作窗口、尚未进入所比较后端的情况也独立标未曝光，不虚构后端表现。

1. `INCOMPLETE_ATTRIBUTION`：任一X/P-S角色缺少有相同完整H且实际后端曝光的合格可比较记录，包括所需臂未启动、身份/证据/完整时间不合格、普通数值不足的UNEVALUABLE、BACKEND_NOT_EXPOSED、截止导致H不完整或START_MISMATCH。保留所有有效局部比较、缺项与具体reason，不以剩余子集顶替五角色分母；真实正确性/身份/时钟故障同时按轮次BLOCKED处理，普通不足不自动称故障。
2. `POSITIVE_ONLY_OBSERVED`：五角色均有资格，W>=1且L=M=0。仅表示本面板有正增量、没有达到材料性门槛的反向观察，不等于逐例严格统治或总体稳定性。
3. `NO_POSITIVE_INCREMENT_OBSERVED`：五角色均有资格，W=M=0。保留实际0至5项LOSS/TIE；不宣称统计等价、后端永远无效或全部P优势已因果归于启动。
4. `MIXED_INCREMENT_OBSERVED`：五角色均有资格的其余情况，即正增量与损失并存或存在MIXED取舍。明确列出所有严重损失，不能只报WIN数量。

另给三个不合并的科学判据：F2/L48当前实际是否为正目标认证、X/P-S是否有窗口证书/完整认证时间增量；C2的M-B收益在P-S面前是否仍成立；G50-C1/G100-R2的取舍对应own UB、合格LB还是认证时间。实际split单列，不由这些对照单独推断AM因果。

这些是有限观察分类，不是新的候选采用门槛，不覆盖R111状态，不要求胜P-S才能承认既有cold P收益。不能用ENS在一个角色的胜利加M-B在另一个角色的胜利凑某个统一方法的结论，也不另设任意WIN数来充当论文资格。

最后用一页 `next_research_decision.md` 作出有条件但明确的下一步优先级：

- 同H后仍有正目标证明与关键角色增量：保留该后端贡献主张，下一阶段优先固定候选的独立覆盖/论文实验。
- P-S在本面板吸收多数cold P优势而后端未见增量：收缩后端贡献表述，优先定位额外模型/探测成本或简化机会；本轮不直接采用P-S。
- 结果因角色分化：指出收益落在primal完成、非零目标证明还是某种实际结构暴露，只提出一个由实测支持的后续问题；无证据则明确目前无法定位。

不在此轮末尾自动实现建议、换默认、另开长跑或恢复已STOP机制。有限结论本身就是本轮交付。

## 8. 总预算、冻结与停止条件

总56保守启动/48000外层秒；资格/reference原生总20/1800已包含。正式为五wrapper+20children=至少25启动、40800 nominal秒；每组另预留120秒外层行政/关闭费用，共600秒，这不是每臂cap的额外求解时间。资格按上限预留后，计划最多45启动/43200秒，剩11启动/4800秒只用于真实资格或工程故障处理。

剩余额度不放宽资格/reference的20次/1800秒子上限；两层上限均须满足。正式臂没有重跑额度。无法在这些界限内完成准入则交BLOCKED，不借总余量无限补资格。

所有实际多出的 driver/原生辅助进程先记账，未知费用取可证明向外上界；失败声明槽不退，native嵌套时间不再额外加一次。实际回执不能在必要尾部完成前提前写成最终费用。构建、纯Python和离线独立审查/打包另列工程，人工未知写unknown。

每组前核对余量足以覆盖所有未开始固定臂的nominal及外层预留。实际早停节省不得用于加Seed、长窗或性能重跑。

**每个正式臂最多启动一次。** 普通正负结果都完整执行五角色；即使前几组已出现强正/负信号，也不取消剩余对照。真实未解决故障暂停。正式开始后实测PE、性能helpers、时间/数值/归因规则冻结；若必须修改这些内容，本轮不能拼接不同身份或重开20臂，交BLOCKED并保留结果。

不并行优化器、编译、压缩或重型复核。只对具体未解决问题追加受影响验证，不用完整重审次数或大载体体积充当研究进展。

## 9. 交付与一次新的公共恢复

必须包含：research_question、算法/物理与Start证明、最小diff、production/PE/DLL/helper身份、原模型等价、有限资格、独立admission、固定manifest/20argv、全部actual raw/Start/车队/clock/费用、same-H比较、30配对、分后端结论、final_report、更新贡献地图和next_research_decision。

独立reviewer从本轮实际raw重算关键物理、原P与P-S矩阵/Start、own UB、当前scope/返回/cover、完整时间、same-H资格与分类；旧R111结论只按固定来源承接，不重新审核旧全部raw矩阵。复核必须包含实际正负结果，不能只检查通过臂。

复用已有去重/分片/恢复工具，载体只收当前必要证据和显式历史依赖；保留原始错误/null，不发布PE/DLL/license/凭证。依赖闭包先检查，再实际export、空目的地restore，从恢复根重建当前核心CSV/JSON并逐字段比较，再做恢复根独立复核。禁止回读原worktree补洞。新public receipt与冻结科学payload分开提交，不让commit“包含未来的自身验证”。

这是离线可恢复证据，不声称重跑完整原生搜索。只有真实恢复失败才修复/重做受影响步骤；不再复制整个R110/R111旧载体或循环全历史审计。

## 10. Stacked Draft PR 与最后额外复核

创建英文research Draft PR，base为核验后的R111分支。建议标题：
`Round112: test tailored backend contribution against a self-paid ENS-start compact control`。

PR开头写唯一轮次状态、两个后端各自结论、20臂完整性及cold P仍为主要benchmark。说明P-S真H/原矩阵/完整Start/独立计费、五角色选择理由、实际增量与最坏P/ENS/P-S代价、预算、公共恢复和局限。不将该控制包装为新数学算法，不写成AM单因素效果或新独立确认。

推送后实际核对远端head/base/open/draft及必要科学文件/分片；区分源码实测冻结、科学payload和后续验证receipt。不改旧PR结论、不合并、不替换默认、不修改用户无关文件或环境权限。

全部任务组织与结果分析完成后，额外做一次完整目标复核：

- 有没有把原P“去掉部分强化”冒充真正compact，或重命名HGA充当当前H？
- 有没有免费导入Start/UB、漏计H或必要验证、只给native时间、修改cap/容差？
- 是否实际核验同H完整车队，而非仅同U；正确提交与native采用是否区分？
- 是否把P-S当新主要benchmark/隐藏晋级门槛，或逐角色挑ENS/MB凑结论？
- 是否如实保留零目标、多叶曝光、删失、普通不足、严重代价与历史STOP边界？
- 是否用本轮实际结果决定一个后续优先级，并在有限任务末尾停止？

只修正实际缺漏。最终回报PR链接、20臂与30配对完整性、两个后端判定及关键证据、coldP比较/代价、全部费用、恢复结果、明确后续优先级。遇真实BLOCKED则给足以解释障碍的证据和已完成结果，不将缺测伪称算法失败，不自动重试。

