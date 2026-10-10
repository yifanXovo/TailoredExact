Round110 第42项完整时钟故障的独立初步判断

原始 `42_G100-R2_S1_M-B` 记录给出：正常原生返回及 legacy 时间为
3570.890000000014 秒；从完整入口累计至 native_end 为
3571.0120709999464 秒；必要的原始 postexit audit 完成于
3600.707823600038 秒；完整回执为 3600.7215734999627 秒。
冻结 cap 为3600秒，因此必要审计本身已经超限，最后约13.75毫秒的
crosscheck/写盘并非唯一原因。不存在将完整耗时合法回填为 cap、legacy
或 native_end 的依据。

原始 `completion.within_cap=true`、正常rc0、原始audit=true、完整回执、
费用和失败包装器全部保留。数学/物理证据可以继续独立核验；它们与正式
性能窗口资格分列。第42项的正式性能资格为false，Seed1配对为UNEVALUABLE，
该配对不计入有效nonLOSS。只读描述性端点比较不能用于候选晋级。

正式结论必须BLOCKED，理由为
`ARM42_FULL_CLOCK_EXCEEDS_FROZEN_3600_SECOND_CAP`。42个原生尝试均已结束，
其中41个可具有有效完整时钟；不将该真实资源/证据故障改称性能负面结果，
不重跑、不改cap，也不改变冻结PE、argv或搜索规则。

新的独立final-only适配器保留已准入core和R109共享kernel的精确bytes。
它仅将一个提前中止的完整时钟断言改为“继续数学重建后记录严格阻断”，
保留offset非负检查并绑定第42项原始whole回执SHA。其他数学、类型、域、
Start、API/cleanup、序列化及原始时钟约束继续使用原独立核。
完整42项审计及正式表格/叙述对照尚待primary/documents准备完毕后执行；
本初步判断不是已完成的全量数学审计。
