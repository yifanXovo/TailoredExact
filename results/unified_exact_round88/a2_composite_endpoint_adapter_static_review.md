# A2 复合惩罚端点适配器独立静态审查

快照：`scripts/round88_quantity_composite_probe.py` SHA256 `7ded4c4ce60bf075be0f373c38a7912e7d915cae658407307c9887c87597c452`；`tests/round88_quantity_composite_probe_test.py` SHA256 `804f4ac9e14f9945cc1972285475bef6a250c9a45e4841029f1ec0e3e547a469`；`a2_composite_endpoint_adapter.md` SHA256 `f5c64dfcb26f1a5d7ebb861fbeb617dc56383a0ffbad4de2e81124ca5900f756`。三个当前文件哈希已独立重算。本审查只读，未执行新测试、脚本、原 C++ 或求解器；新 adapter 仍未准入真实 D6/E8/S12 探针。既有 composite oracle 的 6/6 无 Gurobi 微测由作者原始日志/收据证明，不属于本轮新适配器测试。

## 身份、候选与目标口径

`source_assets` 在 supervisor 启动前和 child 诊断前核冻结 binary、flow、旧 endpoint probe、composite oracle、输入和见证 SHA，supervisor 还记录自身脚本前后 SHA；目前旧 probe/composite/flow SHA 与实际文件一致。新适配器直接调用旧 probe 的 Parser、1-based 站点/depot 排除、路线到库存可逆性、原 C++ `incumbent-import-test` 和严格回执门禁：必须验证输入/方法/候选路线与库存身份、物理可行、原目标重算及 G、P、F 一致，不能把 importer 失败后的空路线 fallback 当候选。每轮的预算从当前 C++ route travel 与 Parser 的名义预算 floor 逐一核同，随后按固定路线网络域检验当前点；严格原 F 下降后删零并重建下一轮固定模板。

复合 oracle 只把 **Gini 局部广义梯度** 线性化，绝对值惩罚 `φ` 保留在有理边际费用中。`one_round` 把完整网络弧流/残量势/边际费用及取放取消的证书写入 checkpoint，再使用旧 `scan_integer_line` 对 primitive 线的每个整数点作内部物理筛查和原 C++ 验收；仅原 C++ F 严降可更新当前点，tie 停止。网络代理负差没有被误标为原 F 增益；`S=0` 返回确定性 `no_gradient_at_zero`。有限库存状态加严格 F 下降和已见状态检查支持终止，但不提供运行时间保证。

## 截止、异常与微测门槛

`supervise` 从预检前启动统一 120 秒计时，ready flag 只在 Win32 kill-on-close Job 分配 child 后写入；child 才可能启动 C++。`communicate` 使用剩余时间，超时关闭 Job 杀进程树，写 `unknown_whole_process_deadline`，保留 event、候选、C++ 回执及 oracle checkpoint；最终哈希和摘要写入越限也转 unknown。没有每轮/组件时间片、Work 或点数上限。实际完整命令退出开销不能从 `whole_process_wall_seconds` 误称全研究成本，其字段明确止于第一次摘要写入前。

首轮发现 supervisor 曾仅凭 `domain_*` 字符串把非预期退出归类为有效 inapplicable；最终快照已增加 `classify_supervision`：完成需 exit 0 + method/case，inapplicable 需 exit 2 + method/case；早期错误回执也写 case。新纯逻辑微测用伪造 returncode/status/method/case 矩阵检查这条门禁。其他新测试静态覆盖来源清单、两点整数线原 F 严降、tie 不收、非法当前点、`S=0` 和非 120 秒参数拒绝。它们**尚未运行**，也没有真实 C++ 端点回执测试。

**结论：**最终快照未见新的静态阻断，可按计划先由 root 单独授权运行新 adapter 的无求解微测与最小真实 C++ 回执资格。真实三点探针还须独立记录冻结身份、整进程成本与资源 lease；本静态审查不准入执行，不改变 ENS-C，也不预判复合代理能否找到原 F 改进。若三个预注册点仍无原 F 正面证据，按已接受提案搁置此 flow 方向。
