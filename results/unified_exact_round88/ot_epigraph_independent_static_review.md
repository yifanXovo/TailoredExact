# Round88 稀疏 OT epigraph 独立静态审查

**结论：当前快照无静态阻断；仅可进入无求解微测和三份真实原 LP 的零 Optimize 身份/结构资格。** 六臂真实 Optimize 仍须资格收据和 root 的单独准入。本审查未运行脚本、测试、Gurobi、LP、编译或压缩。

审查快照 SHA-256：`scripts/round88_ot_epigraph.py` = `5d49c3fc12cc806a8008e43d756bf9c46810b21e7efc2b64c2383da4624bd7da`；`tests/round88_ot_epigraph_test.py` = `2be3e3e51333e29fcfa3b52c17f90ce4603603dd2032979191fb96a1624913ab`；`ot_epigraph_method.md` = `fdd16e1cf61ae3255781a831939800ba54c5218d89adabce5f624ad10fc66f0c`。对照 `ot_compact_epigraph_proposal.md`、`ot_closure_decision.md` 和冻结的原 LP 审计工具作只读核查。

数学：`make_plan` 将各站 `y/D_i` 用精确有理数排序、跨站同值精确合并；`bisect_right` 对闭区间左端取包含该支持的真前缀。`C,Q` 只为真前缀建列并用相邻状态递推；空前缀为零，满前缀分别为常数 1、原列 `G`。因此消去前缀列所得 `A,B` 就是原状态/透视变量的 CDF 差。B1 的两条绝对值上图行及 pair 汇总行，B2 的四条上图行及 `(b−a)h` 汇总行，投影分别等于完整 B1/B2 符号行族；B2 只用原 LP 实际局部 `[a,b]`，零宽域拒绝 B2。整数 one-hot 且 `q=Gs` 时下界恢复真实两站比率距离，原目标未改变。这是所声明切割族的投影等价，不是完整模型凸包。B2 正宽完整族蕴含 B1，六臂分开比较而非叠加冒充两项收益。

规模：脚本按 `N=Σ_i(|Y_i|−1)`、`P=Σ_{i<j}p_ij`、`K=#{p_ij>0}` 检查新增列/行，B1 为 `N+P`/`N+2P+K`，B2 为 `2N+2P`/`2N+4P+K`；行字典实计非零元并核上界 `3N+7P+K`、`6N+26P+K`，插入原 LP 后还对照模型实际增量。全部新列连续、非负、目标系数零。构建将有理系数转成有限 double，故精确投影证明是代数合同，实际界只按原浮点参数及残差门禁解读。

身份与成本：预注册和每臂重新核原 LP/输入字节 SHA、支持、实际 G 域、脚本/助手哈希及固定 solver 参数；每臂从自己的原始 LP `relax()`，不继承历史 rowbank、primal 或另一臂矩阵。原结构审计包含 one-hot、透视、`h`、Gini、目标和 cutoff；原行与新增行逐行残差、变量界、完整 primal、精确新增行账本及 provenance 都留存。共享准备单列成本，须由外层命令另记完整墙钟；每臂 300 秒从监督前检开始计，Windows Job 指派完成才释放子进程读 LP，超时杀进程树并标 unknown，无内部求解预算或转 MIP。数值 OPTIMAL 仅是固定 LP 的求解器数值目标，不是有理下界证书或运行提速证据。

先前收据缺陷已在本快照修复：`supervise` 只接受字典且 `status` 属已登记状态的子结果；结构错误、缺失或异常状态保留 `supervision.json`，标 `invalid_or_unknown_diagnostic_failure`，不再因列表等 JSON 类型触发未捕获的后续索引。新增伪子结果测试覆盖列表、空字典、非字符串和未知状态；B2 单点站满前缀测试独立核 `Q=G` 的系数与 RHS。纯有理测试另从原状态直接累计并枚举符号、验整数端点/内点与非比例透视点；这些测试**已编写但未执行**。随后资格还须实际 API/计数、Windows 子孙超时、三源零 Optimize 读模审计，并保留失败收据。资格通过也不自动准入六臂 Optimize。
