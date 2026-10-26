/goal

# Round131：固定 S2 版本的主 benchmark 补齐与分层证据收口

你负责 `yifanXovo/TailoredExact` 的一次有限研究任务和英文 stacked Draft PR。本轮不是新候选筛选，不继续外层控制消融或调参。**R129已经完成统一二站版本选择，R130已经正式采用 GI-TBC 的 MS2 实现（短名 S2）。本轮只补齐这个实际版本的固定主benchmark表、tiny绝对开销与有限V35范围证据，并将已有论文主张准确收口。**

只运行两个完整方法：冻结S2、原cold P-GRB。不得因某个实例S2R/MB/PS更快而切换，不再验证到“每个组件都赢”。合法负面或开放结果也是完成结果。既有六个SC问题整组迁移，含原双方开放的SC-C20-S；不只重跑旧赢家。所有输入都已曝光，不称为新生成、盲抽或未见独立验证。

固定主入口 `E:\codes\ExactEBRP\`；全部新工作树、raw、临时、稿件、归档与恢复对象位于 **`E:\codes\ExactEBRP-work\`**。复用稀疏 linked worktree、共享Git对象库及现有native资产。PR交付后执行轻量筛查与安全清理，保护用户dirty、未推送内容、唯一证据、失败记录和旧工作树；不自行迁移C/D盘。

## 1. 起点与已定科学结论

编写时核验 R130/PR192：open、Draft、未合并；分支 `codex/round130-ms2-paper-attribution`；head `c302bae0ec128f0d4c651fb29d04cb41b491f721`，科学提交 `dc2cbece4294d16dfab603c2429dee8676f3dd0b`，源冻结提交 `7564a5415331b380e24d1ec06936dcfd56557e67`。建议分支 `codex/round131-final-s2-benchmark`，输出 `results/unified_exact_round131/`。

复用原 E3：
- PE SHA256 `2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c`；
- Gurobi 13.0.2 DLL SHA256 `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。

先检查远端、AGENTS.md、本地HEAD、活动进程、已有产出、用户修改和E盘峰值空间。更晚提交需记录真实继承与差异，不盲目退回或覆盖。相同任务健康进程继续运行，已有产出先核对，不能为了得到新计时而重跑。

必须继承：
1. R130的24臂/30项比较完成。S2/PS在B20两Seed均有实质认证时间优势，在C20两Seed均为S2单侧认证；三方法/四方法在B30仍开放。
2. S2/S2R四项双侧认证为三Lose一Win，但均在既定TIME_CLOSE幅度内。B20实际split三次，单根仍很快。没有重复的外层包实质收益，不把split次数当提速证据。
3. R130不要求继续给D“找正面结果”。R127 tuned-P留出负结果、旧同H混合结果、R129/R128反转继续保留。
4. 论文唯一算法身份已经是S2；旧完整三站M-B为前代。仓库ENS-C历史默认仍不改，论文复现必须显式给模式。
5. R130纠正的是派生support行分类：同站跨车辆唯一服务行不是同车二站cover。原矩阵、结果和费用不变。分析复用更正后的同车辆分类器，不恢复旧shape-only统计。
6. R130相关Start、source/return/cover、数值与E2/E3桥接已合格，本轮不重建全套资格或数值修复平台。

## 2. 本轮的必要增量与停止边界

以前R126/R127六个SC主表及tiny表大量记录的是三站M-B，不可改贴成S2。当前S2虽已有开发、前瞻选择和机制对照证据，尚缺一个整组、同构建的这六题主benchmark表。本轮填这个**版本与证据的一致性缺口**，不是怀疑已经完成的S2采用，也不为改变R130外层归因而再次试验。

三个明确层次：
- A：六个既有V15/V20完整认证主面板，两Seed，24臂。
- B：两个既有V8/V10，三Seed、每Seed两次匹配重复，24臂；检验最终S2而非旧M-B的绝对开销。
- C：既有两个V35角色，Seed0，各S2/P一次，共4臂；使用R122原2400秒窗口，观察最终版本范围边界，不是续接旧树或无限长尾。
共52臂、26个匹配组、10个已知问题、0新输入、0调参、0生产编译、0算法修改。

不运行MB/ENS/PS/PT/S2R/MR/MG/D1，不加新Seed或候选，不运行V50/V60/V100、不改λ、T、Q、库存或时长来制造证书。B层虽然臂数多，名义预算仅2160秒，统计不能因重复多而支配A层结论。V35不必认证才能完成，双方开放也不算速度Win。

