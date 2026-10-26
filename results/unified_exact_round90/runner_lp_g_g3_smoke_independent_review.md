# Round90 LP-G G3 四臂烟测独立审查

**结论：四臂原问题证书及证据身份通过，可按既定顺序另行准入下一预注册角色；LP-G 真正提交的非中点分区尚未暴露，不能据此称运行更快。** 本审查只读已有 raw、runner 收据、原始 C++ 账本与 LP 文件；未重跑模型、测试、构建、压缩或 Git。

签发的 smoke lease 绑定 `identity.json` SHA-256 `119fc81c0868b6069e229571a01ad9b2c89112ed36bf1938caf376ad6c7c4976`。四次 launch 使用相同 `ExactEBRP.exe` SHA-256 `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`、对应角色同一输入 SHA；ENS-C 与 LP-G 的 Round90 flag 分别为 false/true。后检确认 runner `da04cf7481dd6f1841383a9390059297a0db51c4ce509a449d5c71725e38b1fe`、prereg `dbc1543d2d5b112a127151736ac54d13fe168723a9327561f65aaa81bbaf745b`、七份候选源码及二进制仍匹配 prepared identity，且无残留重型进程。只运行四臂，无 rest 臂或重试。

E8 ENS-C/LP-G 进程墙钟为 **3.109/3.515 秒**，S12 LP-G/ENS-C 为 **3.578/3.484 秒**；四臂各在 120 秒整进程上限内正常退出。四份原始结果均 `optimal`，root/parent-child coverage、feasibility gate 与 strict external-tree certificate 均为 true，failure reason 为 `none`；原物理 replay 的 `original_T_feasible=true` 且零 errors，E8 两臂各六条、S12 两臂各两条已核 witness。E8 两臂相同物理 U=`0.021337006039780566`、数值 L=`0.021337006039780573`；约 `6.94e−18` 的负差只是浮点尾差。S12 两臂 U=`0.05856397312578515`、L=`0.05856397312578488`。两个原问题跨臂 L/U 矛盾检查均通过既有 `1e−7` 门槛。中间观察 bound 未被称作终局证书；这里的证书来自正常完成与最终物理验证，并沿用项目数值标准，不是有理对偶证明。

LP-G 行为须与证书分开。E8 候选在父 `L0` 域 `[0,0.022295597484276734]` 两次提出当前父 LP 标量 `G=0.0055660154395367452`，严格不同于中点 `0.011147798742138367`；父 LP 与两个子 LP 的实际模型 SHA、`OPTIMAL` 调用、terminal-valid status、精确子域端点均互相吻合，我还重算了保留的三份 canonical LP 文件 SHA。第一次完整子 LP 对之后 AM/C6 提议 `native-target`，原生 child-disjunction 目标 `0.016037601464493557` 达到并重排父叶；第二次同 epoch 账本记 `reused_identity_verified`，子 LP SHA 与 Optimize 行沿用第一次，AM/C6 转为 `exact-close`，随后父 MIP `OPTIMAL`。两次都 **没有原子分裂**。S12 候选父 LP 原始 G=`0` 位于下端点，按合同回退中点 `0.029281986562892576`；两子 LP 完整，AM/C6 为 `exact-close`，父 MIP `OPTIMAL`，同样没有原子分裂。因此 E8 证明了选点、完整子 LP、同 epoch 缓存重用与 native requeue 的实际接线；S12 是非暴露。incumbent epoch 失效及 LP-G 切点实际替换父覆盖未观察到，不能由这四臂推断已通过。

四个进程墙钟之和 **13.686 秒**，prelaunch 合计 **1.140 秒**，各臂完整可见 end-to-end 合计 **14.826 秒**；单次 `run-smoke` 外层命令墙钟 **15.1096716 秒**，余约 **0.2836716 秒**为外层运行/跨臂处理。离线 per-arm 审计 **0.0598435 秒**已含在外层成本内，不应再加。报告与原始 `summary.jsonl`、completion、outer receipt 相符。烟测没有严重风险信号，也没有方法性能优势证据；下一角色是否执行仍需原先独立 lease 和停批规则。
