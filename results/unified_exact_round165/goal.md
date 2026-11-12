/goal

# Round165：完成当前论文评审稿，核实核心贡献与机制归因

## 0. 本轮目标与执行原则

继承已完成的 R164。**本轮把截至 R164 的数学、算法和实验研究整理为一份可以完整阅读、核对和交给作者讨论的当前英文论文稿，并具体回答：这项研究已经建立了什么可推广的结构认识，完整方法的竞争力由哪些证据支持，哪些机制的独立收益仍未建立？**

实际交付维护中的正文、完整模型与算法附录、补充材料、参考文献、重新组装的 manuscript.md 和可阅读的当前 PDF，以及一份简明的贡献定位与作者决策备忘录。需要直接改好论文；只交“投稿准备报告”、目录、修改建议或一份未与正文同步的新稿，不算完成。

这是 R134/R135/R137 已有论文工作的实质更新。R138–164 的结构研究和确认结果已经陆续写入组件 Markdown，但现有组装稿和 PDF 仍是 2026-10-28 的历史快照；旧组装脚本还会重新生成早期内容。本轮解决当前版本的一致性和科学叙事问题，**不假设现有算法说明、证明或机制归因尚未编写**。已有正确的推导直接复用，只修真实问题。

本轮继续面向 OR 级研究质量：精确的原创性定位、可检查的论证、统一的方法、完整且有解释力的比较。论文稿完成不等于已达到某期刊录用标准；也不预设必须更换期刊、发明新定理或再跑一个有利结果才能交付。给出基于内容的判断。

本轮 **新增 Optimize/正式性能实验预算为 0**。不追加 Seed、配置、root-only 面板、E+ 面板、C35/R96 求解或新算法微变体；不重新编译生产核心。不因还有预算而重跑健康历史实验。允许已有数据的离线重算、必要的数学小例核查、文献阅读、表图生成、文稿组装与 PDF QA。主动工作目标 2–4h，有限工作包容量上限 6h=21600s，含研究、离线计算、稿件整理和终审；普通 Git/传输 I/O 单列。记录实际工作窗口，平行审阅按共同外层窗口计一次，不把多个代理时长相加，也不等待用满预算。若存在真实环境阻塞，保留已完成稿与明确未完成项，不伪造成功。

**正式生产方法与反复执行的算法核心继续为 C++。** Python/Node 可用于编排、读取历史结果、离线核验、图表和文档；这些处理不产生新的算法性能样本，不把 Python 分析时间与历史 C++ 求解时间混比。不得通过 gurobipy、命令行求解器或其他接口偷偷新增求解。算法定义对合法输入一致，实例名、来源、历史胜负、硬件型号/速度不进入在线策略；本轮不修改冻结算法与 main 默认。

## A. 本地入口、版本与 PR 依赖

遵守仓库 AGENTS.md、WORKSPACE_POLICY 和现有工作区约定。入口为 `E:\codes\ExactEBRP-work\worktrees\paper-current`；新增工作、临时文件、缓存和交付均在 `E:\codes\ExactEBRP-work` 内。保护原 `E:\codes\ExactEBRP`、用户未提交修改、已有证据与活动 worktree。先读取 git 状态和已有同轮产物，有同轮工作则接续去重。

开始时读取远端真实状态。以下是任务编写时的已核实身份，不是要求忽略后续合法更新：

