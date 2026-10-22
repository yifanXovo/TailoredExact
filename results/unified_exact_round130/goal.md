/goal

# Round130：固定统一 MS2 论文版本，补齐同启动 compact 与实际分裂控制对照

你负责 `yifanXovo/TailoredExact` 的一次有限阶段研究，并提交英文 stacked Draft PR。**本任务由用户正式发出后，将已通过 R129 前瞻选择的统一 MS2 固定为下一论文版本的唯一 proposed method；不再重复“MS2是否值得进入确认”的选择轮。**继续使用原 H、表示、二站 support、有序供给、C_G、Gini 区间控制与数值政策。仅有的简化是所有输入一律不发出三站 support。历史完整 M-B、ENS-C 和停止的配置不改名、不覆盖。

本轮不调参、不运行PT，不重新生成评价输入；已有调参负结果保留。

本轮回答两个尚未由当前最终版本直接回答的问题：**(i) 相同、各自付费的完整 H 给到原 compact 后，MS2 的后端还有多大增量；(ii) 在已经自然发生多叶分裂的已知角色及另两个风险角色上，MS2 的外层控制包相对同表示、同有效根强化的单根求解是否有增量。**采用三题、两 Seed、四方法，共24正式臂。不是新算法搜索，不要求任何组件或对照必须获胜，不为结论增加输入、Seed、时长或参数。

长期目录约定：主入口 `E:\codes\ExactEBRP\`；所有新工作树、构建、raw、临时、稿件、归档、恢复对象位于 **`E:\codes\ExactEBRP-work\`**。复用适用稀疏 linked worktree 和共享对象库。PR交付后轻量筛查、安全清理，只处理本轮自有可恢复副本；保护唯一证据、失败记录、用户dirty、未推送内容和旧worktree，不自动迁移C/D盘。

## 1. 起点、版本迁移与不变范围

编写时核验 R129 / PR191：open、Draft、未合并；head分支 `codex/round129-uniform-pair-support-confirmation`，head `ce70acd2fb3fa6b7d0033f0cbc74c2aab3113d73`；科学提交 `aa033d57639453544343b4481ed301150b1de94c`。R128 base为 `cc70757304a2019d95f0f934aa5520d0caa946c6`。

原 E2 PE SHA256：`ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa`；Gurobi 13.0.2 DLL SHA256：`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。先核对实际远端、AGENTS.md、HEAD、活动进程、已有同轮产物、用户修改和E盘峰值空间。建议分支 `codex/round130-ms2-paper-attribution`，输出 `results/unified_exact_round130/`；不从main重复累计旧PR。

本轮文稿/manifest中的唯一方法可表述为 **GI-TBC (uniform pair-support implementation, MS2)**，表格短名 `S2`。它不是第三个新算法：算法身份就是 E2 的 `--round127-mode ms2`。旧 `--round127-mode mb` 是三站完整 M-B，标为 predecessor/full-MB，不把旧数字改贴成MS2。历史 ENS-C repository default不擅自更改；需要明确的论文复现入口，而不是无参数调用默认模式。

R129五项选择条件全部通过，是本轮的既成起点；不事后另加一批选择条件来否认或无限延迟它。真实正确性问题仍优先。R129的四新题和保护例保持原分层，正常开放与反转不得消失。选择一个方法不等于已经证明它在V50/V60全面更快。

授权：添加默认关闭的最小研究控制入口与必要桥接，构建并封存一个E3；更新论文唯一配置、证据版本清单和局部章节。**不优化/改写S2、H、模型基本表示、support预算/枚举、AM阈值、数值容差或默认原生参数。**E2保留原字节。原 S2/P 和旧 M-B/MD-R 行为不因新模式而改变。

## 2. 必须准确继承的正负结果

