# R94 四个原模型 P-GRB 身份资格完成

四个**诊断**资格现均通过：首轮已付 F2 由 v2 离线重审，随后 C20→B50→U6 在 root 新 lease 下各启动一次。F2 没有重跑。没有正式三臂运行；四例诊断搜索值全部排除正式面板。冻结 R90 可执行文件 SHA256 `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`，v2 runner `02f78bba3397462f47b04f6ecec486ce739533e944948099c5773d18562c935a`，recovery identity `0e14383b87d61a22d7b05c51a33b0ee0d1e2d1994c482c6bc00515d391488fea`。F2 首轮审计器 `is True` 类型故障和完整已付前缀见[attempt 1 报告](qualification_attempt1_report.md)；v2 只离线修读数并保留原 F2 15件文件，未额外调用 F2 Optimize。

| 角色 | 实际原生进程秒（15秒 cap） | compact.lp SHA256；原 fingerprint；列/行 | 结果 / 审计 |
| --- | ---: | --- | --- |
| F2（原已付） | 0.2920158999 | `ad2ac9af96e732b9407acc39dc7a21922e092e7dd9c7d05d32513ac1ac52a23d`；788240696；1591/3689 | 原 result `314b4b7d0426fdedc31a201a10da0d0c948c5fbe4288028fd4222ce5908e9e95`；v2 离线 F2 audit `e8c8fdfe1a7492d8594aa3adc795290fb34fd18df0d29cd5a1a08c8218a41af4` |
| C20 | 0.1679954003 | `905b7e8b154b218e446b0e116f6035acd2c6b03431e910e1d0040b7171c07cc0`；1303462215；1551/3629 | result `0386f63c6b3af6796a705794d9d248a71e71c1fa895932e32308d3c7a0b42a72`；audit `06657bb17f228d6506a286c274ee78388914891f67bbdf3904c0d98aaec34f61` |
| B50 | 1.0294031999 | `0a88f594dc64ecdcd86712d8b0584b0c1bf3fe22982f35176033bbcc2d5b6b7d`；−250521169；13360/35618 | result `07bfee6debf36fcb84149e3ebe8096d2d788332b057aecec1890451048b22c77`；audit `0282d686d296ab83c9f1b4a28bd8fbbac182b806a5e2b6e5d65f58b2860b8f40` |
| U6 | 1.0469805999 | `5979ffe9f6524c2dcddb705910e1e8b6002382b3fb1ddeb8712ebfb852082998`；1831047900；13340/35588 | result `baa7d434f5467609fb1a867c914dc5f74096ed37b32a96224217d540cc12b967`；audit `19d0f2f19656d0014b4ecef74fbd9e73c6c520cb7c2339bc386ddb36aa0c6b57` |

四份 compact.lp **全文件 SHA** 均与冻结 R87 原模型祖先逐字相同；native fingerprint、维度及变量域检查通过。四份 result 均为 `method=gurobi`、`algorithm_preset=custom`、HGA start=false、Gurobi 13.0.2、原生 lifecycle=true、strict gap parameters=true、Optimize count=1/return code=0。各例 Threads 1、Seed 0、Presolve −1、MIPGap 0、MIPGapAbs 0 的 requested/effective 与预注册一致，十个 set/get 返回码均为0。每例 committed journal 依次恰 identity/call/returned 三事件；call 的 `full_original=1`、`native_preconditions=1` 是 native JSON 整数编码，不是 Python bool。四次都经冻结 R86 `receipt` 与 `audit` 独立只读重放通过：call started/returned 各1，物理见证0、global native bound事件0、分析性 LB=0、UB未知。诊断没有可用的正式 U/L 或证书。

真实新批[资格 completion](runner_lpg_contemporary/recovery_v2/qualification_completion.json) SHA256 `d137c882b83998bbf0b5557543b9e7c54edea16656399b261cabed64244f0246`，记录 remaining completed=3、passed=true、not_run=[]、四身份合计核验4次 Optimize。PowerShell [整次外层收据](qualification_recovery_outer_receipt_v2.json) SHA256 `e39521e070c648687f08a32af5dbd82f14284fc2fcef1436ba9291e9ef218f88`，从命令发射至真实 exit 0 为 **3.4592577秒**，stdout/stderr 均为空。旧 F2 批外层 exit 1 为 **0.9559593秒**；两次资格 Python 整调用合计4.4152170秒（不同批，直接相加）。四个实际原生进程合计 **2.5363950999秒**，已包含在外层调用内，不能与4.4152170秒相加。两次零 Optimize 准备外层另为1.066536秒和0.464768秒；四个步骤全外层合计5.946521秒，未含独立人工/离线复核开销。未使用任何15秒 cap 代替真实成本。

至此，**四资格身份/参数门 PASS**，仅说明同一冻结二进制能在四个原输入上实例化相同 P compact 原模型并真实设/读回参数。它不比较 LP-G 性能，更不授权正式运行。正式12臂仍须独立复核本报告和恢复前缀，并由 root 创建绑定 v2 recovery identity 与本次 qualification completion SHA 的新正式 lease；没有该 lease 时 `run` 不得启动。

独立数学/证据代理另行逐份核对了保留的 F2、余三 raw、v2 类型修复、R86 journal 重放及四层费用，并给出独立 PASS，见[独立复核](qualification_independent_review.md)（SHA256 `2cf9611db363e121b3f92fafb5fd01a62a73a25603720d276fdc002ef4f45bbe`）。
