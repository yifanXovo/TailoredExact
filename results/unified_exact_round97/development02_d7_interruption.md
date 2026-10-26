# D7 P-GRB：硬截止中断与受限继续

原登记第5臂P-GRB于3598.031秒被whole_run_hard_stop终止，returncode1，仍在3600秒共同进程cap内。原命令请求原生TimeLimit3594秒、共同收尾余量3秒，supervisor硬截止3598秒。最后原生日志到3594秒，尚无正常native返回；不能从日志精确判断内部未返回的原因。未修改参数、重跑、延长预算或伪造result。

305条已提交日志经独立原物理/全局界/参数/原compact模型身份审计通过。中断时可审计U=.2372849915487284，L=.19858649317712468，gap=.03869849837160372，未认证。235条物理见证、68个全局界记录、1个观察到的native call且0返回。完整Optimize总数未知；不将观察调用自动当已完成Optimize，也不把中断端点当normal finalized端点或认证时间。

原queue_d7/session78483在normal-only前缀断言处退出1，这是保护性停止；第6/7臂均未启动。原事件、状态、completion/audit/observations均保持。hard_stop05_acknowledgement.json绑定这个确切中断、LP与失败队列哈希。全3598.031秒计费；成本快照costs/development02_d7_interrupted包含本臂及此前失败，不重复加等待。

独立第三视角只读复核后认为可继续原登记的6OFF/7FEEDBACK，不需要重跑5。新脚本round97_continue_development02.py只允许已登记的三个后续块；前缀中唯一例外是已绑定的第5臂。其余已完成臂必须正常且audit通过，ENS向量receipt必须匹配唯一已保存队列审计哈希。新启动必须使用原命令、顺序、cap、构建和从不存在的目标目录；任何新的中断或失败再次停止，不自动放行。语法、真实五臂前缀、既有向量receipt与checker入口检查已通过，0Optimize。

此继续只推进尚未执行的实验，不恢复被终止的原生树。D7分析需使用明确支持中断的分析版本；当前normal-only角色分析不可套用。只用实际保留证据，不能制造缺失result字段。共同授权窗口内的删失质量可以报告，但要同时标明P是硬截止中断，其他臂若正常则为正常限时，认证排序保留未知。最终阶段结论仍需另外开发角色和冻结确认。

后续命令（执行前检查真实进程与目标目录，绝不重复）：

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_continue_development02.py --completed 5 --through 7
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_continue_development02.py --completed 7 --through 10
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_continue_development02.py --completed 10 --through 13
```

每块结束后先审计解释再开始下一块。旧normal-only队列不能越过已如实保留的第5臂，不要修改旧receipt以绕过它。