- R129执行30臂/10组/30个共享比较：四个新输入+一个保护例。每Seed新题P/MB/MS2认证数1/2/2；两Seed同时认证的问题数也是1/2/2。MS2相对MB在新UC-C20-U节省147.147和151.415秒；保护例两Seed证书保留。
- 新UC-B20-B的MB/MS2约4/3.6秒认证，P约317秒；但二者 H 的初始自身目标已经等于最后认证目标0.5773330699702928。这个“最终值已经由H取得”不意味着H自己已证明最优。两种方法各自然执行三次split，必须把发生分裂与分裂的净计算贡献分开。
- UC-C15-S与UC-B30-S两Seed三方法均开放。B30 Seed1的MS2 U/gap劣于MB，Seed0方向相反。不能把这些开放结果算认证Win或全域安全证明。
- R128合法MD-R与完整MB在两个认证角色只差不到1秒，三角色无split；那是旧三站版本/旧角色的控制证据，不是S2在新分裂角色的答案。
- R127的P-tuned合法选出q2，但留出P-tuned认证0/3而默认P1/3；保留，不重训、不逐例在default/tuned中挑赢家。
- R112–R115已有P-S同H控制和混合结论。它不是本轮首次提出。先读取必要小表、模型/Start契约与真实实现，复用已有路径，不恢复V100等历史大campaign，也不把旧构建/旧时钟时间作为本轮对照。

必要读取：R129 goal、candidate_decision、input_manifest、arms/pairs、mechanism_costs、actual differences及E2身份；R128 md_root_contract与源修正、原生资格和review；R125数学附录；R112–R115同H compact接口及少量对应source。只读所需文本/代码，不再遍历全历史。

## 3. 四个方法：单一主算法、三个固定研究对照

| ID | 物理模型与启动 | 静态模型与原生求解 | 本轮角色 |
|---|---|---|---|
| P | 原cold P-GRB，不运行H，无外来Start | 原compact、默认参数、一次完整MIP | 唯一主要benchmark |
| PS | 自付费完成与S2相同的H，提交自己产生的完整合法Start | **与P完全相同的原compact**，默认参数；不加S2行/域/线性cutoff | 同启动基线，沿用P-S含义 |
| S2 | 自付费完整H | 固定MS2：R、二站support、有序供给、C_G及原Gini控制 | 唯一论文方法 |
| S2R | 自付费相同H | **二站版本**的MD-R v1：包容完整根LP+根MIP，无外层控制 | 删除外层控制包的对照，不是新候选 |

PS不是PT，也不保证一定比P快。S2R不是R128仍带三站行的MD-R，不能直接复用旧MD-R时间或忘记删除其三站行。

每臂完整独立启动，不共享 H 车队、上界、Start、basis、搜索树或运行缓存。H_seed保持20260626；同问题/同Seed实际H动作、库存、容量归属车队必须核对，不能只比较一个目标值。H未按固定规则完成的运行仍报告真实方法结果，但不作纯同H归因。

### 3.1 PS：复用真正的同H original-compact路径

优先复用原 `round112_ens_start_compact` 和已有完整原compact Start mapper/validator。先核对实际入口和最终preset覆盖，不能只凭flag名称认定资格。允许最小身份/reader适配，不复制重写H或另做“类似H”的启发式。

PS在自己的完整计时内运行H，以原评价器取得合法U0，然后建立与P相同的原compact。完整核验映射至实际所有列、VType、界、行和原目标，提交并读回Start，正常求解。原正当startup-zero行为沿已验证实现，明确后端未曝光；不添加新的零目标捷径，也不人为压制已有合法证书。正常非零路径只有原compact的一次MIP；不得加S2根LP、目标cutoff行、域收紧、A/B、support或Gini区间。

在第一次Optimize前，P/PS矩阵、目标、变量类型、全部界、参数必须一致（允许日志路径/名称和Start属性不同）。H时间、Start映射/验证/提交时间都计入PS的T_produce。P没有免费得到PS的解；PS不使用S2产生的H文件或已知最优值。

Start提交/读回并不自动保证它成为新的原生incumbent。保存原生日志与实际状态；若原生已找到同样好或更好解而未新增incumbent，应如实解释，不把那条日志单独判成Start非法。若映射不可行、被真实约束拒绝或不得不用另一种部分Start才可运行，先定位并报告，不能静默改变合同或放松容差。绝不以固定变量/求一个IIS后得到的解免费替换正式H。

