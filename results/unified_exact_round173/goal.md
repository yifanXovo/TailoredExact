/goal

# Round173：对齐当前论文阅读与重建入口，完成作者技术审阅交接

## 0. 目标与有限范围

继承已完成的 **Round172 / PR234**。论文的实质修订已经完成：主文以共享库存状态、完整 GI-TBC 方法及有界交通决策组织，数学与算法语义经独立复核保留，主文为8,369词，结论304词。当前不再重写同一篇论文，也不安排新算法实验。

本轮只解决一个实际交付缺口：**当前正文和PDF已是R172，但README、作者阅读入口和运行/重建指南仍混用R165、R170、R171的“当前”指针。尤其 `docs/paper_review.md` 仍让读者执行R171文稿脚本，与新稿表号、节号和实际构建入口不一致。**

完成后，一名新读者应能从README直接找到正确的论文、附录、补充、作者事项及版本身份；需要重建文稿时能使用正确的隔离环境和R172入口；查看历史求解复现时能识别R137合同及其它面板各自的实际记录。改三个当前入口和必要结项文件即可。

这是发布入口的有限收尾，不是新增科学贡献或算法优化。现有R172稿件已经可以交给作者/同行技术审阅，本轮不构成等待反馈的前置研究门槛。

### 0.1 时间、计算与工具

**目标约60分钟，科学工作上限90分钟=5,400s，完成即停止。**建议入口10分钟、三个文档修改25分钟、定向检查和独立读者15分钟、交付10分钟；剩余容量只处理实际问题，不以新任务填满。

- 新Optimize=0；新H=0；C++编译=0；新实验/证书/CSV记录=0。
- 不重新组装或导出已经验收的R172文稿，不运行 `assemble/pdf/qa`；本轮PDF重建=0。
- 保留长期约定：正式算法生产和计时的H、目标/物理验证、Start、模型与Optimize统一使用C++。Python/Node只用于文档、静态读取和下文指定的一次无求解入口检查。
- 记录真实起止及必要的Git/公开取回I/O即可，不建立新实验账本或完整历史审计工程。

## A. 本地工作区、身份与分支

遵守实际 `AGENTS.md`、`WORKSPACE_POLICY.md` 和已有工作区约定。新工作在 `E:\codes\ExactEBRP-work` 内。保护 `E:\codes\ExactEBRP` 及用户活动工作树；`worktrees\paper-current` 和原项目已有未提交修改，不reset、stash、覆盖或以它们作为本轮操作目录。

建议新隔离工作树 `E:\codes\ExactEBRP-work\worktrees\round173`，分支 `codex/round173-review-entry`。已有同轮内容据真实状态接续。文稿权威目录仍为 `results/unified_exact_round137/`；本轮结项目录为 `results/unified_exact_round173/`。

