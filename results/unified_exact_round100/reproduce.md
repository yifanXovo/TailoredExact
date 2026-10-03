# Round100 复现与证据入口

R99 stacked base：`a11fbcdc9bbea4f5ee716c6e49df4e0fb4755dcd`。
公共物理界检查修复：`56866033e2d0407ffa57b1b0de255a744c01babc`。
实际共同生产源码阶段：`b5d6d83bb8fc74682de6f1f6862c2e687712f4cf`。
交付之后的协议/分析/报告提交没有改变该生产源码或性能helper，不能把交付head称为旧R99实测版本。
交付增加Git字节保留属性，并重暂存原baseline/开发协议/protocol/Start reader的实际换行字节，
使Windows checkout保留记录SHA；这只修正仓库存储与checkout行为，未改变实测文件字节或算法。

## 无求解器的复核

- [runs.csv](complete_results_final/runs.csv)、[pairs.csv](complete_results_final/pairs.csv)：24个真实完整臂，8已证、16正常删失。
- [physical_witness_events.jsonl](complete_results_final/physical_witness_events.jsonl)：全部合法见证及原事件SHA；
  `endpoints/`保存终态路线、完整作用域审计、参数回读和完成回执。
- [native_calls.csv](complete_results_final/native_calls.csv)、[native_structure.csv](complete_results_final/native_structure.csv)：
  actual Optimize及native日志可见结构；日志的rounded call-relative数值不是精确全局轨迹。
- [measurement04](measurement04/summary.json)：covered检查点、t_find的安全宽区间、完整认证完成边界、
  至完整完成的尾部区间及另列的journal发布/观测里程碑。后者不表示更早的native发现/认证瞬间。
- [evidence](evidence/native_log_redactions.json)：冻结campaign identities、summary、有限资格/真实Start reader、清理后的必要native日志。
- [local_artifact_index.json](local_artifact_index.json)：实际本地LP、逐列Start、二进制、完整原日志/事件的SHA与范围。
  索引不是恢复文件或独立搜索复现；仓库紧凑提交不包含这些大文件。

仓库输入、路线及事件足以另行重算物理库存、载荷前缀、时长和目标。检查原完整native矩阵或重新运行
原只读作用域工具，需要索引中的本地原文件；没有这些字节时不声称已恢复或用重新生成的模型替换实际模型。
本地原文件齐全时，可用新的独占标签重新提取（0 Optimize）：

```powershell
$r100Py = 'D:/msys64/ucrt64/bin/python.exe'
& $r100Py scripts/round100_results.py replay_results01 development01 certification_CF01 certification_N201 holdout01
& $r100Py scripts/round100_measure.py replay_measurement01 development01 certification_CF01 certification_N201 holdout01
```

原 failed `engineering/measurement01`及旧成功的measurement02/03均保留本地。
measurement01是0-native只读字段重复错误；measurement03更正覆盖记录计数，最终measurement04
按独立审查分开native事件安全区间与记录里程碑，原性能记录没有改写或重跑。
端点audit.json的旧explanation中“interrupted endpoint”指prefix审计合同；实际normal_return与证书
以completion.stop_reason、endpoint.certificate、normal_result_certificate为准，本轮无行政中断臂。

## 同环境完整复测

Windows、GCC14.2 UCRT64、Ninja/CMake路径见 `scripts/round100_common.py` 及engineering构建launch。
实际 `build/research/round100-quantity-v1/ExactEBRP.exe` SHA256：
`fd2a30ea0bdba13dda7c19ee69e8c1f7f874482f3dad7cb2c1df48c4d7404f64`。
同版本源码重新编译未保证PE字节/SHA相同；新构建必须建立新manifest，不冒充本轮binary。

生产DLL固定 `D:/gurobi1302/win64/bin/gurobi130.dll`，SHA256：
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。
原生资格使用 `build/research/round88-ot/venv/Scripts/python.exe`。
`round100_gurobi_runtime.py`先加载该DLL并核对唯一加载模块；不能把另一wheel的相同版本号等同相同DLL。
许可证配置由本机环境提供，没有提交许可证或凭据。

以下是本轮实际driver顺序。已有输出均为exclusive，不能在原工作区覆盖/重跑。
复测应使用独立checkout及新的构建/结果空间，保留原输入/共同cap/顺序，并准备同样运行时。
例如在本机独立checkout中，仅在目标尚不存在时建立现有native Python依赖的junction：

```powershell
New-Item -ItemType Directory -Path build/research/round88-ot -Force
New-Item -ItemType Junction -Path build/research/round88-ot/venv -Target 'E:/codes/ExactEBRP/build/research/round88-ot/venv'
```

这些命令仅准备依赖，不导入旧Start/见证。当前交付已有角色协议和H100输入，
无需重新运行只适用于原R99起点的 `round100_setup.py`，也不能重新生成已观察H100后称新holdout。
新checkout的raw campaign/qualification目录必须尚未存在；`prepare`重新绑定实际新构建/输入/源码/helper，
每臂从头运行且自付费。严格复测保留本轮选定M-B及原共同cap，不重新调优/选模式。

```powershell
$r100Py = 'D:/msys64/ucrt64/bin/python.exe'
& $r100Py scripts/round100_build.py reproduction_build01
& $r100Py scripts/round100_stage1.py

& $r100Py scripts/round100_campaign.py prepare development01 results/unified_exact_round100/development_inputs.json
& $r100Py scripts/round100_run_batch.py development01 1 2 3 4 5 6 7 8 9 10 11 12
& $r100Py scripts/round100_after_development.py

& $r100Py scripts/round100_campaign.py prepare certification_CF01 results/unified_exact_round100/certification_CF_protocol01.json
& $r100Py scripts/round100_run_batch.py certification_CF01 1 2 3 4 5 6
& $r100Py scripts/round100_campaign.py prepare certification_N201 results/unified_exact_round100/certification_N2_protocol01.json
& $r100Py scripts/round100_run_batch.py certification_N201 1 2 3
& $r100Py scripts/round100_campaign.py prepare holdout01 results/unified_exact_round100/holdout_protocol01.json
& $r100Py scripts/round100_run_batch.py holdout01 1 2 3

& $r100Py scripts/round100_results.py reproduced_results01 development01 certification_CF01 certification_N201 holdout01
& $r100Py scripts/round100_measure.py reproduced_measurement01 development01 certification_CF01 certification_N201 holdout01
```

本轮的 `round100_freeze.py`、`round100_holdout.py`、`round100_prepare_n2.py`已分别执行一次，
保存了候选、一次输入生成及N2事前资源决策。它们是原阶段构建历史，复测直接使用所保存协议；
不能覆盖原冻结或根据复测结果改变算法。本轮全部33计费启动/67471.797406外层秒的账本在
[cost_failures.csv](complete_results_final/cost_failures.csv)，内部99 Optimize不另加费用。
复测本身需要另行预算，不属于已交付的计费次数，也未在独立只读复核中执行。

生产数量开关为 `--round100-continuous-quantities`（ENS-Q），M-B沿用
`--round98-state-service m-binary`。不能仅给裸命令加开关后称已复现完整实验；完整准入、原ENS preset、
数学T、24+1自付费启动、VD-P/AM/native参数/时限和normal closing均由上述冻结driver规定。
P命令由同一driver保持原compact/no-Start/default，不通过研究开关修改基准。