### 3.2 S2R：沿用R128包容根语义，但只保留二站support

非零时，自己的完整H给出U0，建立固定根
\[
I_0=[0,\min\{U_0,(n-1)/n\}],\qquad F_{model}\le U_0.
\]
保留S2的全部合法根域、二站support、有序供给、C_G、A/B和惩罚下界行。只抑制带明确语义的 `interval_no_improver_domain_closure` 伪不可行行，不能关整个penalty模块，也不能按行号删常数行。

沿R128 MD-R v1：先对实际原整数类型根作自己的全Start校验；一次完整根LP；恢复真实整数类型；一次完整根MIP并提交合法自己的Start；同一全程deadline。不child LP、不NEXT/AM、不目标事件重启、不split、不epoch重建，也不返回S2接着求。保留原已声明startup-zero范围，非零链不能被相关性容差跳过。

必须保留R128已经通过的细节：预LP核验实际付费并扣减native allowance；非零链具有真实根LP+根MIP和一次submitted Start；TIME_LIMIT/INTERRUPTED保持实际返回语义，不被数值相关性判据改称native OPTIMAL；LP/MIP INFEASIBLE却已有合法等U0根见证时是矛盾，不是认证捷径。沿现有MD-R资格政策形成数值证书，保留raw signed gap，不改成新的更宽标准。

只针对S2R修订最小模式组合。当前 `round127().mode` 是共享变量，连续传入互相覆盖的旧flag不能构成合法组合。建议用一个唯一 `s2-root` 研究模式，使三站发射predicate为false、inclusive-root predicate为true，其余S2配置保持；具体argv必须由最终解析值与实际矩阵验证。不能在S2中也抑制伪行，或误令普通MD-R失去其原三站定义。

### 3.3 有效性与归因边界

对真实物理解，非负惩罚使G<=F；非负比率满足G<=(n-1)/n。因此F<=U0的物理解位于该根。cutoff之外F>U0，不可能改善本臂已验证U0。若根内合格原生下界为L，补集覆盖给出全局下界min(L,U0)；它不是掩盖L>合法自身见证的裁剪。实际见证矛盾优先检查。

原解析区域下界L_a与cutoff关系仍分开：L_a>c排除F<=c，L_a=c只排除严格改进，c−1e−9<=L_a<c不能宣称精确无改善。只有实际原S2根不含伪行、其它所有根数据和H相同，S2/S2R才是纯外层包对照；存在额外语义差异则保留完整方法结果并收缩归因。

即使发生split，本对照的处理变量仍是**全部外层控制包**（探测、target交接、域/强化随区间变化、调度与split），不是单独一个二分公式。两个Seed是有限路径观察，不保证总体稳健性。

## 4. 最小实现、资格与冻结E3

新增控制默认关闭；S2/P主实现复用原代码，不改变其排序、行发射、数值、H和控制。所有24臂使用一个封存E3及原DLL，同编译器与构建设置。E2保留原字节；E3不冒称与E2二进制相同。

资格先做无Optimize检查，有限native smoke使用已有训练/人工资格输入，不试跑正式角色来决定方法或参数：
1. E2/E3的默认S2/P在一个小例和一个中例上比较完整模型、目标、列类型/界、参数与H配置；不得只比较Fingerprint。包含文件名/输出目录不同但数学身份不变的检查。
2. S2R与S2根的差集只能是有语义标识的伪行（有则披露）；三站均为0，二站/有序供给/C_G等均保留。核对共享工厂与fallback，不因新mode漏掉任一处。实际正式自身根之后再核查。
3. P/PS完整原compact同模型；PS完整H/Start逐列映射，原生Start属性读回；P为真正冷启动且没有加载旧解。两者均不得带项目cutoff或新行。
4. 复用R128等cutoff、S=0、tiny-positive-U0、正常开放返回资格；本轮只对新增“二站＋单根”组合做有限必要差集与一条真实非零两call链，不重跑整套历史边界。
5. 对PS复用已有资格，补一个完整自付费H→映射→原compact MIP链，检查两种车队容量、空车辆表示和带载返回的已有见证；不得以一条“Start accepted”代替完整物理和矩阵核验。
6. 更新reader只添加准确的新mode身份/明示证据条件。保留旧Seed0硬编码raw字段与后验source/return/cover含义的区分，不为显示PASS改写raw，不改变三时钟起点。PS/S2R必要契约不成立就阻塞相应模式，继续独立有用工作，不能替换为另一个算法。

