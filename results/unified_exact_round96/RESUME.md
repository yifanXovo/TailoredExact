# R96 恢复与复现

唯一源码目录 E:/codes/ExactEBRP；分支 codex/round96-external-primal，base R95。保护原三份 dirty 文件和历史 raw；不清理、不 git add .、不重开已有 destination。Python：D:/msys64/ucrt64/bin/python.exe。

先核活动进程、serial_queue_started/completion、各 run receipt 与 summary.jsonl，再做任何计算。性能严格串行、mask4；优化期间不编译、重审计或压缩。原用户要求、final_report.md 和数学底稿共同定义未完成工作；阶段 PR158 不等于研究完成。

已完成且禁止重跑：固定路线六例及资格、第一多站原型六例、自由顺序资格与 F5_final、第二有限重排微例及六例、四次 CLI 身份检查。固定路线 F5_final 受限认证不改善；自由顺序超时未知；第二原型相对旧 R83 在四例改善、U6 两例无增量。965 个物理见证、85 次新移动及六个耗尽状态已离线复核；正式新 reader 的六例 fixture 已通过。

外部 H1 三臂均完成并通过 audit：P-GRB 1797.265 秒未证；ENS-C 677.515 秒、LP-G 677.625 秒认证同一数值目标。LP-G 有两次提案、零实际分裂；无严重信号。external_report_h1 与 external_trajectory_h1 保存完整比较和最优见证发布区间。下一外部编号4，不再启动1–3。

R90 external 二进制保持原 SHA bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2。新的默认关闭生产入口已构建，production_build_identity.json 绑定源 ref 9ab0a2b1064022913295c8da02a5f57288d91f44，binary SHA 75915292d0df67ab48e3a9e396ec013a4a2c8b5a0aef50a983ae17ff5e135f56。不要修改其 src/include/CMake 或重构。

V1/V2 已按先前计划一次生成并绑定；primal prepare 四次零 Optimize 导出已完成，实际数值检查通过。primal/identity.json 与 primal_admission.json 已冻结；12 个正式臂尚未启动。不能重跑 prepare 或生成器。已冻结 runner/reader/fixture/oracle/source 的字节不要改动，否则身份门禁将拒绝。

serial_queue_plan.json 已准备，27 个剩余任务：F5 三臂→H2→F2→H3→V1→H4→V2→H5/H6。命令为 python scripts/round96_serial_queue.py run，仅能首次执行，先检查 started 不存在。任何 paid/audit/resource 错误都停止、保留，不自动重试。完整三臂出现材料性信号后暂停，读取 signal 文件并写诚实的 root 自审 serial_review_<campaign>_<role>.json，绑定 signal_sha256 和 continue_planned_runs=true 才继续既定计划；不称独立代理审查。需要行政停止时使用 serial_queue_stop.json，不擅自终止其他任务。

当前保守启动40次，含外部前三臂、新参考导出4次及CLI4次；最终计划67/约72次，native micro 已用2/4。内部 Optimize 另数但费用不重复相加。三组以上3600–7200秒匹配预算已固定；不加种子、不延长救负结果。

完成后仍需：全部外部18臂、新原型12臂的配对与删失结论；新原型实际启动接入审计；三项独立资格决定；实际派生行数值边界说明；完整成本/调用账本；证据归档与索引；最终报告、恢复说明和 draft PR 更新。stage1/stage2 证据包已核，后者9449 members、约6.97MB，含开发源码胶囊及 H1/P；H1/ENS、LP 等后续证据尚待新包。
