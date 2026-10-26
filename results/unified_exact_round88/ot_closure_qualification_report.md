# Round 88 OT 闭包：微测与零 Optimize 资格

资格结论：快速有理行与独立朴素参考、完整 pair 扫描状态分流、失败收据及真实 Win32 Job 子孙进程超时微测均通过；一个可手算的合成连续 LP 经 B1 增行后最优值由 `0` 变为 `1`。F2 root、D7 root、D7 历史 child 的**真实原 LP 只做哈希与结构读模审计，Optimize 调用为 0**，三份结构均与已冻结资格 manifest 完全一致。未生成 `ot_closure_lease.json`，九臂闭包真实 LP 诊断仍未准入。

## 冻结环境与身份

工作目录 `E:/codes/ExactEBRP`；Python `build/research/round88-ot/venv/Scripts/python.exe`，版本 `3.12.14`；Gurobi `13.0.2`。实际脚本 SHA256 `129b9224ac36e44b52fcc911604938a024d79986f8bd5fe8a8ffd6b14d1b2934`，最终测试 SHA256 `01fc21c9689f956a53adff95430cdd4ddd9bafef7bc5a56593c9d0a91bf43a61`；引用的冻结 `round88_ot_math.py` 为 `2b8855609cf469098d050fcd9c89efac01b2cb41ee07f023b5a7b79f9ff71840`，`round88_ot_diagnostic.py` 为 `c1cb1776d1b1eef0f03977e00060c1690e5505517d0e4baa71feb3b672fa0756`。共享准备 manifest SHA256 为 `6293e196160ff00e778c43be2275d8b3fe93020c5207f814dac3ce05f2a0db18`，其中逐臂固定源、依赖、300 秒外部截止、旧 rowbank 禁用及 `+1` 零 tie 明列。测试增补仅在测试文件；准备后闭包脚本与两个引用依赖字节未改。

| 冻结源 | 原 LP SHA256 | 输入 SHA256 | 实际模型变量/行/非零 | 本次结构再审计 |
| --- | --- | --- | ---: | :---: |
| F2 root | `a37e2165fb900bb0d26d9158b89ade883202049456b7d1c6180f361070638091` | `ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e` | 3,488 / 9,269 / 52,879 | 完全相同 |
| D7 root | `06275aba5e2378d719390e295654849d8868fb92fd8b0366619e1c33fa713069` | `d7dbd018331b9d5f3d84c0fd6c907560ef1fa92a2f8c153ac7d81e46a6cd4e9c` | 25,943 / 104,726 / 724,951 | 完全相同 |
| D7 child L0.0 | `27cbb486939374c3f42eb7f1e97cd6ed20281b114115118c89434fa00e85c77f` | `d7dbd018331b9d5f3d84c0fd6c907560ef1fa92a2f8c153ac7d81e46a6cd4e9c` | 25,943 / 104,726 / 724,951 | 完全相同 |

逐源资格 manifest SHA、真实 G 域、支持 fingerprint、输入/LP SHA、审计结果 SHA 与每条精确 argv 均存于 `ot_closure_qualification/source_comparison.json` 和 `source_audit_*_receipt.json`。三份新 `source_audit_*/manifest.json` 的 `structure` 与原资格文件逐字段相同，`audit` 入口只 `gp.read`、`audit_model` 并写 manifest，没有 `model.optimize`；目录内没有求解结果或 LP 求解日志。F2/D7 root/child 新审计的外部墙钟分别 `0.225069 / 1.424528 / 1.477756 s`。

## 实际微测与全部已记录成本

使用真实 venv 执行 `python tests/round88_ot_closure_test.py`，首轮 7/7 通过（`0.725673 s`）；最终文件 8 项中 7 通过、仅需要显式环境变量的 toy 测试正常跳过（`0.767867 s`）。无 Gurobi 的 `_scan` 测试分别实测新行、已有行仍可靠违背、正但低于余量、无观察正违背四态；准备失败的合成子进程返回码 7，仍写完整外层收据。真实 Win32 Job 测试在 ready 握手后启动 Python 子/孙进程，使用生产 `_wait_with_deadline` 的 `0.2 s` 微截止，确认超时及整树终止。纯有理朴素重扫、极端符号枚举和快速前后缀对照全部精确相等，测试覆盖重合率、异质 target、零质量、三种零 tie、等宽与窄宽域及 64 组可行端点耦合。

显式环境 `ROUND88_OT_CLOSURE_TOY_OPTIMIZE=1` 只对 `-k hand_calculated` 合成测试启用；两次有意运行均通过，外层墙钟 `0.181524 / 0.178371 s`，各有 **2 次 toy Optimize，合计 4 次 toy Optimize**，真实三份 LP 的 Optimize 始终为 0。玩具模型固定一站比率为 `0`、另一站为 `1`，目标 `min h`，原值 `0`；新增完整 B1 行为 `h−state_1_0+state_2_0≥0`，独立手算与实际增行后均为 `h=1`。原始行违背 `1`，沿用既定 `reliable` 算出的余量 `10⁻⁶`，比值 `10⁶`；toy 原始/增行 LP、Gurobi 日志与结果在 `ot_closure_qualification/toy_gurobi_final/`。真实三份 LP 未产生 primal，故**没有真实 LP 的违背或最坏数值余量可报**；不以 toy 余量替代。

`prepare-supervise` 完整外层命令墙钟为 `0.3251317 s`，见 `prepare_command_receipt.json`；嵌套 supervisor 发射准备子进程至退出为 `0.1216254 s`，内部准备计时 `0.032294 s`，后二者只作分解，不重复相加或替代完整成本。manifest 与失败收据均保存。上述两次纯微测、两次 toy、一次共享准备、三份真实零 Optimize 审计的八份外层命令收据合计 `5.3059186 s`；后续人工比较与本报告编辑另耗时，未冒称封顶总研究成本。每次完整命令或 argv、退出码、外部墙钟和原始控制台文本在 `ot_closure_qualification/*receipt.json` 与相邻 `*.log`。本阶段无真实失败或重试；第二次 toy 仅因增补余量字段后对新测试版本复核，保留两次证据与 4 次 toy Optimize 成本。原报告把嵌套的准备耗时当作完整耗时；独立审查指出后，root 根据原始收据重新求和并修正此段，未改变运行数据。

资格仍限于微测及零 Optimize 读模。真实 LP 的数值残差、逐轮闭包结果、300 秒截止行为和相对 ENS-C/P-GRB 的完整算法价值均须后续九臂如实诊断；任何截止只记 unknown，不作认证或选型结论。
