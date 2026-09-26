# Round88 A2 离线 endpoint 探针适配层：静态实现记录

状态：代码与微型资格测试已写，**尚未执行任何脚本、测试、py_compile、构建或真实探针**。A1 18 臂运行占用独占计时槽；须先完成独立静态审查，再由 root 发放新的微测及真实探针准入。历史 ENS-C 见证仅作离线机制诊断输入，未接入 ENS-C/A1 正式路径。

## 冻结样本与执行入口

样本和先验 SHA/场景详见 [endpoint 合同](a2_endpoint_probe_contract.md)。`scripts/round88_quantity_probe.py` 固定 D6、E8、S12；每例使用各自已存原输入与已验证 ENS-C 起点/终点见证，固定冻结二进制 SHA `23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693` 与数量流原型 SHA `fdbe04bdc7b933397aac3ec4fa9d9f0b5adf99c8550c98d14e96ce89db43328d`。`supervise` 是研究执行入口，`diagnose` 需监督器环境标志。拟执行时按预选顺序每例一次，输出路径须不存在：

```powershell
python scripts/round88_quantity_probe.py supervise --case D6 --out-dir results/unified_exact_round88/a2_probe_d6_001 --whole-process-limit-seconds 120
python scripts/round88_quantity_probe.py supervise --case E8 --out-dir results/unified_exact_round88/a2_probe_e8_001 --whole-process-limit-seconds 120
python scripts/round88_quantity_probe.py supervise --case S12 --out-dir results/unified_exact_round88/a2_probe_s12_001 --whole-process-limit-seconds 120
```

此处是**待准入命令**，不能据此认定已执行或已获求解资源。正式执行须由 root 再核命令、哈希、资格与排他槽位。

## 映射与验收

原 Parser 的完整 points 优先于文内 serialized distances；用同一 `sqrt(dx²+dy²)/1.5` 重建 double 边长，旧权重最大值 10 时缩放。适配器只支持这三份**确实具有 weights 和完整单行 points** 的固定输入，不实现 Parser 对缺失 weights/points 的一般 fallback。站点 1-based/depot 0 与 Python 0-based 映射严格往返；未访问站仍在全站 S/H/P 中，库存不变；零操作删除站而保留各车相对顺序与完整空车。先校历史 witness 与逆映射完全一致，再调用原 C++ `incumbent-import-test` 复核起点。此入口在 `src/main.cpp:9908` 导入并调用 `verifySolution`；导入失败时会退回空路线，因此适配层要求 `status=diagnostic_complete`、`incumbent_import_verified=true`、`incumbent_source=incumbent-json`、无导入错误、完整 verification flags/errors、有限 F/G/P 与源路径/结果路径/场景身份，并逐车比较返回的节点、取送操作及逐站最终库存。C++ 输出的 F 严格下降才接受；Python Fraction 目标只给梯度与内部交叉判断。

每轮由原 C++ 当前验证的 route travel 与 Python Parser 重建的完整模板旅行分别计算整数预算 floor；若整数 floor 不一致，即 `domain_uncertain_budget_floor_disagreement`，不引入经验 epsilon。当前点还须通过原型的库存、前缀负载、名义预算及固定 `1e-7` 内部物理门槛。之后调用整数负环 circulation 至无负环证书，完整记录原弧整数流、势与线性目标；primitive 段的全部整数点依次检查内部物理门槛，内部拒绝只记录而**不称已 C++ 验证**。通过门槛的每个点才生成独立候选 JSON 调 C++，记录命令、输入/候选/结果身份、退出码、原回执、stdout/stderr 和墙钟。若任何回执与候选不一致或 importer 失败，诊断立即无效并保留原始证据；不能拿回退空路线当作该点通过。严降点删零站、重建模板、继续下一完整轮；`S=0`、无方向或该线无验证改善才正常停，后两者只是启发式停机，不是全邻域或全局最优证据。

整例 120 秒由外层从预检前开始计时，包含解析、所有 C++ 子进程、图与证书、日志及输出；无内部迭代数/按例分支/每臂配额。预检结束若已届截止，**不启动** diagnose；启动后先把 Python 子进程加入 Win32 kill-on-close Job Object，完成后写 ready 标志，它在 ready 前不能发射 C++。到时关闭 Job，连 Python 已意外退出时的 C++ 后代也终止；POSIX 等价路径用独立进程组。若 Job 建立/分配失败则不放行诊断，记无效。超时标记 `unknown_whole_process_deadline`，保留运行中已落盘 `events.jsonl`、每个 candidate、C++ 回执、`result.json` 和 stdout/stderr；不自动重试或扩时。`supervision.json` 分列至首次摘要写入前的计时与写入后逾限标记，完整外部启动到退出墙钟还须由发射者独立记录。原历史 ENS-C 构造耗时与本探针成本分开；本探针内的首次 C++ 验证绝不免费。

## 静态微型资格与剩余门槛

`tests/round88_quantity_probe_test.py` 覆盖 points 优先、depot/1-based/空车/未访问站映射；有效 C++ 回执及失败 fallback、未验证导入、错误路线/操作/库存/路径/场景/非有限目标拒绝；二进制 C++ travel 在极窄预算边界引起 floor 不一致时拒绝；非 metric 删站后物理不可行不调用 C++；primitive 段全部整数点与严格改善/tie；改动 120 秒监督额度被拒绝、预检已过期时禁止启动、Python 父进程已退出时仍关闭覆盖后代的 Job。它只用微型内存夹具和伪造回执，无真实 solver/Optimize。当前这些测试**未运行**，结果只能记为待核。

后续必须做：独立静态代码审查；资源释放后运行已有 flow 微测及本适配层微测；一次最小真实 importer/结果字段微验收并检查解析与 C++ 库存、目标、旅行及预算一致；才可申请三例独占离线探针。任何 `domain_uncertain` 或回执身份失败不能据此推断 A2 效果。实现不修改原 C++、冻结 A1 源码、runner 或 flow 原型。
