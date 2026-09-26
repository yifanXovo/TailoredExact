# Round 88 D7 父/子同组 B1 行归因：准备合同

状态：**仅准备，未授权 Optimize**。首轮 D7 根 LP 的 B1 下界增量和左试探子域 L0.0 的较大增量来自两个不同固定最优 LP 点 `x0`，其 B1 符号行也不同；不能据此称“缩窄 G 域使 B1 更强”。本实验只对同一输入、库存支持和目标 `D_i` 下的两份真实导出 LP 做六臂交叉：每份 LP 分别追加根点选中 B1 行、子点选中 B1 行、两者精确去重并集。B1 系数只含 `state_i_y` 与该对 `h_i_j`，与 G 局部区间无关，因此从子点选出的 B1 行可合法追加至父 LP；B2 和 aggregate 行**绝不**跨子域回传。

| 原始 LP | 真实 G 域 | 追加行集 |
| --- | --- | --- |
| R87 D7 ENS-C L0，SHA256 `06275aba5e2378d719390e295654849d8868fb92fd8b0366619e1c33fa713069` | `[0,0.29144897350424526]` | `R_parent`、`R_child`、`union` |
| R87 D7 ENS-C L0.0，SHA256 `27cbb486939374c3f42eb7f1e97cd6ed20281b114115118c89434fa00e85c77f` | `[0,0.14572448675212263]` | 同上 |

两原 LP 的输入 SHA256 都为 `d7dbd018331b9d5f3d84c0fd6c907560ef1fa92a2f8c153ac7d81e46a6cd4e9c`，支持逐站完全相同，目标、容量、权重、场景 `T/lambda/handling`、冻结来源和原截止 `0.29144897350424526` 均一致。L0.0 是 R87 被 split gate 拒绝的试探左子域，不是已采纳叶。审计仅核对了必要行/域与相同规模，**没有证明两份完整 LP 除 G 区间外完全相同或凸集嵌套**。所以“父/子”间求解目标的单调关系只可在另行证明完整 formulation 嵌套时讨论；本六臂可直接解释的是**各自同一 LP 内**更换 B1 符号行来源的效果。

## 冻结行与身份

`scripts/round88_ot_b1_cross.py prepare` 从已完成的两次原始 `fixed_point_rows.jsonl` 仅提取 `selected=true` 的 B1；同时核对原始 manifest/LP/input/结果/监督及逐列 `x0` SHA、两次求解完成状态、每条源 pair 的叶支持指纹、可靠违背余量，并用冻结 `round88_ot_math.pair_cut("B1")` 从各自 `x0` 重新生成符号与精确有理系数。提取后按归约有理系数向量 SHA256 精确去重，不用浮点容差、原行签名或叶域指纹作跨域去重。原始选中数：`R_parent=1184`、`R_child=1211`；其中完全相同行 52，精确并集 2343。准备结果为 [v4 manifest](E:/codes/ExactEBRP/results/unified_exact_round88/ot_b1_cross_preparation_v4/manifest.json)（SHA256 `d1270dc11f1ed99c011028f0287f70b5bcccbbf4c56c6a8f602787f0ad311755`）及同目录 `row_bank.json`（SHA256 `f35f924ea413fcc16a1b38b3be95d07ae9faeb430d801cded811c42358b7b9e7`）。v1/v2/v3 准备产物保留为后来加严资产哈希与成本记录前的历史尝试，不作运行入口。

`diagnose` 启动时重新核对脚本与两个冻结依赖 SHA、全部源文件哈希、源 LP/input 实际字节、原 LP 必需结构；再次从源 raw 与 `x0` 重建两组 B1 并与行库**逐行精确比较**，防止 manifest 与 bank 同时更改后注入任意行。然后分别从父/子真实 LP `relax()`，只复制并加行，不改目标、原截止、支持或其它约束。六臂顺序为 `parent+R_parent`、`parent+R_child`、`parent+union`、`child+R_parent`、`child+R_child`、`child+union`；各自 Gurobi 13.0.2、Threads 1、Seed 0、Presolve Auto、原 FeasibilityTol/OptimalityTol `1e−6`，无组件时间/Work 切片。历史 base 目标只标为参考，**不在本进程求 base，也不从本次全成本扣除**。

`supervise` 将源重新核对、两 LP 读取/审计/松弛、六次复制/加行/Optimize、证据写入统包在**一个** 120 秒外部墙钟截止内；截止后写 `unknown`，不自动重试或扩时。每臂状态、目标（仅最优时）、Work、求解、复制、加行成本与全程/峰值内存保留；若有非最优臂即停止后续臂并标部分未知。行库初次精确准备至写完行库耗时 `25.2090` 秒；外层记录完整 prepare 命令墙钟 `25.4755` 秒（含进程及工具开销），分别单列研究成本。运行时同源重验计入整进程共享成本；不能把此前已有的 base 求解当成本次免费构模。正式算法不采用这些行，也不据此设固定 k 轮。

## 待授权唯一命令

```powershell
& .\build\research\round88-ot\venv\Scripts\python.exe scripts/round88_ot_b1_cross.py supervise --manifest results/unified_exact_round88/ot_b1_cross_preparation_v4/manifest.json --out-dir results/unified_exact_round88/ot_b1_cross_diagnostic_001 --whole-process-limit-seconds 120
```

命令仅用于待审批的固定 LP 离线归因，不是 ENS/P-GRB 性能臂。运行前必须由协调者重验脚本/manifest/row-bank SHA、空输出目录及独占 solver 槽位；当前未运行该命令。