## 3. 方法身份与不能改变的条件

| ID | 实际完整方法 | 论文定位 |
|---|---|---|
| P | 原cold compact，`--round127-mode p`；无H、无外来Start、无项目cutoff或新强化 | 主要benchmark |
| S2 | 冻结MS2，`--round127-mode ms2`；完整H、R、A/B、二站support、有序供给、C_G、原Gini控制与数值政策 | 唯一proposed method |

S2沿R130 paper_version_manifest的完整argv；不要只运行简写。尤其不要再附加会覆盖模式的 `--round128-mode off`，不要打开`round112_ens_start_compact`或`s2-root`。每臂都使用真实最终解析参数和原生读回验证身份；PS-only收据不要求P具有。

统一lambda=.15、取卸各60秒、H_seed=20260626、Threads=MIPThreads=1、原CPU亲和性、PresolveAuto、MIPFocus=0、原生Cuts=-1、请求MIPGap=MIPGapAbs=0，以及原FeasibilityTol/IntFeasTol/OptimalityTol。不改TimeLimit为WorkLimit。H不按规模换算法、不截断预算求更好MIP时间，不用旧车队或已知最优值免费启动。

各方法独立完整支付准入、H（如适用）、建模、所有LP/MIP、Start、在线核验和规定输出。每次native只用剩余全程时间；沿原30秒shutdown reserve、6秒native偏移、2秒hard-stop偏移，包括90秒tiny合同。cap是相同的完整预算，不是要求求解器内部恰好运行cap秒。

输入与运行常量固定。数学对称性/可达性等合法数据条件可按原规则响应，不新增文件名、规模、机器性能、elapsed-time分派。共同support候选上限及顺序不改；S2无三站行，但仍需记录实际pair/cover/conditional及供应兼容数量。

E3资产缺失或SHA不符时先记录并恢复合格原资产；不得无声重编译成新PE并仍称本cohort。可完成无关准备和文稿；确需新生产构建则属于新的明确授权问题，本轮不混入其性能。

## 4. 已知输入、数学时限与计算预算

不调用数据生成器。读取下列原字节并验证SHA，路径可在本工作根中作明确副本映射，数学内容不能改。原来源是两个既有安全站点表，库存scenario为**服务站总量**shortage/balanced/surplus，不是每个站都缺/富余；地理compact/regional及原欧氏旅行规则不变。

| 层 | id | V/M | 库存／地理 | Q_vector | 物理T秒 | 每方法cap秒 |
|---|---|---|---|---|---:|---:|
| A | SC-C15-S | 15/2 | shortage／compact | [30,30] | 3600 | 600 |
| A | SC-B15-S | 15/2 | shortage／regional | [20,40] | 5400 | 600 |
| A | SC-C15-B | 15/2 | balanced／regional | [30,30] | 5400 | 600 |
| A | SC-B20-S | 20/2 | shortage／compact | [30,30] | 5400 | 1200 |
| A | SC-C20-S | 20/2 | shortage／regional | [20,40] | 7200 | 1200 |
| A | SC-B20-U | 20/2 | surplus／compact | [30,30] | 7200 | 1200 |
| B | SM-C8-S | 8/1 | shortage／compact | [20] | 2400 | 90 |
| B | SM-B10-B | 10/2 | balanced／regional | [15,25] | 3600 | 90 |
| C | PB-C35-U | 35/3 | surplus／regional | [20,25,30] | 10800 | 2400 |
| C | PB-B35-B | 35/3 | balanced／compact | [25,25,25] | 7200 | 2400 |

