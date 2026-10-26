# Round 88 OT 闭包离线诊断：实现与待验收合同

状态：**仅完成实现和静态自查，未运行测试、未导入 Gurobi、未读取模型、未 Optimize；九臂性能诊断未获准。** 实现文件为 `scripts/round88_ot_closure.py`，独立精确有理微参考为 `tests/round88_ot_closure_test.py`。冻结的 `round88_ot_math.py`、`round88_ot_diagnostic.py`、C++ 和 A1 runner 均未修改。

## 数学行与快速构造

每对 `i<j` 将两站固定支持的 `y/D_i` 有理比率排序，按同一层级汇聚 selector `s`、乘积变量 `q` 的差。前扫得到各正间隔左端的 `A_l,B_l`，在实际浮点 primal 的 **精确二进制有理解释** `Fraction.from_float` 下取符号；零仍取 `+1`。B1 取 `sign(A_l)`，B2 分别取 `sign(bA_l−B_l)` 和 `sign(B_l−aA_l)`，其中 `a,b` 为实际 LP 的双精度 G 边界转成的有理数。反向累计 `Δ_l σ_l` 或 B2 的 `Δ_l(bα_l−aβ_l)`、`Δ_l(β_l−α_l)`；每个状态只查其所在层级的后缀，即得到完整行系数。排序后每对线性构造，不逐间隔重扫两站支持。`h_ij` 系数 B1 为 1、B2 为 `b−a`；新增 B2 行仅用本 LP 的真实 `[a,b]`，`a=b` 只准 B1。

家族签名包括源 LP、pair、固定支持、精确规范化系数，以及 B2 的局部 G 域；另有不含家族标签的模型行签名，专门合并同一 LP 内 B1/B2 恰好相同的规范化不等式。两种签名分别记在原始逐行证据与新增行账本，不跨 LP 或叶复用。

精确符号方法与旧 `round88_ot_math.py:pair_cut` 的顺序浮点 `sum` 在极近零处可能选不同符号。因此这里**不宣称逐位重现旧单点行**；两种符号都属于各自合法行族，数学有效性依赖同一固定支持与局部 G 域。逐行另记 `Fraction.from_float` 点的精确原始/归一化活动：若浮点与精确点违背符号不同，记录差异；精确点有正违背而浮点余量不足归入 `no_reliable_new_row`，浮点声称可靠正违背而精确点不正则归入数值拒绝。浮点转系数/活动、原行残差与已有行残差仍须经旧诊断的 `reliable` 余量和 `1e-5` primal 守门；精确有理系数不自动构成精确 LP 证书。

测试文件另写朴素每间隔重扫参考，不调用快速算法组装自身期望。待计算槽许可后，须执行无 Gurobi 的微测试：整行规范系数、符号、每段 CDF、原始精确活动与小支持极端行族的最大违背逐项相等；覆盖异质整数 target、重合比率、零质量、`−1/0/+1` 零 tie、`a=b`、窄正宽及随机可行端点耦合。生产 tie 固定 `+1`，其它 tie 仅数学对照。若任何例不同，阻断 `prepare` 与九臂。

## 冻结源与逐臂合同

只预注册 F2 root、D7 root、D7 历史未采纳 child 的既有资格 manifest，固定 SHA 分别为 `d223756f601a5f9c1966e5087e6ddace81bcf1b53130afdad2bb79366421b905`、`a0996967e9278469defa43ab1c630b0d16f7e996062f71bf91efa9a656f99a4d`、`e73e08318afe65d9c4d145f2dd8efe8732783b11e0628f347434b4093c2f09fd`。每源三臂 `B1/B2/B1+B2` 独立读取**自己的原 LP**、输入和资格结构，不拷贝上臂模型，不装入历史 rowbank，不将 child 局部 B2 行上提 parent。child 仅为机制诊断，不冒充正式树的收益。准备阶段输出九臂身份 manifest；真正执行还需 root 为其 SHA 写 `ot_closure_lease.json`，`supervise` 与子进程均核验该 lease。

每一完整臂由 `supervise` 从逐臂文件身份检查前开始计时，300 秒外部单进程树截止。Windows 使用 kill-on-close Job Object，并用 ready 文件保证子进程先被纳入 Job 才开始导入模型。诊断子进程再核源 LP/输入 SHA，以既有 `audit_model` 检查真实目标、行、支持、cutoff、`[a,b]`，`relax()` 后从原连续 LP 优化。每轮保存 Gurobi 日志、完整 primal、原始/新增模型行最大残差与最差二十行、所有 pair 的完整候选行与精确签名、浮点及精确二进制点的原始/归一化违背与可靠余量、每轮 Optimize wall/Work、行列非零元/峰值内存及新增行账本。每轮加入**全部**可靠且未见签名的新行，再重优化；没有轮数、行数、内部秒数或 Work 截断，也不转 MIP。模型读入、源/结构核验、初始 LP 优化与所有迭代都在同一 300 秒墙钟内；共享 manifest 准备通过 `prepare-supervise` 单独记录**外层发射至子进程退出**完整墙钟与失败收据，再加列研究成本，不当成免费的逐臂运行。

终态互斥：`complete_scan_no_observed_violation` 是完整 pair 扫描无正违背的**数值观察闭合**；`no_reliable_new_row` 表示仍有正候选但无可靠新行；`existing_row_violation_or_numeric_rejection` 表示旧行可靠违背、原/已加行残差失守或系数活动不可靠；`unknown_whole_diagnostic_deadline` 表示整项外部截止；另外保留 `unknown_lp_not_optimal`、`observed_lp_infeasible`、身份/进程失效状态。后几类均不冒称闭包或认证。超时后保留最后完整轮与 `inflight.json`，不重试。

## 分阶段验收

1. 计算槽释放后先运行纯数学微测试、无 Gurobi 的完整 pair 扫描状态机/失败收据测试，以及 Win32 子/孙进程 Job Object 截止终止微测；再用小规模受控模型检验实际 Gurobi 读模/审计/增行路径。测试会启动短暂 Python 子进程，因此当前未执行。不得提前启动九臂真实 LP。
2. 对三份真实原 LP 只做身份与结构/模型读取资格，不 Optimize；确认源 SHA、支持、真实区间、cutoff、行列数、脚本/依赖指纹、输出目录和日志路径。若环境或身份不匹配则阻断。
3. 独立审查实现、微测试与零 Optimize 资格材料后由 root 冻结脚本和 manifest、签九臂 lease；仅此时可按单臂 300 秒顺序真实诊断。每臂无损留原始结果及监管收据，未知与失败全计费。

这项离线 LP 家族诊断即使得到观察性闭合，也只对各自冻结的固定松弛成立；不提供 ENS-C/P-GRB 完整算法速度、整数最优或原问题认证结论。
