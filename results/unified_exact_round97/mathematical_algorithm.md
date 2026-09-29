# R97 原生整数路线闭环 — 已通过接入资格，完整比较进行中

保护默认是ENS-C，新的`--round97-native-closure`默认off；实验OFF用observe，另有shadow/feedback。保留24+1及R83启动、VD-P/F0、AM0.08、深度/宽度、静态行、原生策略及R68 Start。初版算子仅R83/R76；尚未评价R96的独立增量。本说明不宣称阶段完成。

原目标/时长/数值合同完全继承R96 mathematical_algorithm.md：`F=G_true+lambda P`，`G_true=H/(nS)`及原S=0约定；空载出发、逐前缀[0,Q]、单次单向非零服务、允许带载回仓完整卸载，时长为实际有向旅行加`(c_pick+c_drop)*sum pickup`。不依赖距离对称性或三角不等式，数学T与进程cap分开。

流程：

1. 每个现有生产MIP开始前只读取原模型列/界/类型、所有线性行、线性目标和常数；拒绝未资格的非线性/一般约束模型。原生调用及数学target不变。
2. 每次MIPSOL读取完整原列向量，double读取OBJ/OBJBST/NODCNT，int读取SOLCNT/PHASE。自增事件序号不用SOLCNT代替。检查有限性/界/整数/线性行及模型目标，解码并逐个核对所有x/p/d，独立Evaluator重算库存、前缀载量、时长和真实F，核对全部Y。记录模型G和真实Gini；MIPSOL不自动等于新incumbent或后启动事件。
3. 状态hash使用完整归属、顺序、整数操作。当前Instance只有共同T和共同旅行矩阵，因此只在等Q车类内规范化；使用车辆按服务数及完整路线字典序确定排序，显式空路线与缺失空路线同状态。哈希在一个固定实例/lambda session中使用，绝不跨实例复用。
4. 新规范状态进入原R83闭包，不要求原状态先优于全局U。既有R76严格F下降与R83中性等净量换块/平衡块迁移交织；中性步骤保持库存且严格降低降序车辆完整时长向量。有限整数物理状态和词典序(F,时长势)排除循环；并非多项式、全邻域或全局最优证明。
5. accepted observer仅在原闭包接受并经Evaluator验证之后执行；新的更好archive再独立规范化/验解，记录完成时刻。全程截止前已验见证保持，之后扫描中断标未穷尽，不继续改善或倒填结果。默认observer为空，不改变ENS启动算子。没有子优化器/内部时间或Work预算。
6. 缓存物理闭包结果；只有穷尽（或F=0）的输出状态可直接标成已闭包。对每次当前调用重新映射/验行；域/epoch不同不复用可提交性。每个native call对已提交candidate hash去重，输入输出缓存防止自身反馈重复闭包。
7. 仅同目标嵌入：真实Gini须在当前叶域，取G=G_true，重建所有实际列，检查界/类型、每一实际线性行及原模型目标。当前范围无G抬升；物理合法但当前域不兼容不提交，仍可保存archive。允许candidate F等于全局cutoff而改善缺失或较差native incumbent。通过`GRBcbsolution`提交完整向量，没有GRB_UNDEFINED。
8. callback不更新全局U/epoch、前沿、cutoff，不终止或重启树。SHADOW从不提交/交接。FEEDBACK在原生自然返回或原有数学target返回后，先回放本次旧时间界事件并合并普通native incumbent，再交接更好的已验archive、严格降低U、推进epoch和既有安全cutoff收紧；在真实返回时间记事件。下次原有ensureArtifact按新epoch清旧模型/LP/子缓存。旧较宽cutoff的有效界/最优/不可行对较窄集合仍有效。

全局精确性仍依赖完整G域覆盖、合法叶界及原数值证书门禁。任何闭包点仅给原可行UB；单叶界绝不作为全局LB。物理状态有限使严格UB epoch更新有限，再结合既有同epoch稳定目标/有限树控制证明终止，不只依赖depth8。数值容差与Gurobi请求双gap0不改，不声称有理证书。

证据分开记录：API返回码、MIPSOL完整向量匹配、后续MIP或最终native incumbent变化、结束时完整向量匹配。MIPSOL提交返回infinity为待处理含义之一，非拒绝。相同向量不证明唯一来源。Start物理状态匹配与node count帮助界定后启动证据，不能仅以MIPSOL序号宣称native来源。

成本：全进程支付构造、规范化、验证、映射、持久化与正常收尾。adapter RAII累计新callback路径包含cbget和event flush；closure/map为其嵌套子项不重复加总。setup、return观测另存native日志旁收据；archive handoff由phase ledger计时。OFF观测包含向量核查与新状态写盘，必须实测其成本，不先验称零开销。