| 身份 | 编写任务时已核实的值 |
|---|---|
| 仓库 | `yifanXovo/TailoredExact` |
| 前序 | [PR234 / Round172](https://github.com/yifanXovo/TailoredExact/pull/234)，Open Draft |
| R172 delivery head | `111d62ac2cdc52927caed2bfb42d20bbef2e8463` |
| R172科学/文稿提交 | `b770e94be267f27aabfee81bcdd6e7e142034aa3` |
| R172分支 | `codex/round172-journal-manuscript` |
| R171 delivery | `e8c4a0d3ccbaf1c1a6e6f83242d9163fe29e74e4` |
| main | `b2b940c1e517a72e226ec60fc49ff19651737632` |
| 当前历史实测C++ source | `781c548b410a2749190e3f0c4b149c2ad885c054` |
| R169–R171共同实测PE SHA256 | `c6ddf0b62f1200d02a8c654fd3f278ced704130f1a8950fc1e6464b9cbb11e57` |
| R172主稿PDF SHA256 | `79f10db5b4fa2d172d0b9e3f797ff15ffa9ab57c6b1c065cacda5b6f9b8207e8` |
| R172补充PDF SHA256 | `63e3ac936e1318e02bdcedd4ed930f0e2fe70da6831e728d6d976e9851524084` |

入口做一次有限远端/本地核对。如果main已包含完整依赖则基于main，否则基于R172 delivery，以R172分支为stacked Draft PR base，不等待前序合并。若出现真实的新合法提交，核对增量后接续，不能覆盖它。

科学稿的版本仍称R172；R173只修阅读/重建入口。不要将未改的论文、PDF或历史实测PE重标成“R173新科学结果”。若入口问题在实际基线中已全部修好，只交付有限核对结论，不重复修改或创建空PR。

## B. 定向阅读和已完成工作的边界

只需读：

1. R172 `final_report.md`、`revision_record.md`、`review_record.md`、`author_decision_memo.md`、`integrity.json`；
2. README、`docs/paper_review.md`、`docs/paper_s2_release.md`；
3. 当前正文目录、§§3–5的必要位置，以及 `scripts/round172_documents.py` 的路径、命令阶段和写入范围；
4. `scripts/paper_s2.py` 与 `config/gi_tbc_round137.json`，仅核实其历史版本、dry-run和`--run`语义。

遇到具体指针歧义再定位对应小型历史记录。不要重新恢复所有raw、大包、120位置replay、28个CLI向量、旧n50历史、R165贡献清单或R166–R171证明。

接受已完成的有限结论：B仍为冻结统一方法；C166/D167/C169未被推广为默认；R171六组n50比较中B的U5/6、L和gap6/6，双方全OPEN；R172没有新增实验、证书或优势实例。当前CSV仍132条。这些是入口所指向的结果，不需要本轮再证明一次。

## C. 修正三个当前入口

### C1. README：让读者先看到正确成果

更新当前稿版本、阅读路径、作者memo和文稿构建指针。应直接可达：

- 当前主稿PDF和完整 `manuscript.md`；
- 主稿中的Appendix A/B、补充PDF及必要源文件；
- `results/unified_exact_round172/author_decision_memo.md`、R172修订/审阅记录；
- 权威132条benchmark CSV；
- 更新后的阅读说明和运行/重建指南。

按实际需要调整原有短介绍，不另写一篇贡献总结。R171实验报告可以继续作为n50数据来源，但不能再称其作者memo为当前稿决定说明。R165贡献图可以作为有明确版本的历史解释保留，不能取代当前正文。旧 `round170_documents.py` 不再作为当前构建入口。

R136已合并main、旧K1/R135等历史说明可以保留其准确身份。不要为了消除旧轮次数字而全局替换历史内容。

### C2. `docs/paper_review.md`：一个可直接阅读的作者入口

把“当前R171”改为实际R172科学稿，将n50指向 **§4.4 / Table6**，机制边界指向§4.5，交通决策指向§5。采用简洁阅读顺序：

| 阅读问题 | 实际入口 |
|---|---|
| 原问题、共享状态和两个结构结果 | §§1–2，Appendix A.9/A.11 |
| 完整算法、覆盖和实际续解 | §3.2 Algorithm1、Appendix B |
| B/P/付费PS、Seed与n50结果 | §§4.2–4.4，必要补充表 |
| 表示、控制器、初始化的边界 | §4.5，S166/S167/S168/S170 |
| 资源和连续权重能支持的决策 | §5.1–5.2及相应数据 |
| 实际修订、独立读者、作者待定事项 | R172 revision/review/author memo |

保留足够的判断提示：默认B与研究变体分开；full/root独立收益未建立；P/PS、CITI/C35反例及n50全部OPEN仍可见；资源和权重结论是原目标的界。不要将这份入口扩展为新的文献综述或第二份论文。

作者姓名顺序、单位、资助、HGA-TGBC前序稿的归属/状态、公开代码数据说明等沿R172作者memo。未知事实不编造，不以等待作者回复阻断本轮入口修复。可以列最多三个具体的技术阅读问题，供作者判断贡献组织、算法可理解性和证据范围；不安排自动给老师/编辑发消息。

修正当前审阅记录、构建记录和QA链接，避免把R171的旧审阅目录写成R172的实际文稿审阅。已有R172记录继续作为已完成证据，不在R173再生成同内容的“复核报告”。

### C3. `docs/paper_s2_release.md`：区分当前文稿与历史运行合同

开头明确两类入口：

1. **当前科学稿与文稿重建：R172。**链接现有文稿、R172 source/build/QA/review及作者memo；当前文稿入口是 `scripts/round172_documents.py`。
2. **历史R137求解启动合同。**`scripts/paper_s2.py` 仍读取 `config/gi_tbc_round137.json`，其默认source、PE、argv、时钟、affinity和既有资格仍属于R137。它不是所有后续面板的通用复现实验命令。

保留原R137的真实参数和身份：包括其30秒shutdown margin、cap−6 Native上限、cap−2 supervisor语义及原矩阵中的预算。不得为了贴合R171的6秒margin而修改历史profile或文档中的真实历史值。“600/1200/2400按规模”的说法只在明确限定的R137面板内保留；当前论文的多面板协议以新Table1和各自manifest为准。

R169–R171使用另一个已记录的实测PE；需要核对这些面板时，指向各自实际argv/matrix/source记录。说明不同历史观察保留其源、构建和完整费用，不宣称换一个`--exe`就等于复现所有历史结果，也不为本轮建立新的统一运行包装器。

`paper_s2.py` 默认仅展开命令，`--run`才启动C++。本轮不运行其`--run`，不因旧PE缓存缺失重建或换一个文件假装已验证。它的Python角色是启动编排，正式H和优化仍是C++。

移除让读者直接在已有脏 `worktrees\paper-current` 上工作的推荐。当前和历史操作示例均应使用自行新建、未占用的隔离checkout；不要删除、清理或复用用户的活动目录。

## D. 给出准确的R172文稿重建说明

读者只阅读论文时直接使用已发布PDF即可。重建说明针对需要复现文稿输出的人，指向**固定R172提交**及一个新隔离checkout，不能指向用户正在编辑的工作树。

可选重建应使用全新专用根，例如以 `E:\codes\ExactEBRP-work\rebuilds\r172-<唯一标识>\worktrees\paper` 作为checkout。该布局使 `ROOT.parents[1]` 等于专用根；先运行 `paths`，确认PAPER、OUT和TEMP都落在该专用根内，再按需执行文稿阶段。不要只在原 `worktrees` 下换目录名而继续共用历史temp。R173本轮仅在本轮隔离树执行下述一次 `paths`，不创建或执行这个可选重建环境。

明确实际阶段：

```powershell
python -B scripts\round172_documents.py paths
# 仅当读者需要重建文稿时，在该隔离checkout中依次执行：
python -B scripts\round172_documents.py assemble
python -B scripts\round172_documents.py pdf
python -B scripts\round172_documents.py qa
```

文档根据实际本地Python位置给出可用调用形式；不要声称任意新机器已经通过构建。当前环境已有的Pandoc、XeLaTeX、Poppler和Python依赖沿R172真实记录说明，不新增安装、下载商用资产或clean-machine验收工程。

解释这些路径的实际含义：

- `ROOT` 是该次隔离checkout根；
- `PAPER` 是其 `results/unified_exact_round137`；
- `OUT` 是其 `results/unified_exact_round172`；
- `TEMP` 按脚本规则为 `ROOT.parents[1]/temp/round172/pdf`，在上述重建布局中位于全新专用根下。

固定R172文稿重建会在**该隔离checkout的本地副本**中生成R137文稿输出和R172文稿记录；它不应在本轮R173活动工作树中执行。OUT仍叫R172是重建原版本的合同，不要为了轮次把脚本改绑R173。`paths` 打印的Base仍为R171的 `e8c4a0d3ccbaf1c1a6e6f83242d9163fe29e74e4`，这是R172文稿的比较基线，也不应改成R172或R173。任何本地重建输出不自动提交回历史记录。

`paths` 是检查上述绑定的无求解入口。先读清导入链无生产动作，然后只在本轮隔离树中执行一次 `python -B scripts/round172_documents.py paths`，核对打印出的路径并退出。这个阶段不运行文稿构建、资格replay、H或优化；不得将它报告成已重建PDF或重新验证算法。

如果仅`paths`因当前既有依赖缺失不能执行，记录具体缺失，以源码确认实际绑定，不安装一整套工具、不伪造成功、不升级为另一轮构建。R172已经完成的PDF导出和公开恢复可继续引用。

## E. 一次有限检查

检查实际改动而非全仓库：

1. 从README按阅读说明走到当前主稿、补充、R172作者memo和132表；检查新改的相对链接、锚点、节号和表号确实存在。
2. 检查三个入口中“当前/current”的范围与真实对象一致。旧R165/R170/R171可作为标明版本的历史结果保留；不要靠禁止所有旧轮次字符串来验收。
3. 检查文稿说明使用R172入口，历史运行说明仍忠实R137合同；正确区分 `paths`、重建阶段、launcher dry-run 与 `--run`。
4. 检查没有引导用户进入原项目或脏 `paper-current` 操作；示例新目录不能覆盖已存在目录。
5. 比较相同表示层的Git tree/blob：求解核心、config、启动器、全部当前稿组件/PDF和R172历史结果不变。避免把Windows CRLF/LF差异当作内容修改。

权威CSV路径为 `results/benchmark_tables/GI_TBC_vs_P_GRB_All_Tested_Instances.csv`。正常基线为 **132条、28列、82,303bytes、UTF-8 BOM/CRLF**，SHA256：

`0487ebaf90274f85a7cd94358215a701825f328c954a8de235fd5e58633989dc`

本轮新增0行，不再追加R171六行，不重新导入导出或重排CSV。一次入口/结束字节或Git blob核对即可。若基线已有后续合法增长，则保留真实入口版本，不回退到132。

复用现有工具或简单命令完成上述检查，不创建新的通用链接框架、单元测试套件、当前版本切换器或发布平台。没有新的不一致时停止检查。

## F. 保持产出小而完整

正常变更范围仅为：

- `README.md`；
- `docs/paper_review.md`；
- `docs/paper_s2_release.md`；
- `results/unified_exact_round173/` 中的少量本轮结项文件。

结果目录只需原 `goal.md`、简短 `final_report.md`、实际独立 `review_record.md`、`delivery_receipt.json`。入口、实际耗时、路径检查、当前稿/CSV不变身份、变更说明可以合并在这些文件中，不另复制作者memo、文稿、历史数据或raw。

最终报告说明实际纠正了哪些入口、为什么读者不会再混用版本，并明确：没有新算法、运行、证书或性能优势；科学稿仍为R172，CSV保持实际入口版本；下一个有意义的阶段是围绕这份稿件的作者/同行技术审阅。

若检查发现独立于本任务的真实科学缺陷，只精确记录其位置和影响，交作者判断；不静默改论文、不启动本轮未安排的新求解。普通链接和版本文字错误在本轮直接修好。

## G. 成稿后的独立复核

三个入口改好后，请两位独立读者查看实际文件及必要目标：

1. **执行/入口读者：**沿README→阅读说明→构建/运行说明确认版本、路径与写入范围；区别当前文稿重建与历史C++运行合同，核对没有误执行或扩大验证。
2. **研究/作者读者：**确认入口指向已完成的科学稿，贡献、反例和范围的简短介绍准确；没有再次安排重复整稿/实验，也没有把未提供的作者事实写成已确定。

记录具体所读内容、发现的问题和修正后确认。只复查实际影响范围，无需重审全部115页PDF或所有数学证明。若独立代理不可用，如实记录实际替代检查，不虚构外部人类评审。

验收标准是新读者能正确使用入口，固定科学成果保持完整且身份清楚。无需等待作者确认姓名、资助或投稿选择；这些事项继续列在已有memo。

## H. Draft PR和公开读回

正常commit/push，创建英文 **Open Draft PR**。建议标题：

`Round173: align paper review and document build entry points`

PR首段说明实际问题：R172稿件已经完成，但三个入口仍有旧current指针和错误构建建议；说明本PR将入口对齐，同时保留历史运行合同。给当前文稿、作者说明和更新后的指南链接。

按A选择main或R172 stacked base，读回实际head/base/Open/Draft。对本轮新改的三个文档及必要结项文件做一次公开取回/字节核对，复用已有方式。当前PDF、CSV和历史raw未变，不再次下载大包或执行完整恢复。

科学/文档提交与引用其实际SHA的回执提交分开，不填self-SHA。不自动merge、force-push、清理旧PR、删除用户工作树、投稿或联系作者/编辑。正常已授权的本地修改和Draft交付不必再次索要许可。

## I. 最终回复与停止

最终回复先报告三个入口的实际修正及独立复核，再给当前主稿/补充/作者memo和Draft PR链接。明确R172科学稿已经完成，本轮只收尾入口；没有新的性能或CSV增量。

列清作者可以马上阅读哪些章节、已有memo中哪些事实仍需作者决定。不要把本轮包装成新的OR机制、投稿完成或期刊审稿通过；不要求先做一轮新实验才能给作者看。

**入口问题解决后结束本轮，不自动开始Round174。**后续实验须由具体作者/同行问题或一个能与既有历史区分的结构对象和预测触发，不按轮次机械增加Seed、规模、预算或候选。
