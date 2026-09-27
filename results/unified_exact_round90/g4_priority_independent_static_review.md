# G4 F2/D6 priority wrapper：独立静态审查

只读审查 `scripts/round90_lp_g_g4_priority.py` SHA256 `dd58cc4709b5da3d08bc86d438c19aa096dcbd3a9e1ceb395043efd65e059396`、`preregistration_g4_priority.json` SHA256 `69b43ffed0e595703c96b2752f40eef5d5b3c633fd8214dda0645cb376c6ce52`、`g4_priority_preparation.md` SHA256 `73aea869ba80d009b979101d11bd71835ae0a35b1ec835e3cae931134c9d0023` 及既存 19-role manifest/输入身份摘要；未导入、执行、测试、构建或求解。**静态 PASS：可由 root 单独签零 Optimize prepare gate；真实四臂还须另签 exact identity run lease。**

预注册仅 F2 与 D6，次序 F2 ENS-C→LP-G（各 600 s）、D6 LP-G→ENS-C（各 3600 s），seed 0，完整进程 cap 合计 8400 s；native limit 分别 594/3594 s、整臂 hard stop 提前 2 s。两角色的 scenario ID、T=3600/18000、pickup/drop=60、λ=.15、输入 SHA 分别与原 19-role planning/protocol 和 Round88 独立输入 audit 一致；wrapper 在 prepare/run 均重核本地主目录实际输入字节。P-GRB 旧时间只保留未配对历史背景，没有注入 UB。冻结二进制、七份源码和八个 harness SHA 由原 G3 gate 核对；新命令由冻结 `command_for` 生成，仅角色输入、handling/T、cap 随预注册实例变化，Round90 flag 仅随臂开关。线程 1、affinity 4、Presolve −1、原 startup 与证明选项不改。

独立加载的 G3 模块只将 `CAMPAIGN` 转到 F2/D6 新目录；沿用完整 `run_one` 的物理路线、原问题界、覆盖及 LP-G proposal/child/AM/实际事务审计，角色内分别写 cross-arm 原问题矛盾收据及冻结 severe signal。正常结果另核 C++ Seed/Threads/Presolve requested/effective 与 set/get 成功、实际 ENS-C/Round90 preset；截尾结果只记 unknown。每个已启动臂保留 raw、completion、audit、参数证据和 per-role prefix；异常写失败阶段耗时，最后收据区分有 completion 的已付 process wall、未达 completion 的失败尝试下界、未运行臂及整次 outer wall。首次严重信号/审计/身份/资源失败阻止后续臂，不重试。`run_started` 与 lock 防复用旧目录，臂数四条不被误称为内部 Optimize 调用数。

prepare 在写新 campaign 前要求 root 动态绑定已完成 C2 独立 review 的路径/SHA 和 `c2_priority_criterion_accepted=true`、当前脚本/prereg/runner/binary SHA、`allow_optimize=false`；run 再要求新 identity SHA、四臂准确顺序与 `allow_optimize=true` 的独立 lease。该静态通过只保护原有 G4 的 F2/D6 优先顺序，不免除其余预注册角色，不证明 LP-G 性能或 P-GRB 优势。真实执行仍需外层发射至退出收据计入准备、审计与失败成本；本次没有运行任何命令。
