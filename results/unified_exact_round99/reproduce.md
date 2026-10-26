# 复现与证据入口

基线 R98 `10d777d8ecf8d2aaa181f0fbe7445c266a968ef2`。二因素实测 v1 的生产
源码阶段提交 `2458a3f7845d6a6cf6006361268aa737274ea53b`；修改前实际193个
文件在 `frozen/v1/index.json` 绑定，本地 bundle 不提交。
深入原型及完整开发/长窗/确认使用 v2 阶段提交
`4f88a8c040047597dcfe9baa4a95a087cf925a0f` 的生产源码，实际 binary SHA
`2a568f1d729cfec9e5c759531ca39e82da0dc9f490b7a77f2f6aeb6da6be68cf`。
最终打包的分析文件不作为这些实测源码的替身。

环境：Windows、GCC14.2 UCRT64、Ninja、空 CMAKE_BUILD_TYPE、Gurobi13.0.2，
生产 `D:/gurobi1302/win64/bin/gurobi130.dll` SHA
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`。
性能串行，Threads/MIPThreads1、Seed0、PresolveAuto、原容差/零 gap、affinity4。
本轮额度已用满72启动；以下入口用于查阅或另行授权复现，不自动重跑实验。

```powershell
cmake -S . -B build/research/round99-reproduce -G Ninja -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64 -DCMAKE_BUILD_TYPE=
cmake --build build/research/round99-reproduce --target ExactEBRP Round99DiscreteTests Round99ModelExport Round65ReferenceBuild --parallel 4
build/research/round99-reproduce/Round99DiscreteTests.exe results/unified_exact_round99/reproduce_micro_export_new
```

不要全量 CTest：历史 native 测试会启动求解。上述类型/guard和11个微型
writer fixtures 不 Optimize。新增模式使用
`--round98-state-service q-integer|m-binary|m-binary-linked`；off 保持 ENS 原身份，
P 保持 compact。实际性能命令、输入和 build/helper 绑定在各 campaign identity.json。

`factorial01`18臂，`repeat01`4臂有限复核，`linked01`12臂深入开发，`long01`F5
三臂3600s。`confirmation01`仅正常前缀1..6，7中断，8/9未启动；
`confirmation_recovery01`完整三臂补N3，不能再运行原7..9或拼接两次M-B。
`round99_campaign.py prepare <new-label> <protocol>` 以当前实际源/构建冻结新的
付费身份，`run <label> <next-number>`只允许未启动的下一项；历史 identity 和
exclusive 文件不能覆盖。candidate 与生成 recipe 均在数据结果开放前冻结，
N1/N2/N3原输入一起保留。

主要阅读 final_report.md、mathematical_algorithm.md、model_change_table.md、
history_increment.md，以及 complete_results_final/runs.csv、pairs.csv、cost_failures.csv。
interrupted_runs.csv单列原N3；optimal_discovery.csv只回溯有数值F*的物理事件。
native生成/内部可见/root/cuts范围分开；独立presolve不等于optimize内部模型。

实际Start证据：前15个factorial作用域在qualification/factorial_start_*.json；
其余22个在pure_qualification/。纯解析入口为scripts/round99_pure_start_audit.py，
只接受C++ writer的线性单行LP语法，比较所有实际native列序/VType/readback及
全部行/界/目标，按原合同检查所有pd，不加载Gurobi。native reader最后一次失败
仍计费且未重试。重新执行纯解析应使用独立输出标签/临时目录，不能覆盖既有结果。

只读汇总：`scripts/round99_results.py <exclusive-new-label> factorial01 repeat01 linked01 long01 confirmation01 confirmation_recovery01`。
大型矩阵、二进制、原日志和v1 bundle 本地保留，见 local_artifact_index.json。
缺失时先查引用和SHA，不能重新导出不同字节冒充。仓库紧凑见证/CSV支持关键
结论审查；不声称重现整条B&B树、隐含整数或唯一cut因果。独立审查见root_final_review.md。