输入身份：
| id | 原路径 | SHA256 |
|---|---|---|
| SC-C15-S | `results/unified_exact_round126/inputs/SC-C15-S.txt` | `9849095e3496254fa9ea28715939b7380bd47fbaa6e998bff56c688e0e176101` |
| SC-B15-S | `results/unified_exact_round126/inputs/SC-B15-S.txt` | `b87de1a37e60cc2e7cbbf7885bac1155ac4c0b14356de7c5af92e402555474de` |
| SC-C15-B | `results/unified_exact_round126/inputs/SC-C15-B.txt` | `c0d5fc4eee62e1e454b8acde8b721640e410bf496593b14d4cbdb1ccf36f14ea` |
| SC-B20-S | `results/unified_exact_round126/inputs/SC-B20-S.txt` | `70ebad164c3da58c52d0ad7fce651a6f4d90f54323a939d6c109a17eaffb8b3c` |
| SC-C20-S | `results/unified_exact_round126/inputs/SC-C20-S.txt` | `5729b59070d5451750e8e0b2446b08381e5c001e96d3c3f247e57801f6dcde11` |
| SC-B20-U | `results/unified_exact_round126/inputs/SC-B20-U.txt` | `c688de15fc31612b83885efe2e86e60f50ba57a5c5119f7e7801bf240a096bab` |
| SM-C8-S | `results/unified_exact_round127/inputs/SM-C8-S.txt` | `cd0c04a81c0096147d1c365eb4da02ad85397bbef2987d0b13be00628a6b3be0` |
| SM-B10-B | `results/unified_exact_round127/inputs/SM-B10-B.txt` | `32496a729183c1fa6c9837bb6a18455f8e60ea96fc8a8b803a2ddc5ae15aca8f` |
| PB-C35-U | `reference/round122_paper_benchmark/PB-C35-U.txt` | `67fa5712962980350c0b7be00abbcc4866af0fe376d0395b565ec082d36842e5` |
| PB-B35-B | `reference/round122_paper_benchmark/PB-B35-B.txt` | `41fdb57cad176be7746bb7c884f62da1643920ac2c49d75bd5235663936a5e3a` |

A层对应R126完整六题，四shortage、一balanced、一surplus；不删除原SC-C20-S开放题。B层的SM-B10-B在历史上为合法空车队/结构较易问题，保留，不将它称为全部tiny难度代表。C层选取R122的完整两个V35子集，一题surplus、一题balanced，参数和2400秒合同不变。历史较小窗口的MS2开发结果单列，不拼成新长运行。

保留既有selection/landscape小文件解释来源与构造。没有必要重新获取站点网页、安全数据或旧全carrier。若源文件失去可验证字节身份，标必要数据缺项，不按同名再生成“近似相同”实例。

## 5. 增量资格与正式前封存

先做轻量检查，不新增通用审计平台：
1. 核对E3/DLL原字节、源seal、本文52个位置、全部input SHA、真实mode和计时入口。reader的旧Seed0-only顶层字段与已资格endpoint解释沿R130，不改raw以获得PASS。
2. 复用R130 P/S2模型桥接与R127/R128/R129 MS2删除资格，不重做PS/S2R人工边界。检查更正后的support分类器实际生效，跨车辆唯一服务行不计同车pair cover。
3. 对新runner/路径适配允许少量无Optimize或原生smoke，使用既有训练小fixture，不以正式十题的预跑结果选择模式/参数。相同构建无必要时不额外求解。
4. 冻结完整manifest、顺序、脚本身份和资源表后正式开始。生成文稿/分析适配不改变生产算法。完整数学差异或证书矛盾先定位；工具路径/换行/序列化问题允许有限、只读、等价修正，保留失败与旧seal，不自动迫使健康臂重跑。
5. E盘空间估算含raw、压缩中间件和一次恢复峰值；磁盘路径变化不能成为更改计算合同的理由。

尽可能由另一执行者在正式前核对模式、全部固定输入和三层统计，而不是写一个没有实质检查的PASS。

## 6. 唯一正式运行表

`repeat`只表示同Seed、同方法完整新运行，非续跑；同一匹配组两方法串行。以下顺序冻结，不能按前一结果调整。

