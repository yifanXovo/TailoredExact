# Round 88 D7 B1 跨父子叶固定行诊断独立审查

**结论：v4 冻结快照通过静态与无求解资格审查；尚未执行六臂 Optimize，故无六臂结果结论。** 审查对象为 `scripts/round88_ot_b1_cross.py` SHA256 `356c46b05d527f7b594633e65adc9031ed5da73653b839628dd8d00df0a1c006`、`tests/round88_ot_b1_cross_test.py` SHA256 `53fb170a7da65126f28c117277168d30b1b35d43329331e8d5caec21a3337b63`。准备目录 `ot_b1_cross_preparation_v4` 中 manifest SHA256 `d1270dc11f1ed99c011028f0287f70b5bcccbbf4c56c6a8f602787f0ad311755`，row bank SHA256 `f35f924ea413fcc16a1b38b3be95d07ae9faeb430d801cded811c42358b7b9e7`，timing SHA256 `123093da867b414b4d8a5c01a58e84a49b36d8b67c9a273eec4feadfe72198bd`；本人重新计算文件哈希一致。v1–v3 是保留的修订尝试，不能替代 v4 入场。冻结依赖 `round88_ot_math.py` SHA256 `2b8855609cf469098d050fcd9c89efac01b2cb41ee07f023b5a7b79f9ff71840`、`round88_ot_diagnostic.py` SHA256 `c1cb1776d1b1eef0f03977e00060c1690e5505517d0e4baa71feb3b672fa0756`。

## 数学与身份

B1 行为 `h_ij − Σ_t Δt σ_t(A_i(t)−A_j(t)) ≥ 0`，系数只含 `h_ij` 和两站 `state_i_y`；`σ_t` 来自各自已冻结分数点。它是两站库存比值分布一维 CDF 距离下界的一个符号切面，不依赖 `G`、`q=Gs` 或父子区间端点。源码重建精确有理系数与符号，要求 `h_ij` 系数为 1，拒绝 B2、G/q/其它站变量，并核对原始支持及目标；因此同输入、同库存支持的 B1 行可用于两叶。`support_fingerprint` 含原分离叶端点用于追溯来源，但不会把 B1 变成局部有效行。**B2 与 aggregate 不在本次跨叶行库中，也不得从子叶上提父叶。**

原始证据逐项固定 SHA：父叶 `L0.lp` 为 `06275aba5e2378d719390e295654849d8868fb92fd8b0366619e1c33fa713069`，左子叶 `L0.0.lp` 为 `27cbb486939374c3f42eb7f1e97cd6ed20281b114115118c89434fa00e85c77f`；输入 SHA 相同，原诊断 manifest、`fixed_point_rows.jsonl`、完整 `fixed_point_primal.json`、result 与 supervision 均逐字节校验。源监督须退出码 0、身份前后与结果内 manifest SHA 相同、原诊断完整且 base 最优。父子 scenario、源码/二进制、cutoff、实例、target、支持一致；子 `G` 区间包含于父域。每次 `diagnose` 在 Optimize 前由两个原始分数点重新提取、验算所选 B1 行并与行库精确比较，随后重读原 LP、核对输入字节和结构审计，再对 `.relax()` 的连续模型各自复制并加行。

行库精确去重：父叶 1,184 条、子叶 1,211 条、重合 52 条、并集 2,343 条；本人读取 v4 bank/manifest 核对数量与集合。行 ID 取排序后的精确有理系数字典 SHA；`R_parent`、`R_child`、`union` 的自洽及与冻结原始记录一致性分别有校验。六臂为每个实际 LP 加上述三组行；原两份 base 目标仅为历史参考，没有再次求解 base，也没有把两份不同 LP 混作一个模型。

## 成本、状态与结果解释门槛

准备阶段单独计费：冻结 timing 记录从 `prepare` 入口到 row bank 写完 **25.2090177 秒**、零 Optimize；作者另据 `exec_command` 外层计时确认完整 v4 prepare 进程 **25.4755013 秒**，包括随后的 timing/manifest 写入及进程/命令收尾。两值必须按各自范围呈报，不能把前者称为全程。六臂若获单独执行授权，唯一 `supervise` 以冻结 manifest 的 120 秒作为从启动前校验到子进程结束的总墙钟期限，子进程只得到剩余时间；source 重验、LP 读取与 relax、全部六次 Optimize 和落盘均在同一个期限内。每臂 `wall_seconds`/`Work`、拷贝与加行时间、共享准备及整进程监督墙钟分别保留；不能相加六次“共享准备加本臂”形成虚假的总成本，也不能给单臂内部时间/Work 切片。

只有六臂全部 `GRB.OPTIMAL` 且监督 `diagnostic_process_finished`、退出码 0、manifest 前后与结果内 SHA 相同，才可比较六个目标。非最优、超时、文件破损或进程错误保留 partial/unknown 及 stdout、stderr、已有结果，不得作为无改进或失败界。本人用指定 venv 独立运行 `tests/round88_ot_b1_cross_test.py -q`，**9/9 无求解测试通过**，覆盖源身份、B1 系数/作用域、精确并集、总期限剩余时间及 partial 状态；未执行真实 LP 重审计或 Optimize。

对任一**固定的实际 LP**，并集加入的行包含两子集，最优 LP 目标应在数值容差内不小于各子集目标；`R_parent` 与 `R_child` 之间无必然大小顺序。父子同一行集的目标可报告为两份实际 LP 的对照，但仅凭 `G` 区间包含关系与结构摘要，尚不能证明两份完整 LP 除域外完全相同或可行域嵌套；跨叶界差不能单独归因于缩域。即使六臂有效，也只证明固定 LP 上的界行为，不能称 ENS 运行更快或完整模型凸包。入场与解释应使用上述确切 v4 哈希及独立资源授权。
