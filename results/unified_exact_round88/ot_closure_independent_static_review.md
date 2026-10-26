# Round88 OT 闭包工具独立静态审查

审查对象：`scripts/round88_ot_closure.py`（作者最终快照 SHA256 `129b9224ac36e44b52fcc911604938a024d79986f8bd5fe8a8ffd6b14d1b2934`）、`tests/round88_ot_closure_test.py`（`9163731d3f1e1d5fa92c641f26387e8c5ccd34fd314f48c0124b1880ecd21546`）、`ot_closure_method.md`（`31bb1ec5f04b4accb19ba2a056ae25ac152e361b6b3722954b289b08652141ab`）。哈希取自作者快照通知，本审查未重算大文件。最后一次脚本变更仅在 `provenance.json` 添加冻结 manifest 已有的 `T`、`lambda`、取送时间、verified UB 和完整支持；三个源 manifest 均含这些字段，静态复核未见数学、状态或监督路径变化。**当前结论：可准入无求解微测及零 Optimize 身份/读模资格；没有准入九臂真实 LP。** 本轮未运行脚本、测试、Gurobi、LP 读取或构建。

## 数学行、域与身份

`fast_pair_cut` 先以精确 `y/D_i` 合并两站同层支持，再把实际浮点 primal 的每个二进制值转为 `Fraction` 前扫 `A_l,B_l`；符号零取旧工具的 `+1`。B1 的系数后缀为 `−direction·Σ_{l≥k}Δ_l sign(A_l)`；B2 分别用 `bα−aβ`、`β−α`，`h` 系数为 `b−a`。这与原逐段重扫的解析行一致；重复层级没有虚增零长度段。`a=b` 不构造 B2。所选符号是**该二进制表示点**的最大支持行；旧 `pair_cut` 按浮点顺序求和，在近零处可能选另一合法符号，不能宣称两者逐位相同。

`row_signature` 包含源 LP SHA、pair、库存支持、规范系数及 B2 本地 `[a,b]`；`model_row_signature` 用同一 LP 内的规范系数去掉 B1/B2 家族标签，仅为合并**完全相同的不等式**。`audit_model` 在读取原 LP 后核真实 G 边界、VD-P onehot/qsum/product、Gini、目标与 cutoff，随后从实际 G LB/UB 取精确二进制端点。F2 root、D7 root、D7 child 各自读取自己的冻结原 LP 并 `relax()`；没有历史 rowbank 初始化，child B2 不上提 parent。B1/B2/combined 的每轮 pair 扫描和可靠新行都独立于其它臂。

## 闭包循环与数值语义

每轮仅在 LP `OPTIMAL` 且原/新增行和变量界残差通过既定 `1e−5` 守门后扫描全部 pair；`_scan` 加入全部越过原 `reliable` 余量、此前未见规范签名的新行。更新版逐行同时记录 `Fraction.from_float` 点上的精确原始/归一化活动与转 double 后的活动：只要任一视角有正违背，就不会归入“无观察违背”；精确点不违背而浮点称可靠正违背则记数值拒绝。已在模型中的签名仍可靠违背、系数/活动不可可靠转换或残差失守均不转成“闭合”。无可靠新行与完整扫描无观察正违背分列；后者仅是**浮点观察性闭合**，不是精确行族证明。源 LP、完整 primal、逐行残差、所有候选/原因、行账本、每轮 Optimize wall/Work、行列非零元和峰值进程内存都有保存路径。没有内部轮数、行数、秒数或 Work 门槛，也没有转 MIP。

外部 `supervise` 从源身份核验前计整臂 300 秒；Win32 kill-on-close Job 加 ready 握手使诊断进程在 Job 分配前不读 LP，超时关闭整个树，POSIX 用进程组。超时和在途证据独立标 `unknown_whole_diagnostic_deadline`；摘要写入后越限也改 unknown。每臂重复支付原 LP 哈希、读入、审计、relax 与优化成本。共享 `prepare-supervise` 现单独记录外部发射到准备进程退出墙钟及失败收据，也须计入完整研究成本。

## 资格仍须补的验证

测试文件是独立有理朴素重扫与极端符号枚举，静态上覆盖同层、异质 target、零层、窄/等宽域、`−1/0/+1` tie、随机可行端点耦合及双层签名；更新版还新增无 Gurobi 的 `_scan` 四态/旧行违背、准备失败收据，以及实际 `_wait_with_deadline` 加 Win32 Job 的短暂 Python 子孙进程终止微测。**这些测试均尚未执行**，伪造 Gurobi `reliable` 的状态测试只验控制流，不替代真实 LP 数值验收。实际 Win32 微测通过后还须零 Optimize 的三份源身份/读模资格，并由 root 再授权九臂。

资源与 root lease 未下发前不得运行九臂。即使未来九臂均观察性闭合，也只说明各自冻结固定 LP 的行族效果；完整模型凸包、整数证书及 ENS-C 相对 P-GRB 的认证提速均不随之成立。