前置审查重点是S2R的合法包容根和PS同模型/同H，不新建通用消融平台。资格通过后一次冻结E3源码、PE/DLL、protocol与全表；正常正式正负结果出现后不得再改算法/参数。原S2桥接失败先停止，不把改进实现混称冻结MS2。

## 5. 输入与完整运行表

全部复用R129原字节。它们现在是已知机制诊断角色，**不是新的前瞻选择或独立新验证集**；也不是从未看过其难度的盲抽样。三角色包括实际split、非零认证与开放风险，均不换样。

| id | 源路径 | SHA256 | V/M | Q_vector | 物理T秒 | 完整cap秒 |
|---|---|---|---|---|---:|---:|
| UC-B20-B | results/unified_exact_round129/inputs/UC-B20-B.txt | be549149049a41aab0374aa0872ca7bc6f290f3b4ccc18b6f4aae75754d1217b | 20/2 | [20,40] | 7200 | 1200 |
| UC-C20-U | results/unified_exact_round129/inputs/UC-C20-U.txt | e4de3620f2eba0c9c91a18fddbc5db26700914c280e614c37d3c159417f61df5 | 20/2 | [30,30] | 7200 | 1200 |
| UC-B30-S | results/unified_exact_round129/inputs/UC-B30-S.txt | e8ed0a8859b6704ee167e356e740dddd5804112167209403734bb032d5b7e1b0 | 30/3 | [25,25,25] | 7200 | 1200 |

前两题分别balanced、surplus，第三题shortage，均沿原总量scenario定义，不能改写为每站都处在同一库存区间。不改坐标、权重、T/Q或旅行规则。

| 组 | id | Seed | 方法顺序 | 每臂cap秒 | 臂数 | 名义秒 |
|---:|---|---:|---|---:|---:|---:|
| 1 | UC-B20-B | 0 | P → PS → S2 → S2R | 1200 | 4 | 4800 |
| 2 | UC-B20-B | 1 | S2R → S2 → PS → P | 1200 | 4 | 4800 |
| 3 | UC-C20-U | 0 | PS → S2R → P → S2 | 1200 | 4 | 4800 |
| 4 | UC-C20-U | 1 | S2 → P → S2R → PS | 1200 | 4 | 4800 |
| 5 | UC-B30-S | 0 | S2 → P → S2R → PS | 1200 | 4 | 4800 |
| 6 | UC-B30-S | 1 | PS → S2R → P → S2 | 1200 | 4 | 4800 |

共24臂、3题、6匹配组、28800秒正式名义窗口。同角色两个Seed顺序反转，不宣称消除全部负载噪声。两Seed各一次，不best-of-seed。编译、压缩、重型审查不与正式串行性能竞争资源。

每组预定主要对比5项：**S2/P、PS/P、S2/PS、S2/S2R、S2R/PS**，共30个有类型对比。其他成对差值可标探索性列出，但不能改写事前问题。共享方法与输入不构成30个独立试验。全部E3方法新跑自身流程；不借R129的E2 P/S2时间填表。

## 6. 不变预算、参数与证据

lambda=.15，取/卸各60秒，H_seed=20260626，Threads=MIPThreads=1，原CPU亲和性、PresolveAuto、MIPFocus=0、原生Cuts=-1，请求MIPGap=MIPGapAbs=0及原FeasibilityTol/IntFeasTol/OptimalityTol。Gurobi Seed统一按表传递，不逐call重新抽取。不得把同Seed误写成不同表示经历相同原生路径。

