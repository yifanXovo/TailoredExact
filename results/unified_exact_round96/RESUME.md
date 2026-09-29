# R96 恢复与复现（2026-09-29）

E:/codes/ExactEBRP，codex/round96-external-primal，base R95；保护原三份dirty文件和所有旧raw。不清理、不git add .、不重复启动已有destination。Python D:/msys64/ucrt64/bin/python.exe。目标active，完整用户要求见附件；读final_report.md。性能严格串行mask4，不与build/归档/重审计争CPU。

此前诊断/资格全部完成且不得重跑：固定路线六例、第一数量原型六例、自由顺序资格/F5_final、重排微例及六例、965见证/85移动oracle、四个CLI门禁、所有输入生成及零Optimize参考导出。两个native micro已用，六新外部输入和V1/V2全部固定保留。旧三/四站数量分支否定，新有限重排默认关闭。

外部summary.jsonl三行H1均通过：P1797.265秒未证；ENS677.515与LP677.625秒认证，LP零实际分裂。下个外部编号4。R90 binary SHA bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2不动。

新生产binary SHA75915292d0df67ab48e3a9e396ec013a4a2c8b5a0aef50a983ae17ff5e135f56，源码ref9ab0a2b1064022913295c8da02a5f57288d91f44。不修改已绑定src/include/CMake或重构。primal三个F5臂已完整运行。ON原审计失败仅为旧parameter_readback不接受ORDER-ON标签；原失败audit/summary保留，round96_primal_recovery_v2.py已离线recover成功，新增audit_v2与primal_v2有效三行前缀。不要重跑recover，也不要使用旧primal_launch启动后续；新命令是python scripts/round96_primal_recovery_v2.py run --number N，N从4起。

旧serial_queue exec67034已经exit1，serial_queue_completion记录3个任务（含已付费ON、读回失败）；不能再run旧队列。serial_queue_v2_plan.json已准备，仅原计划剩余24项：H2→F2→H3→V1→H4→V2→H5/H6。先看serial_queue_v2_started/completion与真实进程；仅started不存在时才能首次执行python scripts/round96_serial_queue_v2.py run。每个三臂组都在无optimizer时等待serial_review_v2_<campaign>_<role>.json，需root自审、绑定相应decision_signals文件SHA及continue_planned_runs=true；不称独立代理。任何实际失败先保存定位，不重跑paid臂。队列源和recovery adapter/admission已冻结不要编辑。

完整F5结果ON U.3205122270/L.2815237008，OFF .3295041072/.2814538063，P .4342358368/.2682505969，全部未证。新实际启动5重排和40物理见证重放通过；最终速度未知。全部数值、修复原因见f5_full_review.md。当前43次保守启动，native micro2/4，累计native调用34，最终计划67次。

离线工具现在已执行：round96_primal_report.py f5、round96_cost_report.py f5、round96_derived_numeric.py external h1_v2与primal_v2 f5；16现存model所检行族系数均无阈值修改。报告脚本支持audit_path恢复记录。trajectory.py支持primal_v2；当前只有H1得到认证参考，F5没有可靠F*。每个新输出用新label，不覆盖；模型审计在队列review边界运行。

stage3归档已完成，91,094 members、70,892,034字节均SHA复核；含H1 ENS/LP和F5所有raw、修复失败历史、生产源码与导出。stage1/2保留旧证据。stage3为写入时快照，后续final_report/RESUME更新以Git为准。

剩余必须完成：全部18外部与12primal正式臂；保护及两独立验证；每角色认证/删失/P主参照结论；后续派生系数核查；完整费用与内部native数；三项资格判断；最终证据索引/PR更新。阶段PR158不是完成，不晋升、不合并、不扩大预算或重新抽样。

队列v2已首次启动：exec session54788，当前external #4 H2/LP-G。先检查serial_queue_v2_started/completion及runtime_status，严禁重新run队列。最新阶段提交0474cad50已push到draft PR158，生产源ref仍9ab0a2b10；不将报告提交当新binary身份。stage3 zip已远端保存（GitHub仅提示超过推荐50MB，实际push成功）。