| 组 | 层 | id | Seed | repeat | 方法顺序 | 每臂cap秒 | 臂数 | 名义秒 |
|---:|---|---|---:|---:|---|---:|---:|---:|
| 1 | A | SC-C15-S | 0 | 1 | P → S2 | 600 | 2 | 1200 |
| 2 | A | SC-C15-S | 1 | 1 | S2 → P | 600 | 2 | 1200 |
| 3 | A | SC-B15-S | 0 | 1 | S2 → P | 600 | 2 | 1200 |
| 4 | A | SC-B15-S | 1 | 1 | P → S2 | 600 | 2 | 1200 |
| 5 | A | SC-C15-B | 0 | 1 | P → S2 | 600 | 2 | 1200 |
| 6 | A | SC-C15-B | 1 | 1 | S2 → P | 600 | 2 | 1200 |
| 7 | A | SC-B20-S | 0 | 1 | S2 → P | 1200 | 2 | 2400 |
| 8 | A | SC-B20-S | 1 | 1 | P → S2 | 1200 | 2 | 2400 |
| 9 | A | SC-C20-S | 0 | 1 | P → S2 | 1200 | 2 | 2400 |
| 10 | A | SC-C20-S | 1 | 1 | S2 → P | 1200 | 2 | 2400 |
| 11 | A | SC-B20-U | 0 | 1 | S2 → P | 1200 | 2 | 2400 |
| 12 | A | SC-B20-U | 1 | 1 | P → S2 | 1200 | 2 | 2400 |
| 13 | B | SM-C8-S | 0 | 1 | P → S2 | 90 | 2 | 180 |
| 14 | B | SM-C8-S | 0 | 2 | S2 → P | 90 | 2 | 180 |
| 15 | B | SM-C8-S | 1 | 1 | S2 → P | 90 | 2 | 180 |
| 16 | B | SM-C8-S | 1 | 2 | P → S2 | 90 | 2 | 180 |
| 17 | B | SM-C8-S | 2 | 1 | P → S2 | 90 | 2 | 180 |
| 18 | B | SM-C8-S | 2 | 2 | S2 → P | 90 | 2 | 180 |
| 19 | B | SM-B10-B | 0 | 1 | S2 → P | 90 | 2 | 180 |
| 20 | B | SM-B10-B | 0 | 2 | P → S2 | 90 | 2 | 180 |
| 21 | B | SM-B10-B | 1 | 1 | P → S2 | 90 | 2 | 180 |
| 22 | B | SM-B10-B | 1 | 2 | S2 → P | 90 | 2 | 180 |
| 23 | B | SM-B10-B | 2 | 1 | S2 → P | 90 | 2 | 180 |
| 24 | B | SM-B10-B | 2 | 2 | P → S2 | 90 | 2 | 180 |
| 25 | C | PB-C35-U | 0 | 1 | P → S2 | 2400 | 2 | 4800 |
| 26 | C | PB-B35-B | 0 | 1 | S2 → P | 2400 | 2 | 4800 |

A层12组/24臂/21600秒；B层12组/24臂/2160秒；C层2组/4臂/9600秒。总26组/52臂/33360秒。每组唯一预定比较S2/P，共26项；10个不同输入。A两个Seed相反顺序；B每Seed的两个repeat相反顺序，原两题/三Seed/两repeat全部保留。C两个角色方法先后相反，但只Seed0，不作两Seed稳健性解释。

所有正常Win/Lose/未定/零目标/无后端曝光都保留。没有“资格允许再挑一题”，没有根据前组好结果取消后续风险题。正式不与编译、压缩、其他native或重型检查争用计算资源。各次从头运行，不跨臂共享H、UB、Start、basis、树或本次缓存；没有免费warm-up。

## 7. 认证主指标、tiny风险与删失

每臂保留T_produce、T_verify、T_total。只有完整物理、source/return/coverage及原数值政策通过，才T_cert=T_produce；否则null。原生OPTIMAL针对实际提交域，不把target达到、日志有好解、某叶闭合或TIME_LIMIT当全原问题认证。零目标独立依据及后端未曝光单列，不压制合法零证书。

每对先给BOTH_CERTIFIED / S2_ONLY_CERTIFIED / P_ONLY_CERTIFIED / BOTH_OPEN / UNEVALUABLE。双方认证按未舍入T_cert快为Win、慢为Lose、相同Tie；单侧证书按方向判；双方开放UNDETERMINED，不算Tie/Win。未资格是证据缺项，不能当算法普通Lose或超时。不得用cap填未知认证时间或计算未经观测的cap/T精确加速。

双方声称认证但物理原目标超出原一致性容差不相容时，先调查证明／输入问题，不能直接计算时间Win。

同时显示绝对秒差与双方认证时间比。条件几何均值必须明确其双方认证交集，不代表整张表；总生产时间包含timeout但不是总认证时间。若编制求解比例曲线，未认证视为在实际观察终点右删失；不能假定其在名义cap时仍继续运行，不能外推最终时间。

B层单独报告每题六次的完整方向、各Seed两repeat、全六次中位数及范围。`T_S2-T_P>=10秒`单列警示；P单侧认证单列更重要风险。慢0.1秒仍记录Lose，不因未达10秒改Tie。10秒是实用阈值，不是统计噪声定理；不足两个有效repeat时不补一个“估计波动”。B层24臂不能与A/C合成一个加权胜率。