完整cap涵盖输入/身份准入、H、模型生成、根LP（适用时）、MIP、Start检查/提交、在线验证和规定输出；各call只能使用剩余全程deadline。保留30秒shutdown reserve、6秒native偏移、2秒hard-stop偏移。PS不获赠H预算，S2R也不因为少call而获得多一段时间。

T_produce、T_verify、T_total原口径不变；最终资格成立才T_cert=T_produce。未知T_cert为null，不补cap、不按剩余gap预测最终时间。后验不得搜索新解/新界替一个臂补证书；跨臂物理解仅可用于撤销真正矛盾，不给另一方法免费UB。

核查完整source/return/coverage、参数、物理、正常退出和签名gap。原顶层元数据与合格endpoint不同可沿已有明示规则解释，不能只读一个raw布尔值决定证书，也不能无来源把它升级。实际call含伪闭合时必须绑定适用域/解析前提和数值政策；不得单凭含0<=−1模型的INFEASIBLE声称包容域真实不可行。保留真实negative signed gaps与影响记录，不裁剪LB隐藏冲突。

## 7. 因果解释：三个层次不能混淆

| 对照 | 能检验什么 | 不应宣称什么 |
|---|---|---|
| S2/P | 唯一完整方法相对cold compact | 所有收益全来自cuts或D |
| PS/P | 自付费完整H＋合法Start集成的净效果 | 一个免费的oracle最优解的作用 |
| S2/PS | 同H起点后的完整后端/表示/控制包增量 | 单独每个cut或AM阈值的贡献 |
| S2/S2R | 同H、同有效初始根下外层控制包的作用 | 仅凭split次数就证明分裂更快 |
| S2R/PS | 同H单根强化表示与原compact的差异 | 无混杂的“纯cuts”效果：表示、LP预处理、cutoff域仍有差别 |

每角色记录H完整性、同动作/车队/初始U、真实初始域和矩阵差集，native Start实际提交/读回、建模与映射时间、已有LP/MIP时间/Work/节点、call种类、split/target/闭合来源、首次已有日志中最终自身U见证的时刻。利用原日志，不额外跑诊断LP去填表；缺失为unknown。不同方法Work是解释指标，不改成WorkLimit。

对UC-B20-B先从R129已有日志制作一页实际coverage示例：原root、三次自然split、被关闭侧的真实来源及最终terminal，明确H先有目标0.577333…但尚未证明。**不得把这份旧证明/已知最优解注入正式臂**。新实验自己的split或证书未重复也保留，不能强制分裂或替换角色。

如果所有同H方法在B20都很快，说明cold-P优势不能全部归D；如果只有S2快且root对照显著慢，才有该有限角色上的外层包增量；如果PS在某题赢，原结果必须保留，不把PS删掉或改prm。没有结论时用“本面板尚无直接归因”，不继续改变对照直到它输。

## 8. 评价、阶段出口与唯一方法

主方向继续为：双方认证按未舍入T_cert比较，快Win、慢Lose、相等Tie；仅一侧认证按证书判Win/Lose；双方开放UNDETERMINED；证据不合格UNEVALUABLE。仅双方认证计算比率及明确交集统计，不用cap替代求证时间。开放U/L/gap作补充，不能成为认证Win。

方向与幅度分开。解释性“实质双侧差异”采用 `慢者−快者 >= max(10秒,0.10*快者)`，对两侧对称，另保留全部实际秒差；这不是统计检验、算法开关或新增主benchmark准入。单侧证书变化单独报告，不以时间门槛免除。现有tiny10秒检查保持历史身份，不重跑tiny。

执行COMPLETE/PARTIAL/BLOCKED与科学判断分开。真实来源/模型问题优先于速度，必要位置缺项不能称完整消融；正常Lose、开放或无split不叫工程失败。

