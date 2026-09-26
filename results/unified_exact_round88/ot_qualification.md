# Round 88 OT 工具资格记录（待独立复核与 solver 时段）

## 已完成的零 Optimize 检查

- 本地隔离环境：捆绑 Python 3.12.14 建立 `build/research/round88-ot/venv`，只在该 venv 安装 `gurobipy==13.0.2`；导入版本返回 `(13,0,2)`。未复制旧 build 树，未更改全局解释器或 Gurobi 配置。
- `tests/round88_ot_math_test.py` 包含全部小整数点的有理代回、B1/B2 严格见证、`a=b`、极窄域、零层/零库存、跨域反例、aggregate 系数与共同分位耦合。`tests/round88_ot_oracle_test.py` 独立枚举两个端点层各自 2×2 运输多面体的两个角点，以 400 组固定随机有理边际检查 B1 最优值及 300 组正宽域 B2 最优值；包括异质目标、零端点层及宽 `1/1000`。`tests/round88_ot_reader_test.py` 用合成 LP 只读往返核对 Gurobi API、结构拒绝、窄域数值守门、严格端点身份和部分臂状态。`tests/round88_ot_supervise_test.py` 用假进程检查整进程剩余截止和超时 `unknown`。最新完整测试 12/12 通过，耗时约0.13秒；`compileall` 与 supervisor CLI `--help` 通过，均未 Optimize。
- 真实只读资产：R87 `E:/codes/ExactEBRP-round87-runtime/campaign/local_raw/03_D7_ENS-C/external/models/L0.lp`，SHA256 `06275aba5e2378d719390e295654849d8868fb92fd8b0366619e1c33fa713069`，与 `results/unified_exact_round87/package_index.json` 登记一致。输入 SHA256 `d7dbd018331b9d5f3d84c0fd6c907560ef1fa92a2f8c153ac7d81e46a6cd4e9c`，与 R88 runner 合同一致。`paper_leaf_ledger.csv` 确认 L0 为根叶，`[a,b]=[0,0.29144897350424526]`。原 LP 的 cutoff 行 `c6128` 右端正是 `0.29144897350424526`；结果 JSON 后来改进的最终 UB `0.22353154577371831` **不是**本 LP 构建时 cutoff。
- D7 的 `audit` 仅 `gp.read` 与行/域检查，最终输出在 `ot_qualification_d7_audit_v4/`：25,943 列、104,726 行、724,951 非零元；5,616 条必需结构行通过，manifest 记录全支持、目标和实际双精度 G 边界的精确有理表示；审计直到 manifest 落盘的墙钟 1.3182 秒。没有调用 `optimize()`/真实 LP 松弛。

## 失败尝试与修复

第一次真实 D7 `audit` 在变量域检查因工具将源码中的大写 `Y_i` 写成小写 `y_i` 而失败，错误 `unexpected type or bounds for y_1`；失败产生的空 `ot_qualification_d7_audit/` 目录保留。核对 `src/CplexBaseline.cpp` 的 `yName` 后修为 `Y_i`，同步合成 LP 测试，v2 通过。独立审查随后指出模糊端点比较可能导致局部 B2 误用于真子域，于是改成 CLI 双精度端点与真实 LP 界严格相等，并从实际界生成行。v3 第一次使用未加引号的 PowerShell 数字实参，shell 先行舍入，严格审计如预期拒绝；失败目录 `ot_qualification_d7_audit_v3/` 保留。将十进制端点加引号后 v4 通过。所有失败均未触发 Optimize，也未修改 R87 模型或结果。

## 来源与尚缺证据

LP/input 字节哈希、真实模型行和域已经验证；`source_sha256=4496078f25c0cdad1cf7a5c39835fd23121e8978`、旧二进制 SHA256 `25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e`、场景和叶标签由 R83/R87 协议与运行账本提供，不能仅凭 CLI 声明从 LP 文件反推。独立审查尚在进行。真实分数 `x0`、B1/B2/aggregate 违背、四臂根界和完整求解成本尚未取得；在父任务通知唯一 solver 时段之前不得运行 `diagnose`。D7 LP 16.9 MB、50 站，单轮最多 1,225 pair × 2 行加一个 aggregate；须完整求 1 个 base LP 与 4 个同源臂，确切求解时长未知。审计实测约1.28秒，正式诊断预设整个子进程 120 秒上限，截止只记 `unknown`。聚合臂是否有新增根界、以及固定 LP 的改进能否转化为完整认证提速，均未下结论。

当前冻结工具 SHA256：`round88_ot_math.py` 为 `2b8855609cf469098d050fcd9c89efac01b2cb41ee07f023b5a7b79f9ff71840`，`round88_ot_diagnostic.py` 为 `c1cb1776d1b1eef0f03977e00060c1690e5505517d0e4baa71feb3b672fa0756`，`round88_ot_supervise.py` 为 `ea79e400d727bc94ca20c5ddfec61c3dfaaafd2e1f7d175a2fe5f4ffb8135d29`。监督脚本按独立审查意见修正全进程截止与前后 manifest 一致性，并通过无求解 mock 测试；真实 `diagnose` 从未执行。
