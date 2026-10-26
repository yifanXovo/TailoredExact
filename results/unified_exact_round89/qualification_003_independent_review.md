# Round89 native B1 第三批 toy 资格独立验收

**结论：在预注册 parity toy 的 API／后端接线范围内通过；可交由 root 决定下一阶段的独立准入。** 这不是实际实例有效性、证明加速或物理可行解证书。审查只读，未执行测试、构建或求解。

身份与执行：lease SHA-256 `a9c623a7d80dd55579bff230d80c711c5894cfa85d3db924cdc026e52e26d72b`；Micro 源 `7669dd38992d238737b5a6d0e5f8a042e0458b5036d8bab070ca1dc29fbcd279`、可执行文件 `9d268d10a6ab044869ff138bbc87c450997156e4bb7d183a3b7e011656f8b5d8`。前后身份收据逐项匹配九份源码、两份二进制；四个命令均一次退出 0、无超时，原始 37 项文件索引的字节数与 SHA-256 全部匹配，事后进程检查为零。`Fraction` 收据报告 54 个整数点检查，其中 36 个覆盖真实舍入乘积提交行。单个 native 命令只含原定六臂 Optimize，外层进程 0.093 s；四命令外层 wrapper 累计 0.501 s，native 已包含在其中，不能再加一次。这只是四命令计费，前后身份检查与归档的整个时间跨度另计。

直接三臂的原模型 SHA 均为 `2ebb963135e5161cdfa6a866227721f0c46b1604bfeeee6845d1ba1bd19931fb`，静态臂另存加行模型。off/static/callback 均报告数值 OPTIMAL、目标 1，各自保存 30 列原始 primal；十条原始行、变量界、整数性最大残差均为 0，静态臂所加行残差亦为 0。奇偶支持使任何整数库存差至少 1，原 LP 中 `h=0`、两站均值 1 的分数点说明目标 1 可手算。callback 的实际首个分数节点为站一 `0.75 state_1_0 + 0.25 state_1_4`、站二 `state_2_1=1`；所存 B1 行活动为 −1.5、可靠违反下界约 1.5，严格超过实读 `FeasibilityTol≈1e−6`。实读 `IntFeasTol≈1e−5`，3 个分数 selector 节点均有可靠行和 `GRBcbcut` API 成功，`PreCrush=1`；不存在只靠预设 0.5/0.5 点触发的解释。

真实 `FixedIntervalMipBackend` toy 接线的 LP 负控未激活 B1，保存 30 列 primal、原行残差 0、数值目标 0。terminal 和 partial MIP 均审计原模型 10 行/1 站对，`PreCrush=1`，各有 3 个最优 MIPNODE、3 次可靠分离及 3 次 API 成功，`numerical_skips=0`；日志均有根 LP 目标 0、`IntInf=2` 和 `User: 3`，与摘要相互印证。两臂数值 bound 约 `0.999999999999985`。`submitted_api_ok` 只证明回调 API 接收，不能单凭此断言每条 cut 永久留存；这里的日志提供了聚合层面的 User cut 观察。

证据边界：后端 MIP 的冻结接口未导出原始 X，故没有独立 toy MIP primal/原行或物理证书。其 raw outcome 的 `incumbent_objective=0` 来自通用路线重建/物理 verifier 字段，不等于本 toy 的 `min h` 最优值 1，也不得被引用为 toy 见证；toy 整数见证应只取直接三臂原始 primal。六臂没有实际 EBRP 实例，不能据此断言 ENS 证明时间、根界或原方法目标改进。
