# Round88 A2 endpoint 适配层独立静态审查

审查快照：`scripts/round88_quantity_probe.py` SHA256 `6a06a03212dc5da954be57e7c81b5a0f67c77bea592720955dc9c2b8e3c9c77c`；`tests/round88_quantity_probe_test.py` SHA256 `3e0e3ec890d5135665a8f7f2ef892c2f9261b96383576f2267f9c5b4d2a26b11`；实现说明 SHA256 `35e2d020c46451448da1dadffc6a7ac82853099f3f3991219229de30aa9eb9b7`。哈希由作者冻结通知提供；本审查未重新计算。最后一次脚本改动仅同步超时摘要的 `timed_out` 布尔值，已静态复核。结论：**限定三份固定输入的适配接口静态通过，未准入真实探针**。A1 占用计算槽期间未执行脚本、测试、编译、模型或大文件校验。

## 核对结果

- 固定 D6/E8/S12 的输入、见证、二进制、数量流 SHA 与场景参数。`parse_instance` 按 `Parser.cpp` 的 points 优先和 `sqrt(dx²+dy²)/1.5` 重建旅行时间，legacy 最大权重 10 时只缩放站点权重。三份固定输入均有完整单行 points 和 weights；一般格式 fallback 不属于此探针。站点在原 C++ 用 1-based、depot 为 0，Python 内部减一；depot 不进入全站 Gini/penalty。`canonical_routes` 要求每车恰一条、唯一访问、操作与节点一一对应，完整空车 `[0,0]`；历史见证必须经库存重建往返一致。删零后保留各车相对顺序并重建下一轮模板。
- `cpp_verify` 每个候选另写 route JSON，用冻结原 C++ `incumbent-import-test` 验证。`validate_cpp_receipt` 同时要求导入标志、`diagnostic_complete`、`incumbent-json` 来源、无导入/验证错误、所有物理与原目标标志、逐车路线/操作、逐站含 depot 库存、输入/结果路径及 T/取送时间身份、有限且相互一致的 F/G/P。故 `main.cpp` 导入失败后的空路线 fallback 即使物理可行也不能冒充候选证书。每个通过内部门槛的整数 line 点调用 C++；只用其重算 F 的严格下降接受，tie 不动。S=0、无方向、无验证改善均为启发式终止，且严格下降加有限整数库存状态、`seen` 防循环给出有限终止。
- 每轮从当前 C++ 回执读取实际 route travel，用其和 Python points 重建旅行分别计算整数名义预算；floor 不同即 `domain_uncertain`，没有经验 epsilon 扩张。当前点须在名义网络域及内部物理域；每条 primitive 整数线逐点作内部物理过滤，通过者才发 C++。内部过滤在浮点边界可能漏掉原 C++ 可行点，因此 `no_verified_improvement` 不表示完整原问题邻域最优，文档已有该限定。
- 外层 120 秒从预检前计时；预检已到期不启动诊断。Windows 子进程先加入带 `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` 的 Job Object，再写 ready 标志；诊断进程在 ready 前不能发 C++。超时或异常关闭 Job，覆盖 Python 父进程提前退出而 C++ 后代尚存的情形；POSIX 用独立进程组。每个 C++ 调用的候选、命令、回执、stdout/stderr 和墙钟分别落盘；超时标为 `unknown_whole_process_deadline`，未变成正式选型。后置哈希与摘要写入后的越界复核亦有处理。

## 尚待运行的资格门槛

本次只是阅读源码。作者新增的模拟预检过期与父进程退出后 Job 关闭测试，以及原有映射、fallback、预算窄边界、删站、严格 line 改善测试均**未运行**。资源释放后应运行这些无求解微测，特别做一项真实 Win32 子进程树超时试验，确认 Job 分配、ready 握手、关闭 Job 后 C++ 子进程确已终止；伪造 Job 的单元测试不能替代 OS 行为。再做一次最小真实 `incumbent-import-test` 字段/路径/旅行/库存/目标交叉验收，方可申请固定三例离线探针。发射者还需另计完整外部启动到退出墙钟；脚本摘要的计时边界在首次 `supervision.json` 写入前。

未发现需改变 A2 数学方向或阻止上述资格测试的静态缺陷。静态通过不等于运行通过，也不把离线改善认作 ENS-C 正式多实例优势。
