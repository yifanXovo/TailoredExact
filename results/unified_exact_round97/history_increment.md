# 针对性历史与独立复核

独立只读代理 `/root/independent_review` 已核源码与直接相关历史，未运行优化器、未编译。初版复核发现四项工程问题（截止保留、C边界异常、失败后保留archive、完整callback计时），均在真实资格前修正；修订不是性能假说迭代，不能代替用户要求的证据驱动深入研究。

|机制|当前实现及默认|本轮增量|
|---|---|---|
|R60|首次MIP按输入target构造，前两个根MIPNODE按松弛库存/弧构造；完整映射后真实cbsolution；默认off|后来MIPSOL完整路线不是其输入|
|R61|预先PREFIX生成archive；回调取现成点；支持等cutoff且优于native；返回后archive交接；默认off|动态MIPSOL闭包与跨调用物理缓存为新作用域，archive/native/global分离和API不是新发明|
|R68|ENS继承；每个所需MIP（含retained）开始前提交当时外层best；完整VD-P映射、验全部行/目标/Start读回|复用既有mapper，增加真实后启动处理|
|R36|区分U_proof/U_anchor以及启动、几何、证明路径|不重述为新发现|
|R59|H/S/Single-S、simple-start与native Start区分；受限MIPFocus负结果|不否定所有原生反馈，ENS仍有原生启发式|
|R64|资源静态模型与warm/cold启动分开；同初始U可有不同证明成本|本轮固定ENS模型政策，仍须实际OFF/SHADOW/FEEDBACK归因|

复核依据：`src/GurobiBaseline.cpp`旧attemptRound60Candidate及MIPSOL路径，`src/Round61Candidates.cpp` prepare/shouldSubmit，`src/MipStartMapping.cpp`，`src/PaperExternalGiniTree.cpp` solveBudgeted/configure/merge及ensureArtifact，`src/main.cpp` ENS preset与startup；对应历史目录gf_verified_candidate_native_round60、gf_incumbent_decomposition_causal_round36、gf_core_attribution_native_round59、gf_shared_load_time_round64。

发现旧R61交接先于历史bound回放，可能倒填U；R97独立handoff延后至回放完成并用真实返回时间。旧native journal只保存首个/改善/矛盾见证，不能数MIPSOL机会；新增独立逐事件账本。legacy sibling union有更广epoch作用域风险，本轮上下层guard严格隔离标准ENS-C。现有mapper只允许真实G在叶域内的同目标映射，域不兼容不是物理不可行。