A/C也显示对称实质时间差：慢者−快者>=max(10秒,10%快者)，仅解释幅度，不改变Win/Lose、不作隐藏选算法闸。单侧认证不受该阈值豁免。开放U/L/gap可补充呈现，不能作认证速度胜利。

## 8. 物理与证据核查、统一算法范围

服务站求和排除depot；空载出发，允许带载返仓；唯一非零单向服务，库存和每个载荷前缀合法。完整时长是旅行加(pickup_time+drop_time)*累计pickup，累计pickup不是车辆瞬时容量；原目标只含真实Gini与相对目标偏差。不得改变这套语义、权重归一化、零分母或数值容差。

复用可靠reader，核验全部正常返回、实际输入/PE/参数、车队、模型/Start与完整覆盖身份。只读跨臂见证只能撤销同scope的真正矛盾，不能给另一个方法补UB或证书。保留raw signed gap、旧顶层标志与计算后的合格endpoint，不能裁剪LB掩盖错误。实际伪闭合行仍需绑定数值前提/域/覆盖，不按含0<=-1矩阵INFEASIBLE就宣称包容物理域为空。

对每臂记录已有H成本、LP/MIP/Work/节点、split/target、Start以及真实pair/triple数量。三站应为0。没有新cuts，无需额外Optimize去寻找LP违反；诊断缺失写unknown，不填零。不同方法相同Seed并不保证相同搜索路径。Work不替代主时钟，也不改生产停止条件。

## 9. 分层主表与论文迁移

正式后一次性重建本轮结果，形成三张表：
A. 六题两Seed的S2/P完整认证表：证书、T_cert、双/单侧/开放、U/L、全部时间与反向结果；
B. 两个tiny的六匹配观测及10秒警示；
C. 两个V35的Seed0完整结果，若双方开放明确“最终时间排序未知”。

补充一个**证据登记表，不是性能择优表**：每条记录绑定原问题SHA、方法/构建、数值/时钟、Seed/repeat、cap、原轮次、开发/选择/保护/诊断/主benchmark身份。结果去重key应包含真实run身份；同题跨轮性能不能取最优，也不统计成新问题。
- 本轮A是完整既有SC面板的最终版本测量，替代主文中将前代SC结果冒充S2的可能；旧表保留为历史，不能改写或贴标。
- R129四题保留“选择时前瞻”身份，之后已被用于研究，不再称未见。保护例单列；本轮不重跑它。
- R130同H与S2R对照是已知角色的归因层，完整保留PS和S2R的反向/开放数据。
- R127/R128 MS2已有开发数据可准确引用，但不与本轮新时钟拼出一个共同原生实验。
- R122/R123旧完整MB/ENS的V50或长窗仍只作前代，不改成S2。本轮最大V35、C层单Seed，**不宣称已验证V50/V60**。
- R127 tiny为旧MB，不能继承为最终S2全部小例性能。当前B层填这个版本缺口；也不对两个tiny夸大难度代表性。

源于不同轮次的结果可以列在有明确轮次/版本/协议列的完整登记表中，但禁止无层次“总Win/平均加速”。固定A为本轮主要认证面板，B/C与R129/R130各自报告。若需要一个总述，先给不同输入数和分层分母，不能以大量tiny repeat增加成功比例。

本轮没有新组件，不作新的C_G、D或H因果主张。论文可以称tailored branch-and-cut framework with Gini-interval decomposition，但定制表示/有效行、H、外层控制与Gurobi原生分支割职责须分清；存在分解不等于本批已证明其净加速。

## 10. 阶段出口：结束统一版本证据补齐，不重开选择循环

执行COMPLETE/PARTIAL/BLOCKED与科学结论分开。全部有效结果无论是否有利都可以完成本轮。S2采用是既成决定，本轮不要求重新满足R129五项选择条件，不因一例Lose切到S2R/旧MB，也不追加输入/Seed/时长直到“通过”。

优先级：
1. 真实模型/身份/证书矛盾：`PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION`，明确影响范围，保留未受影响结果，不能由Win抵消。
2. 必要正式位置或必要证据缺少：PARTIAL/BLOCKED与缺项；不得用旧构建/旧最佳时间填补。
3. 完整有效数据下：`FINAL_VERSION_BENCHMARK_COMPLETE`，另附有限科学评价（有直接认证支持／混合且有明确反向风险／主要开放、支持不足），不强迫科学标签正面。