完整有效数据下，输出一份简明 `claim_decision.md`，对三轴分别判定：
1. **版本**：论文唯一方法已明确映射为S2/MS2，旧MB数字没有重新贴标；没有改库默认。
2. **同H后端证据**：S2/PS在两个Seed分别有直接增量、混合/反向、接近，还是未定；P仍为主benchmark，PS有价值不要求逐例支配。
3. **外层控制证据**：在实际same-root条件与真实split/target曝光下，是有重复净增量、仅控制成本/混合，还是未定。没有split的角色不能证明多叶提速。

科学总标签选一个，并说明为何：
- `SELECTED_MS2_WITH_DIRECT_BACKEND_AND_CONTROL_EVIDENCE`：同H后端和已曝光外层包各自至少有一个角色在两Seed均出现单侧证书优势或实质双侧时间收益；仍逐项保留反向结果，不声称全域支配。
- `SELECTED_MS2_WITH_SCOPED_OR_MIXED_ATTRIBUTION`：完整方法有既有支持，但某个对照接近、未定、混合或反向；据此收缩主文组件主张，正常收口。
- `REFERENCE_CONTROL_EXPOSES_CORE_CLAIM_GAP`：PS或S2R在同一角色两Seed均有反向单侧证书或实质反向时间优势，且当前待写的核心主张必须因此实质调整；不自动换算法、不拼赢家，提出一个最小、尚未执行的决定点。
- `PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION`：实质数学/证据/身份问题，定位受影响范围，保留正确部分。

优先级：证明/身份问题→必要缺项→可观察的重复反向核心主张缺口→有正面双轴支持→混合/有限归因。总标签并不回溯改写R129候选通过，也不为一次普通的参考方法Win撤销全部M-B/MS2研究。若问题仅是论文曾过强，能用准确范围修正，就先修正文，不自动立项新优化。

本轮完成后结束这些固定对照；不再新增Seed2、H删除、C_G细拆、支持行选择器、S2R作为新候选、更多tuning或V50长窗。是否需要另一项研究由实际缺口决定，而非预先保证每个组件都有正面贡献。

## 9. 预算与恢复弹性

| 项目 | 名义秒/上限 |
|---|---:|
| 三题×两Seed×四方法 | 28800 |
| 研究构建、增量资格及额外诊断弹性上限 | 3600 |
| 六组管理参考 | 720 |
| 最大计划 | 33120 |
| **全轮外层计费总上限** | **39600** |

正式名义8小时，总上限11小时，是机器费用预算，不是等待时间承诺。资格软计划1800秒，有必要可在总预算内扩至3600秒并记录原因，不设机械进程次数硬闸；余6480秒用于必要后验、有限文稿更新、一次恢复和排错，不是备用实验额度。

先检查reader和小型源身份再开始正式；不重做R127全部训练/各轮大carrier。构建/导出有限迭代保留失败，但不因工具成功后略超一个软预估而强制重跑。正式串行，全程记录实际父子进程和非重叠外层费用，H/LP/MIP嵌套秒不重复加。

会话中断先检查PID/出生时刻/argv/seal，健康进程继续，已封存数据优先只读恢复。真实外部失败而无可靠产出时，仅在预算能覆盖剩余完整义务且事前记录的前提下，允许最多一次同角色/Seed的完整四方法组恢复；不只重跑输的一侧。正常慢、Lose、开放不可重试。不能预支未来可能提前认证的节省。

## 10. 论文版本与证据迁移：不要求全历史重跑

交付 `paper_version_manifest.json` 与紧凑 `evidence_migration.csv`，明确每个结果的真实算法配置、程序/数值/时钟、输入、Seed和开发/确认/保护/诊断身份。