H2组完成且通过（external #4–6），新原型F2组为下一任务（primal #4 ORDER-ON、#5 P、#6 OFF，各900秒）。队列exec54788在serial_review_v2_external_H2.json边界等待；写入绑定signals SHA的continue后继续。下次先查真实状态，不能假设仍停在此处。完成启动46次，剩余21正式任务。

F2组已完整完成，primal_v2现有6行全通过，下一任务external #7 H3/ENS-C，cap3600。队列54788当前等待serial_review_v2_primal_F2.json，绑定primal_v2/decision_signals_F2.json SHA后继续。已运行新离线primal_report f2、trajectory primal_v2 f2、derived_numeric primal_v2 f2（通过）、cost_report f2。完成49次保守启动、native56、micro2/4；剩余18正式任务。H2及F2完整raw尚未加入新归档，stage3止于H1/F5，最终需补。

H3组external #7–9已完成全通过，全删失；external summary共9行。队列54788等待serial_review_v2_external_H3.json。下一为primal #7 V1/P，随后ON/OFF，各1800秒。已执行external_report h3、derived_numeric external h3（通过）、cost_report h3。完成52次保守启动，剩余15正式任务；H2/F2/H3 raw等待后续归档，勿重跑。

V1三臂primal #7–9全部完成，primal_v2 summary共9行。ON强启动但终态较OFF退步，详见v1_review.md。队列54788等待serial_review_v2_primal_V1.json；下一个external #10 H4/P，随后LP、ENS，各1800秒。primal_report/derived_numeric/cost_report v1已运行通过；55启动、76native、micro2/4，剩余12正式任务。H2/F2/H3/V1 raw尚待后续归档。

H4 external #10–12完成：全部F0认证、P最快，见h4_review。已执行external_report/trajectory/derived_numeric external h4及cost_report h4，均通过。队列54788等待serial_review_v2_external_H4.json；下一primal #10 V2/OFF、#11 ON、#12 P，各1800秒。完成58启动、85native、micro2/4，剩余9正式任务。最新待提交H4结果；原P损失必须保留。

V2三臂primal #10–12已完成，primal_v2有效summary共12行全通过。primal_final_decision.md完成新机制阶段判断，mixed且默认关闭。primal_report complete、trajectory primal_v2 complete、derived_numeric primal_v2 complete（28模型0阈值改动）、cost_report primal_complete和primal_startup_report均已执行。当前61启动、94native、micro2/4；剩余external #13–18 H5/H6六臂，最终67启动。队列54788在serial_review_v2_primal_V2.json等待，自审后下一H5/ENS cap7200。准备增量归档H2/H3/H4与F2/V1/V2 raw；禁止复跑已完成模型。

增量归档formal_archive_through_v2已完成：18臂、56,651成员、59,276,032字节，全部SHA复核，归档217.3308493秒另计无Optimize。覆盖H2/H3/H4与F2/V1/V2。下一步提交阶段结果并写V2审核ACK启动原H5/H6六臂。

H5 #13–15完成全通过；队列54788等待serial_review_v2_external_H5.json。external_report h5、derived_numeric external h5和cost_report h5已完成。只余#16 H6/LP-G、#17 P、#18 ENS，各3600秒。当前64启动、105native、micro2/4；H5 raw尚待最终增量归档，不重复优化。最新已push提交772e26ab3含完整primal与through_v2归档。

重要最新：旧队列54788已因H6/LP #16截止hardstop审计失败退出1，严禁重新启动。原external summary16行末行为失败，保持不变；新round96_external_recovery_v2.py已成功recover，无Optimize，external_v2有效16行。#16 observed U1.0547814858565612/L.9491247933425749，无证、行政硬停止，5native/16物理见证。详见h6_interruption_review。此新adapter已绑定不可修改。下一命令仅python scripts/round96_external_recovery_v2.py run --number 17，后18；生产源/binary/输入/上限不动。当前65计费启动、110native、micro2/4（新总费用报告尚待更新）。最终报告/cost/trajectory/derived/archive需要支持external_v2、audit_path和journal计数；不能把缺CSV行当零调用，不能误称正常终态。