`benchmark_assessment.md`必须回答：最终S2对P在哪些题/Seed真正更快认证或单侧认证，哪些实际Lose，哪些仅开放端点优势；tiny是否有可重复的10秒警示或P单侧风险；V35是否扩大非零认证范围；两来源和scenario覆盖仍有哪些限制。所有问题都用真实表支持。

如果发现S2对P重复的实质反向认证结果，定位该问题和当前主张应如何收缩，只提出一个必要的决策点；本轮不修算法。若结果足以支持限定论文叙述，就交付用户实质审阅，结束本轮；不因“还能多做一种消融”自动立项下一轮。不能据有限known输入宣称普遍支配、统计显著或某期刊录用保证。

## 11. 预算、恢复与工程弹性

| 费用 | 名义秒／额度 |
|---|---:|
| A：24臂 | 21600 |
| B：24臂 | 2160 |
| C：4臂 | 9600 |
| 正式52臂合计 | **33360** |
| 增量资格／必要额外原生诊断弹性上限 | 1800 |
| 26组管理参考 | 720 |
| 最大计划 | 35880 |
| **全轮外层计费上限** | **43200** |

正式名义9小时16分、外层12小时是机器费用上限，不是向用户承诺等待时间。资格软计划900秒；明确工程需要可在总预算内扩至1800秒，不另设机械启动次数硬闸。剩7320秒覆盖后验、局部文稿更新、发布和一次必要恢复，不是新实验额度。不得预支未知提前认证节省。

中断先检查进程PID/出生时间/argv/seal，不将健康进程当失败重跑。已有封存产出优先只读恢复。真实外部故障且没有可恢复合格产出时，最多一次事前记录的同题/Seed/repeat完整两方法组恢复，须保证总预算能覆盖全部剩余义务；原失败与费用保留，不只重跑慢的一方。正常超时、Lose、无split、无收益不重跑。预算或资产真正不足则明确缺项。

计量非重叠外层子任务，不重复加H/LP/MIP嵌套秒；显式保守allowance不冒充精确CPU时间。复用现有table/reader/archive适配，避免每轮复制大量同义脚本或整个仓库。

## 12. 复核、交付、PR与安全收尾

交付前由另一执行者尽可能重算26项比较、10输入分母、三层统计和所有null；用已可靠读取器回放全部最终车队；至少独立抽查一份非空车队、一条真实完整最优证书链、一个实际pair-only模型，若当轮没有相应证书/非空解则报告缺乏该抽样，不生成新性能样本。区分“另一步作者自审”和另一执行者，不称全量有理证明/外部复现。保留raw/derived支持家族计数差别和失败审查。

有限文件：goal、固定input/运行manifest、真实E3/argv/依赖绑定、arms/pairs、三层summary、benchmark_assessment、完整证据登记与版本迁移、必要来源/物理/call索引、final_report/review_actions/RESUME/费用。维护一个论文源并导出完整PDF，局部更新实验主表、方法版本和限制，保留R125公式/cuts/H/controller；不要重新设计排版平台。检查实际受影响PDF页和交叉引用，导出故障与科学结果状态分开。

英文stacked Draft PR建议：
`Round131: consolidate the frozen S2 certification benchmark and small-instance overhead evidence`

从实际R130研究分支建立，不merge、不force push，不向main累计旧PR，不改历史数据、不代发导师邮件/投稿。核对远端base/head、表格与可读性。

发布扫描实际文本/载体：不提交key、Cookie、许可证、PE/DLL、字体或无权全文。只打包当前必要raw与精确小依赖，不嵌入历轮campaign。科学提交后一次本轮必要公开空根恢复，不新求解/重编译，不为元数据回执递归再次打包；真实失败在同根有限修复并保留事实。

沿每命令禁用无关Git自动维护，不改全局配置、不gc/prune/repack。远端可读、必要核验完毕、相关进程退出后，清理本轮自有重复ZIP/恢复展开/可重建页图/字节同一临时PDF；删除范围外先有可靠保留。保护唯一raw、不同内容稿、失败记录、用户dirty和旧worktree。开头保护用户修改可做轻量定向hash；没有基线就不声称整个任务用户文件字节未变。只报告实际量测的空间差异。

**阶段目标：不再寻找新算法或给每个组件寻找正面故事；用同一个已采用S2和同一个P，在整组既有实例上形成可直接引用的最终版本认证表、独立的小例开销表和有限中例边界，然后交付可以作实质论文判断的完整证据。**