- 新正文唯一proposed method为GI-TBC的MS2实现，support定义为仅二站；一般三站有效性及旧实验放在发展/消融背景，不从理论附录删除，也不写成当前仍启用。
- 直接主方法性能只使用实际MS2的合格观察；R127/R128的MS2是开发层，R129四题是选择时的前瞻层，保护例独立，本轮三题是已知角色的归因诊断。两个Seed不增加问题数。
- 旧M-B/ENS在R122、R123、R126等的表现保留为前代/背景，不能改名MS2。V35/V50旧结果不证明新主方法在同范围已经验证；不足之处写清，不为填满表而重跑全部历史。
- R127 C_G/MR消融属于三站旧表示下的组件证据，不强行移植为最终S2的单组件性能定理。本轮不做这两组新消融，数学有效性仍可论证。
- P-S已有历史混合结果、PT有限筛选失败、R128的时间反转以及R129所有开放/端点反向保留。不能用新稿只展示优势子集。
- 文稿精简修改方法版本、结果层次、同启动/控制节及贡献矩阵，保留R125完整公式、cuts推导、H和controller附录。更新实际PDF并检查受影响页，不再重排整本或增加重复渲染体系。

## 11. 两次有内容的复核、交付与PR

正式前由另一执行者尽可能核对：唯一模式不会互相覆盖、PS同P数学模型且自付费H、S2R二站包容根与真实Start/返回合同、E2/E3桥接和运行预算。没有独立执行者明确另一步作者自审，不伪称第三方。

交付前复算全部30项比较与分母，抽查至少一个真实PS完整Start/原compact同一性、一个S2R完整两call证据、一个实际分裂的S2完整覆盖（若未出现则标未曝光，不能制造），并独立回放一个非空最终车队。仅报告实际做过的范围，不把哈希/源码命中计数当作完整正确性证明。

有限交付：goal、版本manifest/迁移表、method_matrix、E3与源身份、增量资格、冻结argv/input表、完整arms/pairs、same-H/root/Start及曝光/成本摘要、claim_decision、final_report/review_actions、费用/RESUME、必要raw/模型/Start/界的紧凑索引、现有完整稿与PDF。没有必要再建设全仓库审计平台。

英文stacked Draft PR建议标题：
`Round130: establish the uniform pair-support paper version and isolate same-start and outer-control effects`

基于实际R129研究分支，不merge、不强推、不向main重复累计历史，不代发导师邮件或投稿。核对远端base/head与可读内容。实际库默认和旧命令仍保留；论文入口明确，不把采用论文配置等同于修改全局默认。

## 12. 安全与收尾

所有新增资产在E盘工作根；复用同一对象库/稀疏工作树，先估算raw＋压缩＋恢复峰值，不复制整仓、旧build或多个全量恢复根。按每命令禁用无关Git自动维护，不改全局配置、不gc/prune/repack。

发布扫描实际文本和载体，排除key/Cookie、许可证、PE/DLL、字体和无权全文。科学内容封存后一次必要公开空根恢复，只取本轮与准确依赖，不重求解、不恢复全部历史；失败在同一根限定修复，保存事实，不为后续回执递归重新打包恢复。

远端可读、必要核验完成且进程退出后轻量清理本轮自有重复ZIP、恢复展开、可重建页图和字节相同临时PDF；删除范围外先有可靠保留和恢复依据。保护唯一证据、不同内容稿件、失败记录、用户dirty、未推送内容和旧worktree；不强制删除。只报告实际量测的空间数据。

**阶段目标：接受已经取得的统一简化选择，明确一个论文方法；用同H compact和真正可比的二站单根控制，补足当前最影响贡献解释的两项证据；得到能结束的正面或混合归因，而不是再重复候选确认或增加算法数量。**

### 执行时核对的主要一手资料

R129/PR191的完整记录；R128包容根合同与修正；R112–R115同H compact实际实现和既有证据。官方接口按本地Gurobi13.0.2核对，不照搬更新版本行为：
- https://docs.gurobi.com/projects/optimizer/en/13.0/reference/attributes/variable.html （Start）
- https://support.gurobi.com/hc/en-us/articles/360043834831-How-do-I-use-MIP-starts
- https://support.gurobi.com/hc/en-us/articles/15185996954897-What-does-User-MIP-start-did-not-produce-a-new-incumbent-solution-mean
- https://docs.gurobi.com/projects/optimizer/en/13.0/reference/numericcodes/statuscodes.html
- https://docs.gurobi.com/projects/optimizer/en/13.0/reference/attributes/model.html （Work）