| 身份 | 固定值 |
|---|---|
| 仓库 | `yifanXovo/TailoredExact` |
| 前序 | [R164 / PR #226](https://github.com/yifanXovo/TailoredExact/pull/226)，Open Draft、未合并 |
| R164 branch | `codex/round164-seed-confirmation` |
| R164 delivery | `de01e8fb27a954d031abac5fe99442d6c8d29d44` |
| R164 science/carrier | `a29a70d132ecc17e18bc48a660225a6380722f45` |
| R164 数值结果快照 | `b93a8a01ff1b7f3cbee67807be3ac6591db4767f` |
| R163 delivery | `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb` |
| main | `b2b940c1e517a72e226ec60fc49ff19651737632` |
| 已实测 C++ 源 | `e920b92e199e825ec89a2932f701861ff158e0d4` |
| 生产 PE SHA256 | `fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93` |
| Gurobi 13.0.2 DLL SHA256 | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |

若 main 已包含必要依赖，从 main 开始；否则基于核实后的 R164 head 建立 `codex/round165-current-manuscript`，Draft PR base 使用 R164 branch，无需等待前序合并。本轮稿件的源提交、文档生成身份和历史实测身份分别记录；文稿更新不能改写哪个 C++ 版本实际产生了历史结果。

在 `results/unified_exact_round165/` 记录 goal、简明 source manifest、阶段决定和审阅结果。继续以 `results/unified_exact_round137/` 中的既有论文组件作为维护入口；在同处更新派生组装稿/PDF，Git 历史保留旧快照。若已有更明确的仓库维护入口，依据实际约定使用并说明映射，最终只有一套当前权威稿，不并行维护互相冲突的 R137/R165 正文。

## B. 有限历史排重与本轮增量

先读 `docs/current_mainline.md`、R164 goal/final_report/decision/research_navigation、当前 R137 论文组件，以及 R134/R135/R137 的论文组装与贡献定位记录。旧优化方向按下面问题回读相应 final_report/实现，使用固定 commit 与必要 member，不做全仓库无差别重放。

| 已有工作 | 已得到的认识 | 本轮实际使用方式 |
|---|---|---|
| R125、R134、R135 | 近邻文献、完整模型、证明和论文组织已有实质工作 | 继承已读出处；只补影响当前贡献的具体差异，不重做泛泛综述 |
| R137 | 完整英文正文、附录 A/B、完整计算设计、PS、AM 和机制对照 | 是当前稿基础；附录已有 ProcessLeaf/FinalizeCover、plateau/NEXT/AM、H 定义，不从零重写 |
| R137 full/root 与行删除 | 已明确有限角色下 full-over-root 无实质证书时间优势；较难角色 root-only 的最终 L 略高，部分行删除时间排序随 Seed 反转 | 在论证结构中保留；完整 B/P 优势与组件增益分别表述，不新增面板寻找归因胜例 |
| R138–156 | 状态、聚合、库存和 proof-only 方向有真实数学信息及有限正负效果 | 提炼“表示/下界/完整算法价值”的差别；保留 E+ 的真实增益和成本，不逐轮堆正文 |
| R157–162 | 整数资源、物理实现、固定结构、连续 Q 等方向已检查；未给出可推广的完整性能改进 | 保留可证实的结构结论；不把同一模型换输入、上限、接口或命名重新立项 |
| R62、R96、R97、R160 | primal archive、完整固定归属/顺序数量优化、原生路线反馈与物理邻域已有研究 | C35 的只读路线差异不能自动重开这些方向 |
| R163–164 | 冻结主线的新 cohort 确认、两追加 Seed 与有边界的 E+ 结果已完成 | 整合为当前完整稿，关闭常规补 Seed 循环 |

本轮最重要的增量是：把论文的核心问题、理论作用、比较设计、完整结果与结构解释连成一篇当前研究论文，形成能直接讨论贡献是否足够的成稿。旧稿本来已披露机制归因边界；不能把“发现该边界”冒充本轮新发现。

## C. 核心贡献、理论与近邻工作的具体定位

### C1. 先做一张小型贡献—证据映射，再直接改论文

用一份简明表逐项绑定：主张、数学对象/前提、最接近的既有工作、本项目具体差别、支持的定理/实现/实验证据，以及必要的范围。至少覆盖：

1. 同一有限库存状态同时联系 objective 产品、站点服务、移动数量和访问的表示；独立 VD-P 产品块与带物理链接后的模型必须区分。
2. unique nonzero one-way service 与整数最终库存带来的隐式服务整数性；这是条件明确的模型性质，不能扩大为任意 BRP 的结论。
3. 有序供给兼容、support/handling 和相关有效不等式：哪些是标准工具的应用，哪些利用本问题的特殊结构；各自的有效域和实际启用方式。
4. 以 true Gini 划分覆盖、有效 cutoff 与外层下界汇总构成的完整方法；正确性论证与性能机制归因分别建立。
5. proof-only 库存信息与物理路线实现之间的差异，以及 R163/R164 实际支持的完整方法竞争力。

“基本工具已有”不能自动推出“整个方法没有研究贡献”；反过来，把若干已有工具组合在一起、得到几个较好时间，也不能自动宣称一般性方法突破。以确切对象、连接和证据判断。

论文的首要性能主张应与现有证据一致：集成方法相对规定 compact controls 的有限认证/端点优势。GI 外层的完整覆盖是正确性作用；已有消融不足以把完整优势单独归因于外层调度。不要通过换名字、删不利对照或合并分母绕过这个问题。

### C2. 复核现成论证，只补真实缺口

优先复用当前正文和附录的 Lemma/Proposition 及已完成推导。检查符号、假设、结论、实现和实验版本是否一致；不设“新增定理数”配额，不为了本轮显得创新而重证已有基本结论。

重点读回以下容易在重组中写错的边界：

- 原物理问题：空载出发、可载货返回、返回卸货计时、唯一非零单向服务、每个 prefix 的车辆容量；`Q` 不是累计 pickup 上限。
- 原目标 `F=G+lambda*P`；depot 不入 Gini，`S=0` 约定、`D_i>0`、正权/正 lambda 的使用条件；零 Gini 不等于满足 target。
- shared-state 连接与整数服务的条件；独立单乘积块的投影不能冒充整个路线模型的凸包。不要删除已存在的“单独 VD-P 与 McCormick 矩形投影相同”解释。
- 物理 true Gini 与 native 辅助 g 的区别；有些辅助补全可以 inflated-g，但每个合法物理点应有其 true-G 区域内的保目标嵌入。
- inclusive cutoff、补域下界、完整 split、下界来源资格与被否定来源的实际依赖处理、独立 exact-zero floor、有限 tolerance 与 OPEN 的区分。区分冻结实现与理想论证，不为本轮补造未实现的通用 revocation 机制。
- 深度/宽度 guard 只是限制额外划分，完整方法如何保留 exact continuation；已有数值资格不是符号精确有理证明。
- E+ 的 full-domain proof 合法性及其 own-H/代价边界；只读库存目标或不可实现路线不是可行 U。

如有真实推导错误，修正受影响命题、图表和结论；若牵涉历史数值资格，明确指出受影响的证据范围，不悄悄改代码或重跑。一般文字/链接修复只需对应读回。可使用确定性的手算或离线小例帮助解释，不能将例子伪装成一般证明或新增性能实验。

保留 GI-TBC 名称。清楚说明实际自定义有效行在 canonical interval 模型构建时静态加入、Gurobi 内部使用其 Native branch-and-cut、外层执行 Gini 区间控制；不要把本项目写成已有动态 callback 分离器。本轮不为名称重构算法。

### C3. 聚焦近邻，复用文献核验

先用已有 `references.bib` 与 source-access notes，按 C1 的具体主张读取必要原文段落；不要求重新检索每一篇 BRP 文献或积累引用数量。技术结论只依赖原论文、作者稿或官方文档。区分正式发表版、作者稿、摘要与未获取全文。

主要数学近邻包括 Gupte et al. (2013, DOI `10.1137/110836183`)、Köppe et al. (2008, `10.1016/j.disopt.2006.12.003`)、McCormick 及现有凸性/epigraph 来源；主要 BRP 近邻沿用现稿已经核查的 Erdoğan、Schuijbroek、Bruck、Bulhões、Ikonen 等。比较的是本问题中的具体连接与假设，不把 binary expansion、value disjunction、空间划分或 Jensen 当成首次发明。

对两篇已在 bib、但原文定义核查仍有限的 2026 近邻，做有终点的定向核查：

- Qiao et al., “A fairness-aware coordinated two-echelon static rebalancing approach for large-scale bike-sharing systems”, DOI `10.1016/j.tre.2026.104984`。公开内容强调 task-duration fairness、两级协调；逐项分清 equity 对象与操作域。
- Caggiani et al., “An equity-based static relocation and battery swapping optimisation model for free-floating micromobility sharing systems”, DOI `10.1016/j.trc.2026.105691`。官方机构库 [record](https://research.unipd.it/handle/11577/3596099) 已列公开 VoR；[PDF](https://research.unipd.it/retrieve/1ca1c54a-9e2b-4b68-91b7-612ed0aa2942/1-s2.0-S0968090X26001798-main.pdf)。若可获取，重点读模型/公平指标/优化变量与比较方法，不需要整篇逐字综述。

对于新核查，用一个紧凑表记录 equity 定义、库存/服务/车辆约定、目标与决策变量、方法、与本题关系、具体读到的页节。仅凭摘要可说明摘要明确陈述的差异，不能据此证明模型等价、严格不等价、支配或“首次”。编写本任务时该 Caggiani PDF 的 web 读取因文件过大失败、公开直链下载遇到 HTTP403；这是实际访问状态，不是已读全文或付费墙判断。本地有可用合法入口即读取；否则记录一次结果并继续完成文稿，不反复换代理、证书或全局配置。

同问题 HGA-TGBC 前稿的模型/启发式来源须保留归属。使用实际可见的作者提供版本；旧记录的 `Research/docs/Paper Draft 2.docx` 不能未经核实被称为最新版本。缺失作者、发表状态或 DOI 不要编造，必要确认项放内部作者备忘录，不让这些行政未知阻塞技术稿，也不公开私有原稿。

## D. 当前论文的具体改写

### D1. 正文以研究问题组织

在现有稿上完成连贯改写，建议保持“引言与贡献—模型—表示与算法—实验设计—完整方法结果—机制与结构解释—结论”的主线。可调整小节顺序和标题，不为重排而重排，不设机械页数配额。

摘要用一段连贯叙述说明问题、主要方法思想和最重要的结果/边界。正文优先使用清楚的数学和算法语言。研究轮次、分支、hash、每次审计流程及历史执行问题放 source map/补充材料；正文保留理解结果所必需的版本、样本设计和计时政策。

从现有完整 Appendix B 抽取易读的主算法视图，给出输入/输出、共享状态、区域选择、处理/分裂/延续、有效上下界与终止的关系，再引用附录中的精确规则。不要删除附录 B.0–B.11 的真实逻辑，不把主算法写成只有“按既定规则求解”的空壳，也不把全部 CLI 和审计细节塞进主文。

正文明确 B、P、PS、E+ 的用途及哪些研究实际测过它们。E+ 保留为单独命名的有限 proof 扩展，不能在主算法中默认开启，也不能形成按实例择优的 B/E+ portfolio。

数值资格、研究范围和限制集中在适合的位置说明；摘要、每个表后、每段结论不反复堆相同防御性否定。用肯定而准确的句子讲清已经证明、已经观察到什么，同时完整保留不利结果。

### D2. 现有证据分层呈现，不重新造一个“大总样本”

使用现有合格机器可读结果生成表和必要图；展示舍入与底层全精度分离。固定同版本、输入、目标、cap、Seed、方法的身份，保留实际共用 default 的引用，不重复计数。

正文与补充材料至少覆盖下列科学问题，旧大表可放补充并提供精确入口：

| 问题 | 所需内容 |
|---|---|
| 主线完整方法竞争力 | R137 breadth：B 9/12、P 7/12、PS 7/12；resource pairs：B 4/8、P/PS 0/8。按各自原合同保留历史 R132/R134 结果，不合并成共同胜率 |
| primal / proof / 证书成本 | U/L 分开；time ratio 只在双方合格 CERT 的交集；OPEN 不以 cap 当收敛时间，native Runtime 不代替完整 paid lifecycle |
| 真实物理资源和目标权重 | 复用 R137 T-pair、rho/weight 与 physical operation 证据；有限预算端点和 runtime 无须随 T 单调，不能把 synthetic targets 说成实测需求 |
| 机制归因 | 原 full/root、AB/CR/CG 删除和 AM 结果，保留 Seed 反转和 root-only 的不利对照；完整方法收益不拆成未经识别的组件贡献比例 |
| proof-only 增强 | R163 E+/B：U 六例相同，仅 X35 最终 L 从 .3949882559151472 提高到 .42319954961578576；没有新增证书。三个共同 CERT 中仅 C20 约26.10s增加达到既有实质差异尺度 |
| 新 cohort 及 Seed | R163 Seed0 与 R164 Seeds1/2：六配置，每 Seed B 3/6、P 1/6；全部 n35 OPEN；B35/X35 三 Seed 均 B U 更小、L 更大；C35 primal 排序反转而 B 的 L 优势保持 |
| 已知可行目标复现 | 使用已经预冻结的 u_ref 与到达区间/删失记录；它是离线共同标准，不是精确首次找到时间、生产 cutoff 或方法间赠送的 Start |
| 结构认知 | 库存信息变强与物理可实现/完整成本的关系，使用 R138–164 已完成证据；保留正结果及反例，不用研究轮数代替理论与机制解释 |

R163/R164 合计为六配置内的三 Seed 重复、18个 B/P 配对、36个 method observations；其中本轮前序 R164 新增24臂。不是18个独立输入，不据此作总体成功率或稳定 runtime 分布推断。R163 的6个 E+ 观测单列，不把 B/P 的新 Seed 用作 E+ 稳健性证据。

C35 必须同时保留两个事实：Seed1/2 的 B U 优于对应 P，但历史 P Seed0 的 `.09331934374779818` 仍优于三个 B U（`.12956638965196035/.10742986645444105/.10808393649972804`）。新 Seed 的相对排序改善不能写成已消除该 primal 缺口。X35 新 Seed 对历史 u_ref 的未达状态也应保留。使用原 `primal_target_arrival` 数据，不重新挑一个有利目标。

适度制作帮助解释的图，例如按配置分组的三 Seed U/L 端点、理论/实现/证据关系图，或一张复用物理资源信息的图。优先复用当前图表；不要求为每轮或每个指标新增可视化。图必须来自绑定数据，明确 certified/open、历史/新增及条件分母。

### D3. 消除当前文档冲突

实际搜索当前维护材料并修复：

- supplement 中仍指向“single Round163 next question”的过期导航与失效 `paper_body.md#71-one-next-research-question` 锚点；C35/R96 未执行工作清单归入研究导航，不让它继续充当论文结论。
- 仍把 R135 draft 或旧组装稿称为 current 的表述；历史记录保留其时间含义，当前指向一致。
- 正文中的“source-metadata questions for confirmation”、S2/ms2、轮次口令及施工说明。算法历史别名在实现映射处解释一次，待作者确认事项放内部备忘录。
- references.bib、appendix、source_publication/manifest 中历史 E3/source 行号与当前实测 PE 的混用。历史定位保留旧 SHA；新稿声明实际引用哪段源、哪次运行，不全局替换旧身份。
- 章节/公式/表/图交叉引用、重复 caption/label、失效本地相对路径和未定义引文。内部研究记录可以作为数据/代码出处，不伪装成外部同行评议文献。

CITI 的原 capture URL/date 与 station ID 不因本轮改写而变得已知。按现有 archived row identity、坐标/容量与生成规则描述来源，区分 CABI/Divvy 实际 receipt；不编造原站点身份、把 live feed 现在内容填回历史、或因出处欠项重生成整个 benchmark。

## E. 组装、导出与复现

当前维护源是 Markdown + references.bib + figures，既有 `manuscript.md` 与 PDF 为派生文件；没有理由强制新建一个并不存在的维护 manuscript.tex。先读 `scripts/round137_documents.py`、`round137_pdf_qa.py` 及其实际引用的 R134 export helper。

**不要直接重跑旧 `round137_documents.py assemble`。** 它从旧 method_and_model_source 与固定 R137 summaries 重新构造正文，会覆盖 R138–164 更新；旧 QA 的120-arm gate也不是本轮完成条件。适配所需 assembly/export/QA，显式以本轮选定的当前论文组件为输入。若 `method_and_model_source.md` 仍参与生成，须同步并明确其角色；否则将其标为历史/不参与当前生成，避免它与 paper_body 成为两个权威源。

保留既有出版风格和必要的中间 TeX 导出能力，建立一条清楚、有限、可复跑的命令链，生成当前 main+appendices 的 manuscript.md/PDF；supplement 保持单独可读，必要时同链导出补充 PDF。不要把内部作者 memo 或全部执行 receipts 编入投稿正文。

完成以下必要 QA：

1. 源组件 SHA、生成命令、工具版本、输出 SHA 与导出时间可追踪；重新组装不回退当前 R163/R164 数字/结论，旧120结果仍有正确历史归属。
2. 无缺图、未解析引用、失效关键交叉引用、表格截断、公式溢出或异常空页；无 `TODO`、`NaN` 或明显施工占位留在可交给作者的技术正文。合法的待作者署名/确认信息保留在 memo，不伪造作者。
3. 在实际 PDF 上检查摘要、核心公式、主算法、关键结果表、最新 Seed 图/表、附录连接及参考文献页面。先作有限总览，再只修确有问题的页面；不能仅凭文件存在宣布视觉 QA 通过，也不为无差异输出重复全页渲染。
4. 图表数值与原合格 JSON/CSV 交叉核对，正文与附录的方法定义一致。用适合内容的确定性检查即可，不新建大型测试框架或重复全部历史资格。

如果原工具链有真实可修复兼容问题，局部修复后导出；不要改全局 app/proxy/model/credential/权限设置。若环境确实不能生成 PDF，提交可复现来源、具体错误和已经完成的稿，但在完成审计中明确该交付项未完成，不能用一个旧 PDF 冒充当前版本。

## F. GI-TBC / P-GRB 主 CSV 与来源

本轮没有新正式运行，通常没有可新增的性能记录。只核对当前主表是否已含 R164 的12个新配对，避免重复追加；文献、证明小例、PDF QA 或历史重新分析都不构成新性能行。

当前审阅已将用户的94行版本与 R164 12行增量联合为106行、28列的 `GI_TBC_vs_P_GRB_All_Tested_Instances.csv`，UTF-8 BOM、60,603 bytes，SHA256 `8f39e3a23b3b6df621139cb39b4db813ca3e992da091e97251ab8337fd2b0022`。任务附带该106行文件时，以其完整历史为基准，记录实际路径/编码/行数/SHA和结果 key。若本地已存在正确106行版本，不再改写。需要复制到既有主表位置时保留旧文件和来源记录，统一得到同一版本。

原94行包含旧91行版本没有的三条历史 N/A-P 记录：R138 的 R-B35-S-T2 Seed1/cap2400、R155 的 N-B35-S Seed0/cap7200、R156 的 R-X35-S-T2 Seed0/cap7200。保留它们及所有旧来源 URL、lambda/T 和数值精度。R164 当时只找到91行旧表，因此交付103行工作副本及12行增量，这是已披露的本地可用性边界；103行副本不能覆盖完整106行主表。

若运行环境未获得106行附件，在现有配置的实际用户文件/附件入口做一次有限定位；不要凭编写任务的说明宣称已找到。只能找到103行时，记录实际缺失三行及已包含的12行，引用已知对应历史来源，交付准确 reconciliation；不虚构原文件、不反复请求用户、不阻塞其余论文工作。只有能从固定原证据完整重建缺行时才合并，保留来源并逐字段核对。

导出新图表可使用专用 analysis CSV，不修改既有主表语义或把它当作不同版本可任意汇总的统计样本。相关主表实际无需改变时，明确报告“无新实例/Seed 性能数据需追加”。

## G. 交付物与阶段判断

交付实际修订的当前正文、完整模型/算法附录、数学分析、补充材料、bibliography、必要图表、组装稿、当前 PDF 和可复跑生成入口。

`results/unified_exact_round165/` 至少包含以下信息；能合理合并的普通记录可以合并，不为满足文件数量制造重复文书：

- `goal.md`、`source_manifest.json`：本轮输入稿、关键代码/证据/文献身份，单一当前源映射。
- `contribution_positioning.md`：C1 的小型映射及近邻区别、实际新修订；清楚回答本研究的核心价值，而非一串风险清单。
- `document_build.json` 与 `document_qa.json`：实际生成/核验、输出身份和处理的真实问题。
- `author_decision_memo.md`：简洁列明已足以写入论文的主要贡献、当前 OR 目标最重要的实质缺口、少量需作者确认的信息。不要自行承诺投稿、署名、录用档次或发送给他人。
- `final_report.md`、`decision.json`、主 CSV reconciliation、实际费用/工作记录及独立审阅结果。

阶段判断须分别回答：

1. 冻结 B 是否仍是合理主线，E+ 应如何定位，哪些完整性能主张有直接证据？
2. 当前理论和实验说明了什么机制，哪些只是正确性条件、标准构件或有限相关观察？
3. 当前稿是否已具备一次有实质内容的作者/同行内部评审条件？若 OR 级贡献仍有不足，指出最主要的具体对象与缺失论证，不能泛称“还需更多实验”。
4. 是否确有一个值得再立项的科学问题？若有，只给一个最有信息量、经过历史排重的问题及能改变判断的判据；若没有，明确建议先评审现稿。本轮不自动执行下一轮，也不要求为流程续命发明任务。

若成稿评审表明需要在完整 GI 外层与更简单 root-only 主线之间作真实架构选择，可将这一有判据的简化问题列为唯一后续候选；这不同于为外层寻找新的胜例，本轮仍不追加实验。

所有结论必须落到已经修改的稿件和可读结果。文字精简、图表更新和引用修复是交付质量，不能包装成新的算法速度提升。

## H. 独立复核、正常交付与验收

完整稿和生成 PDF 后，交给实际独立代理做三类并行复核；如当前环境不支持独立代理，准确披露可做的替代复核，不虚构 reviewer 身份或三份独立意见：

1. **数学/实现**：抽查核心命题、完整 Appendix A/B 与当前代码/冻结配置的对应；物理问题、true-g、覆盖/终止、static rows 与 C++ 身份是否准确。
2. **数据/复现**：主表、图表、各研究分母、18配对的含义、C35相反排序与绝对目标、E+独立归因、PDF与维护源一致、CSV106/103实际状态。
3. **研究贡献/稿件**：真正读当前成稿，挑战原创性与机制解释，核对近邻差异是否有原文支撑；确认不是重复R134/135准备报告、没有回避不利消融，也没有给下一轮自动加无效实验。

每位 reviewer 给出具体发现、位置与结论影响。修真实问题，按受影响范围读回；不因小文字修复重跑历史 solver 或反复审阅已无剩余风险的全部材料。最终承认未解决的真实科学限制，但消除可修的文档/论证错误后正常交付。

正常 commit/push，创建**英文 Open Draft PR**，建议标题：

`Round165: reconcile the current manuscript and sharpen the scientific contribution`

PR 首段说明为何在有限 Seed 确认后完成当前成稿、实际改了什么、读者现在能看到什么；列出核心定位与重要限制、生成/QA 和没有新增 Optimize 的实际事实。按 A 选择 main 或 R164 stacked base，读回 head/base/Open/Draft及文稿链接。不自动 merge、force-push、删除分支或联系外部作者/审稿人。

文稿和必要图表作为正常 Git 文件。旧实验包固定引用，不重新打包全部历史或下载82k成员作一轮新的全恢复；本轮仅对新增/变更的论文产物做一次有限公开取回和字节检查。商业 DLL、许可证、凭证和私有原稿不发布。依 WORKSPACE_POLICY/R122 仅清理本轮可重建且已恢复覆盖的重复临时对象；零删除允许。

验收应看到：**一份确实包含截至R164证据的当前可阅读论文及PDF；一致的模型、算法与数据来源；有明确近邻对照的贡献判断；正确保留机制归因边界和正负结果；无重复性能实验；独立复核后正常 Draft 交付。**

## I. 固定来源与复用入口

- [R164 / PR #226](https://github.com/yifanXovo/TailoredExact/pull/226)，delivery `de01e8fb27a954d031abac5fe99442d6c8d29d44`。`results/unified_exact_round164/{goal.md,final_report.md,decision.json,research_navigation.md,historical_increment.md,method_freeze.json,Seed0_reuse_qualification.json,reports/summary.json,reports/three_seed_comparisons.json,reports/primal_target_arrival.json,reports/seed_evidence.md,main_table_reconciliation.md}`。
- R164 原数值来源固定为 commit `b93a8a01ff1b7f3cbee67807be3ac6591db4767f` 下的 `results/unified_exact_round164/reports/complete_arms.json`。随后生成的12行 `reports/GI_TBC_vs_P_GRB_Round164_Increment.csv` 从 science `a29a70d132ecc17e18bc48a660225a6380722f45` 或上述 delivery 读取；不要到数值前置提交中查找尚未生成的 CSV。新 carrier SHA256 `69a5fbb42cf13c5ac557c2663228c659416d92d82366d1f81d90fa649e6eaa71`，51,931,501 bytes/82,561 members；本轮仅必要时按索引读少量member。
- [R163 / PR #225](https://github.com/yifanXovo/TailoredExact/pull/225)，delivery `8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb`；`final_report.md`、`decision.json`、`input_manifest.json`、完整 B/E+/P 结果和物理诊断。
- 当前继承 head 的 `results/unified_exact_round137/{paper_body.md,model_and_algorithm_appendices.md,mathematical_analysis.md,supplement.md,references.bib,method_and_model_source.md,manuscript.md,document_assembly.json,document_lineage.json,pdf_export.json}`；维护稿读当前版本，R137历史实验身份按其manifest固定。
- `scripts/round137_documents.py`、`round137_pdf_qa.py`、所引用的 R134 PDF helper：读取并有限适配，不能直接执行会覆盖当前稿的旧 assemble/prepare入口。
- `config/gi_tbc_round137.json`、`config/paper_s2.json`、`docs/paper_s2_release.md`、`docs/current_mainline.md`，及 C++实测源/源胶囊。
- R134/R135已有论文/定位记录；R62/R96/R97/R160、R138–162 的对应 final_report/decision/关键数学入口，仅按实际比较问题回读。
- 可复用主要数学原文：[Gupte et al. 正式版](https://www.pure.ed.ac.uk/ws/files/137476899/110836183.pdf)，[Köppe et al. 作者稿与正式版信息](https://arxiv.org/abs/math/0603311)。保留版本差别，不把当前链接替代已经固定的历史实验出处。

完成后停止本轮工作，提供当前稿、PDF、贡献判断、CSV实际状态与 Draft PR 链接，让作者据此讨论研究的下一步。
