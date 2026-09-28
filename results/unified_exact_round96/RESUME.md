# R96 恢复与复现

唯一源码目录`E:/codes/ExactEBRP`，分支`codex/round96-external-primal`，base为`codex/round95-full-block-descent`。保护旧dirty三文件与历史raw；不`git add .`、不清理、不重开完成生产器。Python为`D:/msys64/ucrt64/bin/python.exe`。每次继续先核活动进程及新账本，禁止重复启动已有destination。

1. 读`final_report.md`、`fixed_route_report.md`、`multi_quantity_decision.md`及用户原Round96完整要求。阶段1完成不等于整轮完成，目标保持active。
2. `round96_prepare.py freeze/generate/recover`均已运行一次，不再重跑。生成规则先提交d5e743717，六输入及六ENS/三P参考见证保留。
3. `round96_fixed_route_qualification.py`和六次`round96_fixed_route.py <id>`已完成；禁止重跑。`round96_analyze_fixed.py`已逐行重算返回向量、核物理与索引。审查完成结果应读既存JSON/CSV，若另作分析必须新输出，不覆盖。
4. `round96_multi_diagnostic.py`已完成六例，三/四站线原型停止且不接入。构建`build/research/round96-multi-quantity`、源码及微型测试保留。下一研究方向是F5固定归属放松顺序的300秒独立诊断（先定义模型/资格），随后依据证据实现有限路线邻域。不要再换二维数量方向。
5. `round96_external.py prepare`已完成：六参考零Optimize，166个R90源码blob绑定，identity在`external/identity.json`。正式18臂尚未启动，需先保存绑定该identity的`external_admission.json`。每臂命令：`python scripts/round96_external.py run --number N`；N须为下一未启动编号。runner拒绝已有目录或不完整前缀，不自动续跑/拼证据。一次完整长运行复用早期检查点；不要重跑short先筛选。
6. 已有检查：`round96_numeric_inputs.py`通过，边界详见numerical_scope；`round96_old_ledger.py`有效结果是v2，v1保留为提取器字段错误记录。
7. 全部性能串行、亲和mask4，禁止与构建/归档/重审计争CPU。可在求解期间准备文稿与源码，实际执行等计算槽空闲。若用户或额度中断，记录实际exit/最后committed时点，不能把cap当cert时间，不主动扩大到24小时。
8. 总预算72次、native micro≤4。阶段1保守20次（14试验+6纯建模），Optimize7次；后续按实际launch台账累计，嵌套时间不重复。18外部正式臂、结构诊断/原型开发/长配对与两独立验证仍需预算。

阶段1压缩包逐member索引可离线复核，保持原始日志和见证。重新复现实验须新明确目录并计入授权预算，不能复用同输出路径；普通验证直接重算保存证据而非重跑优化。
