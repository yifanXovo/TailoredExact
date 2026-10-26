# R94 正式批首次尝试：F2 第二臂审计停止

**状态：正式批已停，后十臂未运行。** Root 绑定恢复身份和四资格的单独正式 lease 后，仅执行一次 `scripts/round94_lpg_contemporary.py run`。独占槽预检为空；完整外层 PowerShell 发射至真实退出 **1442.5685015秒、exit 1**，见[外层收据](formal_outer_receipt_v2.json) SHA256 `b189940f50ea212089f11188ec147813e12b6c9206a4a156e4e5de7512d2ef58`。原始 stdout/stderr、两臂 raw/journal/ledger 和[失败前缀](runner_lpg_contemporary/recovery_v2/formal_completion.json)（SHA256 `0c46a735be0f52d1864e3a593af2b0d89f2e2ec5a7460829e671083965a44e50`）均保留；无重启、延长、源修改、归档或后续 native 调用。

| 付费臂 | 实际完整进程秒 | 进程退出/当前证据 |
| --- | ---: | --- |
| F2/P-GRB | 897.1720000003 / 900 cap | 正常 exit0、审计 PASS。原问题物理 U=0.8659435203229894、合法 L=0.7577452455123087、gap=0.10819827481068067；未认证。 |
| F2/ENS-C | 544.2650000001 / 900 cap | 正常 exit0，**新 adapter 审计 FAIL，endpoint 暂记 audit-pending**。result 原文报告 `status=optimal`、`upper_bound=0.8659435203229894`、`lower_bound=0.865943520322989`、`strict_certified_original_problem=true`，但不能在审计未恢复前作为已确认结论。 |

两进程实际完整 wall 合计 **1441.4370000004秒**，已嵌于外层1442.5685015秒中，不相加。旧 F2/P 与新 F2/ENS 在同一冻结二进制、原输入、seed0 下运行。runner [summary.jsonl](runner_lpg_contemporary/summary.jsonl)含两条实际启动记录；其第二条 `audit_passed=false`、`endpoint=null`。正式 completion 记录 completed=1、attempted=[1,2]，未启动 F2/LP-G 及 C20/B50/U6 的全部臂，共十臂。没有任何 LP-G 正式结果，故不能据此作三臂性能结论。

两臂关键字节锚：P 的 completion/audit/result SHA256 分别为 `a3dbe14ab4ca46204f8a616853f40f035a2d9b1785b64480493a4df82eef250c`、`60791dca51d3978f92263d01ca777053ab777a20b5a89a577e3f1fe8c97fde2c`、`73cd0c3c0d59b515001f60a12e10a1246660b9d42113619dc0dfcf692f23ee29`。ENS 的 completion/audit/result/observations 分别为 `f3a56a73283e71d1c9e120ad3035159aacd54d15ea745ee27f6fc9c75537ba6a`、`3cef8982ecedec3d1f1c4bf2dc66a8443b41a2069622e91aad12965821659abe`、`82de9f47a6a6336ce5e16a3e69ecd586ffa6c5362895dad2d077352086d7d6b7`、`6a84231ba695fa214cc7bd3c9e3cd095ac05101a36f746de23c2c9f9eb7998ec`；[失败收据](runner_lpg_contemporary/failure_02.json) SHA256 `71dbac701a2478950592d150e90993cc663e48e1ddcc419796b03362bc8d59ec`。后续恢复须对完整 raw/ledger 再做逐文件不可变清单。

直接停止原因是 adapter 在进入冻结 R90 旧审计前，对**每一个** native call 强制 `native_preconditions` 为 true。F2/ENS 的五条已提交 call 中，第1–3条对应 `paper_optimize_ledger.csv` 的 LP 解，第4条是 CHILD_BOUND_TARGET_MIP，第5条是终结 MIP；前3条按冻结 `GurobiBaseline.cpp` 的 `!out.lp_relaxation` 条件写整数0，后2条写整数1，五条的实际 `settings` 均与预注册 native 参数/容差字典相同。新适配器遇第1条0即报 `AssertionError('native parameter/domain preconditions failed')`。这是**审计适配断言与合法 LP 调用作用域冲突的候选工程诊断**，不是已判定算法/模型故障。前3条 false 不得被当成完整原问题 native MIP 界；冻结 R86/R90 作用域审计负责只承认有合法覆盖和参数前提的全局界。

只读初查对保留 ENS `observations.json` 直接调用冻结 `round90_lp_g_g3.audit_launch`，其旧读器报告审计 PASS，给出一个**待独立复核**的原问题端点；另对 result 调用 v2 `parameter_readback(require_call=True, arm='ENS-C')`，五项 set/get 全通过。由于新 runner 当次正式 `audit.json` 仍是 FAIL，本文在数学代理复核完成并由 root 审定恢复前，不把旧读器离线产物改写为正式已审计证书，也不推进 LP-G。可接受的窄修方向是仍逐条核 settings 与0/1类型，却不强迫 LP relaxation 的 native MIP precondition=1；P 原模型 call 必须保持真，原 R86/R90 bound/coverage/finalize 和 ENS/LP 的正常返回五参数检查不能削弱。任何续跑须另行冻结修复源/前缀身份并获 root 明确授权，且只允许未启动的十臂；已付两臂不能重跑或双计。
