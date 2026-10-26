# Round100 独立只读审查

审查者：用户授权的独立代理 `/root/round100_readonly_review`。在全部性能运行结束后进行一次审查，
随后仅确认同一次审查提出的报告修正。未启动求解器、原生环境、编译或测试，未修改仓库文件，
未委派其它代理。方法包括源码阅读、实际LP/Start文本核对以及审查者自行编写的内存内标准库复算。
本文件由执行者保存审查者返回的结论；执行者自审另见delivery_validation.json。

## 发现及处理

1. **P2：时间区间应明确标为记录里程碑，而非engine发现/认证瞬间。** 原
   `data_close_seconds + prelaunch_seconds`下界约束journal数据关闭里程碑，不能保证早于已经发生的
   native发现或物理验证。最终application快照也不能下界更早的engine认证瞬间。原报告虽声明
   精确时刻未知，窄t_find/t_tail仍容易误读。执行者在新独占目录measurement04重新提取，0 native：
   真正t_find的安全宽区间从本臂进程启动至首个合格见证观测；t_tail宽区间对应真正取得该见证至
   原完整正常完成边界。窄区间改名为journal发布/观测及其至完整完成的里程碑间隔。
   审查者随后核对脚本和measurement04，确认上下界及语义有效，不用于断言native瞬间或先后。
2. **P3：旧prefix审计说明文字容易误读。** 所有端点audit.json顶层explanation继承
   “Observational interrupted endpoint”，包含正常返回及已认证臂；追加的normal_result_certificate、
   endpoint.certificate和completion.stop_reason正确区分终态。原审计证据保持原样，报告与复现说明
   解释旧文字只表示observational prefix合同，本轮全部normal_return，未发生行政中断。
   审查者确认此处理正确。

未发现新的模型、物理见证或费用缺陷。两项修正均只涉及报告/只读分析，不重跑性能或修改冻结源码。

## 通过的主要核对

- ENS-Q默认关闭，准入拒绝与旧A/B模式混用；实际writer只改变p/d原生声明。Y/load整数、
  s/z/m二元、唯一访问、原方向界及非零服务行保留。无A/B的隐含整数性证明成立；局部反例
  的外推范围在数学文档中受到正确限制。
- 直接解析实际固定F2 LP：C/Q目标、界及类型区前全文相同，恰80个p/d从I改C；Q/M-B类型
  完全相同，M-B恰增加40条数值行、删除0条；没有theta。
- 独立解析全部15个actual submitted Starts，共84,108个列类型、数值及回读，并逐一复查全部行、
  界和目标。最大残差5.268008251846368e-14，目标差0。
- Native LP捕获实际VType数组并按原数组恢复；完整typed canonical SHA及cutoff epoch参与缓存
  有效性。Q及旧研究模式在MIPSOL和最终解码检查全部p/d，包括未访问列的存在、有限性、
  原物理上界和整数容差。最终异常清除UB/原生认证资格并拒绝outcome。
- 独立复算1,077个见证事件、24个终态路线、6个输入：唯一服务、单向非零操作、原操作界、库存、
  空载出发的逐站载荷及含返仓卸载的时长均通过。最大F/G/P差分别为8.88e-16、7.36e-16、
  3.55e-15；最小时间余量约0.119451秒。
- 全部七个实际P导出保留整数p/d，无研究state/theta块，各自仅一次Optimize、无User MIP start。
  三个开发P reference等于实际R99 factorial01 reference。ENS-C默认数学行为未因新开关改变。
- 八个正常数值证书均有原生产完整覆盖/闭合flags；九个长时臂全部未证，H100的C/M-B已证而P未证。
  内部OPTIMAL没有直接升级为原问题证书。微小负signed gap保留，长窗和P的删失限制正确。
- 独立求和确认33次计费启动、67471.79740550002外层进程秒、99次Optimize。正式93次由ENS家族
  ledger的86次及七个P调用组成，另六次有限资格调用。参考生成/reader已收费，内部调用未重复计费；
  工程measurement01的0-native失败保留。
- 四个campaign的177个source hashes等于候选冻结，当前源码及runner/helper字节匹配。N2三臂统一
  3600，资源决策在启动前冻结；H100一次exclusive生成，规则在候选冻结阶段保存，无redraw路径。
- 检查点121条=105 covered+16 uncovered；未覆盖U/L/gap为空，没有插值。主要配对与结论一致：
  Q的F2严重认证回退、M-B的F5质量保护损失、长时相对P窗口收益及H100单角色证书收益均保留。

## 范围与结论

这是独立源码、实际记录和物理可行性审查，不是独立native B&B搜索复现或精确算术证明。
没有独立重新求解LP/MIP、重建完整内部搜索树或验证Gurobi隐藏分支/cut因果；SHA核对不能替代这些工作。
报告口径修正后，现有研究结论可支持。不能据此宣称M-B稳定最终快于P或取得统一算法晋升资格。
