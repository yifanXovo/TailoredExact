# Round 88 OT 工具独立审查（2026-09-26）

结论：以下冻结快照满足**固定、已审计 ENS-C VD-P LP 的一次离线根松弛诊断**所需的数学与静态执行合同。准入仅限先做只读 `audit`，再以 `round88_ot_supervise.py --whole-process-limit-seconds 120` 运行 `diagnose`；仍须协调者安排排他资源与具体实例/叶节点。本文未调用 Optimize、构建或正式 ENS 求解，也不把根界提升称为运行加速。

| 冻结文件 | SHA256 |
| --- | --- |
| `scripts/round88_ot_math.py` | `2b8855609cf469098d050fcd9c89efac01b2cb41ee07f023b5a7b79f9ff71840` |
| `scripts/round88_ot_diagnostic.py` | `c1cb1776d1b1eef0f03977e00060c1690e5505517d0e4baa71feb3b672fa0756` |
| `scripts/round88_ot_supervise.py` | `ea79e400d727bc94ca20c5ddfec61c3dfaaafd2e1f7d175a2fe5f4ffb8135d29` |
| `tests/round88_ot_math_test.py` | `dccc6d7cd9ed66035b2ecba38ce38e393d2bb7307d0f1e01561915fccd7246af` |
| `tests/round88_ot_oracle_test.py` | `6160d628f9e8d72963113bc5d617952f38412576b1c2a60cb77b9c41e611c5e9` |
| `tests/round88_ot_reader_test.py` | `ae20cac1f99f0f773b1bc71bae41f138db732f6131dc14409e7475657e122a02` |
| `tests/round88_ot_supervise_test.py` | `0ca8fdfe72ea0289181f266974ac08f638705efc3f34f163d75ddccc060df6f7` |

**数学核对。** `pair_cut` 用精确有理支持 `y/D_i` 去重排序，`h_i_j` 系数 B1 为 1、B2 为 `b−a`。每个区间宽 Δ 上，B1 由累计状态质量差 `A` 的符号给出 `Δ|A|`；B2 由累计 `q` 差 `B` 给出 `Δ(|bA−B|+|B−aA|)`。`qsum=G` 与 `a·s≤q≤b·s` 令两端点层在所有站质量相同；1D 分位数耦合同时达到全部站对成本。`aggregate_cut` 强制恰好收齐每一站对，把 pair 行求和并通过真实 Gini 行 `n·Σz_i/D_i≥Σh_ij` 消去 `h`。`a=b` 时只用 B1。端点零层、零库存与局部域外反例均有定向测试。此处证明的是有效下界行及隔离库存块的耦合事实，**不证明完整路由/额外 h 约束模型的凸包或 pair 行的全模型投影等价**。

**独立 oracle。** 作者的 12 项无求解微测通过，其中 400 组确定性有理 2×2 运输角点独立枚举核验 B1 与 B2，另有整进程剩余时限/超时 mock 测试；我另以 300 组异目标、不同区间的 Fraction 运输角点抽查系数，全部相符。符号选择取浮点 LP 点，仅决定有效绝对值线性化的方向；临近零点不会破坏行的数学有效性。窄宽度下的 `reliable` 守门会拒绝高系数或不足以压过残差放大/浮点活动误差的候选；这属于保守诊断筛选，不是 solver 数值稳定性的形式保证。

**真实 LP 身份与同源比较。** 零 Optimize 的 D7 L0 `audit` v4 对应 R87 包索引中的 LP SHA `06275aba5e2378d719390e295654849d8868fb92fd8b0366619e1c33fa713069`，读取 25,943 列、104,726 行、724,951 非零元，确认 5,616 个必要 onehot、库存/比例/乘积重建、透视、h 双向、Gini 与 cutoff 行；`G` 的 CLI 边界必须与实际 LP 双精度边界**严格相等**，系数再从实际边界 `Fraction.from_float` 构造。`relax()` 后保存完整固定原始点及逐行/变量界残差，B1、B2、B1+B2、aggregate 均从此同一个 LP 与点复制单轮加行。全适用臂 `OPTIMAL` 才标 `completed`，否则 `partial_unknown`；(a=b) 时 B2 明确不适用。首次真实审计因 `Y_i` 大小写错误、一次因 PowerShell 未保留 gamma 小数而失败，失败记录已保留；v4 通过。这些都是只读审计，非根界实验。

**执行及解释边界。** 监督器从 Popen 前到退出计时，只给子进程剩余整进程时限；逾限记 `unknown_whole_process_deadline` 并终止，前后 manifest SHA 与子进程结果 SHA 不一致则无效。`audit` 与监督运行成本分开列示，内部保存模型读取、松弛、分离、复制、加行与每臂优化成本及峰值内存。`source_sha256`、binary、scenario、leaf 标签仍是操作者声明，须同 R87 导出/包索引记录外部核对；固定 LP SHA 和结构审计自身不证明这些来源标签。cutoff 数值行以固定 LP 中的浮点行和容差核对，不把外部声明的十进制文本视作逐位来源证明。目标整数 target 是本工具当前准入条件，实际 D7 目标满足；其他目标类型需另做精确支持构造与验收。

即使单轮 LP 下界提高，也只支持**该固定根 LP 的松弛比较**。必须另用完整、多实例、等构建/等全程预算且计入全部开销的正式运行，才能评价统一算法是否优于 P-GRB；切割新颖性未证。
