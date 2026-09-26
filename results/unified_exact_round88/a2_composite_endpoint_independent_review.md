# A2 复合惩罚三端点独立只读验收

范围：核对冻结 adapter/test SHA、资格日志与 E8 原 C++ importer 回执、D6/E8/S12 三个原始输出目录的外层收据、监管、结果、events 和 **14 份**候选/原 C++ 回执。不运行测试、原 C++、求解器、重试或新的端点诊断。作者报告 `a2_composite_endpoint_diagnostic_001/report.md` SHA256 `b842e843f1f10b5434deee8284d2256505826a5ffab36a389a2e68b9dc83e4c9`；adapter `7ded4c4ce60bf075be0f373c38a7912e7d915cae658407307c9887c87597c452`、test `804f4ac9e14f9945cc1972285475bef6a250c9a45e4841029f1ec0e3e547a469`，本轮独立重算相同。

**资格与身份。** 新 adapter 微测原始日志为 6/6、exit 0，外层 `0.1682968 s`。单独的 E8 importer 资格外层 `0.1887649 s`、exit 0；原 C++ 回执与 helper 的 `qualification.json` 均为合格，其 C++ 调用 `0.0487138 s` 是嵌套成本，不能重复相加。先前 composite oracle 自身 6/6、外层 `0.2646866 s` 属另一资格证据。三诊断的七类 preflight/final SHA 均逐项相同，含原二进制、flow、旧 probe、composite、新 adapter、固定输入和见证；方法和 case 与各自监管/结果一致。

**三例观察。** D6/E8/S12 各一次，外层 exit 均 0、监管/child 均完成、`timed_out=false`，各只完成一轮；C++ 调用数分别为 `2/10/2`，即初始见证各一次加 primitive 线全部 `1/9/1` 个候选，内部拒绝数均为零。三轮代理差均为负，证书字段保留边际弧、取放投影、整数成本尺度、弧流和残量势；这仅证明所选固定路线**代理**的流最优，不能推出原 F 下降。逐一检查 14 份 native 结果：均为 `incumbent-import-test`、`diagnostic_complete`、import attempted/verified、`incumbent-json`、无 import/verification error；路线节点与操作按字段规范比较后与提交候选完全一致（原 JSON 键顺序不同不影响身份），物理可行与原目标重算等原 verification flags 全真，回执 F 与 import F/verification F 相同。events 中每例 `cpp_verify_started/finished/cpp_candidate_accepted_by_verifier` 数也分别为 `2/10/2`；这里的 `accepted_by_verifier` **只表示 C++ importer 与物理/目标验证通过**，算法接受原 F 严降的次数在三例均为 **0**。

14 份回执的顶层/verification 最终库存、目标分量 `F≈G+0.15P`（既定 `1e−7` 口径）及结果路径亦核同。原 C++ 初始 F 分别约 `0.1575098036 / 0.0222955975 / 0.0585639731`；非初始候选的最小 F 约为 `0.3599279588 / 0.0223259047 / 0.1694946353`，无一严格较低。三份 `result.json` 的终止理由都是 `no_verified_improvement`，最终库存与原库存逐项相同，最终回执指向各自 `candidate_00000_result.json`，原/终 F、G、P 一致。故报告“复合惩罚代理负差仍未救回三个预注册点”的结论有真实原 C++ 证据支持；不能把代理改善、Python Fraction 目标或 importer 成功本身当原 F 改善。

三例完整外层墙钟 `0.4542073+0.7898462+0.4075838=1.6516373 s`；监管内层分别约 `0.326315/0.661073/0.274084 s`，是外层的一部分。三个案例均远未触及统一 120 秒 whole-case 截止，因而不是 timeout unknown；内存未采样，不给峰值结论。微测、E8 资格和先前 oracle 资格成本须另列，不作免费历史启动。

**验收结论：** 证据支持三例均完整、物理及身份有效、无原 F 严降。按已接受的一次机制跟进决策，搁置该 quantity-flow 方向，不扩实例、随机重启、调参数或改 ENS-C 正式策略。本离线结果不证明其它端点不可能获益，也不证明完整方法速度或认证质量。
